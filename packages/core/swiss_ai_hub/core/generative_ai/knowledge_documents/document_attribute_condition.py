import calendar
from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field

from swiss_ai_hub.core.generative_ai.document.classification.amount_text_parser import AmountTextParser
from swiss_ai_hub.core.generative_ai.document.classification.attribute_value_type import AttributeValueType
from swiss_ai_hub.core.generative_ai.document.classification.currency_text_parser import CurrencyTextParser
from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute_definition import (
    DocumentAttributeDefinition,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_verdict import DocumentMetadataVerdict
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_verdict import PathDateVerdict

type _StoredValues = dict[str, str | float | list[str] | None]


class DocumentAttributeCondition(BaseModel):
    """One condition on an attribute ingestion's classification stored, matched by code against the stored value.

    Text matches when the value contains it, case ignored, since a request names "Hooli" where the document says
    "Hooli AG". Dates and amounts match a range, a stored date by the whole span it covers ("März 2025"), so a value
    that overlaps the range is kept. A condition is matched only after `readable()` brought it into one form.
    """

    model_config = ConfigDict(json_schema_mode_override="validation")

    attribute: Annotated[DocumentAttribute, Field(description="The attribute the condition is on.")]
    contains: Annotated[
        str | None,
        Field(
            description="Text the value contains, case ignored, e.g. 'Hooli' for the issuer or the parties, 'CHF' for "
            "the currency; null for a date or an amount."
        ),
    ] = None
    at_least: Annotated[
        str | None,
        Field(description="Lowest value of a date (YYYY-MM-DD) or an amount (a number); null when open or for text."),
    ] = None
    at_most: Annotated[
        str | None,
        Field(description="Highest value of a date (YYYY-MM-DD) or an amount (a number); null when open or for text."),
    ] = None
    currency: Annotated[
        str | None,
        Field(
            description="The currency an amount is stated in, as its ISO code, e.g. 'CHF' for 'over CHF 10'000'; null "
            "when the request names none, and always for a date or text."
        ),
    ] = None

    @property
    def definition(self) -> DocumentAttributeDefinition:
        return DocumentTypeCatalog.attribute_definition(self.attribute)

    def readable(self) -> Self | None:
        """The condition in the one form `verdict` compares, or None when it states nothing code can compare: no text
        for a text attribute, or no readable bound for a date or an amount."""
        match self.definition.value_type:
            case AttributeValueType.DATE | AttributeValueType.PERIOD:
                return self._readable_dates()
            case AttributeValueType.AMOUNT:
                return self._readable_amounts()
            case _:
                text = (self.contains or "").strip()
                return (
                    self.model_copy(update={"contains": text, "at_least": None, "at_most": None, "currency": None})
                    if text
                    else None
                )

    def verdict(
        self,
        document: KnowledgeDocumentSummary,
        inapplicable: Annotated[
            DocumentMetadataVerdict, "The verdict for a type the attribute does not apply to"
        ] = DocumentMetadataVerdict.EXCLUDED,
    ) -> DocumentMetadataVerdict:
        """A type the attribute does not apply to never carries it, so by default it fails the condition; an empty
        value on a type it applies to is unknown. When only a secondary type carries it, ingestion stored the primary
        type's values alone, so the document is unknown rather than excluded."""
        if document.document_type not in DocumentType:
            return DocumentMetadataVerdict.UNKNOWN
        if not self._applies_to(document.document_type):
            secondary = any(self._applies_to(name) for name in document.document_types)
            return DocumentMetadataVerdict.UNKNOWN if secondary else inapplicable
        values = document.document_attributes
        definition = self.definition
        match definition.value_type:
            case AttributeValueType.DATE:
                return self._date_verdict(self._stored_date(values, definition))
            case AttributeValueType.PERIOD:
                return self._date_verdict(self._stored_period(values, definition))
            case AttributeValueType.AMOUNT:
                return self._amount_verdict(values.get(definition.key), values)
            case _:
                return self._text_verdict(values.get(definition.key))

    def _applies_to(self, type_name: str) -> bool:
        if type_name not in DocumentType:
            return False
        return self.attribute in DocumentTypeCatalog.type_definition(DocumentType(type_name)).attributes

    def _readable_dates(self) -> Self | None:
        """A bound the model wrote that names no date drops the condition rather than the request: the condition stays
        in the user's words in the document condition, so the judge still reads it."""
        try:
            period = PathDateRange.written(self.at_least, self.at_most)
        except ValueError:
            return None
        if period is None:
            return None
        return self.model_copy(
            update={
                "contains": None,
                "at_least": period.start.isoformat() if period.start else None,
                "at_most": period.end.isoformat() if period.end else None,
                "currency": None,
            }
        )

    def _readable_amounts(self) -> Self | None:
        """The currency is read from its own field or from a bound written with it ("CHF 10'000"); a currency named but
        not readable drops the condition, since comparing the bare number would mix currencies."""
        low, high = AmountTextParser.parse(self.at_least), AmountTextParser.parse(self.at_most)
        unreadable = (self.at_least and low is None) or (self.at_most and high is None)
        if unreadable or (low is None and high is None):
            return None
        if low is not None and high is not None and low > high:
            return None
        currency = (
            CurrencyTextParser.parse(self.currency)
            or CurrencyTextParser.parse(self.at_least)
            or CurrencyTextParser.parse(self.at_most)
        )
        if (self.currency or "").strip() and currency is None:
            return None
        return self.model_copy(
            update={
                "contains": None,
                "at_least": DocumentAttributeCondition._amount_text(low),
                "at_most": DocumentAttributeCondition._amount_text(high),
                "currency": currency,
            }
        )

    @staticmethod
    def _amount_text(amount: float | None) -> str | None:
        """The amount as plain digits, never in exponent notation, so the form and the summary read it as written."""
        return None if amount is None else format(amount, "f").rstrip("0").rstrip(".")

    def _date_verdict(self, stored: NormalizedDate | None) -> DocumentMetadataVerdict:
        if stored is None:
            return DocumentMetadataVerdict.UNKNOWN
        wanted = PathDateRange.written(self.at_least, self.at_most)
        if wanted is None or wanted.verdict_of(stored) is not PathDateVerdict.OUTSIDE:
            return DocumentMetadataVerdict.MATCH
        return DocumentMetadataVerdict.EXCLUDED

    def _amount_verdict(self, stored: object, values: _StoredValues) -> DocumentMetadataVerdict:
        """An amount in another currency, or one whose currency was not recorded, is unknown: nothing here converts
        currencies, and the bare numbers say nothing about each other."""
        if not isinstance(stored, int | float):
            return DocumentMetadataVerdict.UNKNOWN
        if self.currency is not None:
            stored_currency = values.get(DocumentTypeCatalog.attribute_definition(DocumentAttribute.CURRENCY).key)
            if not isinstance(stored_currency, str) or stored_currency.upper() != self.currency:
                return DocumentMetadataVerdict.UNKNOWN
        too_low = self.at_least is not None and stored < float(self.at_least)
        too_high = self.at_most is not None and stored > float(self.at_most)
        return DocumentMetadataVerdict.EXCLUDED if too_low or too_high else DocumentMetadataVerdict.MATCH

    def _text_verdict(self, stored: object) -> DocumentMetadataVerdict:
        items = [stored] if isinstance(stored, str) else stored if isinstance(stored, list) else []
        texts = [item.casefold() for item in items if isinstance(item, str) and item.strip()]
        if not texts:
            return DocumentMetadataVerdict.UNKNOWN
        wanted = (self.contains or "").casefold()
        return (
            DocumentMetadataVerdict.MATCH if any(wanted in text for text in texts) else DocumentMetadataVerdict.EXCLUDED
        )

    @staticmethod
    def _stored_date(values: _StoredValues, definition: DocumentAttributeDefinition) -> NormalizedDate | None:
        """The span a stored date covers: the value is its first day, the precision says how far it reaches."""
        start, precision = values.get(definition.key), values.get(definition.precision_key)
        if not isinstance(start, str):
            return None
        first = date.fromisoformat(start)
        stated = DatePrecision(precision) if precision in DatePrecision else DatePrecision.DAY
        months = {DatePrecision.DAY: 0, DatePrecision.MONTH: 1, DatePrecision.QUARTER: 3, DatePrecision.YEAR: 12}
        if stated is DatePrecision.DAY:
            return NormalizedDate(start=first, end=first, precision=stated)
        last_month = first.month + months[stated] - 1
        year, month = first.year + (last_month - 1) // 12, (last_month - 1) % 12 + 1
        last = date(year, month, calendar.monthrange(year, month)[1])
        return NormalizedDate(start=first, end=last, precision=stated)

    @staticmethod
    def _stored_period(values: _StoredValues, definition: DocumentAttributeDefinition) -> NormalizedDate | None:
        """A stored period; one that states only one end is read as that day, so it is never taken as open-ended."""
        start, end = values.get(definition.start_key), values.get(definition.end_key)
        first = date.fromisoformat(start) if isinstance(start, str) else None
        last = date.fromisoformat(end) if isinstance(end, str) else None
        if first is None and last is None:
            return None
        return NormalizedDate(start=first or last, end=last or first, precision=DatePrecision.DAY)
