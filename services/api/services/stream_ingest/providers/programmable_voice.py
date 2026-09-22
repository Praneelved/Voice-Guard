import base64
import numpy as np
import librosa
from typing import Optional, Tuple
import logging

try:
    import audioop
except ImportError:
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
        self._expected_speaker_id = None
        self.custom_parameters = {}

    @property
    def call_id(self) -> Optional[str]:
        return self._call_id

    def set_expected_speaker(self, expected_speaker_id: Optional[str]):
        self._expected_speaker_id = expected_speaker_id

    def get_expected_speaker(self) -> Optional[str]:
        return self._expected_speaker_id

    def parse_message(self, message: dict) -> Tuple[Optional[str], Optional[str]]:
        event = message.get("event")
        
        if event == "start":
            start_data = message.get("start", {})
            self._call_id = start_data.get("callSid")
            self._stream_sid = start_data.get("streamSid")
            
            self.custom_parameters = start_data.get("customParameters", {})
            if "expected_speaker_id" in self.custom_parameters:
                self._expected_speaker_id = self.custom_parameters["expected_speaker_id"]
                
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
                
            # Yield the raw base64 payload; decoding is handled by the AudioPreprocessor
            return "media", payload
            
        elif event == "stop":
            logger.info(f"Twilio stream stopped. CallSid: {self._call_id}")
            return "stop", None
            
        else:
            return "ignore", None
