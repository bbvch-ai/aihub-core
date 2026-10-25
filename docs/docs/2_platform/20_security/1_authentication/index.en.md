---
title: Authentication and Authorization
---

# Authentication and Authorization

The Swiss AI Hub implements authentication and authorization based on industry-standard OpenID Connect (OIDC) and OAuth
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

## Dynamic Identity Provider Discovery

The login page dynamically discovers available identity providers from Keycloak at runtime. When a user visits the login
page, the frontend calls `GET /api/v1/auth-providers/` — an unauthenticated API endpoint that queries the Keycloak Admin
API using a dedicated, least-privilege service account (`aihub-api-service`) with only the `view-identity-providers`
permission.

The API filters the provider list to only include enabled, visible providers and returns their alias, display name, and
icon. Results are cached for 5 minutes. The frontend renders a branded login button for each provider. Clicking a button
initiates the OIDC Authorization Code Flow with `kc_idp_hint` set to the provider's alias, redirecting the user directly
to the upstream identity provider without showing Keycloak's login theme.

This approach eliminates any frontend configuration for identity providers — adding or removing an IdP is a
Keycloak-only change.

### Configuring Provider Icons

Each identity provider can have a custom icon displayed on its login button. Icons are configured directly in the
Keycloak identity provider's `config` map as the `icon` field using PrimeIcon CSS classes (e.g., `pi-microsoft`,
`pi-google`). Providers without an icon configured fall back to `pi-sign-in`.

To set an icon, add the `icon` field to the identity provider's configuration in
`infra/deployment/templates/configs/keycloak/bootstrap/identity-providers.json.j2`:

```json
"config": {
  "clientId": "...",
  "icon": "pi-microsoft"
}
```

### Direct Keycloak Login

When `KEYCLOAK_SHOW_KEYCLOAK_LOGIN=true` (API environment variable, default: `true`), an additional "Login with
Keycloak" button appears alongside federated provider buttons. This enables username/password login through Keycloak's
own user store — useful for development environments or deployments where some users authenticate directly with Keycloak
rather than through an external IdP.

### Per-Tenant Login Links

`/{locale}/auth/login/<idp-alias>` shows a single login button for one identity provider. The page resolves the alias
through `GET /api/v1/auth-providers/<idp-alias>`, which returns the provider while it is enabled and not link-only, and
`null` otherwise. Providers hidden on Keycloak's login page still resolve, because Keycloak honours `kc_idp_hint` for
them. An unknown alias falls back to the generic login page. Tenants that share an identity provider share its link.

### Tenant Address as Login Link

A tenant's own address can double as its login link. When a visitor who is not logged in opens `/<tenant-id>` or any
page below it, with or without a locale prefix (`/acme`, `/en/acme/service/openai`), the frontend sends them straight to
that tenant's identity provider with `kc_idp_hint` — no provider list and no login button. After login, the user returns
to the page they opened, and that tenant becomes their active tenant if they are a member of it.

The mapping from tenant ID to IdP alias is set per instance with `KEYCLOAK_TENANT_IDP_ALIASES` (API environment
variable, default: empty):

```bash
KEYCLOAK_TENANT_IDP_ALIASES='acme=acme-entra,beta=shared-idp,gamma=shared-idp'
```

- Tenants that share one identity provider map to the same alias.
- Empty turns this off: visitors reach the login page as before. This is the default, so dedicated customer instances
  are unaffected.
- A malformed entry or a tenant listed twice stops the API from starting.
- An alias is used under the same rule as a per-tenant login link: its identity provider must be enabled and not set to
  account linking only, and providers hidden on Keycloak's login page are accepted.

The frontend resolves the tenant through `GET /api/v1/auth-providers/tenants/{tenant_id}`, an unauthenticated endpoint
that returns `{"alias": "<alias>"}` or `{"alias": null}`. It reads only the configured mapping and never checks whether
a tenant exists, so an unknown tenant and an existing but unlisted tenant get the same answer and both end on the login
page, or on the welcome page when `KEYCLOAK_LOGIN_WELCOME_PAGE` is on. A listed tenant does reveal itself by redirecting
to its identity provider, as any working login link must.

