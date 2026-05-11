# ruff: noqa: E402
from swiss_ai_hub.core.generative_ai import KnowledgeRetrieverConfig

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pytest_bdd import given, parsers, scenario, scenarios, then, when
from swiss_ai_hub.core.events.agent import (
    AddMemoryToChatHistoryEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    RAGSuccessStopEvent,
    RerankerEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    StandaloneQuestionCondenserEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    FewShotGuardExample,
    LLMConfig,
    ModeOptions,
    RerankingModelConfig,
    RetrievePrevNextConfig,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig, create_mongo_document_store
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.testing.milvus_vector_store_content import drop_collection, fill_collection

from swiss_ai_hub.agent.agents.rag_agent.configs.memory_config import MemoryConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.events.limit_chat_history_with_context_event import (
    LimitChatHistoryWithContextEvent,
)
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)

enable_logging()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Load all scenarios
scenarios("./features/rag_agent.feature")


@scenario("features/rag_agent.feature", "Test RAGAgent with multi-language system prompt")
def test_test_ragagent_with_multilanguage_system_prompt():
    """Test RAGAgent with multi-language system prompts."""
    pass


@scenario("features/rag_agent.feature", "Test RAGAgent with valid self hosted configuration")
def test_test_ragagent_with_valid_self_hosted_configuration():
    """Test RAGAgent with valid self hosted configuration."""
    pass


@scenario("features/rag_agent.feature", "Test RAGAgent with reranking enabled")
def test_test_ragagent_with_reranking_enabled():
    """Test RAGAgent with reranking enabled."""
    pass


@scenario(
    "features/rag_agent.feature", "Test RAGAgent retrieves organization memory alongside knowledge base documents"
)
def test_test_ragagent_retrieves_organization_memory_alongside_knowledge_base_documents():
    """Test RAGAgent with organization memory."""
    pass


load_dotenv(Path(__file__).parent / ".env")


def build_rag_agent_config(
    llm_config,
    reranking_config,
    embedding_config,
    vector_store,
    query_mode: VectorStoreQueryMode,
) -> RAGAgentConfig:
    """
    Build a fully populated RAGAgentConfig with the specified LLM, embedding, and vector store configuration.

    We keep the entire parameter list intact to avoid partial Pydantic construction.
    """
    return RAGAgentConfig(
        agent_id="rag_agent",
        name=LocaleString(en="RAG Agent"),
        description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
        llm=llm_config,
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
                retrieve_k=5,
                query_mode=query_mode,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode=ModeOptions.BOTH,
                ),
            ),
        ],
        number_of_input_tokens=8192,
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=False),
        reranking_config=RerankingConfig(enabled=False, reranking_model=reranking_config),
    )


def build_rag_agent_config_with_memory(
    llm_config,
    reranking_config,
    embedding_config,
    vector_store,
    query_mode: VectorStoreQueryMode,
    tenant_id: str = "test_tenant",
    tenant_namespace: str = "default",
) -> RAGAgentConfig:
    """
    Build a RAGAgentConfig with both knowledge retrievers AND organization memory enabled.
    """
    return RAGAgentConfig(
        agent_id="rag_agent_with_memory",
        name=LocaleString(en="RAG Agent with Memory"),
        description=LocaleString(en="Agent with organization memory enabled for testing"),
        llm=llm_config,
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
                retrieve_k=5,
                query_mode=query_mode,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode=ModeOptions.BOTH,
                ),
            ),
        ],
        number_of_input_tokens=8192,
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=False),
        reranking_config=RerankingConfig(enabled=False, reranking_model=reranking_config),
        memory=MemoryConfig(
            enable_organization_memory=True,
            tenant_id=tenant_id,
            tenant_namespace=tenant_namespace,
        ),
    )


@pytest.fixture(scope="session")
def test_collection(event_loop):
    """
    Set up and tear down the test collection for all tests.
    """
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="development",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="development")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield

    drop_collection()


@pytest.fixture(scope="session")
def memory_enabled_agent_config(test_collection):
    """
    Return a RAGAgentConfig with organization memory enabled.

    This configuration enables the agent to retrieve organization memories
    in addition to knowledge base documents.
    """
    llm_config = LLMConfig(model_name="text-generation/gpt-oss-120b")
    reranking_config = RerankingModelConfig(model_name="reranker/bge")
    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        collection_name="development",
        index_namespaces=["ai_knowledge"],
        dimensions=1024,
    )

    return build_rag_agent_config_with_memory(
        llm_config=llm_config,
        reranking_config=reranking_config,
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
        tenant_id="test_tenant",
        tenant_namespace="default",
    )


@pytest.fixture(scope="session")
def self_hosted_agent_config(test_collection):
    """
    Return a RAGAgentConfig that uses a self-hosted LLM and self-hosted embeddings.
    """
    llm_config = LLMConfig(model_name="text-generation/gpt-oss-120b")
    reranking_config = RerankingModelConfig(model_name="reranker/bge")
    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        collection_name="development",
        index_namespaces=["ai_knowledge"],
        dimensions=1024,
    )

    return build_rag_agent_config(
        llm_config=llm_config,
        reranking_config=reranking_config,
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
    )


