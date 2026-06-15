from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear contextvars to avoid leakage between requests (important for async workers)
        clear_contextvars()

        # Extract x-request-id from incoming headers or generate a new one
        # Format: req-<8-char-hex>
        correlation_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:8]}"

        # Bind correlation_id so every log emitted during this request gets it automatically
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Propagate correlation_id and timing back to the client
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = f"{elapsed_ms:.1f}"

        return response
