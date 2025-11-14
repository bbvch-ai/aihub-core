# Tenant-Aware Authorization with X-Tenant-Id Header

**Blocked by:** #01 (Multi-Tenant Database Schema)

## Description

Our `AccessChecker` currently resolves user roles globally via `RoleEntity.get_access_rules_for_roles(user.roles)`, with no concept of tenant context. Controllers receive authenticated `UserIdentity` objects but have no way to know which tenant the user is operating within.

With the multi-tenant infrastructure in place, we need authorization to become tenant-aware. The frontend will send an `X-Tenant-Id` header with every request to indicate which tenant context the user is operating in. The backend must:
1. Extract this tenant context during authentication
2. Resolve the user's roles WITHIN that specific tenant
3. Apply both the user's role-based permissions AND the tenant's maximum access rules
4. Deny access if the user isn't a member of the requested tenant

## Tenant-Level Access Rules

This introduces a two-layer permission model:
- **User permissions** (from roles assigned to user in tenant): What the user can do
- **Tenant permissions** (from tenant's access rules): What the tenant allows at all

Example: A user might have the "AllAgents" role granting `aihub.user.agent.>`, but if the tenant itself only has `aihub.user.agent.specific-agent.*` in its access rules, the user can only access `specific-agent` despite their broader role permissions.

## Key Components to Modify

- `UserIdentity` model needs tenant context
- Auth handlers need to extract `X-Tenant-Id` header
- `AccessChecker.from_user()` needs to query `UserTenantRoleEntity` instead of `UserEntity.roles`
- `AccessChecker` permission matching needs to enforce tenant-level restrictions
- Controllers should validate tenant context is present

## Current Code Locations

- User identity model: `aihub_lib/aihub_lib/auth/identity/UserIdentity.py`
- Auth handlers: `aihub_lib/aihub_lib/auth/dependencies/` (OAuth2, Token, Superuser, OpenWebUI)
- Access checker: `aihub_lib/aihub_lib/auth/access/AccessChecker.py`
- Controller authorization: `aihub_lib/aihub_lib/routes/Controller.py` (`user_with_permission()` method)

## Header Extraction Pattern

Look at how `OpenWebuiAuthHandler` extracts custom headers (`X-OpenWebUI-User-Name`, etc.) for reference.

## Edge Cases

- Superuser should be able to operate without tenant context (global access)
- Missing `X-Tenant-Id` should return clear error (400 or auto-default to default tenant - decide on approach)
- User requesting access with invalid tenant ID (not a member) should be 403 Forbidden

## Definition of Done

This task is accepted when:

- [ ] `UserIdentity` carries tenant context from request
- [ ] All auth handlers extract and populate `X-Tenant-Id` header
- [ ] `AccessChecker` resolves roles by querying user-tenant-role associations
- [ ] `AccessChecker` fetches and enforces tenant-level access rules as a permission ceiling
- [ ] Missing tenant context is handled gracefully (error or default)
- [ ] Superuser can bypass tenant checks
- [ ] OpenTelemetry spans include tenant context for observability
- [ ] All existing authorization tests pass with tenant context

## Hints

- Consider whether to require `X-Tenant-Id` for all requests or auto-default to default tenant
- Think about how `AccessChecker.access_level()` should combine user rules and tenant rules
- The tenant access rules act as a filter BEFORE checking user permissions
