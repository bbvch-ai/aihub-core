# Plan: Filter OpenWebUI Agent Visibility by User Permissions (Issue #779)

## Context

OpenWebUI shows ALL online agents to ALL users. The `pipes()` discovery method is called without user context (OpenWebUI
architecture limitation). Users see agents they can't use, get 403 errors, and agent metadata is exposed to unauthorized
users.

**Root cause**: `AgentDiscoveryService.discover_agents()` in `aihub_pipeline.py` calls `GET /api/v1/agents/instances`
with a **superuser token**, bypassing per-user permission filtering. And `pipes()` cannot be fixed to receive user
context — OpenWebUI calls it without arguments.

**Solution**: AI-Hub creates **OpenWebUI workspace models** (stored in OpenWebUI's `model` table, subject to access
control) for each agent. **OpenWebUI groups** map to AI-Hub tenant+role combinations. AI-Hub computes effective
permissions and manages group memberships + model access grants via OpenWebUI's REST API. Regular users only see
workspace models they have group access to.

## Affected Scopes

| Scope        | Why                                                                      |
| ------------ | ------------------------------------------------------------------------ |
| `aihub_lib`  | New `infrastructure/openwebui/` module (Settings, Client, Provisioner)   |
| `aihub_api`  | Integration into `AgentEndpointsDiscoveryService` and `lifetime_manager` |
| `deployment` | Docker-compose env vars for OpenWebUI access control                     |

## Implementation Steps

### Step 1: Create `OpenWebuiSettings` (aihub_lib)

**File**: `aihub_lib/aihub_lib/infrastructure/openwebui/OpenWebuiSettings.py`

Follow `LangfuseSettings` pattern (`aihub_lib/aihub_lib/infrastructure/langfuse/LangfuseSettings.py`):

```python
class OpenWebuiSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_")
    BASE_URL: Annotated[str, Field(description="OpenWebUI server base URL")]
    API_KEY: Annotated[SecretStr, Field(description="OpenWebUI admin API key")]
```

Also create `aihub_lib/aihub_lib/infrastructure/openwebui/__init__.py` (empty).

### Step 2: Create `OpenWebuiClient` (aihub_lib)

**File**: `aihub_lib/aihub_lib/infrastructure/openwebui/OpenWebuiClient.py`

Thin async httpx wrapper for OpenWebUI's REST API. Takes `httpx.AsyncClient` as param (caller manages lifecycle, same as
`LangfuseProvisioner`).

Methods needed:

- `list_groups()` → `GET /api/v1/groups/`
- `create_group(name, description)` → `POST /api/v1/groups/create`
- `delete_group(group_id)` → `DELETE /api/v1/groups/id/{id}/delete`
- `add_users_to_group(group_id, user_ids)` → `POST /api/v1/groups/id/{id}/users/add`
- `remove_users_from_group(group_id, user_ids)` → `POST /api/v1/groups/id/{id}/users/remove`
- `list_models()` → `GET /api/v1/models/list`
- `create_model(data)` → `POST /api/v1/models/create`
- `update_model(model_id, data)` → `POST /api/v1/models/model/update?id={id}`
- `delete_model(model_id)` → `POST /api/v1/models/model/delete`
- `update_model_access(model_id, grants)` → `POST /api/v1/models/model/access/update?id={id}`
- `list_users()` → `GET /api/v1/users/`

Auth: Bearer token via `Authorization: Bearer {API_KEY}` header on all requests.

### Step 3: Create `OpenWebuiProvisioner` (aihub_lib)

**File**: `aihub_lib/aihub_lib/infrastructure/openwebui/OpenWebuiProvisioner.py`

Follow `LangfuseProvisioner` pattern exactly. Three public methods:

```python
class OpenWebuiProvisioner:
    async def provision(self) -> None:
        """Full sync at startup — groups, workspace models, access grants."""

    async def sync_agents(self, online_agents: list[tuple[str, str, str]]) -> None:
        """Called when agent discovery detects changes. Args: [(agent_class, agent_id, display_name)]"""

    async def sync_access(self) -> None:
        """Called when roles or tenants are modified."""
```

#### Core sync logic

**`_sync_groups(client)`**:

1. Query all tenants from `TenantEntity`
2. For each tenant, get all roles from `RoleEntity.get_roles_for_tenant(tenant_id)`
3. Desired groups: `{f"aihub:{tenant.name}:{role.name}" for each tenant×role combo}`
4. Fetch existing OpenWebUI groups, filter by `aihub:` prefix
5. Create missing groups, delete orphaned groups
6. For each group, query `UserTenantRoleEntity.get_user_ids_in_tenant(tenant_id)` filtered by role
7. Map AI-Hub user IDs → OpenWebUI user IDs via email (fetch OpenWebUI users, build email→owui_id cache)
8. Sync group membership (add missing users, remove extra users)

**`_sync_workspace_models(client, online_agents)`**:

1. For each online agent `(agent_class, agent_id, display_name)`:
   - Workspace model ID: `aihub-agent-{agent_class}-{agent_id}` (stable, independent of pipe ID format)
   - `base_model_id`: `aihub-pipeline.{agent_class}.{agent_id}` (matches pipe-discovered model ID from OpenWebUI's
     `get_function_models()` — format is `{function_id}.{sub_pipe_id}`)
   - `name`: display_name from agent config
2. Fetch existing workspace models from OpenWebUI, filter by `aihub-agent-` prefix
3. Create new models for newly online agents, delete models for offline agents
4. Call `_sync_access_grants()` for each model

**`_sync_access_grants(client)`**:

1. For each workspace model (wrapping agent `agent_class/agent_id`):
2. For each group `aihub:{tenant_name}:{role_name}`:
   - Reconstruct access rules from `TenantEntity.access_rules` + `RoleEntity.access_rules`
   - Create an `AccessChecker(user_access_rules=role_rules, tenant_access_rules=tenant_rules)`
   - Check `checker.has_access_to_agent(agent_class, agent_id)`
   - If yes → include group in access grants
3. Call `update_model_access(model_id, grants)` with:
   ```json
   {"access_grants": [
     {"principal_type": "group", "principal_id": "<group_id>", "permission": "read"}
   ]}
   ```
   Note: empty grants = private/owner-only (not visible). Non-empty = visible to specified groups.

#### User ID mapping

OpenWebUI user IDs ≠ AI-Hub user IDs. Both systems share Keycloak SSO, so **email** is the common key.

- AI-Hub: `UserEntity.by_oid(user_id)` → get email
- OpenWebUI: `GET /api/v1/users/` → find user by email → get OpenWebUI user ID
- Cache this mapping during sync to avoid repeated lookups
- If a user hasn't logged into OpenWebUI yet, skip them (they'll be synced on next cycle after login)

### Step 4: Integrate into `AgentEndpointsDiscoveryService`

**File**: `aihub_api/aihub_api/services/AgentEndpointsDiscoveryService.py`

Add `openwebui_provisioner: OpenWebuiProvisioner | None = None` to constructor (parallel to `langfuse_provisioner`).

Add `_sync_agent_instances_to_openwebui()` method, called at the end of `_discover_and_register()` alongside the
existing Langfuse sync:

```python
async def _sync_agent_instances_to_openwebui(self) -> None:
    if self._openwebui_provisioner is None:
        return
    instances = await AgentService.get_all_agent_instances(t=self.locale_handler, online=True)
    online_agents = [(i.agent_class, i.agent_id, i.name) for i in instances if i.is_conversational]
    try:
        await self._openwebui_provisioner.sync_agents(online_agents)
    except Exception as e:
        logger.warning(f"OpenWebUI agent sync failed (non-fatal): {e}")
```

### Step 5: Integrate into `lifetime_manager.py`

**File**: `aihub_api/aihub_api/runners/lifetime/lifetime_manager.py`

After `langfuse_provisioner` setup:

```python
try:
    openwebui_provisioner = OpenWebuiProvisioner()
except Exception:
    logger.info("OpenWebUI provisioner not configured, skipping agent visibility sync")
    openwebui_provisioner = None

# Pass to discovery service
agent_discovery_service = AgentEndpointsDiscoveryService(
    ...,
    langfuse_provisioner=langfuse_provisioner,
    openwebui_provisioner=openwebui_provisioner,
)

# Full provisioning after DB init
if openwebui_provisioner:
    await openwebui_provisioner.provision()

# Store for role/tenant change triggers
app.state.openwebui_provisioner = openwebui_provisioner
```

### Step 6: Add env vars to docker-compose

**File**: `deployment/templates/docker-compose.yml.j2`

Add to the **api** service environment:

