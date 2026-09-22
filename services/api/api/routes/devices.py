from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional
from core.database import get_db
from core.security import get_current_user
from models.domain import UserDevice

router = APIRouter(prefix="/v1/users", tags=["users"])

class DeviceRegistration(BaseModel):
    push_token: str
    platform: Optional[str] = None

@router.post("/devices")
async def register_device(
    registration: DeviceRegistration,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        # Check if device token already exists
        stmt = select(UserDevice).where(UserDevice.push_token == registration.push_token)
        result = await session.execute(stmt)
        existing_device = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        
        if existing_device:
            # Update existing
            existing_device.user_id = user_id # Handle token reassignment if user changes
            existing_device.platform = registration.platform
            existing_device.last_seen_at = now
            existing_device.enabled = True
        else:
            # Create new
            new_device = UserDevice(
                user_id=user_id,
                push_token=registration.push_token,
                platform=registration.platform,
                last_seen_at=now,
                enabled=True
            )
            session.add(new_device)
            
        await session.commit()
        
        return {"status": "success", "message": "Device registered successfully"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
