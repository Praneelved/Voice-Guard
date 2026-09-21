import numpy as np

def calculate_rms(audio_int16: np.ndarray) -> float:
    """
    Calculates the Root Mean Square (RMS) energy of the audio.
    """
    if len(audio_int16) == 0:
        return 0.0
    
    # Convert to float for calculation to avoid overflow
    audio_float = audio_int16.astype(np.float32)
    rms = np.sqrt(np.mean(np.square(audio_float)))
    return float(rms)

def calculate_clipping_ratio(audio_int16: np.ndarray) -> float:
    """
    Calculates the percentage of samples that hit the max/min boundaries of int16.
    """
    if len(audio_int16) == 0:
        return 0.0
        
    clipped_samples = np.sum((audio_int16 == 32767) | (audio_int16 == -32768))
    return float(clipped_samples / len(audio_int16))

def analyze_quality(audio_int16: np.ndarray) -> dict:
    return {
        "rms": calculate_rms(audio_int16),
        "clipping_ratio": calculate_clipping_ratio(audio_int16),
        "quality": "poor" if calculate_clipping_ratio(audio_int16) > 0.05 or calculate_rms(audio_int16) < 100 else "good"
    }
