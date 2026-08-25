# Agent IMAP Read Capability as Native `@step` Functions

## Context

Agents had no email capability. Issue [#1507](https://github.com/bbvch-ai/aihub-core/issues/1507) introduces the first
one: letting an agent connect to an IMAP inbox, list unread messages, and fetch a chosen message with its attachments.
This is the greenfield foundation two sibling stories build on (moving mail to folders, drafting replies) — both blocked
on this decision.

Three questions had to be settled before writing code:

1. **How should the capability be exposed?** The platform already has an external-tool integration path (`McpReactAgent`
   calling out to MCP servers) and human/bot escalation paths (HITL, BITL). Email reading could plausibly ride any of
   them.
2. **Where do the connection config and the result events live**, given `packages/core` is shared infrastructure and its
   guidance discourages agent-specific events?
3. **How are attachment bytes carried** through the Swiss AI Agent Protocol, whose events are persisted to the audit
   trail (FerretDB) and streamed to the frontend over WebSocket?

The relevant existing pieces: `McpClientConfig` (a `StepConfig` in `packages/core/mcp/`), the `ControlEvent` /
`DisplayEvent` / `ControlAndDisplayEvent` hierarchy, and `UserUploadedFile` — the platform's only file-into-agent
contract, which references files by `file_id` and derives the S3 location at runtime rather than carrying bytes.

## Decision Drivers

- **In-process, deterministic, auditable**\
  Reading mail is a pure workflow step with no human judgement and no external tool server. It should be a native,
  traceable `@step` — not an opaque MCP tool call and not a HITL/BITL pause.
- **Reuse by the sibling stories**\
  The connection config and result events must be shared, first-class protocol types that the move-mail and draft-reply
  stories extend without cross-package internal imports.
- **Events must stay small**\
  Every protocol event is persisted to the audit trail and serialized over WebSocket. Embedding raw attachment bytes
  (base64, +33%) would bloat both paths and risk NATS/FerretDB message-size limits.
- **Follow the one existing file convention**\
  `UserUploadedFile` already establishes reference-by-`file_id` with runtime-derived S3 location for IDOR-safety.
  Attachments should follow the same shape, not invent a bytes-in-event exception.
- **No new secret infrastructure for a first capability**\
  Mailbox credentials should reuse the established `Password` form-field-into-agent-config pattern (`McpClientConfig`'s
  `api_key`), not a bespoke secret store.

## Decision

**The capability is a set of native `@step`-usable functions**, not an MCP tool and not HITL/BITL.

- **Connection config**: `ImapClientConfig` (a `StepConfig`) lives in `packages/core/imap/`, mirroring
  `McpClientConfig`. Its `password` field is a `Password` form element; the value is stored at-rest in the agent config
  (MongoDB `agent_configs`), identical to how `McpClientConfig.api_key` is handled today.
- **Result events**: `UnreadMailListedEvent` and `MailFetchedEvent` live in `packages/core` (`events/agent/imap/`) as
  `ControlAndDisplayEvent`s — control, because steps consume them; display, so they render by name in the event
  timeline. They are protocol types deliberately placed in core for reuse by the sibling stories, the same way MCP's
  `ToolEvent` lives in core.
- **Attachments as S3 references**: `MailFetchedEvent` carries `MailAttachmentRef` (filename, content-type, `file_id`,
  size) — never raw bytes. The fetch step writes attachment bytes to the shared `agent-files` bucket under the agent's
  own path prefix and emits references, mirroring `UserUploadedFile`. This required **wiring an S3 client into the agent
  runtime for the first time** (`MailAttachmentStore`, using `S3StorageSettings` with the blocking put wrapped in a
  thread).
- **New dependency**: `imapclient` (BSD-3-Clause) for IMAP. It is synchronous, so its blocking calls are off-loaded with
  `asyncio.to_thread` (the same pattern the attachment store uses for S3). It parses server responses into structured
  dicts and raises on `NO`/`BAD` responses, so no hand-rolled protocol-line parsing or status-check shim is needed.
  MIME/attachment parsing uses the Python standard-library `email` module — no additional dependency. `aioimaplib` was
  the initial choice but is GPL-3.0, incompatible with the Apache-2.0 license of `packages/agent`, and was rejected on
  the license-check gate.
- **Read-only scope**: no SMTP, no sending — ever. Sending is explicitly out of scope for the whole email capability,
  not just this story. Read-only extends to the protocol level: listing and fetching use a read-only `SELECT`
  (`EXAMINE`) plus `BODY.PEEK[...]` so the `\Seen` flag is never set, and imapclient raises on a failed login or select
  rather than surfacing it as an empty inbox. (The move-mail sibling story, #1508, is the first capability to open the
  folder writable — it relocates a message via `MOVE` or `COPY` + `UID EXPUNGE`, but is still non-destructive at the
  mailbox level: it moves, never permanently deletes, and never sends.)
- **Bounded payloads**: three deployment-fixed caps (not user-configurable) keep a single hostile or oversized message
  from overloading the agent or exceeding NATS/FerretDB message-size limits. `ImapClientConfig.max_message_bytes`
  (default 50 MB) is the peak-memory bound: the raw RFC822 size is checked with a cheap `RFC822.SIZE` fetch *before* the
  body is downloaded, so an oversized message is refused instead of being pulled into memory. `max_body_bytes` (default
  1 MB) then truncates the decoded body carried in a fetch event, and `max_attachment_bytes` (default 10 MB) skips
  oversized attachments — both only trim what is kept *after* parsing.
- **Stable message identity**: messages are addressed by IMAP UID (`UID SEARCH` / `UID FETCH`), not sequence numbers —
  list and fetch run on separate connections (possibly separate servers), and sequence numbers shift when another client
  expunges mail in between.
- **Bounded listing**: `ImapClientConfig.max_messages` (default 50) caps how many unread summaries a single
  `UnreadMailListedEvent` carries, keeping the persisted/streamed event small even for overflowing inboxes.

A demonstrator agent (`playground/minimal_workflow/imap_workflow`) exercises the capability end to end
(`list_unread_step` → `fetch_mail_step` → stop) and hosts the BDD tests. It is **non-conversational**, like
`RetrievalAgent`: it is triggered by a dedicated `ReadMailStartEvent` (a `StartEvent` subclass) rather than
`UserMessageEvent`, so it stays out of the chat UI (`is_conversational` is `False`) and is configured via its form and
started programmatically. It has its own deployable entry point (`app/imap_agent/main.py`) so it can run as a real agent
process; a production email agent can graduate from the final sibling story.

## Consequences

### Positive

- The move-mail and draft-reply stories inherit a ready connection config, event pair, and attachment-reference model —
  no rework.
- Persisted and streamed events stay small; attachment size no longer threatens message-size limits, and the mail body
  is not scattered across the event store in duplicate.
- Attachment handling matches the platform's existing IDOR-safe file contract instead of introducing a bytes-in-event
  exception.
- Mail reading is fully traceable in the timeline like any other workflow step (OpenTelemetry + Langfuse), with no
  external tool server or human pause in the loop.

### Trade-offs

- **The agent runtime now depends on S3.** Agents previously touched only NATS, JetStream, Redis, Milvus, and MongoDB;
  reading mail attachments now also requires SeaweedFS/S3 reachability and credentials in agent deployments.
- **This deviates from the issue's literal wording** ("attachments (bytes + names)"). The reference-based transport was
  chosen over inline bytes for the reasons above and is flagged for reviewer sign-off.
- **Mailbox credentials are stored at-rest in the agent config**, like MCP `api_key`. A platform-wide secret-indirection
  mechanism (Key Vault / references) for agent configs remains a possible follow-up if the security posture needs to
  tighten.
- **`imapclient` is a new runtime dependency** in `packages/agent`, adding to the maintenance and supply-chain surface.
  It is BSD-3-Clause (permissive) and has no transitive runtime dependencies of its own.
- **Mail bodies are protocol payloads.** `MailFetchedEvent` carries only the plain-text `body_text` of arbitrary inbound
  mail into the audit trail (FerretDB) and to the frontend over WebSocket; Presidio only guards the LLM path. The HTML
  body is parsed but deliberately **not** surfaced on the event — it is kept in-process on `ParsedMessage` (`body_html`)
  as the parse result and never enters the persisted/streamed event or the generated SDK types, so a hostile sender's
  markup cannot reach a frontend that might render it as raw HTML (XSS). A future consumer that needs the HTML body must
  add it to the event explicitly and sanitize it server-side first.

## Draft-reply extension (#1509)

The third sibling story lets the agent **draft a reply** to the fetched message and save it for a human, building
directly on the read capability:

- **`APPEND`-only handoff, never send.** The reply is appended to the configured `drafts_folder` flagged `\Draft` via
  `ImapClient.append_draft`; there is **no SMTP path** and no HITL/BITL approval event. The draft sitting in the user's
  Drafts folder *is* the human handoff — a person reviews and sends it from their own mail client. `APPEND` targets the
  folder by name and needs no writable `SELECT`, so the existing connection is reused; it returns the `APPENDUID` when
  the server supports UIDPLUS, else `None`.
- **LLM-drafted body, deterministic envelope.** The reply *body* is generated by a platform LLM selected from the model
  list, steered by an optional `draft_prompt` (a `Textarea` pre-filled with an example prompt). `ReplyComposer` wraps
  that body with a deterministic envelope: `To` = original `Reply-To` else `From`, an idempotent `Re:` subject, and
  `In-Reply-To` / `References` built from the original RFC `Message-ID` so the draft threads correctly. This required
  carrying the RFC `Message-ID`/`References`/`Reply-To` headers on `MailFetchedEvent` (previously only the IMAP UID was
  exposed).
- **New protocol event.** `MailDraftCreatedEvent` (`ControlAndDisplayEvent`, in `packages/core`) records the drafts
  folder, `in_reply_to`, subject, recipient, and the assigned `draft_uid`; it is added to the API `DisplayEvents` union
  so it renders on the timeline.
- **Demonstrator wiring.** The chain is `list → fetch → move → draft → stop`. Drafting stays independent of moving:
  `move_mail_step` does not short-circuit to `StopEvent` when moving is disabled — it emits a no-op
  `MailMovedEvent(moved=False)` (the `moved` flag) purely to forward the run. The draft step consumes both
  `MailFetchedEvent` (identity) and `MailMovedEvent` (ordering) and returns `StopEvent` when drafting is disabled.
- **Untrusted mail into the LLM.** Inbound mail body is attacker-controlled and enters the LLM prompt; the platform's
  Presidio guard covers the LLM path. No new dependency and no frontend change — `Textarea`/`ModelSelect` already render
  via the form-duality FormKit renderer.

## Draft reads from the Move folder + grouped draft settings

A follow-up refined *where* the draft is read from and *how* the draft settings are presented, without changing the
protocol events:

- **Draft reads strictly from the Move step's folder, not the inbox copy.** The draft step no longer drafts from the
  message fetched out of the inbox, and there is **no configurable source folder and no inbox fallback**. It re-reads
  the message from `imap.processed_folder` — the folder the move step files into — re-locating it by its RFC
  `Message-ID` (IMAP UIDs are folder-specific, but the `Message-ID` is stable across the move). Implemented with
  `ImapClient.find_message_uid(folder, message_id)` (an IMAP `SEARCH HEADER Message-ID`) plus a folder-aware
  `fetch_message(uid, folder=…)`. If the message is **not** in the processed folder — e.g. moving is disabled, so
  nothing was relocated — the step stops with a thought and drafts nothing. Consequence: **drafting is only meaningful
  when moving is enabled**; the draft sequences after the move (consuming `MailMovedEvent` for ordering) and sources
  from the move's target. This deliberately removes the earlier move-off duplicate-draft path (with no move to relocate
  the mail and reading capped by `UNSEEN`, re-triggering used to re-draft the same inbox message every run). An earlier
  iteration used a user-configurable `source_folder` (default `INBOX`) with an inbox fallback and kept the steps fully
  independent; that was superseded by this decision.