@given(parsers.parse('check_context_sufficiency set to "{flag}" and max_hops to "{max_hops:d}"'))
def _(flag: bool, max_hops: int, agent_runner: AgentTestRunner):
    agent_runner.agent_config.context_sufficient_guard.check_context_sufficiency = flag
    agent_runner.agent_config.context_sufficient_guard.max_hops = max_hops


@pytest.mark.usefixtures("self_hosted_agent_config")
@given("a RAGAgent runner with a valid self hosted configuration", target_fixture="agent_runner")
def _(self_hosted_agent_config):
    """
    Given a RAGAgent runner with a valid self-hosted configuration.
    """
    return AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=self_hosted_agent_config,
    )


@when(parsers.parse('the start event is sent with a user query "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=fake_user(),
                locale="en",
            ),
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then("a LimitChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.get_event_of_class(LimitChatHistoryEvent), "Agent did not produce LimitChatHistoryEvent"


@then(parsers.parse("a StandaloneQuestionCondenserEvent is present with condensed question"))
def _(agent_runner: AgentTestRunner):
    condenser_event = agent_runner.get_event_of_class(StandaloneQuestionCondenserEvent)
    assert condenser_event.condensed_chat_message.content, "No condensed question found"


@then("a RetrieverEvent is present with retrieved nodes")
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    assert retriever_event.nodes, "RetrieverEvent did not produce nodes"


@then(parsers.parse('a RetrieverEvent is present with more than "{node_count:d}" retrieved nodes'))
def _(agent_runner: AgentTestRunner, node_count: int):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    nodes = len(retriever_event.nodes)
    assert nodes > node_count, f"Expected more than {node_count} nodes, got {nodes}"


@then(parsers.parse('"{count:d}" RetrieverEvent are present'))
def _(count: int, agent_runner: AgentTestRunner):
    retriever_events = len(agent_runner.get_events_of_class(RetrieverEvent, True))
    assert retriever_events == count, f"Expected {count} RetrieverEvents, got {retriever_events}"


@then("an InOrderNodeCombinerEvent is present with ordered context message")
def _(agent_runner: AgentTestRunner):
    combiner_event = agent_runner.get_event_of_class(InOrderNodeCombinerEvent)
    assert combiner_event.context_message, "InOrderNodeCombinerEvent did not produce context message"


@then("a LimitChatHistoryWithContextEvent is present with limited history and context")
def _(agent_runner: AgentTestRunner):
    history_event = agent_runner.get_event_of_class(LimitChatHistoryWithContextEvent)
    assert history_event.limited_history_with_context, "LimitChatHistoryWithContextEvent missing data"


@then("an LLMEvent is present with a generated response")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    assert llm_event, "LLMEvent not produced"


@then("the response contains a detailed explanation")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    assert "detailed" in llm_event.response.content.lower(), "Response does not contain a detailed explanation"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce StopEvent"


@then("a RAGSuccessStopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(RAGSuccessStopEvent), (
        "RAGAgent should emit RAGSuccessStopEvent when no reject events were emitted"
    )


@given("with few shot guard examples")
def _(agent_runner: AgentTestRunner, datatable):
    """
    Given few shot guard examples provided as a table.
    The table should have columns: 'user' and 'agent'
    """
    examples = []
    for row in datatable[1:]:
        examples.append(
            FewShotGuardExample(user=LocaleString(en=row[0]), success=row[1], reason=LocaleString(en=row[2]))
        )
    agent_runner.agent_config.few_shot_guard_examples = examples
    return agent_runner


@when(parsers.parse('the start event is sent with a user query "{query}" and locale {locale}'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str, locale: str):
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                locale=locale,
                user=fake_user(),
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
            ),
        )


@then("the few shot guard should reject the user query")
def _(agent_runner: AgentTestRunner):
    event = agent_runner.get_event_of_class(FewShotRejectEvent)
    assert event is not None, "FewShotRejectEvent was not produced for an invalid user query"


@then("the few shot guard should accept the user query")
def _(agent_runner: AgentTestRunner):
    event = agent_runner.get_event_of_class(FewShotAcceptEvent)
    assert event is not None, "FewShotAcceptEvent was not produced for a valid user query"


@then("respond to the user with the reasoning for the rejection")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    input_messages = llm_event.input_messages
    for msg in input_messages:
        if msg.role == MessageRole.SYSTEM:
            assert "reason" in msg.content.lower(), "The llm does not receive the rejection reasoning"
    response_content = llm_event.output_messages[0].content
    assert response_content, "No response was returned for a rejected user query"


@then("respond to the user with a generated response")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    response_content = llm_event.output_messages[0].content
    assert response_content, "No generated response was returned for a valid user query"


@given("with multi-language system prompt")
def _(agent_runner: AgentTestRunner, datatable):
    """
    Given multi-language system prompt provided as a table.
    The table should have columns: 'locale' and 'prompt'
    """
    prompts = {}
    for row in datatable[1:]:
        locale = row[0]
        prompt = row[1]
        prompts[locale] = prompt

    agent_runner.agent_config.system_prompt = LocaleString(**prompts)
    return agent_runner


@given(parsers.parse('with multi-language system prompt for locale {locale} and prompt "{prompt}"'))
def _(agent_runner: AgentTestRunner, locale: str, prompt: str):
    """
    Given multi-language system prompt for a specific locale and prompt.
    Used for parameterized Scenario Outline with Examples.
    """
    agent_runner.agent_config.system_prompt = LocaleString(**{locale: prompt})
    return agent_runner


@then(parsers.parse('the LLM received the system prompt "{expected_prompt}"'))
def _(agent_runner: AgentTestRunner, expected_prompt: str):
    config = agent_runner.agent_config
    assert config.system_prompt is not None, "System prompt was not configured"

    start_event = agent_runner.get_start_event()
    locale = start_event.locale

    actual_prompt = config.system_prompt.in_locale(locale)
    assert actual_prompt == expected_prompt, f"Expected system prompt '{expected_prompt}', got '{actual_prompt}'"


@given(parsers.parse('with reranking enabled and top_n of "{top_n:d}"'))
def _(agent_runner: AgentTestRunner, top_n: int):
    agent_runner.agent_config.reranking_config = RerankingConfig(
        enabled=True, reranking_model=RerankingModelConfig(model_name="reranker/bge", top_n=top_n)
    )
    return agent_runner


@given("with reranking disabled")
def _(agent_runner: AgentTestRunner):
    agent_runner.agent_config.reranking_config = RerankingConfig(
        enabled=False,
    )
    return agent_runner


@then("a RerankerEvent is present with reranked nodes")
def _(agent_runner: AgentTestRunner):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not produced"
    assert reranker_event.output_nodes, "RerankerEvent did not contain reranked nodes"


@then("a RerankerEvent is present without reranking")
def _(agent_runner: AgentTestRunner):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not produced"
    assert len(reranker_event.input_nodes) == len(reranker_event.output_nodes), (
        "Pass-through mode should preserve all nodes"
    )


@then("the RerankerEvent contains the original nodes from the RetrieverEvent")
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)

    assert retriever_event, "RetrieverEvent was not found"
    assert reranker_event, "RerankerEvent was not found"

    retriever_node_ids = [node.node.node_id for node in retriever_event.nodes]
    reranker_node_ids = [node.node.node_id for node in reranker_event.output_nodes]

    assert retriever_node_ids == reranker_node_ids, "Node IDs should match in pass-through mode"


