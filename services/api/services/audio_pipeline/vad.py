import webrtcvad
import numpy as np

class VoiceActivityDetector:
    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 3):
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(aggressiveness)
        # WebRTC VAD requires 10, 20, or 30 ms frames
        self.frame_duration_ms = 30 
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)

    def process_frames(self, audio_int16: np.ndarray) -> list[bool]:
        """
        Takes an arbitrary length of audio and splits it into 30ms frames,
        evaluating VAD on each full frame.
        """
        results = []
        for i in range(0, len(audio_int16) - self.frame_size + 1, self.frame_size):
            frame = audio_int16[i:i + self.frame_size]
            # webrtcvad expects raw bytes
            is_speech = self.vad.is_speech(frame.tobytes(), self.sample_rate)
            results.append(is_speech)
        return results

    def analyze_speech_ratio(self, audio_int16: np.ndarray) -> dict:
        """
        Returns the percentage of frames that contain speech, and usable duration.
        """
        speech_frames = self.process_frames(audio_int16)
        
        if not speech_frames:
            return {"speech_ratio": 0.0, "usable_speech_duration_s": 0.0}
            
        speech_count = sum(speech_frames)
        ratio = speech_count / len(speech_frames)
        usable_duration = speech_count * (self.frame_duration_ms / 1000.0)
        
        return {
            "speech_ratio": ratio,
            "usable_speech_duration_s": usable_duration
        }
