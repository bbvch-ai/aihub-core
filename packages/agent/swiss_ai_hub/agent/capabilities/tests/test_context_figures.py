"""Figures in the composed context reach the model on the question, held to the profile's and the model's image rules."""

from unittest.mock import patch

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock
from llama_index.llms.openai.utils import to_openai_message_dict
from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter

from swiss_ai_hub.agent.capabilities.conversation.context_figures import ContextFigures

FIGURE_A = "http://seaweedfs-s3:9000/docs/Settings/__figures__/Guide_(1)_docx/figure_00000000000000aa.png"
FIGURE_B = "http://seaweedfs-s3:9000/docs/Settings/__figures__/Guide_(1)_docx/figure_00000000000000bb.png"


def _llm(accept_images: bool = True) -> LLMConfig:
    return LLMConfig(model_name="text-generation/vision", default_parameter=LLMParameter(accept_images=accept_images))


def _model(**model_info: object):
    return patch.object(LLMConfig, "get_model_info", return_value={"model_info": model_info})


def _history(*figures: str, question: ChatMessage | None = None) -> list[ChatMessage]:
    context = [
        TextBlock(text="<REFERENCE_DOCUMENT>Settings"),
        *(ImageBlock(url=url) for url in figures),
        TextBlock(text="</REFERENCE_DOCUMENT>"),
    ]
    return [
        ChatMessage(role=MessageRole.SYSTEM, blocks=context),
        question or ChatMessage(role=MessageRole.USER, content="What is Busylight set to?"),
    ]


def _urls(message: ChatMessage) -> list[str]:
    return [str(block.url) for block in message.blocks if block.block_type == "image"]


class TestContextFigures:
    def test_figures_leave_the_system_message_for_the_question(self) -> None:
        with _model():
            system, question = ContextFigures.on_question(_history(FIGURE_A, FIGURE_B), _llm())

        assert _urls(system) == []
        assert [b.text for b in system.blocks] == ["<REFERENCE_DOCUMENT>Settings", "</REFERENCE_DOCUMENT>"]
        assert _urls(question) == [FIGURE_A, FIGURE_B]
        assert question.blocks[-1].text == "What is Busylight set to?"

    def test_the_provider_receives_the_figures(self) -> None:
        with _model():
            messages = ContextFigures.on_question(_history(FIGURE_A), _llm())

        sent = [to_openai_message_dict(message) for message in messages]

        assert sent[1]["content"][0] == {"type": "image_url", "image_url": {"url": FIGURE_A}}

    def test_a_history_without_figures_is_returned_unchanged(self) -> None:
        history = _history()

        assert ContextFigures.on_question(history, _llm()) is history

    def test_a_profile_without_images_drops_the_figures(self) -> None:
        with _model():
            system, question = ContextFigures.on_question(_history(FIGURE_A), _llm(accept_images=False))

        assert _urls(system) == [] and _urls(question) == []

    def test_a_model_that_cannot_read_images_drops_the_figures(self) -> None:
        with _model(supports_vision=False):
            messages = ContextFigures.on_question(_history(FIGURE_A), _llm())

        assert sum(len(_urls(message)) for message in messages) == 0

    def test_the_users_own_images_are_kept_first_within_max_images(self) -> None:
        own = ChatMessage(
            role=MessageRole.USER,
            blocks=[TextBlock(text="And this photo?"), ImageBlock(url="https://example.test/photo.png")],
        )
        with _model(max_images=2):
            _, question = ContextFigures.on_question(_history(FIGURE_A, FIGURE_B, question=own), _llm())

        assert _urls(question) == [FIGURE_A, "https://example.test/photo.png"]

    def test_figures_after_a_non_user_message_become_a_user_turn(self) -> None:
        history = [*_history(FIGURE_A)[:1], ChatMessage(role=MessageRole.ASSISTANT, content="Let me check.")]
        with _model():
            messages = ContextFigures.on_question(history, _llm())

        assert messages[-1].role == MessageRole.USER
        assert _urls(messages[-1]) == [FIGURE_A]

    def test_a_system_message_holding_only_figures_is_removed(self) -> None:
        history = [ChatMessage(role=MessageRole.SYSTEM, blocks=[ImageBlock(url=FIGURE_A)]), _history()[1]]
        with _model():
            messages = ContextFigures.on_question(history, _llm())

        assert [message.role for message in messages] == [MessageRole.USER]
        assert _urls(messages[0]) == [FIGURE_A]
