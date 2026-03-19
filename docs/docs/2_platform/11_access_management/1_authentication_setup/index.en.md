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
- **Development Mode**: Dangerous dev-only handler (never use in production!)

### 2. User Resolution

Auth handlers automatically create or update users on first login:

```python
user_entity = UserEntity.ensure_user_exists_for_auth(
    oid=user_id,
    name=user_name,
    email=user_email,
)
```

**First User Behavior**: The first user to authenticate automatically receives admin roles. Subsequent users receive
standard user roles (configurable via `UserSignupSettings`).

### 3. Tenant Context Resolution

Every authenticated request must have a tenant context:

```python
# Extract from x-tenant-id header or fall back to default tenant
tenant = TenantIdentity.from_request_for_user(request, user_id)

# Verify user has access to this tenant
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

**Tenant Header**: Clients should include `x-tenant-id: <tenant-id>` header in requests. If omitted, the default tenant
is used.

### 4. UserIdentity Construction

Auth handlers return a `UserIdentity` that includes both user and tenant information:

```python
return UserIdentity(
    id=user.id,
    name=user.name,
    email=user.email,
    roles=user.get_roles(tenant.id),
    acting_within_tenant=tenant,
)
```

## Multi-Tenant Role Management

### Core Entities

**TenantEntity**

- Defines organizational boundaries
- Contains `access_rules` that limit what ANY user in the tenant can access
- Example: `["aihub.user.agent.>"]` grants user-level access to all agents

**UserTenantRoleEntity**

- Maps users to tenants with specific roles
- Authoritative source for user-tenant-role relationships
- Users can have different roles in different tenants

**RoleEntity**

- Defines roles with optional tenant scoping
- System roles: `tenant_id=None` (available to all tenants)
- Tenant-specific roles: `tenant_id=<specific-tenant>` (only for that tenant)

**UserEntity**

- Stores user profile data (name, email, etc.)
- **Does NOT store roles** - roles are fetched from `UserTenantRoleEntity`

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
# Default Tenant Configuration
AIHUB_DEFAULT_TENANT_NAME="Default Organization"
AIHUB_DEFAULT_TENANT_DESCRIPTION="The default organization for all users."
AIHUB_DEFAULT_TENANT_ACCESS_RULES="aihub.admin.>"

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
from aihub_lib.infrastructure.api.DefaultTenantSettings import DefaultTenantSettings
from aihub_lib.infrastructure.api.UserSignupSettings import UserSignupSettings

# Access default tenant settings
tenant_settings = DefaultTenantSettings()
print(tenant_settings.default_access_rules_list)  # ['aihub.admin.>']

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

**Cause**: Tenant access rules are limiting user permissions.

**Solution**: Check tenant access rules:

```python
tenant = TenantEntity.get_tenant_by_id(tenant_id)
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

- **Never use DangerousDevelopmentOnlyAuthHandler in production** - it bypasses all security
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
