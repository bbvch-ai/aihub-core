import time
from typing import Annotated, Any, Self

from bson import ObjectId
from pydantic import Field

from swiss_ai_hub.core.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from swiss_ai_hub.core.nats.events.work.WorkEvent import WorkEvent
from swiss_ai_hub.core.processes.ProcessConfig import ProcessConfig


class ProcessStartEvent(WorkEvent):
    """
    An event signaling the start of a new process walkthrough.
    """

    process_config: Annotated["dict[str, Any] | None", Field(description="Process configuration")] = None

    @classmethod
    def from_raw_data(
        cls,
        raw_event_data: dict[str, Any],
        human_in: HumanInSpecs,
        process_config: ProcessConfig,
        **args,
    ) -> Self:
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "_parent_event_names": human_in.event_specs.event_parents,
            "_event_name": human_in.event_specs.event_name,
            "process_config": process_config.model_dump(),
        }
        return cls.deserialize_event(json_data)
