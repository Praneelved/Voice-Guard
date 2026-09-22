from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.alerts import AlertResponse
from core.database import get_db
from core.security import get_current_user
from repositories.alert_repository import AlertRepository
from typing import Dict, Any

router = APIRouter()

@router.get("/v1/alerts", response_model=List[AlertResponse])
async def get_alerts(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    repo = AlertRepository(db)
    alerts = await repo.get_alerts_for_org(org_id=current_user["id"], limit=limit, offset=offset)
    
    return [
        AlertResponse(
            id=str(a.id),
            call_id=str(a.call_id),
            severity=a.severity,
            timestamp=a.created_at,
            message=a.alert_type,
            acknowledged=(a.status == "resolved")
        ) for a in alerts
    ]

@router.post("/v1/alerts/{id}/ack")
async def acknowledge_alert(id: str, db: AsyncSession = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    from sqlalchemy.future import select
    from models.domain import Alert
    
    stmt = select(Alert).where(Alert.id == id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if alert and str(alert.org_id) == current_user["id"]:
        alert.status = "resolved"
        await db.commit()
        return {"status": "acknowledged", "alert_id": id}
        
    raise HTTPException(status_code=404, detail="Alert not found")
