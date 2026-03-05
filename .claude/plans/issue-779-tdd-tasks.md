# Plan: Filter OpenWebUI Agent Visibility (Issue #779) — TDD Task Breakdown

## Context

OpenWebUI shows ALL online agents to ALL users. The `pipes()` method has no user context (OpenWebUI limitation).
Solution: AI-Hub computes permissions server-side and pushes **workspace models + groups + access grants** to OpenWebUI
via its REST API. See `issue-779-implementation-plan.md` for full architectural rationale.

## Key Reference Files

- Pattern to follow: `aihub_lib/aihub_lib/infrastructure/langfuse/LangfuseProvisioner.py`
- Settings pattern: `aihub_lib/aihub_lib/infrastructure/langfuse/LangfuseSettings.py`
- Test pattern: `aihub_lib/tests/test_langfuse_provisioner.py`
- Permission engine: `aihub_lib/aihub_lib/auth/access/AccessChecker.py` (constructor takes
  `user_access_rules: list[str], tenant_access_rules: list[str]` directly — no DB needed)
- Entities: `TenantEntity`, `RoleEntity`, `UserTenantRoleEntity`, `UserEntity`
- Integration: `aihub_api/aihub_api/services/AgentEndpointsDiscoveryService.py`
- Startup: `aihub_api/aihub_api/runners/lifetime/lifetime_manager.py`

## Mocking Strategy

Follow `test_langfuse_provisioner.py` exactly:

- `MagicMock` for settings objects
- `AsyncMock(spec=httpx.AsyncClient)` for HTTP client
- `httpx.Response(status_code=..., json=...)` for responses
- `patch.object()` for method-level patching
- `pytest.mark.asyncio` + class-grouped tests
- Mock `TenantEntity`, `RoleEntity`, `UserTenantRoleEntity`, `UserEntity` classmethods with `patch`

______________________________________________________________________

## Task 1: OpenWebuiSettings

**Files to create:**

- `aihub_lib/aihub_lib/infrastructure/openwebui/__init__.py`
- `aihub_lib/aihub_lib/infrastructure/openwebui/OpenWebuiSettings.py`

**Implementation:**

```python
class OpenWebuiSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("OPENWEBUI_")
    BASE_URL: Annotated[str, Field(description="OpenWebUI server base URL")]
    API_KEY: Annotated[SecretStr, Field(description="OpenWebUI admin API key")]
```

**Test file:** `aihub_lib/tests/test_openwebui_settings.py`

**Tests:**

| #   | Test                                           | What it verifies                                                         |
| --- | ---------------------------------------------- | ------------------------------------------------------------------------ |
| 1   | `test_settings_load_from_env`                  | Settings load from `OPENWEBUI_BASE_URL` and `OPENWEBUI_API_KEY` env vars |
| 2   | `test_settings_missing_required_fields_raises` | `ValidationError` when required fields missing                           |
| 3   | `test_api_key_is_secret`                       | `API_KEY` is `SecretStr`, not exposed in repr                            |

______________________________________________________________________

## Task 2: OpenWebuiClient

**File to create:** `aihub_lib/aihub_lib/infrastructure/openwebui/OpenWebuiClient.py`

Thin async wrapper. Takes `base_url: str` and `api_key: str` in constructor. Each method takes
`client: httpx.AsyncClient` as first param (caller manages lifecycle, matches LangfuseProvisioner pattern).

**Methods:**

- `list_groups(client)` → `GET /api/v1/groups/`
- `create_group(client, name, description)` → `POST /api/v1/groups/create`
- `delete_group(client, group_id)` → `DELETE /api/v1/groups/id/{id}/delete`
- `update_group_members(client, group_id, user_ids)` → `POST /api/v1/groups/id/{id}/update` (sets full member list)
- `list_models(client)` → `GET /api/v1/models/`
- `create_model(client, model_data)` → `POST /api/v1/models/create`
- `delete_model(client, model_id)` → `DELETE /api/v1/models/delete?id={id}`
- `update_model_access(client, model_id, access_control)` → `POST /api/v1/models/update?id={id}` (update access_control
  field)
- `list_users(client)` → `GET /api/v1/users/`

**Test file:** `aihub_lib/tests/test_openwebui_client.py`

**Tests:**

| #   | Test                                    | What it verifies                                |
| --- | --------------------------------------- | ----------------------------------------------- |
| 1   | `test_list_groups_sends_get_with_auth`  | Correct URL, Bearer token in header             |
| 2   | `test_create_group_sends_post`          | POST with name/description payload              |
| 3   | `test_delete_group_sends_delete`        | DELETE with correct group ID in URL             |
| 4   | `test_update_group_members_sends_post`  | POST with user_ids payload                      |
| 5   | `test_list_models_sends_get`            | Correct URL and auth                            |
| 6   | `test_create_model_sends_post`          | POST with model data                            |
| 7   | `test_delete_model_sends_delete`        | Correct model ID in query param                 |
| 8   | `test_update_model_access_sends_post`   | POST with access_control payload                |
| 9   | `test_list_users_sends_get`             | Correct URL and auth                            |
| 10  | `test_all_methods_include_bearer_token` | Every method sets `Authorization: Bearer {key}` |
| 11  | `test_http_error_propagates`            | `raise_for_status()` on non-2xx responses       |

