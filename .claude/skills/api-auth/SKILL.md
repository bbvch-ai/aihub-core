---
name: api-auth
description: Reference for the API authentication and authorization system in aihub_lib. Use when user says 'how does auth work', 'add permission to endpoint', 'create a role', 'UserIdentity', 'API key setup', 'RBAC permissions', 'AccessChecker usage', 'OAuth2 config', 'superuser token', 'permission template syntax', or 'protect an endpoint'. Do NOT use for bot auth setup (use setup-bot-connection), NATS auth (use nats-events), or frontend auth state. Covers OAuth2, API keys, superuser auth, RBAC roles, permission wildcards, AccessChecker, and identity providers.
allowed-tools: Read, Grep, Glob
---

# API Authentication & Authorization

Look up auth information. Topic or question via `$ARGUMENTS` (e.g., "permission templates", "UserIdentity", "API keys",
"RBAC", "AccessChecker").

## Authentication Overview

The platform uses a **multi-strategy authentication system**. All strategies produce a `UserIdentity`. The composite
handler `TokenAndOauth2Handler` tries bearer handlers in order, then falls back to OAuth2 handlers. First success wins.

**Handler chain** (constructed in `TokenAndOauth2Handler.from_auth_settings`):

```
Request → TokenAndOauth2Handler.__call__
  Bearer handlers (tried in order, first success wins):
    1. OpenWebuiAuthHandler(base=SuperuserAuthHandler)  ← if SUPERUSER_ENABLED
    2. SuperuserAuthHandler                              ← if SUPERUSER_ENABLED
    3. OpenWebuiAuthHandler(base=TokenAuthHandler)       ← if AUTH_ENABLE_API_ACCESS
    4. TokenAuthHandler                                  ← if AUTH_ENABLE_API_ACCESS
  OAuth2 handlers (tried if all bearer handlers fail):
    5. OAuth2AuthHandler (Azure AD JWT)                  ← always registered
  ↓
UserIdentity { id, name, email, roles, profile_image }
```

For `authenticate_token` (WebSocket auth), the order is reversed: OAuth2 handlers first, then bearer handlers.

**Key file**: `aihub_lib/aihub_lib/auth/dependencies/TokenAndOauth2Handler/TokenAndOauth2Handler.py`

---

## UserIdentity

**File**: `aihub_lib/aihub_lib/auth/identity/UserIdentity.py`

```python
class UserIdentity(BaseModel):
    id: str                    # Unique identifier (OID from Azure AD or custom)
    name: str                  # Display name
    email: str                 # Email address
    roles: list[str]           # Role names (e.g., ["AIHubAdmin", "AIHubUser"])
    profile_image: str | None  # Base64 data URL or None
```

### Injecting UserIdentity into endpoints

```python
from aihub_lib.auth.identity.UserIdentity import UserIdentity

# Permission check + get identity:
user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))]

# Permission check only (ignore identity):
_: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.resource"))]
```

---

## Auth Strategies

### 1. OAuth2 (Azure AD)

**Handler**: `aihub_lib/aihub_lib/auth/dependencies/OAuth2AuthHandler/OAuth2AuthHandler.py`

Flow: JWT token -> Verify JWKS signature (MSAL) -> Extract OID -> Resolve via `AzureIdentityProvider`

Constructor is typed to `AzureIdentityProvider` specifically (not the abstract `IdentityProvider`).

Config env vars: `OAUTH_CLIENT_ID`, `OAUTH_AUTHORITY_URL`, `AUTH_IDENTITY_PROVIDER=azure`

### 2. API Keys (Bearer Tokens)

**Handler**: `aihub_lib/aihub_lib/auth/dependencies/TokenAuthHandler/TokenAuthHandler.py`

Flow: Bearer token -> Parse `<24-char-hex-oid>.<128-char-urlsafe-random>` -> `BearerToken.verify_token` (DB lookup +
expiry check) -> Resolve via `TokenIdentityProvider`

**Entity**: `aihub_lib/aihub_lib/persistence/access/entities/BearerToken.py`

Config: `AUTH_ENABLE_API_ACCESS=true` (default)

### 3. Superuser (Master Key)

**Handler**: `aihub_lib/aihub_lib/auth/dependencies/SuperuserAuthHandler/SuperuserAuthHandler.py`

Flow: Bearer token -> Constant-time compare with `SUPERUSER_TOKEN` env var -> Resolve via `SuperuserIdentityProvider`
(fixed identity from env vars)

