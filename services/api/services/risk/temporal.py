import json
from typing import Optional, Dict, Any
from .thresholds import RiskConfig

class TemporalStateTracker:
    def __init__(self, config: Optional[RiskConfig] = None, state_dict: Optional[Dict[str, Any]] = None):
        self.config = config or RiskConfig()
        
        self.smoothed_antispoof = 0.0
        self.valid_window_count = 0
        self.speech_seconds_analyzed = 0.0
        self.high_risk_consecutive_windows = 0
        
        if state_dict:
            self.load_state(state_dict)

    def load_state(self, state_dict: Dict[str, Any]):
        self.smoothed_antispoof = state_dict.get("smoothed_antispoof", 0.0)
        self.valid_window_count = state_dict.get("valid_window_count", 0)
        self.speech_seconds_analyzed = state_dict.get("speech_seconds_analyzed", 0.0)
        self.high_risk_consecutive_windows = state_dict.get("high_risk_consecutive_windows", 0)

    def dump_state(self) -> Dict[str, Any]:
        return {
            "smoothed_antispoof": self.smoothed_antispoof,
            "valid_window_count": self.valid_window_count,
            "speech_seconds_analyzed": self.speech_seconds_analyzed,
            "high_risk_consecutive_windows": self.high_risk_consecutive_windows
        }

    def process_window(self, spoof_prob: Optional[float], window_duration_s: float):
        """
        Update the EMA and persistence tracking for anti-spoofing.
        Only called when audio is of usable quality.
        """
        if spoof_prob is None:
            return
            
        self.valid_window_count += 1
        self.speech_seconds_analyzed += window_duration_s
        
        if self.valid_window_count == 1:
            self.smoothed_antispoof = spoof_prob
        else:
            alpha = self.config.ema_alpha
            self.smoothed_antispoof = (alpha * spoof_prob) + ((1 - alpha) * self.smoothed_antispoof)
            
        if self.smoothed_antispoof >= self.config.high_risk_threshold:
            self.high_risk_consecutive_windows += 1
        else:
            self.high_risk_consecutive_windows = 0
