from pydantic_settings import BaseSettings, SettingsConfigDict

class RiskConfig(BaseSettings):
    """
    Configuration profile for the VoiceGuard Risk Engine.
    """
    # Minimum valid speech required in a window to run analysis
    min_usable_speech_s: float = 0.5 
    
    # Exponential Moving Average smoothing factor. 
    # High alpha = reactive (trusts new data). Low alpha = smooth (trusts history).
    ema_alpha: float = 0.4 
    
    # Threshold boundaries (0.0 to 1.0 scale)
    caution_threshold: float = 0.40
    high_risk_threshold: float = 0.75
    high_risk_exit_threshold: float = 0.60
    
    # Minimum number of valid windows before leaving COLLECTING_EVIDENCE
    min_valid_windows: int = 3
    
    # Persistence required to trigger HIGH state
    high_risk_required_windows: int = 3
    
    # How much to trust the model if audio quality is 'poor'
    poor_quality_discount: float = 0.7 
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
