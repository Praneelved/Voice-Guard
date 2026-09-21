import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from .providers.programmable_voice import TwilioProgrammableVoiceAdapter
from services.audio_pipeline.pipeline import AudioPipeline
from services.antispoof import get_detector
from services.risk_engine import RiskEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# Global detector instance loaded once
antispoof_detector = get_detector()

@router.websocket("/v1/streams/provider/{provider}")
async def websocket_provider_endpoint(websocket: WebSocket, provider: str):
    await websocket.accept()
    
    if provider.lower() != "twilio":
        logger.error(f"Unsupported provider: {provider}")
        await websocket.close(code=1003)
        return
        
    adapter = TwilioProgrammableVoiceAdapter()
    
    # Bounded queue to prevent slow AI/Pipeline from backing up the network socket
    ingest_queue = asyncio.Queue(maxsize=100)
    ai_queue = asyncio.Queue(maxsize=5) # Drop AI windows if we get too far behind
    
    call_id = None
    risk_engine = None
    
    def on_window_ready(window_audio, metrics):
        try:
            ai_queue.put_nowait((window_audio, metrics))
        except asyncio.QueueFull:
            logger.warning(f"AI queue full. Dropping stale audio window for call {call_id}.")

    audio_pipeline = AudioPipeline(on_window_ready=on_window_ready)
    
    # Background Task 1: Pull from ingest queue -> Pipeline
    async def pipeline_worker():
        while True:
            chunk = await ingest_queue.get()
            if chunk is None: # sentinel
                break
            # Push chunk is synchronous but fast
            audio_pipeline.push_chunk(chunk)
            ingest_queue.task_done()
            
    # Background Task 2: Pull from AI queue -> Inference -> Risk Engine
    async def ai_worker():
        while True:
            item = await ai_queue.get()
            if item is None:
                break
            window_audio, metrics = item
            
            # Predict (can be slow, but it's isolated to this background task)
            # We use asyncio.to_thread to prevent blocking the event loop
            try:
                ai_result = await asyncio.to_thread(antispoof_detector.predict, window_audio, metrics)
                spoof_prob = ai_result.get("spoof_probability")
            except Exception as e:
                logger.error(f"AI inference failed: {e}")
                spoof_prob = None
                
            if risk_engine:
                event = risk_engine.process_window(
                    antispoof=spoof_prob,
                    audio_quality=metrics.get("quality", "unknown"),
                    usable_speech_s=metrics.get("usable_speech_duration", 0.0)
                )
                # Here we would broadcast 'event' to the frontend via the other WS manager.
                # For now, just log the state transitions.
                logger.info(f"Risk Update [{event.call_id}]: {event.level} (Risk: {event.risk:.2f})")
                
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
                logger.info(f"Initialized RiskEngine for call: {call_id}")
                
            elif event_type == "media" and audio_data is not None:
                # Fast path ingestion: do not wait for processing
                try:
                    ingest_queue.put_nowait(audio_data)
                except asyncio.QueueFull:
                    logger.warning(f"Ingest queue full. Dropping raw audio frame for call {call_id}")
                    
            elif event_type == "stop":
                break
                
    except WebSocketDisconnect:
        logger.info(f"Provider disconnected unexpectedly for call {call_id}")
    except Exception as e:
        logger.error(f"Error in provider ingestion loop: {e}")
    finally:
        # Cleanup
        try:
            ingest_queue.put_nowait(None)
            ai_queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
            
        # Ensure we don't block the caller if they close
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
            
        logger.info(f"Terminated VoiceGuard session for call {call_id}")
