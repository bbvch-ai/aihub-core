from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.generative_ai.structured_extraction.invalid_record_schema_error import InvalidRecordSchemaError
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema_builder import (
    SCHEMA_PROPOSAL_MAX_TOKENS,
    RecordSchemaBuilder,
)
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

pytestmark = pytest.mark.unit


def _llm(proposal: RecordSchema | Exception) -> tuple[Mock, Mock]:
    """The caller's model and the copy the builder calls, kept apart to prove the caller's is never touched."""
    caller_llm, deterministic_copy = Mock(), Mock()
    caller_llm.model_copy.return_value = deterministic_copy
    deterministic_copy.astructured_predict = AsyncMock(side_effect=[proposal])
    return caller_llm, deterministic_copy


def _proposal(*names: str) -> RecordSchema:
    return RecordSchema(fields=[RecordField(name=name, type="string", description=f"The {name}") for name in names])


@pytest.mark.asyncio
async def test_returns_the_validated_proposal() -> None:
    caller_llm, _ = _llm(_proposal("Invoice Number", "supplier"))

    schema = await RecordSchemaBuilder.build("invoice number, supplier", caller_llm, LocaleHandler("en"))

    assert schema.field_names == ["invoice_number", "supplier"]


@pytest.mark.asyncio
async def test_calls_a_deterministic_capped_copy_never_the_callers_model() -> None:
    caller_llm, deterministic_copy = _llm(_proposal("supplier"))

    await RecordSchemaBuilder.build("supplier", caller_llm, LocaleHandler("en"))

    caller_llm.model_copy.assert_called_once_with(update={"temperature": 0.0, "max_tokens": SCHEMA_PROPOSAL_MAX_TOKENS})
    caller_llm.astructured_predict.assert_not_called()
    deterministic_copy.astructured_predict.assert_awaited_once()


@pytest.mark.asyncio
async def test_passes_the_description_and_field_limit_to_the_prompt() -> None:
    caller_llm, deterministic_copy = _llm(_proposal("supplier"))

    await RecordSchemaBuilder.build("supplier", caller_llm, LocaleHandler("en"), max_fields=7)

    call = deterministic_copy.astructured_predict.await_args
    assert call.args[0] is RecordSchema
    assert call.kwargs == {"description": "supplier", "max_fields": 7}


@pytest.mark.asyncio
async def test_proposal_breaking_the_rules_raises_invalid_schema() -> None:
    caller_llm, _ = _llm(_proposal("a", "b", "c"))

    with pytest.raises(InvalidRecordSchemaError, match="more than the 2 allowed"):
        await RecordSchemaBuilder.build("a, b, c", caller_llm, LocaleHandler("en"), max_fields=2)


@pytest.mark.asyncio
async def test_malformed_model_output_propagates() -> None:
    malformed = ValidationError.from_exception_data("RecordSchema", [])
    caller_llm, _ = _llm(malformed)

    with pytest.raises(ValueError):
        await RecordSchemaBuilder.build("supplier", caller_llm, LocaleHandler("en"))
