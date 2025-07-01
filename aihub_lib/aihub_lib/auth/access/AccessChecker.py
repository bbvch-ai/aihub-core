import re
from typing import List, Set

from aihub_lib.auth.identity.UserIdentity import UserIdentity

# aihub.admin.>
# aihub.admin.process.>
# aihub.admin.process.{process_class}.{process_name}
# aihub.admin.process.{process_class}.{process_name}
# aihub.admin.process.*.{process_name}
# aihub.admin.process.{process_class}.*
# aihub.admin.process.*.*
# aihub.admin.agent.>
# aihub.admin.agent.{agent_class}.{agent_name}
# aihub.admin.agent.{agent_class}.{agent_name}
# aihub.admin.agent.*.{agent_name}
# aihub.admin.agent.{agent_class}.*
# aihub.admin.agent.*.*

# aihub.user.>
# aihub.user.process.>
# aihub.user.process.{process_class}.{process_name}
# aihub.user.process.{process_class}.{process_name}
# aihub.user.process.*.{process_name}
# aihub.user.process.{process_class}.*
# aihub.user.process.*.*
# aihub.user.agent.>
# aihub.user.agent.{agent_class}.{agent_name}
# aihub.user.agent.{agent_class}.{agent_name}
# aihub.user.agent.*.{agent_name}
# aihub.user.agent.{agent_class}.*# aihub.user.agent.*.*


class AccessChecker:
    """
    Performs authorization checks based on a user's hierarchical roles.

    This class supports two types of checks:
    1.  Direct Check: Verifies if a user can access a specific, concrete resource.
        - User Role: `aihub.user.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.id_123` -> Match!

    2.  Implicit Check: Verifies if a user has *any* role that fits a general pattern.
        This uses the '?' wildcard in the permission template.
        - User Role: `aihub.user.agent.class_a.*`
        - Permission Template: `aihub.user.agent.class_a.?*` -> Match!
        - Permission Template: `aihub.user.agent.?>` -> Match!
    """

    def __init__(self, user: UserIdentity):
        self.user = user
        # Validate and filter roles once upon initialization.
        self.valid_roles = self._get_validated_roles(user.roles)

    @staticmethod
    def _validate_user_role(role: str) -> bool:
        """
        Ensures a user role follows the strict format.
        Allows: a-z, 0-9, -, _, *, >
        Format: aihub.(user|admin).(agent|process)(.[...])*
        """
        if not role.startswith(("aihub.user.", "aihub.admin.")):
            return False

        if not re.fullmatch(r"[a-z0-9\.\-\_\*\>]+", role):
            return False

        parts = role.split('.')
        # '>' must be the last token if it exists
        if '>' in parts and parts[-1] != '>':
            return False

        return True

    @staticmethod
    def _validate_permission_template(template: str):
        """
        Ensures a permission template follows the strict format.
        Raises ValueError if the format is invalid.
        """
        if not template.startswith(("aihub.user.", "aihub.admin.")):
            raise ValueError(f"Invalid permission template: Must start with 'aihub.user.' or 'aihub.admin.'. Got: {template}")

        parts = template.split('.')
        for part in parts:
            is_valid_token = re.fullmatch(r"[a-z0-9\-\_]+", part, re.IGNORECASE)
            is_special_wildcard = part in ['?', '?*', '?>']
            if not (is_valid_token or is_special_wildcard):
                raise ValueError(f"Invalid permission template: Contains invalid token '{part}' in '{template}'")

        if '?>' in parts and parts[-1] != '?>':
            raise ValueError(f"Invalid permission template: '?>' must be the last token. Got: {template}")


    def _get_validated_roles(self, roles: List[str]) -> Set[str]:
        """Filters and validates the user's roles."""
        validated = set()
        for role in roles:
            if self._validate_user_role(role):
                validated.add(role)
        return validated

    def _role_matches_concrete_permission(self, user_role: str, concrete_permission: str) -> bool:
        """
        Checks if a user role (with * or >) matches a specific permission string.
        This is the classic NATS-style topic match.
        """
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
        """
        Checks if a user role fulfills a permission template containing '?' wildcards.
        The '?' acts as a placeholder for *any* valid token/permission at that level.
        """
        role_parts = user_role.split('.')
        template_parts = implicit_template.split('.')

        for i, t_part in enumerate(template_parts):
            # If template ends in '?>', it's fulfilled if the role has any token(s) beyond this point.
            if t_part == '?>':
                # The prefix of the role and template must match.
                if role_parts[:i] != template_parts[:i]:
                    return False
                # The role must simply have tokens at or after this position.
                return len(role_parts) > i

            if i >= len(role_parts):
                return False

            r_part = role_parts[i]

            # '?' and '?*' are fulfilled by the existence of any valid token at this position.
            if t_part in ['?', '?*']:
                continue
            # Otherwise, the tokens must be identical.
            elif t_part != r_part:
                return False

        # If we finished the loop without '?>', lengths must match exactly.
        return len(role_parts) == len(template_parts)


    def has_permission(self, permission_template: str) -> bool:
        """
        The main public method to check for permission.
        Orchestrates validation and direct/implicit matching.
        """
        self._validate_permission_template(permission_template)

        templates_to_check = {permission_template}
        if permission_template.startswith("aihub.user."):
            admin_equivalent = permission_template.replace("aihub.user.", "aihub.admin.", 1)
            templates_to_check.add(admin_equivalent)

        is_implicit_check = '?' in permission_template

        for user_role in self.valid_roles:
            for template in templates_to_check:
                # Route to the correct matching logic
                if is_implicit_check:
                    if self._role_fulfills_implicit_template(user_role, template):
                        return True
                else:
                    if self._role_matches_concrete_permission(user_role, template):
                        return True
        return False

    def has_access_to_agent(self, agent_class: str, agent_id: str):
        return self.has_permission(f"aihub.user.agent.{agent_class}.{agent_id}")