from unittest.mock import Mock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.generative_ai.guards.sensitive_info_guard import SensitiveInfoGuardResult, sensitive_info_guard
from aihub_lib.i18n.LocaleHandler import LocaleHandler

scenarios("./features/sensitive_info_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        mock_llm_instance = mock_llm.return_value
        yield mock_llm_instance


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse('a response "{response}"'), target_fixture="response")
def _(response):
    return response


@given(parsers.parse('the LLM returns success={success:w} with reasoning="{reasoning}"'), target_fixture="llm_result")
def _(llm, success, reasoning):
    success_bool = success == "True"
    result = SensitiveInfoGuardResult(reasoning=reasoning, success=success_bool, cleaned_answer=None)
    llm.structured_predict.return_value = result
    return result


@given(
    parsers.parse(
        'the LLM returns success={success:w} with reasoning="{reasoning}" and cleaned_answer="{cleaned_answer}"'
    ),
    target_fixture="llm_result",
)
def _(llm, success, reasoning, cleaned_answer):
    success_bool = success == "True"
    result = SensitiveInfoGuardResult(reasoning=reasoning, success=success_bool, cleaned_answer=cleaned_answer)
    llm.structured_predict.return_value = result
    return result


@when("the sensitive info guard is executed", target_fixture="guard_result")
def _(llm, locale_handler, response):
    result = sensitive_info_guard(
        llm=llm,
        t=locale_handler,
        answer=response,
    )
    return result


@then("the guard should accept the response")
def _(guard_result):
    assert guard_result.success is True, f"Expected guard to accept, but it rejected with: {guard_result.reasoning}"


@then("the guard should reject the response")
def _(guard_result):
    assert guard_result.success is False, f"Expected guard to reject, but it accepted with: {guard_result.reasoning}"


@then(parsers.parse('the reasoning should be "{expected_reasoning}"'))
def _(guard_result, expected_reasoning):
    assert (
        guard_result.reasoning == expected_reasoning
    ), f"Expected reasoning: {expected_reasoning}, got: {guard_result.reasoning}"


@then("no cleaned answer should be provided")
def _(guard_result):
    assert guard_result.cleaned_answer is None, f"Expected no cleaned answer, but got: {guard_result.cleaned_answer}"


@then(parsers.parse('a cleaned answer "{expected_answer}" should be provided'))
def _(guard_result, expected_answer):
    assert (
        guard_result.cleaned_answer == expected_answer
    ), f"Expected cleaned answer: {expected_answer}, got: {guard_result.cleaned_answer}"
