---
title: Creating and configuring tenants
index: 2
---

# Creating and configuring tenants

Tenant administrators create and configure tenants through the admin UI. Each tenant requires a name, description, and access rules that define its boundaries.

## Creating a tenant

Navigate to **Service** → **Tenants** in the admin interface. The tenant list shows existing tenants with their user and role counts.

Click **Create Tenant** to open the configuration dialog.

**Name**: A unique identifier for the tenant. Use clear names that reflect the organization or purpose: "Finance Department", "Customer Demo", "Development Environment".

**Description**: Explain the tenant's purpose. This appears in the tenant selector and helps users understand what each tenant is for.

**Access rules**: Define what resources exist within this tenant's scope. Add one or more access rule patterns.

### Access rule patterns

Access rules use the hierarchical pattern: `aihub.[user|admin].<service>.<resource>.<identifier>`

Common patterns:

```
aihub.admin.>
```
Full platform access. No restrictions. Suitable for administrative tenants or the default tenant.

```
aihub.user.agent.>
aihub.user.process.>
aihub.user.knowledge.>
```
Access to all agents, processes, and knowledge bases, but no admin functions. Suitable for general business units.

```
aihub.user.agent.customer-service.*
aihub.user.knowledge.customer-docs.>
```
Access only to customer service agents and customer documentation. Suitable for customer support teams or customer-specific tenants.

```
aihub.user.agent.research.instance-alpha
```
Access to a single specific agent instance. Suitable for tightly controlled demo or test environments.

### Combining rules

A tenant can have multiple access rules. The platform grants access if any rule matches:

```
aihub.user.agent.research.*
aihub.user.agent.analysis.*
aihub.user.knowledge.research-docs.>
```

This tenant can access all research and analysis agents plus the research-docs knowledge base.

::: tip
Start with broader rules and narrow them if needed. It's easier to restrict access later than to discover users can't reach resources they need.
:::

## Editing tenants

Select a tenant from the list and click **Edit**. You can change the name, description, or access rules.

Changing access rules affects all users in the tenant immediately. Users may lose access to resources if you remove rules they depend on.

The system prevents deleting the default tenant. All other tenants can be edited freely.

## Access rule validation

The platform validates access rules when creating or editing tenants. Rules must:

- Start with `aihub.user.` or `aihub.admin.`
- Use only lowercase letters, numbers, dots, hyphens, and underscores
- Use wildcards (`*` and `>`) correctly
- Place the multi-level wildcard `>` only at the end

Invalid rules trigger an error message with the specific problem.

## Viewing tenant details

Click a tenant name to view its details page. Two tabs organize the information:

**Users tab** lists all users in the tenant with their assigned roles. From here you can:
- Add users to the tenant
- Change user roles
- Remove users from the tenant

**Roles tab** lists all roles defined for this tenant. From here you can:
- Create tenant-specific roles
- Edit role permissions
- Delete roles (except system roles)

Statistics at the top show the total user and role counts.

## Deleting tenants

Click **Delete** on a tenant row. The system prevents deletion if:

- The tenant is the default tenant
- The tenant still has users

Remove all users first, then delete the tenant. Deletion cascades to remove all tenant-specific roles.

::: danger
Deleting a tenant is permanent. All roles defined for that tenant are removed. Users lose their membership in that tenant.
:::

## Configuration via environment variables

Control default tenant behavior through environment variables in `.env`:

```bash
# Default tenant configuration
DEFAULT_TENANT_NAME="Default Organization"
DEFAULT_TENANT_ACCESS_RULES="aihub.admin.>"

# New user signup defaults
USER_SIGNUP_DEFAULT_TENANT="default"
USER_SIGNUP_DEFAULT_ROLES="AIHubUser,AIHubAgentUser"
FIRST_USER_SIGNUP_DEFAULT_ROLES="AIHubAdmin"
```

**DEFAULT_TENANT_NAME**: Name for the automatically created default tenant

**DEFAULT_TENANT_ACCESS_RULES**: Access rules for the default tenant, comma-separated. Default is `aihub.admin.>` (unrestricted)

**USER_SIGNUP_DEFAULT_TENANT**: Which tenant new users join automatically. Use the tenant name, not ID

**USER_SIGNUP_DEFAULT_ROLES**: Roles assigned to new users in the default tenant, comma-separated

**FIRST_USER_SIGNUP_DEFAULT_ROLES**: Roles assigned to the very first user, comma-separated

These settings apply only when users first authenticate. Changing them doesn't affect existing users.

## Best practices

**Start broad**: Create tenants with unrestricted access (`aihub.admin.>`) initially. Narrow the rules once you understand which resources each tenant needs.

**Document tenant purpose**: Use clear descriptions. When users see multiple tenants in the selector, they should immediately understand which to choose.

**Test access rules**: Create a test user account and verify they can access the intended resources before rolling out a new tenant to the organization.

**Plan for growth**: Consider whether you might need finer-grained tenants later. "Customer Tenant A" is clearer than "Customer 1" when you have dozens of customers.

**Monitor unused tenants**: Periodically review tenants with zero users. These might be old test environments that can be deleted.
