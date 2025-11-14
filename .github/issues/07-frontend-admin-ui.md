# Tenant & User Management Admin UI

**Blocked by:**
- #03 (Tenant Management API)
- #04 (Tenant-Scoped Role Management)
- #05 (User-Tenant-Role Assignment API)
- #06 (Frontend Tenant Selection)

## Description

We have role management UI (`/pages/service/roles.vue`) and user listing (`/pages/service/users.vue`), but no UI for:
- Managing tenants (create, edit, delete)
- Viewing users in a tenant with their roles
- Adding/removing users from tenants
- Assigning/revoking roles for users within tenants

Administrators need a comprehensive interface to manage the multi-tenant system. The UI should follow the existing patterns used in the role and user management pages.

## Required Pages & Features

### Tenant Management Page

- List all tenants in a DataTable (name, description, access rules count, user count, actions)
- Create tenant button (opens modal with form)
- Edit tenant button per row
- Delete tenant button with confirmation
- View tenant details (separate page or expanded row)

### Tenant Details Page

- Show tenant information
- Tab view with:
  - Users in tenant (with their roles)
  - Roles in tenant
- Actions to add users, edit roles, remove users

### Enhanced User Management

- Filter users by current tenant
- Show roles for each user in current tenant
- Manage roles button (opens role assignment modal)
- Manage tenants button (shows which tenants user belongs to)

### Access Rules Editor

- Component for editing access rule lists (add/remove rules)
- Validation of access rule format
- Help text showing valid patterns and examples

## Current Reference Code

- Role management UI: `aihub_web/aihub_web/pages/service/roles.vue`
- User management UI: `aihub_web/aihub_web/pages/service/users.vue`
- Role components: `aihub_web/aihub_web/components/Role/` (Create, Edit, Card)
- Existing composables: `aihub_web/aihub_web/composables/role/`, `composables/user/`

## UI Component Library

Use PrimeVue components (DataTable, Dialog, Button, etc.) and Tailwind CSS. Follow the existing patterns - no custom CSS classes.

## Definition of Done

This task is accepted when:

- [ ] Tenant management page with full CRUD operations
- [ ] Tenant details page showing users and roles
- [ ] User management page enhanced with tenant context
- [ ] Modal for assigning roles to users in tenant
- [ ] Modal for adding users to tenants
- [ ] Access rules editor component with validation
- [ ] All mutations invalidate appropriate cache keys (refetch data)
- [ ] Loading states and error handling throughout
- [ ] Responsive design (mobile-friendly)
- [ ] i18n translations for all new UI text

## Hints

- Create composables for all tenant operations (useTenants, useCreateTenant, etc.)
- Follow the mutation pattern used in role management composables
- Use Pinia Colada's `useQuery` and `useMutation` for state management
- Look at how role editing works for inspiration on role assignment UI
- Consider creating reusable components for common patterns
