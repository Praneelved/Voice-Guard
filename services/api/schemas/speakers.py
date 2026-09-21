from pydantic import BaseModel
from datetime import datetime

class SpeakerResponse(BaseModel):
    id: str
    name: str
    enrolled_at: datetime
    status: str
