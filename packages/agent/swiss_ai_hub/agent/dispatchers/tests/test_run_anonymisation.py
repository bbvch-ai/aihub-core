"""A profile's anonymisation reaches every LLM call of its runs: the steps, the runs it delegates to, the notice.

Driven through a real `AgentDispatcher` with its brokers and stores mocked, because what is under test is which
guardrails the dispatcher puts in place around a step and on a delegation, not NATS or Valkey.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from nats.js import JetStreamContext
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.dispatcher import EventsAndKwargs
from swiss_ai_hub.core.events.agent import AgentInTheLoop, StartEvent, StopEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import GatewayGuardrails
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topic_managers import AgentClassTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher
from swiss_ai_hub.agent.dispatchers.run_anonymisation import RunAnonymisation
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.workflow.decorators.step import step

PII = GatewayGuardrails.PII_ANONYMISATION
SEEN: list[tuple[str, ...]] = []


class _RecordingAgent(Agent):
    @step()
    async def answer_step(self, event: StartEvent) -> StopEvent:
        SEEN.append(GatewayGuardrails.requested())
        return None


def _config(anonymise: bool) -> AgentConfig:
    return AgentConfig(
        agent_id="hr", name=LocaleString(en="HR"), description=LocaleString(en="HR"), anonymise=anonymise
    )


def _topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="_RecordingAgent",
        agent_id="hr",
        thread_id="thread",
        display_id="display",
        run_id="run",
        event_type="control_event",
        event_name="StartEvent",
        event_id="event",
    )


def _redis() -> Mock:
    data: dict[str, bytes] = {}
    redis = Mock()

    async def get(key):
        return data.get(key)

    async def set(key, value, **_):
        data[key] = value.encode() if isinstance(value, str) else value
        return True

    redis.get, redis.set = get, set
    return redis


@pytest.fixture
def dispatcher() -> AgentDispatcher:
    topic_manager = Mock(spec=AgentClassTopicManager)
    topic_manager.get_stream = Mock(return_value=("stream", "agent._RecordingAgent.*"))
    dispatcher = AgentDispatcher(
        agent=_RecordingAgent,
        agent_config=_config(anonymise=False),
        nc=Mock(),
        js=Mock(spec=JetStreamContext),
        redis=_redis(),
        topic_manager=topic_manager,
        locale_handler=Mock(spec=AgentLocaleHandler),
    )
    dispatcher.step_store = Mock(
        was_called_with_events=AsyncMock(return_value=False), report_execution_context_with_events=AsyncMock()
    )

    @asynccontextmanager
    async def span(*_):
        yield Mock()

    dispatcher.agent_run_tracer = Mock(
        trace_step_start=span, trace_step_stop=AsyncMock(), start_aitl_wrapper_span=AsyncMock()
    )
    dispatcher._build_method_kwargs = AsyncMock(return_value=EventsAndKwargs(events=[], kwargs={"event": StartEvent()}))
    dispatcher.js_publisher = Mock(publish_event=AsyncMock())
    SEEN.clear()
    return dispatcher


async def _run_step(dispatcher: AgentDispatcher, config: AgentConfig) -> tuple[str, ...]:
    run_context = RunContext.for_topic(dispatcher.redis, _topic())
    thread_context = ThreadContext.for_topic(dispatcher.redis, _topic())
    await dispatcher.execute_step(
        StartEvent(), _RecordingAgent.answer_step, {}, run_context, thread_context, _topic(), config
    )
    return SEEN[-1]


@pytest.mark.asyncio
async def test_should_run_every_step_under_the_guardrail_when_the_profile_anonymises(dispatcher) -> None:
    assert await _run_step(dispatcher, _config(anonymise=True)) == (PII,)


@pytest.mark.asyncio
async def test_should_run_steps_as_today_when_the_profile_does_not_anonymise(dispatcher) -> None:
    assert await _run_step(dispatcher, _config(anonymise=False)) == ()


@pytest.mark.asyncio
async def test_should_drop_the_guardrail_once_the_step_is_done(dispatcher) -> None:
    await _run_step(dispatcher, _config(anonymise=True))

    assert GatewayGuardrails.requested() == ()


@pytest.mark.asyncio
async def test_should_anonymise_a_delegated_run_whose_own_profile_does_not(dispatcher) -> None:
    start = StartEvent()
    start._aihub_headers = {"x-aihub-anonymise": "true"}
    run_context = RunContext.for_topic(dispatcher.redis, _topic())
    await RunAnonymisation.remember_inherited(start, run_context)

    assert await _run_step(dispatcher, _config(anonymise=False)) == (PII,)


@pytest.mark.asyncio
async def test_should_tell_the_delegated_run_to_anonymise(dispatcher) -> None:
    request = AgentInTheLoop.invoke(agent_class="RAGAgent", agent_id="rag", start_event=StartEvent())
    subscriber = Mock(start=AsyncMock())
    target = "swiss_ai_hub.agent.dispatchers.agent_dispatcher.AgentNCSubscriber.for_thread_control_events"

    with patch(target, return_value=subscriber), GatewayGuardrails.requesting(PII):
        await dispatcher.trigger_agent_in_the_loop(request, _topic())

    assert dispatcher.js_publisher.publish_event.await_args.args[2] == {RunAnonymisation.HEADER: "true"}


@pytest.mark.asyncio
async def test_should_send_no_header_when_the_delegating_run_does_not_anonymise(dispatcher) -> None:
    request = AgentInTheLoop.invoke(agent_class="RAGAgent", agent_id="rag", start_event=StartEvent())
    target = "swiss_ai_hub.agent.dispatchers.agent_dispatcher.AgentNCSubscriber.for_thread_control_events"

    with patch(target, return_value=Mock(start=AsyncMock())):
        await dispatcher.trigger_agent_in_the_loop(request, _topic())

    assert dispatcher.js_publisher.publish_event.await_args.args[2] is None


def _user_message() -> UserMessageEvent:
    return UserMessageEvent(user=fake_user(), messages=[ChatMessage(role=MessageRole.USER, content="Hallo")])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("anonymise", "event", "headers", "notice"),
    [
        (True, _user_message(), None, True),
        (False, _user_message(), None, False),
        (True, StartEvent(), None, False),
        (True, _user_message(), {"x-aihub-anonymise": "true"}, False),
    ],
    ids=["chat-with-toggle-on", "toggle-off", "not-a-chat", "delegated-run"],
)
async def test_should_show_the_notice_once_per_anonymised_chat(dispatcher, anonymise, event, headers, notice) -> None:
    event._aihub_headers = headers
    dispatcher.agent_run_tracer.trace_run_start = AsyncMock()
    dispatcher.get_topic_manager_for_thread = Mock(return_value=Mock())
    run_context = RunContext.for_topic(dispatcher.redis, _topic())

    with patch.object(RunAnonymisation, "show_notice", new=AsyncMock()) as show_notice:
        await dispatcher._start_run(event, run_context, _topic(), _config(anonymise))

    assert show_notice.await_count == (1 if notice else 0)


@pytest.mark.asyncio
async def test_should_word_the_notice_in_the_run_locale_at_the_top_of_the_answer() -> None:
    displayer = Mock(display_chunk=AsyncMock())
    t = Mock(return_value="Personendaten wurden ersetzt.")

    await RunAnonymisation.show_notice(displayer, t)

    t.assert_called_once_with("agent.base_agent.notice.anonymised")
    assert displayer.display_chunk.await_args.args[0] == "_Personendaten wurden ersetzt._\n\n"


def test_should_ignore_a_header_that_does_not_say_true() -> None:
    assert RunAnonymisation.delegation_headers() is None
