import abc
import logging
from typing import Annotated, Literal, TypeVar

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topic_managers.process.process_topic_manager import ProcessTopicManager

logger = logging.getLogger(__name__)

# TypeVar for backward compatibility with existing imports
TEvent = TypeVar("TEvent", bound=BaseEvent)


class AbstractPublisher[TEvent: BaseEvent](abc.ABC):
    def __init__(
        self,
        name: Annotated[str, "Name of the publisher shown in otel"],
        protocol: Annotated[Literal["JetStream", "NATS"], "Protocol used to publish events, either JetStream or NATS"],
    ):
        self.name = name if name.endswith(f"{protocol}Publisher") else f"{name}{protocol}Publisher"

    def _detect_and_log_subject_mismatch(self, event: TEvent, subject: str):
        if f".{AgentTopicManager.CONTROL_EVENT}." in subject and not event.is_control_event:
            logger.warning(
                f"{self.name}: Control event {event.event_name} is being published to a non-control subject: {subject}"
            )

        if f".{AgentTopicManager.DISPLAY_EVENT}." in subject and not event.is_display_event:
            logger.warning(
                f"{self.name}: Display event {event.event_name} is being published to a non-display subject: {subject}"
            )

        if f".{ProcessTopicManager.WORK_REQUEST_EVENT}." in subject and not event.is_work_request_event:
            logger.warning(
                f"{self.name}: Work-Request event {event.event_name} is being published "
                f"to a non-work-request subject: {subject}"
            )

        if f".{ProcessTopicManager.WORK_EVENT}." in subject and not event.is_work_event:
            logger.warning(
                f"{self.name}: Work event {event.event_name} is being published to a non-work subject: {subject}"
            )

    @abc.abstractmethod
    async def publish_event(self, event: TEvent, subject: str, **kwargs):
        pass
