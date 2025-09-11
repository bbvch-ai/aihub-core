import abc
import logging
from typing import Generic, TypeVar

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class AbstractPublisher(Generic[TEvent], abc.ABC):
    def _detect_and_log_subject_mismatch(self, event: TEvent, subject: str):
        if f".{AgentTopicManager.CONTROL_EVENT}." in subject and not event.is_control_event:
            logger.warning(f"Control event {event.event_name} is being published to a non-control subject: {subject}")

        if f".{AgentTopicManager.DISPLAY_EVENT}." in subject and not event.is_display_event:
            logger.warning(f"Display event {event.event_name} is being published to a non-display subject: {subject}")

        if f".{ProcessTopicManager.WORK_REQUEST_EVENT}." in subject and not event.is_work_request_event:
            logger.warning(
                f"Work-Request event {event.event_name} is being published to a non-work-request subject: {subject}"
            )

        if f".{ProcessTopicManager.WORK_EVENT}." in subject and not event.is_work_event:
            logger.warning(f"Work event {event.event_name} is being published to a non-work subject: {subject}")

    @abc.abstractmethod
    async def publish_event(self, event: TEvent, subject: str, **kwargs):
        pass
