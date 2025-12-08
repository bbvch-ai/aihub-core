---
title: AI-Hub Library
index: 2
---

# 📚 AI-Hub Library Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_lib-core&metric=alert_status&token=fd16708223dbf5307a0ac28f15879abb57a8fc68)](https://sonarcloud.io/summary/new_code?id=aihub-core_lib-core)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_lib-core&metric=security_rating&token=fd16708223dbf5307a0ac28f15879abb57a8fc68)](https://sonarcloud.io/summary/new_code?id=aihub-core_lib-core)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_lib-core&metric=vulnerabilities&token=fd16708223dbf5307a0ac28f15879abb57a8fc68)](https://sonarcloud.io/summary/new_code?id=aihub-core_lib-core)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_lib-core&metric=sqale_rating&token=fd16708223dbf5307a0ac28f15879abb57a8fc68)](https://sonarcloud.io/summary/new_code?id=aihub-core_lib-core)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_lib-core&metric=ncloc&token=fd16708223dbf5307a0ac28f15879abb57a8fc68)](https://sonarcloud.io/summary/new_code?id=aihub-core_lib-core)

## 1. 🎯 Foundational Knowledge of Library Development

This section covers the foundational architecture, patterns, and terminology you need to know before contributing to the shared library.

::: info
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_lib`

::: tip Core Principle
You are contributing to the **aihub_lib** scope, which serves as the foundational shared library within the AI-Hub platform. This scope implements core infrastructure and utilities used across all other services. The guiding principle is simple: **if code is used by more than one other service, it belongs here**.
:::

The library provides essential building blocks including event-driven architecture, authentication/authorization systems, internationalization support, generative AI utilities, and comprehensive testing frameworks.

### 📁 Project Structure

The `aihub_lib` scope is organized as follows:

```
aihub_lib/
├── aihub_lib/                 # Main package source
│   ├── auth/                  # Authentication and authorization system
│   │   ├── access/            # Permission-based access control
│   │   ├── dependencies/      # Auth handlers and strategies
│   │   └── identity/          # User identity providers
│   ├── nats/                  # Event-driven messaging system
│   │   ├── events/            # Event definitions and hierarchies
│   │   ├── dispatcher/        # Workflow orchestration engine
│   │   ├── publishers/        # Event publishing mechanisms
│   │   ├── subscribers/       # Event subscription handling
│   │   └── topic_managers/    # Subject/topic routing management
│   ├── generative_ai/         # AI/ML utilities and abstractions
│   │   ├── document/          # Document processing and parsing
│   │   ├── evaluation/        # AI model evaluation frameworks
│   │   ├── resources/         # LLM configuration and cost tracking
│   │   └── prompting/         # Prompt engineering utilities
│   ├── i18n/                  # Internationalization system
│   │   ├── translations/      # Translation files (DE, EN, FR, IT)
│   │   └── LocaleHandler.py   # Core i18n functionality
│   ├── infrastructure/        # Cloud service configurations
│   │   ├── azure/             # Azure service integrations
│   │   ├── google/            # Google Cloud service configs
│   │   └── phoenix/           # Phoenix tracing configuration
│   ├── persistence/           # Database and storage abstractions
│   │   ├── agents/            # Agent entity management
│   │   ├── messaging/         # Message persistence
│   │   └── rag/               # Document and vector storage
│   ├── routes/                # FastAPI controller base classes
│   │   ├── Controller.py      # Base controller with auth integration
│   │   └── health/            # Health check endpoints
│   ├── testing/               # Testing framework and utilities
│   │   ├── asyncio_utils/     # Async testing support
│   │   ├── auth_utils/        # Authentication testing helpers
│   │   └── logging/           # Test logging configuration
│   └── ...                    # Other shared utilities
└── tests/                     # Comprehensive test suite
```

### 🏗️ Core Architectural Principles

::: info
The library is built on these foundational principles:
:::

#### 📶 1. Event-Driven Architecture

All communication happens via events, enabling loose coupling and scalability. Events are strongly typed Pydantic models with automatic registration and serialization.

#### ⚙️ 2. Configuration-Driven Development

Pydantic-based configuration management with environment variable integration, validation, and hierarchical inheritance.

#### 🌍 3. Internationalization by Design

Built-in multi-language support with YAML-based translations, dynamic locale switching, and comprehensive fallback mechanisms.

---

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to contributing to the shared library.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

::: warning
Always activate the Poetry environment before working. All subsequent commands must be run from within this activated shell.
:::

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

```bash
cd aihub_lib
poetry shell
```

### 🔍 Step 1: Understanding the Domain and Scope

::: info
Before implementing any functionality, determine if it belongs in the library.
:::

#### ✅ When to Add to `aihub_lib`

- **Shared Utilities**: Code used by multiple services (agent, api, process, etc.)
- **Core Infrastructure**: Authentication, messaging, configuration management
- **Common Patterns**: Event definitions, base classes, shared abstractions
- **Testing Utilities**: Fixtures, mocks, and helpers used across services

#### ❌ When NOT to Add to `aihub_lib`

- **Service-Specific Logic**: Business logic specific to one service
- **Implementation Details**: Concrete implementations that don't need sharing
- **Service Dependencies**: Code that depends on specific service requirements

#### 📊 Integration Assessment

1. **Identify Dependencies**: What other services will use this code?
2. **Review Existing Patterns**: Are there similar utilities already implemented?
3. **Consider Breaking Changes**: How will changes affect existing consumers?

### 🛠️ Step 2: Implement Core Components

::: info
Follow these patterns for implementing different types of library components.
:::

#### 🔐 Authentication and Authorization Components

::: tip AuthHandlers and IdentityProviders
**AuthHandlers** are responsible for extracting authentication credentials from HTTP requests and validating them to produce a `UserIdentity`. They serve as the bridge between different authentication mechanisms (OAuth2, token-based, etc.) and the AI-Hub's internal user representation.

**IdentityProviders** are responsible for retrieving detailed user information from identity systems (like Microsoft Graph, LDAP, or custom user databases) given a user identifier. They separate the concerns of authentication (validating credentials) from user information retrieval.
:::

**When to Create New AuthHandlers:**

- Supporting a new authentication protocol (e.g., SAML, custom JWT format)
- Integrating with a new identity provider that requires specific token handling
- Adding multi-factor authentication or custom validation logic
- Creating development/testing authentication bypasses

**When to Create New IdentityProviders:**

- Connecting to a new user directory service (Active Directory, LDAP, etc.)
- Supporting a new user profile storage system
- Adding custom user role resolution logic
- Creating mock providers for testing environments

1. **Create Auth Handler**: For new authentication strategies.

   ```python
   # auth/dependencies/MyAuthHandler/MyAuthHandler.py
   from typing import Annotated
   from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
   from aihub_lib.auth.identity.UserIdentity import UserIdentity
   from fastapi import HTTPException, Request

   class MyAuthHandler(AuthHandler):
       async def __call__(self, request: Request) -> UserIdentity:
           """Extract and validate authentication from FastAPI Request."""
           token = self.extract_token_from_request(request)
           return await self.authenticate_token(token)
       
       async def authenticate_token(self, token: str) -> UserIdentity:
           """Validate token and return user identity."""
           # Implementation-specific authentication logic
           if not self.validate_token_format(token):
               raise HTTPException(status_code=401, detail="Invalid token format")
           
           user_data = await self.validate_token_with_provider(token)
           if not user_data:
               raise HTTPException(status_code=401, detail="Invalid token")
           
           # Use identity provider to get full user details
           return await self.identity_provider.get_user_identity_by_oid(user_data["oid"])
   ```

2. **Create Identity Provider**: For new user identity sources.

   ```python
   # auth/identity/MyIdentityProvider/MyIdentityProvider.py
   from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
   from aihub_lib.auth.identity.UserIdentity import UserIdentity

   class MyIdentityProvider(IdentityProvider):
       async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
           """Retrieve user by Object ID (primary key)."""
           user_data = await self.fetch_user_from_directory(user_oid)
           roles = await self.get_user_roles(user_oid)
           return UserIdentity(
               id=user_data["id"],
               email=user_data["email"],
               display_name=user_data["name"],
               roles=roles
           )
       
       async def get_user_identity_by_email(self, email: str) -> UserIdentity:
           """Retrieve user by email address."""
           user_oid = await self.lookup_oid_by_email(email)
           return await self.get_user_identity_by_oid(user_oid)
       
       async def get_user_roles(self, user_oid: str) -> list[str]:
           """Get user roles from role management system."""
           return await self.fetch_roles_from_directory(user_oid)
       
       async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
           """Get user profile image as data URL."""
           return await self.fetch_profile_image(user_oid)
   ```

#### 📶 Event System Extensions

::: info Event System Architecture
The AI-Hub event system is a sophisticated event-driven architecture that powers all communication between components. Understanding the event hierarchy and when to create new event types is crucial for extending the system effectively.
:::

**Event Directory Structure:**

```
aihub_lib/nats/events/
├── BaseEvent.py                   # Core foundational event class
├── ControlAndDisplayEvent.py      # Multi-inheritance bridge
├── agent_in_the_loop/             # Agent involvement patterns
├── bot_in_the_loop/               # Bot interaction patterns  
├── common/                        # Shared utility events
├── control/                       # System flow control events
├── cost/                          # Cost tracking events
├── discovery/                     # Service discovery events
│   ├── agent/                     # Agent discovery responses
│   └── process/                   # Process discovery responses
├── display/                       # User-facing display events
├── form/                          # Form generation and handling
├── guard/                         # Safety and validation events
├── human_in_the_loop/             # Human involvement patterns
├── process/                       # Process lifecycle events
├── router/                        # Event routing logic
├── semantic/                      # OpenInference tracing events
├── user/                          # User interaction events
├── work/                          # Work completion events
└── work_request/                  # Work delegation events
```

::: details Event Type Categories
**1. Control Events** (`ControlEvent`)
Control events are system-level signals that influence workflow execution. **Only ControlEvent types can drive workflow steps and control system flow.**

Key characteristics:

- Must inherit from `ControlEvent`
- Can be consumed by workflow steps as input
- Drive the progression of automated processes
- Examples: `StartEvent`, `StopEvent`, `ExceptionEvent`, `RouterEvent`

**2. Display Events** (`DisplayEvent`)
Display events are user-facing informational events for UIs and monitoring dashboards. They are purely informational and never affect control flow.

Key characteristics:

- Must inherit from `DisplayEvent`
- Include internationalization support with `LocaleString`
- Never influence workflow execution
- Examples: `ChunkEvent`, `ThoughtEvent`, general `DisplayEvent`

**3. Process Events** (`ProcessEvent`)
Base class for events that influence process control flow, extending `BaseEvent`.

Key characteristics:

- Foundation for work-related events
- Used in agentic process orchestration
- Examples: `WorkEvent`, `WorkRequestEvent`

**4. Semantic Events** (`SemanticEvent`)
Events that must report to OpenInference-compatible tracing systems like Arize Phoenix.

Key characteristics:

- Inherit from `ControlAndDisplayEvent` (both control and display)
- Must implement `to_semantic_convention()` method
- Provide structured semantic attributes for observability
- Examples: `LLMEvent`, `RetrieverEvent`, `EmbeddingEvent`

**5. Work Events** (`WorkEvent`)
Signal successful work completion by entities in agentic processes.

Key characteristics:

- Extend `ProcessEvent`
- Primary drivers of agentic processes
- Signal step completion to process dispatchers
- Variants: `AgentWorkEvent`, `HumanWorkEvent`, `ProcessWorkEvent`, `ProgramWorkEvent`

**6. Work Request Events** (`WorkRequestEvent`)
Delegate work to specific entities in agentic processes.

Key characteristics:

- Extend `ProcessEvent`
- Request work from specific entity types
- Variants: `AgentWorkRequestEvent`, `HumanWorkRequestEvent`, `ProgramWorkRequestEvent`

**7. Discovery Events**
Enable dynamic service discovery and integration.

Key characteristics:

- `AgentDiscoveryResponseEvent`: Details agent capabilities, configs, start/stop events
- `ProcessDiscoveryResponseEvent`: Exposes process inputs for humans/programs/agents
- Enable runtime service integration without manual configuration

**8. In-The-Loop Events**
Support human, agent, and bot involvement in workflows.

Key characteristics:

- Request/response patterns that pause and resume workflows
- Helper classes with `invoke()` methods for easy integration
- Examples: `HumanInTheLoop`, `AgentInTheLoop`, `BotInTheLoop`
:::

::: tip Event Architecture Principles
1. **Automatic Registration**: Events auto-register when imported, enabling dynamic deserialization
2. **Type Safety**: Strong typing with Pydantic validation and comprehensive type annotations
3. **Separation of Concerns**: Clear distinction between control (workflow) and display (UI) events
4. **Extensibility**: Easy addition of new event types without modifying core infrastructure
5. **Observability**: Semantic events provide rich tracing integration
6. **Internationalization**: Display events support multi-language interfaces
7. **Resilience**: Unknown event fallback preserves system functionality
:::

### 🧪 Step 3: Write Comprehensive Tests

::: info
The library uses both BDD and unit testing approaches depending on the component complexity.
:::

#### 📝 BDD Testing for Complex Logic

1. **Create Feature Files**: Describe behavior in Gherkin syntax.

   ```gherkin
   # tests/features/my_component.feature
   Feature: My Component
     Scenario: Test basic functionality
       Given a configured component
       When the component processes input "test data"
       Then the output should contain "processed: test data"
   ```

2. **Implement Test Steps**: Write Python implementations.

   ```python
   # tests/test_my_component.py
   from aihub_lib.testing.asyncio_utils.bdd import async_test
   from pytest_bdd import given, parsers, scenarios, then, when

   scenarios("./features/my_component.feature")

   @given("a configured component", target_fixture="component")
   def _():
       return MyComponent(config=test_config)

   @when(parsers.parse('the component processes input "{input_data}"'))
   @async_test
   async def _(component: MyComponent, input_data: str):
       component.result = await component.process(input_data)

   @then(parsers.parse('the output should contain "{expected}"'))
   def _(component: MyComponent, expected: str):
       assert expected in component.result
   ```

#### 🧪 Unit Testing for Individual Components

1. **Create Unit Tests**: For specific functionality.
   ```python
   # tests/unit/test_my_utility.py
   import pytest
   from aihub_lib.my_domain.MyUtility import MyUtility

   @pytest.mark.asyncio
   async def test_my_utility_basic_functionality():
       utility = MyUtility()
       result = await utility.process("test input")
       assert result == "expected output"

   def test_my_utility_error_handling():
       utility = MyUtility()
       with pytest.raises(ValueError):
           utility.process_invalid_input("invalid")
   ```

### 🔍 Step 4: Debug and Validate

#### 📝 Enable Comprehensive Logging

```python
# Add to test files or debugging scripts
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```

### ✅ Step 5: Ensure Code Quality

::: warning
Before committing changes, use the provided Makefile commands.
:::

```bash
# Run this before creating a pull request
make pr-ready

