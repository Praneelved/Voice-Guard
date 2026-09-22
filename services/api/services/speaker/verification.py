import logging
import time
import numpy as np
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_session_maker
from models.domain import TrustedVoice
from .ecapa import get_verifier
from .schemas import VerificationResult
from core.metrics import SPEAKER_LATENCY, MODEL_ERRORS

logger = logging.getLogger(__name__)

# Configurable thresholds
# Depending on ECAPA-TDNN and cosine similarity, typical thresholds are ~0.25 to 0.50
# Needs to be tuned based on real distributions.
SIMILARITY_THRESHOLD = 0.40

async def verify_speaker(audio_window: np.ndarray, expected_speaker_id: str) -> VerificationResult:
    """
    Compares the audio window embedding against the stored embeddings of the expected speaker.
    Returns the maximum similarity found.
    """
    _t = time.perf_counter()
    verifier = get_verifier()
    
    if not verifier.is_loaded():
        return VerificationResult(
            expected_speaker=expected_speaker_id,
            similarity=0.0,
            match_state="MODEL_UNAVAILABLE",
            confidence=0.0
        )
        
    # 1. Extract live embedding
    try:
        live_emb = verifier.extract_embedding(audio_window)
    except Exception as e:
        MODEL_ERRORS.labels(model="speaker").inc()
        logger.error(f"Failed to extract embedding during verification: {e}")
        return VerificationResult(
            expected_speaker=expected_speaker_id,
            similarity=0.0,
            match_state="EXTRACTION_FAILED",
            confidence=0.0
        )
        
    # 2. Fetch expected speaker embeddings from DB
    async with async_session_maker() as session:
        stmt = select(TrustedVoice).where(TrustedVoice.id == expected_speaker_id).options(selectinload(TrustedVoice.embeddings))
        result = await session.execute(stmt)
        trusted_voice = result.scalars().first()
        
    if not trusted_voice or not trusted_voice.embeddings:
        return VerificationResult(
            expected_speaker=expected_speaker_id,
            similarity=0.0,
            match_state="SPEAKER_NOT_FOUND",
            confidence=0.0
        )
        
    # 3. Compute similarities
    max_sim = -1.0
    for ve in trusted_voice.embeddings:
        stored_emb = np.array(ve.embedding, dtype=np.float32)
        sim = verifier.compute_similarity(live_emb, stored_emb)
        if sim > max_sim:
            max_sim = sim
            
    # 4. Determine state
    if max_sim >= SIMILARITY_THRESHOLD:
        match_state = "LIKELY_MATCH"
        confidence = min(max_sim / (SIMILARITY_THRESHOLD * 1.5), 1.0)
    else:
        match_state = "NO_MATCH"
        confidence = 1.0 - max(0.0, max_sim / SIMILARITY_THRESHOLD)
    
    SPEAKER_LATENCY.observe(time.perf_counter() - _t)
    return VerificationResult(
        expected_speaker=expected_speaker_id,
        similarity=max_sim,
        match_state=match_state,
        confidence=confidence
    )
