import numpy as np
from typing import TypedDict, Optional

class AudioQuality(TypedDict):
    usable: bool
    rms: float
    clipping_ratio: float
    voiced_ratio: float
    reason: Optional[str]

def calculate_rms(audio: np.ndarray) -> float:
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio))))

def calculate_clipping_ratio(audio: np.ndarray) -> float:
    if len(audio) == 0:
        return 0.0
    # Assuming float32 in range [-1.0, 1.0]
    # We consider anything >= 0.99 or <= -0.99 as clipped
    clipped_samples = np.sum(np.abs(audio) >= 0.99)
    return float(clipped_samples / len(audio))

def analyze_quality(audio: np.ndarray, voiced_ratio: float = 1.0) -> AudioQuality:
    """
    Evaluates the quality of a raw audio window to ensure it's suitable for inference.
    """
    rms = calculate_rms(audio)
    clipping = calculate_clipping_ratio(audio)
    
    # Heuristics for poor quality
    usable = True
    reason = None
    
    # Silence Check (Too quiet)
    if rms < 0.005: 
        usable = False
        reason = "INSUFFICIENT_AUDIO_QUALITY"
        
    # Clipping Check (Too loud/distorted)
    elif clipping > 0.05: 
        usable = False
        reason = "INSUFFICIENT_AUDIO_QUALITY"
        
    # Silence ratio / Unvoiced check
    elif voiced_ratio < 0.2:
        usable = False
        reason = "INSUFFICIENT_AUDIO_QUALITY"

    return {
        "usable": usable,
        "rms": rms,
        "clipping_ratio": clipping,
        "voiced_ratio": voiced_ratio,
        "reason": reason
    }
