---
name: api-auth-guide
description: >-
  Reference guide for the API authentication and authorization system. Use when user says 'how
  does auth work', 'add permission to endpoint', 'create a role', 'UserIdentity', 'API key
  setup', 'RBAC permissions', 'AccessChecker usage', 'OAuth2 config', 'superuser token',
  'permission template syntax', or 'protect an endpoint'. Covers OAuth2, API keys, superuser
  auth, RBAC roles, permission wildcards, and AccessChecker patterns.
allowed-tools: Read, Grep, Glob
---

# API Authentication & Authorization Guide

Look up auth information. Topic or question via `$ARGUMENTS` (e.g., "permission templates", "UserIdentity", "API keys", "RBAC", "AccessChecker").

## Authentication Overview

The platform uses a **multi-strategy authentication system** with 4 auth methods, all producing a `UserIdentity`:

```
Request
  |
  v
TokenAndOauth2Handler (composite)
  ├── BearerAuthHandler(s):
  │   ├── OpenWebuiAuthHandler -> SuperuserAuthHandler
  │   ├── SuperuserAuthHandler (master key)
  │   ├── OpenWebuiAuthHandler -> TokenAuthHandler
  │   └── TokenAuthHandler (API keys)
  └── OAuth2AuthHandler(s):
      └── OAuth2AuthHandler (Azure AD JWT)
  |
  v
UserIdentity { id, name, email, roles, profile_image }
```

All strategies are tried sequentially. First success wins.

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

### How to inject UserIdentity into endpoints

```python
from typing import Annotated
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from fastapi import Security

# Permission check + get identity:
user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))]

# Permission check only (ignore identity):
_: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.resource"))]
```

### UserIdentity fields

| Field | Type | Description |
|-------|------|-------------|
| `user.id` | `str` | Unique user OID (from Azure AD or custom) |
| `user.name` | `str` | Display name |
| `user.email` | `str` | Email address |
| `user.roles` | `list[str]` | Role names from identity provider |
| `user.profile_image` | `str \| None` | Base64 data URL (`data:image/jpeg;base64,...`) |

---

## Auth Strategies

### 1. OAuth2 (Azure AD)

**Handler**: `OAuth2AuthHandler`
**File**: `aihub_lib/aihub_lib/auth/dependencies/OAuth2AuthHandler/`

**Flow**: JWT token -> Verify JWKS signature -> Extract OID -> Fetch from Microsoft Graph API

**Config**:
```bash
OAUTH_CLIENT_ID=<azure-app-client-id>
OAUTH_AUTHORITY_URL=https://login.microsoftonline.com/<tenant-id>
AUTH_IDENTITY_PROVIDER=azure
```

**Identity Provider**: `AzureIdentityProvider` -> Microsoft Graph API for user profile, roles, photo

### 2. API Keys (Bearer Tokens)

**Handler**: `TokenAuthHandler`
**File**: `aihub_lib/aihub_lib/auth/dependencies/TokenAuthHandler/`

**Flow**: Bearer token -> Parse `<oid>.<random128>` -> Lookup in MongoDB -> Verify expiry

**Token format**: `507f1f77bcf86cd799439011.kj3h4k2jh3k4jhk2j3hk4j2h3kj4h2k3jh...` (24-char ObjectId + `.` + 128-char random)

**Entity**: `BearerToken` in `aihub_lib/aihub_lib/persistence/access/entities/BearerToken.py`

**Config**:
```bash
AUTH_ENABLE_API_ACCESS=true
```

### 3. Superuser (Master Key)

**Handler**: `SuperuserAuthHandler`
**File**: `aihub_lib/aihub_lib/auth/dependencies/SuperuserAuthHandler/`

**Flow**: Bearer token -> Constant-time compare with env var -> Fixed identity from env

**Config**:
```bash
SUPERUSER_ENABLED=true
SUPERUSER_NAME="AI Hub Superuser"
SUPERUSER_EMAIL=superuser@example.com
SUPERUSER_OID=<unique-uuid>
SUPERUSER_ROLE=AIHubSuperuser
SUPERUSER_TOKEN=<min-64-char-secret>
```

