# Correct End-to-End Behaviour of the Dynamic Agent/Process Configuration Form

## Context

The Form Duality system in `packages/core/swiss_ai_hub/core/form/` lets a single Pydantic class double as a form schema
and a typed data model. It powers the dynamic agent and process configuration forms in `packages/web`
(`useFormKitTransform.ts`, `Agent/CreateModal.vue`, `DynamicConfiguration.vue`). Two earlier ADRs established this area:
`2026_01_07_enable_dynamic_agent_configuration_ui.md` (render backend-defined schemas as forms) and
`2026_05_07_nullable_form_fields_over_enabled_toggle.md` (treat `T | None` as the source of truth for an optional
sub-form and synthesize a `__<field>__enabled` toggle in the frontend).

An end-to-end audit of the configuration form (five parallel reviews over backend generation, frontend transform,
create/edit data-flow, round-trip integrity, and custom inputs) surfaced a cluster of correctness defects that all
shared one root: the form's create path and edit path were **two separate implementations** of "schema → hydrated model
→ submitted payload", and several invariants held in one but not the other. Concretely, against a real `RAGAgent`:

- A nullable field with a **non-null default** (`system_prompt`, `context_prompt`, and `org_memory`, which defaults to a
  populated `OrgMemoryReadConfig()`) loaded **enabled** on edit but came up **disabled** on a fresh create, so its
  default was silently dropped at submit. `2026_05_07`'s `seedNullableToggles()` only handled the saved-data case
  (`field !== null`); the fresh-create case was never specified.
- The edit submit never stripped the repeater `__validate__<name>__<index>` mirror keys (only create did), so the two
  endpoints validating the same config sanitized it asymmetrically.
- Repeater rows were keyed by array index (both as the Vue `:key` and inside the per-item FormKit group id), so deleting
  a non-last row reindexed survivors and rebound FormKit groups to the wrong row's data (`[5, 5, 22]` → delete middle →
  `[5, 5]`).
- A `useChangeCase` (VueUse) composable used in selector option resolvers returns a `ComputedRef`;
  `display_name || useChangeCase(name, 'capitalCase')` leaked a `Ref` into PrimeVue/FormKit labels and, because it ran
  inside render computeds, spawned throwaway reactive effects every render — the instability behind intermittently
  blank/broken forms.
- PrimeVue `InputNumber` is integer-only unless fraction digits are configured, so fractional fields (LLM `temperature`,
  step `0.1`) rejected the decimal point.
- `buildFormKitSchema` wrapped the whole element list in one `try/catch` returning `[]`, so a single throwing element
  wiped an entire section (most visibly the Basic Info step, leaving an unsubmittable form).

These are not abstract: each was reproduced live, and each is the kind of regression that the absence of a frontend test
harness (`make test` is a no-op in `packages/web`) lets through silently.

## Decision Drivers

- **One behaviour, not two**\
  The create and edit forms must hydrate and serialize identically. Divergent pipelines are the structural cause of
  "works on edit, broken on create" (and vice-versa); every such pair of code paths is a latent inconsistency.
- **The schema must carry enough to render a fresh form correctly**\
  `2026_05_07` made `T | None` the toggle's source of truth, but the *initial* toggle state on a brand-new form depends
  on whether the field's **data default** is null — information the serialized schema did not preserve. The duality
  pattern requires `as_form()` to always emit a fully-populated `Group` (so children can render when re-enabled), and a
  `Group` extends `FormkitElement`, which has **no `value` field**. So a `None`-default nullable group
  (`reranking_config = None`) and an object-default one (`org_memory = OrgMemoryReadConfig()`) serialize
  **identically**. The frontend cannot infer the difference; the backend — the only place the Pydantic default is
  visible at schema-generation time — must transmit it.
- **Defaults are a contract, not decoration**\
  A field that declares a default must present that default in the form and persist it unless the user changes it.
  Dropping `system_prompt`'s default because a toggle defaulted off is a silent contract violation.
- **Stable identity for list rows**\
  A repeater row's UI identity must track the logical row, not its current array index, or editing one row after
  deleting another corrupts data.
- **Pure functions in render paths**\
  Option/label resolvers run inside Vue render computeds; they must be pure (no reactive-effect allocation, no `Ref`
  leakage into props) to keep rendering stable.
- **Graceful degradation over all-or-nothing**\
  One malformed schema element should drop itself, not the whole form. A config form that can't be submitted because of
  one bad field is worse than one missing field.
- **Symmetric server-side sanitisation**\
  Create and update must normalize submitted config through the same path so neither endpoint is one frontend bug away
  from persisting FormKit artifacts.

## Decision

