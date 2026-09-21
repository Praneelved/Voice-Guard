# VoiceGuard API Contract

## REST API (FastAPI)
Base URL: `/v1`

### System
- `GET /health`
  - Response: `{ "status": "ok", "service": "voiceguard-api" }`
- `GET /v1/models`
  - Response: `{ "models": [...] }`

### Calls
- `POST /v1/calls`
  - Body: `{ "caller_number": "+1234567890" }`
  - Response: `{ "id": "uuid", "caller_number": "...", "status": "active", "started_at": "..." }`
- `GET /v1/calls/{id}`
  - Response: Call details.
- `GET /v1/calls/{id}/events`
  - Response: List of historical events for the call.

### Alerts
- `GET /v1/alerts`
  - Response: List of active alerts.
- `POST /v1/alerts/{id}/ack`
  - Response: `{ "status": "acknowledged", "alert_id": "uuid" }`

### Verification
- `POST /v1/verification/{call_id}`
  - Response: `{ "status": "started", "call_id": "...", "challenge": "...", "expires_in": 60 }`

---

## Realtime WebSocket API
Endpoint: `ws://api.voiceguard.com/v1/calls/{call_id}/events`

### Server-to-Client Events

**Risk Update (Sent frequently)**
```json
{
  "type": "risk.update",
  "call_id": "uuid",
  "timestamp_ms": 1690000000000,
  "risk": 0.42,
  "level": "caution",
  "confidence": 0.85,
  "quality": "good",
  "signals": {
    "antispoof": 0.52,
    "speaker_mismatch": null,
    "signal_anomaly": 0.24
  }
}
```
