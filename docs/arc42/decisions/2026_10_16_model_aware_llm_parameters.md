# LLM Parameters Follow the Selected Model

## Context

Every agent profile carried the same model constants, whichever model it picked:

- **Temperature:** a class-level `0.0` with a fixed 0–2 range, and no way to set `top_p` at all.
- **Input budget:** `number_of_input_tokens` had a static 1,024–200,000 range. A budget a small-context model cannot
  serve saved without complaint and was only capped at run time.
- **Images:** they reached the model unchecked. A text-only model received them anyway, and a vision model with a
  per-request limit returned a raw provider 400 once a conversation crossed it. Chat clients resend every earlier image
  on each turn, so a conversation crosses such a limit long after the image that tipped it.

The platform already fetches each model's LiteLLM `model_info` live (`LiteLLMBase.get_model_info()`) and uses its
`max_input_tokens` for run-time guards. The model's recommended sampling values and image limit were nowhere.

Measured on 2026-10-16 and 2026-10-21 against the dev stack. A model counts as reading images when it named two
unguessable colour sequences of image inputs correctly; accepting images is not enough.

| Model (provider)                  | Images read          | Image limit per request         |
| --------------------------------- | -------------------- | ------------------------------- |
| gemma-4-31B-it (Infomaniak)       | yes, 258 tokens each | 20 (upstream 400 names it)      |
| gemma-4-31B-it (stoney)           | yes, 258 tokens each | none up to 128                  |
| Apertus-70B (Infomaniak)          | yes                  | none up to 128                  |
| Kimi-K2.6 (Infomaniak)            | yes                  | none up to 128                  |
| Ministral-3-14B (Infomaniak)      | yes                  | 10 (upstream 400 names it)      |
| Qwen3.5-122B (Infomaniak)         | yes                  | 20 (upstream 400 names it)      |
| MinerU2.5-2509-1.2B (stoney, OCR) | yes, 6 tokens each   | none up to 128                  |
| Qwen3-VL-30B (local vLLM, GPU)    | yes                  | 8 (our `--limit-mm-per-prompt`) |

## Decision Drivers

- **One source of truth per model**\
  Defaults and limits belong to the model, so they live next to its other facts in the LiteLLM config, not in every
  profile.
- **Existing profiles keep working**\
  Stored values stay what they are; only an unset value changes meaning.
- **A save that cannot work is refused**\
  The admin learns about a limit when choosing the value, not from a truncated or failed run.
- **No new runtime dependency**\
  Values are curated by hand, like the costs and windows already are, not pulled from Hugging Face or LiteLLM's bundled
  map.

## Decision

**Curated `model_info` keys.** `litellm-config.yml.j2` gains three AI-Hub keys per chat model. They are literal numbers,
under the same rule as `max_input_tokens`:

- **`default_temperature` and `default_top_p`:** from the model's `generation_config.json`, or its model card when that
  file sets none.
- **`max_images`:** only where a limit is known, by measurement or by our own vLLM flag.

`supports_vision` is set for every chat model from these measurements. Apertus is served with vision although its model
card describes a text model, and Qwen3.5's earlier `supports_vision: false` was wrong; a model without a measured limit
gets no `max_images`, so its input window bounds it.

**Unset means the model's default.** `LLMParameter.temperature` and the new `top_p` are `float | None`, with `None` by
default. `LLMConfig.to_llama_index` resolves an unset value to the model's curated default:

- An unset temperature falls back to `DEFAULT_TEMPERATURE = 0.0` when the model curates none, the value every model used
  before.
- An unset `top_p` is left to the provider when the model curates none.

Platform-internal callers that need reproducible output (ingestion, translation, mail drafting) use
`LLMConfig.deterministic(model_name)`, so they never pick up a chat-tuned default.

**Helper steps stay at 0.0.** `LLMConfig.as_task_llm` builds the task model for guards, meta-question detection,
question condensation, titles and follow-up questions. It still copies an explicitly set main temperature, but pins an
unset one to `DEFAULT_TEMPERATURE` rather than passing `None` on. Otherwise these classification steps would run at the
task model's chat default (1.0 for gemma) whenever the admin leaves the temperature to the model. The curated default
only ever reaches the main answer.

**Form fields bound to the model picker.**

- **The elements:** `ModelBoundInputNumber` reads its maximum (`max_from`), its default hint (`default_from`) and
  optionally a `fill_factor` from the `model_info` of the model picked elsewhere on the same form. `ModelGatedCheckbox`
  can only be switched on while that model does not declare `requires` false.
