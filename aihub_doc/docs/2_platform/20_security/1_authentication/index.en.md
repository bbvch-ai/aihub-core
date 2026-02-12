---
title: Authentication and Authorization
---

# TODO: @mhoegger verify

# Authentication and Authorization

The Swiss AI-Hub implements authentication and authorization based on industry-standard OpenID Connect (OIDC) and OAuth
2.0 protocols. This standards-based approach ensures compatibility with enterprise identity providers while maintaining
secure access control across all platform resources.

## Authentication: OpenID Connect (OIDC)

The platform authenticates users through OpenID Connect, an identity layer built on top of OAuth 2.0. This enables
secure user authentication through enterprise identity providers such as Microsoft Entra ID (Azure Active Directory)
while supporting the OAuth 2.0 Authorization Code Flow.

### How Authentication Works

**Token-Based Authentication:** Users authenticate through their organization's identity provider, which issues a JSON
Web Token (JWT) containing cryptographically signed claims about the user's identity. The platform validates these
tokens on every request to ensure authenticity and freshness.

**JWT Token Validation:** The platform retrieves public keys from the identity provider's JWKS (JSON Web Key Set)
endpoint and uses them to verify the cryptographic signature of each JWT token. This validation includes checking the
token's issuer, audience, expiration time, and signature integrity according to the JWT standard (RFC 7519).

**User Identity Resolution:** After successful token validation, the platform extracts the user's unique identifier
(OID) from the token claims and retrieves complete user information including name, email, and role assignments from the
identity provider through the Microsoft Graph API.

### Supported Authentication Methods

**OAuth 2.0 Authorization Code Flow:** The primary authentication method for interactive users follows the OAuth 2.0
Authorization Code Flow with PKCE (Proof Key for Code Exchange). Users are redirected to their organization's identity
provider for authentication, and upon successful login, receive a secure authorization code that is exchanged for access
tokens.

**Bearer Token Authentication:** For API access and programmatic integrations, the platform supports standard OAuth 2.0
Bearer Token authentication. API clients present valid JWT tokens in the HTTP Authorization header, which are validated
using the same JWKS-based verification process.

## Authorization: Permission-Based Access Control

Authorization is implemented independently from authentication, enabling consistent access control regardless of how
users authenticate. The platform evaluates permissions for every API request based on the user's assigned roles and the
hierarchical permission model described in the [Permissions](../../11_access_management/2_permissions/).

### Enterprise Identity Provider Integration

The platform integrates with enterprise identity providers through standard OIDC/OAuth 2.0 protocols. The primary
integration point is Microsoft Entra ID (Azure Active Directory), with support for extensibility to other OIDC-compliant
identity providers.

**Microsoft Entra ID Integration:** The platform connects to Microsoft Entra ID as an OAuth 2.0 authorization server and
OIDC identity provider. User authentication is delegated to Entra ID, which handles credential validation, multi-factor
authentication, and session management according to the organization's security policies.

**User Profile and Role Retrieval:** After authentication, the platform queries the Microsoft Graph API to retrieve
complete user profiles including display name, email address, and organizational group memberships. These group
memberships are mapped to platform roles, which determine the user's access permissions within the AI-Hub.

### How Authorization Works

Authorization decisions are made independently from authentication. After a user's identity is established through OIDC
authentication, the platform determines what resources and operations the user can access based on their assigned roles.

**Permission Evaluation Process:**

1. The platform extracts the user's role assignments from the identity provider
2. Each role is associated with a set of access rules stored in the platform database
3. For every API request, the platform evaluates the required permission against the user's access rules
4. Access rules support hierarchical matching with wildcard patterns for flexible permission management
5. The authorization decision (grant or deny) is made and logged for audit purposes

**API-Level Permission Enforcement:** Every API endpoint declares its required permissions. These permissions are
automatically checked before the endpoint logic executes, ensuring no resource access bypasses authorization. The
permission evaluation uses the hierarchical permission model described in the
[Permissions](../../11_access_management/2_permissions/).

**Dynamic Authorization:** For operations requiring runtime permission checks, the platform provides programmatic access
to the permission evaluation system. This enables filtering result sets based on user permissions, implementing
different behaviors for different access levels, and validating permissions before resource-intensive operations.

## Admin Service Authentication via OAuth2 Proxy

