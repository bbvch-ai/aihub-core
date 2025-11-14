# User-Tenant-Role Assignment API

**Blocked by:**
- #01 (Multi-Tenant Database Schema)
- #03 (Tenant Management API)
- #04 (Tenant-Scoped Role Management)

## Description

We have no API endpoints for the core tenant membership operations:
- Adding users to tenants
- Removing users from tenants
- Assigning roles to users within a tenant
- Viewing which users belong to which tenants
- Viewing which tenants a user belongs to

Administrators need to manage tenant membership and role assignments through the API. A user can belong to multiple tenants with different roles in each. The current `UserController` only handles user profiles, not tenant membership.

## Required Functionality

Users need to be managed within tenant contexts:
- Add an existing user to a tenant with initial role assignment
- Remove a user from a tenant (deletes their tenant membership)
- View all users in a tenant with their assigned roles
- Update a user's roles within a tenant (add, remove, or replace)
- Allow users to query which tenants they belong to

## Key Considerations

- When adding a user to a tenant, validate the roles belong to that tenant
- When assigning roles, validate all roles exist and belong to the correct tenant
- Removing a user from a tenant removes their access to all tenant resources
- Users should be able to see their own tenant memberships
- Admins should be able to see all users in their tenant

## Current Code Locations

- User controller: `aihub_api/aihub_api/routes/user/UserController.py`
- User service: `aihub_api/aihub_api/routes/user/UserService.py`
- User entity: `aihub_lib/aihub_lib/persistence/user/UserEntity.py`

## Pagination

The user list endpoint should support pagination - look at how existing user listing works in `UserService.get_paginated_users()`.

## Definition of Done

This task is accepted when:

- [ ] API exists to add users to tenants with role assignment
- [ ] API exists to remove users from tenants
- [ ] API exists to view all users in a tenant (paginated)
- [ ] API exists to update user's roles within a tenant
- [ ] API exists for users to query their own tenant memberships
- [ ] All operations validate tenant context and role ownership
- [ ] Removing user from tenant cleans up the association
- [ ] Admin permissions required for management operations
- [ ] Users can query their own memberships without admin rights

## Hints

- Consider creating a separate service class for user-tenant operations
- Think about the response DTOs - should they include full user details or minimal info?
- Look at how the role controller returns role information for reference
