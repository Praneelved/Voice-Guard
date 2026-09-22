import pytest
import asyncio
import base64
import json
import uuid
import numpy as np
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from starlette.testclient import TestClient as StarletteClient
from unittest.mock import patch, AsyncMock, MagicMock

from main import app

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
@patch("services.stream_ingest.router.publish_event", new_callable=AsyncMock)
@patch("services.stream_ingest.router.CallRepository", autospec=True)
async def test_e2e_pipeline(MockRepo, mock_publish_event):
    call_id = str(uuid.uuid4())
    client = StarletteClient(app)
    
    with client.websocket_connect("/v1/streams/provider/twilio") as websocket:
        
        # 1. Send start
        websocket.send_json(generate_mock_twilio_start(call_id))
        
        # 2. Wait a tiny bit for async init
        await asyncio.sleep(0.1)
        
        # 3. Create dummy mu-law audio (1 second of silence)
        silence_mulaw = b'\xff' * 8000
        b64_audio = base64.b64encode(silence_mulaw).decode('utf-8')
        
        for _ in range(4):
            websocket.send_json(generate_mock_twilio_media(b64_audio))
            
        await asyncio.sleep(1.0)
        
        # 4. Stop
        websocket.send_json(generate_mock_twilio_stop())
        
    assert mock_publish_event.called
