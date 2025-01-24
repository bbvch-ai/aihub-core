from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
)
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoop):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
