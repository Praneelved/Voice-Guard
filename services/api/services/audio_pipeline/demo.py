import sys
import numpy as np
from .pipeline import AudioPipeline

def on_window_ready(audio: np.ndarray, metrics: dict):
    print("--------------------------------------------------")
    print(f"EVENT: audio.window.ready")
    print(f"Window Size: {len(audio)} samples ({len(audio)/16000:.2f}s)")
    print(f"Metrics:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    print("--------------------------------------------------\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m services.audio_pipeline.demo <path_to_wav>")
        sys.exit(1)
        
    wav_path = sys.argv[1]
    
    print(f"Starting VoiceGuard Audio Pipeline Demo for: {wav_path}")
    print("Target Contract: Mono, 16kHz, PCM16")
    print("Window: 3.0s | Stride: 1.0s\n")
    
    pipeline = AudioPipeline(on_window_ready=on_window_ready)
    
    try:
        pipeline.process_wav_file(wav_path)
    except Exception as e:
        print(f"Error processing file: {e}")
        
    print("Pipeline finished.")

if __name__ == "__main__":
    main()
