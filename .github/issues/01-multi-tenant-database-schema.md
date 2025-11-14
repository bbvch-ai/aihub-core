# Core Multi-Tenant Database Schema & User Signup Flow

**Blocked by:** None

## Description

We currently use OAuth2/OIDC identity providers (Azure AD, Google, etc.) for both authentication AND authorization. User roles are fetched from the identity provider on every authentication and aggressively synced to our local database via `UserEntity.ensure_user_exists()`, completely overwriting any local role assignments.

This creates several problems:
- **Identity Provider Lock-in**: Each provider implements roles differently, requiring custom `IdentityProvider` implementations
- **No Local Role Management**: Roles must be configured in external systems, not in our platform
- **Single-Tenant Only**: Users have global roles with no concept of organization isolation
- **Sync Conflicts**: External role changes instantly override any local state

We need to pivot to a multi-tenant architecture where:
- Identity providers are used ONLY for authentication (verifying user identity)
- Roles are managed locally within our system
- Users can belong to multiple tenants with different roles in each
- Tenants have their own access rules that define maximum scope for all users

This issue establishes the foundational database schema and removes the identity provider role dependency.

## Key Concepts to Address

The platform needs three new data structures:
1. **Tenants** - Organizations that can have users and roles, with their own access rule boundaries
2. **Tenant-Scoped Roles** - Roles that belong to specific tenants (not global)
3. **User-Tenant-Role Associations** - Mapping users to tenants with their assigned roles

## Current Code Locations

- Identity provider role fetching: `aihub_lib/aihub_lib/auth/identity/AzureIdentityProvider/`
- User synchronization: `UserEntity.ensure_user_exists()` in `aihub_lib/aihub_lib/persistence/user/UserEntity.py`
- Role initialization: `initialize_roles()` in `aihub_api/aihub_api/runners/lifetime/initialize_db.py`
- Existing role entity: `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py`

## Default Tenant Concept

On first startup, the system should create a default tenant that all users are automatically added to. This ensures backward compatibility - the system behaves like single-tenant mode until admins explicitly create new tenants. The default tenant should have unrestricted access rules (full platform access) and cannot be deleted.

## User Signup Flow

New users signing in for the first time should be:
- Automatically added to the default tenant
- Assigned default roles (configurable via environment variables)
- The very first user should receive admin roles

Consider environment variables like:
- `DEFAULT_TENANT_NAME`, `DEFAULT_TENANT_ACCESS_RULES`
- `USER_SIGNUP_DEFAULT_ROLES` (for regular users)
- `FIRST_USER_SIGNUP_DEFAULT_ROLES` (for the first user)

## Definition of Done

This task is accepted when:

- [ ] New entity exists for tenants with name, description, and access rules
- [ ] New entity exists for user-tenant-role associations
- [ ] `RoleEntity` supports tenant scoping (roles can belong to specific tenants)
- [ ] Identity provider implementations no longer fetch or sync roles
- [ ] Database initialization creates a default tenant with system roles on first startup
- [ ] New users are automatically added to default tenant with appropriate roles
- [ ] First user receives admin roles, subsequent users receive standard roles
- [ ] All configuration options documented in `.env.dev`
- [ ] System still functions in single-tenant mode (all users in default tenant)
- [ ] Existing tests pass

## Hints

- Look at how `initialize_roles()` currently works - extend this pattern for tenant initialization
- Consider how MongoDB indexes need to change for `RoleEntity` (tenant + name uniqueness)
- The user signup flow should be integrated into wherever `UserEntity.ensure_user_exists()` is called
- Think about the relationship between global system roles (superuser) and tenant-scoped roles
