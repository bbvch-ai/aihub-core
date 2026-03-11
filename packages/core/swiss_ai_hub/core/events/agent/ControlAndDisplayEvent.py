from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent
from swiss_ai_hub.core.events.agent.display.DisplayEvent import DisplayEvent


class ControlAndDisplayEvent(ControlEvent, DisplayEvent):
    """
    Frequently, events should be both control- and display events. This could be easily achieved
    using multi-inheritance. However, this can lead to a problem: When an agent encounters an unknown
    event class, it will create an instance of the lowest-level known parent class.
    When a class is both a control and display event, we have two parent classes with the same level,
    hence, the deserializer in the BaseEvent treats this special case by instantiating this ControlAndDisplayEvent.
    It is not mandatory to use this class, it is totally fine to do multi-inheritance from display and control event,
    however, for simplicity, it is considered good practice to use this class instead.
    """

    pass
