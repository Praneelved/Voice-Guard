from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from datetime import datetime
import uuid
import asyncio

from schemas.calls import CallCreate, CallResponse
from core.sessions import active_calls
from core.risk_engine import RiskSimulator

router = APIRouter()

active_simulators = {}

@router.post("/v1/calls", response_model=CallResponse)
def create_call(call: CallCreate):
    call_id = str(uuid.uuid4())
    new_call = CallResponse(
        id=call_id,
        caller_number=call.caller_number,
        status="active",
        started_at=datetime.utcnow()
    )
    active_calls[call_id] = new_call
    return new_call

@router.get("/v1/calls", response_model=List[CallResponse])
def get_calls():
    return list(active_calls.values())

@router.get("/v1/calls/{id}", response_model=CallResponse)
def get_call(id: str):
    if id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    return active_calls[id]

@router.get("/v1/calls/{id}/events")
def get_call_events(id: str):
    # Mocking past events for the call
    if id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    return {"events": []}

@router.websocket("/v1/calls/{call_id}/events")
async def websocket_call_events(websocket: WebSocket, call_id: str):
    await websocket.accept()
    
    simulator = RiskSimulator(call_id=call_id)
    active_simulators[call_id] = simulator
    
    task = asyncio.create_task(simulator.run(websocket.send_text))
    
    try:
        while True:
            # Keep connection open, wait for client to disconnect or send data
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        simulator.stop()
        task.cancel()
        del active_simulators[call_id]
