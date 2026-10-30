from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event import (
    HumanInTheLoopChatRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_choice_question import (
    HumanInTheLoopChoiceQuestion,
)
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class HumanInTheLoopQuestionsRequestEvent(HumanInTheLoopChatRequestEvent):
    """A chat question that also carries its parts as choice questions.

    Clients with a dialog show the questions and answer with the JSON of the chosen answers; every other client shows
    `question` as text, and the next chat message answers it, so the request works everywhere a chat request does.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_questions_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_questions_request_event.description"
    )

    questions: Annotated[
        list[HumanInTheLoopChoiceQuestion],
        Field(min_length=1, max_length=3, description="The question's parts, for clients that show a dialog."),
    ]
