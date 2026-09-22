"""
core/logger.py — Structured logging for VoiceGuard.

Outputs JSON lines when ENV != "development" so log aggregators
(Loki, CloudWatch, Datadog) can parse fields directly.
In development, falls back to a human-readable format.

Privacy rules (always enforced):
  - Phone numbers masked: +1234567890 → +1***7890
  - JWTs masked: eyJ... → eyJ***(redacted)
  - Raw audio bytes NEVER logged anywhere in this codebase.
"""

import logging
import json
import re
import sys
import os
import time
from typing import Any, Optional
from contextvars import ContextVar

# ── Correlation ID context ────────────────────────────────────────────────────
# Set these in your request handlers/WebSocket handlers for automatic inclusion
# in every log line emitted during that coroutine's execution.

_call_id_var: ContextVar[Optional[str]] = ContextVar("call_id", default=None)
_session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


def set_correlation_ids(call_id: Optional[str] = None, session_id: Optional[str] = None):
    """Call at the start of a WebSocket session or request handler."""
    if call_id:
        _call_id_var.set(call_id)
    if session_id:
        _session_id_var.set(session_id)


def get_correlation_ids() -> dict:
    return {
        k: v
        for k, v in {
            "call_id": _call_id_var.get(),
            "session_id": _session_id_var.get(),
        }.items()
        if v is not None
    }


# ── Privacy masking ───────────────────────────────────────────────────────────

_PHONE_RE = re.compile(r'\+?\d{10,15}')
_JWT_RE = re.compile(r'ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')


def _mask(text: str) -> str:
    def _mask_phone(m):
        p = m.group(0)
        return f"{p[:2]}***{p[-4:]}" if len(p) > 6 else "***"

    text = _PHONE_RE.sub(_mask_phone, text)
    text = _JWT_RE.sub("eyJ***(redacted)", text)
    return text


# ── Formatters ────────────────────────────────────────────────────────────────

class StructuredJSONFormatter(logging.Formatter):
    """
    Emits a single JSON object per log line.

    Fields always present:
      ts         ISO-8601 timestamp
      level      DEBUG / INFO / WARNING / ERROR / CRITICAL
      logger     logger name (dotted module path)
      message    the log message (privacy-masked)
      service    "voiceguard-api"

    Fields included when available:
      call_id    from context var
      session_id from context var
      exc_info   exception traceback (if present)
      **extra    any extra= kwargs passed to the logger call
    """

    SERVICE = "voiceguard-api"

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": _mask(record.getMessage()),
            "service": self.SERVICE,
        }

        # Correlation IDs
        payload.update(get_correlation_ids())

        # Extra fields (latency_ms, model, etc.) passed via extra={}
        for key, val in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            ) and not key.startswith("_"):
                payload[key] = val

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class HumanReadableFormatter(logging.Formatter):
    """Privacy-masking human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return _mask(msg)


# ── Factory ───────────────────────────────────────────────────────────────────

_ENV = os.environ.get("ENV", "development")


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    handler = logging.StreamHandler(sys.stdout)

    if _ENV == "development":
        formatter = HumanReadableFormatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
        )
    else:
        formatter = StructuredJSONFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if _ENV == "development" else logging.INFO)
    logger.propagate = False
    return logger
