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

        # Check for invalid characters
        if not re.fullmatch(r"[a-z0-9\.\-\_\*\>]+", role):
            return False

        parts = role.split('.')
        # '>' must be the last token if it exists
        if '>' in parts and parts[-1] != '>':
            return False

        return True

    @staticmethod
    def _validate_permission_template(template: str) -> bool:
        """
        Ensures a permission template follows the strict format.
        Allows: a-z, 0-9, -, _, ?, ?*, ?>
        Format: aihub.(user|admin).(agent|process)(.[...])*
        """
        if not template.startswith(("aihub.user.", "aihub.admin.")):
            return False

        # Check for invalid characters
        if not re.fullmatch(r"[a-z0-9\.\-\_\?\{\}\*]+", template, re.IGNORECASE):
            return False

        parts = template.split('.')
        # '?>' must be the last token if it exists
        if any('?>' in p for p in parts) and not parts[-1].endswith('?>'):
            return False

        return True

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
        """
        role_parts = user_role.split('.')
        template_parts = implicit_template.split('.')

        if len(role_parts) != len(template_parts):
            # A multi-level wildcard in the template could change this, but for now we keep it simple
            if '?>' not in template_parts and '>' not in role_parts:
                return False

        for i, t_part in enumerate(template_parts):
            if i >= len(role_parts):
                return t_part == '?>'

            r_part = role_parts[i]

            if t_part == '?': # Matches any single token
                continue
            if t_part == '?*': # Matches a '*' token
                if r_part != '*':
                    return False
            elif t_part == '?>': # Matches a '>' token at the end
                return r_part == '>' and i == len(role_parts) - 1
            elif t_part != r_part: # Tokens must otherwise be identical
                return False

        return len(role_parts) == len(template_parts)


    def has_permission(self, permission_template: str) -> bool:
        """
        The main public method to check for permission.
        Orchestrates validation and direct/implicit matching.
        """
        if not self._validate_permission_template(permission_template):
            raise ValueError(f"Invalid permission template format: {permission_template}")

        templates_to_check = {permission_template}
        if permission_template.startswith("aihub.user."):
            admin_equivalent = permission_template.replace("aihub.user.", "aihub.admin.", 1)
            templates_to_check.add(admin_equivalent)

        is_implicit_check = '?' in permission_template

        for user_role in self.valid_roles:
            for template in templates_to_check:
                if is_implicit_check:
                    # Check if the user's role fits the general template
                    if self._role_fulfills_implicit_template(user_role, template):
                        return True
                else:
                    # Check if the user's role grants access to the concrete resource
                    if self._role_matches_concrete_permission(user_role, template):
                        return True
        return False

    def has_access_to_agent(self, agent_class: str, agent_id: str):
        return self.has_permission(f"aihub.user.agent.{agent_class}.{agent_id}")
