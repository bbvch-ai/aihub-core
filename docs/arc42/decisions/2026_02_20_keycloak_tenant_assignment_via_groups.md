# Keycloak Tenant Assignment via Groups

## Context

Swiss AI Hub is a multi-tenant platform where users can belong to multiple tenants. Previously, tenant assignment was
managed exclusively in the application's local database (`UserTenantRoleEntity` in MongoDB). With the introduction of
Keycloak as the sole identity broker, the platform needs a way to store tenant assignments on the Keycloak user so that:

- The application can read tenant memberships directly from the OIDC token
- Users logging in via different identity providers (e.g., separate Azure AD app registrations per tenant) can be
  automatically assigned to the corresponding tenant
- The same user (same email) authenticating through multiple IDPs accumulates tenant memberships rather than having them
  overwritten
- All accepted users (those with the `AIHubAccess` role) are automatically members of a default tenant

The platform supports a scenario where a customer has multiple Azure AD app registrations, each representing a different
tenant. A user may have the same email across all app registrations and should be merged into a single Keycloak user
with all tenant memberships preserved.

## Decision Drivers

- **Additive IDP Mapping**:\
  When a user logs in via different identity providers, their tenant assignment must accumulate, not overwrite.
  Keycloak's `Hardcoded Attribute` IDP mapper overwrites user attributes on each login (`syncMode: FORCE`), making user
  attributes unsuitable for multi-valued, multi-IDP tenant assignment. The `Hardcoded Group` IDP mapper, by contrast,
  adds group memberships additively.
- **Token Accessibility**:\
  The application must be able to read tenant memberships from the OIDC token without additional API calls. Keycloak's
  `Group Membership` protocol mapper produces a JSON array claim with all group memberships.
- **Default Tenant for All Users**:\
  Keycloak natively supports "default groups" that are automatically assigned to every new user, providing the mechanism
  for automatic default tenant membership.
- **Admin UI Manageability**:\
  Groups are first-class citizens in Keycloak's admin console, allowing administrators to manually assign or remove
  tenant memberships without custom tooling.
- **Maturity Over Innovation**:\
  Keycloak's Organizations feature (introduced in v25, GA in v26.2) is purpose-built for multi-tenancy but has known
  bugs with multi-organization token claims and lacks organization-scoped roles. Groups are a mature, battle-tested
  mechanism.

## Decision

**Tenant assignments are stored as Keycloak group memberships under a `/tenants` parent group.** Each tenant is
represented as a sub-group (e.g., `/tenants/default`, `/tenants/customer-a`). A `Group Membership` protocol mapper
exposes these memberships as a `tenants` claim in the OIDC token.

### Responsibilities

1. **Keycloak owns tenant assignment**: Which user belongs to which tenant is stored as group membership in Keycloak.
   The `tenants` claim in the OIDC token is the source of truth for the application.

2. **Keycloak does NOT manage active tenants**: What tenants exist, their configuration, and which tenant is "active"
   for a given session remains the responsibility of the application (`TenantEntity` in MongoDB). Keycloak only stores
   the user-to-tenant mapping.

3. **Default tenant for all users**: The `/tenants/default` group is configured as a Keycloak default group. All new
   users (from any IDP or manual creation) are automatically members of the default tenant.

4. **Manual tenant assignment is the default**: By default, administrators assign users to tenants manually via the
   Keycloak admin console (adding/removing users from `/tenants/*` groups). No automatic IDP-to-tenant mapping is
   configured out of the box.

5. **IDP-to-tenant mapping is an optional capability**: The platform supports automatic tenant assignment based on which
   identity provider (Azure AD app registration) a user authenticates through. This is achieved via Keycloak's
   `Hardcoded Group` IDP mapper, which adds the user to a specific tenant group on every login via that IDP. This
   capability is **not a default feature** — it must be configured by the installation team per deployment. The platform
   documents how to set it up.

### Implementation

