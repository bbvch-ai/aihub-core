from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopInput import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopInputResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
