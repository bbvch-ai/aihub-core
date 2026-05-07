# Use Annotation-Driven Nullable Form Fields Instead of Per-Config `enabled` Toggles

## Context

The Form Duality system in `packages/core/swiss_ai_hub/core/form/` lets a single Pydantic class double as a form schema
(when fields hold `FormkitElement` instances) and a typed data model (when fields hold primitives). Several sub-configs
that wrap an optional capability — `RetrievePrevNextConfig`, `RetrieveSummariesConfig`, `RerankingConfig` — emerged with
a recurring pattern:

```python
class RerankingConfig(Form):
    enabled: Annotated[bool | Checkbox, Field(...)] = False
    reranking_model: Annotated[RerankingModelConfig | None, Field(...)] = None
```

The `enabled` field exists purely to drive a UI toggle. Each dependent field carries
`condition_if="$get(reranking_config_enabled).value"` to hide itself when off, runtime code reads
`config.reranking_config.enabled`, and when toggled off the form still submits a payload like
`{enabled: false, reranking_model: {top_n: 5, ...}}` — dead values that travel over the wire and pollute the runtime
config. The pattern duplicated semantics that Pydantic's `T | None` annotation already encodes ("this whole thing is
optional"), forced every new optional sub-form to repeat the pattern, and leaked UI concerns into the persisted data
model.

The first attempt on `feat/toggle-retrieval-postprocessors` shipped this `enabled`-checkbox pattern on the two retrieval
post-processor configs. Reviewing the diff surfaced the duplication and motivated lifting the toggle into the form
framework itself.

## Decision Drivers

- **Single source of truth for optionality**\
  `T | None` already encodes "this is optional" in the type system. A separate `enabled: bool` field encodes the same
  fact a second time, and the two can drift (e.g. `enabled=true, reranking_model=None` is a valid Pydantic state but
  meaningless at runtime — guarded only by ad-hoc `model_validator`s).
- **Clean wire payload**\
  When the user disables a sub-form, the framework should submit `field: null` rather than
  `field: {enabled: false, ...stale defaults}`. This keeps Mongo documents small, makes diffs in the agent config
  trivial to read, and removes the need for runtime code to interpret an `enabled` flag alongside the value.
- **Eliminate per-config boilerplate**\
  Every nullable sub-form previously needed an `enabled` field, an `as_form()` Checkbox with a unique `ref`, a
  `condition_if` on every dependent element, and i18n strings for the toggle label. The framework approach removes all
  of this from user code.
- **No new abstraction in the data model**\
  The decision deliberately keeps the toggle out of the persisted Pydantic model. Devs who write a `Form | None` field
  get the toggle for free; the data model stays a clean record of what is or isn't configured.
- **Symmetric handling of nullable groups and nullable scalars**\
  A single `nullable: bool` flag on `FormkitElement` lets the same UI affordance work for both `SubForm | None` and
  `int | InputNumber | None`, instead of forcing two parallel patterns.
- **Pre-existing infrastructure already round-trips null**\
  `Form._convert_union_for_submission` already preserves `type(None)`, `Form.deep_merge` already overwrites with `null`,
  and the frontend `cleanFormData` already passes `null` through. The missing piece was only the toggle UI and the
  submit-time coercion — a small framework addition rather than a large refactor.

## Decision

We treat any `Form | None` or `T | None` annotation in a `Form` subclass as the source of truth for the toggle, and
remove every hand-rolled `enabled` field that exists solely to drive that UI affordance.

**Backend** (`packages/core/swiss_ai_hub/core/form/`):

- `FormkitElement` gains a `nullable: bool = False` field on the base class.
- `Form.to_formkit_form()` auto-stamps `nullable=True` on emitted elements when the field annotation allows `None`,
  skipping boolean inputs (`primeCheckbox`, `primeToggleSwitch`) where a tri-state toggle would be meaningless.
- For a `Form | None` field whose form-mode value is `None`, the emitter instantiates a placeholder `Group` from the
  nested `Form.as_form()` template so the user can re-enable a previously-null sub-form.

**Frontend** (`packages/web/swiss_ai_hub_web/composables/form/`):

- When `useFormKitTransform` encounters `element.nullable === true`, it emits a synthetic `__<field>__enabled` Checkbox
  sibling and gates the original element with `if: $__<field>__enabled` (combined with any author-supplied
  `condition_if`).
- `seedNullableToggles()` initialises the synthetic flag from initial data (`<field> !== null && !== undefined`).
- `coerceNullableToggles()` runs at submit time: when the synthetic toggle is off, it sets the field to `null` and
  strips the synthetic key. Both helpers recurse into nested groups and repeater items.

**Migration on the same branch**: drop the `enabled` field from `RetrievePrevNextConfig`, `RetrieveSummariesConfig`, and
`RerankingConfig`; revert runtime guards in `KnowledgeRetriever`, `RetrievalAgent`, `RAGAgent`, and `ExpertRAGAgent` to
plain truthy / `is not None` checks; delete the now-unused `enabled.label` / `enabled.help` keys from the de/en/fr/it
translation files.

Plain-bool toggles that carry independent semantic meaning (`enable_organization_memory`, `enable_user_memory_*`,
`LLMConfig.logprobs`) are **not** in scope — they are real domain flags forwarded to runtime logic or downstream APIs,
not wrappers around an optional sub-form.

## Consequences

### Positive

- Removes ~45 lines of `enabled` boilerplate from three retrieval/reranking configs and unifies them under the framework
  feature.
- Persisted agent configs are cleaner: a disabled retrieval post-processor stores as `retrieve_prev_next: null` instead
  of `{enabled: false, num_nodes: 10, mode: "both"}`.
- Future optional sub-forms get the toggle for free — developers only declare `field: SubConfig | None = None`.
- Runtime code uses idiomatic Python (`if config.retrieve_prev_next:`) rather than reading a bespoke `.enabled` flag.
- The synthetic toggle key (`__<field>__enabled`) lives only in the frontend transform layer, not in the data model or
  on the wire.

### Trade-offs

- The placeholder Group emitted for a `None`-valued sub-form requires the nested `Form` subclass to implement
  `as_form()`. Sub-forms without `as_form()` cannot be re-enabled by the user once null — they would need either a
  default form-mode template or a code change.
- Nullable scalar fields whose form-mode value is also `None` are out of scope: the framework needs *some* element
  instance to attach the toggle to, so devs must still assign a `FormkitElement` in `as_form()` even when the data-mode
  default is `None`.
- Nullable top-level groups extracted by `extractGroupConfigs` (rendered as their own stepper step) do not receive the
  toggle — only nested-group and leaf cases are handled. Real-world configs are nested, so this is acceptable; if
  needed, a follow-up can extend stepper rendering.
- The frontend now carries a small bespoke `__<field>__enabled` convention. It is encapsulated in
  `useFormKitTransform.ts` and `useCreateInstanceForm.ts`, but anyone reading raw `formData` mid-edit will see the
  synthetic keys.
