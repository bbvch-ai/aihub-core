---
title: Authentication and Authorization
---

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
(OID) and basic profile information (name, email) from the JWT token claims. Role assignments are managed locally within
the platform through tenant-scoped role entities, not fetched from the identity provider.

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

The platform integrates with enterprise identity providers through standard OIDC/OAuth 2.0 protocols. Any OIDC-compliant
provider (Microsoft Entra ID, Google Workspace, Okta, Auth0, Keycloak) can be used for authentication.

**Generic OIDC Integration:** The platform connects to the configured OIDC provider as an OAuth 2.0 authorization server
and identity provider. User authentication is delegated to the provider, which handles credential validation,
multi-factor authentication, and session management according to the organization's security policies.

**Local Role Management:** User profiles are extracted from JWT token claims (name, email, OID). Roles are managed
locally within the platform through tenant-scoped role assignments, not synced from the identity provider. This
decouples platform authorization from any specific identity provider's group or role model.

### How Authorization Works

Authorization decisions are made independently from authentication. After a user's identity is established through OIDC
authentication, the platform determines what resources and operations the user can access based on their assigned roles.

**Permission Evaluation Process:**

1. The platform resolves the user's role assignments from the local tenant-scoped role database
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
