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

| Type                      | A document of this type…                                                                                                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `invoice`                 | requests payment for goods or services that were delivered or agreed. Includes partial, final and advance-payment invoices, QR-bills, and utility and telecom bills.                                                |
| `credit_note`             | reduces, cancels or credits an amount instead of requesting one: credit notes, cancellations (Storno), corrections with a negative total, and a self-billing Gutschrift under § 14 UStG.                            |
| `offer`                   | proposes goods or services at a stated price before they are ordered: offers, quotes, cost estimates and pro-forma invoices.                                                                                        |
| `order`                   | places or confirms an order: purchase orders the buyer sends and order confirmations the supplier sends back.                                                                                                       |
| `delivery_note`           | accompanies delivered goods or confirms their delivery: delivery notes and packing slips.                                                                                                                           |
| `receipt`                 | confirms a payment already made: till receipts, cash receipts (Quittung) and payment confirmations.                                                                                                                 |
| `account_statement`       | lists the movements, balance or open items of an account: bank and credit card statements, and a supplier's statement of open items.                                                                                |
| `payment_reminder`        | asks for payment of overdue invoices: payment reminders, dunning letters (Mahnung) and overdue notices.                                                                                                             |
| `contract`                | records an agreement between named parties: contracts, framework, employment, rental and licence agreements, and amendments.                                                                                        |
| `service_level_agreement` | defines the service levels a provider commits to, such as availability and response times: a stand-alone SLA or a service level annex.                                                                              |
| `letter`                  | is a single letter or e-mail of no other type: notices, requests, confirmations, terminations and invitations.                                                                                                      |
| `report`                  | reports results, status or findings: annual and quarterly reports, project status, audit and inspection reports.                                                                                                    |
| `documentation`           | explains how to install, use, operate or maintain a product, system or process: handbooks, manuals, guides, technical documentation and specifications, technical or not.                                           |
| `policy`                  | sets rules that employees, members or customers must follow: policies, guidelines, directives, regulations, codes of conduct, staff handbooks that set working hours or holidays, and general terms and conditions. |
| `email_thread`            | is a conversation of several e-mails, replies or forwards kept in one document, such as an exported thread or a mailbox history.                                                                                    |
| `other`                   | is anything else, for example meeting minutes, presentations, forms and tenders.                                                                                                                                    |

A final invoice stays an invoice when the advance payments it deducts make its total negative; a correction of an
earlier invoice whose total is negative is a credit note. A QR payment part on its own, without its invoice, is `other`.
An offer, order, invoice or contract sent as a letter is of that type, not a letter. A conversation of several e-mails
is an `email_thread`; a single e-mail is a `letter`. A policy, guideline or regulation that sets rules is a `policy`,
not `documentation`, even when it carries a version number or explains what to do; so is a staff or employee handbook,
even when it explains how to request holidays or report sick. General terms and conditions not agreed between named
parties are a `policy`, not a `contract`, and a service level annex that commits to service levels is a
`service_level_agreement` even when it is called a service description (Leistungsbeschreibung).

A document has one **primary type**, the one that describes it as a whole. It may also list up to three **secondary
types**, for example an invoice that is also its delivery note, or a contract with a service level annex (`contract`,
with `service_level_agreement` as a secondary type). Attributes always belong to the primary type; a secondary type only
makes the document findable under that type too. A document that merely mentions another document's number is not of
that document's type.

## Attributes per type

Attributes are shared across types, so one filter such as "dated 2025" or "issuer Hooli AG" works on every type that has
the attribute. Each type has only the attributes that make sense for it:

