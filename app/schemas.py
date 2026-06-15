from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., examples=["u_team_01"])
    session_id: str = Field(..., examples=["s_demo_01"])
    feature: str = Field(default="qa", examples=["qa", "summary"])
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    correlation_id: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LogRecord(BaseModel):
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["info", "warning", "error", "critical"]
    service: str
    event: str
    correlation_id: str
    env: str
    user_id_hash: Optional[str] = None
    session_id: Optional[str] = None
    feature: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    error_type: Optional[str] = None
    tool_name: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
