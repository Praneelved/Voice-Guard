import os
from pydantic_settings import BaseSettings

class AudioConfig(BaseSettings):
    analysis_window_seconds: int = 4
    analysis_stride_seconds: int = 1
    
    # Internal configuration
    target_sample_rate: int = 16000
    
    class Config:
        env_prefix = "AUDIO_"

audio_config = AudioConfig()
