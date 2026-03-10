import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from bson import ObjectId
from swiss_ai_hub.core.nats.events.process.stop.ProcessStopEvent import ProcessStopEvent
from swiss_ai_hub.core.nats.events.work.process.ProcessWorkEvent import ProcessWorkEvent
from swiss_ai_hub.core.nats.events.work.WorkEvent import WorkEvent
from swiss_ai_hub.core.nats.events.work_request.WorkRequestEvent import WorkRequestEvent
from swiss_ai_hub.core.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from swiss_ai_hub.core.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from swiss_ai_hub.core.nats.topics import ProcessInstanceTopic
from swiss_ai_hub.core.nats.topics.process.ProcessClassTopic import ProcessClassTopic

from swiss_ai_hub.process.delegators.AbstractEntityDelegator import AbstractEntityDelegator

logger = logging.getLogger(__name__)


class ProcessDelegator(AbstractEntityDelegator):
    """
    The process delegator is responsible for connecting one terminated process to the input of another.
    Note that processes do not 'delegate' work to each other. Hence, the 'handle_process_step_output' is completely
    empty.
    However, process can very well be triggered by the termination of another process, hence, the delegator
    finds all Process.In annotations and creates a nats subscription to these processes and their respective
    ProcessStopEvent, translating them into ProcessWorkEvents and publishing them into their own process topic.
    Hence, the process delegator acts as a bridge between processes.
    Note that Process.In is only valid for a process start.
    Why?
    Because processes never explicitly delegate to another process, hence, there is never a specific
    association between two different process walkthrough's. Hence, it is only valid that the completed
    walkthrough of one process triggers a fresh walkthrough of another, but never that one walkthrough
    is like a 'sub walkthrough' of another.
    """

    async def start(self):
        """
        The process delegator must find all process steps that are configured with Process.In and
        create a nats subscription to these processes with the relevant process stop event.
        """
        await super().start()
        logger.debug(f"Starting external-process delegator for process class '{self.process_class}'")
        for work_event, process_in in self.process_class.get_events_with_process_in():
            logger.debug(f"Found process step with process work input: '{work_event.event_name_from_class()}'")
            stop_events = work_event.get_stop_event_type()

            for stop_event in stop_events:
                process_instance_topic_manager = ProcessInstanceTopicManager(
                    process_class=process_in.process_class,
                    process_id=process_in.process_id,
                )

                subscription = ProcessNCSubscriber.for_specific_work_event_in_process_instance(
                    nc=self.nc,
                    topic_manager=process_instance_topic_manager,
                    handler=self.handle_process_step_input_factory(
                        work_event_type=work_event,
                        is_process_start=True,  # Being triggered from another process is only valid for a process start
                    ),
                    event=stop_event,
                    subscriber_name=f"{self.process_class.__name__}ProcessDelegator",
                )
                await subscription.start()
                self.subscriptions.append(subscription)

                logger.debug(
                    f"Subscribed to external-process '{process_in.process_class}' "
                    f"with id '{process_in.process_id}' for event '{stop_event.event_name_from_class()}'"
                )

    def handle_process_step_input_factory(
        self, work_event_type: type[ProcessWorkEvent], is_process_start: bool
    ) -> Callable[[ProcessStopEvent, ProcessInstanceTopic], Awaitable[None]]:
        async def _handle_process_step_input(
            event: Annotated[ProcessStopEvent, "The incoming process stop event to handle."],
            topic: Annotated[ProcessInstanceTopic, "The parsed topic of the event."],
        ):
            logger.debug(f"Handling process stop event: {event.event_name}")
            work_event: WorkEvent = work_event_type(process_stop_event=event)
            process_walkthrough_id = str(ObjectId())
            logger.debug(f"Creating new walkthrough with ID {process_walkthrough_id}")

            await self._publish_work_event(
                work_event=work_event,
                process_walkthrough_id=process_walkthrough_id,
            )

        return _handle_process_step_input

    async def handle_process_step_output(self, event: WorkRequestEvent, topic: ProcessClassTopic):
        # The ProcessOutput Event is already published in the right format anyways
        return
