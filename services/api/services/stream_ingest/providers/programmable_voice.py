import base64
import numpy as np
import librosa
from typing import Optional, Tuple
import logging

try:
    import audioop
except ImportError:
    # Fallback to audioop-lts on Python 3.13+
    pass

from .base import ProviderAdapter

logger = logging.getLogger(__name__)

class TwilioProgrammableVoiceAdapter(ProviderAdapter):
    """
    Adapter for Twilio Media Streams.
    Twilio streams audio as base64 encoded G.711 mu-law at 8000 Hz.
    """
    def __init__(self):
        self._call_id = None
        self._stream_sid = None
        self._track = "inbound" # We typically only care about what the caller says

    @property
    def call_id(self) -> Optional[str]:
        return self._call_id

    def parse_message(self, message: dict) -> Tuple[Optional[str], Optional[np.ndarray]]:
        event = message.get("event")
        
        if event == "start":
            start_data = message.get("start", {})
            self._call_id = start_data.get("callSid")
            self._stream_sid = start_data.get("streamSid")
            logger.info(f"Twilio stream started. CallSid: {self._call_id}, StreamSid: {self._stream_sid}")
            return "start", None
            
        elif event == "media":
            media_data = message.get("media", {})
            track = media_data.get("track")
            
            # Twilio sends inbound (caller) and outbound (our AI/IVR). 
            # We only analyze the caller.
            if track != self._track:
                return "ignore", None
                
            payload = media_data.get("payload")
            if not payload:
                return "ignore", None
                
            # 1. Base64 Decode
            raw_bytes = base64.b64decode(payload)
            
            # 2. Decode G.711 mu-law to 16-bit linear PCM
            pcm_bytes = audioop.ulaw2lin(raw_bytes, 2)
            
            # 3. Convert to NumPy array
            pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)
            
            # 4. Upsample 8000Hz to 16000Hz
            # Librosa expects float32 in range [-1.0, 1.0]
            float_array = pcm_array.astype(np.float32) / 32768.0
            resampled_float = librosa.resample(float_array, orig_sr=8000, target_sr=16000)
            
            # Convert back to Int16
            canonical_pcm16 = (resampled_float * 32767).astype(np.int16)
            
            return "media", canonical_pcm16
            
        elif event == "stop":
            logger.info(f"Twilio stream stopped. CallSid: {self._call_id}")
            return "stop", None
            
        else:
            return "ignore", None
