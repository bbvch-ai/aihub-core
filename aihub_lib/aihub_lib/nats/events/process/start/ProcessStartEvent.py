import time
from typing import Annotated, Any

from bson import ObjectId
from pydantic import Field

from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.work.WorkEvent import WorkEvent
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessStartEvent(WorkEvent):
    """
    An event signaling the start of a new process walkthrough.
    """

    process_config: Annotated["dict[str, Any] | None", Field(description="Process configuration")] = None

    pass

    @classmethod
    def from_raw_data(
        cls,
        raw_event_data: dict[str, Any],
        human_in: HumanInSpecs,
        process_config: ProcessConfig,
    ) -> "ProcessStartEvent":
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "_parent_event_names": human_in.event_specs.event_parents,
            "_event_name": human_in.event_specs.event_name,
            "process_config": process_config.model_dump(),
        }
        return ProcessStartEvent.deserialize_event(json_data)
