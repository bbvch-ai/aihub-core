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
  `@capability("api.access.capabilities.ops.<key>")`, which carries **only** the i18n label/description — mirroring how
  controllers already declare `name`/`description`. The decorator lets the method register its route, then tags that
  route with the metadata.
- Path-parameter guards (`{agent_class}`, `{agent_id}`, `{database}`, `{namespace}`, …) are enumerated across the
  concrete agents/processes/knowledge namespaces; the implicit service gate (`aihub.user.service.<name>`) is synthesized
  from the controller's `service_name`, with "Administer" surfaced when an `aihub.admin.service.<name>` endpoint exists.

Each capability is evaluated against a draft rule set to produce `granted` / `locked` (granted via a broader rule) /
`toggleable`. A `restrict_to_tenant` flag selects the audience: the **role editor** passes the acting tenant's ceiling
so capabilities it cannot grant are pruned from the catalog entirely; the **sysadmin ceiling editor** passes none and
sees the full platform catalog. The same engine renders read-only on the user-detail page (effective access from the
user's resolved rules). Ticking a capability adds its exact rule; broad/wildcard grants (and named presets like
`aihub.admin.>`) render as locked, with the raw rule list retained as the power-user escape hatch.

To keep the sysadmin plane same-origin (see
[sysadmin_api_full_self_contained_lifespan](2026_05_26_sysadmin_api_full_self_contained_lifespan.md)), the capability
and preset endpoints are mounted on `RoleController`, which sysadmin-api already re-mounts.

## Consequences

### Positive

- Operators see and edit access as named capabilities with their exact rules, not opaque strings.
- The catalog cannot drift from enforcement: the guard is the single source of truth for every rule.
- The role editor structurally cannot reveal or grant beyond the tenant ceiling — no leakage.
- One engine powers three surfaces (role editor, tenant-ceiling editor, read-only user view).
- New endpoints self-describe with a one-line `@capability(...)` on their builder method; no rule restated.
- Named presets cover the common broad grants in one click.

### Trade-offs

- Labels/descriptions must be authored: the codebase has effectively no endpoint summaries, so the human text cannot be
  auto-derived — only the rule can.
- The engine depends on reading the guard from the `user_with_permission` dependency closure; a change to how that
  template is captured would require updating the introspection.
- Per-resource enumeration (agents, processes, knowledge namespaces) is custom per resource type rather than fully
  generic.
- Broad wildcard grants are shown as locked and cannot be decomposed into per-resource toggles, so the raw rule list
  remains necessary as a fallback.
- The sysadmin tenant-ceiling editor's catalog is limited to the controllers mounted on sysadmin-api; surfacing the full
  platform catalog there would require pointing those calls at the main API.
