# Ingestors Announce Their Configuration Form the Way Agent Classes Do

## Context

`2026_06_18_rag_pipeline_route_per_run` made a deployed ingestion pipeline advertise itself to the API through a
registration record carrying an id, a display name and a description, so the pipeline dropdown in the create-database
dialog is discovered at runtime. `2026_08_31_per_database_models_and_embedding_contract` then let each knowledge
database choose its text and embedding model — as two fixed columns on `BucketEntity`, two fixed fields on
`CreateDatabaseRequest`, and two hand-written selects in `Knowledge/Database/CreateModal.vue`.

Every further knob a pipeline needs therefore costs a request field, an entity column, a UI control and an SDK
regeneration inside the platform: a crawl depth for the web-scrape pipeline (#1606), a source connection for the sync
pipeline (#1721), the per-database enrichment flags (#1821), a vision model (#1819). The platform owns knobs that belong
to a pipeline, and a deployment's own pipeline cannot add one at all.

Agent classes solved exactly this problem once already. An `AgentConfig` is a Form-duality class; the runner publishes
its rendered form and a JSON schema over discovery; the API stores both, validates every instance submission against the
schema with jambo, and walks the form for authorization; the frontend renders the elements generically. None of that is
agent-specific except its names.

## Decision Drivers

1. **A pipeline's knobs belong to the pipeline.** Adding one must be a declaration in the pipeline's own code, with no
   change to the API, the UI or the SDK — the same contract agent blueprints enjoy.
2. **One form machinery, not two.** The Form-duality stack (`Form`, the FormKit transform, `ModelCreationService`,
   `InstanceConfigHelper`, `ConfigAuthorizationService`, `useCreateInstanceForm`) is the platform's way of turning a
   Pydantic class into a validated, rendered, localized form. A second mechanism for ingestors would diverge from it.
3. **What is offered is what is running.** An ingestor the API knows about but no pipeline serves would accept databases
   nobody ingests.
4. **Existing databases keep ingesting unchanged.** Rows created before a knob existed carry no value for it and must
   keep behaving exactly as before, without re-embedding anything.
5. **The vector-dimension contract stays enforced at the API boundary.** A model that cannot declare its width must be
   refused before a database is bound to it.

## Decision

**Ingestors announce a configuration form and schema; a knowledge database stores one configuration object validated
against them; the platform renders and validates generically.**

1. **`IngestorConfig(Form)`** in `packages/core` mirrors `AgentConfig`: it owns the identity fields `name` and
   `description` as `LocaleInput`s (so databases become multilingual, like agent profiles) and an `as_form()` that
   subclasses extend. The shipped `DocumentIngestionConfig` in `packages/pipeline` declares the text, embedding and
   vision model pickers and the three enrichment flags, pre-filled with the deployment's defaults.

2. **The registration record carries form and schema.** `Ingestor.from_config()` produces both surfaces from one
   form-mode config, exactly as `AgentRunner` does — `to_formkit_form()` and `ConfigSpecs.from_form()` — and
   `IngestorEntity` stores them the way `AgentClassEntity` does (alias-free element dicts, schema as a JSON string).

3. **The agent-named schema helpers are lifted to generic names.** `AgentConfigSpecs`/`ProcessConfigSpecs` become
   `ConfigSpecs` (`core/form/config_specs.py`), their entities become `ConfigSpecsEntity` (`core/persistence/form/`),
   and `ModelCreationService.create_config_model` serves agents, processes and ingestors. The attribute
   `agent_config_specs` / `process_config_specs` on the class entities and DTOs keeps its name.

4. **The shipped pipeline registers like any custom one.** The API has no built-in ingestor any more: platform labels
   move from the API's i18n into `lib.ingestors.document_ingestion.*` in core and travel on the row.
   `IngestorType.selectable()` is gone; an ingestor is selectable when a pipeline has registered it.
   `document_ingestion` leaves the reserved-id set; the inert and frozen tokens (`unassigned`, `default_rag`,
   `shared_rag`) stay reserved.

5. **`BucketEntity.configuration`** (a dict) replaces the `llm_model` and `embedding_model` columns.
   `BucketEntity.carry_over_retired_model_columns()` moves existing values into the object and unsets the columns; the
   API runs it at start and the pipeline on every registration tick — the repo's reconcile-on-startup pattern, since it
   has no migration runner.

6. **`create_database` mirrors `create_agent_instance`.** It looks the ingestor up, builds the model from the announced
   schema, validates with `InstanceConfigHelper` (a mismatch is a 400 naming the field path), walks the form for
   authorization, and additionally checks every announced `ModelSelect` value against LiteLLM: mode match, tenant model
   access, and a declared `output_vector_size` for embedding pickers. The API never learns a pipeline's field names; it
   knows which elements are model pickers. `name`/`description` land on the row, everything else in `configuration`.

7. **The pipeline reads one resolved config per run.** `ingestor_config_for_bucket` merges the stored object over the
   deployment defaults; every per-database reader (`llm_model_name_for_bucket`, `vision_model_name_for_bucket`, the
   enrichment flags) derives from it. The asset graph is the same for every database — the summary asset, table
   refinement and figure descriptions always exist — and each enrichment op decides per run whether it has work to do.
   Table refinement and summaries use the database's own text model; figure descriptions use its vision model, falling
   back to its text model.

8. **The create dialog is the agent create dialog.** `Knowledge/Database/CreateModal.vue` is built on
   `useCreateInstanceForm` with the ingestor list as the class list, renders the announced form through the FormKit
   transform with one step per group and repeater, and submits `serializeFormData(...)` as `configuration`. The database
   name stays a path parameter and a plain input, since it is the storage identifier and the reserved-name check runs on
   it.

## Consequences

### Positive

- A pipeline adds a knob with a field on its config class; it appears in the dialog, is validated by the API and lands
  in the database's configuration without any platform change. #1606, #1721 and #1821 have their mechanism.
- Two deployed ingestors with different forms coexist, each database held to its own ingestor's schema.
- Groups, repeaters, nullable toggles, model pickers, locale inputs and every other form element work for ingestors
  because the stack is shared, not copied.
- Enrichment flags, the table-refinement model and the vision model are per database (#1821, #1818, #1819), read per
  run, with no redeploy to change them.
- Knowledge databases carry multilingual names and descriptions, like agent profiles.

### Trade-offs

- **Nothing is offered until a pipeline registers.** The dropdown is empty until the ingestor's sensor has ticked once
  after a first deploy (it runs at code-location load); a dev stack whose pipeline is down offers no ingestor. This is
  deliberate: the alternative accepts databases nobody would ingest.
- **A registration without a form is not offered.** A row left by a pre-announcement pipeline image carries labels but
  no schema; `IngestorEntity.all()` skips it and `create_database` rejects it, rather than rendering an empty form whose
  submission nothing could validate. It becomes usable on that pipeline's first tick after its own upgrade.
- **The retired columns are carried over by whichever side starts first.** The API runs the carry-over at start and the
  pipeline on every registration tick, so a pipeline image that rolls before the API still reads legacy rows correctly.
- **The embedding model is a configuration key, not a column.** `configuration["embedding_model"]` becomes the
  cross-package contract the retriever will read for #1820. The query side still does not honour it; the write-path-only
  enforcement noted in `2026_08_31_per_database_models_and_embedding_contract` stands.
- **The vision picker is unfiltered.** It offers every chat model; capability filtering stays with #1769, and in the
  cloud LiteLLM configs only the OCR model currently declares vision support anyway.
- **Description is required.** The form requires both identity fields, as the agent form does; the previous dialog
  treated description as optional. Consistency with the shared stack won over the old behaviour.
- **A schema rename touches stored agent and process classes.** `ConfigSpecsEntity` reads the renamed field
  `config_schema_json`; rows discovered before this change read an empty schema until the next discovery cycle (seconds
  after the API starts), during which an instance save would be validated against nothing. Registration self-heals; no
  migration was added for a window that short.
- **The generic-configuration-per-run `DocumentIngestionPipelineSettings` and the definitions factory defaults are two
  places.** The factory's arguments pre-fill the announced form; the settings are the run-time fallback for rows that
  store nothing. The shipped app feeds the same settings into both, so they agree; a custom deployment that passes
  different factory arguments than its environment declares would see the form pre-filled with one and legacy rows
  falling back to the other.

## Related Decisions

- `2026_06_18_rag_pipeline_route_per_run` — the registration record this extends, and why it goes through Mongo.
- `2026_08_31_per_database_models_and_embedding_contract` — the two columns this retires; its dimension contract is kept
  and enforced on the announced `ModelSelect` elements instead.
- `2026_01_07_enable_dynamic_agent_configuration_ui` and `2026_06_15_correct_dynamic_config_form_behaviour` — the
  Form-duality stack reused here.
