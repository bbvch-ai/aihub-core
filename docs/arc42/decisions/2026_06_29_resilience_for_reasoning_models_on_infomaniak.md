# Resilience for Reasoning Models (Kimi-K2.6, Qwen3.5) on Infomaniak

> **Superseded by
> [`2026_07_13_response_format_as_default_structured_output`](2026_07_13_response_format_as_default_structured_output.md).**
> This ADR assumed the `response_format` JSON-schema path was also unreliable on the Infomaniak reasoning models; that
> was never separately verified and later proved false (JSON schema with reasoning disabled parses cleanly on
> Kimi/Qwen). The structured-object callers now default to `response_format`, and the disabled meta features are
> re-enabled. The plain-text-verdict conversion of the relevance guards and meta-question detection described below is
> **retained** — it remains the mechanism for those single-token classifiers.

## Context

Swiss AI Hub routes all chat LLM access through LiteLLM. In CPU (non-GPU) deployments there is no self-hosted vLLM —
every text-generation model is served by **Infomaniak's managed inference** (`SWISS_LLM_CLOUD_API_BASE_URL`,
`api.infomaniak.com/.../openai/v1`). Two of the offered models, **Kimi-K2.6** and **Qwen3.5-122B-A10B-FP8**, are
*reasoning* models.

Several agent steps depend on **structured output** from the LLM via LlamaIndex `astructured_predict`: the guards
(`agent_description_guard`, `few_shot_guard`, `context_sufficient_guard`), LLM routing, and — until recently — the
self-awareness meta-question detector. These calls force a tool call (`tool_choice="required"`) or request a JSON schema
so the result can be parsed into a Pydantic model.

The reasoning models on Infomaniak **cannot reliably produce parseable structured output**. Empirically, the same
request fails in several distinct, intermittent ways depending on the model and the moment:

- forced tool call returns `finish_reason: "tool_calls"` but an **empty `tool_calls` array** (the model's intent is
  stranded in `reasoning_content`);
- JSON-schema mode returns JSON wrapped in a ```` ```json ```` fence, prose instead of JSON, truncated JSON, or a
  multi-block response the parser rejects;
- with reasoning disabled the model **omits required fields**.

We confirmed the actual `vllm serve` configuration is on Infomaniak's side and not editable from this repository, so the
true fix (a correct tool-call/reasoning parser) can only come from the provider. The failures surfaced as run-killing
`ExceptionEvent`s in OpenWebUI (e.g. "Expected at least one tool call, but got 0 tool calls", pydantic
`json_invalid`/`missing`). Qwen3.5 additionally rejects with `400 - System message must be at the beginning` when a
system message follows any user/assistant turn — which Kimi tolerated.

The team has **temporarily disabled** the two most affected conversational features — `#1535` (conversation title +
follow-up generation) and `#1536` (the per-agent self-awareness meta-question steps, see ADR
`2026_06_04_self_awareness_as_explicit_per_agent_steps` and
`2026_06_18_conversation_metadata_as_explicit_per_agent_steps`). However, the **underlying structured-output fragility
still affects live agents**: the `FewShotAgent`'s suitability check calls `agent_description_guard`, and the `RAGAgent`
calls `few_shot_guard` and `context_sufficient_guard` — all of which still crash on Kimi/Qwen.

## Decision Drivers

- **The agent must not crash on a model the deployment is configured to use**\
  A flaky managed endpoint must degrade gracefully, not surface a 500 to the end user mid-conversation.
- **No control over the serving layer**\
  On CPU deployments the models run on Infomaniak; we cannot change the vLLM parsers. Mitigations must live in the
  application/LiteLLM layer.
- **Reasoning models are reliable at free text, unreliable at structured output**\
  A single-token classification ("NORMAL" / "META_IDENTITY" / …) comes back cleanly where a forced tool call or JSON
  object does not.
- **Distinguish relevance guards from security controls**\
  `agent_description_guard`, `few_shot_guard`, and `context_sufficient_guard` decide topical suitability and retrieval
  sufficiency — they are not authentication, PII, or injection boundaries. Their failure should not block the user.
- **The disablement of self-awareness is temporary**\
  The feature is expected to return. Improvements that make it work on reasoning models should be preserved rather than
  discarded and re-derived later.
- **Latency**\
  Letting a reasoning model "think" before a trivial classification adds ~4-5s per message for no benefit.

## Decision

We harden every structured-output path at the application/LiteLLM layer and keep the (now-dormant) self-awareness
improvements for future re-enablement.

