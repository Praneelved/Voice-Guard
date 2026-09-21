import numpy as np
import librosa

def normalize_audio(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """
    Normalizes the audio stream to:
    - Mono
    - 16 kHz sample rate
    - Signed 16-bit PCM (int16)
    """
    # Convert to mono if stereo
    if len(audio.shape) > 1 and audio.shape[1] > 1:
        audio = np.mean(audio, axis=1)

    # Convert to float32 for librosa processing if not already float
    if audio.dtype != np.float32 and audio.dtype != np.float64:
        audio = audio.astype(np.float32)
        # If it was int16, normalize to -1.0 to 1.0
        if np.max(np.abs(audio)) > 1.0:
            audio = audio / 32768.0

    # Resample if needed
    if orig_sr != target_sr:
        audio = librosa.resample(y=audio, orig_sr=orig_sr, target_sr=target_sr)

    # Convert back to signed int16 (PCM16)
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    return audio_int16
