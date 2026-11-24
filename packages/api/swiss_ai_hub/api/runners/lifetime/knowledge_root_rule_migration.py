from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity


class KnowledgeRootRuleMigration:
    """Adds ``aihub.admin.knowledge`` to every ``AIHubKnowledgeAdmin`` role still exactly as seeded before v0.321.0.

    Creating a knowledge database is guarded on that root, which ``aihub.admin.knowledge.>`` does not match, and the
    role used to be seeded without it. This runs on every start, so only a role still holding exactly the old seeded
    rules is touched: any other set was edited by an admin, who may have left the root out on purpose
    (aihub-core-private#401).

    One edit cannot be told apart from the seeded state: removing the root from a role that was seeded before v0.321.0
    and otherwise left alone. That role gets the root back at every start until this migration is deleted, which is
    why it is meant to live for one release only.
    """

    ROLE_NAME = "AIHubKnowledgeAdmin"
    ROOT = f"{AccessChecker.ADMIN_PREFIX}knowledge"
    SEEDED_BEFORE_ROOT = frozenset({f"{AccessChecker.ADMIN_PREFIX}agent.>", f"{AccessChecker.ADMIN_PREFIX}knowledge.>"})

    @staticmethod
    def run() -> list[str]:
        """Adds the root to the roles still as seeded before it existed; returns the roles it rewrote."""
        migrated: list[str] = []
        for role in RoleEntity.objects(name=KnowledgeRootRuleMigration.ROLE_NAME):
            if set(role.access_rules) == KnowledgeRootRuleMigration.SEEDED_BEFORE_ROOT:
                role.access_rules = [*role.access_rules, KnowledgeRootRuleMigration.ROOT]
                role.save()
                migrated.append(f"role {role.name} ({role.tenant_id})")
        return migrated
