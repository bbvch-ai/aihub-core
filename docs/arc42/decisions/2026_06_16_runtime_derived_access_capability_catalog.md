# Runtime-Derived Access Capability Catalog

## Context

Authorization in Swiss AI Hub is expressed as hierarchical dotted access-rule strings —
`aihub.[user|admin].<resource>.<subresource>.<id>` with `*` (one segment) and `>` (tail) wildcards — evaluated by
`AccessChecker` against a two-tier model: a tenant ceiling caps the union of a user's role grants (see
[tenant_scoped_roles](2026_04_14_tenant_scoped_roles.md),
[sysadmin_implicit_admin_access](2026_04_15_sysadmin_implicit_admin_access.md)).

The model is expressive but opaque to the operators who actually author it. Tenant admins editing roles and sysadmins
editing a tenant's ceiling typed raw strings into a free-text box (e.g. `aihub.admin.agent.WeatherAgent.>`), with no
feedback on what they grant; the user-detail page showed only a flat list of resolved resources. Operators could not
answer "if I grant this, what can the user actually do?" — and crucially, the difference between creating an agent class
(`aihub.admin.agent.ClassX`), using all its instances (`aihub.user.agent.ClassX.>`), and administering them
(`aihub.admin.agent.ClassX.>`) is invisible in the raw strings.

We wanted a human-readable catalog of grantable capabilities — per service, agent and process — that operators can see
and toggle, **without that catalog drifting from the access rules the endpoints actually enforce**.

## Decision Drivers

- *Operator comprehension*\
  The dominant cost was not the model's power but its legibility. A capability needs a plain-language label ("Create
  instances", "Configure & delete") and its exact access string side by side.
- *Single source of truth — no drift*\
  The set of grantable capabilities and their rules must come from the endpoints' real `user_with_permission` guards. A
  separately maintained mapping would silently diverge from the routes as the API evolves.
- *No information leakage*\
  When editing a role, the editor must not reveal — let alone offer — capabilities the tenant's ceiling cannot grant.
  Showing an agent the tenant has no access to is a real leak, not just a dead toggle.
- *Reuse across surfaces*\
  The same catalog must drive the role editor (filtered by the tenant ceiling), the sysadmin tenant-ceiling editor (full
  platform catalog), and a read-only "effective access" view on the user page.
- *Minimal per-endpoint authoring burden*\
  Adding an endpoint should not require restating its access rule anywhere; the only authored artifact should be the
  human label.

## Decision

Introduce an `AccessCapabilityService` (`packages/api/.../routes/access/`) that builds the catalog by **introspecting
each controller's routes at runtime**:

- For every `TenantScopedController` route it reads the `user_with_permission` template out of the route's dependency
  closure — the guard the endpoint actually enforces.
- **The access rule is derived from that guard, never restated.** A guard with no `?` is itself a concrete grant
  (`aihub.admin.agent.{agent_class}`); a guard containing a `?>`/`?*` query has no single satisfying rule, so its
  capability is **read-only** (shown, not toggleable). This makes divergence between the catalog and the enforced guard
  structurally impossible.
- Endpoints opt into the catalog by annotating their **fluent builder method** with
  `@access_catalog_entry(i18n_path="api.access.capabilities.ops.<key>")` (the decorator lives in
  `packages/api/.../decorators/`, not under `routes/`), which carries **only** the i18n label/description — mirroring
  how controllers already declare `name`/`description`. The decorator lets the method register its route, then tags that
  route with the metadata. Opting in is deliberate: controllers whose access is not a per-operator grant decision — the
  chat/thread, token, notification, file, model and OpenAI-compatibility surfaces — carry no `@access_catalog_entry`
  annotation and simply do not appear in the catalog. Their service-level gate still surfaces once any resource
  capability exists; they are absent because there is nothing meaningful for an operator to toggle, not by oversight.
- Path-parameter guards (`{agent_class}`, `{agent_id}`, `{database}`, `{namespace}`, …) are enumerated across the
  concrete agents/processes/knowledge namespaces; the implicit service gate (`aihub.user.service.<name>`) is synthesized
  from the controller's `service_name`, with "Administer" surfaced when an `aihub.admin.service.<name>` endpoint exists.

Each capability's `granted` flag is evaluated by calling **the subject's own `AccessChecker.has_access` — the same call
the endpoint's guard makes at request time** — so the table matches enforcement exactly, the sysadmin short-circuit and
the tenant-ceiling cap included. There is no parallel matcher: the catalog rides on the authorization engine rather than
re-deriving access from rule strings, so neither the rule *nor* the grant decision can drift. `locked` (granted via a
rule broader than the one this checkbox would add) and `toggleable` are then read off the draft rule set.

Who the `subject` and `ceiling` are selects the audience: the **role editor** evaluates the draft rules under the acting
tenant's ceiling, which prunes — never merely disables — capabilities the ceiling cannot grant; the **sysadmin ceiling
editor** drops the ceiling to show the full platform; the **user-detail page** renders read-only against the viewed
user's effective access, including the `AIHubSysAdmin` short-circuit (a sysadmin holds admin via the realm role, not via
rules, so the catalog must evaluate it as such, otherwise it shows nothing). Crucially, the two privileged selectors —
dropping the ceiling and evaluating as a sysadmin — arrive as request fields but are **gated on the authenticated
identity, never trusted from the body**: only an acting sysadmin may wield them, so a tenant role-admin cannot set them
to enumerate the platform beyond its own tenant. Ticking a capability adds its exact rule; broad/wildcard grants (and
named presets like `aihub.admin.>`) render as locked, with the raw rule list retained as the power-user escape hatch.

The capability and preset endpoints live on a dedicated `AccessController` (`/access/capabilities`, `/access/presets`),
which sysadmin-api re-mounts so the sysadmin plane stays same-origin (see
[sysadmin_api_full_self_contained_lifespan](2026_05_26_sysadmin_api_full_self_contained_lifespan.md)).

**Catalog completeness on the sysadmin plane via a server-to-server proxy.** Because `packages/api` is consumed as an
SDK, every deployment mounts its own subset of controllers — the sysadmin API mounts a deliberately lean slice (user,
role, identity, auth-provider). Introspecting *its* runner would therefore report a misleadingly narrow catalog, yet the
sysadmin tenant-ceiling editor must show the **full** platform surface. Only the main API authoritatively knows what it
serves, and that is deployment-dependent — so it cannot be resolved by importing controllers. The main API's
`AccessController` therefore builds the catalog locally with no proxy branch; the sysadmin plane instead mounts a
`SysadminAccessController` subclass that **overrides** the two endpoints to proxy the caller's request server-to-server
(forwarding the bearer token and locale) to the main platform API, returning the same DTOs. It learns the authoritative
URL from its runner — `SysadminApiRunner.platform_api_base_url` resolves to the main API's internal URL
(`AIHubSettings.INTERNAL_API_BASE_URL` — `http://api:8000` in compose, `http://localhost:8000` in local dev). Keeping
the override and its `PlatformAccessProxy` wholly inside the sysadmin package means the main API and the shared
controllers carry no proxy concern, while the sysadmin web app stays purely same-origin against sysadmin-api.

## Consequences

### Positive

- Operators see and edit access as named capabilities with their exact rules, not opaque strings.
- The catalog cannot drift from enforcement: the guard is the single source of truth for the rule, and `granted` is the
  guard's own `has_access` verdict — there is no second access-matching code path to keep in sync.
- The role editor structurally cannot reveal or grant beyond the tenant ceiling, and the two privileged audience
  selectors (drop-the-ceiling, evaluate-as-sysadmin) are gated on the acting identity — so neither a missing ceiling nor
  a forged request field leaks the platform surface to a non-sysadmin.
- One engine powers three surfaces (role editor, tenant-ceiling editor, read-only user view), sysadmin-aware on the
  last.
- New endpoints self-describe with a one-line `@access_catalog_entry(...)` on their builder method; no rule restated.
- Named presets cover the common broad grants in one click.
- The sysadmin tenant-ceiling editor shows the full platform catalog by proxying to the main API, so it reflects exactly
  what that deployment serves — without the sysadmin plane having to mount every controller or hardcode the surface.

### Trade-offs

- Labels/descriptions must be authored: the codebase has effectively no endpoint summaries, so the human text cannot be
  auto-derived — only the rule can.
- The engine depends on reading the guard from the `user_with_permission` dependency closure; a change to how that
  template is captured would require updating the introspection. A regression test asserts a real guarded route stays
  discoverable, so such a change fails loudly rather than silently dropping rows.
- Per-resource enumeration (agents, processes, knowledge namespaces) is custom per resource type rather than fully
  generic.
- Broad wildcard grants are shown as locked and cannot be decomposed into per-resource toggles, so the raw rule list
  remains necessary as a fallback.
- The sysadmin tenant-ceiling editor's full catalog depends on the main API being reachable from the sysadmin plane (a
  server-to-server hop over the shared Docker network, predictable per deployment). If the main API is not deployed
  alongside the sysadmin plane, the editor cannot enumerate the platform surface — the trade-off for not duplicating the
  controller set or hardcoding it.
