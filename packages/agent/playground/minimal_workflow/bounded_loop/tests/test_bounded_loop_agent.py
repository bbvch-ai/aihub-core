from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test

from playground.minimal_workflow.bounded_loop.bounded_loop_agent import BoundedLoopAgent
from playground.minimal_workflow.bounded_loop.bounded_loop_agent_config import BoundedLoopAgentConfig
from playground.minimal_workflow.bounded_loop.events.begin_event import BeginEvent
from playground.minimal_workflow.bounded_loop.events.bounded_loop_a_event import BoundedLoopAEvent
from playground.minimal_workflow.bounded_loop.events.decision_event import DecisionEvent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/bounded_loop_agent.feature")


@given(
    parsers.parse('a BoundedLoopAgent runner with a loop_max value of "{loop_max:d}"'),
    target_fixture="agent_runner",
)
def _(loop_max: int):
    return AgentTestRunner(
        agent_type=BoundedLoopAgent,
        agent_config=BoundedLoopAgentConfig(
            agent_id="bounded_iterative_loop_agent",
            name=LocaleString(en="Bounded Iterative Agent"),
            description=LocaleString(en="This is an agent that loops"),
            loop_max=2,
        ),
    )


@when("a the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


@then("a StartEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive start event"


@then(parsers.parse('"{loop_max:d}" BeginEvent are present'))
def _(loop_max: int, agent_runner: AgentTestRunner):
    received_loop_max = len(agent_runner.get_events_of_class(BeginEvent))
    assert received_loop_max == loop_max, f"Agent received {received_loop_max} BeginEvents, but expected {loop_max}"


@then(parsers.parse('"{loop_max:d}" BoundedLoopAEvent are present'))
def _(loop_max: int, agent_runner: AgentTestRunner):
    received_loop_max = len(agent_runner.get_events_of_class(BoundedLoopAEvent))
    assert received_loop_max == loop_max, (
        f"Agent received {received_loop_max} BoundedLoopAEvent, but expected {loop_max}"
    )


@then("a DecisionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.get_event_of_class(DecisionEvent), "Agent did not receive DecisionEvent"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"
