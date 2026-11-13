---
title: Document types and attributes
---

# Document types and attributes

Agents that pick documents from a knowledge database, such as Document Tables, can filter by what a document is and by a
few of its business values, for example "invoices from Hooli AG dated 2025". A model reads each document once and
assigns it one type from a fixed list, then copies that type's attributes from it. Code checks what the model copied and
turns it into values a filter can compare.

The list is fixed on purpose. A filter over a known vocabulary is reliable; types and attribute names a model invents
per document are not. Changing the list is a release, not a setting, and is the same for every tenant and knowledge
database.

## Types

| Type      | A document of this type…                                                                                                                                                                                                 |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `invoice` | requests payment for goods or services that were delivered or agreed, and states an amount the recipient owes the issuer. Includes partial, final and advance-payment invoices, QR-bills, and utility and telecom bills. |
| `other`   | is anything else.                                                                                                                                                                                                        |

Not invoices, although they look alike: offers and quotes, order confirmations (even with a total), delivery notes,
receipts for a payment already made, credit notes, payment reminders, account statements and pro-forma invoices. They
are `other` until the list has a type for them. A German "Gutschrift" is `other` too, even a self-billing one issued by
the buyer under § 14 UStG: the word also means credit note, and the two are told apart once the list has a credit note
type.

A document has one **primary type**, the one that describes it as a whole. It may also list up to three **secondary
types**, for example an invoice that is also its delivery note. Attributes always belong to the primary type; a
secondary type only makes the document findable under that type too. A document that merely mentions another document's
number is not of that document's type.

## Invoice attributes

| Attribute                     | Value type | Meaning                                                                                                                                                                            | Example: copied → stored                     |
| ----------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `document_date`               | date       | Issue date. Not the due date, the delivery date or the date of supply.                                                                                                             | `14. März 2025` → `2025-03-14`               |
| `document_reference_number`   | text       | Invoice number.                                                                                                                                                                    | `RE-2025-0412` → `RE-2025-0412`              |
| `document_issuer`             | text       | Seller who issued the invoice and is owed the payment, by its legal name. Never a factoring or collection company named as payee.                                                  | `Hooli AG`                                   |
| `document_issuer_tax_id`      | tax ID     | Issuer's VAT number, or else its Swiss UID. Never a commercial register number or the recipient's number.                                                                          | `CHE-123.456.788 MWST` → `CHE123456788`      |
| `document_recipient`          | text       | Customer the invoice is addressed to: the billed organisation or person, not a contact person within it.                                                                           | `Muster Treuhand GmbH`                       |
| `document_parties`            | text list  | Issuer and recipient, computed from the two above.                                                                                                                                 | `[Hooli AG, Muster Treuhand GmbH]`           |
| `document_total_amount`       | amount     | Final total of this invoice, including VAT where VAT is charged. Not an amount due that adds earlier unpaid balances.                                                              | `CHF 12'496.36` → `12496.36`                 |
| `document_currency`           | currency   | ISO 4217 code of that total. Amounts converted into another currency are ignored.                                                                                                  | `Fr.` → `CHF`                                |
| `document_due_date`           | date       | Payment due date. Payment terms without a date are kept as text only.                                                                                                              | `Zahlbar innert 30 Tagen` → empty            |
| `document_period_start`/`end` | period     | Service or billing period, or the single date of supply.                                                                                                                           | `Februar 2025` → `2025-02-01` / `2025-02-28` |
| `document_related_references` | text list  | Numbers of the orders, order confirmations, delivery notes or contracts the invoice refers to. Not the QR payment reference, a customer number or an account number. At most five. | `[PO-3333, LS-8812]`                         |

Left out on purpose: addresses and contact details, bank details, customer and account numbers, net and tax amounts, tax
breakdowns and line items. They are not useful for picking documents, some of them are personal or financial data, and
line items are read when a request needs them.

The attributes follow the invoice models of
[Azure Document Intelligence](https://github.com/Azure-Samples/document-intelligence-code-samples/blob/main/schema/2024-11-30-ga/invoice.md),
[Google Document AI](https://docs.cloud.google.com/document-ai/docs/processors-list),
[AWS Textract](https://docs.aws.amazon.com/textract/latest/dg/invoices-receipts.html) and the
[DocILE benchmark](https://github.com/rossumai/docile/blob/main/docile/dataset/__init__.py), with meanings taken from
[EN 16931](https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/tree/), the
[Swiss VAT Act, Art. 26](https://justement.ch/de/doc/act/ch/641_20/tit_2/chap_6/art_26) and the
[German VAT Act, § 14](https://www.gesetze-im-internet.de/ustg_1980/__14.html). Swiss law does not require an invoice
number, so an empty `document_reference_number` on a Swiss invoice is expected.

## How values are stored

The model only copies text; it never converts or completes a value. For every attribute, the document and each of its
chunks in the vector store carry:

- the **value**, under the attribute's key, read by code from the copied text and empty when it cannot be read;
- the **copied text**, under the key with `_raw` appended;
- for dates and periods, the **precision** (`day`, `month`, `quarter` or `year`), under the key with `_precision`
  appended, so "März 2025" is never mistaken for 1 March.

Every attribute of the type is present, empty where unknown. A filter should treat an empty value as unknown, not as a
mismatch. An attribute that does not apply to a type is not stored on documents of that type.

Rules that keep values from being guessed:

- **Not in the document, not stored.** Text the model copied that the document does not contain is dropped.
- **Ambiguous dates stay empty.** `03/04/2025` could be March or April, so only its text is kept. Dates with dots or
  dashes are read day first; a slash date only when one order is impossible.
- **Tax IDs are checked.** A Swiss UID must pass its check digit. An EU VAT number must match its country's format. A
  German tax office number (Steuernummer) has no standard form and is kept as text only.
- **Amounts in every convention.** `12'496.36`, `12.496,36`, `12 496,36` and `12,496.36` are the same amount; the Swiss
  `1'250.–` is 1250.00. A negative total keeps its sign. A bare `$` is not read as a currency.

Each document also records `document_classification_version` and `document_normalizer_version`. When the list of types
or the meaning of an attribute changes, the classification version rises and the documents are classified again. When
only the reading of copied text improves, the normaliser version rises and values are read again from the stored text,
without asking a model.