______________________________________________________________________

## Task 3: OpenWebuiProvisioner — Group Sync

**File to create:** `aihub_lib/aihub_lib/infrastructure/openwebui/OpenWebuiProvisioner.py`

This task implements only the group-related logic:

- `_build_desired_groups()` → pure computation: tenants × roles → set of group names
- `_build_user_id_mapping()` → maps AI-Hub user emails to OpenWebUI user IDs
- `_sync_groups(client)` → orchestrates: fetch existing groups, create/delete diff, sync memberships

**Test file:** `aihub_lib/tests/test_openwebui_provisioner_groups.py`

**Tests — Pure logic (no I/O, no mocking of DB/HTTP):**

| #   | Test                                                  | What it verifies                                  |
| --- | ----------------------------------------------------- | ------------------------------------------------- |
| 1   | `test_build_desired_groups_single_tenant_single_role` | `{"aihub:TenantA:RoleA"}`                         |
| 2   | `test_build_desired_groups_cross_product`             | 2 tenants × 2 roles → 4 groups                    |
| 3   | `test_build_desired_groups_empty_tenants`             | No tenants → empty set                            |
| 4   | `test_build_desired_groups_empty_roles`               | Tenant with no roles → no groups for that tenant  |
| 5   | `test_group_name_format`                              | Group names follow `aihub:{tenant}:{role}` format |

**Tests — User ID mapping (mock DB + mock OpenWebUI users API):**

| #   | Test                                       | What it verifies                                      |
| --- | ------------------------------------------ | ----------------------------------------------------- |
| 6   | `test_user_id_mapping_by_email`            | AI-Hub user email → OpenWebUI user ID via email match |
| 7   | `test_user_id_mapping_skips_unknown_users` | Users not in OpenWebUI are silently skipped           |

**Tests — Group sync orchestration (mock client + mock DB entities):**

| #   | Test                                 | What it verifies                                                               |
| --- | ------------------------------------ | ------------------------------------------------------------------------------ |
| 8   | `test_sync_creates_missing_groups`   | New tenant×role combo → `client.create_group()` called                         |
| 9   | `test_sync_deletes_orphaned_groups`  | Group with `aihub:` prefix not in desired set → `client.delete_group()` called |
| 10  | `test_sync_ignores_non_aihub_groups` | Groups without `aihub:` prefix are never touched                               |
| 11  | `test_sync_updates_group_membership` | Users with role in tenant → added to corresponding group                       |
| 12  | `test_sync_idempotent`               | Running twice produces same result, no duplicate creates                       |

______________________________________________________________________

## Task 4: OpenWebuiProvisioner — Workspace Model Sync

Adds `_sync_workspace_models(client, online_agents)` to the provisioner.

**Key logic:**

- Workspace model ID: `aihub-agent-{agent_class}-{agent_id}`
- `base_model_id`: `aihub-pipeline.{agent_class}.{agent_id}` (pipe model format)
- Create workspace models for newly online agents, delete for offline agents
- Filter existing models by `aihub-agent-` prefix to identify managed models

**Test file:** `aihub_lib/tests/test_openwebui_provisioner_models.py`

**Tests — Pure logic:**

| #   | Test                             | What it verifies                                                  |
| --- | -------------------------------- | ----------------------------------------------------------------- |
| 1   | `test_workspace_model_id_format` | `("rag-agent", "default")` → `"aihub-agent-rag-agent-default"`    |
| 2   | `test_base_model_id_format`      | `("rag-agent", "default")` → `"aihub-pipeline.rag-agent.default"` |
| 3   | `test_compute_models_to_create`  | New agent not in existing models → in create set                  |
| 4   | `test_compute_models_to_delete`  | Existing model not in online agents → in delete set               |
| 5   | `test_compute_models_unchanged`  | Already-existing model for online agent → neither set             |

**Tests — Model sync orchestration (mock client):**

| #   | Test                                              | What it verifies                                          |
| --- | ------------------------------------------------- | --------------------------------------------------------- |
| 6   | `test_sync_creates_workspace_model_for_new_agent` | `client.create_model()` called with correct base_model_id |
| 7   | `test_sync_deletes_model_for_offline_agent`       | `client.delete_model()` called with correct model ID      |
| 8   | `test_sync_preserves_existing_models`             | No create/delete for unchanged agents                     |
| 9   | `test_sync_ignores_non_aihub_models`              | Models without `aihub-agent-` prefix never touched        |

______________________________________________________________________

## Task 5: OpenWebuiProvisioner — Access Grant Computation

Adds `_sync_access_grants(client)` to the provisioner. This is the **core business logic** — determines which groups can
see which workspace models.

**Key logic:**

- For each group `aihub:{tenant}:{role}`, load tenant access rules + role access rules
- Construct `AccessChecker(user_access_rules=role_rules, tenant_access_rules=tenant_rules)`
- For each workspace model (agent), check `checker.has_access_to_agent(agent_class, agent_id)`
- Build access_control dict: `{group_ids: ["read"]}` for groups that have access
- Call `client.update_model_access()` for each model

