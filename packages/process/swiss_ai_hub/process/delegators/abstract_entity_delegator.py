import abc
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated, cast

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.process import WorkEvent
from swiss_ai_hub.core.events.process import WorkRequestEvent
from swiss_ai_hub.core.publishers import JSPublisher
from swiss_ai_hub.core.subscribers import ProcessJSSubscriber
from swiss_ai_hub.core.subscribers import ProcessNCSubscriber
from swiss_ai_hub.core.topic_managers import ProcessClassTopicManager
from swiss_ai_hub.core.topic_managers import ProcessInstanceTopicManager
from swiss_ai_hub.core.topic_managers import ProcessWalkthroughTopicManager
from swiss_ai_hub.core.topics import Topic
from swiss_ai_hub.core.topics import ProcessClassTopic

from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess

logger = logging.getLogger(__name__)


class AbstractEntityDelegator(abc.ABC):
    """
    The AbstractEntityDelegator is responsible for connecting process entities with the process workflow itself.
    Think of it this way: You define a process as a set of steps. Each step takes some work as input and
    delegates work to some other entity as part of its step output.

    The process itself is a dispatchable workflow which cares only about Work-Events and WorkRequest-Events.

    The delegator is responsible for connecting other entities such as humans, agents and programs to the process
    by listening to WorkRequest-Events that are delegated to them, and ensuring they receive the work request in
    a form that they understand. For example, a work request directed to an agent must be translated to
    a StartEvent for said agent and emitted as an event that said agent will receive.

    Similarly, work completed by an entity must be translated to a Work-Event that the process understands and can
    hence use to bring the process forwards. Staying with the agent example, this would mean that a StopEvent from
    an Agent is translated into a Work-Event and emitted in a way that the process can use it to move on to the next
    step.
    """

    def __init__(
        self,
        process_type: Annotated[type[AgenticProcess], "The agentic process defining steps and logic."],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        topic_manager: Annotated[ProcessClassTopicManager, "Manages event subjects."],
        queue_group: Annotated[str, "Queue group for the delegator's subscriptions."],
    ):
        self.process_class = process_type
        self.nc = nc
        self.js = js

        self.js_publisher = JSPublisher(f"{self.process_class.__name__}{self.__class__.__name__}", self.js)

        self.topic_manager = topic_manager

        self.queue_group = queue_group

        self.subscriptions: list[ProcessNCSubscriber | ProcessJSSubscriber] = []

    @abc.abstractmethod
    async def start(self):
        """
        In the simplest case, the delegator subscribes to the work requests emitted by this process and
        calls the `handle_process_step_output` method with the respective work request.
        Note that this is not very efficient, as each delegator (human, agent, program and process) will create
        this subscription and hence will receive work events of ALL types, not just the ones that it is interested in.

        However, this was a deliberate design decision: It reduces the precision of the delegator's subscription,
        but also reduces the number of subscriptions it needs to manage as well as the implementation complexity.

        As we can generally assume that a process may only consist of a few dozen steps at most, and given that
        the subscription we make here has a very limited scope (only this one process class), this is reasonable.

        Note that this method is abstract as it does not handle process inputs / work events at all! This is
        up to the specific delegator to implement.
        """
        subscription = ProcessJSSubscriber.for_process_class_work_request_events(
            nc=self.nc,
            topic_manager=self.topic_manager,
            handler=self.handle_process_step_output,
            queue_group=self.queue_group,
            js=self.js,
            subscriber_name=f"{self.process_class.__name__}{self.__class__.__name__}WorkRequestEvent",
        )
        await subscription.start()
        self.subscriptions.append(subscription)

    async def stop(self):
        """
        Stops all subscriptions created by this delegator.
        """
        for subscription in self.subscriptions:
            await subscription.stop()

    @abc.abstractmethod
    def handle_process_step_input_factory(
        self, work_event_type: type[WorkEvent], is_process_start: bool
    ) -> Callable[[BaseEvent, Topic], Awaitable[None]]:
        """
        A delegator must usually create some kind of subscription for each event from its entity of interest and map
        it to a work event to dispatch to the process. The connection between the received event type and the work
        event that must be emitted is usually given as part of the ProcessEntity.In configuration. Hence, this
        method helps to create a subscription that will map the received event to the work event that must be emitted.
        """
        pass

    @abc.abstractmethod
    async def handle_process_step_output(self, event: WorkRequestEvent, topic: ProcessClassTopic):
        """
        In the default implementation, this method will receive ALL WorkReqeustEvents returned in this process.
        Note that you must usually filter by class to ensure you only process events that match the entity type.
        """
        pass

    async def _publish_work_event(
        self,
        work_event: WorkEvent,
        process_walkthrough_id: str,
    ) -> None:
        if hasattr(self.topic_manager, "process_id"):
            topic_manager = cast(ProcessInstanceTopicManager, self.topic_manager)
            walkthrough_topic_manager = ProcessWalkthroughTopicManager.from_process_instance_topic_manager(
                topic_manager=topic_manager, process_walkthrough_id=process_walkthrough_id
            )
        else:
            walkthrough_topic_manager = ProcessWalkthroughTopicManager.from_process_class_topic_manager(
                topic_manager=self.topic_manager, process_walkthrough_id=process_walkthrough_id
            )
        subject = walkthrough_topic_manager.get_subject_for_work_event_in_walkthrough(
            event_name=work_event.event_name,
            event_id=work_event.event_id,
        )
        logger.debug(f"Publishing work {work_event} to subject '{subject}'")
        await self.js_publisher.publish_event(work_event, subject)
