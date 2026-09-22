from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from core.database import async_session_maker
from models.domain import TrustedVoice
from services.speaker import enroll_trusted_voice, TrustedVoiceCreate, TrustedVoiceResponse
from core.security import get_current_user
from typing import Dict, Any

router = APIRouter()

class SampleUpload(BaseModel):
    samples: List[str] # base64 encoded audio strings

@router.get("/v1/trusted-voices", response_model=List[TrustedVoiceResponse])
async def get_trusted_voices(current_user: Dict[str, Any] = Depends(get_current_user)):
    async with async_session_maker() as session:
        stmt = select(TrustedVoice).where(TrustedVoice.user_id == current_user["id"]).options(selectinload(TrustedVoice.embeddings))
        result = await session.execute(stmt)
        voices = result.scalars().all()
        
        return [
            TrustedVoiceResponse(
                id=str(v.id),
                user_id=str(v.user_id),
                name=v.name,
                label=v.label,
                samples_count=len(v.embeddings),
                created_at=v.created_at
            )
            for v in voices
        ]

@router.post("/v1/trusted-voices", response_model=TrustedVoiceResponse)
async def create_trusted_voice(data: TrustedVoiceCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    async with async_session_maker() as session:
        tv = TrustedVoice(user_id=current_user["id"], name=data.name, label=data.label)
        session.add(tv)
        await session.commit()
        await session.refresh(tv)
        
        return TrustedVoiceResponse(
            id=str(tv.id),
            user_id=str(tv.user_id),
            name=tv.name,
            label=tv.label,
            samples_count=0,
            created_at=tv.created_at
        )

@router.post("/v1/trusted-voices/{id}/samples", response_model=TrustedVoiceResponse)
async def upload_voice_samples(id: str, data: SampleUpload, current_user: Dict[str, Any] = Depends(get_current_user)):
    async with async_session_maker() as session:
        stmt = select(TrustedVoice).where(TrustedVoice.id == id).options(selectinload(TrustedVoice.embeddings))
        result = await session.execute(stmt)
        tv = result.scalars().first()
        
        if not tv or str(tv.user_id) != current_user["id"]:
            raise HTTPException(status_code=404, detail="Trusted voice not found")
            
        # We delete old embeddings and enroll new ones.
        for emb in tv.embeddings:
            await session.delete(emb)
        await session.commit()
            
        try:
            # Re-enroll using the new samples
            tv = await enroll_trusted_voice(session, tv.user_id, tv.name, tv.label, data.samples)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        stmt = select(TrustedVoice).where(TrustedVoice.id == tv.id).options(selectinload(TrustedVoice.embeddings))
        result = await session.execute(stmt)
        tv = result.scalars().first()
            
        return TrustedVoiceResponse(
            id=str(tv.id),
            user_id=str(tv.user_id),
            name=tv.name,
            label=tv.label,
            samples_count=len(tv.embeddings),
            created_at=tv.created_at
        )

@router.delete("/v1/trusted-voices/{id}")
async def delete_trusted_voice(id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    async with async_session_maker() as session:
        stmt = select(TrustedVoice).where(TrustedVoice.id == id)
        result = await session.execute(stmt)
        tv = result.scalars().first()
        
        if not tv or str(tv.user_id) != current_user["id"]:
            raise HTTPException(status_code=404, detail="Trusted voice not found")
            
        await session.delete(tv)
        await session.commit()
        
        return {"status": "deleted"}

