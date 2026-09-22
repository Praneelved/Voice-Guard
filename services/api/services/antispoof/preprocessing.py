import numpy as np

def preprocess_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """
    Applies any necessary preprocessing to the audio tensor before AASIST inference.
    Assumes incoming audio is float32 [-1, 1].
    """
    if audio is None or len(audio) == 0:
        return audio
        
    # Ensure float32
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32) / 32768.0
        
    return audio
