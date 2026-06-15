"""Tests for metrics helpers in app/metrics.py"""
import pytest

from app.metrics import percentile, record_error, record_request, snapshot

# Reset global state between tests using monkeypatch
import app.metrics as _m


@pytest.fixture(autouse=True)
def reset_metrics():
    """Isolate each test by resetting all in-memory metrics."""
    _m.REQUEST_LATENCIES.clear()
    _m.REQUEST_COSTS.clear()
    _m.REQUEST_TOKENS_IN.clear()
    _m.REQUEST_TOKENS_OUT.clear()
    _m.ERRORS.clear()
    _m.TRAFFIC = 0
    _m.QUALITY_SCORES.clear()
    yield


# ---------------------------------------------------------------------------
# percentile()
# ---------------------------------------------------------------------------

def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_percentile_empty_returns_zero() -> None:
    assert percentile([], 95) == 0.0


def test_percentile_single_value() -> None:
    assert percentile([500], 95) == 500.0


def test_percentile_p100() -> None:
    assert percentile([10, 20, 30, 40, 50], 100) == 50.0


def test_percentile_p0() -> None:
    assert percentile([10, 20, 30, 40, 50], 0) >= 10.0


def test_percentile_p95_reasonable() -> None:
    values = list(range(1, 101))  # 1..100
    p95 = percentile(values, 95)
    assert 90 <= p95 <= 100


# ---------------------------------------------------------------------------
# record_request() and snapshot()
# ---------------------------------------------------------------------------

def test_record_request_increments_traffic() -> None:
    record_request(latency_ms=100, cost_usd=0.01, tokens_in=50, tokens_out=80, quality_score=0.8)
    assert snapshot()["traffic"] == 1


def test_record_multiple_requests() -> None:
    for i in range(5):
        record_request(latency_ms=100 + i * 10, cost_usd=0.01, tokens_in=50, tokens_out=80, quality_score=0.7)
    snap = snapshot()
    assert snap["traffic"] == 5
    assert snap["latency_p50"] > 0
    assert snap["latency_p95"] >= snap["latency_p50"]


def test_snapshot_empty() -> None:
    snap = snapshot()
    assert snap["traffic"] == 0
    assert snap["latency_p50"] == 0.0
    assert snap["avg_cost_usd"] == 0.0
    assert snap["quality_avg"] == 0.0


def test_snapshot_cost_totals() -> None:
    record_request(latency_ms=100, cost_usd=0.50, tokens_in=100, tokens_out=100, quality_score=0.9)
    record_request(latency_ms=200, cost_usd=0.50, tokens_in=100, tokens_out=100, quality_score=0.9)
    snap = snapshot()
    assert abs(snap["total_cost_usd"] - 1.00) < 0.001
    assert abs(snap["avg_cost_usd"] - 0.50) < 0.001


def test_snapshot_token_totals() -> None:
    record_request(latency_ms=100, cost_usd=0.01, tokens_in=200, tokens_out=150, quality_score=0.8)
    snap = snapshot()
    assert snap["tokens_in_total"] == 200
    assert snap["tokens_out_total"] == 150


def test_snapshot_quality_avg() -> None:
    record_request(latency_ms=100, cost_usd=0.01, tokens_in=50, tokens_out=80, quality_score=0.6)
    record_request(latency_ms=100, cost_usd=0.01, tokens_in=50, tokens_out=80, quality_score=0.8)
    snap = snapshot()
    assert abs(snap["quality_avg"] - 0.70) < 0.01


# ---------------------------------------------------------------------------
# record_error()
# ---------------------------------------------------------------------------

def test_record_error_counts() -> None:
    record_error("TimeoutError")
    record_error("TimeoutError")
    record_error("ValueError")
    snap = snapshot()
    assert snap["error_breakdown"]["TimeoutError"] == 2
    assert snap["error_breakdown"]["ValueError"] == 1


def test_record_error_does_not_affect_traffic() -> None:
    record_error("SomeError")
    assert snapshot()["traffic"] == 0
