"""The aihub login theme links to AI Hub from pages Keycloak leaves without a link, such as "Account updated" after an
admin-console invitation, which names no application to return to.

Run with: uv run pytest infra/deployment/tests/test_keycloak_theme_aihub_link.py
"""

import sys
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

DEPLOYMENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_DIR))

import generate_compose  # noqa: E402

ENV = Environment(
    loader=FileSystemLoader(DEPLOYMENT_DIR),
    keep_trailing_newline=True,
    autoescape=select_autoescape(),
)
THEME_TEMPLATES = DEPLOYMENT_DIR / "templates" / "configs"
INFRA_DIR = DEPLOYMENT_DIR.parent


def _keycloak_environment(stage: str) -> dict:
    """Reads the generated compose file; CI's compose consistency check keeps it equal to the template's output."""
    compose = yaml.safe_load((INFRA_DIR / f"docker-compose.{stage}.yml").read_text(encoding="utf-8"))
    return compose["services"]["keycloak"]["environment"]


def test_theme_reads_the_ai_hub_address_from_the_environment() -> None:
    properties = ENV.get_template("templates/configs/keycloak-theme-properties.j2").render({})

    assert "aihubUrl=${env.AIHUB_FRONTEND_ORIGIN}" in properties.splitlines()


def test_dev_keycloak_links_to_the_locally_running_ai_hub() -> None:
    assert _keycloak_environment("dev")["AIHUB_FRONTEND_ORIGIN"] == "${AIHUB_FRONTEND_ORIGIN}"


@pytest.mark.parametrize("stage", ["local", "build", "nightly", "latest"])
def test_deployed_keycloak_links_to_the_ai_hub_of_its_own_domain(stage: str) -> None:
    assert _keycloak_environment(stage)["AIHUB_FRONTEND_ORIGIN"] == "https://${DOMAIN}"


def test_info_page_shows_the_ai_hub_link_only_where_keycloak_shows_none() -> None:
    info = (THEME_TEMPLATES / "keycloak-theme-info.ftl").read_text(encoding="utf-8")
    form_section = info.split('<#elseif section = "form">', 1)[1]
    branches = [line.strip() for line in form_section.splitlines() if line.strip().startswith(("<#if ", "<#elseif "))]
    branches = [branch for branch in branches if "requiredActions" not in branch]

    assert branches[-1] == "<#elseif aihubUrl?has_content>"
    assert all(branch.startswith(("<#if !skipLink??", "<#elseif !skipLink??")) for branch in branches[:-1])


def test_a_realm_specific_address_wins_over_the_keycloak_wide_one() -> None:
    """One Keycloak hosting several AI Hubs (a realm each, as on Kubernetes) needs a link per realm."""
    info = (THEME_TEMPLATES / "keycloak-theme-info.ftl").read_text(encoding="utf-8")

    assert '<#assign aihubUrl = properties["aihubUrl." + realm.name]!properties.aihubUrl!"">' in info


def test_theme_files_are_published_into_the_mounted_theme_directory() -> None:
    copies = {(src, dst, name) for src, dst, name in generate_compose.STATIC_COPY_FILES}

    assert ("templates/configs/keycloak-theme-info.ftl", "configs/keycloak/themes/aihub/login", "info.ftl") in copies
    assert (
        "templates/configs/keycloak-theme-messages_en.properties",
        "configs/keycloak/themes/aihub/login/messages",
        "messages_en.properties",
    ) in copies
