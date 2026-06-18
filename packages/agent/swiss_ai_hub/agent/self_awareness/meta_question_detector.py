from typing import Annotated

from llama_index.core import PromptTemplate
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.self_awareness.meta_question_classification import (
    MetaQuestionCategory,
    MetaQuestionClassification,
)


def _localized_classification(t: LocaleHandler) -> type[MetaQuestionClassification]:
    """Localize field descriptions so the structured output is reasoned in the user's language."""

    class LocalizedMetaQuestionClassification(MetaQuestionClassification):
        is_meta_question: Annotated[bool, Field(description=t("agent.self_awareness.detect.is_meta"))]
        category: Annotated[
            MetaQuestionCategory | None,
            Field(default=None, description=t("agent.self_awareness.detect.category")),
        ]
        reasoning: Annotated[str, Field(description=t("agent.self_awareness.detect.reasoning"))]

    return LocalizedMetaQuestionClassification


async def detect_meta_question(llm: LLM, t: LocaleHandler, user_query: str) -> MetaQuestionClassification:
    """Classify whether a user message is a meta question about the agent itself."""
    prompt = PromptTemplate(t("agent.self_awareness.detect.prompt"))

    llm_kwargs: dict = {}
    if llm.metadata.is_function_calling_model:
        llm_kwargs["tool_choice"] = "required"
    else:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    result = await llm.astructured_predict(
        _localized_classification(t),
        prompt,
        llm_kwargs=llm_kwargs,
        user_query=user_query,
    )

    return MetaQuestionClassification.model_validate(result)
