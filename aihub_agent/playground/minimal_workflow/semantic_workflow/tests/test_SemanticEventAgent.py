from pytest_bdd import scenarios, given, when, then, parsers

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, RetrieverEvent, RerankerEvent, LLMStopEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.semantic_workflow.SemanticEventAgent import SemanticEventAgent
from playground.minimal_workflow.semantic_workflow.SemanticEventAgentConfig import SemanticEventAgentConfig

scenarios("../tests/features/semantic_event_agent.feature")


@given("a SemanticEventAgent runner", target_fixture="agent_runner")
def _():
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
        await agent_runner.send_event_from_topic(topic=topic, start_event=StartEvent())


@then("a StartEvent is present")
def start_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then(parsers.parse('a RetrieverEvent is present that retrieved "{count:d}" documents'))
def retrieve_present(agent_runner: AgentTestRunner, count: int):
    assert agent_runner.has_event_of_type(RetrieverEvent), "Agent did not receive retriever event"
    num_documents = len(agent_runner.get_event_of_type(RetrieverEvent).documents)
    assert num_documents == count, f"Expected {count} documents, got {num_documents}"


@then("a RerankerEvent is present")
def rerank_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(RerankerEvent), "Agent did not receive reranker event"


@then("a LLMStopEvent is present")
def stop_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_type(LLMStopEvent), "Agent did not receive stop event"
