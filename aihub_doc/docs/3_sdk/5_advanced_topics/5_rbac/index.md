---
title: RBAC Implementation Guide
index: 5
---

# RBAC Implementation Guide :shield: :gear:

::: info **SDK Developer Overview**
This guide covers how to implement Role-Based Access Control (RBAC) in your AI-Hub applications, including API endpoint
protection, agent access controls, and custom permission checking. Learn how to leverage the AI-Hub's sophisticated
permission system to secure your custom agents, processes, and services.
:::

## Controller-Level Access Protection

### Basic Endpoint Protection

The AI-Hub provides a comprehensive framework for protecting API endpoints through the `Controller` base class and its
permission checking mechanisms.

**Simple Permission Checking:**

```python
from aihub_lib.routes.Controller import Controller
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from fastapi import Security
from typing import Annotated

class MyController(Controller):
    def __init__(self, *, auth: AuthHandler, route: str = "/my-service"):
        super().__init__(auth=auth, route=route)

    def protected_endpoint(self, route: str = "/protected") -> "MyController":
        @self.router.get(route, tags=self.tags)
        async def protected_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.service.my_service"))]
        ) -> dict:
            """Only users with access to my_service can access this endpoint."""
            return {"message": "Access granted", "user_id": user.id}
        return self
```

### Dynamic Permission Resolution

The AI-Hub supports dynamic permission checking where path parameters are automatically substituted into permission
templates:

**Path Parameter Integration:**

```python
def agent_specific_endpoint(self, route: str = "/{agent_class}/{agent_id}") -> "MyController":
    @self.router.get(route, tags=self.tags)
    async def agent_specific_endpoint(
        agent_class: str,
        agent_id: str,
        user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))]
    ) -> dict:
        """Permission is dynamically constructed as aihub.user.agent.customer_service.chatbot_v1"""
        return {
            "message": "Access granted to specific agent",
            "agent_class": agent_class,
            "agent_id": agent_id,
            "user": user.email
        }
    return self
```

### Multi-Level Permission Checking

The Controller framework implements three-tier authorization that can be customized for your specific requirements:

**Service-Level Access Control:**

```python
class SecureController(Controller):
    def __init__(self, *, auth: AuthHandler, route: str = "/secure",
                 additionally_required_permission: str | None = None):
        # The additionally_required_permission adds an extra layer of security
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission="aihub.admin.special_access"
        )

    def admin_only_endpoint(self, route: str = "/admin") -> "SecureController":
        @self.router.post(route, tags=self.tags)
        async def admin_only_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.service.secure"))]
        ) -> dict:
            """
            Users need both:
            1. aihub.admin.special_access (from additionally_required_permission)
            2. aihub.admin.service.secure (from the endpoint permission)
            """
            return {"message": "Admin access granted"}
        return self
```

## Service-Level Access Control Implementation

### Custom Service Integration

When building custom services that integrate with the AI-Hub, implement proper access control through the established
patterns:

**Service Class Implementation:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from fastapi import HTTPException

class MyCustomService:
    @staticmethod
    async def get_user_data(user: UserIdentity, resource_id: str) -> dict:
        """Service method with integrated access checking."""
        access_checker = AccessChecker.from_user(user)

        # Check if user has access to this specific resource
        if not access_checker.has_access(f"aihub.user.service.my_custom.{resource_id}"):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to resource {resource_id}"
            )

        # Proceed with business logic
        return await fetch_user_specific_data(user.id, resource_id)

    @staticmethod
    async def get_admin_overview(user: UserIdentity) -> dict:
        """Administrative function with access level checking."""
        access_checker = AccessChecker.from_user(user)

        # Check for admin-level access
        access_level = access_checker.access_level("aihub.admin.service.my_custom")
        if access_level == AccessLevel.ACCESS_DENIED:
            raise HTTPException(status_code=403, detail="Administrative access required")

        # Return different data based on access level
        if access_level == AccessLevel.ACCESS_ADMIN:
            return await fetch_comprehensive_admin_data()
        else:
            return await fetch_limited_admin_data()
```

### Dynamic Access Evaluation

Implement dynamic access checking for scenarios where permissions need to be evaluated based on runtime conditions:

**Runtime Permission Checking:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel

class DynamicAccessService:
    @staticmethod
    async def get_agent_list(user: UserIdentity, agent_type: str | None = None) -> list[dict]:
        """Return filtered agent list based on user permissions."""
        access_checker = AccessChecker.from_user(user)
        available_agents = await fetch_all_agents()

        filtered_agents = []
        for agent in available_agents:
            # Check access to each agent individually
            if access_checker.has_access_to_agent(agent.agent_class, agent.agent_id):
                # Add access level information
                access_level = access_checker.access_level_for_agent(
                    agent.agent_class, agent.agent_id
                )
                filtered_agents.append({
                    "agent_id": agent.agent_id,
                    "agent_class": agent.agent_class,
                    "access_level": access_level.value,
                    "can_configure": access_level == AccessLevel.ACCESS_ADMIN
                })

        return filtered_agents

    @staticmethod
    async def check_bulk_permissions(user: UserIdentity, resources: list[str]) -> dict[str, bool]:
        """Efficiently check permissions for multiple resources."""
        access_checker = AccessChecker.from_user(user)
        results = {}

        for resource in resources:
            results[resource] = access_checker.has_access(resource)

        return results
```

