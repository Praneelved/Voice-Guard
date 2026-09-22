# VoiceGuard Threat Model

This document outlines potential threats to VoiceGuard and how the system architecture defends against them.

## 1. Spoofed Twilio Requests
**Threat:** An attacker discovers the Twilio webhook endpoint URL and attempts to send falsified `POST` requests to simulate fake calls or inject malicious TwiML.
**Mitigation:** VoiceGuard validates the cryptographic `X-Twilio-Signature` using `twilio.request_validator.RequestValidator` against the secret `TWILIO_AUTH_TOKEN`. Requests lacking a valid signature are rejected with a `403 Forbidden` response.

## 2. Audio Injection & Unauthorized Streaming
**Threat:** An attacker connects directly to the WSS streaming ingestion endpoint and pipes pre-recorded, synthesized, or malicious audio into the AI inference engine.
**Mitigation:** The ingestion WebSocket is secured via HTTP Basic Auth. The credentials are dynamically injected into the TwiML response sent strictly back to Twilio. An attacker cannot bypass the webhook signature to obtain the TwiML and therefore cannot authenticate into the stream.

## 3. WebSocket Abuse & Resource Exhaustion (DoS)
**Threat:** Malicious actors attempt to exhaust server resources by opening thousands of WebSocket connections or streaming infinite loops of junk data to stall the AI models.
**Mitigation:** 
- User and Ingestion WebSockets enforce strict `asyncio.wait_for` heartbeats. Connections idle for > 60 seconds are terminated.
- Maximum session length is strictly capped at 2 hours.
- Payloads are decoded inside wrapped `try/except` blocks; invalid JSON or malformed Base64 frames are safely dropped without crashing the `asyncio` worker tasks.
- FastAPI endpoints are protected by `slowapi` rate limiting.

## 4. Cross-User Data Access
**Threat:** An authenticated user modifies API requests or WebSocket URLs to fetch call histories, alerts, or risk streams belonging to another organization.
**Mitigation:** 
- The Supabase PostgreSQL database implements strict Row Level Security (RLS). All select/insert policies mandate `auth.uid() = org_id`.
- The FastAPI endpoints implicitly validate ownership before querying the DB.
- User WebSocket subscriptions extract the `sub` from the JWT and only broadcast `RiskEvents` bound to authorized sessions.

## 5. Stolen JWT & Token Abuse
**Threat:** A user's JWT is intercepted or leaks via logs, allowing an attacker to impersonate them.
**Mitigation:** 
- HTTPS/WSS is strictly enforced by middleware in production; unencrypted traffic is denied, mitigating MITM.
- The custom `core.logger` redacts all JWT signatures before they reach stdout or logging pipelines.
- JWT expiration is strictly enforced.

## 6. Model Endpoint Abuse
**Threat:** An attacker bombards the AI inference service (e.g., PyTorch ECAPA-TDNN or AASIST) with high volumes of traffic to incur computational costs.
**Mitigation:** The inference models are completely internal. They are not exposed to the public internet and are only accessible via the authorized ingest pipelines following Twilio Signature and Basic Auth validation.

## 7. Sensitive Logging
**Threat:** Developers reviewing system logs are exposed to PII, including complete phone numbers or active tokens.
**Mitigation:** The `PrivacyMaskingFormatter` automatically sanitizes phone numbers (e.g., `+131***4012`) and masks JWTs before emission.

## 8. Malicious Audio Input
**Threat:** The system receives specifically crafted audio files meant to trigger buffer overflows in Python audio processing libraries (e.g., `librosa`, `soundfile`).
**Mitigation:** The Twilio adapter strictly parses standard `mulaw` encoding via Python's native `audioop`. Invalid bytes are ignored. The application does not write audio bytes to disk, mitigating file-system level exploits.
