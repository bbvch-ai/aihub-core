from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_choice_option import HumanInTheLoopChoiceOption

QUESTION_HEADER_LENGTH = 48
QUESTION_TEXT_LENGTH = 500


class HumanInTheLoopChoiceQuestion(BaseModel):
    """A question a client with a dialog shows with its options; the first option is the one the agent recommends."""

    id: Annotated[str, Field(min_length=1, max_length=64, description="Key the answer is returned under.")]
    header: Annotated[str, Field(max_length=QUESTION_HEADER_LENGTH, description="A short title for the question.")]
    question: Annotated[str, Field(min_length=1, max_length=QUESTION_TEXT_LENGTH, description="The question itself.")]
    options: Annotated[
        list[HumanInTheLoopChoiceOption],
        Field(min_length=1, max_length=3, description="The answers offered, the recommended one first."),
    ]
    allow_other: Annotated[bool, Field(description="Whether the user may write an answer of their own.")] = True