Config: `SUPERUSER_ENABLED`, `SUPERUSER_NAME`, `SUPERUSER_EMAIL`, `SUPERUSER_OID`, `SUPERUSER_ROLE`, `SUPERUSER_TOKEN`
(min 64 chars)

### 4. OpenWebUI Proxy

**Handler**: `aihub_lib/aihub_lib/auth/dependencies/OpenWebuiAuthHandler/OpenWebuiAuthHandler.py`

Flow: Delegate to base handler (Superuser or Token) to validate bearer token -> Verify HMAC-SHA256 signature of
OpenWebUI headers (`name:{name},email:{email}`) -> Resolve the **OpenWebUI user** (not the token owner) via
`AzureIdentityProvider.get_user_identity_by_email`

The bearer token is only a validity proof. The returned `UserIdentity` is the OpenWebUI user identified by the signed
headers.

Headers: `X-OpenWebUI-User-Name`, `X-OpenWebUI-User-Email`, `X-OpenWebUI-Signature`

Config: `AUTH_OPEN_WEBUI_SIGNING_SECRET` (min 64 chars)

---

## Identity Providers

Identity providers resolve tokens/OIDs into `UserIdentity` objects. Each auth handler delegates to a specific provider.

**Abstract base**: `aihub_lib/aihub_lib/auth/identity/IdentityProvider.py`

```python
class IdentityProvider(ABC):
    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity: ...
    async def get_user_identity_by_email(self, email: str) -> UserIdentity: ...
    async def get_user_roles(self, user_oid: str) -> list[str]: ...
    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None: ...
```

| Provider                                   | File                                                                  | Used by                    | What it does                                                                            |
| ------------------------------------------ | --------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------- |
| `AzureIdentityProvider`                    | `.../identity/AzureIdentityProvider/AzureIdentityProvider.py`         | OAuth2, OpenWebUI handlers | Graph API for profile, roles, photo; syncs local DB via `UserEntity.ensure_user_exists` |
| `SuperuserIdentityProvider`                | `.../identity/SuperuserIdentityProvider/SuperuserIdentityProvider.py` | SuperuserAuthHandler       | Fixed identity from `SuperuserSettings`; raises if OID/email mismatch                   |
| `TokenIdentityProvider`                    | `.../identity/TokenIdentityProvider/TokenIdentityProvider.py`         | TokenAuthHandler           | Looks up user from MongoDB `UserEntity`; no external calls                              |
| `DangerousDevelopmentOnlyIdentityProvider` | `.../identity/DangerousDevelopmentOnlyIdentityProvider/...`           | Dev auth handler           | Fixed dev user from `DangerousDevelopmentOnlyAuthSettings`                              |

---

## Permission System

### Permission Template Format

```
aihub.[user|admin].<resource>.<subresource>.<id>
```

Examples:

```
aihub.user.?>                                    # Any authenticated user
aihub.user.agent.?>                              # Any agent access
aihub.user.agent.{agent_class}.{agent_id}        # Specific agent instance
aihub.admin.agent.{agent_class}                  # Admin access to agent class
aihub.admin.service.user                         # Admin access to user service
```

### Wildcards

**In access rules (what roles grant)**:

- `*` -- Single-level wildcard (matches one segment)
- `>` -- Multi-level wildcard (matches remaining path, MUST be last)

**In permission templates (what endpoints require)**:

- `?*` -- Implicit single-level check (matches if user has ANY rule at this level)
- `?>` -- Implicit multi-level check (matches if user has ANY rule at or below this level)

The `?` prefix distinguishes template wildcards from access rule wildcards. Templates use `?*`/`?>`, access rules use
`*`/`>`.

### How Permission Checking Works

```python
# 1. Controller defines permission template with {path_param} placeholders:
@self.router.get("/agents/classes/{agent_class}/instances/{agent_id}")
async def get_agent_instance(
    agent_class: str, agent_id: str,
    _: Annotated[UserIdentity, Security(
        self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))],
):

# 2. user_with_permission resolves template against path params:
#    "aihub.user.agent.{agent_class}.{agent_id}"
#    -> "aihub.user.agent.TranslationAgent.translator_1"

# 3. Three-gate check (in Controller.user_with_permission):
#    Gate 1: has_access_to_service(self.service_name)  <- derived from class name
#    Gate 2: has_access(additionally_required_permission)  <- if set on controller
#    Gate 3: has_access(resolved_permission)  <- the route-specific check

# 4. Admin rules also grant user access:
#    "aihub.admin.agent.TranslationAgent.*" grants both admin AND user access
```

