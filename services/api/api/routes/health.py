from fastapi import APIRouter, Response, status
from services.antispoof.loader import get_detector
from core.database import engine
from core.redis_client import get_redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check(response: Response):
    health_status = {
        "status": "ok",
        "service": "voiceguard-api",
        "dependencies": {
            "postgres": "unknown",
            "redis": "unknown"
        }
    }
    
    is_healthy = True
    
    # Check Postgres
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            health_status["dependencies"]["postgres"] = "up"
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        health_status["dependencies"]["postgres"] = "down"
        is_healthy = False
        
    # Check Redis
    try:
        r = await get_redis()
        await r.ping()
        health_status["dependencies"]["redis"] = "up"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["dependencies"]["redis"] = "down"
        is_healthy = False
        
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        health_status["status"] = "degraded"
        
    return health_status

@router.get("/health/ai")
def ai_health_check():
    detector = get_detector()
    return {
        "antispoof": detector.get_health()
    }
