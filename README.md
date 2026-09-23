<p align="center">
  <h1 align="center">🛡️ VoiceGuard</h1>
  <p align="center">
    <strong>Real-Time AI Voice Integrity Layer for Telecom & VoIP Calls</strong>
  </p>
  <p align="center">
    Protect against deepfakes, AI voice cloning, and audio spoofing — in real time.
  </p>
  <p align="center">
    <a href="#how-it-works">How It Works</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#api-reference">API</a> •
    <a href="#security--privacy">Security</a> •
    <a href="#roadmap">Roadmap</a>
  </p>
</p>

---

## 🎯 What is VoiceGuard?

VoiceGuard is a **cybersecurity platform** that adds continuous AI voice-integrity monitoring to existing voice communication channels. It is **not** a replacement calling app — it's an invisible security layer that sits alongside your telephony provider, analyzing live audio streams for synthetic speech, spoofing artifacts, and voice impersonation.

When a call is in progress, VoiceGuard:
- **Intercepts** a copy of the caller-side audio stream (via Twilio Media Streams)
- **Analyzes** the audio in real-time using deep learning anti-spoofing models (AASIST)
- **Computes** a rolling risk score using a multi-signal fusion engine
- **Pushes** live risk updates to a React Native mobile dashboard via WebSockets

> **Key Insight:** VoiceGuard produces a *rolling risk score* — not a single irreversible "real/fake" decision. Temporary audio anomalies are smoothed, and alerts fire only when suspicious signals persist across multiple analysis windows.

---

## 🔄 How It Works

### High-Level Flow

```
NORMAL CALL
Caller  ─────────────────────────────────►  Receiver

VOICEGUARD-ENABLED CALL
Caller ──► Telephony Provider (Twilio) ──► Receiver
                     │
                     └── audio copy ──► VoiceGuard AI ──► Risk/Alert ──► Mobile App
```

