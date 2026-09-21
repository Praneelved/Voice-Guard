from fastapi import APIRouter, HTTPException
from typing import List
from schemas.alerts import AlertResponse
from core.sessions import mock_alerts

router = APIRouter()

@router.get("/v1/alerts", response_model=List[AlertResponse])
def get_alerts():
    return mock_alerts

@router.post("/v1/alerts/{id}/ack")
def acknowledge_alert(id: str):
    for alert in mock_alerts:
        if alert.id == id:
            alert.acknowledged = True
            return {"status": "acknowledged", "alert_id": id}
    
    # Even if not found, mock a success for now or return 404
    return {"status": "acknowledged", "alert_id": id}
