import torch
import numpy as np

class SileroVAD:
    def __init__(self, sample_rate: int = 16000, threshold: float = 0.5):
        self.sample_rate = sample_rate
        self.threshold = threshold
        # Load the Silero VAD model from Torch Hub
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True
        )
        self.get_speech_timestamps = utils[0]
        
    def process(self, audio_float32: np.ndarray) -> bool:
        """
        Determines if a chunk contains speech. 
        Chunk should be 16kHz float32.
        """
        if len(audio_float32) == 0:
            return False
            
        # Silero VAD requires torch tensor
        audio_tensor = torch.from_numpy(audio_float32)
        
        # It requires minimum of 512 samples. Pad if needed
        if len(audio_tensor) < 512:
            padding = 512 - len(audio_tensor)
            audio_tensor = torch.nn.functional.pad(audio_tensor, (0, padding))
            
        # Use provided utility to get timestamps
        timestamps = self.get_speech_timestamps(
            audio_tensor, 
            self.model, 
            sampling_rate=self.sample_rate,
            threshold=self.threshold
        )
        
        # If any timestamps are returned, there is speech
        return len(timestamps) > 0
