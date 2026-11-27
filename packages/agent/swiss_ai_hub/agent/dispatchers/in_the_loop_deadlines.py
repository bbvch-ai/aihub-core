import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

from nats.js import JetStreamContext
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoopExceptionEvent,
    AgentInTheLoopRequestEvent,
    AgentInTheLoopResponseEvent,
    BotInTheLoopRequestEvent,
    BotInTheLoopResponseEvent,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
    InTheLoopTimeoutEvent,
)
from swiss_ai_hub.core.topic_managers import AgentClassTopicManager, AgentThreadTopicManager

from swiss_ai_hub.agent.context.run.run_context import RunContext

logger = logging.getLogger(__name__)

type InTheLoopRequest = HumanInTheLoopRequestEvent | AgentInTheLoopRequestEvent | BotInTheLoopRequestEvent


class InTheLoopDeadlines:
    """
    Deadlines of the questions a run asks humans, agents and bots, kept by NATS rather than by a process.

    A request with `timeout_seconds` gets its timeout event published ahead of time as a scheduled message, which
    JetStream delivers onto the run's own control subject at the deadline, so the fallback fires even when every
    dispatcher restarted in between. The first of answer and timeout settles the request; the other is dropped.
    """

    _DEADLINE_KEY = "_in_the_loop_deadline:{request_event_id}"
    _SETTLED_KEY = "_in_the_loop_settled:{request_event_id}"

    def __init__(self, js: JetStreamContext, topic_manager: AgentClassTopicManager):
        self.js = js
        self.topic_manager = topic_manager

    async def arm(
        self,
        request: Annotated[InTheLoopRequest, "A request whose `timeout_seconds` is set."],
        thread_topic_manager: Annotated[AgentThreadTopicManager, "The asking run's topics."],
        run_context: RunContext,
    ) -> None:
        """Schedules the request's timeout. Called before the request is published, so no answer can precede it."""
        if request.timeout_seconds is None:
            return
        timeout = request.timed_out()
        deadline = datetime.now(UTC) + timedelta(seconds=math.ceil(request.timeout_seconds))
        deadline_subject = self.topic_manager.get_subject_for_in_the_loop_deadline(request.event_id)
        target = thread_topic_manager.get_subject_for_control_event_in_thread(timeout.event_name, timeout.event_id)
        await run_context.set(self._DEADLINE_KEY.format(request_event_id=request.event_id), deadline_subject)
        await self.js.publish(
            deadline_subject,
            timeout.model_dump_json(serialize_as_any=True).encode(),
            headers={
                "Nats-Schedule": f"@at {deadline.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "Nats-Schedule-Target": target,
            },
        )

    async def settles(
        self,
        event: Annotated[BaseEvent, "An incoming control event."],
        run_context: RunContext,
    ) -> Annotated[bool, "False for the answer or timeout of a request that is settled already."]:
        """
        Lets the first answer or timeout of a request with a deadline through, and only that one.

        A request without a deadline is never tracked here, so its answers pass as they always did. The winner
        cancels the pending timeout; a timeout that fired anyway, or a backup restore replaying an overdue one, finds
        the request settled and is dropped.
        """
        request_event_id = self.request_answered_by(event)
        if request_event_id is None:
            return True
        deadline_subject = await run_context.get(self._DEADLINE_KEY.format(request_event_id=request_event_id))
        if deadline_subject is None:
            return True
        if not await run_context.set_if_absent(self._SETTLED_KEY.format(request_event_id=request_event_id), True):
            logger.info(f"Dropped {event.event_name}: request {request_event_id} was settled already")
            return False
        if not event.is_in_the_loop_timeout_event:
            await self.js.purge_stream(self.topic_manager.get_stream()[0], subject=deadline_subject)
        return True

    @staticmethod
    def request_answered_by(event: BaseEvent) -> str | None:
        """The `event_id` of the in-the-loop request an event answers or times out, None for any other event."""
        if event.is_in_the_loop_timeout_event:
            return cast(InTheLoopTimeoutEvent, event).request_event_id
        if event.is_aitl_response_event or event.is_aitl_exception_event:
            return cast(AgentInTheLoopResponseEvent | AgentInTheLoopExceptionEvent, event).request_event_id
        if event.is_hitl_response_event or event.is_bitl_response_event:
            return cast(HumanInTheLoopResponseEvent | BotInTheLoopResponseEvent, event).request_event.event_id
        return None
