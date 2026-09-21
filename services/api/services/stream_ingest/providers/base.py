from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np

class ProviderAdapter(ABC):
    """
    Base interface for all VoiceGuard stream ingestion adapters.
    Adapters are responsible for taking raw WebSocket JSON payloads,
    identifying the call, and converting the audio to canonical 16kHz PCM16 Mono.
    """

    @abstractmethod
    def parse_message(self, message: dict) -> Tuple[Optional[str], Optional[np.ndarray]]:
        """
        Parses a single WebSocket message from the provider.
        
        Returns:
            (event_type, audio_data)
            
            event_type: One of 'start', 'media', 'stop', 'error'
            audio_data: If 'media', a NumPy array of shape (N,) dtype=np.int16 at 16000Hz.
                        Else, None.
        """
        pass

    @property
    @abstractmethod
    def call_id(self) -> Optional[str]:
        """
        Returns the mapped VoiceGuard call ID (or provider call ID if direct mapping is used).
        Should return None if the 'start' event hasn't been parsed yet.
        """
        pass
