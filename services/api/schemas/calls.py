from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CallCreate(BaseModel):
    caller_number: str

class CallEvent(BaseModel):
    timestamp: datetime
    description: str
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None

class CallResponse(BaseModel):
    id: str
    caller_number: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    max_risk_score: float = 0.0
    final_risk_level: Optional[str] = None
    duration: Optional[int] = None
    analyzed_duration: Optional[int] = None
    timeline: Optional[List[CallEvent]] = None
