import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.events.agent.user.response_schema import ResponseSchema
from swiss_ai_hub.core.events.agent.user.response_schema_violation import ResponseSchemaViolation
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent

INVOICE = {
    "type": "object",
    "properties": {
        "issuer": {"type": "string"},
        "total": {"type": ["number", "null"]},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"item": {"type": "string"}, "amount": {"type": "number"}},
                "required": ["item", "amount"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["issuer", "total", "lines"],
    "additionalProperties": False,
}


def _invoice_schema(**update) -> ResponseSchema:
    return ResponseSchema(name="invoice", json_schema=INVOICE, strict=True, **update)


def test_a_nested_answer_matching_the_schema_is_parsed():
    answer = '{"issuer": "ACME AG", "total": null, "lines": [{"item": "Bolts", "amount": 12.5}]}'

    assert _invoice_schema().validated(answer) == {
        "issuer": "ACME AG",
        "total": None,
        "lines": [{"item": "Bolts", "amount": 12.5}],
    }


def test_a_code_fence_around_the_json_is_tolerated():
    assert _invoice_schema().validated('```json\n{"issuer": "ACME AG", "total": 1, "lines": []}\n```')["total"] == 1


def test_every_violation_is_named_with_its_location():
    with pytest.raises(ResponseSchemaViolation) as violation:
        _invoice_schema().validated('{"issuer": "ACME AG", "lines": [{"item": "Bolts"}]}')

    assert "(root): 'total' is a required property" in str(violation.value)
    assert "lines/0: 'amount' is a required property" in str(violation.value)


@pytest.mark.parametrize("answer", ["The total is 12.", "[1, 2]", ""])
def test_prose_and_non_objects_are_violations(answer: str):
    with pytest.raises(ResponseSchemaViolation):
        ResponseSchema(name="any").validated(answer)


def test_without_a_schema_any_object_is_accepted_as_json_object_mode():
    any_object = ResponseSchema(name="any")

    assert any_object.response_format() == {"type": "json_object"}
    assert any_object.validated('{"anything": [1]}') == {"anything": [1]}


def test_the_response_format_carries_name_description_schema_and_strictness():
    assert _invoice_schema(description="An invoice's header").response_format() == {
        "type": "json_schema",
        "json_schema": {"name": "invoice", "schema": INVOICE, "strict": True, "description": "An invoice's header"},
    }


def test_an_invalid_json_schema_is_refused():
    with pytest.raises(ValidationError, match="not a valid JSON schema"):
        ResponseSchema(name="broken", json_schema={"type": "invoice"})


def test_a_name_openai_would_reject_is_refused():
    with pytest.raises(ValidationError):
        ResponseSchema(name="an invoice")


def test_the_request_is_part_of_the_api_input_and_optional():
    assert "response_schema" in UserMessageEvent.api_input_model().model_fields
    assert UserMessageEvent.model_fields["response_schema"].default is None
