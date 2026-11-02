from collections.abc import Callable

from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.events.agent import KnowledgeReference
from swiss_ai_hub.core.generative_ai import UserScopedRetrievers
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.knowledge.narrowed_knowledge_scope import NarrowedKnowledgeScope


class KnowledgeToolScope:
    """The collections the knowledge tool offers in one run: the profile's, or every readable one, plus those the
    user referenced, each only while it exists and the asking user may read it.

    "Every readable collection" needs someone to read for, so a run without a user is offered only what the
    profile lists.
    """

    @staticmethod
    def collections(
        config: KnowledgeToolConfig,
        references: list[KnowledgeReference],
        access: AccessChecker | None,
        namespaces_of: Callable[[str], list[str]] | None = None,
        databases: Callable[[], list[str]] | None = None,
    ) -> list[KnowledgeReference]:
        namespaces_of = namespaces_of or UserScopedRetrievers.namespaces_of
        everything = config.every_readable_collection and access is not None
        candidates = [
            *(
                KnowledgeToolScope._all(namespaces_of, databases or KnowledgeToolScope.live_databases)
                if everything
                else KnowledgeToolScope._listed(config, namespaces_of)
            ),
            *(reference for reference in references if reference.namespace in namespaces_of(reference.database)),
        ]
        unique = list({(reference.database, reference.namespace): reference for reference in candidates}.values())
        if access is None:
            return unique
        return [
            reference
            for reference in unique
            if access.has_access_to_knowledge_namespace(reference.database, reference.namespace)
        ]

    @staticmethod
    def narrowed_collections(
        config: KnowledgeToolConfig,
        references: list[KnowledgeReference],
        access: AccessChecker | None,
        namespaces_of: Callable[[str], list[str]] | None = None,
        databases: Callable[[], list[str]] | None = None,
    ) -> NarrowedKnowledgeScope:
        """The profile's collections, cut down to the referenced ones when the user referenced any, for blueprints
        whose profile is the hard boundary of what a run may touch: a reference can pick among the profile's
        collections but never add one. References that pick nothing are ignored, so a run never ends up with no
        collection only because the user named one the profile does not list."""
        configured = KnowledgeToolScope.collections(config, [], access, namespaces_of, databases)
        picked = [reference for reference in configured if reference in references]
        return NarrowedKnowledgeScope(
            collections=picked or configured,
            ignored=[reference for reference in references if reference not in configured],
        )

    @staticmethod
    def live_databases() -> list[str]:
        return [bucket.db_name for bucket in BucketEntity.get_all_buckets() if not bucket.deleting]

    @staticmethod
    def _listed(config: KnowledgeToolConfig, namespaces_of: Callable[[str], list[str]]) -> list[KnowledgeReference]:
        listed = []
        for source in config.sources:
            store = source.vector_store
            live = namespaces_of(store.collection_name)
            chosen = live if store.all_namespaces else [ns for ns in store.index_namespaces if ns in live]
            listed.extend(KnowledgeReference(database=store.collection_name, namespace=ns) for ns in chosen)
        return listed

    @staticmethod
    def _all(namespaces_of: Callable[[str], list[str]], databases: Callable[[], list[str]]) -> list[KnowledgeReference]:
        return [
            KnowledgeReference(database=database, namespace=namespace)
            for database in databases()
            for namespace in namespaces_of(database)
        ]
