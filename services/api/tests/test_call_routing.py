import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid
from main import app
from core.database import async_session_maker
from models.domain import ProtectedNumber, Organization, User

@pytest.mark.asyncio
async def test_webhook_routing_flow():
    # Generate unique IDs for this test run
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    twilio_number_a = f"+1555{str(uuid.uuid4().int)[:7]}"
    twilio_number_b = f"+1555{str(uuid.uuid4().int)[:7]}"
    unregistered_number = "+15550000000"
    
    async with async_session_maker() as session:
        # Create Orgs
        org_a = Organization(id=user_a_id, name="User A Org")
        org_b = Organization(id=user_b_id, name="User B Org")
        session.add_all([org_a, org_b])
        
        # Create Users
        u_a = User(id=user_a_id, org_id=user_a_id, email=f"a_{user_a_id}@test.com", role="authenticated")
        u_b = User(id=user_b_id, org_id=user_b_id, email=f"b_{user_b_id}@test.com", role="authenticated")
        session.add_all([u_a, u_b])
        
        # Create Protected Numbers
        pn_a = ProtectedNumber(user_id=user_a_id, provider="twilio", provider_number=twilio_number_a)
        pn_b = ProtectedNumber(user_id=user_b_id, provider="twilio", provider_number=twilio_number_b)
        session.add_all([pn_a, pn_b])
        
        await session.commit()
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Routes to User A
        res_a = await ac.post("/v1/providers/twilio/webhook", data={"To": twilio_number_a})
        assert res_a.status_code == 200
        assert "Stream" in res_a.text
        assert f'<Parameter name="user_id" value="{user_a_id}"/>' in res_a.text
        assert "<Reject/>" not in res_a.text
        
        # 2. Routes to User B
        res_b = await ac.post("/v1/providers/twilio/webhook", data={"To": twilio_number_b})
        assert res_b.status_code == 200
        assert "Stream" in res_b.text
        assert f'<Parameter name="user_id" value="{user_b_id}"/>' in res_b.text
        assert "<Reject/>" not in res_b.text
        
        # 3. Rejects unregistered
        res_unreg = await ac.post("/v1/providers/twilio/webhook", data={"To": unregistered_number})
        assert res_unreg.status_code == 200
        assert "<Reject/>" in res_unreg.text
        assert "Stream" not in res_unreg.text
        
        # 4. Works with GET method
        res_get = await ac.get("/v1/providers/twilio/webhook", params={"To": twilio_number_a})
        assert res_get.status_code == 200
        assert f'<Parameter name="user_id" value="{user_a_id}"/>' in res_get.text