### Step-by-Step Call Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VOICEGUARD CALL PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ① CALL INITIATION                                                          │
│     Caller dials the protected Twilio phone number                          │
│     Twilio establishes call + opens WebSocket media stream to VoiceGuard    │
│                           │                                                 │
│                           ▼                                                 │
│  ② AUDIO INGESTION                                                          │
│     Base64-encoded μ-law audio packets arrive via WebSocket                 │
│     Decoded to raw PCM → normalized float32 → resampled 8kHz → 16kHz       │
│                           │                                                 │
│                           ▼                                                 │
│  ③ VOICE ACTIVITY DETECTION (Silero VAD)                                    │
│     Silence/noise discarded — only voiced speech passes through             │
│                           │                                                 │
│                           ▼                                                 │
│  ④ SLIDING WINDOW BUFFER                                                    │
│     Voiced chunks accumulate into 4-second overlapping windows              │
│     Windows slide forward by 1 second (configurable stride)                 │
│                           │                                                 │
│                           ▼                                                 │
│  ⑤ QUALITY ANALYSIS                                                         │
│     RMS energy, clipping ratio, voiced ratio checked                        │
│     Poor-quality windows are flagged (not sent to AI inference)             │
│                           │                                                 │
│                           ▼                                                 │
│  ⑥ AI INFERENCE (AASIST Anti-Spoofing)                                      │
│     PyTorch AASIST model produces spoof probability per window              │
│     Runs via asyncio.to_thread() to avoid blocking the event loop           │
│                           │                                                 │
│                           ▼                                                 │
│  ⑦ RISK FUSION ENGINE                                                       │
│     Weighted fusion of anti-spoof score + audio quality + speaker verify    │
│     Exponential Moving Average smooths transient spikes                     │
│     Evidence codes generated (not "FAKE"/"REAL" labels)                     │
│                           │                                                 │
│                           ▼                                                 │
│  ⑧ REAL-TIME BROADCAST                                                      │
│     Risk update published to Redis pub/sub                                  │
│     Forwarded to mobile app via authenticated WebSocket                     │
│                           │                                                 │
│                           ▼                                                 │
│  ⑨ MOBILE DASHBOARD                                                         │
│     Live risk meter, anti-spoof signals, audio quality indicators           │
│     Security alerts triggered if risk persists above threshold              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   📱 Mobile App (React Native / Expo)                                   │
│   ┌──────────────────────────────────────────────┐                      │
│   │  Live Risk Dashboard  │  Call History         │                      │
│   │  Alert Banners        │  Speaker Enrollment   │                      │
│   │  Audio Quality View   │  Settings             │                      │
│   └──────────────┬───────────────────────────────┘                      │
│                  │ WebSocket (WSS)                                       │
│                  │                                                       │
│   ┌──────────────▼───────────────────────────────────────────────┐      │
│   │                   VoiceGuard Backend (FastAPI)                │      │
│   │                                                              │      │
│   │  ┌─────────────┐  ┌─────────────────┐  ┌────────────────┐   │      │
│   │  │   Twilio     │  │  Audio Pipeline │  │  Risk Fusion   │   │      │
│   │  │   Webhook    │  │                 │  │  Engine        │   │      │
│   │  │   Handler    │  │  • Decoder      │  │                │   │      │
│   │  │             ├──►│  • Resampler    │  │  • EMA Smooth  │   │      │
│   │  │  Stream     │  │  • Silero VAD   ├──►│  • Evidence    │   │      │
│   │  │  Ingest     │  │  • Buffer/Window│  │    Codes       │   │      │
│   │  │  (WebSocket)│  │  • Quality Gate │  │  • Temporal    │   │      │
│   │  └─────────────┘  └───────┬─────────┘  │    Tracking    │   │      │
│   │                           │             └───────┬────────┘   │      │
│   │                  ┌────────▼────────┐            │            │      │
│   │                  │   AI Inference  │            │            │      │
│   │                  │                 │            │            │      │
│   │                  │  • AASIST       ├────────────┘            │      │
│   │                  │    (Anti-Spoof) │                         │      │
│   │                  │  • ECAPA-TDNN   │                         │      │
│   │                  │    (Speaker ID) │                         │      │
│   │                  └─────────────────┘                         │      │
│   │                                                              │      │
│   │  ┌────────────────────┐  ┌───────────────────────────────┐   │      │
│   │  │     REST API       │  │        WebSocket Hub          │   │      │
│   │  │  /v1/calls         │  │  • Twilio Media Ingest        │   │      │
│   │  │  /v1/alerts        │  │  • Mobile Client Broadcast    │   │      │
│   │  │  /v1/speakers      │  │  • Redis Pub/Sub Bridge       │   │      │
│   │  │  /health           │  │                               │   │      │
│   │  └────────────────────┘  └───────────────────────────────┘   │      │
│   └──────────┬──────────────────────────┬────────────────────────┘      │
│              │                          │                                │
│   ┌──────────▼──────────┐    ┌──────────▼──────────┐                    │
│   │    Redis             │    │   PostgreSQL        │                    │
│   │    (Docker)          │    │   (Supabase)        │                    │
│   │                      │    │                     │                    │
│   │  • Pub/Sub events    │    │  • Users & Orgs     │                    │
│   │  • Call state cache  │    │  • Call Sessions    │                    │
│   │  • Rolling scores    │    │  • Risk Events      │                    │
│   │  • Notification      │    │  • Alerts           │                    │
│   │    cooldowns         │    │  • Speaker Profiles │                    │
│   └─────────────────────┘    │  • Audit Logs       │                    │
│                               └─────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### End-to-End Sequence Diagram

