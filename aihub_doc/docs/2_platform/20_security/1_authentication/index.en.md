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

## Hardening: Keycloak Admin Console Access

The Keycloak admin console (`https://auth.<domain>/admin/`) is protected by username and password but is accessible from
any IP address by default. For production deployments, restricting access to the admin console and metrics endpoint to
known administrator IP addresses is strongly recommended.

### Recommended: IP Allowlisting via Traefik

The platform uses Traefik v3 as its reverse proxy. Traefik's
[`ipAllowList`](https://doc.traefik.io/traefik/middlewares/http/ipallowlist/) middleware can restrict access to the
Keycloak admin paths while keeping the OIDC login endpoints publicly accessible for all users.

**Implementation steps:**

1. Add an environment variable to `.env` with your allowed IP ranges:

   ```bash
   KEYCLOAK_ADMIN_ALLOWED_IPS="203.0.113.0/24,198.51.100.10/32"
   ```

2. In `docker-compose.yml`, add a second Traefik router for admin paths on the `keycloak`
   service labels (alongside the existing `keycloak` router):

   ```yaml
   # Admin-only router with IP restriction (higher priority than public router)
   - "traefik.http.routers.keycloak-admin.rule=Host(`auth.${DOMAIN}`) && (PathPrefix(`/admin`) || PathPrefix(`/metrics`))"
   - "traefik.http.routers.keycloak-admin.entrypoints=websecure"
   - "traefik.http.routers.keycloak-admin.tls=true"
   - "traefik.http.routers.keycloak-admin.priority=7500"
   - "traefik.http.routers.keycloak-admin.middlewares=keycloak-admin-ipallowlist,keycloak-security-headers"
   - "traefik.http.routers.keycloak-admin.service=keycloak"
   # IP allowlist middleware
   - "traefik.http.middlewares.keycloak-admin-ipallowlist.ipallowlist.sourcerange=${KEYCLOAK_ADMIN_ALLOWED_IPS}"
   ```

The public router (priority 7000) continues to serve OIDC endpoints (`/realms/...`) without restriction, while the admin
router (priority 7500) intercepts `/admin` and `/metrics` requests and rejects connections from non-allowlisted IPs with
a `403 Forbidden` response.

::: tip
The same pattern can be applied to any service exposed through Traefik. Consider also restricting access to the Traefik
dashboard itself if it is enabled in production.
:::

## Keycloak Realm Roles and Automatic Assignment

Keycloak manages realm-level roles that determine whether a user may access the platform. These roles are coarse access
gates — fine-grained permissions are managed locally by the platform (see
[Permissions](../../11_access_management/2_permissions/)).

| Role | Purpose |
|---|---|
| `AIHubAccess` | Required for platform login. Users without this role are denied at the Keycloak login flow. |
| `AIHubAdmin` | Full administrative access |
| `AIHubUser` | Standard user access |
| `AIHubDeveloper` | Developer tools access (Dagster, Attu, etc.) |
| `AIHubSysAdmin` | System administrator access to infrastructure tools |

By default, no roles are automatically assigned to new users. This ensures that users federated from an external identity
provider only receive the roles explicitly mapped from their IdP claims, following the principle of least privilege.

### Configuring Automatic Role Assignment

If your deployment requires that all new users receive a default role (e.g., `AIHubUser`), this can be configured in
Keycloak:

**Option 1: Realm default roles (applies to all new users)**

In the Keycloak admin console, navigate to **Realm Settings > User Registration > Default Roles** and add the desired
roles. Alternatively, set the `defaultRoles` array in the realm configuration template
(`keycloak-realm.json.j2`):

```json
"defaultRoles": ["AIHubUser"]
```

**Option 2: Identity provider mappers (applies per IdP)**

For more granular control, configure role mappers on individual identity providers. This allows different roles for
users from different organizations. In the Keycloak admin console, navigate to **Identity Providers > [your IdP] >
Mappers** and add a **Hardcoded Role** mapper:

| Field | Value |
|---|---|
| Name | `default-user-role` |
| Mapper Type | Hardcoded Role |
| Role | `AIHubUser` |

This assigns the role only to users authenticating through that specific identity provider.

**Option 3: Claim-based role mapping (conditional assignment)**

For conditional role assignment based on IdP claims (e.g., Azure AD app roles), use the existing `oidc-role-idp-mapper`
pattern already configured in `keycloak-identity-providers.json.j2`. Each Azure AD app role is mapped to a corresponding
Keycloak realm role. To add a new mapping, add an entry to the `identityProviderMappers` array:

```json
{
  "name": "role-mapper-my-role",
  "identityProviderAlias": "azure-ad",
  "identityProviderMapper": "oidc-role-idp-mapper",
  "config": {
    "syncMode": "INHERIT",
    "claim": "roles",
    "claim.value": "MyAzureAppRole",
    "role": "AIHubUser"
  }
}
```

::: warning
The `AIHubAccess` role is enforced at the Keycloak login flow level via the "Post Broker Login - AIHubAccess Check"
authentication flow. Users without this role are denied access regardless of any other role assignments. Ensure that
your role mapping strategy includes `AIHubAccess` for users who should be able to log in.
:::

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
