# Keycloak Integration for Swiss AI-Hub

**Status**: Implemented
**Date**: 2025-12-28
**Authors**: Claude (AI)
**Related ADRs**:
- 2025_08_11_global_superuser_authentication.md
- 2025_12_25_local_role_management.md

---

## Executive Summary

Keycloak is now the **sole identity provider** for Swiss AI-Hub. All OAuth2/OIDC authentication goes through Keycloak, which acts as an identity broker for upstream providers (Azure AD, Google, etc.).

**Key Benefits**:
1. **Development Environment**: Local Keycloak with configurable dev user - no external IdP needed
2. **E2E Testing**: Consistent, reproducible authentication with known credentials
3. **Production Flexibility**: Keycloak brokers to Azure AD, Google, SAML - one integration point
4. **Swiss Sovereignty**: Self-hosted identity management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Swiss AI-Hub                           │
├─────────────────────────────────────────────────────────────┤
│  Admin UI  │  OpenWebUI  │  API  │  Agents  │  Pipelines   │
└──────┬─────┴──────┬──────┴───┬───┴─────┬────┴──────┬───────┘
       │            │          │         │           │
       └────────────┴──────────┴────┬────┴───────────┘
                                    │
                              ┌─────▼─────┐
                              │ Keycloak  │ (Identity Broker)
                              └─────┬─────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
    ┌─────▼─────┐            ┌──────▼──────┐           ┌──────▼──────┐
    │ Azure AD  │            │   Google    │           │ Local Users │
    │(Production)│            │  (Optional) │           │    (Dev)    │
    └───────────┘            └─────────────┘           └─────────────┘
