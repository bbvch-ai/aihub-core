import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.RagAgent.events.FewShotAcceptEvent import FewShotAcceptEvent
from aihub_agent.agents.RagAgent.events.FewShotRejectEvent import FewShotRejectEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.resources.models.llm.chat.openai_like.OpenaiLikeLLMConfig import (
    OpenaiLikeLLMConfig,
    OpenaiLikeLLMParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
    SelfHostedEmbeddingParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import LLMEvent, UserMessageEvent
from aihub_lib.nats.events.common.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_lib.nats.events.common.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.persistence.rag.documents.stores.MongoDocumentStoreFactory import create_mongo_document_store
from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreFactory import create_azure_ai_search_vector_store
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.testing.logging.logger import enable_logging
from aihub_lib.testing.milvus_vector_store_content import fill_collection, drop_collection

enable_logging()


# Set up an event loop for the test session
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("./features/rag_agent.feature")
load_dotenv(Path(__file__).parent / ".env")


def build_rag_agent_config(
    llm_config,
    embedding_config,
    vector_store,
    query_mode: VectorStoreQueryMode,
) -> RAGAgentConfig:
    """
    Build a fully populated RAGAgentConfig, substituting in the LLM/Embedding config
    and vector store that differ between Azure vs. Self-Hosted.

    We keep the entire parameter list intact to avoid partial Pydantic construction.
    """
    return RAGAgentConfig(
        agent_id="rag_agent",
        name=LocaleString(en="RAG Agent"),
        description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
        system_prompt=LocaleString(
            en="You're an agent answering user requests. Only use the context information provided."
        ),
        llm=llm_config,
        retrieve_step_config=RetrieveStepConfig(
            embed_model=embedding_config,
            index_namespaces=["ai_knowledge"],
            retrieve_k=5,
            query_mode=query_mode,
            node_types=["content"],
            vector_store=vector_store,
            retrieve_prev_next=RetrievePrevNextConfig(
                num_nodes=2,
                mode=ModeOptions.BOTH,
            ),
        ),
        number_of_input_tokens=8192,
        check_context_sufficiency=False,
    )


@pytest.fixture
def azure_agent_config():
    """
    Return a RAGAgentConfig that uses Azure OpenAI for both the LLM and embeddings.
    """
    llm_config = AzureOpenAILLMConfig(
        name="gpt-4o-mini",
        base_url="https://aihub-dev-openai-che.openai.azure.com/",
        api_version="2024-08-01-preview",
        prompt_tokens_costs_per_thousand=0.0045,
        completion_tokens_costs_per_thousand=0.0133,
        default_parameter=AzureOpenAIParameter(temperature=0.0),
    )
    embedding_config = AzureOpenAIEmbeddingConfig(
        name="text-embedding-ada-002",
        base_url="https://aihub-dev-openai-che.openai.azure.com/",
        api_version="2024-12-01-preview",
        embedding_tokens_costs_per_thousand=0.0,
        default_parameter=AzureOpenAIEmbeddingParameter(),
    )
    vector_store = create_azure_ai_search_vector_store(
        # needed for embedding field
        vector_store_name="development",
        semantic_configuration_name="mySemanticConfig",
    )

    return build_rag_agent_config(
        llm_config=llm_config,
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
    )


@pytest.fixture(scope="function")
def self_hosted_agent_config(event_loop):
    """
    Return a RAGAgentConfig that uses a self-hosted LLM and self-hosted embeddings.
    """
    # Set the event loop for this function
    asyncio.set_event_loop(event_loop)

    llm_config = OpenaiLikeLLMConfig(
        name="unsloth/Llama-3.2-1B-Instruct",
        base_url="http://localhost:8182/v1",
        api_key=None,
        context_size=16384,
        is_chat_model=True,
        is_function_calling_model=False,
        default_parameter=OpenaiLikeLLMParameter(
            logit_bias=None,
            logprobs=None,
        ),
    )
    embedding_config = SelfHostedEmbeddingConfig(
        name="Alibaba-NLP/gte-base-en-v1.5",
        base_url="http://localhost:8183",
        api_key=None,
        timeout=60,
        embed_batch_size=32,
        default_parameter=SelfHostedEmbeddingParameter(
            text_instruction=None,
            query_instruction=None,
            truncate_text=False,
        ),
    )
    vector_store = create_milvus_vector_store(
        uri="http://localhost",
        collection_name="development",
        embedding_vector_dimension=768,
    )
    doc_store = create_mongo_document_store(document_store_name="development")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield build_rag_agent_config(
        llm_config=llm_config,
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.DEFAULT,
    )

    drop_collection()


@pytest.mark.usefixtures("azure_agent_config")
@given("a RAGAgent runner with a valid azure configuration", target_fixture="agent_runner")
def _(azure_agent_config):
    """
    Given a RAGAgent runner with a valid Azure configuration.
    """
    return AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=azure_agent_config,
    )


@given(parsers.parse('check_context_sufficiency set to "{flag}" and max_hops to "{max_hops:d}"'))
def _(flag: bool, max_hops: int, agent_runner: AgentTestRunner):
    agent_runner.agent_config.check_context_sufficiency = flag
    agent_runner.agent_config.max_hops = max_hops


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
    async with agent_runner.test_run(delay_before_stop=40) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)], user=fake_user(), locale="en"
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
    async with agent_runner.test_run(delay_before_stop=30) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                locale=locale, user=fake_user(), messages=[ChatMessage(content=query, role=MessageRole.USER)]
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
