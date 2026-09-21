from pydantic import BaseModel

class RiskConfig(BaseModel):
    """
    Configuration profile for the VoiceGuard Risk Engine.
    NOTE: Initial values are prototypes and must be calibrated in production.
    """
    # Minimum valid speech required in a window to run analysis
    min_usable_speech_s: float = 0.5 
    
    # Exponential Moving Average smoothing factor. 
    # High alpha = reactive (trusts new data). Low alpha = smooth (trusts history).
    ema_alpha: float = 0.4 
    
    # Threshold boundaries (0.0 to 1.0 scale)
    caution_threshold: float = 0.40
    high_threshold: float = 0.70
    
    # Persistence required to trigger an actual alert state
    # e.g., 3 means 3 consecutive windows strictly >= high_threshold
    persistence_required_for_alert: int = 3
    
    # How much to trust the model if audio quality is 'poor'
    # We penalize/discount the spoof probability so bad audio doesn't cause false positives.
    poor_quality_discount: float = 0.7 
