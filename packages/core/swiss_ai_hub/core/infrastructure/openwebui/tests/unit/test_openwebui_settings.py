import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings


def _settings(**overrides: str) -> OpenWebuiSettings:
    base: dict[str, str] = {
        "BASE_URL": "http://open-webui:8080",
        "SECRET_KEY": "sk-test",
        "SCIM_TOKEN": "scim-test",
        "WEBHOOK_SECRET": "webhook-test",
        "SERVICE_ACCOUNT_ID": "00000000-0000-4000-a000-000000000001",
    }
    base.update(overrides)
    return OpenWebuiSettings(**base)


class TestModelNameLocale:
    def test_default_is_en(self) -> None:
        assert _settings().MODEL_NAME_LOCALE == "en"

    @pytest.mark.parametrize("value", ["", "   "])
    def test_blank_locale_falls_back_to_en(self, value: str) -> None:
        assert _settings(MODEL_NAME_LOCALE=value).MODEL_NAME_LOCALE == "en"

    def test_valid_locale_preserved(self) -> None:
        assert _settings(MODEL_NAME_LOCALE="fr").MODEL_NAME_LOCALE == "fr"

    def test_unsupported_locale_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _settings(MODEL_NAME_LOCALE="xx")
