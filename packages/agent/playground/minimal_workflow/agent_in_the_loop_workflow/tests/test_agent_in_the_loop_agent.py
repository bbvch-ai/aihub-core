import copy

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoopExceptionEvent,
    AgentInTheLoopRequestEvent,
    AgentInTheLoopResponseEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from playground.minimal_workflow.agent_in_the_loop_workflow.orchestrator_agent.events.orchestration_result_event import (  # noqa: E501
    OrchestrationResultEvent,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.orchestrator_agent.orchestrator_agent import (
    OrchestratorAgent,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.orchestrator_agent.orchestrator_agent_config import (
    OrchestratorAgentConfig,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.events.worker_stop_event import WorkerStopEvent
from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.worker_agent import WorkerAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.worker_agent_config import WorkerAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

# Link to feature file
scenarios("./features/agent_in_the_loop_agent.feature")


@pytest.fixture
def orchestrator_config():
    return OrchestratorAgentConfig(
        agent_id="orchestrator_agent",
        agent_class=OrchestratorAgent.__name__,
        name=LocaleString(en="Orchestrator Agent"),
        description=LocaleString(en="This is an orchestrator agent"),
    )


@pytest.fixture
def worker_config():
    return WorkerAgentConfig(
        agent_id="worker_agent",
        agent_class=WorkerAgent.__name__,
        name=LocaleString(en="Worker Agent"),
        description=LocaleString(en="This is a worker agent"),
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


@given("WorkerStopEvent is removed from the registry", target_fixture="original_registry")
def remove_worker_stop_event_from_registry():
    # Save the original registry
    original_registry = copy.deepcopy(BaseEvent._event_registry)

    # Remove WorkerStopEvent from the registry
    if WorkerStopEvent.event_name_from_class() in BaseEvent._event_registry:
        del BaseEvent._event_registry[WorkerStopEvent.event_name_from_class()]

    # Return the original registry so we can restore it later
    return original_registry


@when(parsers.parse('a start event with message "{message}" is sent to the orchestrator'))
@async_test
async def send_start_to_orchestrator(
    orchestrator_runner: AgentTestRunner, worker_runner: AgentTestRunner, message: str
):
    async with worker_runner.test_run():
        async with orchestrator_runner.test_run() as topic:
            await orchestrator_runner.send_event_from_topic(
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content=message, role=MessageRole.USER)],
                    user=fake_user(),
                ),
                topic=topic,
            )


@then("a StartEvent is received by the orchestrator")
def check_orchestrator_start(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_start_event


@then("an AgentInTheLoopRequest is received by the orchestrator")
def check_agent_in_loop_request(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_event_of_class(AgentInTheLoopRequestEvent)


@then(parsers.parse("exactly {count:d} unique AgentInTheLoopResponse is received by the orchestrator"))
def check_no_duplicate_aitl_response(orchestrator_runner: AgentTestRunner, count: int):
    responses = orchestrator_runner.get_events_of_class(AgentInTheLoopResponseEvent)
    unique_ids = {r.event_id for r in responses}
    assert len(unique_ids) == count, (
        f"Expected {count} unique AgentInTheLoopResponseEvent(s) but got {len(unique_ids)} — "
        f"duplicate AITL responses indicate the ControlAndDisplayEvent dual-publish bug"
    )


@then(parsers.parse("exactly {count:d} unique OrchestrationResultEvent is received by the orchestrator"))
def check_no_duplicate_orchestration_result(orchestrator_runner: AgentTestRunner, count: int):
    results = orchestrator_runner.get_events_of_class(OrchestrationResultEvent)
    unique_ids = {r.event_id for r in results}
    assert len(unique_ids) == count, (
        f"Expected {count} unique OrchestrationResultEvent(s) but got {len(unique_ids)} — "
        f"duplicate results indicate a step ran multiple times due to duplicate AITL responses"
    )


@then(parsers.parse("an AgentInTheLoopResponse with result {result} is received by the orchestrator"))
def check_agent_in_loop_response_with_result(orchestrator_runner: AgentTestRunner, result: str):
    assert orchestrator_runner.has_event_of_class(AgentInTheLoopResponseEvent)
    response_event = orchestrator_runner.get_events_of_class(AgentInTheLoopResponseEvent)[-1]
    assert response_event.stop_event.result == int(result)


@then("an AgentInTheLoopResponse with exception is received by the orchestrator")
def check_agent_in_loop_response_with_exception(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_event_of_class(AgentInTheLoopExceptionEvent)
    exception_event = orchestrator_runner.get_events_of_class(AgentInTheLoopExceptionEvent)[-1]
    assert exception_event.exception_event is not None


@then("an AgentInTheLoopResponse with unknown event type is received by the orchestrator")
def check_agent_in_loop_response_with_unknown_event(orchestrator_runner: AgentTestRunner):
    assert orchestrator_runner.has_event_of_class(AgentInTheLoopResponseEvent)
    response_event = orchestrator_runner.get_events_of_class(AgentInTheLoopResponseEvent)[-1]

    # Check if the stop_event is an instance of BaseEvent (fallback) but still has the right data
    assert not isinstance(response_event.stop_event, WorkerStopEvent)
    assert isinstance(response_event.stop_event, BaseEvent)
    assert hasattr(response_event.stop_event, "result")
    assert response_event.stop_event.result == 16

    # Verify the unknown type information is preserved
    assert response_event.stop_event._unknown_event_name == WorkerStopEvent.event_name_from_class()


@then(parsers.parse("an OrchestrationResultEvent with result {result} is received by the orchestrator"))
def check_orchestrator_result(orchestrator_runner: AgentTestRunner, result: str):
    assert orchestrator_runner.has_stop_event
    result_event = orchestrator_runner.get_events_of_class(OrchestrationResultEvent)[-1]
    assert result_event.result == int(result)


@then("WorkerStopEvent is restored to the registry")
def restore_worker_stop_event_to_registry(original_registry):
    # Restore the original registry
    BaseEvent._event_registry.clear()
    BaseEvent._event_registry.update(original_registry)
