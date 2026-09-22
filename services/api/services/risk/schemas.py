from pydantic import BaseModel
from typing import List, Optional

class AntiSpoofSignal(BaseModel):
    status: str
    score: Optional[float] = None
    confidence: Optional[float] = None

class SpeakerVerificationSignal(BaseModel):
    available: bool
    similarity: Optional[float] = None

class AudioQualitySignal(BaseModel):
    status: str

class RiskSignals(BaseModel):
    antiSpoof: AntiSpoofSignal
    speakerVerification: SpeakerVerificationSignal
    audioQuality: AudioQualitySignal

class RiskEvidence(BaseModel):
    code: str
    severity: str

class RiskAssessment(BaseModel):
    riskScore: float
    riskLevel: str
    confidence: float
    signals: RiskSignals
    evidence: List[RiskEvidence]