**1. Retry structured prediction — `ResilientOpenAILike`.** `LLMConfig.to_llama_index()` returns a thin `OpenAILike`
subclass (`resilient_open_ai_like.py`, mirroring the existing `PatchedOpenAILLM` provider-quirk pattern) that retries
`(a)structured_predict` a few times before letting the error propagate. This absorbs the *intermittent* failures.

**2. Plain-text verdicts for the relevance guards.** `agent_description_guard`, `few_shot_guard`, and
`context_sufficient_guard` no longer call `astructured_predict`. They append a parseable output instruction to their
existing prompt, ask the model (reasoning disabled) for a one-word verdict — `ALLOW`/`BLOCK` for the suitability guards,
`SUFFICIENT`/`INSUFFICIENT` (plus a `QUERY:` line) for context — and parse it (shared `text_verdict.py`). This is the
same technique that makes detection work, so these guards now return **reliable** decisions on reasoning models rather
than degrading. As a final safety net, an unrecognizable response **fails open** (`success=True` → accept / treat
context as sufficient): these are relevance/quality guards, not security controls, and blocking every request on a model
that occasionally returns no verdict would make the agent unusable. The security-relevant `sensitive_info_guard` is
deliberately **not** converted and has **no** fallback. Guard failures are logged with the exception **type only**
(never the raw text, which can echo the query or retrieved context).

**3. Plain-text token classification for meta-question detection.** `detect_meta_question` no longer uses
`astructured_predict`. It sends a purpose-built English prompt asking for exactly one token (`NORMAL` / `META_IDENTITY`
/ `META_CAPABILITIES` / `META_BEHAVIOR`), calls `achat`, and parses the last token; an unrecognized response degrades to
"not a meta question". Reasoning is disabled for this call (`extra_body={"chat_template_kwargs": {"thinking": false}}`)
since the classification is trivial — cutting latency from ~4-5s to sub-second with no loss of accuracy.

**4. System prompt must lead the message list.** `do_answer_meta_question` and the `RAGAgent` guard-reject branch now
place the system message first, satisfying Qwen3.5's "System message must be at the beginning" constraint. The normal
RAG answer path already complies (its retrieved-context message is a user-role message).

**5. Keep the dormant self-awareness changes.** Even though `#1536` removed the self-awareness *steps* from the agents,
the shared `self_awareness/` functions remain in the codebase. The improvements above to `detect_meta_question` and
`do_answer_meta_question` are **intentionally retained** (with their unit tests) so that re-enabling self-awareness
later requires only re-adding the per-agent steps, not re-discovering how to make detection work on reasoning models.

## Consequences

### Positive

- Agents no longer crash on Kimi/Qwen — verified zero crashes across the `FewShotAgent` and `RAGAgent` guard paths on
  both models.
- The fix is centralized: `ResilientOpenAILike` covers every structured-prediction caller (current and future) through
  the single `to_llama_index()` chokepoint, with no per-call-site changes.
- Meta-question detection becomes both reliable *and* faster on reasoning models (sub-second vs ~4-5s), and correctly
  classifies edge cases ("what can I do with this document?" → normal).
- The self-awareness detection improvement is preserved and unit-tested, ready for the feature's return.
- Guard-failure logs no longer leak model output / query / context text.

### Trade-offs

- **Relevance guards fail open on an unparseable response.** With the text-verdict conversion the guards now return
  reliable decisions on reasoning models, so this is a last-resort path rather than the common case. When it does
  trigger, the guard accepts the request rather than rejecting it — a deliberate, documented choice: these guards gate
  topical relevance and retrieval sufficiency (not a security boundary), and failing closed would reject requests
  whenever the model returns no verdict, harming usability. Scoped to relevance guards only; the security-relevant
  `sensitive_info_guard` retains fail-closed behavior and is not converted.
- **Reasoning is disabled for guard/detection calls.** A guard verdict and a meta-question label are trivial
  classifications, so thinking is pure latency. Disabling it is what keeps these calls reliable and fast, but it means
  the verdict is a direct judgment rather than a reasoned one — acceptable for these gates, not a pattern to copy for
  answer generation.
- **The detection prompt is a code-built English token prompt**, not the localized i18n prompt — the fixed tokens are
  parse-critical and language-agnostic; the model still reads any-language user queries. This is a minor deviation from
  the "prompts live in i18n" convention.
- **Dormant code is carried in the tree.** The self-awareness detection changes are not exercised by any agent while the
  feature is disabled, which can confuse readers; this ADR records why they are kept.
- **The real fix is provider-side.** These are mitigations around a flaky managed endpoint. An instruct model (gemma-4 /
  Ministral / Apertus) makes all structured features work natively; reasoning models remain best-effort until Infomaniak
  corrects their tool-call/reasoning/structured-output handling.
