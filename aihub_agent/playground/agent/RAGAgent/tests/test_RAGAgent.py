from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.agents.rag.Configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.Events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.rag.Events.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from aihub_agent.agents.rag.RAGAgent import RAGAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.llms.models.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import LLMEvent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreFactory import create_azure_ai_search_vector_store
from aihub_lib.testing.asyncio_utils.bdd import async_test

scenarios("../tests/features/rag_agent.feature")


@given("a RAGAgent runner with a valid configuration", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig(
            agent_id="rag_agent",
            name=LocaleString(en="RAG Agent"),
            description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. Only use the context information provided."
            ),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o-mini",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-ada-002",
                    base_url="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-12-01-preview",
                    embedding_tokens_costs_per_thousand=0.0,
                    default_parameter=AzureOpenAIEmbeddingParameter(),
                ),
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=VectorStoreQueryMode.HYBRID,
                node_types=["content"],
                vector_store=create_azure_ai_search_vector_store("development"),
            ),
            number_of_input_tokens=2048,
            tokenizer_for_model="gpt-4o-mini",
            condense_question_prompt=LocaleString(
                en="""
                Given the following conversation between a user and an AI assistant and a follow-up question from the user,
                rephrase the follow-up question to be a standalone question.

                Chat history:
                {chat_history}
                Follow-up input: {question}
                Standalone question:"""
            ),
            context_prompt=LocaleString(
                en="""
                You are provided with some additional context information in form of structured documents with its general
                structure and relevant information in more detail. Each document starts with an indicator <DOC_START [documentname]>
                and ends with <DOC_END [documentname]>.
                Here are the relevant documents for the context:

                {context_str}

                Instruction: Based on the above documents, provide a detailed answer for the user question below."""
            ),
        ),
    )


@when(parsers.parse('the start event is sent with a user query "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=30) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[ChatMessage(content=query, role=MessageRole.USER)]),
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