- **Group hierarchy**: A parent group `tenants` contains sub-groups for each tenant (e.g., `default`). The parent group
  is an organizational container — users are members of the sub-groups, not the parent.
- **Default group**: `/tenants/default` is set as a Keycloak default group via the realm's `defaultGroups` setting.
- **Protocol mapper**: A `tenants` client scope contains a `Group Membership` protocol mapper
  (`oidc-group-membership-mapper`) with `full.path = true` and `multivalued = true`. This produces a token claim like:
  ```json
  { "tenants": ["/tenants/default", "/tenants/customer-a"] }
  ```
- **Client scope assignment**: The `tenants` scope is added to the `aihub-frontend` client's default scopes so the Admin
  UI receives tenant information in the token.
- **IDP-to-tenant mapping** (when configured): A `Hardcoded Group` IDP mapper (`oidc-hardcoded-group-idp-mapper`) on
  each identity provider assigns users from that IDP to the corresponding tenant group. Since group membership is
  additive, a user logging in via multiple IDPs accumulates all tenant memberships.

### IDP-to-Tenant Mapping Setup (for Installation Teams)

To map an Azure AD app registration to a tenant:

1. Create a tenant group under `/tenants/` in Keycloak (e.g., `/tenants/customer-a`)
2. Create a corresponding tenant in the Swiss AI Hub application
3. Add a `Hardcoded Group` IDP mapper on the identity provider:
   - **Mapper Type**: `oidc-hardcoded-group-idp-mapper`
   - **Group**: `/tenants/customer-a`
   - **Sync Mode Override**: `IMPORT` (assign on first login only) or `INHERIT` (follow IDP sync mode)
4. Ensure the IDP's `firstBrokerLoginFlowAlias` links accounts by email to merge users across IDPs

### Alternatives Considered

- **User Attributes**: Simple but IDP mappers overwrite (not append) multi-valued attributes. Custom SPI needed for
  merge logic. Rejected due to overwrite limitation.
- **Realm/Client Roles**: Semantic mismatch — roles represent permissions, not tenancy. Does not scale well with many
  tenants. Rejected.
- **Keycloak Organizations** (v25+): Purpose-built but has known bugs with multi-organization token claims
  (keycloak/keycloak#33556, keycloak/keycloak#39402) and lacks organization-scoped roles. From a Viewpoint of the Swiss
  AI Hub there is only one User-Tenant. the Multitenancy is with tenant inside the Swiss AI Hub. Might be re-evaluated
  when the feature matures.

## Consequences

### Positive

- Tenant assignments are visible in the OIDC token — no extra API calls needed
- Group membership is additive across IDPs, solving the multi-app-registration use case
- Default tenant membership is automatic for all new users
- Administrators can manage tenant assignments via the standard Keycloak admin console
- IDP-to-tenant mapping is a configuration-only task (no code changes)
- The approach is portable across Keycloak versions and does not depend on experimental features

### Trade-offs

- The `tenants` token claim includes full group paths (e.g., `/tenants/default`), requiring the application to parse
  paths rather than using simple tenant names
- The `Group Membership` protocol mapper includes ALL group memberships unless the claim is filtered by the application
  — tenant groups must be distinguished by the `/tenants/` path prefix
- Keycloak becomes a dependency for tenant assignment data, adding to the platform's reliance on Keycloak availability
- The `defaultGroups` mechanism applies to all new users, including those who may later be denied access (no
  `AIHubAccess` role) — these orphaned group memberships are harmless but not cleaned up automatically

### Related Decisions

- `2025_12_28_keycloak_as_identity_broker.md` — Keycloak is the sole OIDC provider; this decision extends its role to
  include tenant assignment
- `2025_12_25_local_role_management.md` — Swiss AI Hub manages roles locally in MongoDB; tenant assignment in Keycloak
  complements (not replaces) the local `UserTenantRoleEntity` for role-within-tenant management
