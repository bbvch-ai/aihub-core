from typing import List

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.rag.StandaloneQuestionCondenserEvent import (
    StandaloneQuestionCondenserEvent,
)
from aihub_agent.agents.rag.StandaloneQuestionCondenserStepConfig import (
    StandaloneQuestionCondenserStepConfig,
)


def _messages_to_history_str(messages: List[ChatMessage]) -> str:
    """Convert messages to a history string."""
    string_messages = []
    for message in messages:
        role = message.role
        content = message.content
        string_message = f"{role.value}: {content}"

        additional_kwargs = message.additional_kwargs
        if additional_kwargs:
            string_message += f"\n{additional_kwargs}"
        string_messages.append(string_message)
    return "\n".join(string_messages)


def condense_standalone_question_step(
    config: StandaloneQuestionCondenserStepConfig,
    message: str,
    chat_history: List[ChatMessage],
) -> StandaloneQuestionCondenserEvent:

    chat_history_str = _messages_to_history_str(chat_history)
    condense_prompt = agent.t("agent.prompt.condenser.standalone_question")
    if config.condense_prompt:
        condense_prompt = LocaleHandler(agent.locale).extract(
            config.condense_prompt, agent.locale
        )

    response = config.llm.predict(
        prompt=PromptTemplate(condense_prompt),
        question=message,
        chat_history=chat_history_str,
    )
    return StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content=response)
    )
