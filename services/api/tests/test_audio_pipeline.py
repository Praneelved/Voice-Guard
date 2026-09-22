import numpy as np
import pytest
import base64
import audioop

from services.audio.decoder import decode_twilio_payload
from services.audio.resampler import normalize_and_resample
from services.audio.vad import SileroVAD
from services.audio.buffer import SpeechBuffer
from services.audio.quality import analyze_quality
from services.audio.preprocessing import AudioPreprocessor

def test_decoder_valid_payload():
    # Create fake PCM 16-bit
    pcm_data = np.zeros(160, dtype=np.int16)
    # Encode to mu-law
    mu_law = audioop.lin2ulaw(pcm_data.tobytes(), 2)
    b64_payload = base64.b64encode(mu_law).decode('utf-8')
    
    decoded = decode_twilio_payload(b64_payload)
    assert decoded.dtype == np.int16
    assert len(decoded) == 160

def test_decoder_empty_payload():
    decoded = decode_twilio_payload("")
    assert len(decoded) == 0

def test_resampler():
    # 8000Hz 16-bit PCM max amplitude sine wave
    t = np.linspace(0, 1, 8000)
    pcm = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    resampled = normalize_and_resample(pcm, orig_sr=8000, target_sr=16000)
    
    assert resampled.dtype == np.float32
    assert len(resampled) == 16000
    assert np.max(np.abs(resampled)) > 0.5

def test_quality_silence():
    silence = np.zeros(16000, dtype=np.float32)
    quality = analyze_quality(silence)
    assert quality["rms"] == 0.0
    assert quality["clipping_ratio"] == 0.0
    assert quality["usable"] == False
    assert quality["reason"] == "INSUFFICIENT_AUDIO_QUALITY"

def test_quality_clipping():
    # Signal with 10% clipping
    signal = np.zeros(16000, dtype=np.float32)
    signal[:1600] = 1.0
    quality = analyze_quality(signal)
    assert quality["clipping_ratio"] == 0.1
    assert quality["usable"] == False
    assert quality["reason"] == "INSUFFICIENT_AUDIO_QUALITY"

def test_quality_good_speech():
    # Sine wave (not clipping, high enough RMS)
    t = np.linspace(0, 1, 16000)
    signal = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    quality = analyze_quality(signal)
    assert quality["usable"] == True
    assert quality["reason"] is None

def test_buffer_accumulation_and_stride():
    buf = SpeechBuffer(window_seconds=4, stride_seconds=1, sample_rate=16000)
    
    # Push 3 seconds of audio
    w1 = buf.push_and_extract_windows(np.zeros(48000, dtype=np.float32))
    assert len(w1) == 0
    
    # Push 2 more seconds -> Total 5s. 
    # Buffer should yield 4s window, slide 1s, leaving 4s.
    # Wait, sliding 1s from 5s leaves 4s, which is another window!
    # Let's trace: 
    # Acc=5s. len >= 4s -> Window 1 [0:4s], slide 1s -> Acc=4s.
    # Acc=4s. len >= 4s -> Window 2 [1:5s], slide 1s -> Acc=3s.
    # Loop ends.
    w2 = buf.push_and_extract_windows(np.zeros(32000, dtype=np.float32))
    assert len(w2) == 2
    assert len(w2[0]) == 64000
    assert len(w2[1]) == 64000
    assert len(buf.accumulator) == 48000 # 3 seconds left

def test_vad_silence():
    vad = SileroVAD()
    silence = np.zeros(16000, dtype=np.float32)
    assert vad.process(silence) == False

def test_preprocessor_orchestration():
    windows_emitted = []
    def on_window(window, quality):
        windows_emitted.append((window, quality))
        
    pipeline = AudioPreprocessor(on_window_ready=on_window)
    
    # Send empty
    pipeline.process_twilio_payload("")
    assert len(windows_emitted) == 0
