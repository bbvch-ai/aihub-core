"""Unit tests for the Milvus request dependencies.

Milvus answers `/healthz` long before its proxy accepts register, so the client can be missing from
``app.state`` when a request arrives. These tests pin the two behaviours that keep an unready Milvus
from taking the API down: the dependency reconnects instead of returning ``None``, and it degrades to
a 503 on one request instead of propagating out of the process.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from pymilvus.exceptions import MilvusException
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from swiss_ai_hub.core.infrastructure.milvus.use_milvus import use_milvus
from swiss_ai_hub.core.infrastructure.milvus.use_optional_milvus import use_optional_milvus

MILVUS_SETTINGS = {"MILVUS_URL": "http://milvus:19530", "MILVUS_DIMENSION": "1024"}


def _request_with_client(milvus_client: object | None) -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(milvus_client=milvus_client)))


def test_returns_the_client_already_on_app_state():
    existing_client = MagicMock()
    request = _request_with_client(existing_client)

    assert use_milvus(request) is existing_client


def test_connects_and_caches_when_app_state_has_no_client(monkeypatch: pytest.MonkeyPatch):
    """A Milvus that was unreachable at startup must be picked up by the next request."""
    for key, value in MILVUS_SETTINGS.items():
        monkeypatch.setenv(key, value)
    request = _request_with_client(None)
    reconnected_client = MagicMock()

    with patch(
        "swiss_ai_hub.core.infrastructure.milvus.use_milvus.MilvusClient", return_value=reconnected_client
    ) as milvus_client_cls:
        assert use_milvus(request) is reconnected_client
        assert use_milvus(request) is reconnected_client

    assert request.app.state.milvus_client is reconnected_client
    milvus_client_cls.assert_called_once()


def test_raises_503_when_milvus_is_unreachable(monkeypatch: pytest.MonkeyPatch):
    """The connection failure must stay inside the request, not escape as a process-level error."""
    for key, value in MILVUS_SETTINGS.items():
        monkeypatch.setenv(key, value)
    request = _request_with_client(None)

    with (
        patch(
            "swiss_ai_hub.core.infrastructure.milvus.use_milvus.MilvusClient",
            side_effect=MilvusException(message="Milvus Proxy is not ready yet"),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        use_milvus(request)

    assert raised.value.status_code == HTTP_503_SERVICE_UNAVAILABLE
    assert request.app.state.milvus_client is None


def test_optional_dependency_reports_unreachable_milvus_as_no_client(monkeypatch: pytest.MonkeyPatch):
    """Readiness must keep reporting the other dependencies instead of failing on Milvus alone."""
    for key, value in MILVUS_SETTINGS.items():
        monkeypatch.setenv(key, value)
    request = _request_with_client(None)

    with patch(
        "swiss_ai_hub.core.infrastructure.milvus.use_milvus.MilvusClient",
        side_effect=MilvusException(message="Milvus Proxy is not ready yet"),
    ):
        assert use_optional_milvus(request) is None


def test_raises_503_when_the_driver_fails_outside_milvus_exception(monkeypatch: pytest.MonkeyPatch):
    """pymilvus re-raises the codes in its IGNORE_RETRY_CODES set as bare `grpc.RpcError`.

    An UNAUTHENTICATED from a token mismatch therefore never reaches the caller as a
    `MilvusException`, and must still degrade to a 503 instead of a 500.
    """
    for key, value in MILVUS_SETTINGS.items():
        monkeypatch.setenv(key, value)
    request = _request_with_client(None)

    with (
        patch(
            "swiss_ai_hub.core.infrastructure.milvus.use_milvus.MilvusClient",
            side_effect=RuntimeError("StatusCode.UNAUTHENTICATED, auth check failure"),
        ),
        pytest.raises(HTTPException) as raised,
    ):
        use_milvus(request)

    assert raised.value.status_code == HTTP_503_SERVICE_UNAVAILABLE
    assert request.app.state.milvus_client is None


def test_optional_dependency_tolerates_a_failure_outside_milvus_exception(monkeypatch: pytest.MonkeyPatch):
    """Readiness must report `milvus: false` for a bare `grpc.RpcError` too, not fail the whole report."""
    for key, value in MILVUS_SETTINGS.items():
        monkeypatch.setenv(key, value)
    request = _request_with_client(None)

    with patch(
        "swiss_ai_hub.core.infrastructure.milvus.use_milvus.MilvusClient",
        side_effect=RuntimeError("StatusCode.UNAUTHENTICATED, auth check failure"),
    ):
        assert use_optional_milvus(request) is None
