from unittest.mock import Mock, patch

import pytest
from llama_index.core import PromptTemplate
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.guards.few_shot_guard import GuardResult, few_shot_guard
from swiss_ai_hub.core.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

scenarios("./features/few_shot_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        mock_llm_instance = mock_llm.return_value
        mock_llm_instance.structured_predict.return_value = GuardResult(reasoning="Expected reasoning", success=True)
        yield mock_llm_instance


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse("the following few-shot examples:"), target_fixture="examples")
def _(datatable, locale_handler):
    examples = []
    for row in datatable[1:]:
        user_message = LocaleString(**{locale_handler.locale: row[0]})
        success = row[1] == "True"
        reason = LocaleString(**{locale_handler.locale: row[2]})
        examples.append(FewShotGuardExample(user=user_message, success=success, reason=reason))
    return examples


@given(parsers.parse('a user query "{query}"'), target_fixture="user_query")
def _(query):
    return query


@when("the few-shot guard is executed")
@async_test
async def _(examples, llm, locale_handler, user_query):
    await few_shot_guard(
        examples=examples,
        llm=llm,
        t=locale_handler,
        user_query=user_query,
    )


@then("structured_predict should be called", target_fixture="call_args")
def _(llm):
    llm.structured_predict.assert_called()
    call_args = llm.structured_predict.call_args
    return call_args


@then("structured_predict should be called with prompt:")
def _(call_args, locale_handler, user_query, examples, docstring):
    prompt = PromptTemplate(locale_handler("lib.guards.few_shot_guard.prompt")).format(**call_args[1])

    def normalize(text):
        return "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())

    normalized_prompt = normalize(prompt)
    normalized_docstring = normalize(docstring)

    assert normalized_prompt == normalized_docstring, (
        f"\nExpected:\n{repr(normalized_docstring)}\n\nGot:\n{repr(normalized_prompt)}"
    )
