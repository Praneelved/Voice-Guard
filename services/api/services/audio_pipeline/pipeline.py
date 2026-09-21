import numpy as np
from typing import Callable
from .decoder import decode_wav
from .normalizer import normalize_audio
from .quality import analyze_quality
from .vad import VoiceActivityDetector
from .windowing import WindowManager

class AudioPipeline:
    def __init__(self, on_window_ready: Callable[[np.ndarray, dict], None]):
        self.vad = VoiceActivityDetector(sample_rate=16000, aggressiveness=3)
        self.window_manager = WindowManager(window_seconds=3.0, stride_seconds=1.0, sample_rate=16000)
        self.on_window_ready = on_window_ready

    def process_wav_file(self, file_path: str):
        """
        Simulates an incoming stream by reading a whole WAV file, 
        normalizing it, and streaming it chunk by chunk into the window manager.
        """
        # 1. Decode
        raw_audio, sr = decode_wav(file_path)
        
        # 2. Normalize to 16kHz Mono PCM16
        normalized_audio = normalize_audio(raw_audio, orig_sr=sr, target_sr=16000)
        
        # We can simulate streaming by pushing in 1-second chunks
        chunk_size = 16000 # 1 second
        
        for i in range(0, len(normalized_audio), chunk_size):
            chunk = normalized_audio[i:i+chunk_size]
            self.push_chunk(chunk)
            
    def push_chunk(self, audio_chunk: np.ndarray):
        """
        Pushes a new raw chunk of PCM16 audio (must be 16kHz mono) into the pipeline.
        """
        # 3. Push to window manager
        windows = self.window_manager.push_and_extract_windows(audio_chunk)
        
        # 4. Process any generated windows
        for window in windows:
            self._process_window(window)
            
    def _process_window(self, window_audio: np.ndarray):
        # 5. Calculate Quality Metrics
        quality_metrics = analyze_quality(window_audio)
        
        # 6. Calculate VAD / Speech Ratio
        vad_metrics = self.vad.analyze_speech_ratio(window_audio)
        
        # Combine metrics
        metrics = {
            **quality_metrics,
            **vad_metrics
        }
        
        # 7. Emit audio.window.ready
        self.on_window_ready(window_audio, metrics)
