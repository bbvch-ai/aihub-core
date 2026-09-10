# Model Curation Is a Tenant-Ceiling Policy, Not a Gateway Edit

## Context

Issue #1736 asked to "verify supported models and remove unstable ones" and to standardise the initial configuration for
new tenants/instances. QC's capability report cleared the roster except one model:
`text-generation/Apertus-70B-Instruct-2509`.

The literal reading is to delete that entry from `litellm-config.yml.j2`. Two findings ruled it out.

**A removed model fails hard, with no fallback.** Verified against the running dev proxy:

```
{"error":{"message":"/chat/completions: Invalid model name passed in
 model=text-generation/Apertus-70B-Instruct-2509-GONE. …","code":"400"}}
```

`default_fallbacks` does not rescue it — the rejection happens during model-name resolution, before the router selects a
deployment, so there is no failed deployment call for a fallback to catch. This is the same failure recorded in
[model_gateway_error_translation](2026_08_19_model_gateway_error_translation.md), where a model name the upstream did
not serve simply broke the feature.

**Agent configs pin model names as unvalidated strings.** `ModelSelect` is a *render hint*: it populates a dropdown from
`/api/v1/models/mode/{mode}` when the form renders. The chosen value is stored as a plain string in
`config_data.llm.model_name` and is **never re-validated** — not on save, and not on any later read. An agent pinned to
a removed model therefore looks entirely normal in the database and fails only when it next runs, surfacing as an
`ExceptionEvent` (per
[agent_config_failures_surface_as_exception_events](2026_08_07_agent_config_failures_surface_as_exception_events.md)).

Gateway removal is also instance-wide and needs a redeploy to undo, so it cannot express "new tenants start clean" at
all — the requirement is inherently per-tenant.

## Decision Drivers

- *Existing tenants must not break*\
  Apertus is in use. Any change that hard-fails a running agent is a regression, not a cleanup.
- *The curation must be per-tenant and reversible*\
  "Standard set for new tenants" implies old tenants keep what they have, and that a customer can be granted an excluded
  model later without a deployment.
- *The rule grammar is additive only*\
  `AccessChecker.validate_user_access_rule` rejects every negation form. "Everything except X" is inexpressible; a
  curated ceiling must enumerate survivors.
- *The ceiling caps every rule family*\
  `agent`, `knowledge`, `memory`, `model`, `process`, `service`. A model-only ceiling silently locks a tenant out of
  everything else.
- *CPU and GPU deployments serve different rosters*\
  GPU serves `Qwen3-VL-30B-A3B-Instruct-FP8` and `faster-whisper-large-v3`, no cloud chat models and no flux. A
  hardcoded default list leaves a GPU tenant with **zero** chat models.
- *The sysadmin plane's narrow dependency set is deliberate*\
  `packages/sysadmin-api` has no LiteLLM configuration and constructs no `LiteLLMProxySettings`.

## Decision

**Models are curated by the ceiling a tenant is created with — never by removing them from the gateway.**

**1 — The default ceiling is derived, not hardcoded.** `DefaultTenantAccessRulesService.derive()`
(`packages/api/swiss_ai_hub/api/routes/access/`) reads the live roster via
`AccessCapabilityService.available_models_by_capability()` and emits, per model capability: a wildcard
`aihub.user.model.<capability>.>` when nothing in it is excluded, otherwise one concrete `AccessChecker.model_user_rule`
per survivor. Fixed non-model rules cover the other five families.

Deriving is what makes this hardware-agnostic — the same code yields the right ceiling on CPU and GPU with no per-mode
configuration. The wildcard/enumerate split is deliberate: infrastructure models (embedding, rerank, STT, image) reach
new tenants automatically, while a new **chat** model — the kind QC vets and users pick — needs an explicit grant.

*A `.>` rule does not match its own root.* This is the non-obvious constraint that makes an enumerated ceiling harder to
get right than the single `aihub.admin.>` it replaces. `aihub.admin.knowledge.>` covers every named database but not the
bare `aihub.admin.knowledge`, which is what *creating* one is guarded on — a database that does not exist yet cannot be
named by a rule. `_NON_MODEL_RULES` therefore carries both forms for `knowledge`, exactly as the seeded
`AIHubKnowledgeAdmin` role does. Because a ceiling caps every role beneath it, omitting the root does not merely narrow
a role — it makes the permission unreachable for the whole tenant, and `AccessCapabilityService._capability_for_guard`
*hides* such a row rather than showing it blocked, so the loss is silent.

Getting this right per family by hand is what the family-coverage guard failed to catch, because the gap was one of
*depth*, not of family. `test_the_derived_ceiling_permits_every_route_guard` therefore reads the guards off the real
mounted routes via `AccessCapabilityService._route_template` and asserts the derived ceiling permits each one — the same
"derive it, do not restate it" principle the model half already follows.

