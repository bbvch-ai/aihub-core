from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class FollowUpQuestionsEvent(DisplayEvent):
    """
    Carries follow-up questions the user might want to ask next, produced by the agent after each
    answer. These are non-blocking UI suggestions — unlike the namespace-selection
    ``FollowUpQuestion`` HITL events, the user is never required to answer them.

    Regenerated every turn since they depend on the latest answer.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.follow_up_questions_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.follow_up_questions_event.description"
    )

    questions: Annotated[list[str], Field(description="The suggested follow-up questions for the user.")]
