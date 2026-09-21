import pytest
import asyncio
import base64
import json
import uuid
import numpy as np
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from starlette.testclient import TestClient as StarletteClient

from main import app
from core.redis_client import subscribe_events, get_state, get_redis

# Pytest async config
pytest_plugins = ('pytest_asyncio',)

def generate_mock_twilio_start(call_id: str):
    return {
        "event": "start",
        "sequenceNumber": "1",
        "start": {
            "accountSid": "AC...",
            "streamSid": "MZ...",
            "callSid": call_id,
            "tracks": ["inbound", "outbound"],
            "mediaFormat": {
                "encoding": "audio/x-mulaw",
                "sampleRate": 8000,
                "channels": 1
            }
        }
    }

def generate_mock_twilio_media(payload_b64: str):
    return {
        "event": "media",
        "sequenceNumber": "2",
        "media": {
            "track": "inbound",
            "chunk": "1",
            "timestamp": "5",
            "payload": payload_b64
        }
    }

def generate_mock_twilio_stop():
    return {
        "event": "stop",
        "sequenceNumber": "3",
        "stop": {
            "accountSid": "AC...",
            "callSid": "CA..."
        }
    }

@pytest.mark.asyncio
async def test_e2e_pipeline():
    """
    Simulates a Twilio call coming in and tests the entire pipeline:
    1. Provider sends 'start'
    2. Provider sends 'media'
    3. Pipeline processes and publishes risk to Redis
    4. Provider sends 'stop'
    5. Summary is stored in Redis
    """
    # Flush redis for testing
    r = await get_redis()
    await r.flushdb()
    
    call_id = str(uuid.uuid4())
    client = StarletteClient(app)
    
    # We will run the websocket client in a separate task so we can also subscribe to redis
    with client.websocket_connect("/v1/streams/provider/twilio") as websocket:
        
        # 1. Send start
        websocket.send_json(generate_mock_twilio_start(call_id))
        
        # 2. Wait a tiny bit for async init
        await asyncio.sleep(0.1)
        
        # 3. Create dummy mu-law audio (e.g. 1 second of silence)
        # 8000 samples for 1 second. '0xff' is silence in mu-law
        silence_mulaw = b'\xff' * 8000
        b64_audio = base64.b64encode(silence_mulaw).decode('utf-8')
        
        # Send enough media to trigger a window (3 seconds needed, so send 4 seconds)
        for _ in range(4):
            websocket.send_json(generate_mock_twilio_media(b64_audio))
            
        # Give the pipeline a moment to process the window and run inference
        await asyncio.sleep(1.0)
        
        # 4. Stop
        websocket.send_json(generate_mock_twilio_stop())
        
    # Now check Redis for the events
    summary_raw = await get_state(f"summary:{call_id}")
    assert summary_raw is not None
    
    summary = json.loads(summary_raw)
    assert summary["call_id"] == call_id
    assert summary["total_audio_windows"] > 0
    assert summary["analyzed_windows"] > 0
