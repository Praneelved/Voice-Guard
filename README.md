# VoiceGuard

VoiceGuard is a cybersecurity platform designed to protect users against deepfakes, AI voice cloning, and audio spoofing in real-time. It monitors live audio streams, analyzing speaker consistency, signal anomalies, and overall voice integrity, presenting a real-time risk dashboard to the user.

## Architecture

VoiceGuard consists of:
- **Mobile Application**: A React Native (Expo) frontend providing live dashboards, history, and trusted voice enrollment.
- **Backend API**: A Python FastAPI service that orchestrates real-time WebSocket communication, alerts, and call state.
- **Audio Pipeline**: A strictly bounded audio processing engine that decodes, normalizes, and chunks incoming PCM streams. It executes real-time Voice Activity Detection (VAD) using `webrtcvad` and compiles precise sliding speech windows for deep learning ingestion.

## Requirements

### Mobile
- Node.js >= 18
- Expo CLI
- React Native dependencies

### Backend
- Python 3.10+
- `numpy`, `webrtcvad`, `soundfile`, `librosa`

## Getting Started

### 1. Backend Setup
```bash
cd services/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Run the API:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Mobile Setup
Create a `.env` file in `apps/mobile/`:
```env
EXPO_PUBLIC_API_URL=http://<YOUR_LOCAL_IP>:8000/v1
EXPO_PUBLIC_WS_URL=ws://<YOUR_LOCAL_IP>:8000/v1
EXPO_PUBLIC_USE_MOCKS=false
```

**Run the App:**
```bash
cd apps/mobile
npm install
npx expo start -c
```

### 3. Demo the Audio Pipeline
You can run a standalone verification of the backend audio processor using the included demo script, which streams a fixture WAV file through the ring buffers and VAD components.
```bash
cd services/api
source venv/bin/activate
python -m services.audio_pipeline.demo tests/fixtures/test.wav
```
