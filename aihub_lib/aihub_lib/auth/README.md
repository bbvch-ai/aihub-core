---
title: Authentication & Authorization System
---

# Authentication & Authorization System

## Overview

The AI-Hub authentication system provides enterprise-grade security through a modular architecture that separates
authentication from authorization. The system supports multiple authentication strategies while maintaining a unified
authorization model based on hierarchical permissions.

## Architecture

### Core Components

The authentication system is built around these main abstractions:

- **AuthHandlers**: Validate credentials and return user identities (standalone classes, no inheritance required)
- **UserEntity**: Persistent user data with local role management
- **UserIdentity**: Lightweight DTO for authenticated users
- **AccessChecker**: Enforces hierarchical permission-based authorization
- **Multi-Tenant Roles**: Roles are managed locally, not fetched from identity providers

### Authentication Flow

1. **Credential Extraction**: AuthHandlers extract tokens/credentials from HTTP requests
2. **Token Validation**: Handlers validate tokens against their respective authorities (OAuth2, database tokens, etc.)
3. **User Resolution**: User data is fetched from UserEntity (local database)
4. **Identity Creation**: UserIdentity DTO is created from UserEntity
5. **Permission Evaluation**: AccessChecker determines user access levels based on locally-managed roles

### Key Design Decisions

- **Local Role Management**: Roles are stored in UserEntity and UserTenantRoleEntity, not fetched from identity providers
- **No Identity Provider Abstraction**: Auth handlers directly handle authentication without an intermediate IdentityProvider layer
- **Multi-Tenant Support**: Users can belong to multiple tenants with different roles in each

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

### Permission Templates

The system supports two types of permission checks:

1. **Direct Checks**: Verify access to specific resources
2. **Implicit Checks**: Verify if user has any matching access pattern (using `?*` and `?>`)

## Supported Authentication Strategies

### OAuth2 (Microsoft Azure AD)

- JWT token validation using JWKS
- Automatic token caching and RSA key management
- User profile fetched from Microsoft Graph API
- Roles managed locally (not synced from Azure AD)

### Token-Based Authentication

- Bearer token lookup in database
- Token expiration validation
- User identity from UserEntity

### Superuser Authentication

- Static token-based authentication for administrative access
- Configurable via environment variables
- Bypasses normal authentication flow

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
- Contains cached roles list (synced from tenant memberships)
- Additional user preferences (dashboard, favorite_modules)

### UserIdentity

- Lightweight Pydantic DTO for API responses
- Created from UserEntity via `UserIdentity.from_user_entity()`
- No database dependencies

### Multi-Tenant Roles

- TenantEntity: Organization/tenant definitions
- UserTenantRoleEntity: User-tenant-role associations
- RoleEntity: Role definitions with access rules
- First user signup automatically gets admin roles

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

The system powers all AI-Hub services and enables secure access to agents, processes, and administrative functions
through a unified security model.
