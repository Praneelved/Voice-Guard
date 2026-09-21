# VoiceGuard Development Checklist

## Pre-requisites
- [ ] Initialize Git repository
- [ ] Set up `docs/` folder with architecture and planning documents

## Milestone 1: Mobile application running with mocked data
- [x] Initialize Expo project in `mobile/`
- [x] Configure Expo Router and base layout
- [x] Implement Zustand store (`useActiveCallStore`) with mock data
- [x] Build Login UI (`app/(auth)/login.tsx`)
- [x] Build Main Tabs (`Home`, `History`, `Settings`)
- [x] Build Active Call UI (`app/call/[id].tsx`)
- [x] Build `RiskMeter` and `AntiSpoofIndicator` components
- [x] Write Jest snapshot tests

## Milestone 2: Mobile application connected to FastAPI REST API
- [x] Initialize Python environment and FastAPI project in `backend/` (in `services/api`)
- [ ] Set up PostgreSQL and Alembic migrations
- [ ] Implement DB Models (`users`, `user_settings`, `calls`)
- [x] Create REST endpoints (`/auth/login`, `/users/me`, `/calls`) (mocked for now)
- [x] Set up TanStack Query in the mobile app
- [x] Create API client service in mobile app
- [x] Connect mobile UI to real API data for authentication and history
- [x] Write Pytest unit tests for endpoints

## Milestone 3: Realtime WebSocket risk updates
- [ ] Implement WebSocket manager in FastAPI
- [ ] Create `wss://.../ws/calls/active` endpoint
- [ ] Implement WebSocket client service in mobile app
- [ ] Create `useCallWebSocket` hook in mobile app
- [ ] Connect WebSocket data to Zustand store
- [ ] Validate UI updates based on simulated server WS messages
- [ ] Write Pytest Asyncio tests for WebSockets

## Milestone 4: Real provider call media reaches backend
- [ ] Set up SIP/Programmable Voice provider account (e.g., Twilio)
- [ ] Create webhook endpoints in FastAPI to receive call initiation events
- [ ] Implement audio stream receiver to handle incoming media streams
- [ ] Configure local tunneling (e.g., ngrok) for webhook testing
- [ ] Conduct a test call and verify raw audio chunks are received by backend

## Milestone 5: Audio normalization + VAD + speech windows
- [ ] Integrate VAD library (`webrtcvad` or `silero-vad`)
- [ ] Implement audio format conversion and normalization
- [ ] Build processing pipeline to buffer raw chunks into speech windows
- [ ] Write unit tests to validate VAD behavior on sample audio
- [ ] Tune VAD parameters

## Milestone 6: Anti-spoof model
- [ ] Download AASIST model weights
- [ ] Create model wrapper and inference engine in backend
- [ ] Connect speech window pipeline to the inference engine
- [ ] Verify model outputs probabilities (0.0 - 1.0) for windows
- [ ] Write tests with sample real and deepfake audio

## Milestone 7: Rolling risk engine
- [ ] Set up local Redis instance
- [ ] Implement time-series buffering in Redis
- [ ] Implement mathematical smoothing (moving average) for risk scores
- [ ] Connect risk engine to WebSocket manager
- [ ] Validate smooth UI updates in mobile app during simulated score spikes

## Milestone 8: Alerts and verification
- [ ] Define risk thresholds in backend
- [ ] Implement logic to emit `call.alert` WS events
- [ ] Build `SecurityAlertModal` in mobile app
- [ ] Build `VerificationChallenge` UI in mobile app
- [ ] Implement client-to-server `call.action` event for challenges
- [ ] Write E2E test for the alert trigger flow

## Milestone 9: Trusted speaker enrollment
- [ ] Download ECAPA-TDNN model weights
- [ ] Build mobile enrollment UI (instructions and recording)
- [ ] Implement device microphone capture via `expo-av`
- [ ] Create `/enrollment/*` REST endpoints
- [ ] Build ECAPA-TDNN inference pipeline to generate embeddings
- [ ] Store embeddings in PostgreSQL
- [ ] Write integration test for the full enrollment flow

## Milestone 10: Push notifications and production hardening
- [ ] Configure APNs and FCM credentials
- [ ] Implement push notification service in backend
- [ ] Request push permissions and handle tokens in mobile app
- [ ] Write `Dockerfile` and `docker-compose.yml` for backend
- [ ] Verify environment variables and secrets management
- [ ] Test push notifications on physical devices
- [ ] Final manual QA and production build verification
