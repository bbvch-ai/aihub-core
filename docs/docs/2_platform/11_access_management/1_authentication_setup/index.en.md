---
title: Authentication Setup
---

# Authentication Setup

Swiss AI Hub uses a multi-tenant authentication and authorization system with local role management.

## Overview

The authentication system consists of several key components:

- **Auth Handlers**: Validate credentials and resolve user identity
- **Identity Models**: `UserIdentity` and `TenantIdentity` represent authenticated users and their tenant context
- **Access Control**: `AccessChecker` enforces permissions based on hierarchical access rules
- **Multi-Tenancy**: All operations occur within a tenant context

## Authentication Flow

### 1. Token Validation

Auth handlers validate incoming requests and extract user information:

```python
# Keycloak OIDC JWT validation
user_identity = await KeycloakAuthHandler()(request)

# Token-based authentication
user_identity = await TokenAuthHandler()(request)
```

Supported authentication methods:

- **OAuth2/OIDC**: JWT tokens from Keycloak (supports federated identity providers like Azure AD, Google, etc.)
- **API Tokens**: Long-lived tokens for programmatic access
- **OpenWebUI Integration**: Special handler for OpenWebUI users

For tests and interactive playground servers, a dedicated `TestAuthHandler` lives under
`swiss_ai_hub.core.testing.auth_utils` (not `core.auth`) and bypasses token parsing to return a fixed test identity. It
is deliberately not reachable from production code via the public auth interface.

### 2. User Resolution

User profile data (name, email) is read from JWT claims for OAuth2 flows or fetched via `KeycloakAdminService` for
bearer tokens. There is no local user record — Keycloak is the single source of truth for user identity.

**First User Behavior**: The first user to join a tenant automatically receives admin roles. Subsequent users receive
standard user roles (configurable via `UserSignupSettings`). This applies per-tenant, not globally, and is enforced in
`UserTenantRoleEntity` when a new membership is created.

### 3. Tenant Context Resolution

Most authenticated requests have a tenant context. The tenant is identified via a `{tenant_id}` path parameter in the
URL — most API routes are mounted at `/api/v1/{tenant_id}/...`. Sysadmin-only endpoints (e.g. the tenant administration
controller) are mounted globally without a tenant prefix.

