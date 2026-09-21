from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from typing import List
from datetime import datetime, timezone
import uuid
import asyncio
import json

from sqlalchemy.ext.asyncio import AsyncSession
from schemas.calls import CallCreate, CallResponse
from core.redis_client import subscribe_events, get_state
from core.database import get_db
from repositories.call_repository import CallRepository

router = APIRouter()
DUMMY_ORG_ID = "00000000-0000-0000-0000-000000000000"

@router.post("/v1/calls", response_model=CallResponse)
async def create_call(call: CallCreate, db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    started_at = datetime.now(timezone.utc)
    new_call = await repo.create_call_session(
        org_id=DUMMY_ORG_ID,
        provider_call_id=call.caller_number,
        started_at=started_at
    )
    await db.commit()
    
    return CallResponse(
        id=str(new_call.id),
        caller_number=new_call.provider_call_id,
        status="active",
        started_at=started_at
    )

@router.get("/v1/calls", response_model=List[CallResponse])
async def get_calls(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    calls = await repo.get_call_history(org_id=DUMMY_ORG_ID, limit=limit, offset=offset)
    
    return [
        CallResponse(
            id=str(c.id),
            caller_number=c.provider_call_id,
            status="ended" if c.ended_at else "active",
            started_at=c.started_at,
            ended_at=c.ended_at,
            max_risk_score=c.final_risk_score or 0.0
        ) for c in calls
    ]

@router.get("/v1/calls/{id}", response_model=CallResponse)
async def get_call(id: str, db: AsyncSession = Depends(get_db)):
    repo = CallRepository(db)
    # Note: id here is provider_call_id or internal UUID? Usually we use the DB UUID.
    # For now, we'll try fetching by DB UUID if possible. Wait, the frontend might be polling by provider ID.
    # We will just fetch by provider ID.
    call = await repo.get_call_by_provider_id(id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
        
    return CallResponse(
        id=str(call.id),
        caller_number=call.provider_call_id,
        status="ended" if call.ended_at else "active",
        started_at=call.started_at,
        ended_at=call.ended_at,
        max_risk_score=call.final_risk_score or 0.0
    )

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
