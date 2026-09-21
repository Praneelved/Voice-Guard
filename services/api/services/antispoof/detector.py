import time
import numpy as np
from abc import ABC, abstractmethod

class AntiSpoofDetector(ABC):
    """
    Abstract interface for VoiceGuard anti-spoofing detection.
    """
    @abstractmethod
    def predict(self, audio_window: np.ndarray, quality_metrics: dict = None) -> dict:
        """
        Takes a 16kHz PCM16 audio window and returns inference metrics.
        Returns:
        {
          "model": str,
          "model_version": str,
          "spoof_probability": float,
          "calibrated_probability": float,
          "window_quality": str,
          "inference_ms": float
        }
        """
        pass

class MockAntiSpoofDetector(AntiSpoofDetector):
    def __init__(self):
        self.model = "VoiceGuardMock"
        self.version = "1.0.0"

    def predict(self, audio_window: np.ndarray, quality_metrics: dict = None) -> dict:
        start = time.perf_counter()
        
        # Simulate processing delay
        time.sleep(0.01)
        
        # In a real scenario, probability approaches 1.0 for spoofed audio.
        # Here we just generate a random safe baseline (0.1 - 0.3) 
        # unless it's perfectly silent, in which case we return 0.5 (uncertain).
        
        is_silent = False
        if quality_metrics:
            is_silent = quality_metrics.get("speech_ratio", 1.0) == 0.0
            
        prob = 0.5 if is_silent else np.random.uniform(0.1, 0.3)
        
        inference_ms = (time.perf_counter() - start) * 1000
        
        return {
            "model": self.model,
            "model_version": self.version,
            "spoof_probability": prob,
            "calibrated_probability": min(1.0, prob * 1.05),
            "window_quality": quality_metrics.get("quality", "unknown") if quality_metrics else "unknown",
            "inference_ms": inference_ms
        }

class AASISTDetector(AntiSpoofDetector):
    def __init__(self):
        self.model = "AASIST"
        self.version = "lab260/spectra_aasist"
        
        try:
            import torch
            from transformers import AutoModel
            
            # Use MPS if on Apple Silicon, else CUDA, else CPU
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
                
            # Attempt to load the model from Hugging Face
            print(f"Loading {self.version} onto {self.device}...")
            self.model_instance = AutoModel.from_pretrained(self.version, trust_remote_code=True)
            self.model_instance.to(self.device)
            self.model_instance.eval()
            print("AASIST model loaded successfully.")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load AASIST model: {e}")

    def predict(self, audio_window: np.ndarray, quality_metrics: dict = None) -> dict:
        import torch
        start = time.perf_counter()
        
        # Convert PCM16 to float32 tensor
        # audio_window is shape (N,)
        audio_float = audio_window.astype(np.float32) / 32768.0
        
        # Add batch dimension: (1, N)
        tensor = torch.from_numpy(audio_float).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            # AASIST usually returns (embeddings, output)
            _, output = self.model_instance(tensor)
            
            # The output is typically log-softmax or logits over [bonafide, spoof] classes.
            # Assuming output[:, 1] represents the spoof logit/prob.
            if len(output.shape) == 2 and output.shape[1] == 2:
                probs = torch.softmax(output, dim=1)
                spoof_prob = probs[0, 1].item()
            else:
                # Fallback if architecture differs
                spoof_prob = 0.5
                
        inference_ms = (time.perf_counter() - start) * 1000
        
        return {
            "model": self.model,
            "model_version": self.version,
            "spoof_probability": spoof_prob,
            "calibrated_probability": spoof_prob,  # Replace with actual calibration if available
            "window_quality": quality_metrics.get("quality", "unknown") if quality_metrics else "unknown",
            "inference_ms": inference_ms
        }