# Or run commands individually
make format      # Ruff formatting
make lint        # Ruff linting
make test        # Run tests (excluding cloud dependencies)
make test-cov    # Run tests with coverage reporting
```

::: danger Critical Requirements
- All library code must use strict Python type annotations
- All public classes and methods must have comprehensive docstrings
- Breaking changes must be documented and communicated
- Tests must cover both success and failure scenarios
:::

---

## 3. 🎨 Core Library Patterns and Best Practices

This section covers established patterns and best practices for building robust library components.

### ⚙️ Configuration Management Patterns

#### 📝 Pydantic-Based Configuration

::: tip Configuration Management
The AI-Hub uses Pydantic's `BaseSettings` for configuration management rather than `python-dotenv`. This approach provides automatic type validation, environment variable parsing, and comprehensive configuration management without requiring explicit dotenv loading.
:::

Pydantic's `BaseSettings` automatically:

- Loads values from environment variables
- Parses `.env` files when configured
- Validates data types and constraints
- Provides detailed error messages for invalid configurations
- Supports nested configuration objects and complex types

```python
from typing import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class ServiceConfig(BaseSettings):
    endpoint: Annotated[str, Field(description="Service endpoint URL")]
    timeout: Annotated[int, Field(description="Request timeout", ge=1, le=300)] = 30
    api_key: Annotated[str, Field(description="API key for authentication")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SERVICE_",
    )

