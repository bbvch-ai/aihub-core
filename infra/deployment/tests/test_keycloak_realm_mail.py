"""Realm mail server: the realm import leaves it empty and the entrypoint writes it to every realm.

Run with: uv run pytest infra/deployment/tests/test_keycloak_realm_mail.py
"""

import json
import sys
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

DEPLOYMENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_DIR))

import generate_compose  # noqa: E402

# select_autoescape only escapes .html/.htm/.xml templates; the .j2 templates rendered here stay unescaped,
# exactly as generate_compose.py renders them.
ENV = Environment(
    loader=FileSystemLoader(DEPLOYMENT_DIR),
    keep_trailing_newline=True,
    autoescape=select_autoescape(),
)


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
def test_realm_import_leaves_the_mail_server_to_the_entrypoint(stage: str, tmp_path: Path) -> None:
    """Keycloak rejects the whole import when the sender address is invalid, as it is with an unset variable."""
    assert _render_realm(stage, tmp_path)["smtpServer"] == {}


def test_entrypoint_sends_through_microsoft_365_from_the_configured_mailbox_with_a_vault_secret() -> None:
    smtp_server = _entrypoint_smtp_document()["smtpServer"]

    assert smtp_server["host"] == "smtp.office365.com"
    assert smtp_server["authType"] == "token"
    assert smtp_server["from"] == "$(env:KEYCLOAK_SMTP_MAILBOX)"
    assert smtp_server["user"] == "$(env:KEYCLOAK_SMTP_MAILBOX)"
    assert smtp_server["authTokenClientSecret"] == "${vault.smtp-client-secret}"
    assert "password" not in smtp_server