## Agent Access Control Implementation

### Agent-Specific Permission Checking

When building custom agents, implement proper access controls to ensure only authorized users can interact with your
agents:

**Agent Access Integration:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity

class CustomAgent:
    def __init__(self, agent_class: str, agent_id: str):
        self.agent_class = agent_class
        self.agent_id = agent_id

    async def process_user_request(self, user: UserIdentity, request: str) -> str:
        """Process request with proper access control."""
        access_checker = AccessChecker.from_user(user)

        # Verify user has access to this specific agent
        if not access_checker.has_access_to_agent(self.agent_class, self.agent_id):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to agent {self.agent_class}/{self.agent_id}"
            )

        # Check access level to determine response detail
        access_level = access_checker.access_level_for_agent(self.agent_class, self.agent_id)

        if access_level == AccessLevel.ACCESS_ADMIN:
            # Provide detailed response for administrators
            return await self.process_admin_request(request, user)
        else:
            # Standard user response
            return await self.process_user_request_internal(request, user)

    async def get_agent_configuration(self, user: UserIdentity) -> dict:
        """Return agent configuration based on user access level."""
        access_checker = AccessChecker.from_user(user)
        access_level = access_checker.access_level_for_agent(self.agent_class, self.agent_id)

        if access_level == AccessLevel.ACCESS_DENIED:
            raise HTTPException(status_code=403, detail="Agent access denied")
        elif access_level == AccessLevel.ACCESS_ADMIN:
            return await self.get_full_configuration()
        else:
            return await self.get_user_configuration()
```

### Agent Discovery with Access Control

Implement agent discovery that respects user permissions:

**Filtered Agent Discovery:**

```python
class AgentDiscoveryService:
    @staticmethod
    async def discover_available_agents(user: UserIdentity) -> list[dict]:
        """Return only agents the user has access to."""
        access_checker = AccessChecker.from_user(user)
        all_agents = await fetch_registered_agents()

        accessible_agents = []
        for agent_info in all_agents:
            if access_checker.has_access_to_agent(
                agent_info.agent_class,
                agent_info.agent_id
            ):
                # Include access level in response
                access_level = access_checker.access_level_for_agent(
                    agent_info.agent_class,
                    agent_info.agent_id
                )

                accessible_agents.append({
                    "agent_class": agent_info.agent_class,
                    "agent_id": agent_info.agent_id,
                    "display_name": agent_info.display_name,
                    "description": agent_info.description,
                    "access_level": access_level.value,
                    "can_configure": access_level == AccessLevel.ACCESS_ADMIN
                })

        return accessible_agents

    @staticmethod
    async def check_agent_access(user: UserIdentity, agent_class: str, agent_id: str) -> dict:
        """Check specific agent access with detailed information."""
        access_checker = AccessChecker.from_user(user)

        return {
            "has_access": access_checker.has_access_to_agent(agent_class, agent_id),
            "access_level": access_checker.access_level_for_agent(agent_class, agent_id).value,
            "can_view": access_checker.has_access_to_agent(agent_class, agent_id),
            "can_configure": access_checker.access_level_for_agent(agent_class, agent_id) == AccessLevel.ACCESS_ADMIN,
            "has_class_access": access_checker.has_access_to_agent_class(agent_class)
        }
