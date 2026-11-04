"""A step result the broker refuses ends the run like a failing step does.

The broker refuses an event above its payload limit, and publishing a step's result happened outside the handling that
reports a failing step. Nothing then ended the run: no stop event, no `ExceptionEvent`, and the chat waited forever.
Driven through a real `AgentDispatcher` and `AgentRunTracer` on real OpenTelemetry spans, with publishing mocked,
because what is under test is what the dispatcher does when a publish fails, not NATS. The spans are real because an OK
status is final in OpenTelemetry: a mocked span would accept the ERROR that a real one ignores once OK was set.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from nats.errors import MaxPayloadError
from nats.js import JetStreamContext
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.trace import StatusCode
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.dispatcher import EventsAndKwargs
from swiss_ai_hub.core.events.agent import ExceptionEvent, StartEvent, StopEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.topic_managers import AgentClassTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.tracing.agent_run_tracer import AgentRunTracer
from swiss_ai_hub.agent.workflow.decorators.step import step


class _AnsweringAgent(Agent):
    @step()
    async def answer_step(self, event: StartEvent) -> StopEvent:
        return StopEvent()

    @step(stop_on_error=False)
    async def optional_step(self, event: StartEvent) -> StopEvent:
        return StopEvent()


CONFIG = AgentConfig(agent_id="hr", name=LocaleString(en="HR"), description=LocaleString(en="HR"))
TOPIC = AgentInstanceTopic(
    agent_class="_AnsweringAgent",
    agent_id="hr",
    thread_id="thread",
    display_id="display",
    run_id="run",
    event_type="control_event",
    event_name="StartEvent",
    event_id="event",
)


def _refusing_stop_events(published: list[BaseEvent]) -> AsyncMock:
    async def publish_event(event: BaseEvent, _topic: AgentInstanceTopic) -> None:
        if isinstance(event, StopEvent):
            raise MaxPayloadError
        published.append(event)

    return AsyncMock(side_effect=publish_event)


def _tracer(spans: list[Span]) -> AgentRunTracer:
    trace_store = Mock(
        get_user_input=AsyncMock(return_value=""),
        get_user_id=AsyncMock(return_value=""),
        get_tenant_id=AsyncMock(return_value=""),
        get_output=AsyncMock(return_value=""),
        get_aitl_parent_context=AsyncMock(return_value=None),
    )
    tracer = AgentRunTracer(trace_store)
    provider = TracerProvider()

    @asynccontextmanager
    async def span(*_):
        step_span = provider.get_tracer(__name__).start_span("step")
        spans.append(step_span)
        yield step_span
        step_span.end()

    tracer.trace_step_start = span
    return tracer


@pytest.fixture
def spans() -> list[Span]:
    return []


@pytest.fixture
def dispatcher(spans: list[Span]) -> AgentDispatcher:
    topic_manager = Mock(spec=AgentClassTopicManager)
    topic_manager.get_stream = Mock(return_value=("stream", "agent._AnsweringAgent.*"))
    dispatcher = AgentDispatcher(
        agent=_AnsweringAgent,
        agent_config=CONFIG,
        nc=Mock(),
        js=Mock(spec=JetStreamContext),
        redis=Mock(),
        topic_manager=topic_manager,
        locale_handler=Mock(spec=AgentLocaleHandler),
    )
    dispatcher.step_store = Mock(
        was_called_with_events=AsyncMock(return_value=False), report_execution_context_with_events=AsyncMock()
    )
    dispatcher.agent_run_tracer = _tracer(spans)
    dispatcher._build_method_kwargs = AsyncMock(return_value=EventsAndKwargs(events=[], kwargs={"event": StartEvent()}))
    return dispatcher


async def _execute(dispatcher: AgentDispatcher, step_method) -> None:
    await dispatcher.execute_step(
        StartEvent(),
        step_method,
        {},
        RunContext.for_topic(dispatcher.redis, TOPIC),
        ThreadContext.for_topic(dispatcher.redis, TOPIC),
        TOPIC,
        CONFIG,
    )


@pytest.mark.asyncio
async def test_a_refused_result_ends_the_run_with_an_exception_event(dispatcher, spans) -> None:
    published: list[BaseEvent] = []
    dispatcher.publish_event = _refusing_stop_events(published)

    await _execute(dispatcher, _AnsweringAgent.answer_step)

    assert [type(event) for event in published] == [ExceptionEvent]
    assert published[0].message == "nats: maximum payload exceeded"
    assert spans[0].status.status_code == StatusCode.ERROR


@pytest.mark.asyncio
async def test_a_refused_result_of_an_optional_step_is_only_logged(dispatcher, spans) -> None:
    published: list[BaseEvent] = []
    dispatcher.publish_event = _refusing_stop_events(published)

    await _execute(dispatcher, _AnsweringAgent.optional_step)

    assert published == []
    assert spans[0].status.status_code == StatusCode.ERROR


@pytest.mark.asyncio
async def test_a_published_result_marks_the_step_succeeded(dispatcher, spans) -> None:
    dispatcher.publish_event = AsyncMock()

    await _execute(dispatcher, _AnsweringAgent.answer_step)

    assert [type(call.args[0]) for call in dispatcher.publish_event.await_args_list] == [StopEvent]
    assert spans[0].status.status_code == StatusCode.OK
