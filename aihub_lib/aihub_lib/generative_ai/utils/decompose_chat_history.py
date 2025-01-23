from typing import List, Type

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from openai import BaseModel
from pydantic import Field

from aihub_lib.generative_ai.utils.condense_standalone_question import _messages_to_history_str
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString


class DecomposeResult(BaseModel):
    questions: List[str]


def decompose_result_factory(t: LocaleHandler, hops: int) -> Type[DecomposeResult]:
    class LocalizedDecomposeResult(DecomposeResult):
        questions: List[str] = Field(
            description=t("lib.utils.decompose_chat_history.decompose_result.questions"))
#            description=str(PromptTemplate(t("lib.utils.decompose_chat_history.decompose_result.questions")
#        )).format(hops=hops))

    LocalizedDecomposeResult.__doc__ = t("lib.utils.decompose_chat_history.decompose_result.doc_string")

    return LocalizedDecomposeResult


def decompose_chat_history(
    message: str,
    chat_history: List[ChatMessage],
    t: LocaleHandler,
    llm: LLM,
    hops: int,
    decompose_prompt: LocaleString = None,
) -> List[ChatMessage]:
    chat_history_str = _messages_to_history_str(chat_history)
    if decompose_prompt:
        decompose_prompt_locale = LocaleHandler(t.locale).extract(decompose_prompt, t.locale)
    else:
        decompose_prompt_locale = t("lib.utils.decompose_chat_history.decompose_prompt")

    response = llm.structured_predict(
        decompose_result_factory(t, hops=hops),
        prompt=PromptTemplate(decompose_prompt_locale),
        question=message,
        chat_history=chat_history_str,
    )
    return [ChatMessage(role=MessageRole.USER, content=question) for question in response]
