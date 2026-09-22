import pytest
import os
import numpy as np
from services.antispoof.config import AntiSpoofConfig
from services.antispoof.aasist import AASISTDetector

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("AASIST_MODEL_PATH"), reason="AASIST_MODEL_PATH not configured")
async def test_aasist_detector_integration():
    config = AntiSpoofConfig()
    detector = AASISTDetector(config)
    
    # If the model path is provided but invalid, it might fail to load.
    if not detector.is_loaded():
        pytest.skip("AASIST model failed to load. Check AASIST_MODEL_PATH.")
        
    window = np.random.uniform(-1, 1, 48000).astype(np.float32)
    
    result = await detector.analyze(window, 16000)
    
    assert result.model_name == "AASIST"
    assert result.quality_usable is True
    assert 0.0 <= result.spoof_probability <= 1.0
    assert result.inference_time_ms > 0.0
    
    health = detector.get_health()
    assert health["status"] == "healthy"
    assert health["loaded"] is True
