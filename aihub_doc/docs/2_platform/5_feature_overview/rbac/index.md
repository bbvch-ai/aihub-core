---
title: Role-Based Access Control (RBAC)
index: 2
---

# Role-Based Access Control (RBAC) :shield: :lock:

::: info **Documentation Structure Update**
The RBAC documentation has been reorganized to better serve different audiences. This page provides quick access to the
appropriate documentation for your needs.
:::

## Quick Navigation

### For Platform Users and Administrators

If you're looking to understand how RBAC works from a business and operational perspective, including how to configure
roles, manage permissions, and set up authentication:

::: tip **Platform Documentation**
📖 **[Complete Platform RBAC Guide](../../../1_vision_and_positioning/3_solution/4_security/2_rbac/index.md)**

Covers:

- Role management concepts and business benefits
- Permission system architecture and examples
- User and admin privilege levels
- Authentication and identity provider integration
- Role configuration and best practices
- Security, compliance, and monitoring
- Deployment and getting started guide
:::

### For Developers and SDK Users

If you're implementing RBAC in your custom agents, APIs, or services, and need technical implementation details:

::: tip **SDK Documentation**
🛠️ **[Complete SDK RBAC Implementation Guide](../../../3_sdk/5_advanced_topics/5_rbac/index.md)**

Covers:

- Controller-level access protection
- Dynamic permission resolution
- Service and agent access control implementation
- Advanced permission patterns and wildcards
- Custom validation logic
- Testing RBAC implementations
- Performance optimization and best practices
:::

## Quick Overview

**Role-Based Access Control (RBAC)** is a security framework that restricts system access based on user roles within an
organization. The AI-Hub implements a sophisticated, hierarchical RBAC system that provides granular control over every
aspect of your AI platform.

### Key Benefits

**🛡️ Enterprise Security Compliance**: Meet strict regulatory requirements with comprehensive audit trails and granular
access controls.

**🎯 Granular Resource Control**: Control access to specific AI agents, processes, and services with precision.

**⚡ Scalable Permission Management**: Manage permissions efficiently across large organizations using role-based
hierarchies.

**🔗 Seamless Enterprise Integration**: Native integration with existing enterprise identity systems.

**🧠 Risk-Aware AI Deployment**: Deploy AI capabilities with confidence knowing access is controlled and monitored.

### Core Components

- **Roles**: Named collections of access rules that define what users can do
- **Access Rules**: Specific permissions using dot-notation (e.g., `aihub.admin.service.roles`)
- **User Identity**: Integration with enterprise authentication systems (Azure AD, OAuth2)
- **Permission Templates**: Dynamic permission checking with path parameter substitution
- **Wildcard Support**: Flexible pattern matching using `*`, `>`, `?*`, and `?>` wildcards

### Permission Structure

The system uses a structured permission naming convention:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Examples:**

- `aihub.user.agent.customer_service.chatbot_v2` - User access to specific agent
- `aihub.admin.service.roles` - Admin access to role management
- `aihub.user.agent.?>` - User access to any agent (wildcard)

## Choose Your Path

- **Business Users & Admins**: Start with the
  [Platform RBAC Guide](../../../1_vision_and_positioning/3_solution/4_security/2_rbac/index.md)
- **Developers & Integrators**: Begin with the
  [SDK Implementation Guide](../../../3_sdk/5_advanced_topics/5_rbac/index.md)

Both guides provide comprehensive coverage of the AI-Hub RBAC system tailored to your specific needs and use cases.
