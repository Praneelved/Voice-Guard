# VoiceGuard Deployment Guide

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│              Docker Compose                  │
│                                              │
│  ┌────────────────────┐  ┌───────────────┐   │
│  │   voiceguard-api   │  │     Redis     │   │
│  │                    │  │  (7-alpine)   │   │
│  │  FastAPI + Uvicorn │──│               │   │
│  │  AI Inference      │  │  pub/sub      │   │
│  │  Twilio WebSocket  │  │  state cache  │   │
│  └────────┬───────────┘  └───────────────┘   │
│           │                                  │
│     /app/model_weights (volume, read-only)   │
└───────────┼──────────────────────────────────┘
            │
     ┌──────┴──────┐
     │   Supabase  │  ← Hosted PostgreSQL (NOT in Docker)
     │  PostgreSQL │
     └─────────────┘
```

VoiceGuard runs two containers:
1. **voiceguard-api** — FastAPI application handling REST, Twilio webhooks, WebSocket streaming, and AI inference.
2. **redis** — Pub/sub for live call events, temporal state caching, and push notification cooldowns.

PostgreSQL is hosted on **Supabase** and is intentionally excluded from Docker.

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Docker | 24.0+ |
| Docker Compose | v2 (bundled with Docker Desktop) |
| A Supabase project | With database URL and JWT secret |
| Twilio account | With a phone number and auth token |

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/your-org/Voice-Guard.git
cd Voice-Guard

# Create root .env from template
cp .env.example .env

# Create API .env from template
cp services/api/.env.example services/api/.env
```

Edit `services/api/.env` with your real credentials:
- `DATABASE_URL` — Your Supabase PostgreSQL connection string
- `SUPABASE_JWT_SECRET` — Your Supabase JWT secret
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` — Twilio credentials
- `TWILIO_PHONE_NUMBER` — Your Twilio number
- `BASE_URL` — Your public URL (ngrok, Cloudflare Tunnel, or production domain)

### 2. Prepare model weights

```bash
mkdir -p model_weights/aasist model_weights/speechbrain
```

Download your AASIST weights into `model_weights/aasist/`:
```bash
# Example using HuggingFace CLI
huggingface-cli download your-org/aasist-voiceguard --local-dir ./model_weights/aasist
```

> [!IMPORTANT]
> Model weight files (`.pt`, `.pth`, `.bin`, `.safetensors`) are **gitignored** and must be provisioned on each deployment target. They are mounted read-only into the container.

### 3. Start services

```bash
docker compose up
```

Or detached:
```bash
docker compose up -d
```

### 4. Verify

```bash
# Check overall health (Postgres + Redis)
curl http://localhost:8000/health

# Check AI model status
curl http://localhost:8000/health/ai
```

A healthy response looks like:
```json
{
  "status": "ok",
  "service": "voiceguard-api",
  "dependencies": {
    "postgres": "up",
    "redis": "up"
  }
}
```

If any dependency is down, the endpoint returns **HTTP 503** with `"status": "degraded"`.

### 5. Stop services

```bash
docker compose down
```

To also remove volumes (Redis data):
```bash
docker compose down -v
```

---

## Service Details

### API Container (`voiceguard-api`)

| Property | Value |
|----------|-------|
| Base image | `python:3.11-slim` |
| Runs as | `voiceguard` (UID 1000, non-root) |
| Port | `8000` (configurable via `API_PORT`) |
| Health check | `GET /health` every 30s, 40s start period |
| Restart policy | `unless-stopped` |

The API container handles everything in a single process:
- REST API endpoints
- Twilio webhook receiver
- Twilio Media Stream WebSocket consumer (audio ingest)
- AASIST inference
- ECAPA-TDNN speaker verification
- Risk fusion engine
- Client-facing authenticated WebSocket broadcaster

### Redis Container (`voiceguard-redis`)

| Property | Value |
|----------|-------|
| Image | `redis:7-alpine` |
| Port | `6379` (configurable via `REDIS_PORT`) |
| Max memory | 256 MB (LRU eviction) |
| Persistence | RDB snapshot every 60s if ≥1000 writes |
| Health check | `redis-cli ping` every 10s |

---

## Model Weights

Model weights are **never baked into the Docker image**. They are mounted from the host filesystem at runtime.

### Volume mount

The `compose.yaml` mounts `${MODEL_WEIGHTS_DIR:-./model_weights}` → `/app/model_weights` (read-only).

### Expected structure

```
model_weights/
├── aasist/               ← AASIST anti-spoof weights
│   ├── config.yaml
│   └── model.pth         (or .bin, .safetensors)
└── speechbrain/          ← ECAPA-TDNN cache (auto-populated)
```

### Environment variables

| Variable | Default (Docker) | Purpose |
|----------|-----------------|---------|
| `AASIST_MODEL_PATH` | `/app/model_weights/aasist` | Path to AASIST model directory |
| `SPEECHBRAIN_CACHE_DIR` | `/app/model_weights/speechbrain` | SpeechBrain download cache |
| `ANTISPOOF_PROVIDER` | `aasist` | `aasist` for real inference, `mock` for dev |
| `AI_DEVICE` | `auto` | `cpu`, `cuda`, `mps`, or `auto` |

---

## Startup Order and Health

Docker Compose enforces startup order:

```
redis (healthy) → api
```

The API container will not start until Redis passes its health check (`redis-cli ping`).

The API's own `/health` endpoint checks:
1. **PostgreSQL** — Executes `SELECT 1` against Supabase
2. **Redis** — Sends `PING`

If either fails, the API returns **HTTP 503** (`"status": "degraded"`), causing Docker's health check to mark the container as `unhealthy`.

---

## Local Development (Without Docker)

Docker is **not required** for local development. The existing workflow is preserved:

```bash
cd services/api

