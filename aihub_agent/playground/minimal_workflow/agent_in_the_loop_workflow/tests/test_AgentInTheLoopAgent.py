import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, AgentInTheLoopExceptionEvent
from aihub_lib.nats.events.agent_in_the_loop import (
    AgentInTheLoopRequestEvent,
    AgentInTheLoopResponseEvent,
)
from aihub_lib.testing.asyncio_utils.bdd import async_test
from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.Events.OrchestrationResultEvent import (
    OrchestrationResultEvent,
)

from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.OrchestratorAgent import OrchestratorAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.WorkerAgent import WorkerAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.OrchestratorAgent.OrchestratorAgentConfig import (
    OrchestratorAgentConfig,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.WorkerAgentConfig import WorkerAgentConfig

# Link to feature file
scenarios("./features/agent_in_the_loop_agent.feature")


@pytest.fixture
def orchestrator_config():
    return OrchestratorAgentConfig(
        agent_id="orchestrator_agent",
        name=LocaleString(en="Orchestrator Agent"),
        description=LocaleString(en="This is an orchestrator agent"),
        system_prompt=LocaleString(en="You are an orchestrator agent"),
    )


@pytest.fixture
def worker_config():
    return WorkerAgentConfig(
        agent_id="worker_agent",
        name=LocaleString(en="Worker Agent"),
        description=LocaleString(en="This is a worker agent"),
        system_prompt=LocaleString(en="You are a worker agent"),
    )


@given("an OrchestratorAgent runner", target_fixture="orchestrator_runner")
def _(orchestrator_config):
    return AgentTestRunner(
        agent_type=OrchestratorAgent,
        agent_config=orchestrator_config,
    )


@given("a WorkerAgent runner", target_fixture="worker_runner")
def _(worker_config):
    return AgentTestRunner(
        agent_type=WorkerAgent,
        agent_config=worker_config,
    )


@when(parsers.parse('a start event with message "{message}" is sent to the orchestrator'))
@async_test
async def send_start_to_orchestrator(
    orchestrator_runner: AgentTestRunner, worker_runner: AgentTestRunner, message: str
):
    async with worker_runner.test_run(delay_before_stop=5):
        async with orchestrator_runner.test_run(delay_before_stop=3) as topic:
            await orchestrator_runner.send_event_from_topic(
                start_event=StartEvent(messages=[ChatMessage(content=message, role=MessageRole.USER)]), topic=topic
            )


@then("a StartEvent is received by the orchestrator")
def check_orchestrator_start(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_start_event


@then("an AgentInTheLoopRequest is received by the orchestrator")
def check_agent_in_loop_request(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_event_of_type(AgentInTheLoopRequestEvent)


@then(parsers.parse("an AgentInTheLoopResponse with result {result} is received by the orchestrator"))
def check_agent_in_loop_response(orchestrator_runner: AgentTestRunner, result: str):
    assert orchestrator_runner.has_event_of_type(AgentInTheLoopResponseEvent)
    response_event = orchestrator_runner.get_events_of_type(AgentInTheLoopResponseEvent)[-1]
    assert response_event.stop_event.result == int(result)


@then("an AgentInTheLoopResponse with exception is received by the orchestrator")
def check_agent_in_loop_response(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_event_of_type(AgentInTheLoopExceptionEvent)
    exception_event = orchestrator_runner.get_events_of_type(AgentInTheLoopExceptionEvent)[-1]
    assert exception_event.exception_event is not None


@then(parsers.parse("an OrchestrationResultEvent with result {result} is received by the orchestrator"))
def check_orchestrator_result(orchestrator_runner: AgentTestRunner, result: str):
    assert orchestrator_runner.has_stop_event
    result_event = orchestrator_runner.get_events_of_type(OrchestrationResultEvent)[-1]
    assert result_event.result == int(result)
