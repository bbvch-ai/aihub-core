"""With "Restrict to the user's access" on, a RAG run retrieves only from the collections the asking user may read,
and says so when that leaves nothing to search instead of answering as if the documents had no answer. The asking
user's rules arrive as the injected `AccessChecker`, absent on a run without a user."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.events.agent import CompleteConversationEvent, RAGFailureReason, RAGFailureStopEvent
from swiss_ai_hub.core.generative_ai import EmbeddingModelConfig, KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig

from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.tests.test_task_llm_resolution import _rag_config

RAG_MODULE = "swiss_ai_hub.agent.agents.rag_agent.rag_agent"
HR = KnowledgeRetrieverConfig(
    embed_model=EmbeddingModelConfig(model_name="embedding/test"),
    vector_store=MilvusVectorStoreConfig(collection_name="hr", dimensions=1024, index_namespaces=["policies"]),
    retrieve_k=5,
)


def _config(**overrides) -> RAGAgentConfig:
    return _rag_config(**overrides).model_copy(update={"retrievers": [HR]})


async def _retrieve(config: RAGAgentConfig, access, restricted: list) -> tuple:
    displayer = MagicMock(display_chunk=AsyncMock())
    with (
        patch(f"{RAG_MODULE}.UserScopedRetrievers.narrow", new=AsyncMock(return_value=restricted)) as scope,
        patch(f"{RAG_MODULE}.do_retrieve", new=AsyncMock(return_value="retrieved")) as retrieve,
    ):
        result = await RAGAgent().retrieve_step(
            event=MagicMock(),
            _=MagicMock(),
            start_event=MagicMock(spec=[]),
            agent_config=config,
            displayer=displayer,
            t=LocaleHandler("en"),
            user=None,
            access=access,
        )
    return result, scope, retrieve


@pytest.mark.asyncio
async def test_the_setting_narrows_retrieval_to_what_the_user_may_read():
    narrowed = [MagicMock()]

    result, scope, retrieve = await _retrieve(_config(restrict_to_user_access=True), MagicMock(), narrowed)

    scope.assert_awaited_once()
    assert retrieve.await_args.args[1] is narrowed
    assert result == "retrieved"


@pytest.mark.asyncio
async def test_without_the_setting_retrieval_is_unchanged():
    _, scope, retrieve = await _retrieve(_config(), MagicMock(), [])

    scope.assert_not_awaited()
    assert [c.config for c in retrieve.await_args.args[1]] == [HR]


@pytest.mark.asyncio
async def test_a_run_without_a_user_keeps_the_profile_scope():
    _, scope, retrieve = await _retrieve(_config(restrict_to_user_access=True), None, [])

    scope.assert_not_awaited()
    retrieve.assert_awaited_once()


@pytest.mark.asyncio
async def test_a_user_who_may_read_none_of_it_is_told_so():
    result, _, retrieve = await _retrieve(_config(restrict_to_user_access=True), MagicMock(), [])

    retrieve.assert_not_awaited()
    assert isinstance(result, CompleteConversationEvent)
    assert isinstance(result.stop, RAGFailureStopEvent)
    assert result.stop.reason == RAGFailureReason.NO_ACCESSIBLE_KNOWLEDGE
    assert "not available to you" in result.stop.answer


def test_existing_profiles_keep_it_off_and_new_ones_start_with_it_on():
    assert _config().restrict_to_user_access is False
    assert RAGAgentConfig.as_form().restrict_to_user_access.value is True
    assert ExpertRAGAgentConfig.as_form().restrict_to_user_access.value is True


def test_the_expert_form_offers_every_rag_field_the_rag_form_does():
    rag_form = RAGAgentConfig.as_form()
    expert_form = ExpertRAGAgentConfig.as_form()

    for field in RAGAgentConfig.model_fields:
        assert repr(getattr(expert_form, field)) == repr(getattr(rag_form, field)), field
