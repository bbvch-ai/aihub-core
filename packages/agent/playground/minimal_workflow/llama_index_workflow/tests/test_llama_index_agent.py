from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events.agent import ChunkEvent, LLMEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from playground.minimal_workflow.llama_index_workflow.llama_index_agent import LlamaIndexAgent
from playground.minimal_workflow.llama_index_workflow.llama_index_agent_config import LlamaIndexAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/llama_index_agent.feature")


@given("a LlamaIndexAgent is initialized and configured with a language model", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=LlamaIndexAgent,
        agent_config=LlamaIndexAgentConfig(
            agent_id="llama_index_agent",
            agent_class=LlamaIndexAgent.__name__,
            name=LocaleString(en="Llama Index Agent"),
            description=LocaleString(en="This is an agent that uses a llama index llm"),
            llm=LLMConfig(model_name="text-generation/gpt-oss-120b"),
        ),
    )


@when(parsers.parse('the user sends a message "{payload}"'))
@async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run(delay_before_stop=10) as topic:
        await agent_runner.send_event_from_topic(
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=payload, role=MessageRole.USER)],
                user=fake_user(),
            ),
            topic=topic,
        )


@then(parsers.parse('the agent should call the LLM to process the message "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    print(llm_event.input_messages)
    assert llm_event.input_messages[0].role == MessageRole.USER
    assert llm_event.input_messages[0].content == payload


@then("the agent should stream a partial response")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(ChunkEvent), "Agent did not stream a partial response"


@then("the agent should produce a complete response from the LLM")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_class(LLMEvent)
    assert llm_event.output_messages[0].role == MessageRole.ASSISTANT
    assert llm_event.output_messages[0].content, "Agent did not produce a complete response"


@then("the agent should stop after completing the response")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not stop after completing the response"