- **`DraftEmailSettings` config group.** Because a form `Group` is also a data group (its name is a key in the submitted
  config), grouping the draft settings under one **"Draft email settings"** section required nesting them structurally.
  A new `DraftEmailSettings` (`StepConfig`, in `packages/core/imap/`) holds `enable_draft`, `drafts_folder`, the LLM
  `model_name` (`ModelSelect`), and `draft_prompt`; `enable_draft`/`drafts_folder` moved out of the shared
  `ImapClientConfig`, and `llm`/`draft_prompt` moved off `ImapAgentConfig`. The drafting LLM is rebuilt from the
  selected model via a `DraftEmailSettings.llm` property (`LLMConfig(model_name=…)`), so the chat-LLM **default
  parameters (temperature, timeout, …) are no longer exposed in the form** — the form shows only the model picker. This
  is a breaking config-shape change (no compatibility shim); existing IMAP agent profiles must be recreated.

## Independent batch drafting (own start event + flag-based dedup)

A further iteration made drafting a **fully independent capability** rather than a tail of the read/move run, because
drafting is scheduled separately and must be able to work through mail that accumulated in a folder over earlier runs:

- **Own start event, same agent.** Drafting is triggered by a new `DraftMailStartEvent` (a `StartEvent` on the same
  `ImapAgent`), so the platform exposes a second trigger endpoint automatically. The read/move chain no longer drafts —
  it ends at a `finish_after_move_step`. Both start events are fired by an external scheduler (out of scope).
