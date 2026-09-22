from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from prometheus_client import make_asgi_app as make_metrics_app

from api.routes import health, calls, alerts, speakers, verification, devices

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="VoiceGuard API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

env = os.environ.get("ENV", "development")

# Security Middleware: HTTPS / WSS Enforcement
@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if env != "development":
        proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
        if proto == "http":
            return JSONResponse(status_code=403, content={"detail": "HTTPS required"})
    return await call_next(request)

# CORS config
if env == "development":
    origins = [
        "http://localhost",
        "http://localhost:8081", # Default expo web port
        "*" # For mobile development bridging
    ]
else:
    # Restrict to strictly defined frontends in production
    origins = [
        "https://voiceguard.app",
        "https://api.voiceguard.app"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Register routes
app.include_router(health.router)
app.include_router(calls.router)
app.include_router(alerts.router)
app.include_router(speakers.router)
app.include_router(verification.router)
app.include_router(devices.router)

from services.stream_ingest import router as ingest_router
app.include_router(ingest_router)

# Prometheus /metrics endpoint — mounted as a sub-app so it bypasses
# FastAPI middleware (CORS, HTTPS enforcement, rate limiting).
# Restrict scraping to internal network via firewall/reverse-proxy in prod.
metrics_app = make_metrics_app()
app.mount("/metrics", metrics_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
