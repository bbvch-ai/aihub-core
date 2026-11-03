"""A chat question that carries choice questions stays a chat request for every client and keeps its questions."""

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event import (
    HumanInTheLoopChatRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_choice_option import HumanInTheLoopChoiceOption
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_choice_question import (
    HumanInTheLoopChoiceQuestion,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_questions_request_event import (
    HumanInTheLoopQuestionsRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import HumanInTheLoopRequestEvent
from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic


def _request() -> HumanInTheLoopQuestionsRequestEvent:
    question = HumanInTheLoopChoiceQuestion(
        id="rows",
        header="Which rows",
        question="Which rows should the table keep?",
        options=[
            HumanInTheLoopChoiceOption(label="As understood", description="invoices from Lieferant GmbH"),
            HumanInTheLoopChoiceOption(label="Every row", description="Keep every row"),
        ],
    )
    return HumanInTheLoopQuestionsRequestEvent(
        question="- **Which rows:** invoices from Lieferant GmbH",
        questions=[question],
        topic=PartialAgentTopic(event_type="control", event_name="HumanInTheLoopChatResponseEvent"),
    )


def test_the_request_is_a_chat_request_that_round_trips_with_its_questions():
    request = _request()

    restored = HumanInTheLoopRequestEvent.deserialize_event(request.model_dump_json(by_alias=True))

    assert isinstance(restored, HumanInTheLoopQuestionsRequestEvent)
    assert isinstance(restored, HumanInTheLoopChatRequestEvent)
    assert restored.hitl_type == "chat"
    assert restored.questions == request.questions


def test_a_label_longer_than_the_dialog_shows_is_rejected():
    with pytest.raises(ValidationError):
        HumanInTheLoopChoiceOption(label="x" * 81, description="d")