- **Batch, read from a configurable source folder.** `draft_batch_step` lists up to `DraftEmailSettings.batch_size`
  (default 5, configurable) messages from `DraftEmailSettings.source_folder` (default `INBOX`; point it at the processed
  folder for the accumulate-then-draft flow) and drafts a reply for each. A **single looping step** is used rather than
  event fan-out because the engine's fan-out join (`FixedList(T, N)`) needs a compile-time constant, unusable for a
  runtime-variable candidate count.
- **Flag-based idempotency, source stays unread.** Re-drafting is prevented by a dedup flag on the source message, not
  by `\Seen`: a custom IMAP keyword `$AiHubDrafted` is preferred (detected via `PERMANENTFLAGS \*`), falling back to
  `\Answered` where custom keywords are unsupported. The drafter lists `UNKEYWORD $AiHubDrafted` (or `UNANSWERED`), and
  after appending each draft marks the source with the flag. All reads use `BODY.PEEK` and the flag `STORE` never sets
  `\Seen`, so the source mail stays unread. This removes the previous "no move ⇒ re-draft every run" footgun without
  relying on the move step.
- **At-least-once ordering.** The draft is appended to Drafts **before** the source is flagged, so a crash in between
  re-drafts that one message next run (a recoverable duplicate) rather than dropping the reply.
- **New batch event.** `MailBatchDraftedEvent` (`ControlAndDisplayEvent`, in `packages/core`) summarises a run:
  `source_folder`, `count`, and `drafted: list[DraftedReplyRef]`. It is added to the API `DisplayEvents` union and
  renders on the timeline via the generic display fallback (no bespoke frontend component — matching the other mail
  events). `ReplyComposer` gained `compose_from_parsed` so the batch drafter can build the threaded envelope from a
  freshly-fetched `ParsedMessage` instead of a `MailFetchedEvent`. This supersedes the move-follower single-draft step
  and its per-draft `MailDraftCreatedEvent` in the workflow.

## Oldest-first candidate ordering (#118)

Neither chain ordered its candidates: both list methods ran an IMAP `SEARCH` and truncated the result (`uids[:limit]`)
with no sort key anywhere. RFC 3501 does not guarantee `SEARCH` result order, and the de-facto UID order is *arrival
into that folder* — so in the accumulate-then-draft flow, where `source_folder` points at the processed folder, a moved
message carries a fresh higher UID and the effective order is **move order**. Combined with truncate-before-sort,
`batch_size` picked an arbitrary slice rather than the head of the backlog.

- **Sort key is the sent date, with an `INTERNALDATE` fallback.** Not `INTERNALDATE` alone: a moved message gets a fresh
  one, which is the cause above. Ties break on UID so the order is total.

- **Server-side `SORT` when advertised, client-side otherwise.** `SORT` (RFC 5256) is an extension rather than part of
  IMAP4rev1 — Dovecot offers it, Gmail does not — so the path is chosen at runtime from `has_capability(b"SORT")` rather
  than assumed. The fallback issues one batched `FETCH (INTERNALDATE ENVELOPE)` over the matched UIDs and sorts in the
  client. The criterion is `DATE` and deliberately **not `ARRIVAL`**: RFC 5256 defines `SORT DATE` as the sent date
  falling back to `INTERNALDATE`, which is exactly what the client-side branch computes, so the two paths agree.
  `ARRIVAL` ignores the sent date and would disagree on precisely the moved-mail case.

  That agreement holds only for servers implementing the fallback. GreenMail advertises `SORT` but sorts mail with no
  parseable `Date:` header *last* instead of falling back to `INTERNALDATE`, so on such a server the ordering of
  Date-less mail differs between the two paths. Not worked around: real mail carries a `Date:` header, the client-side
  branch is the RFC-conforming one, and compensating for a server-side deviation would mean re-dating every candidate,
  discarding the entire benefit of the `SORT` path.

- **Sorting happens before truncation**, so the limit takes the oldest N rather than reordering an arbitrary N.

- **Flag semantics are untouched.** Both list methods already ran inside a read-only `SELECT` (`EXAMINE`), and the new
  helpers add no `SELECT` of their own; `ENVELOPE`, `INTERNALDATE` and `SORT` cannot implicitly set `\Seen` (RFC 3501
  §6.4.5 limits that to `RFC822`, `RFC822.TEXT` and non-peek `BODY[<section>]`). The search criteria are unchanged —
  drafting candidacy is still "not carrying the dedup flag", never `UNSEEN`, per the section above.

- **The ids must stay UIDs.** `imapclient` issues `UID SORT` because the connection is built with the default
  `use_uid=True`; the returned ids flow into `mark_drafted`, so a `use_uid=False` connection would flag the wrong
  message while replying to another. Do not override it in `ImapClientFactory`.

- **Summary fetches are batched.** The per-UID header fetch became a single `FETCH` over all selected UIDs, iterated in
  the sorted order rather than in server response order — a 50-message listing drops from 50 round trips to 2.

- **The fallback path is bounded to the 1000 oldest arrivals.** The client-side ordering fetch grows with the number of
  matches rather than with `limit`, because which message is oldest cannot be known without dating every candidate. Left
  unbounded that is not merely slow but a hard failure: `imapclient` comma-joins every UID into one command line without
  collapsing ranges, and servers cap command length — Dovecot's default 64 KB is roughly 9000 UIDs. So the candidate set
  is capped at `_MAX_ORDERING_CANDIDATES` (1000), and the window is the **lowest UIDs**, taken by sorting rather than by
  slicing the `SEARCH` response, since RFC 3501 does not guarantee that response's order. Only `ENVELOPE` and
  `INTERNALDATE` are fetched, never bodies.

  The window trades exactness on one shape of folder. UID order is arrival order, only a proxy for sent order — and in a
  processed folder it is *move* order. So with more than 1000 candidates there, the true oldest can fall outside the
  window and be missed; below 1000 the result is exact. The proxy holds for an inbox, where the oldest-sent mail is all
  but certainly among the oldest-arrived. A `SINCE` window was rejected as the bound instead: it discards mail by age,
  which is precisely the mail this change exists to surface. The dedup flag limits the cost further —
  `UNKEYWORD $AiHubDrafted` matches only never-drafted mail, so the worst case is a first run over a large existing
  archive.

  The server-side path is deliberately **not** capped: `SORT` returns bare integers the server has already ordered, so
  `limit` alone bounds it and a window could only discard correct ordering. Returning part of a `SORT` would anyway
  require RFC 5267 `CONTEXT=SEARCH`/`PARTIAL`, which neither Gmail nor GreenMail advertises.

