from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from datetime import datetime
import uuid
import asyncio

from schemas.calls import CallCreate, CallResponse
from core.sessions import active_calls
from core.redis_client import subscribe_events, get_state
import json

router = APIRouter()

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
    
    # Check if the call already ended
    summary = await get_state(f"summary:{call_id}")
    if summary:
        await websocket.send_text(json.dumps({
            "event_type": "call.ended",
            "payload": json.loads(summary)
        }))
        await websocket.close()
        return
        
    try:
        async for event in subscribe_events(call_id):
            await websocket.send_text(event)
            
            event_dict = json.loads(event)
            if event_dict.get("event_type") == "call.ended":
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Client disconnected or error: {e}")
    finally:
        from starlette.websockets import WebSocketState
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
