from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopInput,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopInputResponseEvent,
)


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
