from llama_index.core import ChatPromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from llama_index.core.program import LLMTextCompletionProgram
from pydantic import BaseModel

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class GuardResult(BaseModel):
    reasoning: str
    success: bool


async def context_sufficient_guard(llm: LLM, t: LocaleHandler, user_query: str, context: str) -> GuardResult:
    prompt_template = ChatPromptTemplate(
        message_templates=[
            ChatMessage(
                role="system",
                content=t("lib.guards.context_sufficient_guard.prompt"),
            ),
            ChatMessage(
                role="user",
                content=t("lib.guards.context_sufficient_guard.message"),
            ),
        ]
    )

    program = LLMTextCompletionProgram.from_defaults(
        output_cls=GuardResult,
        prompt=prompt_template,
        llm=llm,
    )

    result = program(user_query=user_query, context=context)
    return result
