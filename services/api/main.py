from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import health, calls, alerts, speakers, verification

app = FastAPI(title="VoiceGuard API", version="1.0.0")

# CORS config
origins = [
    "http://localhost",
    "http://localhost:8081", # Default expo web port
    "*" # For mobile development bridging
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(calls.router)
app.include_router(alerts.router)
app.include_router(speakers.router)
app.include_router(verification.router)

from services.stream_ingest import router as ingest_router
app.include_router(ingest_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
