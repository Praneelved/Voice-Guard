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
from core.security import get_current_user
from repositories.call_repository import CallRepository
from models.domain import CallSession
from sqlalchemy.future import select
from typing import Dict, Any
from core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/v1/calls", response_model=CallResponse)
async def create_call(call: CallCreate, db: AsyncSession = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = CallRepository(db)
    started_at = datetime.now(timezone.utc)
    new_call = await repo.create_call_session(
        org_id=current_user["id"],
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
async def get_calls(
    limit: int = 20, 
    offset: int = 0, 
    risk_level: str = "ALL",
    db: AsyncSession = Depends(get_db), 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    repo = CallRepository(db)
    calls = await repo.get_call_history(org_id=current_user["id"], limit=limit, offset=offset, risk_level=risk_level)
    
    return [
        CallResponse(
            id=str(c.id),
            caller_number=c.provider_call_id,
            status="ended" if c.ended_at else "active",
            started_at=c.started_at,
            ended_at=c.ended_at,
            max_risk_score=c.final_risk_score or 0.0,
            final_risk_level=c.max_risk_level,
            duration=int((c.ended_at - c.started_at).total_seconds()) if c.ended_at else None,
            analyzed_duration=c.analyzed_windows * 4 if c.analyzed_windows else None
        ) for c in calls
    ]

@router.get("/v1/calls/{id}", response_model=CallResponse)
async def get_call(id: str, db: AsyncSession = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = CallRepository(db)
    call = await repo.get_call_by_provider_id(id)
    if not call or str(call.org_id) != current_user["id"]:
        # Try finding by UUID if provider id doesn't match
        from uuid import UUID
        try:
            call_stmt = select(CallSession).where(CallSession.id == UUID(id))
            call_res = await db.execute(call_stmt)
            call = call_res.scalar_one_or_none()
            if not call or str(call.org_id) != current_user["id"]:
                raise HTTPException(status_code=404, detail="Call not found")
        except ValueError:
            raise HTTPException(status_code=404, detail="Call not found")
            
    events = await repo.get_call_events(id)
        
    return CallResponse(
        id=str(call.id),
        caller_number=call.provider_call_id,
        status="ended" if call.ended_at else "active",
        started_at=call.started_at,
        ended_at=call.ended_at,
        max_risk_score=call.final_risk_score or 0.0,
        final_risk_level=call.max_risk_level,
        duration=int((call.ended_at - call.started_at).total_seconds()) if call.ended_at else None,
        analyzed_duration=call.analyzed_windows * 4 if call.analyzed_windows else None,
        timeline=events
    )

@router.websocket("/v1/calls/{call_id}/events")
async def websocket_call_events(websocket: WebSocket, call_id: str, token: str = None):
    # Authenticate via query param token
    if not token:
        await websocket.close(code=1008)
        return
        
    try:
        from core.security import JWT_SECRET
        import jwt
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return
        
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
        max_duration_seconds = 7200 # 2 hours
        session_start_time = asyncio.get_event_loop().time()
        
        async for event in subscribe_events(call_id):
            if asyncio.get_event_loop().time() - session_start_time > max_duration_seconds:
                break
                
            await websocket.send_text(event)
            
            try:
                event_dict = json.loads(event)
                if event_dict.get("event_type") == "call.ended":
                    break
            except Exception:
                pass
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"Client disconnected or error: {e}")
    finally:
        from starlette.websockets import WebSocketState
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
