import os
import asyncio
import time
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response, HTTPException, Header
from starlette.websockets import WebSocketState
import base64
import numpy as np

from .providers.programmable_voice import TwilioProgrammableVoiceAdapter
from services.audio import AudioPreprocessor, AudioQuality
from services.antispoof import get_detector
from core.redis_client import publish_event, set_state, get_state, delete_state
from core.database import async_session_maker
from repositories.call_repository import CallRepository
from schemas.pipeline import PipelineEvent, CallSummary
from services.risk import RiskFusionEngine, TemporalStateTracker
from services.speaker.verification import verify_speaker
from models.domain import ProtectedNumber
from sqlalchemy.future import select
import uuid
from datetime import datetime, timezone
import json
from services.notifications.push import send_high_risk_alert
from core.logger import get_logger, set_correlation_ids
from core.metrics import (
    ACTIVE_CALLS, ACTIVE_WS_CONNECTIONS,
    AUDIO_PACKETS_RECEIVED, AUDIO_PACKETS_DROPPED,
    AUDIO_WINDOWS_TOTAL, AUDIO_WINDOWS_VALID, AUDIO_WINDOWS_POOR_QUALITY,
    E2E_ANALYSIS_LATENCY, HIGH_RISK_ALERTS, CALLS_TOTAL
)

