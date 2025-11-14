---
title: User and role management
index: 3
---

# User and role management

Managing users in a multi-tenant environment involves assigning users to tenants and granting them appropriate roles within each tenant.

## Adding users to tenants

Users must be members of a tenant before they can access resources in that tenant. New users join the default tenant automatically during their first login. Add them to additional tenants manually.

Navigate to **Service** → **Tenants** and select the tenant. Switch to the **Users** tab.

Click **Add User**. Search for the user by name or email, then select which roles to assign in this tenant. Users must have at least one role to be useful members of the tenant.

The user can now select this tenant from their tenant switcher and access resources according to their assigned roles and the tenant's access rules.

## Removing users from tenants

From the tenant's **Users** tab, find the user and click **Remove**. This removes their membership entirely - they lose all roles in that tenant and can no longer select it.

Removing a user from the default tenant is allowed but unusual. Users removed from all tenants cannot access any platform resources.

## Managing user roles

Click **Manage Roles** next to a user in the tenant's user list. This shows their current roles in that tenant.

Add or remove roles using the role selector. Changes take effect immediately. The user doesn't need to log out and back in.

A user with no roles in a tenant serves no purpose. The system allows this state but it's generally unintentional.

## Creating tenant roles

Roles are scoped to specific tenants. The "Analyst" role in Finance tenant is separate from "Analyst" in Marketing tenant.

Navigate to the tenant's **Roles** tab and click **Create Role**.

**Name**: Choose a descriptive name. "Agent User", "Document Reviewer", "Department Admin" explain what the role does.

**Description**: Document the role's purpose and intended users. This helps when assigning roles later.

**Access rules**: Define what this role permits. Add multiple rules to grant access to different resources.

Example analyst role:
```
aihub.user.agent.>
aihub.user.knowledge.>
aihub.user.process.review-workflow.*
```

This role can use all agents and knowledge bases, and participate in review workflow processes.

## Editing roles

Select a role and click **Edit**. You can change the name, description, or access rules.

Role changes affect all users with that role immediately. Adding access rules grants new permissions to everyone with the role. Removing access rules revokes those permissions.

::: warning
Test role changes carefully. Removing an access rule might prevent users from completing work in progress.
:::

## Deleting roles

Click **Delete** on a role. The system removes the role from all users in the tenant.

System roles (created during initialization) cannot be deleted. These include roles like AIHubUser, AIHubAdmin, and AIHubSuperuser.

## Bulk user import

Import many users at once using CSV upload. Navigate to **Service** → **Users** and click **Import Users**.

The CSV requires three columns:
- `email` - User's email address (required)
- `name` - Display name (required)
- `initial_roles` - Comma-separated role names (optional)

Example CSV:
```csv
email,name,initial_roles
john.doe@company.com,John Doe,"AIHubUser,AIHubAgentUser"
jane.smith@company.com,Jane Smith,AIHubUser
admin@company.com,Admin User,AIHubAdmin
```

The import process:
1. Validates the CSV format
2. Shows a preview of users to import
3. Creates user accounts if they don't exist
4. Adds users to the current tenant (determined by X-Tenant-Id header)
5. Assigns the specified roles

Users who haven't logged in yet receive placeholder profiles. Their name and email update when they first authenticate through the identity provider.

The results summary shows how many users were created, updated, or failed with error details for failures.

## Bulk role assignment

Assign the same roles to multiple users at once. Navigate to **Service** → **Users**, select users using checkboxes, then choose **Bulk Actions** → **Assign Roles**.

Three modes:

**Add roles**: Adds the selected roles to each user's existing roles. Users keep their current roles and gain the new ones.

**Remove roles**: Removes the selected roles from each user. Users keep any roles not in the removal list.

**Replace roles**: Replaces all roles with the selected ones. Users lose their current roles and receive only the specified roles.

Select the desired roles and apply. Changes take effect immediately for all selected users.

::: tip
Use bulk assignment when onboarding teams or reorganizing departments. It's faster than assigning roles individually.
:::

## User role inheritance

Users don't inherit roles between tenants. A user who is an admin in one tenant has no privileges in another tenant unless explicitly granted.

When a user switches tenants, the system resolves their roles within the new tenant context. Their permissions change based on their roles in the selected tenant.

## Viewing user details

Navigate to **Service** → **Users** and click a username. This shows:

- Basic profile (name, email, profile picture)
- All tenants the user belongs to
- Roles in each tenant
- Last access timestamp

From here you can manage the user's memberships and roles across all tenants.

## Common role patterns

**Viewer**: Read-only access to specific resources
```
aihub.user.agent.specific-agent.*
aihub.user.knowledge.department-docs.>
```

**Contributor**: Can use agents and processes but not administer them
```
aihub.user.agent.>
aihub.user.process.>
aihub.user.knowledge.>
```

**Department admin**: Full control within department resources
```
aihub.admin.agent.department-*
aihub.admin.knowledge.department-docs.>
aihub.admin.process.department-*
```

**Tenant admin**: Full control within the tenant
```
aihub.admin.>
```

Avoid granting `aihub.admin.>` in tenant roles unless you want users to have full administrative control. This includes user management, role changes, and system configuration.

## Security considerations

**Principle of least privilege**: Grant users the minimum permissions needed for their work. Start restrictive and expand if they need more access.

**Regular audits**: Periodically review user roles. People change positions and responsibilities. Remove unneeded permissions.

**Role consolidation**: If many users need the same permissions, create a role instead of granting individual access rules.

**Admin role limits**: Restrict who has admin roles. Admin users can grant themselves any permission within the tenant, so admin access should be limited to trusted personnel.

**External user management**: For customer-facing tenants, consider whether to allow users to invite others or require admin-only user management.