# Usage - automatically loads from environment and .env file
config = ServiceConfig()
```

### 💾 Persistence Patterns

#### 📊 Entity Design

::: info Entity Pattern
In the AI-Hub, entity classes serve a dual purpose: they define the database schema using MongoEngine's `Document` class, and they also function as repositories by implementing business logic and data access methods as `@classmethod` methods. This pattern combines the Active Record and Repository patterns, providing both data structure definition and data access logic in a single class.
:::

**Repository Pattern via Class Methods:**
Entity classes use `@classmethod` methods to implement repository-like functionality for data access, creation, and business operations. This approach:

- Centralizes data access logic within the entity class
- Provides a consistent interface for database operations
- Enables complex queries and business logic encapsulation
- Maintains clean separation between data structure and access patterns

```python
from mongoengine import Document, StringField, DoesNotExist

class ResourceEntity(Document):
    name = StringField(required=True)
    status = StringField(default="active")
    
    meta = {'collection': 'resources'}
    
    # Repository methods using @classmethod   
    @classmethod
    def by_name(cls, name: str) -> "ResourceEntity":
        return cls.objects.get(name=name)
```

### 🌍 Internationalization Patterns

#### 🌍 Multi-Language Support

::: warning Multi-Language Requirement
The AI-Hub provides comprehensive internationalization (i18n) support with a **mandatory minimum of four languages**: English (en), German (de), French (fr), and Italian (it). German serves as the default locale, reflecting the primary development region. All user-facing content must support these four languages at minimum.
:::

**Key Characteristics:**

- **Default Locale**: German (`de`) - used as fallback when requested locale is unavailable
- **Supported Locales**: `["de", "en", "fr", "it"]` (whitelist enforced)
- **Fallback Chain**: Requested locale → German (`de`) → First available locale
- **Translation Files**: YAML-based, organized by domain (e.g., `common.de.yml`, `errors.en.yml`)
- **Dynamic Loading**: Translations loaded from multiple paths with automatic discovery

#### 📁 Translation File Management

```yaml
# translations/lib/common.en.yml
common:
  welcome_message: "Welcome, {name}!"
  error_occurred: "An error occurred"
  processing: "Processing..."