logger = get_logger(__name__)
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
    from twilio.request_validator import RequestValidator
    
    load_dotenv()
    
    # 1. Verify Twilio Signature
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if auth_token:
        validator = RequestValidator(auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        
        # We need the absolute URL requested by Twilio (usually our ngrok or prod domain)
        url = str(request.url)
        # Twilio validates using https in production, ensure scheme matches what they sent
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto and url.startswith("http://"):
            url = url.replace("http://", f"{forwarded_proto}://", 1)
            
        form_data = await request.form()
        post_vars = dict(form_data) if request.method == "POST" else {}
        
        if not validator.validate(url, post_vars, signature) and os.environ.get("ENV") != "development":
            logger.warning(f"Invalid Twilio Signature for webhook: {url}")
            return Response(content='<Response><Reject/></Response>', media_type="application/xml", status_code=403)
    
    base_url = os.environ.get("BASE_URL", "https://localhost:8000")
    # Convert https:// to wss:// or http:// to ws://
    ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
    
    # We strip trailing slashes if present
    if ws_url.endswith("/"):
        ws_url = ws_url[:-1]
        
    # Parse 'To' number to route the call
    if request.method == "POST":
        to_number = form_data.get("To")
    else:
        to_number = request.query_params.get("To")
        
    if not to_number:
        logger.warning("Twilio webhook received without a 'To' number.")
        return Response(content='<Response><Reject/></Response>', media_type="application/xml")
        
    # Lookup the protected number
    async with async_session_maker() as session:
        stmt = select(ProtectedNumber).where(ProtectedNumber.provider_number == to_number, ProtectedNumber.enabled == True)
        result = await session.execute(stmt)
        protected_number = result.scalar_one_or_none()
        
    if not protected_number:
        logger.warning(f"Incoming call to unregistered or disabled number: {to_number}")
        return Response(content='<Response><Reject/></Response>', media_type="application/xml")

    user_id = str(protected_number.user_id)
    
    # Inject basic auth credentials for WebSocket security
    ws_user = "twilio_stream"
    ws_pass = os.environ.get("TWILIO_AUTH_TOKEN", "default_secret")
    
    # Insert credentials into WSS URL: wss://user:pass@domain/path
    if "://" in ws_url:
        protocol, domain = ws_url.split("://")
        stream_url = f"{protocol}://{ws_user}:{ws_pass}@{domain}/v1/streams/provider/twilio"
    else:
        stream_url = f"{ws_url}/v1/streams/provider/twilio"
    
    # Generate simple TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>This call is protected by Voice Guard. Please wait while we analyze the connection.</Say>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="track" value="inbound_track"/>
            <Parameter name="user_id" value="{user_id}"/>
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
    
    ACTIVE_WS_CONNECTIONS.labels(connection_type="twilio_ingest").inc()
    
    if provider.lower() != "twilio":
        logger.error(f"Unsupported provider: {provider}")
        ACTIVE_WS_CONNECTIONS.labels(connection_type="twilio_ingest").dec()
        await websocket.close(code=1003)
        return
        
    # 2. Verify Basic Auth sent by Twilio
    auth_header = websocket.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        logger.warning("Rejecting streaming connection: Missing Basic Auth")
        ACTIVE_WS_CONNECTIONS.labels(connection_type="twilio_ingest").dec()
        CALLS_TOTAL.labels(outcome="unauthorized").inc()
        await websocket.close(code=1008)
        return
        
    try:
        decoded_auth = base64.b64decode(auth_header.split(" ")[1]).decode()
        username, password = decoded_auth.split(":")
        expected_pass = os.environ.get("TWILIO_AUTH_TOKEN", "default_secret")
        if username != "twilio_stream" or password != expected_pass:
            logger.warning("Rejecting streaming connection: Invalid Basic Auth credentials")
            ACTIVE_WS_CONNECTIONS.labels(connection_type="twilio_ingest").dec()
            CALLS_TOTAL.labels(outcome="unauthorized").inc()
            await websocket.close(code=1008)
            return
    except Exception as e:
        logger.warning(f"Rejecting streaming connection: Malformed Basic Auth ({e})")
        ACTIVE_WS_CONNECTIONS.labels(connection_type="twilio_ingest").dec()
        CALLS_TOTAL.labels(outcome="unauthorized").inc()
        await websocket.close(code=1008)
        return
        
    adapter = TwilioProgrammableVoiceAdapter()
    
    ingest_queue = asyncio.Queue(maxsize=100)
    ai_queue = asyncio.Queue(maxsize=5) 
    
    session_id = str(uuid.uuid4())
    call_id = None
    db_call_id = None
    risk_engine = None
    session_started_at = datetime.now(timezone.utc)
    
    # Stats
    total_audio_windows = 0
    analyzed_windows = 0
    max_risk_level = "STARTING"
    user_id = None
    DUMMY_ORG_ID = "00000000-0000-0000-0000-000000000000"
    
    def on_window_ready(window_audio: np.ndarray, quality: AudioQuality):
        nonlocal total_audio_windows
        total_audio_windows += 1
        AUDIO_WINDOWS_TOTAL.inc()
        try:
            ai_queue.put_nowait((window_audio, quality, time.perf_counter()))
            if quality.get("usable", True):
                AUDIO_WINDOWS_VALID.inc()
            else:
                AUDIO_WINDOWS_POOR_QUALITY.inc()
        except asyncio.QueueFull:
            AUDIO_PACKETS_DROPPED.labels(reason="ai_queue_full").inc()
            logger.warning(
                f"AI queue full. Dropping stale audio window.",
                extra={"session_id": session_id, "call_id": call_id}
            )

    audio_pipeline = AudioPreprocessor(on_window_ready=on_window_ready)
    
    async def pipeline_worker():
        while True:
            chunk = await ingest_queue.get()
            if chunk is None:
                break
            audio_pipeline.process_twilio_payload(chunk)
            ingest_queue.task_done()
            
    async def ai_worker():
        nonlocal analyzed_windows, max_risk_level, user_id
        last_processed_timestamp = -1.0
        
        while True:
            item = await ai_queue.get()
            if item is None:
                break
            window_audio, quality, packet_received_at = item
            _e2e_start = packet_received_at  # measure from when window was queued
            
            # The AudioPreprocessor yields AI-ready float32 audio.
            # If the quality is too poor, skip inference to avoid false positives.
            if not quality.get("usable", True):
                logger.info(
                    "Skipping inference: poor audio quality",
                    extra={"reason": quality.get('reason'), "session_id": session_id, "call_id": call_id}
                )
                spoof_prob = None
                ai_status = "LOW_AUDIO_QUALITY"
            else:
                try:
                    # Detector expects float32 window (16kHz)
                    ai_result = await antispoof_detector.analyze(window_audio, 16000)
                    spoof_prob = ai_result.spoof_probability
                    ai_status = ai_result.status
                except Exception as e:
                    logger.error(
                        f"AI inference failed: {e}",
                        extra={"session_id": session_id, "call_id": call_id}
                    )
                    spoof_prob = None
                    ai_status = "ANALYSIS_ERROR"
                
            if call_id:
                # 1. Fetch current risk state from Redis
                state_key = f"risk_state:{call_id}"
                state_raw = await get_state(state_key)
                
                state_dict = json.loads(state_raw) if state_raw else None
                temporal_tracker = TemporalStateTracker(state_dict=state_dict)
                
                # 2. Update Temporal Anti-Spoof Tracking
                quality_usable = quality.get("usable", True)
                temporal_tracker.process_window(
                    spoof_prob=spoof_prob,
                    window_duration_s=4.0 if quality_usable else 0.0
                )
                
                # 3. Save state back to Redis
                await set_state(state_key, json.dumps(temporal_tracker.dump_state()), expire_seconds=3600)
                
                # 4. Optional Speaker Verification
                expected_speaker_id = adapter.get_expected_speaker()
                speaker_result = None
                speaker_similarity = None
                
                if expected_speaker_id and quality_usable:
                    verification = await verify_speaker(window_audio, expected_speaker_id)
                    speaker_similarity = verification.similarity
                
                # 5. Fusion Engine Evaluation
                fusion_engine = RiskFusionEngine()
                assessment = fusion_engine.evaluate(
                    ai_status=ai_status,
                    raw_spoof_prob=spoof_prob,
                    quality_usable=quality_usable,
                    speaker_similarity=speaker_similarity,
                    temporal_state=temporal_tracker
                )
                
                # Publish event to Redis
                pipeline_event = PipelineEvent(
                    session_id=session_id,
                    call_id=call_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="risk.update",
                    payload=assessment.model_dump()
                )
                
                await publish_event(call_id, pipeline_event.model_dump_json())
                
                # Observe E2E latency
                E2E_ANALYSIS_LATENCY.observe(time.perf_counter() - _e2e_start)
                
                logger.info(
                    "Risk update published",
                    extra={
                        "call_id": call_id,
                        "session_id": session_id,
                        "risk_level": assessment.riskLevel,
                        "risk_score": round(assessment.riskScore, 3),
                        "confidence": round(assessment.confidence, 3),
                    }
                )
                
                # Save asynchronously to DB
                if db_call_id:
                    async with async_session_maker() as db_session:
                        repo = CallRepository(db_session)
                        now = datetime.now(timezone.utc)
                        # We use rawRisk for signal score, smoothed risk for risk event
                        await repo.add_risk_event(db_call_id, now, assessment.riskLevel, assessment.riskScore, assessment.confidence)
                        await repo.add_signal_score(
                            db_call_id, now, 
                            spoof_prob if spoof_prob is not None else 0.0, 
                            "poor" if not quality_usable else "good", 
                            4.0 if quality_usable else 0.0
                        )
                        
                        # Push Notification Check
                        if assessment.riskLevel == "HIGH" and user_id:
                            cooldown_key = f"alert_cooldown:{call_id}"
                            is_cooldown = await get_state(cooldown_key)
                            if not is_cooldown:
                                logger.info(
                                    "Triggering HIGH risk push notification",
                                    extra={"call_id": call_id, "user_id": user_id}
                                )
                                await send_high_risk_alert(uuid.UUID(user_id), call_id, db_session)
                                HIGH_RISK_ALERTS.inc()
                                # 60 seconds cooldown
                                await set_state(cooldown_key, "1", expire_seconds=60)
                                
                        await db_session.commit()
                
            ai_queue.task_done()

    pipeline_task = asyncio.create_task(pipeline_worker())
    ai_task = asyncio.create_task(ai_worker())

    ACTIVE_CALLS.inc()

    try:
        max_duration_seconds = 7200 # 2 hours
        session_start_time = asyncio.get_event_loop().time()
        
        while True:
            # 1. Check max duration
            if asyncio.get_event_loop().time() - session_start_time > max_duration_seconds:
                logger.warning(f"Max session duration exceeded for call {call_id}. Terminating.")
                break
                
            # 2. Receive with timeout (acts as heartbeat check)
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket timeout (no media received) for session {session_id}")
                break
                
            # 3. Handle message with payload protection
            try:
                event_type, audio_data = adapter.parse_message(data)
            except Exception as e:
                logger.warning(f"Malformed WebSocket payload in session {session_id}: {e}")
                continue # drop invalid frames instead of crashing
            
            if event_type == "start":
                call_id = adapter.call_id
                
                # Retrieve expected speaker id if provided in custom parameters
                expected_speaker_id = adapter.custom_parameters.get("expected_speaker_id")
                adapter.set_expected_speaker(expected_speaker_id)
                
                # Initialize Risk state in Redis
                tracker = TemporalStateTracker()
                await set_state(f"risk_state:{call_id}", json.dumps(tracker.dump_state()), expire_seconds=3600)
                
                logger.info(f"Stream started from {provider} - Call {adapter.call_id}")
                
                # Extract the assigned user_id from the webhook custom parameters
                user_id = adapter.custom_parameters.get("user_id")
                
                if not user_id:
                    logger.warning("Stream started without a user_id parameter. Dropping stream.")
                    await websocket.close(code=1008)
                    break

                # Create call session
                async with async_session_maker() as session:
                    repo = CallRepository(session)
                    call_session = await repo.create_call_session(
                        org_id=uuid.UUID(user_id), # Using user_id as org_id since it's personal org
                        provider=provider,
                        provider_call_id=adapter.call_id,
                        caller_number="Unknown", # Ideally extracted from webhook, but ok for now
                        direction="inbound"
                    )
                    db_call_id = call_session.id
                
                await publish_event(call_id, PipelineEvent(
                    session_id=session_id,
                    call_id=call_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="call.started",
                    payload={}
                ).model_dump_json())
                
            elif event_type == "media" and audio_data is not None:
                AUDIO_PACKETS_RECEIVED.inc()
                try:
                    ingest_queue.put_nowait(audio_data)
                except asyncio.QueueFull:
                    AUDIO_PACKETS_DROPPED.labels(reason="ingest_queue_full").inc()
                    logger.warning(
                        "Ingest queue full. Dropping raw audio frame.",
                        extra={"session_id": session_id, "call_id": call_id}
                    )
                    
            elif event_type == "stop":
                break
                
    except WebSocketDisconnect:
        logger.info(
            "Provider WebSocket disconnected",
            extra={"session_id": session_id, "call_id": call_id}
        )
    except Exception as e:
        CALLS_TOTAL.labels(outcome="error").inc()
        logger.error(
            f"Error in provider ingestion loop: {e}",
            extra={"session_id": session_id, "call_id": call_id}
        )
    finally:
        ACTIVE_CALLS.dec()
        ACTIVE_WS_CONNECTIONS.labels(connection_type="twilio_ingest").dec()
        # Cleanup
        try:
            ingest_queue.put_nowait(None)
            ai_queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
            
        try:
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()
        except RuntimeError:
            pass
            
        if call_id:
            ended_at = datetime.now(timezone.utc)
            
            # Emit call ended
            await publish_event(call_id, PipelineEvent(
                session_id=session_id,
                call_id=call_id,
                timestamp=ended_at.isoformat(),
                event_type="call.ended",
                payload={}
            ).model_dump_json())
            
            # Update call session in DB
            final_risk = 0.0
            state_raw = await get_state(f"risk_state:{call_id}")
            if state_raw:
                state_dict = json.loads(state_raw)
                final_risk = state_dict.get("smoothed_score", 0.0)
                
            if db_call_id:
                async with async_session_maker() as db_session:
                    repo = CallRepository(db_session)
                    await repo.finalize_call_session(
                        db_call_id, ended_at, max_risk_level, 
                        final_risk, 
                        total_audio_windows, analyzed_windows
                    )
                    await db_session.commit()
            
            # Persist summary
            summary = CallSummary(
                session_id=session_id,
                call_id=call_id,
                started_at=session_started_at.isoformat(),
                ended_at=ended_at.isoformat(),
                max_risk_level=max_risk_level,
                total_audio_windows=total_audio_windows,
                analyzed_windows=analyzed_windows,
                provider="twilio"
            )
            await set_state(f"summary:{call_id}", summary.model_dump_json(), expire_seconds=86400)
            
            # Clean up active state
            await delete_state(f"risk_state:{call_id}")
            
        logger.info(f"Terminated VoiceGuard session {session_id}")
