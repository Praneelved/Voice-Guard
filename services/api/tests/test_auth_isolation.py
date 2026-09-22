import pytest
import jwt
import time
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from main import app
from core.security import JWT_SECRET

def generate_token(user_id: str, expired: bool = False, invalid: bool = False) -> str:
    if invalid:
        return "invalid.token.string"
    
    payload = {
        "sub": user_id,
        "email": f"{user_id}@example.com",
        "role": "authenticated",
        "exp": time.time() - 3600 if expired else time.time() + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@pytest.fixture
def user_a_token():
    return generate_token(str(uuid4()))

@pytest.fixture
def user_b_token():
    return generate_token(str(uuid4()))

@pytest.mark.asyncio
async def test_missing_token_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/calls")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_token_rejected():
    headers = {"Authorization": f"Bearer {generate_token(str(uuid4()), invalid=True)}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/calls", headers=headers)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_expired_token_rejected():
    headers = {"Authorization": f"Bearer {generate_token(str(uuid4()), expired=True)}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/calls", headers=headers)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_tenant_isolation_trusted_voices(user_a_token, user_b_token):
    headers_a = {"Authorization": f"Bearer {user_a_token}"}
    headers_b = {"Authorization": f"Bearer {user_b_token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User A creates a trusted voice
        create_payload = {"name": "Mom", "label": "family"}
        res_a = await ac.post("/v1/trusted-voices", json=create_payload, headers=headers_a)
        assert res_a.status_code == 200
        voice_id = res_a.json()["id"]
        
        # User A can retrieve it
        res_a_get = await ac.get("/v1/trusted-voices", headers=headers_a)
        assert any(v["id"] == voice_id for v in res_a_get.json())
        
        # User B CANNOT retrieve it
        res_b_get = await ac.get("/v1/trusted-voices", headers=headers_b)
        assert not any(v["id"] == voice_id for v in res_b_get.json())
        
        # User B CANNOT delete it
        res_b_delete = await ac.delete(f"/v1/trusted-voices/{voice_id}", headers=headers_b)
        assert res_b_delete.status_code == 404

@pytest.mark.asyncio
async def test_tenant_isolation_calls(user_a_token, user_b_token):
    headers_a = {"Authorization": f"Bearer {user_a_token}"}
    headers_b = {"Authorization": f"Bearer {user_b_token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User A creates a call
        create_payload = {"caller_number": "+15555555555"}
        res_a = await ac.post("/v1/calls", json=create_payload, headers=headers_a)
        assert res_a.status_code == 200
        call_id = res_a.json()["id"]
        
        # User A can retrieve it
        res_a_get = await ac.get("/v1/calls", headers=headers_a)
        assert any(c["id"] == call_id for c in res_a_get.json())
        
        # User B CANNOT retrieve it
        res_b_get = await ac.get("/v1/calls", headers=headers_b)
        assert not any(c["id"] == call_id for c in res_b_get.json())
        
        # User B CANNOT retrieve specific call
        res_b_get_one = await ac.get(f"/v1/calls/{call_id}", headers=headers_b)
        assert res_b_get_one.status_code == 404
