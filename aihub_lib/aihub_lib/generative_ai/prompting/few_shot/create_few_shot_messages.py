from typing import List

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.generative_ai.prompting.few_shot.FewShotExample import FewShotExample


def create_few_shot_messages(few_shot_examples: List[FewShotExample], locale: str) -> List[ChatMessage]:
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
