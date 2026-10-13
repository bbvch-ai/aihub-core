"""Collections a user references are searched only while they exist and the user may read them, each database with
the embedding model it was indexed with."""

from unittest.mock import MagicMock, patch

from mongoengine import DoesNotExist

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.generative_ai.retrievers.referenced_knowledge import ReferencedKnowledge

MODULE = "swiss_ai_hub.core.generative_ai.retrievers.referenced_knowledge"


def _reference(database: str, namespace: str) -> KnowledgeReference:
    return KnowledgeReference(database=database, namespace=namespace)


def _access(readable: set[tuple[str, str]]) -> MagicMock:
    access = MagicMock()
    access.has_access_to_knowledge_namespace.side_effect = lambda database, namespace: (database, namespace) in readable
    return access


def _namespaces(database: str) -> list[str]:
    return {"hr": ["policies", "reports"], "legal": ["contracts"]}.get(database, [])


def test_readable_live_collections_are_searched_and_the_rest_refused():
    references = [_reference("hr", "policies"), _reference("hr", "reports"), _reference("hr", "gone")]

    searchable, refused = ReferencedKnowledge.partition(references, _access({("hr", "policies")}), _namespaces)

    assert searchable == [_reference("hr", "policies")]
    assert refused == [_reference("hr", "reports"), _reference("hr", "gone")]


def test_a_run_without_a_user_searches_every_live_reference():
    references = [_reference("hr", "reports"), _reference("vanished", "x")]

    searchable, refused = ReferencedKnowledge.partition(references, None, _namespaces)

    assert searchable == [_reference("hr", "reports")]
    assert refused == [_reference("vanished", "x")]


def test_a_collection_referenced_twice_is_searched_once():
    references = [_reference("hr", "policies"), _reference("hr", "policies")]

    searchable, _ = ReferencedKnowledge.partition(references, None, _namespaces)

    assert searchable == [_reference("hr", "policies")]


def test_one_retriever_per_database_with_its_own_embedding_model():
    references = [_reference("hr", "policies"), _reference("legal", "contracts"), _reference("hr", "reports")]
    models = {"hr": "embedding/bge-m3", "legal": "embedding/qwen3"}

    with patch.object(ReferencedKnowledge, "embedding_model_of", side_effect=models.get):
        retrievers = ReferencedKnowledge.retrievers(references, retrieve_k=7)

    shapes = [
        (r.config.vector_store.collection_name, r.config.vector_store.index_namespaces, r.config.embed_model.model_name)
        for r in retrievers
    ]
    assert shapes == [("hr", ["policies", "reports"], "embedding/bge-m3"), ("legal", ["contracts"], "embedding/qwen3")]
    assert {r.config.retrieve_k for r in retrievers} == {7}


def test_the_embedding_model_is_the_one_the_database_was_created_with():
    bucket = MagicMock(configuration={"embedding_model": "embedding/qwen3"})

    with patch(f"{MODULE}.BucketEntity.get_bucket_by_db_name", return_value=bucket):
        assert ReferencedKnowledge.embedding_model_of("legal") == "embedding/qwen3"


def test_a_database_without_a_stored_model_uses_the_deployment_default():
    with (
        patch(f"{MODULE}.BucketEntity.get_bucket_by_db_name", side_effect=DoesNotExist),
        patch(
            f"{MODULE}.DocumentIngestionPipelineSettings", return_value=MagicMock(EMBEDDING_MODEL="embedding/default")
        ),
    ):
        assert ReferencedKnowledge.embedding_model_of("old") == "embedding/default"
