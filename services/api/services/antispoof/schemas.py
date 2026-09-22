from pydantic import BaseModel
from typing import Optional

class AntiSpoofResult(BaseModel):
    status: str
    spoof_probability: Optional[float] = None
    genuine_probability: Optional[float] = None
    confidence: Optional[float] = None
    model_name: str
    model_version: str
    audio_duration_ms: int
    quality_usable: bool
    inference_time_ms: float
