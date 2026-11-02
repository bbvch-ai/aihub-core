from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class NotAMetaQuestionEvent(ControlAndDisplayEvent):
    """
    Internal "all-clear" gate signal: the user's message is a normal task, not a meta
    question about the agent. It releases the agent's normal entry steps, which depend
    on it so they cannot start until meta-question detection has cleared the message.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.not_a_meta_question_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.not_a_meta_question_event.description"
    )

    reasoning: Annotated[str, Field(description="Why the message was classified as a normal (non-meta) request.")]
