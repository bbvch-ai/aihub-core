# Keycloak Is the Sole Authority for Tenant Existence; MongoDB Holds Display Metadata Only

## Context

ADR `2026_02_20_keycloak_tenant_assignment_via_groups` placed user-to-tenant *membership* in Keycloak (groups under
`/tenants/`) but left tenant *existence* in MongoDB: `TenantEntity` was treated as the canonical record of which tenants
the platform knew about. The Keycloak group and the Mongo document were created together, by the same code path, and
were assumed to stay in lockstep.

That assumption broke in two directions over time. First, the Keycloak admin console is a first-class operator tool —
operators routinely create `/tenants/<id>` groups manually (especially when wiring up IDP-to-tenant mappings per ADR
`2026_02_20`) before any Mongo metadata exists. The platform had no way to surface those tenants in the sysadmin UI;
they were "invisible" until someone ran an init path that created the matching Mongo row. Second, when an operator
deleted a Keycloak group out-of-band, the Mongo document remained and continued to grant access checks that referenced
it — an orphan with no users that could ever reach it, but still a live row in `tenants`.

The deeper issue: with Keycloak responsible for membership and (per ADR `2026_04_07`) the active-tenant attribute,
*everything that decides whether a user can act on a tenant* already routes through Keycloak. Letting Mongo also claim
authority over existence created a second source of truth that nothing actually consulted at the access-control layer.

## Decision Drivers

- **Single source of truth**: One system must own "does this tenant exist". The system that already owns membership and
  active-tenant state is the natural choice; splitting authority across two stores produces orphans in both directions.
- **Operator workflows must work**: Operators creating groups in the Keycloak console (the documented path for
  IDP-to-tenant mapping) need those tenants to be discoverable by the platform without re-running init code.
- **Make orphans visible, not silent**: When the two stores diverge, the platform should surface the divergence to
  sysadmins as a state, not pretend it isn't happening or fail opaquely at access-check time.
- **Preserve display metadata**: Name, description, and tenant-level access rules are presentation concerns Keycloak
  doesn't model well. Forcing them into Keycloak attributes would conflate identity infrastructure with UI fields.
- **Migration cost stays low**: Renaming the entity and tightening its semantics is cheaper than moving metadata to
  Keycloak attributes or to a new collection; the schema doesn't change.

## Decision

**The Keycloak group `/tenants/<tenant_id>` is the only authoritative signal that a tenant exists. The MongoDB
collection `tenants` (renamed conceptually to `TenantMetadataEntity`) holds display metadata only — name, description,
and access rules. A returned metadata document does not imply the tenant still exists in Keycloak; a missing metadata
document does not imply the tenant is absent from Keycloak.**

The two stores can be in three states, all of which must be representable:

- **Active**: group present, metadata present. The normal case; tenant is reachable by end users.
- **Orphaned**: metadata present, group absent. Visible to sysadmins read-only with a delete-metadata action only;
  unreachable by end users.
- **Unconfigured**: group present, metadata absent. Visible to sysadmins as a candidate to attach metadata to (the
  "configure tenant" flow); unreachable by end users until configured.

Any service method that acts on a tenant verifies group existence in Keycloak before trusting metadata. The metadata
class documents this contract explicitly and exposes no methods that imply existence on their own.

The "startup tenant" — the one the platform seeds on first boot — is identified by its configured id
(`StartupTenantSettings().ID`) rather than by a database flag; there is no schema-level distinction between it and
operator-configured tenants. The deletion-protection invariant is a count-based check, not a per-tenant marker (ADR
`2026_04_15_last_tenant_invariant_replaces_default_tenant_guard`).

## Consequences

### Positive

- One system answers "does this tenant exist". Access checks, membership lookups, and active-tenant resolution all agree
  by construction.
- Operators creating Keycloak groups manually (the documented IDP-mapping path) immediately see those tenants in the
  sysadmin UI as Unconfigured, with a clear action to attach metadata.
- Out-of-band Keycloak group deletions surface as Orphaned in the sysadmin view rather than silently granting stale
  access. Sysadmins can then clean up the metadata.
- The metadata class's narrowed contract makes the dependency on Keycloak explicit at the call site; future refactors
  cannot accidentally treat metadata presence as proof of existence.

### Trade-offs

- Most service methods that touch a tenant now incur an additional Keycloak Admin API call to verify group existence
  before reading or writing metadata. Acceptable for the current load; cacheable later if it becomes hot.
- Sysadmins must reason about three tenant states instead of one. The UI carries that complexity (state badges,
  conditional actions per state) but the alternative — pretending divergence cannot happen — produced silent failures.
- Platform availability for tenant-scoped operations is now more tightly coupled to Keycloak Admin API reachability.
  JWKS-based token validation remains independent.
- A bulk operation that touches many tenants (e.g., listing all of them with state) requires a Keycloak round-trip per
  tenant or a single bulk fetch; the bulk path was added (`filter_existing_tenant_ids`) to keep N+1 calls out of the
  list endpoints.

### Supersedes

- The implicit assumption in `2026_02_20_keycloak_tenant_assignment_via_groups` that the MongoDB `TenantEntity` was the
  source of truth for tenant existence. Membership-in-Keycloak (the original decision of that ADR) stands; existence-in-
  Keycloak is now added.

### Related Decisions

- `2026_02_20_keycloak_tenant_assignment_via_groups.md` — Tenant membership via Keycloak groups (premise; partially
  superseded as noted above)
- `2026_04_07_active_tenant_as_keycloak_user_attribute.md` — Active-tenant selection in Keycloak (consistent direction)
- `2026_04_14_tenant_scoped_roles.md` — Roles bound to a concrete tenant id (relies on the existence authority being
  unambiguous)
- `2026_04_15_sysadmin_implicit_admin_access.md` — Companion: sysadmins must be able to act on Unconfigured/Orphaned
  tenants without membership rows
- `2026_04_15_last_tenant_invariant_replaces_default_tenant_guard.md` — Deletion-protection invariant moved off
  `is_default` (and the flag was subsequently removed entirely)
