# AIHub Infrastructure as Code (IaC)

This repository contains the Infrastructure as Code implementation for the AIHub platform, 
using Pulumi with Python to define and manage Azure cloud resources.

## Core Architecture

The IaC code follows a modular, component-based architecture designed to be extensible, maintainable, 
and to promote reusability. The following core architectural principles shape the design:

### 1. Component-Based Design

The infrastructure is organized into logical components, each represented as a Pulumi `ComponentResource`. 
Each component encapsulates its internal resources and dependencies while exposing well-defined inputs and outputs. 
This approach enables components to be composed into larger infrastructures while maintaining a clear separation of 
concerns, making the code easier to understand and maintain. Components handle their own dependency graph internally, 
reducing the need for manual dependency management at higher levels.

### 2. Provider Pattern

The codebase implements a provider pattern to abstract service creation and dependency injection. 
The `NetworkProvider` manages network-related resources and naming conventions, 
`IdentityProvider` handles Azure managed identities and role assignments, 
`StorageResourceFactory` creates and configures storage resources, and 
`WebAppCreator` standardizes web application deployment. 
These providers deliver a consistent approach to resource creation across components and reduce code duplication. 
Providers act as factories for common resource types, ensuring consistency and reducing boilerplate.

### 3. Configuration Management System

The configuration system is a core strength of the architecture, built on a layered approach with Pydantic 
models and environment variables:

At the foundation are `Settings` classes (e.g., `ProjectSettings`, `OAuthSettings`, `PostgresAuthSettings`) that directly 
map environment variables to typed properties. These classes handle the raw loading of configuration from environment 
files and provide basic validation. They focus on a specific domain of configuration (project details, authentication, etc.) 
and typically have no dependencies on other settings.

Above the Settings layer are `Config` classes (e.g., `ApiConfig`, `PhoenixConfig`, `WebUIConfig`) which compose and 
transform settings into the specific configuration needed for infrastructure components. These Config classes 
incorporate business logic for computing derived values, setting defaults, and validating relationships between 
configuration parameters. They typically consume multiple Settings classes and expose a unified configuration 
interface to components.

This layered approach provides clear separation between raw environment variables and the business logic that 
transforms them into usable configuration. The `from_env()` static factory method pattern enables comprehensive 
configuration construction from environment variables with domain-specific defaulting logic.

## Directory Structure

```
aihub_iac/
├── azure/
│   ├── constants/                 # Common constants (resource types, roles)
│   ├── modules/                   # Core infrastructure components
│   │   ├── agent/                 # Agent container deployment
│   │   ├── api/                   # API service resources
│   │   ├── bot/                   # Bot service resources
│   │   ├── dagster/               # Dagster orchestration
│   │   ├── nats/                  # NATS messaging infrastructure
│   │   ├── network/               # Network infrastructure
│   │   ├── phoenix/               # Phoenix application
│   │   ├── stores/                # Data storage resources
│   │   └── webui/                 # Web UI components
│   ├── providers/                 # Service provider abstractions
│   ├── resources/                 # Common resource definitions
│   └── settings/                  # Configuration settings
```
