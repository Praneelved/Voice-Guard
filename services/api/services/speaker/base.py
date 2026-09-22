from abc import ABC, abstractmethod
import numpy as np

class SpeakerVerifier(ABC):
    """
    Abstract interface for extracting embeddings and computing similarity.
    """
    @abstractmethod
    def extract_embedding(self, audio: np.ndarray) -> np.ndarray:
        """
        Takes 16kHz float32 audio and returns a speaker embedding vector.
        """
        pass
        
    @abstractmethod
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Computes cosine similarity between two embeddings.
        Returns a float between -1.0 and 1.0 (typically 0 to 1 for normalized vectors).
        """
        pass
        
    @abstractmethod
    def is_loaded(self) -> bool:
        """Returns True if the verification model is loaded."""
        pass
