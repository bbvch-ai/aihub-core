from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
