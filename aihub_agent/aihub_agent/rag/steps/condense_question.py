from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StandaloneQuestionCondenserEvent
from llama_index.core.base.llms.types import ChatMessage


async def execute_condense_standalone_question(
    limited_history: list[ChatMessage],
    user_query: str,
    llm_config: LLMConfig,
    t: LocaleHandler,
    displayer: EventDisplayer,
    condense_prompt: LocaleString | None = None,
) -> StandaloneQuestionCondenserEvent:
    """
    Condenses the chat history and user query into a standalone question.
    """
    await displayer.display_thought(t("agent.thought.condense_question"))
    async with llm_config.cost_reporting_llm(displayer) as llm:
        condensed_question = condense_standalone_question(
            chat_history=limited_history,
            message=user_query,
            t=t,
            llm=llm,
            condense_prompt=condense_prompt,
        )
        return StandaloneQuestionCondenserEvent(condensed_chat_message=condensed_question)
