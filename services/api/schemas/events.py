from pydantic import BaseModel
from typing import Optional, Dict, Any

class Signals(BaseModel):
    antispoof: Optional[float] = None
    speaker_mismatch: Optional[float] = None
    signal_anomaly: Optional[float] = None

class RiskUpdateEvent(BaseModel):
    type: str = "risk.update"
    call_id: str
    timestamp_ms: int
    risk: float
    level: str
    confidence: float
    quality: str
    signals: Signals
