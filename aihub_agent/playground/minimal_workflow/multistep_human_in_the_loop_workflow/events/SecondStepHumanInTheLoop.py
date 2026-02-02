from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
