"""The knowledge tool offers the profile's collections, or every readable one, plus those the user referenced, and
only while they exist and the asking user may read them."""

from unittest.mock import MagicMock

from swiss_ai_hub.core.events.agent import KnowledgeReference
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope import KnowledgeToolScope
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_source import KnowledgeToolSource

POLICIES = KnowledgeReference(database="hr", namespace="policies")
REPORTS = KnowledgeReference(database="hr", namespace="reports")
CONTRACTS = KnowledgeReference(database="legal", namespace="contracts")
LIVE = {"hr": ["policies", "reports"], "legal": ["contracts"]}


def _namespaces_of(database: str) -> list[str]:
    return LIVE.get(database, [])


def _access(readable: set[tuple[str, str]]) -> MagicMock:
    access = MagicMock()
    access.has_access_to_knowledge_namespace.side_effect = lambda database, namespace: (database, namespace) in readable
    return access


def _listing(*stores: MilvusVectorStoreConfig, everything: bool = False) -> KnowledgeToolConfig:
    return KnowledgeToolConfig(
        every_readable_collection=everything, sources=[KnowledgeToolSource(vector_store=store) for store in stores]
    )


def _scope(
    config: KnowledgeToolConfig, references: list[KnowledgeReference], access: MagicMock | None
) -> list[KnowledgeReference]:
    return KnowledgeToolScope.collections(
        config, references, access, namespaces_of=_namespaces_of, databases=lambda: list(LIVE)
    )


def test_a_listed_database_offers_the_named_collections_the_user_may_read():
    config = _listing(MilvusVectorStoreConfig(collection_name="hr", index_namespaces=["policies", "reports"]))

    assert _scope(config, [], _access({("hr", "policies")})) == [POLICIES]


def test_a_whole_listed_database_offers_its_live_collections():
    config = _listing(MilvusVectorStoreConfig(collection_name="hr", all_namespaces=True))

    assert _scope(config, [], None) == [POLICIES, REPORTS]


def test_a_listed_collection_that_no_longer_exists_is_not_offered():
    config = _listing(MilvusVectorStoreConfig(collection_name="hr", index_namespaces=["policies", "archive"]))

    assert _scope(config, [], None) == [POLICIES]


def test_every_readable_collection_spans_all_databases():
    access = _access({("hr", "reports"), ("legal", "contracts")})

    assert _scope(_listing(everything=True), [], access) == [REPORTS, CONTRACTS]


def test_every_readable_collection_needs_a_user_to_read_for():
    config = _listing(MilvusVectorStoreConfig(collection_name="legal", all_namespaces=True), everything=True)

    assert _scope(config, [], None) == [CONTRACTS]


def test_referenced_collections_are_offered_on_top_once():
    config = _listing(MilvusVectorStoreConfig(collection_name="hr", index_namespaces=["policies"]))

    assert _scope(config, [POLICIES, CONTRACTS], None) == [POLICIES, CONTRACTS]


def test_a_referenced_collection_the_user_may_not_read_is_not_offered():
    assert _scope(_listing(), [REPORTS], _access({("hr", "policies")})) == []
