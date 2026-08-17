# Model Identity as a Platform-Injected System Prompt for Plain LLM Chats

## Context

Issue #144: a user asked "who are you" with `Kimi-K2.6` selected, switched the model picker to `Qwen3.5-122B-A10B-FP8`
**within the same conversation**, and asked again. Qwen answered *"I'm Kimi, an AI assistant created by Moonshot AI."*

This is not a routing fault. Every chat model in `litellm-config.yml.j2` maps 1:1 to a distinct upstream deployment, the
only fallback target is `text-generation/gemma-4-31B-it`, and Kimi is never a fallback target — so a Qwen request cannot
be served by Kimi. The cause is the message list. OpenWebUI keeps **one history per conversation across a model
switch**, and `OpenaiService.chat_completion` passes `messages` to LiteLLM untouched. Nothing on the plain-LLM path ever
established who the model is, so the model resolved the question from the transcript — where "the assistant" had already
claimed to be Kimi. The model's own reasoning trace states the mechanism outright:

> *"In the first turn, I identified myself as Kimi […] I don't have access to my external system prompt to know my exact
> brand name right now. I must rely on the context provided."*

**The defect is probabilistic, not deterministic.** Replaying the contaminated history against Qwen3.5 four times with
no system prompt produced the wrong identity **3 of 4 times** in an English conversation and **0 of 4 times** in a
German one. Any single reproduction — or any single "it works now" — is therefore weak evidence, and this ADR's claims
rest on repeated sampling rather than one observation.

One trace also showed the model unable to resolve its trained identity against the transcript persona and looping —
`Wait, I am Qwen. → Okay, I should not say Kimi. → Wait, I don't know.` — for 38 seconds. That was observed once and is
recorded as a symptom, **not** as a cost this decision claims to remove (see Trade-offs).

Agents do not have this problem. ADR `2026_06_04_self_awareness_as_explicit_per_agent_steps` gives each conversational
blueprint explicit `detect_meta_question_step` / `answer_meta_question_step` methods that answer identity questions from
the agent's own workflow definition. Plain LLM models bypass all agent machinery, so they inherit none of it. This issue
is the plain-model gap in that same concept.

## Decision Drivers

- **A model must not misreport which model it is**\
  The UI labels the answer with the selected model. An answer naming a different vendor makes that label a lie, and the
  user cannot tell which model actually ran.
- **The identity conflict must be *resolved*, not merely contradicted**\
  A bare "you are X" competes with the transcript. The prompt has to name the foreign turns as foreign, or it is just
  one more voice in the conversation.
- **Qwen3.5 constrains where a system message may go**\
  Per ADR `2026_06_29_resilience_for_reasoning_models_on_infomaniak`, Qwen3.5 rejects with
  `400 - System message must be at the beginning` when a system message follows any user or assistant turn.
- **Agents own their identity**\
  Whatever the platform injects must not reach an agent, or it contradicts that agent's own self-awareness steps.
- **A caller's own system prompt must keep winning on task behaviour**\
  Platform identity is a default, not an override of what the customer configured.
- **Changes to the prompt must be measured, not argued**\
  Output token counts on this question swing 8-10x within a single prompt variant, so intuitions about prompt wording
  are untestable by inspection. Every wording claim below is backed by a sweep or dropped.
- **No new abstractions**\
  The codebase already inserts system messages into a message list (`extend_chat_history_with_user_memory`) and already
  keeps prompts in `lib/prompt.{locale}.yml`.

## Decision

**A platform-authored system message asserting the model's identity leads the message list of every plain-LLM chat
completion.**

**1 — The prompt lives in i18n.** `lib.prompt.model.identity_system_message` in
`packages/core/swiss_ai_hub/core/i18n/translations/lib/prompt.{de,en,fr,it}.yml`, interpolating `{model_name}`. It does
three things:

- names the model as itself;
- states that earlier assistant turns may come from a different model and are not its own;
- declares the statement authoritative and, **for identity questions only**, forbids deliberating and asks for a
  one-sentence answer.

That last clause is scoped on purpose. Injection is unconditional (Decision 3), so the message also leads OpenWebUI's
*task-model* calls: search- and retrieval-query generation both default to on in v0.9.5
(`ENABLE_SEARCH_QUERY_GENERATION`, `ENABLE_RETRIEVAL_QUERY_GENERATION`), neither is set in any compose file, and both
route through `TASK_MODEL` to this same endpoint. Their prompt demands a strict JSON object, and an unscoped *"answer in
one short sentence"* would lead it. The damage would be silent: on a parse failure OpenWebUI turns the raw response into
a single search query rather than erroring (`utils/middleware.py`). Gating the injection off those calls is not
available — OpenWebUI pops `metadata`, which is what carries `task`, before forwarding (`routers/openai.py:1101`), so a
task call arrives indistinguishable from a chat turn. Wording is the only lever. The sweep below sampled identity
questions exclusively, so scoping the clause to exactly that traffic leaves every cell of it valid.

