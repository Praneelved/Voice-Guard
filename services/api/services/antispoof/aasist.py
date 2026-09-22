import time
import asyncio
import logging
import numpy as np
from typing import Dict, Any
import torch

from .base import AntiSpoofDetector
from .schemas import AntiSpoofResult
from .preprocessing import preprocess_audio
from .calibration import calibrate_probability
from .config import AntiSpoofConfig
from core.metrics import ANTISPOOF_LATENCY, MODEL_ERRORS

logger = logging.getLogger(__name__)

class AASISTDetector(AntiSpoofDetector):
    def __init__(self, config: AntiSpoofConfig):
        self.config = config
        self.model_name = "AASIST"
        self.version = "unknown"
        self._loaded = False
        self.device = self._resolve_device(config.ai_device)
        self.model_instance = None
        
        self._load_model()

    def _resolve_device(self, device_str: str) -> torch.device:
        if device_str == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            else:
                return torch.device("cpu")
        return torch.device(device_str)

    def _load_model(self):
        model_path = self.config.aasist_model_path
        if not model_path:
            logger.error("AASIST_MODEL_PATH is not set. AASIST inference will be unavailable.")
            return

        try:
            from transformers import AutoModel
            logger.info(f"Loading AASIST model from local path '{model_path}' onto {self.device}...")
            # Enforce local_files_only to prevent silent internet downloads
            self.model_instance = AutoModel.from_pretrained(
                model_path, 
                trust_remote_code=True, 
                local_files_only=True
            )
            self.model_instance.to(self.device)
            self.model_instance.eval()
            self._loaded = True
            self.version = "local-weights"
            logger.info("AASIST model loaded successfully.")
            
            # Model warmup
            logger.info("Warming up AASIST model...")
            dummy_input = torch.zeros((1, 16000), dtype=torch.float32).to(self.device)
            with torch.inference_mode():
                _ = self.model_instance(dummy_input)
            logger.info("AASIST model warmup complete.")
            
        except Exception as e:
            logger.error(f"Failed to load AASIST model from {model_path}: {e}")
            self.model_instance = None
            self._loaded = False

    def _predict_sync(self, audio: np.ndarray, sample_rate: int) -> AntiSpoofResult:
        t_start = time.perf_counter()
        duration_ms = int(len(audio) / sample_rate * 1000) if sample_rate > 0 else 0
        
        if not self._loaded or self.model_instance is None:
            return self._build_unavailable_result(duration_ms)
            
        if len(audio) == 0 or np.all(audio == 0):
            return self._build_unusable_result(duration_ms)

        audio_processed = preprocess_audio(audio, sample_rate)
        tensor = torch.from_numpy(audio_processed).unsqueeze(0).to(self.device)
        
        try:
            with torch.inference_mode():
                _, output = self.model_instance(tensor)
                
                # output typically contains logits over [bonafide, spoof]
                if len(output.shape) == 2 and output.shape[1] == 2:
                    probs = torch.softmax(output, dim=1)
                    raw_spoof_prob = probs[0, 1].item()
                else:
                    # Fallback architecture
                    raw_spoof_prob = 0.5
                    
                calibrated_prob = calibrate_probability(raw_spoof_prob)
                elapsed_s = time.perf_counter() - t_start
                ANTISPOOF_LATENCY.observe(elapsed_s)
                inference_ms = elapsed_s * 1000
                
                return AntiSpoofResult(
                    status="OK",
                    spoof_probability=calibrated_prob,
                    genuine_probability=1.0 - calibrated_prob,
                    confidence=1.0,
                    model_name=self.model_name,
                    model_version=self.version,
                    audio_duration_ms=duration_ms,
                    quality_usable=True,
                    inference_time_ms=inference_ms
                )
                
        except Exception as e:
            MODEL_ERRORS.labels(model="antispoof").inc()
            logger.error(f"AASIST inference failed: {e}")
            return AntiSpoofResult(
                status="ANALYSIS_ERROR",
                spoof_probability=None,
                genuine_probability=None,
                confidence=None,
                model_name=self.model_name,
                model_version=self.version,
                audio_duration_ms=duration_ms,
                quality_usable=False,
                inference_time_ms=0.0
            )

    async def analyze(self, audio: np.ndarray, sample_rate: int) -> AntiSpoofResult:
        # Run synchronous PyTorch inference in a separate thread to prevent blocking FastAPI
        return await asyncio.to_thread(self._predict_sync, audio, sample_rate)

    def _build_unavailable_result(self, duration_ms: int) -> AntiSpoofResult:
        return AntiSpoofResult(
            status="AI_STATUS=UNAVAILABLE",
            spoof_probability=None,
            genuine_probability=None,
            confidence=None,
            model_name=self.model_name,
            model_version="unavailable",
            audio_duration_ms=duration_ms,
            quality_usable=False,
            inference_time_ms=0.0
        )
        
    def _build_unusable_result(self, duration_ms: int) -> AntiSpoofResult:
        return AntiSpoofResult(
            status="INSUFFICIENT_AUDIO", # Or LOW_AUDIO_QUALITY depending on quality checks, but usually insufficient here
            spoof_probability=None,
            genuine_probability=None,
            confidence=None,
            model_name=self.model_name,
            model_version=self.version,
            audio_duration_ms=duration_ms,
            quality_usable=False,
            inference_time_ms=0.0
        )

    def is_loaded(self) -> bool:
        return self._loaded

    def get_health(self) -> Dict[str, Any]:
        return {
            "provider": "aasist",
            "loaded": self._loaded,
            "device": str(self.device),
            "model": self.model_name,
            "version": self.version,
            "status": "healthy" if self._loaded else "degraded"
        }
