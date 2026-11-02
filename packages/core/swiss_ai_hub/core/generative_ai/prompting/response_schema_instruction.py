from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole, TextBlock


class ResponseSchemaInstruction:
    """
    What a model asked for a JSON shape is told besides the shape.

    `response_format` makes every field required, so a model that finds no value invents one: on a live check an
    invoice without a date came back dated with the day from the agent's own system prompt. The instruction goes into
    the leading system message, since strict chat templates refuse a system message anywhere else.
    """

    TEXT: ClassVar[str] = (
        "The answer is a JSON object in the requested format. Take every value from the conversation and the "
        "documents provided. Where they do not state a value, use null, or leave it out where the format allows "
        "it; never infer, assume or invent one, and never use today's date for a date they do not give."
    )

    @staticmethod
    def added_to(messages: list[ChatMessage]) -> list[ChatMessage]:
        if messages and messages[0].role == MessageRole.SYSTEM:
            head = messages[0].model_copy(
                update={"blocks": [*messages[0].blocks, TextBlock(text=f"\n\n{ResponseSchemaInstruction.TEXT}")]}
            )
            return [head, *messages[1:]]
        return [ChatMessage(role=MessageRole.SYSTEM, content=ResponseSchemaInstruction.TEXT), *messages]
