# Partial Reads of Long Documents in Record Extraction

## Context

Record extraction (#1888, ADR `2026_10_19_table_extraction_as_a_capability_tool_and_blueprint`) reads every selected
document in full, window by window, with the extraction model, because a record condition such as "hardware positions"
is semantic: a line saying "Laptop T14" is a hardware position without containing the word. Only a full read finds every
such line.

The first version failed a document longer than a profile limit (120,000 characters) as "too long", before reading any
of it. Every record in it was lost, and only the list of failed files said so (e2e case E19). The documents this hits
are the long ones: supplier contracts and SLAs, which the first customer setup extracts clauses and terms from
(aihub-core-private#263), next to invoices. That ticket describes the agent as extracting rows "from every matched
document's full text".

A full read of a long document costs latency more than money: windows used to run one after another, so a 200-page
contract took many minutes, and a whole answer is meant to finish within about five minutes.

## Decision Drivers

- *No silent loss.* A selected document must not turn into zero rows unannounced.
- *Bounded latency* per answer, about five minutes, with visible progress.
- *Honesty over completeness claims:* a result that may miss rows must say so where the rows are shown.
- *No model decides to skip text.* Deciding which text matters with the main model costs as much as reading it.

## Decision

- **Windows run side by side.** A document's windows are extracted concurrently, bounded per agent replica by the
  profile's "model calls at once". Each window is sent with the document's opening, never with an earlier window's
  output, so the records do not change; only adjacent windows' records are merged as overlap copies.
- **Full reads up to 500,000 characters** (the profile's "longest fully read document", a few hundred pages), which
  covers nearly every contract, SLA and invoice in full.
- **Above that, a partial read instead of a failure.** The extractor reads at most 12 windows: the opening window, then
  the windows where the wanted lines are most likely, ranked by matches of `row_terms` (words or a pattern the model
  supplies with its selection, such as `Hardware|Laptop|Monitor`), the rest spread evenly over the document.
- **The result says it is partial.** `DocumentExtractionResult.partial` is set; every row from such a document reads
  `file.pdf (partly read)` in the file column, and the summary lists the document under "Partly read (rows may be
  missing)". The number of parts read is logged, not shown.

Rejected:

- *Failing long documents*, as before: loses every record and only reports it afterwards.
- *Silently truncating* to a prefix, the default of some document-ETL tools: the missing end reads as complete.
- *Letting the main model choose documents or parts to skip*: it must read the text to decide, which costs what the
  extraction costs, and it has not seen documents it was not shown.
- *Vector search inside the document as the only part selection*: top-k retrieval caps the records it can find and
  cannot promise every line. In-document hybrid search (Milvus `document_id` filter with BM25) remains a candidate to
  add to the ranking, once its chunk text is mapped to window offsets reliably.

## Consequences

- AC4 of #1888 ("several matching lines become several rows") holds for fully read documents; for partly read ones it
  holds within the parts read, and the table and summary say which documents those are.
- This deviates from the root ticket's "every matched document's full text" for documents above 500,000 characters only;
  a profile can raise the limit to 2,000,000 characters at the cost of latency.
- `row_terms` that miss the wording of the wanted lines lower recall in partial reads; the even spread and the opening
  bound how much is missed, not whether.
- More model calls run at once per replica, still bounded by the profile; gateway cooldowns are shared by every user of
  the extraction model.
- Revisit when windows get cheaper, when per-section reading by document structure (headings, tables) is available, or
  when in-document search can select parts reliably.
