from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity


class KnowledgeRootRuleMigration:
    """Adds the bare ``aihub.admin.knowledge`` root to every ``AIHubKnowledgeAdmin`` role that still lacks it.

    Creating a knowledge database is guarded on the root, which ``aihub.admin.knowledge.>`` does not match, and the
    role was seeded with only the wildcard before that guard existed. Only the default role is touched, and only while
    it still holds the wildcard: a custom role never could create a database, and one narrowed to named databases was
    narrowed on purpose.
    """

    ROLE_NAME = "AIHubKnowledgeAdmin"
    ROOT = f"{AccessChecker.ADMIN_PREFIX}knowledge"
    WILDCARD = f"{AccessChecker.ADMIN_PREFIX}knowledge.>"

    @staticmethod
    def run() -> list[str]:
        """Adds the root where it is missing; returns the roles it rewrote."""
        migrated: list[str] = []
        for role in RoleEntity.objects(
            name=KnowledgeRootRuleMigration.ROLE_NAME, access_rules=KnowledgeRootRuleMigration.WILDCARD
        ):
            if KnowledgeRootRuleMigration.ROOT not in role.access_rules:
                role.access_rules = [*role.access_rules, KnowledgeRootRuleMigration.ROOT]
                role.save()
                migrated.append(f"role {role.name} ({role.tenant_id})")
        return migrated
