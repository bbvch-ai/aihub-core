import re
from typing import Any, ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.amount_text_parser import AmountTextParser
from swiss_ai_hub.core.generative_ai.document.classification.attribute_value_type import AttributeValueType
from swiss_ai_hub.core.generative_ai.document.classification.currency_text_parser import CurrencyTextParser
from swiss_ai_hub.core.generative_ai.document.classification.date_text_parser import DateTextParser
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute_definition import (
    DocumentAttributeDefinition,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog
from swiss_ai_hub.core.generative_ai.document.classification.period_text_parser import PeriodTextParser
from swiss_ai_hub.core.generative_ai.document.classification.raw_value_locator import RawValueLocator
from swiss_ai_hub.core.generative_ai.document.classification.tax_id_text_parser import TaxIdTextParser

type _Raw = str | list[str] | None


class DocumentValueNormalizer:
    """Turns the text the model copied into the metadata stored for each attribute of the document's type.

    Enforces "never guessed" in code rather than trusting the model to report its own doubt: an attribute that does
    not apply to the type is not stored, text that is not in the document is dropped, and text no parser understands
    keeps its copy with an empty value. Raise `VERSION` when a parser reads stored text differently; a backfill then
    re-reads every document's kept text without calling a model.
    """

    VERSION: ClassVar[int] = 1

    @classmethod
    def normalize(
        cls, document_type: DocumentType, answer: DocumentClassificationAnswer, document_text: str
    ) -> dict[str, Any]:
        """The stored keys and values of every attribute that applies to `document_type`; explicit None when unknown."""
        applicable = DocumentTypeCatalog.applicable(document_type)
        values: dict[str, Any] = {}
        for definition in applicable:
            if not definition.is_derived:
                raw = cls._located(getattr(answer, definition.attribute.value), document_text)
                values |= cls._stored(definition, raw)
        cls._complete_currency(values)
        cls._drop_own_number(values)
        for definition in applicable:
            if definition.is_derived:
                sources = [values.get(source) for source in definition.derived_from]
                values[definition.key] = cls._distinct(sources) or None
        return values

    @classmethod
    def _located(cls, raw: _Raw, document_text: str) -> _Raw:
        if isinstance(raw, list):
            found = [item.strip() for item in raw if item.strip() and RawValueLocator.appears_in(item, document_text)]
            return found or None
        if raw is None or not raw.strip():
            return None
        return raw.strip() if RawValueLocator.appears_in(raw, document_text) else None

    @classmethod
    def _stored(cls, definition: DocumentAttributeDefinition, raw: _Raw) -> dict[str, Any]:
        match definition.value_type:
            case AttributeValueType.DATE:
                parsed = DateTextParser.parse(raw)
                return {
                    definition.key: parsed.start.isoformat() if parsed else None,
                    definition.raw_key: raw,
                    definition.precision_key: parsed.precision.value if parsed else None,
                }
            case AttributeValueType.PERIOD:
                period = PeriodTextParser.parse(raw)
                return {
                    definition.start_key: period.start.isoformat() if period else None,
                    definition.end_key: period.end.isoformat() if period else None,
                    definition.raw_key: raw,
                    definition.precision_key: period.precision.value if period else None,
                }
            case AttributeValueType.AMOUNT:
                return {definition.key: AmountTextParser.parse(raw), definition.raw_key: raw}
            case AttributeValueType.CURRENCY:
                return {definition.key: CurrencyTextParser.parse(raw), definition.raw_key: raw}
            case AttributeValueType.TAX_ID:
                return {definition.key: TaxIdTextParser.parse(raw), definition.raw_key: raw}
            case AttributeValueType.TEXT_LIST:
                items = cls._distinct(raw or [])
                return {definition.key: items[: definition.max_items] or None, definition.raw_key: raw}
            case _:
                return {definition.key: raw, definition.raw_key: raw}

    @classmethod
    def _complete_currency(cls, values: dict[str, Any]) -> None:
        """A total copied with its currency ("CHF 12'496.36") also states the currency, when none was copied apart."""
        amount_raw = values.get(DocumentTypeCatalog.attribute_definition(DocumentAttribute.TOTAL_AMOUNT).raw_key)
        if DocumentAttribute.CURRENCY in values and values[DocumentAttribute.CURRENCY] is None:
            values[DocumentAttribute.CURRENCY] = CurrencyTextParser.parse(amount_raw)

    @classmethod
    def _drop_own_number(cls, values: dict[str, Any]) -> None:
        """The document's own number is not a reference to another document, however the model listed it."""
        own_number = values.get(DocumentAttribute.REFERENCE_NUMBER)
        references = values.get(DocumentAttribute.RELATED_REFERENCES)
        if not own_number or not references:
            return
        kept = [item for item in references if cls._compact(item) != cls._compact(own_number)]
        values[DocumentAttribute.RELATED_REFERENCES] = kept or None

    @classmethod
    def _distinct(cls, items: list[str | None]) -> list[str]:
        seen: set[str] = set()
        distinct = []
        for item in items:
            if item and cls._compact(item) not in seen:
                seen.add(cls._compact(item))
                distinct.append(item)
        return distinct

    @classmethod
    def _compact(cls, text: str) -> str:
        return re.sub(r"[^0-9a-z]", "", text.casefold())