The middle clause is the one that fixes the bug. **"served by Swiss AI Hub" is deliberately absent and must not be added
back for branding**: models routinely conflate "served by" with "created by", so naming the deployment next to an
identity assertion invites a fresh misattribution ("I was created by Swiss AI Hub") of exactly the kind this ADR exists
to remove. Verified live — asked "who created you?", Qwen answers *"I was created by Alibaba Cloud."*

It uses `str.format` brace interpolation, not Jinja, because `jinja2` is not a declared dependency of `packages/api` or
`packages/core` (only transitively present) and `lib.prompt.condenser.standalone_question` already establishes brace
substitution in this very file. Note that yamlfix strips blank lines inside the YAML block scalar, so the prompt reaches
the model as consecutive lines; do not reintroduce them expecting them to survive.

**2 — Injection happens in `OpenaiService._apply_model_identity`,** called from `chat_completion`. The message is
**prepended**, satisfying Qwen3.5's constraint, and any caller-supplied system prompt is preserved after ours — so the
caller still wins on task behaviour. Multiple leading system messages are already production behaviour on this stack
(`extend_chat_history_with_user_memory` inserts after existing leading system messages), so no merging is needed. The
display name is `model_name.rpartition("/")[2]`, which strips the capability prefix (`text-generation/Kimi-K2.6` →
`Kimi-K2.6`) and leaves an unprefixed name untouched.

The call site is pinned by `test_streaming_response_outlives_the_handler`, the suite's only happy path through
`chat_completion`. Every other identity test either calls `_apply_model_identity` directly or asserts it did *not* run,
so without that assertion the call could be deleted from `chat_completion` and the whole suite would stay green while
#144 silently returned.

**3 — Injection is unconditional.** OpenWebUI does **not** reach this endpoint through `openai_pipeline`; it reaches it
through its own native OpenAI connection (`OPENAI_API_BASE_URL=…/api/v1/active/openai`), and the models users actually
pick are OpenWebUI workspace models whose `base_model_id` points at that connection. Its payload carries no `metadata`,
no `thread_id` — nothing that distinguishes it from a stock OpenAI SDK client. There is therefore no field to gate on
(see the rejected alternative below).

**4 — Agents are excluded by call ordering, not by a conditional.** `chat_completion_with_assistants` reaches its agent
branch only by catching the 404 that `chat_completion`'s `get_model` raises for a non-model. Placing the injection
**after** `get_model` yields the correct behaviour with no branch: a plain model is injected, an agent raises before
injection and reaches the agent branch with `messages` untouched. Two unit tests (`TestAssistantsKeepTheirOwnIdentity`)
pin this ordering so reordering the two lines fails loudly instead of silently handing every agent a contradicting
persona.

**5 — Reasoning is not disabled for this call.** ADR `2026_06_29` disables reasoning for single-token classifiers but
records that this is *"not a pattern to copy for answer generation"*. This is answer generation.

**6 — Foreign assistant turns are not stripped or annotated.** Removing or relabelling another model's turns would be
semantically tidier but changes the meaning of the history the caller sent and costs tokens. The system prompt is the
smaller intervention; escalate only if measurement shows it insufficient.

### Rejected: gate the injection on `metadata.thread_id`

`OpenaiController` promises a drop-in OpenAI replacement, so injecting a system message the caller never wrote is a real
change to that contract: it can collide with an external client's own persona, shifts their token accounting, and makes
their evals non-reproducible against a direct provider call. Gating on the AI Hub-only `metadata.thread_id` looked like
a way to protect external callers while still fixing the hub's own chat.

**It was implemented, then reverted after live verification proved it inert.** With the gate in place, issue #144 still
reproduced in the browser, because the hub's own chat does not send `thread_id` either (Decision 3). The gate protected
external callers by also protecting the bug. Since the hub's payload and an external client's payload are
indistinguishable, no gate can separate them, and fixing the product flow wins over passthrough purity.

### Rejected: an explicit answer-language clause

The prompt is localized, but on this path the locale always resolves to `LocaleHandler.DEFAULT_LOCALE = "de"` —
OpenWebUI sends no locale header — so an English conversation receives a German system prompt. A trace showed the model
spending part of its deliberation on *"the system instruction is in German, the user is in English, which language do I
answer in?"*, which suggested adding an explicit "always reply in the user's language" clause.

