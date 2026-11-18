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
    DOCUMENT_TYPE_VERSION,
    DOCUMENT_TYPES,
)

_A = DocumentAttribute
_V = AttributeValueType


class DocumentTypeCatalog:
    """The closed set of document types and their attributes, and everything built from it.

    The output schema's descriptions, the prompt, the stored metadata keys and the documentation all come from here, so
    adding a type or an attribute changes this file and nothing that lists keys by hand.

    Two levels of version decide what a backfill re-classifies, one model call per document:

    - a type's own `version`, when a change could classify only that type's documents differently. Adding a type
      raises `OTHER`'s, since only documents marked `OTHER` can now be of the new type;
    - `VERSION`, when a change could classify any document differently, such as a shared attribute's meaning or the
      prompt's rules. It re-classifies every document, so prefer a type's version whenever the change allows.
    """

    VERSION: ClassVar[int] = 2
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
        DocumentAttributeDefinition(
            attribute=_A.VALID_UNTIL,
            value_type=_V.DATE,
            meaning="The date until which the document's offer or terms are valid",
        ),
        DocumentAttributeDefinition(
            attribute=_A.NOTICE_PERIOD,
            value_type=_V.TEXT,
            meaning=(
                "The notice period for terminating the agreement, as written; null when ordinary termination is "
                "excluded"
            ),
        ),
        DocumentAttributeDefinition(
            attribute=_A.SERVICE_LEVELS,
            value_type=_V.TEXT_LIST,
            meaning=(
                "Each service level the provider commits to, such as an availability, a response or a resolution time, "
                "copied as written"
            ),
            max_items=5,
        ),
    )

    TYPES: ClassVar[tuple[DocumentTypeDefinition, ...]] = (
        DocumentTypeDefinition(
            type=DocumentType.INVOICE,
            description=(
                "Requests payment for goods or services that were delivered or agreed, and states an amount the "
                "recipient owes the issuer. Includes partial, final and advance-payment invoices, QR-bills, and "
                "utility and telecom bills. A final invoice stays an invoice when the advance payments it deducts "
                "make its total negative."
            ),
            excludes=[
                "offers and quotes",
                "order confirmations, even when they end with a total",
                "delivery notes",
                "receipts for a payment already made (Quittung, Kassenbon)",
                "credit notes and every Gutschrift, including a self-billing one the buyer issues under § 14 UStG",
                "a correction of an earlier invoice (Rechnungskorrektur, facture rectificative) whose total is "
                "negative, which works as a credit note",
                "a QR payment part (Zahlteil, section paiement) on its own, without the invoice it belongs to",
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
            type=DocumentType.CREDIT_NOTE,
            description=(
                "Reduces, cancels or credits an amount instead of requesting one: credit notes, the cancellation "
                "(Storno) of an earlier invoice, a correction of an invoice whose total is negative, and a "
                "self-billing Gutschrift the buyer issues to pay the seller under § 14 UStG."
            ),
            excludes=[
                "a final invoice whose total turns negative after deducting advance payments, which stays an invoice",
                "a receipt confirming that a refund was paid out",
            ],
            cue_words=[
                "Gutschrift",
                "Stornorechnung",
                "Rechnungskorrektur",
                "note de crédit",
                "avoir",
                "facture rectificative",
                "nota di credito",
                "credit note",
                "credit memo",
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
                _A.ISSUER: (
                    "The party that issued the credit note, by its legal name; for a self-billing Gutschrift, the "
                    "buyer who issues it"
                ),
                _A.ISSUER_TAX_ID: (
                    "The issuer's VAT number, or else its company identification number (Swiss UID); for a "
                    "self-billing Gutschrift the buyer's, never the supplier's number printed beside it"
                ),
                _A.TOTAL_AMOUNT: (
                    "The total amount credited, including VAT where VAT is shown, with its sign as written"
                ),
                _A.DUE_DATE: "The date by which the credit is paid out or settled",
                _A.PERIOD: "The service or billing period the credit concerns",
                _A.RELATED_REFERENCES: (
                    "Numbers of the invoices the credit note corrects or cancels, and of the orders or contracts it "
                    "names; not a customer number or an account number"
                ),
            },
            references=[
                "https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-creditnote/tree/",
                "https://www.gesetze-im-internet.de/ustg_1980/__14.html",
            ],
        ),
        DocumentTypeDefinition(
            type=DocumentType.OFFER,
            description=(
                "Proposes goods or services at a stated price before they are ordered, and requests no payment for "
                "anything delivered: offers, quotes, cost estimates and pro-forma invoices."
            ),
            excludes=[
                "an order confirmation, which confirms an order already placed",
                "a call for tenders, which asks for prices instead of stating them",
            ],
            cue_words=[
                "Offerte",
                "Angebot",
                "Kostenvoranschlag",
                "Proformarechnung",
                "devis",
                "offre",
                "facture proforma",
                "offerta",
                "preventivo",
                "quote",
                "quotation",
                "estimate",
                "pro forma invoice",
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
                _A.VALID_UNTIL,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.ISSUER: "The supplier making the offer, by its legal name",
                _A.RECIPIENT: "The prospective customer the offer is addressed to",
                _A.TOTAL_AMOUNT: "The offer's total price, including VAT where VAT is shown",
                _A.VALID_UNTIL: (
                    "The date until which the offer is valid, or its validity as written when no date is stated"
                ),
                _A.RELATED_REFERENCES: "Numbers of the inquiry, tender or earlier offer it answers",
            },
            references=["https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.html"],
        ),
        DocumentTypeDefinition(
            type=DocumentType.ORDER,
            description=(
                "Places or confirms an order for goods or services: purchase orders the buyer sends, and order "
                "confirmations (Auftragsbestätigung) the supplier sends back, including an online shop's."
            ),
            excludes=[
                "an offer made before any order",
                "a delivery note accompanying the goods",
                "an invoice requesting payment for the order",
            ],
            cue_words=[
                "Bestellung",
                "Auftragsbestätigung",
                "Bestellbestätigung",
                "bon de commande",
                "confirmation de commande",
                "ordine",
                "conferma d'ordine",
                "purchase order",
                "order confirmation",
                "sales order",
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
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.ISSUER: (
                    "The party that sent the document, by its legal name: the buyer for a purchase order, the "
                    "supplier for an order confirmation"
                ),
                _A.TOTAL_AMOUNT: "The order total, including VAT where VAT is shown",
                _A.DUE_DATE: "The agreed or requested delivery date",
                _A.RELATED_REFERENCES: (
                    "Numbers of the offer, the purchase order or the contract it refers to; not a customer number"
                ),
            },
            references=[
                "https://docs.peppol.eu/poacc/upgrade-3/syntax/Order/tree/",
                "https://docs.peppol.eu/poacc/upgrade-3/syntax/OrderResponse/tree/",
            ],
        ),
        DocumentTypeDefinition(
            type=DocumentType.DELIVERY_NOTE,
            description=(
                "Accompanies delivered goods or confirms their delivery, with or without prices: delivery notes and "
                "packing slips."
            ),
            excludes=["an invoice that also lists the delivered goods", "an order confirmation"],
            cue_words=[
                "Lieferschein",
                "Packliste",
                "bon de livraison",
                "bulletin de livraison",
                "bolla di consegna",
                "documento di trasporto",
                "delivery note",
                "packing slip",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.DATE: "The delivery or dispatch date the note carries",
                _A.REFERENCE_NUMBER: "The delivery note's own number; never the number of the order it delivers",
                _A.ISSUER: "The supplier that delivers, by its legal name",
                _A.RECIPIENT: "The customer the goods are delivered to",
                _A.RELATED_REFERENCES: "Numbers of the orders or order confirmations it delivers",
            },
            references=["https://docs.peppol.eu/poacc/upgrade-3/syntax/DespatchAdvice/tree/"],
        ),
        DocumentTypeDefinition(
            type=DocumentType.RECEIPT,
            description=(
                "Confirms a payment already made: till receipts, cash receipts (Quittung) and payment confirmations."
            ),
            excludes=[
                "an invoice, even one stamped as paid",
                "a QR payment part (Zahlteil) on its own",
                "an account statement listing payments",
            ],
            cue_words=[
                "Quittung",
                "Kassenbon",
                "Zahlungsbestätigung",
                "quittance",
                "ticket de caisse",
                "reçu",
                "scontrino",
                "ricevuta",
                "receipt",
                "payment confirmation",
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
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.REFERENCE_NUMBER: "The receipt or transaction number",
                _A.ISSUER: "The merchant or party that received the payment, by its legal name",
                _A.RECIPIENT: "The payer, only when the receipt names one",
                _A.TOTAL_AMOUNT: "The total amount paid",
                _A.RELATED_REFERENCES: "Numbers of the invoices the payment settles",
            },
            references=["https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/receipt"],
        ),
        DocumentTypeDefinition(
            type=DocumentType.ACCOUNT_STATEMENT,
            description=(
                "Lists the movements, balance or open items of an account: bank and credit card statements, and a "
                "supplier's statement of open items (Kontoauszug)."
            ),
            excludes=["a payment reminder, which asks for overdue invoices to be paid"],
            cue_words=[
                "Kontoauszug",
                "Kreditkartenabrechnung",
                "Offene Posten",
                "relevé de compte",
                "extrait de compte",
                "estratto conto",
                "account statement",
                "bank statement",
                "statement of account",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.TOTAL_AMOUNT,
                _A.CURRENCY,
                _A.DUE_DATE,
                _A.PERIOD,
            ],
            meanings={
                _A.DATE: (
                    "The statement date, or else the date of its closing balance; never the opening balance's date"
                ),
                _A.REFERENCE_NUMBER: "The statement's own number; never an account number or IBAN",
                _A.ISSUER: "The bank, card issuer or supplier that sends the statement, by its legal name",
                _A.RECIPIENT: "The account holder or customer",
                _A.TOTAL_AMOUNT: "The closing balance, or the amount due on a card or open-items statement",
                _A.DUE_DATE: "The date by which the amount due must be paid",
                _A.PERIOD: "The period the statement covers; never a single date the balance is stated at",
            },
            references=[
                "https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/bank-statement"
            ],
        ),
        DocumentTypeDefinition(
            type=DocumentType.PAYMENT_REMINDER,
            description=(
                "Asks for payment of one or more overdue invoices: payment reminders, dunning letters (Mahnung) and "
                "overdue notices, at any dunning level."
            ),
            excludes=["the invoice itself", "an account statement listing open items without asking for payment"],
            cue_words=[
                "Zahlungserinnerung",
                "Mahnung",
                "rappel",
                "sommation",
                "sollecito",
                "payment reminder",
                "overdue notice",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.TOTAL_AMOUNT,
                _A.CURRENCY,
                _A.DUE_DATE,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.REFERENCE_NUMBER: "The reminder's own number; never the number of the invoice it chases",
                _A.ISSUER: "The creditor asking for payment, by its legal name",
                _A.RECIPIENT: "The debtor the reminder is addressed to",
                _A.TOTAL_AMOUNT: "The total amount now to pay, including reminder fees and interest",
                _A.DUE_DATE: "The new payment deadline, or the terms as written when no date is stated",
                _A.RELATED_REFERENCES: "Numbers of the overdue invoices it chases",
            },
            references=["https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_102"],
        ),
        DocumentTypeDefinition(
            type=DocumentType.CONTRACT,
            description=(
                "Records an agreement between named parties and its terms, signed or as a draft: contracts, framework "
                "and service agreements, employment, rental and licence agreements, and amendments to them."
            ),
            excludes=[
                "a service level agreement on its own, which is a service_level_agreement",
                "an offer or an order confirmation",
                "general terms and conditions, or a policy, not agreed between named parties",
            ],
            cue_words=[
                "Vertrag",
                "Vereinbarung",
                "Rahmenvertrag",
                "Arbeitsvertrag",
                "Mietvertrag",
                "Nachtrag",
                "contrat",
                "avenant",
                "contratto",
                "accordo",
                "contract",
                "agreement",
                "amendment",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.TOTAL_AMOUNT,
                _A.CURRENCY,
                _A.PERIOD,
                _A.NOTICE_PERIOD,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.DATE: "The date it was signed or concluded, else the date it carries",
                _A.ISSUER: (
                    "The party that provides the goods, service, work, premises, licence or position: the supplier, "
                    "contractor, landlord, licensor or employer, by its legal name"
                ),
                _A.RECIPIENT: "The other party: the customer, client, tenant, licensee or employee",
                _A.TOTAL_AMOUNT: "The contract value, or else the recurring fee, rent or salary it states",
                _A.PERIOD: "Its term, only when it states both its start and its end date; never its start alone",
                _A.RELATED_REFERENCES: "Numbers of the offer, the framework contract or the contract it amends",
            },
            references=[
                "https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/contract",
                "https://www.atticusprojectai.org/cuad",
            ],
        ),
        DocumentTypeDefinition(
            type=DocumentType.SERVICE_LEVEL_AGREEMENT,
            description=(
                "Defines the service levels a provider commits to for a service, such as availability, response and "
                "resolution times and support hours, and what applies when they are missed: a stand-alone service "
                "level agreement (SLA) or a service level annex."
            ),
            excludes=[
                "a contract that includes service levels among its other terms: it is a contract, with "
                "service_level_agreement as a secondary type",
                "a support or operations manual",
            ],
            cue_words=[
                "Service Level Agreement",
                "SLA",
                "Leistungsvereinbarung",
                "Verfügbarkeit",
                "Reaktionszeit",
                "accord de niveau de service",
                "disponibilité",
                "accordo sul livello di servizio",
                "service level agreement",
                "uptime",
                "response time",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.PERIOD,
                _A.NOTICE_PERIOD,
                _A.SERVICE_LEVELS,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.DATE: "The date it was signed or concluded, else the date it carries",
                _A.ISSUER: "The service provider, by its legal name",
                _A.RECIPIENT: "The customer that receives the service",
                _A.PERIOD: "Its term, only when it states both its start and its end date; never its start alone",
                _A.RELATED_REFERENCES: "Numbers of the master or framework contract it belongs to",
            },
            references=[
                "https://digital-strategy.ec.europa.eu/en/news/cloud-service-level-agreement-standardisation-guidelines"
            ],
        ),
        DocumentTypeDefinition(
            type=DocumentType.LETTER,
            description=(
                "A letter or e-mail that is not of another type in this list: notices, requests, confirmations, "
                "terminations, invitations and recommendations."
            ),
            excludes=["an offer, order, invoice, reminder or contract sent as a letter, which is that type"],
            cue_words=[
                "Brief",
                "Schreiben",
                "Kündigung",
                "Mitteilung",
                "Einladung",
                "lettre",
                "courrier",
                "résiliation",
                "lettera",
                "letter",
                "notice",
                "e-mail",
            ],
            attributes=[
                _A.DATE,
                _A.REFERENCE_NUMBER,
                _A.ISSUER,
                _A.RECIPIENT,
                _A.PARTIES,
                _A.RELATED_REFERENCES,
            ],
            meanings={
                _A.REFERENCE_NUMBER: 'The letter\'s own reference, such as "Unser Zeichen" or "Notre référence"',
                _A.RECIPIENT: (
                    "The organisation or person the letter is addressed to, by name; never a salutation such as "
                    '"Dear customers" or an e-mail address'
                ),
                _A.ISSUER: "The sender: the organisation, or the person when no organisation sends it",
                _A.RELATED_REFERENCES: (
                    "Numbers of the contracts, invoices, orders or other documents it refers to; not a customer number"
                ),
            },
        ),
        DocumentTypeDefinition(
            type=DocumentType.REPORT,
            description=(
                "Reports results, status or findings on a period or a subject: annual and quarterly reports, project "
                "status reports, audit and inspection reports, and analyses."
            ),
            excludes=["meeting minutes", "a slide presentation", "an account statement"],
            cue_words=[
                "Bericht",
                "Jahresbericht",
                "Statusbericht",
                "Prüfbericht",
                "rapport",
                "rapport annuel",
                "rapporto",
                "relazione",
                "report",
                "annual report",
                "status report",
                "audit report",
            ],
            attributes=[_A.DATE, _A.ISSUER, _A.PERIOD],
            meanings={
                _A.ISSUER: "The organisation that wrote the report, or the author when no organisation is named",
                _A.PERIOD: (
                    "The period the report covers, such as a year, a quarter or a month; never the single date of an "
                    "inspection or a visit"
                ),
            },
        ),
        DocumentTypeDefinition(
            type=DocumentType.OTHER,
            version=2,
            description=(
                "Any document that is not of another type in this list, such as meeting minutes, manuals, policies, "
                "presentations, forms and tenders."
            ),
        ),
    )

    @classmethod
    def type_definition(cls, document_type: DocumentType) -> DocumentTypeDefinition:
        return next(definition for definition in cls.TYPES if definition.type == document_type)

    @classmethod
    def attribute_definition(cls, attribute: DocumentAttribute) -> DocumentAttributeDefinition:
        return next(definition for definition in cls.ATTRIBUTES if definition.attribute == attribute)

    @classmethod
    def needs_classification(
        cls, classification_version: int | None, document_type: str | None, type_version: int | None
    ) -> bool:
        """Whether a document classified with these stored versions would now be classified differently."""
        if classification_version is None or classification_version < cls.VERSION:
            return True
        if document_type not in DocumentType:
            return True
        return (type_version or 0) < cls.type_definition(DocumentType(document_type)).version

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
            DOCUMENT_TYPE_VERSION,
            DOCUMENT_NORMALIZER_VERSION,
            *attribute_keys,
        ]

    @classmethod
    def value_keys(cls) -> list[str]:
        """The attribute keys that hold values a filter compares, i.e. every attribute key but the copied text."""
        return [key for definition in cls.ATTRIBUTES for key in definition.stored_keys() if key != definition.raw_key]

    @classmethod
    def filter_keys(cls) -> list[str]:
        """The keys a retrieval filter may name on any knowledge database: the types and the values, not the copies."""
        return [DOCUMENT_TYPE, DOCUMENT_TYPES, *cls.value_keys()]

    @classmethod
    def prompt_types(cls) -> list[dict[str, Any]]:
        return [
            definition.model_dump(include={"type", "description", "excludes", "cue_words"}) for definition in cls.TYPES
        ]

    @classmethod
    def prompt_attributes(cls) -> list[dict[str, Any]]:
        """Each attribute the model fills, with its meaning for the types it applies to.

        Types sharing a meaning are named together, so the prompt grows with the meanings that differ, not with the
        number of types.
        """
        return [
            {"name": definition.attribute.value, "meanings": cls._meanings_by_type(definition)}
            for definition in cls.extracted_attributes()
        ]

    @classmethod
    def _meanings_by_type(cls, definition: DocumentAttributeDefinition) -> list[dict[str, Any]]:
        types_by_meaning: dict[str, list[str]] = {}
        for type_definition in cls.TYPES:
            if definition.attribute in type_definition.attributes:
                meaning = type_definition.meaning_of(definition.attribute, definition.meaning)
                types_by_meaning.setdefault(meaning, []).append(type_definition.type.value)
        return [{"types": types, "meaning": meaning} for meaning, types in types_by_meaning.items()]
