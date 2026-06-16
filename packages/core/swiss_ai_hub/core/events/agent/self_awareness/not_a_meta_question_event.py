from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class NotAMetaQuestionEvent(ControlEvent):
    """
    Internal "all-clear" gate signal: the user's message is a normal task, not a meta
    question about the agent. Control-only (not displayed) — its sole purpose is to
    release the agent's normal entry steps, which depend on it so they cannot start
    until meta-question detection has cleared the message.
    """

    reasoning: Annotated[str, Field(description="Why the message was classified as a normal (non-meta) request.")]
