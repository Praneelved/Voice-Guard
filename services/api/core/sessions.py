from typing import Dict, Any
from schemas.calls import CallResponse

# In-memory storage for active calls
active_calls: Dict[str, CallResponse] = {}

# Mock data
mock_alerts = []
mock_speakers = [
    {
        "id": "speaker_1",
        "name": "Sarah (CEO)",
        "enrolled_at": "2026-09-20T10:00:00Z",
        "status": "active"
    }
]
