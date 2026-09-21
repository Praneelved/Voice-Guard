import soundfile as sf
import numpy as np

def decode_wav(file_path: str) -> tuple[np.ndarray, int]:
    """
    Decodes a WAV file into a NumPy array and returns the sample rate.
    """
    data, samplerate = sf.read(file_path)
    return data, samplerate
