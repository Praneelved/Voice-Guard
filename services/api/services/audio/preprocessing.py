import logging
import numpy as np
from typing import Callable, Optional

from .config import audio_config
from .decoder import decode_twilio_payload
from .resampler import normalize_and_resample
from .vad import SileroVAD
from .buffer import SpeechBuffer
from .quality import analyze_quality, AudioQuality

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """
    Orchestrates the conversion of incoming raw Twilio Base64 payloads 
    into fixed-size, AI-ready float32 tensors containing verified speech.
    """
    def __init__(self, on_window_ready: Callable[[np.ndarray, AudioQuality], None]):
        self.on_window_ready = on_window_ready
        
        self.vad = SileroVAD(sample_rate=audio_config.target_sample_rate)
        self.buffer = SpeechBuffer(
            window_seconds=audio_config.analysis_window_seconds,
            stride_seconds=audio_config.analysis_stride_seconds,
            sample_rate=audio_config.target_sample_rate
        )
        
    def process_twilio_payload(self, b64_payload: str):
        """
        Processes a single incoming Twilio payload.
        """
        # 1. Base64 & μ-law Decode
        pcm16_audio = decode_twilio_payload(b64_payload)
        
        if len(pcm16_audio) == 0:
            return
            
        # 2. Resample & Normalize to Float32
        # Twilio is inherently 8000Hz mono
        audio_float32 = normalize_and_resample(pcm16_audio, orig_sr=8000, target_sr=audio_config.target_sample_rate)
        
        if len(audio_float32) == 0:
            return
            
        # 3. Voice Activity Detection
        # Only push to buffer if it contains speech
        is_speech = self.vad.process(audio_float32)
        
        if is_speech:
            windows = self.buffer.push_and_extract_windows(audio_float32)
            
            # 4. Evaluate extracted windows
            for window in windows:
                self._process_window(window)
        else:
            # We skip pushing silence to the buffer.
            # Depending on use-case, you might want to push a little bit of padding,
            # but for anti-spoofing, pure speech is best.
            pass
            
    def _process_window(self, window_audio: np.ndarray):
        """
        Analyzes the quality of a complete speech window and emits it.
        """
        # Since we only buffered voiced frames, voiced_ratio is effectively 1.0.
        # But you could recalculate it precisely over the whole window if needed.
        quality = analyze_quality(window_audio, voiced_ratio=1.0)
        
        if not quality["usable"]:
            logger.warning(f"Audio window discarded due to poor quality: {quality['reason']}")
            
        # Always emit so the downstream risk engine knows a window was processed 
        # (it can handle INSUFFICIENT_AUDIO_QUALITY itself if we pass it down)
        self.on_window_ready(window_audio, quality)

    def clear(self):
        """Clears the internal buffers for a new call."""
        self.buffer.clear()