Internal admin services (Dagster, Attu, SeaweedFS) are protected by [OAuth2 Proxy](https://oauth2-proxy.github.io/)
instances that sit in front of each service. OAuth2 Proxy handles the full OIDC login flow against Keycloak before
forwarding authenticated requests to the upstream service.

### Split Internal/External URL Configuration

In a Docker Compose deployment, Keycloak is reachable by other containers via its internal Docker hostname
(`http://keycloak:8080`), while browsers access it through Traefik at the external URL
(`https://auth.<domain>`). This creates a split-horizon problem: OAuth2 Proxy needs the internal URL for
server-to-server communication, but must redirect browsers to the external URL for login.

When OAuth2 Proxy performs OIDC discovery against the internal URL, Keycloak's discovery document returns endpoints
using its configured hostname but with the internal scheme and port (e.g., `http://auth.<domain>:8080/...`).
These URLs are unreachable from both browsers (wrong scheme/port) and containers (the domain resolves to `127.0.0.1`
in local environments using `nip.io`).

### Why OIDC Discovery Is Skipped

To resolve this, OIDC discovery is disabled (`OAUTH2_PROXY_SKIP_OIDC_DISCOVERY=true`) and all endpoints are configured
explicitly:

| Endpoint | URL Used | Reason |
|---|---|---|
| Authorization (login redirect) | External HTTPS (`https://auth.<domain>/...`) | Browser-facing, must be reachable by the user's browser |
| Token exchange (redeem) | Internal HTTP (`http://keycloak:8080/...`) | Server-to-server, stays within Docker network |
| JWKS (token verification) | Internal HTTP (`http://keycloak:8080/...`) | Server-to-server, stays within Docker network |
| Issuer (token `iss` claim) | External HTTPS (`https://auth.<domain>/...`) | Must match the `iss` claim in tokens issued by Keycloak |

### Consequences and Risk Assessment

**What is lost by skipping discovery:**

- **No automatic endpoint rotation.** If Keycloak's OIDC endpoints change (e.g., during a major Keycloak upgrade that
  alters URL paths), the hardcoded URLs in `docker-compose.yml.j2` must be updated manually. In practice, Keycloak's
  OIDC endpoint paths have been stable across major versions and follow the OIDC standard.
- **No automatic key algorithm detection.** Discovery normally advertises supported signing algorithms. With discovery
  skipped, OAuth2 Proxy falls back to its defaults (RS256), which matches Keycloak's default configuration.

**What is NOT affected (security remains intact):**

- **JWT signature verification is fully preserved.** Tokens are still validated against Keycloak's JWKS endpoint using
  RSA public keys. This is the primary security mechanism — a forged or tampered token will be rejected.
- **Token expiration and claims validation still applies.** OAuth2 Proxy validates `exp`, `iss`, and other standard
  claims.
- **The OIDC authorization code flow with PKCE is unchanged.** The login flow is identical — only the source of the
  endpoint URLs differs (explicit config vs. discovery document).
- **TLS is enforced on all browser-facing communication.** The authorization URL uses HTTPS. Internal container-to-container
  traffic uses HTTP over the isolated Docker network, which is standard practice.

**Why this trade-off is acceptable:**

1. Keycloak's OIDC endpoints follow a well-defined, stable URL convention
   (`/realms/{realm}/protocol/openid-connect/{auth|token|certs}`). These paths are part of the OIDC specification and
   unlikely to change.
2. The endpoints are generated from Jinja2 template variables (`KEYCLOAK_INTERNAL_URL`, `KEYCLOAK_REALM`), so they
   remain consistent with the rest of the deployment configuration.
3. The alternative — having Keycloak return correct split-horizon URLs in its discovery document — would require complex
   hostname configuration in Keycloak that behaves differently depending on whether the request comes from inside or
   outside the Docker network.

## Security Standards and Operational Capabilities

### Standards Compliance

The authentication and authorization implementation adheres to industry-standard protocols and specifications:

**OIDC and OAuth 2.0 Standards:**

- OpenID Connect Core 1.0 for authentication
- OAuth 2.0 Authorization Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow with PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Usage (RFC 6750)

**Cryptographic Security:** All JWT tokens are validated using RSA-256 cryptographic signatures. Public keys are
retrieved from the identity provider's JWKS endpoint and cached for performance. Token validation includes signature
verification, issuer validation, audience validation, and expiration checking on every request.

### Audit and Monitoring

All authentication and authorization events are comprehensively logged with structured metadata for audit and security
monitoring purposes. This includes user identity, requested resources, permission evaluations, access decisions, and
full request context.

**Security Event Logging:** The platform integrates with OpenTelemetry standards to provide structured, traceable
security events. This enables correlation of security events across distributed system components and supports
compliance requirements for audit trails.

**Real-Time Security Monitoring:** Security teams can monitor authentication patterns, authorization failures, token
validation events, and access patterns in real-time. This visibility enables rapid detection and response to potential
security incidents.

### Regulatory and Enterprise Compliance

The authentication and authorization architecture supports compliance with regulatory requirements and enterprise
security standards:

**Data Protection Compliance:**

- GDPR-compliant user authentication and data handling
- Swiss data protection law compliance through self-hosted deployment options
- Comprehensive audit trails meeting regulatory requirements for access logging
- Data sovereignty maintained through on-premises or Swiss cloud deployment

**Enterprise Security Requirements:**

- Multi-factor authentication support through enterprise identity providers
- Integration with existing enterprise identity infrastructure
- Protection against common authentication attacks (token replay, session hijacking, CSRF)
- Secure token lifecycle management with expiration and revocation
- HTTPS-only communication for all authentication flows

**Security Best Practices:**

- Zero-trust security model with authentication required for all API access
- Separation of authentication and authorization concerns
- Principle of least privilege through granular permission system
- Defense in depth with multiple layers of security controls
- Regular token validation and refresh mechanisms

This standards-based approach to authentication and authorization ensures the platform meets enterprise security
requirements while remaining interoperable with standard identity providers and security infrastructure. The use of OIDC
and OAuth 2.0 provides proven security mechanisms that are widely understood, audited, and trusted in enterprise
environments.
