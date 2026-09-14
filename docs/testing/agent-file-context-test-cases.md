# Agent file context — test cases

Coverage for the change that stops Open WebUI inlining attachments into agent prompts and has agents read the vectors
the chat client already built. Fixes [aihub-core-private#147](https://github.com/bbvch-ai/aihub-core-private/issues/147).

Groups A and B run with `pytest` and need no stack. Groups C and D are end-to-end on the dev stack.

**Measurement rule for C and D:** read results from `aihub.agent_events` in FerretDB, never from the browser. Driving
`/api/chat/completions` with a fabricated `chat_id` makes Open WebUI raise inside its own event emitter
(`socket/main.py`, the `source`/`citation` branch dereferences a chat row that does not exist), which leaves the
response open. A run is finished when its events contain `RAGSuccessStopEvent`, `RAGFailureStopEvent`, `LLMStopEvent`
or `ExceptionEvent`.

Before running group A or B: **kill every `app/rag_agent/main.py` process first.** The suite starts real `RAGAgent`
runners on the NATS queue group `agent_runner_RAGAgent` and **leaks them — they outlive pytest**, so each run competes
with the previous run's orphans and with any agent you started by hand. The symptom is four or five failures that are a
*different* four or five each time, and live chats that stall at two events. Killed first, the suite is green: 646
passed, 3 skipped. Any failure that survives a kill-then-rerun is real; one that does not is this.

## A · Unit — provisioning, retriever, wiring

| # | Case | Asserts |
| --- | --- | --- |
| A.1 | Agent workspace model is provisioned with capabilities | `{web_search: false, file_context: false}` |
| A.2 | Plain LLM model carries no capabilities | stays `null` — structural guard for goal 1 |
| A.3 | Drift: missing capability back-filled, admin-set capability (vision) preserved | `_compute_model_diff` iterates desired keys generically |
| A.4 | `source_file_id` is optional, survives serialisation round-trip, rejects a non-UUID4 | `UserUploadedFile` |
| A.5 | Collection name matches Open WebUI's sanitisation | `-` → `_`, prefix `open_webui_file_` |
| A.6 | Collection does not exist yet → returns empty, does not raise | upload-then-ask-immediately is normal |
| A.7 | File without `source_file_id` is skipped | nothing to read |
| A.8 | 20 files → 20 searches, all issued | `asyncio.gather` fan-out |
| A.9 | A hit maps to a node with filename, document_id, namespace, score | `_to_ingested_node` |
| A.10 | No attachments → knowledge retrieval only, no retriever constructed | no behaviour change without files |
| A.11 | Agent with no configured retriever leaves uploads unread | rather than guessing an embedding model |
| A.12 | Embedding model is taken from the agent's first retriever | query and stored vectors must share a model |
| A.13 | Uploaded chunks lead the merged result | attachment enters the prompt ahead of the corpus |
| A.14 | An attachment that yielded no node is named to the user | `agent.thought.attachments_unreadable` |
| A.15 | A readable attachment produces no such message | no false alarms |
| A.16 | Knowledge retrieval still runs when no file is attached | regression guard |
| A.17 | Attachments are ordered against each other by score | one COSINE index, one model — unlike the knowledge merge these are comparable |
| A.18 | The file attached to this message leads on a marginally weaker score | `attached_in_current_turn`; "this document" is a reference no score carries |
| A.18b | Naming an earlier file beats the one just attached | `DECISIVELY_BETTER_MATCH` — the user resolved the reference themselves |
| A.19 | A turn that attaches nothing ranks purely on relevance | asking back about an earlier file must still reach it |
| A.20 | A hit with no distance sinks instead of leading | an absent score must not sort as better than everything |
| A.21 | `attached_in_current_turn` survives serialisation, defaults to false | `UserUploadedFile` |
| A.22 | The condenser is given the filenames of this message | so "this document" resolves to them instead of a file from the history |
| A.23 | Only this message's files are named, not the thread's | eleven carried names would say no more than the history already does |
| A.24 | A turn that attached nothing names nothing | the reference does belong to the history then — pre-existing behaviour |
| A.25 | All four locales render the condenser prompt, no `{` left | one template serves every condensing agent; a missing variable fails only at runtime, in that language |

## B · No side effects

| # | Case | Asserts |
| --- | --- | --- |
| B.1 | `packages/core` suite | 1881 passed; 9 failed + 16 errors are the Windows baseline (`time.tzset`, unseeded Keycloak, mem0 subprocess), identical before and after |
| B.2 | `packages/agent` suite | 646 passed, 3 skipped, 0 failed — after killing leaked runners |
| B.3 | Meta-question gate unchanged | `test_self_awareness_wiring.py` |
| B.4 | User and organization memory unchanged | `test_do_retrieve_memory.py` |
| B.5 | Non-RAG agents still import and keep their step count | LLMWrapping, FewShot, NamespaceSelection, Retrieval, Imap, EmailClassification |
| B.6 | `expert_rag_agent` suite | 4 passed — second call site of `do_retrieve` |
| B.7 | `make pr-ready` clean on every modified scope | format, lint, compose generation, license check |
| B.8 | Every agent that condenses, after the prompt change | 124 passed, 3 skipped — RAGAgent, ExpertRAGAgent, FewShotAgent, self-awareness |

## C · The five goals, end to end

| # | Goal | Case | Result |
| --- | --- | --- | --- |
| C.1 | 1 | Plain LLM + 1 file, 5 questions | 5/5 HTTP 200, every answer grounded in the file |
| C.2 | 1 | Plain LLM + a 44-chunk document, ask about a section at the very end | answers §6.1 and §2.3.3 — full context not truncated |
| C.3 | 2 | Agent, no file, question only the knowledge base answers | 11 nodes from the corpus, all five departments correct |
| C.4 | 3 | Agent + 1 file | quotes the chunk verbatim, guard reports sufficient, no escalation |
| C.5 | 3 | Agent + 2 files, question only the knowledge base answers | uploads contribute 21 of 33 nodes yet the answer comes only from the corpus |
| C.6 | 3 | Bridging question spanning file and knowledge base | one answer, both sources cited separately by name |
| C.7 | 4 | Turn 1 file A, turn 2 add file B, ask about B | cites B, never A — this is #147 |
| C.8 | 4 | Ask back about A while B is still attached | cites A, never B, though B contributes 16 of 33 nodes |
| C.9 | 5 | `RetrieverEvent` labels each chunk | `source`, `source_origin=user_upload`, `namespace`, `document_title` |
| C.10 | 5 | No `ExceptionEvent` in any scenario above | zero across every passing run |

C.5 through C.8 must run against a **populated** knowledge base. With an empty corpus the only competitor for the
targeted file is the other attachment, which is a weaker test.

## D · Scale and edges

| # | Case | Result |
| --- | --- | --- |
| D.1 | 20 files attached to one chat | 20 nodes from 20 distinct files, 94.5 s, zero exceptions |
| D.2 | 20 files, ask about the 17th | cites `Merkblatt 17`, `VHS-1017`, `34 Arbeitstage`; no bleed from the other 19 |
| D.3 | File uploaded but not yet indexed, attached beside a good file | skipped quietly, good file still answers, nothing invented |
| D.4 | Corrupt PDF that cannot be parsed | user sees `Could not read these attachments yet, answering without them: …` and the answer still lands |
| D.5 | Knowledge collection attached in the chat | warning names the collection instead of dropping it silently |
| D.6 | Agent with no retriever configured + an attachment | upload left unread, no error |
| D.7 | Ten-turn conversation with files interleaved | see below |

### D.7 in detail

Files enter at turns 1, 4 and 7 and stay attached. Ten turns, zero `ExceptionEvent`.

| turn | files | seconds | turn | files | seconds |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 20.0 | 6 | 2 | 27.6 |
| 2 | 1 | 21.9 | 7 | 3 | 29.2 |
| 3 | 1 | 18.3 | 8 | 3 | 26.0 |
| 4 | 2 | 29.8 | 9 | 3 | 23.8 |
| 5 | 2 | 29.4 | 10 | 3 | 30.0 |

No latency growth with conversation length. The single step is at turn 4, where the second file is attached — that is
the cost of one more vector search, not accumulation. Within a fixed file count the numbers are flat or fall.

No memory leak: agent RSS 349.5 MB → 186.3 MB, Valkey `steps:*` unchanged at 8 (per-run state is cleared at teardown),
`step_markers:*` 188 → 198. The markers grow by exactly one per completed run and are **meant** to outlive teardown, so
a redelivered terminal event is a no-op.

### D.7 #147 checkpoints

Run these as their own conversation with a real alternating history — user turn, assistant answer, user turn. Sending
only user messages makes the model treat the thread as a list of unanswered questions and summarise all of them, which
invalidates the check.

| turn | attached | asked about | must cite | must not cite | result |
| --- | --- | --- | --- | --- | --- |
| 1 | A | A | A | — | pass |
| 2 | A, B | B | B | A | pass |
| 3 | A, B, C | C | C | A, B | pass — C won from **1 of 34 nodes** |
| 4 | A, B, C | A | A | B, C | pass |

A = `bbv_AI_Guidelines.pdf` (5 chunks), B = `Spesenreglement_bbv.pdf` (44 chunks), C = `merkblatt_17_Elternzeit.md`
(1 chunk). Turn 3 is the strongest evidence: the newly attached file supplies 3% of the retrieved nodes and still owns
the answer.

## E · Ordering across a long thread

Open WebUI forwards **every** file of the conversation on every turn — `RAG_FILE_MAX_COUNT` guards one attach action,
not the thread — so a long chat reaches the agent with far more attachments than the cap suggests. These ran on the dev
stack against a real 11-file thread, driven through `/api/chat/completions` against a genuine persisted chat row, and
measured from the `RetrieverEvent` in `aihub.agent_events`.

| # | Case | Result |
| --- | --- | --- |
| E.1 | The flag survives pipe → API → agent | `UserMessageEvent.files` carries `attached_in_current_turn: true` on exactly the one file of that message, `false` on the other ten |
| E.2 | Nothing attached this turn, 11 carried files | uploads ordered purely by score, 0.519 → 0.368; knowledge nodes still follow them, unchanged |
| E.3 | Same question, one file attached this turn | that file leads from 5th place on score (0.415 against a top of 0.473), every other document keeps its relevance order |

E.2 and E.3 are the same question one after the other, so the attachment is the only variable.

### How a user refers to a file

Both ways of pointing at a document have to work, and they pull against each other — the second is why the
just-attached file leads on a tie rather than outright. `DECISIVELY_BETTER_MATCH` is the line between them, and the
numbers below are what it was set from.

| # | The user says | Attached this turn | Result |
| --- | --- | --- | --- |
| E.4 | "this document", naming nothing | one file | the attachment leads from 0.415 against a top of 0.473 — a question that singles out nothing leaves the field within a few hundredths, so the reference is the attachment |
| E.5 | names an earlier file (`Spesenreglement`) | a **different** file | the named file leads at 0.759 against a next-best 0.493, and the attachment drops to 9th on its own 0.410 — the user resolved the reference themselves |
| E.6 | names an earlier file | nothing | same as E.5 without the contest: relevance alone finds it |

E.5 is the regression guard for E.4. An unconditional "the attachment always leads" put a 0.410 file ahead of the
0.759 one the question named.

Two traps when driving this by hand. The API must be restarted after a change to `UserUploadedFile`, or its own
Pydantic model silently drops the new field and every file arrives `false`. And a synthetic assistant message may reach
the pipe without a `parentId`, which is why the current-turn lookup falls back to the newest user message.

### The condenser resolves the reference

`condense_standalone_question` used to resolve a demonstrative against the chat history alone, so "what is in this
doc?" condensed to a question naming a **different** file — `bbv_AI_Guidelines.pdf` in the original report and
`test_upload_file.pdf` in a re-run. Retrieval then embedded a query about the wrong document, which no ordering
downstream can recover. It is now given the filenames of this message.

| # | Case | Result |
| --- | --- | --- |
| E.7 | The original failing question, verbatim, on the same thread | condenses to `Knowledge_Library.pdf`, guard accepts, and that file is now the **top-scoring** upload at 0.578 — it no longer needs the tie-break at all |
| E.8 | Naming an earlier file while a different one is attached | condenser keeps the name the user wrote; `Spesenreglement` leads at 0.586, the attachment sits 7th on 0.376 |

E.7 is the payoff of the whole chain: with the query bound to the right document, relevance finds it on its own —
0.578 against the 0.415 the same file scored when the query was about another one.

One template serves every agent that condenses, in four locales, and `PromptTemplate.format` fails only at runtime
on a variable a locale forgot. A parametrised test renders all four and asserts no `{` survives.

## Before rollout

| # | Check | Why |
| --- | --- | --- |
| R.1 | `select count(*) from knowledge;` on the staging openwebui database | `0` is safe. Above `0` means someone uses Open WebUI Knowledge, which agents will not read |
| R.2 | Same query on production | same |
| R.3 | `select distinct f->>'type' from chat, jsonb_array_elements((chat::jsonb)->'files') f;` | only `file` is safe; `collection` needs handling first |
| R.4 | Add `file_context` and `web_search` to the Open WebUI upgrade checklist | both rely on v0.9.5 internals |
| R.5 | Re-measure before raising `RAG_FILE_MAX_COUNT` | the default stays 4; an admin can raise it at runtime, or clear it to unlimited. See the note below |

## Raising the attachment cap

`RAG_FILE_MAX_COUNT` defaults to 4. It is a `PersistentConfig`, so an admin can raise it at runtime from the
Open WebUI admin UI — or clear it, which removes the limit entirely. The cap is a **frontend guard only**: the
backend never enforces it, it is exposed through `/api/config` as `file.max_count`, and the bundle blocks the
attach. There is no per-model variant of it; the frontend reads one global value regardless of the selected
model.

So the question is not what the default should be, but whether both paths survive an admin raising it.

**Agents: yes, measured.** D.1 and D.2 ran with 20 attachments — 20 nodes from 20 distinct files, 94.5 s, zero
exceptions. Agents retrieve rather than inline, so the cost of another file is one more vector search.

**Plain LLM: yes at the sizes measured.** This path still inlines every attachment, so the concern was the
model's input limit. Measured against `text-generation/Apertus-70B-Instruct-2509`, which declares the smallest
`max_input_tokens` of any configured model (65,536):

| Probe | Prompt | Result |
| --- | --- | --- |
| Summarise a long repetitive document | ~106k tokens | HTTP 200 in 21.3 s, correct summary |
| Two unique markers, one at the very start and one at the very end | ~98k tokens | HTTP 200 in 16.5 s, **both** returned |

The second probe is the one that matters: repetitive filler cannot distinguish "read it all" from "silently
truncated and summarised the first part", and silent truncation is the dangerous failure — a confident answer
missing half its evidence. Both markers came back, so the prompt was processed end to end at roughly 1.5x the
declared limit.

Conclusion: `max_input_tokens` in LiteLLM's `model_info` is routing and cost metadata, **not an enforced
ceiling**. Do not treat it as one. If a future deployment needs a hard guarantee, measure the provider first —
these numbers are for this stack's providers at these sizes, and nothing was measured above ~106k tokens.