```
Caller        Twilio        VoiceGuard API      AI Engine       Redis         Mobile App
  │               │               │                │              │               │
  │── dial ──────►│               │                │              │               │
  │◄═══ normal voice call ═══════════════════════════════════════►│ Receiver      │
  │               │               │                │              │               │
  │               │── webhook ───►│ (call.started)  │              │               │
  │               │── WS open ───►│                │              │               │
  │               │               │──publish──────────────────────►│               │
  │               │               │                │              │──notify──────►│
  │               │               │                │              │               │
  │               │   ┌───────────────────────────────────────┐   │               │
  │               │   │  Every audio frame (~20ms):           │   │               │
  │               │── media ─────►│                │              │               │
  │               │   │           │  decode → resample → VAD  │   │               │
  │               │   └───────────────────────────────────────┘   │               │
  │               │               │                │              │               │
  │               │   ┌───────────────────────────────────────┐   │               │
  │               │   │  Every 4s window (1s stride):         │   │               │
  │               │   │           │── inference ──►│              │               │
  │               │   │           │◄── spoof_prob ─│              │               │
  │               │   │           │                │              │               │
  │               │   │           │  risk_fusion() │              │               │
  │               │   │           │── publish ─────────────────►│               │
  │               │   │           │                │              │── update ───►│
  │               │   │           │                │              │               │
  │               │   │  (if risk > threshold for N windows)  │   │               │
  │               │   │           │── alert ───────────────────►│               │
  │               │   │           │                │              │── alert ────►│
  │               │   └───────────────────────────────────────┘   │               │
  │               │               │                │              │               │
  │── hang up ──►│── WS close ──►│                │              │               │
  │               │               │── finalize ────────────────►│               │
  │               │               │  save summary to PostgreSQL  │               │
  │               │               │                │              │               │
```

### Audio Pipeline Architecture

```
 Twilio WebSocket                    VoiceGuard Audio Pipeline
 ─────────────────                   ─────────────────────────────────────────────

 ┌──────────────┐     ┌────────────┐     ┌────────────┐     ┌──────────────┐
 │ Base64 μ-law │────►│  Decoder   │────►│ Resampler  │────►│  Silero VAD  │
 │ 8kHz mono    │     │            │     │            │     │              │
 │ (~20ms pkts) │     │ base64 →   │     │ 8kHz PCM → │     │ Speech?      │
 └──────────────┘     │ int16 PCM  │     │ 16kHz f32  │     │ Yes ──► Next │
                      └────────────┘     │ normalize  │     │ No  ──► Drop │
                                         └────────────┘     └──────┬───────┘
                                                                   │
                                                                   ▼
 ┌───────────────┐     ┌───────────────┐     ┌─────────────────────────────┐
 │  Risk Engine  │◄────│   AASIST AI   │◄────│    Rolling Speech Buffer    │
 │               │     │               │     │                             │
 │ fuse signals  │     │ spoof_prob    │     │  Accumulate voiced chunks   │
 │ EMA smooth    │     │ float [0, 1]  │     │  Extract 4s window          │
 │ evidence code │     │               │     │  Slide by 1s stride         │
 │               │     │ asyncio       │     │  Quality gate (RMS, clip,   │
 │ ──► Redis     │     │  .to_thread() │     │   voiced ratio)             │
 └───────────────┘     └───────────────┘     └─────────────────────────────┘
```

### Database Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  ORGANIZATIONS   │       │     USERS        │       │ SPEAKER_PROFILES │
│──────────────────│       │──────────────────│       │──────────────────│
│ id (PK)          │──┐    │ id (PK)          │──┐    │ id (PK)          │
│ name             │  │    │ org_id (FK)      │  │    │ user_id (FK)     │
│ created_at       │  │    │ email            │  │    │ embedding_path   │
└──────────────────┘  │    │ role             │  │    │ created_at       │
                      │    └──────────────────┘  │    └──────────────────┘
                      │                          │
    ┌─────────────────┴──────────────────────────┘
    │
    ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  CALL_SESSIONS   │       │   RISK_EVENTS    │       │  SIGNAL_SCORES   │
