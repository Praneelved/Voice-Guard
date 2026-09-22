from pydantic_settings import BaseSettings, SettingsConfigDict

class AntiSpoofConfig(BaseSettings):
    antispoof_provider: str = "aasist"
    aasist_model_path: str = "./models/aasist_weights"
    calibration_temp: float = 1.0
    ai_device: str = "auto"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )
