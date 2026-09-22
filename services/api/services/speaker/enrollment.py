import logging
import base64
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_session_maker
from models.domain import TrustedVoice, VoiceEmbedding
from services.audio.decoder import decode_twilio_payload
from services.audio.resampler import normalize_and_resample
from services.audio.vad import SileroVAD
from services.audio.quality import analyze_quality
from services.audio.config import audio_config
from .ecapa import get_verifier

logger = logging.getLogger(__name__)

async def enroll_trusted_voice(
    session: AsyncSession, 
    user_id: str, 
    name: str, 
    label: str, 
    audio_b64_samples: list[str]
) -> TrustedVoice:
    """
    Enroll a new trusted voice by extracting embeddings from multiple samples.
    """
    verifier = get_verifier()
    vad = SileroVAD(sample_rate=audio_config.target_sample_rate)
    
    valid_embeddings = []
    
    for sample_b64 in audio_b64_samples:
        try:
            # 1. Decode base64 
            # (Assuming the client sends standard WAV or raw PCM16, not Twilio payload here.
            # But the prompt mentions "Enrollment audio -> preprocessing -> VAD". 
            # Usually enrollment happens via mobile app sending base64 audio.
            # If it's Twilio mu-law, decode_twilio_payload. If it's standard base64 PCM, we just decode.)
            # For this exercise, let's assume it's standard raw PCM16 16kHz base64 from the phone, OR mu-law from twilio.
            # Let's decode it as raw bytes. We might need a proper WAV decoder if they send WAV.
            raw_bytes = base64.b64decode(sample_b64)
            pcm16_audio = np.frombuffer(raw_bytes, dtype=np.int16)
            
            # Normalizing to float32
            # Assuming incoming is 16kHz from mobile app, but let's resample from 16000 to 16000 just in case.
            audio_float32 = normalize_and_resample(pcm16_audio, orig_sr=16000, target_sr=audio_config.target_sample_rate)
            
            # 2. VAD - only extract if enough speech
            is_speech = vad.process(audio_float32)
            
            quality = analyze_quality(audio_float32, voiced_ratio=1.0 if is_speech else 0.0)
            if not quality["usable"]:
                logger.warning(f"Discarding enrollment sample due to quality: {quality['reason']}")
                continue
                
            if not is_speech:
                logger.warning("Discarding enrollment sample due to insufficient speech/silence.")
                continue
                
            # 3. Extract embedding
            emb = verifier.extract_embedding(audio_float32)
            valid_embeddings.append(emb)
            
        except Exception as e:
            logger.error(f"Failed to process enrollment sample: {e}")
            continue
            
    if not valid_embeddings:
        raise ValueError("No valid speech samples provided for enrollment.")
        
    # Create the DB entries
    tv = TrustedVoice(user_id=user_id, name=name, label=label)
    session.add(tv)
    await session.flush() # To get tv.id
    
    for emb in valid_embeddings:
        ve = VoiceEmbedding(
            trusted_voice_id=tv.id,
            embedding=emb.tolist(),
            model_name="speechbrain/spkrec-ecapa-voxceceb",
            model_version="1.0"
        )
        session.add(ve)
        
    await session.commit()
    await session.refresh(tv)
    
    return tv
