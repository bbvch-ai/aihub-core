# AI-Hub Manages OpenWebUI Model Visibility

**Date:** 2026-03-05

## Context

OpenWebUI shows ALL online agents to ALL users because its `pipes()` discovery method is called without user context
(OpenWebUI architecture limitation). Users see agents they cannot use, get 403 errors, and agent metadata is exposed to
unauthorized users.

The root cause: `AgentDiscoveryService.discover_agents()` calls `GET /api/v1/agents/instances` with a superuser token,
bypassing per-user permission filtering. The `pipes()` method cannot receive user context.

## Decision Drivers

- OpenWebUI's pipe discovery architecture cannot be extended with per-user filtering
- AI-Hub already has a mature permission system (AccessChecker with tenant/role hierarchies)
- OpenWebUI supports workspace models with group-based access control via its REST API
- OpenWebUI exposes a SCIM 2.0 API for group and user management
- The solution must not require OpenWebUI code changes

## Decision

AI-Hub manages OpenWebUI's internal state (groups, workspace models, access grants) via the OpenWebUI REST API,
following the same provisioner pattern used for Langfuse (`LangfuseProvisioner`).

### How it works

1. **Groups** (via SCIM 2.0): AI-Hub creates OpenWebUI groups for each tenant-role combination
   (`aihub:{tenant}:{role}`). Memberships are synced via email-based user ID mapping, scoped to each user's active
   tenant — users only appear in groups matching their currently active tenant.
2. **Workspace models** (via JWT-authenticated REST API): For each online agent, AI-Hub creates a workspace model that
   delegates to the pipe function (`base_model_id = "aihub-pipeline.{agent_class}.{agent_id}"`).
3. **Access grants**: For each workspace model, AI-Hub computes which groups have access using `AccessChecker` with
   tenant ceiling enforcement, then sets `access_control` on the model.

The provisioner runs on six triggers — all changes propagate immediately:

- **Startup** (`provision()`): full sync of groups, workspace models, and access grants
- **Agent discovery cycle** (`sync_agents()`): the periodic reconciler — when the set of online agent instances changes
  (checked every 60 seconds), syncs workspace models and access grants
- **Agent config changes** (`sync_known_agents()`): when an agent instance is created, renamed, or deleted, syncs
  workspace models and access grants immediately (via `AgentConfigChangeHook` MongoEngine signals on
  `AgentConfigEntityDocument`) instead of waiting for the next discovery cycle
- **Tenant switch** (`sync_access()`): when a user changes active tenant (via `AuthHandler` hook)
- **OpenWebUI signup webhook** (`sync_access()`): when a new user signs up (via `WebhookController`)
- **Access entity changes** (`sync_access()`): when roles, tenants, or user-role assignments are created, updated, or
  deleted (via `AccessChangeHook` MongoEngine signals)

### Key design choices

- **Server-side push** over client-side filtering: AI-Hub pushes permissions to OpenWebUI rather than filtering in the
  pipe. This works within OpenWebUI's architecture without modifications.
- **SCIM 2.0 for identity**: Groups and users are managed via the standard SCIM API, workspace models via JWT-
  authenticated proprietary endpoints.
- **Active tenant scoping**: Users only belong to groups matching their active tenant, not all tenants they have roles
  in. This prevents cross-tenant visibility leakage.
- **`AccessChangeHook` pattern**: MongoEngine `post_save`/`post_delete` signals on RoleEntity, TenantMetadataEntity, and
  UserTenantRoleEntity automatically trigger `sync_access()`. Signals are connected by the API lifetime manager, so
  they're only active in production — not during unit tests. No manual notification calls in entity code. Rapid
  mutations are debounced with a 2-second quiet window so bulk operations (e.g. assigning 50 users) collapse into a
  single sync call.
- **`AgentConfigChangeHook` pattern**: the workspace-model analogue of `AccessChangeHook`. `post_save`/`post_delete`
  signals on `AgentConfigEntityDocument` trigger `sync_known_agents()` (same debounce, lock, and lifetime-manager
  wiring). The discovery cycle remains the periodic backstop that reconciles drift.
- **Distributed locking**: Each sync method (`provision`, `sync_agents`, `sync_access`) acquires a non-blocking Redis
  lock before executing. Concurrent calls across API replicas skip gracefully instead of racing. Locks use separate keys
  per sync type so agent sync and access sync don't block each other.
- **Redis-backed agent change detection**: The discovery service stores a SHA-256 hash of the online agent set in Redis
  (with 1-hour TTL) instead of an in-memory set. This survives API restarts and works correctly across replicas.
- **Group naming convention**: `aihub:` prefix identifies managed groups, preventing interference with manually-created
  groups.
- **Model ID convention**: `aihub-agent-` prefix identifies managed workspace models.
- **`BYPASS_MODEL_ACCESS_CONTROL=False`**: Must be set on OpenWebUI to enforce access control.

## Consequences

### Positive

- Users only see agents they have permission to use
- No OpenWebUI code changes required
- Follows existing provisioner pattern (consistent with Langfuse integration)
- Tenant ceiling enforcement preserved (tenant rules act as upper bound)
- Idempotent syncing with change detection (Redis-backed hash comparison)
- All access changes propagate immediately (no stale visibility windows)
- Distributed locking prevents race conditions across API replicas
- Debouncing collapses bulk admin operations into single sync calls

### Negative

- Adds dependency on OpenWebUI SCIM token and JWT secret key configuration (`OPENWEBUI_SCIM_TOKEN`,
  `OPENWEBUI_SECRET_KEY`)
- Email-based user mapping requires users to have logged into both systems

### Risks

- OpenWebUI SCIM or model API changes in future versions may require provisioner updates
- High number of tenant-role combinations creates many groups (scales as tenants x roles)
- High-frequency admin operations are mitigated by debouncing but the 2-second quiet window adds latency to visibility
  updates during bulk changes
