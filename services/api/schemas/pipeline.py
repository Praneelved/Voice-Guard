from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class PipelineEvent(BaseModel):
    """
    Standard event structure flowing through the Redis pub/sub.
    """
    session_id: str
    call_id: str
    timestamp: str  # ISO-8601 string
    event_type: str
    payload: dict

class CallSummary(BaseModel):
    """
    Final summary generated when a call session ends.
    """
    session_id: str
    call_id: str
    started_at: str
    ended_at: str
    max_risk_level: str
    total_audio_windows: int
    analyzed_windows: int
    provider: str
