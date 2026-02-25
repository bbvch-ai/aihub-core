# Introduce Global Superuser Authentication for Docker Compose and Backend-Only Deployments

> **Partially superseded** by [2025_12_25_local_role_management](./2025_12_25_local_role_management.md): The
> `SUPERUSER_ENABLED` toggle and `SuperuserIdentityProvider` were removed. Superuser authentication is now always
> available (via `SuperuserAuthHandler`) and operates within a virtual `__superuser_tenant__` tenant context. The
> `IdentityProvider` abstraction no longer exists.

## Context

The AI-Hub platform faced critical authentication gaps that prevented seamless deployment and integration in two key
scenarios:

### Problem 1: Docker Compose Integration Challenge

When using `docker-compose up` to start the entire AI-Hub ecosystem, external services (monitoring, proxies, third-party
integrations) had no way to authenticate with AI-Hub services out-of-the-box. The existing authentication options were
inadequate:

- **DangerousDevelopmentOnlyAuthHandler**: Completely disables authentication and security - acceptable only for local
  testing, not for any production-like environment
- **Token-based authentication**: Requires manual database setup to create tokens before services can authenticate,
  breaking the "docker-compose up and go" experience
- **OAuth2/MSAL authentication**: Requires external identity providers that aren't available in containerized
  environments

### Problem 2: Backend-Only Customer Deployments

Some customers deploy AI-Hub purely as a backend service without any identity provider integration (no Azure MSAL, LDAP,
etc.). Our existing authentication system always required an identity provider, even for token-based authentication,
leaving these customers without viable authentication options.

### Inspiration from LiteLLM

LiteLLM solves similar challenges by providing a global master key that can be configured via environment variables,
enabling immediate authentication for all services without complex setup procedures.

## Decision Drivers

- **Docker Compose Simplicity**: Enable `docker-compose up` to work out-of-the-box without manual token creation or
  database initialization
- **Backend-Only Customer Support**: Provide authentication for customers who use AI-Hub purely as a backend without
  identity providers
- **Environment Variable Configuration**: Follow industry patterns (like LiteLLM) for simple environment-based
  authentication setup
- **Service Integration**: Enable external Docker services to authenticate with AI-Hub immediately upon startup
- **Security by Choice**: Provide a secure authentication method that can be completely disabled when not needed
- **Identity Provider Independence**: Remove the hard requirement for external identity providers in all authentication
  scenarios

## Decision

We will implement a **Global Superuser Authentication System** that solves the Docker Compose and backend-only
deployment challenges through a simple, LiteLLM-inspired approach:

### Core Solution: Environment-Based Global Token

- A single `SUPERUSER_TOKEN` environment variable that can be set in both AI-Hub services and external services
- No database setup required - the superuser is defined entirely through environment variables
- Immediate authentication capability upon service startup
- Self-contained identity provider that doesn't require external systems

### Implementation Components:

### 1. SuperuserAuthHandler

- Token-based authentication handler that validates against a configurable superuser token
- Integrates with the existing authentication middleware and permission system
- Follows the same patterns as other authentication handlers (OAuth2, Token, etc.)

### 2. SuperuserIdentityProvider

- Provides user identity information for the superuser account
- Returns a configured `UserIdentity` with full administrative privileges
- Supports the standard identity provider interface for consistency

### 3. SuperuserSettings Configuration

- Environment-driven configuration for superuser credentials and settings
- Configurable enable/disable flag (`SUPERUSER_ENABLED`) for security control
- Full user profile configuration (name, email, OID, roles) through environment variables
- Secure token-based authentication (`SUPERUSER_TOKEN`)

### 4. Database Integration

- Automatic superuser account creation during database initialization
- Ensures superuser exists in the user management system for proper access control
- Role-based permission assignment for the superuser account

### 5. Security Controls

- **Configurable Enablement**: Can be completely disabled via `SUPERUSER_ENABLED=false`
- **Token-Based Security**: Uses secure token authentication (not password-based)
- **Role-Based Access**: Superuser receives "AIHubSuperuser" role with appropriate permissions
- **Audit Trail**: All superuser actions are logged and traceable like any other user

## Consequences

### Positive

- **True "Docker Compose Up" Experience**: External services can authenticate immediately without manual token creation
  or database setup
- **Backend-Only Customer Support**: Customers without identity providers finally have a viable authentication option
- **Environment Variable Simplicity**: Following LiteLLM's pattern, configuration is as simple as setting
  `SUPERUSER_TOKEN=your_token`
- **Self-Contained Authentication**: No dependency on external identity providers or manual database initialization
- **Immediate Service Integration**: Docker containers can authenticate with AI-Hub API from the moment they start
- **Consistent Architecture**: Uses the same authentication patterns and permission system as other auth handlers
- **Security by Design**: Can be completely disabled via `SUPERUSER_ENABLED=false` when not needed
- **Audit Compliance**: All superuser actions are tracked and auditable through standard logging

### Negative

- **Global Token Security Risk**: A single token that grants access to everything represents a high-value target if
  compromised
- **Token Management Responsibility**: Teams must implement proper token rotation and secure storage practices
- **Potential Overuse**: May be used as a convenient shortcut instead of implementing proper service-specific
  authentication
- **Environment Variable Exposure**: Tokens in environment variables can be visible in process lists or container
  configurations
- **Operational Security**: Requires careful management to prevent token leakage in logs, error messages, or
  configuration files

### Neutral

- **Additional Authentication Strategy**: Expands the authentication system with another handler type
- **Environment Configuration**: Requires proper setup of superuser environment variables in deployment
- **Documentation Requirements**: Need for clear guidance on when and how to use superuser authentication
- **Monitoring Considerations**: Superuser actions should be monitored and alerted appropriately
- **Role Management**: The "AIHubSuperuser" role needs proper permission configuration and maintenance

## Security Considerations

This decision introduces a powerful authentication mechanism that requires careful security practices:

1. **Token Security**: The `SUPERUSER_TOKEN` must be treated as a critical secret with proper rotation policies
2. **Network Security**: Superuser authentication should only be used within secure network boundaries
3. **Monitoring**: All superuser actions should be monitored and logged for security analysis
4. **Least Privilege**: Despite being "super", the user still operates within the role-based permission system
5. **Disable in Production**: Consider disabling superuser authentication in high-security production environments where
   service-to-service authentication can be handled through other mechanisms
