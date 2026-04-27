"""Unit tests for the SQLAlchemy engine builder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.maintenance.postgres_engine import build_dagster_engine
from swiss_ai_hub.backup.settings import BackupSettings


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_engine.create_engine")
def test_build_dagster_engine_constructs_url_from_maintenance_settings(
    mock_create_engine: MagicMock, settings: BackupSettings
) -> None:
    """Engine targets MAINTENANCE_POSTGRES_HOST/PORT, not POSTGRES_HOST directly.

    They default to the same value but the indirection lets operators override
    the connection (e.g., bypass pgbouncer) without touching backup config.
    """
    settings.MAINTENANCE_POSTGRES_HOST = "custom-postgres"
    settings.MAINTENANCE_POSTGRES_PORT = 6543
    settings.MAINTENANCE_DAGSTER_DB = "my_dagster_db"

    build_dagster_engine(settings)

    assert mock_create_engine.call_count == 1
    args, kwargs = mock_create_engine.call_args
    url = args[0]
    assert "custom-postgres" in url
    assert ":6543/" in url
    assert "/my_dagster_db" in url
    assert settings.POSTGRES_USER in url


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_engine.create_engine")
def test_build_dagster_engine_uses_null_pool(mock_create_engine: MagicMock, settings: BackupSettings) -> None:
    """NullPool — maintenance runs are infrequent; pooling adds zero value."""
    from sqlalchemy.pool import NullPool

    build_dagster_engine(settings)
    _, kwargs = mock_create_engine.call_args
    assert kwargs["poolclass"] is NullPool


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_engine.create_engine")
def test_build_dagster_engine_sets_application_name(mock_create_engine: MagicMock, settings: BackupSettings) -> None:
    """application_name lets DBAs identify our connections in pg_stat_activity."""
    build_dagster_engine(settings)
    _, kwargs = mock_create_engine.call_args
    assert kwargs["connect_args"]["application_name"] == "swiss-ai-hub-maintenance"


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_engine.create_engine")
def test_build_dagster_engine_uses_psycopg_driver(mock_create_engine: MagicMock, settings: BackupSettings) -> None:
    """URL must use postgresql+psycopg, not generic postgresql:// (which would pick psycopg2)."""
    build_dagster_engine(settings)
    args, _ = mock_create_engine.call_args
    assert args[0].startswith("postgresql+psycopg://")
