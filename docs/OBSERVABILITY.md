# VoiceGuard Observability Guide

## Overview

VoiceGuard exposes production observability through two mechanisms:

| Mechanism | Purpose | Endpoint |
|-----------|---------|----------|
| **Prometheus metrics** | Counters, gauges, histograms for every pipeline stage | `GET /metrics/` |
| **Structured JSON logs** | Correlated log lines with `call_id`, `session_id`, latency fields | `stdout` |

No additional infrastructure is required to use either. Prometheus can scrape `/metrics` directly. Logs can be shipped to any aggregator (Loki, CloudWatch, Datadog) that accepts JSON-line stdin.

---

## Metrics Reference

### Active State Gauges

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `voiceguard_active_calls` | Gauge | — | Calls currently being processed in the streaming pipeline |
| `voiceguard_active_websocket_connections` | Gauge | `connection_type` | Open WebSocket connections. Labels: `twilio_ingest`, `mobile_client` |

### Audio Pipeline Counters

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `voiceguard_audio_packets_received_total` | Counter | — | Raw μ-law media packets received from Twilio |
| `voiceguard_audio_packets_dropped_total` | Counter | `reason` | Dropped packets. `reason`: `ingest_queue_full`, `ai_queue_full` |
| `voiceguard_audio_windows_total` | Counter | — | Windows produced by the audio preprocessor |
| `voiceguard_audio_windows_valid_total` | Counter | — | Windows that passed VAD + quality checks |
| `voiceguard_audio_windows_poor_quality_total` | Counter | — | Windows rejected due to noise, silence, or low SNR |

### Latency Histograms

| Metric | Type | Target P95 | Description |
|--------|------|-----------|-------------|
| `voiceguard_antispoof_inference_latency_seconds` | Histogram | **300 ms** | AASIST wall-clock inference time (includes thread dispatch via `asyncio.to_thread`) |
| `voiceguard_speaker_inference_latency_seconds` | Histogram | **500 ms** | ECAPA-TDNN speaker verification total latency |
| `voiceguard_risk_engine_latency_seconds` | Histogram | **10 ms** | Pure-Python risk fusion evaluation |
| `voiceguard_e2e_analysis_latency_seconds` | Histogram | **1000 ms** | Window queued by preprocessor → risk assessment published to Redis |

> [!IMPORTANT]
> The E2E latency target assumes AASIST loaded on CPU. GPU will lower antispoof latency to ~50–100 ms, bringing E2E well under 500 ms.

### Error Counters

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `voiceguard_model_errors_total` | Counter | `model` | Inference failures. `model`: `antispoof`, `speaker` |

### Business Event Counters

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `voiceguard_high_risk_alerts_total` | Counter | — | Push notifications sent for HIGH risk calls |
| `voiceguard_websocket_reconnects_total` | Counter | `connection_type` | Client reconnections after disconnect |
| `voiceguard_calls_total` | Counter | `outcome` | All calls by final outcome: `completed`, `error`, `timeout`, `unauthorized` |

---

## Latency Targets

These are the P95 targets used to set histogram bucket boundaries. They represent acceptable performance under normal telephony conditions (8 kHz μ-law input, CPU inference).

| Stage | P95 Target | Rationale |
|-------|-----------|-----------|
| Antispoof inference | 300 ms | AASIST on CPU; measured warmup ~150–250 ms |
| Speaker verification | 500 ms | ECAPA-TDNN includes DB query for stored embedding |
| Risk fusion engine | 10 ms | Pure Python deterministic evaluation |
| End-to-end | 1000 ms | User-perceivable: analysis result must arrive within 1 s of audio window |

### Measuring actual vs target

```bash
# Check current P95 antispoof latency using promtool or PromQL
curl -s http://localhost:8001/metrics/ | grep antispoof_inference_latency | grep _bucket

# PromQL example (if Prometheus is running)
histogram_quantile(0.95, rate(voiceguard_antispoof_inference_latency_seconds_bucket[5m]))
```

---

## Structured Logs

### Format

In `ENV=production`, every log line is a JSON object:

```json
{
  "ts": "2026-09-23T02:10:45",
  "level": "INFO",
  "logger": "services.stream_ingest.router",
  "message": "Risk update published",
  "service": "voiceguard-api",
  "call_id": "CA1234abcd...",
  "session_id": "f5f0b075-...",
  "risk_level": "HIGH",
  "risk_score": 0.847,
  "confidence": 0.91
}
```

In `ENV=development`, a human-readable format is used instead:
```
2026-09-23 02:10:45  INFO      services.stream_ingest.router  Risk update published
```

### Correlation IDs

Every log line emitted within a WebSocket session automatically carries:

| Field | Description |
|-------|-------------|
| `call_id` | Twilio CallSid — uniquely identifies the telephone call |
| `session_id` | Internal VoiceGuard session UUID — survives reconnects within the same call |

These are injected via Python `ContextVar` — no explicit threading required.

### Privacy guarantees

The logger applies masking before any output leaves the process:

| Pattern | Before | After |
|---------|--------|-------|
| Phone number | `+17372508034` | `+1***8034` |
| JWT | `eyJhbGci...` | `eyJ***(redacted)` |
| Raw audio | Never logged | Not applicable |

---

## Accessing the Metrics Endpoint

```bash
# Raw Prometheus text exposition format
curl http://localhost:8000/metrics/

# Health + dependencies
curl http://localhost:8000/health
```

> [!WARNING]
> In production, restrict `/metrics/` to internal network access only (VPC, internal LB, or firewall rule). It should never be publicly reachable. Add to nginx:
> ```nginx
> location /metrics {
>     allow 10.0.0.0/8;
>     deny all;
>     proxy_pass http://api:8000/metrics/;
> }
> ```

---

## Prometheus Integration

Add a scrape job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: voiceguard_api
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics/
    scrape_interval: 15s
```

If running with Docker Compose, add Prometheus as an optional service:

```yaml
# docker-compose.override.yaml (gitignored)
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    depends_on:
      - api
```

---

## Recommended Alerts

These PromQL alert rules cover the most operationally important conditions:

```yaml
groups:
  - name: voiceguard
    rules:

      # API is down or unhealthy
      - alert: VoiceGuardAPIDown
        expr: up{job="voiceguard_api"} == 0
        for: 1m
        labels:
          severity: critical

      # Antispoof P95 latency breaches target
      - alert: AntiSpoofLatencyHigh
        expr: >
          histogram_quantile(0.95,
            rate(voiceguard_antispoof_inference_latency_seconds_bucket[5m])
          ) > 0.300
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Antispoof P95 latency above 300ms"

      # E2E latency breaches target
      - alert: E2ELatencyHigh
        expr: >
          histogram_quantile(0.95,
            rate(voiceguard_e2e_analysis_latency_seconds_bucket[5m])
          ) > 1.0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "End-to-end analysis P95 latency above 1s"

      # Model errors spiking
      - alert: ModelErrorRate
        expr: >
          rate(voiceguard_model_errors_total[5m]) > 0.1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "AI model error rate above 0.1/s"

      # Audio being dropped (queue saturation)
      - alert: AudioPacketDropRate
        expr: >
          rate(voiceguard_audio_packets_dropped_total[1m]) > 5
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "More than 5 audio packets/s being dropped"
```

---

## Log Aggregation

### Loki (with Docker)

```yaml
# docker-compose.override.yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail.yml:/etc/promtail/config.yml:ro
```

LogQL example to find all HIGH risk events:
```logql
{service="voiceguard-api"} | json | risk_level="HIGH"
```

Find all events for a specific call:
```logql
{service="voiceguard-api"} | json | call_id="CA1234abcd"
```

### CloudWatch / Datadog

Since logs are emitted as JSON to stdout, any log driver that reads container stdout will work natively. The structured fields (`call_id`, `session_id`, `risk_level`, `risk_score`) are automatically parsed as filterable attributes.

---

## What is NOT Measured (and Why)

| Signal | Reason excluded |
|--------|----------------|
| Raw audio bytes | Privacy — raw audio must never appear in observability systems |
| Individual user IDs in metrics | Cardinality risk; user identity stays in structured logs with masking |
| Full phone numbers | Privacy; masked in logs, never in metric labels |
| Supabase query latency | SQLAlchemy pool is managed by the DB driver; add if DB becomes a bottleneck |
| WebSocket message body | Protocol-level detail; not needed for observability |
