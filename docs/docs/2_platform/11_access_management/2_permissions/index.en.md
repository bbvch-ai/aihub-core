---
title: Permission and Access Control
---

# Permission and Access Control

The Swiss AI Hub suite interface implements sophisticated permission-based access control that dynamically adapts the
user experience to each individual's authorization level. This approach ensures users see only relevant capabilities
while maintaining security and compliance requirements.

## Dynamic Service Visibility

Traditional application interfaces often present all features to all users, relying on authentication checks to block
unauthorized access. This creates cluttered interfaces filled with disabled buttons and features users cannot use,
leading to confusion and support burden. The Swiss AI Hub fundamentally reimagines this approach through dynamic service
visibility.

**Permission-Filtered Service Catalog**: When the suite loads, it queries the backend for the user's authorized service
catalog. The backend evaluates the user's permissions against each registered service's requirements, returning only
services the user can access. The interface renders navigation elements exclusively for authorized services - users
simply never see capabilities they cannot use.

**Clean, Focused Interface**: This approach creates dramatically simpler interfaces compared to traditional
applications. A data scientist sees evaluation and experimentation services prominently featured. A business analyst
sees conversation threads and knowledge exploration tools. An administrator sees user management and system
configuration options. Each user's interface reflects their actual capabilities, not a universal feature set cluttered
with inaccessible options.

**Automatic Permission Updates**: When an administrator modifies a user's role assignments or permission grants, these
changes automatically reflect in the user's interface upon their next session. There is no cache invalidation, manual
refresh, or logout-login cycle required. The suite's architecture ensures the interface always presents an accurate view
of current authorization state.

**Security Through Invisibility**: By not rendering unauthorized service navigation elements, the suite eliminates an
entire class of security vulnerabilities. Users cannot attempt to access restricted services through interface
manipulation because those services have no interface presence. This defense-in-depth approach complements backend
authorization enforcement.

## Hierarchical Permission System

The suite integrates with the Swiss AI Hub's comprehensive hierarchical permission system, which provides fine-grained
access control through a structured, dot-notation permission syntax.

**Permission Structure**: Permissions follow the format `aihub.[user|admin].<service>.<resource_type>.<resource_id>`,
creating a hierarchical namespace that enables precise access control. For example,
`aihub.user.agent.support_agent.instance_001` grants access to a specific agent instance, while `aihub.admin.knowledge`
grants administrative access to the entire knowledge management service.

**Wildcard Support**: The permission system supports sophisticated wildcards that enable flexible access control without
requiring explicit enumeration of every resource. The `*` wildcard matches any single path segment, while the `>`
wildcard matches any remaining path segments. This enables rules like `aihub.user.agent.>` to grant access to all agent
resources at any depth.

**Implicit Permissions**: Users with the implicit permission pattern `aihub.user.?>` gain access to all user-level
services without requiring explicit grants for each service. This simplifies permission management for standard users
while maintaining fine-grained control for specialized access patterns.

**Service-Level Access Control**: Each service controller declares minimum permission requirements for access. The suite
endpoint evaluates whether the user possesses these minimum permissions when constructing the service catalog. Services
requiring permissions the user lacks simply don't appear in the catalog response.

## Role-Based Interface Adaptation

Beyond simple show/hide logic, the suite implements role-aware interface adaptation that presents different views and
capabilities based on user authorization levels.

**Administrative Privileges**: When the suite endpoint evaluates permissions, it determines not just whether the user
can access a service, but whether they have administrative privileges for that service. This distinction is communicated
to the frontend, which can present additional administrative capabilities within that service's interface.

**Context-Aware Navigation**: The suite maintains awareness of the user's current authorization context. When viewing an
agent, the interface can determine whether the user has administrative access to that specific agent, presenting
administrative controls like configuration editing only when authorized. Standard users see read-only views of the same
resources.

**Granular Feature Control**: Within individual services, the interface can query the user's permissions for specific
resources or operations. A user might have read access to knowledge bases but lack upload permissions. The interface
reflects this by showing knowledge exploration features while hiding document upload controls.

**Multi-Tenant Isolation**: In deployments serving multiple organizational units or customer tenants, the permission
system ensures complete data isolation. Users see only services and resources belonging to their organizational context,
creating secure, isolated workspaces within a shared platform deployment.

## Permission Evaluation Architecture

The suite's permission-aware behavior results from sophisticated coordination between frontend queries and backend
evaluation logic.

**Backend Permission Evaluation**: All permission evaluation occurs on the backend, ensuring security enforcement cannot
be bypassed through client-side manipulation. The suite endpoint queries the permission system, evaluates access rules
against the user's roles and grants, and returns a pre-filtered service catalog. The frontend trusts this catalog
without performing its own permission logic.

**Access Checker Integration**: The backend employs an Access Checker component that encapsulates permission evaluation
logic. This component accepts a user identity and permission pattern, evaluates whether the user's access rules match
the pattern, and returns either boolean access decisions or detailed access level enumeration (denied, user access,
administrative access).

