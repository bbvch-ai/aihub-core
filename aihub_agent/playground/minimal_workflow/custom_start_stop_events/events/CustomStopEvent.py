from aihub_lib.nats.events import StopEvent
from playground.minimal_workflow.custom_start_stop_events.events.CustomStartEvent import PydanticPayload


class CustomStopEvent(StopEvent):
    payload: PydanticPayload
