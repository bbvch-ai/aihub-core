from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.attribute_value_type import AttributeValueType
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute


class DocumentAttributeDefinition(BaseModel):
    """One attribute: its general meaning, how its text is read, and the metadata keys it is stored under.

    Every attribute keeps the text the model copied next to the value read from it, so a better parser can fill the
    value later without asking the model again. A derived attribute is computed from others and has no text of its own.
    """

    RAW_SUFFIX: ClassVar[str] = "_raw"
    PRECISION_SUFFIX: ClassVar[str] = "_precision"
    START_SUFFIX: ClassVar[str] = "_start"
    END_SUFFIX: ClassVar[str] = "_end"

    attribute: Annotated[DocumentAttribute, Field(description="The attribute, also its metadata key")]
    value_type: Annotated[AttributeValueType, Field(description="How the copied text is read")]
    meaning: Annotated[str, Field(description="General meaning, used where a type does not override it")]
    derived_from: Annotated[
        list[DocumentAttribute],
        Field(description="Attributes this one is computed from; empty when the model fills it"),
    ] = []
    max_items: Annotated[int | None, Field(description="Most items a list attribute keeps")] = None

    @property
    def is_derived(self) -> bool:
        return bool(self.derived_from)

    @property
    def key(self) -> str:
        return self.attribute.value

    @property
    def raw_key(self) -> str:
        return f"{self.key}{self.RAW_SUFFIX}"

    @property
    def precision_key(self) -> str:
        return f"{self.key}{self.PRECISION_SUFFIX}"

    @property
    def start_key(self) -> str:
        return f"{self.key}{self.START_SUFFIX}"

    @property
    def end_key(self) -> str:
        return f"{self.key}{self.END_SUFFIX}"

    def stored_keys(self) -> list[str]:
        """Every metadata key this attribute writes, so storage, exclusion lists and filters never list them by hand."""
        if self.is_derived:
            return [self.key]
        match self.value_type:
            case AttributeValueType.DATE:
                return [self.key, self.raw_key, self.precision_key]
            case AttributeValueType.PERIOD:
                return [self.start_key, self.end_key, self.raw_key, self.precision_key]
            case _:
                return [self.key, self.raw_key]
