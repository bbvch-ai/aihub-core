import logging

from bson import ObjectId
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.nats.distributor.events.ExternalProcessEvent import ExternalProcessEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager

logger = logging.getLogger(__name__)


class ExternalProcessEventDistributor:
    """
    Process work events received from the user via an external system like API, WebSockets or Bots,
    transforming them into NATS/JetStream events that the rest of the system can consume.
    This class essentially bridges user actions back into the event-driven architecture.

    Users or external programs might send work events or request forms that define the user interface
    to submit such work events.
    The server must:
    - Validate that the user is authorized to submit work events for the given process walkthrough.
    - Publish the work event as a JetStream event, ensuring downstream agents or services can react.
    """

    def __init__(self, nc: NATS, js: JetStreamContext):
        self.nc_publisher = NCPublisher("ExternalProcessEventDistributor", nc)
        self.js_publisher = JSPublisher("ExternalProcessEventDistributor", js)

    async def distribute_event(self, external_event: ExternalProcessEvent, user: UserIdentity):
        """
        Entry point for distributing an external event (ExternalProcessEvent) to processes or other
        systems through NATs.
        """
        if external_event.event.is_process_start_event:
            process_walkthrough_id = str(ObjectId())
            external_event.process_walkthrough_id = process_walkthrough_id

        if external_event.event.is_human_work_event or external_event.event.is_program_work_event:
            # TODO: For human inputs, validate that the user is allowed to submit the given work
            await self._handle_work_event(external_event, user)
        else:
            raise ValueError(f"Received event of unhandled type: {external_event.event.event_name}")

    async def _handle_work_event(
        self,
        external_event: ExternalProcessEvent,
        user: UserIdentity,
    ):
        """Distributes a work event to the process walkthrough using JetStream"""
        event = external_event.event.model_copy(deep=True)
        event.event_id = str(ObjectId())
        event.submitted_by = user.model_copy()
        topic_manager = ProcessWalkthroughTopicManager(
            process_walkthrough_id=external_event.process_walkthrough_id,
            process_class=external_event.process_class,
            process_id=external_event.process_id,
        )
        subject = topic_manager.get_subject_for_work_event_in_walkthrough(
            event_name=event.event_name,
            event_id=event.event_id,
        )
        await self.js_publisher.publish_event(event, subject)
        return external_event