│──────────────────│       │──────────────────│       │──────────────────│
│ id (PK)          │──┐    │ id (PK)          │       │ id (PK)          │
│ org_id (FK)      │  ├───►│ call_id (FK)     │       │ call_id (FK)     │
│ provider_call_id │  │    │ timestamp        │       │ timestamp        │
│ started_at       │  │    │ risk_level       │       │ antispoof_score  │
│ ended_at         │  │    │ risk_score       │       │ audio_quality    │
│ max_risk_level   │  │    │ confidence       │       │ speech_duration  │
│ final_risk_score │  │    └──────────────────┘       └──────────────────┘
│ total_windows    │  │
│ analyzed_windows │  │    ┌──────────────────┐       ┌──────────────────┐
└──────────────────┘  │    │     ALERTS       │       │ VERIFICATION     │
                      ├───►│──────────────────│       │   _ACTIONS       │
                      │    │ id (PK)          │       │──────────────────│
                      │    │ org_id (FK)      │       │ id (PK)          │
                      │    │ call_id (FK)     │       │ call_id (FK)     │
                      │    │ alert_type       │       │ action_type      │
                      │    │ severity         │       │ status           │
                      │    │ status           │       │ timestamp        │
                      │    └──────────────────┘       └──────────────────┘
                      │
                      │    ┌──────────────────┐       ┌──────────────────┐
                      │    │  MODEL_VERSIONS  │       │   AUDIT_LOGS     │
                      │    │──────────────────│       │──────────────────│
                      │    │ id (PK)          │       │ id (PK)          │
                      │    │ model_name       │       │ org_id (FK)      │
                      │    │ version          │       │ user_id (FK)     │
                      │    │ deployed_at      │       │ action           │
                      │    │ is_active        │       │ resource_type    │
                      │    └──────────────────┘       │ details (JSON)   │
                      │                               │ timestamp        │
                      │                               └──────────────────┘
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI | Async REST API + WebSocket server |
| **Audio Decoding** | `audioop-lts` + `librosa` | μ-law decoding, resampling (8kHz → 16kHz), normalization |
| **Voice Activity Detection** | Silero VAD (PyTorch Hub) | Filter silence and noise from speech |
| **Anti-Spoofing AI** | AASIST (PyTorch) | Detect synthetic/cloned/replayed speech |
| **Speaker Verification** | ECAPA-TDNN (SpeechBrain) | Compare voices against enrolled trusted profiles |
| **Risk Fusion** | Custom Python engine | Weighted signal fusion, EMA smoothing, evidence codes |
| **Cache & Pub/Sub** | Redis 7 | Real-time call state, cross-process event broadcasting |
| **Database** | PostgreSQL (Supabase) | Persistent storage: users, calls, alerts, audit logs |
| **ORM & Migrations** | SQLAlchemy (async) + Alembic | Schema management and database access |
| **Rate Limiting** | slowapi | API abuse prevention |
| **Observability** | Prometheus + structured JSON logs | Metrics, histograms, correlated log lines |
| **Telephony** | Twilio Programmable Voice | Call routing and live media stream delivery |

### Mobile

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | React Native + Expo (SDK 57) | Cross-platform mobile application |
| **Language** | TypeScript | Type safety |
| **Navigation** | Expo Router | File-based routing |
| **Live State** | Zustand | Real-time call state, risk scores |
| **API State** | TanStack Query (React Query) | Server state caching and synchronization |
| **Real-Time** | WebSocket API | Live risk updates from backend |
| **Auth Tokens** | Expo SecureStore | Secure JWT storage |
| **Notifications** | Expo Notifications | Push alerts for high-risk calls |
| **Animations** | React Native Reanimated | Smooth UI transitions and risk visualizations |

### Infrastructure

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Containerization** | Docker + Docker Compose | Service orchestration |
| **Tunnel** | Ngrok | Expose local API to Twilio webhooks |
| **Model Weights** | Volume-mounted (never in Docker image) | AASIST + ECAPA-TDNN weights |
| **GPU Support** | NVIDIA Container Toolkit (optional) | CUDA-accelerated inference |

---

## 📁 Project Structure

