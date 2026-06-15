from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import get_langfuse, tracing_enabled


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        lf = get_langfuse()

        if lf and tracing_enabled():
            # Langfuse v3: use start_as_current_span as context manager
            with lf.start_as_current_span(
                name="agent.run",
                input={"message": summarize_text(message), "feature": feature},
            ) as span:
                result = self._run_pipeline(message, feature)
                # Tag the trace with user/session metadata
                lf.update_current_trace(
                    user_id=hash_user_id(user_id),
                    session_id=session_id,
                    tags=["lab", feature, self.model],
                    metadata={"model": self.model},
                )
                lf.update_current_span(
                    output={"answer": summarize_text(result.answer)},
                    metadata={
                        "latency_ms": result.latency_ms,
                        "tokens_in": result.tokens_in,
                        "tokens_out": result.tokens_out,
                        "cost_usd": result.cost_usd,
                        "quality_score": result.quality_score,
                    },
                )
        else:
            result = self._run_pipeline(message, feature)

        metrics.record_request(
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            quality_score=result.quality_score,
        )
        return result

    def _run_pipeline(self, message: str, feature: str) -> AgentResult:
        started = time.perf_counter()
        docs = retrieve(message)
        prompt = f"Feature={feature}\nDocs={docs}\nQuestion={message}"
        response = self.llm.generate(prompt)
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)
        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        return round((tokens_in / 1_000_000) * 3 + (tokens_out / 1_000_000) * 15, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(
            token in answer.lower() for token in question.lower().split()[:3]
        ):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
