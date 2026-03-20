from swiss_ai_hub.core.events.agent import StopEvent

from playground.minimal_workflow.custom_start_stop_events.events.my_custom_start_event import PydanticPayload


class MyCustomStopEvent(StopEvent):
    payload: PydanticPayload
