from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


@trace_fn
def create_few_shot_messages(few_shot_examples: list[FewShotExample], locale: str) -> list[ChatMessage]:
    example_messages = []

    for example in few_shot_examples:
        example_messages.append(
            ChatMessage(
                role=MessageRole.USER,
                content=example.user.in_locale(locale),
                additional_kwargs={},
            )
        )
        example_messages.append(
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content=example.agent.in_locale(locale),
                additional_kwargs={},
            )
        )

    return example_messages
