"""Unit tests for the SQLAlchemy engine builder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr
from sqlalchemy.engine import URL

from swiss_ai_hub.backup.maintenance.postgres_engine import build_dagster_engine
from swiss_ai_hub.backup.settings import BackupSettings


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_engine.create_engine")
def test_build_dagster_engine_passes_url_object(mock_create_engine: MagicMock, settings: BackupSettings) -> None:
    """create_engine receives a URL object, not a hand-built string. URL.create
    handles credential escaping; f-string interpolation does not."""
    settings.POSTGRES_HOST = "custom-postgres"
    settings.POSTGRES_PORT = 6543
    settings.DAGSTER_DB = "my_dagster_db"

    build_dagster_engine(settings)

    assert mock_create_engine.call_count == 1
    args, _ = mock_create_engine.call_args
    url = args[0]
    assert isinstance(url, URL)
    assert url.host == "custom-postgres"
    assert url.port == 6543
    assert url.database == "my_dagster_db"
    assert url.username == settings.POSTGRES_USER
    assert url.drivername == "postgresql+psycopg"


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
    assert args[0].drivername == "postgresql+psycopg"


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_engine.create_engine")
def test_build_dagster_engine_escapes_url_reserved_chars_in_password(
    mock_create_engine: MagicMock,
    settings: BackupSettings,
) -> None:
    """Regression guard: passwords with @, :, /, #, ? must not break URL parsing.

    f-string interpolation (the previous implementation) would silently produce
    a malformed URL for any of these characters; URL.create() escapes them
    correctly when the URL is rendered.
    """
    nasty_password = "p@ss:word/with#reserved?chars"
    settings.POSTGRES_PASSWORD = SecretStr(nasty_password)

    build_dagster_engine(settings)

    args, _ = mock_create_engine.call_args
    url = args[0]
    # URL stores the password unescaped on the object — escaping happens at render time.
    assert url.password == nasty_password
    # render_as_string with hide_password=False produces the percent-encoded form.
    rendered = url.render_as_string(hide_password=False)
    assert "p%40ss%3Aword%2Fwith%23reserved%3Fchars" in rendered