@then(parsers.parse('the RerankerEvent should limit results to "{top_n:d}" nodes'))
def _(agent_runner: AgentTestRunner, top_n: int):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not found"
    assert len(reranker_event.output_nodes) <= top_n, (
        f"Expected at most {top_n} nodes, got {len(reranker_event.output_nodes)}"
    )


@then(parsers.parse('the RerankerEvent model name should be "{model_name}"'))
def _(agent_runner: AgentTestRunner, model_name: str):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not found"
    assert reranker_event.rerank_model_name == model_name, (
        f"Expected model {model_name}, got {reranker_event.rerank_model_name}"
    )


# ====== Organization Memory Retrieval Step Definitions ======


@pytest.mark.usefixtures("memory_enabled_agent_config")
@given("a RAGAgent runner with organization memory enabled", target_fixture="agent_runner")
def _(memory_enabled_agent_config):
    """
    Given a RAGAgent runner with organization memory enabled.

    This agent will retrieve organization memories in addition to knowledge documents.
    """
    return AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=memory_enabled_agent_config,
    )


@given("organization memories are pre-seeded in the system")
def _(agent_runner: AgentTestRunner):
    """
    Given organization memories are pre-seeded in the system.

    NOTE: This step is a placeholder. In a real test environment, you would:
    1. Use the Mem0Service to seed organization memories
    2. Or mock the AgentMemory.search_organization_memory() response

    For now, this step documents the requirement but doesn't perform seeding.
    The agent's memory retrieval will be tested with whatever data exists in the environment.
    """
    # TODO: Add memory seeding when integration test infrastructure is available
    # See packages/core/swiss_ai_hub/core/generative_ai/memory/tests/test_agent_memory.py for examples
    pass


@then("a RetrieveOrganizationMemoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Assert that the agent emitted a RetrieveOrganizationMemoryEvent."""
    event = agent_runner.get_event_of_class(RetrieveOrganizationMemoryEvent)
    assert event is not None, "RetrieveOrganizationMemoryEvent was not emitted"


@then("an AddOrganizationMemoryToChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Assert that organization memories were added to chat history."""
    event = agent_runner.get_event_of_class(AddMemoryToChatHistoryEvent)
    assert event is not None, "AddMemoryToChatHistoryEvent was not emitted"
    assert event.extended_history, "Chat history was not extended with organization memory"
