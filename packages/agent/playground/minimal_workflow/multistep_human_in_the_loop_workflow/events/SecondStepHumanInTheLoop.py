from swiss_ai_hub.core.nats.events.human_in_the_loop.HumanInTheLoopInput import HumanInTheLoopInput
from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.nats.events.human_in_the_loop.response.HumanInTheLoopInputResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
