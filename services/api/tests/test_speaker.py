import pytest
import numpy as np
from services.speaker.base import SpeakerVerifier
from services.speaker.schemas import VerificationResult
from services.speaker.verification import verify_speaker
from services.speaker.ecapa import ECAPATDNNVerifier

@pytest.fixture
def mock_ecapa():
    # Since we might not want to download the real ECAPA model in CI, we mock it.
    class MockECAPA(SpeakerVerifier):
        def __init__(self):
            self._loaded = True
            
        def extract_embedding(self, audio: np.ndarray) -> np.ndarray:
            return np.ones(192, dtype=np.float32)
            
        def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
            return 0.85
            
        def is_loaded(self) -> bool:
            return self._loaded
            
    return MockECAPA()

@pytest.mark.asyncio
async def test_verify_speaker_no_model(monkeypatch):
    import services.speaker.verification as verif_module
    
    class UnloadedModel(SpeakerVerifier):
        def is_loaded(self): return False
        def extract_embedding(self, audio): return np.array([])
        def compute_similarity(self, emb1, emb2): return 0.0
        
    monkeypatch.setattr(verif_module, "get_verifier", lambda: UnloadedModel())
    
    res = await verify_speaker(np.zeros(16000, dtype=np.float32), "some-id")
    assert res.match_state == "MODEL_UNAVAILABLE"
