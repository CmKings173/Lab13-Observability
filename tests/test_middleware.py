"""Tests for CorrelationIdMiddleware in app/middleware.py"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import CorrelationIdMiddleware


@pytest.fixture()
def test_app():
    """Minimal FastAPI app with only the middleware under test."""
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=True)


def test_correlation_id_generated_when_missing(test_app) -> None:
    """Middleware must generate a correlation_id when none is provided."""
    resp = test_app.get("/ping")
    assert resp.status_code == 200
    cid = resp.headers.get("x-request-id")
    assert cid is not None
    assert cid.startswith("req-")
    assert len(cid) == 12  # "req-" + 8 hex chars


def test_correlation_id_not_missing(test_app) -> None:
    """Generated correlation_id must NOT be the sentinel value 'MISSING'."""
    resp = test_app.get("/ping")
    cid = resp.headers.get("x-request-id")
    assert cid != "MISSING"


def test_correlation_id_propagated_from_header(test_app) -> None:
    """Middleware must echo back a caller-supplied x-request-id."""
    resp = test_app.get("/ping", headers={"x-request-id": "req-cafebabe"})
    assert resp.headers.get("x-request-id") == "req-cafebabe"


def test_response_time_header_present(test_app) -> None:
    """Middleware must add x-response-time-ms to every response."""
    resp = test_app.get("/ping")
    rtt = resp.headers.get("x-response-time-ms")
    assert rtt is not None
    assert float(rtt) >= 0


def test_unique_correlation_ids_per_request(test_app) -> None:
    """Each request without a provided id should get a unique correlation_id."""
    ids = {test_app.get("/ping").headers["x-request-id"] for _ in range(5)}
    assert len(ids) == 5
