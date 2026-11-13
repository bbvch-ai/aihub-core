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

1. **A closed set in code.** `DocumentTypeCatalog` in `packages/core` defines the types (`invoice`, `other`) and their
   attributes. The output schema, the prompt, the stored keys and the documentation all come from it. Changing the set
   is a release; types per tenant or database are out of scope.
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
5. **Two versions per document.** `document_classification_version` rises when the set or a meaning changes, and
   documents are classified again. `document_normalizer_version` rises when a parser changes, and values are read again
   from the stored copies without a model call.
6. **The database's own text model.** The classifier takes the model as an argument; ingestion passes the knowledge
   database's text model rather than a deployment-wide one, so no document reaches a model its database did not approve.
   An optional override can follow if measured cost demands it.
7. **Metadata only.** Values are stored on the document record and on every chunk, kept out of embedded and model-facing
   text. `IngestedNode` keeps them apart from a synced record's fields, although both are excluded from the embedding.
8. **Names are stored like other values.** The PII guardrail keeps data from leaving the platform, not from being stored
   inside a tenant's knowledge database, so recipients that are people are stored as written.

The classifier reads a document's first two pages, capped at 8,000 characters, and the last 1,500 characters of the
rest, where totals and payment terms often stand.

## Consequences

- Agents can filter by type and attributes in the document listing and in vector search, once ingestion stores them
  (#2482) and existing documents are backfilled (#2483).
- Every ingested document costs one more model call, through the PII guardrail for external models. #2482 measures it.
- With only `invoice` and `other`, everything that is not an invoice is `other`. Adding a type raises the classification
  version, and documents marked `other` are classified again.
- An attribute a parser cannot read stays empty, and the share of such values per attribute shows which formats to
  support next (#2481 reports it).
- Prompts for ingestion stay English, like table refinement's: ingestion has no user language.
