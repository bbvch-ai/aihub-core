# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import LLMEvent, UserMessageEvent
from aihub_lib.nats.events.agent_in_the_loop import AgentInTheLoopRequestEvent, AgentInTheLoopResponseEvent
from aihub_lib.nats.events.common.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_lib.nats.events.common.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from aihub_lib.nats.events.guard.FewShotAcceptEvent import FewShotAcceptEvent
from aihub_lib.nats.events.guard.FewShotRejectEvent import FewShotRejectEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from aihub_agent.rag.events import InOrderNodeCombinerEvent, LimitChatHistoryWithContextEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("./features/rag_agent.feature")
load_dotenv(Path(__file__).parent / ".env")

TIMEOUT = 120


def build_rag_agent_config(llm_config: LLMConfig) -> RAGAgentConfig:
    """
    Build a RAGAgentConfig with the specified LLM configuration.

    Note: Retrieval is now handled by RetrievalAgent via AgentInTheLoop.
    The retrieval config (retrievers, reranking) is in RetrievalAgentConfig.
    """
    return RAGAgentConfig(
        agent_id="rag_agent",
        agent_class=RAGAgent.__name__,
        name=LocaleString(en="RAG Agent"),
        description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
        llm=llm_config,
        retrieval_agent_class="RetrievalAgent",
        retrieval_agent_id="test_retrieval_agent",
        number_of_input_tokens=8192,
        check_context_sufficiency=False,
    )


@pytest.fixture(scope="session")
def self_hosted_agent_config():
    """
    Return a RAGAgentConfig that uses a self-hosted LLM.

    Note: Retrieval is now handled by RetrievalAgent via AgentInTheLoop.
    """
    llm_config = LLMConfig(model_name="text-generation/mini")
    return build_rag_agent_config(llm_config=llm_config)


@given(parsers.parse('check_context_sufficiency set to "{flag}" and max_hops to "{max_hops:d}"'))
def _(flag: bool, max_hops: int, agent_runner: AgentTestRunner):
    agent_runner.default_agent_config.check_context_sufficiency = flag
    agent_runner.default_agent_config.max_hops = max_hops


@pytest.mark.usefixtures("self_hosted_agent_config")
@given("a RAGAgent runner with a valid self hosted configuration", target_fixture="agent_runner")
def _(self_hosted_agent_config):
    """
    Given a RAGAgent runner with a valid self-hosted configuration.
    """
    return AgentTestRunner(
        agent_type=RAGAgent,
        default_agent_config=self_hosted_agent_config,
    )


@when(parsers.parse('the start event is sent with a user query "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=TIMEOUT) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )
        # Wait for AgentInTheLoop request to RetrievalAgent
        await agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

        # Mock RetrievalAgent response with relevant context
        mock_retrieval_response = RetrievalResponseEvent(
            context_message=ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Retrieved context about AI:\n"
                    "Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
                    "It includes machine learning, neural networks, and natural language processing. "
                    "AI systems can learn from data, identify patterns, and make decisions."
                ),
            ),
            nodes=[],  # Nodes would normally come from the retrieval
        )
        await agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_retrieval_response),
            topic=topic,
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
    agent_runner.default_agent_config.few_shot_guard_examples = examples
    return agent_runner


@when(parsers.parse('the start event is sent with a user query "{query}" and locale {locale}'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str, locale: str):
    async with agent_runner.test_run(delay_before_stop=TIMEOUT) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                locale=locale,
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
            ),
        )
        # Wait for AgentInTheLoop request to RetrievalAgent
        await agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

        # Mock RetrievalAgent response with relevant context
        mock_retrieval_response = RetrievalResponseEvent(
            context_message=ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Retrieved context about AI:\n"
                    "Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
                    "It includes machine learning, neural networks, and natural language processing."
                ),
            ),
            nodes=[],
        )
        await agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_retrieval_response),
            topic=topic,
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

    agent_runner.default_agent_config.system_prompt = LocaleString(**prompts)
    return agent_runner


@given(parsers.parse('with multi-language system prompt for locale {locale} and prompt "{prompt}"'))
def _(agent_runner: AgentTestRunner, locale: str, prompt: str):
    """
    Given multi-language system prompt for a specific locale and prompt.
    Used for parameterized Scenario Outline with Examples.
    """
    agent_runner.default_agent_config.system_prompt = LocaleString(**{locale: prompt})
    return agent_runner


@then(parsers.parse('the LLM received the system prompt "{expected_prompt}"'))
def _(agent_runner: AgentTestRunner, expected_prompt: str):
    config = agent_runner.default_agent_config
    assert config.system_prompt is not None, "System prompt was not configured"

    start_event = agent_runner.get_start_event()
    locale = start_event.locale

    actual_prompt = config.system_prompt.in_locale(locale)
    assert actual_prompt == expected_prompt, f"Expected system prompt '{expected_prompt}', got '{actual_prompt}'"


# Note: Reranking and insight retrieval step definitions have been removed.
# These are now tested in the RetrievalAgent tests since retrieval logic
# has been moved to the shared RetrievalAgent.
