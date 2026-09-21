from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, update
from typing import List, Optional
from uuid import UUID
import datetime
from models.domain import CallSession, RiskEvent, SignalScore

class CallRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_call_session(self, org_id: str, provider_call_id: str, started_at: datetime.datetime) -> CallSession:
        call = CallSession(
            org_id=UUID(org_id),
            provider_call_id=provider_call_id,
            started_at=started_at
        )
        self.session.add(call)
        await self.session.flush()
        return call
        
    async def get_call_by_provider_id(self, provider_call_id: str) -> Optional[CallSession]:
        stmt = select(CallSession).where(CallSession.provider_call_id == provider_call_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_call_history(self, org_id: str, limit: int = 20, offset: int = 0) -> List[CallSession]:
        stmt = (
            select(CallSession)
            .where(CallSession.org_id == UUID(org_id))
            .order_by(desc(CallSession.started_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_risk_event(self, call_id: UUID, timestamp: datetime.datetime, risk_level: str, risk_score: float, confidence: float):
        event = RiskEvent(
            call_id=call_id,
            timestamp=timestamp,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence
        )
        self.session.add(event)
        
    async def add_signal_score(self, call_id: UUID, timestamp: datetime.datetime, antispoof: float, quality: str, duration: float):
        score = SignalScore(
            call_id=call_id,
            timestamp=timestamp,
            antispoof_score=antispoof,
            audio_quality=quality,
            speech_duration=duration
        )
        self.session.add(score)
        
    async def finalize_call_session(self, call_id: UUID, ended_at: datetime.datetime, max_risk_level: str, final_score: float, total_windows: int, analyzed_windows: int):
        stmt = (
            update(CallSession)
            .where(CallSession.id == call_id)
            .values(
                ended_at=ended_at,
                max_risk_level=max_risk_level,
                final_risk_score=final_score,
                total_windows=total_windows,
                analyzed_windows=analyzed_windows
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
