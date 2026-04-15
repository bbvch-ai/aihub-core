# Sysadmins Have Implicit Admin Access to Every Tenant and Resource

## Context

ADR `2026_04_14_superuser_via_keycloak_realm_role` retired the synthetic superuser identity and made `AIHubSysAdmin` (a
Keycloak realm role) the single signal for "this principal is a platform administrator". `UserIdentity.is_sys_admin` is
populated from the JWT roles claim at authentication time and is available throughout the request lifecycle.

The natural follow-up question was how the access pipeline should treat that flag. The pre-existing model required every
acting principal to (a) be a member of a concrete tenant, (b) have at least one `UserTenantRoleEntity` row in that
tenant, and (c) pass the two-stage tenant-then-user rule check in `AccessChecker`. None of these were satisfiable for a
sysadmin acting on a tenant they had no operational reason to be a member of — for example, when triaging an Orphaned
tenant (per ADR `2026_04_15_keycloak_as_tenant_existence_authority`) or configuring a brand-new tenant before any users
exist in it.

Two patches were possible: (1) maintain `UserTenantRoleEntity` rows for sysadmins in every tenant, recreated on every
tenant creation and on every sysadmin-role grant; or (2) treat the `AIHubSysAdmin` realm role as a first-class bypass at
the access-check layer. Option (1) reproduces the synthetic-superuser problem in a different shape: a parallel set of
membership rows whose only purpose is to satisfy a check that conceptually doesn't apply to platform admins. Option (2)
matches how operators already think about the role.

## Decision Drivers

- **Coherent with the realm-role model**: ADR `2026_04_14_superuser_via_keycloak_realm_role` already promoted
  `AIHubSysAdmin` to "the" admin signal. Honouring it at the access-check layer follows from that decision; ignoring it
  there would make the role half-effective.
- **Sysadmins must be able to act on tenants without being members**: Configuring a fresh tenant, deleting an Orphaned
  one, or inspecting an Unconfigured group are all sysadmin actions that by construction cannot involve membership.
- **No parallel data plane for admin access**: Maintaining `UserTenantRoleEntity` rows for sysadmins in every tenant is
  bookkeeping the platform doesn't need. Every such row would be created and deleted in tandem with the realm-role grant
  — a synchronization problem with no upside.
- **Revocation must be immediate**: Stripping `AIHubSysAdmin` in Keycloak should remove platform-admin privileges on the
  next request, without requiring cascading deletes of derived rows.
- **The bypass must be loud, not subtle**: Sysadmin access skipping the tenant-and-user rule check is a real privilege
  expansion. It must be a single, named, documented short-circuit at the top of the check — not a scattered set of "if
  sysadmin then ignore" branches sprinkled through the code.

## Decision

**A principal whose `UserIdentity.is_sys_admin` is true receives `AccessLevel.ACCESS_ADMIN` on every permission check,
in every tenant, regardless of tenant access rules, role assignments, or tenant membership. This bypass is implemented
as a single short-circuit at the entry point of `AccessChecker.access_level()` and is the only place in the access
pipeline that consults the flag for authorization purposes.**

Two further consequences follow from this short-circuit and are part of the decision:

- **Tenant resolution skips membership for sysadmins.** The auth handler's `_resolve_tenant_by_id` and
  `_resolve_active_tenant` paths do not require a sysadmin to be a member of the tenant they are acting on. A tenant
  identity is constructed from Keycloak group + metadata as long as the tenant exists; no `UserTenantRoleEntity` lookup
  gates the resolution.
- **A sysadmin may act with `acting_within_tenant=None`.** When a sysadmin endpoint is reached without a tenant context
  (e.g., the cross-tenant tenant-list view), the access check still returns `ACCESS_ADMIN` and downstream code does not
  need to fabricate a tenant identity to satisfy the check.

The bypass applies to authorization only. It does not exempt sysadmins from authentication, audit logging, OpenTelemetry
attribution, or per-request tracing — every sysadmin action remains attributable to a real Keycloak user with a real
user id.

## Consequences

### Positive

- Sysadmins can configure, edit, and delete any tenant — including Orphaned and Unconfigured ones — without prior
  membership setup. The "first sysadmin acting on a new tenant" flow works without bootstrapping rows.
- One mechanism, one signal: `AIHubSysAdmin` in Keycloak grants admin access everywhere. Revoking the role in Keycloak
  immediately strips access on the next request without any cascade.
- No `UserTenantRoleEntity` rows exist purely to satisfy the access check for sysadmins. The `roles` collection per
  tenant continues to reflect actual user-to-role assignments, not synthetic admin entries.
- The bypass lives at exactly one location in `AccessChecker`, making the privilege boundary easy to audit. Adding new
  permission templates does not require thinking about whether sysadmins are also covered — they always are.

### Trade-offs

- The two-stage tenant-ceiling check (per the original `AccessChecker` design) does not apply to sysadmins. A tenant
  whose own access rules forbid `aihub.admin.agent.foo` will still allow a sysadmin to act on `agent.foo` within that
  tenant. This is the intended semantics of "platform admin" but is worth stating explicitly: tenant access rules are
  not a defence against sysadmins.
- An `AIHubSysAdmin` grant is now extremely powerful — there is no per-tenant scoping. Operators must treat the realm
  role as a high-trust assignment; the mitigation is that grants and revocations are auditable in Keycloak and
  immediately effective.
- Endpoints that previously could assume `acting_within_tenant` was always set must now tolerate `None` on the sysadmin
  path. Most sysadmin endpoints already operate cross-tenant by design; the few that did not have been adjusted.
- Tests covering tenant-ceiling behaviour now need a non-sysadmin user to exercise the rule path — using a sysadmin
  identity bypasses the very logic under test.

### Related Decisions

- `2026_04_14_superuser_via_keycloak_realm_role.md` — Establishes `AIHubSysAdmin` as the admin signal (premise)
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — Companion: sysadmins must act on tenants where membership
  doesn't apply (Orphaned, Unconfigured)
- `2026_04_14_tenant_scoped_roles.md` — Tenant-scoped roles (the rule layer the sysadmin bypass sits above)
- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak as sole OIDC provider (premise for realm-role-based signals)
