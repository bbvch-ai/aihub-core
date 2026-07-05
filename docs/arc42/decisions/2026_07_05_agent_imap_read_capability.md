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
- **Result events**: `UnreadMailListedEvent` and `MailFetchedEvent` live in `packages/core`
  (`events/agent/imap/`) as `ControlAndDisplayEvent`s — control, because steps consume them; display, so they render by
  name in the event timeline. They are protocol types deliberately placed in core for reuse by the sibling stories,
  the same way MCP's `ToolEvent` lives in core.
- **Attachments as S3 references**: `MailFetchedEvent` carries `MailAttachmentRef` (filename, content-type, `file_id`,
  size) — never raw bytes. The fetch step writes attachment bytes to the shared `agent-files` bucket under the agent's
  own path prefix and emits references, mirroring `UserUploadedFile`. This required **wiring an S3 client into the agent
  runtime for the first time** (`MailAttachmentStore`, using `S3StorageSettings` with the blocking put wrapped in a
  thread).
- **New dependency**: `aioimaplib` for async IMAP. MIME/attachment parsing uses the Python standard-library `email`
  module — no additional dependency.
- **Read-only scope**: no SMTP, no sending — ever. Sending is explicitly out of scope for the whole email capability,
  not just this story. Read-only extends to the protocol level: listing and fetching use `BODY.PEEK[...]` so the
  `\Seen` flag is never set, and every server response is status-checked (`ImapCommandError`) instead of trusting
  aioimaplib's non-raising `NO`/`BAD` responses.
- **Stable message identity**: messages are addressed by IMAP UID (`UID SEARCH` / `UID FETCH`), not sequence numbers —
  list and fetch run on separate connections (possibly separate servers), and sequence numbers shift when another
  client expunges mail in between.
- **Bounded listing**: `ImapClientConfig.max_messages` (default 50) caps how many unread summaries a single
  `UnreadMailListedEvent` carries, keeping the persisted/streamed event small even for overflowing inboxes.

A playground demonstrator agent (`playground/minimal_workflow/imap_workflow`) exercises the capability end to end
(`list_unread_step` → `fetch_mail_step` → stop) and hosts the BDD tests.

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
- **Mailbox credentials are stored at-rest in the agent config**, like MCP `api_key`. A platform-wide
  secret-indirection mechanism (Key Vault / references) for agent configs remains a possible follow-up if the security
  posture needs to tighten.
- **`aioimaplib` is a new runtime dependency** in `packages/agent`, adding to the maintenance and supply-chain surface.
- **Mail bodies are protocol payloads.** `MailFetchedEvent` carries `body_text`/`body_html` of arbitrary inbound mail
  into the audit trail (FerretDB) and to the frontend over WebSocket; Presidio only guards the LLM path. Frontends must
  never render `body_html` as raw HTML (XSS from a hostile sender).
