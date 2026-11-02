# Table Extraction Reads the Whole Scope, in One Answer, with Tables Stored by Reference

## Context

ADR `2026_10_19_table_extraction_as_a_capability_tool_and_blueprint` (amended 2026-10-21) let the Knowledge Extraction
Agent's model find the documents in a bounded search loop, extracted a selection too large for one answer in parts the
user continued one by one, and carried every row and table inside NATS events, held under the broker's payload limit (1
MB in development, 2 MB on VMs and k8s) by byte caps. Testing on synthetic and real documents (October 2026) showed:

- **The search decides completeness, and it is unreliable.** Models spent the search verifying conditions on the rows
  (liability caps below an amount) until the limit, so selections missed documents or never formed; one model
  substituted a file of the same name for one outside the path filter; one wrote its own judgement into the row
  condition. Whatever the search misses is missing from the table, and nothing tells the user. Ranking by meaning
  (#2200) shortened the search and raised its precision, but the hardest case still hit the limit in every run.
- **Parts and caps cut the result.** A document's rows beyond 200 KB were dropped (under 40 rows of full contract
  clauses); a tool call's table was paged at 100 rows; rows waiting for the next answer lived in thread state without
  expiry; earlier tables could not be opened again. Parts made a 150-document request a conversation of several turns.
- **The same bytes were copied** into the persisted event history, JetStream and Langfuse traces.

The customer setup behind #1888 (supplier contracts, SLAs, invoices; a human makes the final call) needs every matched
document's full text read and every row kept.

## Decision Drivers

- *Completeness over speed*: a missing row the user cannot see is worse than a slow answer.
- *Nothing cut silently*, and no limit the user only discovers by counting rows.
- *Events stay small whatever the documents hold*, so the broker limit can never lose an event.
- *One request, one answer*, with a confirmation only where the cost warrants it.

## Decision

1. **The whole scope by default.** Without the new profile setting `discovery` (off by default), one structured call
   reads the message into the columns, the row condition, the row terms and the places the user named (folders, files,
   years, as path globs or patterns), and every document in the profile's collections and path filter, narrowed only by
   those places, is extracted. A supplier, a party or a topic is a row condition, never a document filter. A named place
   that holds no document is reported with the scope's folders, never replaced by a similar document. A file path the
   user wrote out is such a place even when the model read it as a topic: it is matched as the end of a document's path,
   without a model. With `discovery` on, the search loop of the 2026-10-19 decision runs as before.
2. **One answer extracts everything.** Parts and *continue* are removed, with the settings `max_files`,
   `minutes_per_turn` and `max_rows`. The answer runs as long as the documents take; progress names each long document
   when it starts, each document when it finishes with its first rows, and a document still being read after a minute.
3. **A sample above 100 documents.** A selection of more than 100 documents (fixed, not a setting) first extracts five
   documents chosen as likely to hold wanted rows: ranked by meaning when the profile enables it, otherwise documents
   whose text contains the terms that identify them (a supplier) and the row terms, filled up by a spread over the
   largest folders. The answer states the columns, the row condition, the count and the estimated minutes; a "yes"
   extracts the stored selection with the sample's columns in one answer. The waiting selection is small (no rows), kept
   per conversation and profile, and taken in one atomic step, so two confirmations never extract it twice; any new
   request replaces it. Above `max_documents_total` only narrowing is offered.
4. **Tables and rows by reference** (#2220). Each document's rows are stored as JSON and the assembled table as a CSV
   file (UTF-8 with byte order mark; cells that a spreadsheet would run as a formula prefixed with `'`) in the
   `agent-files` bucket under `record-extraction/{extraction_id}/`. Events carry a reference and a preview of at most
   100 rows; cells are cut only in the preview. OpenWebUI attaches the CSV to the answer, the OpenAI-compatible API and
   bots end the answer with a presigned download link, and the admin event view offers a download through an endpoint
   that checks access to the thread. The bucket is created with the platform's buckets and keeps the existing 7-day
   expiry; a download after it says the file expired.
5. **Ranking by meaning orders, never filters.** `KnowledgeSemanticSearch.rank` (Milvus grouping search per document,
   within the path filter resolved to document ids, each database with its own embedding model, merged by reciprocal
   rank fusion) serves the search loop's `rank_knowledge_documents` tool and orders the whole-scope list and the sample.
   No document is left out because of its score.
6. **A condition on the whole document applies to every row in it.** The extraction prompt keeps a row that *may* meet
   the row condition, marked *unsure*, but a document that clearly fails a condition on the document as a whole (its
   supplier, party or year) gives no rows. Reading the whole scope makes the extraction model the only place where
   *"Acme's invoices"* excludes another supplier's invoice; without the rule it judged each line alone and kept other
   suppliers' hardware lines (precision 0.26 in the German invoice case, 0.95 with it).

## Consequences

- A table can no longer miss a document in scope for its wording; a request costs one extraction pass over the whole
  scope, so profiles should keep their path filter narrow. An answer over hundreds of documents takes many minutes.
- No event of an extraction carries more than a preview, whatever the documents hold; the per-document byte cap and the
  row overflow in thread state are gone.
- A run that dies mid-way (a redeploy, a Valkey timeout) loses the extraction; the user asks again. Surviving that is a
  follow-up.
- Stored files expire after 7 days, links in answers after 24 hours; the copy attached in OpenWebUI stays with the chat.
  Files are not removed when a thread is deleted (follow-up).
- A non-interactive caller (a coordinating agent or a scheduled run) is not asked for a sample confirmation by a person;
  it will need a mode that confirms or narrows on its own.
- Precision now rests on the extraction model. The rule of decision 6 brings most requests to 0.95–1.0, but a request
  for one supplier among many in the same folders can still keep a row of another supplier's document, and a document
  that only partly fits a document condition (a reseller's invoice naming the supplier) gives no rows; it is listed
  under "No rows from". Profiles used for exact, narrow requests over large mixed collections switch on `discovery`.
- Known limits, accepted for now: one confirmed request over many documents holds the profile's extraction slots on a
  replica until it ends, and there is no cancellation; every progress line makes OpenWebUI re-render the answer; a
  download link posted into a Teams or Slack channel works for every member of the channel for 24 hours; and the bot
  holds the storage key to sign those links.
- Rejected: keeping parts with storage by reference (still several turns for one table); a sample by folder spread (over
  a whole scope it mostly shows documents without wanted rows); semantic search as a pre-filter (it needs a calibrated
  score threshold per embedding model and would drop documents silently); a configurable sample threshold (it is about
  the user's patience, not the profile).
