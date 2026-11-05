import re
import unicodedata
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

RecordFieldType = Literal["string", "number", "integer", "boolean"]

_NON_IDENTIFIER_CHARACTERS = re.compile(r"[^a-z0-9]+")


class RecordField(BaseModel):
    """One column of an extracted record.

    Only primitive types, because the schema is rebuilt into a model by jambo, which reads nothing but `properties`
    and would silently drop a nested or free-form value. Names are normalised on parse so two runs that spell a column
    differently ("Invoice Number", "invoice-number") still produce the same column.
    """

    name: Annotated[str, Field(description="Short snake_case identifier of the field, e.g. 'invoice_number'")]
    type: Annotated[RecordFieldType, Field(description="JSON type of the value: string, number, integer or boolean")]
    description: Annotated[str, Field(description="What the field holds and in which format, in one sentence")]

    @field_validator("name")
    @classmethod
    def normalise_name(cls, name: str) -> str:
        """Never raises: the wrapping LLM retries on validation errors, and an identical request cannot fix a name.

        An empty result is left for `RecordSchema.validated` to reject once, with every other problem of the schema.
        A name shadowing a Pydantic attribute (`json`, `copy`, `schema`) is suffixed rather than rejected, because
        jambo accepts it with only a warning and the generated model would hide the attribute.
        """
        ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
        normalised = _NON_IDENTIFIER_CHARACTERS.sub("_", ascii_name.strip().lower()).strip("_")
        if normalised[:1].isdigit():
            normalised = f"field_{normalised}"
        if normalised and hasattr(BaseModel, normalised):
            normalised = f"{normalised}_field"
        return normalised
