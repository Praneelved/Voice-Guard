import pytest
from services.risk import RiskFusionEngine, TemporalStateTracker, RiskConfig

@pytest.fixture
def config():
    return RiskConfig(min_valid_windows=2, high_risk_threshold=0.75, ema_alpha=0.4)

def test_insufficient_evidence(config):
    engine = RiskFusionEngine(config=config)
    tracker = TemporalStateTracker(config=config)
    
    # Only 1 window processed (min is 2)
    tracker.process_window(0.8, 4.0)
    
    res = engine.evaluate("OK", 0.8, True, None, tracker)
    assert res.riskLevel == "COLLECTING"
    assert "INSUFFICIENT_EVIDENCE" in [e.code for e in res.evidence]

def test_missing_speaker_does_not_inflate_risk(config):
    engine = RiskFusionEngine(config=config)
    tracker = TemporalStateTracker(config=config)
    
    # Process 2 windows
    tracker.process_window(0.1, 4.0)
    tracker.process_window(0.1, 4.0)
    
    # Speaker is missing (None)
    res = engine.evaluate("OK", 0.1, True, None, tracker)
    assert res.riskLevel == "LOW"
    assert res.riskScore < 0.4
    assert res.signals.speakerVerification.available is False

def test_speaker_mismatch_inflates_risk(config):
    engine = RiskFusionEngine(config=config)
    tracker = TemporalStateTracker(config=config)
    
    tracker.process_window(0.60, 4.0)
    tracker.process_window(0.60, 4.0) # Smoothed anti-spoof will be around 0.60
    
    # Without mismatch
    res1 = engine.evaluate("OK", 0.60, True, 0.80, tracker)
    
    # With mismatch
    res2 = engine.evaluate("OK", 0.60, True, 0.20, tracker)
    
    assert res2.riskScore > res1.riskScore
    assert "EXPECTED_SPEAKER_MISMATCH" in [e.code for e in res2.evidence]
    # In our engine logic, if it gets boosted over 0.75 it might become HIGH.
    assert res2.riskLevel in ["MEDIUM", "HIGH"]

def test_poor_audio_drops_confidence(config):
    engine = RiskFusionEngine(config=config)
    tracker = TemporalStateTracker(config=config)
    
    tracker.process_window(0.5, 4.0)
    tracker.process_window(0.5, 4.0)
    
    res = engine.evaluate("LOW_AUDIO_QUALITY", 0.5, False, None, tracker)
    assert res.confidence == 0.5
    assert "POOR_AUDIO_QUALITY" in [e.code for e in res.evidence]

def test_persistent_antispoof(config):
    engine = RiskFusionEngine(config=config)
    tracker = TemporalStateTracker(config=config)
    
    # Push 3 high risk windows
    for _ in range(3):
        tracker.process_window(0.9, 4.0)
        
    res = engine.evaluate("OK", 0.9, True, None, tracker)
    assert res.riskLevel == "HIGH"
    assert "PERSISTENT_ANTISPOOF_SIGNAL" in [e.code for e in res.evidence]
    
def test_transient_spike(config):
    engine = RiskFusionEngine(config=config)
    tracker = TemporalStateTracker(config=config)
    
    # Baseline low
    tracker.process_window(0.1, 4.0)
    tracker.process_window(0.1, 4.0)
    
    # Single spike
    tracker.process_window(0.9, 4.0)
    
    # Smoothed score will be pulled up by EMA but shouldn't hit 0.75 persistently yet.
    res = engine.evaluate("OK", 0.9, True, None, tracker)
    # The transient spike is logged in evidence
    assert "TRANSIENT_ANTISPOOF_SPIKE" in [e.code for e in res.evidence]
    assert "PERSISTENT_ANTISPOOF_SIGNAL" not in [e.code for e in res.evidence]
    
