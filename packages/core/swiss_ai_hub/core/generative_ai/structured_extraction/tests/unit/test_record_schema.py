import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.generative_ai.structured_extraction.invalid_record_schema_error import InvalidRecordSchemaError
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema

pytestmark = pytest.mark.unit


def _schema(*fields: tuple[str, str, str]) -> RecordSchema:
    return RecordSchema(fields=[RecordField(name=n, type=t, description=d) for n, t, d in fields])


@pytest.mark.parametrize(
    ("raw", "normalised"),
    [
        ("Invoice Number", "invoice_number"),
        ("invoice-number", "invoice_number"),
        ("  Prüfdatum ", "prufdatum"),
        ("2nd line", "field_2nd_line"),
        ("json", "json_field"),
        ("___", ""),
    ],
)
def test_field_names_are_normalised_without_raising(raw: str, normalised: str) -> None:
    assert RecordField(name=raw, type="string", description="d").name == normalised


def test_field_type_outside_the_primitives_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RecordField(name="lines", type="array", description="d")


def test_valid_schema_passes_validation_unchanged() -> None:
    schema = _schema(("invoice_number", "string", "Invoice number"), ("amount", "number", "Line amount"))

    assert schema.validated(max_fields=5) is schema


def test_validation_reports_every_problem_at_once() -> None:
    schema = _schema(("amount", "number", "A"), ("Amount", "number", " "), ("!!", "string", "x"))

    with pytest.raises(InvalidRecordSchemaError) as raised:
        schema.validated(max_fields=2)

    assert len(raised.value.problems) == 4
    assert "amount" in str(raised.value)


def test_empty_schema_is_rejected() -> None:
    schema = RecordSchema(fields=[])

    with pytest.raises(InvalidRecordSchemaError, match="no fields"):
        schema.validated()


def test_invalid_schema_error_is_a_value_error_so_callers_degrade_with_one_clause() -> None:
    assert issubclass(InvalidRecordSchemaError, ValueError)


def test_json_schema_makes_every_field_nullable_and_required() -> None:
    schema = _schema(("supplier", "string", "Supplier name"), ("amount", "number", "Line amount"))

    json_schema = schema.to_json_schema()

    assert json_schema["required"] == ["supplier", "amount"]
    assert json_schema["properties"]["amount"] == {"type": ["number", "null"], "description": "Line amount"}


def test_records_model_accepts_zero_one_or_many_records_with_nulls() -> None:
    records_model = _schema(("supplier", "string", "S"), ("amount", "number", "A")).to_records_model()

    assert records_model(records=[]).records == []
    parsed = records_model(records=[{"supplier": "Acme", "amount": None}, {"supplier": None, "amount": 12.5}])
    assert [record.model_dump() for record in parsed.records] == [
        {"supplier": "Acme", "amount": None},
        {"supplier": None, "amount": 12.5},
    ]


def test_records_model_rejects_a_record_missing_a_field() -> None:
    records_model = _schema(("supplier", "string", "S"), ("amount", "number", "A")).to_records_model()

    with pytest.raises(ValidationError):
        records_model(records=[{"supplier": "Acme"}])


def test_records_model_schema_keeps_field_descriptions_for_the_model() -> None:
    records_model = _schema(("amount", "number", "Line amount in the invoice currency")).to_records_model()

    rendered = str(records_model.model_json_schema())

    assert "Line amount in the invoice currency" in rendered


def test_schema_survives_a_json_round_trip_so_it_can_travel_on_an_event() -> None:
    schema = _schema(("amount", "number", "Line amount"))

    assert RecordSchema.model_validate_json(schema.model_dump_json()) == schema
