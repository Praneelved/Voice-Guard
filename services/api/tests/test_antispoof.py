import numpy as np
from services.antispoof import get_detector

def test_mock_detector():
    detector = get_detector()
    # It should fallback to mock in our test env if weights missing, 
    # but the interface should be identical either way.
    
    # 3 second window of silence
    window = np.zeros(48000, dtype=np.int16)
    
    metrics = {"speech_ratio": 0.0, "quality": "poor"}
    
    result = detector.predict(window, metrics)
    
    assert "model" in result
    assert "model_version" in result
    assert "spoof_probability" in result
    assert "calibrated_probability" in result
    assert "window_quality" in result
    assert "inference_ms" in result
    
    assert isinstance(result["spoof_probability"], float)
    assert isinstance(result["inference_ms"], float)
    
    if result["model"] == "VoiceGuardMock":
        assert result["spoof_probability"] == 0.5 # Silence fallback logic in mock
