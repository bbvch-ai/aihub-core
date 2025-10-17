---
title: Role-Based Access Control (RBAC)
index: 2
---

# Role-Based Access Control (RBAC)

The Swiss AI Hub implements a sophisticated, hierarchical Role-Based Access Control (RBAC) system that provides enterprise-grade security and granular control over every aspect of the AI platform. This security model ensures that users can only access resources and perform operations appropriate to their organizational role.

## Overview

RBAC is a security framework that restricts system access based on user roles within an organization. Rather than assigning permissions directly to individual users, permissions are associated with roles, and users are assigned to roles. This approach significantly simplifies permission management in enterprise environments while maintaining precise control over access rights.

## Core Components

### Roles

Roles are named collections of access rules that define what users can do within the platform. A role represents a set of responsibilities within your organization, such as:

- **Data Scientist**: Access to agents, evaluation tools, and knowledge exploration
- **Business Analyst**: Access to conversation threads and reporting features
- **Administrator**: Full access to user management, system configuration, and all platform resources
- **Content Manager**: Access to knowledge base management and document ingestion pipelines

Roles can be assigned to multiple users, and users can be assigned multiple roles, with their effective permissions being the union of all role permissions.

### Access Rules

Access rules are specific permissions that use a hierarchical dot-notation syntax to define what operations are allowed on which resources. The syntax follows this structure:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Examples:**
- `aihub.user.agent.customer_service.chatbot_v2` - User access to a specific agent instance
- `aihub.admin.service.roles` - Administrative access to role management
- `aihub.user.knowledge.hr_documents.policies` - User access to a specific knowledge namespace
- `aihub.admin.pipeline.data_ingestion` - Administrative access to data ingestion pipelines

### Hierarchical Permission Model

The permission system uses a hierarchical structure that enables both broad and narrow access control. Higher-level permissions implicitly grant access to lower-level resources:

```
aihub.user.agent                          # Access to all agents
├── aihub.user.agent.customer_service     # Access to all customer service agents
│   ├── aihub.user.agent.customer_service.chatbot_v2   # Access to specific instance
│   └── aihub.user.agent.customer_service.chatbot_v3
└── aihub.user.agent.sales                # Access to all sales agents
    ├── aihub.user.agent.sales.lead_qualifier
    └── aihub.user.agent.sales.proposal_generator
```

### Wildcard Support

The system supports sophisticated wildcard patterns for flexible permission management:

- **`*` (Single Segment Wildcard)**: Matches any single path segment
  - `aihub.user.agent.customer_service.*` grants access to all customer service agent instances
  
- **`>` (Deep Wildcard)**: Matches any remaining path segments at any depth
  - `aihub.user.agent.>` grants access to all agents regardless of category or instance
  
- **`?*` (Optional Single Segment)**: Matches zero or one path segment
  - `aihub.user.agent.?*` grants access to agents with or without a category
  
- **`?>` (Optional Deep Wildcard)**: Matches zero or more remaining segments
  - `aihub.user.?>` grants access to all user-level services (commonly used for standard users)

### User Identity Integration

User identities are integrated with enterprise authentication systems, ensuring that RBAC decisions are based on verified organizational identity:

- **Microsoft Entra ID (Azure Active Directory)**: Primary integration for enterprise single sign-on
- **OAuth 2.0 / OIDC**: Standards-based authentication with any OIDC-compliant identity provider
- **Group-Based Role Assignment**: Automatically assigns roles based on directory group memberships
- **Real-Time Sync**: Changes to user roles in the identity provider are reflected immediately in the platform

## Permission Evaluation Process

When a user attempts to access a resource or perform an operation, the platform follows this evaluation process:

1. **Authentication**: Verify the user's identity through the enterprise identity provider
2. **Role Resolution**: Retrieve all roles assigned to the user from the platform's role database
3. **Access Rule Collection**: Gather all access rules associated with the user's roles
4. **Permission Check**: Evaluate whether any of the user's access rules match the required permission
5. **Hierarchical Matching**: Apply wildcard patterns and hierarchical inheritance rules
6. **Authorization Decision**: Grant or deny access based on the evaluation result
7. **Audit Logging**: Record the permission check, including user, resource, and decision for compliance

## User vs. Admin Permissions

The platform distinguishes between two levels of access:

### User-Level Permissions (`aihub.user.*`)

These permissions grant standard access to use platform features and resources:
- Interact with agents and start conversations
- Search and explore knowledge bases
- View their own conversation history
- Execute processes they have permission to use
- Read-only access to resources unless explicitly granted modification rights

### Administrative Permissions (`aihub.admin.*`)

These permissions grant privileged access to manage platform resources:
- Create, modify, and delete agents, pipelines, and processes
- Manage user accounts and role assignments
- Configure system settings and integrations
- Access audit logs and security monitoring
- View all user activity and resource usage across the platform

A user can have both user-level and admin-level permissions for different resources. For example, a user might have:
- `aihub.user.agent.>` (use any agent)
- `aihub.admin.knowledge.department_docs` (manage knowledge base for their department)

## Dynamic Service Visibility

One of the most powerful features of the RBAC system is dynamic service visibility. Rather than showing users disabled features they cannot access, the platform dynamically adjusts the user interface based on permissions:

**Permission-Filtered Navigation**: When users log in, the platform queries their permissions and displays only the services and features they can access. This creates a clean, focused interface tailored to each user's role.

