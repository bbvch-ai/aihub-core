from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock

from swiss_ai_hub.core.generative_ai.chat_history.image_budget import ImageBudget


def _turn(role: MessageRole, text: str, images: int = 0) -> ChatMessage:
    blocks = [TextBlock(text=text)] if text else []
    blocks += [ImageBlock(url=f"https://example.test/{text or 'image'}-{index}.png") for index in range(images)]
    return ChatMessage(role=role, blocks=blocks)


class TestCount:
    def test_images_are_counted_across_turns(self) -> None:
        history = [
            _turn(MessageRole.USER, "a", images=2),
            _turn(MessageRole.ASSISTANT, "b"),
            _turn(MessageRole.USER, "c", 1),
        ]

        assert ImageBudget.count(history) == 3


class TestFit:
    def test_a_history_within_the_limit_is_unchanged(self) -> None:
        history = [_turn(MessageRole.USER, "a", images=1), _turn(MessageRole.USER, "b", images=1)]

        assert ImageBudget.fit(history, max_images=2) == history

    def test_the_oldest_images_go_first(self) -> None:
        history = [
            _turn(MessageRole.USER, "old", images=2),
            _turn(MessageRole.USER, "newer", images=2),
            _turn(MessageRole.USER, "now", images=1),
        ]

        fitted = ImageBudget.fit(history, max_images=3)

        assert [ImageBudget.count([message]) for message in fitted] == [0, 2, 1]
        assert fitted[0].content == "old"

    def test_the_last_turn_is_never_touched(self) -> None:
        history = [_turn(MessageRole.USER, "old", images=1), _turn(MessageRole.USER, "now", images=4)]

        fitted = ImageBudget.fit(history, max_images=2)

        assert fitted[-1] == history[-1]
        assert ImageBudget.count(fitted[:-1]) == 0

    def test_a_turn_left_with_nothing_to_send_is_dropped(self) -> None:
        history = [_turn(MessageRole.USER, "", images=1), _turn(MessageRole.USER, "now", images=1)]

        fitted = ImageBudget.fit(history, max_images=1)

        assert [message.content for message in fitted] == ["now"]


class TestWithoutImages:
    def test_every_image_is_removed_and_the_text_kept(self) -> None:
        history = [_turn(MessageRole.USER, "look", images=2), _turn(MessageRole.USER, "", images=1)]

        stripped = ImageBudget.without_images(history)

        assert [message.content for message in stripped] == ["look"]
        assert ImageBudget.count(stripped) == 0