```

## Process Access Control Implementation

### Process-Level Permission Management

When implementing custom processes, integrate proper access controls to ensure secure process execution:

**Process Access Integration:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

class CustomProcess:
    def __init__(self, process_class: str, process_id: str):
        self.process_class = process_class
        self.process_id = process_id

    async def start_process(self, user: UserIdentity, process_data: dict) -> str:
        """Start process with proper access verification."""
        access_checker = AccessChecker.from_user(user)

        # Check if user can start this specific process
        if not access_checker.has_access_to_process(self.process_class, self.process_id):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to process {self.process_class}/{self.process_id}"
            )

        # Check access level for process configuration
        access_level = access_checker.access_level_for_process(self.process_class, self.process_id)

        if access_level == AccessLevel.ACCESS_ADMIN:
            # Admin users can override default process settings
            return await self.start_process_with_overrides(process_data, user)
        else:
            # Standard users use default process configuration
            return await self.start_standard_process(process_data, user)

    async def get_process_status(self, user: UserIdentity, execution_id: str) -> dict:
        """Get process status with appropriate detail level."""
        access_checker = AccessChecker.from_user(user)

        # Verify access to the process type
        if not access_checker.has_access_to_process(self.process_class, self.process_id):
            raise HTTPException(status_code=403, detail="Process access denied")

        execution_info = await fetch_execution_info(execution_id)

        # Check if user can view other users' executions
        if execution_info.user_id != user.id:
            access_level = access_checker.access_level_for_process(self.process_class, self.process_id)
            if access_level != AccessLevel.ACCESS_ADMIN:
                raise HTTPException(status_code=403, detail="Cannot view other users' process executions")

        return await build_process_status_response(execution_info, user)
```

## Advanced Permission Patterns

### Wildcard Permission Implementation

Understand and implement wildcard permission checking for flexible access control:

**Wildcard Pattern Usage:**

```python
class AdvancedAccessService:
    @staticmethod
    async def check_wildcard_access(user: UserIdentity) -> dict:
        """Demonstrate different wildcard permission patterns."""
        access_checker = AccessChecker.from_user(user)

        return {
            # Specific resource access
            "specific_agent": access_checker.has_access("aihub.user.agent.customer_service.chatbot_v1"),

            # Single-level wildcard (any instance of customer_service agents)
            "customer_service_agents": access_checker.has_access("aihub.user.agent.customer_service.*"),

            # Multi-level wildcard (any agent)
            "any_agent": access_checker.has_access("aihub.user.agent.>"),

            # Capability checking wildcards
            "has_agent_access": access_checker.has_access("aihub.user.agent.?*"),
            "has_service_access": access_checker.has_access("aihub.user.service.?>"),

            # Admin privilege checking
            "admin_any_service": access_checker.has_access("aihub.admin.service.?>"),
            "admin_specific": access_checker.has_access("aihub.admin.service.roles")
        }

    @staticmethod
    async def get_accessible_resources(user: UserIdentity, resource_type: str) -> list[str]:
        """Return list of resources user has access to based on wildcard patterns."""
        access_checker = AccessChecker.from_user(user)
        all_resources = await fetch_resources_by_type(resource_type)

        accessible_resources = []
        for resource in all_resources:
            resource_permission = f"aihub.user.{resource_type}.{resource.category}.{resource.id}"
            if access_checker.has_access(resource_permission):
                accessible_resources.append(resource.id)

        return accessible_resources
```

### Custom Permission Validation

Implement custom permission validation logic for complex scenarios:

**Custom Validation Logic:**

```python
class CustomPermissionValidator:
    @staticmethod
    async def validate_complex_access(user: UserIdentity, request_data: dict) -> bool:
        """Implement complex permission logic combining multiple checks."""
        access_checker = AccessChecker.from_user(user)

        # Multiple permission requirements
        required_permissions = [
            "aihub.user.service.data_processing",
            f"aihub.user.knowledge.{request_data.get('knowledge_base')}",
            f"aihub.user.agent.{request_data.get('agent_type')}.?*"
        ]

        # All permissions must be satisfied
        for permission in required_permissions:
            if not access_checker.has_access(permission):
                return False

        # Additional business logic checks
        if request_data.get('sensitive_data', False):
            # Sensitive data requires admin access
            if access_checker.access_level("aihub.admin.service.data_processing") == AccessLevel.ACCESS_DENIED:
                return False

        return True

    @staticmethod
    async def get_permission_summary(user: UserIdentity) -> dict:
        """Generate comprehensive permission summary for user."""
        access_checker = AccessChecker.from_user(user)

        return {
            "user_info": {
                "id": user.id,
                "email": user.email,
                "roles": user.roles
            },
            "access_summary": {
                "total_rules": len(access_checker.access_rules),
                "admin_rules": len(access_checker.admin_access_rules),
                "user_rules": len(access_checker.user_access_rules)
            },
            "capabilities": {
                "can_access_agents": access_checker.has_access("aihub.user.agent.?*"),
                "can_access_processes": access_checker.has_access("aihub.user.process.?*"),
                "can_access_services": access_checker.has_access("aihub.user.service.?*"),
                "has_admin_access": access_checker.has_access("aihub.admin.?>")
            },
            "specific_access": {
                "role_management": access_checker.access_level("aihub.admin.service.roles").value,
                "experiment_service": access_checker.access_level("aihub.user.service.experiments").value
            }
        }
```

## Testing RBAC Implementation

### Unit Testing Permission Logic

Implement comprehensive tests for your RBAC integration:

**Permission Testing Framework:**