| Attribute                     | invoice, credit note | offer | order | delivery note | receipt | statement | reminder | contract | SLA | letter | report | documentation | policy | e-mail thread |
| ----------------------------- | :------------------: | :---: | :---: | :-----------: | :-----: | :-------: | :------: | :------: | :-: | :----: | :----: | :-----------: | :----: | :-----------: |
| `document_date`               |          ✓           |   ✓   |   ✓   |       ✓       |    ✓    |     ✓     |    ✓     |    ✓     |  ✓  |   ✓    |   ✓    |       ✓       |   ✓    |       ✓       |
| `document_reference_number`   |          ✓           |   ✓   |   ✓   |       ✓       |    ✓    |     ✓     |    ✓     |    ✓     |  ✓  |   ✓    |        |       ✓       |   ✓    |               |
| `document_issuer`             |          ✓           |   ✓   |   ✓   |       ✓       |    ✓    |     ✓     |    ✓     |    ✓     |  ✓  |   ✓    |   ✓    |       ✓       |   ✓    |               |
| `document_issuer_tax_id`      |          ✓           |   ✓   |   ✓   |               |    ✓    |           |          |          |     |        |        |               |        |               |
| `document_recipient`          |          ✓           |   ✓   |   ✓   |       ✓       |    ✓    |     ✓     |    ✓     |    ✓     |  ✓  |   ✓    |        |               |        |               |
| `document_parties`            |          ✓           |   ✓   |   ✓   |       ✓       |    ✓    |     ✓     |    ✓     |    ✓     |  ✓  |   ✓    |        |               |        |       ✓       |
| `document_total_amount`       |          ✓           |   ✓   |   ✓   |               |    ✓    |     ✓     |    ✓     |    ✓     |     |        |        |               |        |               |
| `document_currency`           |          ✓           |   ✓   |   ✓   |               |    ✓    |     ✓     |    ✓     |    ✓     |     |        |        |               |        |               |
| `document_due_date`           |          ✓           |       |   ✓   |               |         |     ✓     |    ✓     |          |     |        |        |               |        |               |
| `document_period_start`/`end` |          ✓           |       |       |               |         |     ✓     |          |    ✓     |  ✓  |        |   ✓    |               |        |               |
| `document_related_references` |          ✓           |   ✓   |   ✓   |       ✓       |    ✓    |           |    ✓     |    ✓     |  ✓  |   ✓    |        |               |        |       ✓       |
| `document_valid_until`        |                      |   ✓   |       |               |         |           |          |          |     |        |        |               |        |               |
| `document_notice_period`      |                      |       |       |               |         |           |          |    ✓     |  ✓  |        |        |               |        |               |
| `document_service_levels`     |                      |       |       |               |         |           |          |          |  ✓  |        |        |               |        |               |
| `document_product`            |                      |       |       |               |         |           |          |          |     |        |        |       ✓       |        |               |
| `document_participants`       |                      |       |       |               |         |           |          |          |     |        |        |               |        |       ✓       |
| `document_jurisdiction`       |                      |       |       |               |         |           |          |    ✓     |  ✓  |        |        |               |   ✓    |               |

Where an attribute means something specific for a type:

- **Issuer and recipient.** The issuer is the party that sends the document; the recipient is the party it is addressed
  to. For an order, the issuer is the buyer on a purchase order and the supplier on an order confirmation. For a
  contract or SLA, the issuer is the party that provides the goods, service, premises, licence or position (supplier,
  contractor, landlord, licensor, employer, service provider) and the recipient the other party. For a receipt, the
  issuer is the merchant and the recipient the payer, only when named. For a self-billing Gutschrift, the issuer is the
  buyer who issues it. For documentation, the issuer is the manufacturer, publisher or organisation that wrote it, or
  the author when no organisation is named. For a policy, the issuer is the organisation that sets the rules.
- **Total amount.** For a credit note, the amount credited with its sign as written; for a statement, the closing
  balance or the amount due; for a reminder, the amount now to pay including fees and interest; for a contract, the
  contract value or else the recurring fee, rent or salary.
- **Due date.** For an order, the delivery date; for a reminder, the new payment deadline; for a credit note, the date
  the credit is paid out.
- **Reference number.** A statement's own number, never an account number or IBAN; a reminder's own number, never the
  number of the invoice it chases (that one is a related reference); a letter's own reference, such as "Unser Zeichen";
  for documentation and a policy, its document number, and its version or release number without the word "Version" only
  when it has no document number.
