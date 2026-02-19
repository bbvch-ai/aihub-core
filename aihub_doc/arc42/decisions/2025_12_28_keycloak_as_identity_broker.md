# Keycloak as Identity Broker for Swiss AI-Hub

## Context

Swiss AI-Hub requires enterprise-grade authentication supporting diverse deployment scenarios: local development without
external dependencies, on-premise installations with customer-specific identity providers, and cloud deployments with
Azure AD or Google Workspace. Previously, the platform integrated directly with Azure AD via the Microsoft Graph API,
creating tight coupling to a single identity provider and making local development and testing cumbersome.

The platform needed a unified authentication interface that all services (Admin UI, OpenWebUI, API, Agents, Pipelines)
could rely on, regardless of which upstream identity provider the customer uses. At the same time, the platform's own
role management (tenant-based AI-Hub roles like data access, agent permissions, workflow assignments) must remain
independent from any external identity provider.

## Decision Drivers

- **Uniform Interface for All Services**: Every AI-Hub component must authenticate against a single, predictable OIDC
  endpoint. This eliminates provider-specific code paths and reduces the surface area for authentication bugs.
- **IdP Independence**: Customers bring their own identity providers (Azure AD, Google, Okta, SAML-based systems). The
  platform must not be coupled to any specific one.
- **Swiss Data Sovereignty**: Self-hosted identity management aligns with the platform's privacy-first philosophy. No
  authentication data leaves the customer's infrastructure.
- **Development and Testing**: Local development and E2E testing must work without external IdP dependencies, using
  reproducible, configurable credentials.
- **Separation of Access Control and Role Management**: The identity provider handles *who may access the platform*
  (authentication + coarse access roles). The platform itself handles *what users may do within it* (fine-grained
  AI-Hub roles and permissions).

## Decision

**Keycloak is the sole OAuth2/OIDC identity provider for Swiss AI-Hub.** All platform services authenticate exclusively
against Keycloak. Keycloak acts as an identity broker, federating authentication to upstream providers (Azure AD, Google,
SAML, local users) as configured per deployment.

### Key Principles

1. **Single Authentication Interface**: All services (Admin UI, OpenWebUI, API, OAuth2 Proxy for admin tools) use
   Keycloak's OIDC endpoints. There is no `IDENTITY_PROVIDER` switch or provider-specific auth handler in the
   application code—only `KeycloakAuthHandler`.

2. **Keycloak Owns Access Gating, Not AI-Hub Roles**: Keycloak manages realm-level roles that determine *whether*
   a user may access the platform at all:
   - `AIHubAdmin` — administrative access
   - `AIHubUser` — standard access
   - `AIHubDeveloper` — developer tools access
   - `AIHubSysAdmin` — system administrator access to infrastructure tools (Dagster, SeaweedFS, Attu)

   These roles are mapped from the upstream IdP's claims (e.g., Azure AD app role assignments → Keycloak realm roles via
   identity provider mappers). The upstream IdP only needs to provide the role claims required to grant platform access.

3. **AI-Hub Manages Its Own Roles Locally**: All fine-grained, domain-specific role management (tenant assignments,
   agent permissions, data access controls, workflow authorizations) is handled by the platform's local role management
   system (see ADR `2025_12_25_local_role_management.md`). Keycloak has no knowledge of these roles. This separation
   ensures that:
   - Onboarding a new IdP only requires configuring role mapping for the access roles
   - AI-Hub's permission model is portable across any identity provider
   - Role changes within the platform do not require IdP administrator involvement

4. **Identity Broker Pattern**: Keycloak federates to upstream providers. The platform never communicates with Azure AD,
   Google, or any other IdP directly. Adding a new upstream provider is a Keycloak configuration task, not a code change.

### Implementation

- **Infrastructure**: Keycloak 26.0 (LTS) runs as a Docker Compose service with PostgreSQL backend. Dev environments
  expose port 8180 directly; production deployments route through Traefik at `auth.${DOMAIN}`.
- **Realm Configuration**: A Jinja2 template (`keycloak-realm.json.j2`) generates stage-specific realm configs with
  appropriate SSL settings, client configurations, and (in dev) a pre-configured test user.
- **Auth Handler**: `KeycloakAuthHandler` validates JWTs using Keycloak's JWKS endpoint with 6-hour caching. User data
  is extracted directly from JWT claims—no external API calls during authentication.
- **OAuth2 Clients**: Three OIDC clients are configured:
  - `aihub-frontend` — public client with PKCE for the Admin UI
  - `openwebui` — confidential client for the chat interface
  - `aihub-api` — confidential service account client for backend-to-backend communication
- **Admin Tool Protection**: OAuth2 Proxy instances protect Dagster, Attu (Milvus), and SeaweedFS using Keycloak as the
  OIDC provider with role-based access control.
- **Split-Horizon DNS**: Non-dev deployments configure separate internal (`http://keycloak:8080`) and external
  (`https://auth.${DOMAIN}`) URLs to handle Docker network vs. browser access patterns.

## Consequences

### Positive

- All services use one authentication interface — no provider-specific code paths
- Adding a new upstream IdP (e.g., switching from Azure AD to Okta) is a Keycloak admin task, zero code changes
- Local development works out of the box with a configurable dev user, no external IdP required
- E2E tests use reproducible, known credentials against a local Keycloak instance
- AI-Hub role management is fully decoupled from the identity provider
- Self-hosted authentication aligns with Swiss data sovereignty requirements

### Negative

- Additional infrastructure component (Keycloak + PostgreSQL database) to operate and maintain
- Keycloak requires ~512MB RAM and adds startup time to the Docker Compose stack
- Team needs Keycloak administration knowledge for realm and identity provider configuration
- Split-horizon DNS configuration adds deployment complexity for non-dev environments

### Related Decisions

- `2025_12_25_local_role_management.md` — Complements this decision by defining how AI-Hub manages its own roles
  independently from any identity provider
- `2025_08_11_global_superuser_authentication.md` — Superuser token auth remains as a parallel bearer-based
  authentication path for Docker Compose deployments without a browser