```yaml
OPENWEBUI_BASE_URL: http://open-webui:8080
OPENWEBUI_API_KEY: ${OPENWEBUI_API_KEY}
```

Add to the **open-webui** service environment:

```yaml
BYPASS_MODEL_ACCESS_CONTROL: "False"
```

**File**: `.env.dev`

```
OPENWEBUI_BASE_URL=http://localhost:8080
OPENWEBUI_API_KEY=<admin JWT or API key - see note below>
```

**Auth note**: OpenWebUI's API requires an admin bearer token. Options:

1. Generate an API key from OpenWebUI admin UI and store in `.env`
2. Generate a JWT using `WEBUI_SECRET_KEY` (OpenWebUI uses PyJWT with HS256)
3. The provisioner could generate a short-lived JWT at startup from the `WEBUI_SECRET_KEY`

Option 3 is most practical — avoids manual config. Add `WEBUI_SECRET_KEY` as a setting in `OpenWebuiSettings` and
generate the JWT programmatically.

### Step 7: Hook role/tenant changes into sync (optional — can be follow-up)

When roles or tenants are modified via the admin API, trigger `openwebui_provisioner.sync_access()`. This requires
accessing the provisioner from the service layer.

Two options:

- Store on `app.state.openwebui_provisioner`, create a `use_openwebui_provisioner` FastAPI dependency
- Or defer this to a periodic full sync (the 60-second discovery cycle already runs `sync_agents`)

**Recommendation**: Start without this trigger. The 60-second agent discovery cycle calls `sync_agents()` which also
refreshes access grants. Role/tenant changes are admin-only and infrequent — a 60-second delay is acceptable. Add
explicit triggers as a follow-up if needed.

### Step 8: Tests

**File**: `aihub_lib/tests/infrastructure/openwebui/test_openwebui_provisioner.py`

Mock httpx responses to test:

- Group sync: creates expected groups, deletes orphaned ones
- Workspace model sync: creates models for online agents, removes for offline
- Access grant computation: role+tenant rules correctly determine which groups access which agents
- User ID mapping: email-based resolution handles missing users gracefully
- Idempotency: running sync twice produces same result
- Resilience: step failure doesn't block others

## Key Technical Details

### Pipe model ID format

OpenWebUI's `get_function_models()` builds model IDs as `{function_id}.{sub_pipe_id}`.

- Function ID for `aihub_pipeline.py`: `aihub-pipeline` (from `init-functions.sh`: `basename .py | tr _ -`)
- Sub-pipe ID from `pipes()`: `{agent_class}.{agent_id}`
- **Full pipe model ID**: `aihub-pipeline.{agent_class}.{agent_id}`

### Workspace model → pipe delegation

Workspace model `base_model_id = "aihub-pipeline.{agent_class}.{agent_id}"` tells OpenWebUI to route user messages
through the pipe function. The pipe function handles SSE streaming, HMAC auth, etc. — no change needed there.

### Access control semantics in OpenWebUI

- No access_grants on a model = public (visible to all) — this is the CURRENT state for pipe models
- Empty access_grants = private (owner-only)
- Explicit group grants = visible only to those groups
- `BYPASS_MODEL_ACCESS_CONTROL=False` enforces this (currently not set → defaults to True)

### Group naming convention

`aihub:{tenant_name}:{role_name}` — e.g., `aihub:Default Organization:AIHubUser`

- The `aihub:` prefix lets the provisioner identify managed groups
- Human-readable in OpenWebUI admin panel

## Cross-Scope Impact

- `aihub_lib` changes are new files only — no existing code modified
- `aihub_api` changes are additive (new constructor param, new method call)
- Docker-compose changes add env vars only

## ADR Needed?

**Yes** — this introduces a new architectural pattern (AI-Hub managing OpenWebUI's internal state via its API). Create
`aihub_doc/arc42/decisions/2026_03_05_aihub_manages_openwebui_model_visibility.md`.

## Verification

1. Start docker-compose dev stack
2. Log in as a user with limited role (e.g., only access to AgentA)
3. Open OpenWebUI in the iframe
4. Verify: only AgentA workspace model visible, other agents hidden
5. Switch to a role with broader access → verify more agents become visible
6. Test: clicking an agent routes through the pipe function correctly (SSE streaming works)
7. Run `make test` in aihub_lib and aihub_api
