# `response_format` JSON Schema as the Default Structured-Output Mechanism

- Status: accepted
- Supersedes: [`2026_06_29_resilience_for_reasoning_models_on_infomaniak`](2026_06_29_resilience_for_reasoning_models_on_infomaniak.md)

::: warning Update (2026-07-14)
Two parts of this decision were revised after monitoring:

- **The reasoning-disable flag was wrong for Qwen3.** `chat_template_kwargs={"thinking": false}` is silently ignored by
  Qwen3.5, which kept emitting ~1k reasoning tokens (~13s for a single-token classification). Qwen3 reads
  `enable_thinking`; both keys are now sent — `{"thinking": false, "enable_thinking": false}` — dropping detection to
  ~1s and the structured/meta paths to a fraction of their former latency. The mechanism (decision #3) is otherwise
  unchanged.
- **Conversation metadata (title + follow-up) is disabled again**, pending investigation — decision #6 below is
  therefore only partially in force. Per-agent self-awareness stays enabled (it now also disables reasoning on the
  streamed meta answer), **except `McpReactAgent`, which opted out of self-awareness entirely**.
  :::

## Context

Swiss AI Hub routes all chat LLM access through LiteLLM. On CPU (non-GPU) deployments every text-generation model is
served by **Infomaniak's managed inference**; two of them — **Kimi-K2.6** and **Qwen3.5-122B-A10B-FP8** — are *reasoning*
models. Several agent steps need **structured output** from the LLM via LlamaIndex `astructured_predict`: conversation
metadata (title + follow-up questions), the per-agent self-awareness meta-question steps, LLM routing, and namespace
selection.

LlamaIndex `OpenAILike.astructured_predict` picks one of two mechanisms:

- **Forced tool call** (`tool_choice="required"`) — the default when the model is not known to support JSON schema.
- **`response_format` JSON Schema** — used when `should_use_structured_outputs` is set (it sends
  `response_format={"type":"json_schema", …}` and drops `tool_choice`).

ADR `2026_06_29` disabled the two meta features and converted the relevance guards + meta-question detection to
plain-text token verdicts, because the **forced-tool-call** path fails on the reasoning models (empty `tool_calls`,
intent stranded in `reasoning_content`). That ADR also assumed the JSON-schema path was unreliable on the same models.
That assumption was **not separately verified** — the failures it recorded were observed with reasoning enabled and via
the tool-call path.

We re-tested the JSON-schema path directly through LiteLLM, with reasoning disabled
(`extra_body={"chat_template_kwargs":{"thinking":false,"enable_thinking":false}}`), against the Pydantic result models
used in production
(`TitleResult`, `FollowUpQuestionsResult`), 5 runs per model+schema:

| Model                         | Title parsed | Follow-ups parsed | Fenced/recovered |
| ----------------------------- | ------------ | ----------------- | ---------------- |
| Kimi-K2.6 (reasoning)         | 5/5          | 5/5               | 0                |
| Qwen3.5-122B (reasoning)      | 5/5          | 5/5               | 0                |
| gemma-4-31B-it (instruct)     | 5/5          | 5/5               | 0                |
| Apertus-70B (instruct)        | 5/5          | 5/5               | 0                |
| Ministral-3-14B (instruct)    | 5/5          | 5/5               | 0                |

`response_format` JSON Schema, **with reasoning disabled**, produces clean parseable JSON on every model — reasoning and
instruct alike — with no fences, no truncation, and no omitted fields. The forced-tool-call incompatibility is specific
to `tool_choice`, not to structured output in general.

## Decision Drivers

- **One mechanism for all models.** A single structured-output path that works on reasoning *and* instruct models is
  simpler than routing per-model-family and lets the disabled meta features come back unchanged.
- **`response_format` is the ecosystem standard.** It is the native structured-output mechanism across LiteLLM, vLLM
  (guided decoding / xgrammar), and the OpenAI-compatible API — decoupled from tool-calling quirks.
- **Reasoning is pure latency for these calls.** A title, a follow-up list, a route, or a meta-question label is a
  trivial extraction; letting a reasoning model "think" first adds seconds of latency (measured ~13s for a single-token
  classification on Qwen3.5) and is what produced the fenced/partial output the old ADR saw.
- **Capability must reflect the deployment, not a static registry.** LlamaIndex's built-in
  `is_json_schema_supported()` only knows OpenAI's public model names and returns false negatives for custom-named
  vLLM/Infomaniak models. The deployment's LiteLLM `model_list` is the source of truth.
- **Meta features must never fail the run.** Conversation metadata and meta-question steps are best-effort
  enhancements; a structured-output failure must degrade, not surface a 500.

## Decision

**1. `response_format` JSON Schema is the default structured-output mechanism, gated on deployment-declared capability.**
`LLMConfig.to_llama_index()` reads `supports_response_schema` from the deployment's LiteLLM `/model/info`
(`model_list`, the authoritative capability) and passes it as `should_use_structured_outputs` on `ResilientOpenAILike`.
When set, LlamaIndex uses `response_format` and drops `tool_choice`. Models that do not declare the capability keep the
forced-tool-call behaviour, so the switch is inert until the LiteLLM config opts a model in.

**2. Every chat model in the LiteLLM config declares `supports_response_schema: true`.** All Infomaniak cloud chat
models (Apertus, gemma-4, Kimi-K2.6, Ministral, Qwen3.5) and the local GPU model (vLLM, native constrained decoding)
carry the flag, driven from the Jinja2 template `templates/configs/litellm-config.yml.j2`.

**3. Reasoning is disabled on the structured-output path.** `ResilientOpenAILike` injects
`extra_body={"chat_template_kwargs":{"thinking":false,"enable_thinking":false}}` on `(a)structured_predict` when
`should_use_structured_outputs` is set. Model families read different keys — Qwen3 honours `enable_thinking` and
silently ignores `thinking`, other vLLM templates honour `thinking` — so both are sent. Mistral-tokenizer models
(Ministral) reject `chat_template_kwargs` with a 400, so the call falls back to a plain request — the same pattern
already used in `text_verdict.py`.

**4. Forced `tool_choice` becomes explicit opt-in.** The conversation-metadata path no longer forces `tool_choice`;
LlamaIndex's `response_format` path removes it anyway when the capability is declared. A call site that genuinely needs a
forced tool call passes `llm_kwargs={"tool_choice": "required"}` itself. Forced `tool_choice` is never sent to a model on
the `response_format` path.

**5. Resilience and best-effort behaviour are retained.** `ResilientOpenAILike` still retries malformed structured
output a few times. The re-enabled conversation-metadata and self-awareness steps keep their non-blocking wrappers
(`asyncio.gather(return_exceptions=True)` / `stop_on_error=False`), so a metadata/meta failure is logged and swallowed —
the answer and its stop event are unaffected.

**6. The meta features are re-enabled.** The temporarily disabled conversation metadata (title + follow-up) and per-agent
self-awareness meta-question steps are restored on all answer-owning conversational agents.

## Consequences

### Positive

- Conversation metadata and self-awareness work on the reasoning models (Kimi/Qwen) where they previously crashed, and
  continue to work on the instruct models — verified 5/5 across all five cloud models.
- One structured-output mechanism for every model; no per-model-family branching in application code.
- The mechanism is centralized at the `to_llama_index()` chokepoint and covers all `astructured_predict` callers
  (metadata, self-awareness, routing, namespace) without per-call-site changes.
- Structured calls are faster (reasoning disabled) and the capability lookup is cached with the model_info fetch.
- Capability is deployment-declared, so a deployment whose provider cannot do JSON schema simply omits the flag and
  falls back to the prior behaviour — no code change, no 500.

### Trade-offs

- **Capability is trusted from the LiteLLM config, not probed at runtime.** Declaring `supports_response_schema: true`
  for a model that cannot honour it would route structured calls to a failing path; the retry + best-effort wrappers
  contain the blast radius, but the flag must be set only for verified models (all current ones are).
- **Reasoning is disabled for structured extraction.** The verdict is a direct judgment rather than a reasoned one —
  acceptable for these trivial extractions, not a pattern to copy for answer generation.
- **Relevance guards and meta-question detection stay on plain-text verdicts.** Their `text_verdict` conversion from
  ADR `2026_06_29` remains — it is reliable and even simpler than JSON schema for single-token classification. Only the
  structured-object callers move to `response_format`. The security-relevant `sensitive_info_guard` is unchanged.
- **The real fix is still provider-side.** Forced tool-calling remains broken on Infomaniak's reasoning models; this
  decision routes around it rather than fixing the provider's tool-call/reasoning parser.
