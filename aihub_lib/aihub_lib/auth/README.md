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

The authentication system is built around three main abstractions:

- **AuthHandlers**: Extract and validate authentication credentials from requests
- **IdentityProviders**: Retrieve user information from identity systems
- **AccessChecker**: Enforces hierarchical permission-based authorization

### Authentication Flow

1. **Credential Extraction**: AuthHandlers extract tokens/credentials from HTTP requests
1. **Token Validation**: Handlers validate tokens against their respective authorities
1. **Identity Resolution**: IdentityProviders fetch detailed user information
1. **Permission Evaluation**: AccessChecker determines user access levels

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
1. **Implicit Checks**: Verify if user has any matching access pattern (using `?*` and `?>`)

## Supported Authentication Strategies

### OAuth2 (Microsoft Azure AD)

- JWT token validation using JWKS
- Automatic token caching and RSA key management
- Claims mapping to user identity

### Token-Based Authentication

- Bearer token lookup in database
- Token expiration validation
- Direct user identity mapping

### Development Authentication

- Bypasses authentication for development environments
- Configurable mock user identities
- **WARNING**: Only for development use

### Multi-Strategy Support

- Combines OAuth2 and token authentication
- Fallback authentication mechanisms
- Flexible deployment configurations

## Identity Providers

### Azure Identity Provider

- Microsoft Graph API integration
- Automatic user profile synchronization
- Role and permission mapping from Azure AD

### Token Identity Provider

- Database-driven user management
- Custom role assignment
- Offline authentication support

## Key Features

- **Stateless Architecture**: All authentication state is contained in tokens
- **Caching**: Intelligent caching of JWKS keys and user data
- **Multi-Language Support**: Error messages support internationalization
- **Extensible Design**: Easy to add new authentication strategies
- **Enterprise Integration**: Native support for OAuth2 and enterprise identity systems
- **Security by Design**: Comprehensive validation and error handling

## Usage Context

This authentication system is designed for enterprise environments requiring:

- Multiple authentication methods
- Fine-grained authorization control
- Integration with existing identity providers
- Scalable, stateless operation
- Comprehensive audit trails

The system powers all AI-Hub services and enables secure access to agents, processes, and administrative functions
through a unified security model.
