from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopInput import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopInputResponseEvent import (
    HumanInTheLoopInputResponseEvent,
)


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
