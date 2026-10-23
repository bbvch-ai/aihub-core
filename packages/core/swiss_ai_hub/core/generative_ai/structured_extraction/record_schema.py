from collections import Counter
from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, Field, create_model
from swiss_ai_hub.jambo import SchemaConverter

from swiss_ai_hub.core.generative_ai.structured_extraction.invalid_record_schema_error import InvalidRecordSchemaError
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField

DEFAULT_MAX_FIELDS = 20


class RecordSchema(BaseModel):
    """The columns of the records to extract, decided at request time.

    A plain model rather than a generated class, so a workflow can carry it on an event from the step that builds it
    to every step that extracts with it.
    """

    fields: Annotated[list[RecordField], Field(description="Fields every extracted record has, in display order")]

    MATCH_FIELD: ClassVar[str] = "record_match"
    MATCH_UNSURE: ClassVar[str] = "unsure"

    def with_match(self) -> Self:
        """The schema plus the field the model marks each record with when instructions decide which records to keep:
        "yes" when the record clearly meets them, "unsure" when it may. Keeping the unsure ones and marking them lets a
        person decide, where dropping them would lose records silently."""
        match = RecordField(
            name=self.MATCH_FIELD,
            type="string",
            description='"yes" when the record clearly meets the instructions, "unsure" when it may; no other value.',
        )
        return self.model_copy(update={"fields": [*self.fields, match]})

    def validated(self, max_fields: int = DEFAULT_MAX_FIELDS) -> Self:
        """Check the rules strict structured output and jambo impose, reporting every problem at once.

        Kept out of Pydantic validation on purpose: the wrapping LLM retries on a validation error, and re-sending an
        identical request at temperature zero returns the same schema.
        """
        problems = []
        if not self.fields:
            problems.append("it has no fields")
        if len(self.fields) > max_fields:
            problems.append(f"it has {len(self.fields)} fields, more than the {max_fields} allowed")
        if any(not field.name for field in self.fields):
            problems.append("a field name has no letters or digits")
        if any(not field.description.strip() for field in self.fields):
            problems.append("a field has no description")
        if any(field.name == self.MATCH_FIELD for field in self.fields):
            problems.append(f"'{self.MATCH_FIELD}' is reserved for marking records that may not match")
        duplicates = sorted(name for name, count in Counter(f.name for f in self.fields).items() if name and count > 1)
        if duplicates:
            problems.append(f"field names repeat: {', '.join(duplicates)}")
        if problems:
            raise InvalidRecordSchemaError(problems)
        return self

    @property
    def field_names(self) -> list[str]:
        return [field.name for field in self.fields]

    def to_json_schema(self) -> dict[str, Any]:
        """Every property nullable *and* required, the only shape strict structured output accepts for "unknown".

        Strict mode puts every property into `required`, so a field the model cannot fill must still be emittable;
        without `null` the model cannot close the object and pads to its output limit instead.
        """
        return {
            "title": "ExtractedRecord",
            "type": "object",
            "properties": {
                field.name: {"type": [field.type, "null"], "description": field.description} for field in self.fields
            },
            "required": self.field_names,
        }

    def to_records_model(self) -> type[BaseModel]:
        """The record wrapped in a list, so one call returns zero, one or many records."""
        record_model = SchemaConverter.build(self.to_json_schema())
        return create_model(
            "ExtractedRecords",
            records=(list[record_model], Field(description="Every matching record, in document order")),
        )
