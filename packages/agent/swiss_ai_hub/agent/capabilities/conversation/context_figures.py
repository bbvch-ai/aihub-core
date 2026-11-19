from llama_index.core.base.llms.types import ChatMessage, ContentBlock, MessageRole, TextBlock
from swiss_ai_hub.core.generative_ai import ImageBudget, LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.conversation.image_admission import ImageAdmission


class ContextFigures:
    """Moves the figures of composed context out of system messages, onto the question the model is asked.

    Retrieved documents reach the model in the system head, and llama-index sends a system message as text only
    (`to_openai_message_dict`), so every figure a knowledge search found was dropped on the way to the provider. On
    the question they are held to the rules the user's own images follow: none for a profile or model that takes no
    images, and within the model's `max_images`, the user's own images first. They go ahead of the question's text,
    introduced as figures of the retrieved documents: without that line, Qwen3.5 under a prompt that allows only the
    retrieved context took them for the user's own pictures and ignored them in three of five runs, with it in none
    of six.
    """

    @staticmethod
    def on_question(history: list[ChatMessage], llm: LLMConfig, t: LocaleHandler) -> list[ChatMessage]:
        """`history` with every system message's images moved ahead of the last message's text, as a user turn."""
        figures = [
            block
            for message in history
            if message.role == MessageRole.SYSTEM
            for block in message.blocks
            if block.block_type == "image"
        ]
        if not figures:
            return history
        stripped = [ContextFigures._without_images(message) for message in history]
        without_figures = [message for message in stripped if message.blocks]
        if not ImageAdmission.accepts_images(llm):
            return without_figures
        max_images = llm.max_images
        if max_images is not None:
            room = max(max_images - ImageBudget.count(without_figures[-1:]), 0)
            figures = figures[:room]
        introduced = [TextBlock(text=t("agent.conversation.prompt.context_figures")), *figures] if figures else []
        with_figures = ContextFigures._onto_question(without_figures, introduced)
        return with_figures if max_images is None else ImageBudget.fit(with_figures, max_images)

    @staticmethod
    def _without_images(message: ChatMessage) -> ChatMessage:
        if message.role != MessageRole.SYSTEM:
            return message
        return message.model_copy(update={"blocks": [b for b in message.blocks if b.block_type != "image"]})

    @staticmethod
    def _onto_question(history: list[ChatMessage], figures: list[ContentBlock]) -> list[ChatMessage]:
        if not figures:
            return history
        question = history[-1] if history else None
        if question is None or question.role != MessageRole.USER:
            return [*history, ChatMessage(role=MessageRole.USER, blocks=figures)]
        return [*history[:-1], question.model_copy(update={"blocks": [*figures, *question.blocks]})]
