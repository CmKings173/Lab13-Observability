from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import Langfuse as _Langfuse

    _client = _Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        host=os.getenv("LANGFUSE_HOST", os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")),
    )

    def tracing_enabled() -> bool:
        return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

    def get_langfuse() -> _Langfuse:
        return _client

except Exception:
    def tracing_enabled() -> bool:  # type: ignore[misc]
        return False

    def get_langfuse() -> Any:  # type: ignore[misc]
        return None