```
Voice-Guard/
├── README.md
├── blueprint.md                    # Full product specification & design document
├── compose.yaml                    # Docker Compose (API + Redis)
├── .env.example                    # Root env template (Docker config)
│
├── services/
│   └── api/                        # ⚡ Python FastAPI Backend
│       ├── main.py                 # App entry point, middleware, route registration
│       ├── Dockerfile              # Multi-stage Docker build (CPU/GPU)
│       ├── requirements.txt        # Python dependencies (pinned)
│       ├── alembic.ini             # Alembic migration config
│       ├── alembic/                # Database migration scripts
│       ├── .env.example            # API environment template
│       │
│       ├── api/
│       │   └── routes/             # REST API route handlers
│       │       ├── health.py       #   GET /health, GET /health/ai
│       │       ├── calls.py        #   GET/POST /v1/calls
│       │       ├── alerts.py       #   GET /v1/alerts
│       │       ├── speakers.py     #   Speaker enrollment endpoints
│       │       ├── devices.py      #   Push notification device registration
│       │       └── verification.py #   Secondary verification actions
│       │
│       ├── services/
│       │   ├── stream_ingest/      # Twilio WebSocket media stream handler
│       │   ├── audio/              # Audio preprocessing pipeline
│       │   │   ├── decoder.py      #   Base64 μ-law → int16 PCM
│       │   │   ├── resampler.py    #   8kHz → 16kHz, float32 normalize
│       │   │   ├── vad.py          #   Silero Voice Activity Detection
│       │   │   ├── buffer.py       #   Rolling speech buffer + windowing
│       │   │   ├── quality.py      #   RMS, clipping, voiced ratio checks
│       │   │   └── preprocessing.py#   Pipeline orchestrator
│       │   ├── antispoof/          # AASIST anti-spoofing inference
│       │   ├── speaker/            # ECAPA-TDNN speaker verification
│       │   ├── risk/               # Risk fusion engine (EMA + evidence)
│       │   ├── notifications/      # Push notification service
│       │   └── services/           # Shared service utilities
│       │
│       ├── models/                 # SQLAlchemy ORM models
│       ├── schemas/                # Pydantic request/response schemas
│       ├── repositories/           # Database access layer
│       ├── core/                   # App configuration and settings
│       ├── scripts/                # Utility scripts (test calls, benchmarks)
│       ├── evaluation/             # Model evaluation tools
│       └── tests/                  # Pytest test suite
│
├── apps/
│   └── mobile/                     # 📱 React Native Mobile App
│       ├── app/                    # Expo Router pages
│       │   ├── (auth)/             #   Login / Signup screens
│       │   ├── (tabs)/             #   Home, History, Settings tabs
│       │   ├── call/               #   Live call monitoring screen
│       │   ├── alerts/             #   Alert details
│       │   ├── settings/           #   App settings
│       │   ├── enrollment.tsx      #   Trusted voice enrollment
│       │   └── verification.tsx    #   Secondary verification flow
│       ├── components/             # Reusable UI components
│       ├── features/               # Feature-specific modules
│       ├── hooks/                  # Custom React hooks (WebSocket, queries)
│       ├── services/               # API client & WebSocket client
│       ├── stores/                 # Zustand state stores
│       ├── theme/                  # Design tokens and theming
│       ├── types/                  # TypeScript type definitions
│       └── utils/                  # Utilities and constants
│
├── model_weights/                  # 🧠 AI Model Weights (gitignored)
│   ├── aasist/                     #   AASIST anti-spoof model files
│   └── speechbrain/                #   ECAPA-TDNN speaker verification cache
│
└── docs/                           # 📚 Detailed Documentation
    ├── ARCHITECTURE.md
    ├── AUDIO_PIPELINE.md
    ├── AASIST_INTEGRATION.md
    ├── RISK_ENGINE.md
    ├── DATABASE_SCHEMA.md
    ├── DEPLOYMENT.md
    ├── SECURITY.md
    ├── OBSERVABILITY.md
    ├── MOBILE_ARCHITECTURE.md
    ├── API_CONTRACT.md
    ├── AUTHENTICATION.md
    ├── SPEAKER_VERIFICATION.md
    ├── THREAT_MODEL.md
    └── ... (more docs)
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Node.js** | ≥ 18 | For the React Native mobile app |
| **Python** | 3.10+ | For the FastAPI backend |
| **Redis** | 7+ | `brew install redis && brew services start redis` |
| **Docker** (optional) | 24.0+ | For containerized deployment |
| **Ngrok** | Latest | To expose local API to Twilio |
| **Twilio Account** | — | With a provisioned Voice-capable phone number |
| **Supabase Project** | — | Hosted PostgreSQL instance |

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Voice-Guard.git
cd Voice-Guard
```

