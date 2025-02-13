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
            description=t("lib.utils.decompose_chat_history.decompose_result.questions", hops=hops)
        )

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
    prompt = PromptTemplate(decompose_prompt_locale)
    response = llm.structured_predict(
        output_cls=decompose_result_factory(t, hops=hops),
        prompt=prompt,
        llm_kwargs=None,
        chat_history=chat_history_str,
        question=message,
    )
    return [ChatMessage(role=MessageRole.USER, content=question) for question in response.questions]
