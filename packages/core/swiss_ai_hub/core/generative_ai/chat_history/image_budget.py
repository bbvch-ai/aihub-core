from llama_index.core.base.llms.types import ChatMessage


class ImageBudget:
    """Keeps the images in a prompt within what the model may receive, at the expense of the oldest turns.

    Chat clients resend every earlier image on each turn, so a conversation outgrows a model's image limit (vLLM's
    `--limit-mm-per-prompt`, curated as `max_images`) long after the image that tipped it was answered. The earlier
    images go first; the last turn is what is being asked, so it is never touched and its caller refuses when that
    turn alone is over the limit.
    """

    @staticmethod
    def count(messages: list[ChatMessage]) -> int:
        """The image blocks across `messages`."""
        return sum(ImageBudget._image_count(message) for message in messages)

    @staticmethod
    def fit(messages: list[ChatMessage], max_images: int) -> list[ChatMessage]:
        """`messages` with images dropped from the oldest earlier turns until at most `max_images` remain beside the
        last turn's; a turn left with nothing to send is dropped with them."""
        if not messages:
            return messages
        earlier, last = messages[:-1], messages[-1]
        excess = ImageBudget.count(messages) - max_images
        fitted: list[ChatMessage] = []
        for message in earlier:
            images = ImageBudget._image_count(message)
            if excess <= 0 or images == 0:
                fitted.append(message)
                continue
            dropped = min(images, excess)
            excess -= dropped
            trimmed = ImageBudget._without_oldest_images(message, dropped)
            if trimmed.blocks:
                fitted.append(trimmed)
        return [*fitted, last]

    @staticmethod
    def without_images(messages: list[ChatMessage]) -> list[ChatMessage]:
        """`messages` with every image removed, for a model that is not sent images at all."""
        stripped = [
            ImageBudget._without_oldest_images(message, ImageBudget._image_count(message)) for message in messages
        ]
        return [message for message in stripped if message.blocks]

    @staticmethod
    def _image_count(message: ChatMessage) -> int:
        return sum(1 for block in message.blocks if block.block_type == "image")

    @staticmethod
    def _without_oldest_images(message: ChatMessage, number_to_drop: int) -> ChatMessage:
        if number_to_drop == 0:
            return message
        kept_blocks = []
        for block in message.blocks:
            if block.block_type == "image" and number_to_drop > 0:
                number_to_drop -= 1
                continue
            kept_blocks.append(block)
        return message.model_copy(update={"blocks": kept_blocks})