When a session cannot be renewed on a tenant page, the user takes the same route: to the tenant's identity provider,
then back to the page. Per-tenant login links keep working alongside tenant addresses.

### Welcome Page for Shared Instances

On an instance that serves several organisations, the generic login page would show every tenant's identity provider to
anyone. Setting `KEYCLOAK_LOGIN_WELCOME_PAGE=true` (environment variable on `api` and `sysadmin-api`, default: `false`)
replaces the provider buttons with a welcome message that points visitors to their organisation's login link or to their
administrator.

The switch acts in the API, not only on the page. `GET /api/v1/auth-providers/` then returns `welcome_page: true` and no
federated provider, and does not query Keycloak at all. Per-tenant login links keep working. If
`KEYCLOAK_SHOW_KEYCLOAK_LOGIN` is also `true`, the welcome page shows a small "Administrator login" link to Keycloak's
own login page for username/password accounts.

Two things the switch does not cover:

- **Keycloak's login page** lists every identity provider that is not hidden on it. The administrator link, the
  OpenWebUI sign-in and any hand-built authorization URL all lead there. On a shared instance, enable **Hide on login
  page** for every tenant's identity provider in the Keycloak admin console. Per-tenant links are unaffected.
- **Tenants without a link** have no way in. Hand every tenant its link, or list it in `KEYCLOAK_TENANT_IDP_ALIASES` so
  its address works as one, before turning the switch on.

## Admin Service Authentication via OAuth2 Proxy

