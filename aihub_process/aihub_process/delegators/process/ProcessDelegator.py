import logging
from typing import Annotated, Awaitable, Callable, Type

from aihub_lib.nats.events import ProcessStopEvent, WorkRequestEvent
from aihub_lib.nats.events.work.process.ProcessWorkEvent import ProcessWorkEvent
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager
from aihub_lib.nats.topics import ProcessTopic
from bson import ObjectId

from aihub_process.delegators.AbstractEntityDelegator import AbstractEntityDelegator

logger = logging.getLogger(__name__)


class ProcessDelegator(AbstractEntityDelegator):
    """
    The process delegator is responsible for connecting one terminated process to the input of another.
    Note that processes do not 'delegate' work to each other. Hence, the 'handle_process_step_output' is completely
    empty.
    However, process can very well be triggered by the termination of another process, hence, the delegator
    finds all Process.In annotations and creates a nats subscription to these processes and their respective
    ProcessStopEvent, translating them into AgentWorkEvents and publishing them into their own process topic.
    Hence, the process delegator acts as a bridge between processes.
    Note that Process.In is only valid for a process start.
    Why?
    Because processes never explicitly delegate to another process, hence, there is never a specific
    association between two different process walkthrough's. Hence, it is only valid that the complted
    walkthrough of one process triggers a fresh walkthrough of another, but never that one walkthrough
    is like a 'sub walkthrough' of another.
    """

    async def start(self):
        """
        The process delegator must find all process steps that are configured with Process.In and
        create a nats subscription to these processes with the relevant process stop event.
        """
        await super().start()
        logger.debug(f"Starting external-process delegator for process '{self.process_id}'")
        for work_event, config in self.process_class.get_events_with_process_in():
            logger.debug(f"Found process step with process work input: '{work_event.event_name_from_class()}'")
            stop_events = work_event.get_stop_event_type()

            for stop_event in stop_events:
                process_instance_topic_manager = ProcessInstanceTopicManager(
                    process_class=config.process_class,
                    process_id=config.process_id,
                )

                subscription = ProcessNCSubscriber.for_specific_work_request_event_in_process_instance(
                    nc=self.nc,
                    topic_manager=process_instance_topic_manager,
                    handler=self.handle_process_step_input_factory(
                        work_event_type=work_event,
                        is_process_start=True,  # Being triggered from another process is only valid for a process start
                    ),
                    event=stop_event,
                )
                await subscription.start()
                self.subscriptions.append(subscription)

                logger.debug(
                    f"Subscribed to external-process '{config.process_class}' with id '{config.process_id}' for event '{stop_event.event_name_from_class()}'"
                )

    def handle_process_step_input_factory(
        self, work_event_type: Type[ProcessWorkEvent], is_process_start: bool
    ) -> Callable[[ProcessStopEvent, ProcessTopic], Awaitable[None]]:
        async def _handle_process_step_input(
            event: Annotated[ProcessStopEvent, "The incoming process stop event to handle."],
            topic: Annotated[ProcessTopic, "The parsed topic of the event."],
        ):
            logger.debug(f"Handling process stop event: {event.event_name}")
            work_event = work_event_type(process_stop_event=event)
            process_walkthrough_id = str(ObjectId())
            logger.debug(f"Creating new walkthrough with ID {process_walkthrough_id}")

            walkthrough_topic_manager = ProcessWalkthroughTopicManager.from_process_instance_topic_manager(
                topic_manager=self.topic_manager, process_walkthrough_id=process_walkthrough_id
            )
            subject = walkthrough_topic_manager.get_subject_for_work_event_in_walkthrough(
                event_name=work_event.event_name,
                event_id=work_event.event_id,
            )
            logger.debug(f"Publishing work {work_event} to subject '{subject}'")
            await self.js_publisher.publish_event(work_event, subject)

        return _handle_process_step_input

    async def handle_process_step_output(self, event: WorkRequestEvent, topic: ProcessTopic):
        # The ProcessOutput Event is already published in the right format anyways
        return
