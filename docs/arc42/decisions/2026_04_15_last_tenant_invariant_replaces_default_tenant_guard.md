# The Startup Tenant Is Not Special; The Platform Just Needs At Least One Tenant

## Context

The original tenant model treated `is_default=True` as a load-bearing flag: the startup tenant could not be deleted, was
the implicit fallback for users with no active-tenant attribute, and was the target of various startup paths that seeded
roles, knowledge buckets, and provisioning hooks. Deleting it would have left the platform in an inconsistent state, so
a hard guard at the entity layer raised on any attempt to remove the default.

Two prior decisions eroded the rationale for that guard. ADR `2026_04_07_active_tenant_as_keycloak_user_attribute` moved
active-tenant selection to a Keycloak attribute and introduced an explicit fallback chain (last-active → startup tenant
→ first-available), removing the need for a single fixed default at the entity layer. Subsequent work on the
multi-tenant sysadmin UI introduced the "configure a Keycloak group as a tenant" flow, which means tenants other than
the bootstrap one are now first-class — operators routinely have multiple tenants and may want to retire the bootstrap
one once a real production tenant exists.

What was actually being protected by the deletion guard was a different invariant: the platform must always have *at
least one* tenant, because a user with zero accessible tenants cannot do anything useful and several startup paths (role
seeding, Langfuse provisioning, knowledge bucket creation) assume a tenant exists. That invariant has nothing to do with
which tenant was seeded first.

## Decision Drivers

- **Match the protection to the actual invariant**: "Don't delete the last tenant" is the real constraint. Hardcoding it
  to "don't delete the startup tenant" prevents legitimate operator workflows (retire the bootstrap tenant after a real
  one exists) and fails to prevent the underlying problem (someone deletes every non-startup tenant and the startup one
  remains, but is no longer the one anyone uses).
- **`is_default` had no remaining load-bearing role**: With active-tenant selection moved to Keycloak and the
  multi-tenant fallback chain in place, the flag's only remaining job was deletion-blocking. Once we removed that, the
  column was passive metadata — not worth the schema surface.
- **Identify the startup tenant by id, not by a flag**: The only thing that makes the startup tenant different from
  other tenants is that the first-boot initialization seeds it. That seeding reads `AIHUB_STARTUP_TENANT_ID` from
  `StartupTenantSettings`, and callers that need to locate the startup tenant look it up by that id
  (`TenantMetadataEntity.get_startup_tenant_metadata()`). No database flag is necessary.
- **Enforce the invariant once, at the right layer**: A count check in the delete service is simple, obvious, and lives
  next to the operation it constrains. An entity-layer guard hides the rule from API consumers and produces a less
  helpful error.

## Decision

**The platform-wide invariant is "there must always be at least one tenant", enforced as a count-based check in the
tenant-delete service path. `is_default` is removed from `TenantMetadataEntity` entirely; the startup tenant is
identified by its configured id (`StartupTenantSettings().ID`) and carries no schema-level marker.**

The deletion path returns a `409 Conflict` with a clear message when a sysadmin tries to delete the only remaining
tenant. The startup tenant has no special protection beyond the count check — once a second tenant exists, the startup
tenant can be deleted as freely as any other.

The frontend reflects this in the sysadmin tenant list: the trash action is disabled (with a tooltip explaining why)
when only one tenant exists. There is no "default" badge because there is no longer any database-level distinction
between the startup tenant and operator-configured ones.

## Consequences

### Positive

- The protected invariant matches the real one. Operators cannot accidentally leave the platform tenant-less, but they
  can delete the bootstrap tenant once a production tenant has taken over.
- One source of truth for the rule. The check is in the service layer, visible to API consumers as a documented `409`,
  and has no entity-layer counterpart that could disagree.
- `TenantMetadataEntity` carries only schema — no flags that mean different things at different call sites. Identifying
  the startup tenant is a plain id lookup, mockable and explicit.
- No "Default" badge in the UI. Sysadmins see what the platform actually constrains (can't delete the last one) rather
  than a label with no behavioural consequence.

### Trade-offs

- Operators who relied on the implicit "the startup tenant is always here" guarantee must now think about which tenant
  is load-bearing for their deployment. In practice this was always true — the startup tenant could be renamed and
  reconfigured freely — but the deletion guard masked that fact.
- Code that wanted a "mark this tenant as fallback" semantic would have to reintroduce the concept under a different,
  purpose-named flag. Currently there is no such semantic in the model.

### Supersedes

- The implicit deletion-protection contract on `is_default=True` from the original tenant model.
- The `is_default` field itself, which is no longer part of the schema.

### Related Decisions

- `2026_04_07_active_tenant_as_keycloak_user_attribute.md` — Removed the startup tenant's role as the active-tenant
  fallback (premise)
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — Tenants are no longer rare or sacred; multiple tenants
  (Active, Orphaned, Unconfigured) are normal (premise)
- `2026_04_14_tenant_scoped_roles.md` — Default roles seeded per-tenant, not globally; the bootstrap tenant is no longer
  the only role-bearer (premise)
