# Sysadmins Have Implicit Admin Access Within Tenants They Belong To

## Context

ADR `2026_04_14_superuser_via_keycloak_realm_role` retired the synthetic superuser identity and made `AIHubSysAdmin` (a
Keycloak realm role) the single signal for "this principal is a platform administrator". `UserIdentity.is_sys_admin` is
populated from the JWT roles claim at authentication time and is available throughout the request lifecycle.

The natural follow-up question was how the access pipeline should treat that flag. The pre-existing model required every
acting principal to (a) be a member of a concrete tenant, (b) have at least one `UserTenantRoleEntity` row in that
tenant, and (c) pass the two-stage tenant-then-user rule check in `AccessChecker`. Points (a) and (c) describe two
different concerns that were previously conflated: **membership** (does this principal belong to this tenant?) and
**authorization** (given that they belong, what may they do there?). Keycloak's `/tenants/<id>` groups own the former;
`AccessChecker` and `RoleEntity` own the latter.

An earlier version of this ADR extended the sysadmin short-circuit from authorization into membership: sysadmins were
permitted to act on any tenant regardless of Keycloak group membership, on the assumption that a sysadmin triaging an
Orphaned tenant or configuring a brand-new one "by construction" could not be a member. That assumption turned out to be
wrong. ADR `2026_04_15_superuser_added_to_every_new_tenant` guarantees that the superuser is added to the Keycloak group
of every tenant at creation time, so the operator who actually needs cross-tenant reach reaches it through explicit
group membership — the same mechanism every other user uses. Granting a membership bypass to the realm role would be
redundant with that guarantee for the superuser and a genuine privilege expansion for any other sysadmin who does not
happen to be in the group.

Two patches were possible: (1) maintain `UserTenantRoleEntity` rows for sysadmins in every tenant, recreated on every
tenant creation and on every sysadmin-role grant; or (2) treat the `AIHubSysAdmin` realm role as a first-class bypass at
the access-check layer. Option (1) reproduces the synthetic-superuser problem in a different shape: a parallel set of
membership rows whose only purpose is to satisfy a check that conceptually doesn't apply to platform admins. Option (2)
— correctly scoped to authorization, not membership — matches how operators already think about the role.

## Decision Drivers

- **Coherent with the realm-role model**: ADR `2026_04_14_superuser_via_keycloak_realm_role` already promoted
  `AIHubSysAdmin` to "the" admin signal. Honouring it at the access-check layer follows from that decision; ignoring it
  there would make the role half-effective.
- **Membership and authorization are orthogonal**: "Is this principal in tenant X?" is a question Keycloak owns via
  `/tenants/<id>` groups; "given that they are, what may they do?" is a question `AccessChecker` owns via tenant/user
  access rules. A single flag that collapses both into "sysadmin may do anything anywhere" breaks the separation and
  creates two different ways to be a tenant member (group membership vs. realm-role implicit membership), each with its
  own consistency rules.
- **Cross-tenant reach for the superuser is already solved**: ADR `2026_04_15_superuser_added_to_every_new_tenant` adds
  the superuser to every tenant group on creation. The operator who most needs to act across tenants is already a member
  of every tenant through the ordinary mechanism — no role-based membership short-circuit is required.
- **No parallel data plane for admin access**: Maintaining `UserTenantRoleEntity` rows for sysadmins in every tenant is
  bookkeeping the platform doesn't need. Every such row would be created and deleted in tandem with the realm-role grant
  — a synchronization problem with no upside.
- **Revocation must be immediate**: Stripping `AIHubSysAdmin` in Keycloak should remove platform-admin privileges on the
  next request, without requiring cascading deletes of derived rows.
- **The bypass must be loud, not subtle**: Sysadmin access skipping the tenant-and-user rule check is a real privilege
  expansion. It must be a single, named, documented short-circuit at the top of the check — not a scattered set of "if
  sysadmin then ignore" branches sprinkled through the code.

## Decision

**A principal whose `UserIdentity.is_sys_admin` is true receives `AccessLevel.ACCESS_ADMIN` on every permission check
within any tenant they are a member of, regardless of that tenant's access rules or the principal's role assignments.
This bypass is implemented as a single short-circuit at the entry point of `AccessChecker.access_level()` and is the
only place in the access pipeline that consults the flag for authorization purposes.**

The bypass is strictly an **authorization** short-circuit. It does NOT extend to membership:

