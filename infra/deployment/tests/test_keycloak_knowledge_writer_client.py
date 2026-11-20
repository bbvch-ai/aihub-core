"""External knowledge writer: a managed client-credentials client, so keycloak-config-cli keeps it on every deploy
instead of deleting it like a hand-made client, and its tokens pass the API's audience and tenant checks.

Run with: uv run pytest infra/deployment/tests/test_keycloak_knowledge_writer_client.py
"""

import json
import sys
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

DEPLOYMENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DEPLOYMENT_DIR.parents[1]
sys.path.insert(0, str(DEPLOYMENT_DIR))

import generate_compose  # noqa: E402

ENV = Environment(
    loader=FileSystemLoader(DEPLOYMENT_DIR),
    keep_trailing_newline=True,
    autoescape=select_autoescape(),
)
STAGES = ["dev", "local", "build", "nightly", "latest"]
CLIENT_ID_PLACEHOLDER = "$(env:KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_ID)"
SECRET_PLACEHOLDER = "$(env:KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_SECRET)"


def _render_realm(stage: str, tmp_path: Path) -> dict:
    context = {"stage": stage, "gpu_enabled": False, **generate_compose.load_config()}
    output_path = tmp_path / f"aihub-realm.{stage}.json"
    generate_compose.generate_keycloak_realm(ENV, context, output_path)
    return json.loads(output_path.read_text(encoding="utf-8"))


def _knowledge_writer(realm: dict) -> dict:
    return next(client for client in realm["clients"] if client["clientId"] == CLIENT_ID_PLACEHOLDER)


@pytest.mark.parametrize("stage", STAGES)
def test_client_allows_only_client_credentials(stage: str, tmp_path: Path) -> None:
    client = _knowledge_writer(_render_realm(stage, tmp_path))

    assert client["publicClient"] is False
    assert client["serviceAccountsEnabled"] is True
    assert client["standardFlowEnabled"] is False
    assert client["implicitFlowEnabled"] is False
    assert client["directAccessGrantsEnabled"] is False
    assert client["clientAuthenticatorType"] == "client-secret"
    assert client["secret"] == SECRET_PLACEHOLDER


@pytest.mark.parametrize("stage", STAGES)
def test_token_carries_the_tenants_claim_and_the_account_audience(stage: str, tmp_path: Path) -> None:
    realm = _render_realm(stage, tmp_path)
    client = _knowledge_writer(realm)

    assert "tenants" in client["defaultClientScopes"]
    assert "tenants" in {scope["name"] for scope in realm["clientScopes"]}
    audience_mappers = [
        mapper["config"]
        for mapper in client["protocolMappers"]
        if mapper["protocolMapper"] == "oidc-audience-mapper"
    ]
    assert audience_mappers == [
        {"included.client.audience": "account", "id.token.claim": "false", "access.token.claim": "true"}
    ]


@pytest.mark.parametrize("env_file", [".env.dev", ".env.prod"])
def test_env_templates_define_client_id_and_secret(env_file: str) -> None:
    defined = {
        line.split("=", 1)[0]
        for line in (REPO_ROOT / env_file).read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }

    assert {"KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_ID", "KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_SECRET"} <= defined


def test_prod_secret_is_a_generated_placeholder_checked_by_env_guard() -> None:
    assert "KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_SECRET" in generate_compose.env_guard_vars()
