# Creating an Agent Instance Auto-Grants Per-Instance Access to the Creator

## Context

Agent access is governed by hierarchical rule strings (`aihub.[user|admin].agent.<class>.<id>`) evaluated by
`AccessChecker` as the **minimum** of two tiers: the **tenant ceiling** (`TenantMetadataEntity.access_rules`) and the
**creator's roles** (the union of `RoleEntity.access_rules` for the roles the user holds in the tenant, resolved via
`UserTenantRoleEntity`). Per ADR `2026_04_14_tenant_scoped_roles`, access rules live only on shared, named,
tenant-scoped roles — there is no per-user rule store. Per ADR `2026_04_15_sysadmin_implicit_admin_access`, sysadmins
bypass both tiers.

Agent instances (`AgentConfigEntityDocument`, keyed by `(agent_class, agent_id)`) do not belong to a tenant at the data
layer; tenant isolation is enforced entirely through the access rules. In deployments that restrict agents per instance,
a tenant has **no** access to an instance by default — each one must be granted explicitly.

This created a self-service gap: to create an instance a tenant admin only needs `aihub.admin.agent.<class>`
(class-level, no id). But that concrete rule does **not** match the longer `aihub.admin.agent.<class>.<id>` —
`AccessChecker` requires equal segment counts unless a `*`/`>` wildcard is present. So immediately after creating an
instance, the same admin was blocked from opening, editing, deleting, or chatting with it until a sysadmin manually
added the instance rule in tenant management. A tenant admin could create an instance they were not allowed to use.

## Decision Drivers

- **Self-service creation**\
  A tenant admin who can create an instance must be able to use it immediately, with no sysadmin step in between. This
  is the core requirement driving the change.
- **Tenant isolation preserved**\
  The grant must only ever cover the single instance in the creating tenant. Broad grants or cross-tenant sharing would
  break the isolation that per-instance access exists to provide; cross-tenant sharing stays a deliberate sysadmin
  action.
- **No per-user rule store exists**\
  Because access rules attach only to shared roles (ADR `2026_04_14_tenant_scoped_roles`), granting a single user
  instance access without leaking it to everyone holding a broad role requires a dedicated role for that instance.
- **No redundant rules**\
  When the tenant ceiling already covers the instance through a wildcard (e.g. `aihub.admin.>`), adding an explicit
  per-instance rule would be noise that accumulates over the platform's lifetime.
- **No half-created state**\
  If the access grant fails, the platform must not be left with an instance its creator cannot use. Creation either
  fully succeeds or rolls back.
- **OpenWebUI stays in sync**\
  `AccessChangeHook` re-syncs OpenWebUI access from MongoEngine `post_save`/`post_delete` signals on the access
  entities. Grants must therefore go through `.save()`/`.delete()` (read-modify-write), never atomic `update()`, or chat
  access in OpenWebUI would drift.

## Decision

**Creating an agent instance automatically grants the creator per-instance admin access at both tiers, scoped to that
single instance; deleting the instance removes those grants across all tenants.** The admin rule
`aihub.admin.agent.<class>.<id>` is used throughout — admin implies user in `AccessChecker`, so one rule unlocks open +
chat (user-level) and edit + delete (admin-level).

### Tenant tier — conditional

The instance rule is added to the creating tenant's `TenantMetadataEntity.access_rules` **only if not already covered**
by an existing rule (checked via `AccessChecker.rules_grant_admin_to_agent`). When a broader wildcard already grants
access, the add is skipped. Append is idempotent.

### User tier — always

A dedicated per-instance role `agent-<class>-<id>-admin` (rules `["aihub.admin.agent.<class>.<id>"]`) is created in the
creating tenant and assigned to the creator via `UserTenantRoleEntity.add_roles`. This is **always** done — it gives the
specific creator instance access without widening any shared role. Role creation and assignment are idempotent (reused
if present; assignment is a set union).

### Cleanup on delete

Because an instance is globally unique, deletion removes both `aihub.user.agent.<class>.<id>` and
`aihub.admin.agent.<class>.<id>` from **every** tenant ceiling that holds them, and deletes the
`agent-<class>-<id>-admin` role wherever it exists (cascading the role off all `UserTenantRoleEntity` rows). Broad
wildcard rules and shared default roles are untouched.

### Failure handling

If any grant step fails, the orchestration compensates in reverse — revoke the tenant rule, delete the per-instance
role, delete the just-saved config — and returns a clear error, so no half-created instance survives.

### Scope of "rename"

The instance key `(agent_class, agent_id)` is immutable: the update endpoint only changes `config_data` and
name/description/icon, and there is no rename endpoint. The only way to change an instance's id is delete + create, both
of which are already covered. A future rename feature would have to move the grant and role.

### Implementation

- `AccessChecker.rules_grant_admin_to_agent(rules, agent_class, agent_id)` — coverage check reused for the conditional
  tenant grant.
- `TenantMetadataEntity.grant_access_rule` / `revoke_access_rule_from_all_tenants` — idempotent append / cross-tenant
  removal, both via `.save()`.
- `RoleEntity.delete_role_from_all_tenants` — name-based deletion across tenants, reusing the existing `delete_role`
  cascade.
- `AgentService.create_agent_instance` / `delete_agent_instance` orchestrate the grant/cleanup. The grant is skipped
  when `acting_within_tenant` is `None` (a sysadmin without a tenant context needs no grant — they bypass
  `AccessChecker`).

## Consequences

### Positive

- A non-sysadmin tenant admin can create an instance and immediately list, open, edit, delete, and chat with it — no
  sysadmin step.
- Grants are strictly per-instance; tenants remain isolated and cross-tenant sharing stays a deliberate sysadmin action.
- The conditional tenant grant keeps ceilings free of redundant rules when a wildcard already covers the instance.
- Deletion leaves no stale permissions; OpenWebUI access re-syncs automatically via `AccessChangeHook`.
- Reuses the existing rule model and role cascade — no new access primitives.

### Trade-offs

- Each instance creates a dedicated `agent-<class>-<id>-admin` role, which appears in the roles listing and
  role-assignment UI. Filtering these from the UI is a possible follow-up.
- A `try/except` compensation block appears in `create_agent_instance`, a deliberate exception to the project's
  fail-fast convention, justified by the no-half-created-state requirement.
- The grant touches three access entities per create, each triggering a (debounced) OpenWebUI re-sync.

### Related Decisions

- `2026_04_14_tenant_scoped_roles.md` — roles are tenant-scoped with no per-user store (the reason a per-instance role
  is needed)
- `2026_04_15_sysadmin_implicit_admin_access.md` — sysadmins bypass `AccessChecker` (why the grant is skipped for them)
- `2025_12_25_local_role_management.md` — `RoleEntity` access-rule model (premise)
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — `TenantMetadataEntity` holds metadata only (premise)
- `2026_03_05_aihub_manages_openwebui_model_visibility.md` — OpenWebUI access derives from these rules (sync premise)
