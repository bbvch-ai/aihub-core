from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole


async def execute_respond_with_llm(
    messages: list[ChatMessage],
    llm_config: LLMConfig,
    t: LocaleHandler,
    displayer: EventDisplayer,
    system_prompt: LocaleString | None = None,
    reject_reason: str | None = None,
    context_insufficient_prompt: LocaleString | None = None,
) -> LLMStopEvent:
    """
    Generates a response using the configured LLM.
    """
    # Add rejection context if provided
    if reject_reason:
        context_insufficient_text = t.extract(context_insufficient_prompt)
        prompt_text = t("agent.prompt.guard.reject").format(prompt=context_insufficient_text, reason=reject_reason)
        messages = messages + [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=prompt_text,
            ),
        ]

    await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))

    # Add system prompt if provided
    system_prompt_text = t.extract(system_prompt) if system_prompt else None
    if system_prompt_text:
        system_message = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt_text)
        messages = [system_message] + messages

    # Merge consecutive messages with the same role (required by LiteLLM)
    messages = merge_consecutive_messages(messages)

    async with llm_config.cost_reporting_llm(displayer) as llm:
        return await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=True)
