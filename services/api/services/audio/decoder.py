import base64
import numpy as np

try:
    import audioop
except ImportError:
    pass

def decode_twilio_payload(b64_payload: str) -> np.ndarray:
    """
    Decodes a base64 encoded G.711 mu-law payload from Twilio 
    into a raw 16-bit PCM numpy array.
    """
    if not b64_payload:
        return np.array([], dtype=np.int16)
        
    raw_bytes = base64.b64decode(b64_payload)
    
    # audioop handles the mu-law to linear PCM (16-bit) expansion
    pcm_bytes = audioop.ulaw2lin(raw_bytes, 2)
    
    # Return as 16-bit signed integer array
    return np.frombuffer(pcm_bytes, dtype=np.int16)
