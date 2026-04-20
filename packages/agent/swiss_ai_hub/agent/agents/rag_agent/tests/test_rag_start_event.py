from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, EmbeddingModelConfig, KnowledgeRetrieverConfig
from swiss_ai_hub.core.generative_ai.utils.filter_retrievers_by_namespace import filter_retrievers_by_namespace
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.agents.rag_agent.events.rag_start_event import RAGStartEvent


def _make_user() -> UserIdentity:
    return UserIdentity(id="u1", name="Test User", email="test@example.com", roles=[], tenants=[])


def _make_rag_start_event(
    messages: list[ChatMessage] | None = None,
    namespaces: list[BucketNamespacePair] | None = None,
) -> RAGStartEvent:
    return RAGStartEvent(
        user=_make_user(),
        messages=[ChatMessage(role=MessageRole.USER, content="What is AI?")] if messages is None else messages,
        selected_namespaces=namespaces if namespaces is not None else [],
    )


class TestRAGStartEventProperties:
    def test_user_query_returns_last_user_message_content(self):
        event = _make_rag_start_event(
            messages=[
                ChatMessage(role=MessageRole.USER, content="first question"),
                ChatMessage(role=MessageRole.ASSISTANT, content="answer"),
                ChatMessage(role=MessageRole.USER, content="follow-up"),
            ],
        )
        assert event.user_query == "follow-up"

    def test_user_query_returns_empty_string_when_no_user_messages(self):
        event = _make_rag_start_event(messages=[ChatMessage(role=MessageRole.SYSTEM, content="system")])
        assert event.user_query == ""

    def test_last_user_message_returns_full_chat_message(self):
        msg = ChatMessage(role=MessageRole.USER, content="hello")
        event = _make_rag_start_event(messages=[msg])
        assert event.last_user_message == msg

    def test_last_user_message_fallback_is_empty_user_message(self):
        event = _make_rag_start_event(messages=[])
        result = event.last_user_message
        assert result.role == MessageRole.USER
        assert result.content == ""


class TestNamespaceFilteringBranch:
    """Verifies that the isinstance(start_event, RAGStartEvent) branch filters retrievers."""

    def _make_retrievers(self) -> list[KnowledgeRetrieverConfig]:
        return [
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/test"),
                vector_store=MilvusVectorStoreConfig(
                    collection_name="bucket_a",
                    dimensions=1024,
                ),
                index_namespaces=["ns1", "ns2"],
                retrieve_k=5,
            ),
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/test"),
                vector_store=MilvusVectorStoreConfig(
                    collection_name="bucket_b",
                    dimensions=1024,
                ),
                index_namespaces=["ns3"],
                retrieve_k=5,
            ),
        ]

    def test_rag_start_event_triggers_namespace_filtering(self):
        retrievers = self._make_retrievers()
        start_event = _make_rag_start_event(
            namespaces=[BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
        )

        assert isinstance(start_event, RAGStartEvent)
        filtered = filter_retrievers_by_namespace(retrievers, start_event.selected_namespaces)

        assert len(filtered) == 1
        assert filtered[0].vector_store.collection_name == "bucket_a"
        assert filtered[0].vector_store.index_namespaces == ["ns1"]

    def test_user_message_event_skips_namespace_filtering(self):
        retrievers = self._make_retrievers()
        start_event = UserMessageEvent(
            user=_make_user(),
            messages=[ChatMessage(role=MessageRole.USER, content="hello")],
        )

        assert not isinstance(start_event, RAGStartEvent)
        # UserMessageEvent path uses all retrievers unfiltered
        assert len(retrievers) == 2
