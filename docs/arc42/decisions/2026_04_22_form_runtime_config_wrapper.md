# Separate Form-Duality Config from Per-Run Runtime Overrides via a Plain `BaseModel` Wrapper

## Context

The Swiss AI Hub agent framework uses a single `Form` subclass for both rendering (each field typed as
`T | FormkitElement`) and data submission (each field typed as `T`). This duality is established for design-time agent
configuration: what the admin sees in the UI, what the agent receives at runtime. The form schema is published to the UI
through agent discovery and stored in MongoDB as the profile's configuration.

The RAG metadata filtering work (`feat/rag-metadata-filtering`) introduced a category of data that does not fit this
model: **per-run overrides supplied by the publisher of a `StartEvent`**. Concretely, a publisher sending
`RAGStartEvent` can attach `additional_filters`, and these filters must reach the retrieval step as part of a
retriever's configuration. But they differ from every previous kind of config field in three ways:

1. **They are not design-time**. The admin never configures them via the Admin UI — they are set per run by whoever
   publishes the start event (a chat client, an orchestrating process, another agent).
2. **They must not appear in the discovery-published form schema**. The form schema is how the UI decides what to
   render. Exposing publisher-only fields there would be a category error: the admin should not be editing a field whose
   values come from somewhere else entirely.
3. **They require validation against the admin-configured whitelist** (`allowed_metadata_filter_fields`). The admin
   controls *which* filter keys are permitted; the publisher controls *which of those* are active for this run.
   Collapsing both into one config object conflates these concerns.

Two options existed. (a) Add runtime fields directly onto `KnowledgeRetrieverConfig` (which inherits `Form`) and teach
the form-extraction machinery to hide them from the rendered schema. (b) Keep `KnowledgeRetrieverConfig` as a pure
design-time `Form` and wrap it in a plain Pydantic `BaseModel` that carries the design-time config alongside per-run
overrides. Option (a) pushes two orthogonal concerns into one class and requires every code path that reads "the config"
to know which fields are real config and which are runtime-only. Option (b) keeps the form unchanged and gives every
downstream step a single runtime-shaped input that already has the overrides threaded through.

## Decision Drivers

- **Form schema integrity**: The JSON schema published via agent discovery must describe exactly what the admin UI can
  configure. Adding publisher-only fields to a `Form` subclass risks them leaking into the rendered schema, the stored
  profile document, or the admin's view of "what this agent does".
- **Separation of trust boundaries**: Admin-configured fields and publisher-supplied fields have different trust
  properties. The admin's data is authored within the platform's auth boundary and audited; the publisher's data comes
  from outside and must be validated against the admin's whitelist. A single type that holds both conflates those
  boundaries.
- **No reuse through inheritance**: `RetrievalRuntimeConfig` is not a kind-of `KnowledgeRetrieverConfig` — it is a
  pairing *of* one. Using composition keeps the "has-a" relationship explicit and avoids the Form registry from
  accidentally registering a runtime wrapper as if it were a form.
- **Minimal churn to the form system**: The Form base class, the form element registry, and the discovery schema
  generation all remain unchanged. New patterns that want the same split can adopt it by wrapping, without touching
  shared infrastructure.
- **Test ergonomics**: Runtime narrowing logic (`narrow_retrievers`) can be tested with plain Pydantic models, without
  instantiating a form or exercising the discovery pipeline.

## Decision

**When per-run runtime overrides must be paired with a design-time `Form`-based config, introduce a plain Pydantic
`BaseModel` wrapper that holds the `Form` subclass as one field and the overrides as sibling fields. Do not add the
overrides to the `Form` subclass itself.**

Shape of the wrapper:

```python
class RetrievalRuntimeConfig(BaseModel):
    config: Annotated[KnowledgeRetrieverConfig, Field(...)]
    additional_metadata_filters: Annotated[
        list[MetadataFilterPair],
        Field(default_factory=list, description=...),
    ]

    @classmethod
    def from_config(cls, config: KnowledgeRetrieverConfig) -> Self:
        return cls(config=config)
```

Rules for the pattern:

- The wrapper **must not** inherit from `Form`. `Form` subclasses are the form registry's concern and participate in
  discovery-published schemas; the wrapper is a runtime-only data envelope.
- The wrapped `Form` subclass **must not** gain publisher-only fields. Its schema is the admin contract; keep it that
  way.
- A `from_config` classmethod provides a default-wrapper constructor for code paths that have no overrides to apply
  (e.g. start events that are not `RAGStartEvent`).
- Runtime validation (e.g. whitelist enforcement via `allowed_metadata_filter_fields`) lives in the function that
  produces the wrapper (`narrow_retrievers`), not on the wrapper itself. The wrapper is a data carrier, not a validator
  — the validation belongs with the transition from "publisher input" to "runtime-ready config", which is conceptually
  different from "is this wrapper well-formed".
- Steps that consume the configuration accept the wrapper (`RetrievalRuntimeConfig`), not the underlying `Form`
  subclass. This makes the presence of runtime overrides visible in the step signature.

## Consequences

### Positive

- The form schema published via agent discovery stays a faithful description of the admin UI — no publisher-only fields
  leak into the discovery payload or the admin form.
- Admin-controlled and publisher-controlled data are distinguishable by type, not by convention. A reader of
  `narrow_retrievers` sees `KnowledgeRetrieverConfig` (admin) on one side and `list[BucketMetadataFilters]` (publisher)
  on the other; the wrapper is what fuses them.
- The pattern generalizes without touching shared infrastructure. Future agents with the same need (per-run memory
  overrides, per-run tool overrides) can add their own `*RuntimeConfig` wrappers without changing the Form base class.
- Unit tests for narrowing logic do not require a form fixture or a discovery pipeline; they can instantiate plain
  models.
- Whitelist validation is colocated with the code path that creates the wrapper, which is the only point where admin
  configuration and publisher input meet — a natural place for a trust-boundary check.

### Trade-offs

- Step signatures gain one level of indirection (`cfg.config.field` instead of `cfg.field`). Mitigated by the wrapper
  being shallow and the indirection being load-bearing: it makes the split visible.
- Future contributors must learn the rule: *if it's admin-configured, put it on the `Form` subclass; if it's
  publisher-supplied at runtime, put it on the wrapper.* This ADR exists to document that rule.
- Overrides are additive only. The wrapper does not replace, remove, or reshape fields of the wrapped config — it
  carries sibling values that downstream code (e.g. `retrieve_nodes`) composes with the config's own fields. Override
  semantics that would rewrite a wrapped field (e.g. shrinking `index_namespaces` to the publisher's selection) belong
  to the transformer that builds the wrapper (`narrow_retrievers` uses `model_copy(update=...)` on the wrapped config
  for this) — not to the wrapper itself.
- The split creates two types in the public interface where one existed before. Treat the wrapper as the runtime-facing
  type for downstream code and the `Form` subclass as the configuration-facing type — do not use both interchangeably.

### Related Decisions

- No predecessor ADR covers the Form duality itself; this ADR is the first time the runtime-override concern has been
  separated from it.
- `2026_02_17_agent_profile_templates.md` — Agent blueprint vs. profile separation (orthogonal: this ADR is about a
  single profile's runtime overrides, not about the blueprint/profile split).
