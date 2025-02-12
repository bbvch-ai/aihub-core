import pytest
from aihub_agent.agents.rag.Configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.Events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.rag.Events.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.agents.rag.RAGAgent import RAGAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.resources.models.llm.chat.self_hosted.SelfHostedLLMConfig import (
    SelfHostedLLMConfig,
    SelfHostedLLMParameter,
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
from aihub_lib.nats.events import LLMEvent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreFactory import create_azure_ai_search_vector_store
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.milvus_vector_store_content import fill_collection, drop_collection

scenarios("../tests/features/rag_agent.feature")


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
                mode="both",
            ),
        ),
        number_of_input_tokens=2048,
    )


@pytest.fixture
def azure_agent_config():
    """
    Return a RAGAgentConfig that uses Azure OpenAI for both the LLM and embeddings.
    """
    llm_config = AzureOpenAILLMConfig(
        name="gpt-4o-mini",
        base_url="https://aihub-dev-openai-che.openai.azure.com/",
        api_version="2023-12-01-preview",
        prompt_tokens_costs_per_thousand=0.0045,
        completion_tokens_costs_per_thousand=0.0133,
        default_parameter=AzureOpenAIParameter(temperature=0.0),
    )
    embedding_config = AzureOpenAIEmbeddingConfig(
        name="text-embedding-ada-002",
        base_url="https://aihub-dev-openai-che.openai.azure.com/",
        api_version="2023-12-01-preview",
        embedding_tokens_costs_per_thousand=0.0,
        default_parameter=AzureOpenAIEmbeddingParameter(),
    )
    vector_store = create_azure_ai_search_vector_store("development")

    return build_rag_agent_config(
        llm_config=llm_config,
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
    )


@pytest.fixture
def self_hosted_agent_config():
    """
    Return a RAGAgentConfig that uses a self-hosted LLM and self-hosted embeddings.
    """
    llm_config = SelfHostedLLMConfig(
        name="unsloth/Llama-3.2-1B-Instruct",
        base_url="http://localhost:8182/v1",
        api_key=None,
        context_size=512,
        is_chat_model=True,
        is_function_calling_model=False,
        default_parameter=SelfHostedLLMParameter(
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

    fill_collection(
        embedding_config,
        vector_store,
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
    async with agent_runner.test_run(delay_before_stop=30) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[ChatMessage(content=query, role=MessageRole.USER)], locale="en"),
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then("a LimitChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.get_event_of_type(LimitChatHistoryEvent), "Agent did not produce LimitChatHistoryEvent"


@then(parsers.parse("a StandaloneQuestionCondenserEvent is present with condensed question"))
def _(agent_runner: AgentTestRunner):
    condenser_event = agent_runner.get_event_of_type(StandaloneQuestionCondenserEvent)
    assert condenser_event.condensed_chat_message.content, "No condensed question found"


@then("a RetrieverEvent is present with retrieved documents")
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_type(RetrieverEvent)
    assert retriever_event.documents, "RetrieverEvent did not produce documents"


@then("an InOrderNodeCombinerEvent is present with ordered context message")
def _(agent_runner: AgentTestRunner):
    combiner_event = agent_runner.get_event_of_type(InOrderNodeCombinerEvent)
    assert combiner_event.context_message, "InOrderNodeCombinerEvent did not produce context message"


@then("a LimitChatHistoryWithContextEvent is present with limited history and context")
def _(agent_runner: AgentTestRunner):
    history_event = agent_runner.get_event_of_type(LimitChatHistoryWithContextEvent)
    assert history_event.limited_history_with_context, "LimitChatHistoryWithContextEvent missing data"


@then("an LLMEvent is present with a generated response")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_type(LLMEvent)
    assert llm_event, "LLMEvent not produced"


@then("the response contains a detailed explanation")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_type(LLMEvent)
    assert "detailed" in llm_event.response.content.lower(), "Response does not contain a detailed explanation"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce StopEvent"
