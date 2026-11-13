from typing import Any, ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.attribute_value_type import AttributeValueType
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_attribute_definition import (
    DocumentAttributeDefinition,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_definition import DocumentTypeDefinition
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    DOCUMENT_CLASSIFICATION_VERSION,
    DOCUMENT_NORMALIZER_VERSION,
    DOCUMENT_TYPE,
    DOCUMENT_TYPES,
)

_A = DocumentAttribute
_V = AttributeValueType


class DocumentTypeCatalog:
    """The closed set of document types and their attributes, and everything built from it.

    The output schema's descriptions, the prompt, the stored metadata keys and the documentation all come from here, so
    adding a type or an attribute changes this file and nothing that lists keys by hand. Raise `VERSION` whenever a
    change would classify a stored document differently; a backfill re-classifies every document of an older version.
    """

    VERSION: ClassVar[int] = 1
    MAX_SECONDARY_TYPES: ClassVar[int] = 3

    ATTRIBUTES: ClassVar[tuple[DocumentAttributeDefinition, ...]] = (
        DocumentAttributeDefinition(
            attribute=_A.DATE, value_type=_V.DATE, meaning="The date the document carries as its own date"
        ),
        DocumentAttributeDefinition(
            attribute=_A.REFERENCE_NUMBER, value_type=_V.TEXT, meaning="The document's own number"
        ),
        DocumentAttributeDefinition(
            attribute=_A.ISSUER, value_type=_V.TEXT, meaning="The organisation that issued or sent the document"
        ),
        DocumentAttributeDefinition(
            attribute=_A.ISSUER_TAX_ID,
            value_type=_V.TAX_ID,
            meaning="The issuer's VAT number or company identification number",
        ),
        DocumentAttributeDefinition(
            attribute=_A.RECIPIENT,
            value_type=_V.TEXT,
            meaning="The organisation or person the document is addressed to, not a contact person within it",
        ),
        DocumentAttributeDefinition(
            attribute=_A.PARTIES,
            value_type=_V.TEXT_LIST,
            meaning="Every party the document names as issuer or recipient",
            derived_from=[_A.ISSUER, _A.RECIPIENT],
        ),
        DocumentAttributeDefinition(
            attribute=_A.TOTAL_AMOUNT, value_type=_V.AMOUNT, meaning="The final total amount the document states"
        ),
        DocumentAttributeDefinition(
            attribute=_A.CURRENCY, value_type=_V.CURRENCY, meaning="The currency of the total amount"
        ),
        DocumentAttributeDefinition(
            attribute=_A.DUE_DATE, value_type=_V.DATE, meaning="The date by which something is due"
        ),
        DocumentAttributeDefinition(
            attribute=_A.PERIOD, value_type=_V.PERIOD, meaning="The period the document covers"
        ),
        DocumentAttributeDefinition(
            attribute=_A.RELATED_REFERENCES,
            value_type=_V.TEXT_LIST,
            meaning="Numbers of other documents this document refers to",
            max_items=5,
        ),
    )

    TYPES: ClassVar[tuple[DocumentTypeDefinition, ...]] = (
        DocumentTypeDefinition(
            type=DocumentType.INVOICE,
            description=(
                "Requests payment for goods or services that were delivered or agreed, and states an amount the "
                "recipient owes the issuer. Includes partial, final and advance-payment invoices, QR-bills, and "
                "utility and telecom bills."
            ),
            excludes=[
                "offers and quotes",
                "order confirmations, even when they end with a total",
                "delivery notes",
                "receipts for a payment already made (Quittung, Kassenbon)",
                "credit notes",
                "payment reminders (Mahnung)",
                "account statements",
                "pro-forma invoices",
            ],
            cue_words=[
                "Rechnung",
                "Faktura",
                "QR-Rechnung",
                "Rechnungsnummer",
                "zahlbar bis",
                "zahlbar innert",
                "facture",
                "n° de facture",
                "payable jusqu'au",
                "fattura",
                "numero fattura",
                "pagabile entro",
                "invoice",
                "invoice number",
                "bill",
                "amount due",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.ISSUER_TAX_ID,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.TOTAL_AMOUNT,
                _A.CURRENCY,
                _A.DUE_DATE,
                _A.PERIOD,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.DATE: "The issue date (Rechnungsdatum), not the due date, delivery date or date of supply",
                _A.REFERENCE_NUMBER: "The invoice number",
                _A.ISSUER: (
                    "The seller who issued the invoice and is owed the payment, by its legal name; never a factoring "
                    "or collection company named only as the payee"
                ),
                _A.ISSUER_TAX_ID: (
                    "The issuer's VAT number, or else its company identification number (Swiss UID); never a "
                    "commercial register number or the recipient's number"
                ),
                _A.RECIPIENT: "The customer the invoice is addressed to, the billed organisation or person",
                _A.TOTAL_AMOUNT: (
                    "The final total of this invoice, including VAT where VAT is charged; not an amount due that "
                    "adds earlier unpaid balances"
                ),
                _A.CURRENCY: "The currency of that total; ignore amounts converted into another currency",
                _A.DUE_DATE: "The payment due date, or the payment terms as written when no date is stated",
                _A.PERIOD: "The service or billing period, or the single date of supply",
                _A.RELATED_REFERENCES: (
                    "Numbers of the orders, order confirmations, delivery notes or contracts the invoice refers to; "
                    "not the QR payment reference, a customer number or an account number"
                ),
            },
            references=[
                "https://github.com/Azure-Samples/document-intelligence-code-samples/blob/main/schema/2024-11-30-ga/invoice.md",
                "https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/tree/",
                "https://justement.ch/de/doc/act/ch/641_20/tit_2/chap_6/art_26",
                "https://www.gesetze-im-internet.de/ustg_1980/__14.html",
                "https://github.com/rossumai/docile/blob/main/docile/dataset/__init__.py",
            ],
        ),
        DocumentTypeDefinition(
            type=DocumentType.OTHER,
            description="Any document that is not of another type in this list.",
        ),
    )

    @classmethod
    def type_definition(cls, document_type: DocumentType) -> DocumentTypeDefinition:
        return next(definition for definition in cls.TYPES if definition.type == document_type)

    @classmethod
    def attribute_definition(cls, attribute: DocumentAttribute) -> DocumentAttributeDefinition:
        return next(definition for definition in cls.ATTRIBUTES if definition.attribute == attribute)

    @classmethod
    def applicable(cls, document_type: DocumentType) -> list[DocumentAttributeDefinition]:
        """The attributes that apply to a type, in the catalog's order."""
        wanted = set(cls.type_definition(document_type).attributes)
        return [definition for definition in cls.ATTRIBUTES if definition.attribute in wanted]

    @classmethod
    def extracted_attributes(cls) -> list[DocumentAttributeDefinition]:
        """The attributes the model fills, i.e. every attribute that is not computed from others."""
        return [definition for definition in cls.ATTRIBUTES if not definition.is_derived]

    @classmethod
    def metadata_keys(cls) -> list[str]:
        """Every metadata key classification writes, for storage, exclusion lists and filters to take from one place."""
        attribute_keys = [key for definition in cls.ATTRIBUTES for key in definition.stored_keys()]
        return [
            DOCUMENT_TYPE,
            DOCUMENT_TYPES,
            DOCUMENT_CLASSIFICATION_VERSION,
            DOCUMENT_NORMALIZER_VERSION,
            *attribute_keys,
        ]

    @classmethod
    def value_keys(cls) -> list[str]:
        """The attribute keys that hold values a filter compares, i.e. every attribute key but the copied text."""
        return [key for definition in cls.ATTRIBUTES for key in definition.stored_keys() if key != definition.raw_key]

    @classmethod
    def prompt_types(cls) -> list[dict[str, Any]]:
        return [
            definition.model_dump(include={"type", "description", "excludes", "cue_words"}) for definition in cls.TYPES
        ]

    @classmethod
    def prompt_attributes(cls) -> list[dict[str, Any]]:
        """Each attribute the model fills, with its general meaning and its meaning for every type it applies to."""
        return [
            {
                "name": definition.attribute.value,
                "meaning": definition.meaning,
                "per_type": {
                    type_definition.type.value: type_definition.meaning_of(definition.attribute, definition.meaning)
                    for type_definition in cls.TYPES
                    if definition.attribute in type_definition.attributes
                },
            }
            for definition in cls.extracted_attributes()
        ]
