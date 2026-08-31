"""The deadline that stops a silent delegate wedging its caller.

`trigger_agent_in_the_loop` subscribes, publishes and returns. A delegate that never starts — an agent that is
offline, a mistyped `agent_id`, a profile that does not exist — publishes neither a stop event nor an exception, so
without this the caller's run simply never resumes. A fan-out makes it worse: one silent delegate wedges the batch.

Exercised against the scheduler directly rather than through a live dispatcher: everything it touches is the task set
and the `settle` callback, and standing up NATS to watch a timer expire would test the broker, not the deadline.
"""

import asyncio
from contextlib import contextmanager, suppress
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from swiss_ai_hub.core.events.agent import AgentInTheLoop, StartEvent, StopEvent
from swiss_ai_hub.core.subscribers import AgentNCSubscriber
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher

_SCHEDULE = AgentDispatcher._schedule_agent_in_the_loop_timeout


def _dispatcher() -> SimpleNamespace:
    """Everything the scheduler touches on `self` — deliberately not a real dispatcher."""
    return SimpleNamespace(_aitl_timeout_tasks=set())


def _topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="RAGAgent",
        agent_id="rag-support",
        thread_id="thread",
        display_id="display",
        run_id="run",
        event_type="control_event",
        event_name="StartEvent",
        event_id="event",
    )


def _request(timeout_seconds: float | None) -> AgentInTheLoop.request:
    return AgentInTheLoop.invoke(
        agent_class="RAGAgent",
        agent_id="rag-support",
        start_event=StartEvent(),
        timeout_seconds=timeout_seconds,
    )


def _recorder() -> tuple[list, callable]:
    settled = []

    async def settle(outcome, success: bool) -> None:
        settled.append((outcome, success))

    return settled, settle


@async_test
async def test_no_deadline_is_armed_when_none_is_asked_for():
    """The default has to stay 'wait forever', or every chat-facing delegation starts failing on a slow answer."""
    dispatcher = _dispatcher()
    _settled, settle = _recorder()

    assert _SCHEDULE(dispatcher, _request(None), settle, AgentInTheLoop.exception, _topic()) is None
    assert not dispatcher._aitl_timeout_tasks


@async_test
async def test_a_delegate_that_never_answers_is_failed_so_the_caller_can_continue():
    dispatcher = _dispatcher()
    settled, settle = _recorder()

    task = _SCHEDULE(dispatcher, _request(0.1), settle, AgentInTheLoop.exception, _topic())
    await asyncio.wait_for(task, timeout=2)

    assert len(settled) == 1
    outcome, success = settled[0]
    assert success is False
    assert outcome.is_aitl_exception_event
    assert "did not answer" in outcome.exception_event.message


@async_test
async def test_the_failure_names_the_delegation_it_belongs_to():
    """A fan-out caller cannot complete its batch from a failure it cannot attribute."""
    dispatcher = _dispatcher()
    settled, settle = _recorder()
    request = _request(0.1)

    await asyncio.wait_for(_SCHEDULE(dispatcher, request, settle, AgentInTheLoop.exception, _topic()), timeout=2)

    assert settled[0][0].request_event_id == request.event_id


@async_test
async def test_a_delegation_that_answers_first_cancels_its_deadline():
    """Left to expire, a delegation answered in a second keeps a task asleep for the whole deadline — and a
    dispatcher serving a steady stream of them accumulates one per delegation for no purpose."""
    dispatcher = _dispatcher()
    settled, settle = _recorder()

    task = _SCHEDULE(dispatcher, _request(30), settle, AgentInTheLoop.exception, _topic())
    # Let the timer actually start before cancelling it: cancelling a task the loop has never run discards the
    # coroutine unstarted, which is not the state a delegation that answered quickly leaves it in.
    await asyncio.sleep(0)
    task.cancel()
    # Awaited rather than yielded to once: the cancellation has to be delivered to the coroutine before the
    # done-callback that drops the strong reference can run.
    with suppress(asyncio.CancelledError):
        await task

    assert task.cancelled()
    assert not settled, "a delegation that answered must not also be reported as timed out"
    assert not dispatcher._aitl_timeout_tasks, "a finished timer must not stay in the set"


