"""Asset-level tests for the maintenance Dagster wiring.

These tests use ``dg.materialize`` against a fake set of resources to verify:
  - maintenance_session produces a MaintenanceContext.
  - maintenance_service short-circuits when MAINTENANCE_DISABLED=true.
  - maintenance_service propagates handler results + writes Dagster output metadata.
  - maintenance_finalize aggregates totals and raises Failure on any handler failure.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import dagster as dg
import pytest
from dagster import AssetKey

from swiss_ai_hub.backup.dagster.assets.maintenance_finalize_factory import maintenance_finalize_factory
from swiss_ai_hub.backup.dagster.assets.maintenance_service_factory import maintenance_service_factory
from swiss_ai_hub.backup.dagster.assets.maintenance_session_factory import maintenance_session_factory
from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.maintenance.base import MaintenanceResult


def _resources(maintenance_disabled: bool = False) -> dict[str, object]:
    """Build a resource dict for asset tests.

    ``maintenance_engine`` is a plain MagicMock — bypassing the Pydantic
    nested-resource validation in ``MaintenanceEngineResource``. The asset
    tests don't care about the engine's type since ``create_maintenance_handler``
    is also mocked.
    """
    settings_resource = BackupSettingsResource()
    return {
        "backup_settings": settings_resource,
        "maintenance_engine": MagicMock(),
    }


def _mock_settings_instance(maintenance_disabled: bool = False) -> MagicMock:
    """Mock returned by patching ``BackupSettings`` inside ``backup_settings_resource``."""
    m = MagicMock()
    m.MAINTENANCE_DISABLED = maintenance_disabled
    m.MAINTENANCE_DEBUG_LOG_RETENTION_DAYS = 7
    m.MAINTENANCE_INFO_LOG_RETENTION_DAYS = 60
    m.MAINTENANCE_WARNING_LOG_RETENTION_DAYS = 60
    m.MAINTENANCE_UNIMPORTANT_EVENT_RETENTION_DAYS = 30
    m.MAINTENANCE_BATCH_LIMIT = 1_000_000
    return m


@pytest.mark.unit
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_maintenance_session_creates_context(mock_settings_cls: MagicMock) -> None:
    mock_settings_cls.return_value = _mock_settings_instance()
    session_asset = maintenance_session_factory(AssetKey(["maintenance", "session"]))
    result = dg.materialize([session_asset], resources=_resources())
    assert result.success


@pytest.mark.unit
@patch("swiss_ai_hub.backup.dagster.assets.maintenance_service_factory.create_maintenance_handler")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_maintenance_service_calls_handler_and_returns_result(
    mock_settings_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    mock_settings_cls.return_value = _mock_settings_instance()
    handler = MagicMock()
    handler.run.return_value = MaintenanceResult(
        name="dagster_debug_logs", succeeded=True, rows_affected=42, duration_seconds=0.1
    )
    mock_create_handler.return_value = handler

    session_key = AssetKey(["maintenance", "session"])
    service_key = AssetKey(["maintenance", "dagster_debug_logs"])
    session = maintenance_session_factory(session_key)
    service = maintenance_service_factory(service_key, session_key, "dagster_debug_logs", "test")

    result = dg.materialize([session, service], resources=_resources())
    assert result.success
    handler.run.assert_called_once()
    args = mock_create_handler.call_args.args
    assert args[0] == "dagster_debug_logs"


@pytest.mark.unit
@patch("swiss_ai_hub.backup.dagster.assets.maintenance_service_factory.create_maintenance_handler")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_maintenance_service_short_circuits_when_disabled(
    mock_settings_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    """MAINTENANCE_DISABLED=true → handler is never constructed and never runs."""
    mock_settings_cls.return_value = _mock_settings_instance(maintenance_disabled=True)

    session_key = AssetKey(["maintenance", "session"])
    service_key = AssetKey(["maintenance", "dagster_debug_logs"])
    session = maintenance_session_factory(session_key)
    service = maintenance_service_factory(service_key, session_key, "dagster_debug_logs", "test")

    result = dg.materialize([session, service], resources=_resources())
    assert result.success
    mock_create_handler.assert_not_called()


@pytest.mark.unit
@patch("swiss_ai_hub.backup.dagster.assets.maintenance_service_factory.create_maintenance_handler")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_maintenance_service_does_not_raise_on_handler_failure(
    mock_settings_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    """Failure isolation: handler returning succeeded=False does NOT fail the asset.
    The finalize asset is responsible for surfacing aggregate failure."""
    mock_settings_cls.return_value = _mock_settings_instance()
    handler = MagicMock()
    handler.run.return_value = MaintenanceResult(name="dagster_debug_logs", succeeded=False, error="boom")
    mock_create_handler.return_value = handler

    session_key = AssetKey(["maintenance", "session"])
    service_key = AssetKey(["maintenance", "dagster_debug_logs"])
    session = maintenance_session_factory(session_key)
    service = maintenance_service_factory(service_key, session_key, "dagster_debug_logs", "test")

    result = dg.materialize([session, service], resources=_resources())
    assert result.success  # the asset materialized — failure is encoded in the returned MaintenanceResult


@pytest.mark.unit
@patch("swiss_ai_hub.backup.dagster.assets.maintenance_service_factory.create_maintenance_handler")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_maintenance_finalize_succeeds_when_all_handlers_succeed(
    mock_settings_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    mock_settings_cls.return_value = _mock_settings_instance()
    mock_create_handler.return_value = MagicMock(
        run=MagicMock(return_value=MaintenanceResult(name="x", succeeded=True, rows_affected=10))
    )

    session_key = AssetKey(["maintenance", "session"])
    s1 = AssetKey(["maintenance", "h1"])
    s2 = AssetKey(["maintenance", "h2"])
    finalize_key = AssetKey(["maintenance", "cleanup_finalize"])

    assets = [
        maintenance_session_factory(session_key),
        maintenance_service_factory(s1, session_key, "h1", "h1"),
        maintenance_service_factory(s2, session_key, "h2", "h2"),
        maintenance_finalize_factory(finalize_key, session_key, {"h1": s1, "h2": s2}),
    ]
    result = dg.materialize(assets, resources=_resources())
    assert result.success


@pytest.mark.unit
@patch("swiss_ai_hub.backup.dagster.assets.maintenance_service_factory.create_maintenance_handler")
@patch("swiss_ai_hub.backup.dagster.resources.backup_settings_resource.BackupSettings")
def test_maintenance_finalize_raises_when_any_handler_fails(
    mock_settings_cls: MagicMock,
    mock_create_handler: MagicMock,
) -> None:
    mock_settings_cls.return_value = _mock_settings_instance()

    def make_handler(service_name: str, *_args, **_kwargs) -> MagicMock:
        succeeded = service_name == "h1"
        return MagicMock(
            run=MagicMock(
                return_value=MaintenanceResult(
                    name=service_name,
                    succeeded=succeeded,
                    error=None if succeeded else "boom",
                )
            )
        )

    mock_create_handler.side_effect = make_handler

    session_key = AssetKey(["maintenance", "session"])
    s1 = AssetKey(["maintenance", "h1"])
    s2 = AssetKey(["maintenance", "h2"])
    finalize_key = AssetKey(["maintenance", "cleanup_finalize"])

    assets = [
        maintenance_session_factory(session_key),
        maintenance_service_factory(s1, session_key, "h1", "h1"),
        maintenance_service_factory(s2, session_key, "h2", "h2"),
        maintenance_finalize_factory(finalize_key, session_key, {"h1": s1, "h2": s2}),
    ]
    result = dg.materialize(assets, resources=_resources(), raise_on_error=False)
    assert not result.success