### 4. OpenWebUI Proxy

**Handler**: `OpenWebuiAuthHandler`
**File**: `aihub_lib/aihub_lib/auth/dependencies/OpenWebuiAuthHandler/`

**Flow**: Delegate to base handler (Superuser/Token) -> Verify HMAC signature of OpenWebUI headers -> Lookup user by email

**Headers**: `X-OpenWebUI-User-Name`, `X-OpenWebUI-User-Email`, `X-OpenWebUI-Signature`

**Config**:
```bash
AUTH_OPEN_WEBUI_SIGNING_SECRET=<min-64-char-secret>
```

---

## Permission System

### Permission Template Format

```
aihub.[user|admin].<resource>.<subresource>.<id>
```

**Examples**:
```
aihub.user.?>                                    # Any authenticated user
aihub.user.agent.?>                              # Any agent access
aihub.user.agent.{agent_class}.{agent_id}        # Specific agent instance
aihub.admin.agent.{agent_class}                  # Admin access to agent class
aihub.admin.service.user                         # Admin access to user service
```

### Wildcards

**In Access Rules (what roles grant)**:
- `*` — Single-level wildcard (matches one segment)
- `>` — Multi-level wildcard (matches remaining path, MUST be last)

**In Permission Templates (what endpoints require)**:
- `?*` — Implicit single-level check (matches if user has ANY rule at this level)
- `?>` — Implicit multi-level check (matches if user has ANY rule at or below this level)

### How Permission Checking Works

```python
# 1. Controller defines permission template with {path_param} placeholders:
@self.router.get("/agents/classes/{agent_class}/instances/{agent_id}")
async def get_agent_instance(
    agent_class: str,
    agent_id: str,
    _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))],
):

# 2. Controller base class resolves template against path params:
#    "aihub.user.agent.{agent_class}.{agent_id}"
#    -> "aihub.user.agent.TranslationAgent.translator_1"

# 3. AccessChecker checks user's roles against resolved permission:
#    User roles -> RoleEntity.get_access_rules_for_roles(roles) -> set of rules
#    Match rules against permission using wildcard logic

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

Use when you need **dynamic permission checks** beyond the endpoint-level template.

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel

access_checker = AccessChecker.from_user(user)
```

### Methods

| Method | Returns | Purpose |
|--------|---------|---------|
| `has_access(template)` | `bool` | General permission check |
| `access_level(template)` | `AccessLevel` | Get admin/user/denied level |
| `has_access_to_service(name)` | `bool` | Service-level check |
| `has_access_to_agent(cls, id)` | `bool` | Agent instance access |
| `has_access_to_agent_class(cls)` | `bool` | Any instance in class |
| `has_access_to_process(cls, id)` | `bool` | Process instance access |
| `access_level_for_agent(cls, id)` | `AccessLevel` | Admin vs user for agent |
| `access_level_for_service(name)` | `AccessLevel` | Admin vs user for service |

### AccessLevel Enum

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
    name: str                 # Unique role name
    description: str          # Human-readable description
    access_rules: list[str]   # Permission patterns
```

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
# Via entity
RoleEntity(
    name="AgentViewer",
    description="Can view all agent instances",
    access_rules=[
        "aihub.user.agent.>",
        "aihub.user.service.agent",
    ]
).save()

# Superuser role (full access)
RoleEntity(
    name="AIHubSuperuser",
    description="Full access to everything",
    access_rules=[
        "aihub.user.>",
        "aihub.admin.>",
    ]
).save()
```

---

## Controller Base Class: user_with_permission

**File**: `aihub_lib/aihub_lib/routes/Controller.py`

The `user_with_permission` method creates a FastAPI dependency that:

1. **Authenticates** the request (via `self.auth`)
2. **Checks service-level access** (`has_access_to_service(self.service_name)`)
3. **Checks additional permission** (if `additionally_required_permission` set)
4. **Checks endpoint permission** (resolves template against path params)
5. **Enriches OpenTelemetry span** (user ID, email, roles, permission)
6. **Returns `UserIdentity`** if all checks pass

