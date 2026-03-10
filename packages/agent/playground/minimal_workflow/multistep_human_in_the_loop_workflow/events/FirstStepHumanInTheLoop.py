from swiss_ai_hub.core.nats.events.human_in_the_loop import HumanInTheLoopInput
from swiss_ai_hub.core.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
