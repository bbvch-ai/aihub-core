import re
import unicodedata
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
from swiss_ai_hub.core.generative_ai.document.classification.slash_date_order import SlashDateOrder
from swiss_ai_hub.core.generative_ai.document.classification.tax_id_text_parser import TaxIdTextParser

type _Raw = str | list[str] | None


class DocumentValueNormalizer:
    """Turns the text the model copied into the metadata stored for each attribute of the document's type.

    Enforces "never guessed" in code rather than trusting the model to report its own doubt: an attribute that does
    not apply to the type is not stored, text that is not in the document is dropped, and text no parser understands
    keeps its copy with an empty value. Raise `VERSION` when a parser reads stored text differently; a backfill then
    re-reads every document's kept text without calling a model.
    """

    VERSION: ClassVar[int] = 4
    _SLASH_DATE: ClassVar[re.Pattern[str]] = re.compile(r"\b(\d{1,2})/(\d{1,2})/(?:\d{4}|\d{2})\b")
    _PLACEHOLDER: ClassVar[re.Pattern[str]] = re.compile(
        r"_{3,}|\.{4,}|…{2,}|\[\s?\]|\[\s*(?:[YMDJTX#*.…/\s-]{2,}|[^\]]*_{2,}[^\]]*)\s*\]"
    )
    """A gap a template leaves to fill in: a blank line, dots, "[YYYY]", "[####]", "[______]" or an empty box."""
    _E_MAIL: ClassVar[re.Pattern[str]] = re.compile(r"<?[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+>?")
    _JURISDICTION_CLAUSE: ClassVar[re.Pattern[str]] = re.compile(
        r"gericht(?!et)|\ble for\b|\bfor (?:juridique|exclusif|est)\b|\bforo\b|\bcourts?\b|\bvenue\b|jurisdiction|"
        r"juridiction|tribuna(?:l|ux)|giurisdizion",
        re.IGNORECASE,
    )
    _TERM_TYPES: ClassVar[frozenset[DocumentType]] = frozenset(
        {DocumentType.CONTRACT, DocumentType.SERVICE_LEVEL_AGREEMENT}
    )
    """Types whose period is a term, which may state only its start or only its end; any other period is whole."""
    _NAMES: ClassVar[frozenset[DocumentAttribute]] = frozenset(
        {DocumentAttribute.ISSUER, DocumentAttribute.RECIPIENT, DocumentAttribute.PARTICIPANTS}
    )

    @classmethod
    def normalize(
        cls, document_type: DocumentType, answer: DocumentClassificationAnswer, document_text: str
    ) -> dict[str, Any]:
        """The stored keys and values of every attribute that applies to `document_type`; explicit None when unknown."""
        applicable = DocumentTypeCatalog.applicable(document_type)
        slash_order = cls._slash_order(answer, document_text)
        values: dict[str, Any] = {}
        for definition in applicable:
            if not definition.is_derived:
                is_term = document_type in cls._TERM_TYPES
                raw = cls._located(getattr(answer, definition.attribute.value), document_text)
                if raw is None and is_term and definition.value_type is AttributeValueType.PERIOD:
                    raw = cls._term_by_its_dates(getattr(answer, definition.attribute.value), document_text)
                values |= cls._stored(definition, raw, slash_order, document_text, is_term)
        cls._complete_currency(values)
        cls._drop_own_number(values)
        cls._drop_names_only_in_addresses(values, document_text)
        cls._drop_jurisdiction_outside_its_clause(values, document_text)
        for definition in applicable:
            if definition.is_derived:
                values[definition.key] = cls._derived(definition, values)
        return values

    @classmethod
    def _derived(cls, definition: DocumentAttributeDefinition, values: dict[str, Any]) -> list[str] | None:
        """The distinct values of the sources the type has; a source the type lacks counts as unknown."""
        sources: list[str | None] = []
        for source in definition.derived_from:
            value = values.get(source)
            sources.extend(value if isinstance(value, list) else [value])
        return cls._distinct(sources) or None

    @classmethod
    def _located(cls, raw: _Raw, document_text: str) -> _Raw:
        """The copied text that is in the document; a template's unfilled gap is not a value, even where it is."""
        if isinstance(raw, list):
            items = [item.strip() for item in raw if item.strip() and not cls._PLACEHOLDER.search(item)]
            return RawValueLocator.found_in(items, document_text) or None
        if raw is None or not raw.strip() or cls._PLACEHOLDER.search(raw):
            return None
        return raw.strip() if RawValueLocator.appears_in(raw, document_text) else None

    @classmethod
    def _term_by_its_dates(cls, raw: _Raw, document_text: str) -> _Raw:
        """A term the model wrote in words of its own, kept when every date it names is in the document.

        A contract often states its start and its end on lines of their own ("Vertragsbeginn 1. April 2025",
        "Vertragsende 31. März 2028"), which no single copy spans, and a model adds a word ("ab") the document does
        not have. Two dates or more keep the model's text, which reads as a range; one date keeps only the date as
        written, so its end is read from its own line in the document rather than from the model's words.
        """
        if not isinstance(raw, str) or cls._PLACEHOLDER.search(raw):
            return None
        dates = PeriodTextParser.dates_written(raw)
        if not dates or len(RawValueLocator.found_in(dates, document_text)) < len(dates):
            return None
        return dates[0] if len(dates) == 1 else raw.strip()

    @classmethod
    def _slash_order(cls, answer: DocumentClassificationAnswer, document_text: str) -> SlashDateOrder | None:
        """The order the document writes slash dates in, for the ones both orders allow.

        The document's own unambiguous slash dates settle it (`17/11/2017` is day first, `11/17/2017` month first);
        when they disagree, none is read. Without such a date, a currency whose countries write day first settles it,
        and USD, a bare `$` or no currency leave it unread, since month first is the US order.
        """
        orders = {
            SlashDateOrder.DAY_FIRST if int(first) > 12 else SlashDateOrder.MONTH_FIRST
            for first, second in cls._SLASH_DATE.findall(document_text)
            if (int(first) > 12) != (int(second) > 12)
        }
        if orders:
            return orders.pop() if len(orders) == 1 else None
        currency = CurrencyTextParser.parse(
            cls._located(answer.document_currency, document_text)
        ) or CurrencyTextParser.parse(cls._located(answer.document_total_amount, document_text))
        return SlashDateOrder.DAY_FIRST if currency is not None and currency != "USD" else None

    @classmethod
    def _stored(
        cls,
        definition: DocumentAttributeDefinition,
        raw: _Raw,
        slash_order: SlashDateOrder | None,
        document_text: str,
        is_term: bool,
    ) -> dict[str, Any]:
        match definition.value_type:
            case AttributeValueType.DATE:
                parsed = DateTextParser.parse(raw, slash_order)
                return {
                    definition.key: parsed.start.isoformat() if parsed else None,
                    definition.raw_key: raw,
                    definition.precision_key: parsed.precision.value if parsed else None,
                }
            case AttributeValueType.PERIOD:
                period = PeriodTextParser.parse(raw, slash_order)
                states_start, states_end = (
                    cls._stated_ends(raw, slash_order, document_text) if is_term else (True, True)
                )
                return {
                    definition.start_key: period.start.isoformat() if period and states_start else None,
                    definition.end_key: period.end.isoformat() if period and states_end else None,
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
                plain = cls._plain(raw)
                items = cls._distinct((cls._name(plain) if definition.attribute in cls._NAMES else plain) or [])
                return {definition.key: items[: definition.max_items] or None, definition.raw_key: raw}
            case _ if definition.attribute in cls._NAMES:
                return {definition.key: cls._name(cls._plain(raw)), definition.raw_key: raw}
            case _:
                return {definition.key: cls._plain(raw), definition.raw_key: raw}

    @classmethod
    def _plain(cls, raw: _Raw) -> _Raw:
        """Text as a filter matches it: typographic ligatures ("ﬀ" in "Schaﬀhausen") and other compatibility
        characters a PDF writes become plain letters; the copy itself is kept as written."""
        if isinstance(raw, list):
            return [unicodedata.normalize("NFKC", item) for item in raw]
        return unicodedata.normalize("NFKC", raw) if raw is not None else None

    @classmethod
    def _name(cls, raw: _Raw) -> _Raw:
        """A party's name without e-mail addresses: an address names a mailbox, not who sends or receives.

        "Anna Meier <anna@example.ch>" keeps "Anna Meier"; a bare address keeps nothing.
        """
        if isinstance(raw, list):
            return [name for name in (cls._name(item) for item in raw) if isinstance(name, str)]
        if raw is None or not cls._E_MAIL.search(raw):
            return raw
        return cls._E_MAIL.sub("", raw).strip(" ,;:()<>\"'") or None

    @classmethod
    def _stated_ends(cls, raw: _Raw, slash_order: SlashDateOrder | None, document_text: str) -> tuple[bool, bool]:
        context = RawValueLocator.line_of(raw, document_text) if isinstance(raw, str) else None
        return PeriodTextParser.stated_ends(raw if isinstance(raw, str) else None, slash_order, context)

    @classmethod
    def _drop_jurisdiction_outside_its_clause(cls, values: dict[str, Any], document_text: str) -> None:
        """A place counts only where a clause or its heading names a court, since models take one from an address or
        the place a document was signed."""
        place = values.get(DocumentAttribute.JURISDICTION.value)
        if not isinstance(place, str):
            return
        passages = RawValueLocator.passages_holding(place, document_text, 2)
        if not any(cls._JURISDICTION_CLAUSE.search(passage) for passage in passages):
            values[DocumentAttribute.JURISDICTION.value] = None

    @classmethod
    def _drop_names_only_in_addresses(cls, values: dict[str, Any], document_text: str) -> None:
        """A name the document writes only inside an e-mail address ("northpeak" in billing@northpeak.example) was
        made up from the mailbox, so it is dropped while its copied text is kept."""
        names = [
            name
            for attribute in cls._NAMES
            for name in (values.get(attribute) if isinstance(values.get(attribute), list) else [values.get(attribute)])
            if isinstance(name, str)
        ]
        found = set(RawValueLocator.found_in(names, cls._E_MAIL.sub(" ", document_text)))
        for attribute in cls._NAMES:
            value = values.get(attribute)
            if isinstance(value, str) and value not in found:
                values[attribute] = None
            elif isinstance(value, list):
                values[attribute] = [name for name in value if name in found] or None

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