**Test file:** `aihub_lib/tests/test_openwebui_provisioner_access.py`

**Tests — Pure access computation (no DB, uses AccessChecker directly):**

| #   | Test                                         | What it verifies                                                                       |
| --- | -------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1   | `test_group_with_matching_rules_gets_access` | Tenant+role rules allowing `aihub.user.agent.rag.*` → access granted for `rag/default` |
| 2   | `test_group_without_matching_rules_denied`   | Tenant rules missing agent → access denied                                             |
| 3   | `test_tenant_ceiling_blocks_role_access`     | Role has rule but tenant doesn't → denied (tenant is ceiling)                          |
| 4   | `test_wildcard_rules_grant_broad_access`     | `aihub.user.agent.>` → access to all agents                                            |
| 5   | `test_empty_tenant_rules_deny_all`           | Empty tenant access rules → no agent visible                                           |
| 6   | `test_multiple_groups_different_visibility`  | GroupA sees AgentX only, GroupB sees AgentX+AgentY                                     |

**Tests — Access sync orchestration (mock client + mock DB):**

| #   | Test                                          | What it verifies                                             |
| --- | --------------------------------------------- | ------------------------------------------------------------ |
| 7   | `test_sync_sets_access_grants_on_model`       | `client.update_model_access()` called with correct group IDs |
| 8   | `test_model_with_no_groups_gets_empty_grants` | No group has access → empty access_control (private)         |
| 9   | `test_model_accessible_by_multiple_groups`    | Multiple groups → all included in access_control             |

______________________________________________________________________

## Task 6: OpenWebuiProvisioner — Orchestration

Wires `provision()`, `sync_agents()`, and `sync_access()` as top-level methods. Adds `_run_step()` resilience pattern
(from LangfuseProvisioner).

**Test file:** `aihub_lib/tests/test_openwebui_provisioner_orchestration.py`

**Tests:**

| #   | Test                                           | What it verifies                                                                    |
| --- | ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | `test_provision_calls_all_sync_steps`          | `provision()` calls `_sync_groups`, `_sync_workspace_models`, `_sync_access_grants` |
| 2   | `test_provision_continues_after_step_failure`  | One step fails → remaining steps still execute                                      |
| 3   | `test_sync_agents_calls_model_and_access_sync` | `sync_agents()` calls `_sync_workspace_models` and `_sync_access_grants`            |
| 4   | `test_sync_agents_detects_changes`             | Only calls sync when agent set has changed from last sync                           |
| 5   | `test_sync_agents_skips_on_no_change`          | Same agent set → no sync                                                            |
| 6   | `test_sync_access_calls_group_and_access_sync` | `sync_access()` calls `_sync_groups` and `_sync_access_grants`                      |

______________________________________________________________________

## Task 7: API Integration + Docker Config + ADR

**Files to modify:**

- `aihub_api/aihub_api/services/AgentEndpointsDiscoveryService.py` — add `openwebui_provisioner` param +
  `_sync_agent_instances_to_openwebui()`
- `aihub_api/aihub_api/runners/lifetime/lifetime_manager.py` — instantiate provisioner, pass to discovery, call
  `provision()`
- `deployment/templates/docker-compose.yml.j2` — add env vars
- `.env.dev` — add `OPENWEBUI_BASE_URL` and `OPENWEBUI_API_KEY`

**File to create:**

- `aihub_doc/arc42/decisions/2026_03_05_aihub_manages_openwebui_model_visibility.md`

**No new test file** — these are integration wiring changes. Covered by:

- Existing `AgentEndpointsDiscoveryService` test patterns (if any)
- Manual verification (see Verification section)

**Changes:**

1. `AgentEndpointsDiscoveryService.__init__()`: Add `openwebui_provisioner: OpenWebuiProvisioner | None = None`
2. Add `_sync_agent_instances_to_openwebui()` method (same pattern as `_sync_agent_instances_to_langfuse()`)
3. Call it at end of `_discover_and_register()`
4. `lifetime_manager.py`: Instantiate `OpenWebuiProvisioner()`, pass to discovery service, call `provision()` after DB
   init
5. Docker-compose: `OPENWEBUI_BASE_URL`, `OPENWEBUI_API_KEY`, `BYPASS_MODEL_ACCESS_CONTROL: "False"`
6. ADR documenting the pattern

______________________________________________________________________

## Execution Order

```
Task 1 (Settings) → Task 2 (Client) → Task 3 (Groups) → Task 4 (Models) → Task 5 (Access) → Task 6 (Orchestration) → Task 7 (Integration)
```

Each task is independently testable. Tasks 3-5 build on the provisioner file incrementally. After each task, `make test`
should pass.

## Verification (after all tasks)

1. `make test` in `aihub_lib` — all new tests pass
2. Start docker-compose dev stack
3. Log in as user with limited role → only permitted agents visible in OpenWebUI
4. Log in as admin → all agents visible
5. Take agent offline → workspace model disappears within 60s
6. Click workspace model → SSE streaming works (pipe delegation)
