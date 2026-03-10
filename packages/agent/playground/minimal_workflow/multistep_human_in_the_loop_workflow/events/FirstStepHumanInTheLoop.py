from swiss_ai_hub.core.nats.events.human_in_the_loop.HumanInTheLoopInput import HumanInTheLoopInput
from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.nats.events.human_in_the_loop.response.HumanInTheLoopInputResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
