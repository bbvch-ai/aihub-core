from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopInput,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopInputResponseEvent,
)


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
