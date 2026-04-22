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
- **KeycloakAdminService**: Reads user profile data and active tenant from Keycloak
- **UserIdentity**: Lightweight DTO for authenticated users
- **AccessChecker**: Enforces hierarchical permission-based authorization
- **Multi-Tenant Roles**: Roles are managed locally, not fetched from identity providers

### Authentication Flow

1. **Credential Extraction**: AuthHandlers extract tokens/credentials from HTTP requests
2. **Token Validation**: Handlers validate tokens against their respective authorities (OAuth2, database tokens, etc.)
3. **User Resolution**: User data is extracted from token claims (OAuth2) or Keycloak Admin API (Token auth)
4. **Tenant Sync**: Tenant memberships from the JWT `tenants` claim are synced to UserTenantRoleEntity
5. **Tenant Resolution**: Tenant context is resolved from the `tenant_id` path parameter. The special value `"active"`
   resolves to the user's active tenant stored as a Keycloak user attribute. If no active tenant is set, the request is
   rejected with a 400 error
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
- User identity from Keycloak via KeycloakAdminService

### Sysadmin Access

- Granted via the `AIHubSysAdmin` Keycloak realm role (carried on `UserIdentity.is_sys_admin`)
- Short-circuits `AccessChecker.access_level()` to `ACCESS_ADMIN` for every resource in every tenant
- Bypasses both the tenant-access-rules check and the `UserTenantRoleEntity` membership check
- No synthetic identity or "virtual tenant" — sysadmins are real Keycloak users with real ids
- The platform seeds a real Keycloak user from `SUPERUSER_USERNAME`/`SUPERUSER_EMAIL`/`SUPERUSER_PASSWORD`/
  `SUPERUSER_FIRSTNAME`/`SUPERUSER_LASTNAME`/`SUPERUSER_ROLES_JSON` in the realm import and materializes
  `SUPERUSER_TOKEN` as a regular bearer token bound to that user (validated by `TokenAuthHandler`, no dedicated handler)

### Development Authentication

- Bypasses authentication for development environments
- Configurable mock user identities
- **WARNING**: Only for development use

### Multi-Strategy Support

- Combines OAuth2 and token authentication via TokenAndOauth2Handler
- Fallback authentication mechanisms
- Flexible deployment configurations

## User & Role Management

### UserIdentity

- Lightweight Pydantic representation of authenticated users
- Constructed directly from JWT claims or Keycloak Admin API data
- **Always includes tenant context** via `acting_within_tenant: TenantIdentity`
- Roles are resolved for the specific tenant the user is acting within
- No database dependencies

### KeycloakAdminService

- Wraps Keycloak Admin API for user and group management
- User profile data (name, email) is read from Keycloak, not stored locally
- Active tenant is stored as a Keycloak user attribute (`active_tenant_id`)
- Tenant group membership is managed via Keycloak groups under `/tenants/`

### Multi-Tenant Roles

- **TenantMetadataEntity**: Display metadata (name, description, access_rules) for a tenant. **NOT** the source of truth
  for tenant existence — the Keycloak group `/tenants/<id>` is authoritative. Verify existence via
  `KeycloakAdminService.tenant_exists()` before trusting metadata.
- **UserTenantRoleEntity**: Authoritative source for user-tenant-role associations
- **RoleEntity**: Role definitions with access rules. Every role belongs to exactly one tenant — `tenant_id` is
  required. System-wide roles no longer exist; see ADR `2026_04_14_tenant_scoped_roles.md`.
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
