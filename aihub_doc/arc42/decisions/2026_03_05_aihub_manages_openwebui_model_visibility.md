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
- The solution must not require OpenWebUI code changes

## Decision

AI-Hub manages OpenWebUI's internal state (groups, workspace models, access grants) via the OpenWebUI REST API,
following the same provisioner pattern used for Langfuse (`LangfuseProvisioner`).

### How it works

1. **Groups**: AI-Hub creates OpenWebUI groups for each tenant-role combination (`aihub:{tenant}:{role}`), with
   memberships synced via email-based user ID mapping
2. **Workspace Models**: For each online agent, AI-Hub creates a workspace model that delegates to the pipe function
   (`base_model_id = "aihub-pipeline.{agent_class}.{agent_id}"`)
3. **Access Grants**: For each workspace model, AI-Hub computes which groups have access using `AccessChecker` with
   tenant ceiling enforcement, then sets `access_control` on the model

The provisioner runs at startup (`provision()`) and on every agent discovery cycle (`sync_agents()`).

### Key design choices

- **Server-side push** over client-side filtering: AI-Hub pushes permissions to OpenWebUI rather than filtering in the
  pipe. This works within OpenWebUI's architecture without modifications.
- **Group naming convention**: `aihub:` prefix identifies managed groups, preventing interference with manually-created
  groups
- **Model ID convention**: `aihub-agent-` prefix identifies managed workspace models
- **`BYPASS_MODEL_ACCESS_CONTROL=False`**: Must be set on OpenWebUI to enforce access control

## Consequences

### Positive

- Users only see agents they have permission to use
- No OpenWebUI code changes required
- Follows existing provisioner pattern (consistent with Langfuse integration)
- Tenant ceiling enforcement preserved (tenant rules act as upper bound)
- Idempotent syncing with change detection

### Negative

- Adds dependency on OpenWebUI admin API key configuration
- Access changes have up to 60-second propagation delay (agent discovery cycle)
- Email-based user mapping requires users to have logged into both systems

### Risks

- OpenWebUI API changes in future versions may require provisioner updates
- High number of tenant-role combinations creates many groups (scales as tenants x roles)
