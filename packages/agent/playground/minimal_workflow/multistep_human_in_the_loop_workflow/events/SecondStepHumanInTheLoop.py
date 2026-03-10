from swiss_ai_hub.core.nats.events.human_in_the_loop import HumanInTheLoopInput
from swiss_ai_hub.core.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
