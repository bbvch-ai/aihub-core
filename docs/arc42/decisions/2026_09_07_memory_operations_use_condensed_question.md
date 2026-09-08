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
- The meta-question gate (ADR `2026_06_04`) must stay intact: no memory operation on a raw chat message before detection
  clears it.
- No payload-contract change toward `MemoryWriterAgent` (#1179).

## Decision

Reorder the workflow in both agents so every memory operation consumes the condenser's output:

- `limit_chat_history_step` drops its memory dependency and becomes the sole gated raw-chat entry step; it truncates the
  raw start messages. This is the cycle break.
- `retrieve_user_memory_step` / `retrieve_organization_memory_step` consume `StandaloneQuestionCondenserEvent` and
  search with `condensed_chat_message.content`. Their `_clear` gate is dropped — they are gated transitively through the
  condenser (pinned by `test_meta_question_gate.py`).
- `add_memory_to_chat_history_step` grafts the memory system blocks onto the *limited* history (copying the list — the
  extend helpers mutate in place) and re-limits the result, so the event it emits is inside the token budget rather than
  the budget plus the blocks. `context_sufficient_guard_step`, `limit_chat_history_with_context_step`, and
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
- Memory blocks are added *after* the entry-step limiting, so `add_memory_to_chat_history_step` re-limits before
  emitting `AddMemoryToChatHistoryEvent` — `extended_history` carries the same "fits `number_of_input_tokens`" guarantee
  `limited_history` does. Without that, three consumers would read an over-budget history unchecked:
  `context_sufficient_guard` formats it straight into a prompt, `do_respond_with_llm`'s reject paths prepend a system
  message and send it, and `limit_chat_history_with_context` *reserves* system messages rather than trimming them, so an
  oversized block raises `ValueError` there instead of being cut. The blocks are ~450 (user) + ~375 (organization)
  tokens at their retrieval caps.
- **(−)** When history plus blocks do not fit, the blocks are what is dropped: `ChatMemoryBuffer` keeps the most recent
  messages and the blocks sit at the front. That matches the pre-reorder order, where memory was added before the only
  limiter, and it is the right loser — the alternative is discarding the turn the user asked about, and the template
  presents memories as optional context. Pinned by `test_memory_blocks_respect_token_budget.py`.
- **(−)** A personal statement fused into a question survives storage only as well as the condenser preserves it. The
  fix belongs in the condenser prompt (`lib.prompt.condenser.standalone_question`, all four locales) and is **not yet
  applied**. When it is, it must cover stated facts about the user only, and deliberately **not** verbatim code blocks
  or logs: the same string is embedded for retrieval, so carrying unbounded pasted content back into it reintroduces the
  embedder-window failure this decision exists to remove. Prompt compliance is probabilistic, so it belongs in a
  Langfuse evaluation set rather than a CI assertion that would flake.
- Making the condensed question load-bearing everywhere makes an empty one fatal, so `condense_standalone_question`
  raises `EmptyCondensationError` on a blank answer and both condenser events reject blank content with a
  `field_validator` — on the field, because JetStream replay and redelivery deserialize events with no step body to
  check them. Blank condensations are real: 8 runs between 30 June and 14 July 2026, all `ExpertRAGAgent`. There is no
  retry (identical re-issue at `temperature=0.1` returns the same nothing) and no fallback to the raw last user message,
  which is the document-inlined prompt this decision removes. `StandaloneQuestionCondenserEvent` and
  `FewShotStandaloneQuestionCondenserEvent` each need their own validator — different bases, no shared ancestor.
- **(−)** `FewShotAgent` inherits that raise even though it never retrieves, stores or escalates. Accepted rather than
  exempted: it drops chat history and the original message from its final prompt, so a blank condensation leaves the
  model classifying nothing — the failure the raise prevents is worse there than in the RAG agents, not milder.
- The condenser and the title generator still receive the augmented message (task-LLM window, not the embedder) —
  unchanged by this decision.
