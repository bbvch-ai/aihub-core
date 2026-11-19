# A Closed Set of Document Types and Attributes, Copied by a Model and Read by Code

## Context

Agents that select documents from a knowledge database, Document Tables first (#2348), can only filter by path and text.
Ingestion stores timestamps and a title derived from the filename, but not what a document is or its business values,
such as an invoice's date or issuer. So an agent either guesses from paths or reads every document in scope.

#2346 asks for a closed set of document types, each with a fixed list of attributes extracted once at ingestion and
stored as filterable metadata. Planning settled what the set contains and how values are produced and stored. It starts
with invoices (#2480), because the 106-invoice benchmark of #2312 and #2393 can measure the result before ingestion
stores it (#2481). Further types follow in #2485.

## Decision Drivers

- **Filters must be reliable.** A wrong value silently drops a correct document from a result; an empty value only costs
  reading it. So a value is never guessed, and that is enforced in code rather than left to the model.
- **One filter across types.** "Everything from Hooli in 2025" must not need one date key per type.
- **Values improve without re-running the model.** A parser that learns a new date format should not cost a model call
  per document.
- **Existing content must not change.** Embeddings and retrieval of ingested documents stay as they are, and a backfill
  must not embed again.
- **Sovereignty.** A knowledge database's model choice reflects where its data may go.

## Decision

1. **A closed set in code.** `DocumentTypeCatalog` in `packages/core` defines the types and their attributes: `invoice`
   and `other` first, fourteen more since #2485 (see Consequences). The output schema, the prompt, the stored keys and
   the documentation all come from it. Changing the set is a release; types per tenant or database are out of scope.
2. **Shared attributes, applicability and meaning per type.** Attributes are shared keys (`document_date`,
   `document_issuer`, …). Each type lists the attributes that apply to it, so a filter on an attribute never matches a
   type it does not apply to, and overrides an attribute's meaning where the general one is ambiguous (an invoice's date
   is its issue date). Considered and rejected: keys per type (`invoice_date`, `contract_date`), which make every
   cross-type filter a disjunction over keys that grows with each type.
3. **One primary type, up to three secondary labels.** The primary type owns the attributes; a secondary type only makes
   the document findable under it. Splitting bundles of several documents is out of scope.
4. **The model copies, code reads.** One structured-output call per document returns the types and each attribute's text
   exactly as written. `DocumentValueNormalizer` drops text that is not in the document, stores attributes that do not
   apply as absent, reads dates, periods, amounts, currencies and tax IDs into one form, and checks a Swiss UID's check
   digit. Unreadable text keeps its copy with an empty value (`_raw` key), and dates keep their precision.
5. **Versions per document, at the narrowest level a change needs.** Re-classifying costs a model call per document, so
   a change redoes only the documents it can affect:
   - `document_type_version` is the version of the document's own type. Changing a type's definition raises it and
     redoes that type's documents only. `other` means "none of the listed types", so adding a type raises `other`'s
     version and redoes the documents marked `other`, not every invoice.
   - `document_classification_version` rises for a change that can affect any document (a shared attribute's meaning,
     the prompt's rules) and redoes every document.
   - `document_normalizer_version` rises when a parser changes, and values are read again from the stored copies without
     a model call.
6. **The database's own text model.** The classifier takes the model as an argument; ingestion passes the knowledge
   database's text model rather than a deployment-wide one, so no document reaches a model its database did not approve.
   An optional override can follow if measured cost demands it.
7. **Metadata only.** Values are stored on the document record and on every chunk, kept out of embedded and model-facing
   text. `IngestedNode` keeps them apart from a synced record's fields, although both are excluded from the embedding.
8. **Names are stored like other values.** The PII guardrail keeps data from leaving the platform, not from being stored
   inside a tenant's knowledge database, so recipients that are people are stored as written, and so are the
   participants of an e-mail thread. Whether participants of internal e-mails should be stored at all is open for the
   data protection owner (#2485).

The classifier reads a document's first two pages, capped at 8,000 characters, and the last 1,500 characters of the
rest, where totals and payment terms often stand.

## Consequences

- Agents can filter by type and attributes in the document listing and in vector search, once ingestion stores them
  (#2482) and existing documents are backfilled (#2483).
- Every German "Gutschrift" is a `credit_note` since #2485, a self-billing one under § 14 UStG included, with the buyer
  who issues it as the issuer. The evaluation (#2481) showed that calling self-billing Gutschriften invoices made the
  model take a plain credit note for one and swap issuer and recipient.
- Two more boundaries, set on 2026-11-18 after testing 141 sample documents (ZUGFeRD/Factur-X, scans, generated Swiss QR
  invoices): a correction of an earlier invoice whose total is negative works as a credit note (`other` until #2485,
  `credit_note` since), while a final invoice whose deducted advance payments make its total negative stays an invoice;
  a QR payment part on its own, without the invoice it belongs to, is `other`.
- A slash date both orders allow (`05/11/2026`) is read in the order the document itself shows: its other slash dates
  settle it when one of them allows only one order (`11/17/2026` is month first). Without such a date, it is read day
  first when the document's currency is CHF, EUR or another non-dollar currency, and stays empty with USD, a bare `$`,
  no currency or contradicting dates: month first is the US order. A French sample written month first under English
  labels showed that the currency alone is not enough.
- Every ingested document costs one more model call, through the PII guardrail for external models. #2482 measures it.
- With only `invoice` and `other`, everything that is not an invoice is `other`. Adding a type raises `other`'s version,
  so only documents marked `other` are classified again. A type carved out of an existing one (say, credit notes out of
  invoices) narrows that type too, so its version rises as well.
- #2485 (2026-11-18) added `credit_note`, `offer`, `order`, `delivery_note`, `receipt`, `account_statement`,
  `payment_reminder`, `contract`, `service_level_agreement`, `letter`, `report`, `documentation`, `policy` and
  `email_thread`: the look-alikes the invoice evaluation already measured, the general types #2346 named, SLAs, and the
  manuals, rules and e-mail histories customers hold. Pro-forma invoices are offers. A `letter` is a single letter or
  e-mail, a conversation of several is an `email_thread`. Policies, guidelines, directives, staff handbooks that set
  rules and general terms and conditions are a `policy`; meeting minutes, presentations, forms and tenders stay `other`.
  Five attributes came with them (`document_valid_until`, `document_notice_period`, `document_service_levels`,
  `document_product` for documentation and `document_participants` for threads); a contract's or SLA's issuer is the
  party that provides the service, so issuer and recipient filters keep working across types. `document_parties` is
  derived from issuer, recipient and participants, and applies to a type that has any of them, so one parties filter
  finds a company's invoices and its conversations alike. Only `other`'s version rose: invoices keep theirs, since none
  of the new types was carved out of `invoice`.
- Classification stays one call per document. On 154 synthetic documents (8 to 21 per type) every type reached 100%
  recall and precision, and every attribute stayed under 2% wrong or guessed, in two runs in a row, so a second,
  type-specific extraction call is not worth doubling the cost. The prompt grew from about 4,800 to 19,300 characters:
  on the short synthetic documents about 4,400 prompt tokens and a median of 3 to 8 s per document (the provider's
  latency varied between runs), against 1,070 tokens and 1.4 s with only invoices. Types sharing an attribute's meaning
  are named together in the prompt, so it grows with the meanings that differ.
- `document_product` and `document_participants` apply to one type each, so with eight or nine documents one slip is 11%
  and misses the 2% target on its own. Both reached it only after their meanings named what the model otherwise added:
  neither a handbook's own title nor a work process it describes is a product, and a participant includes the company a
  signature names but never a party a message only mentions. A name the document writes only inside an e-mail address is
  dropped in code, since the model builds names from mailbox domains.
- A backfill on the dev stack's 12 documents classified a rule-setting IT security guideline with a version number as
  `documentation`; the synthetic sample had no guideline titled like one. `documentation` now excludes policies,
  guidelines and directives that set rules. They first went to `other`, which put the same backfill's rule-based
  employee handbook there too; since HR and compliance rules are among what people ask a knowledge base most, they
  became a type of their own, `policy`, with the policies, guidelines and general terms of `other`'s sample and three
  new cases. The same backfill, with `other`'s version raised, classified only the documents marked `other` again.
- The attribute target (at most 2% wrong or guessed) holds per attribute over all types, as it did for invoices; shares
  per type and attribute are reported for diagnosis. With eight to ten documents a type, one slip is 10% of a type.
- An attribute a parser cannot read stays empty, and the share of such values per attribute shows which formats to
  support next (#2481 reports it).
- Prompts for ingestion stay English, like table refinement's: ingestion has no user language.
