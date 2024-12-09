from lib_core.nats.events.human_in_the_loop import HumanInTheLoop, HumanInTheLoopRequestEvent, \
    HumanInTheLoopResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopRequestEvent):
    pass

class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopResponseEvent):
    pass

class SecondStepHumanInTheLoop(HumanInTheLoop):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent