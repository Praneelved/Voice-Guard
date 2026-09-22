import numpy as np
import librosa

def normalize_and_resample(pcm16_audio: np.ndarray, orig_sr: int = 8000, target_sr: int = 16000) -> np.ndarray:
    """
    Converts PCM16 audio into AI-ready format:
    - float32
    - range approximately [-1.0, 1.0]
    - Mono
    - 16 kHz sample rate
    """
    if len(pcm16_audio) == 0:
        return np.array([], dtype=np.float32)

    # 1. Convert to mono if it happens to be stereo
    if len(pcm16_audio.shape) > 1 and pcm16_audio.shape[1] > 1:
        pcm16_audio = np.mean(pcm16_audio, axis=1)

    # 2. Convert to float32 and normalize
    # PCM16 bounds are -32768 to 32767
    audio_float32 = pcm16_audio.astype(np.float32) / 32768.0

    # 3. Resample if necessary
    if orig_sr != target_sr:
        audio_float32 = librosa.resample(audio_float32, orig_sr=orig_sr, target_sr=target_sr)

    return audio_float32
