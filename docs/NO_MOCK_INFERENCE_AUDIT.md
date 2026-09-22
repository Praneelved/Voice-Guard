# No Mock Inference Audit

This document certifies that VoiceGuard's production execution paths have been thoroughly audited and stripped of mock or randomized risk score generations.

## Removed/Gated Mock Implementations

1. **Anti-Spoofing Fallbacks (Python Backend)**
   - **Previous State**: If `AASISTDetector` failed to load or encountered an exception, it silently returned `0.5` or `0.0` as the `spoof_probability`. 
   - **Current State**: It explicitly passes `AI_STATUS=UNAVAILABLE` or `ANALYSIS_ERROR`. The probability scores evaluate to `None`. The `RiskFusionEngine` correctly cascades these string flags without attempting to mathematically smooth fabricated inputs.
   - **Config Update**: Default backend `antispoof_provider` is now explicitly set to `aasist`. `mock` is restricted to local test environments.

2. **Frontend UI Demonstrations (React Native)**
   - **Previous State**: The Home screen allowed users to inject fake WebSocket payloads ("Simulate Incoming Call") and the Trusted Voices screen forced a direct import of hardcoded mock data.
   - **Current State**: The "Simulate Incoming Call" trigger is completely removed from production builds and hidden behind the explicit `CONFIG.USE_MOCKS` flag. `trusted-voices.tsx` now correctly utilizes the `useSpeakers` REST hook, ensuring it communicates with the actual PostgreSQL/Supabase database.

## Production Flow Verification

The current VoiceGuard production pipeline mandates real audio at every stage:

1. **Twilio**: Submits raw base64 encoded μ-law data via WebSocket.
2. **Preprocessing**: Validates duration, decodes μ-law to PCM, and verifies VAD (Voice Activity Detection). If VAD fails, `LOW_AUDIO_QUALITY` or `INSUFFICIENT_AUDIO` is emitted. No dummy score is assigned.
3. **Inference**: The AASIST model executes the tensor operation. If it fails, `ANALYSIS_ERROR` is emitted. No random fallback is provided.
4. **Risk Engine**: The rule-based `RiskFusionEngine` consumes the signals explicitly. Missing signals are reported transparently in the `evidence` payload.
5. **Mobile Application**: Renders the strict schema payload it receives.

**Audit Result: PASS**
No mathematical randomness (`Math.random()`, `np.random`, hardcoded probabilities) remains in the production inference pathways.
