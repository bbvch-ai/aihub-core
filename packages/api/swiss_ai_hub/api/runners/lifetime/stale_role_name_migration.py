from datetime import UTC, datetime

from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity


class StaleRoleNameMigration:
    """Removes from every user the role names that no longer match a role in their tenant.

    Users hold roles by name, and deleting a role used to leave its name on every user that had it. Such a name grants
    nothing until a role with the same name is created again, which then reaches every former holder without anyone
    assigning it. Deleting a role now strips the name; this removes the names left behind before.
    """

    @staticmethod
    def run() -> list[str]:
        """Strips the names without a role; returns the users it rewrote and the names it removed."""
        existing_roles = {(role.tenant_id, role.name) for role in RoleEntity.objects()}
        migrated: list[str] = []
        for assignment in UserTenantRoleEntity.objects():
            kept = [name for name in assignment.roles if (assignment.tenant_id, name) in existing_roles]
            if len(kept) == len(assignment.roles):
                continue
            removed = sorted(set(assignment.roles) - set(kept))
            assignment.roles = kept
            assignment.updated_at = datetime.now(UTC)
            assignment.save()
            migrated.append(f"user {assignment.user_id} in tenant {assignment.tenant_id} ({', '.join(removed)})")
        return migrated
