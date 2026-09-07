# Memory Search and Storage Use the Condensed Standalone Question

## Status

Accepted. Addresses issue #1753 (sibling of #1752, the embedder-window crash guard). Builds on
`2025_12_18_adopt_mem0_for_agent_memory`, `2026_07_07_decoupled_user_memory_storage` (#1179), and
`2026_07_07_disable_graph_store_for_user_memory` (#1713).

## Context

Issue #1753: `retrieve_user_memory_step` and `retrieve_organization_memory_step` in `RAGAgent` and `ExpertRAGAgent`
searched mem0 with `event.user_query` — the raw content of the last user message. The platform runs OpenWebUI with
`RAG_FULL_CONTEXT: true`, so when a knowledge base is attached that message is the full-document-inlined prompt: memory
search embedded document text instead of the question (semantically unrelated results), and on 2026-08-19 the oversized
query blew the embedder's 8192-token window on the `be` instance, killing the run. Document retrieval was already immune
because `retrieve_step` searches with the LLM-condensed standalone question.

Memory **storage** had the same disease with a subtler mechanism: `store_user_memory_step` fed `llm_event.chat_messages`
— the entire final LLM input plus the answer — into mem0 fact extraction. `AgentMemory.messages_to_dict` filters SYSTEM
messages, but that filter catches neither the RAG context message (rendered with `{% chat role="user" %}`) nor the
client-augmented user message, so retrieved-document text reached stored "user facts" from two sources.

The structural obstacle: memory retrieval sat *upstream* of condensation (`retrieve_*_memory` →
`add_memory_to_chat_history` → `limit_chat_history` → `condense`), so consuming the condensed question naively creates a
dependency cycle.

## Decision Drivers

- Memory search and storage must never see raw client-augmented messages — for any chat client, without coupling the
  agent to a client's prompt template (`RAG_TEMPLATE` is configurable platform config).
- No extra LLM call and no added critical-path latency.
- The meta-question gate (ADR `2026_06_04`) must stay intact: no memory operation on a raw chat message before
  detection clears it.
- No payload-contract change toward `MemoryWriterAgent` (#1179).

## Decision

Reorder the workflow in both agents so every memory operation consumes the condenser's output:

- `limit_chat_history_step` drops its memory dependency and becomes the sole gated raw-chat entry step; it truncates the
  raw start messages. This is the cycle break.
- `retrieve_user_memory_step` / `retrieve_organization_memory_step` consume `StandaloneQuestionCondenserEvent` and
  search with `condensed_chat_message.content`. Their `_clear` gate is dropped — they are gated transitively through the
  condenser (pinned by `test_meta_question_gate.py`).
- `add_memory_to_chat_history_step` grafts the memory system blocks onto the *limited* history (copying the list — the
  extend helpers mutate in place). `context_sufficient_guard_step`, `limit_chat_history_with_context_step`, and
  `respond_with_llm_step` consume the extended history when a memory source is enabled
  (`check_memory_added_to_chat_history` precondition), falling back to the plain limited history otherwise.
- `store_user_memory_step` persists `build_memory_conversation(...)` = the condensed question plus the answer, on both
  the inline and the delegated (#1179) path. The final LLM input never reaches fact extraction again.
- `forward_to_expert_asking_agent_step` (ExpertRAG) sends the condensed question as `question_to_expert`, so a
  document-inlined prompt is never posted to a Teams/Slack channel.

Two facts make the reorder safe and cheap: the condenser strips SYSTEM messages before building its prompt, so memory
blocks never influenced condensation even before — the reorder is behavior-neutral for the condenser; and the condenser
always runs (no first-turn passthrough), so the condensed question exists on every path that stores memory or escalates
to an expert, including multi-hop retrieval and the expert-answer re-entry.

The minimal storage payload was chosen over "cleaned full history" because prior turns were already extracted by their
own runs' store steps, prior-turn messages from full-context clients are not guaranteed clean either, and mem0's update
prompt reconciles duplicates — re-feeding history only multiplies embedding cost.

## Consequences

- **(+)** Memory search embeds the question, not documents; stored memories contain user facts. The #1752 crash trigger
  disappears for the agent path (condensed questions are short) — the guard there still covers the memory REST API.
- **(+)** Latency: memory search leaves the serial pre-condense path and overlaps document retrieval and the few-shot
  guard. Worst case (mem0 slower than retrieval + guard combined) equals the wait the old graph imposed up front.
- **(−)** Memory blocks are added *after* token limiting: reject-path LLM inputs can exceed `number_of_input_tokens` by
  the memory-block size (the main answer path re-limits in `limit_chat_history_with_context`). Bounded by the ~10
  retrieved facts per scope.
- **(−)** A personal statement fused into a question survives storage only as well as the condenser's
  semantic-equivalence instruction preserves it. If this proves lossy, fix the condenser prompt
  (`lib.prompt.condenser.standalone_question`), not the memory pipeline.
- The condenser and the title generator still receive the augmented message (task-LLM window, not the embedder) —
  unchanged by this decision.
