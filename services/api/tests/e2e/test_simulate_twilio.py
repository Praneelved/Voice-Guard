import pytest
import httpx
import websockets
import json
import base64
import os
import uuid
import jwt
import asyncio
import pytest_asyncio
from twilio.request_validator import RequestValidator
from urllib.parse import urlparse

BASE_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001"

# Fallback secrets since this runs locally
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "placeholder-secret")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "c4d1868f73d8ff7fb089f6a9ce3f502a")

def generate_jwt(user_id=None):
    if not user_id:
        user_id = str(uuid.uuid4())
    random_email = f"test_{uuid.uuid4().hex[:8]}@voiceguard.app"
    payload = {
        "sub": user_id,
        "email": random_email,
        "role": "authenticated"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256"), user_id

def sign_twilio_request(url, params):
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    signature = validator.compute_signature(url, params)
    return signature

@pytest_asyncio.fixture
async def authenticated_user():
    token, user_id = generate_jwt()
    return {"token": token, "user_id": user_id}

@pytest_asyncio.fixture
async def create_webhook_call(authenticated_user):
    # Make a dummy authenticated request to ensure the user is provisioned in the DB
    token = authenticated_user["token"]
    async with httpx.AsyncClient() as client:
        await client.get(f"{BASE_URL}/health", headers={"Authorization": f"Bearer {token}", "X-Forwarded-Proto": "https"})
        await client.get(f"{BASE_URL}/v1/calls", headers={"Authorization": f"Bearer {token}", "X-Forwarded-Proto": "https"})

    # Register the protected number manually in DB for the test user
    import asyncpg
    conn = await asyncpg.connect(os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres.pyodckcogklxrlfcbhpc:Ayush%4025117@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres").replace("+asyncpg", ""))
    
    user_uuid = authenticated_user["user_id"]
    await conn.execute("INSERT INTO organizations (id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING", uuid.UUID(user_uuid), "Test Org")
    await conn.execute("INSERT INTO users (id, org_id, email, role) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING", uuid.UUID(user_uuid), uuid.UUID(user_uuid), f"test_{user_uuid[:8]}@voiceguard.app", "authenticated")
    
    await conn.execute("DELETE FROM protected_numbers WHERE provider_number = $1", "+17372508034")
    await conn.execute("INSERT INTO protected_numbers (id, user_id, provider, provider_number, enabled) VALUES ($1, $2, $3, $4, $5)",
        uuid.uuid4(), uuid.UUID(user_uuid), "twilio", "+17372508034", True
    )
    await conn.close()

    async def _create(called="+17372508034", caller="+15551234567"):
        call_sid = "CA" + str(uuid.uuid4().hex)[:32]
        params = {
            "CallSid": call_sid,
            "Caller": caller,
            "Called": called,
            "To": called,
            "From": caller,
            "AccountSid": os.environ.get("TWILIO_ACCOUNT_SID", "ACtest000000000000000000000000000000")
        }
        
        url = f"{BASE_URL}/v1/providers/twilio/webhook"
        sign_url = url.replace("http://", "https://")
        signature = sign_twilio_request(sign_url, params)
        
        async with httpx.AsyncClient() as client:
            # We mock the X-Forwarded-Proto so the HTTPS middleware passes
            headers = {
                "X-Twilio-Signature": signature,
                "X-Forwarded-Proto": "https"
            }
            resp = await client.post(url, data=params, headers=headers)
            
        return resp, call_sid
    return _create

@pytest.mark.asyncio
async def test_invalid_twilio_webhook():
    """Scenario 12: Invalid Twilio webhook"""
    url = f"{BASE_URL}/v1/providers/twilio/webhook"
    params = {"CallSid": "123"}
    # Missing signature entirely
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=params, headers={"X-Forwarded-Proto": "https"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_valid_webhook_returns_twiml_with_auth(create_webhook_call):
    """Verifies that Twilio webhook returns proper TwiML with injected credentials."""
    resp, call_sid = await create_webhook_call()
    assert resp.status_code == 200
    assert "Connect" in resp.text
    assert "Stream" in resp.text
    assert "wss://" in resp.text or "ws://" in resp.text
    
    # Extract WSS URL from TwiML
    import re
    match = re.search(r'url="(wss?://[^"]+)"', resp.text)
    assert match is not None
    wss_url = match.group(1)
    
    # Must contain auth
    parsed = urlparse(wss_url)
    assert parsed.username is not None
    assert parsed.password is not None
    return wss_url, call_sid

@pytest.mark.asyncio
async def test_unauthorized_websocket_attempt():
    """Scenario 11: Unauthorized WebSocket attempt."""
    # Try connecting without auth
    ws_url = f"{WS_URL}/v1/streams/provider/twilio"
    try:
        async with websockets.connect(ws_url) as ws:
            await ws.recv()
            assert False, "Should have been rejected"
    except websockets.exceptions.InvalidStatus as e:
        assert e.response.status_code in [401, 403]
    except websockets.exceptions.ConnectionClosedError as e:
        assert e.code == 1008

@pytest.mark.asyncio
async def test_genuine_call_flow(create_webhook_call, authenticated_user):
    """Scenario 1: Normal genuine call & Scenario 14: Call termination."""
    # 1. Fire Webhook
    resp, call_sid = await create_webhook_call()
    import re
    match = re.search(r'url="(wss?://[^"]+)"', resp.text)
    wss_url = match.group(1)
    
    # Swap wss for ws for local testing, keep auth
    parsed = urlparse(wss_url)
    local_wss_url = f"ws://{parsed.username}:{parsed.password}@localhost:8001{parsed.path}"
    
    # 2. Connect Twilio Stream
    async with websockets.connect(local_wss_url) as ws:
        # Send start event
        start_event = {
            "event": "start",
            "start": {
                "streamSid": "MZ123",
                "callSid": call_sid,
                "customParameters": {
                    "user_id": str(authenticated_user["user_id"])
                }
            }
        }
        await ws.send(json.dumps(start_event))
        
        # Send 1 second of silence (Scenario 3 simulated briefly)
        # Mu-law 8kHz -> 8000 bytes per second
        mu_law_silence = b'\xff' * 8000
        media_event = {
            "event": "media",
            "streamSid": "MZ123",
            "media": {
                "payload": base64.b64encode(mu_law_silence).decode('ascii')
            }
        }
        await ws.send(json.dumps(media_event))
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Send Stop event
        stop_event = {
            "event": "stop",
            "streamSid": "MZ123"
        }
        try:
            await ws.send(json.dumps(stop_event))
            await ws.recv() # Wait for closure
        except websockets.exceptions.ConnectionClosedOK:
            pass

@pytest.mark.asyncio
async def test_user_websocket_auth(authenticated_user):
    """Tests the mobile WebSocket authentication."""
    token = authenticated_user["token"]
    
    # Create a dummy call first
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/v1/calls", 
            json={"caller_number": "+12223334444"},
            headers={"Authorization": f"Bearer {token}", "X-Forwarded-Proto": "https"}
        )
    assert resp.status_code == 200
    call_id = resp.json()["id"]
    
    # Connect
    ws_url = f"{WS_URL}/v1/calls/{call_id}/events?token={token}"
    
    async with websockets.connect(ws_url) as ws:
        # We connected successfully
        pass
        
    # Bad token
    bad_ws_url = f"{WS_URL}/v1/calls/{call_id}/events?token=badtoken"
    try:
        async with websockets.connect(bad_ws_url) as ws:
            await ws.recv()
            assert False, "Should reject bad token"
    except websockets.exceptions.InvalidStatus as e:
        assert e.response.status_code in [401, 403]
    except websockets.exceptions.ConnectionClosedError as e:
        assert e.code == 1008
