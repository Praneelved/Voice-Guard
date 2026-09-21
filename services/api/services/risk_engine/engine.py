from typing import Optional, Dict, Any
import time

from schemas.events import Signals, RiskUpdateEvent
from .config import RiskConfig

class RiskState:
    STARTING = "STARTING"
    ANALYZING = "ANALYZING"
    LOW = "LOW"
    CAUTION = "CAUTION"
    HIGH = "HIGH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ANALYSIS_UNAVAILABLE = "ANALYSIS_UNAVAILABLE"

class RiskEngine:
    def __init__(self, call_id: str, config: Optional[RiskConfig] = None):
        self.call_id = call_id
        self.config = config or RiskConfig()
        
        self.current_state = RiskState.STARTING
        self.rolling_risk = 0.0
        self.high_risk_counter = 0
        self.has_first_valid_window = False

    def process_window(self, 
                       antispoof: Optional[float], 
                       audio_quality: str, 
                       usable_speech_s: float,
                       speaker_mismatch: Optional[float] = None,
                       signal_anomaly: Optional[float] = None) -> RiskUpdateEvent:
        """
        Process a single window of telemetry and update the state machine.
        """
        timestamp_ms = int(time.time() * 1000)
        confidence = 1.0
        
        # 1. Quality Gating
        if usable_speech_s < self.config.min_usable_speech_s:
            self.current_state = RiskState.INSUFFICIENT_EVIDENCE
            return self._build_event(timestamp_ms, self.rolling_risk, confidence, audio_quality, antispoof, speaker_mismatch, signal_anomaly)
            
        if antispoof is None:
            self.current_state = RiskState.ANALYSIS_UNAVAILABLE
            return self._build_event(timestamp_ms, self.rolling_risk, 0.0, audio_quality, antispoof, speaker_mismatch, signal_anomaly)
            
        # 2. Quality-Adjusted Score
        adjusted_score = antispoof
        if audio_quality == "poor":
            adjusted_score *= self.config.poor_quality_discount
            confidence = 0.5
            
        # 3. EMA Smoothing
        if not self.has_first_valid_window:
            self.rolling_risk = adjusted_score
            self.has_first_valid_window = True
        else:
            alpha = self.config.ema_alpha
            self.rolling_risk = (alpha * adjusted_score) + ((1 - alpha) * self.rolling_risk)
            
        # 4. Persistence Tracking & State Machine
        if self.rolling_risk >= self.config.high_threshold:
            self.high_risk_counter += 1
            # Require persistence to officially declare HIGH risk
            if self.high_risk_counter >= self.config.persistence_required_for_alert:
                self.current_state = RiskState.HIGH
            else:
                # Still evaluating the spike, stay in CAUTION temporarily
                self.current_state = RiskState.CAUTION
        elif self.rolling_risk >= self.config.caution_threshold:
            self.high_risk_counter = 0
            self.current_state = RiskState.CAUTION
        else:
            self.high_risk_counter = 0
            self.current_state = RiskState.LOW
            
        return self._build_event(timestamp_ms, self.rolling_risk, confidence, audio_quality, antispoof, speaker_mismatch, signal_anomaly)

    def _build_event(self, ts, risk, conf, qual, as_score, sm_score, sa_score) -> RiskUpdateEvent:
        signals = Signals(
            antispoof=as_score,
            speaker_mismatch=sm_score,
            signal_anomaly=sa_score
        )
        return RiskUpdateEvent(
            call_id=self.call_id,
            timestamp_ms=ts,
            risk=risk,
            level=self.current_state,
            confidence=conf,
            quality=qual,
            signals=signals
        )
