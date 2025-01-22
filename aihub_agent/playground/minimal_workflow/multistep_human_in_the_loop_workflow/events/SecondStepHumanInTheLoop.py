from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
)
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoop):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