# Create virtualenv
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Supabase credentials

# Start Redis locally (if not using Docker)
redis-server &

# Run the API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or use Docker only for Redis while running the API natively:
```bash
docker compose up redis -d
# Then run uvicorn locally, with REDIS_URL=redis://localhost:6379
```

---

## GPU Deployment

> [!WARNING]
> GPU deployment requires the NVIDIA Container Toolkit installed on the host machine.

### Prerequisites

1. **NVIDIA drivers** installed on the host (check with `nvidia-smi`)
2. **NVIDIA Container Toolkit**:
   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

### Build with GPU support

```bash
docker compose build --build-arg COMPUTE=gpu api
```

This skips the CPU-only PyTorch installation and uses the default CUDA-enabled wheels.

### Create `compose.override.yaml`

Create a `compose.override.yaml` at the project root (this file is gitignored):

```yaml
services:
  api:
    build:
      args:
        COMPUTE: gpu
    environment:
      - AI_DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Then run normally:
```bash
docker compose up
```

Docker Compose automatically merges `compose.yaml` + `compose.override.yaml`.

### GPU Memory

AASIST + ECAPA-TDNN together require approximately **1.5 GB VRAM** during inference. Any GPU with ≥2 GB VRAM will work (e.g., T4, A10G, RTX 3060).

---

## Production Deployment Checklist

- [ ] Set `ENV=production` (not `development`)
- [ ] Use a strong `SUPABASE_JWT_SECRET` (≥32 bytes)
- [ ] Set `BASE_URL` to your real public HTTPS domain
- [ ] Enable Twilio webhook signature validation (automatic in production mode)
- [ ] Mount model weights directory with real AASIST weights
- [ ] Verify `/health` returns `200 OK` with all dependencies `up`
- [ ] Verify `/health/ai` returns `loaded: true`
- [ ] Configure a reverse proxy (nginx, Caddy, or cloud LB) with TLS termination
- [ ] Set up log aggregation (the API logs to stdout/stderr)
- [ ] Configure Expo push notification credentials if using push alerts

---

## Scaling Notes

The current architecture runs a single API worker. For horizontal scaling:

1. **Multiple API replicas** — Each can connect to the same Redis and Supabase. Use `docker compose up --scale api=N` with a load balancer.
2. **WebSocket stickiness** — If scaling API replicas, ensure WebSocket connections are sticky (same client → same backend) or use Redis pub/sub for cross-replica event routing (already implemented).
3. **Separate AI worker** — For high throughput, split AI inference into a dedicated service communicating via a Redis job queue. This is not required until you exceed ~50 concurrent calls on a single machine.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `/health` → 503, postgres down | `DATABASE_URL` is wrong or Supabase is unreachable | Verify connection string, check Supabase dashboard |
| `/health` → 503, redis down | Redis container not running | `docker compose up redis` |
| `/health/ai` → `loaded: false` | Model weights not found at mount path | Check `model_weights/aasist/` contains weight files |
| Container exits immediately | Missing `.env` or bad `DATABASE_URL` | Check `docker compose logs api` |
| `CUDA not available` | NVIDIA toolkit not configured | Follow GPU deployment steps above |
