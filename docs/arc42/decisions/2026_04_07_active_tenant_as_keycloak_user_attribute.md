# Active Tenant as Keycloak User Attribute

## Context

As part of the migration from the monolithic `UserEntity` MongoDB collection to Keycloak as the source of truth for user
data, the `active_tenant_id` field needs a new home. ADR `2026_02_20_keycloak_tenant_assignment_via_groups` established
that "Keycloak does NOT manage active tenants" and placed this responsibility on the application database. However, with
`UserEntity` being eliminated entirely, storing a single field in a dedicated MongoDB collection introduces unnecessary
complexity when Keycloak already supports custom user attributes.

## Decision Drivers

- **Eliminate MongoDB dependency for user state**:\
  The goal of the `UserEntity` removal is to stop duplicating user data in MongoDB. Creating a new
  `UserActiveTenantEntity` collection to hold one field undermines this goal.
- **Keycloak already owns user identity**:\
  Active tenant is user-scoped state. Keycloak is already the authoritative source for user identity and tenant
  membership (via groups). Storing the active tenant selection alongside the user record is a natural fit.
- **Immediate updates without token refresh**:\
  The Keycloak Admin API allows reading and writing user attributes instantly. Unlike JWT claims, attributes do not
  require a token refresh to take effect — the API server reads them directly via the Admin API.
- **Reduced operational complexity**:\
  One fewer MongoDB collection to manage, back up, and monitor.

## Decision

**The user's active tenant ID is stored as a Keycloak custom user attribute (`active_tenant_id`), read and written via
the Keycloak Admin API.**

This supersedes point 2 of ADR `2026_02_20_keycloak_tenant_assignment_via_groups` ("Keycloak does NOT manage active
tenants").

### Implementation

- **Storage**: Keycloak user attribute `active_tenant_id` (single-valued, contains the MongoDB `TenantEntity` ObjectId
  string).
- **Read**: `KeycloakAdminService.get_active_tenant_id(user_id)` calls `a_get_user(user_id)` and extracts
  `attributes.active_tenant_id[0]`.
- **Write**: `KeycloakAdminService.set_active_tenant(user_id, tenant_id)` calls
  `a_update_user(user_id, {"attributes": {"active_tenant_id": [tenant_id]}})`.
- **Clear on tenant deletion**: When a tenant is deleted, all users whose `active_tenant_id` matches the deleted tenant
  have the attribute cleared.
- **Service account**: The existing `aihub-api-service` service account requires the `manage-users` realm-management
  role (already planned as part of the `UserEntity` migration).

## Consequences

### Positive

- No new MongoDB collection needed for active tenant storage
- Active tenant data lives alongside the user record in Keycloak, consistent with the direction of Keycloak as source of
  truth
- Attribute updates are immediate — no token refresh cycle needed
- Simplifies the `UserEntity` migration by reducing the number of replacement entities

### Trade-offs

- Every request that resolves the `"active"` tenant slug requires a Keycloak Admin API call instead of a direct MongoDB
  query. This adds network latency (~1-5ms internal) but can be mitigated with short-lived caching.
- Increases the platform's dependency on Keycloak Admin API availability for the authentication hot path. If the Admin
  API is unreachable, active tenant resolution fails (JWKS-based token validation still works independently).
- User attributes in Keycloak are stored as `list[str]` (multi-valued by default), requiring the application to read
  `attributes["active_tenant_id"][0]` rather than a simple string field.

### Supersedes

- Point 2 of `2026_02_20_keycloak_tenant_assignment_via_groups.md`: "Keycloak does NOT manage active tenants" is no
  longer accurate. Keycloak now manages active tenant selection as a user attribute.

### Related Decisions

- `2026_02_20_keycloak_tenant_assignment_via_groups.md` — Tenant assignments as Keycloak groups (partially superseded)
- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak as sole OIDC provider
- `2025_12_25_local_role_management.md` — Roles managed locally in MongoDB (unchanged)
