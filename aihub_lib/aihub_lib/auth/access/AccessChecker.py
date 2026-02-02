import re

from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity


class AccessChecker:
    """
    Performs authorization checks based on a user's hierarchical access rules.

    This class supports two types of checks:
    1.  Direct Check: Verifies if a user can access a specific, concrete resource.
        - User Access Rule: `aihub.user.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.id_123` -> Match!

    2.  Implicit Check: Verifies if a user has *any* access rule that fits a general pattern.
        This uses the '?*' or '?>' wildcards in the permission template.
        - User Access Rule: `aihub.user.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.?*` -> Match!
        - Permission Template: `aihub.user.agent.?>` -> Match!

    3.  Admin Check: aihub.admin are automatically also aihub.user. To differentiate whether a user accessing an
        endpoint has user or admin privilege, we use AccessLevel.ACCESS_ADMIN or AccessLevel.ACCESS_USER.
        Note that an admin accessing an endpoint requiring user privileges will still enter the endpoint
        with AccessLevel.ACCESS_ADMIN
        - User Access Rule: `aihub.admin.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.?*` -> Match, user will enter with AccessLevel.ACCESS_ADMIN
    """

    def __init__(self, user_access_rules: list[str]):
        self.valid_access_rules = self._get_validated_access_rules(user_access_rules)
        self.admin_access_rules = {r for r in self.valid_access_rules if r.startswith("aihub.admin.")}
        self.user_access_rules = {r for r in self.valid_access_rules if r.startswith("aihub.user.")}

    @property
    def access_rules(self):
        return self.valid_access_rules

    @classmethod
    def from_user(cls, user: UserIdentity):
        user_access_rules = RoleEntity.get_access_rules_for_roles(user.roles)
        return cls(user_access_rules=list(user_access_rules))

    @staticmethod
    def validate_user_access_rule(access_rule: str) -> bool:
        """Ensures a users access_rules follows the strict format."""
        if not access_rule.startswith(("aihub.user.", "aihub.admin.")):
            return False
        if not re.fullmatch(r"[a-z0-9\.\-\_\*\>]+", access_rule):
            return False
        parts = access_rule.split(".")
        if ">" in parts and parts[-1] != ">":
            return False
        return True

    @staticmethod
    def validate_permission_template(template: str):
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

    def _get_validated_access_rules(self, access_rules: list[str]) -> set[str]:
        """Filters and validates the user's access_rules."""
        validated = set()
        for access_rule in access_rules:
            if self.validate_user_access_rule(access_rule):
                validated.add(access_rule)
        return validated

    def _access_rule_matches_concrete_permission(self, user_access_rule: str, concrete_permission: str) -> bool:
        """Checks if a users access rule (with * or >) matches a specific permission string."""
        access_rule_parts = user_access_rule.split(".")
        permission_parts = concrete_permission.split(".")
        for i, part in enumerate(access_rule_parts):
            if part == ">":
                return i < len(permission_parts)
            if i >= len(permission_parts):
                return False
            if part != "*" and part != permission_parts[i]:
                return False
        return len(access_rule_parts) == len(permission_parts)

    def _access_rule_fulfills_implicit_template(self, access_rule: str, implicit_template: str) -> bool:
        """Checks if a users access rule fulfills a permission template with '?*' or '?>'."""
        access_rule_parts = access_rule.split(".")
        template_parts = implicit_template.split(".")
        ti, ri = 0, 0
        while ti < len(template_parts) and ri < len(access_rule_parts):
            t_part, r_part = template_parts[ti], access_rule_parts[ri]
            if r_part == ">":
                return ti < len(template_parts)
            if t_part == "?>":
                return ri < len(access_rule_parts)
            if r_part == "*" or t_part == "?*":
                ti, ri = ti + 1, ri + 1
                continue
            if r_part != t_part:
                return False
            ti, ri = ti + 1, ri + 1
        if ri < len(access_rule_parts) and access_rule_parts[ri] == ">":
            return True
        return ri == len(access_rule_parts) and ti == len(template_parts)

    def access_level(self, permission_template: str) -> AccessLevel:
        """
        Checks for the highest level of permission (Admin, User, or Denied).
        It orchestrates validation and matching, prioritizing admin access.
        """
        self.validate_permission_template(permission_template)
        is_implicit_check = "?" in permission_template
        match_func = (
            self._access_rule_fulfills_implicit_template
            if is_implicit_check
            else self._access_rule_matches_concrete_permission
        )

        # 1. Check for Admin access (admins implicitly have user-access as well)
        admin_perm_to_check = permission_template.replace("aihub.user.", "aihub.admin.", 1)
        for access_rule in self.admin_access_rules:
            if match_func(access_rule, admin_perm_to_check):
                return AccessLevel.ACCESS_ADMIN

        # 2. Check for User access (only if permission is user-level)
        if permission_template.startswith("aihub.user."):
            for access_rule in self.user_access_rules:
                if match_func(access_rule, permission_template):
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

    def access_level_for_service(self, service_name) -> AccessLevel:
        """Convenience method to check access level for a specific service."""
        return self.access_level(f"aihub.user.service.{service_name}")

    def has_access_to_service(self, service_name) -> bool:
        """Convenience method to check access level for a specific service."""
        return self.access_level_for_service(service_name) != AccessLevel.ACCESS_DENIED