### 2. Database Setup (Supabase)

VoiceGuard uses Alembic to manage PostgreSQL schemas hosted on Supabase.

```bash
# Copy the API environment template
cp services/api/.env.example services/api/.env
```

Edit `services/api/.env` and set these values:
```env
DATABASE_URL=postgresql+asyncpg://user:password@your-supabase-host:5432/postgres
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
```

> **⚠️ Important:** URL-encode any special characters in your password (e.g., `@` → `%40`, `#` → `%23`).

### 3. Backend Setup (FastAPI)

```bash
cd services/api

# Create virtual environment
python -m venv venv
source venv/bin/activate     # macOS/Linux
# venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Expose the API with Ngrok

Twilio requires a public URL to send webhook events and media streams:

```bash
ngrok http 8000
```

Copy the `https://...ngrok-free.app` URL and update `BASE_URL` in `services/api/.env`.

### 5. Twilio Configuration

1. Purchase a Twilio Voice-capable phone number
2. In the Twilio Console, set the phone number's **"A call comes in"** webhook to:
   ```
   https://YOUR-NGROK-URL/v1/providers/twilio/webhook    (HTTP POST)
   ```
3. Update these values in `services/api/.env`:
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

### 6. AI Model Weights

```bash
# Create the model weights directories
mkdir -p model_weights/aasist model_weights/speechbrain

# Download AASIST weights (example using HuggingFace CLI)
huggingface-cli download your-org/aasist-voiceguard --local-dir ./model_weights/aasist
```

Update `services/api/.env`:
```env
ANTISPOOF_PROVIDER=aasist           # Use "mock" for dev without weights
AASIST_MODEL_PATH=./model_weights/aasist
AI_DEVICE=auto                      # auto, cpu, cuda, or mps
```

> **💡 Tip:** For development without GPU/model weights, set `ANTISPOOF_PROVIDER=mock` to use simulated risk scores.

### 7. Mobile App Setup (React Native)

```bash
cd apps/mobile

# Create environment file
cp .env.example .env
```

Edit `.env` with your local network IP (not `localhost`):
```env
EXPO_PUBLIC_API_URL=http://192.168.1.X:8000
EXPO_PUBLIC_WS_URL=ws://192.168.1.X:8000
EXPO_PUBLIC_USE_MOCKS=false
```

Install and run:
```bash
npm install
npx expo start -c
```

Scan the QR code with **Expo Go** on your phone, or press `i` for iOS Simulator / `a` for Android Emulator.

---

## 🐳 Docker Deployment

For a containerized setup (API + Redis):

```bash
# Copy environment templates
cp .env.example .env
cp services/api/.env.example services/api/.env
# Edit both .env files with your credentials

# Start services
docker compose up

# Or detached
docker compose up -d

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/health/ai

# Stop
docker compose down
```

### GPU Deployment

```bash
# Build with GPU support
docker compose build --build-arg COMPUTE=gpu api

# Create compose.override.yaml with GPU config
cat > compose.override.yaml << 'EOF'
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
EOF

docker compose up
```

> AASIST + ECAPA-TDNN require ~1.5 GB VRAM. Any GPU with ≥ 2 GB works (T4, A10G, RTX 3060+).

---

## 🧪 Testing the Pipeline

Once everything is running:

1. Open the **Live Protection** screen on the VoiceGuard mobile app
2. Dial your provisioned **Twilio phone number** from an external phone
3. Twilio executes the webhook → opens a WebSocket media stream to your API
4. **Speak into the phone** — the audio pipeline will:
   - Decode and resample the audio
   - Filter silence via VAD
   - Buffer into 4-second overlapping windows
   - Run AASIST inference on each window
   - Fuse scores into a rolling risk assessment
5. Watch the **mobile dashboard update in real-time** with risk levels, anti-spoof signals, and audio quality indicators

---

## 📡 API Reference

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health (PostgreSQL + Redis connectivity) |
| `GET` | `/health/ai` | AI model loading status |

### Call Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/calls` | List call history with risk summaries |
| `GET` | `/v1/calls/{id}` | Get detailed call analysis |
| `POST` | `/v1/providers/twilio/webhook` | Twilio voice webhook (creates calls) |

### Alert Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/alerts` | List security alerts |

### Speaker Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/speakers` | List enrolled trusted speakers |
| `POST` | `/v1/speakers` | Enroll a new trusted voice |

### Device Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/devices` | Register device for push notifications |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/v1/providers/twilio/stream` | Twilio media stream ingest (internal) |
| `/v1/calls/{id}/ws` | Mobile client real-time risk updates |

### Observability

| Endpoint | Description |
|----------|-------------|
| `GET /metrics/` | Prometheus metrics (counters, gauges, histograms) |

---

## 🛡️ Security & Privacy

### Audio Data
- **Ephemeral processing** — Raw audio is held strictly in memory as `float32` arrays during inference and immediately garbage collected
- **No disk logging** — Audio is never written to disk, PostgreSQL, or Redis
- **Speaker embeddings** — Only mathematical representations are stored; original voice samples are discarded

### Authentication & Authorization
- **JWT verification** — Mobile clients authenticate via Supabase JWTs
- **Twilio signature validation** — Cryptographic `X-Twilio-Signature` verification on all webhooks
- **Row-Level Security** — Supabase RLS ensures strict multi-tenant data isolation

### API Hardening
- **Rate limiting** — `slowapi` enforces request limits
- **HTTPS/WSS enforcement** — Middleware rejects unencrypted traffic in production
- **Strict CORS** — Only whitelisted frontend origins allowed
- **Log sanitization** — Phone numbers and JWTs are automatically redacted

### DoS & Exhaustion Protection
- **WebSocket timeouts** — Silent connections severed within 60 seconds
- **Max session duration** — Hard cap at 2 hours to prevent resource leaks
- **Payload limits** — Oversized or malformed frames safely dropped

---

## ⚙️ Environment Variables

### API (`services/api/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `production` | `production` or `development` |
| `DATABASE_URL` | — | Supabase PostgreSQL connection string |
| `SUPABASE_JWT_SECRET` | — | JWT verification secret |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `VOICE_PROVIDER` | `twilio` | Telephony provider |
| `TWILIO_ACCOUNT_SID` | — | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | — | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | — | Twilio phone number |
| `BASE_URL` | — | Public URL for webhooks (ngrok URL) |
| `ANTISPOOF_PROVIDER` | `aasist` | `aasist` for real inference, `mock` for dev |
| `AASIST_MODEL_PATH` | — | Path to AASIST model weights directory |
| `AI_DEVICE` | `auto` | `auto`, `cpu`, `cuda`, or `mps` |
| `SPEECHBRAIN_CACHE_DIR` | `tmp_ecapa_models` | ECAPA-TDNN model cache directory |
| `AUDIO_ANALYSIS_WINDOW_SECONDS` | `4` | Duration of each analysis window |
| `AUDIO_ANALYSIS_STRIDE_SECONDS` | `1` | Window slide stride |

### Mobile (`apps/mobile/.env`)

| Variable | Description |
|----------|-------------|
| `EXPO_PUBLIC_API_URL` | Backend API URL (use local network IP) |
| `EXPO_PUBLIC_WS_URL` | Backend WebSocket URL |
| `EXPO_PUBLIC_USE_MOCKS` | `true` to use mock data without backend |

---

