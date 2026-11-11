"""Federated-user gate: users who sign in through an identity provider can neither sign in with a password nor reset
one, so a password never stands in for the identity provider's MFA, conditional access or account disabling.

Run with: uv run pytest infra/deployment/tests/test_keycloak_federated_user_gate.py
"""

import json
import re
import sys
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

DEPLOYMENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_DIR))

import generate_compose  # noqa: E402

ENV = Environment(
    loader=FileSystemLoader(DEPLOYMENT_DIR),
    keep_trailing_newline=True,
    autoescape=select_autoescape(),
)
FEDERATED_ROLE = "AIHubFederatedUser"
STAGES = ["dev", "local", "build", "nightly", "latest"]


def _render_realm(stage: str, tmp_path: Path) -> dict:
    context = {"stage": stage, "gpu_enabled": False, **generate_compose.load_config()}
    output_path = tmp_path / f"aihub-realm.{stage}.json"
    generate_compose.generate_keycloak_realm(ENV, context, output_path)
    return json.loads(output_path.read_text(encoding="utf-8"))


def _steps(realm: dict, flow_alias: str) -> list[str]:
    """Authenticator or sub-flow alias of each step of a flow, in execution order."""
    flow = next(flow for flow in realm["authenticationFlows"] if flow["alias"] == flow_alias)
    executions = sorted(flow["authenticationExecutions"], key=lambda execution: execution["priority"])
    return [execution.get("authenticator") or execution["flowAlias"] for execution in executions]


def _denies_federated_users(realm: dict, gate_alias: str) -> bool:
    flow = next(flow for flow in realm["authenticationFlows"] if flow["alias"] == gate_alias)
    condition, deny = sorted(flow["authenticationExecutions"], key=lambda execution: execution["priority"])
    condition_config = next(
        config["config"] for config in realm["authenticatorConfig"] if config["alias"] == condition["authenticatorConfig"]
    )
    return (
        condition["authenticator"] == "conditional-user-role"
        and condition_config == {"condUserRole": FEDERATED_ROLE, "negate": "false"}
        and deny["authenticator"] == "deny-access-authenticator"
    )


@pytest.mark.parametrize("stage", STAGES)
def test_reset_denies_federated_users_after_the_mail_so_the_form_reveals_nothing(stage: str, tmp_path: Path) -> None:
    realm = _render_realm(stage, tmp_path)

    assert realm["resetCredentialsFlow"] == "reset-credentials-aihub"
    assert _steps(realm, "reset-credentials-aihub") == [
        "reset-credentials-choose-user",
        "reset-credential-email",
        "federated-user-gate-reset",
        "reset-password",
        "reset-credentials-aihub-conditional-otp",
    ]
    assert _denies_federated_users(realm, "federated-user-gate-reset")


@pytest.mark.parametrize("stage", STAGES)
def test_password_form_denies_federated_users(stage: str, tmp_path: Path) -> None:
    realm = _render_realm(stage, tmp_path)

    assert _steps(realm, "browser-aihub-forms") == [
        "auth-username-password-form",
        "federated-user-gate-browser",
        "browser-aihub-conditional-2fa",
    ]
    assert _denies_federated_users(realm, "federated-user-gate-browser")


@pytest.mark.parametrize("stage", STAGES)
def test_every_bootstrap_identity_provider_grants_the_federated_role_on_every_sign_in(
    stage: str, tmp_path: Path
) -> None:
    realm = _render_realm(stage, tmp_path)
    federated_mappers = {
        mapper["identityProviderAlias"]: mapper["config"]
        for mapper in realm["identityProviderMappers"]
        if mapper["identityProviderMapper"] == "oidc-hardcoded-role-idp-mapper"
    }

    assert FEDERATED_ROLE in {role["name"] for role in realm["roles"]["realm"]}
    for provider in realm["identityProviders"]:
        assert federated_mappers[provider["alias"]] == {"syncMode": "FORCE", "role": FEDERATED_ROLE}


def test_entrypoint_marks_the_same_role_and_mapper_as_the_realm(tmp_path: Path) -> None:
    """Identity providers added after the first start get the mapper only from the entrypoint."""
    realm = _render_realm("latest", tmp_path)
    context = {"stage": "default", "gpu_enabled": False, **generate_compose.load_config()}
    entrypoint = ENV.get_template("templates/configs/keycloak-entrypoint.sh.j2").render(context)
    mapper_name = next(
        mapper["name"]
        for mapper in realm["identityProviderMappers"]
        if mapper["config"].get("role") == FEDERATED_ROLE
    )

    assert re.search(rf"^FEDERATED_ROLE={FEDERATED_ROLE}$", entrypoint, re.MULTILINE)
    assert re.search(rf"^FEDERATED_MAPPER={mapper_name}$", entrypoint, re.MULTILINE)
    assert "identityProviderMapper=oidc-hardcoded-role-idp-mapper" in entrypoint
    assert "config.syncMode=FORCE" in entrypoint
