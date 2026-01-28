from enum import StrEnum
from typing import Annotated

from llama_index.core import PromptTemplate
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.azure_openai import AzureOpenAI
from pydantic import BaseModel, Field

from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_LANGUAGE_ENGLISH,
    NODE_LANGUAGE_FRENCH,
    NODE_LANGUAGE_GERMAN,
    NODE_LANGUAGE_ITALIAN,
)


class LanguageEnum(StrEnum):
    de = NODE_LANGUAGE_GERMAN
    en = NODE_LANGUAGE_ENGLISH
    fr = NODE_LANGUAGE_FRENCH
    it = NODE_LANGUAGE_ITALIAN
    other = "other"


class Language(BaseModel):
    language: Annotated[LanguageEnum, Field(description="Language shortname of user query.")]


def check_language(
    question: str,
    llm: AzureOpenAI,
) -> str:
    check_language_prompt = """
        You will receive a user request. Decide which language it is. Possible options are:
        'en', 'de', 'fr', 'it'. If the language is not one of these, select 'other'.
    
        Here is the user request:
        <user request>
        {question}
        </user request>
    """

    prompt = PromptTemplate(check_language_prompt)

    program = LLMTextCompletionProgram.from_defaults(
        output_cls=Language,
        prompt=prompt,
        llm=llm,
    )

    result = program(question=question)
    return Language.model_validate(result).language
