import os
import logging
import torch
import numpy as np
from .base import SpeakerVerifier
import asyncio

logger = logging.getLogger(__name__)

class ECAPATDNNVerifier(SpeakerVerifier):
    def __init__(self):
        self.device = self._resolve_device()
        self.model = None
        self._loaded = False
        self._load_model()

    def _resolve_device(self) -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def _load_model(self):
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            # SpeechBrain will download to ~/.cache/huggingface unless overridden
            savedir = os.environ.get("SPEECHBRAIN_CACHE_DIR", "tmp_ecapa_models")
            logger.info(f"Loading ECAPA-TDNN onto {self.device}...")
            
            # Using the standard SpeechBrain ECAPA-TDNN model
            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceceb", 
                savedir=savedir,
                run_opts={"device": str(self.device)}
            )
            self.model.eval()
            self._loaded = True
            logger.info("ECAPA-TDNN loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ECAPA-TDNN: {e}")
            self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    def extract_embedding(self, audio: np.ndarray) -> np.ndarray:
        if not self._loaded:
            raise RuntimeError("ECAPA-TDNN model is not loaded.")
            
        # SpeechBrain expects [batch_size, time] torch tensor
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            
        tensor = torch.from_numpy(audio).unsqueeze(0).to(self.device)
        
        with torch.inference_mode():
            # Output is [batch, 1, channels] -> squeeze to [channels]
            embeddings = self.model.encode_batch(tensor)
            emb = embeddings.squeeze().cpu().numpy()
            
        return emb

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm_a = np.linalg.norm(embedding1)
        norm_b = np.linalg.norm(embedding2)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))

# Singleton instance
_verifier_instance = None

def get_verifier() -> SpeakerVerifier:
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = ECAPATDNNVerifier()
    return _verifier_instance