**Context-Aware Controls**: Within a service, the interface shows different controls based on permission level. For example:
- Standard users see read-only views of knowledge bases
- Content managers see upload and delete buttons
- Administrators see configuration and access control settings

**Automatic Updates**: When an administrator changes a user's role assignments, the changes are reflected immediately in the user's interface upon their next action, without requiring logout or manual refresh.

## Service-Specific Permission Patterns

Different platform services implement different permission patterns based on their functional requirements:

### Agent Service
Controls access to AI agents with per-agent granularity:
- `aihub.user.agent.customer_support.cs_001` - Access to a specific agent instance
- `aihub.user.agent.customer_support.*` - Access to all instances of an agent class
- `aihub.admin.agent.customer_support` - Administrative control over the agent class

### Knowledge Service
Implements namespace-based access control for knowledge bases:
- `aihub.user.knowledge.hr_documents` - Access to browse and search the HR documents knowledge base
- `aihub.user.knowledge.hr_documents.policies` - Access to a specific namespace within the knowledge base
- `aihub.admin.knowledge.hr_documents` - Administrative access to manage documents and configuration

### Thread Service
Controls access to conversation threads:
- Users automatically have access to threads they created or participated in
- `aihub.admin.thread` grants administrators visibility into all conversations for support and monitoring

### Pipeline Service
Manages access to data ingestion and processing pipelines:
- `aihub.user.pipeline.document_ingestion` - Permission to trigger a pipeline
- `aihub.admin.pipeline.document_ingestion` - Permission to modify pipeline configuration and view execution logs

### Process Service
Controls access to agentic process automation:
- `aihub.user.process.invoice_processing` - Permission to initiate and monitor a business process
- `aihub.admin.process.invoice_processing` - Permission to modify process definitions and view all executions

## Enterprise Security Benefits

### Compliance and Audit

The RBAC system supports regulatory compliance requirements:

- **Complete Audit Trail**: Every permission check is logged with user identity, resource, timestamp, and decision
- **Separation of Duties**: Different roles can be assigned to ensure no single user has excessive privileges
- **Least Privilege Principle**: Users receive only the minimum permissions necessary for their role
- **Access Reviews**: Administrators can review role assignments and access patterns for compliance reporting

### Scalable Permission Management

The hierarchical permission model enables efficient administration at scale:

- **Role-Based Administration**: Manage permissions through roles rather than individual user grants
- **Group Synchronization**: Automatically assign roles based on directory group memberships
- **Centralized Control**: All permission management occurs through a single role management service
- **Permission Inheritance**: Hierarchical structure reduces the number of explicit permission grants needed

### Multi-Tenant Isolation

For deployments serving multiple organizational units:

- **Tenant-Scoped Resources**: Each tenant's resources are isolated through permission boundaries
- **Cross-Tenant Restrictions**: Users cannot discover or access resources outside their tenant
- **Shared Service Isolation**: Even shared infrastructure components enforce tenant boundaries
- **Data Sovereignty**: Ensures sensitive data remains accessible only to authorized organizational units

## Implementation for Developers

For developers building custom agents, APIs, or services, the platform provides comprehensive RBAC integration capabilities. Complete implementation details are available in the [SDK RBAC Implementation Guide](../../../3_sdk/5_advanced_topics/5_rbac/).

### Controller-Level Protection

Service endpoints automatically enforce permission requirements:

```python
@router.get("/agents/{agent_id}")
@require_permission("aihub.user.agent.{agent_id}")
async def get_agent(agent_id: str, user: UserIdentity):
    # Permission is automatically checked before this code executes
    # The {agent_id} placeholder is dynamically replaced
    return agent_service.get_agent(agent_id)
```

### Dynamic Permission Checks

For runtime permission evaluation:

```python
from aihub_lib.auth import AccessChecker, AccessLevel

async def list_agents(user: UserIdentity, access_checker: AccessChecker):
    all_agents = await agent_service.get_all_agents()
    
    # Filter to only agents the user can access
    accessible_agents = []
    for agent in all_agents:
        access = await access_checker.check_access_level(
            user, f"aihub.user.agent.{agent.id}"
        )
        if access >= AccessLevel.USER:
            accessible_agents.append(agent)
    
    return accessible_agents
```

## Best Practices

### Role Design

- **Role Granularity**: Create roles that align with organizational responsibilities, not individuals
- **Separation of Concerns**: Design roles that separate read access from write access
- **Progressive Access**: Create entry-level, intermediate, and advanced roles for career progression
- **Emergency Access**: Define break-glass administrative roles for incident response

### Permission Assignment

- **Default Deny**: Start with minimal permissions and add access as needed
- **Regular Reviews**: Periodically audit role assignments to ensure they remain appropriate
- **Temporary Grants**: Use time-limited role assignments for short-term access needs
- **Group-Based**: Leverage directory groups for automatic role assignment when possible

### Security Monitoring

- **Failed Access Attempts**: Monitor permission denials for potential security incidents
- **Privilege Escalation**: Alert on changes to administrative role assignments
- **Unusual Patterns**: Detect users accessing resources outside their normal usage patterns
- **Compliance Reporting**: Generate regular reports on role assignments and access patterns

## Conclusion

The Swiss AI Hub's RBAC system provides enterprise-grade access control that is both powerful and manageable. By implementing a hierarchical permission model with dynamic service visibility, the platform ensures users have exactly the access they need while maintaining the security and compliance required for enterprise deployments. The system scales from small teams to large multi-tenant environments while remaining easy to understand and administer.
