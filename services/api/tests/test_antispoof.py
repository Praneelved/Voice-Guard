import pytest
import numpy as np
from services.antispoof import AntiSpoofResult
from services.antispoof.mock import MockAntiSpoofDetector

@pytest.mark.asyncio
async def test_mock_detector():
    detector = MockAntiSpoofDetector()
    assert detector.is_loaded()
    
    # 3 second window of silence
    window = np.zeros(48000, dtype=np.float32)
    
    result = await detector.analyze(window, 16000)
    
    assert isinstance(result, AntiSpoofResult)
    assert result.model_name == "VoiceGuardMock"
    assert result.model_version == "1.0.0"
    
    # Check probabilities
    assert isinstance(result.spoof_probability, float)
    assert isinstance(result.genuine_probability, float)
    assert result.spoof_probability + result.genuine_probability == 1.0
    
    # Check mock logic fallback
    assert result.spoof_probability == 0.5
    assert result.quality_usable is False
    assert result.inference_time_ms >= 0.0

    health = detector.get_health()
    assert health["provider"] == "mock"
    assert health["status"] == "healthy"
