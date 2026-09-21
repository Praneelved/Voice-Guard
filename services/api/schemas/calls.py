from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CallCreate(BaseModel):
    caller_number: str

class CallResponse(BaseModel):
    id: str
    caller_number: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    max_risk_score: float = 0.0