**2 — Policy lives in exclusions, not an allow list.** `TenantDefaultAccessSettings.EXCLUDED_MODELS`
(`AIHUB_TENANT_DEFAULT_ACCESS_EXCLUDED_MODELS`, default `text-generation/Apertus-70B-Instruct-2509`). An allow list
would have to be maintained per hardware mode; the exclusion is the same policy on both. An exclusion the roster does
not serve **warns and is ignored** rather than failing — legitimate on a mode that never served it.

**3 — It is a seed, read once.** The setting is consulted only while computing a new tenant's starting ceiling.
Afterwards the tenant's `access_rules` is the sole authority, so granting an excluded model later is an ordinary
access-rule edit and the setting has no say in it.

**4 — The sysadmin plane proxies rather than gaining a gateway dependency.** `create_tenant_metadata` and the
form-prefill endpoint call the platform API through `PlatformAccessProxy` — the pattern `SysadminAccessController`
already uses. `AIHUB_INTERNAL_API_BASE_URL` is already configured, so this adds no infrastructure. Resolution happens in
the controller (HTTP-layer work needing a `Request`) and **before any side effect**, so a gateway failure leaves the
tenant Unconfigured and retryable rather than half-built.

**5 — `access_rules` is nullable, and the distinction is load-bearing.** Omitted means "this instance's standard set";
an explicit `[]` means a tenant that deliberately starts with no access. Defaulting to `[]` would have collapsed the two
and removed the ability to create a locked-down tenant in one step.

## Consequences

**Enumerating is what makes models toggleable.** A capability row is a real checkbox only when its own concrete rule is
present — `locked = granted and rule not in granted_rules`, and a locked row cannot be toggled off. Because every tenant
ceiling was previously `aihub.admin.>`, **no model could be unticked at all**. After this change, in the sysadmin's
tenant-ceiling editor:

| Row                              | `granted` | `locked` | Result                         |
| -------------------------------- | --------- | -------- | ------------------------------ |
| the surviving chat models        | true      | false    | ticked, can be unticked        |
| the excluded model               | false     | false    | empty checkbox — tick to grant |
| embedding / rerank / STT / image | true      | true     | ticked and locked, as before   |

Inside the tenant, a tenant admin editing a *role* never sees the excluded row — `_capability_for_guard` returns `None`
for anything the ceiling cannot grant, "hidden, never merely disabled".

**Accepted limitations**

- *The stored ceiling is an enumerated snapshot.* With no deny syntax, "all chat models except X" cannot be persisted as
  a live rule, so a chat model added later does not appear for tenants created earlier.

- *Two classes of tenant coexist.* Existing tenants keep `aihub.admin.>` and continue to auto-inherit new models, until
  someone migrates them. Out of scope here, and the reason nothing breaks.

- *This is a permission control, not a hard block.* The model stays served and callable by anyone permitted, and
  sysadmins bypass the ceiling entirely. If a model must become genuinely unreachable, that is gateway removal — and it
  must be preceded by a check for agent configs pinned to it, because nothing else will catch them.

- *Unticking does not stop a running agent.* Model access is enforced on the plain-LLM chat path, the model listing, and
  the OpenWebUI grant computation — never in the agent runtime, which calls LiteLLM with whatever its config names. This
  is the same property that makes the change non-breaking and the reason unticking is not an enforcement boundary.

- *The startup tenant now reads the roster on first boot.* `AIHUB_STARTUP_TENANT_ACCESS_RULES` defaults to empty,
  meaning "derive". That puts a network call inside `initialize_startup_tenant`, which is **not** wrapped in
  `_provision_non_fatal` — so on the first boot of a brand-new instance, an unreachable gateway fails API startup
  outright rather than degrading. `restart: always` recovers it once LiteLLM is healthy, and the early return makes the
  window unreachable on every later start. Naming the rules explicitly opts out of the lookup entirely, which is the
  escape hatch for a deployment whose gateway is not reachable at boot.

  A `depends_on: litellm: service_healthy` on `api` was considered and **rejected**: it would have bought an ordered
  first boot at the price of the API refusing to start whenever LiteLLM is unhealthy, on every start of every
  deployment, despite serving threads, users, roles and the admin UI perfectly well without it. Ordering containers is
  the wrong layer for this — the underlying fragility is the bare `await initialize_startup_tenant()` in
  `lifetime_manager`, sitting outside the `_provision_non_fatal` wrapper its neighbours use. That call could already
  take startup down before this decision (a duplicate tenant name does it) and is not made materially worse by it.
