# Choice Questions in the Chat, and Table Requests Confirmed Before They Are Extracted

## Context

ADR `2026_10_26_whole_scope_extraction_and_tables_by_reference` lets the Knowledge Extraction Agent (KEA, the **Document
Tables** template) read a request in one structured call and extract it at once from every document in scope. A part the
reading gets wrong, such as the place to read, the row condition, or a calculation (*"the sum of all invoices from
Acme"*) written into the columns, shows only in the finished table, after every document in scope has been read. With
discovery on, the search also set paths of its own; a model that combined the user's folder with a file the message
named selected nothing and reported the folder as empty.

The platform's human-in-the-loop (HITL) requests could not ask such a question well. An input request is a popup with
one text field, a confirmation request a yes/no, and a chat request shows its `question` as text, answered by the next
chat message. Only the chat type works in every client: the API's `ChatService` answers input and chat requests from the
next message but refuses confirmation requests, so the Universal Agent's yes/no approval of `extract_records` stopped
API and bot users, and the shipped templates set it to *never*. OpenWebUI 0.11.4 adds `request:user_input`, a dialog
that steps through choice questions, each with options and an optional free answer, and returns the answers by question
id. No other client has such a dialog.

Two settings decided how the KEA searched: `discovery` at the top level of its config, and `semantic_search` under
**Knowledge Documents**, which alone offered `rank_knowledge_documents` (#2200) and was in no other blueprint's form.
The ranking only orders documents, never leaves one out, and shortened the search in testing.

`ChatService` decided whether a thread had an open HITL by comparing the number of HITL request and response events. The
request count included each request's display copy (a request is persisted both as a control and as a display event), so
after the first HITL in a thread the counts no longer matched, and the next message was routed as the answer to a
request that had been answered already.

## Decision Drivers

- *Catch a misread request before it costs a pass over every document.*
- *Every client keeps working*: the OpenAI-compatible API, the Teams and Slack bots and the web chat must answer the
  same question without code of their own.
- *Say what the agent does not do* instead of doing it badly or silently.
- *Fewer settings an admin has to combine correctly.*
- *Routing an answer must not depend on how many copies of an event are stored.*

## Decision

1. **A chat HITL that carries structured questions.** Core adds `HumanInTheLoopQuestionsRequestEvent`, a subclass of
   `HumanInTheLoopChatRequestEvent` with one to five `HumanInTheLoopChoiceQuestion`s (id, header, question, one to three
   `HumanInTheLoopChoiceOption`s with the recommended one first, `allow_other`). Lengths are capped as OpenWebUI's
   dialog caps them. `question` still carries the whole form as text, and the answer is a chat response whose `response`
   is either the dialog's answers as JSON or the user's typed reply. A client without a dialog treats it as any chat
   request, so the API, the bots and the web chat need no change.
2. **OpenWebUI's `request:user_input` is the dialog.** For a chat request with questions, the OpenWebUI pipe opens the
   dialog through the event caller, without a timeout, lists the chosen answers in the message and sends them as JSON. A
   cancelled or failed dialog, or an OpenWebUI without the event, falls back to the text question.
3. **A table request is confirmed before it is extracted.** The KEA reads every new request once, in both modes, and
   asks it back: **Location** (with the scope's largest folders and their counts as a hint), **Filter Condition** and
   **Values to extract**, and with discovery also **Exact keyword(s)** and **Semantic keyword(s)**, which guide the
   search and never filter. Each part is pre-filled as understood; an option keeps it or chooses its alternative (all
   documents, every row, none), and a free answer corrects it. Typed, *yes* keeps the reading, *no* declines, and
   anything else is a correction read once more, with no second form. A *yes* to a waiting sample, a greeting and a
   question about the agent get no form. The confirmed reading is kept in the run context and decides what is read and
   extracted: without discovery, the scope at the confirmed places; with discovery, the search gets the confirmed parts,
   then the confirmed Location replaces any path it set, and the confirmed columns, row condition and row terms replace
   its own. In the Universal Agent, a new `extract_records` call is asked back the same way in three parts pre-filled
   from its arguments (no keywords, as the model has searched already). The form replaces the yes/no approval, whose
   default for `extract_records` becomes *never*. A written location is matched against the folders, files and years in
   scope; *no* returns "the user declined" to the model; any other reply, or a location naming nothing in scope, goes
   back to the model, whose next call in the run then runs unasked.
4. **Calculations are named, not done.** The reading separates a requested sum, average, count, maximum or comparison
   from the columns, which stay the value of each record. The KEA's form and the table say *"I don't calculate …"*, and
   the agent never answers with a number in text. The extraction model reads one document at a time, so a total is only
   as good as every row; the CSV file or an assistant that answers questions is where it belongs.
5. **Ranking by meaning is always on.** `semantic_search` is removed; `rank_knowledge_documents` is offered wherever the
   document tools are (the KEA's discovery mode, the Universal Agent), and both prompts say when to search by keyword
   (names, numbers, folders) and when to rank (a described kind of document). Without discovery, the sample above 100
   documents and the order of a whole-scope extraction are ranked by meaning, with the keyword scans as the fallback.
   The KEA's `discovery` moves to `knowledge_documents.discovery`, labelled **Discovery mode**. Stored values of the old
   fields are ignored.
6. **Open HITL requests are matched by id.** `PersistedAgentEventEntity.open_human_in_the_loop_requests_for_thread`
   returns the requests (control events only) whose `event_id` no response names as its `request_event`. `ChatService`
   and the API's open-chat-HITL check both use it.

## Consequences

- A misread request is visible before any document is read. Every new table costs one more turn: a dialog in OpenWebUI,
  a typed reply elsewhere. A correction is read once more without a second form, so a misread correction still shows
  only in the table.
- Non-interactive callers (a coordinating agent, a scheduled run) cannot answer the form, as they cannot answer the
  sample confirmation; a mode that confirms on its own remains a follow-up.
- The Universal Agent's extraction can now be confirmed from the API and the bots, which the yes/no approval could not.
  A profile that sets an explicit approval rule for **Extract a table** asks for both.
- The dialog depends on OpenWebUI 0.11.4. A long question is cut at 500 characters with an ellipsis, so the end of the
  Location hint, where the folder list stands, is what it loses.
- Breaking: a KEA profile that had the top-level `discovery` on reads every document again until **Discovery mode** is
  ticked; `semantic_search` values vanish without effect.
- Ranking on every large sample adds an embedding call and a grouped Milvus search per database; a ranking that fails,
  times out or places nothing falls back to the keyword scans, as before.
- A thread with several HITLs routes each message to the request it answers; the API's open-chat-HITL check and the chat
  path can no longer disagree.
- Rejected: a new HITL type beside the chat type (every client would need code for it); a form before every tool call of
  the Universal Agent (only extraction reads enough documents to warrant it); calculating in the agent (unreliable over
  many documents, and not what a table answers); keeping ranking optional (it only orders and never drops a document, so
  switching it off protected nothing).
