# VoiceGuard Implementation Plan

## Milestone 1: Mobile application running with mocked data
- **Objective**: Build the initial React Native (Expo) UI with navigation, state management (Zustand), and mocked data for all primary screens to validate the UX.
- **Files to create**: 
  - `mobile/package.json`, `mobile/app.json`
  - `mobile/app/(auth)/login.tsx`
  - `mobile/app/(tabs)/home.tsx`, `mobile/app/(tabs)/history.tsx`, `mobile/app/(tabs)/settings.tsx`
  - `mobile/app/call/[id].tsx` (Active Call Screen)
  - `mobile/src/store/useActiveCallStore.ts`
  - `mobile/src/components/RiskMeter.tsx`, `mobile/src/components/AntiSpoofIndicator.tsx`
- **APIs involved**: None (Mocked local data via Zustand).
- **Data flow**: Mock data injected into Zustand -> UI re-renders -> User navigates through simulated call lifecycle.
- **Tests**: Jest snapshot tests for UI components.
- **Completion criteria**: A developer can run `npx expo start`, navigate through login, home, view a mock active call with dynamic (mocked) risk changes, and check history.
- **Dependencies**: React Native, Expo, Expo Router, Zustand.
- **Manual actions required from the developer**: Set up the Expo environment, run the app on iOS simulator / Android emulator, verify layout across screen sizes.

## Milestone 2: Mobile application connected to FastAPI REST API
- **Objective**: Create the Python backend foundation and connect the mobile app to real authentication, user profile, and call history endpoints.
- **Files to create**:
  - `backend/requirements.txt`, `backend/main.py`
  - `backend/api/routes/auth.py`, `backend/api/routes/users.py`, `backend/api/routes/calls.py`
  - `backend/db/models.py`, `backend/db/session.py`
  - `mobile/src/services/apiClient.ts`
  - `mobile/src/hooks/useQueries.ts`
- **APIs involved**: `POST /auth/login`, `GET /users/me`, `GET /calls` (REST).
- **Data flow**: Mobile App (TanStack Query) -> HTTP GET/POST -> FastAPI Backend -> PostgreSQL -> Response back to Mobile.
- **Tests**: Pytest for FastAPI endpoints; unit tests for `apiClient.ts`.
- **Completion criteria**: Mobile app successfully authenticates against the backend, fetches real user settings, and displays call history from the database.
- **Dependencies**: FastAPI, SQLAlchemy, PostgreSQL, TanStack Query (Mobile).
- **Manual actions required from the developer**: Provision local PostgreSQL DB, run database migrations (Alembic), configure `.env` variables for backend and mobile.

## Milestone 3: Realtime WebSocket risk updates
- **Objective**: Establish a secure WebSocket connection between the mobile app and the FastAPI backend to stream live risk updates.
- **Files to create**:
  - `backend/api/websockets/manager.py`
  - `backend/api/websockets/routes.py`
  - `mobile/src/services/websocketClient.ts`
  - `mobile/src/hooks/useCallWebSocket.ts`
- **APIs involved**: `wss://api.../ws/calls/active`
- **Data flow**: Backend generates simulated risk payload -> WebSocket Manager -> WSS Connection -> Mobile WebSocket Client -> Zustand State Update -> RiskMeter Component Re-render.
- **Tests**: Pytest Asyncio tests for WebSocket connections.
- **Completion criteria**: Mobile app connects to the WebSocket upon entering an active call screen and visually updates the risk meter based on incoming real-time server messages.
- **Dependencies**: FastAPI WebSockets, Redis (Pub/Sub for scaling later).
- **Manual actions required from the developer**: Verify network connectivity for WebSockets (especially if using physical devices on local network), inspect WSS frames in debugger.

## Milestone 4: Real provider call media reaches backend
- **Objective**: Integrate with the SIP/Programmable Voice provider to route live audio streams to the backend during a call.
- **Files to create**:
  - `backend/services/audio/stream_receiver.py`
  - `backend/api/routes/webhooks.py` (for call initiation webhooks)
- **APIs involved**: SIP Provider Webhooks (e.g., Twilio/Plivo Media Streams API).
- **Data flow**: Caller -> SIP Provider -> Provider forks media -> HTTP/WebSocket stream -> `stream_receiver.py` (Backend).
- **Tests**: Unit tests for audio chunk parsing and format validation.
- **Completion criteria**: Backend successfully receives, decodes, and logs raw audio payload chunks from a test call initiated via the SIP provider.
- **Dependencies**: Provider SDK or raw socket handling for media streams.
- **Manual actions required from the developer**: Set up provider account (e.g., Twilio), configure webhook URLs (using ngrok for local dev), make a real phone call to trigger the flow.

## Milestone 5: Audio normalization + VAD + speech windows
- **Objective**: Process the raw incoming audio chunks into normalized, structured speech windows ready for AI analysis.
- **Files to create**:
  - `backend/services/audio/processor.py`
  - `backend/services/audio/vad.py`