Tenant resolution is handled inside `AuthHandler.build_identity()` and `AuthHandler._resolve_tenant_by_id()`. The latter
consults `KeycloakAdminService.tenant_exists()` first — Keycloak is the authority on whether a tenant exists — and only
then checks `UserTenantRoleEntity` membership. The membership check is skipped entirely for sysadmins (see "Sysadmin
access" below). Controllers do not call these resolvers directly; they are wired into `user_with_permission()` and
`sys_admin_user()`.

**Tenant Path Parameter**: All API requests must include the `{tenant_id}` in the URL path. Two formats are supported:

- **Concrete ID**: `/api/v1/507f1f77bcf86cd799439011/agents/...` — directly specifies the tenant by MongoDB ObjectId
- **Active slug**: `/api/v1/active/agents/...` — resolves to the user's persisted active tenant

The active tenant is never automatically updated during request resolution. It can only be changed via a dedicated API
endpoint. Health endpoints remain outside tenant scope at `/api/v1/health/`.

### 4. UserIdentity Construction

Auth handlers return a `UserIdentity` that includes both user and tenant information:

```python
return UserIdentity(
    id=user.id,
    name=user.name,
    email=user.email,
    roles=roles,
    acting_within_tenant=tenant,  # may be None for sysadmin-only requests
    is_sys_admin=is_sys_admin,    # derived from the AIHubSysAdmin Keycloak realm role
)
```

The `is_sys_admin` flag is the single signal for platform-admin status — it short-circuits the access checker (see
"Sysadmin access" below) and is the basis for the `Controller.sys_admin_user()` dependency that gates sysadmin-only
endpoints.

## Multi-Tenant Role Management

### Core Entities

**TenantMetadataEntity**

- Holds display metadata (name, description, access rules) for a tenant
- **NOT** the source of truth for tenant existence — the Keycloak group `/tenants/<id>` is authoritative. Service code
  must verify existence via `KeycloakAdminService.tenant_exists()` before trusting metadata.
- Contains `access_rules` that cap what ANY user in the tenant can access
- Example: `["aihub.user.agent.>"]` grants user-level access to all agents

**UserTenantRoleEntity**

- Maps users to tenants with specific roles
- Authoritative source for user-tenant-role relationships
- Users can have different roles in different tenants

**RoleEntity**

- Every role belongs to exactly one tenant — `tenant_id` is required
- The default role set (`AIHubUser`, `AIHubAdmin`, `AIHubAgentUser`, etc.) is seeded per tenant at creation time
- System-wide roles no longer exist; see ADR `2026_04_14_tenant_scoped_roles.md`

**User profile data**

- Stored in Keycloak, not locally — `KeycloakAdminService.get_user_by_id()` / `find_user_by_email()` for lookup
- Name, email, and identity attributes all flow from Keycloak; the platform writes nothing to user records
- Roles are NOT attached to the user record — they are fetched from `UserTenantRoleEntity` per tenant

### Accessing User Roles

```python
# Get user's roles in a specific tenant
roles = user.get_roles(tenant_id)

# Get all access rules for a user in a tenant
access_rules = RoleEntity.get_access_rules_for_roles(roles, tenant_id=tenant_id)
```

## Access Control

### AccessChecker

The `AccessChecker` class performs authorization checks with two-stage access control:

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

# Create checker from UserIdentity (includes tenant context)
checker = AccessChecker.from_user(user)

# Check access level
level = checker.access_level("aihub.user.agent.class-a.id-123")
# Returns: AccessLevel.ACCESS_ADMIN | ACCESS_USER | ACCESS_DENIED
```

### Two-Stage Access Checking

**CRITICAL**: Tenant access rules act as a CEILING/BOUNDARY for user permissions.

1. **STAGE 1**: Determine tenant's access level (admin or user)
2. **STAGE 2**: Determine user's access level (admin or user)
3. **STAGE 3**: Return MINIMUM of both levels

**Example**:

```python
# Tenant has: aihub.user.agent.> (user-level access to all agents)
# User has: aihub.admin.agent.> (admin-level access to all agents)

# User gets ACCESS_USER (capped by tenant boundary)
checker.access_level("aihub.user.agent.class-a.id-1")  # → ACCESS_USER
```

### Access Rule Format

Access rules follow a hierarchical dot-notation:

```
aihub.[admin|user].<resource>.<subresource>.<id>
```

**Wildcards**:

- `*` - Single-level wildcard: `aihub.user.agent.*` matches any single agent
- `>` - Multi-level wildcard: `aihub.user.agent.>` matches all agents and sub-resources

**Examples**:

```python
"aihub.admin.>"                    # Full admin access to everything
"aihub.user.>"                     # Full user access to everything
"aihub.user.agent.>"               # User access to all agents
"aihub.user.agent.class-a.*"       # User access to all class-a agents
"aihub.user.agent.class-a.id-123"  # User access to specific agent
```

### Convenience Methods

```python
# Check specific agent access
has_access = checker.has_access_to_agent("class-a", "id-123")
access_level = checker.access_level_for_agent("class-a", "id-123")

# Check agent class access
has_access = checker.has_access_to_agent_class("class-a")

# Check process access
has_access = checker.has_access_to_process("workflow", "proc-456")

# Check service access
has_access = checker.has_access_to_service("llm-gateway")
```

## Configuration

### Environment Variables

```bash
# Startup Tenant Configuration (seeded on first boot; an ordinary tenant thereafter)
AIHUB_STARTUP_TENANT_NAME="Default Organization"
AIHUB_STARTUP_TENANT_DESCRIPTION="The default organization for all users."
AIHUB_STARTUP_TENANT_ACCESS_RULES="aihub.admin.>"

# User Signup Role Assignment
AIHUB_USER_SIGNUP_DEFAULT_ROLES="AIHubUser"
AIHUB_USER_SIGNUP_REGULAR_USER_ROLES="AIHubUser"
AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES="AIHubAdmin,AIHubUser"

# OAuth2 Configuration
OAUTH2_ENABLED=true
OAUTH2_JWKS_URL="https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
OAUTH2_ISSUER="https://login.microsoftonline.com/{tenant}/v2.0"
OAUTH2_AUDIENCE="api://{app-id}"
```

### Settings Classes

```python
from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
from swiss_ai_hub.core.infrastructure.api.user_signup_settings import UserSignupSettings

# Access startup tenant settings
tenant_settings = StartupTenantSettings()
print(tenant_settings.access_rules_list)  # ['aihub.admin.>']

# Access user signup settings
signup_settings = UserSignupSettings()
print(signup_settings.first_admin_user_roles_list)  # ['AIHubAdmin', 'AIHubUser']
```

## Best Practices

### 1. Always Provide Tenant Context

Never create `AccessChecker` without tenant access rules:

```python
# ❌ BAD: Manual construction without tenant context
checker = AccessChecker(user_access_rules, [])

# ✅ GOOD: Use factory method that extracts both user and tenant rules
checker = AccessChecker.from_user(user)  # user is UserIdentity with tenant context
```

### 2. Verify Tenant Membership

Always verify users have access to the tenant before performing operations:

```python
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

### 3. Use the Minimum Required Access Level

Grant users the minimum access level needed for their role:

```python
# ❌ BAD: Over-permissive
access_rules = ["aihub.admin.>"]

# ✅ GOOD: Scoped to specific resources
access_rules = ["aihub.user.agent.class-a.>"]
```

### 4. Tenant Access Rules as Boundaries

Use tenant access rules to limit the scope of ALL users in a tenant:

```python
# Tenant for analytics team - only access to specific agent classes
tenant_access_rules = [
    "aihub.user.agent.analytics.*",
    "aihub.user.service.data-pipeline"
]

# Even admin users in this tenant cannot access other resources
```

## Troubleshooting

### "User not assigned to tenant" Error

**Cause**: User exists but doesn't have any roles in the requested tenant.

**Solution**: Assign user to tenant with roles:

```python
UserTenantRoleEntity.create_or_update(
    user_id=user_id,
    tenant_id=tenant_id,
    roles=["AIHubUser"]
)
```

### "Access Denied" Despite User Having Admin Roles

**Cause**: Tenant access rules are limiting user permissions. (Sysadmins — users with the `AIHubSysAdmin` Keycloak realm
role — bypass this check entirely; if the issue persists for a sysadmin, the bypass itself is misconfigured.)

**Solution**: Check tenant access rules:

```python
tenant = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
print(tenant.access_rules)  # Check what the tenant allows
```

### Empty Tenant Access Rules = No Access

If a tenant has no access rules (`[]`), ALL users in that tenant are denied access to everything.

**Solution**: Set appropriate tenant access rules:

```python
tenant.access_rules = ["aihub.user.>"]
tenant.save()
```

## Security Considerations

- **Never mount `TestAuthHandler` on production entry points** — it lives under `core.testing` for this reason;
  production `app/main.py` files must use `KeycloakAuthHandler` or `TokenAuthHandler`
- **Validate JWTs properly** - always verify issuer, audience, and signature
- **Use HTTPS** - never transmit tokens over unencrypted connections
- **Rotate API tokens regularly** - implement token expiration and rotation
- **Audit access control changes** - log all role and permission modifications
- **Principle of least privilege** - grant minimum required access
- **Tenant isolation** - users cannot access resources outside their tenant's boundaries

## Migration from Previous System

Previous versions fetched roles from Azure AD via Microsoft Graph API. The new system:

- ✅ **Stores roles locally** in `UserTenantRoleEntity`
- ✅ **No external API calls** during authentication
- ✅ **Tenant-scoped roles** for multi-tenancy
- ❌ **No automatic role sync** from identity provider
- ❌ **No automatic profile image fetching** from identity provider

See [ADR: Local Multi-Tenant Role Management](/arc42/decisions/2025_12_25_local_role_management.md) for details.
