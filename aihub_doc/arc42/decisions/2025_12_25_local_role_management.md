# Local Multi-Tenant Role Management

## Context

Previously, user roles were fetched from Azure AD via the Microsoft Graph API during authentication. This created
external dependencies, added latency, and made the system tightly coupled to Azure AD's role assignment model.

## Decision Drivers

- **Reduced External Dependencies** Eliminate Graph API calls during authentication for faster, more reliable auth.
- **Multi-Tenancy Support** Enable role management per tenant rather than globally via identity provider.
- **Simplified Architecture** Remove the IdentityProvider abstraction layer that added complexity without benefit.
- **JWT Self-Containment** User identity data (name, email, oid) is already in the JWT—no need to fetch it again.
- **Tenant Boundaries** Tenant access rules must act as a ceiling for user permissions.

## Decision

### Core Entities

Roles are now managed locally in the database via a multi-tenant model:

- **TenantEntity** defines organizational boundaries with `access_rules` that limit what ANY user in that tenant can
  access
- **UserTenantRoleEntity** maps users to tenants with specific roles (authoritative source for user-tenant-role
  relationships)
  - Unique constraint on `(user_id, tenant_id)` ensures one record per user-tenant pair
  - Stores list of role names that reference RoleEntity documents
- **RoleEntity** defines roles with `tenant_id` scoping (system roles have `tenant_id=None`, tenant roles are scoped)
  - Unique constraint changed from `name` to `(tenant_id, name)` to support tenant-specific roles
- **UserEntity** stores user profile data (name, email, profile_image) but NO LONGER has a `roles` field
  - Provides `get_roles(tenant_id)` method that queries UserTenantRoleEntity for the user's roles in a specific tenant
  - Returns empty list if user has no roles in the specified tenant

### Identity Resolution

- **UserIdentity** includes both user data AND `acting_within_tenant: TenantIdentity`
- **TenantIdentity** resolved from `x-tenant-id` HTTP header or defaults to default tenant
- **Auth handlers** resolve BOTH user and tenant during authentication:
  1. Extract user data from JWT claims
  2. Create or update user in the database
  3. Resolve tenant from `x-tenant-id` header or fall back to default tenant
  4. Verify user has at least one role in the tenant
  5. Return user identity with embedded tenant context

### Access Control

- **AccessChecker** performs two-stage access checking with tenant as boundary:
  1. **STAGE 1:** Determine tenant's access level (admin or user) based on tenant access rules
  2. **STAGE 2:** Determine user's access level (admin or user) based on user roles, then return MINIMUM of both levels
     (tenant acts as ceiling)
- **Tenant access rules act as a filter** - if tenant has no matching access rules for a resource, access is DENIED
  regardless of user roles
- **User permissions cannot exceed tenant permissions** - even admin users are capped at user-level if tenant only has
  user-level access
- **Empty tenant.access_rules = full denial** - tenants with empty access_rules list deny all access to all resources

### User Onboarding

- **First user** receives admin roles; subsequent users receive standard roles (configurable via `UserSignupSettings`)
- **Automatic tenant assignment** to default tenant during first login
- **No external role sync** - all role management happens locally

### Superuser Authentication

- **Virtual superuser tenant**: Superuser operates within a virtual (non-persisted) tenant with `aihub.admin.>` access
  rules. The tenant ID is the literal constant `__superuser_tenant__`, defined in `SuperuserAuthHandler.py`. This ID
  never appears in the database — it exists only in memory during request processing
- **Bypasses tenant restrictions**: While still going through two-stage access control, the virtual tenant ensures all
  permission checks pass
- **Static token authentication**: Uses `SUPERUSER_TOKEN` instead of OAuth2
- **Created for audit trail**: Superuser user entity is created in database for auditing, but not assigned to any real
  tenant

### Removed Components

The IdentityProvider abstraction (AzureIdentityProvider, TokenIdentityProvider, etc.) and AzureGraphService have been
removed entirely. Auth handlers are now standalone classes that validate tokens and manage users locally.

## Consequences

### Breaking Changes

- **Profile images** are no longer fetched from Azure AD during auth
  - Must be stored locally in UserEntity.profile_image field
  - Only http:// and https:// URLs are allowed (data URLs and base64 not permitted)
  - UserEntity validates profile_image format on save
- **UserEntity.roles field removed** - roles must be fetched via `user.get_roles(tenant_id)` which queries
  UserTenantRoleEntity
- **All operations require tenant context** - no more global role lookups
- **RoleEntity unique constraint changed** - from `name` unique to `(tenant_id, name)` unique
- **AccessChecker constructor signature changed** - now requires both `user_access_rules` and `tenant_access_rules`
  parameters

### Access Control Behavior

- **Tenant boundaries enforced** - users cannot access resources outside their tenant's access rules
- **Admin users capped by tenant** - if tenant has user-level access, admin users get user-level access
- **Empty tenant access rules = no access** - tenants with no access rules deny all user access

### Multi-Tenancy

- **Tenant header optional** - `x-tenant-id` header identifies the tenant context; defaults to default tenant if not
  provided
- **User-tenant isolation** - users can have different roles in different tenants
- **Tenant-scoped roles** - roles can be system-wide (`tenant_id=None`) or tenant-specific (`tenant_id` set)
- **Tenant membership required** - users must have at least one role in a tenant to access it (enforced during auth
  handler tenant resolution)

### Migration & Deployment

**For new deployments:**

- Default tenant is created automatically during initialization via `initialize_default_tenant()`
- System roles are created with `tenant_id=None` via `initialize_system_role()`
- First user signup receives admin roles in default tenant
- Subsequent users receive standard roles in default tenant

**For existing deployments:**

- **Default tenant creation**: Automatic via `TenantEntity.ensure_default_tenant_exists()`
- **System roles migration**: Existing RoleEntity records need `tenant_id=None` set (system roles)
- **User role migration**: Data in old `UserEntity.roles` field must be migrated to UserTenantRoleEntity
- **No automatic migration**: Deployments upgrading from previous versions must manually migrate data
- **Rollback considerations**: UserEntity.roles field removal makes rollback complex; backup database before upgrade