```python
# Service name is derived from controller class name:
# AgentController -> "agent"
# UserController -> "user"
# RoleController -> "role"

@property
def service_name(self):
    return self.__class__.__name__.lower().replace("controller", "")
```

---

## Testing Auth

### Development Auth Handler

```python
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler

# Bypasses all auth for testing:
auth = DangerousDevelopmentOnlyAuthHandler()
controller = MyController(auth=auth)
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

| Category | File |
|----------|------|
| **Composite handler** | `aihub_lib/aihub_lib/auth/dependencies/TokenAndOauth2Handler/TokenAndOauth2Handler.py` |
| **OAuth2** | `aihub_lib/aihub_lib/auth/dependencies/OAuth2AuthHandler/OAuth2AuthHandler.py` |
| **API keys** | `aihub_lib/aihub_lib/auth/dependencies/TokenAuthHandler/TokenAuthHandler.py` |
| **Superuser** | `aihub_lib/aihub_lib/auth/dependencies/SuperuserAuthHandler/SuperuserAuthHandler.py` |
| **OpenWebUI** | `aihub_lib/aihub_lib/auth/dependencies/OpenWebuiAuthHandler/OpenWebuiAuthHandler.py` |
| **UserIdentity** | `aihub_lib/aihub_lib/auth/identity/UserIdentity.py` |
| **AccessChecker** | `aihub_lib/aihub_lib/auth/access/AccessChecker.py` |
| **AccessLevel** | `aihub_lib/aihub_lib/auth/access/AccessLevel.py` |
| **Controller base** | `aihub_lib/aihub_lib/routes/Controller.py` |
| **RoleEntity** | `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py` |
| **BearerToken** | `aihub_lib/aihub_lib/persistence/access/entities/BearerToken.py` |
| **UserEntity** | `aihub_lib/aihub_lib/persistence/user/UserEntity.py` |
| **Auth settings** | `aihub_lib/aihub_lib/auth/dependencies/AuthSettings.py` |
| **Superuser ADR** | `aihub_doc/arc42/decisions/2025_08_11_global_superuser_authentication.md` |
| **Main app** | `aihub_api/app/main.py` |

---

## Environment Variables

```bash
# Identity Provider
AUTH_IDENTITY_PROVIDER=azure              # azure | (future: ldap)

# OAuth2 (Azure AD)
OAUTH_CLIENT_ID=<app-client-id>
OAUTH_AUTHORITY_URL=https://login.microsoftonline.com/<tenant>

# API Keys
AUTH_ENABLE_API_ACCESS=true

# Superuser
SUPERUSER_ENABLED=true
SUPERUSER_NAME="AI Hub Superuser"
SUPERUSER_EMAIL=superuser@example.com
SUPERUSER_OID=<uuid>
SUPERUSER_ROLE=AIHubSuperuser
SUPERUSER_TOKEN=<min-64-chars>

# OpenWebUI
AUTH_OPEN_WEBUI_SIGNING_SECRET=<min-64-chars>
```

---

## Examples

- `/api-auth-guide how to protect a new endpoint` -- Shows `user_with_permission` pattern with Security dependency
- `/api-auth-guide permission template syntax` -- Explains wildcards (`*`, `>`, `?*`, `?>`) and template format
- `/api-auth-guide create a role for agent viewers` -- Shows RoleEntity creation with access rules
- `/api-auth-guide test auth in dev` -- Shows DangerousDevelopmentOnlyAuthHandler and superuser token usage

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| 401 Unauthorized on all endpoints | SUPERUSER_TOKEN not set or too short | Set token with min 64 chars in .env |
| 403 Forbidden despite valid token | User's roles lack required access rule | Check RoleEntity access_rules match the permission template |
| OAuth2 token rejected | Wrong OAUTH_CLIENT_ID or AUTHORITY_URL | Verify Azure AD app registration matches env vars |
| API key not working | `AUTH_ENABLE_API_ACCESS` is false | Set to `true` in env, restart API |
| Permission template not matching | Path params not resolving in template | Verify `{param}` names match FastAPI path parameter names exactly |
