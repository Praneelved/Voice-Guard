# VoiceGuard Mobile Architecture

## Core Technology Stack
- **Framework:** React Native with Expo (Development Build unless a native module requires bare workflow).
- **Language:** TypeScript for type safety and scalability.
- **Routing:** Expo Router for file-based navigation.
- **State Management:**
  - **Zustand:** Used for live, ephemeral application state (e.g., active call status, real-time risk scores).
  - **TanStack Query (React Query):** Used for API/server state caching, synchronization, and data fetching (e.g., call history, user settings).
- **Real-time Communication:** WebSocket API for receiving live call events and risk updates.

## Core Responsibilities

### 1. Authentication & Security
- Secure login and token management.
- Integration with biometric authentication for secondary verification workflows.

### 2. Dashboard & Navigation
- **Home / Protection Status:** Global indicator of whether the user is actively protected.
- **Settings:** Privacy, security, profile, and organization settings.
- **Call History:** Log of past calls, their risk assessment, and any flagged anomalies.

### 3. Active Protected-Call Monitoring (Live Call Screen)
- **Live Rolling Risk:** Dynamic UI component (e.g., a dial or waveform color change) showing the ongoing risk score.
- **Anti-Spoof Signal Display:** Specific visual indicators when synthetic or AI-generated speech artifacts are detected.
- **Speaker Consistency Display:** Indicators confirming the speaker matches a known trusted profile (when applicable).
- **Audio-Quality Display:** Feedback if the audio is too poor to be confidently analyzed.

### 4. Interactive Alerts
- **Security Alerts:** Prominent overlays/modals warning the user of high risk.
- **Secondary Verification Workflows:** UI prompts asking the user to confirm their identity or challenging the caller if suspicious activity is detected.

### 5. Trusted Voice Enrollment
- Dedicated UI flow for recording and registering trusted voices.
- Requires high-quality audio capture using device microphone.

## Directory Structure (Proposed)
```
app/
 ├── (auth)/             # Login, Signup, OTP
 ├── (tabs)/             # Home, History, Settings
 ├── call/               # Active call monitoring screen
 ├── enrollment/         # Trusted voice setup
 ├── _layout.tsx
src/
 ├── components/         # Reusable UI (RiskMeter, AlertBanners, AudioVisualizer)
 ├── store/              # Zustand stores (useActiveCallStore, etc.)
 ├── hooks/              # Custom hooks (useWebSocket, useTanStackQueries)
 ├── services/           # API clients, WebSocket client
 ├── utils/              # Formatting, constants, theme
 ├── types/              # TypeScript interfaces
```
