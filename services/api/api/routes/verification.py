from fastapi import APIRouter

router = APIRouter()

@router.post("/v1/verification/{call_id}")
def start_verification(call_id: str):
    return {
        "status": "started",
        "call_id": call_id,
        "challenge": "Please say: 'My voice is my password'",
        "expires_in": 60
    }
