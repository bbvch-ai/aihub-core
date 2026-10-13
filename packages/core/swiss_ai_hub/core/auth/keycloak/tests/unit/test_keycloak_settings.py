import pytest

from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings


def _settings_with_welcome_page(monkeypatch: pytest.MonkeyPatch, value: str) -> KeycloakSettings:
    monkeypatch.setenv("KEYCLOAK_LOGIN_WELCOME_PAGE", value)
    return KeycloakSettings(URL="http://keycloak:8080")


def test_login_welcome_page_is_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KEYCLOAK_LOGIN_WELCOME_PAGE", raising=False)

    assert KeycloakSettings(URL="http://keycloak:8080").LOGIN_WELCOME_PAGE is False


def test_login_welcome_page_empty_value_is_off(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _settings_with_welcome_page(monkeypatch, "").LOGIN_WELCOME_PAGE is False


def test_login_welcome_page_turns_on(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _settings_with_welcome_page(monkeypatch, "true").LOGIN_WELCOME_PAGE is True