```python
import pytest
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.identity.UserIdentity import UserIdentity

class TestRBACImplementation:
    @pytest.fixture
    def test_user(self) -> UserIdentity:
        """Create test user with specific roles."""
        return UserIdentity(
            id="test_user_123",
            email="test@example.com",
            name="Test User",
            roles=["agent_user", "process_participant"]
        )

    @pytest.fixture
    def admin_user(self) -> UserIdentity:
        """Create admin test user."""
        return UserIdentity(
            id="admin_user_123",
            email="admin@example.com",
            name="Admin User",
            roles=["ai_admin"]
        )

    def test_user_agent_access(self, test_user):
        """Test user-level agent access."""
        access_checker = AccessChecker.from_user(test_user)

        # Test specific agent access
        assert access_checker.has_access_to_agent("customer_service", "chatbot_v1")
        assert not access_checker.has_access_to_agent("admin_tools", "user_manager")

        # Test access levels
        access_level = access_checker.access_level_for_agent("customer_service", "chatbot_v1")
        assert access_level == AccessLevel.ACCESS_USER

    def test_admin_privileges(self, admin_user):
        """Test administrative access capabilities."""
        access_checker = AccessChecker.from_user(admin_user)

        # Admin should have access to management services
        assert access_checker.has_access("aihub.admin.service.roles")
        assert access_checker.access_level("aihub.admin.service.roles") == AccessLevel.ACCESS_ADMIN

        # Admin should inherit user permissions
        assert access_checker.has_access("aihub.user.agent.customer_service.chatbot_v1")

    def test_wildcard_permissions(self, test_user):
        """Test wildcard permission patterns."""
        access_checker = AccessChecker.from_user(test_user)

        # Test different wildcard patterns
        assert access_checker.has_access("aihub.user.agent.customer_service.*")
        assert access_checker.has_access("aihub.user.agent.?>")
        assert not access_checker.has_access("aihub.admin.?>")

    @pytest.mark.asyncio
    async def test_service_integration(self, test_user):
        """Test service-level access integration."""
        # Mock service call with permission checking
        service = MyCustomService()

        # Should succeed for authorized resource
        result = await service.get_user_data(test_user, "allowed_resource")
        assert result is not None

        # Should fail for unauthorized resource
        with pytest.raises(HTTPException) as exc_info:
            await service.get_user_data(test_user, "forbidden_resource")
        assert exc_info.value.status_code == 403
```

### Integration Testing

Test RBAC integration with your API endpoints:

**API Integration Tests:**

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

class TestRBACAPIIntegration:
    @pytest.fixture
    async def authenticated_client(self):
        """Create authenticated test client."""
        # Set up test client with proper authentication
        auth = TestAuthHandler()  # Your test auth handler
        runner = ApiTestRunner()
        runner.mount(MyController(auth=auth))

        async with AsyncClient(app=runner.create_app()) as client:
            yield client

    @pytest.mark.asyncio
    async def test_protected_endpoint_access(self, authenticated_client):
        """Test access to protected endpoints."""
        # Test successful access with proper permissions
        response = await authenticated_client.get("/my-service/protected")
        assert response.status_code == 200

        # Test denied access without permissions
        response = await authenticated_client.get("/my-service/admin-only")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dynamic_permission_resolution(self, authenticated_client):
        """Test dynamic permission checking with path parameters."""
        # Test access to specific agent
        response = await authenticated_client.get("/agents/customer_service/chatbot_v1")
        assert response.status_code == 200

        # Test denied access to restricted agent
        response = await authenticated_client.get("/agents/admin_tools/user_manager")
        assert response.status_code == 403
```

## Best Practices for RBAC Implementation

### Security Considerations

**Fail-Safe Defaults**: Always default to denying access when permission checks are unclear or fail.

**Comprehensive Logging**: Log all permission checks and access decisions for audit and security monitoring.

**Consistent Error Handling**: Use consistent HTTP status codes and error messages for permission denials.

**Permission Validation**: Validate permission templates and access rules to prevent security vulnerabilities.

### Performance Optimization

**Caching Strategies**: Implement appropriate caching for permission checks to optimize performance.

**Batch Permission Checking**: When checking multiple permissions, use batch operations where possible.

**Lazy Evaluation**: Only perform permission checks when necessary to minimize performance impact.

### Development Guidelines

**Clear Permission Naming**: Use descriptive and consistent permission naming conventions.

**Documentation**: Document permission requirements for all endpoints and services.

**Testing Coverage**: Ensure comprehensive test coverage for all permission scenarios.

**Regular Reviews**: Conduct regular reviews of permission structures and access patterns.

This implementation guide provides the foundation for integrating RBAC into your AI-Hub applications while maintaining
security, performance, and maintainability.