- **How they find the model:** each names the picker relative to its own form (`../model_name`), and the rendered form
  carries the path from the root. That is the precedent `KnowledgeCollectionSelector` set for cross-field references.
- **Where they are enforced:** the frontend applies the bounds as the model changes, and `ModelLimitValidator` enforces
  them on every agent and process save. The announced JSON schema cannot carry a bound that depends on another field.

**The input budget is bounded at the share the run fills, and the hint names the window.**

- **The bound:** `number_of_input_tokens` is bounded at `WINDOW_SAFETY_FACTOR` (0.85) of the main model's
  `max_input_tokens` (`ModelBoundInputNumber.maximum_for`). Prompts are counted with tiktoken, so the run fills only 85%
  of the window, and a value between 85% and 100% would behave exactly like 85%.
- **Why not the real window:** an earlier version bounded the field at the window and explained the 85% in the hint.
  Once the unset field showed the 85% figure, ticking the override offered values up to the window that the run never
  uses, so what the admin saw was no longer what applied. The hint now names the 85% bound and the model's full window
  next to it, so the bound is not mistaken for a wrong figure.
- **One source for the factor:** the field declares it as `fill_factor`; the form, `ModelLimitValidator` and the
  migration below all read it from there, so the API holds no copy of 0.85.
- **Where 0.85 comes from:** it is one global value, based on #2077's measurement on English text (Ministral +6%, gemma
  +4%). It is not a per-model fact.

**An unset input limit fills the window.** `number_of_input_tokens` is `int | None`, with `None` by default, and gets
the same override checkbox as the temperature.

- **Unset:** `ConversationFields.input_budget` fills 85% of the narrowest window of the main and the task model, and the
  form shows that figure while the checkbox is off. With no window known, it falls back to
  `FALLBACK_INPUT_TOKENS = 128000`, the value every profile used to be created with.
- **Set:** the admin's own limit, a cost ceiling, bounded at 85% of the main model's window on save.
- **Why not keep a pre-filled number:** any fixed number is either above the window of the smaller models (128,000 is
  above Apertus, Ministral, gemma on Infomaniak and MinerU) or wastes the larger ones, and a pre-filled value above the
  window would block every save of a new profile on a smaller model.
- **Templates** set no limit unless they mean one as a cost ceiling (the 50,000 ones keep theirs).
- **Stored profiles:** `OversizedInputLimitMigration` runs at API startup and unsets every stored limit above its main
  model's bound (85% of its window), which is what such a profile already ran at. A limit within the bound is kept, as
  it may be deliberate, and a model whose window cannot be established leaves its profiles alone until a later start.

**Images are admitted once, in the conversation capability.** `Conversation`'s query step passes the history through
`ImageAdmission` before anything is spent on the turn. Every chat blueprint goes through that step.

- **Earlier turns** lose their oldest images silently until the prompt holds at most `max_images`. If the profile
  switched `accept_images` off, or the model declares `supports_vision: false`, earlier turns lose all their images.
- **The latest message** is never trimmed. If it alone exceeds the limit, or carries images the model may not receive,
  the run ends with a localized refusal (`RefusalReason.TOO_MANY_IMAGES` / `IMAGES_NOT_ACCEPTED`) instead of a model
  call.
- **A model that declares nothing is not held back.** LiteLLM leaves most capability flags unset, so only an explicit
  `false` gates.

## Consequences

- **Agents without a stored temperature answer at the model's recommendation.** For gemma that is 1.0 instead of 0.0;
  their helper steps keep 0.0. Profiles created through the form before this change stored their value and are
  unaffected. Every shipped template sets its temperature explicitly.
- **Adding a chat model means curating more keys.** `default_temperature` and `default_top_p` come from its card,
  `max_images` from a measurement. A missing key degrades to the previous behaviour, never to an error.
- **The provider serving a model decides its image limit.** The same model can need different values per
  `LITELLM_CONFIG_VARIANT`, as gemma does today. Re-probe when a provider changes.
- **A budget saved above the window before this change** is not flagged until the profile is saved again. Until then the
  run caps it to the window, as before.
- **Cross-field form bounds are now a reusable pattern.** A new model-dependent field declares `model_ref` and the
  `model_info` key it reads. The save check picks it up without further wiring.
