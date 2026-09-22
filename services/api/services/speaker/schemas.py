from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TrustedVoiceCreate(BaseModel):
    name: str
    label: Optional[str] = None
    
class TrustedVoiceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    label: Optional[str] = None
    samples_count: int
    created_at: datetime
    
class VerificationResult(BaseModel):
    expected_speaker: str
    similarity: float
    match_state: str  # e.g., LIKELY_MATCH, UNCERTAIN, NO_MATCH
    confidence: float
