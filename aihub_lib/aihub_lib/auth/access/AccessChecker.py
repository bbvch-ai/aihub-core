import re
from typing import List, Set

from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.identity.UserIdentity import UserIdentity


class AccessChecker:
    """
    Performs authorization checks based on a user's hierarchical roles.

    This class supports two types of checks:
    1.  Direct Check: Verifies if a user can access a specific, concrete resource.
        - User Role: `aihub.user.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.id_123` -> Match!

    2.  Implicit Check: Verifies if a user has *any* role that fits a general pattern.
        This uses the '?*' or '?>' wildcards in the permission template.
        - User Role: `aihub.user.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.?*` -> Match!
        - Permission Template: `aihub.user.agent.?>` -> Match!
    """

    def __init__(self, user_roles: List[str]):
        self.valid_roles = self._get_validated_roles(user_roles)
        self.admin_roles = {r for r in self.valid_roles if r.startswith("aihub.admin.")}
        self.user_roles = {r for r in self.valid_roles if r.startswith("aihub.user.")}

    @classmethod
    def from_user(cls, user: UserIdentity):
        return cls(user_roles=user.roles)

    @staticmethod
    def _validate_user_role(role: str) -> bool:
        """Ensures a user role follows the strict format."""
        if not role.startswith(("aihub.user.", "aihub.admin.")):
            return False
        if not re.fullmatch(r"[a-z0-9\.\-\_\*\>]+", role):
            return False
        parts = role.split(".")
        if ">" in parts and parts[-1] != ">":
            return False
        return True

    @staticmethod
    def _validate_permission_template(template: str):
        """Ensures a permission template follows the strict format."""
        if not template.startswith(("aihub.user.", "aihub.admin.")):
            raise ValueError(
                f"Invalid permission template: Must start with 'aihub.user.' or 'aihub.admin.'. Got: {template}"
            )
        parts = template.split(".")
        for part in parts:
            is_valid_token = re.fullmatch(r"[a-z0-9\-\_]+", part, re.IGNORECASE)
            is_special_wildcard = part in ["?*", "?>"]
            if not (is_valid_token or is_special_wildcard):
                raise ValueError(f"Invalid permission template: Contains invalid token '{part}' in '{template}'")
        if "?>" in parts and parts[-1] != "?>":
            raise ValueError(f"Invalid permission template: '?>' must be the last token. Got: {template}")

    def _get_validated_roles(self, roles: List[str]) -> Set[str]:
        """Filters and validates the user's roles."""
        validated = set()
        for role in roles:
            if self._validate_user_role(role):
                validated.add(role)
        return validated

    def _role_matches_concrete_permission(self, user_role: str, concrete_permission: str) -> bool:
        """Checks if a user role (with * or >) matches a specific permission string."""
        role_parts = user_role.split(".")
        permission_parts = concrete_permission.split(".")
        for i, part in enumerate(role_parts):
            if part == ">":
                return i < len(permission_parts)
            if i >= len(permission_parts):
                return False
            if part != "*" and part != permission_parts[i]:
                return False
        return len(role_parts) == len(permission_parts)

    def _role_fulfills_implicit_template(self, user_role: str, implicit_template: str) -> bool:
        """Checks if a user role fulfills a permission template with '?*' or '?>'."""
        role_parts = user_role.split(".")
        template_parts = implicit_template.split(".")
        ti, ri = 0, 0
        while ti < len(template_parts) and ri < len(role_parts):
            t_part, r_part = template_parts[ti], role_parts[ri]
            if r_part == ">":
                return ti < len(template_parts)
            if t_part == "?>":
                return ri < len(role_parts)
            if r_part == "*" or t_part == "?*":
                ti, ri = ti + 1, ri + 1
                continue
            if r_part != t_part:
                return False
            ti, ri = ti + 1, ri + 1
        if ri < len(role_parts) and role_parts[ri] == ">":
            return True
        return ri == len(role_parts) and ti == len(template_parts)

    def access_level(self, permission_template: str) -> AccessLevel:
        """
        Checks for the highest level of permission (Admin, User, or Denied).
        It orchestrates validation and matching, prioritizing admin access.
        """
        self._validate_permission_template(permission_template)
        is_implicit_check = "?" in permission_template
        match_func = (
            self._role_fulfills_implicit_template if is_implicit_check else self._role_matches_concrete_permission
        )

        # 1. Check for Admin access
        admin_perm_to_check = permission_template.replace("aihub.user.", "aihub.admin.", 1)
        for role in self.admin_roles:
            if match_func(role, admin_perm_to_check):
                return AccessLevel.ACCESS_ADMIN

        # 2. Check for User access (only if permission is user-level)
        if permission_template.startswith("aihub.user."):
            for role in self.user_roles:
                if match_func(role, permission_template):
                    return AccessLevel.ACCESS_USER

        # 3. Default to Denied
        return AccessLevel.ACCESS_DENIED

    def has_access(self, permission_template: str) -> bool:
        """Convenience method to check if a user has access to a specific resource."""
        return self.access_level(permission_template) != AccessLevel.ACCESS_DENIED

    def access_level_for_agent(self, agent_class: str, agent_id: str) -> AccessLevel:
        """Convenience method to check access level for a specific agent."""
        return self.access_level(f"aihub.user.agent.{agent_class}.{agent_id}")

    def has_access_to_agent(self, agent_class: str, agent_id: str) -> bool:
        """Convenience method to check access level for a specific agent."""
        return self.access_level_for_agent(agent_class, agent_id) != AccessLevel.ACCESS_DENIED

    def has_access_to_agent_class(self, agent_class: str) -> bool:
        """Convenience method to check access level for a specific agent."""
        return self.access_level(f"aihub.user.agent.{agent_class}.?*") != AccessLevel.ACCESS_DENIED

    def access_level_for_process(self, process_class: str, process_id: str) -> AccessLevel:
        """Convenience method to check access level for a specific process."""
        return self.access_level(f"aihub.user.process.{process_class}.{process_id}")

    def has_access_to_process(self, process_class: str, process_id: str) -> bool:
        """Convenience method to check access level for a specific process."""
        return self.access_level_for_process(process_class, process_id) != AccessLevel.ACCESS_DENIED

    def has_access_to_process_class(self, process_class: str) -> bool:
        """Convenience method to check access level for a specific process."""
        return self.access_level(f"aihub.user.process.{process_class}.?*") != AccessLevel.ACCESS_DENIED
