import logging
from .detector import AntiSpoofDetector, MockAntiSpoofDetector, AASISTDetector

logger = logging.getLogger(__name__)

def get_detector() -> AntiSpoofDetector:
    """
    Factory function to get the best available anti-spoof detector.
    Attempts to load AASIST, but falls back to Mock if PyTorch or weights are missing.
    """
    try:
        logger.info("Attempting to initialize AASISTDetector...")
        return AASISTDetector()
    except Exception as e:
        logger.warning(f"Failed to initialize AASISTDetector: {e}")
        logger.warning("Falling back to MockAntiSpoofDetector.")
        return MockAntiSpoofDetector()
