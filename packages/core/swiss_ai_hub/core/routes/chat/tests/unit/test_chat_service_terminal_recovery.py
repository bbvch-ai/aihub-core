import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.events.agent.semantic.llm.message import Message
from swiss_ai_hub.core.routes.chat.chat_service import ChatService


@pytest.mark.parametrize(
    ("streamed", "full_answer", "expected"),
    [
        pytest.param("", "whole answer", "whole answer", id="no-stream"),
        pytest.param("whole ", "whole answer", "answer", id="partial-stream"),
        pytest.param("whole answer", "whole answer", "", id="complete-stream"),
        pytest.param("diverged", "whole answer", "", id="diverged-stream"),
    ],
)
def test_missing_suffix_matches_live_response_contract(streamed: str, full_answer: str, expected: str):
    assert ChatService.missing_suffix(streamed, full_answer) == expected


def test_terminal_output_text_accepts_live_and_persisted_message_representations():
    core_message = Message.from_string(role="assistant", content="whole answer")
    llama_message = ChatMessage(role=MessageRole.ASSISTANT, content="whole answer")

    assert ChatService.terminal_output_text(None) == ""
    assert ChatService.terminal_output_text([]) == ""
    assert ChatService.terminal_output_text([llama_message]) == "whole answer"
    assert ChatService.terminal_output_text([core_message]) == "whole answer"
    assert ChatService.terminal_output_text([core_message.model_dump()]) == "whole answer"
