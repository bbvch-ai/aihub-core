# Document Condition Judged in the First Extraction Window

## Context

The Document Tables agent (Knowledge Extraction Agent, ADR `2026_10_26_whole_scope_extraction_and_tables_by_reference`)
reads every document in scope and keeps the rows a condition asks for. A condition on the whole document ("only
contracts with Hooli", "signed versions only", "invoices from Q1 2026") used to travel inside the row condition
(`instructions`). The extraction model then judged it again on every window of every document (#2347):

- a document that clearly failed it was still read in full, window by window, and only its rows were dropped;
- the user could not tell a document that failed the condition from one that held no matching row: both were listed
  under "No rows from";
- on long documents the judgement was made on windows that do not show the supplier or the parties at all, so a window
  far from the header could keep or drop rows inconsistently with the rest of the document.

ADR `2026_10_21_partial_reads_of_long_documents_in_record_extraction` runs a document's windows side by side; any
judgement of the whole document has to fit that.

## Decision Drivers

- *No rows from documents that clearly fail* the condition, and every skipped document listed with its reason.
- *Unsure is kept, never silently dropped*: a document whose start does not settle the condition is read as before.
- *No extra model call per document* and no extra latency for documents that fit one window.
- *Requests without a document condition behave as before*, prompt and windows included.
- *Observable*: how often the judge says "no" or "unsure", and on what, must be measurable later.

## Decision

- **The condition is its own field.** The reading of a Document Tables request gains `document_condition`, asked back in
  the request form as its own part ("Document Condition"), and carried on `ExtractRecordsEvent` and on every document's
  run to `RecordExtractor.extract(document_condition=...)`. A value the rows carry themselves (a supplier per line of a
  statement) stays a row condition, and a period a location already expresses exactly (a year folder) is not repeated.
- **Judged inside the first window's structured output.** With a condition, window 0 is extracted with a records model
  whose first field is `document_match` (`verdict` "yes" / "no" / "unsure", `reason`), then `records`. On the
  strict-output path field order is generation order, so the model decides before it lists records. Window 0 is the
  whole document when it fits one window, which most invoices do.
- **Window 0 runs first and alone.** Only when its verdict is not "no" do the other chosen windows run side by side, as
  before, without the condition. A "no" makes the document `DocumentExtractionResult.skipped_by`: no records, even those
  the model listed, and its other windows are never read.
- **Only a stated contradiction gives "no".** The prompt asks for "no" only when the excerpt or title states a
  contradicting fact (another supplier, a date outside the period, "draft"); a fact that is not in the excerpt gives
  "unsure". An unsure document is read whole and every one of its rows is marked "unsure, please check".
- **A skip is not a failure.** `DocumentExtractedEvent.skipped_reason` and `RecordsExtractedEvent.skipped_count` sit
  next to `failure_reason` and `failed_count`; the progress names each skipped document with its reason, and the summary
  lists them in a block of their own, capped with "and N more".
- **Traced.** Each verdict and its reason are set on the span of `RecordExtractor.extract`
  (`extraction.document_condition.verdict`, `.reason`, `extraction.document.path`) and logged.

Rejected:

- *A separate judgement call on the document's opening*: one more call on every document, and the opening
  (`DOCUMENT_OPENING_TOKENS`, 512 tokens) is too short for parties or dates below a letterhead.
- *Keeping the condition in `instructions`*: every window keeps paying for documents that clearly fail, and a skip stays
  indistinguishable from an empty document.
- *Treating "unsure" as "no"*: loses documents whose supplier stands on page 2 or whose signature is on the last page.

## Consequences

- A long document with a condition waits for its first window before the others start: one window's extra latency, only
  for long documents and only when a condition is set. Without a condition nothing changes.
- While window 0 runs, a long document holds a `documents` slot without using all its `calls`; with many long documents,
  call slots may idle and throughput drops somewhat. No deadlock: `ExtractionSlots.calls` and `.documents` are separate
  FIFO semaphores.
- The judge is the extraction model in the same call, not an independent check. Its false-skip rate is unmeasured; the
  span attributes are there to sample verdicts and label them before tightening or loosening the rule.
- A document whose start passes but whose later pages contradict the condition is read whole; a later contradiction
  cannot stop it. Evidence-augmented or progressive judging is a follow-up, to be decided once the traces show how often
  window 0 is unsure.
- The Universal Agent's `extract_records` tool keeps document conditions in its row condition for now (follow-up issue).
- The request form has a fourth question; with discovery it has six, so `HumanInTheLoopQuestionsRequestEvent` allows up
  to six questions.
