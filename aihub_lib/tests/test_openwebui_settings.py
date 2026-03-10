"""Tests for OpenWebuiSettings."""

import pytest
from pydantic import SecretStr, ValidationError

from aihub_lib.infrastructure.openwebui.OpenWebuiSettings import OpenWebuiSettings


class TestOpenWebuiSettings:
    def test_settings_load_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENWEBUI_BASE_URL", "http://open-webui:8080")
        monkeypatch.setenv("OPENWEBUI_SECRET_KEY", "sk-test-key")
        monkeypatch.setenv("OPENWEBUI_SCIM_TOKEN", "scim-test-token")

        settings = OpenWebuiSettings()

        assert settings.BASE_URL == "http://open-webui:8080"
        assert settings.SECRET_KEY.get_secret_value() == "sk-test-key"

    def test_settings_missing_required_fields_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENWEBUI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENWEBUI_SECRET_KEY", raising=False)
        monkeypatch.delenv("OPENWEBUI_SCIM_TOKEN", raising=False)

        with pytest.raises(ValidationError):
            OpenWebuiSettings(_env_file=None)

    def test_secret_key_is_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENWEBUI_BASE_URL", "http://open-webui:8080")
        monkeypatch.setenv("OPENWEBUI_SECRET_KEY", "sk-secret-key")
        monkeypatch.setenv("OPENWEBUI_SCIM_TOKEN", "scim-test-token")

        settings = OpenWebuiSettings()

        assert isinstance(settings.SECRET_KEY, SecretStr)
        assert "sk-secret-key" not in repr(settings)
