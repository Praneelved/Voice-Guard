# VoiceGuard

VoiceGuard is a cybersecurity platform designed to protect users against deepfakes, AI voice cloning, and audio spoofing in real-time. It intercepts live audio streams via programmable telephony, analyzing speaker consistency, signal anomalies, and overall voice integrity, presenting a real-time risk dashboard to the user's mobile app.

## Architecture

VoiceGuard consists of:
- **Mobile Application**: A React Native (Expo) frontend providing live dashboards, history logs, alerts, and trusted voice enrollment.
- **Backend API**: A Python FastAPI service that orchestrates real-time WebSocket communication, PostgreSQL persistence, and call state.
- **Audio Pipeline & AI**: A highly concurrent, non-blocking pipeline handling live base64 `mu-law` audio decoding, Silero Voice Activity Detection (VAD), overlapping speech windowing, and inference. See [Audio Pipeline Documentation](docs/AUDIO_PIPELINE.md) and [AASIST Integration Guide](docs/AASIST_INTEGRATION.md) for full details on the machine learning implementation.
- **State & Data**: Redis is used for fast cross-process pub/sub broadcasting and transient call state. PostgreSQL (Supabase) is used for robust relational persistence of telemetry, models, and alert history.

## Prerequisites

Before starting, ensure you have:
- **Node.js** >= 18 and **npm**
- **Python** 3.10+
- **Redis Server** running locally (`brew install redis` -> `brew services start redis`)
- A **Twilio** Account with a provisioned phone number.
- A **Supabase** (PostgreSQL) project.
- **Ngrok** installed for exposing local ports to the internet.

## Getting Started

### 1. Database Setup (Supabase)
VoiceGuard uses Alembic to manage PostgreSQL schemas.

1. Create a `services/api/.env` file using the provided template:
```bash
cp services/api/.env.example services/api/.env
```
2. Update the `DATABASE_URL` in `.env` with your Supabase connection string. **Make sure to prefix the protocol with `postgresql+asyncpg://`** and URL-encode any special characters in your password (e.g., `@` becomes `%40`).

### 2. Backend Setup (FastAPI)
```bash
cd services/api
python -m venv venv
source venv/bin/activate

# Install dependencies (requires audioop-lts for Python 3.13+)
pip install -r requirements.txt

# Run Database Migrations to create schemas in Supabase
alembic upgrade head

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Expose the API to the Internet
Twilio needs a public URL to reach your local webhook. Run Ngrok in a new terminal:
```bash
ngrok http 8000
```
*Copy the resulting `https://...ngrok-free.app` URL and update the `BASE_URL` in your `services/api/.env` file.*

### 4. Twilio Setup
1. Purchase a Twilio Voice-capable phone number.
2. In the Twilio Console, configure the phone number's **"A call comes in"** webhook to point to:
   `[YOUR_NGROK_URL]/v1/providers/twilio/webhook` (HTTP POST).
3. Update `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` in your `services/api/.env` file.

### 5. Mobile Setup (React Native)
The mobile app displays live dashboards of active calls.

Create an environment file:
```bash
cd apps/mobile
cp .env.example .env
```

Update `.env` with your local IP address (NOT localhost/127.0.0.1, use your network IP like `192.168.1.x`):
```env
EXPO_PUBLIC_API_URL=http://<YOUR_LOCAL_IP>:8000
EXPO_PUBLIC_WS_URL=ws://<YOUR_LOCAL_IP>:8000
EXPO_PUBLIC_USE_MOCKS=false
```

Run the App:
```bash
npm install
npx expo start -c
```
*Scan the QR code with the Expo Go app on your physical device, or run it in an iOS/Android emulator.*

## Testing the Pipeline
Once everything is running:
1. Open the **Live Protection** screen on your VoiceGuard mobile app.
2. Dial your provisioned Twilio Phone Number from an external phone.
3. Twilio will execute the webhook, establish a live media WebSocket to your Ngrok tunnel, and route the audio.
4. Speak into the phone! The backend Audio Pipeline will chunk your speech, analyze it for spoofing, and broadcast Risk Updates to Redis.
5. The Mobile App will instantly render the changing risk levels and signal anomalies in real-time. 

## Remaining Tasks / Roadmap
- **Speaker Verification**: Implement ECAPA-TDNN embeddings to allow enrollment of trusted voices.
- **Authentication**: Integrate Supabase Auth to securely associate users, organizations, and call history.
- **Out-of-band Verification**: Implement push-notification actions triggered when a high-risk spike is detected.
