# Documents Selected by Their Ingested Type and Attributes

## Context

Since #2346, ingestion classifies every document into one type of a closed set (16 since #2485) and stores that type's
attributes: its date, issuer, parties, total amount, period and more (ADR
`2026_11_13_closed_document_types_and_attributes_at_ingestion`). The Document Tables agent did not use them. A request
such as "every contract with Hooli" or "offers from 2025" was answered by reading every document in scope. A
non-matching document was left out only when the per-document judge read its first window and said "no" (#2347, ADR
`2026_11_18_document_condition_judged_in_the_first_extraction_window`), or when its path dated it outside the period
(#2349, ADR `2026_11_21_document_periods_matched_against_path_dates_by_code`). #2348 asks the agent to select documents
by what ingestion stored.

## Decision Drivers

- *Never narrow on doubt*: a document that was not classified, or whose value is empty, must still be read.
- *Requests that name no type or value behave as before*: same selection, same judge input, same summary.
- *No type hard-coded in the agent*: a type added to the catalog reaches the agent without a change to it.
- *The user sees what the filter did*: how many documents it kept, left out, or could not tell, and which.
- *Deterministic*: code compares the stored values, not a model.

## Decision

- **The request reading names types and conditions; code compares them.** `ExtractionRequestPlainAnswer` gains
  `document_types` (values of `DocumentType`) and `attribute_conditions` (`DocumentAttributeCondition`: an attribute,
  then `contains` for text or `at_least`/`at_most` for dates and amounts). The prompt lists the types in scope with
  their counts and the attributes each carries, built from `DocumentTypeCatalog` (`SelectionFacets.document_types`). The
  output schema's enums come from the catalog's enums too, so a new type needs no agent change. A condition is brought
  into one form by `readable()`: dates as ISO days through `PathDateRange`, amounts through `AmountTextParser`. A
  condition no code can read is dropped, and the condition stays in `document_condition` in the user's words anyway, so
  the judge still sees it.
- **One filter per selection, applied after the period.** `KnowledgeDocumentSelection.metadata_filter`
  (`DocumentMetadataFilter`) is applied by `KnowledgeDocumentSelector` after `path_date_range`, to the union of the
  entries and before `limit` (`KnowledgeDocumentListing.with_metadata`). The result carries `DocumentMetadataCounts`
  (matched, excluded, unknown, and up to ten left-out paths within 2,000 serialized bytes), which ride on
  `ExtractionRun.metadata` into the table's summary, the sample's notices, and the "nothing selected" answer.
- **What each verdict means.** Every part of the filter must hold. One exclusion excludes the document. Otherwise, one
  unknown part leaves it unknown and kept.
  - A document without a type (not classified, or classified before the database switched it on) is unknown.
  - A type matches the primary type or one of the secondary labels.
  - An attribute the document's primary type does not carry excludes it. The catalog stores nothing there, so a filter
    on it could never match. Treating it as unknown would let every report and policy through a filter on the issuer's
    total.
  - An empty value on a type that carries the attribute is unknown.
  - Text matches when the value contains it, case ignored, any item of a list. A request names "Hooli" where the
    document says "Hooli AG", so equality would leave out nearly every match.
  - A stored date covers the whole span its precision states ("März 2025" is all of March). Stored dates and periods
    match when they overlap the range, as path dates do.
- **The request's period also applies to the document's own date, but only with a filter.** When the reading names a
  type or a condition, the period that dates the documents is matched against `document_date` as well. A type without
  that attribute, and a document without a date, are unknown here rather than excluded, because the period belongs to
  the request, not to the type. A period-only request is unchanged: it narrows by path alone, as ADR `2026_11_21` says.
- **The confirmed filter wins in both modes.** The reading happens before the request form in both modes, so whole-scope
  extraction takes the filter from `reading.selection`. After a discovery search, `SelectedExtraction.of` sets the
  confirmed filter on the model's selection, exactly as it sets the confirmed period. The form shows the filter under
  Document Condition, and dropping that part drops the filter with the period.

## Consequences

- A request naming a type or a value reads only matching documents and the unknown ones. The judge then decides the
  unknown ones from their first window (#2347).
- On a database that never classified its documents, every document is unknown and kept: the request reads as before,
  and the summary says so in its counts.
- A document classified wrongly is left out without a model ever seeing it. The summary names up to ten left-out paths
  and the count of all of them, so this stays visible. Accuracy beyond invoices has not been measured against the #2346
  targets yet.
- The Universal Agent's `extract_records` tool takes no filter. It still selects by path and text.
