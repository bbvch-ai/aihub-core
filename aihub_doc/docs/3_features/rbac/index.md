---
title: Role-Based Access Control (RBAC)
index: 2
---

# Role-Based Access Control (RBAC) :shield: :lock:

::: info **TL;DR - What is RBAC?** The AI-Hub provides enterprise-grade **Role-Based Access Control (RBAC)** that
enables organizations to securely manage who can access what resources across their AI ecosystem. This hierarchical
permission system uses flexible access rules with dot-notation and wildcard support, allowing administrators to grant
precise access to agents, processes, and services while maintaining strict security boundaries. :::

## What is RBAC and How Does It Work? :brain:

**Role-Based Access Control (RBAC)** is a security framework that restricts system access based on user roles within an
organization. The AI-Hub implements a sophisticated, hierarchical RBAC system that separates authentication from
authorization, providing granular control over every aspect of your AI platform.

The system operates on a **dot-notation permission model** similar to DNS or file system paths, where permissions are
structured as `aihub.user.agent.class_a.id_123`. This allows for both specific resource access and flexible wildcard
patterns using `*` (single-level) and `>` (multi-level recursive) wildcards.

**Key Components:**

- **Roles**: Named collections of access rules that define what users can do
- **Access Rules**: Specific permissions using dot-notation (e.g., `aihub.admin.service.roles`)
- **User Identity**: Integration with enterprise authentication systems (Azure AD, OAuth2)
- **Permission Templates**: Dynamic permission checking with path parameter substitution
- **Three-Tier Authorization**: Service access → Additional permissions → Specific resource permissions

The system supports **multiple authentication strategies** including Azure AD integration, token-based authentication,
and development-friendly bypass options, making it suitable for any deployment environment.

## Why This is Critical for Your AI Strategy :trophy:

Implementing robust access control is not just a security requirement—it's a business enabler that allows you to scale
AI adoption safely across your organization:

**🛡️ Enterprise Security Compliance**: Meet strict regulatory requirements (GDPR, HIPAA, SOX) and corporate security
policies by ensuring only authorized users can access sensitive AI processes and data. The system provides comprehensive
audit trails and granular access controls essential for compliance.

**🎯 Granular Resource Control**: Control access to specific AI agents, processes, and services with precision. Users can
access only the AI capabilities they need for their role, preventing accidental misuse of powerful AI tools and
protecting sensitive business logic.

**⚡ Scalable Permission Management**: Manage permissions efficiently across large organizations using role-based
hierarchies. Instead of managing individual user permissions, administrators can create roles once and assign them to
multiple users, dramatically reducing administrative overhead.

**🔗 Seamless Enterprise Integration**: Native integration with existing enterprise identity systems (Azure AD, OAuth2)
means users can access AI-Hub using their existing corporate credentials, while IT administrators maintain centralized
control through familiar identity management tools.

**🧠 Risk-Aware AI Deployment**: Deploy AI agents and processes with confidence knowing that access is controlled and
monitored. Different teams can have different levels of access to AI capabilities, allowing gradual rollout of AI
features while maintaining security boundaries.

::: details **Setting Up and Using RBAC**

## Configuration Requirements

Setting up RBAC in your AI-Hub deployment:

1. **Authentication Configuration**: Configure your preferred authentication method in the AI-Hub environment

   - **Azure AD**: Set up OAuth2 integration with Microsoft Graph API
   - **Token-based**: Configure database-driven user management
   - **Development**: Use bypass authentication for development environments

1. **Role Definition**: Create roles that match your organizational structure

   - Navigate to the AI-Hub admin interface
   - Access the "Roles" management section
   - Define roles with appropriate access rules

1. **User Assignment**: Assign users to roles through your identity provider

   - Azure AD: Map Azure AD groups to AI-Hub roles
   - Token-based: Assign roles directly through the AI-Hub interface

## Usage Examples

### Basic Role Management

**Creating a Role for AI Agent Users:**

```json
{
  "name": "agent_user",
  "description": "Users who can access and interact with AI agents",
  "access_rules": [
    "aihub.user.agent.?>",
    "aihub.user.process.basic.?>",
    "aihub.user.service.chat"
  ]
}
```

**Creating an Admin Role:**

```json
{
  "name": "ai_admin",
  "description": "Full administrative access to AI-Hub",
  "access_rules": [
    "aihub.admin.?>",
    "aihub.user.?>"
  ]
}
```

### Advanced Permission Patterns

**Specific Resource Access:**

- `aihub.user.agent.class_a.id_123` - Access to specific agent instance
- `aihub.admin.service.roles` - Admin access to role management service

**Wildcard Permissions:**

- `aihub.user.agent.class_a.*` - Access to any agent in class_a
- `aihub.user.agent.?>` - Access to any agent of any class
- `aihub.admin.?>` - Full admin access to all resources

### API Integration

**Protecting API Endpoints:**

```python
@Security(controller.user_with_permission("aihub.admin.service.roles"))
async def create_role(role_data: RoleCreateDto):
    # Only users with admin role permissions can create roles
    pass

@Security(controller.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))
async def get_agent_details(agent_class: str, agent_id: str):
    # Dynamic permission checking with path parameters
    pass
```

## Available Capabilities

The AI-Hub RBAC system provides:

- **Role Management API**: Complete CRUD operations for roles and permissions
- **User Identity Integration**: Support for multiple authentication providers
- **Permission Templates**: Dynamic permission checking with parameter substitution
- **Hierarchical Access**: Admin roles automatically inherit user permissions
- **Wildcard Support**: Flexible pattern matching for broad or specific access
- **Audit Integration**: Comprehensive logging and monitoring capabilities
- **Frontend Management**: Web-based interface for role administration

## Security and Best Practices

**Permission Design:**

- Follow the **principle of least privilege**: Grant only the minimum access required
- Use **role hierarchies** to simplify permission management
- Implement **regular access reviews** to ensure permissions remain appropriate

**Authentication Security:**

- Use **enterprise identity providers** (Azure AD) for centralized management
- Implement **token rotation** for token-based authentication
- Enable **multi-factor authentication** where supported

**Monitoring and Auditing:**

- Monitor access patterns through AI-Hub observability tools
- Set up alerts for suspicious permission usage
- Regular review of role assignments and access patterns
- Maintain audit logs for compliance requirements

**Development vs Production:**

- Use development authentication bypass only in isolated development environments
- Implement proper role-based testing with mock users
- Validate permission logic through comprehensive test suites

:::

## Getting Started

To begin implementing RBAC in your AI-Hub deployment:

1. **Configure Authentication**: Set up your preferred authentication method (Azure AD recommended for enterprise)
1. **Define Organizational Roles**: Create roles that match your team structure and access requirements
1. **Assign Initial Users**: Map users to roles through your identity provider or AI-Hub interface
1. **Test Access Patterns**: Verify that users can access appropriate resources and are blocked from unauthorized areas

For detailed API documentation and advanced configuration options, refer to the AI-Hub API reference and your specific
authentication provider's documentation.
