# Tenant-Scoped Role Management

**Blocked by:**
- #01 (Multi-Tenant Database Schema)
- #03 (Tenant Management API)

## Description

The existing `RoleController` manages global roles without any tenant filtering. All role queries are performed without tenant context, and role names are globally unique.

In the multi-tenant model, roles must be scoped to tenants:
- Each tenant has its own set of roles
- Role names only need to be unique within a tenant (can reuse names across tenants)
- System roles (tenant_id = null) exist for special cases like superuser

The role management API needs to be updated to:
- Accept tenant context from `X-Tenant-Id` header
- Create roles within the current tenant
- List only roles belonging to the current tenant
- Prevent modification/deletion of roles from other tenants
- Prevent deletion of system roles

## Key Considerations

When listing roles, a user should only see roles from their current tenant. When creating a role, it should automatically be associated with the current tenant. When updating or deleting, verify the role belongs to the current tenant.

Deleting a role should remove it from all user-tenant-role assignments in that tenant.

## Current Code Locations

- Role controller: `aihub_api/aihub_api/routes/role/RoleController.py`
- Role service: `aihub_api/aihub_api/routes/role/RoleService.py`
- Role entity: `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py`

## System Roles

System roles (like `AIHubSuperuser`) have `tenant_id = null` and `is_system_role = True`. These should not be deletable and should only be accessible to superusers.

## Definition of Done

This task is accepted when:

- [ ] All role endpoints extract tenant context from authenticated user
- [ ] Creating a role associates it with the current tenant
- [ ] Listing roles filters by current tenant
- [ ] Updating/deleting roles validates they belong to current tenant
- [ ] System roles cannot be deleted
- [ ] Deleting a role removes it from user-tenant-role associations
- [ ] Role name uniqueness is enforced within tenant scope (not globally)
- [ ] Existing role management UI continues to work (scoped to current tenant)

## Hints

- The controller's `user_with_permission()` already provides `UserIdentity` with `tenant_id`
- Think about how to handle the existing role initialization for the default tenant
- Consider adding tenant_id as a parameter to all service methods
