---
title: Authentication & Authorization System
---

# Authentication & Authorization System

## Overview

The Swiss AI Hub authentication system provides enterprise-grade security through a modular architecture that separates
authentication from authorization. The system supports multiple authentication strategies while maintaining a unified
authorization model based on hierarchical permissions.

## Architecture

### Core Components

The authentication system is built around these main abstractions:

- **AuthHandlers**: Validate credentials and return user identities
- **UserEntity**: Persistent user data with local role management
- **UserIdentity**: Lightweight DTO for authenticated users
- **AccessChecker**: Enforces hierarchical permission-based authorization
- **Multi-Tenant Roles**: Roles are managed locally, not fetched from identity providers

### Authentication Flow

1. **Credential Extraction**: AuthHandlers extract tokens/credentials from HTTP requests
2. **Token Validation**: Handlers validate tokens against their respective authorities (OAuth2, database tokens, etc.)
3. **User Resolution**: User data is extracted from token claims (OAuth2) or database lookup (Token auth)
4. **User Persistence**: User is created or updated in UserEntity via `ensure_user_exists_for_auth()`
5. **Tenant Resolution**: Tenant context is resolved from the `tenant_id` path parameter. The special value `"active"`
   resolves to the user's persisted active tenant. If no active tenant is set, the request is rejected with a 400 error
6. **Membership Verification**: User's membership in the tenant is verified via UserTenantRoleEntity
7. **Identity Creation**: UserIdentity DTO is created with embedded TenantIdentity
8. **Permission Evaluation**: AccessChecker performs two-stage authorization (tenant + user) based on locally-managed
   roles

## Permission System

### Hierarchical Access Rules

The system uses dot-notation permissions with wildcard support:

- `aihub.user.agent.class_a.id_123` - Specific resource access
- `aihub.user.agent.class_a.*` - All resources in class
- `aihub.user.agent.class_a.?>` - Recursive access to all subresources

### Access Levels

- **ACCESS_DENIED**: No access to the resource
- **ACCESS_USER**: Standard user-level access
- **ACCESS_ADMIN**: Administrative access (includes user privileges)

### Two-Stage Access Control (Tenant + User)

**CRITICAL**: AccessChecker performs authorization in TWO stages with tenant access rules acting as a ceiling:

1. **STAGE 1**: Determine tenant's access level (what the tenant allows)
2. **STAGE 2**: Determine user's access level (what the user has been granted)
3. **STAGE 3**: Return the MINIMUM of both levels

**Key Behaviors**:

- If tenant has no matching access rules for a resource, access is DENIED regardless of user permissions
- If tenant has only user-level access, admin users are capped at user-level access
- Both tenant AND user must have matching permissions for access to be granted

**Example**: Even if a user has `aihub.admin.agent.>` role, if their tenant only has `aihub.user.agent.>` access rules,
the user gets user-level access (not admin).

### Permission Templates

The system supports two types of permission checks:

1. **Direct Checks**: Verify access to specific resources
2. **Implicit Checks**: Verify if user has any matching access pattern (using `?*` and `?>`)

## Supported Authentication Strategies

### OAuth2

- JWT token validation using JWKS
- Automatic token caching and RSA key management
- User profile data (name, email, oid) extracted directly from JWT claims
- No external API calls to Microsoft Graph
- Roles managed locally in UserTenantRoleEntity (not synced from Azure AD)

### Token-Based Authentication

- Bearer token lookup in database
- Token expiration validation
- User identity from UserEntity to which the token belongs

### Superuser Authentication

- Static token-based authentication for administrative access
- Operates within a virtual "superuser tenant" with `aihub.admin.>` access rules
- Bypasses tenant restrictions while still going through two-stage access control
- Virtual tenant ensures all permission checks pass (tenant grants admin, user has admin)
- Configurable via environment variables (SUPERUSER_TOKEN, SUPERUSER_OID, etc.)

### Development Authentication

- Bypasses authentication for development environments
- Configurable mock user identities
- **WARNING**: Only for development use

### Multi-Strategy Support

- Combines OAuth2 and token authentication via TokenAndOauth2Handler
- Fallback authentication mechanisms
- Flexible deployment configurations

## User & Role Management

### UserEntity

- Persisted in MongoDB users collection
- Contains profile info (name, email, profile_image)
- **Does NOT store roles** - roles are fetched from UserTenantRoleEntity via `get_roles(tenant_id)`
- Profile images must be valid http:// or https:// URLs (data URLs not allowed)
- Additional user preferences (dashboard, favorite_modules)

### UserIdentity

- Lightweight Pydantic representation of authenticated users
- Created from UserEntity via `UserIdentity.from_user_entity(user, tenant)`
- **Always includes tenant context** via `acting_within_tenant: TenantIdentity`
- Roles are resolved for the specific tenant the user is acting within
- No database dependencies

### Multi-Tenant Roles

- **TenantEntity**: Organization/tenant definitions with `access_rules` that define maximum permissions for all users
- **UserTenantRoleEntity**: Authoritative source for user-tenant-role associations (replaces UserEntity.roles)
- **RoleEntity**: Role definitions with access rules, can be system-wide (`tenant_id=None`) or tenant-scoped
- **TenantIdentity**: Resolved from `tenant_id` path parameter. No implicit fallback — an active tenant must be
  explicitly set
- First user signup automatically gets admin roles in default tenant (configurable via UserSignupSettings)

## Key Features

- **Stateless Architecture**: All authentication state is contained in tokens
- **Caching**: Intelligent caching of JWKS keys and user profiles
- **Multi-Language Support**: Error messages support internationalization
- **Extensible Design**: Easy to add new authentication strategies
- **Enterprise Integration**: Native support for OAuth2 and enterprise identity systems
- **Security by Design**: Comprehensive validation and error handling
- **Local Role Management**: No dependency on external role providers

## Usage Context

This authentication system is designed for enterprise environments requiring:

- Multiple authentication methods
- Fine-grained authorization control
- Local role management independent of identity providers
- Multi-tenant support
- Scalable, stateless operation
- Comprehensive audit trails

The system powers all Swiss AI Hub services and enables secure access to agents, processes, and administrative functions
through a unified security model.