errors:
  invalid_input: "Invalid input provided"
  unauthorized: "Unauthorized access"
  not_found: "Resource not found"
```

### 📖 Glossary of Library-Specific Terms

This glossary defines terms, concepts, and technologies that have specific meaning within the `aihub_lib` scope, building upon the core AI-Hub terminology.

| Term                            | Definition                                                                                                                          |
| :------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------- |
| **Access Checker**              | Core authorization component that evaluates user permissions against resources using hierarchical wildcards (`*`, `>`, `?*`, `?>`). |
| **Auth Handler**                | Abstract base class for authentication strategies. Implementations include OAuth2, Token, OpenWebUI, and Development-only handlers. |
| **Base Event**                  | Foundation class for all events in the system. Provides automatic type registration, serialization, and metadata handling.          |
| **Base Dispatcher**             | Core workflow execution engine that processes events through registered handlers in a stateless, distributed manner.                |
| **Configuration Management**    | Pydantic-based system for managing service configurations with environment variable integration and validation.                     |
| **Event-Driven Architecture**   | Core architectural pattern where all communication happens via events, enabling scalable, stateless distributed systems.            |
| **Event Store**                 | Persistence layer for events, providing replay capabilities and audit trails using NATS JetStream.                                  |
| **Hierarchical Permissions**    | Permission system using dot notation (e.g., `aihub.user.agent.class.id`) with wildcard support for flexible access control.         |
| **Identity Provider**           | Strategy pattern implementation for user authentication supporting multiple backends (Azure AD, Token, Development).                |
| **Internationalization (i18n)** | Multi-language support system with YAML-based translations and dynamic locale switching.                                            |
| **Locale Handler**              | Core i18n component that manages language-specific content extraction and fallback mechanisms.                                      |
| **Locale String**               | Multi-language string representation supporting dynamic locale resolution and default fallbacks.                                    |
| **NATS Integration**            | Message bus integration providing event publishing, subscription, and stream management for distributed communication.              |
| **Persistence Layer**           | Database abstraction layer supporting multiple storage backends (MongoDB, Cosmos, Redis) with entity management.                    |
| **Resource Config**             | Pydantic models for configuring AI/ML services including LLMs, embeddings, and other generative AI resources.                       |
| **Topic Manager**               | NATS subject/topic routing system that manages message distribution across services and workflow components.                        |
| **User Identity**               | Core user representation including roles, permissions, and authentication state management.                                         |
| **Vector Store**                | Abstraction for vector database operations supporting multiple backends (Milvus, Azure AI Search) for RAG implementations.          |
| **Workflow Orchestration**      | Event-driven workflow execution system enabling complex business processes through distributed state management.                    |