### Common Permission Patterns for Controllers

```python
# Any authenticated user
Security(self.user_with_permission("aihub.user.?>"))

# User access to specific resource
Security(self.user_with_permission("aihub.user.resource.{resource_id}"))

# Admin access to create
Security(self.user_with_permission("aihub.admin.resource"))

# Admin access to modify specific resource
Security(self.user_with_permission("aihub.admin.resource.{resource_id}"))

# Service-level admin (entire controller)
Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
```

---

## AccessChecker

**File**: `aihub_lib/aihub_lib/auth/access/AccessChecker.py`

Use for **dynamic permission checks** beyond the endpoint-level template.

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel

access_checker = AccessChecker.from_user(user)
```

### Methods

| Method                                       | Returns         | Purpose                                                  |
| -------------------------------------------- | --------------- | -------------------------------------------------------- |
| `from_user(user)` (classmethod)              | `AccessChecker` | Construct from UserIdentity (fetches role rules from DB) |
| `has_access(template)`                       | `bool`          | General permission check                                 |
| `access_level(template)`                     | `AccessLevel`   | Get admin/user/denied level                              |
| `has_access_to_service(name)`                | `bool`          | Service-level check                                      |
| `access_level_for_service(name)`             | `AccessLevel`   | Admin vs user for service                                |
| `has_access_to_agent(cls, id)`               | `bool`          | Agent instance access                                    |
| `has_access_to_agent_class(cls)`             | `bool`          | Any instance in class (uses `?*`)                        |
| `access_level_for_agent(cls, id)`            | `AccessLevel`   | Admin vs user for agent                                  |
| `has_access_to_process(cls, id)`             | `bool`          | Process instance access                                  |
| `has_access_to_process_class(cls)`           | `bool`          | Any instance in process class                            |
| `access_level_for_process(cls, id)`          | `AccessLevel`   | Admin vs user for process                                |
| `validate_user_access_rule(rule)` (static)   | `bool`          | Validates a DB access rule (returns False on invalid)    |
| `validate_permission_template(tpl)` (static) | `None`          | Validates a code-level template (raises ValueError)      |

### AccessLevel Enum

**File**: `aihub_lib/aihub_lib/auth/access/AccessLevel.py`

```python
class AccessLevel(Enum):
    ACCESS_DENIED = 0
    ACCESS_USER = 1
    ACCESS_ADMIN = 2
```

### Usage: Filter results by access

```python
@staticmethod
async def get_visible_agents(user: UserIdentity, t: LocaleHandler) -> list[AgentDTO]:
    all_agents = await AgentService.get_all_agents(t)
    access_checker = AccessChecker.from_user(user)
    return [
        agent for agent in all_agents
        if access_checker.has_access_to_agent(agent.agent_class, agent.agent_id)
    ]
```

### Usage: Admin sees all, user sees own

```python
access_level = AccessChecker.from_user(user).access_level_for_agent(agent_class, agent_id)
if access_level == AccessLevel.ACCESS_ADMIN:
    threads = ThreadEntity.get_all_threads_for_agent(agent_class, agent_id)
elif access_level == AccessLevel.ACCESS_USER:
    threads = ThreadEntity.get_threads_for_agent_and_user(agent_class, agent_id, user.id)
else:
    raise HTTPException(status_code=403, detail="No access")
```

---

## RBAC (Role-Based Access Control)

### RoleEntity

**File**: `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py`

```python
class RoleEntity(Document):
    name = StringField(required=True, unique=True)
    description = StringField(required=True)
    access_rules = ListField(StringField(), default=list)
```

Classmethods: `get_role_by_name(name) -> RoleEntity | None`, `get_access_rules_for_roles(names) -> set[str]`,
`filter_existing_roles(names) -> list[str]` (static)

### Access Rule Examples

```python
# Full access to everything
"aihub.user.>"
"aihub.admin.>"

# Agent management
"aihub.user.agent.>"            # User access to all agents
"aihub.admin.agent.>"           # Admin access to all agents
"aihub.user.agent.MyAgent.*"    # User access to all MyAgent instances
"aihub.admin.agent.MyAgent.*"   # Admin access to all MyAgent instances

# Service access
"aihub.user.service.agent"      # User can view agent service
"aihub.admin.service.role"      # Admin can manage roles

