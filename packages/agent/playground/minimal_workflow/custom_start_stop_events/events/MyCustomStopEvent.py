from swiss_ai_hub.core.nats.events.control.stop.StopEvent import StopEvent

from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStartEvent import PydanticPayload


class MyCustomStopEvent(StopEvent):
    payload: PydanticPayload
