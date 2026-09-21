from typing import Annotated, ClassVar, Literal

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString

type MetaQuestionCategory = Literal["identity", "capabilities", "behavior"]


class MetaQuestionDetectedEvent(ControlAndDisplayEvent):
    """
    Emitted when the user's message is a meta question about the agent itself —
    its identity, its capabilities, or why it behaved a certain way — rather than a
    task for the agent to perform. Routes the run to the self-awareness answer step
    instead of the agent's normal workflow.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.meta_question_detected_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.meta_question_detected_event.description"
    )

    user_query: Annotated[str, Field(description="The user message classified as a meta question.")]
    category: Annotated[
        MetaQuestionCategory,
        Field(description="Which aspect of the agent the question is about."),
    ]
    reasoning: Annotated[str, Field(description="Why the message was classified as a meta question.")]