Make the configuration form correct end-to-end by unifying its pipelines and closing the create-path gap left by
`2026_05_07`, plus targeted fixes for the independent defects found in the same audit.

**1. `default_enabled` signal (backend → frontend).** `FormkitElement` gains `default_enabled: bool | None` (alias
`defaultEnabled`). `Form.to_formkit_form()` sets it on nullable leaves and groups from
`_default_is_non_null(field_info)` (`default is not None and not PydanticUndefined`). The frontend's
`seedNullableToggles()` now falls back to `default_enabled` when a field is **absent** from the source data (a fresh
form), while still using the value's null-ness when it is present (edit/clone). This is the create-path completion of
`2026_05_07`: that ADR specified the saved-data case only. BaseModel defaults (e.g. a `LocaleString` prompt) are
`model_dump()`-ed into the primitive `value` so they no longer trip the Pydantic serializer.

**2. Unify create and edit behind two shared functions** in `useFormKitTransform.ts`:

- `hydrateFormData = seedFormDefaults ∘ seedNullableToggles` — raw saved/template/empty data → hydrated model.
- `serializeFormData = cleanFormData ∘ normalizeFormLocaleStrings ∘ coerceNullableToggles` — model → submission payload.

`useCreateInstanceForm` drops its bespoke `initializeGroupData` / `stripNullsForGroups` / `cleanFormData`;
`DynamicConfiguration` and both create modals call the shared helpers. This removes the create-path default discard and
the edit-path `__validate__` leak in one move.

**3. Stable repeater row keys.** `Repeater.vue` assigns each row a `crypto.randomUUID()` on add/load and keys both the
`v-for` and the per-item FormKit group (`__validate__<name>__<uuid>`) by it. add/remove keep the key array aligned; a
watch reconciles external model replacement. The mirror keys keep the `__validate__` prefix and are still stripped at
submit by `serializeFormData`.

**4. Auto-derive `InputNumber` fraction digits.** `InputNumber` derives `max_fraction_digits` from the field's own
precision (step/min/max/value) when unset, so fractional fields accept decimals while integer fields stay integer-only.

**5. Pure `capitalCase` in resolvers.** Replace `useChangeCase(x, 'capitalCase')` with the synchronous `capitalCase(x)`
from `change-case` across all selector option resolvers and related pages, eliminating the `Ref`-in- label class and
per-render reactive-effect churn.

**6. Per-element error isolation.** `buildFormKitSchema` and the group/repeater extractors wrap each element
individually, so a malformed element is skipped and logged while siblings render.

**7. Symmetric server-side normalisation.** Agent and process **create** endpoints route through
`InstanceConfigHelper.normalize_form_configuration` (which strips FormKit `_`-prefixed keys), matching update.

Deferred, latent/structural items were filed rather than bundled: transform hardening (#1475: `combineConditions` string
surgery, `isLocaleStringObject` heuristic, schema churn, merge-arrays, nested repeaters), backend persistence
canonicalisation (#1476: storing `model_dump()` and de-duplicating identity fields), and a Vitest harness for the
transform layer (#1477).

## Consequences

### Positive

- Create and edit forms hydrate and serialize through one code path, so behaviour is provably consistent and the "works
  in one, broken in the other" class is closed.
- Fresh forms present nullable fields enabled exactly when their data default is non-null; declared defaults are no
  longer silently discarded.
- A disabled nullable group still round-trips as `null` (verified: DB keeps `reranking_config`/`org_memory` null on
  save) with no `__validate__`/`slots` leakage from either endpoint.
- Deleting a repeater row no longer corrupts the surviving rows.
- Fractional numeric inputs accept decimals; one bad element can't blank the form.

### Trade-offs

- `default_enabled` adds a field to `FormkitElement` that is meaningful only for nullable elements. It duplicates, on
  the wire, information the backend already holds — a deliberate cost, because the serialized group schema cannot
  otherwise convey it (see the second Decision Driver). An alternative — inferring from `element.value` for leaves and
  leaving groups unhandled — was rejected as two code paths for one concept.
- The repeater still relies on the `__validate__<field>__<key>` mirror group for per-item FormKit validation; the keys
  are now stable and stripped at submit, but the mirror itself remains (full removal is follow-up).
- The frontend transform layer carries shared `hydrateFormData`/`serializeFormData` conventions and synthetic
  `__<field>__enabled` keys, visible to anyone reading raw `formData` mid-edit. With no Vitest harness yet (#1477) these
  invariants are guarded only by the `packages/core` form tests and manual verification.
- This branch corrected behaviour but did not address the structural persistence smells (dual-stored identity fields,
  raw-vs-`model_dump()` storage) deferred to #1476.