Internal admin services (Dagster, Attu, SeaweedFS, Backup, LiteLLM) are protected by
[OAuth2 Proxy](https://oauth2-proxy.github.io/) instances that sit in front of each service. OAuth2 Proxy handles the
full OIDC login flow against Keycloak before forwarding authenticated requests to the upstream service. Only users with
the `AIHubSysAdmin` role can access these services, and the session cookie is `Secure`.

`litellm.<domain>` reaches LiteLLM only through `oauth2proxy-litellm`, so its UI and its admin API need an SSO session
first. Applications outside the platform call models through the API's OpenAI-compatible endpoint
(`https://<domain>/api/v1/active/openai`), never through LiteLLM directly.

The image is the upstream OAuth2 Proxy release pinned in `compose-config.yml` and mirrored to the platform registry. The
sign-in button colour comes from `infra/deployment/templates/oauth2-proxy/sign_in.html`, mounted as a custom template;
re-copy upstream's `sign_in.html` of the new version into it when bumping the tag.

Due to the split-horizon networking in Docker deployments (containers use internal hostnames, browsers use external
URLs), OIDC discovery is skipped and endpoints are configured explicitly.

## Langfuse Access

Langfuse does not sit behind an OAuth2 Proxy — it uses its native Keycloak SSO integration (OIDC client `langfuse`).
Access is restricted to users with the `AIHubSysAdmin` role directly in Keycloak: the `langfuse` client carries the
marker client scope `langfuse-sysadmin-gate`, which activates a conditional deny in the authentication flows
(`browser-aihub` browser flow and the post-broker-login flow). Users without `AIHubSysAdmin` are denied at the Keycloak
login — on fresh logins via the identity provider as well as on existing SSO sessions.

## Keycloak Admin Console Access

Traefik serves the Keycloak admin console (`https://auth.<domain>/admin/`) and the `master` realm
(`https://auth.<domain>/realms/master/`) only to the source ranges in `KEYCLOAK_ADMIN_ALLOWED_SOURCE_RANGES`
(comma-separated CIDRs). Every other client gets `403 Forbidden` from the
[`ipAllowList`](https://doc.traefik.io/traefik/middlewares/http/ipallowlist/) middleware on a dedicated router (priority
7500, above the public Keycloak router at 7000). The `aihub` realm's login, token and account endpoints stay public.

- `.env.prod` ships `127.0.0.1/32`, which shuts the console off from every outside address. Set your administrators'
  office or VPN ranges, for example `KEYCLOAK_ADMIN_ALLOWED_SOURCE_RANGES='203.0.113.0/24,198.51.100.10/32'`, then
  recreate `keycloak` so Traefik picks up the new label.
- The platform itself never goes through this route: the API, `keycloak-config` and the OAuth2 proxies call Keycloak at
  `http://keycloak:8080` inside the Docker network.

## Keycloak Realm Roles and Automatic Assignment

Keycloak manages realm-level roles that determine whether a user may access the platform. These roles are coarse access
gates — fine-grained permissions are managed locally by the platform through tenant-scoped roles (see
[Permissions](../../11_access_management/2_permissions/)).

Two realm roles take effect in the platform:

| Role            | Effect                                                                                                                                                            |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AIHubAccess`   | Required for platform login. Users without this role are denied at the Keycloak login flow.                                                                       |
| `AIHubSysAdmin` | Platform administrator. Read from the token to grant admin access and gate the OAuth2-Proxy admin tools (Dagster, Attu, SeaweedFS, Backup, LiteLLM) and Langfuse. |

::: info Realm roles vs. platform roles
The `aihub` realm defines only these two roles. Fine-grained, day-to-day permissions are handled separately by
**tenant-scoped roles** managed inside the platform — these may share names such as `AIHubUser` or `AIHubAdmin` but are
unrelated to Keycloak realm roles and are not derived from the IdP. Assign only `AIHubAccess` and `AIHubSysAdmin` in
your identity provider.

For the operator setup of the Azure app registration and role assignment, see
[Identity Provider Setup](../../3_deployment_guide/10_identity_provider_setup/).
:::

By default, no realm roles are automatically assigned to new users: a federated user receives only the realm roles
explicitly mapped from their IdP claims (principle of least privilege). At the Keycloak / IdP level there are only ever
**two** roles to assign — `AIHubAccess` and `AIHubSysAdmin` (see the info box above). `AIHubUser` / `AIHubAdmin` and the
other "platform roles" are **not** Keycloak realm roles and are never set on the IdP; they are tenant-scoped and
configured inside the platform (see [Default platform roles](#default-platform-roles) below).

### Mapping the realm roles from the IdP

The `azure-ad` provider already maps the two realm roles from the Azure `roles` claim via two `oidc-role-idp-mapper`
entries in `infra/deployment/templates/configs/keycloak/bootstrap/identity-providers.json.j2` (`role-mapper-access` →
`AIHubAccess`, `role-mapper-sysadmin` → `AIHubSysAdmin`). To federate the same two roles from a different provider, add
the equivalent mappers — targeting only `AIHubAccess` and `AIHubSysAdmin`:

```json
{
  "name": "role-mapper-access",
  "identityProviderAlias": "<your-idp-alias>",
  "identityProviderMapper": "oidc-role-idp-mapper",
  "config": {
    "syncMode": "INHERIT",
    "claim": "roles",
    "claim.value": "AIHubAccess",
    "role": "AIHubAccess"
  }
}
```

::: warning Identity providers are bootstrap config
Identity providers and their mappers are seeded from `bootstrap/identity-providers.json.j2` by the realm import on the
**first start only** — they are not reconciled by keycloak-config-cli. Edits made in the Keycloak admin console survive
restarts, and changes to the config file reach an already-initialized deployment only via the admin console (or a fresh
realm database).
:::

::: warning AIHubAccess is required to log in
`AIHubAccess` is enforced at the Keycloak login flow ("Post Broker Login - AIHubAccess Check"): a user without it is
denied regardless of any other assignment. Make sure your IdP grants `AIHubAccess` to everyone who should be able to log
in.
:::

### Default platform roles

Day-to-day permissions come from **platform roles** (`AIHubUser`, `AIHubAdmin`, `AIHubAgentUser`, …), which are
tenant-scoped and managed inside the platform — not in Keycloak and not from the IdP. Which roles a new user receives is
controlled by the `AIHUB_USER_SIGNUP_*` environment variables (`AIHUB_USER_SIGNUP_DEFAULT_ROLES`,
`AIHUB_USER_SIGNUP_REGULAR_USER_ROLES`, `AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES`), and each tenant is seeded with its
default role set at creation. See [Access Management](../../11_access_management/1_authentication_setup/) and
[Permissions](../../11_access_management/2_permissions/).

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
