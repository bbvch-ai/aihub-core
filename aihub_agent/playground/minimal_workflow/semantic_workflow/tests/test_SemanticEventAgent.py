from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import LLMStopEvent, RerankerEvent, RetrieverEvent, StartEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.semantic_workflow.SemanticEventAgent import SemanticEventAgent
from playground.minimal_workflow.semantic_workflow.SemanticEventAgentConfig import SemanticEventAgentConfig

scenarios("./features/semantic_event_agent.feature")


@given("a SemanticEventAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=SemanticEventAgent,
        agent_config=SemanticEventAgentConfig(
            agent_id="semantic_event_agent",
            name=LocaleString(en="Semantic Event Agent"),
            description=LocaleString(en="This is an agent with semantic events"),
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


@then(parsers.parse('a RetrieverEvent is present that retrieved "{count:d}" nodes'))
def retrieve_present(agent_runner: AgentTestRunner, count: int):
    assert agent_runner.has_event_of_class(RetrieverEvent), "Agent did not receive retriever event"
    num_nodes = len(agent_runner.get_event_of_class(RetrieverEvent).nodes)
    assert num_nodes == count, f"Expected {count} documents, got {num_nodes}"


@then("a RerankerEvent is present")
def rerank_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(RerankerEvent), "Agent did not receive reranker event"


@then("a LLMStopEvent is present")
def stop_present(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(LLMStopEvent), "Agent did not receive stop event"
