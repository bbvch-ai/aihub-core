# Asynchronous User-Memory Storage Is the Only Mode

## Status

Accepted. Supersedes the flag half of `2026_07_07_decoupled_user_memory_storage`, whose reasoning for the mechanism
itself still stands.

## Context

`2026_07_07_decoupled_user_memory_storage` introduced the `MemoryWriterAgent` and put it behind
`UserMemoryConfig.enable_async_memory_storage`, defaulting to **off**. The flag was a rollout device: it let the
decoupled path ship without changing behaviour for any existing profile, and it left an escape hatch for an agent
needing read-your-writes memory.

Since then the writer is deployed in every stage (`infra/deployment/compose-config.yml`, with a
`make run-memory-writer-agent` target for local runs), so the inline path is no longer the safe default — it is the slow
one. It is also the reason for three pieces of complexity that earn nothing once the flag is always on:

- `store_user_memory_step` branched on the flag, which is why the dispatcher injected `AgentMemory` into a step that, on
  the decoupled path, never touches mem0.
- The step's return type was a union, so `RAGAgent` and `ExpertRAGAgent` **announced** `StoreUserMemoryEvent` as one of
  their output events even though the writer is what emits it.
- `check_ready_for_stop` took both events and picked which one gates the stop by re-reading the flag, so the terminal
  gate of every RAG run depended on a storage-mode switch.

The escape hatch was never the right shape for the staleness it addresses: a fast follow-up run can outrun the write
whether or not one profile opts out, because the window belongs to the writer's queue, not to the caller's
configuration. The follow-ups named in the previous ADR (idempotency on `origin_run_id`, per-user ordering) are what
actually close it, and they remain open.

## Decision Drivers

- The decoupled write is the behaviour every profile should have; a per-profile switch for it is configuration surface
  with no good setting.
- Removing a mode removes a branch from the terminal gate of every RAG run, which is the highest-risk precondition in
  the blueprint.
- No user-visible regression: the flag's off state was the slow path, so profiles move from slower to faster.

## Decision

Delete `UserMemoryConfig.enable_async_memory_storage` and the inline branch behind it.

- `store_user_memory_step` returns `MemoryStorageRequestedEvent` unconditionally and no longer receives `AgentMemory`.
  `RAGAgent` and `ExpertRAGAgent` therefore no longer announce `StoreUserMemoryEvent`; the `MemoryWriterAgent` is its
  only producer.
- `check_ready_for_stop` gates on the delegation marker alone. It keeps the `has_user` check, which is what still makes
  an identity-less run terminate rather than wait for a write it deliberately skipped.
- The **Store memory asynchronously** checkbox disappears from the agent configuration form. Nothing replaces it.
- Saved profiles need no migration: a config model ignores keys it does not declare, and the API's update validation
  ignores undeclared nested keys, so a stored `enable_async_memory_storage` is inert at runtime and on re-save. To keep
  stored documents honest anyway, the API strips the key at startup (`strip_retired_agent_config_keys` in
  `initialize_db.py`, via `AgentConfigEntityDocument.unset_config_key`). That pass is transitional: **delete it, and the
  entity method, once deployments have upgraded past this release.**

## Consequences

**Positive**

- One storage path to reason about, test and trace. The stop gate no longer branches.
- Every profile gets the run-finalizes-immediately behaviour, including the ones that never knew the flag existed.
- The step no longer asks for a mem0 client it does not use, so it is unit-testable without infrastructure.

**Negative / risks**

- **The writer is now a hard runtime dependency of RAG and ExpertRAG.** With it undeployed, the delegation publish
  retries and fails, the memory is lost, and only an error in the log says so — the chat run still answers and still
  terminates, because the marker is published to the caller's own store first. Self-hosted deployments that run the RAG
  agent must run the writer.
- **No read-your-writes opt-out remains.** A follow-up run may retrieve before the previous run's write lands. This is
  the staleness the previous ADR listed, now without a per-profile mitigation; its idempotency and per-user-ordering
  follow-ups are the real fix and are still open.
- BDD suites for both blueprints now publish to the writer's stream on every run, so they create it via
  `ensure_dependent_agent_stream` rather than logging publish retries.

## Related

- `2026_07_07_decoupled_user_memory_storage` — introduced the mechanism and the flag this removes.
- `2026_07_07_disable_graph_store_for_user_memory` — the companion cost reduction.
- Issues #1179, #1590.