@async_test
async def test_a_fired_deadline_removes_itself_from_the_dispatcher():
    """The strong reference has to be dropped once the timer is done, or the set is a leak of its own."""
    dispatcher = _dispatcher()
    _settled, settle = _recorder()

    task = _SCHEDULE(dispatcher, _request(0.1), settle, AgentInTheLoop.exception, _topic())
    await asyncio.wait_for(task, timeout=2)
    await asyncio.sleep(0)

    assert not dispatcher._aitl_timeout_tasks


def _caller_topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="EmailClassificationAgent",
        agent_id="mailbox",
        thread_id="caller-thread",
        display_id="caller-display",
        run_id="caller-run",
        event_type="control_event",
        event_name="ClassifyMailStartEvent",
        event_id="caller-event",
    )


async def _suspending(*_args, **_kwargs) -> None:
    """A stand-in for real I/O that actually yields to the loop.

    Load-bearing: an `AsyncMock` whose await never suspends lets a coroutine run to completion inside one task step,
    which hides a pending cancellation entirely. The bug these tests exist for only appears at a real suspension
    point, so the doubles have to have one.
    """
    await asyncio.sleep(0)


def _wired_dispatcher(published: list) -> AgentDispatcher:
    """A dispatcher with only the collaborators `trigger_agent_in_the_loop` touches, and its real methods."""
    dispatcher = object.__new__(AgentDispatcher)
    dispatcher.agent = SimpleNamespace(__name__="EmailClassificationAgent")
    dispatcher.nc = SimpleNamespace()
    dispatcher._aitl_timeout_tasks = set()
    dispatcher.js_publisher = SimpleNamespace(publish_event=AsyncMock(side_effect=_suspending))
    dispatcher.agent_run_tracer = SimpleNamespace(
        start_aitl_wrapper_span=AsyncMock(return_value=None, side_effect=_suspending),
        end_aitl_wrapper_span=AsyncMock(side_effect=_suspending),
    )

    async def publish_event(event, _topic) -> None:
        await asyncio.sleep(0)
        published.append(event)

    dispatcher.publish_event = publish_event
    return dispatcher


@contextmanager
def _stub_subscriber():
    subscriber = SimpleNamespace(start=AsyncMock(side_effect=_suspending), stop=AsyncMock(side_effect=_suspending))
    with patch.object(AgentNCSubscriber, "for_thread_control_events", return_value=subscriber):
        yield subscriber


@async_test
async def test_a_timed_out_delegation_actually_reaches_the_caller():
    """Drives the real `settle` closure, which the scheduler tests above cannot: they pass their own recorder.

    The regression this pins had `settle` cancel the task it was running on, so the CancelledError landed at the
    unsubscribe and the synthesized exception was never published — while `settled` was already set, so the
    delegate's real answer could never resume the run either.
    """
    published: list = []
    dispatcher = _wired_dispatcher(published)

    with _stub_subscriber():
        await AgentDispatcher.trigger_agent_in_the_loop(dispatcher, _request(0.05), _caller_topic())
        await asyncio.sleep(0.3)

    failures = [event for event in published if event.is_aitl_exception_event]
    assert failures, "a delegation that timed out published nothing — the caller's run can never resume"
    assert "did not answer" in failures[0].exception_event.message


@async_test
async def test_a_delegation_that_answers_does_not_also_report_a_timeout():
    """The other half of the guard: the deadline must not fire behind an answer that already settled the run."""
    published: list = []
    dispatcher = _wired_dispatcher(published)

    with _stub_subscriber() as subscriber:
        await AgentDispatcher.trigger_agent_in_the_loop(dispatcher, _request(0.05), _caller_topic())
        deadline = next(iter(dispatcher._aitl_timeout_tasks))
        handler = AgentNCSubscriber.for_thread_control_events.call_args.kwargs["handler"]
        await handler(StopEvent(), _caller_topic())
        # Awaited so the cancelled deadline is actually stepped before the loop closes. Without it the coroutine is
        # collected unstarted and Python reports "coroutine was never awaited" against whichever test happens to
        # trigger the GC — noise that survives teardown and points at the wrong file.
        with suppress(asyncio.CancelledError):
            await deadline

    assert len(published) == 1, "the delegation settled twice — the answer and its deadline both reported"
    assert published[0].is_aitl_response_event
    assert subscriber.stop.await_count == 1
    assert not dispatcher._aitl_timeout_tasks, "the unfired deadline was left behind"
