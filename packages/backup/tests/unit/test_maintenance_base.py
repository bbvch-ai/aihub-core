"""Unit tests for the MaintenanceResult model and MaintenanceHandler ABC."""

from __future__ import annotations

from typing import override

import pytest

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult


@pytest.mark.unit
def test_maintenance_result_defaults_are_sensible() -> None:
    r = MaintenanceResult(name="foo", succeeded=True)
    assert r.duration_seconds == 0.0
    assert r.rows_affected is None
    assert r.error is None
    assert r.metadata == {}


@pytest.mark.unit
def test_maintenance_result_round_trips_via_pydantic() -> None:
    r = MaintenanceResult(
        name="foo",
        succeeded=True,
        duration_seconds=1.5,
        rows_affected=42,
        metadata={"k": "v", "n": 7},
    )
    dumped = r.model_dump()
    restored = MaintenanceResult.model_validate(dumped)
    assert restored == r


@pytest.mark.unit
def test_maintenance_handler_is_abstract() -> None:
    with pytest.raises(TypeError):
        MaintenanceHandler()  # type: ignore[abstract]


@pytest.mark.unit
def test_concrete_handler_implements_run_and_service_name() -> None:
    class _Stub(MaintenanceHandler):
        @property
        @override
        def service_name(self) -> str:
            return "stub"

        @override
        def run(self) -> MaintenanceResult:
            return MaintenanceResult(name="stub", succeeded=True)

    handler = _Stub()
    assert handler.service_name == "stub"
    assert handler.run().succeeded