- **Expunge races skip rather than fail.** A UID can be expunged by another client between the `SEARCH` and either
  `FETCH`. Batching raises the stakes — one vanished message would fail the entire listing, whereas the old per-UID loop
  failed only that message — so a UID missing from the ordering fetch sorts last and one missing from the summary fetch
  is skipped. This is not error suppression: a message that no longer exists is not a listing candidate.

## Archiving the original message (#1575)

Only attachments were persisted; the message they arrived in was parsed, summarised onto `MailFetchedEvent`, and then
lost. Issue [#1575](https://github.com/bbvch-ai/aihub-core/issues/1575) requires the original mail itself to be kept
"for future reference and processing".

- **The raw RFC822 bytes are archived, not a projection of the parsed fields.** A JSON envelope of what
  `MailFetchedEvent` carries would preserve only what we happened to model, which fails the story's own criterion that
  the stored mail "preserves all original content". The raw bytes *are* the original by definition, so they also carry
  what the event deliberately omits — the **recipients**, which `MailParser` never extracted at all (`To`/`Cc` appear
  nowhere in the parsed model), and the HTML body kept off the event for XSS reasons.

- **It costs no extra IMAP round-trip.** `fetch_message` already downloads the whole message with `BODY.PEEK[]` and
  threw the bytes away after handing them to `email.message_from_bytes`. `ParsedMessage.raw` keeps what was already in
  memory, alongside `body_html` and under the same rule: it never enters an event. Peak memory is unchanged and still
  bounded by the pre-download `RFC822.SIZE` check against `max_message_bytes`.

- **`max_body_bytes` must not reach the archive.** That cap exists to bound what an event may carry. Applying it to the
  stored copy would make the "original" a silently truncated one, so the raw bytes bypass every truncation the parser
  applies — pinned by a test.

- **The archive is deliberately NOT sanitized, and must not become so.** Sanitizing the HTML before storing was
  considered and rejected: it invalidates any DKIM/S-MIME signature, so the archived mail could no longer be shown to be
  authentic; and it destroys precisely the markup an email **classifier** needs — link structure (display text vs real
  `href`), tracking pixels and obfuscated markup are the phishing signals, and stripping them is irreversible. XSS is an
  output-encoding problem, and nothing renders these objects today. The obligation is therefore deferred to the
  consumer: **anything that renders HTML out of an archived `.eml` must sanitize at render time.** As a transport-level
  guard the object is written with `ContentType: message/rfc822` and `ContentDisposition: attachment`, so a browser
  handed the signed URL downloads it instead of rendering it. Whoever later finds unsanitized markup in the data lake
  should not "fix" it at the storage layer.

- **Attachments are stored twice.** Once inline inside the archived `.eml`, once as their own objects. Accepted so the
  existing attachment contract (and its `MailAttachmentRef` consumers) stays unchanged; the cost is roughly the base64
  inflation of the attachment bytes per message.

- **Only the read chain archives, and the fetch signature enforces it.** `fetch_mail_step` stores; `draft_batch_step`
  does not, even though it also calls `fetch_message`. Archiving there would re-store what the read chain already kept,
  once per message per batch run. The raw bytes are therefore retained only under `fetch_message(with_raw=True)`, which
  only `fetch_mail_step` passes. Without that gate the drafting chain would hold the raw bytes of a whole batch alive
  across its per-message LLM calls — up to `batch_size` × `max_message_bytes` of data it never reads. `parse_message`
  takes `raw` with no default for the same reason: a caller that does not archive says so explicitly rather than
  dropping the original by omission.

- **`MailAttachmentStore` became `MailStore`** (`store_attachments` + `store_message`) — it no longer stores only
  attachments. Breaking rename with no compatibility shim, per the repository convention.

- **`MailFetchedEvent.original_message`** is a nullable `MailMessageRef` (mirroring `MailAttachmentRef`, resolving its
  S3 location through `UserUploadedFile` so all file contracts share one layout). Nullable because a message parsed
  without raw bytes has nothing to archive, and a missing archive must not fail the run. No `DisplayEvents` union change
  is needed — a new field on an event already in the union does not re-tag it.

- **Retrieval needs no new endpoint.** `resolve_s3_location` yields the bucket and key, and the existing
  `GET /files/logged-in/url/{container}/{file_path:path}` issues the signed URL — the same path attachments already use.

- **Retention is unresolved.** The archive now holds complete inbound mail, headers and all, in the `agent-files`
  bucket, which carries no lifecycle policy. That is a deliberate acceptance for this story, not an oversight, and a
  data-protection follow-up if the posture needs to tighten — the same open question the at-rest mailbox secrets raise.

## Verify-or-create target folders (#1636)

The move step originally required its target folder to already exist, which holds for a single fixed processed-folder an
admin creates once by hand but not for classification, which files into one folder per category plus a fallback. Filing
now creates the folder when it is missing:

- **Creation, not just resolution.** `move_message` resolves through `_resolve_or_create_folder` instead of the
  special-use-aware `_resolve_folder` that `append_draft` still uses. Drafts must never create: their fallback is the
  server's `\Drafts` SPECIAL-USE folder, and inventing a second drafts folder would split the human handoff.
- **This widens the mailbox mutation surface.** The move story characterised itself as non-destructive — moves, never
  deletes, never sends. Folder creation keeps that property (it is additive and nothing is removed) but it is the first
  capability that changes mailbox *structure* rather than the location of one message, which is why the effect is
  recorded in the protocol rather than only in logs: `MailMovedEvent.folder_created` puts "the agent added a folder to
  this mailbox" in the audit trail, and the step emits a matching thought.
- **Per-level creation.** Each level of the hierarchy is created in turn (`Invoices`, then `Invoices/2026`), using the
  delimiter the server reports in its own `LIST` response, because RFC 3501 only *recommends* that a server create
  superior names. A `NIL` delimiter (flat namespace) creates the full name in one call.
- **The follow-up `LIST` is the only authority on success.** A `create` that fails because a parent already exists and
  one refused outright are indistinguishable at the protocol level, and a concurrent run may legitimately have won the
  race, so creation errors are not raised where they occur — the folder is looked up again afterwards and only its
  continued absence raises, carrying the server's reason.
- **Ordering is what protects the message.** Resolution and creation run before the inbox is selected writable and
  before any `MOVE`/`COPY`/`EXPUNGE`, so a server that refuses the folder fails the step with the message untouched in
  the inbox rather than half-filed. A test asserts `select_folder` is never reached on that path.
- **New folders are subscribed.** Creation is followed by a best-effort `SUBSCRIBE`: most mail clients only show
  subscribed folders, so an unsubscribed target would make correctly-filed mail look lost to the human who has to read
  it. A server that refuses to subscribe does not fail the move.
- **Unconditional, no new config.** Creation applies to every agent using the move capability rather than sitting behind
  a toggle — a per-category classifier cannot enumerate its folders in advance, so a disabled-by-default switch would
  only reintroduce the same first-run failure.

## Classification into per-category folders (#1637)

The customer use case is a mailbox that triages itself: read unread mail, classify each message, file it into the folder
for its category. `ImapAgent` cannot do this — it is a demonstrator that fetches only the *first* unread message and
moves it into one fixed processed-folder with no description attached. A new `EmailClassificationAgent` blueprint does
the whole batch and routes per category.

- **A separate blueprint, not a third chain on `ImapAgent`.** Two mailbox chains on one agent would both emit
  `UnreadMailListedEvent`, and the dispatcher routes an event to *every* step waiting on it, so the chains would
  cross-trigger; both would also consume unread INBOX mail, so on one profile whichever ran first would steal the
  other's work. `ImapAgent` is unchanged in behaviour and stays as the demonstrator and the fallback for testing.

- **The orchestration glue is shared, not copied.** `list`, `fetch-and-archive` and `file` moved into
  `agent/imap/step_functions.py` as `do_*` free functions, following `rag/step_functions.py` and
  `self_awareness_step_functions.py`; both blueprints are now thin `@step` wrappers over them. This is what keeps
  #1575's archiving in *one* place: copy-pasting the fetch body would have left two archives to maintain, and the read
  chain that owns archiving today stops running the moment classification takes over the mailbox.

- **Categories are configuration, not a taxonomy in code.** A `MailCategory` repeater (`category`, `imap_folder`,
  `description`) plus a fallback folder. The description is load-bearing: a model cannot reliably choose between
  `information_request` and `support_request` from folder names, but it can from "we can resolve this by providing
  information" versus "this requires an action from our team". A customer adds or renames a category without a
  deployment.

- **The model returns an index, never a folder name.** The response schema is built at runtime from the configured list
  with `ge=0, lt=len(categories)`, so the index cannot address a category that does not exist. This is the containment
  boundary for prompt injection: inbound mail is attacker-controlled and enters the prompt, but the worst a hostile
  message can achieve is misfiling into a folder the admin already configured — it cannot invent a destination or reach
  any other capability.

- **One route to the fallback folder: the model declining.** An explicit `selected_index: null` ("none of these fit") is
  the only way a message reaches the fallback folder. Mail is never forced into a bucket.

  The first implementation also had the model rate its own confidence and diverted anything below a configurable
  threshold. That was removed after measuring it. `confidence` was never an API signal — it is a field we invented in
  our own response schema, so the model writes the number as output tokens in the same forward pass that produces the
  answer. Across all five chat models on the gateway, given a deliberately ambiguous message, the explicit decline fired
  four times out of five and the threshold fired zero times; the one model that misfiled did so at **0.95**, which no
  usable threshold would catch. A knob that never fires but must still be tuned is worse than no knob. The field was
  dropped from the response schema and from `MailClassificationRef` as well as from the settings — keeping a number
  nothing acts on invites a later reader to trust it. `reason` is retained and is the better audit trail.

  If a real confidence signal is ever wanted, token **logprobs** are the measured one, and `LLMParameter` already plumbs
  them. They are not reachable from this code path today: `astructured_predict` returns only the validated model and
  discards the raw response.

- **Filing is the deduplication mechanism.** Every message — categorised or fallback — leaves the inbox, so the next
  `UNSEEN` listing cannot see it. Unlike drafting, no `$AiHubDrafted`-style flag is needed. A batch that fails half-way
  is therefore safe: filed messages stay filed, the rest are still unread and get picked up next run. IMAP UIDs are
  stable, so filing one message never shifts another's.

  Two limits on that guarantee, both deliberate:

  **A target folder equal to the inbox would defeat it entirely**, so it is rejected at validation. Filing into the
  inbox is not a no-op: on the `COPY` + `UID EXPUNGE` path the original is expunged and a fresh *unread* copy takes its
  place, so the next run classifies the copy, archives it again and never terminates. Folder names are admin-entered
  free text, so a typo reaches this. `fallback_folder` is checked the same way, as is the weaker case of a fallback
  folder that duplicates a category folder (which would make `per_category` and `fallback_count` indistinguishable).

  **Dedup only starts once filing does.** Fetch-and-archive runs for the whole batch before the first message moves, so
  a message that fails classification — an unparseable body, a context-window overflow — aborts the run with nothing
  filed, and the next run re-fetches and re-archives the entire batch to S3. Since listing is oldest-first, the same
  message leads every attempt, so a single bad message wedges the mailbox and grows the archive on every run. This
  compounds the unresolved retention gap below.

  Per-message isolation was considered and rejected. Routing a message whose classification *failed* into
  `fallback_folder` would unwedge the mailbox, but it converts a loud failure into a quiet one: with the LLM gateway
  down, every message in the batch would be filed as "uncategorised" and the run would report success, scattering mail
  on a transient outage. Failing the run keeps the mailbox untouched and the cause visible, which for a mailbox nobody
  is watching is the safer default. Revisit if wedging is observed in practice; the fix then is to isolate only
  *per-message* errors (parse, context length) and keep failing fast on infrastructure errors.

- **One looping step, three phases, two connections.** Fan-out was not usable — the engine's fixed-size join needs a
  compile-time constant and the message count is only known at runtime, the same constraint `draft_batch_step` hit. The
  IMAP connection is opened to fetch, **closed** for the model calls, and reopened to file, because many servers drop a
  socket left idle across a slow batch of LLM round-trips.

- **Archiving was pulled in ahead of its own ticket.** #1637 lists it out of scope, deferring to #1575 — but #1575 is
  merged and lives in the read chain that classification displaces. Leaving it out would have silently un-shipped a
  closed story for the agent that actually reads production mail. `do_fetch_and_archive` already retains the raw bytes
  under `with_raw=True`, so the archiving itself was free — the retention it implies was not; see below.

- **Fetch, archive and strip run per message, not per batch.** The first implementation fetched every message into a
  list before archiving any of them, and left `raw` and the decoded attachment bytes on the `ParsedMessage` that
  `FetchedMail` carries. That reproduced, in the classification chain, precisely the exposure the `with_raw` gate was
  introduced to prevent in the drafting chain: the whole batch's raw bytes held alive across every per-message LLM
  round-trip. `max_message_bytes` bounds one message, so the effective ceiling became `max_messages` ×
  `max_message_bytes` — 2.5 GB at the defaults — for fields nothing downstream reads once the S3 references exist. Each
  message is now archived and stripped before the next is fetched, putting peak memory back at one message.

  This keeps the connection open across the S3 writes, which the two-connection split above otherwise avoids. That split
  exists to keep the socket off the *caller's* LLM round-trips, which it still does; in-cluster `put_object` calls are
  orders of magnitude below the idle timeout RFC 3501 obliges servers to allow. The accepted cost is that a fetch
  failure part-way through a batch now leaves the already-archived messages in S3 with no event referencing them, which
  the unresolved retention question above already has to cover.

- **The expunge-race skip extends to the batch fetch.** The listing skips a vanished UID; the batch fetch did not, so
  one message expunged between the two failed the entire run. The shipped *Shared Mailbox Triage* template makes that
  routine rather than exotic — a human filing mail by hand in the mailbox being triaged is the normal case. Skipping is
  opt-in (`do_fetch_and_archive(skip_vanished=True)`) because `ImapAgent` fetches exactly one message and must still
  fail: it has no batch to salvage, and its step has to return a `MailFetchedEvent`.

  The skip is narrow by construction. `fetch_message` raised one `ValueError` for both a vanished UID and a message over
  `max_message_bytes`; catching that broadly would have made an oversized message a silent no-op, unread and unreported
  on every subsequent run. `MessageVanishedError` (a `ValueError` subclass, so existing handling is unaffected)
  separates the race from the refusal.

  Filing deliberately does **not** skip. `_file_all` builds one `MailClassificationRef` per message regardless of
  whether the move succeeded, so skipping a vanished UID there would emit an audit record asserting a message was filed
  when it was not. Failing keeps the record honest, and sequential filing already means the messages moved so far stay
  moved.

- **A single batch event, not one per message.** `MailBatchClassifiedEvent` carries `count`, `per_category`,
  `fallback_count` and the per-message `MailClassificationRef`s, matching the `MailBatchDraftedEvent` precedent. Each
  ref records the model's stated reason, so a misfile is explainable after the fact.

- **Filing is batched: one connection and one folder check per run.** The first implementation filed message by message
  through `do_file_message`, which opens its own connection and runs a full folder `LIST` inside `move_message`. A
  fifty-message batch therefore cost fifty-two connections and fifty-plus `LIST` commands. That was initially accepted
  as a bounded inefficiency, which under-read it: servers that cap concurrent or per-interval connections (Gmail among
  them) refuse the extra connections rather than merely slow them down, making it a correctness problem.

  `ImapClient` now splits into `ensure_folders(folders)` — one `LIST`, create the missing hierarchies, one verifying
  `LIST`, subscribe what it made — and `relocate_message`, the move with resolution already done. `move_message` remains
  their composition so `ImapAgent`'s single-message step is unchanged. `do_file_messages` holds one connection for the
  batch: three connections per run in total, down from fifty-two.

  A second benefit falls out of the ordering: because every folder is created before any message moves, a folder the
  server refuses aborts the batch with the whole inbox intact, instead of stranding it half-filed. Filing itself stays
  sequential, so a mid-batch failure still leaves the filed messages filed and the rest unread for the next run.

- **Configured folder names are delimiter-specific, and the platform does not translate them.** `_hierarchy_paths`
  splits on the delimiter the server reports in its `LIST` response, which is correct but means one configured name
  produces different mailboxes on different servers. Verified against GreenMail (delimiter `.`): `Triage/Support` is
  created as a *single flat folder literally named* `Triage/Support`, with no `Triage` parent, while the same name on
  Gmail (delimiter `/`) creates a real `Triage` → `Support` tree. Supplying `Triage.Support` to GreenMail does produce
  the parent-and-children tree, confirming the hierarchy logic itself is right.

  Nothing is broken either way — mail is filed and found in both shapes — so no translation layer was added. Admins
  configuring nested categories need to use their own server's delimiter, and the shipped template's `Triage/…` names
  assume Gmail's.

- **Verified against two real servers, not only mocks.** `ImapClient` was probed end-to-end against GreenMail 2.1.5 and
  a live Gmail account: capability detection, `list_unread` ordering, `BODY.PEEK` leaving mail unread, attachment
  parsing, batch `ensure_folders` creating and subscribing folders that did not exist, filing, and a second run finding
  nothing left to do. Both passed every check.

  The two exercise genuinely different code paths, which is the value of running both:

  |                    | GreenMail 2.1.5 | Gmail      |
  | ------------------ | --------------- | ---------- |
  | `MOVE` / `UIDPLUS` | yes / yes       | yes / yes  |
  | `SORT`             | advertised      | **absent** |
  | `LIST` delimiter   | `.`             | `/`        |
  | SPECIAL-USE        | no              | yes        |

  Gmail does not advertise `SORT`, so it is the client-side ordering fallback that runs there — the branch that matters
  most in production, and the one a GreenMail-only check would never reach. Gmail's localized `[Gmail]/…` namespace (the
  test account lists its special folders in Vietnamese) appears in `LIST` without confusing `ensure_folders`, because
  the batch matches configured names literally and only creates what is missing.

- **`enable_move` / `processed_folder` are baked non-configurable** on this blueprint's form. A single fixed
  processed-folder is meaningless when the classifier picks the destination, and a field that must not exist is not the
  same as a field that is conditionally hidden.

Drafting replies per category (#1639), grounding those drafts in per-category knowledge (#1720) and running the agent on
a schedule (#1638) are separate stories, all blocked on this one.
