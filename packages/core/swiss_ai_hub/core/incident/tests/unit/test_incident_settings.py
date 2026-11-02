import pytest

from swiss_ai_hub.core.incident.incident_settings import IncidentSettings

PEM = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----\n"
ALL_VARIABLES = (
    "INCIDENT_GITHUB_REPOSITORY",
    "INCIDENT_GITHUB_APP_ID",
    "INCIDENT_GITHUB_INSTALLATION_ID",
    "INCIDENT_GITHUB_PRIVATE_KEY",
)


def test_should_be_disabled_when_every_variable_is_passed_through_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """The compose template forwards every INCIDENT_* variable, and an unused one arrives as ''."""
    for name in ALL_VARIABLES:
        monkeypatch.setenv(name, "")

    assert IncidentSettings().enabled is False


def test_should_read_the_private_key_from_a_docker_secret_that_an_empty_env_var_does_not_shadow(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The documented production path: key mounted at /run/secrets, the env file leaving the variable ''."""
    (tmp_path / "incident_github_private_key").write_text(PEM, encoding="utf-8")
    monkeypatch.setenv("INCIDENT_GITHUB_PRIVATE_KEY", "")
    monkeypatch.setenv("INCIDENT_GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("INCIDENT_GITHUB_APP_ID", "1")
    monkeypatch.setenv("INCIDENT_GITHUB_INSTALLATION_ID", "2")

    settings = IncidentSettings(_secrets_dir=str(tmp_path))

    # EnvironmentSettings strips surrounding whitespace from every value, the secret file's trailing newline included.
    assert settings.GITHUB_PRIVATE_KEY == PEM.strip()
    assert settings.enabled is True


def test_should_let_an_explicit_env_var_override_the_secret(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    (tmp_path / "incident_github_private_key").write_text(PEM, encoding="utf-8")
    monkeypatch.setenv("INCIDENT_GITHUB_PRIVATE_KEY", "from-env")

    assert IncidentSettings(_secrets_dir=str(tmp_path)).GITHUB_PRIVATE_KEY == "from-env"