- **APIs involved**: Internal audio processing pipeline.
- **Data flow**: Raw Audio Chunks -> Format Conversion (e.g., to 16kHz mono PCM) -> Voice Activity Detection (VAD) -> Buffered Speech Windows -> AI Engine Queue.
- **Tests**: Process a sample `.wav` file through the pipeline and assert correct VAD timestamps and window sizes.
- **Completion criteria**: Backend correctly drops silence and aggregates active speech into discrete, normalized windows (e.g., 2-second overlapping windows).
- **Dependencies**: `pydub`, `webrtcvad` or `silero-vad`, `numpy`.
- **Manual actions required from the developer**: Tune VAD aggressiveness parameters based on test call audio quality.

## Milestone 6: Anti-spoof model
- **Objective**: Integrate the PyTorch-based AASIST anti-spoofing model to score speech windows for synthetic artifacts.
- **Files to create**:
  - `backend/ai/models/aasist_wrapper.py`
  - `backend/ai/inference_engine.py`
- **APIs involved**: Internal ML inference pipeline.
- **Data flow**: Speech Window -> PyTorch Model -> Spoof Probability Score (0.0 to 1.0).
- **Tests**: Pytest passing known real audio (score should be low) and known deepfake audio (score should be high).
- **Completion criteria**: The AI engine successfully outputs a probability score for each speech window in real-time (< 200ms latency).
- **Dependencies**: `torch`, `torchaudio`, pre-trained AASIST weights.
- **Manual actions required from the developer**: Download model weights to the proper directory, ensure PyTorch runs efficiently (CPU/MPS/CUDA depending on environment).

## Milestone 7: Rolling risk engine
- **Objective**: Aggregate individual AI scores into a smoothed "rolling risk" metric over time using Redis for fast state management.
- **Files to create**:
  - `backend/services/risk/engine.py`
  - `backend/services/risk/redis_store.py`
- **APIs involved**: Redis internal commands.
- **Data flow**: Inference Score -> Redis Time-Series Buffer -> Moving Average/Exponential Smoothing -> New Rolling Risk Score -> WebSocket Manager -> Mobile App.
- **Tests**: Unit tests verifying the math of the rolling window aggregation.
- **Completion criteria**: The mobile app displays a smooth, non-jittery risk score that reacts appropriately to sudden spikes in spoof probability during a live call.
- **Dependencies**: `redis-py`.
- **Manual actions required from the developer**: Ensure Redis server is running locally, tune the rolling window duration and decay factors.

## Milestone 8: Alerts and verification
- **Objective**: Implement logic to trigger security alerts on the mobile app when risk exceeds predefined thresholds, and build the secondary verification UI.
- **Files to create**:
  - `backend/services/risk/thresholds.py`
  - `mobile/src/components/SecurityAlertModal.tsx`
  - `mobile/src/components/VerificationChallenge.tsx`
- **APIs involved**: `call.alert` and `call.action` WebSocket events.
- **Data flow**: Risk Engine crosses threshold -> Backend emits `call.alert` WS event -> Mobile App shows `SecurityAlertModal` -> User taps "Verify Caller" -> Mobile emits `call.action` WS event -> Backend executes challenge logic via SIP provider.
- **Tests**: E2E tests simulating a high-risk call and verifying the alert pops up.
- **Completion criteria**: Deepfake audio triggers a critical alert on the mobile app, allowing the user to initiate a secondary verification challenge.
- **Dependencies**: None additional.
- **Manual actions required from the developer**: Define standard threshold boundaries (e.g., Risk > 85 = Critical).

## Milestone 9: Trusted speaker enrollment
- **Objective**: Allow users to record their voice and create an ECAPA-TDNN embedding to serve as a trusted voice profile.
- **Files to create**:
  - `mobile/app/enrollment/index.tsx`, `mobile/app/enrollment/record.tsx`
  - `backend/api/routes/enrollment.py`
  - `backend/ai/models/ecapa_wrapper.py`
- **APIs involved**: `POST /enrollment/start`, `POST /enrollment/{session_id}/audio`
- **Data flow**: Mobile App records audio -> Uploads multipart/form-data to Backend -> Audio Processor -> ECAPA-TDNN Model -> Vector Embedding -> Saved to PostgreSQL.
- **Tests**: Integration test for the full enrollment upload and embedding generation flow.
- **Completion criteria**: User can complete the enrollment flow in the app, resulting in a new valid vector embedding stored in the database.
- **Dependencies**: `expo-av` (for mobile recording), pre-trained ECAPA-TDNN weights.
- **Manual actions required from the developer**: Handle mobile microphone permissions, verify audio quality of the mobile recording.

## Milestone 10: Push notifications and production hardening
- **Objective**: Add push notifications for background call alerts and prepare the application for production deployment.
- **Files to create**:
  - `backend/services/notifications/apns_fcm.py`
  - `mobile/src/services/pushNotifications.ts`
  - `ops/Dockerfile`, `ops/docker-compose.yml`
- **APIs involved**: Apple APNs / Firebase Cloud Messaging (FCM).
- **Data flow**: Backend detects critical risk while app is backgrounded -> Push Notification Service -> User Device -> User taps notification -> Opens App to Active Call Screen.
- **Tests**: Trigger test push notifications.
- **Completion criteria**: The system is containerized, environment variables are securely managed, and backgrounded devices receive alerts if a monitored call becomes high-risk.
- **Dependencies**: `expo-notifications`, push provider SDKs.
- **Manual actions required from the developer**: Configure Apple/Google developer certificates for push, write deployment documentation, test the production build on physical devices.