- **Tenant resolution validates Keycloak group membership for every principal, including sysadmins.** The auth handler's
  `_resolve_tenant_by_id` and `_resolve_active_tenant` paths require the principal to be a member of the Keycloak
  `/tenants/<id>` group. The same rule applies to sysadmins — the `AIHubSysAdmin` realm role grants authorization, not
  membership. Cross-tenant endpoints that a sysadmin must reach without acting within any tenant (e.g., the tenant-list
  view used to configure Unconfigured or triage Orphaned tenants) are global, non-tenant-scoped controllers and never
  invoke tenant resolution.
- **Membership sources are unified.** `KeycloakAdminService.is_user_member_of_tenant` and
  `KeycloakAdminService.get_user_tenant_ids` are the only authorities for "does this user belong to this tenant".
  `UserTenantRoleEntity` stores role assignments within a tenant; a missing or empty row does not imply non-membership,
  and a stale row does not imply membership.
- **The superuser reaches every tenant through explicit group membership**, not through this bypass. ADR
  `2026_04_15_superuser_added_to_every_new_tenant` is what makes cross-tenant sysadmin operations work; this ADR is what
  makes them admin-level once inside.
- **A sysadmin may still act with `acting_within_tenant=None`** on global (non-tenant-scoped) endpoints. The access
  check returns `ACCESS_ADMIN` without requiring a tenant identity.

The bypass applies to authorization only. It does not exempt sysadmins from authentication, audit logging, OpenTelemetry
attribution, or per-request tracing — every sysadmin action remains attributable to a real Keycloak user with a real
user id.

## Consequences

### Positive

- One authorization signal: `AIHubSysAdmin` in Keycloak grants admin-level permissions within any tenant the principal
  is a member of. Revoking the role in Keycloak immediately strips those privileges on the next request without any
  cascade.
- Membership remains a single, uniform question answered by Keycloak groups. "Who is in tenant X" has one answer
  regardless of whether you ask it for a regular user, a sysadmin, or the superuser — no per-role special cases, no
  `UserTenantRoleEntity` rows maintained purely to represent admin membership.
- The bypass lives at exactly one location in `AccessChecker`, making the privilege boundary easy to audit. Adding new
  permission templates does not require thinking about whether sysadmins are also covered — within tenants they belong
  to, they always are.
- A sysadmin who does not happen to be in a given tenant's Keycloak group has no access to that tenant's scoped
  endpoints. Accidentally granting `AIHubSysAdmin` to someone no longer implicitly exposes every tenant's data to that
  user; they still need to be added to the groups they should reach.
- The superuser's cross-tenant reach follows from a data invariant enforced at tenant-creation time (ADR
  `2026_04_15_superuser_added_to_every_new_tenant`), not from a code branch. Auditing "what can the superuser touch" is
  equivalent to auditing group membership — the same tooling operators already use for regular users.

### Trade-offs

- The two-stage tenant-ceiling check (per the original `AccessChecker` design) does not apply to sysadmins within
  tenants they belong to. A tenant whose own access rules forbid `aihub.admin.agent.foo` will still allow a sysadmin
  member to act on `agent.foo`. This is the intended semantics of "platform admin" but is worth stating explicitly:
  tenant access rules are not a defence against sysadmins who are members of the tenant.
- An `AIHubSysAdmin` grant combined with membership in any tenant is extremely powerful — within that tenant there is no
  access-rule scoping. Operators must treat the realm role as a high-trust assignment; the mitigation is that grants,
  revocations, and group memberships are all auditable in Keycloak and immediately effective.
- Non-superuser sysadmins must be explicitly added to a tenant's Keycloak group before they can act within it. For the
  initial triage of an Orphaned tenant or the configuration of an Unconfigured one, this is handled on the cross-tenant
  admin endpoints (which are global, not tenant-scoped). Sysadmin operators who expected "sysadmin = instant access"
  must now use the group-add flow (or rely on the superuser for the very first touch).
- Tests covering tenant-ceiling behaviour need a non-sysadmin user to exercise the rule path — using a sysadmin identity
  bypasses the very logic under test.

### Related Decisions

- `2026_04_14_superuser_via_keycloak_realm_role.md` — Establishes `AIHubSysAdmin` as the admin signal (premise)
- `2026_04_15_superuser_added_to_every_new_tenant.md` — The companion decision that makes cross-tenant sysadmin
  operations work through explicit group membership rather than a membership bypass
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — Keycloak owns tenant existence; this ADR extends that to
  tenant membership as well
- `2026_02_20_keycloak_tenant_assignment_via_groups.md` — `/tenants/<id>` groups as the membership mechanism
- `2026_04_14_tenant_scoped_roles.md` — Tenant-scoped roles (the rule layer the sysadmin bypass sits above)
- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak as sole OIDC provider (premise for realm-role-based signals)
