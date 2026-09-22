import httpx
import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.domain import UserDevice
import asyncio

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

async def send_high_risk_alert(
    user_id: uuid.UUID, 
    call_id: str,
    session: AsyncSession
) -> bool:
    """
    Retrieves all enabled push tokens for the user and sends a High Risk alert.
    Returns True if at least one notification was attempted.
    """
    stmt = select(UserDevice).where(UserDevice.user_id == user_id, UserDevice.enabled == True)
    result = await session.execute(stmt)
    devices = result.scalars().all()

    if not devices:
        logger.info(f"No enabled push tokens found for user {user_id}")
        return False

    tokens = [device.push_token for device in devices]
    
    title = "VoiceGuard Security Alert"
    body = "Elevated voice authenticity risk detected on your active call. Verify the caller before taking sensitive action."
    
    data = {
        "call_id": call_id,
        "type": "high_risk_alert"
    }
    
    # We shouldn't block the caller (ingest stream) on this network request
    # Fire and forget
    asyncio.create_task(_send_expo_push_batch(tokens, title, body, data))
    
    return True

async def _send_expo_push_batch(tokens: list[str], title: str, body: str, data: Dict[str, Any]):
    messages = []
    for token in tokens:
        messages.append({
            "to": token,
            "title": title,
            "body": body,
            "data": data,
            "sound": "default",
            "priority": "high",
            "channelId": "default"
        })
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Successfully dispatched push notification to {len(tokens)} devices.")
    except Exception as e:
        logger.error(f"Failed to send Expo push notification: {e}")
