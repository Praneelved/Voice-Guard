import pytest
from services.risk_engine import RiskEngine, RiskState, RiskConfig

def test_low_risk_baseline():
    engine = RiskEngine(call_id="123")
    
    # 3 normal windows
    for _ in range(3):
        evt = engine.process_window(antispoof=0.1, audio_quality="good", usable_speech_s=3.0)
        assert evt.level == RiskState.LOW
        assert evt.risk < 0.4
        
def test_short_spike_no_alert():
    engine = RiskEngine(call_id="123")
    
    # Baseline
    engine.process_window(antispoof=0.1, audio_quality="good", usable_speech_s=3.0)
    
    # Spike - extreme spoof probability
    evt = engine.process_window(antispoof=0.9, audio_quality="good", usable_speech_s=3.0)
    
    # It might breach the HIGH threshold, but due to persistence it should only be CAUTION.
    # Note: If EMA smooths it enough, it might just be CAUTION anyway.
    assert evt.level == RiskState.CAUTION
    assert engine.high_risk_counter == 0 # Because of EMA, it never breaches 0.70 in 1 tick
    
def test_persistent_high_risk():
    engine = RiskEngine(call_id="123")
    
    # 4 windows of absolute high risk
    states = []
    for _ in range(4):
        evt = engine.process_window(antispoof=0.9, audio_quality="good", usable_speech_s=3.0)
        states.append(evt.level)
        
    # By the 3rd or 4th window, it must be HIGH
    assert RiskState.HIGH in states
    assert engine.high_risk_counter >= 3
    
def test_bad_audio_discounting():
    engine = RiskEngine(call_id="123")
    
    # The config discounts poor audio.
    # 0.8 raw score with poor audio will be discounted to 0.8 * 0.7 = 0.56
    # 0.56 is above caution (0.4) but below high (0.7)
    evt = engine.process_window(antispoof=0.8, audio_quality="poor", usable_speech_s=3.0)
    
    assert evt.confidence == 0.5
    assert evt.risk == pytest.approx(0.56)
    assert evt.level == RiskState.CAUTION

def test_insufficient_speech():
    engine = RiskEngine(call_id="123")
    evt = engine.process_window(antispoof=0.5, audio_quality="good", usable_speech_s=0.2)
    assert evt.level == RiskState.INSUFFICIENT_EVIDENCE
    
def test_missing_ai_result():
    engine = RiskEngine(call_id="123")
    evt = engine.process_window(antispoof=None, audio_quality="good", usable_speech_s=3.0)
    assert evt.level == RiskState.ANALYSIS_UNAVAILABLE
    
def test_recovery():
    engine = RiskEngine(call_id="123")
    
    # Get to HIGH
    for _ in range(3):
        engine.process_window(antispoof=0.9, audio_quality="good", usable_speech_s=3.0)
        
    assert engine.current_state == RiskState.HIGH
    assert engine.high_risk_counter >= 3
    
    # Drop back to safe
    for _ in range(4):
        engine.process_window(antispoof=0.1, audio_quality="good", usable_speech_s=3.0)
        
    assert engine.current_state == RiskState.LOW
    assert engine.high_risk_counter == 0