- **Date.** For documentation, its publication or revision date; for a policy, the date it takes effect, else the date
  it was issued or revised; for an e-mail thread, the date of the latest message.
- **Period.** For a contract or SLA, its term. A single date is the whole period unless a word next to it says which end
  it is: a contract that begins on a date and runs until terminated ("ab 1. Juli 2025", "tritt am 1. März 2026 in
  Kraft", "prend effet le", "from") stores only its start, and one that names only its end ("endet am 30. Juni 2027",
  "until") only its end. Only words in the date's own sentence count. So "contracts ending in 2026" finds every contract
  that states its end, and the date it was signed is never its start. A contract that states its start and its end on
  lines of their own ("Vertragsbeginn 1. April 2025", "Vertragsende 31. März 2028") keeps both, when every date the model
  names is in the document; a word the model adds to a date is not read, only the date's own line. Every other type's
  period stays whole, whatever words stand near it.
- **Valid until**, **notice period** and **service levels** are new with these types: the date an offer is valid until;
  the notice period of a contract or SLA, kept as written; and up to five service levels an SLA commits to, copied as
  written ("Verfügbarkeit 99,9 % pro Monat").
- **Product** applies to documentation only: the product, system or service it documents, by its name as written, so a
  filter can find "the manuals for the AquaTherm WP 12". Empty when it names none; neither a work process it describes
  nor a handbook's own title is a product.
- **Participants** applies to e-mail threads only: up to ten people and organisations that send or receive a message of
  the conversation, by the name a header or signature gives, including the company a signature names for a person. An
  e-mail address or a domain is never a participant.
- **Jurisdiction** applies to contracts, SLAs and policies: the place of jurisdiction for disputes as written
  (Gerichtsstand, for, foro, courts of), such as "Luzern". A governing law alone ("Es gilt schweizerisches Recht"), a
  party's address and the place it was signed are no jurisdiction: code keeps a place only where its line, or the
  heading above it, names a court.
- **Parties** lists the issuer and the recipient, or the participants of an e-mail thread, so one parties filter finds a
  company's invoices, contracts and conversations alike.

