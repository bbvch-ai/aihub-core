# The Default Tenant Is Not Special; The Platform Just Needs At Least One Tenant

## Context

The original tenant model treated `is_default=True` as a load-bearing flag: the default tenant could not be deleted, was
the implicit fallback for users with no active-tenant attribute, and was the target of various startup paths that seeded
roles, knowledge buckets, and provisioning hooks. Deleting it would have left the platform in an inconsistent state, so
a hard guard at the entity layer raised on any attempt to remove the default.

Two prior decisions eroded the rationale for that guard. ADR `2026_04_07_active_tenant_as_keycloak_user_attribute` moved
active-tenant selection to a Keycloak attribute and introduced an explicit fallback chain (last-active → default →
first-available), removing the need for a single fixed default at the entity layer. Subsequent work on the multi-tenant
sysadmin UI introduced the "configure a Keycloak group as a tenant" flow, which means tenants other than the bootstrap
one are now first-class — operators routinely have multiple tenants and may want to retire the bootstrap one once a real
production tenant exists.

What was actually being protected by the default-tenant guard was a different invariant: the platform must always have
*at least one* tenant, because a user with zero accessible tenants cannot do anything useful and several startup paths
(role seeding, Langfuse provisioning, knowledge bucket creation) assume a tenant exists. That invariant has nothing to
do with which tenant is marked default.

## Decision Drivers

- **Match the protection to the actual invariant**: "Don't delete the last tenant" is the real constraint. Hardcoding it
  to "don't delete the default" prevents legitimate operator workflows (retire the bootstrap tenant after a real one
  exists) and fails to prevent the underlying problem (someone deletes every non-default tenant and the default remains,
  but is no longer the one anyone uses).
- **`is_default` already lost its other roles**: With active-tenant selection moved to Keycloak and the multi-tenant
  fallback chain in place, the flag's only remaining job was deletion-blocking. Either it gets a new job or it stops
  being load-bearing.
- **Keep the bootstrap marker, drop the semantics**: It is still useful to know which tenant the platform created at
  first start (for diagnostics, for distinguishing operator-configured tenants from the auto-seeded one), so the column
  itself stays. What changes is what reading it implies.
- **Enforce the invariant once, at the right layer**: A count check in the delete service is simple, obvious, and lives
  next to the operation it constrains. An entity-layer guard hides the rule from API consumers and produces a less
  helpful error.

## Decision

**The platform-wide invariant is "there must always be at least one tenant", enforced as a count-based check in the
tenant-delete service path. The `is_default` flag remains as a passive marker for "tenant created at startup" but
carries no semantic weight: it does not gate deletion, does not grant additional access, and does not designate the
fallback tenant for active-tenant resolution.**

The deletion path returns a `409 Conflict` with a clear message when a sysadmin tries to delete the only remaining
tenant. The default tenant has no special protection beyond the count check — once a second tenant exists, the default
can be deleted as freely as any other.

The frontend reflects this in the sysadmin tenant list: the trash action is disabled (with a tooltip explaining why)
when only one tenant exists, and there is no longer any visual indication that one tenant is "the default" beyond what
the sysadmin themselves chose to put in its display name and description.

## Consequences

### Positive

- The protected invariant matches the real one. Operators cannot accidentally leave the platform tenant-less, but they
  can delete the bootstrap tenant once a production tenant has taken over.
- One source of truth for the rule. The check is in the service layer, visible to API consumers as a documented `409`,
  and has no entity-layer counterpart that could disagree.
- `is_default` becomes a passive piece of metadata. Code paths that previously needed to think about whether they were
  acting on the default no longer have to.
- The "Default" badge is removed from the sysadmin UI, which previously implied a special status that no longer exists.
  The disabled-when-last delete button is a clearer signal of what the platform actually constrains.

### Trade-offs

- Operators who relied on the implicit "the default is always here" guarantee must now think about which tenant is
  load-bearing for their deployment. In practice this was always true — the default could be renamed and reconfigured
  freely — but the deletion guard masked that fact.
- A future change that wanted to give `is_default` semantics again (e.g., "use this as the fallback if a user has no
  tenants assigned") would have to reintroduce the concept under a different, purpose-named flag. The current code
  treats `is_default=True` as historical information only.

### Supersedes

- The implicit deletion-protection contract on `is_default=True` from the original tenant model. The flag survives, its
  meaning shrinks.

### Related Decisions

- `2026_04_07_active_tenant_as_keycloak_user_attribute.md` — Removed the default tenant's role as the active-tenant
  fallback (premise)
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — Tenants are no longer rare or sacred; multiple tenants
  (Active, Orphaned, Unconfigured) are normal (premise)
- `2026_04_14_tenant_scoped_roles.md` — Default roles seeded per-tenant, not globally; the bootstrap tenant is no longer
  the only role-bearer (premise)
