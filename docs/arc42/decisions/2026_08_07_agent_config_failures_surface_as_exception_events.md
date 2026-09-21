# Agent Config Failures Surface as ExceptionEvents; Config Models Do Not Enforce Cross-Field Invariants

## Status

Accepted.

## Context

Issue #146 (aihub-core-private): an admin saved a RAG profile whose organization-memory `default_tenant_namespace`
(`engineering`) was outside its `allowed_tenant_namespaces` (`test`, `default`). The Admin UI accepted the save. From
then on the agent answered nothing — the chat hung on "The agent has received a message and is processing it", with no
error anywhere the user could see.

Three properties of the platform combined into that outage:

1. `OrgMemoryWriteConfig` carried a Pydantic `model_validator` requiring the default to be a member of the allow-list.
2. That rule **cannot** run at save time. Agent config schemas travel to the API as JSON Schema over NATS discovery
   (`AgentConfigSpecs.from_agent_config` → `to_configurable_submission_model().model_json_schema()`), and the API
   validates submissions against a model `jambo` rebuilds from that schema. JSON Schema cannot express a cross-field
   Pydantic validator, so the constraint was silently dropped and the config was stored.
3. `AgentDispatcher.handle_event` validates the whole agent config on **every** dispatched event, before any step runs.
   The raise happened outside the per-step `try/except`, reached `JSSubscriber`, which only logs — and the message had
   already been acked. No `ExceptionEvent` was published, so the run never terminated and never retried.

The same shape applies to `AgentConfig.validate_locale_strings_have_content`: this was a class of bug, not one bug.

## Decision Drivers

- A saved config must never be able to render an agent permanently mute with no diagnostics.
- The API cannot execute agent-side Pydantic validators without new machinery (an RPC round-trip that would also make
  saving a config require the agent to be online).
- An allow-list is a scoping control; silently widening it to swallow the inconsistency would be worse than failing.

## Decision

**1. A config model must not raise for an invariant that only some code paths depend on.** The
`default_tenant_namespace` ∈ `allowed_tenant_namespaces` check is removed from `OrgMemoryWriteConfig`.
`OrgMemoryNamespaceResolver.resolve_for_write` already enforces it — from inside a `@step`, where the dispatcher turns
the failure into an `ExceptionEvent` the user sees, and only when a write actually resolves a disallowed namespace.
Reads are unaffected: `resolve_for_search` scopes to the allow-list as before.

Generally: enforce a config invariant at the point of use, not in `model_validate`, unless every code path using that
config genuinely requires it. Config validation runs on the dispatch hot path for the whole agent; a raise there is not
a validation error, it is an outage.

**2. Config resolution failures are reported, not propagated.** `AgentDispatcher.handle_event` wraps config fetch, merge
and validation, and publishes an `ExceptionEvent` on failure. This covers any future config-level validator, plus RPC
and RunContext failures during resolution. `ExceptionEvent` is already terminal for the OpenAI-compatible stream and
present in the WebSocket `DisplayEvents` union, so the hang becomes a visible error message.

Terminal-event teardown sitting **above** config resolution is load-bearing for this, not cosmetic: teardown needs no
config, and if the published `ExceptionEvent` had to pass the same validation on its way back in, it would hit the very
error it reports and the run would never be retired. That ordering arrived independently with the redelivery fix
(#1692), which needed it to make a redelivered terminal event idempotent; this decision depends on it and must not be
reordered without reinstating it.

**3. Admin-facing invariants are expressed as form rules.** A generic `memberOf` FormKit rule (registered in
`packages/web/formkit.config.ts`) is attached to `default_tenant_namespace` via the existing
`PrimeVueElement.additional_validation_rules` passthrough, so the admin sees the conflict inline while editing. FormKit
2 tracks dependencies read through `node.at()` during rule execution, so the rule re-runs when the allow-list itself
changes. This is **advisory**: it is client-side only, and the API still accepts a mismatch via direct REST, config
import, or checked-in config templates. Nothing in the backend may depend on it.

## Consequences

**Positive**

- No agent config can brick an agent silently; the worst case is a visible `ExceptionEvent` and a crashed run.
- The reporter's configuration now chats normally. Only an org-memory *write* resolving a disallowed namespace fails,
  and it fails with a clear message — affecting `ExpertAskingAgent`, the only agent that writes org memory.
- Admins get immediate feedback in the form instead of discovering the conflict at write time.

**Negative / risks**

- A config inconsistency is no longer detectable by static validation of the stored document — it surfaces at write time
  or in the form. Anything generating configs programmatically (templates, imports, seeders) is not guarded.
- Config-resolution failures that used to escape (and be retried by nothing) now mark the run crashed. This is
  intentional, but it means a transient RPC or Redis blip during resolution ends the run visibly rather than silently.
- The `memberOf` rule is duplicated knowledge: the membership semantics live both in
  `OrgMemoryNamespaceResolver.resolve_for_write` and in the frontend rule. They are allowed to drift only in the safe
  direction (the form warns about something the backend permits).

## Related

- `2025_12_18_adopt_mem0_for_agent_memory` — organization-memory scoping this config drives.
- Org-memory namespace overrides and allow-list: PR #1202; Milvus `in`-filter translation: PR #1548.
