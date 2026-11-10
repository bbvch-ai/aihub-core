# Capability- and Location-Aware Model Selection

## Context

A model picker on an agent form (`ModelSelect`) offered every model of one LiteLLM `mode`. An agent whose loop calls
tools could be saved on a model that rejects tool calls, an agent with data-sovereignty constraints could not keep its
picker to Swiss or local models, and the OCR model MinerU, registered as `mode: chat`, was offered to every chat agent
(#1769).

The LiteLLM config already describes each model: `supports_function_calling`, `supports_response_schema`,
`supports_vision` and, since this change, `supports_reasoning`, plus our own `aihub_hosting_location` and
`aihub_general_purpose`. LiteLLM v1.106 returns these in `/v1/model/info` but cannot filter on them: there is no
capability filter, and `allowed_model_region` is deprecated and only knows `eu` and `us`.

## Decision Drivers

- An agent declares what its model must offer once, in code, next to the field it applies to.
- The picker and the save use the same rule, so a value the picker would not offer cannot be saved through the API.
- No migration of stored profiles.
- Operators can add models through the LiteLLM UI (`STORE_MODEL_IN_DB` is on in every stage), where nothing makes them
  set our keys.

## Decision

- **Requirements live on the picker.** `ModelSelect.requirements: ModelRequirements` (core) holds the required
  capabilities and an optional set of allowed hosting locations. Configs pass it through
  `LLMConfig.as_form(requirements=...)` and `ConversationFields.conversation_form_elements(llm_requirements=...)`, which
  apply it to the main `llm` only. The MCP ReAct agent declares `tool_calling` as the reference.
- **Filtering happens in our backend.** `GET /models/mode/{mode}` takes repeated `capability` and `hosting_location`
  query parameters and `include_special_purpose`. The picker sends its requirements; `ModelLimitValidator` checks them
  again when an agent or process profile is saved. Stored profiles that no longer qualify keep running, show "not
  selectable" in the picker and are refused on their next save.
- **`null` is strict here.** A capability counts only when its flag is `true`, and a missing or unknown location fails a
  location requirement. `ModelGatedCheckbox` treats `null` leniently, because it gates a feature on a model already
  chosen; these rules decide what may be chosen.
- **Purpose is ours, `mode` is LiteLLM's.** `mode` is the API contract LiteLLM calls and health-probes a model by.
  MinerU is served over `/chat/completions`, so it stays `mode: chat`: LiteLLM's `ocr` mode means the Mistral-style
  `/v1/ocr` document API and would turn every health probe of MinerU red. Instead `aihub_general_purpose: false` keeps
  it out of every picker and every save, whatever the requirements. A model without the key counts as general-purpose,
  which is what covers models added through the LiteLLM UI; they still fail every requirement they do not declare.
- **No forced-`tool_choice` flag.** Whether a reasoning model honours a forced tool choice depends on the provider's
  vLLM version, not on the model, so it is not something a model declares. `supports_reasoning` only says the model can
  think.
- **Deployment-level model settings are the operator's.** Models named by environment variables (`MEM0_LLM_NAME`,
  `DOCUMENT_INGESTION_*_MODEL`, the translation model, the MinerU VLM) are not form values and are not checked.

## Consequences

- `GET /models/mode/{mode}` no longer returns MinerU unless `include_special_purpose=true`, for every caller. Ingestion
  is unaffected: it reaches MinerU by name.
- A requirement nobody's model meets leaves the picker empty; it shows an empty-state message rather than an error.
- The location half has no shipped consumer yet: no agent declares a location. An agent-wide location policy checked at
  run start is a follow-up.
- `HostingLocation` in core and `HOSTING_LOCATIONS` in `generate_compose.py` must stay in sync by hand.