A sweep across both an English and a German conversation (4 samples per cell) showed the concern is unfounded and the
cure is harmful:

| variant                          | wrong identity     | wrong answer language | output tokens (median) en / de |
| -------------------------------- | ------------------ | --------------------- | ------------------------------ |
| no system prompt                 | **3/4 en**, 0/4 de | 0/8                   | 171 / 275                      |
| German prompt (shipped)          | 0/8                | 0/8                   | 800 / 624                      |
| English prompt                   | 0/8                | 0/8                   | 340 / 919                      |
| English prompt + language clause | 0/7                | 0/7                   | **2576 / 1678**                |

The model follows the **user's** language, not the system prompt's, in both directions (0 wrong-language across all 31
samples), so the mismatch costs nothing in correctness. Adding the clause tripled output tokens and degraded the answer
— some samples dropped the model name entirely (*"Ich bin ein KI-Assistent."*). The clause was dropped.

The same sweep found no separable token difference between the German and English prompt (German cheaper in one
conversation language, dearer in the other), so **English-only was also dropped**: it would trade the repo's i18n
convention for no measured gain.

## Consequences

### Positive

- Issue #144 is fixed at the single chokepoint every plain-model caller passes through. Across 23 sampled requests
  carrying an identity-contaminated history, **0 returned the wrong identity**, against 3-of-4 wrong without the prompt.
- Verified end-to-end in the browser through the real user flow (`packages/web` → iframe → OpenWebUI → API), not only in
  unit tests.
- Vendor attribution stays correct: the model names its real maker, not the platform.
- Agents are unaffected, and the call ordering that guarantees it is test-enforced.
- No change to `openai_pipeline.py`, so the fix needs no `openwebui-init` re-registration cycle to reach a running
  stack.

### Trade-offs

- **Output tokens roughly double to quadruple on identity questions.** Median output tokens for this question went from
  171 → 340-800 (English) and 275 → 624-919 (German). This is the measured price of a correct answer, not a free fix. It
  applies only to the model's response length on such questions; the added input is a handful of lines.
- **This decision does not claim to stop the reasoning loop.** The earlier draft asserted the anti-deliberation clause
  removed an unbounded token cost. No measurement supports that: no sample in the sweep hit `finish_reason: "length"`
  either with or without the prompt, and a browser trace still showed the model looping on *wording*
  (`"Wait, I'll check…" → "Okay." → "Wait…"`) after the prompt was added. The clause stays because it is cheap and
  plausibly helps, not because it is proven.
- **External callers get no protection from this class of bug.** A customer building their own model-switching UI on
  this endpoint will reproduce #144 and must set their own system prompt. They own their message list, so they own the
  fix — and per Decision 3 we cannot tell them apart from the hub anyway.
- **The endpoint is no longer a byte-for-byte passthrough.** Every plain-model caller receives a leading system message
  it did not author.
- **The identity string is config-derived.** It comes from the LiteLLM `model_name`, so renaming a model in
  `litellm-config.yml.j2` silently changes what the model calls itself.
- **The localization is nominal on this path.** Because the locale always resolves to `de` here, the fr/it translations
  are effectively unreachable and the de one is correct only by coincidence. Fixing that needs a real locale signal from
  the caller, which OpenWebUI's native connection does not send; it is out of scope here.
- **The plain-model path still has no resilience wrapper.** `ResilientOpenAILike` from ADR `2026_06_29` sits in
  `LLMConfig.to_llama_index()`, the agent path. Plain-model chat uses a raw `AsyncOpenAI` client via
  `LiteLLMService.openai_aclient_for_user`, so none of that ADR's reasoning-model mitigations apply here.
- **Mitigation, not a guarantee.** A long transcript with many contrary assistant turns can still outweigh a single
  leading system message.
- **Task-model calls still receive the identity message.** Query generation for web search and RAG retrieval gets the
  two identity clauses prepended to a JSON-only prompt. They are inert for that task — neither names a format nor asks
  for brevity — but they are tokens those calls did not ask for, and no sweep covers non-identity traffic.
- **One existing test double had to become real.** `test_streaming_response_outlives_the_handler` passed
  `t=Mock(locale="en")`, which reached the message list as an unserializable `Mock` once `chat_completion` began
  resolving a translation through `t`. The test now uses a real `LocaleHandler`; making the production code tolerate a
  non-resolving `t` was rejected as defensive.
