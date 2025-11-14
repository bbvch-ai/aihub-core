# Tenant Management API Endpoints

**Blocked by:**
- #01 (Multi-Tenant Database Schema)
- #02 (Tenant-Aware Authorization)

## Description

We currently have no API endpoints for managing tenants. Tenants are only created during database initialization. Administrators need the ability to create, list, view, update, and delete tenants through the API.

Tenants are the top-level organizational unit in our multi-tenant system. Each tenant has:
- A unique name and description
- A set of access rules that define the maximum scope for all users in that tenant
- Associated users and roles

## Required Endpoints

Create a new `TenantController` following the same pattern as the existing `RoleController`:
- Create tenant (with access rules validation)
- List all tenants
- Get specific tenant details (including stats like user count, role count)
- Update tenant properties and access rules
- Delete tenant (with safeguards)

## Important Constraints

- Access rules must be validated using `AccessChecker.validate_user_access_rule()`
- The default tenant cannot be deleted
- Cannot delete a tenant that still has users (must remove users first)
- Deleting a tenant should cascade to delete the tenant's roles
- Only users with `aihub.admin.service.tenant` permission should access these endpoints

## Current Reference Code

- Role management pattern: `aihub_api/aihub_api/routes/role/RoleController.py` and `RoleService.py`
- User management pattern: `aihub_api/aihub_api/routes/user/UserController.py` and `UserService.py`
- Controller mounting: `aihub_api/app/main.py`

## Additional Endpoint

Users should be able to query their current tenant context. Consider an endpoint like `GET /tenants/me` that returns the tenant corresponding to the `X-Tenant-Id` header.

## Definition of Done

This task is accepted when:

- [ ] Full CRUD API exists for tenants
- [ ] Access rules are validated on create/update
- [ ] Default tenant cannot be deleted (validation enforced)
- [ ] Tenants with users cannot be deleted (validation enforced)
- [ ] Deleting tenant removes associated tenant-scoped roles
- [ ] Tenant details endpoint returns useful statistics (user count, role count)
- [ ] Users can query their current tenant via the API
- [ ] All endpoints require appropriate admin permissions
- [ ] OpenAPI documentation is generated correctly
- [ ] Controller is mounted in main application

## Hints

- Follow the service-controller pattern used throughout the codebase
- Consider what DTOs are needed (CreateTenantRequest, TenantResponse, etc.)
- Think about pagination for listing tenants if the list could grow large
