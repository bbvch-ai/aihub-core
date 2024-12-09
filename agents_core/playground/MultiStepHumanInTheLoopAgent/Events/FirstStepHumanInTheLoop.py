from lib_core.nats.events.human_in_the_loop import HumanInTheLoop, HumanInTheLoopRequestEvent, \
    HumanInTheLoopResponseEvent


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopRequestEvent):
    pass

class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopResponseEvent):
    pass

class FirstStepHumanInTheLoop(HumanInTheLoop):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent