# Roles are Strictly Tenant-Scoped; Defaults Seeded per Tenant

## Context

ADR `2025_12_25_local_role_management` introduced `RoleEntity` with a nullable `tenant_id`, distinguishing "system
roles" (`tenant_id=None`, available to every tenant via `tenant_id__in=[None, tenant_id]` in every access query) from
"tenant-scoped roles" (`tenant_id` set, visible only in that tenant). The default role set — `AIHubUser`, `AIHubAdmin`,
`AIHubAgentUser`, `AIHubAgentAdmin`, `AIHubKnowledgeAdmin`, `AIHubProcessUser`, `AIHubProcessAdmin`, plus
`AIHubSuperuser` — was created once at API startup as system roles.

Once ADR `2026_03_30_tenant_path_parameter` and the subsequent `TenantMetadataEntity` refactor established Keycloak as
the source of truth for tenant existence (tenants are Keycloak groups under `/tenants/`; the MongoDB collection merely
holds display metadata), the notion of a role that transcends all tenants became semantically out of place. System roles
also silently bypassed tenant boundaries: a tenant admin querying "roles in my tenant" got system roles mixed in whether
they wanted them or not, and every permission check had to `OR` the two buckets together.

## Decision Drivers

- **Coherent tenancy model**: Tenants are the primary isolation boundary; roles belonging to no tenant violate that
  boundary at the query level.
- **Query simplicity**: The recurring `tenant_id__in=[None, tenant_id]` pattern appeared in every role-related
  `RoleEntity` method. It invites mistakes when new methods are added.
- **Uniform provisioning across tenants**: Sysadmin-configured tenants (attached to pre-existing Keycloak groups) did
  not receive the default role set and started out empty, which was surprising.
- **`AIHubSuperuser` role was unused**: `SuperuserAuthHandler` short-circuits via `is_sys_admin=True` with hardcoded
  access rules — it never reads the DB row. Keeping it as a system role added noise.

## Decision

**Every `RoleEntity` belongs to exactly one tenant. The `tenant_id` field is required (`NOT NULL`). The default role set
is seeded per tenant at tenant-creation time, gated by the existing `AIHUB_CREATE_DEFAULT_ROLES` flag. `AIHubSuperuser`
is retired entirely.**

### Implementation

- `RoleEntity.tenant_id` becomes `StringField(required=True)`; `null=True, default=None` removed.
- Deleted methods: `is_system_role`, `get_system_role_by_name`, `create_system_role`, `get_system_roles`.
- All remaining queries (`get_access_rules_for_roles`, `filter_existing_roles`, `get_roles_for_tenant`,
  `get_usage_limits_for_roles`) replace `tenant_id__in=[None, tenant_id]` with `tenant_id=tenant_id`.
- New helper `initialize_default_roles_for_tenant(tenant_id: str)` in `initialize_db.py` seeds the 7 defaults
  idempotently (existence check per role before insert).
- Call sites:
  - `initialize_default_tenant()` calls it after tenant creation / on every startup (idempotent).
  - `TenantAdminService.create_tenant_metadata()` calls it after attaching metadata to a Keycloak group.
- `RoleResponse.is_system_role` computed field removed from the SDK; `tenant_id` is now a required string in the DTO.
- Lifetime orchestration renamed: `initialize_roles()` → `finalize_role_setup()` (runs signup-role validation after
  tenant initialization has already seeded the defaults).

### Migration

Existing installations that carry `tenant_id=None` roles need a one-shot update to stamp the default tenant's id onto
those rows (or delete and re-seed them). This is a platform-wide breaking change; it is not backward compatible, in line
with the "no backwards-compatibility shims" convention.

## Consequences

### Positive

- Single, consistent query shape: every access check is scoped to one concrete `tenant_id`.
- Every tenant — default or sysadmin-configured — boots with the same default role set when `CREATE_DEFAULT_ROLES` is
  true, eliminating an onboarding footgun.
- Tenant admins see only their own roles in UI lists; no cross-tenant leakage.
- One fewer concept to reason about; `is_system_role` no longer exists to confuse DTO consumers.

### Trade-offs

- Default role definitions now live in seven copies (one per tenant) instead of one global copy. Changing a default
  requires the seeding helper to run on next startup for each tenant.
- Platform operators upgrading from the previous model must run a data migration before first start — the API will
  otherwise reject `RoleEntity` documents that still have `tenant_id=None`.

### Supersedes

- The "System roles vs tenant-scoped roles" design in `2025_12_25_local_role_management.md` — Only tenant-scoped roles
  remain.

### Related Decisions

- `2025_12_25_local_role_management.md` — Roles live in MongoDB (unchanged premise)
- `2026_03_30_tenant_path_parameter.md` — Explicit tenant routing (premise)
- `2026_02_20_keycloak_tenant_assignment_via_groups.md` — Tenant membership via Keycloak groups (premise)
- `2026_04_14_superuser_via_keycloak_realm_role.md` — Drops `AIHubSuperuser` role along with the handler
