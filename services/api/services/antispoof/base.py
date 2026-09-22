from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any
from .schemas import AntiSpoofResult

class AntiSpoofDetector(ABC):
    """
    Abstract interface for VoiceGuard anti-spoofing detection.
    """
    @abstractmethod
    async def analyze(self, audio: np.ndarray, sample_rate: int) -> AntiSpoofResult:
        """
        Takes an audio window and returns inference metrics asynchronously.
        """
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """
        Returns True if the model weights are successfully loaded into memory.
        """
        pass

    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        """
        Returns health status dictionary for the /health/ai route.
        """
        pass
