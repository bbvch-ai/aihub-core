from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.llms.models.chat.self_hosted.SelfHostedLLMConfig import (
    SelfHostedLLMConfig,
    SelfHostedLLMParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, LLMEvent, ChunkEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.llama_index_workflow.LlamaIndexAgent import LlamaIndexAgent
from playground.minimal_workflow.llama_index_workflow.LlamaIndexAgentConfig import LlamaIndexAgentConfig

scenarios("../tests/features/llama_index_agent.feature")


@given("a LlamaIndexAgent is initialized and configured with a language model", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=LlamaIndexAgent,
        agent_config=LlamaIndexAgentConfig(
            agent_id="llama_index_agent",
            name=LocaleString(en="Llama Index Agent"),
            description=LocaleString(en="This is an agent that uses a llama index llm"),
            system_prompt=LocaleString(en="You are an agent"),
            llm=SelfHostedLLMConfig(
                name="unsloth/Llama-3.2-1B-Instruct",
                api_endpoint="http://localhost:8182/v1",
                api_key="fake",
                is_chat_model=True,
                is_function_calling_model=False,
                context_size=512,
                default_parameter=SelfHostedLLMParameter(
                    logprobs=None,
                    logit_bias=None,
                ),
            ),
        ),
    )


@when(parsers.parse('the user sends a message "{payload}"'))
@async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run(delay_before_stop=5) as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content=payload, role=MessageRole.USER)]),
            topic=topic,
        )


@then(parsers.parse('the agent should call the LLM to process the message "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    llm_event = agent_runner.get_event_of_type(LLMEvent)
    assert llm_event.input_messages[0].role == MessageRole.USER
    assert llm_event.input_messages[0].content == payload


@then("the agent should stream a partial response")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(ChunkEvent), "Agent did not stream a partial response"


@then("the agent should produce a complete response from the LLM")
def _(agent_runner: AgentTestRunner):
    llm_event = agent_runner.get_event_of_type(LLMEvent)
    assert llm_event.output_messages[0].role == MessageRole.ASSISTANT
    assert llm_event.output_messages[0].content, "Agent did not produce a complete response"


@then("the agent should stop after completing the response")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not stop after completing the response"
