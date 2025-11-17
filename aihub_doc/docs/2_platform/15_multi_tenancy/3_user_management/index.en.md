---
title: Managing users and roles
---

# Managing users and roles

Users access the platform through your identity provider (Azure AD, Google Workspace, Okta, etc.), but their roles and
tenant memberships are managed within the platform itself.

## User lifecycle

### First login

::: info Authentication vs Authorization
When someone logs in for the first time:

1. Your identity provider verifies who they are
2. The platform creates their user profile (name, email, profile picture)
3. They automatically join the default tenant with standard user roles
4. They see the default tenant's agents and resources

**Important**: The platform doesn't import roles from your identity provider. It only imports identity information (who
you are, not what you can do).
:::

### Adding to additional tenants

After someone's first login, administrators can add them to other tenants. Navigate to **Service** → **Tenants**, select
a tenant, and click **Add User** on the Users tab.

Search for the user by name or email. Select which roles to assign in this tenant. The user can now switch to this
tenant and will have the permissions defined by those roles.

Users don't need to log out and back in. Changes take effect on their next request.

### Removing from tenants

Click **Remove** next to a user in the tenant's user list. This removes their membership entirely - they lose all roles
in that tenant and cannot select it anymore.

Removing someone from the default tenant is unusual but allowed. Users removed from all tenants cannot access any
platform resources.

## Roles

Roles are collections of permissions scoped to a specific tenant. The "Manager" role in the Finance tenant is completely
separate from a "Manager" role in the HR tenant.

### Creating roles

Navigate to a tenant's **Roles** tab and click **Create Role**.

Choose a descriptive name: "Agent User", "Document Reviewer", "Department Admin". The name should explain what the role
allows.

Define what this role permits. For a department user role:

- Access to department agents
- Access to department processes
- Cannot see administrative services
- Cannot see other departments' resources

For a department admin role:

- Everything department users can do
- Create agent instances
- Manage knowledge ingestion
- Add users to the department tenant
- Assign roles to department users

### Role scope within tenant boundaries

Roles grant permissions up to the tenant's boundary. If the tenant can only access Finance agents, a role in that tenant
cannot grant access to HR agents even if configured to do so.

The tenant defines what exists. Roles define what users with that role can do within what exists.

### Changing roles

Select a role and click **Edit**. Changes affect all users with that role immediately.

Adding permissions to a role grants those permissions to everyone who has it. Removing permissions revokes them from
everyone with that role.

Test role changes carefully, preferably in a test tenant first.

## Managing user roles

Click **Manage Roles** next to a user in the tenant's user list.

Add roles by selecting from available roles in that tenant. Remove roles by deselecting them.

Users can have multiple roles in the same tenant. Their effective permissions are the union of all their roles. If one
role grants access to agents and another grants access to processes, they can access both.

A user with no roles in a tenant is technically allowed but serves no purpose.

## Bulk operations

### CSV import

::: details CSV Import Format
Import many users at once through **Service** → **Users** → **Import Users**.

Create a CSV file with three columns:

- email
- name
- initial_roles (comma-separated role names)

Example:

```csv
email,name,initial_roles
john.doe@company.com,John Doe,"StandardUser,AgentUser"
jane.smith@company.com,Jane Smith,StandardUser
```

The import:

- Creates user profiles if they don't exist yet
- Adds users to your current tenant (determined by which tenant you're in)
- Assigns the specified roles

Users who haven't logged in yet receive placeholder profiles that update when they first authenticate.
:::

### Bulk role assignment

Select multiple users using checkboxes in the user list. Choose **Bulk Actions** → **Assign Roles**.

Three modes:

- **Add**: Add selected roles to users' existing roles
- **Remove**: Remove selected roles, keeping others
- **Replace**: Replace all roles with selected roles

Changes apply immediately to all selected users.

## Cross-tenant membership

Users often belong to multiple tenants with different roles in each.

Someone might be:

- Admin in Development tenant (can deploy and configure freely)
- Standard user in Staging tenant (can test but not modify)
- Viewer in Production tenant (read-only access)

They switch between tenants using the selector in the top bar. The interface shows only what's available in the selected
tenant. Their permissions change based on their roles in that tenant.

## Permissions inheritance

Permissions don't inherit between tenants. Being an admin in one tenant grants no privileges in another tenant.

Permissions don't inherit within role hierarchies. Having user access doesn't automatically grant admin access.

## Common role structures

### Department tenant

**Standard User**: Chat with department agents, participate in processes, view results

**Power User**: Standard user abilities plus create agent instances, configure agents, run evaluations

**Department Admin**: Power user abilities plus manage users, assign roles, create department-specific roles

### Management tenant

**Tenant Manager**: Create new tenants, configure tenant boundaries, assign agents to tenants

**User Administrator**: Add users to tenants, assign roles, manage user access across all tenants

**Platform Administrator**: Full administrative access to all services and configurations

### Development tenant

**Developer**: Deploy agents, create pipelines, modify configurations, full service access for testing

**QA**: Create test agent instances, run evaluations, view all agents, cannot deploy code

**Observer**: Read-only access to all resources for learning and documentation

## Best practices

::: tip User Management Best Practices
**Principle of least privilege**: Grant users the minimum permissions needed for their work. You can always expand
access later.

**Regular audits**: Review user roles quarterly. People change positions. Access granted for a project might not be
appropriate six months later.

**Clear role names**: "Finance Standard User" is clearer than "FSU". Future administrators will thank you.

**Test before rolling out**: Create a test user, add them to a tenant with a new role, and verify they see exactly what
you intend.

**Document role purposes**: When creating a role, document why it exists and what its responsibilities are. This
prevents confusion when reviewing access later.

**Limit admin roles**: Admin users can grant themselves any permission within their tenant. Only trusted personnel
should have admin roles.
:::

## Troubleshooting access issues

When a user reports they can't access something:

1. Verify they selected the correct tenant (check the tenant selector in the top bar)
2. Check if their tenant has access to that resource
3. Verify they have roles assigned in that tenant
4. Review what those roles permit

The most common issue is users working in the wrong tenant. The second most common is the tenant boundary preventing
access even though the role would permit it.
