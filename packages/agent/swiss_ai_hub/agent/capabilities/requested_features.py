from typing import ClassVar

from swiss_ai_hub.core.events.agent import ChatFeature

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext


class RequestedFeatures:
    """
    Whether the user asked for a chat feature on the message that started this run.

    The dispatcher copies the start event into the run context, so every step and precondition of the run can
    ask, not only the ones consuming the `UserMessageEvent`. A feature the blueprint does not support never counts
    as requested: chat clients only offer supported toggles, but an API caller can send anything.
    """

    RUN_CONTEXT_KEY: ClassVar[str] = "requested_features"

    @classmethod
    async def contains(cls, feature: ChatFeature, run_context: RunContext, blueprint: type[Agent]) -> bool:
        if feature not in blueprint.supported_features():
            return False
        return feature.value in (await run_context.get(cls.RUN_CONTEXT_KEY) or [])
