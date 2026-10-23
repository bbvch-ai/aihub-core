# Table Extraction Across Knowledge Documents Ships as a Capability, Offered as a Tool and as a Blueprint

## Context

Issue #1888 asks for one table across many knowledge documents from one chat message, such as every hardware position on
a supplier's 2025 invoices, each row naming its file. Its building blocks were already merged: listing and reading
documents (#1948), exact and regex content search (#1024), record extraction with a schema decided at request time
(#1949, ADR `2026_10_02_runtime_record_schemas_for_structured_extraction`) and the tool loop (#1950, the tool-loop
amendment of ADR `2026_09_28_capabilities_and_the_conversational_spine`).

Two places want the result. The issue describes a dedicated agent with its own profile limits. The Universal Agent
(#1937) expects the document tools to join its loop "once delivered", and users of one general assistant should not need
a second profile to get a table.

Three properties make it harder than another tool:

- **The answer is the table.** A model in an answering loop reads tool results cut to `max_result_tokens` (4,000 by
  default) and would have to retype hundreds of rows it never saw whole, inventing or dropping some.
- **The work fans out.** Every document is one or more model calls; a run may extract twice, so the join must be per
  extraction, and one failing document must not stall or end it.
- **The broker's message limit is silent.** NATS rejects events over `max_payload` (1 MB in development) without an
  error the caller sees, so a run waits forever. Tables, rows and chat history each grow with the data.

## Decision Drivers

- *One implementation*: the blueprint and the Universal Agent must extract identically.
- *The profile bounds the run*: the configured collections, the asking user's access and the profile's path glob hold
  whatever the model or the user asks for.
- *Exact tables*: no model ever retypes the table.
- *Bounded events*: no event of a run may come near the broker's limit, whatever the documents hold.
- *No surprise for existing profiles*: a Universal profile saved before the tools existed keeps its tools.

## Decision

**Extraction is a capability, `RecordExtraction`.** `extract(selection, fields, collections, ...)` answers with
`RecordsExtractedEvent`: a plan step resolves the selection and designs the columns, one step per document extracts in
parallel, and an assemble step joins them. Every per-document event carries its extraction's id and file count, so the
join is triggered by each result and checks only its own extraction; a precondition on earlier results keeps it from
firing twice. A failing document answers with its failure. As a tool (`extract_records`), the same steps run, with
approval on every call by default because one model decision can start hundreds of model calls.

**Selections are described, then resolved by the platform.** The model writes a `KnowledgeDocumentSelection` (path
globs, a path regex, a content query or ids; AND within an entry, OR across), and core's `KnowledgeDocumentSelector`
resolves it with the profile's glob applied first and `max_files` as the cap. The blueprint's discovery loop runs in
gathering mode, which drops the model's closing text, so its last successful `select_knowledge_documents` call is the
hand-over; calls are ordered by the loop's iteration and position, since their events are created by parallel tasks.

**The table reaches the user without the model.** The blueprint streams it as its answer. In the Universal Agent the
result event itself is shown: the OpenWebUI pipe pins it as a block of the answer that a later tool call never folds
into a thought, and `ChatService` turns it into answer text for the OpenAI-compatible API and the bots. The model reads
the summary and the first rows.

**Every size is capped.** Cells have a character cap, per-document events and the table a byte cap below the broker's
limit, and tables are marked (`ExtractedTableMarkup`) so the API, the pipe and the agents replace earlier ones with a
line before they ride back on later events.

**Parallelism is bounded per agent replica**, with a profile-set cap and a semaphore per event loop, profile and cap.

**The Universal Agent's document tools are off by default**, switched on per profile; the shipped knowledge and data
templates switch them on.

## Consequences

- One capability serves both agents; RAG can adopt it once it runs a tool loop (#1568).
- A selection is resolved twice, once to show the model the count and once to extract. A content search that timed out,
  or documents that changed in between, can make the two differ; the summary says when the result was cut short.
- The parallelism cap is not global: N replicas extract N times as many documents at once, and model gateway cooldowns
  then hit every user of that model.
- An extraction running across a redeploy hangs, since JetStream acknowledges events before they are processed.
- Content-search globs are applied after the database's regex scan, so the database still reads documents outside the
  glob; none of them reaches the model, a result or the extraction.
- Clients that cannot answer an approval, such as the OpenAI-compatible API, need the extraction's approval set to
  *never* on the Universal Agent.

## Amendment 2026-10-21: no silent cuts

The product owner reviewed the first version and decided:

- **A selection larger than one answer is never cut.** The first version extracted the first `max_files` documents by
  path and noted the cut. Now the planner estimates the work from the documents' page counts; a selection that does not
  fit one answer (about five minutes, the profile's "minutes per answer", or more than "files per answer") is not
  extracted. The answer shows a sample from three documents, the count, how the documents break down by folder, year in
  the path and collection, and offers to narrow the request or to continue in parts. Above "most matching documents"
  (1000) only narrowing is offered.
- **Parts continue across turns.** The unfinished extraction is kept per conversation in the thread context
  (`PendingExtraction`: the ordered documents, the columns, the next part, rows not shown yet), not on events. The
  blueprint offers `continue_extraction` only while one is pending; the Universal Agent's `extract_records` takes
  `continue_pending`. Every part keeps the columns of the first; a new selection replaces the pending one. One run
  continues at most one part: after a continuing call, or after an extraction that left documents or rows for later (a
  sample of a too broad selection), a `continue_pending` call in the same run gets a tool result telling the model to
  leave the rest to the user. A model taking "yes, all of them" literally cannot run every part in one answer, nor run
  part 1 right after the sample before the user confirmed. A model may still narrow the selection on its own in the same
  run; the summary names what it chose.
- **Rows beyond one answer follow** on the next *continue* instead of being cut. A table answering a tool call is paged
  to what a chat client shows inline (100 rows and about 60,000 characters, below the OpenWebUI pipe's own cap, which
  exists because OpenWebUI re-renders the whole message on every streamed event), so the model's "the user sees the full
  table" stays true and the rest follows on *continue*. The blueprint's own answer keeps "rows in the table".
- **A part whose run died is extracted again.** A part is marked taken before it runs, so a repeated *continue* goes on
  with the next one, and finished once its table is assembled. After every part was taken, a *continue* runs a taken
  part that never finished; the totals count only extracted documents and say so when some are missing.
- **Discovery state stays below the broker's limit.** Every tool-loop event carries the loop's whole state. The
  extraction agent's loop does not keep the gathered results it never reads (`RunToolLoopEvent.hands_back_results`), and
  the tool loop condenses when its serialized state passes 600,000 bytes, not only when the prompt is full
  (`ToolLoopCondenser.oversized`). This applies to every tool loop; it triggers only where an event would otherwise be
  refused. Moving tables and rows out of events into storage remains the lasting fix (see byte caps below).
- **Borderline rows are kept and marked.** With row instructions, the extractor marks each record `yes` or `unsure`
  (`record_match`); unsure rows are kept, shown in a Match column and counted in the summary.
- **A search stopped at its limit selects by folder.** When the blueprint's discovery loop ends without a selection, the
  same model is asked once for the selection its searches point to (`SelectionFallback`). Its answer offers no document
  ids, so it cannot narrow the table to the documents its searches happened to show; after a search stopped at its limit
  it keeps only path conditions, and every other condition (an amount, a supplier) is checked in each document as a row
  condition. Real contracts showed why (2026-10-23): asked for liability caps below an amount, models searched for the
  amount until the limit, and a selection of the hits extracted 2 of 7 contracts. Reading every document of the folder
  costs more; a folder too large for one answer gets the sample and the offer to narrow, as any selection does.
- **Rows left for later carry their collections**, also when the extraction fitted one answer and only its rows did not,
  so a *continue* after access was revoked, or in another profile of the same conversation, ends the extraction instead
  of showing them.
- **Long documents are read in part**, see ADR `2026_10_21_partial_reads_of_long_documents_in_record_extraction`.
- **Templates that offer extraction set its approval to never** (Knowledge Assistant, Data Analyst): clients that cannot
  answer a confirmation stopped at it, and the size check now asks before a large extraction. Workplace Assistant keeps
  the document tools off: it is the everyday assistant, and fewer tools keep its tool choice reliable.
- **Byte caps are measured as events are serialized**, non-ASCII characters escaped to six bytes, so German text cannot
  push an event past the broker's limit; moving tables out of events into storage with a reference was considered and
  left for later (it would also serve stored results, the root ticket's phase 3).

Known limits of this amendment, until tables and rows move out of events into storage:

- A document's rows travel in one event (200 KB), so rows beyond it are left out of that document, named with their
  count in the summary rather than carried to the next answer.
- The unfinished extraction is one per conversation: two extractions in one answer that both leave rows for later keep
  only the second's. The one-part-per-answer guard is a read-then-write on the run context, so two continuing calls in
  the same round could both pass; neither has been seen in tests.
- Rows waiting for the next answer stay in the thread context, which has no expiry: up to about 20 MB for an abandoned
  conversation at the default limits.

Consequences: an answer may now end with a question to the user instead of a cut table, and a non-interactive caller (a
coordinating agent or a scheduled run, root phases 2 and 3) will need a mode that extracts all parts or none; the
pending state is per thread and is cleared by the last part or by a new selection.
