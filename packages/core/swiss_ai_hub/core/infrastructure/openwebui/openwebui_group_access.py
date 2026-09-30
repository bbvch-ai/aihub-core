from collections.abc import Callable

from scim2_models import Group

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant

AIHUB_GROUP_PREFIX = "aihub:"

type TenantAccessRules = dict[str, list[str]]
"""Maps tenant name to its access rule strings."""

type RoleAccessRules = dict[tuple[str, str], list[str]]
"""Maps (tenant display name, role name) to that role's access rule strings.

Keyed by the pair because role names are only unique per tenant (index ``(tenant_id, name)``):
the same name (``AIHubUser``, a shared ``TestRole``, …) exists in every tenant with its own rules,
so a name-only key would collapse them and let one tenant's rules mask another's."""


class OpenWebuiGroupAccess:
    """Read grants on an OpenWebUI resource for each of our role groups whose rules allow it.

    Every ``aihub:{tenant}:{role}`` group carries that role's rules under its tenant's ceiling, so a group sees a
    resource in OpenWebUI exactly when a member of the role could open it in our system.
    """

    @staticmethod
    def read_grants(
        groups: list[Group],
        tenant_rules: TenantAccessRules,
        role_rules: RoleAccessRules,
        allows: Callable[[AccessChecker], bool],
    ) -> list[AccessGrant]:
        grants: list[AccessGrant] = []
        for group in groups:
            group_name = group.display_name or ""
            if not group_name.startswith(AIHUB_GROUP_PREFIX):
                continue
            parts = group_name[len(AIHUB_GROUP_PREFIX) :].rsplit(":", 1)
            if len(parts) != 2:
                continue
            tenant_name, role_name = parts
            checker = AccessChecker(
                user_access_rules=role_rules.get((tenant_name, role_name), []),
                tenant_access_rules=tenant_rules.get(tenant_name, []),
            )
            if allows(checker):
                grants.append(AccessGrant(principal_type="group", principal_id=group.id, permission="read"))
        return grants
