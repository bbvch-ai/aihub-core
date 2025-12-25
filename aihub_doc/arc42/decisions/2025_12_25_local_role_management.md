# Local Multi-Tenant Role Management

## Context

Previously, user roles were fetched from Azure AD via the Microsoft Graph API during authentication. This created
external dependencies, added latency, and made the system tightly coupled to Azure AD's role assignment model.

## Decision Drivers

- **Reduced External Dependencies** Eliminate Graph API calls during authentication for faster, more reliable auth.
- **Multi-Tenancy Support** Enable role management per tenant rather than globally via identity provider.
- **Simplified Architecture** Remove the IdentityProvider abstraction layer that added complexity without benefit.
- **JWT Self-Containment** User identity data (name, email, oid) is already in the JWT—no need to fetch it again.

## Decision

Roles are now managed locally in the database via a multi-tenant model:

- **UserEntity** stores the user's current roles (synced from their default tenant assignment)
- **TenantEntity** defines organizational boundaries with access rules
- **UserTenantRoleEntity** maps users to tenants with specific roles
- **Auth handlers** extract user data directly from JWT claims and call `UserEntity.ensure_user_exists_for_auth()`
- **First user** receives admin roles; subsequent users receive standard roles (configurable via TenantSettings)

The IdentityProvider abstraction (AzureIdentityProvider, TokenIdentityProvider, etc.) and AzureGraphService have been
removed entirely. Auth handlers are now standalone classes that validate tokens and manage users locally.

## Consequences

- Profile images are no longer fetched from Azure AD during auth (must be stored locally or fetched separately)
- Role changes require updating UserTenantRoleEntity, not Azure AD app role assignments
- Existing users retain their roles; new role assignments only affect new users or explicit updates
