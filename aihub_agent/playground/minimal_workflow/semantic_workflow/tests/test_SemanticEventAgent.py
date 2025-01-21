import pytest
from pytest_bdd import scenarios, given, when, then

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, RetrieverEvent, RerankerEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test

from playground.minimal_workflow.semantic_workflow.SemanticEventAgent import SemanticEventAgent
from playground.minimal_workflow.semantic_workflow.SemanticEventAgentConfig import SemanticEventAgentConfig

scenarios("../tests/features/semantic_event_agent.feature")


@pytest.fixture()
@given("a SemanticEventAgent runner")
def agent_runner():
    return AgentTestRunner(
        agent_type=SemanticEventAgent,
        agent_config=SemanticEventAgentConfig(
            agent_id="semantic_event_agent",
            name=LocaleString(en="Semantic Event Agent"),
            description=LocaleString(en="This is an agent with semantic events"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when("a the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(topic=topic, start_event=StartEvent(messages=[]))


@then("a StartEvent is present")
def test_start_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event == True, "Agent did not receive start event"


@then("a RetrieverEvent is present")
def test_retrieve_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(RetrieverEvent), "Agent did not receive retriever event"


@then("a RerankerEvent is present")
def test_rerank_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(RerankerEvent), "Agent did not receive reranker event"


@then("a LLMStopEvent is present")
def test_stop_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"
