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
    def __init__(self, nc: NATS, js: JetStreamContext):
        self.nc_publisher = NCPublisher(nc)
        self.js_publisher = JSPublisher(js)

    async def distribute_event(self, external_event: ExternalProcessEvent, user: UserIdentity | None = None):
        if external_event.event.is_process_start_event:
            process_walkthrough_id = str(ObjectId())
        else:
            assert external_event.process_walkthrough_id, "Process Walkthrough ID missing for non-start event"
            process_walkthrough_id = external_event.process_walkthrough_id

        if external_event.event.is_human_work_event or external_event.event.is_program_work_event:
            await self._handle_work_event(process_walkthrough_id, external_event, user)
        else:
            raise ValueError(f"Received event of unhandled type: {external_event.event.event_name}")

    async def _handle_work_event(
        self,
        process_walkthrough_id: str,
        external_event: ExternalProcessEvent,
        user: UserIdentity | None = None,
    ):
        event = external_event.event.model_copy(deep=True)
        event.event_id = str(ObjectId())
        event.submitted_by = user.model_copy()
        event.submitted_by.profile_image = None
        topic_manager = ProcessWalkthroughTopicManager(
            process_walkthrough_id=process_walkthrough_id,
            process_class=external_event.process_class,
            process_id=external_event.process_id,
        )
        subject = topic_manager.get_subject_for_work_event_in_walkthrough(
            event_name=event.event_name,
            event_id=event.event_id,
        )
        await self.js_publisher.publish_event(event, subject)
