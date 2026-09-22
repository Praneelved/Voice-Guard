# VoiceGuard Security Policies

This document outlines the security architecture and guarantees implemented within VoiceGuard.

## 1. Authentication & Authorization
- **JWT Verification**: Mobile clients authenticate via Supabase JWTs. WebSockets validate the JWT in the query parameters during the handshake.
- **Twilio Webhooks**: VoiceGuard verifies the cryptographic `X-Twilio-Signature` on all incoming webhook traffic to ensure it genuinely originates from Twilio.
- **WebSocket Streaming Security**: Twilio streams authenticate into the ingestion engine via Basic Auth injected into the TwiML.

## 2. Privacy & Audio Data
- **Ephemeral Audio**: Raw audio frames streamed from Twilio are held strictly in memory (`float32` arrays) for the duration of inference. They are immediately garbage collected once they pass through the Risk Fusion Engine.
- **No Disk Logging**: Raw audio is **never** written to disk. Audio is never persisted in PostgreSQL or Redis.
- **Speaker Verification Embeddings**: Speaker verification utilizes ECAPA-TDNN derived embeddings. The original voice sample is discarded after the embedding (a mathematical representation) is generated.

## 3. Database Security
- **Row Level Security (RLS)**: VoiceGuard strictly employs Supabase RLS. No query can retrieve `call_sessions`, `alerts`, or `risk_events` belonging to a different organization.

## 4. API Hardening
- **Rate Limiting**: `slowapi` enforces strict limits on inbound REST traffic to prevent abuse and brute force enumeration.
- **Strict HTTPS/WSS**: Middleware forcefully rejects unencrypted traffic unless running in a designated `development` environment.
- **CORS**: Enforces explicit allowed origins matching the production frontend domains.
- **Logging Sanitization**: Phone numbers and JWTs are automatically redacted via a custom Python `logging.Formatter` before reaching stdout or APM tools.

## 5. Defense against DoS & Exhaustion
- **WebSocket Timeouts**: All active streams contain `asyncio.wait_for` heartbeats. Silent connections are severed within 60 seconds.
- **Max Duration**: Active analysis sessions are hard-capped at 2 hours to prevent resource leaks from malformed disconnects.
- **Payload Limits**: Ingestion workers safely drop unparseable or oversized frames without crashing the core AI loops.
