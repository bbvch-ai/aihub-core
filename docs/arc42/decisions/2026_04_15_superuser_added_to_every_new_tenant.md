# Superuser Is Added to Every Tenant at Creation Time

## Context

ADR `2026_04_14_superuser_via_keycloak_realm_role` made the Superuser an ordinary Keycloak user identified by the
`AIHubSysAdmin` realm role. ADR `2026_04_15_sysadmin_implicit_admin_access` makes holders of that role admins **within
tenants they are a member of**, but explicitly does NOT grant implicit membership — membership is strictly a Keycloak
group question. This ADR is the mechanism by which the Superuser — the one sysadmin that must reach every tenant by
design — becomes a member of every tenant: through ordinary Keycloak group membership, added at tenant creation time. It
is the counterpart to the authorization-only sysadmin bypass; together the two ADRs replace the earlier (and briefly
considered) model in which the realm role alone granted both.

What the realm role does not do is make the Superuser **visible** in any tenant. The Superuser does not appear in
`/tenants/<id>` group member listings, does not show up when iterating tenant members for provisioning or attribution,
and does not exist in any per-tenant directory walked by adjacent tooling (Langfuse trace ownership, OpenWebUI group
sync, etc.). Without explicit group membership, sysadmin presence is invisible — a quiet asymmetry between identity and
the directories other services read from. Adding the Superuser to the group closes that asymmetry **and** is the sole
mechanism by which the Superuser becomes an authorized actor within each tenant.

A second motivation: the platform's two paths through which a tenant becomes Active are the startup-tenant bootstrap and
`TenantAdminService.create_tenant_metadata` (per ADR `2026_04_15_keycloak_as_tenant_existence_authority`). Both already
construct or validate the Keycloak group; both are natural seams for adding "the platform's own user" to that group as
part of bringing the tenant into being. The alternative — leaving membership to ad-hoc operator action — produces a
class of tenants where the Superuser is not a member by accident rather than by design.

The user explicitly framed the desired behaviour as a **default**, not an enforced invariant: if a sysadmin later
removes the Superuser from a tenant via the Keycloak admin console, that removal should be respected. The platform
should not "fight" the operator. This rules out periodic reconciliation and Keycloak SPI-based blocking.

## Decision Drivers

- **Authorization without presence is incomplete**: A principal authorized to act everywhere should be visible
  everywhere. Membership is the surface that operator tooling and downstream services read from; missing rows produce
  silent gaps in attribution and discovery.
- **Add at creation, not by reconciliation**: A reconciler that re-adds the Superuser after removal would override
  deliberate operator intent. The user's directive is that runtime removal is a legitimate sysadmin action and must
  stand.
- **Two well-defined creation paths**: Default-tenant bootstrap and `create_tenant_metadata` are the only routes by
  which a tenant becomes Active. Both already touch the Keycloak group; adding the Superuser there is local to the
  operation that creates the tenant.
- **Idempotent, low-cost mechanism**: Keycloak's group-add is a no-op for an existing member. Calling it during creation
  costs one Admin API call per new tenant — negligible — and stays correct regardless of prior state.
- **No parallel role rows**: Within each tenant the Superuser is a member of, authorization follows the `AIHubSysAdmin`
  realm-role bypass in `AccessChecker` (per ADR `2026_04_15_sysadmin_implicit_admin_access`). The Superuser is added as
  a Keycloak group member only; no `UserTenantRoleEntity` rows are created for it. Reintroducing per-tenant role rows
  for the Superuser would resurrect exactly the parallel data plane that ADR explicitly rejected.
- **Membership is the sole mechanism for cross-tenant reach.** Because the sysadmin ADR was scoped to authorization and
  not membership, this group-add is not merely additive (closing a visibility gap) — it is load-bearing: without it, the
  Superuser would fail the Keycloak membership check on tenant-scoped endpoints.

## Decision

**At tenant metadata creation, the Superuser is added as a member of the new tenant's `/tenants/<id>` Keycloak group.
This applies to both creation paths — the startup-tenant bootstrap and the `create_tenant_metadata` flow that attaches
metadata to a pre-existing Keycloak group. After creation, the membership is treated as ordinary: no startup
reconciliation, no periodic restoration, no Keycloak SPI to block removal. A sysadmin who removes the Superuser from a
tenant via the Keycloak admin console removes them, and the removal stands.**

The scope is **Active tenants only** — tenants that exist in both Keycloak and MongoDB metadata. Unconfigured Keycloak
groups (groups under `/tenants/` with no metadata yet) are not touched; the Superuser is added at the moment those
groups become Active via `create_tenant_metadata`.

The Superuser identity is resolved by email lookup against Keycloak (`SUPERUSER_EMAIL` →
`KeycloakAdminService.find_user_by_email`) and the resulting user id is memoized for the process lifetime. The lookup is
lazy — the first tenant creation in the process triggers it; subsequent creations reuse the cached id.

## Consequences

### Positive

- Every Active tenant has the Superuser as a visible member from the moment it comes into existence. Tenant-member
  walks, per-tenant attribution, and operator tooling all see a consistent picture.
- The asymmetry between "the Superuser can act on this tenant" (authorized) and "the Superuser is in this tenant"
  (visible) closes for the common path. The two ADRs that enable the former now have a structural counterpart on the
  latter.
- Operator intent is preserved end-to-end: the Superuser is in by default, but a deliberate removal sticks. There is no
  surprise re-add behaviour to trip up troubleshooting.
- The mechanism is local to the two creation paths and uses an idempotent Keycloak operation. No background tasks, no
  extra deployment artefacts, no SPI compilation.

### Trade-offs

- **Tenants that existed before this change are not retroactively touched.** The startup tenant in the current
  deployment already has the Superuser via the existing first-startup user backfill, so in practice this is a non-issue
  today; for any future migration where pre-existing tenants matter, a one-shot manual add via the Keycloak admin
  console is the documented remedy.
- **Drift is possible.** A sysadmin who removes the Superuser from a tenant gets exactly what they asked for — including
  the loss of visibility benefits described above. This is the intended semantics; documenting that "removal is
  permanent" is the operator-facing consequence.
- **Tampering is not surfaced.** Because the platform does not reconcile, there is no log line or alert when the
  Superuser is removed from a tenant out-of-band. If tampering detection is later desired, it is a separate decision on
  top of this one (e.g., a periodic comparison job that emits a security event without re-adding) and would not change
  the membership model itself.
- **The first tenant creation per process pays for the Superuser-id lookup.** One additional Keycloak Admin API call,
  cached thereafter. Acceptable; the alternative (resolving on every call) would be wasteful, and the alternative
  (resolving at startup unconditionally) would couple more code to startup ordering for no real benefit.

### Related Decisions

- `2026_04_14_superuser_via_keycloak_realm_role.md` — Establishes the Superuser as an ordinary Keycloak user (premise)
- `2026_04_15_sysadmin_implicit_admin_access.md` — Establishes that `AIHubSysAdmin` grants admin-level authorization
  *within tenants the principal is a member of*; this ADR is the membership mechanism that makes that authorization
  reachable for the Superuser on every tenant
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — Defines the two creation paths (`initialize_default_tenant`,
  `create_tenant_metadata`) at which the Superuser is now added
- `2026_02_20_keycloak_tenant_assignment_via_groups.md` — `/tenants/<id>` groups as the sole membership mechanism, which
  this ADR uses directly
