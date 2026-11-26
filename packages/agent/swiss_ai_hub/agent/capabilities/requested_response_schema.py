from typing import ClassVar

from swiss_ai_hub.core.events.agent import ResponseSchema

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext


class RequestedResponseSchema:
    """
    The JSON shape the message that started this run asked the answer in, if any.

    Read from the run context, where the dispatcher copies the start event, so the answering step, the meta-question
    gate and the completion all see the same request. A blueprint without support never has one: the API refuses the
    field for it, and an event sent around the API must not change how such an agent answers.
    """

    RUN_CONTEXT_KEY: ClassVar[str] = "response_schema"

    @classmethod
    async def of(cls, run_context: RunContext, blueprint: type[Agent]) -> ResponseSchema | None:
        if not blueprint.supports_response_schema():
            return None
        stored = await run_context.get(cls.RUN_CONTEXT_KEY)
        return ResponseSchema.model_validate(stored) if stored else None
