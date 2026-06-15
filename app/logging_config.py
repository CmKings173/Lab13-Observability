from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_text

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


class JsonlFileProcessor:
    """Writes every log line to the main JSONL log file."""

    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(rendered + "\n")
        return event_dict


class AuditFileProcessor:
    """
    Bonus: writes a separate audit trail for security-relevant events
    (incident_enabled, incident_disabled, request_received, request_failed).
    Only captures a lean subset of fields — no payload — to keep audit log minimal.
    """

    AUDIT_EVENTS = {"incident_enabled", "incident_disabled", "request_received", "request_failed"}

    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        if event_dict.get("event") not in self.AUDIT_EVENTS:
            return event_dict
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        audit_record = {
            "ts": event_dict.get("ts"),
            "level": event_dict.get("level"),
            "event": event_dict.get("event"),
            "service": event_dict.get("service"),
            "correlation_id": event_dict.get("correlation_id"),
            "user_id_hash": event_dict.get("user_id_hash"),
            "session_id": event_dict.get("session_id"),
            "feature": event_dict.get("feature"),
        }
        rendered = structlog.processors.JSONRenderer()(logger, method_name, audit_record)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(rendered + "\n")
        return event_dict


def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """PII scrubbing processor — redacts sensitive patterns in payload and event strings."""
    payload = event_dict.get("payload")
    if isinstance(payload, dict):
        event_dict["payload"] = {
            k: scrub_text(v) if isinstance(v, str) else v for k, v in payload.items()
        }
    if "event" in event_dict and isinstance(event_dict["event"], str):
        event_dict["event"] = scrub_text(event_dict["event"])
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            scrub_event,            # PII scrubbing — must run before file writers
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            AuditFileProcessor(),   # bonus: separate audit trail for sensitive events
            JsonlFileProcessor(),   # main application log
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger()
