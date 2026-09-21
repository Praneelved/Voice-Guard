from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertResponse(BaseModel):
    id: str
    call_id: str
    severity: str
    timestamp: datetime
    message: str
    acknowledged: bool = False
