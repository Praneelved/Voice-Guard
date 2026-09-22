import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from core.database import get_db

from unittest.mock import patch, AsyncMock, MagicMock

def override_get_db():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_alert = MagicMock()
    mock_alert.status = "new"
    mock_result.scalar_one_or_none.return_value = mock_alert
    mock_db.execute.return_value = mock_result
    yield mock_db

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "voiceguard-api"}

def test_create_call():
    response = client.post("/v1/calls", json={"caller_number": "+15551234567"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["caller_number"] == "+15551234567"
    assert data["status"] == "active"



def test_start_verification():
    response = client.post("/v1/verification/test-call-123")
    assert response.status_code == 200
    data = response.json()
    assert data["call_id"] == "test-call-123"
    assert data["status"] == "started"

def test_acknowledge_alert():
    response = client.post("/v1/alerts/alert-123/ack")
    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"