## 🔍 Risk Engine & Evidence Codes

VoiceGuard avoids labels like "FAKE" or "SCAMMER". Instead, it produces transparent **evidence codes**:

| Evidence Code | Severity | Meaning |
|---------------|----------|---------|
| `PERSISTENT_ANTISPOOF_SIGNAL` | 🔴 HIGH | Anti-spoofing model consistently flags audio windows |
| `EXPECTED_SPEAKER_MISMATCH` | 🟠 MEDIUM/HIGH | Voice doesn't match enrolled trusted profile |
| `TRANSIENT_ANTISPOOF_SPIKE` | 🟡 LOW | Single anomalous window (smoothed by EMA) |
| `POOR_AUDIO_QUALITY` | 🟡 LOW | Audio too poor for reliable analysis |
| `INSUFFICIENT_EVIDENCE` | 🟡 LOW | Not enough speech analyzed yet |
| `NO_RISK_DETECTED` | 🟢 LOW | All signals normal |

### Risk Assessment Output

```json
{
  "riskScore": 0.82,
  "riskLevel": "HIGH",
  "confidence": 0.86,
  "signals": {
    "antiSpoof": { "score": 0.88, "confidence": 0.91 },
    "speakerVerification": { "available": true, "similarity": 0.31 },
    "audioQuality": { "status": "GOOD" }
  },
  "evidence": [
    { "code": "PERSISTENT_ANTISPOOF_SIGNAL", "severity": "HIGH" },
    { "code": "EXPECTED_SPEAKER_MISMATCH", "severity": "MEDIUM" }
  ]
}
```

---

## 🗺️ Roadmap

- [x] Real-time Twilio media stream ingestion
- [x] Audio preprocessing pipeline (decode → resample → VAD → buffer)
- [x] AASIST anti-spoofing inference integration
- [x] Risk fusion engine with EMA smoothing
- [x] Redis pub/sub real-time broadcasting
- [x] React Native mobile dashboard with live risk updates
- [x] Docker Compose deployment (CPU + GPU)
- [x] Prometheus observability metrics
- [x] Structured JSON logging
- [ ] **Speaker Verification** — ECAPA-TDNN embeddings for trusted voice enrollment
- [ ] **Authentication** — Supabase Auth integration for user/org management
- [ ] **Out-of-Band Verification** — Push notification challenges on high-risk detection
- [ ] **Enterprise Dashboard** — Next.js web dashboard for security operations
- [ ] **ONNX/TensorRT Optimization** — Reduced inference latency for production
- [ ] **SIP/RTP Integration** — Direct enterprise telephony media support
- [ ] **Multi-language Support** — Extended accent and language coverage

---

## 📚 Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview and component design |
| [AUDIO_PIPELINE.md](docs/AUDIO_PIPELINE.md) | Audio transformation pipeline stages |
| [AASIST_INTEGRATION.md](docs/AASIST_INTEGRATION.md) | PyTorch AASIST model integration guide |
| [RISK_ENGINE.md](docs/RISK_ENGINE.md) | Risk fusion engine rules and evidence codes |
| [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | PostgreSQL schema and ER diagram |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker deployment and GPU setup |
| [SECURITY.md](docs/SECURITY.md) | Security policies and privacy guarantees |
| [OBSERVABILITY.md](docs/OBSERVABILITY.md) | Prometheus metrics and logging reference |
| [MOBILE_ARCHITECTURE.md](docs/MOBILE_ARCHITECTURE.md) | React Native app architecture |
| [AUTHENTICATION.md](docs/AUTHENTICATION.md) | Auth strategy and JWT handling |
| [SPEAKER_VERIFICATION.md](docs/SPEAKER_VERIFICATION.md) | ECAPA-TDNN speaker ID design |
| [THREAT_MODEL.md](docs/THREAT_MODEL.md) | Threat model and attack surface analysis |
| [API_CONTRACT.md](docs/API_CONTRACT.md) | API contract and endpoint specs |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](apps/mobile/LICENSE) file for details.