```

### Authentication Flow

1. User accesses AI-Hub application
2. Application redirects to Keycloak
3. Keycloak handles authentication (local user or federated IdP)
4. Keycloak issues JWT token
5. Application validates JWT via Keycloak JWKS endpoint

### Authentication Handlers

| Handler | Purpose | Configuration |
|---------|---------|---------------|
| `KeycloakAuthHandler` | OIDC JWT validation via Keycloak | `KEYCLOAK_URL`, `KEYCLOAK_REALM` |
| `SuperuserAuthHandler` | Token-based admin access | `SUPERUSER_ENABLED=True` |
| `TokenAuthHandler` | API bearer tokens | `AUTH_ENABLE_API_ACCESS=True` |
| `OpenWebuiAuthHandler` | HMAC-signed requests from OpenWebUI | `AUTH_OPEN_WEBUI_SIGNING_SECRET` |

---

## Implementation Details

---

## Implementation Plan

### 1. Docker Compose Infrastructure

#### 1.1 Keycloak Service Definition

Add to `deployment/templates/docker-compose.yml.j2`:

```yaml
keycloak:
  image: quay.io/keycloak/keycloak:{{ images.keycloak }}
  container_name: keycloak
  {%- if stage == 'dev' %}
  ports:
    - "8180:8080"  # Dev: Expose directly
  command:
    - start-dev
    - --import-realm
  volumes:
    - ../configs/keycloak/aihub-realm.json:/opt/keycloak/data/import/aihub-realm.json:ro
  {%- else %}
  command:
    - start
    - --import-realm
    - --hostname=auth.${DOMAIN}
    - --proxy-headers=xforwarded
    - --http-enabled=true
  volumes:
    - ../configs/keycloak/aihub-realm.json:/opt/keycloak/data/import/aihub-realm.json:ro
  {%- endif %}
  environment:
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
    KC_DB_USERNAME: ${POSTGRES_USER}
    KC_DB_PASSWORD: ${POSTGRES_PASSWORD}
    KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN_USER}
    KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
    KC_FEATURES: token-exchange,admin-fine-grained-authz
    KC_HEALTH_ENABLED: true
    KC_METRICS_ENABLED: true
  healthcheck:
    test: ["CMD-SHELL", "exec 3<>/dev/tcp/127.0.0.1/8080;echo -e 'GET /health/ready HTTP/1.1\r\nhost: localhost\r\nConnection: close\r\n\r\n' >&3;grep -q '200 OK' <&3"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
  depends_on:
    postgres:
      condition: service_healthy
  restart: unless-stopped
  {%- if stage != 'dev' %}
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.keycloak.rule=Host(`auth.${DOMAIN}`)"
    - "traefik.http.routers.keycloak.entrypoints=websecure"
    - "traefik.http.routers.keycloak.tls.certresolver=letsencrypt"
    - "traefik.http.services.keycloak.loadbalancer.server.port=8080"
  {%- endif %}
```

#### 1.2 PostgreSQL Database Extension

Add `keycloak` to the PostgreSQL init script:

```bash
# deployment/templates/configs/pg-init-multiple-dbs.sh.j2
DATABASES="openwebui phoenix dagster litellm keycloak"
```

#### 1.3 compose-config.yml Updates

```yaml
images:
  keycloak: "26.0"  # Latest LTS version
```

### 2. Realm Configuration

#### 2.1 Create Realm Export Template

Create `deployment/templates/configs/keycloak-realm.json.j2`:

```json
{
  "realm": "aihub",
  "enabled": true,
  "displayName": "Swiss AI-Hub",
  "loginTheme": "keycloak",
  "sslRequired": "{{ 'none' if stage == 'dev' else 'external' }}",
  "registrationAllowed": false,
  "resetPasswordAllowed": true,
  "rememberMe": true,

  "roles": {
    "realm": [
      { "name": "AIHubAdmin", "description": "Full administrative access" },
      { "name": "AIHubUser", "description": "Standard user access" },
      { "name": "AIHubDeveloper", "description": "Developer tools access" }
    ]
  },

  "clients": [
    {
      "clientId": "aihub-frontend",
      "name": "AI-Hub Frontend",
      "enabled": true,
      "publicClient": true,
      "standardFlowEnabled": true,
      "implicitFlowEnabled": false,
      "directAccessGrantsEnabled": false,
      "rootUrl": "{{ 'http://localhost:3000' if stage == 'dev' else 'https://${DOMAIN}' }}",
      "baseUrl": "/",
      "redirectUris": [
        "{{ 'http://localhost:3000/*' if stage == 'dev' else 'https://${DOMAIN}/*' }}",
        "{{ 'http://localhost:8080/*' if stage == 'dev' else 'https://openwebui.${DOMAIN}/*' }}"
      ],
      "webOrigins": ["+"],
      "defaultClientScopes": ["openid", "profile", "email", "roles"],
      "protocolMappers": [
        {
          "name": "realm-roles",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-realm-role-mapper",
          "config": {
            "claim.name": "roles",
            "jsonType.label": "String",
            "multivalued": "true",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true"
          }
        }
      ]
    },
    {
      "clientId": "aihub-api",
      "name": "AI-Hub API",
      "enabled": true,
      "publicClient": false,
      "standardFlowEnabled": false,
      "serviceAccountsEnabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "{{ '${KEYCLOAK_API_CLIENT_SECRET}' }}"
    },
    {
      "clientId": "openwebui",
      "name": "Open WebUI",
      "enabled": true,
      "publicClient": false,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": false,
      "clientAuthenticatorType": "client-secret",
      "secret": "{{ '${KEYCLOAK_OPENWEBUI_CLIENT_SECRET}' }}",
      "rootUrl": "{{ 'http://localhost:8080' if stage == 'dev' else 'https://openwebui.${DOMAIN}' }}",
      "redirectUris": ["{{ 'http://localhost:8080/oauth/oidc/callback' if stage == 'dev' else 'https://openwebui.${DOMAIN}/oauth/oidc/callback' }}"],
      "webOrigins": ["+"],
      "defaultClientScopes": ["openid", "profile", "email"]
    }
  ],

  {%- if stage == 'dev' %}
  "users": [
    {
      "username": "${KEYCLOAK_DEV_USER_USERNAME}",
      "email": "${KEYCLOAK_DEV_USER_EMAIL}",
      "firstName": "${KEYCLOAK_DEV_USER_FIRSTNAME}",
      "lastName": "${KEYCLOAK_DEV_USER_LASTNAME}",
      "enabled": true,
      "emailVerified": true,
      "credentials": [
        {
          "type": "password",
          "value": "${KEYCLOAK_DEV_USER_PASSWORD}",
          "temporary": false
        }
      ],
      "realmRoles": ${KEYCLOAK_DEV_USER_ROLES_JSON}
    }
  ],
  {%- endif %}

  "browserSecurityHeaders": {
    "contentSecurityPolicy": "frame-src 'self'; frame-ancestors 'self' {{ 'http://localhost:*' if stage == 'dev' else 'https://*.${DOMAIN}' }}; object-src 'none';"
  }
}
```

### 3. Environment Variable Updates

#### 3.1 New Variables for .env.dev

```bash
# -----------------------------------------------------------------------------
# Keycloak Configuration
# -----------------------------------------------------------------------------
# Keycloak Admin Console credentials
KEYCLOAK_ADMIN_USER="admin"
KEYCLOAK_ADMIN_PASSWORD="admin-dev-password-changeme"

# Client secrets for OIDC clients
KEYCLOAK_API_CLIENT_SECRET="aihub-api-secret-dev-changeme"
KEYCLOAK_OPENWEBUI_CLIENT_SECRET="openwebui-secret-dev-changeme"

# -----------------------------------------------------------------------------
# Keycloak Development User (configurable)
# -----------------------------------------------------------------------------
# This user is auto-created in the Keycloak realm for development and E2E testing
KEYCLOAK_DEV_USER_USERNAME="admin"
KEYCLOAK_DEV_USER_PASSWORD="admin"
KEYCLOAK_DEV_USER_EMAIL="admin@ai-hub.local"
KEYCLOAK_DEV_USER_FIRSTNAME="Admin"
KEYCLOAK_DEV_USER_LASTNAME="User"
KEYCLOAK_DEV_USER_ROLES="AIHubAdmin"
# JSON array format for realm import (generated from KEYCLOAK_DEV_USER_ROLES)
KEYCLOAK_DEV_USER_ROLES_JSON='["AIHubAdmin"]'

# Keycloak Endpoints (for local development outside Docker)
KEYCLOAK_URL="http://localhost:8180"
KEYCLOAK_REALM="aihub"
```

#### 3.2 OAuth Variables (Keycloak)

```bash
# OAuth2 / OIDC Configuration
# All authentication goes through Keycloak (which brokers to Azure AD, etc.)
OAUTH_PROVIDER_NAME="Keycloak"
OAUTH_CLIENT_ID="aihub-frontend"
OAUTH_CLIENT_SECRET=""  # Public client for frontend
OAUTH_AUTHORITY_URL="http://localhost:8180/realms/aihub"
OAUTH_TENANT_ID=""  # Not used with Keycloak
```

#### 3.3 New Variables for .env.prod

```bash
# -----------------------------------------------------------------------------
# Keycloak Configuration (Production)
# -----------------------------------------------------------------------------
KEYCLOAK_ADMIN_USER="admin"
KEYCLOAK_ADMIN_PASSWORD="REPLACE_WITH_YOUR_SECURE_ADMIN_PASSWORD"
KEYCLOAK_API_CLIENT_SECRET="REPLACE_WITH_YOUR_API_CLIENT_SECRET"
KEYCLOAK_OPENWEBUI_CLIENT_SECRET="REPLACE_WITH_YOUR_OPENWEBUI_CLIENT_SECRET"

# Identity Broker Configuration (Azure AD)
KEYCLOAK_AZURE_CLIENT_ID="REPLACE_WITH_YOUR_AZURE_APP_CLIENT_ID"
KEYCLOAK_AZURE_CLIENT_SECRET="REPLACE_WITH_YOUR_AZURE_APP_CLIENT_SECRET"
KEYCLOAK_AZURE_TENANT_ID="REPLACE_WITH_YOUR_AZURE_TENANT_ID"
```

### 4. Pydantic Settings Updates

#### 4.1 New Settings Class

Create `aihub_lib/aihub_lib/auth/dependencies/KeycloakSettings.py`:

```python
"""Keycloak identity provider settings."""

from typing import Annotated

from pydantic import Field, SecretStr, computed_field

from aihub_lib.settings import EnvironmentSettings


class KeycloakSettings(EnvironmentSettings):
    """Settings for Keycloak identity provider."""

    model_config = EnvironmentSettings.create_settings_config("KEYCLOAK_")

    URL: Annotated[str, Field(description="Keycloak base URL (e.g., http://localhost:8180)")]
    REALM: Annotated[str, Field(description="Keycloak realm name")] = "aihub"
    API_CLIENT_SECRET: Annotated[SecretStr | None, Field(description="API client secret")] = None

    @computed_field
    @property
    def ISSUER_URL(self) -> str:
        """OIDC issuer URL."""
        return f"{self.URL}/realms/{self.REALM}"

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        """JWKS endpoint URL."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/certs"

    @computed_field
    @property
    def TOKEN_URL(self) -> str:
        """Token endpoint URL."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/token"

    @computed_field
    @property
    def AUTHORIZATION_URL(self) -> str:
        """Authorization endpoint URL."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/auth"

    @computed_field
    @property
    def USERINFO_URL(self) -> str:
        """Userinfo endpoint URL."""
        return f"{self.ISSUER_URL}/protocol/openid-connect/userinfo"

    @computed_field
    @property
    def WELL_KNOWN_URL(self) -> str:
        """OpenID Connect discovery URL."""
        return f"{self.ISSUER_URL}/.well-known/openid-configuration"
```

#### 4.2 AuthSettings (Simplified)

The `AuthSettings` class no longer has an `IDENTITY_PROVIDER` field since Keycloak is the only OAuth2/OIDC provider:

```python
class AuthSettings(EnvironmentSettings):
    """
    Authentication settings for the API.

    All OAuth2/OIDC authentication goes through Keycloak, which acts as an
    identity broker for upstream providers (Azure AD, Google, etc.).
    """

    model_config = EnvironmentSettings.create_settings_config("AUTH_")

    ENABLE_API_ACCESS: Annotated[bool, Field(description="Enable API access")] = True
    OPEN_WEBUI_SIGNING_SECRET: Annotated[SecretStr, Field(description="OpenWebUI signing secret", min_length=64)]
```

### 5. Auth Handler Updates

#### 5.1 Create KeycloakAuthHandler

Create `aihub_lib/aihub_lib/auth/dependencies/KeycloakAuthHandler/`:

```python
"""Keycloak OIDC authentication handler."""

from typing import Annotated

import httpx
from cachetools import TTLCache
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.KeycloakSettings import KeycloakSettings
from aihub_lib.auth.identity import UserIdentity
from aihub_lib.persistence.user import UserEntity


class KeycloakAuthHandler(AuthHandler):
    """Handles Keycloak OIDC authentication."""

    def __init__(self, settings: KeycloakSettings | None = None):
        self.settings = settings or KeycloakSettings()
        self._jwks_cache: TTLCache = TTLCache(maxsize=1, ttl=21600)  # 6 hours

    async def _get_jwks(self) -> dict:
        """Fetch and cache Keycloak JWKS."""
        if "jwks" in self._jwks_cache:
            return self._jwks_cache["jwks"]

        async with httpx.AsyncClient() as client:
            response = await client.get(self.settings.JWKS_URL)
            response.raise_for_status()
            jwks = response.json()
            self._jwks_cache["jwks"] = jwks
            return jwks

    async def __call__(
        self,
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    ) -> UserIdentity:
        """Validate Keycloak JWT and return user identity."""
        token = credentials.credentials

        # Fetch JWKS
        jwks = await self._get_jwks()

        # Decode and validate JWT
        try:
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience="account",
                issuer=self.settings.ISSUER_URL,
            )
        except JWTError as e:
            raise UnauthorizedError(f"Invalid token: {e}")

        # Extract user info from claims
        user_id = payload.get("sub")
        name = payload.get("name", payload.get("preferred_username", "Unknown"))
        email = payload.get("email", "")
        roles = payload.get("roles", payload.get("realm_access", {}).get("roles", []))

        # Filter to only AI-Hub roles
        aihub_roles = [r for r in roles if r.startswith("AIHub")]

        # Ensure user exists in database
        await UserEntity.ensure_user_exists_for_auth(
            oid=user_id,
            name=name,
            email=email,
            profile_image=None,
        )

        return UserIdentity(
            id=user_id,
            name=name,
            email=email,
            roles=aihub_roles,
            profile_image=None,
        )
```

#### 5.2 TokenAndOauth2Handler Factory (Simplified)

The factory now directly uses `KeycloakAuthHandler` - no provider switching needed:

```python
@classmethod
def from_auth_settings(cls) -> "TokenAndOauth2Handler":
    """Creates a handler with Keycloak OAuth2 and configured bearer handlers."""
    bearer_handlers: list[Any] = []
    oauth2_handlers: list[KeycloakAuthHandler] = []

    config = AuthSettings()

    # All OAuth2/OIDC goes through Keycloak (which brokers to Azure AD, etc.)
    logger.info("Using Keycloak as identity provider")
    keycloak_handler = KeycloakAuthHandler()
    oauth2_handlers.append(keycloak_handler)

    if SuperuserSettings().ENABLED:
        logger.info("Using superuser authentication")
        superuser_handler = SuperuserAuthHandler()
        bearer_handlers.append(OpenWebuiAuthHandler(base_auth_handler=superuser_handler))
        bearer_handlers.append(superuser_handler)

    if config.ENABLE_API_ACCESS:
        logger.info("Using token authentication")
        token_handler = TokenAuthHandler()
        bearer_handlers.append(OpenWebuiAuthHandler(base_auth_handler=token_handler))
        bearer_handlers.append(token_handler)

    return cls(bearer_handlers=bearer_handlers, oauth2_handlers=oauth2_handlers)
```

### 6. OpenWebUI Integration

#### 6.1 Update Docker Compose Template

Update OpenWebUI OIDC configuration in `docker-compose.yml.j2`:

```yaml
openwebui:
  environment:
    # --- Auth & OIDC ---
    WEBUI_AUTH: True
    ENABLE_OAUTH_SIGNUP: True
    OAUTH_MERGE_ACCOUNTS_BY_EMAIL: True
    OAUTH_PROVIDER_NAME: ${OAUTH_PROVIDER_NAME}
    OAUTH_CLIENT_ID: openwebui
    OAUTH_CLIENT_SECRET: ${KEYCLOAK_OPENWEBUI_CLIENT_SECRET}
    {%- if stage == 'dev' %}
    OPENID_PROVIDER_URL: http://keycloak:8080/realms/aihub/.well-known/openid-configuration
    OPENID_REDIRECT_URI: http://localhost:8080/oauth/oidc/callback
    {%- else %}
    OPENID_PROVIDER_URL: https://auth.${DOMAIN}/realms/aihub/.well-known/openid-configuration
    OPENID_REDIRECT_URI: https://openwebui.${DOMAIN}/oauth/oidc/callback
    {%- endif %}
    OAUTH_SCOPES: openid email profile
    OAUTH_USERNAME_CLAIM: preferred_username
    OAUTH_EMAIL_CLAIM: email
    OAUTH_PICTURE_CLAIM: picture
```

### 7. Frontend Updates

#### 7.1 Update OIDC Client Configuration

Modify `aihub_web/aihub_web/plugins/oidc-client.ts`:

```typescript
// Keycloak-compatible OIDC settings
const settings: UserManagerSettings = {
  authority: process.env.OAUTH_AUTHORITY_URL,  // http://localhost:8180/realms/aihub
  client_id: process.env.OAUTH_CLIENT_ID,      // aihub-frontend
  redirect_uri: `${window.location.origin}/auth/callback`,
  post_logout_redirect_uri: `${window.location.origin}/auth/login`,
  response_type: 'code',
  scope: 'openid profile email',
  automaticSilentRenew: true,
  // Keycloak-specific: Include refresh token
  includeIdTokenInSilentRenew: true,
  // Disable PKCE if using confidential client
  disablePKCE: false,
};
```

### 8. E2E Testing Infrastructure

#### 8.1 Test User Credentials

The development user is configured via environment variables and used for both development and E2E testing:

| Variable | Default | Description |
|----------|---------|-------------|
| `KEYCLOAK_DEV_USER_USERNAME` | `admin` | Login username |
| `KEYCLOAK_DEV_USER_PASSWORD` | `admin` | Login password |
| `KEYCLOAK_DEV_USER_EMAIL` | `admin@ai-hub.local` | User email |
| `KEYCLOAK_DEV_USER_ROLES` | `AIHubAdmin` | Comma-separated roles |

For E2E tests, these credentials are read from environment variables ensuring consistency.

#### 8.2 Playwright Configuration

Create test helper for E2E authentication:

```typescript
// tests/e2e/auth-helpers.ts
export async function loginAsDevUser(page: Page) {
  const username = process.env.KEYCLOAK_DEV_USER_USERNAME || 'admin';
  const password = process.env.KEYCLOAK_DEV_USER_PASSWORD || 'admin';

  await page.goto('/auth/login');

  // Click "Login with Keycloak" button
  await page.click('button:has-text("Keycloak")');

  // Fill Keycloak login form
  await page.fill('#username', username);
  await page.fill('#password', password);
  await page.click('#kc-login');

  // Wait for redirect back to app
  await page.waitForURL('**/dashboard');
}
```

### 9. Production Identity Broker Configuration

#### 9.1 Azure AD as Identity Provider

Add to realm configuration for production:

```json
{
  "identityProviders": [
    {
      "alias": "azure-ad",
      "displayName": "Microsoft Azure AD",
      "providerId": "oidc",
      "enabled": true,
      "firstBrokerLoginFlowAlias": "first broker login",
      "config": {
        "clientId": "${KEYCLOAK_AZURE_CLIENT_ID}",
        "clientSecret": "${KEYCLOAK_AZURE_CLIENT_SECRET}",
        "tokenUrl": "https://login.microsoftonline.com/${KEYCLOAK_AZURE_TENANT_ID}/oauth2/v2.0/token",
        "authorizationUrl": "https://login.microsoftonline.com/${KEYCLOAK_AZURE_TENANT_ID}/oauth2/v2.0/authorize",
        "issuer": "https://login.microsoftonline.com/${KEYCLOAK_AZURE_TENANT_ID}/v2.0",
        "userInfoUrl": "https://graph.microsoft.com/oidc/userinfo",
        "defaultScope": "openid email profile",
        "syncMode": "IMPORT"
      }
    }
  ],
  "identityProviderMappers": [
    {
      "name": "azure-ad-roles",
      "identityProviderAlias": "azure-ad",
      "identityProviderMapper": "oidc-role-idp-mapper",
      "config": {
        "claim": "roles",
        "role": "AIHubUser"
      }
    }
  ]
}
```

### 10. Migration Strategy

#### 10.1 Keycloak as Single IdP

All OAuth2/OIDC authentication now goes exclusively through Keycloak:

1. **Development**: Keycloak with local users (no external IdP needed)
2. **Production**: Keycloak with Azure AD identity broker

No `IDENTITY_PROVIDER` switching - Keycloak is the only OAuth2 handler.

#### 10.2 Azure AD Migration

For production environments currently using Azure AD directly:

1. Configure Keycloak with Azure AD as an identity provider
2. Update application OAuth URLs to point to Keycloak
3. Users authenticate via Keycloak → Azure AD federation
4. User OIDs are preserved (Keycloak uses Azure AD's `sub` claim)
5. Roles and permissions remain in local database

---

## Documentation Updates Required

### 11.1 New Documentation Pages

| Location | Topic |
|----------|-------|
| `docs/2_platform/11_access_management/1_authentication_setup/index.en.md` | Complete Keycloak setup guide |
| `docs/2_platform/3_deployment_guide/2_keycloak_setup/index.en.md` | Production Keycloak configuration |
| `docs/2_platform/19_security/1_authentication/index.en.md` | Update with Keycloak details |

### 11.2 README Updates

Update `/home/user/aihub-core/README.md` with:
- New Keycloak service in architecture diagram
- Updated development login credentials
- E2E testing instructions

### 11.3 ADR Creation

This document serves as the ADR. Additional ADRs may be needed for:
- Breaking changes to auth flow
- Production migration decisions
- Identity broker federation patterns

---

## File Changes Summary

### New Files

| Path | Description |
|------|-------------|
| `deployment/templates/configs/keycloak-realm.json.j2` | Keycloak realm configuration template |
| `configs/keycloak/aihub-realm.*.json` | Generated realm configs for all stages |
| `aihub_lib/.../KeycloakAuthHandler/KeycloakAuthHandler.py` | Keycloak JWT validation handler |
| `aihub_lib/.../KeycloakAuthHandler/KeycloakSettings.py` | Keycloak OIDC settings |

### Modified Files

| Path | Changes |
|------|---------|
| `deployment/templates/docker-compose.yml.j2` | Add Keycloak service, update OpenWebUI OIDC |
| `deployment/compose-config.yml` | Add Keycloak image version |
| `deployment/generate_compose.py` | Add realm config generation |
| `.env.dev` | Add Keycloak variables, remove IDENTITY_PROVIDER |
| `aihub_lib/.../AuthSettings.py` | Remove IDENTITY_PROVIDER (Keycloak is the only IdP) |
| `aihub_lib/.../TokenAndOauth2Handler.py` | Use KeycloakAuthHandler directly |
| `aihub_web/aihub_web/plugins/oidc-client.ts` | Keycloak-compatible OIDC settings |
| `docker-compose.*.yml` | Regenerated with Keycloak service |

---

## Access Points After Implementation

| Service | Dev URL | Production URL |
|---------|---------|----------------|
| Keycloak Admin | http://localhost:8180 | https://auth.${DOMAIN} |
| Keycloak Realm | http://localhost:8180/realms/aihub | https://auth.${DOMAIN}/realms/aihub |
| OpenWebUI | http://localhost:8080 | https://openwebui.${DOMAIN} |
| Admin UI | http://localhost:3000 | https://${DOMAIN} |

---

## Consequences

### Positive

1. **Self-contained Development**: No external IdP required for local development
2. **Reproducible Testing**: Consistent E2E test environment with known credentials
3. **Provider Flexibility**: Easy migration between identity providers
4. **Swiss Sovereignty**: Self-hosted identity management
5. **Standards Compliance**: Full OIDC/OAuth 2.0 support
6. **Single Sign-On**: Unified authentication across all services

### Negative

1. **Increased Complexity**: Additional service to maintain
2. **Resource Overhead**: Keycloak requires ~512MB RAM
3. **Learning Curve**: Team needs Keycloak expertise
4. **Migration Effort**: Existing Azure AD integrations need updates

### Neutral

1. **Database Addition**: One more PostgreSQL database to manage
2. **Configuration Management**: Realm JSON needs version control
3. **Port Allocation**: New port 8180 for Keycloak admin

---

## References

- [Keycloak Docker Documentation](https://www.keycloak.org/getting-started/getting-started-docker)
- [Keycloak Realm Import](https://www.keycloak.org/server/importExport)
- [Keycloak Azure AD Identity Broker](https://www.alphabold.com/azure-ad-configuration/)
- [Keycloak 26.0 Release Notes](https://www.keycloak.org/docs/latest/release_notes/)

---

## Appendix A: Quick Start Commands

### Start Development Environment with Keycloak

```bash
# Generate compose files with Keycloak
make generate-compose

# Start development stack
docker compose -f docker-compose.dev.yml up -d

# Verify Keycloak is running
curl http://localhost:8180/health/ready

# Access Keycloak admin console
open http://localhost:8180  # admin / admin-dev-password-changeme

# Login to OpenWebUI with configurable dev user (defaults: admin / admin)
open http://localhost:8080
```

### Customize Development User

```bash
# Override user credentials in .env or directly
export KEYCLOAK_DEV_USER_USERNAME="myuser"
export KEYCLOAK_DEV_USER_PASSWORD="mypassword"
export KEYCLOAK_DEV_USER_EMAIL="myuser@example.com"
export KEYCLOAK_DEV_USER_ROLES="AIHubAdmin"
export KEYCLOAK_DEV_USER_ROLES_JSON='["AIHubAdmin"]'

# Regenerate and restart
make generate-compose
docker compose -f docker-compose.dev.yml up -d --force-recreate keycloak
```

### Run E2E Tests

```bash
# Start dev environment
docker compose -f docker-compose.dev.yml up -d

# Wait for services
./scripts/wait-for-services.sh

# Run E2E tests
cd aihub_web && pnpm test:e2e
```

---

## Appendix B: Keycloak Admin CLI Commands

```bash
# Export realm for backup
docker compose exec keycloak /opt/keycloak/bin/kc.sh export \
  --dir /opt/keycloak/data/export \
  --realm aihub \
  --users realm_file

# Create additional user via CLI (if needed)
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh create users \
  --realm aihub \
  -s username=newuser \
  -s email=newuser@example.com \
  -s enabled=true \
  --server http://localhost:8080 \
  --user admin \
  --password admin-dev-password-changeme

# Reset dev user password
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh set-password \
  --realm aihub \
  --username ${KEYCLOAK_DEV_USER_USERNAME:-admin} \
  --new-password new-password \
  --server http://localhost:8080 \
  --user admin \
  --password admin-dev-password-changeme

# Add role to user
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh add-roles \
  --realm aihub \
  --uusername ${KEYCLOAK_DEV_USER_USERNAME:-admin} \
  --rolename AIHubDeveloper \
  --server http://localhost:8080 \
  --user admin \
  --password admin-dev-password-changeme
```
