from datetime import UTC, datetime

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity


class ProcessRootRuleMigration:
    """Adds the bare ``aihub.admin.process`` root next to every ``aihub.admin.process.>`` it finds.

    Creating a process instance is now guarded on the root, which ``process.>`` does not match: a ``>`` needs at
    least one more token. Tenants and roles holding only the wildcard could create instances before, so without
    this they would lose that on upgrade. Adding the root widens nothing, as the wildcard already reached every
    instance. The wildcard itself is left in place: the platform cannot tell which instances a tenant built.
    """

    WILDCARD = f"{AccessChecker.ADMIN_PREFIX}process.>"

    @staticmethod
    def run() -> list[str]:
        """Adds the root where it is missing; returns the tenants and roles it rewrote."""
        root = AccessChecker.process_root_admin_rule()
        migrated: list[str] = []
        for tenant in TenantMetadataEntity.objects(access_rules=ProcessRootRuleMigration.WILDCARD):
            if root not in tenant.access_rules:
                tenant.access_rules = [*tenant.access_rules, root]
                tenant.updated_at = datetime.now(UTC)
                tenant.save()
                migrated.append(f"tenant {tenant.id}")
        for role in RoleEntity.objects(access_rules=ProcessRootRuleMigration.WILDCARD):
            if root not in role.access_rules:
                role.access_rules = [*role.access_rules, root]
                role.save()
                migrated.append(f"role {role.name} ({role.tenant_id})")
        return migrated
