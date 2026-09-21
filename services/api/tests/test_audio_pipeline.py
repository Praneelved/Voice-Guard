import numpy as np
import pytest
from services.audio_pipeline.quality import analyze_quality
from services.audio_pipeline.vad import VoiceActivityDetector
from services.audio_pipeline.windowing import WindowManager
from services.audio_pipeline.ring_buffer import AudioRingBuffer
from services.audio_pipeline.normalizer import normalize_audio

def test_quality_silence():
    # 1 second of silence
    silence = np.zeros(16000, dtype=np.int16)
    metrics = analyze_quality(silence)
    assert metrics["rms"] == 0.0
    assert metrics["clipping_ratio"] == 0.0
    assert metrics["quality"] == "poor"

def test_quality_clipping():
    # 1 second of clipping audio
    clipping = np.full(16000, 32767, dtype=np.int16)
    metrics = analyze_quality(clipping)
    assert metrics["clipping_ratio"] == 1.0
    assert metrics["quality"] == "poor"

def test_vad_detection():
    # It's hard to test VAD perfectly on raw sine waves, 
    # but we can test the function signatures and ratio logic.
    vad = VoiceActivityDetector()
    silence = np.zeros(16000, dtype=np.int16) # 1 sec
    metrics = vad.analyze_speech_ratio(silence)
    assert metrics["speech_ratio"] == 0.0
    assert metrics["usable_speech_duration_s"] == 0.0

def test_windowing_stride():
    wm = WindowManager(window_seconds=3.0, stride_seconds=1.0, sample_rate=16000)
    
    # Push 2 seconds, no window yet
    w1 = wm.push_and_extract_windows(np.zeros(32000, dtype=np.int16))
    assert len(w1) == 0
    
    # Push 1 more second, should get 1 window
    w2 = wm.push_and_extract_windows(np.zeros(16000, dtype=np.int16))
    assert len(w2) == 1
    assert len(w2[0]) == 48000
    
    # Push 2 more seconds, should get 2 windows
    w3 = wm.push_and_extract_windows(np.zeros(32000, dtype=np.int16))
    assert len(w3) == 2
    assert len(w3[0]) == 48000
    assert len(w3[1]) == 48000

def test_normalizer():
    # Fake stereo 44.1kHz float32
    audio = np.random.uniform(-1.0, 1.0, (44100, 2)).astype(np.float32)
    normalized = normalize_audio(audio, orig_sr=44100, target_sr=16000)
    
    assert normalized.dtype == np.int16
    assert len(normalized.shape) == 1
    assert len(normalized) == 16000
