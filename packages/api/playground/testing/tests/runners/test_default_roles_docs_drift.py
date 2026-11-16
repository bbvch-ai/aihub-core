import re
from pathlib import Path

from swiss_ai_hub.core.infrastructure import UserSignupSettings

from swiss_ai_hub.api.runners.lifetime.initialize_db import _DEFAULT_ROLE_DEFINITIONS

DEFAULT_ROLES_PAGE = Path(__file__).parents[6] / "docs/docs/2_platform/11_access_management/3_default_roles/index.en.md"


def _documented_roles() -> dict[str, set[str]]:
    """Reads the default-roles table: a row whose first cell is a backticked role name and whose second lists rules."""
    roles: dict[str, set[str]] = {}
    for line in DEFAULT_ROLES_PAGE.read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 3 and re.fullmatch(r"`AIHub\w+`", cells[0]) and cells[1].startswith("`aihub."):
            roles[cells[0].strip("`")] = set(re.findall(r"`([^`]+)`", cells[1]))
    return roles


def _documented_default(variable: str) -> str:
    match = re.search(rf"^{variable}='([^']*)'$", DEFAULT_ROLES_PAGE.read_text(), re.MULTILINE)
    assert match, f"{variable} default is not shown on {DEFAULT_ROLES_PAGE.name}"
    return match.group(1)


class TestDefaultRolesPageMatchesCode:
    """Fails when a default role or signup default changes without the operator page; run /sync-role-docs to fix."""

    def test_lists_exactly_the_seeded_roles(self):
        assert set(_documented_roles()) == {role.name for role in _DEFAULT_ROLE_DEFINITIONS}

    def test_lists_each_roles_access_rules(self):
        documented = _documented_roles()
        for role in _DEFAULT_ROLE_DEFINITIONS:
            assert documented.get(role.name) == set(role.access_rules), role.name

    def test_shows_the_signup_role_defaults(self):
        fields = UserSignupSettings.model_fields
        assert _documented_default("AIHUB_USER_SIGNUP_REGULAR_USER_ROLES") == fields["REGULAR_USER_ROLES"].default
        assert (
            _documented_default("AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES") == fields["FIRST_ADMIN_USER_ROLES"].default
        )
