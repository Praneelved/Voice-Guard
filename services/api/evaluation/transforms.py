import numpy as np
import audioop
import random

def apply_mu_law_encoding(audio_data: np.ndarray, sample_width=2) -> np.ndarray:
    """
    Simulates G.711 mu-law encoding/decoding degradation.
    """
    if len(audio_data) == 0:
        return audio_data
        
    # Scale to int16 range
    audio_int16 = (audio_data * 32767).astype(np.int16)
    raw_bytes = audio_int16.tobytes()
    
    # Encode to mu-law then back to linear
    mu_encoded = audioop.lin2ulaw(raw_bytes, sample_width)
    mu_decoded = audioop.ulaw2lin(mu_encoded, sample_width)
    
    # Back to float32
    decoded_int16 = np.frombuffer(mu_decoded, dtype=np.int16)
    return decoded_int16.astype(np.float32) / 32767.0

def apply_background_noise(audio_data: np.ndarray, snr_db=15) -> np.ndarray:
    """
    Adds Gaussian white noise at a specific Signal-to-Noise Ratio (SNR).
    """
    if len(audio_data) == 0:
        return audio_data
        
    signal_power = np.mean(audio_data ** 2)
    if signal_power == 0:
        return audio_data
        
    signal_power_db = 10 * np.log10(signal_power)
    noise_power_db = signal_power_db - snr_db
    noise_power = 10 ** (noise_power_db / 10)
    
    noise = np.random.normal(0, np.sqrt(noise_power), len(audio_data))
    noisy_signal = audio_data + noise
    
    # Clip to prevent overflow
    return np.clip(noisy_signal, -1.0, 1.0).astype(np.float32)

def apply_telephony_resampling(audio_data: np.ndarray, orig_sr=16000) -> np.ndarray:
    """
    Simulates downsampling to 8kHz (narrowband) and back up to 16kHz for the model.
    """
    # Simple naive decimation for 16k -> 8k -> 16k
    # We take every second sample, then duplicate it
    if len(audio_data) == 0 or orig_sr != 16000:
        return audio_data
        
    downsampled = audio_data[::2]
    upsampled = np.repeat(downsampled, 2)
    
    # If odd length, match original length
    if len(upsampled) < len(audio_data):
        upsampled = np.append(upsampled, upsampled[-1])
    elif len(upsampled) > len(audio_data):
        upsampled = upsampled[:len(audio_data)]
        
    return upsampled.astype(np.float32)

def apply_packet_loss(audio_data: np.ndarray, loss_prob=0.05, chunk_size=320) -> np.ndarray:
    """
    Simulates VoIP packet loss by zeroing out random chunks of audio.
    chunk_size 320 at 16kHz = 20ms packets.
    """
    if len(audio_data) == 0:
        return audio_data
        
    result = np.copy(audio_data)
    num_chunks = len(result) // chunk_size
    
    for i in range(num_chunks):
        if random.random() < loss_prob:
            start = i * chunk_size
            end = start + chunk_size
            result[start:end] = 0.0
            
    return result

def apply_low_volume(audio_data: np.ndarray, scale=0.3) -> np.ndarray:
    """
    Reduces volume to simulate distant speakers or poor mics.
    """
    return (audio_data * scale).astype(np.float32)

def simulate_telephony(audio_data: np.ndarray) -> np.ndarray:
    """
    Applies standard telephony degradations (8kHz + mu-law + minor packet loss).
    """
    audio = apply_telephony_resampling(audio_data)
    audio = apply_mu_law_encoding(audio)
    audio = apply_packet_loss(audio, loss_prob=0.02)
    return audio

def simulate_noisy_telephony(audio_data: np.ndarray) -> np.ndarray:
    """
    Applies telephony degradations + background noise.
    """
    audio = simulate_telephony(audio_data)
    audio = apply_background_noise(audio, snr_db=10)
    return audio
