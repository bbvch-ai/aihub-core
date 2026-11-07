"""Realm mail server rendered by generate_compose.py into the realm import file and into the
entrypoint's default migration for existing realms.

Run with: uv run pytest infra/deployment/tests/test_keycloak_realm_mail.py
"""

import json
import sys
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

DEPLOYMENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_DIR))

import generate_compose  # noqa: E402

ENV = Environment(loader=FileSystemLoader(DEPLOYMENT_DIR), keep_trailing_newline=True)


def _render_realm(stage: str, tmp_path: Path) -> dict:
    context = {"stage": stage, "gpu_enabled": False, **generate_compose.load_config()}
    output_path = tmp_path / f"aihub-realm.{stage}.json"
    generate_compose.generate_keycloak_realm(ENV, context, output_path)
    return json.loads(output_path.read_text(encoding="utf-8"))


def _entrypoint_smtp_document() -> dict:
    """The JSON the entrypoint writes to existing realms; it is rendered once for all stages."""
    context = {"stage": "default", "gpu_enabled": False, **generate_compose.load_config()}
    rendered = ENV.get_template("templates/configs/keycloak-entrypoint.sh.j2").render(context)
    heredoc = rendered.split("<< 'SMTP_EOF'\n", 1)[1].split("\nSMTP_EOF\n", 1)[0]
    return json.loads(heredoc)


@pytest.mark.parametrize("stage", ["dev", "local", "build", "nightly", "latest"])
def test_realm_sends_through_microsoft_365_with_a_vault_secret(stage: str, tmp_path: Path) -> None:
    smtp_server = _render_realm(stage, tmp_path)["smtpServer"]

    assert smtp_server["host"] == "smtp.office365.com"
    assert smtp_server["authType"] == "token"
    assert smtp_server["from"] == "noreply.ai-hub@bbv.ch"
    assert smtp_server["authTokenClientSecret"] == "${vault.smtp-client-secret}"
    assert "password" not in smtp_server


def test_existing_realms_get_the_same_mail_server_as_new_ones(tmp_path: Path) -> None:
    assert _entrypoint_smtp_document() == {"smtpServer": _render_realm("latest", tmp_path)["smtpServer"]}
