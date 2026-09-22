import logging
from .config import AntiSpoofConfig
from .base import AntiSpoofDetector
from .mock import MockAntiSpoofDetector
from .aasist import AASISTDetector

logger = logging.getLogger(__name__)

# Singleton instance
_detector_instance = None

def get_detector() -> AntiSpoofDetector:
    """
    Returns the configured anti-spoofing detector.
    Instantiates it on the first call.
    """
    global _detector_instance
    if _detector_instance is not None:
        return _detector_instance

    config = AntiSpoofConfig()
    provider = config.antispoof_provider.lower()
    
    if provider == "aasist":
        logger.info("Initializing AASISTDetector...")
        _detector_instance = AASISTDetector(config)
    else:
        logger.info("Initializing MockAntiSpoofDetector...")
        _detector_instance = MockAntiSpoofDetector()
        
    return _detector_instance
