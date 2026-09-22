import time
import numpy as np
from typing import Dict, Any
from .base import AntiSpoofDetector
from .schemas import AntiSpoofResult

class MockAntiSpoofDetector(AntiSpoofDetector):
    def __init__(self):
        self.model_name = "VoiceGuardMock"
        self.version = "1.0.0"
        self._loaded = True

    async def analyze(self, audio: np.ndarray, sample_rate: int) -> AntiSpoofResult:
        start = time.perf_counter()
        
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(0.01)
        
        # Simulate probability (0.1 - 0.3 for a safe baseline)
        is_silent = len(audio) == 0 or np.all(audio == 0)
        spoof_prob = 0.5 if is_silent else np.random.uniform(0.1, 0.3)
        
        inference_ms = (time.perf_counter() - start) * 1000
        duration_ms = int(len(audio) / sample_rate * 1000) if sample_rate > 0 else 0
        
        return AntiSpoofResult(
            status="OK",
            spoof_probability=spoof_prob,
            genuine_probability=1.0 - spoof_prob,
            confidence=0.5 if is_silent else 1.0,
            model_name=self.model_name,
            model_version=self.version,
            audio_duration_ms=duration_ms,
            quality_usable=not is_silent,
            inference_time_ms=inference_ms
        )

    def is_loaded(self) -> bool:
        return self._loaded

    def get_health(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "loaded": self._loaded,
            "device": "cpu",
            "model": self.model_name,
            "version": self.version,
            "status": "healthy"
        }
