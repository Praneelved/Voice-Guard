import pytest
from fastapi.testclient import TestClient
from main import app

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

def test_get_models():
    response = client.get("/v1/models")
    assert response.status_code == 200
    assert "models" in response.json()

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
