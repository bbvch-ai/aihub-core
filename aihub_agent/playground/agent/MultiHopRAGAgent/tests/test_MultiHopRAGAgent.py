from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.agents.rag.Configs.MultiHopRAGAgentConfig import MultiHopRAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.Events.ConcatenationEvent import ConcatenationEvent
from aihub_agent.agents.rag.Events.DecomposeQueryEvent import DecomposeQueryEvent
from aihub_agent.agents.rag.Events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.rag.MultiHopRAGAgent import MultiHopRAGAgent
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
from aihub_lib.testing.asyncio_utils.bdd import async_test

scenarios("../tests/features/multi_hop_rag_agent.feature")


@given(parsers.parse('a MultiHopRAGAgent runner with a valid configuration with "{hops:d}" hops'), target_fixture="agent_runner")
def _(hops: int):
    return AgentTestRunner(
        agent_type=MultiHopRAGAgent,
        agent_config=MultiHopRAGAgentConfig(
            agent_id="multi_hop_rag_agent",
            name=LocaleString(en="Multi Hop RAG Agent"),
            description=LocaleString(
                en="This is an agent that can be used to answer user questions using Multi Hop RAG"
            ),
            system_prompt=LocaleString(
                en="You're an agent answering user requests. Only use the context information provided."
            ),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o-mini",
                api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2024-08-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
            retrieve_step_config=RetrieveStepConfig(
                embed_model=AzureOpenAIEmbeddingConfig(
                    name="text-embedding-ada-002",
                    api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                    api_version="2023-05-15",
                    embedding_tokens_costs_per_thousand=0.0,
                    default_parameter=AzureOpenAIEmbeddingParameter(),
                ),
                index_name="development",
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode="hybrid",
                node_types=["content"],
            ),
            number_of_input_tokens=8000,
            tokenizer_for_model="gpt-4o-mini",
            hops=hops,
            decompose_chat_history_prompt=LocaleString(
                en="""
                Given the following conversation between a user and an AI assistant and a follow-up question from the user,
                rephrase the follow-up question into multiple questions.

                Chat history:
                {chat_history}
                Follow-up input: {question}
                Multiple questions:"""
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
            start_event=StartEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                locale="en"
            ),
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then("a LimitChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.get_event_of_type(LimitChatHistoryEvent), "Agent did not produce LimitChatHistoryEvent"


@then(parsers.parse('"{count:d}" DecomposeQueryEvent are present'))
def _(agent_runner: AgentTestRunner, count: int):
    decompose_events = agent_runner.get_events_of_type(DecomposeQueryEvent)

    assert len(decompose_events) == count, f"Expected {count} decomposed questions found {len(decompose_events)}"
    assert decompose_events[0].decomposed_chat_history.content, "No decomposed questions found"

@then(parsers.parse('"{count:d}" RetrieverEvent are present'))
def _(agent_runner: AgentTestRunner, count: int):
    retriever_events = agent_runner.get_events_of_type(RetrieverEvent)
    assert len(retriever_events) == count, f"Expected {count} retriever events found {len(retriever_events)}"
    assert retriever_events[0].documents, "RetrieverEvent did not produce documents"


@then("a ConcatenationEvent is present with concatenated documents")
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_type(ConcatenationEvent)
    assert retriever_event.documents, "ConcatenationEvent did not produce documents"


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