# Specific resource
"aihub.user.agent.MyAgent.instance-1"  # Access to one specific instance
```

### Creating Roles

```python
RoleEntity(
    name="AgentViewer",
    description="Can view all agent instances",
    access_rules=[
        "aihub.user.agent.>",
        "aihub.user.service.agent",
    ]
).save()
```

---

## Controller Base Class

**File**: `aihub_lib/aihub_lib/routes/Controller.py`

`Controller.__init__` accepts `auth: AuthHandler` (keyword-only). If falsy, falls back to
`DangerousDevelopmentOnlyAuthHandler` -- this is why tests work without explicit auth setup.

`service_name` is derived from the class name: `AgentController` -> `"agent"`, `RoleController` -> `"role"`.

`additionally_required_permission` (optional `str | None`) adds an extra gate checked between the service-level and
route-level permission checks.

---

## Testing Auth

### Development Auth Handler

```python
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler

# Bypasses all auth -- returns a fixed dev user identity.
# Used automatically by Controller when no auth handler is provided.
auth = DangerousDevelopmentOnlyAuthHandler(
    identity_provider=DangerousDevelopmentOnlyIdentityProvider()
)
```

### Test with Superuser Token

```python
headers = {"Authorization": f"Bearer {SUPERUSER_TOKEN}"}
response = await client.get("/api/v1/resources", headers=headers)
```

### Test with API Key

```python
token = BearerToken.create_new_token(name="test", expiry_date=future_date, user_oid=user_oid)
headers = {"Authorization": f"Bearer {token.token}"}
response = await client.get("/api/v1/resources", headers=headers)
```

---

## Key Files Reference

| Category          | File                                                                                   |
| ----------------- | -------------------------------------------------------------------------------------- |
| Composite handler | `aihub_lib/aihub_lib/auth/dependencies/TokenAndOauth2Handler/TokenAndOauth2Handler.py` |
| Auth base class   | `aihub_lib/aihub_lib/auth/dependencies/AuthHandler.py`                                 |
| Bearer base class | `aihub_lib/aihub_lib/auth/dependencies/BearerAuthHandler.py`                           |
| OAuth2            | `aihub_lib/aihub_lib/auth/dependencies/OAuth2AuthHandler/OAuth2AuthHandler.py`         |
| API keys          | `aihub_lib/aihub_lib/auth/dependencies/TokenAuthHandler/TokenAuthHandler.py`           |
| Superuser         | `aihub_lib/aihub_lib/auth/dependencies/SuperuserAuthHandler/SuperuserAuthHandler.py`   |
| OpenWebUI         | `aihub_lib/aihub_lib/auth/dependencies/OpenWebuiAuthHandler/OpenWebuiAuthHandler.py`   |
| Identity base     | `aihub_lib/aihub_lib/auth/identity/IdentityProvider.py`                                |
| UserIdentity      | `aihub_lib/aihub_lib/auth/identity/UserIdentity.py`                                    |
| AccessChecker     | `aihub_lib/aihub_lib/auth/access/AccessChecker.py`                                     |
| AccessLevel       | `aihub_lib/aihub_lib/auth/access/AccessLevel.py`                                       |
| Controller base   | `aihub_lib/aihub_lib/routes/Controller.py`                                             |
| RoleEntity        | `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py`                        |
| BearerToken       | `aihub_lib/aihub_lib/persistence/access/entities/BearerToken.py`                       |
| Auth settings     | `aihub_lib/aihub_lib/auth/dependencies/AuthSettings.py`                                |
| Superuser ADR     | `aihub_doc/arc42/decisions/2025_08_11_global_superuser_authentication.md`              |

---

## Troubleshooting

| Issue                             | Likely Cause                                     | Fix                                                               |
| --------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------- |
| 401 on all endpoints              | `SUPERUSER_TOKEN` not set or too short           | Set token with min 64 chars in .env                               |
| 403 despite valid token           | User's roles lack required access rule           | Check `RoleEntity` access_rules match the permission template     |
| OAuth2 token rejected             | Wrong `OAUTH_CLIENT_ID` or `OAUTH_AUTHORITY_URL` | Verify Azure AD app registration matches env vars                 |
| API key not working               | `AUTH_ENABLE_API_ACCESS` is false                | Set to `true` in env, restart API                                 |
| Permission template not matching  | Path params not resolving in template            | Verify `{param}` names match FastAPI path parameter names exactly |
| OpenWebUI 400 "headers missing"   | Missing `X-OpenWebUI-*` headers                  | Ensure OpenWebUI sends all 3 headers with HMAC signature          |
| OpenWebUI 401 "invalid signature" | `AUTH_OPEN_WEBUI_SIGNING_SECRET` mismatch        | Must match between API and OpenWebUI config                       |
