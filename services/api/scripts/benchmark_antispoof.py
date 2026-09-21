import sys
import numpy as np
import soundfile as sf
import time
from services.antispoof import get_detector

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.benchmark_antispoof <path_to_wav>")
        sys.exit(1)
        
    wav_path = sys.argv[1]
    
    # Load audio
    print(f"Loading {wav_path}...")
    audio, sr = sf.read(wav_path)
    if sr != 16000:
        print("Error: audio must be 16kHz")
        sys.exit(1)
        
    # Create window
    if len(audio) < 48000:
        # pad
        audio = np.pad(audio, (0, 48000 - len(audio)))
        
    window = audio[:48000]
    
    # Int16 conversion if needed
    if window.dtype != np.int16:
        window = (window * 32767).astype(np.int16)
        
    print("Initializing detector...")
    detector = get_detector()
    
    print(f"Loaded model: {detector.model} v{detector.version}")
    
    # Warmup
    print("Warming up (5 iterations)...")
    for _ in range(5):
        detector.predict(window)
        
    n_iters = 100
    latencies = []
    
    print(f"Benchmarking {n_iters} iterations...")
    
    for i in range(n_iters):
        result = detector.predict(window)
        latencies.append(result["inference_ms"])
        
    latencies = np.array(latencies)
    
    print("\n--- BENCHMARK RESULTS ---")
    print(f"Window count: {n_iters}")
    print(f"Mean latency: {np.mean(latencies):.2f} ms")
    print(f"p50 latency:  {np.percentile(latencies, 50):.2f} ms")
    print(f"p95 latency:  {np.percentile(latencies, 95):.2f} ms")
    print(f"p99 latency:  {np.percentile(latencies, 99):.2f} ms")
    print("-------------------------")

if __name__ == "__main__":
    main()
