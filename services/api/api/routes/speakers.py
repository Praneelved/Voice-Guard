from fastapi import APIRouter
from typing import List
from schemas.speakers import SpeakerResponse
from core.sessions import mock_speakers

router = APIRouter()

@router.get("/v1/models")
def get_models():
    # As requested by GET /v1/models (could be AI models or speakers, assuming general models here)
    return {
        "models": [
            {"name": "antispoof", "version": "1.0.0", "status": "active"},
            {"name": "speaker_verification", "version": "1.0.0", "status": "active"}
        ]
    }

@router.get("/v1/speakers", response_model=List[SpeakerResponse])
def get_speakers():
    return mock_speakers
