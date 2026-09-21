from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from models.domain import Alert

class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_alert(self, org_id: str, call_id: str, alert_type: str, severity: str) -> Alert:
        alert = Alert(
            org_id=UUID(org_id),
            call_id=UUID(call_id),
            alert_type=alert_type,
            severity=severity
        )
        self.session.add(alert)
        await self.session.flush()
        return alert
        
    async def get_alerts_for_org(self, org_id: str, limit: int = 20, offset: int = 0) -> List[Alert]:
        stmt = (
            select(Alert)
            .where(Alert.org_id == UUID(org_id))
            .order_by(desc(Alert.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
