"""
core/metrics.py — Prometheus metric registry for VoiceGuard.

All metrics are defined here and imported where needed.
This keeps the registry centralised — no duplicate registrations.

Latency targets (P95 goals):
  antispoof_inference_latency  < 300 ms
  speaker_inference_latency    < 500 ms
  risk_engine_latency          < 10 ms
  e2e_analysis_latency         < 1000 ms  (audio arrives → risk published)
"""

from prometheus_client import (
    Counter, Histogram, Gauge,
    REGISTRY, CollectorRegistry
)

# ── Active state gauges ──────────────────────────────────────────────────────

ACTIVE_CALLS = Gauge(
    "voiceguard_active_calls",
    "Number of calls currently being processed by the streaming pipeline"
)

ACTIVE_WS_CONNECTIONS = Gauge(
    "voiceguard_active_websocket_connections",
    "Number of open WebSocket connections (Twilio ingest + mobile clients)",
    ["connection_type"]  # "twilio_ingest" | "mobile_client"
)

# ── Audio pipeline counters ──────────────────────────────────────────────────

AUDIO_PACKETS_RECEIVED = Counter(
    "voiceguard_audio_packets_received_total",
    "Total raw audio media packets received from Twilio WebSocket"
)

AUDIO_PACKETS_DROPPED = Counter(
    "voiceguard_audio_packets_dropped_total",
    "Total audio packets dropped (ingest queue full)",
    ["reason"]  # "ingest_queue_full" | "ai_queue_full"
)

AUDIO_WINDOWS_TOTAL = Counter(
    "voiceguard_audio_windows_total",
    "Total audio windows produced by the preprocessor (before quality filtering)"
)

AUDIO_WINDOWS_VALID = Counter(
    "voiceguard_audio_windows_valid_total",
    "Audio windows that passed VAD and quality checks and were submitted to AI inference"
)

AUDIO_WINDOWS_POOR_QUALITY = Counter(
    "voiceguard_audio_windows_poor_quality_total",
    "Audio windows rejected due to low quality or insufficient speech"
)

# ── AI inference latency histograms ─────────────────────────────────────────
# Buckets chosen around target P95 values.

ANTISPOOF_LATENCY = Histogram(
    "voiceguard_antispoof_inference_latency_seconds",
    "End-to-end latency of AASIST anti-spoof inference (wall time including thread dispatch)",
    buckets=[0.025, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 2.0]
)

SPEAKER_LATENCY = Histogram(
    "voiceguard_speaker_inference_latency_seconds",
    "Latency of ECAPA-TDNN speaker verification inference",
    buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0]
)

RISK_ENGINE_LATENCY = Histogram(
    "voiceguard_risk_engine_latency_seconds",
    "Latency of the risk fusion engine evaluation (pure Python, no I/O)",
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.010, 0.025, 0.05]
)

E2E_ANALYSIS_LATENCY = Histogram(
    "voiceguard_e2e_analysis_latency_seconds",
    "End-to-end latency: audio packet received → risk assessment published to Redis",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
)

# ── Error counters ───────────────────────────────────────────────────────────

MODEL_ERRORS = Counter(
    "voiceguard_model_errors_total",
    "Total errors during AI model inference",
    ["model"]  # "antispoof" | "speaker"
)

# ── Business event counters ──────────────────────────────────────────────────

HIGH_RISK_ALERTS = Counter(
    "voiceguard_high_risk_alerts_total",
    "Total push notifications sent for HIGH risk calls"
)

WS_RECONNECTS = Counter(
    "voiceguard_websocket_reconnects_total",
    "WebSocket reconnections (client reconnected after disconnect)",
    ["connection_type"]  # "twilio_ingest" | "mobile_client"
)

CALLS_TOTAL = Counter(
    "voiceguard_calls_total",
    "Total calls processed since startup",
    ["outcome"]  # "completed" | "error" | "timeout" | "unauthorized"
)
