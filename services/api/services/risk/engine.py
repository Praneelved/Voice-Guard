import time
from typing import Optional
from .temporal import TemporalStateTracker
from .thresholds import RiskConfig
from .schemas import (
    RiskAssessment, RiskSignals, AntiSpoofSignal, 
    SpeakerVerificationSignal, AudioQualitySignal, RiskEvidence
)
from .explanations import EVIDENCE_CODES
from core.metrics import RISK_ENGINE_LATENCY

class RiskFusionEngine:
    """
    Evaluates multiple raw signals deterministically to produce a final RiskAssessment.
    """
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    def evaluate(self, 
                 ai_status: str,
                 raw_spoof_prob: Optional[float],
                 quality_usable: bool,
                 speaker_similarity: Optional[float],
                 temporal_state: TemporalStateTracker) -> RiskAssessment:
        _t = time.perf_counter()
        evidence = []
        confidence = 1.0
        
        # 1. Quality Rules
        if not quality_usable:
            confidence = 0.5
            evidence.append(RiskEvidence(code="POOR_AUDIO_QUALITY", severity=EVIDENCE_CODES["POOR_AUDIO_QUALITY"]["severity"]))
            
        # 2. Speaker Verification Rules
        speaker_mismatch = False
        if speaker_similarity is not None:
            # If similarity is lower than threshold, it's a mismatch
            if speaker_similarity < 0.40: # Using 0.40 as boundary for mismatch based on previous rules
                speaker_mismatch = True
                evidence.append(RiskEvidence(code="EXPECTED_SPEAKER_MISMATCH", severity=EVIDENCE_CODES["EXPECTED_SPEAKER_MISMATCH"]["severity"]))
        
        # Missing speaker enrollment does NOT increase risk, so we do nothing if None
        
        # 3. Anti-Spoof Temporal Rules
        smoothed_score = temporal_state.smoothed_antispoof
        
        if temporal_state.high_risk_consecutive_windows >= self.config.high_risk_required_windows:
            evidence.append(RiskEvidence(code="PERSISTENT_ANTISPOOF_SIGNAL", severity=EVIDENCE_CODES["PERSISTENT_ANTISPOOF_SIGNAL"]["severity"]))
        elif raw_spoof_prob and raw_spoof_prob >= self.config.high_risk_threshold:
            evidence.append(RiskEvidence(code="TRANSIENT_ANTISPOOF_SPIKE", severity=EVIDENCE_CODES["TRANSIENT_ANTISPOOF_SPIKE"]["severity"]))

        # 4. Minimum Evidence
        if temporal_state.valid_window_count < self.config.min_valid_windows:
            evidence.append(RiskEvidence(code="INSUFFICIENT_EVIDENCE", severity=EVIDENCE_CODES["INSUFFICIENT_EVIDENCE"]["severity"]))
            
        if not evidence:
            evidence.append(RiskEvidence(code="NO_RISK_DETECTED", severity=EVIDENCE_CODES["NO_RISK_DETECTED"]["severity"]))

        # 5. Final Risk Calculation
        # Base risk is the smoothed antispoof
        final_risk_score = smoothed_score
        
        # Weighted rule: Speaker mismatch amplifies risk
        if speaker_mismatch:
            # Boost the risk score by 30% if they don't match, cap at 1.0
            final_risk_score = min(final_risk_score * 1.3, 1.0)
            
        # 6. Risk Level Assignment
        if temporal_state.valid_window_count < self.config.min_valid_windows:
            risk_level = "COLLECTING"
        elif "PERSISTENT_ANTISPOOF_SIGNAL" in [e.code for e in evidence]:
            risk_level = "HIGH"
        elif final_risk_score >= self.config.high_risk_threshold:
            # Catch cases where speaker mismatch boosted it above threshold
            risk_level = "HIGH"
        elif final_risk_score >= self.config.caution_threshold:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        result = RiskAssessment(
            riskScore=round(final_risk_score, 4),
            riskLevel=risk_level,
            confidence=round(confidence, 4),
            signals=RiskSignals(
                antiSpoof=AntiSpoofSignal(
                    status=ai_status,
                    score=round(smoothed_score, 4) if smoothed_score is not None else None,
                    confidence=confidence if raw_spoof_prob is not None else None
                ),
                speakerVerification=SpeakerVerificationSignal(
                    available=speaker_similarity is not None,
                    similarity=round(speaker_similarity, 4) if speaker_similarity is not None else None
                ),
                audioQuality=AudioQualitySignal(
                    status="GOOD" if quality_usable else "POOR"
                )
            ),
            evidence=evidence
        )
        RISK_ENGINE_LATENCY.observe(time.perf_counter() - _t)
        return result
