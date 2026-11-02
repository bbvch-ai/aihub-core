import pytest
from fastapi import HTTPException

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.openai_structured_request import OpenaiStructuredRequest
from swiss_ai_hub.api.routes.openai.structured_presentation import StructuredPresentation

MESSAGES = [{"role": "user", "content": "Extract the invoice."}]
FUNCTION = {"type": "function", "function": {"name": "extract_invoice", "parameters": {"type": "object"}}}


def _request(**fields) -> ChatCompletionRequest:
    return ChatCompletionRequest(model="Agent/agent", messages=MESSAGES, **fields)


def _refusal(**fields) -> dict:
    with pytest.raises(HTTPException) as refused:
        OpenaiStructuredRequest.from_request(_request(**fields))
    assert refused.value.status_code == 400
    return refused.value.detail


@pytest.mark.parametrize(
    "fields",
    [{}, {"response_format": {"type": "text"}}, {"tools": [FUNCTION], "tool_choice": "none"}],
    ids=["nothing", "text", "tools-off"],
)
def test_a_plain_answer_needs_no_schema(fields):
    assert OpenaiStructuredRequest.from_request(_request(**fields)) is None


def test_a_json_schema_response_format_keeps_name_description_schema_and_strictness():
    json_schema = {"name": "invoice", "description": "Header", "schema": {"type": "object"}, "strict": True}

    structured = OpenaiStructuredRequest.from_request(
        _request(response_format={"type": "json_schema", "json_schema": json_schema})
    )

    assert structured.presentation == StructuredPresentation.CONTENT
    assert structured.response_schema.model_dump() == {
        "name": "invoice",
        "description": "Header",
        "json_schema": {"type": "object"},
        "strict": True,
    }


def test_required_with_its_only_function_forces_it():
    structured = OpenaiStructuredRequest.from_request(_request(tools=[FUNCTION], tool_choice="required"))

    assert structured.presentation == StructuredPresentation.TOOL_CALL
    assert structured.response_schema.name == "extract_invoice"


def test_a_function_without_parameters_asks_for_an_empty_object():
    function = {"type": "function", "function": {"name": "mark_done"}}

    structured = OpenaiStructuredRequest.from_request(_request(tools=[function], tool_choice="required"))

    assert structured.response_schema.json_schema == {"type": "object", "properties": {}}


def test_forcing_another_function_than_the_one_offered_is_refused():
    assert _refusal(tools=[FUNCTION], tool_choice={"type": "function", "function": {"name": "x"}})["param"] == (
        "tool_choice"
    )


def test_a_forced_function_and_a_response_format_together_are_refused():
    detail = _refusal(tools=[FUNCTION], tool_choice="required", response_format={"type": "json_object"})

    assert detail["param"] == "response_format"


def test_legacy_functions_are_refused():
    assert _refusal(functions=[{"name": "extract_invoice"}], function_call="auto")["param"] == "functions"


def test_a_schema_that_is_not_a_json_schema_is_refused_by_name():
    detail = _refusal(response_format={"type": "json_schema", "json_schema": {"name": "x", "schema": {"type": 3}}})

    assert detail["param"] == "response_format"
    assert "not a valid JSON schema" in detail["message"]