**Efficient Permission Queries**: Permission evaluation is optimized for performance through caching strategies and
efficient pattern matching algorithms. When the suite endpoint evaluates service visibility for a user, it performs
these evaluations in parallel rather than sequentially, ensuring responsive interface load times even with numerous
services.

**Audit Trail Generation**: Every permission evaluation generates audit log entries documenting what permissions were
checked, for which user, and what decision was made. This creates comprehensive audit trails supporting compliance
reporting and security forensics.

## Service-Specific Permission Patterns

Different services implement different permission patterns based on their functional requirements, demonstrating the
flexibility of the hierarchical permission system.

**Agent Service**: Implements per-agent access control where users might have access to specific agent instances but not
others. Permissions like `aihub.user.agent.customer_support.cs_001` grant access to a specific agent, while
`aihub.user.agent.customer_support.*` grants access to all instances of that agent class.

**Thread Service**: Controls access to conversation threads based on ownership and sharing rules. Users generally have
access to threads they created or participated in, with administrators having broader visibility for support and
monitoring purposes.

**Knowledge Service**: Implements namespace-based access control where permissions can be granted at the database level
(`aihub.user.knowledge.hr_documents`) or namespace level (`aihub.user.knowledge.hr_documents.policies`), with
hierarchical inheritance through the permission tree.

**Administrative Services**: Require explicit administrative permissions like `aihub.admin.users` or
`aihub.admin.roles`. These services never appear for users without administrative grants, creating a clear separation
between standard and administrative interfaces.

## User Experience Benefits

The permission-aware suite architecture delivers significant user experience and operational advantages.

**Elimination of Access Denied Errors**: Users never encounter "access denied" messages for visible interface elements
because unauthorized features simply don't appear. This eliminates a common source of user frustration and support
tickets in traditional enterprise applications.

**Reduced Interface Complexity**: By showing only authorized capabilities, the interface remains uncluttered and
focused. Users don't need to mentally filter visible-but-disabled features from available capabilities - everything they
see, they can use.

**Self-Service Access Understanding**: Users can immediately understand their authorized capabilities by observing what
appears in the suite navigation. There's no need to consult separate documentation or contact support to determine what
features they can access.

**Streamlined Onboarding**: New users see only the capabilities relevant to their role, dramatically simplifying initial
platform orientation. Training can focus on relevant features rather than helping users understand what they cannot
access and why.

## Security and Compliance Advantages

The permission-aware architecture provides security and compliance benefits beyond user experience improvements.

**Defense in Depth**: Client-side filtering of unauthorized services complements backend permission enforcement,
creating multiple security layers. Even if an attacker manipulates the frontend, backend authorization enforcement
prevents unauthorized operations.

**Reduced Attack Surface**: By not exposing information about services users cannot access, the suite reveals less about
the deployment's capabilities to potential attackers. Users cannot probe disabled features to gather information for
attacks.

**Compliance Support**: The comprehensive audit logging of permission evaluations supports regulatory compliance
requirements for access control, particularly in sectors with strict data protection requirements like healthcare,
finance, and public administration.

**Zero-Trust Architecture**: The suite implements zero-trust principles where every service access requires explicit
permission evaluation. There are no implicit trust assumptions based on network location or previous authentication -
every operation is independently authorized.

## Operational Advantages

Beyond security and user experience, the permission system provides operational benefits for platform administrators.

**Centralized Permission Management**: Administrators manage permissions through the role management service, with
changes automatically reflected across the entire suite. There's no need to configure access controls separately for
each service or coordinate permissions across multiple systems.

**Flexible Delegation**: The hierarchical permission system enables sophisticated delegation patterns. Senior staff can
be granted broad access patterns like `aihub.user.agent.>`, while junior staff receive specific grants for individual
resources. This flexibility supports organizational structures without requiring complex access control configurations.

**Permission Inheritance**: The hierarchical structure enables permission inheritance where granting access to a
higher-level resource automatically provides access to contained resources. This simplifies permission management while
maintaining precise control when needed.

**Role-Based Administration**: Rather than managing individual user permissions, administrators typically assign users
to roles that define standard permission sets. Role modifications automatically apply to all assigned users, ensuring
consistent access control across user populations.

This permission-aware architecture ensures that the Swiss AI Hub suite provides each user with a focused, secure
interface precisely tailored to their authorization level and organizational role, while maintaining the operational
simplicity and security rigor required for enterprise and public sector deployments.

# Role-Based Access Control (RBAC)

## Overview

**Role-Based Access Control (RBAC)** is a security framework that restricts system access based on user roles within an
organization. The Swiss AI Hub implements a hierarchical RBAC system with tenant-scoped roles that provides granular
control over every aspect of the platform.

### Core Components

- **Roles**: Named collections of access rules that define what users can do (managed locally, not synced from identity
  providers)
- **Tenants**: Organizational boundaries that scope role assignments
- **Access Rules**: Specific permissions using dot-notation (e.g., `aihub.admin.service.roles`)
- **User Identity**: Authenticated via OAuth2/OIDC, with roles resolved from the local tenant-scoped role database
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

For multi-tenancy and access control details, see the
[Multi-Tenancy Access Control](../../16_multi_tenancy/4_access_control/) documentation.
