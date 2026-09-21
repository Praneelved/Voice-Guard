import numpy as np
import soundfile as sf
import os

def generate_test_wav(filepath: str, duration: int = 10, sr: int = 16000):
    # 5 seconds tone (speech proxy)
    t1 = np.linspace(0, 5, 5 * sr, False)
    tone1 = np.sin(2 * np.pi * 440 * t1)
    
    # 2 seconds silence
    silence = np.zeros(2 * sr)
    
    # 3 seconds tone
    t2 = np.linspace(0, 3, 3 * sr, False)
    tone2 = np.sin(2 * np.pi * 880 * t2)
    
    # Combine
    audio = np.concatenate((tone1, silence, tone2))
    
    # Add some noise
    noise = np.random.normal(0, 0.01, len(audio))
    audio = audio + noise
    
    # Normalize and save
    audio = np.clip(audio, -1.0, 1.0)
    
    # Save as 16-bit PCM WAV
    sf.write(filepath, audio, sr, subtype='PCM_16')
    print(f"Generated test file: {filepath}")

if __name__ == "__main__":
    os.makedirs('tests/fixtures', exist_ok=True)
    generate_test_wav('tests/fixtures/test.wav')
