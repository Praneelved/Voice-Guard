import os
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response
from starlette.websockets import WebSocketState

from .providers.programmable_voice import TwilioProgrammableVoiceAdapter
from services.audio_pipeline.pipeline import AudioPipeline
from services.antispoof import get_detector
from services.risk_engine import RiskEngine
from schemas.pipeline import PipelineEvent, CallSummary
from core.redis_client import publish_event, set_state
import uuid
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Global detector instance loaded once
antispoof_detector = get_detector()

@router.api_route("/v1/providers/twilio/webhook", methods=["GET", "POST"])
async def twilio_inbound_webhook(request: Request):
    """
    Twilio hits this endpoint when someone dials the VoiceGuard phone number.
    We return TwiML instructing Twilio to open a WebSocket stream to our ingestion server.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    base_url = os.environ.get("BASE_URL", "https://localhost:8000")
    # Convert https:// to wss:// or http:// to ws://
    ws_url = base_url.replace("http", "ws")
    
    # We strip trailing slashes if present
    if ws_url.endswith("/"):
        ws_url = ws_url[:-1]
        
    stream_url = f"{ws_url}/v1/streams/provider/twilio"
    
    # Generate simple TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>This call is protected by Voice Guard. Please wait while we analyze the connection.</Say>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="track" value="inbound_track"/>
        </Stream>
    </Connect>
    <!-- Pause keeps the call alive while the stream is open -->
    <Pause length="3600"/>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")

@router.websocket("/v1/streams/provider/{provider}")
async def websocket_provider_endpoint(websocket: WebSocket, provider: str):
    await websocket.accept()
    
    if provider.lower() != "twilio":
        logger.error(f"Unsupported provider: {provider}")
        await websocket.close(code=1003)
        return
        
    adapter = TwilioProgrammableVoiceAdapter()
    
    ingest_queue = asyncio.Queue(maxsize=100)
    ai_queue = asyncio.Queue(maxsize=5) 
    
    session_id = str(uuid.uuid4())
    call_id = None
    risk_engine = None
    session_started_at = datetime.now(timezone.utc).isoformat()
    
    # Stats
    total_audio_windows = 0
    analyzed_windows = 0
    max_risk_level = "STARTING"
    
    def on_window_ready(window_audio, metrics):
        nonlocal total_audio_windows
        total_audio_windows += 1
        try:
            ai_queue.put_nowait((window_audio, metrics))
        except asyncio.QueueFull:
            logger.warning(f"AI queue full. Dropping stale audio window for session {session_id}.")

    audio_pipeline = AudioPipeline(on_window_ready=on_window_ready)
    
    async def pipeline_worker():
        while True:
            chunk = await ingest_queue.get()
            if chunk is None:
                break
            audio_pipeline.push_chunk(chunk)
            ingest_queue.task_done()
            
    async def ai_worker():
        nonlocal analyzed_windows, max_risk_level
        last_processed_timestamp = -1.0
        
        while True:
            item = await ai_queue.get()
            if item is None:
                break
            window_audio, metrics = item
            
            # Stale / Out of order detection
            window_start = metrics.get("window_start_s", 0.0)
            if window_start < last_processed_timestamp:
                logger.warning(f"Discarding out-of-order prediction. Window start: {window_start}")
                ai_queue.task_done()
                continue
                
            last_processed_timestamp = window_start
            
            try:
                ai_result = await asyncio.to_thread(antispoof_detector.predict, window_audio, metrics)
                spoof_prob = ai_result.get("spoof_probability")
            except Exception as e:
                logger.error(f"AI inference failed: {e}")
                spoof_prob = None
                
            if risk_engine and call_id:
                event = risk_engine.process_window(
                    antispoof=spoof_prob,
                    audio_quality=metrics.get("quality", "unknown"),
                    usable_speech_s=metrics.get("usable_speech_duration", 0.0)
                )
                
                analyzed_windows += 1
                max_risk_level = event.level # simplified tracking
                
                # Publish event to Redis
                pipeline_event = PipelineEvent(
                    session_id=session_id,
                    call_id=call_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="risk.update",
                    payload={
                        "level": event.level,
                        "risk": event.risk,
                        "confidence": event.confidence
                    }
                )
                
                await publish_event(call_id, pipeline_event.model_dump_json())
                logger.info(f"Published Risk Update [{call_id}]: {event.level} (Risk: {event.risk:.2f})")
                
            ai_queue.task_done()

    pipeline_task = asyncio.create_task(pipeline_worker())
    ai_task = asyncio.create_task(ai_worker())

    try:
        while True:
            data = await websocket.receive_json()
            event_type, audio_data = adapter.parse_message(data)
            
            if event_type == "start":
                call_id = adapter.call_id
                risk_engine = RiskEngine(call_id=call_id)
                logger.info(f"Initialized Session {session_id} for call {call_id}")
                
                await publish_event(call_id, PipelineEvent(
                    session_id=session_id,
                    call_id=call_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="call.started",
                    payload={}
                ).model_dump_json())
                
            elif event_type == "media" and audio_data is not None:
                try:
                    ingest_queue.put_nowait(audio_data)
                except asyncio.QueueFull:
                    logger.warning(f"Ingest queue full. Dropping raw audio frame for session {session_id}")
                    
            elif event_type == "stop":
                break
                
    except WebSocketDisconnect:
        logger.info(f"Provider disconnected unexpectedly for session {session_id}")
    except Exception as e:
        logger.error(f"Error in provider ingestion loop: {e}")
    finally:
        # Cleanup
        try:
            ingest_queue.put_nowait(None)
            ai_queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
            
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
            
        if call_id:
            ended_at = datetime.now(timezone.utc).isoformat()
            
            # Emit call ended
            await publish_event(call_id, PipelineEvent(
                session_id=session_id,
                call_id=call_id,
                timestamp=ended_at,
                event_type="call.ended",
                payload={}
            ).model_dump_json())
            
            # Persist summary
            summary = CallSummary(
                session_id=session_id,
                call_id=call_id,
                started_at=session_started_at,
                ended_at=ended_at,
                max_risk_level=max_risk_level,
                total_audio_windows=total_audio_windows,
                analyzed_windows=analyzed_windows,
                provider="twilio"
            )
            await set_state(f"summary:{call_id}", summary.model_dump_json(), expire_seconds=86400)
            
        logger.info(f"Terminated VoiceGuard session {session_id}")