The types and their meanings follow [UBL 2.1](https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.html) and the Peppol
[credit note](https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-creditnote/tree/),
[order](https://docs.peppol.eu/poacc/upgrade-3/syntax/Order/tree/),
[order response](https://docs.peppol.eu/poacc/upgrade-3/syntax/OrderResponse/tree/) and
[despatch advice](https://docs.peppol.eu/poacc/upgrade-3/syntax/DespatchAdvice/tree/) documents, the Azure Document
Intelligence [receipt](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/receipt),
[bank statement](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/bank-statement) and
[contract](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/contract) models, the
[CUAD](https://www.atticusprojectai.org/cuad) contract dataset, the Swiss Code of Obligations on default
([Art. 102 OR](https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_102)) and the EU
[cloud SLA standardisation guidelines](https://digital-strategy.ec.europa.eu/en/news/cloud-service-level-agreement-standardisation-guidelines).

### E-mail threads and personal data

Participants are names of people, and they are stored as written, like the recipient of a letter. A thread exported from
an internal mailbox therefore puts employees' names into the filter metadata of every chunk. When the knowledge
database's text model is an external one behind the PII guardrail, the model sees `<PERSON_1>` instead of a name; that
placeholder is not in the document, so it is dropped and the participants stay empty. Whether participants of internal
e-mails should be stored at all is an open decision for the data protection owner.

## Invoice attributes in detail

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

## When documents are classified

Ingestion classifies every new or changed document once, after parsing and table refinement, with the knowledge
database's own text model. The setting **Classify documents** of the knowledge database switches it off; it is on by
default.

- Records synced from Jira, Confluence or MediaWiki are not classified: their own fields already say what they are.
- If the model call fails, the document is ingested without a type and stays fully searchable. It is classified later by
  a backfill.
- Documents ingested before classification existed, or before the list of types changed, are classified by a backfill
  from the text already stored, without being parsed or embedded again. It runs when it is requested for a knowledge
  database; when only the reading of copied values improved, it reads the stored copies again without asking a model. A
  knowledge administrator requests it with **Classify existing documents** (the tag button next to the database's name
  on the Knowledge page). A clock shows instead while the request waits for the pipeline. Each document that still needs
  a type costs one model call. If the backfill fails three times in a row, for example while a store is unreachable, it
  stops and a warning sign next to the button says so; requesting again starts over.
- The type and attributes are filter metadata only. They are not part of the text that is embedded or shown to a model,
  so search results for existing content do not change.
- Every knowledge database can be filtered by `document_type`, `document_types` and each attribute's value, in vector
  search and in the document listing, without configuring the keys.

## How values are stored

The model only copies text; it never converts or completes a value. For every attribute, the document and each of its
chunks in the vector store carry:

- the **value**, under the attribute's key, read by code from the copied text and empty when it cannot be read;
- the **copied text**, under the key with `_raw` appended;
- for dates and periods, the **precision** (`day`, `month`, `quarter` or `year`), under the key with `_precision`
  appended, so "März 2025" is never mistaken for 1 March. For a period it describes each end that is stored: a term "ab
  März 2025" stores its start at month precision and no end.

Every attribute of the type is present, empty where unknown. A filter should treat an empty value as unknown, not as a
mismatch. An attribute that does not apply to a type is not stored on documents of that type.

Rules that keep values from being guessed:

- **Not in the document, not stored.** Text the model copied that the document does not contain is dropped.
- **A template's gap is no value.** A copy holding an unfilled placeholder (`[YYYY]`, `[####]`, `______`, an empty box)
  is stored empty, so a half-filled template does not file "NW-SLA-[YYYY]-[####]" as its number.
- **Stored text uses plain letters.** A ligature a PDF writes as one character ("ﬀ" in "Schaﬀhausen") is stored as its
  letters, so a filter for "Schaffhausen" finds it; the copied text is kept as written.
- **Ambiguous dates are read only in the document's own order.** Dates with dots or dashes are read day first. A slash
  date such as `03/04/2025` could be March or April. The document's other slash dates settle it when one of them allows
  only one order (`17/11/2025` is day first, `11/17/2025` month first). Without such a date, it is read day first on a
  document whose currency is CHF, EUR or another non-dollar currency, since month first is the US order, and stays
  empty, with only its text kept, with USD, a bare `$`, no currency, or slash dates that contradict each other.
- **A name is never an e-mail address.** An e-mail address copied with an issuer, recipient or participant is removed
  from the stored name ("Anna Meier <anna@example.ch>" is stored as "Anna Meier"), and one copied without a name is
  stored empty, with its text kept: the address names a mailbox, not a party. A name the document writes only inside an
  e-mail address ("Northpeak" from billing@northpeak.example) is dropped the same way.
- **Tax IDs are checked.** A Swiss UID must pass its check digit. An EU VAT number must match its country's format. A
  German tax office number (Steuernummer) has no standard form and is kept as text only.
- **Amounts in every convention.** `12'496.36`, `12.496,36`, `12 496,36` and `12,496.36` are the same amount; the Swiss
  `1'250.–` is 1250.00. A negative total keeps its sign when the minus touches the number (`-500`, `CHF -500`, `500-`)
  or brackets enclose the number alone (`(500.00)`); a spaced dash (`Betrag - CHF 500`) or a bracketed total with its
  currency (`Total (CHF 500.00)`) is not a sign. When a total names two currencies, the one written first is its
  currency. A bare `$` is not read as a currency.

Each document also records the versions it was classified with, so a later change redoes only the documents it can
affect:

- `document_type_version`: the version of the document's own type. When a type's definition changes, only documents of
  that type are classified again. Adding a type changes what `other` means, so only documents marked `other` are
  classified again.
- `document_classification_version`: rises for a change that can affect every document, such as the meaning of a shared
  attribute; then all documents are classified again.
- `document_normalizer_version`: rises when only the reading of copied text improves; values are read again from the
  stored text, without asking a model.
