# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.220.0] - 2025-07-11 - Enhanced SharePoint Integration Clarity and Data Lake Observability

### Refactor
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).
- 🔄 **Updated SharePoint Asset Factories**: Renamed the `sharepoint_files_to_data_lake_files_factory` function and its internal parameters to align with the new, standardized naming conventions, enhancing code clarity.
- 📄 **Refined SharePoint IO Manager**: Updated the SharePoint IO Manager to use the new `share_point_client` resource name consistently, improving maintainability.
- 🧼 **Cleaned Up SharePoint Utilities**: Standardized naming within metadata utility functions related to SharePoint files, contributing to a more coherent codebase.

### Changed
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.

---



## [v0.219.0] - 2025-07-11 - Internal Workflow Automation Adjustment

### Removed
- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.

---



## [v0.218.0] - 2025-07-11 - Enhanced API Configuration and Extensibility

### Added
- ✨ **Enabled custom environment variable configuration for API services:** This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.

---



## [v0.217.0] - 2025-07-10 - Automated Agent API Integration and Event Inheritance

### Added
- ✨ **Automated Agent API Endpoint Generation**: Introduced a new `AgentDiscoveryService` that dynamically discovers agents and registers corresponding API endpoints for their start events. This significantly streamlines the integration of new agents with the API, eliminating the need for manual endpoint configuration.
- 🦾 **Event Inheritance Tracking**: `EventSpecs` now include an `event_parents` field, providing a hierarchical view of event types. This new metadata enhances dynamic model generation and event handling capabilities.
- 📄 **EventSpecs Creation Helper**: Added a convenient `EventSpecs.from_event_class` method to simplify and standardize the generation of event specifications from event classes.
- 🔑 **Role Provisioning for API Tokens**: The `generate_api_token` script has been enhanced to automatically create specified roles if they do not already exist, improving the initial setup experience for new environments.

### Changed
- ⚡️ **Flexible Agent Event Dispatch**: The `AgentService.send_event` method now universally accepts any `BaseEvent` as input, offering greater flexibility in initiating diverse agent interactions.
- 🔄 **Dynamic Agent Endpoint Management**: Transitioned the agent event endpoint management from static, hardcoded definitions in `AgentController` to a dynamic, discovery-driven approach powered by the new `AgentDiscoveryService`.
- 📚 **Event Model Creation Encapsulation**: Internal methods within `EventModelCreationService` have been refactored for improved code organization and clearer encapsulation.
- 🏗️ **API State Access for Services**: The `ApiRunner` now stores the `AgentController` and API application instance directly in FastAPI's state, enabling seamless access for new services like `AgentDiscoveryService`.
- ⚠️ **Refined Unauthorized Access Handling**: Introduced a specific HTTP exception to provide clearer and more precise error responses when a user lacks authorization to view a particular thread.

### Refactor
- 🧹 **Unified Event Specification Creation**: Standardized the process of creating `EventSpecs` across `AgentRunner` and `SimulatedAgentBotTestRunner` to consistently use the new `EventSpecs.from_event_class` helper.
- 🏷️ **Agent Configuration Entity Renaming**: The `AgentConfig` embedded document within the persistence layer was renamed to `AgentConfigEntity` for improved naming consistency across the codebase.

### Removed
- 🗑️ **Static Agent Event Endpoint Configuration**: Eliminated the manual and hardcoded API endpoint generation logic for agent events from `AgentController` and related playground examples, fully transitioning to the dynamic agent discovery service.

---



## [v0.216.0] - 2025-07-08 - Foundational Polish: Modernizing Python Syntax and Enhancing Type Safety

### Added
- ✨ **Deprecated `AgentConfig` Fields:** Introduced deprecation warnings for `color`, `voice`, and `system_prompt` fields within `AgentConfig`, guiding users to define these properties directly in agent subclasses for better customization.

### Changed
- 🔄 **Standardized Datetime Handling:** Updated datetime operations to consistently use timezone-aware UTC for improved time-based accuracy and consistency across the platform.
- 🔄 **Improved Subprocess Execution:** Enhanced `subprocess.run` calls in internal scripts for more robust and secure execution, particularly within bot setup processes.
- 🔄 **`jambo` Library Update:** Upgraded the `jambo` schema conversion library to `v0.4.0`, bringing internal improvements for dynamic model creation and API event handling.
- 🔄 **Refined Docstrings and Comments:** Various docstrings and inline comments across the codebase were updated for greater clarity and precision, especially concerning complex components like dispatchers and service methods.

### Fixed
- 🐛 **Clarified Error Messages:** Enhanced error messages in several API endpoints (e.g., thread and role management) to provide more informative feedback to users.
- 🐛 **Robust Type Parsing:** Corrected and improved the internal parsing of type annotations for event and parameter extraction, ensuring more reliable and accurate workflow dispatching.

### Refactor
- 🧹 **Type Hint Modernization:** Performed a comprehensive refactoring across the entire codebase to leverage native Python type hints (e.g., `list`, `dict`, `set`, `tuple`, `X | None`) for improved readability, maintainability, and static analysis.
- 🧹 **Linting and Formatting Overhaul:** Consolidated and enhanced code quality checks by deprecating `isort` and configuring `ruff` to handle import sorting and enforce stricter linting rules.

---



## [v0.215.0] - 2025-07-08 - Granular Access Control and Enhanced User Management

### Security
- 🔑 **Introduced Hierarchical Role-Based Access Control (RBAC)**: Implemented a new, comprehensive RBAC system that supports hierarchical access rules with granular control over services, agents, and processes.
- 🔐 **Enforced Granular Endpoint Permissions**: All major API endpoints across agents, evaluations, events, files, i18n, knowledge, OpenAI, threads, and tokens now utilize the new RBAC, ensuring fine-grained access based on user roles and specific resource permissions.
- 🔒 **Restricted Knowledge Base Access**: Access to knowledge bases, including databases, documents, and nodes, is now limited to users with administrative privileges.
- 🛡️ **Enhanced Thread Management Security**: Improved security checks for thread creation, viewing, and modification, including verifying user and agent access, and preventing unauthorized changes to process-owned threads.
- 👁️ **Refined Event Visibility**: The general event retrieval endpoint has been removed, and access to thread-specific events and event timeseries is now strictly controlled by user permissions.

### Added
- 🗄️ **Role Management API**: Introduced a new API (`/roles`) enabling administrators to create, list, retrieve, update, and delete custom roles with associated hierarchical access rules.
- 📋 **User Management API for Administrators**: New API endpoints (`/users`, `/users/{user_id}`) provide administrators with the ability to list all users and retrieve detailed information for specific users, including their assigned roles and granular access levels across services, agents, and processes.
- 👤 **Minimal User DTO**: Introduced a lightweight `MinimalUserDTO` for contexts where only essential user information is required, improving API efficiency.
- 📊 **Paginated User Listing**: Administrators can now retrieve a paginated list of all users via the API, enhancing user management capabilities.
- 👑 **User Access Details in User Profile**: Users can now view their specific access levels for different services, agents, and processes directly in their profile (visible to admins).
- 💬 **Process-Associated Thread Metadata**: Added `process_class`, `process_id`, and `process_walkthrough_id` to `ThreadDTO` for better contextualization of threads initiated by processes.
- 🤖 **Agent Metadata in Model Details**: `agent_class` and `agent_id` fields were added to `ModelDetails` to provide clearer context for AI-Hub agents exposed as OpenAI models.
- ⌛ **User-Friendly Time Ago Display**: Implemented a new composable for displaying relative time (e.g., "Last hour", "Last week") with severity indicators in the UI.
- 💥 **Global HTTP Error Toasts**: Configured the frontend client to display informative toast messages for HTTP response errors, improving user feedback.
- 🛠️ **New UI Components for Role Management**: Introduced dedicated components for creating, editing, and displaying roles, enhancing the administrative user experience.
- 👨‍💻 **New UI Components for User Management**: Added new components to list users and display their detailed access information for administrators.

### Changed
- 🔄 **Updated Role Naming Convention**: The `AllAgents` role has been renamed to `TestOnlyFullAdminAccess` for clearer intent and consistency with the new access control model.
- 🛣️ **Streamlined Frontend Routing**: All previously "admin" specific routes (e.g., `/admin/agents`) have been unified under a `/service/` prefix, aligning with the new granular access control model where permissions define access rather than a fixed "admin" route.
- 🌐 **Refined Internationalization Endpoint Access**: The `/i18n/my-locale` endpoint now requires a general user permission.
- 📂 **File Access Endpoints**: Access to logged-in file URLs is now managed by the new permission system.
- 📈 **Dashboard Event Labels**: Improved clarity of labels for various event types displayed in dashboard widgets.
- 🎨 **Service Selection Layout**: Adjusted the layout of the service selection component for improved visual consistency.

### Refactor
- 🧹 **Centralized Access Control Logic**: All access validation logic has been consolidated into the new `AccessChecker` class within `aihub_lib`, removing redundant checks from individual controllers and DTOs.
- ⚙️ **Refined Controller Initialization**: The `Controller` base class now uses a more flexible `additionally_required_permission` parameter instead of a simple `is_admin_only` flag.
- 🚀 **Optimized Service Layer Dependencies**: Removed direct `IdentityProvider` dependencies from several service methods, pushing identity retrieval and access checks to higher layers or internal `UserEntity` management.
- 📦 **Consolidated User DTOs**: Simplified the user data transfer object hierarchy by replacing `MyUserDTO` with a more comprehensive `UserDTO` that includes roles and dashboard configurations, and introducing `MinimalUserDTO` for basic user representation.
- 🧪 **Improved Testing Infrastructure**: Enhanced test client fixtures and introduced dedicated mock fixtures for `RoleEntity` and `UserEntity` methods, making authentication and data-related tests more robust and easier to set up.
- ⏱️ **Standardized Caching Durations**: Updated `staleTime` configurations across multiple composables to use `date-fns` `minutesToMilliseconds` for better readability and consistency.

---



## [v0.214.0] - 2025-07-08 - Streamlined Event Model Handling and Enhanced Developer Experience

### Added
- ✨ **New Event Model Creation Service**: Introduced `EventModelCreationService` to provide a unified and robust mechanism for generating Pydantic models from event classes or JSON schemas, enabling dynamic and consistent API model definitions.
- 🧪 **Comprehensive Event Model Tests**: Added extensive test suites for the new `EventModelCreationService`, including complex nested models, union types, and list structures, to ensure the reliability and correctness of dynamically generated event models.
- 🛠️ **Standardized IDE Inspection Profiles**: Integrated new IntelliJ IDEA inspection profiles and scopes (`Core.xml`, `ExcludeJambo.xml`) to enforce consistent code quality standards and improve developer experience.
- 📦 **Jambo Dependency**: Introduced `jambo` as a new dependency to support advanced JSON schema to Pydantic model conversion within the new event model creation service.

### Changed
- 🚀 **CI/CD Workflow Enhancements**: Updated the `analyze-test-pr.yml` GitHub Actions workflow to include SSH setup and cleanup steps, facilitating secure interactions with private Git repositories during testing.
- 🔄 **API Endpoint and Test Integration**: Migrated existing agent API endpoints and their associated tests to utilize the new `EventModelCreationService`, ensuring all model generation leverages the centralized logic.

### Removed
- 🗑️ **Deprecated Event Model Functions**: Removed the standalone `create_input_model` and `create_output_model` functions, as their functionality has been absorbed and improved by the new `EventModelCreationService`.

---



## [v0.213.0] - 2025-07-07 - New Retrieval Agent for Focused Data Access

### Added
- ✨ **Introduced `RetrievalAgent`**: A new, specialized agent designed to streamline information retrieval from knowledge bases. This agent focuses solely on fetching and organizing relevant context, enabling more flexible and modular Retrieval-Augmented Generation (RAG) workflows.
- 📄 **Dedicated Configuration for Retrieval Agent**: Added `RetrievalAgentConfig` to provide comprehensive configuration options for customizing retrieval behavior, including specifying embedding models, vector stores, and various node retrieval strategies.
- ⚡️ **New Event Types for Retrieval Workflows**: Implemented `QuestionStartEvent` for clear initiation of retrieval queries and `RetrievalResponseEvent` to encapsulate the retrieved and ordered context, facilitating seamless integration with subsequent processing steps.
- 🧪 **Comprehensive Test Coverage for `RetrievalAgent`**: Included a full suite of BDD (Behavior-Driven Development) tests to ensure the robust and reliable operation of the new `RetrievalAgent`, validating its ability to accurately retrieve and combine relevant documents.

---



## [v0.212.0] - 2025-07-03 - Flexible OpenAI Authentication & Resource Management

### Added
- ✨ **Flexible OpenAI Resource Authentication**: Introduced the ability to authenticate with Azure OpenAI resources using either an API Key or Azure AD credentials, providing greater flexibility in deployment environments.
- 🔑 **Centralized OpenAI API Key Configuration**: Added a new base `OpenaiResourceSettings` class for consistent management of OpenAI API keys across different services and environments.

### Changed
- 🔄 **Generalized Resource Configuration**: Extended the base `ResourceConfig` to include an optional `api_key` field, enabling API key authentication for all derived generative AI resource configurations.
- 🚀 **Improved Azure OpenAI Client Initialization**: Updated the Azure OpenAI client instantiation logic to intelligently use either an API key or Azure AD token provider based on the provided configuration, simplifying setup.
- 📄 **Updated Development Playground Models**: Renamed the `o1-mini` model to `gpt-4o-mini` in the development environment configuration for improved clarity and alignment with current model names.

### Refactor
- 🧹 **Streamlined API Key Definitions**: Removed redundant `api_key` fields from specific model configurations (e.g., chat LLMs, embedding LLMs, image models) as they are now managed centrally by the generalized `ResourceConfig`.

---



## [v0.211.0] - 2025-07-03 - Enhanced RAG Context and Workflow Streamlining

### Added
- ✨ **Introduced Parent Summary Node Retrieval:** The RAG Agent can now retrieve relevant parent summary nodes from the knowledge base, providing richer context and improving the quality of generated answers.
- ⚙️ **Configurable Parent Summary Retrieval:** Added a new `retrieve_summaries` configuration option to the `RetrieveStepConfig` for RAG agents, allowing users to specify the maximum hierarchical levels for parent summary retrieval.
- 🚀 **Improved Agent Step Metadata:** Enhanced the `@step()` decorator in the RAG Agent to include explicit `name` and `description` fields, improving clarity and introspection for agent workflows.

### Changed
- ⚡️ **Streamlined LLM Response Workflow:** The RAG Agent's LLM response step now directly signals the completion of the workflow, simplifying internal event handling and removing the need for a separate `StopEvent`.

---



## [v0.210.0] - 2025-07-03 - SharePoint Ingestion and Pipeline Structure Enhancements

### Added
- ✨ **Introduced SharePoint Integration**: A comprehensive new set of assets, operations, and resources for ingesting documents directly from SharePoint into the data lake. This includes robust capabilities for fetching, transforming, and managing files, ensuring your knowledge base is kept up-to-date with SharePoint content.
- 🚀 **New Azure OpenAI Model Configurations**: Added dedicated configuration classes (`EmbeddingModelConfig` and `LanguageModelConfig`) to simplify the setup and management of Azure OpenAI embedding and language models, enabling clearer model definitions.
- ⚙️ **Flexible Pipeline Scheduling**: Enhanced scheduling utilities to allow for more granular control over pipeline execution times, including a new `daily_schedule_at` function for precise timing.
- 📄 **SharePoint IO Manager**: Implemented a new I/O manager specifically for SharePoint, streamlining the process of loading files from SharePoint into pipeline assets.
- 📊 **SharePoint Metadata Utilities**: Introduced helper functions to generate rich metadata tables for SharePoint files, improving observability and insights into ingested data.

### Refactor
- 🧹 **Pipeline Asset Reorganization**: Restructured the pipeline's asset factories into more logical subdirectories (`data_lake_to_vector_store` and `share_point_to_data_lake`) to improve modularity, readability, and maintainability.
- 🔄 **Centralized SharePoint Utilities**: Consolidated SharePoint-related operations, resources, and data types into dedicated modules for better code organization and clarity, preparing for future expansions.

---



## [v0.209.0] - 2025-07-03 - Automated PR Readiness Checks with Claude Integration

### Added
- 🦾 **Automated Subproject PR Readiness:** Introduced a new intelligent script that automatically identifies the root of a subproject based on edited files and executes `make pr-ready`, standardizing pre-PR checks and ensuring code quality.
- ⚡️ **Claude Post-Edit Automation:** Configured Claude to automatically trigger the new PR readiness script immediately after any file modifications (Write, Edit, MultiEdit), providing instant feedback on code quality and readiness within the development workflow.

---



## [v0.208.0] - 2025-07-03 - Refined Context Metadata for Generative AI

### Changed
- 📄 **Streamlined RAG Context Metadata**: The **`document_title`** is now explicitly included in the metadata when combining nodes for Retrieval Augmented Generation (RAG) contexts, providing more direct document identification within prompts.
- 🗑️ **Consolidated Node Metadata Fields**: To simplify and optimize the context provided to generative AI models, the `namespace`, `type`, and `content_type` fields are no longer emitted as part of the combined node metadata.

---



## [v0.207.0] - 2025-07-01 - Streamlined Release Tagging

### Removed
- 🗑️ **Streamlined Release Tagging**: Removed the redundant step of deleting existing Git tags in the CI/CD workflow, simplifying the release automation process.

---



## [v0.206.0] - 2025-07-01 - Core System Refinement: Pydantic V2 and Type Clarity

### Refactor
- 🧹 **Pydantic Model Modernization**: Migrated numerous Pydantic models across `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, and `aihub_pipeline` to leverage Pydantic V2's `Annotated` type hinting. This significantly improves type safety, explicit default value handling, and prepares the codebase for future Pydantic enhancements.
- ⚙️ **Explicit Default Values**: Updated all `Optional` fields and collections (lists, dictionaries, sets) in Pydantic models to use explicit default values (e.g., `= None`, `= []`, `= {}`, `= set()`) instead of `default_factory`. This enhances code readability and consistency.

### Changed
- 🔄 **Platform Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to `v0.206.0`, ensuring a unified and consistent release across the entire platform.
- ⚠️ **Deprecated AgentConfig Fields**: Marked `color`, `voice`, and `system_prompt` fields in `AgentConfig` as deprecated, encouraging subclasses to define these properties directly for better customization and reduced coupling.
- 📄 **Streamlined Docling and OpenWebUI Configurations**: Refined default value assignments for `DOCLING_FROM_FORMATS`, `DOCLING_TO_FORMATS` in `DoclingConfig` and various `Pipe.Valves`/`Action.Valves` settings in `webui_pipelines` for clearer and more direct configuration.

---



## [v0.205.0] - 2025-07-01 - Core System Version Synchronization

### Changed
- 🔄 **Platform Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to `v0.205.0`, ensuring a unified and consistent release across the entire platform.

---



## [v0.204.0] - 2025-07-01 - Streamlined Release Automation and Core Service Alignment

### Changed
- 🔄 **Core Service Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to version `v0.204.0`, ensuring consistent and current builds across the platform.
- ⚡️ **Robust Changelog Generation**: The automated changelog generation process in the CI/CD pipeline is now more resilient; the workflow will continue even if changelog generation encounters an error, and the changelog file will only be committed if its generation was successful.
- 📝 **Updated `llm` CLI Syntax**: The `llm keys set` command used in the release workflow now explicitly requires the `--value` flag (e.g., `llm keys set gemini --value "$API_KEY"`), aligning with recent updates to the `llm` tool.

### Refactor
- 🧹 **Optimized CI/CD Workflow**: Removed redundant Poetry caching from the Python setup step in the GitHub Actions workflow, streamlining environment setup.
- ⚙️ **Script Robustness**: Improved the internal logic of the changelog generation script by adding specific error handling for LLM calls, preventing a complete script failure if the language model service is unreachable or returns an error.

---



## [v0.203.0] - 2025-06-30 - AI-Powered Release Automation

### Added
- ✨ **Automated Changelog Generation:** Introduced a new CI/CD workflow and accompanying scripts (`generate-changelog.sh`, `changelog-prompt.md`) to automatically generate changelog entries using an LLM based on git diffs between tags.
- 🚀 **AI-Powered Release Notes:** Integrated `llm` and `llm-gemini` into the release workflow, enabling the use of Large Language Models to summarize code changes into human-readable changelog entries.
- 📄 **Changelog Prompt Template:** Added a dedicated Markdown file (`changelog-prompt.md`) to define the instructions and format for LLM-generated changelog entries, ensuring consistent output.
- ⚙️ **Makefile Integration for Changelog:** A new `changelog` target has been added to the `Makefile` to simplify the execution of the changelog generation process.

### Changed
- 🔄 **Enhanced Release Workflow:** The `add-tag.yml` GitHub Actions workflow has been significantly restructured and renamed to "Auto Tag, Gen-Changelog & Release," encompassing version bumping, changelog generation, and final tag/commit operations for a more robust release pipeline.
- ⚡️ **Refined Versioning and Tagging Logic:** Updated the CI/CD's commit and tagging process to amend the version update commit with the newly generated changelog entry, ensuring that release tags accurately reflect the complete changes.
- 🧹 **Streamlined Python/Poetry Setup in CI:** Optimized the Python and Poetry installation and caching steps in GitHub Actions for improved efficiency and dependency management during the build process.

---



## [v0.202.0] - 2025-06-30 - Revamped User Identity and API Authentication

### Added
- ✨ **Introduced `IdentityProvider` Abstraction**: A new, flexible `IdentityProvider` interface and its concrete implementations (`AzureIdentityProvider`, `TokenIdentityProvider`, `DangerousDevelopmentOnlyIdentityProvider`) have been added to centralize and standardize user information retrieval across the platform. This allows for easier integration of various authentication sources.
- ⚡️ **Unauthenticated Health Endpoint**: The `/health` endpoint no longer requires authentication, making it easier to monitor service availability in secure environments.
- 📄 **User Entity Email Lookup**: Added a new `by_email` class method to `UserEntity` for direct retrieval of user entities by their email address, improving data access efficiency.

### Changed
- 🔄 **Refined Image Description Prompts**: Updated prompts for figure description generation to ensure that descriptions are solely based on visual content and are not influenced by surrounding document context, leading to more factual and accurate alt-text.
- 🔌 **Explicit Authentication Handler Injection**: All API and Bot controllers now explicitly require an `AuthHandler` instance in their constructors, enforcing clearer dependency management and configuration.
- 🤖 **Azure Bot API Path**: The API path for the Azure Bot's bot-in-the-loop functionality has been updated to `/bearer_token/v1/bot-in-the-loop/response` for better alignment with the token-based authentication scheme.
- 🚀 **Azure Bot Setup Parameters**: Renamed `--api-path` and `--api-url` to `--token-path` and `--token-url` respectively in the Azure Bot setup script for clearer naming conventions.

### Fixed
- 🐛 **Robust Figure Description Generation**: Implemented enhanced error handling for the figure description generation process in the data pipeline, specifically addressing `BadRequestError` (e.g., content safety filter issues) by retrying without surrounding text to ensure documents are processed successfully.

### Refactor
- 🧹 **Centralized User Identity Model**: The `AuthenticatedUser` model has been deprecated and replaced across the codebase with the new `UserIdentity` model, which now handles user attributes like `id` (formerly `oid`) and `email` (formerly `preferred_username`).
- ⚙️ **Streamlined Auth Handlers**: Authentication handlers (`OAuth2AuthHandler`, `TokenAuthHandler`, `OpenWebuiAuthHandler`) have been refactored to leverage the new `IdentityProvider` abstraction, simplifying their internal logic and promoting modularity.
- 🚨 **Renamed Development-Only Auth Components**: The `NoAuthHandler` and `NoAuthConfig` have been renamed to `DangerousDevelopmentOnlyAuthHandler` and `DangerousDevelopmentOnlyAuthConfig` respectively, providing a clearer warning about their intended use for development and testing only.
- 🗑️ **Removed Redundant Identity Providers (API)**: The previously internal user information providers (`BaseUserInformationProvider`, `MultiStrategyUserInformationProvider`, `ApiTokenUserInformationProvider`, `AzureUserInformationProvider`, `DevUserInformationProvider`) from the `aihub_api` module have been removed, as their functionality is now centralized and provided by the new `IdentityProvider` layer in `aihub_lib`.
- 📄 **Consolidated Frontend User Properties**: Frontend components (`Chat/Message.vue`, `Chat/Thread.vue`, `Event/Display/UserMessageEvent.vue`) have been updated to use the `email` property instead of `preferredUsername` for user display, aligning with the backend `UserIdentity` model.

---



## [v0.201.0] - 2025-06-30 - Next-Gen Identity: A Core Authentication Rearchitecture

### Refactor
- 🔄 **Core Identity System Rearchitected**: Replaced the legacy `AuthenticatedUser` model with a new, more robust `UserIdentity` model, establishing a clearer and more extensible foundation for user representation across the system.
- 🧹 **Unified Identity Providers**: Introduced a standardized `IdentityProvider` interface and migrated existing user information retrieval logic into concrete implementations (e.g., `AzureIdentityProvider`, `TokenIdentityProvider`), centralizing how user details are fetched from various sources.
- 🔐 **Enhanced Authentication Handlers**: Updated all authentication handlers (`OAuth2AuthHandler`, `TokenAuthHandler`, `OpenWebuiAuthHandler`) to leverage the new identity provider pattern, ensuring consistent user identity resolution and improving security.
- ⚡️ **Improved Development-Only Auth**: Renamed `NoAuthHandler` to `DangerousDevelopmentOnlyAuthHandler` and integrated it with the new identity provider system, clearly signaling its purpose as a development-only tool and emphasizing its security implications.
- ⚙️ **Refined Controller Initialization**: Standardized how authentication handlers are injected into API and Bot controllers, making `AuthHandler` a mandatory keyword argument for clearer dependency management and increased type safety.
- 📄 **Synchronized User Attributes**: Updated all internal and external references from `user.oid` to `user.id` and `user.preferred_username` to `user.email` to align with the new `UserIdentity` model.

### Added
- ✨ **User Lookup by Email**: Introduced a new `UserEntity.by_email` method, enabling direct retrieval of user entities from the database using their email address.

### Changed
- 📝 **CLI Parameter Renaming**: Renamed command-line interface parameters for Azure Bot setup from `--api-path` to `--token-path` and `--api-url` to `--token-url` for improved clarity and consistency with the new authentication flows.

### Improved
- 🚀 **Unauthenticated Health Checks**: Removed the authentication requirement for the `/health` endpoint, allowing for simpler and more robust health monitoring of services without needing a valid user context.

---



## [v0.200.0] - 2025-06-30 - Introducing Process Orchestration and Core Workflow Refinements

### Added
- ✨ **Process Orchestration Microservice (`aihub_process`)**: A new dedicated microservice is introduced, enabling the creation and management of complex, multi-entity workflows that orchestrate AI agents, human tasks, and external programs.
- 🚀 **Generalized Workflow Abstractions**: Core concepts like `DispatchableWorkflow` (base for agents and processes) and `BaseDispatcher` are added to `aihub_lib`, providing a robust, extensible framework for event-driven execution across the platform.
- ⚙️ **Process-Specific Eventing System**: A comprehensive set of new NATS event types (`WorkEvent`, `WorkRequestEvent`, `ProcessStartEvent`, `ProcessStopEvent`, `ProcessExceptionEvent`), along with specialized topic managers and subscribers, are added to facilitate seamless communication within process workflows.
- 📚 **Dedicated Process Event Persistence**: Introduced `PersistedProcessEventEntity` for reliable storage and retrieval of all process-related events, crucial for auditing, debugging, and visualization of long-running workflows.
- 🛠️ **Process Configuration and Step Definition**: New `ProcessConfig` and the `@process_step` decorator are added, allowing developers to define process-level settings and structure process logic, clearly articulating interactions with various entities.
- 🤝 **Entity Delegators**: Developed specialized delegators for agents, humans, and external programs, which act as intelligent bridges, translating generic process work requests into entity-specific actions and converting entity outputs back into process-consumable work events.
- 🧪 **Streamlined Process Testing Infrastructure**: New `ProcessRunner` and `ProcessTestRunner` classes are provided to simplify the development, testing, and deployment of new process definitions.
- 🌎 **Extended Internationalization Support**: New localization strings have been integrated to support process-specific events and concepts across multiple languages.
- 💡 **Developer Convenience Run Configurations**: Added new IntelliJ IDEA run configurations to easily launch GPU infrastructure and execute process-specific tests, enhancing the local development experience.

### Changed
- 🔄 **Unified Workflow Architecture**: Existing `aihub_agent` and related `aihub_lib` components have been refactored to align with the new generalized `DispatchableWorkflow` and `BaseDispatcher` abstractions, improving modularity and consistency across agent and process implementations.
- 📄 **Enhanced Thread Management**: The `ThreadEntity` now includes fields (`process_class`, `process_id`, `process_walkthrough_id`) to explicitly link conversation threads with specific process executions, enabling better tracking and context.
- 🧰 **Refined NATS Infrastructure Components**: Core NATS components such as `StreamManager`, `AbstractPublisher`, and `AbstractSubscriber` within `aihub_lib` are now more generic and flexible, supporting diverse eventing patterns for both agent and process workflows.
- ⚠️ **Agent Configuration Field Deprecation**: Certain generic fields (`color`, `voice`, `system_prompt`) in `AgentConfig` have been marked as deprecated, encouraging more specialized and customizable configurations within agent subclasses.
- 🏷️ **Improved Localization Metadata**: `LocaleString` fields now include explicit `Annotated` types and descriptions, enhancing clarity and maintainability for internationalization efforts.
- 🏗️ **CI/CD Pipeline Integration**: The continuous integration and delivery (CI/CD) pipelines and local development Makefiles have been updated to seamlessly incorporate the new `aihub_process` module for linting, testing, and tagging.
- 📊 **Synchronized Frontend SDK**: The frontend SDK has been updated to reflect all backend API changes, including new event schemas, refined `LocaleString` handling, and updated metadata structures for ingested documents and nodes.

### Fixed
- 🐛 **Corrected API Type Checking**: Resolved a configuration error in the `aihub_api` Makefile where type checks were incorrectly applied to the `aihub_agent` module.
- 🔑 **Optimized Database Indexing**: Added unique and performance-enhancing indexes to `ConversationEntity`, `PathEntity`, and `UserEntity` for improved data integrity and faster query execution.
- 📦 **Resolved Module Source Root Configuration**: Corrected the `.idea/aihub_lib.iml` file to accurately define `aihub_lib` as a source root, improving project setup and dependency resolution.

---



## [v0.199.0] - 2025-06-27 - Streamlined Document Ingestion: Introducing Docling and AI-Powered Figure Descriptions

### Added
- ✨ **New Docling Document Loader**: Introduced `DoclingLoader` to support advanced document processing via the Docling service, enabling robust conversion of various document formats to Markdown, including automated extraction and handling of figures and tables.
- 🚀 **Docling API Integration**: Implemented `DoclingAccess` for seamless interaction with the Docling API, facilitating comprehensive document conversion capabilities such as OCR, table extraction, and embedded image handling.
- 🛠️ **Docling Service Configuration**: Added `DoclingConfig` to centralize and manage all configurable parameters for the new Docling service integration, including API endpoints, supported formats, and processing options.
- 🖼️ **Automated Figure Description Generation**: Introduced the `generate_figure_descriptions` operation to automatically create detailed, context-aware alt text for figures in documents using a vision language model, significantly enhancing document accessibility and searchability.

### Changed
- 🔄 **Enhanced Document Intelligence Loader**: Improved `DocumentIntelligenceLoader` to directly handle figure extraction and table reformatting (converting HTML tables to Markdown and tagging them), simplifying the document processing pipeline by reducing external dependencies for these steps.
- 💬 **Prompt Template Alignment**: Updated `figure_description_generator` prompts across all supported languages (`de`, `en`, `fr`, `it`) to utilize `{% chat role="..." %}` syntax and `RichPromptTemplate` for more flexible and powerful prompt engineering.
- ⚙️ **Configurable Document Parsers**: Introduced `LoaderType` and a `loader_type` parameter in `DocumentParserResource`, enabling explicit selection of document parsing backends (Docling, Document Intelligence, or both) and dynamic loading of supported file extensions from their respective configurations.
- 📄 **Streamlined Document Parsing**: Updated `parse_document_from_data_lake` to directly output `RefDocDocument` and pass figure directory information to the document loaders, simplifying subsequent pipeline steps.
- 📄 **Simplified Figure Metadata**: Removed the `figure_url` field from `FigureMetadata` as figures are now managed via local paths within the document processing pipeline.
- ⚙️ **Document Intelligence Configuration**: Added `DOCUMENTINTELLIGENCE_EXTENSIONS` to `DocumentIntelligenceConfig` to explicitly define supported file types for the Document Intelligence service.
- 🧪 **Playground Document Parser Default**: Updated the playground environment to default to `DoclingLoader` for document parsing, demonstrating the new configurable loader types.

### Refactor
- 🧹 **Streamlined Document Ingestion Pipeline**: Refactored the document ingestion process within `documents_factory` by removing intermediate figure and table handling operations, consolidating figure description generation into a new dedicated operation, and simplifying the overall data flow.
- 🧹 **Path Utility Relocation**: Moved and renamed `path_utils.py` from `aihub_pipeline` to `aihub_lib/generative_ai/utils` and generalized `create_data_lake_figures_folder_name` to `create_figures_folder_name` for broader utility across document loaders.
- 🧹 **Figure Deletion Path Update**: Updated `delete_figures_for_many_ref_doc` to use the relocated and generalized path utility for figure folder name generation.

### Removed
- 🗑️ **Deprecated Document Conversion Operations**: Eliminated `doc_with_figures_to_ref_doc`, `inject_figures`, `reformat_tables`, and `save_figures_to_data_lake` operations. Their functionalities have been integrated directly into the new document loaders and the `generate_figure_descriptions` op for a more efficient and consolidated pipeline.

---



## [v0.198.0] - 2025-06-24 - Enhanced Embedding Content Preparation

### Changed
- ✨ **Improved Node Embedding:** The `embed_nodes` operation now utilizes `get_content(metadata_mode=MetadataMode.EMBED)` for extracting node content, ensuring that vector embeddings are generated from a more comprehensive and contextually relevant representation of the text, potentially including optimized metadata.

---



## [v0.197.0] - 2025-06-24 - Azure Data Lake Storage Integration

### Added
- ✨ **Introduced new Azure roles** for Data Lake Storage, including `STORAGE_BLOB_DATA_READER` and `STORAGE_BLOB_DELEGATOR`, to facilitate enhanced access control.
- 📝 **Defined a default suffix for Data Lake Storage** resources, ensuring consistent naming conventions within the infrastructure.
- 🚀 **Added a dedicated Data Lake Storage resource definition**, allowing for programmatic provisioning of Azure Data Lake Storage Gen2 accounts through Infrastructure as Code (IaC).
- 🔑 **Enabled role assignment for Data Lake Storage access** to user-assigned identities, providing necessary permissions for generating Shared Access Signatures (SAS) tokens and managing data.

---



## [v0.196.0] - 2025-06-20 - Workflow Enhancements

### Changed
- 🚀 **Automated Pull Request Creation:** Enhanced the GitHub Actions workflow responsible for creating draft pull requests. This update ensures the workflow automatically fills the pull request description and improves repository checkout for better reliability during the automation process.

---



## [v0.195.0] - 2025-06-20 - Optimized Dynamic Partition Management

### Changed
- ⚡️ **Improved Dynamic Partition Management:** The `replace_partition_keys` utility in the pipeline module now efficiently updates dynamic partitions by only adding new keys and removing obsolete ones, significantly reducing overhead compared to the previous full recreation method.

---



## [v0.194.0] - 2025-06-19 - Streamlined Data Lake Operations

### Refactor
- 🧹 **Optimized Data Lake File Fetching**: Streamlined the internal operations of data lake file fetching functions by removing direct dependencies on the Dagster `OpExecutionContext`, simplifying their interfaces and internal logging.

---



## [v0.193.0] - 2025-06-19 - Improved Auto-Draft PR Workflow with Branch Validation

### Added
- ✨ **Introduced Branch Naming Validation:** Implemented stricter validation and parsing for new branch names (requiring a `base/scope` format) to ensure consistent and informative draft Pull Request titles.
- 🔑 **Enhanced GitHub App Authentication:** Switched to generating a temporary GitHub App token for improved security and more granular permissions when creating Pull Requests.
- 🛡️ **Duplicate PR Prevention:** Added a check to prevent the creation of redundant draft Pull Requests for branches that already have an open PR.

### Changed
- 📝 **Dynamic Draft PR Titles:** Updated the automatic draft Pull Request titles to dynamically include parsed base and scope information from the branch name, providing clearer context.
- 🔄 **Standardized Base Branch:** All auto-drafted Pull Requests now consistently target the `main` branch as their base.

### Refactor
- 🧹 **Workflow Trigger Simplification:** Refined the workflow trigger to be more concise and explicit about running only on branch creation events.
- ⚡️ **Optimized GitHub CLI Setup:** Removed the explicit GitHub CLI installation step, leveraging the pre-installed version on runner environments for efficiency.

---



## [v0.192.0] - 2025-06-18 - Streamlined Development Workflows

### Changed
- ⚙️ **Simplified PR Branch Naming Conventions:** Relaxed and generalized the allowed branch naming patterns for pull requests within the semantic PR workflow, providing developers with greater flexibility in feature and bugfix branch naming.

---



## [v0.191.0] - 2025-06-18 - Enhanced LLM Event Logging and Integration

### Added
- 📈 **Streamlined LLM Event Creation:** Introduced a new utility method (`from_chat_response`) on the **LLMEvent** class, enabling easier generation of LLM events directly from LlamaIndex chat responses. This includes automatic token counting and integration of agent configuration details for more comprehensive logging.

---



## [v0.190.0] - 2025-06-16 - Enhanced Pipeline Path Handling

### Fixed
- 🐛 **Improved Data Lake Folder Naming:** Addressed an issue in the pipeline's data lake folder creation logic, leveraging `os.path.splitext` for more robust and accurate parsing of file names and extensions, preventing errors with certain URI formats.

---



## [v0.189.0] - 2025-06-16 - Empowering RAG with Multi-modal Context and Secure File Sharing

### Added
- ✨ **Multi-modal Content Recognition:** Introduced new capabilities to the Markdown parser to identify and tag different content types within documents, including **text, figures, and tables**, enabling richer RAG interactions.
- 🖼️ **Secure Anonymous File URLs:** Added a new mechanism to generate secure, time-limited URLs for anonymous access to files, particularly for displaying images within multi-modal contexts.

### Changed
- 🚀 **Enhanced RAG Context Generation:** The core RAG context generation logic has been significantly updated to support **multi-modal inputs (text and images)**, leveraging LlamaIndex's `RichPromptTemplate` to dynamically construct prompts that can include direct image references.
- 📄 **Updated RAG Prompt Templates:** Localized RAG system prompt templates across German, English, French, and Italian have been revised to accommodate **multi-modal context blocks**, ensuring seamless integration of images and structured data.
- ⚙️ **Refined `IngestedNode` Schema:** The `IngestedNode` data model now includes a distinct `content_type` field, allowing precise classification of node content as **text, figure, or table** for improved RAG processing.
- 🛠️ **Pipeline Content Tagging:** The document processing pipeline now explicitly tags injected figures and reformatted tables with their respective content types, enhancing downstream RAG capabilities.

### Fixed
- 🐛 **NATS ChatMessage Serialization:** Resolved an issue where `ChatMessage` objects containing `AnyUrl` (e.g., image paths) were not correctly serialized when sent over NATS, ensuring reliable transmission of multi-modal messages.

### Refactor
- 🧹 **Streamlined File Access Services:** Reorganized and centralized the logic for generating Azure Blob Storage SAS URLs and managing anonymous file access within dedicated services, improving modularity and security.
- 🔄 **Simplified RAG Agent Methods:** Simplified the method signatures within the RAG Agent for improved maintainability and cleaner code.

---



## [v0.188.0] - 2025-06-13 - Streamlined File Access and Improved Document Experience

### Added
- 🔐 **Introduced Secure File Access**: A new API and backend infrastructure (`FileController`, `FileService`, `BlobStorageAccess`, `BlobStorageConfig`) to generate secure, time-limited Azure SAS URLs for both authenticated and anonymous file access.
- 🔗 **Enabled Anonymous File Sharing**: Implemented `AnonymousFileAccessService` to generate and validate secure, time-limited URLs, allowing for controlled anonymous sharing of files.
- 🖼️ **New Markdown Components**: Added dedicated Vue components (`MarkdownFigure`, `MarkdownTable`, `ResolveImageComponent`) to enhance the rendering of figures and tables within Markdown content. The `ResolveImageComponent` dynamically fetches and displays images from secure storage using signed URLs.

### Changed
- 📊 **Enhanced Document Metadata**: The `IngestedDocument` data model now includes the **number of pages**, providing richer information for each document.
- ⬇️ **Improved Document List UI**: The document list interface now features a prominent **"Download" button**, enabling direct secure download of files from the document overview.
- 🎨 **Refined Markdown Rendering**: Updated Markdown rendering styles and component integration for improved visual consistency and readability of documents. This includes adjusted heading spacing and link appearances.
- ⚙️ **API and Client Updates**: Expanded API schemas and client SDK to support the new file access functionalities, including handling uploaded files in messages and providing signed URL responses.
- 🌐 **Internationalization Updates**: Updated translation strings across various languages to support new UI elements and document properties.

---



## [v0.187.0] - 2025-06-12 - Improved Document Processing Robustness

### Fixed
- 🐛 **Markdown Parser Robustness**: The Markdown structural node parser now gracefully handles empty content, preventing errors during document splitting.
- 🐛 **Table Reformatting Stability**: Enhanced the table reformatting process to include checks for documents without text content, ensuring more robust and efficient processing.

### Refactor
- 🧹 **Document Factory Clarity**: Improved code readability within the document factory by explicitly naming arguments in function calls, contributing to better maintainability.

---



## [v0.186.0] - 2025-06-12 - Enhanced Core Capabilities: Flexible Ingestion and Azure OpenAI Improvements

### Changed
- ✨ **Flexible Document Data Models**: Updated core document ingestion models (`IngestedBase`) to support arbitrary additional fields, enhancing flexibility for future data attributes.
- 🚀 **Comprehensive Node Metadata Ingestion**: Ensured that all custom and additional metadata from LlamaIndex nodes are fully preserved during the ingestion process, improving context richness for RAG.

### Fixed
- 🐛 **Azure OpenAI Embeddings Authentication**: Resolved an issue to ensure proper utilization of Azure AD token providers for Azure OpenAI embedding models.

---



## [v0.185.0] - 2025-06-11 - Internal Build Enhancements

### Refactor
- 🧹 **Optimized Build Image Action**: Streamlined the internal `build_image` GitHub Action by removing a redundant code checkout step, contributing to more efficient CI/CD pipelines.

---



## [v0.184.0] - 2025-06-11 - Streamlined Web Development and Infrastructure Updates

### Changed
- ⚙️ **Updated Web UI Local Development Port:** The default local development port for the web user interface in `docker-compose` has been updated from `5173` to `8080`.

### Removed
- 🗑️ **Storybook Development Environment:** The Storybook configuration and associated development scripts for the web UI have been removed, streamlining the frontend development workflow.
- 🔑 **Externalized OIDC Client Configuration:** Direct OIDC client configuration has been removed from `nuxt.config.ts`, indicating a more centralized or externalized approach to authentication settings.
- 🧹 **Deprecated Shadcn-Vue Makefile:** The dedicated Makefile for managing `shadcn-vue` components in the web UI has been removed.

### Refactor
- 🔄 **Enhanced Route Query Handling:** Improved the robustness of `useRouteQuery` in web UI composables and pages by explicitly passing `route` and `router` parameters.

---



## [v0.183.0] - 2025-06-11 - Smarter Summaries and Enhanced Document Parsing

### Changed
- 🔄 **Improved Recursive Document Summarization:** The core logic for recursively summarizing documents has been significantly refined, leading to more coherent and contextually relevant summaries. This includes smarter grouping of content nodes and more robust handling of complex document structures.
- 💬 **Updated Summarizer Prompts:** The prompt templates for document summarization have been revised across all supported languages (English, German, French, Italian) to guide the LLM towards producing concise, "TL;DR" style summaries.
- 📄 **Enhanced Summary Node Relationships:** Generated summary nodes now include `PREVIOUS` and `NEXT` relationships, along with an `INDEX` field, ensuring proper sequential ordering and navigability within the vector store.
- ⚙️ **Refined Node Parsing with Document Store Name:** The document parsing pipeline now automatically tags generated nodes with their originating document store name, improving data traceability.
- 🧪 **Playground Environment Configuration:** The default Azure Data Lake storage paths for the playground environment have been updated, and the default LLM for the playground has been switched to `gpt-4o-mini` to optimize local development and testing.

### Added
- ✨ **New `DOCUMENT_STORE_NAME` Metadata Field:** A new metadata field has been introduced to explicitly link document nodes back to their specific document store, enhancing data provenance and filtering capabilities.

### Refactor
- 🧹 **Streamlined Recursive Summarizer Internals:** Key internal methods within the `RecursiveSummaryParser` have been refactored and integrated for improved code clarity and maintainability.

---



## [v0.182.0] - 2025-06-11 - Enhanced Bot Responsiveness and Typing Indicator Logic

### Fixed
- 🐛 **Improved Bot Typing Indicator Logic:** The bot's "typing..." indicator is now only displayed after confirming the bot will respond, preventing misleading typing statuses for ignored or expired messages.

---



## [v0.181.0] - 2025-06-10 - Bot Interaction and Stability Improvements

### Fixed
- 🐛 **Enhanced file content extraction reliability**: Added robust checks for `content_type` in the `ContentExtractor` to prevent potential errors during file processing, ensuring more stable handling of various file types.
- 🐞 **Corrected agent display ID assignment**: Addressed an issue in the `AgentCompletionHandler` to ensure that the `display_id` is correctly passed and utilized when initiating agent interactions.

### Changed
- ⚙️ **Improved localized error handling**: The `OpenaiCompletionHandler` now integrates with the `LocaleHandler` to support localized error messages, providing more user-friendly feedback during exceptions.

### Refactor
- 🧹 **Streamlined completion handler calls**: Removed a redundant `service` parameter from the `get_stream_completion` and `get_completion` methods in `BaseChatBot` for cleaner and more efficient code.
- 📦 **Consolidated `CompletionHandler` logic**: The core completion handling logic was refined and extracted into a dedicated `CompletionHandler` module, improving modularity and updating import paths across `AgentCompletionHandler` and `OpenaiCompletionHandler`.
- 🔄 **Standardized channel ID usage**: Replaced the hardcoded "webchat" string with the `Channels.webchat` constant from `botframework.connector` in `StreamAgentChatBot`, enhancing consistency and maintainability.

---



## [v0.180.0] - 2025-06-10 - Chat Bot Robustness and Version Alignment

### Fixed
- 🐛 **Enhanced Chat Bot Locale Handling:** Improved the `BaseChatBot` to gracefully handle situations where the user's locale is not provided, falling back to a default locale to prevent errors and ensure stable operation.

---



## [v0.179.0] - 2025-06-10 - Enhanced Assistant Interactions with File Uploads

### Added
- ✨ **File Upload Support**: Introduced core infrastructure to enable attaching user-uploaded files (e.g., documents, images) to chat completion requests, allowing for richer and more contextual interactions with AI-Hub assistants.
- 📄 **Open WebUI File Sending Pipeline**: Implemented a new pipeline script specifically for Open WebUI, which facilitates the seamless transfer of user-uploaded files from the UI to AI-Hub assistants during chat interactions.
- 🦾 **UserUploadedFile Data Model**: Defined a new, dedicated data model for standardizing the representation of user-uploaded files, encapsulating their filename, base64-encoded content, and MIME type.

### Fixed
- 🐛 **Azure CLI Command Execution**: Addressed an issue in the API token generation script by ensuring Azure CLI commands are executed reliably, improving the token generation process.

---



## [v0.178.0] - 2025-06-05 - Infrastructure & WebUI Enhancements

### Added
- ✨ Introduced **Azure Container Apps workload profiles** (Consumption and D4), enabling more granular control over resource allocation and cost optimization for deployed services.
- ⚡️ Enhanced **Azure Container App environment integration** by adding subnet delegations for Dagster and WebUI components, improving network configuration and future capabilities.
- 🔑 Added **`WEBUI_SECRET_KEY` configuration** for OpenWebUI, enhancing the security of the user interface.
- 🚀 Implemented **performance tuning environment variables** for OpenWebUI (Uvicorn workers, thread pool size), optimizing web UI responsiveness and throughput.

### Changed
- ⚙️ Improved **WebUI deployment scalability** by making `min_replicas` and `max_replicas` configurable, allowing dynamic scaling based on demand.
- 🔄 Updated **OpenWebUI Redis integration** to explicitly set `REDIS_URL`, ensuring consistent and reliable caching and session management.
- 💾 Configured **Dagster PostgreSQL database to retain data on deletion**, preventing accidental data loss when tearing down infrastructure.

### Refactor
- 🧹 Cleaned up **unused imports** within Infrastructure as Code (IaC) configurations, improving code clarity and reducing clutter.

---



## [v0.177.0] - 2025-06-04 - Enhanced Document Processing with Figure and Table Support

### Added
- 🖼️ **Introduced Figure Extraction and Description Generation:** The document intelligence loader now extracts figures and their IDs from documents. A new pipeline flow is implemented to save these figures to the data lake, generate descriptive alt-text using a vision-enabled Large Language Model, and inject them back into the document as Markdown, significantly improving content accessibility and searchability.
- 📄 **Added Page Number Tracking to Document Nodes:** Document nodes now include a `page` metadata field, providing more granular location information and context within a document.
- ✨ **New Prompts for Figure Descriptions:** Integrated specialized prompts to guide LLMs in generating high-quality, concise alt-text for figures based on their visual content and surrounding document context.
- 🗑️ **Automated Figure Cleanup:** When a document is removed from the document store, its associated extracted figures are now automatically deleted from the data lake, ensuring data hygiene and efficient storage management.

### Changed
- 🔄 **Improved Markdown Parsing for Figures and Tables:** The Markdown structural node parser now intelligently handles HTML `<table>` and `<figure>` tags by splitting them into separate nodes or reformatting tables to Markdown for better representation and search indexing.
- 🧹 **Centralized Azure Resource Naming Suffixes (IaC):** Refactored Azure Infrastructure-as-Code to use a centralized set of constants for resource naming suffixes, improving consistency and maintainability across deployments.
- 🦾 **Updated Summarizer Prompt:** Enhanced the summarizer prompt to explicitly instruct the model to produce summaries in the same language as the input text, improving multi-lingual support and output quality.
- 🚀 **Upgraded Playground LLM:** The default language model for the playground environment has been updated to `gpt-4o`, leveraging its latest capabilities for better performance and accuracy.

### Refactor
- ⚙️ **Refined Document Processing Pipeline:** Overhauled the document processing pipeline to support a multi-stage approach for handling figures and tables, including dedicated steps for parsing, saving figures, injecting descriptions, and reformatting tables before final ingestion.

---



## [v0.176.0] - 2025-06-04 - Enhanced Document Processing with Figure and Table Intelligence

### Added
- ✨ Introduced **advanced document parsing capabilities** to extract and process figures and tables from documents.
- 🖼️ Implemented **automatic figure extraction and storage** in Azure Data Lake, saving image data alongside document content.
- ✍️ Added **AI-powered figure description generation** using vision models, enhancing document accessibility and providing richer context for RAG.
- 📊 Integrated **HTML table conversion to Markdown** within documents, improving readability and data extraction for structured content.
- 📄 Introduced **page number tracking** during document parsing, adding granular metadata to document nodes for better context.
- 🚀 New **`DocumentWithFigureInfo` and `FigureMetadata` types** to facilitate comprehensive processing of rich document content.
- 🗑️ Enhanced the document deletion workflow to **automatically remove associated figures** from Data Lake when a document is deleted.

### Changed
- 🔄 Revamped the **document processing pipeline** for more modular and robust handling of documents, figures, and tables.
- ⚙️ Updated the **Document Intelligence Loader** to leverage native figure extraction capabilities and provide `operation_id` for subsequent processing steps.
- 🧹 Enhanced the **Markdown Structural Node Parser** to intelligently split content based on page breaks and extract tables and figures into distinct nodes for improved chunking.
- 🗣️ Improved **summarizer prompts** across all supported languages to ensure generated summaries maintain the original text's language.
- 📦 Adjusted **Data Lake file fetching** to correctly exclude dedicated figure storage folders, streamlining document ingestion.
- ⚡️ Upgraded the **playground environment's language model** to `gpt-4o`, providing enhanced performance and capabilities for development and testing.

### Refactor
- ♻️ Restructured core document parsing logic by **renaming and repurposing `data_lake_file_to_ref_doc`** into `parse_document_from_data_lake`, streamlining the initial document load into the new figure-aware pipeline.

---



## [v0.175.0] - 2025-06-02 - Enhanced API Integration and Environment Stability

### Changed
- 🐳 **Docker Image Updates**: Updated `docker-compose-webui.yml` to utilize organization-specific and versioned Docker images for **PostgreSQL with pgvector** and **Open WebUI**. This provides greater control and stability for development and deployment environments.

### Refactor
- 🧹 **Streamlined OpenAI API Calls**: Refactored the internal handling of OpenAI API requests for chat completions, image generation, and text-to-speech. This change intelligently filters and prepares arguments based on the OpenAI SDK's method signatures, improving robustness and simplifying future API integrations.

---



## [v0.174.0] - 2025-05-30 - Infrastructure Refinements and Core Updates

### Refactor
- 🧹 **Centralized Azure Resource Naming Constants:** The `DEFAULT_DOCSTORE_SUFFIX` constant has been moved to a new, dedicated `suffix.py` file within the `aihub_iac` module. This improves code organization and maintainability by centralizing constants used for Azure resource naming.

---



## [v0.173.0] - 2025-05-30 - Expanding Azure Infrastructure with Cosmos DB Support

### Added
- ✨ **Cosmos DB Document Store Integration:** Introduced comprehensive support for deploying and configuring Azure Cosmos DB as a document store, including resource naming conventions and necessary role assignments for managed identities.

---



## [v0.172.0] - 2025-05-28 - Enhanced LLM Evaluation and API Consistency

### Added
- ✨ **LLM Evaluation Framework**: Introduced a comprehensive framework for evaluating LLM agent performance using Arize Phoenix. This includes:
    - 📊 **Evaluation APIs**: New API endpoints (`/evaluations`) for managing evaluation datasets and running experiments, complete with detailed DTOs for data and results.
    - 🧠 **LLM Judge**: Implemented LLM-based judges (`PhoenixExperimentEvaluator`) to automatically score agent responses on criteria like correctness, completeness, and conciseness, leveraging structured prompts and multi-language support.
    - 🧪 **Dedicated Evaluation UI**: New administrative pages and components for creating, viewing, and managing evaluation datasets and experiments, providing a dedicated interface for analyzing agent performance.
- 🔐 **GitHub Actions Permissions**: Added `packages: read` permissions to GitHub Actions workflows to enable seamless integration with private package repositories.
- 🚀 **Updated Docker Images**: Upgraded several core service Docker images (including Phoenix, NATS, Redis, MongoDB, Llama.cpp, HF-TEI, OpenWebUI, etcd, MinIO, Milvus, and Attu) to their latest stable versions, enhancing performance, security, and stability.
- 💚 **Docker Service Health Checks**: Introduced comprehensive health checks and persistent volume configurations for key Docker services (Phoenix, NATS, Redis, MongoDB, Llama.cpp, HF-TEI, Attu) to improve system reliability and data persistence.

### Changed
- 🔄 **API Route Standardization**: Renamed API endpoints for Agent, Event, Suite, Thread, and User controllers from singular to plural forms (e.g., `/agent` to `/agents`, `/thread` to `/threads`) to align with RESTful API best practices.
- 🌐 **UI Navigation Alignment**: Updated the web application's routes and navigation structures to consistently reflect the new pluralized API endpoints, ensuring a cohesive user experience.
- 📄 **Improved I18n File Loading**: Enhanced the internationalization (i18n) `t_object` method to dynamically locate and load translation files based on configured paths, increasing flexibility for new language additions.
- 🎨 **UI Design System**: Adjusted the base theme's primary color definitions to utilize `surface` tones, contributing to a refined and consistent visual design.

### Refactor
- 🧹 **Phoenix Configuration Relocation**: Moved the `PhoenixConfig` class from `aihub_agent` to the shared `aihub_lib` module, improving code organization and reusability across components.
- ♻️ **LlamaIndex Document Handling**: Updated internal document representations within LlamaIndex-based vector processing from `Document` to `TextNode`, reflecting a more precise and aligned data model.

---



## [v0.171.0] - 2025-05-27 - Streamlined Azure Infrastructure and Performance Boosts

### Added
- ✨ **New Azure Role:** Introduced `STORAGE_BLOB_DATA_CONTRIBUTOR` for finer-grained access control to Azure Storage Blobs.
- 🔑 **Dagster Role Assignment:** Automatically assigns the `STORAGE_BLOB_DATA_CONTRIBUTOR` role to Dagster's managed identity, ensuring proper permissions for data operations within the platform.

### Changed
- 🚀 **Dagster Webserver Resources:** Increased CPU and memory allocation for the Dagster webserver (CPU from 0.5 to 1.5, Memory from 1Gi to 3Gi) to enhance performance and responsiveness.
- 📈 **PostgreSQL Database Scaling:** Upgraded PostgreSQL database resources by increasing storage from 32GB to 64GB and the SKU from `Standard_B1ms` to `Standard_B2s`, providing improved performance and capacity for database operations.
- 🛡️ **Network Security Group Rules:** Fine-tuned NSG rules for the **Dagster storage subnet** to allow inbound traffic on port 4180 for proxy access, and for the **API Cosmos DB subnet** to permit specific VPN IP access, enhancing connectivity and security.
- ✏️ **NATS File Share Naming:** Corrected the NATS file share name from "blob" to "nats" for improved clarity and accuracy in resource identification.

### Refactor
- 🧹 **Infrastructure Network Architecture:** Re-architected Azure networking by decentralizing subnet creation and Network Security Group (NSG) management to their respective service modules (Dagster, NATS, Phoenix, Stores, WebUI), significantly improving modularity and maintainability of the infrastructure code.
- 🔄 **Pulumi Provider Module Alignment:** Updated Pulumi Azure Native imports to utilize dedicated modules like `cosmosdb` and `privatedns` instead of deprecated ones, ensuring alignment with the latest provider best practices and improved resource definition accuracy.
- ⚙️ **Pulumi Resource Orchestration:** Improved handling of Pulumi resource dependencies by refactoring resource creation with `pulumi.Output.all().apply()`, leading to more robust and reliable deployments.
- 📄 **Centralized Network Configurations:** Moved Virtual Network and Subnet CIDR definitions from hardcoded values into dedicated configuration classes, centralizing network planning and making it easier to manage and update.

---



## [v0.170.0] - 2025-05-26 - Infrastructure Utility Enhancements

### Added
- ✨ **Introduced `mirror-image` Makefile target:** Added a new utility command within the infrastructure (IaC) module to simplify mirroring Docker images from one registry to another (e.g., from public to private), enhancing deployment flexibility and security.

---



## [v0.169.0] - 2025-05-26 - Core Service Synchronization and DataLakeFile Robustness

### Changed
- 🔄 **DataLakeFile Owner Determination:** Enhanced the logic for automatically assigning the owner of a **DataLakeFile**. The system now robustly checks for the `USER` and `USERNAME` environment variables as fallbacks and defaults to "pipeline-user" if no user can be identified, improving reliability in diverse environments.

---



## [v0.168.0] - 2025-05-24 - NATS Network Configuration Update

### Changed
- ⚙️ **Configured Static IP for NATS:** Assigned a fixed private IP address (`10.0.1.4`) to the NATS container instance within the Azure infrastructure, enhancing network predictability and stability for internal service communication.

---



## [v0.167.0] - 2025-05-23 - Enhanced Knowledge Management & Data Model Refinements

### Added
- ✨ **Knowledge Management API & UI**: Introduced a comprehensive API and user interface for managing knowledge bases, enabling users to explore databases, view documents, and inspect individual nodes and their summaries within the platform.
- 🧱 **Standardized Ingested Content Models**: New `IngestedBase`, `IngestedDocument`, `IngestedNode`, `Namespace`, and `NodeSummaryDto` data models were added to provide a consistent and enriched representation of processed documents and their granular chunks across the entire system.
- 🚀 **Retrieve Previous/Next Node Configuration**: Enhanced the RAG agent with `RetrievePrevNextConfig`, allowing for more comprehensive context retrieval by including neighboring nodes.
- 🛠️ **Automated Pipeline Metadata Operations**: Integrated new pipeline operations (`ensure_refdoc_default_metadata`, `ensure_node_default_metadata`) to automatically validate and inject default metadata into documents and nodes during the ingestion process, ensuring data consistency.
- 📈 **OpenWebUI Integration Actions**: Introduced new OpenWebUI actions that enable direct navigation from OpenWebUI chat to AI-Hub's detailed source document view and the new event tracing view for deeper analysis.
- 📊 **Milvus GUI (Attu) Support**: Added the `attu` service to the Milvus Docker Compose setup, providing a user-friendly graphical interface for managing Milvus vector stores.
- 🎨 **Markdown Rendering Component**: A new, reusable Markdown rendering component (`MarkdownRenderer.vue`) was developed and integrated, enhancing the display of rich text content across chat messages and knowledge views.
- 🔑 **Data Lake Account Key Authentication**: Introduced a new configuration option (`DATA_LAKE_ACCOUNT_KEY`) for authenticating with Azure Data Lake, offering more flexible access control.

### Changed
- 🔄 **RAG Agent Configuration Update**: The default RAG agent now leverages Azure OpenAI for both LLM and embedding models in its playground setup, and Milvus connection parameters (port, dimension, collection name) have been updated.
- 💬 **Improved Chat Message Formatting**: Chat messages now support Markdown rendering, significantly improving the readability and structure of responses in the UI.
- 🏷️ **Updated Context Prompt Tagging**: The RAG agent's context prompt template was updated to use `<REFERENCE_DOCUMENT>` tags instead of `<DOCUMENT>`, standardizing how external knowledge is referenced in prompts.
- 🔑 **Relaxed API Token Access Control**: The API endpoint for managing tokens (`/tokens`) is now accessible to all authenticated users, removing the previous admin-only restriction.
- 🧪 **Enriched Test Document Metadata**: Default test documents in `aihub_lib` have been updated to include more comprehensive metadata fields, such as `DOCUMENT_ID`, `CREATED_AT`, `UPDATED_AT`, and `INSERTED_AT`.
- 📊 **Refined Event Statistics Accuracy**: The calculation of start events in persisted event entities has been improved by incorporating `event_type` filtering, leading to more accurate run statistics.
- 🌍 **Expanded Internationalization**: Comprehensive updates to French, German, and Italian translations have been applied across the application, especially for new Knowledge Management features.

### Refactor
- 🧹 **Unified Data Model for Ingested Content**: The internal `Document` type was deprecated and replaced with the more specific `IngestedNode` and `IngestedDocument` models across agents, API, and library for improved consistency and expressiveness.
- ⚙️ **Dedicated Cosmos Document Store Access**: CosmosDB access for the document store has been refactored into a dedicated `CosmosDocstoreAccess` and `CosmosDocstoreConfig`, improving module separation and configuration clarity.
- 📦 **Modular Pipeline Resource Management**: The `aihub_pipeline` now features a reorganized and more modular approach to resource factories, enabling clearer and more explicit management of document stores and various vector store types (e.g., Milvus, Azure AI Search).
- 🌐 **Frontend Component Streamlining**: Replaced the `ChatSourceDocument` component with `ChatSourceNodes` and `KnowledgeNodeContent` to enhance UI modularity and ensure consistent display of retrieved knowledge elements.
- ⚙️ **Unique Event ID Generation**: The `ExternalEventDistributor` now deep copies events and regenerates unique `event_id`s for each agent, ensuring distinct traceability per agent run.
- 📊 **Tracing Page URL Restructure**: The OpenAI service's tracing page URL has been refactored to explicitly include `/tracing`, improving URL structure and semantic clarity.

### Removed
- 🗑️ **Deprecated RAG Trigger Script**: The standalone `aihub_agent/playground/agent/RAGAgent/trigger.py` script has been removed, as its functionality has been integrated into other parts of the agent framework.
- 🗑️ **Legacy Generic Document Type**: The generic `Document` Pydantic model previously used in `aihub_lib.nats.events.semantic.retriever` has been completely removed, superseded by the new, more descriptive `IngestedNode` and `IngestedDocument` types.

---



## [v0.166.0] - 2025-05-20 - Refined Data Processing and System Robustness

### Added
- ✨ **Introduced Dedicated Summary Node Pipeline**: A new `summary_nodes_factory` graph asset has been added to provide a distinct pipeline step for generating and processing summary nodes, separate from general document node creation.
- 🚀 **New Playground Shortcut for Development**: Added a `playground` command to the Makefile for easier local Dagster development and exploration of pipeline assets.

### Changed
- 🔐 **Improved Azure Data Lake Authentication**: The `DataLakeAccess` component now explicitly passes credentials when initializing `AzureBlobFileSystem`, enhancing secure and reliable connections to Azure Data Lake.
- ⚡️ **Enhanced Vector Store Query Robustness**: Implemented retry logic in the `VectorStoreIOManager` when querying for nodes, significantly improving the reliability of data retrieval from vector stores, especially in transient error scenarios.
- ⚙️ **Updated Playground Configuration**: Modified playground settings to align with the new summary node processing, preparing it for dedicated testing and development.

### Fixed
- 🐛 **Ensured Document ID Indexing for Azure AI Search**: Corrected the `AzureAISearchVectorStoreFactory` to ensure that `DOCUMENT_ID` is consistently included and properly typed as a filterable field in Azure AI Search indexes, improving search and filtering capabilities.

### Refactor
- 🔄 **Refactored Node Generation Workflows**: Extracted summary node generation from the primary `nodes_factory` into a dedicated `summary_nodes_factory` graph asset, allowing for more flexible and explicit control over the processing of summary nodes.

---



## [v0.165.0] - 2025-05-16 - Personalized Dashboards and Enhanced User Management

### Added
- ✨ **Personalized Dashboards**: Introduced a new, customizable dashboard feature allowing users to add, configure, and arrange widgets to visualize agent event statistics (e.g., started runs, successful runs, errors, human-in-the-loop requests) directly on their homepage.
- 🚀 **Persistent User Profiles**: Implemented persistent storage for user profiles in a dedicated `UserEntity` within the database. This allows for storing user-specific settings like dashboard configurations and favorite modules.
- 🔐 **Azure Graph Service**: Added a new core service, `AzureGraphService`, to centralize and manage interactions with the Microsoft Graph API, enabling more comprehensive and efficient retrieval of user profiles, images, and application-specific roles from Azure AD.
- 📊 **New Dashboard Components**: Introduced various UI components for dashboard widgets, including number displays, line charts, and bar charts, powered by ApexCharts for robust data visualization.

### Changed
- ⚡️ **Asynchronous API Operations**: Migrated numerous core API services and endpoints (including Thread management, OpenAI interactions, and User information retrieval) to asynchronous operations, significantly improving application responsiveness and scalability under load.
- 🔄 **API Token Role Resolution**: Updated API token authentication such that roles are no longer stored directly within the token. Instead, user roles are dynamically resolved at authentication time from the newly introduced `UserEntity`, ensuring permissions are always up-to-date.
- 🔑 **Enhanced OpenWebUI Integration**: Strengthened the authentication flow for OpenWebUI by adding hash validation for user identification headers and leveraging Azure Graph for authoritative resolution of user roles, improving security and data consistency.
- 📄 **Improved User Profile Management**: Refactored the internal handling of user information, introducing a distinct `UserIdentity` for internal system use and updating `UserDTO` for data transfer. User data is now consistently retrieved and updated in the `UserEntity`.
- 🌐 **Expanded Internationalization**: Added new localization keys for time ranges, chart messages, and various dashboard elements across supported languages.

### Refactor
- 🧹 **Unified User Data Model**: Consolidated the user data model by deprecating the embedded `ApiUser` in `BearerToken` and centralizing user profile information and roles within the new `UserEntity`.
- ⚙️ **Modular Authentication Handlers**: Enhanced the `TokenAndOauth2Handler` to support a list of multiple bearer and OAuth2 authentication strategies, improving flexibility and extensibility.
- 📈 **Refined Event Timeseries Querying**: Updated the event timeseries composable to allow querying event statistics for specific agents and threads, enabling more granular data analysis.

### Fixed
- 🐛 **Query Invalidation Logic**: Adjusted the logic for invalidating cached queries on `StopEvent` and `ExceptionEvent` to ensure related threads and agent data are refreshed reliably.

---



## [v0.164.0] - 2025-05-15 - Infrastructure Consistency Update

### Refactor
- 🧹 **Pulumi Azure Agent Configuration:** Corrected the type definition for environment variables from `EnvironmentVarArgs` to `EnvironmentVariableArgs` within the Azure Agent deployment module for improved consistency and alignment with the Pulumi Azure Native SDK.

---



## [v0.163.0] - 2025-05-15 - Enhanced Agent Deployment Configuration and Developer Tooling

### Added
- ✨ **Customizable Agent Environment Variables**: Introduced the ability to specify additional environment variables for agent containers during deployment, including support for secret references, providing greater flexibility for custom configurations.

### Changed
- 🔄 **Infrastructure Development Enhancements**: Updated development dependencies for `aihub_iac` to include new testing and linting tools such as `pytest`, `ruff`, `mypy`, and `isort`, improving code quality and development workflows.

### Refactor
- 🧹 **Improved AI Search Naming Logic**: Refined the internal logic for generating AI Search service names in infrastructure deployments, ensuring more consistent and robust resource naming.
- 📄 **Minor Library Cleanups**: Performed small refactorings in the `aihub_lib` related to import statements and type annotations for improved code clarity and maintainability.

---



## [v0.162.0] - 2025-05-14 - Azure Bot Setup Enhancements and Core Updates

### Changed
- 🚀 **Improved Azure Bot Setup**: Enhanced the `setup_azure_bot` script to automatically create a **service principal** for the Azure AD application, ensuring proper authentication and authorization for bot operations.

---



## [v0.161.0] - 2025-05-13 - Revamped Admin Experience: Structured Views and Event Displays

### Added
- 🆕 **New Structural Components**: Introduced `StructuralColumn` and `StructuralScreen` to provide a consistent and modern layout across various administration pages.
- 🖼️ **Agent List Component**: Added a dedicated `Agent/List.vue` component for displaying available agents, enhancing clarity in the Agent Admin section.
- 📊 **Interaction Display List**: Implemented a new `Display/List/DisplayList.vue` component and corresponding page (`/admin/thread/[thread_id]/display`) to group and navigate through different interaction "displays" within a thread.
- 📄 **Thread Details View**: Introduced the `Thread/Details.vue` component, which consolidates display-level statistics and event viewing within a thread's comprehensive overview.
- 🔄 **Infinite Scroll Re-extraction**: Extracted the infinite scrolling logic into a new `useThreadsInfinite.ts` composable, maintaining the functionality for potential future use cases.
- 🌐 **New Internationalization Keys**: Added new i18n keys to support the new Agent List and Display List components, improving multi-language support.

### Changed
- 🚀 **Thread List Pagination**: Switched the main thread listing from infinite scrolling to a paginated table (`useThreads`), offering better control and performance for managing large numbers of threads.
- 🗺️ **Updated Thread and Agent Navigation**: Replaced custom top navigation bars on thread and agent detail pages with `SelectButton` for a more consistent and user-friendly sub-navigation experience.
- ⚡️ **Event View Rework**: Simplified the `Event/List/EventList.vue` component by moving its tabbed display and summary statistics into the new `Thread/Details.vue`, streamlining event visualization.
- 🎨 **Enhanced UI Styling**: Applied various minor styling adjustments across components like `Event/Display/Base.vue`, `Event/Statistics.vue`, and `Service/Selection.vue` to improve visual consistency and user experience.
- 🔗 **Updated Thread Navigation Paths**: Adjusted routing for thread hierarchy and chat messages to align with the new "Display" concept, now linking to `/admin/thread/[id]/display/[display_id]`.
- 📊 **Timeseries Chart Y-axis Labels**: Improved readability of timeseries charts by adjusting the Y-axis label positioning.

### Refactor
- 🧹 **Unified Internationalization (i18n) Key Structure**: Refactored numerous i18n keys across the application (e.g., from `eventList` to `event.list`, `threadUtils` to `thread.utils`) for better organization and consistency.
- ⚙️ **Optimized Data Lake Access**: Implemented lazy loading for the `AzureBlobFileSystem` client within `DataLakeAccess` to improve resource utilization and startup performance.
- 📚 **Consolidated Layout Logic**: Moved core layout logic and `ProgressBar` management into the new `StructuralColumn` component, reducing duplication and simplifying page implementations.
- 🔄 **ESLint Configuration Update**: Adjusted ESLint rules to support Vue 3 template roots and whitelisted new PrimeIcons classes for Tailwind CSS.

### Fixed
- 🐛 **Workflow Visualization Loading**: Ensured the workflow visualization component only attempts to render when `network_graph` data is available, preventing potential display issues.

---



## [v0.160.0] - 2025-05-13 - Embedding Model Configuration Improvements

### Changed
- ⚡️ **Refined Azure OpenAI Embedding Configuration**: Enhanced the handling of the `dimensions` parameter for Azure OpenAI embedding models, ensuring more accurate and flexible integration with models that support specific embedding vector sizes, such as `text-embedding-3`.

---



## [v0.159.0] - 2025-05-13 - Core Enhancements: Embedding Control & Faster Event Retrieval

### Added
- ✨ **Expanded Embedding Model Configuration:** Introduced a `dimensions` parameter for embedding models (e.g., text-embedding-3) to allow specifying the desired output vector size, offering finer control over embeddings.
- 🚀 **Improved Event Query Performance:** Added a new database index on `event_data.created_at` for `PersistedEventEntity`, significantly enhancing the efficiency of querying events by their creation timestamp.

---



## [v0.158.0] - 2025-05-12 - Internal API Model Refinements

### Refactor
- 🧹 Streamlined **API Model Creation**: Removed redundant `__base__=BaseModel` parameter when dynamically generating input and output Pydantic models for events, simplifying the codebase.

---



## [v0.157.0] - 2025-05-08 - Infrastructure and Configuration Refinements

### Refactor
- 🧹 **WebUI Configuration Clarity:** Explicitly set `None` as the default value for optional API key fields within the OpenWebUI configuration, enhancing readability and consistency.
- ⚙️ **Improved WebUI Infrastructure Naming:** Refined the naming convention for WebUI container applications and integrated registry settings, contributing to more robust and consistent infrastructure deployments.

---



## [v0.156.0] - 2025-05-08 - Deeper Insights: Event Timeseries and UI Refinements

### Added
- ✨ **Event Timeseries API and UI**: Introduced new API endpoints and comprehensive frontend components to visualize time-based event statistics, offering insights into event trends, agent invocations, and various interaction types (Start, Stop, HITL, BITL, AITL).
- 📈 **Interactive Charts**: Integrated the ApexCharts library to render interactive timeseries charts for event data on both agent and thread overview pages, allowing users to select different time ranges (1h, 24h, 30d, 365d).
- 💰 **LLM Cost & Run Duration Metrics**: Added explicit display of LLM costs and overall run duration directly on the thread overview for better performance tracking.
- ℹ️ **Detailed Agent Overview**: Enhanced the agent overview page to prominently display key agent information such as name, class, ID, and online status.

### Changed
- 🔄 **Consistent Terminology**: Renamed "latency" to "**duration**" across all API responses, data transfer objects (DTOs), and user interfaces for improved clarity and consistency in performance metrics.
- 🎨 **UI/UX Improvements**: Refined the visual presentation and responsiveness of various UI elements, including chat message styling, event list layouts, and overall agent/thread overview pages.
- ⚙️ **Optimized Data Handling**: Implemented more robust timezone handling for datetime objects in API responses, ensuring consistent and accurate time representation across the platform.
- ⚡️ **Improved Caching & Real-time Updates**: Adjusted frontend query caching strategies and introduced intelligent cache invalidation to provide more immediate updates for thread and agent statistics upon event completion.
- 📝 **Message Content Structure**: Revised the internal representation of **message content** to support a flexible block-based structure (e.g., text, image, audio) while maintaining a simplified `content` property for basic text.

### Fixed
- 🐛 **Accurate Run Statistics**: Corrected the backend aggregation logic for run statistics to prevent duplicate counting of events within a single run, ensuring more precise data for performance analysis.

### Refactor
- 🧹 **Centralized User Access Checks**: Consolidated user membership verification within threads into a dedicated helper function for cleaner and more maintainable code.
- ⚙️ **Standardized Frontend Query States**: Standardized the naming convention for query loading states from `isLoading` to `isPending` across frontend composables for consistency with the underlying query library.

---



## [v0.155.0] - 2025-05-08 - Revolutionizing Speech-to-Text and Data Persistence

### Added
- ✨ **Introduced Audio Chunking Service:** A new `AudioChunkingService` has been added to `aihub_api`, providing intelligent methods to split large audio files at silence points and seamlessly merge their transcriptions, enabling robust processing of files that exceed API size limits.
- 🎙️ **Enhanced Speech-to-Text (STT) for Large Files:** The STT service within `aihub_api` now automatically chunks large audio inputs, processes them in segments, and merges the resulting transcriptions, significantly increasing the maximum supported audio file size.
- 🗄️ **Persistent MongoDB Storage:** Added a dedicated Docker volume for MongoDB, ensuring that all database data is permanently stored and persists across container restarts.
- 📦 **FFmpeg Requirement for Audio Processing:** Integrated `ffmpeg` as a new dependency for `aihub_api` to power advanced audio manipulation capabilities, crucial for the new chunking service.

---



## [v0.154.0] - 2025-05-08 - Enhanced Release Process and IAC Integration

### Changed
- 🚀 **Aligned `aihub_iac` Versioning:** The `aihub_iac` (Infrastructure as Code) component's version has been significantly synchronized with the main project release cadence, bringing it up to `v0.154.0`.
- ⚙️ **Integrated `aihub_iac` into Release Workflow:** The `aihub_iac` component is now included in the automated GitHub Actions workflow for version tagging, streamlining its release management.
- 📦 **Standardized Microservice Versions:** All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_pipeline`) have been updated to `v0.154.0` to ensure consistent versioning across the platform.

---



## [v0.153.0] - 2025-05-08 - Core Version Updates and CI/CD Enhancements

### Added
- ✨ **Expanded Semantic PR Scopes**: Introduced `iac` and `ci-cd` as new validation scopes for semantic pull requests, improving categorization and consistency for contributions related to Infrastructure as Code and Continuous Integration/Delivery.

### Changed
- 🔄 **Core Version Alignment**: Synchronized the version across `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline` to `v0.153.0`, ensuring all core components reflect the latest release.

---



## [v0.152.0] - 2025-05-08 - Introducing Pulumi-Powered Azure IaC for AIHub

### Added
- 🚀 **New Infrastructure as Code (IaC) Module**: Introduced `aihub_iac`, a comprehensive Pulumi-based solution for deploying and managing AIHub's Azure infrastructure. This enables automated, reproducible, and secure provisioning of resources.
- 🌐 **Automated Network Setup**: Implemented Infrastructure as Code for creating and managing Azure Virtual Networks (VNet), subnets, and Network Security Groups (NSGs) with predefined access rules.
- 💻 **Centralized Microservice Deployment**: Added IaC definitions for deploying core AIHub microservices, including **Agents**, **API**, **Bots**, **Phoenix**, **Dagster**, and **OpenWebUI**, ensuring consistent and efficient deployments.
- 💾 **Managed Data Stores**: Integrated IaC for configuring and deploying essential data stores such as **Azure Cognitive Search** (for vector search), **Cosmos DB** (for document and API data), and **PostgreSQL** (with pgvector support for relational data).
- 🔑 **Enhanced Security with Private Endpoints and Identities**: Incorporated private endpoints for secure access to data services and automated user-assigned managed identity creation for granular access control.
- 📄 **Updated On-Premises Technology Documentation**: Expanded the `README.md` to include **PG-vector**, **Postgres**, and **Docker** as supported on-premises technologies.

### Changed
- 🔄 **Integrated CI/CD Workflows**: Updated the project's `Makefile` to include linting, formatting, and type-checking for the newly introduced `aihub_iac` module, ensuring code quality across the entire codebase.

---



## [v0.151.0] - 2025-05-06 - AI-Hub Evolution: Persistent Agents, Enriched Thread Details, and Multilingual UI

### Added
- 🦾 **Persistent Agent Profiles:** Introduced a new persistence layer for agents (`AgentEntity`), allowing their configurations, workflow graphs, and event specifications to be stored in the database. This enables the display of agent information even when agents are offline.
- 📊 **Advanced Thread Analytics:** Implemented comprehensive thread statistics, including turn counts, event counts, LLM costs, and various "in-the-loop" states (Human-In-The-Loop, Agent-In-The-Loop, Bot-In-The-Loop). This provides a deeper understanding of conversation flows and agent performance.
- 📄 **Paginated Thread and Agent Views:** Introduced pagination for listing user threads and agent-specific threads, improving performance and user experience for large datasets.
- 🌐 **Comprehensive UI Localization:** Added extensive new localization keys across the user interface, enabling a fully multilingual experience for various UI elements, including dynamic event names and descriptions.
- 📈 **Enhanced Workflow Visualization:** Improved the workflow visualizer to accurately represent "in-the-loop" request-response patterns (AITL, HITL, BITL), offering a clearer understanding of complex agent interactions.
- 🔌 **Live Event Streaming via WebSockets:** Implemented WebSocket support for real-time event updates to the UI, providing live feedback on agent activities and thread progression.
- ✨ **Multimodal Message Support:** Updated internal message structures to support diverse content types, including text, images, and audio, paving the way for richer interactions.
- 🛣️ **Router Event Visualization:** Introduced a new event type and UI component to visualize routing decisions made by LLMs within a workflow, detailing chosen paths and reasons.
- 🚨 **Dedicated Exception Event Display:** Added a specific event and UI component for displaying exceptions, providing immediate visibility into errors during agent runs.
- 🚀 **Frontend Testing Events:** Expanded the `FrontendTestingAgent` with new events and patterns to facilitate more robust UI testing of complex workflows.
- 🧩 **Modular UI Components:** Introduced new reusable Vue components for Agent and User Avatars, and generic Navigation bars (Left and Top), enhancing UI consistency and development speed.

### Changed
- 🔄 **Refactored Thread Management:** Migrated core thread management logic from real-time NATS interactions to a database-driven persistence model, enabling richer query capabilities and historical data analysis.
- 🏷️ **Localization Key Renaming:** Standardized localization keys by changing the `agents.` prefix to `agent.` for consistency across the application.
- 💬 **API Endpoint Naming:** Renamed OpenAI-compatible endpoints (e.g., `get_models` to `get_models_with_assistants`) to clarify that they also include AI-Hub assistants.
- 🖥️ **Centralized WebSocket Event Localization:** Refactored WebSocket event processing to localize display names and descriptions directly on the backend before sending to the client, simplifying frontend logic.
- 🗺️ **Dynamic Event Display Logic:** Updated event display components to dynamically render localized event names and descriptions directly from the backend, reducing hardcoded strings.
- 📇 **UI Layout for Admin Pages:** Redesigned the agent and thread administration pages to leverage new navigation components, providing a more structured and intuitive user experience.

### Fixed
- 🐛 **Improved Error Logging:** Replaced numerous `logger.error` calls with `logger.exception` across the codebase, ensuring that stack traces are consistently captured for better debugging.
- 🩹 **Event Deserialization Robustness:** Enhanced event deserialization logic to correctly handle complex inheritance hierarchies, particularly for events with multiple parent classes, preventing data integrity issues.
- 🛡️ **Stricter Event Validation:** Implemented stricter validation for incoming `ExternalEvent`s, ensuring `thread_id` is always present and setting default `display_id` values.
- 📐 **UI Layout Correction:** Addressed a UI issue in the default layout where content was partially hidden by the fixed top navigation bar.
- 🔒 **Enhanced WebSocket Security:** Improved WebSocket connection handling with more specific `PermissionError` for unauthorized users.
- 🔗 **API Client Regeneration:** Updated the generated OpenAPI client to reflect all new DTOs, endpoints, and changes across the API, ensuring seamless communication.

### Removed
- 🗑️ **Deprecated Thread Management UI:** Removed outdated and less flexible thread management UI components and pages, superseded by the new, more comprehensive administration views.
- 🧹 **Legacy Data Stores:** Migrated away from old Pinia stores for agents, events, and threads, replacing them with new composables using Pinia Colada for improved data fetching and state management patterns.
- 🚫 **Unused Gemini Configuration:** Cleaned up unused and deprecated Gemini LLM configurations from the development environment.

---



## [v0.150.0] - 2025-05-04 - Enhancing LLM Capabilities with Gemini Integration and Recursive Summarization

### Added
- 🚀 **Google Gemini LLM Integration:** Introduced native support for Google Gemini Large Language Models, expanding the range of available conversational AI capabilities and model choices.
- 📄 **Recursive Document Summarization:** Implemented a new recursive summarization feature within the data ingestion pipeline, enabling the generation of multi-level document summaries for enhanced Retrieval-Augmented Generation (RAG).
- ⚙️ **New Data Pipeline Playground:** Added a comprehensive playground example that demonstrates the new recursive summarization and data ingestion pipeline for easier experimentation and setup.

### Changed
- 📝 **Improved Agent Description Guard Prompt:** Refined the prompt for the agent description guard to enforce a stricter JSON output format, enhancing the reliability and consistency of LLM responses for structured parsing.
- 📏 **Adjusted Summarization Minimum Length:** Modified the minimum character length required for text summarization in the recursive parser, optimizing the granularity of generated summaries.

### Refactor
- 🔄 **Standardized OpenAI-like LLM Configuration:** Renamed `SelfHostedLLMConfig` and its associated parameters to `OpenaiLikeLLMConfig` for more accurate representation of Large Language Models that adhere to OpenAI-compatible APIs, improving clarity and consistency across the configuration.
- 🧹 **Streamlined RAG Agent Structure:** Reorganized internal directories and imports for the RAG agent components, enhancing codebase maintainability and logical grouping.

---



## [v0.149.0] - 2025-05-04 - Gemini Integration and LLM Configuration Standardisation

### Added
- ✨ **Google Gemini LLM Integration:** Introduced native support for Google Gemini Large Language Models, allowing seamless integration and usage of Gemini models (e.g., `gemini-2.0-flash`) within the platform. This includes new configuration classes and API key management.

### Refactor
- 🧹 **Standardized LLM Configurations to OpenAI-like:** Renamed `SelfHostedLLMConfig` and `SelfHostedLLMParameter` to `OpenaiLikeLLMConfig` and `OpenaiLikeLLMParameter` respectively. This change broadens the scope to encompass any LLM that adheres to the OpenAI API standard, enhancing flexibility and clarity for model integrations.
- 🔄 **Updated LLM Configuration References:** All internal components and examples (including `RAGAgent`, `FewShotAgent`, and `LlamaIndexAgent` playgrounds) have been updated to utilize the new `OpenaiLikeLLMConfig` naming convention, ensuring consistency across the codebase.
- 📦 **Agent Import Path Refinement:** Adjusted internal import paths for `RAGAgent` components for improved module naming consistency.

---



## [v0.148.0] - 2025-04-24 - Smarter Context Sufficiency for RAG Agent

### Changed
- 🦾 **Improved RAG Agent Context Assessment**: The RAG Agent's ability to determine if it has sufficient context has been enhanced. The underlying guard now intelligently adapts its assessment and feedback based on whether additional retrieval attempts (hops) are available, leading to more refined decision-making and clearer indications when no further context can be obtained.

---



## [v0.147.0] - 2025-04-24 - Enhanced Azure AI Search Vector Store Configuration

### Added
- ✨ **Configurable Azure AI Search Vector Dimensions**: Introduced a new `dimensions` parameter for Azure AI Search vector stores, allowing explicit control over the `embedding_dimensionality` when creating or configuring vector indexes. This enhancement provides greater flexibility and precision for vector search operations across `aihub_lib` and `aihub_pipeline` resources.

---



## [v0.146.0] - 2025-04-17 - Enhanced Conversation Lifecycle Management

### Added
- ✨ **Conversation Expiration Management**: Implemented a comprehensive Time-To-Live (TTL) mechanism for conversations, enabling automatic cleanup of inactive chat histories in the database and freeing up resources.
- 🦾 **User-Friendly Expiration Notifications**: Introduced a new feature to inform users when a conversation has expired due to inactivity, providing clarity on chat history availability.
- 🔄 **Teams Conversation Reset Handling**: Added intelligent tracking to differentiate between naturally expired conversations and those explicitly deleted or reset by users in platforms like Microsoft Teams, preventing incorrect "expired" messages after a user-initiated reset.
- ⚡️ **Configurable Typing Indicator Duration**: Introduced a `typing_timeout_seconds` parameter, allowing for customization of how long the bot's "typing" indicator is shown to the user before a response is delivered.
- 🧪 **New Test Suite for Conversation TTL**: Added comprehensive integration tests to ensure the robustness and correctness of the new conversation expiration and tracking features.

### Changed
- 🧹 **Centralized TTL Configuration**: The `BotRunner` now provides a central place to configure the conversation Time-To-Live (TTL) duration in days, simplifying deployment and management of conversation data lifecycle.
- 📄 **Updated Conversation Persistence**: Modified conversation persistence logic to automatically update the `last_activity` timestamp on every message, ensuring conversations are correctly identified for TTL expiration based on recent user interaction.

---



## [v0.145.0] - 2025-04-16 - Improved Streaming and New Agent Patterns

### Added
- 🦾 **New Playground Example: Long-Running Agent:** Introduced a comprehensive example demonstrating how to build and run an agent that operates over an extended period, showcasing asynchronous operations and continuous output streaming capabilities.

### Changed
- ⚡️ **Asynchronous API Integration for WebUI:** Transitioned the WebUI connection to utilize the `httpx` library for all API requests, enabling fully asynchronous and more efficient handling of both streaming and non-streaming interactions with the AIHub API.
- 🚀 **Robust Model Fetching:** Enhanced the `pipes` method in the WebUI connection to include improved error handling and more informative error messages, increasing reliability when fetching available models.

### Refactor
- 🧹 **WebUI Streaming and Non-Streaming Logic:** Rearchitected the main `pipe` function in the WebUI connection by separating the logic into distinct `pipe_stream` and `pipe_non_stream` methods, along with a new dispatcher `pipe`. This significantly improves code organization, maintainability, and ensures proper asynchronous behavior for different request types.

---



## [v0.144.0] - 2025-04-15 - RAG Agent Multi-Hop Retrieval and Contextual Enhancements

### Added
- ✨ **Introduced Multi-Hop Retrieval for RAG Agent:** The RAG agent can now perform multiple retrieval attempts (hops) to gather more relevant context if the initial information is insufficient. This significantly improves the agent's ability to answer complex questions requiring deeper knowledge base exploration.
- ⚙️ **Configurable `max_hops` for RAG Agent:** A new `max_hops` parameter has been added to the RAG Agent configuration, allowing users to control the maximum number of retrieval attempts the agent can make when seeking sufficient context.
- 🚀 **Dynamic Query Generation for Context Guard:** The `context_sufficient_guard` has been enhanced to intelligently generate a new, distinct query when the current context is insufficient. This new query guides subsequent retrieval hops, improving the quality of retrieved information.
- 📄 **New `ContextInsufficientWithQueryEvent`:** A new event type was introduced to facilitate the multi-hop retrieval process, allowing the RAG Agent to signal the need for further context retrieval with a revised query.

### Changed
- 🔄 **Refined Azure AI Search Integration:** The configuration for Azure AI Search Vector Store now explicitly includes `semantic_configuration_name`, leading to more robust and accurate semantic searches.
- ⚡️ **Expanded LLM Context Window:** The default context size for self-hosted LLMs in development environments (docker-compose) has been significantly increased from 512 to 8192 tokens, enabling the models to handle much longer conversations and more extensive contexts.
- ⬆️ **Updated Example/Trigger LLM to Azure OpenAI:** The RAG Agent's example usage has been updated to utilize Azure OpenAI models, showcasing the agent's compatibility with cloud-based LLM services and demonstrating the new multi-hop feature.
- 🧹 **Standardized NATS Event Imports:** Refactored internal NATS event imports within the RAG Agent for improved code organization and readability.
- ➡️ **Switched to `UserMessageEvent` in RAG Agent Trigger:** The example trigger now uses `UserMessageEvent` instead of `StartEvent`, providing richer user and locale metadata for agent interactions.

### Refactor
- ♻️ **Renamed Context Guard Results:** Internal data models and factory functions related to the `context_sufficient_guard` have been renamed from `GuardResult` to `ContextGuardResult` for clearer naming conventions and improved code clarity.

### Removed
- 🗑️ **Simplified Azure OpenAI Embedding Parameters:** The explicit `dimensions` field has been removed from the `AzureOpenAIEmbeddingParameter` configuration, streamlining the setup for Azure embedding models.

---



## [v0.143.0] - 2025-04-11 - Unleash Expert Knowledge: Introducing Collaborative Agents and Intelligent Workflow Routing

### Added
- 🦾 **Expert Asking Agent:** Introduced a new agent capable of posing questions to dedicated expert channels (e.g., Slack), validating responses, asking follow-up questions, and saving sufficient answers as knowledge snippets to OpenWebUI.
- 🧠 **Expert Grounded Agent:** Implemented a new agent that grounds its answers in available context and, if knowledge is missing, seeks user consent to forward queries to the Expert Asking Agent for external expertise.
- 🔗 **OpenWebUI Python SDK:** A comprehensive new Python SDK is now available for programmatic interaction with the OpenWebUI API, enabling direct management of chats, files, and knowledge bases.
- 🛣️ **LLM-Based Routing Utility:** Introduced a new utility for dynamic workflow routing using Large Language Models, allowing agents to intelligently select the next step based on instructions and available options.
- 👁️ **Enhanced Event Display for Frontend:** `LimitChatHistoryEvent`, `StandaloneQuestionCondenserEvent`, and `StartEvent` are now explicitly displayable in the frontend, providing greater transparency into agent workflow execution.

### Changed
- 🔄 **Agent Directory Restructuring:** Streamlined the agent directory structure by moving `FewShotAgent`, `LLMWrappingAgent`, `RAGAgent`, and `WebuiAgent` to top-level agent directories for improved organization and discoverability.
- 🚀 **Azure OpenAI API Version Update:** Updated the Azure OpenAI API version from `2023-12-01-preview` to `2024-12-01-preview` across agent configurations and pipeline resources.
- 🌐 **Locale Forwarding in OpenAI Endpoints:** OpenAI API endpoints now correctly forward user locale information to agents, enabling more accurate and localized responses.
- 📦 **Event Serialization Enhancements:** Improved the serialization and deserialization of NATS events to robustly handle nested events and lists containing event objects, increasing data integrity.
- 💬 **Thought Event Formatting:** Adjusted `ThoughtEvent` display to ensure consistent newlines, improving readability of agent thought processes.
- 📄 **WebUI Docker Compose Configuration:** Updated the default Docker Compose configuration for OpenWebUI, enabling API key usage, disabling channels, and adding RAG embedding batch size for improved performance.
- ⚙️ **WebUI Pipeline Request Headers:** Added `Accept-Language` header to requests originating from WebUI pipelines, ensuring proper locale propagation.

### Refactor
- 🧹 **Agent Base Class Relocation:** The core `Agent` base class was refactored and moved out of the `abstract` subdirectory for a flatter, more intuitive directory structure.
- 📦 **Consolidated Common Events:** Moved `LimitChatHistoryEvent` and `StandaloneQuestionCondenserEvent` from `aihub_agent` to `aihub_lib`, centralizing common event definitions for broader reuse.
- 📝 **Improved Internal Logging:** Replaced direct `traceback.print_exc()` calls with `logger.exception(e)` across Dispatcher, EventController, EventService, and NATS Subscribers for standardized and more effective error reporting.

### Fixed
- 🐛 **BotInTheLoopAgent Playground Example:** Corrected `slack_channel_id` example and `UserMessageEvent` signature in the BotInTheLoopAgent playground example.

---



## [v0.142.0] - 2025-04-10 - Enhanced Bot-in-the-Loop & Azure Bot Setup

### Added
- ✨ **Responder Information in Bot-in-the-Loop Responses**: The `BotInTheLoopResponseEvent` now includes detailed information about the human responder (e.g., Slack user ID, name), enabling agents to track and react to specific user inputs.
- ⚡️ **Dynamic Slack ID Retrieval & Caching**: Introduced an internal mechanism in the `aihub_bot` to dynamically fetch and cache Slack bot and team IDs using the Slack `auth.test` API, improving reliability and reducing manual configuration.

### Changed
- 🚀 **Simplified Bot-in-the-Loop Request API**: The `BotInTheLoop.invoke` method (and `BotInTheLoopRequestEvent`) now only requires the Slack channel ID for initiating a request, automatically handling the full conversation ID internally. This streamlines integration for agents.
- ⚙️ **Improved Internal Bot-in-the-Loop Slack Handling**: Refactored the internal handling of Slack conversation IDs and thread timestamps within the `aihub_bot` to better manage human-in-the-loop interactions.

### Fixed
- 🐛 **Robust Azure Bot Setup Script**: The Azure bot setup script has been made more resilient by checking for existing Azure AD app registrations before creation and improving JSON parsing for command outputs.

---



## [v0.141.0] - 2025-04-09 - Enhanced Test Stability and Core Dependency Updates

### Changed
- 🚀 **Improved Backend Test Reliability:** Enhanced the CI/CD backend test action by implementing more robust Docker service health checks, including detailed status output, a timeout mechanism, and clearer error handling, to ensure test environments are consistently ready.
- 🔄 **Updated Milvus Vector Store Dependency:** Upgraded the `llama-index-vector-stores-milvus` library to version `0.7.3`, incorporating the latest features and stability improvements for Milvus integration.

### Fixed
- 🐛 **Resolved Milvus Test Instability:** Addressed intermittent test failures related to Milvus vector store initialization by introducing a small delay in the test setup, ensuring the store is fully ready before operations begin.

---



## [v0.140.0] - 2025-04-09 - Introducing Bot-in-the-Loop and Core Refinements

### Added
- ✨ **New Bot-in-the-Loop (BiTL) Feature:** Introduced a robust mechanism allowing agents to interact with bots (e.g., Slack) to solicit human input or approval at critical workflow junctures, enhancing guided automation and error handling. This includes new event definitions (`BotInTheLoopRequestEvent`, `BotInTheLoopResponseEvent`) and a helper class in `aihub_lib`.
- 🦾 **`BotInTheLoopAgent`:** A new example agent has been added to the playground, demonstrating how to effectively integrate and utilize the Bot-in-the-Loop functionality within agent workflows.
- 🚀 **Dedicated BiTL Bot and Controller:** Core components (`BotInTheLoopBot` and `BotInTheLoopController`) have been integrated into the `aihub_bot` service to facilitate communication and handle responses from bot-in-the-loop interactions, including a handler for managing conversation threads.

### Changed
- 🔄 **Enhanced Event Dispatching:** The `ExternalEventDistributor` in `aihub_lib` now explicitly supports processing `BotInTheLoopResponseEvent`, enabling agent workflows to seamlessly resume after receiving input from a bot interaction.
- 📄 **Improved Dependency Management Script:** The `switch_dependencies.py` script now automatically executes `poetry install` after locking dependencies, streamlining the setup process for both local and remote core development environments.

### Refactor
- 🧹 **Streamlined Chat Bot Architecture:** The `aihub_bot`'s chat-related modules (including `BaseChatBot`, `CompletionHandler`, `ContentExtractor`, and their `agent`/`openai` specific implementations) have been reorganized into a dedicated `aihub_bot/bots/chat` subdirectory. This improves code structure, modularity, and maintainability across different chat bot implementations.

---



## [v0.139.0] - 2025-04-08 - Deepened Frontend Integration with Advanced Event Tracing and Core Event System Refinements

### Added
- ✨ **New Frontend Testing Agent**: Introduced `FrontendTestingAgent` and its configurations, providing a dedicated agent for testing and developing frontend components that display various event types (e.g., embeddings, retrievers, rerankers, tool calls, Human-in-the-Loop interactions).
- ⚙️ **Open Web UI Docker Integration**: Provided a new `docker-compose-webui.yml` to easily run Open Web UI alongside AI-Hub, offering a comprehensive local development environment.
- 🤝 **Open Web UI Custom Pipeline**: Implemented a new custom pipeline for Open Web UI (`webui_pipelines/aihub_connection.py`) to seamlessly integrate AI-Hub agents as models, enabling direct interaction and transparent proxying of chat completions.
- 🕵️ **Open Web UI Tracing Action**: Introduced a new Open Web UI action (`webui_pipelines/suite_connection.py`), allowing users to directly open the detailed AI-Hub event tracing view for specific chat interactions from within Open Web UI.
- 🚀 **Advanced Event Display Components**: Developed a suite of new UI components for granular event visualization, including dedicated displays for agent delegations, LLM costs, embedding searches, document retrievals, reranking, tool calls, internal thoughts, and Human-in-the-Loop requests/responses.
- 📈 **LLM Cost Visualization**: Implemented a new UI component (`Costs/Table.vue`) to display LLM token usage and associated costs within the event trace, enhancing transparency for resource consumption.
- 📄 **New Product Pitch Documentation**: Added a comprehensive `0_product_pitch.md` document, detailing the vision, core concepts, evolutionary stages, architecture, benefits, and security principles of the AI-Hub.
- ⚡️ **Performance Caching for User & Thread Data**: Implemented `TTLCache` in `AzureUserInformationProvider` and `WebSocketSender` to cache user and thread information, significantly improving performance for frequently accessed data.
- 📦 **Centralized ID Conversion Utility**: Introduced `aihub_lib.persistence.utils.str_to_object_id` to centralize the conversion of string IDs to MongoDB `ObjectId` across the codebase, ensuring consistency.
- 🔌 **WebSocket Dependency Injection**: Added new dependencies to properly inject core services (Locale, NATS, External Event Distributor, WebSocket Manager, WebSocket Sender) into WebSocket contexts, standardizing their usage.

### Changed
- 🔄 **Core Event Model Overhaul**: Refactored the fundamental `BaseEvent` model to use `_event_name` and `_parent_event_names` for more robust and flexible event identification and deserialization across microservices, improving cross-service communication.
- 📢 **Test Runner API**: Updated the `AgentTestRunner` API (e.g., `get_events_of_class`, `has_event_of_class`) to provide more precise control over event class matching in tests, enabling stricter assertions.
- 🌐 **WebSocket Event Payload Structure**: Modified the `WSServerEvent` payload to use strongly-typed Pydantic models for the `event` field, enhancing data integrity and enabling the frontend to dynamically render diverse event types with full data.
- ⚙️ **Chat Service Output**: The chat service's `build_json_response_content` now returns a `ChatContent` object, which includes both the LLM's final response and any streamed reasoning content, providing richer output for conversational agents.
- 💡 **ThoughtEvent Hierarchy**: `ThoughtEvent` now inherits from `ChunkEvent`, allowing internal reasoning to be streamed and displayed as partial content, aligning with the incremental nature of LLM processing.
- 🔑 **Authentication Handler API**: Broadened the `AuthHandler` interface to include an `authenticate_token` method, enabling direct token validation for WebSocket connections and other non-HTTP contexts across all authentication strategies.
- 📊 **Agent Discovery Deduplication**: Ensured that the agent discovery process correctly deduplicates agent entries by `(agent_class, agent_id)`, preventing redundant listings of the same agent.
- 📈 **Granular Event Retrieval**: Enhanced the event retrieval API (`/event/`) to support filtering by `thread_id`, `display_id`, and `event_class`, providing more control over the events fetched from persistence.
- 🩺 **Health Check Response**: Extended the `/health` endpoint response to include an HTTP status `code` field, providing more explicit health information.
- 🎨 **UI Styling and Layout**: Adjusted various UI components and layouts to improve visual consistency and responsiveness, including updates to the default layout, admin pages, and chat message display.
- ⚙️ **OpenAI API Compatibility**: Refined the OpenAI service to handle messages and tool calls more robustly, improving compatibility with various OpenAI models and their features.
- 🖼️ **Frontend Serving Capabilities**: Enhanced the `Runner` to serve Nuxt.js assets and implement Single Page Application (SPA) routing fallback, improving frontend serving alongside the backend.

### Refactor
- 🧹 **Event Naming Consistency**: Standardized event naming conventions across the codebase, consistently using `event_name` instead of `event_type` or `__class__.__name__` in internal logic, logging, and method signatures for improved clarity and maintainability.
- 🔗 **Internal Event Routing**: Streamlined how event subjects are constructed and validated in NATS publishers and dispatchers, enforcing correct routing patterns.
- 📦 **Core Library Structure**: Reorganized internal modules within `aihub_lib` and `aihub_agent` for better logical separation of concerns (e.g., consolidating `ExternalEventDistributor` and ID utilities).
- 🧹 **Test Code Adaptations**: Updated numerous test files across agents and APIs to align with new event naming conventions and API changes.

### Removed
- 🗑️ **Deprecated External Event Module**: Removed the outdated `aihub_api/aihub_api/sockets/events/user_to_server/__init__.py` and `aihub_api/aihub_api/sockets/receiver/__init__.py` modules, as their functionality has been refactored and consolidated into the `aihub_lib.nats.distributor` module.
- 🗑️ **Legacy Thread ID Conversion**: Removed the `ThreadEntity.to_thread_id` static method in favor of the new centralized `aihub_lib.persistence.utils.str_to_object_id` utility.
- 🗑️ **Dedicated Open Web UI Page**: Removed the isolated Open Web UI page (`pages/module/webui/index.vue`) in the AI-Hub frontend, as its functionality is now seamlessly integrated into the new OpenAI service page.

---



## [v0.138.0] - 2025-04-07 - Vector Store Upgrades and Test Infrastructure Improvements

### Changed
- 🔄 **Updated Milvus Integration:** Upgraded `llama-index-vector-stores-milvus` and `pymilvus` to their latest stable versions, enhancing compatibility and performance with Milvus vector stores.
- ⚙️ **RAGAgent Environment Configuration:** Adjusted RAGAgent environment variables, including Azure subscription ID and regional settings, to align with updated deployment configurations.
- 🐳 **Streamlined Docker Compose for NATS:** Removed the health check configuration for the NATS service in `docker-compose.yml` to simplify the local development environment.

### Refactor
- 🧪 **Improved Asynchronous Test Setup:** Implemented a session-scoped `asyncio` event loop fixture for tests, significantly enhancing the stability and reliability of asynchronous test execution across agents and processors.

---



## [v0.137.0] - 2025-04-07 - Improved Event Handling for Human-in-the-Loop Workflows

### Changed
- 🔄 **Refined Human-in-the-Loop Response Event Handling:** Enhanced the serialization and deserialization logic for `HumanInTheLoopResponseEvent` in the `ChatService` to ensure robust and accurate event reconstruction, particularly for complex event inheritance structures.

---



## [v0.136.0] - 2025-04-02 - AIHub Library Enhancements: Smarter Guards and Localization

### Refactor
- 🦾 **Modernized `context_sufficient_guard` Implementation**: Re-engineered the core logic of the context sufficiency guard to directly leverage `llm.structured_predict`. This significantly improves the robustness and efficiency of structured output parsing and enhances compatibility with diverse Large Language Model capabilities, including non-function-calling models.

### Changed
- 🌐 **Enhanced Localization for Guard Results**: Introduced dynamic Pydantic model generation for `GuardResult` within `context_sufficient_guard`, allowing for fully localized field descriptions and improved clarity in guard decision explanations across all supported languages.
- ⚙️ **Streamlined Prompt Structure**: Simplified the internal prompt template for the `context_sufficient_guard` by removing redundant message elements, leading to cleaner code and improved maintainability.
- 📝 **Improved German Translation**: Corrected a minor typo in the German translation file for guard-related text.

---



## [v0.135.0] - 2025-04-01 - Streamlined Bot Architecture and Enhanced User Experience

### Added
- 🌐 **Internationalized Error Messages:** Implemented support for localized error messages (timeout and generic errors) within bots across English, German, French, and Italian, enhancing the user experience.

### Changed
- 🐛 **Improved OpenAI Error Handling:** Enhanced error handling for OpenAI API status errors, providing more specific and user-friendly messages directly from the API.
- ⚙️ **Standardized Database Connection:** Updated bot database connections to use a configurable database name and collection name (`bot_paths`), improving consistency and flexibility.
- 📡 **Refined Channel Detection:** Improved detection of specific channels, specifically for "webchat", by using the `Channels.webchat` enum.

### Refactor
- 🧹 **Unified Bot Architecture:** Introduced `BaseChatBot` to centralize common chatbot functionalities like conversation handling, message processing, typing indicators, and error management, simplifying individual bot implementations.
- 🔄 **Refactored Completion Handling:** Renamed the core `Service` class to `CompletionHandler` and restructured it as an abstract strategy interface, allowing for clear separation and consistent handling of different completion types (e.g., OpenAI, Agent).
- ⚡️ **Centralized Route Management:** Extracted and consolidated route-specific logic, such as path retrieval and adapter management, into a new `RoutesService` for cleaner separation of concerns.
- 🧹 **Streamlined Bot Implementations:** Agent and OpenAI chatbots (`AgentChatBot`, `OpenaiChatBot`, `StreamAgentChatBot`, `StreamOpenaiChatBot`) have been significantly simplified by leveraging the new `BaseChatBot` and `CompletionHandler` architecture.
- 📄 **Code Organization:** Performed extensive renaming and relocation of core bot files to improve modularity and readability.

---



## [v0.134.0] - 2025-04-01 - Core Library Update and Version Synchronization

### Changed
- 🔄 **Synchronized Core Library:** All services (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) have been updated to use the latest `aihub-lib` version `v0.134.0`.
- 🚀 **Version Increment:** The version of all core services and the main `aihub_lib` has been bumped to `v0.134.0` to reflect the latest release.

---



## [v0.133.0] - 2025-04-01 - Enhanced API Error Reporting

### Changed
- ⚡️ **Improved API Error Handling:** The `ExceptionEvent` now includes an `http_status_code` field, enabling API endpoints to propagate specific HTTP status codes (e.g., 4xx, 5xx) from internal exceptions, leading to more precise error responses for client applications.

---



## [v0.132.0] - 2025-04-01 - Improved Chatbot Reliability and User Experience

### Added
- 🚀 **Introduced Comprehensive Exception Handling:** Implemented a new shared `handle_exception` method within the `Service` class to centralize and standardize error reporting and user feedback across all chatbot types.
- ⏱️ **Added Chatbot Response Timeout:** Implemented a timeout mechanism for the "typing" indicator, automatically informing users with a friendly message if a chatbot takes too long to respond.

### Changed
- 🦾 **Enhanced Chatbot Error Resilience:** Integrated the new centralized exception handling into `AgentChatBot`, `StreamAgentChatBot`, `OpenaiChatBot`, and `StreamOpenaiChatBot` to gracefully manage various errors and provide clearer feedback to users.

### Fixed
- 🐛 **Corrected Agent Service Exception Propagation:** Ensured that underlying exceptions (represented as `ExceptionEvent`s) from core agent services are properly caught and re-raised, allowing for consistent and robust error handling by the chatbots.

---



## [v0.131.0] - 2025-04-01 - Enhanced Markdown Parsing and Core Library Update

### Fixed
- 🐛 **Improved Markdown Parsing Robustness:** The `MarkdownStructuralNodeParser` now correctly unescapes HTML entities within Markdown content, ensuring accurate processing and splitting of documents that may contain such characters.

### Changed
- 🔄 **Updated Core Library Dependency:** All microservices, including the Agent, API, Bot, and Pipeline, have been updated to utilize the latest `aihub-lib` core library (`v0.131.0`).

---



## [v0.130.0] - 2025-03-31 - Unleash Agent Insights: Workflow Visualization and Dynamic API Discovery

### Added
- ✨ **Agent Workflow Visualization**: Agents now expose their internal step-by-step logic as a comprehensive network graph, viewable in a new dedicated admin panel in the Web UI. This includes detailed insights into step inputs, outputs, and event schemas.
- 🚀 **Dynamic API Service Discovery**: A new `/suite` API endpoint provides a structured list of all available API services (controllers), including their localized names, descriptions, and icons. The Web UI now leverages this for dynamic service navigation.
- ⚙️ **New Agent Admin Pages**: Introduces dedicated admin pages in the Web UI for comprehensive agent management and inspection, displaying detailed configurations and interactive workflow visualizations.
- 🎨 **Step Icons**: Agent steps can now define a visual `icon` which is displayed in the new workflow visualization, improving clarity and intuitiveness.
- ℹ️ **Localized Agent Configuration**: Agent configurations (`AgentConfigDTO`) now support localized names, descriptions, and system prompts, providing a more tailored experience across different languages.
- 👤 **User Settings Interface**: A basic user settings component has been added to the Web UI, including a logout option.
- 📄 **Dedicated Event Form Components**: Initial components for displaying event forms, such as `UserMessageEvent.vue`, have been introduced to the Web UI.

### Changed
- 🌐 **Comprehensive API Localization**: All API controllers (`AgentController`, `EventController`, `I18nController`, `OpenaiController`, `ThreadController`, `TokenController`, `UserController`) now define localized names, descriptions, and icons for improved OpenAPI documentation and client-side discoverability.
- 🧩 **Enhanced Agent Definition**: The `Agent` abstract base class now explicitly aggregates and exposes all output event types (`get_output_events`) produced by its steps, enabling more accurate workflow analysis and visualization.
- 🤖 **Improved Agent Step Decorator**: The `@step` decorator now supports `name`, `description`, and `icon` attributes for better UI representation and clarity of individual agent steps.
- 🔑 **Robust Authentication Flow**: The OIDC authentication middleware has been improved to handle silent token renewal more robustly, enhancing session management and reducing unexpected logouts.
- 💅 **Updated Web UI Theming**: The default primary color scheme of the Web UI theme has been updated for a fresh visual appearance.
- ⚡️ **Dynamic Web UI Navigation**: The main layout and navigation of the Web UI have been refactored to dynamically load and display services based on the new `/suite` API endpoint.
- 👤 **Simplified User Data Access**: The `UserController.get_user` endpoint has been renamed to `get_my_user` and now returns a dedicated `MyUserDTO` for the authenticated user, streamlining user profile handling.

### Fixed
- 🐛 **Reliable Function Signature Extraction**: Improved the extraction of return event types from function signatures within the agent workflow system for increased accuracy and stability.

### Refactor
- 🔄 **Standardized Runner Architecture**: Introduced a new abstract `Runner` base class to provide a consistent and extensible foundation for building all FastAPI applications (API and Bot services), improving code reusability and maintainability.
- 🧹 **Unified Frontend Types**: The Web UI now exclusively relies on OpenAPI generated SDK types, removing redundant manual type definitions and ensuring strict consistency with the backend API.
- 🗑️ **Consolidated Persistence Modules**: The `EventPersister` module has been reorganized into a dedicated `events` subpackage for better modularity.
- 🔠 **Component Naming Conventions**: Web UI components under `components/thread` have been renamed to follow PascalCase (`Thread/Chat.vue`, `Thread/ThreadList.vue`) for consistency.
- ⚙️ **Updated ESLint Configuration**: The Web UI's ESLint setup has been enhanced with new rules for import sorting, SonarJS quality checks, and Tailwind CSS linting for improved code quality.

---



## [v0.129.0] - 2025-03-28 - New Iterative Agent Example and Workflow Testing Capabilities

### Added
- ✨ **Introduced `BoundedLoopAgent` example:** A new comprehensive playground example demonstrating how to build agents with **bounded iterative workflows**. This includes the agent itself, utilizing `RunContext` for state management, and showing how to define agent-specific configurations.
- 🦾 **Enhanced workflow testing with BDD:** Added dedicated **BDD feature files and Pytest tests** for the `BoundedLoopAgent` to validate its iterative behavior and event flow, providing a clear example of testing complex agent workflows.
- 📄 **Custom workflow events and configuration:** Implemented **`BoundedLoopAgentConfig`** to allow dynamic control over the loop iterations and defined **custom events (`BeginEvent`, `DecisionEvent`, `ProcessEvent`)** to orchestrate the iterative process within the `BoundedLoopAgent`.

---



## [v0.128.0] - 2025-03-27 - Pipeline Embedding Robustness Enhancement

### Fixed
- 🐛 **Improved Embedding Node Resilience:** The `embed_nodes` operation in the pipeline now includes enhanced error handling for `ValidationError` during batch processing. If an embedding model encounters a validation error for a batch of nodes, the operation will automatically attempt to split the batch and process it in smaller chunks, increasing the robustness and reliability of embedding pipelines.

---



## [v0.127.0] - 2025-03-25 - Enhanced Chat Bot Responsiveness

### Changed
- ⚡️ **Improved chat bot responsiveness** by implementing a continuous typing indicator, providing users with dynamic feedback while the bot processes their requests.

---



## [v0.126.0] - 2025-03-24 - Enhanced LLM Control with Configurable Timeouts

### Added
- ✨ **Introduced LLM Request Timeout:** Added a new `timeout` parameter to `ChatLLMConfig`, allowing users to specify a timeout in seconds (defaulting to 30.0s) for LLM model requests. This provides finer control over model interactions and helps manage long-running requests.

### Changed
- ⚙️ **Applied Configurable Timeouts to LLMs:** Integrated the new `timeout` parameter into the underlying LLM calls for `AzureOpenAILLMConfig` and `SelfHostedLLMConfig`. This ensures that all LLM interactions leveraging these configurations will respect the defined timeout duration.

---



## [v0.125.0] - 2025-03-21 - New WebUI Agent and Core API Improvements

### Added
- 🦾 **WebuiAgent Integration:** Introduced a new `WebuiAgent` that enables seamless integration with Open WebUI, allowing chat completions and streamed responses from WebUI-backed models.
- 🧪 **WebuiAgent Playground Examples:** Provided new playground examples to demonstrate the setup and usage of the `WebuiAgent`, facilitating easier testing and development.

### Changed
- 🔄 **OpenAI API Model Listing:** Enhanced the `/models` endpoint of the OpenAI API to include an option (`exclude_webui_agents`) to prevent recursive discovery of WebuiAgents, improving API stability.
- 💬 **Chat Completion Request Handling:** Refined the processing of chat completion requests, now expecting the `chat_id` to be passed within the `metadata` dictionary instead of as a top-level field.
- 🎨 **Image Generation Default Model:** Updated the default model for image generation requests to **DALL-E 3**, ensuring users benefit from the latest capabilities.
- 📊 **Performance Test Output:** Improved the performance test results table by adding an "Error" column, providing clearer insights into test failures.

### Removed
- 🗑️ **Direct `chat_id` Field:** The direct `chat_id` field has been removed from the `ChatCompletionRequest` DTO, as its functionality is now handled via the `metadata` field for consistency.

### Refactor
- 🧹 **Internal LLM Context Manager:** Adjusted the `ChatLLMConfig` context manager's type signature to explicitly return an `AsyncIterator[LLM]`, improving type consistency and internal API clarity.
- ⚡️ **Chat Service Model Naming:** Streamlined the internal derivation of model names within the `ChatService` to directly utilize `agent_class` and `agent_id` parameters, enhancing code readability.

---



## [v0.124.0] - 2025-03-21 - Streamlined Bot Data Management and Core Library Updates

### Changed
- 🚀 **Updated Core Library Dependencies:** All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) have been updated to use the latest `aihub-lib` (v0.124.0), ensuring consistency and access to the newest features.
- 💬 **Enhanced Chat Service Message Processing:** Adjusted the chat service's message content extraction logic to improve compatibility with updated message structures.
- 📡 **Flexible External Event Distribution:** Removed the requirement for an explicit agent-in-thread check during external event distribution, allowing for more dynamic and flexible event handling.

### Refactor
- 🗄️ **Consolidated Bot Database Connection:** The `aihub_bot` service now connects to a unified `aihub` database, streamlining data storage and management across services.
- 🏷️ **Renamed Bot Data Collections:** Persistence collections within `aihub_bot` have been renamed from `conversations` to `bot_conversations` and `paths` to `bot_paths` for clearer identification and organization.

---



## [v0.123.0] - 2025-03-21 - Enhanced Document Parsing and Metadata Management

### Added
- ✨ **New `MetadataExtractor` Interface:** Introduced an abstract interface for custom metadata extraction from document splits, allowing for more flexible and powerful document processing.
- 📄 **Expanded Node Metadata:** Added `reference_name` and `reference_url` fields to document node metadata, enabling richer source attribution and traceability for retrieved information.

### Changed
- 🔄 **Improved Markdown Parsing:** The `MarkdownStructuralNodeParser` now integrates with the new `MetadataExtractor`, allowing for dynamic metadata enrichment during the document splitting process.
- 📊 **Enhanced Metadata Reporting:** The `aihub_pipeline` now includes `reference_name` and `reference_url` in generated metadata tables, providing better visibility into document sources.

### Refactor
- 🧹 **Modular `Split` Definition:** The `Split` dataclass, used in document parsing, has been moved to its own dedicated module for improved code organization and reusability.
- ⚙️ **Internal Parser Improvements:** Refined the initialization logic of `MarkdownStructuralNodeParser` to leverage Pydantic v2 features, enhancing internal robustness and maintainability.

---



## [v0.122.0] - 2025-03-21 - Improved Exception Handling and Core Updates

### Changed
- ⚡️ **Enhanced Agent Event Handling**: The Agent Controller in the API now robustly handles `ExceptionEvent`s originating from agent operations, translating them into clear HTTP 500 errors to provide better feedback for API consumers.
- ⚠️ **Improved Chat Service Stability**: The `ChatService` in the core library has been updated to explicitly listen for and process `ExceptionEvent`s, ensuring that chat interactions gracefully terminate and log warnings when an underlying process encounters an error.
- 🔄 **Core Library Update**: All core services (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) have been updated to depend on the latest `aihub-lib` version, incorporating the aforementioned exception handling improvements across the platform.

---



## [v0.121.0] - 2025-03-20 - Enhanced Event Stream Ordering and Dispatching

### Added
- ✨ **Event Sequence Numbers:** Events now capture and expose their JetStream sequence number via a new `sequence_number` property, providing a guaranteed ordered stream for all event processing.

### Changed
- 🔄 **Precise Event Dispatching and Retrieval:** The agent's event dispatching and retrieval logic has been significantly updated. It now utilizes the reliable JetStream sequence numbers instead of timestamps, ensuring more accurate and consistent step triggering based on the exact order of events in the stream.

---



## [v0.120.0] - 2025-03-20 - Introducing Language Detection and Core Synchronization

### Added
- ✨ **Introduced Language Detection Utility:** Added a new `check_language` function within `aihub_lib` to intelligently detect the language of user queries (German, English, French, Italian, or other) using an LLM. This enables language-aware processing and prompt routing.

### Changed
- 🔄 **Synchronized Core Library Versions:** Updated all microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) to use the latest `aihub-lib` version, ensuring consistent functionality and access to new features.

### Refactor
- 🧹 **Streamlined IDE Project Configurations:** Cleaned up internal `.iml` project configuration files for `aihub_api` and `aihub_lib` to improve project setup and consistency.

---



## [v0.119.0] - 2025-03-19 - Enhanced Agent Event Naming and Core Updates

### Changed
- 🔄 **Improved Agent Event Naming**: Enhanced the dynamic naming of agent event endpoints by incorporating a route-based postfix. This refinement increases clarity and reduces potential naming conflicts for agents managing multiple event routes.

---



## [v0.118.0] - 2025-03-19 - Improved Event Serialization & Core Updates

### Added
- ✨ **Introduced `model_dump_json` to `BaseEvent`**: A new method for robust JSON serialization of events, ensuring that all data, including previously unknown fields, is correctly merged and preserved during serialization.

---



## [v0.117.0] - 2025-03-19 - Workflow Customization with Custom Events

### Added
- ✨ **New Playground Example for Custom Events:** Introduced a comprehensive example demonstrating how to create and utilize agents with custom `StartEvent` and `StopEvent` types, enabling more flexible and domain-specific workflow definitions.
- ⚙️ **Showcased Custom Start/Stop Event Agent:** Added `CustomStartStopEventAgent` as part of the new example, illustrating an agent capable of processing a custom start event and emitting a custom stop event with a defined payload.
- 📄 **Custom Event Definitions:** Included `MyCustomStartEvent` and `MyCustomStopEvent` to exemplify how to define application-specific `StartEvent` and `StopEvent` structures using Pydantic for robust data validation.
- 🧪 **Dedicated Test Suite for Custom Events:** Provided a full test suite using `pytest-bdd` and `AgentTestRunner` for the custom start/stop event agent, ensuring reliability and serving as a blueprint for testing custom event flows.

---



## [v0.116.0] - 2025-03-19 - Enhanced Thread Interaction and Agent Event Management

### Changed
- ✨ **Enhanced Thread Event Subscription**: Introduced a new `subscribe_to_thread` option in `ChatService`, allowing clients to receive all events within a chat thread. This provides a more comprehensive view and better control over multi-agent interactions by receiving events from any agent in the thread, not just the initially requested one.
- 🔄 **Refined Agent Interaction Initialization**: Updated `ChatService` and `AgentService` to consistently pass `agent_class` and `agent_id` parameters during JSON event interactions, improving clarity and control over agent communication flows.
- 🎯 **Precise Stop Event Handling**: Modified the stop event logic in `ChatService` (for both streaming and JSON interactions) to ensure that event processing gracefully ceases only when a stop signal is received from the *primary* agent requested by the user, preventing premature interruptions from other agents within complex multi-agent threads.
- 📊 **Dynamic Agent Reporting**: The `model_name` reported in `JsonResources` for JSON interactions now dynamically reflects the specific `agent_class` and `agent_id`, enabling more granular tracking and logging for agent activities.
- 🦾 **Robust Human-in-the-Loop Handling**: Improved the processing of Human-in-the-Loop (HITL) responses by correctly deserializing the request event and reusing its `display_id`, enhancing the continuity and traceability of HITL interactions.

### Refactor
- 🧹 **Codebase Cleanup**: Removed unnecessary imports from `OpenaiService` and `ExternalEventDistributor`, contributing to a cleaner and more efficient codebase.

---



## [v0.115.0] - 2025-03-19 - Enhanced Event Handling for Broader Integration

### Refactor
- 🔄 **Generalized Event Distribution**: The `WebSocketReceiver` component has been refactored and renamed to `ExternalEventDistributor`. This change broadens its scope, enabling it to process and route events from diverse external sources, including APIs, web sockets, and bot frameworks, instead of being limited to WebSocket-specific interactions.
- ⚡️ **Standardized External Events**: The `WSUserEvent` class has been renamed to `ExternalEvent`. This standardizes the event structure for all user-initiated inputs, ensuring a consistent approach regardless of the origin system.
- 🧹 **Updated Event Flow Across Services**: Core services like `aihub_api` and `aihub_bot` have been updated to utilize the new `ExternalEventDistributor` and `ExternalEvent` components, ensuring a unified and more extensible event processing architecture.
- 📄 **Improved Internal Documentation**: Updated docstrings and comments across the codebase to accurately reflect the generalized event handling system and its expanded capabilities.

### Removed
- 🗑️ **Deprecated WebSocket Receiver Modules**: Obsolete `WebSocketReceiver` specific files and dependencies have been removed. These components were superseded by the new, generalized `ExternalEventDistributor` architecture.

---



## [v0.114.0] - 2025-03-19 - Smarter Events, Safer APIs

### Added
- 🛡️ **Enhanced API Output Model Generation**: Introduced a new utility (`create_output_model`) to dynamically create Pydantic models for API responses, ensuring sensitive fields are automatically excluded, improving data security.
- 🧪 **Improved Event Deserialization Utilities**: Added new helper functions (`get_inheritance_depth`, `get_parent_classes_until_base`) to intelligently determine event inheritance hierarchies, crucial for robust deserialization.
- ✅ **Expanded Event System Test Coverage**: Integrated comprehensive new tests for `BaseEvent`'s enhanced deserialization, `is_*_event` properties, and handling of unknown and nested event types, ensuring the reliability of the new event architecture.
- 🚀 **New Playground Scenario for Unknown Events**: Included a new test scenario in the Agent-in-the-Loop workflow playground to validate the orchestrator's ability to gracefully handle and process events with unknown types from worker agents.
- 📄 **Enabled Logging in Playground Examples**: Added `enable_logging()` to various playground triggers for easier debugging and observation of workflow execution.

### Changed
- 🔒 **Secure Agent API Responses**: The Agent API now leverages the new output model generation to filter sensitive information from event responses, enhancing data privacy and security.
- 🔄 **Standardized Optional Workflow Start Event**: The optional workflow example now consistently uses a `StartEvent` instead of a `UserMessageEvent`, aligning with typical agent initiation patterns.

### Refactor
- 🧬 **Overhauled Core Event Handling with Type Properties**: Replaced numerous `isinstance()` checks across the codebase with new, declarative `is_*_event` properties (e.g., `is_start_event`, `is_display_event`, `is_control_event`) within the `BaseEvent`. This significantly improves type checking consistency, readability, and future extensibility of event handling logic.
- 🧩 **Intelligent Event Deserialization Fallback**: Enhanced `BaseEvent.deserialize_event` to intelligently identify the most specific known parent class when encountering an unknown event type, preserving data and context while ensuring forward compatibility. This includes support for extra fields.
- 🧹 **Streamlined Orchestrator Agent Logic**: Simplified the `OrchestratorAgent`'s step logic by leveraging the new generic event handling capabilities, reducing specific type checks for incoming agent-in-the-loop responses.
- ⚙️ **Optimized Event Publishing Checks**: Updated `JSPublisher` and `NCPublisher` to use the new `is_control_event` and `is_display_event` properties for more consistent event type validation during publishing.

---



## [v0.113.0] - 2025-03-17 - Smarter Event Persistence with Inheritance Support

### Refactor
- 🧹 **Streamlined Event Persistence:** The process of persisting events has been refactored, moving the core logic from `EventPersister` into a static method within the `PersistedEventEntity` itself for better encapsulation.

### Added
- ✨ **Introduced Event Inheritance Tracking:** A new computed property, `_parent_class_names`, has been added to `BaseEvent` to automatically record the full inheritance hierarchy of events.
- 💾 **New `event_parents` Field:** The `PersistedEventEntity` now includes an `event_parents` field, which stores the inheritance chain of each event, enabling more detailed event categorization and search.
- 🧪 **Simplified Local Development Authentication:** The `aihub_api` development playground now supports a `NoAuthHandler`, allowing for easier local testing without requiring complex authentication configurations.

### Changed
- 🔍 **Improved Event Querying:** Event retrieval methods within `PersistedEventEntity` have been updated to utilize the new `event_parents` field, significantly enhancing the flexibility and accuracy of queries, especially for inherited event types.

---



## [v0.112.0] - 2025-03-17 - Enhanced Chat Experiences and Human-in-the-Loop Workflows

### Added
- 🦾 **Human-in-the-Loop Support:** Introduced comprehensive handling for Human-in-the-Loop request and response events, enabling interactive agent workflows where models can solicit user input.
- ✨ **Expanded OpenAI API Parameters:** Added support for numerous new parameters in `ChatCompletionRequest` and `ImageGenerationRequest` DTOs, aligning more closely with the official OpenAI API specifications for greater flexibility.
- 🔗 **Persistent Thread ID Mapping:** Implemented a new mechanism to map external conversation identifiers (e.g., `chat_id` or bot `conversation.id`) to persistent internal `thread_id`s, ensuring consistent conversation tracking and continuation.

### Changed
- 🔄 **Unified Conversation Threading:** All chat interactions, including OpenAI API routes and bot frameworks, now consistently leverage a `thread_id` for robust and continuous conversation management across sessions.
- 📖 **Accurate Message History Reconstruction:** Improved the message history retrieval logic to correctly incorporate and order Human-in-the-Loop events, providing a more complete and coherent conversation transcript.
- 💬 **Smarter Chat Completion Responses:** Modified chat completion responses for both streaming and JSON formats to gracefully handle and indicate Human-in-the-Loop requests by including the prompt question in the final output.
- ⏱️ **Chronological Event Ordering:** Display events are now consistently retrieved and ordered by creation timestamp, ensuring accurate reconstruction of chat timelines and historical context.

---



## [v0.111.0] - 2025-03-17 - Enhanced Real-time Event Processing

### Changed
- ⚡️ **Optimized WebSocket Event Publishing:** The internal `WebSocketReceiver` has been refactored to use dedicated NATS publishers for different event types. This change ensures that time-sensitive `DisplayEvent`s are now published directly via NATS core for faster, real-time delivery, while critical events such as `StartEvent` and `HumanInTheLoopResponseEvent` continue to leverage NATS JetStream for reliable and persistent messaging. This improvement enhances overall messaging efficiency and reliability within the system.

---



## [v0.110.0] - 2025-03-14 - Improved Bot Interactions with Advanced File Handling

### Added
- ✨ **New `ContentExtractor` Module**: Introduced a dedicated module for comprehensive content extraction from bot activities, significantly enhancing the handling of diverse file and attachment types from platforms such as Slack and Microsoft Teams. This allows agents to process user-provided files more effectively.

### Refactor
- 🧹 **Centralized Bot Content Processing Logic**: The core bot service's content and attachment processing logic has been extracted into the new `ContentExtractor` module, leading to a cleaner architecture, better maintainability, and improved extensibility for future content and file types.

---



## [v0.109.0] - 2025-03-14 - Enhanced Bot Conversation Management and Attachment Handling

### Fixed
- 🐛 **Improved Microsoft Teams Conversation Reset:** Resolved an issue where bot conversations in Microsoft Teams were not properly reset when the bot was added to a conversation, ensuring a fresh interaction context for new sessions.

### Added
- ⚡️ **Base64 Encoding Utility:** Introduced a new internal utility to fetch and encode URL-based content (e.g., images) into base64 data URLs, streamlining the processing of various attachments.
- 📄 **Conversation Deletion Functionality:** Added the ability to explicitly delete existing bot conversations, providing more granular control over conversation states and data retention.

### Refactor
- 🧹 **Standardized Attachment Processing:** Refactored the internal logic for handling image and text file attachments from platforms like Slack and Microsoft Teams to consistently utilize the new base64 encoding utility, enhancing reliability and maintainability of content processing.

---



## [v0.108.0] - 2025-03-13 - Asynchronous Preconditions for Enhanced Workflow Control

### Changed
- ⚡️ **Asynchronous Step Preconditions**: Workflow step `precondition` functions can now be defined as `async`, allowing for non-blocking I/O operations (e.g., API calls, database lookups) within your step readiness checks. This provides greater flexibility and control over workflow execution.

---



## [v0.107.0] - 2025-03-13 - API Enhancements and Core Alignment

### Added
- 🧹 **Agent Cache Management**: Introduced a new `clear_cache` static method to `AgentService` within the API, allowing for the programmatic clearing of in-memory agent discovery caches. This is particularly useful for testing and development to ensure fresh agent lookups.

---



## [v0.106.0] - 2025-03-11 - Streamlined Event Management and Core Library Alignment

### Refactor
- 🧹 **Consolidated Core Events**: Moved the `LLMStopEvent` from the `playground` examples into the `aihub_lib`'s core NATS events, establishing it as a standard and easily accessible event type within the library.
- 🔗 **Unified Event Import Paths**: Streamlined import statements for `LLMStopEvent` and `GuardRejectionEvent` across the `aihub_agent` and `aihub_api` services, allowing for consistent direct imports from `aihub_lib.nats.events`.
- 🗄️ **Improved Event Structure**: Enhanced the modularity and clarity of the event system by reorganizing `GuardRejectionEvent` into a new, dedicated `guard` subdirectory within `aihub_lib.nats.events`.

---



## [v0.105.0] - 2025-03-11 - Core Component Alignment and Documentation Refinements

### Changed
- 🔄 **Synchronized Component Versions:** All microservices (Agent, API, Bot, Pipeline) have been updated to align with the `v0.105.0` release of the central **aihub-lib** core library, ensuring consistent functionality and compatibility across the platform.
- 📄 **Documentation Syntax Improvement:** Applied minor syntax adjustments to Mermaid flowchart node labels within the **introduction documentation** for improved clarity and adherence to best practices.

---



## [v0.104.0] - 2025-03-10 - Deeper Integration with Slack and Teams Attachments

### Added
- ✨ **New Attachment Handling for Slack:** Bots can now process images and text files shared directly in Slack conversations by utilizing a configurable Slack OAuth token, significantly improving content recognition and interaction.
- 📄 **Configurable Slack OAuth Tokens:** Introduced the ability to store Slack OAuth tokens within the bot's configuration, enabling secure and direct access to Slack file attachments for comprehensive bot processing.
- 🖼️ **Enhanced Microsoft Teams File Support:** Bots now feature improved handling of native Teams file attachments, providing direct support for both image and text files shared within conversations.

### Changed
- 🔄 **Refined Message Content Processing:** The internal mechanism for processing user messages and attachments has been updated to consistently utilize `path` information, allowing for more channel-specific configurations and enhanced content extraction across platforms.
- 🚀 **Centralized Path Context in Conversation Services:** The bot's conversation services now uniformly pass `path` arguments to core message handling functions, enabling more dynamic and context-aware interactions for multi-channel deployments.

### Refactor
- 🧹 **Streamlined Text File Content Formatting:** Introduced an internal utility function to standardize the representation of text file content extracted from various attachments, improving code consistency.

---



## [v0.103.0] - 2025-03-10 - Improved Agent Orchestration with Direct API Access

### Added
- ✨ **New Agent API Endpoint:** Introduced a dedicated API endpoint (`/agent/{class}/{id}/send_event`) that allows direct initiation of agent workflows by sending `StartEvent`s and waiting for the final `StopEvent`, simplifying external system integrations.
- 🛠️ **Dynamic Pydantic Input Model Creation:** Added a utility (`create_input_model`) to automatically generate Pydantic input models for API endpoints, which filters out internal/generated fields from event schemas, leading to cleaner API contracts.
- 🧪 **Comprehensive API Tests:** Implemented new test cases to ensure the robustness and correct functionality of the newly introduced direct agent interaction API.

### Changed
- 🚀 **Semantic LLM Stop Events:** The `LLMWrappingAgent` now emits a more specific `LLMStopEvent` upon completion, enhancing event granularity and providing richer context for LLM-related workflow terminations.
- 🔄 **Expanded WebSocket Event Support:** The core `WSUserEvent` and WebSocket receiver have been updated to support a wider range of `StartEvent` types, enabling more flexible and powerful ways to initiate agent interactions via WebSockets.
- ⬆️ **Updated Simulation and Playground Examples:** The API test runner and development playground have been updated to leverage and showcase the new semantic event types and direct agent interaction capabilities.

### Refactor
- 🧹 **Clearer Stop Signal Naming:** Renamed internal `_stop_event` variables to `_stop_signal` across various runners and services for improved clarity and consistency in signaling termination.
- 📦 **Centralized LLMStopEvent:** The `LLMStopEvent` was moved from the `aihub_agent` specific location to a more central, reusable position within `aihub_lib`, making it a core semantic event available across the platform.
- ⚙️ **Refined Chat Service Event Handling:** The `ChatService` was refactored to explicitly store the final `StopEvent` and generalize the process of initiating JSON-based event interactions, improving the robustness and extensibility of chat workflow management.

---



## [v0.102.0] - 2025-03-07 - Improved Document Metadata Handling

### Changed
- ✨ **Enhanced `RefDocDocument` Metadata Retrieval:** Improved the robustness of `RefDocDocument` properties (`namespace`, `hash`, `uri`, `updated`) to safely retrieve metadata, preventing errors when fields are missing by providing sensible default values.
- 🔄 **Refined Document Metadata Inheritance:** Updated the `RefDocDocument` to prioritize existing metadata from `DataLakeFile` when enriching documents, ensuring more accurate and complete metadata preservation.

---



## [v0.101.0] - 2025-03-07 - Enhanced Agent Workflows and Infrastructure Reliability

### Added
- ✨ **Precondition Decorator:** Introduced a new `@precondition` decorator for workflow steps, allowing developers to define complex conditions that must be met before a step executes.
- 🚀 **JetStream Event Store:** Implemented a new `JetStreamEventStore` replacing the Redis-based event store, providing durable, ordered, and replayable event storage leveraging NATS JetStream.
- 📈 **Performance Testing Framework:** Added a dedicated performance testing framework with a `PerformanceTestingAgent` and utilities to benchmark agent workflow throughput and latency.
- 📄 **NATS Server Configuration:** Included a `nats.conf` file and updated Docker Compose for more explicit and configurable NATS server setup.

### Changed
- 🔄 **Event Storage Mechanism:** The underlying event storage for agent runs has been migrated from Redis to NATS JetStream, significantly enhancing reliability and data integrity.
- ⚡️ **Dispatcher Lifecycle Management:** The `Dispatcher` now includes explicit `start` and `stop` methods, allowing for more controlled initialization and graceful shutdown of agent workflows.
- ⚙️ **Optimized Step Execution Tracking:** Improved the efficiency of tracking step execution counts and preventing duplicate step calls by leveraging atomic Redis operations and MD5 hashing for event input keys.
- 📂 **NATS Stream Configuration:** Updated NATS JetStream stream settings to use file-based storage by default, increased maximum messages to 10 million, and reduced the duplicate window for better data management.
- 🔒 **Graceful Multiprocess Shutdown:** Enhanced the `MultiprocessAgentRunner` to respond robustly to termination signals (`SIGTERM`, `SIGINT`), ensuring cleaner shutdowns for agents running across multiple processes.
- 💨 **Agent Method Caching:** Applied caching to core agent methods (e.g., `get_steps`, `get_input_events`) to improve performance by reducing redundant computations.
- 📤 **Refined NATS Publishing:** Split event publishing responsibilities, using `JSPublisher` for durable `ControlEvent`s and `NCPublisher` for fast `DisplayEvent`s, optimizing event delivery.
- 📥 **Improved NATS Subscription Management:** `JSSubscriber` now limits concurrent message processing with a semaphore, enhancing stability, and explicitly subscribes to streams for more reliable message delivery.

### Removed
- 🗑️ **Redis-based Distributed Event Store:** The `DistributedEventStore` (Redis-based) has been removed, superseded by the new `JetStreamEventStore`.

---



## [v0.100.0] - 2025-03-07 - Enhanced Azure Bot Configuration and Structure

### Added
- ✨ **System Message Configuration for Azure Bots**: Introduced the capability to define a system message when setting up an Azure Bot. This can be provided via new command-line arguments (`--system-message` or `--system-message-file`) during the bot setup process, allowing for more precise control over the bot's initial behavior and persona.

### Refactor
- 🧹 **Bot Setup Script Relocation**: The `setup_azure_bot.py` script has been moved from the root of the `aihub_bot` directory to `aihub_bot/aihub_bot/` to improve project structure and maintainability.

### Changed
- 📄 **Updated Chatbot Documentation**: The documentation for chatbots has been updated to reflect the new path of the `setup_azure_bot.py` script, ensuring users can easily locate and utilize the deployment tool.

---



## [v0.99.0] - 2025-03-07 - Enhanced AI Conversation Context and Error Handling

### Added
- ✨ **Dynamic System Message Personalization**: Introduced support for the `{assistant_name}` placeholder in system messages, allowing for more personalized bot introductions and responses based on the bot's configured name.
- 📄 **Enhanced Conversation Message Metadata**: The conversation history now captures and persists the **`name` field** for all messages (user, bot, and system), providing richer context for interactions.
- 🦾 **OpenAI Chat Name Support**: Enabled the passing of cleaned user, bot, and system names to OpenAI chat completion requests, which is crucial for distinguishing participants in multi-turn conversations and when utilizing advanced features like tool calling.

### Fixed
- 🐛 **Robust OpenAI Chat Error Handling**: Improved stability by gracefully handling `BadRequestError` responses from OpenAI API calls, now displaying the specific error message to the user for better debugging and user experience. This applies to both standard and streaming chat completions.

---



## [v0.98.0] - 2025-03-06 - Multimodal Chat & Smarter Slack Interactions

### Added
- ✨ **Multimodal Input Support:** Bots can now process and respond to messages containing both text and attachments (e.g., images and text files), significantly enhancing conversational capabilities.
- 🖼️ **Enabled Image and Text File Attachments:** Users can now include images and text files directly in their messages, which the bot will interpret and incorporate into its responses.

### Changed
- ⚡️ **Improved Slack Channel Interaction:** Bots now respond more intelligently in Slack, engaging in direct messages, when explicitly mentioned, and automatically continuing conversations in threads where they were previously mentioned.
- 🔄 **Updated Conversation Data Model:** The internal message and conversation storage has been redesigned to flexibly support diverse content types, laying the groundwork for richer, more dynamic interactions.

### Refactor
- 🧹 **Consolidated Slack Message Processing:** Core logic for handling Slack messages has been centralized and streamlined for improved maintainability and clarity.
- ⚙️ **Standardized Content Conversion:** Internal methods for converting messages and content between different formats (e.g., persistence to LLM input) have been harmonized for better consistency.

---



## [v0.97.0] - 2025-03-06 - LLM Configuration Enhancements

### Added
- ✨ **Enhanced ChatLLM Configuration**: Introduced the ability to specify a **system prompt** directly when instantiating an LLM via the `cost_reporting_llm` context manager, allowing for more precise and dynamic model instructions.

---



## [v0.96.0] - 2025-03-06 - Enhanced Bot Stability and Core Service Update

### Changed
- 🚀 **Synchronized Core Service Versions:** All `aihub` components, including `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline`, have been updated to `v0.96.0`, ensuring consistent dependency management across the ecosystem.

### Fixed
- 🐛 **Improved Bot Message Handling:** Resolved an issue in `aihub_bot` where empty messages could potentially be sent. The `_send_buffer_to_user` method now includes a check to prevent sending messages when the buffer is empty, enhancing bot reliability and user experience.

---



## [v0.95.0] - 2025-03-06 - Enhanced User Experience and Configuration Standardization

### Added
- ✨ **Typing Indicators**: Introduced "typing" indicators in `AgentChatBot` and `OpenaiChatBot` to provide real-time feedback to users while the bot is generating a response, significantly improving user experience.
- 📄 **Standardized Playground Configurations**: Added new `.env` files for `testing` environments, ensuring consistent setup across development and testing playgrounds.

### Changed
- ⚙️ **Updated Environment Variable Naming**: Modified environment variable names and values in `.env` configurations for `development` and `testing` playgrounds to standardize Azure subscription and application naming conventions.

### Refactor
- 🧹 **Streamlined Text Sending Logic**: Refactored the internal text sending utility within `send_response_stream` to improve encapsulation and maintainability of the bot's response streaming mechanism.

---



## [v0.94.0] - 2025-03-05 - Improved Chat Experience and Core Configuration Flexibility

### Changed
- ✨ **Enhanced Bot Streaming for Long Responses:** Bots now provide a smoother user experience when generating lengthy responses by continuously updating the message in real-time. This also intelligently handles platform message limits by seamlessly transitioning to new messages when necessary.
- ⚙️ **Extended Azure App Name Flexibility:** The configuration for Azure `APP_NAME` now supports hyphens, allowing for more descriptive and flexible naming conventions in deployment setups.

### Fixed
- 🐛 **Improved Streaming Reliability:** Addressed a potential issue where bot streaming responses could time out or stall, ensuring robust and reliable message delivery even when streams conclude.

---



## [v0.93.0] - 2025-03-05 - Core Library Upgrade and Version Synchronization

### Changed
- 🚀 **Dependency Upgrade:** All core microservices, including `aihub_agent`, `aihub_api`, `aihub_bot`, and `aihub_pipeline`, have been synchronized to utilize the latest `aihub_lib` version `v0.93.0`, ensuring compatibility and integrating the newest shared functionalities.

---



## [v0.92.0] - 2025-03-05 - Enhanced RAG Agents with Context Sufficiency Guard

### Added
- 🛡️ **Introduced Context Sufficiency Guard for RAG Agents:** A new guard has been implemented that evaluates if the retrieved context is adequate to answer a user's query, helping to prevent the generation of responses based on incomplete or irrelevant information.
- ⚙️ **Configurable Context Sufficiency Check:** RAG agents now include a `check_context_sufficiency` configuration option, allowing users to enable or disable the new context sufficiency validation.
- 💬 **New Control Events for Context Sufficiency:** Added `ContextSufficientEvent` and `ContextInsufficientEvent` to clearly indicate the outcome of the context sufficiency check within the agent's operational flow.
- 🌍 **Internationalization for Context Guard:** Implemented new translation strings for the context sufficiency guard's prompts and messages across multiple languages (German, English, French, Italian).

### Changed
- 🔄 **Improved RAG Agent Response Handling:** The RAG agent's response generation logic now gracefully manages scenarios where the context is deemed insufficient, aligning its behavior with how few-shot rejections are handled.
- 🧹 **Minor Internal Cleanup in Few-Shot Guard:** Streamlined the `FewShotAcceptEvent` by removing a redundant `success` parameter, enhancing internal code consistency.

### Refactor
- 🏗️ **Prepared for Agent-in-the-Loop Events:** Established foundational directory structures and `__init__.py` files for upcoming `agent_in_the_loop` exception, request, and response events, setting the stage for future enhancements in agent interaction and control.

---



## [v0.91.0] - 2025-03-05 - Agent Scaling and Observability Improvements

### Added
- 🚀 **Multi-Process Agent Runner:** Introduced `MultiprocessAgentRunner` to enable horizontal scaling of agents by running multiple instances across separate processes, supporting true parallelism and improved performance.
- 🐳 **GPU-Enabled Docker Compose:** Added a new `docker-compose-gpu.yml` configuration to easily spin up a local AI infrastructure with GPU support for components like `llama.cpp` and Hugging Face Text Embeddings Inference (hf-TEI).

### Changed
- 📈 **Improved CI/CD Test Reporting:** Enhanced GitHub Actions for backend tests and pytest coverage comments to provide clearer and more organized reporting within pull requests and checks.
- ⚡️ **Agent Runner Redis Dependency:** The `AgentRunner` now explicitly requires a `redis_url` during initialization, indicating Redis as a core dependency for agent operations.
- 🔍 **Enhanced OpenInference Tracing:** Improved the accuracy and compliance of OpenInference tracing by ensuring semantic attributes are properly formatted, including JSON serialization for LLM invocation parameters and filtering out empty/None values.
- 📄 **Timestamped Logging:** Enabled timestamps with millisecond precision in console logs for better debugging and event correlation.

### Refactor
- 🧹 **Refined Distributed Event Store:** Enhanced the internal `DistributedEventStore` to improve type safety and efficiency in retrieving and caching `ControlEvent` objects.
- 🔄 **Optimized OpenTelemetry Span Management:** Adjusted the handling of OpenTelemetry spans, particularly for error states, to ensure more accurate and complete trace representations.
- 🧪 **Playground Example Cleanups:** Simplified and cleaned up existing playground examples by removing boilerplate and non-essential logic, improving clarity.

### Removed
- 🗑️ **Deprecated Docker Compose File:** Removed the non-functional `docker-compose-open-webui.yml` example.

---



## [v0.90.0] - 2025-03-04 - Enhanced Observability and Codebase Refinement

### Added
- ✨ **Logging Configuration**: Introduced `LoggingConfig` in `aihub_lib` to allow log levels to be dynamically set via environment variables for more flexible control.
- ⚡️ **Playground Logging**: Enabled enhanced logging in `aihub_api` and `aihub_bot` playground environments to leverage the new dynamic logging configuration.

### Changed
- 🚀 **Improved Tracing Performance**: Switched OpenTelemetry tracing in `aihub_agent` from `SimpleSpanProcessor` to `BatchSpanProcessor`, significantly enhancing trace export performance and reliability with optimized batching parameters.
- ⚙️ **Logging Control**: The `enable_logging` utility in `aihub_lib` now offers more flexible log level management, including the ability to configure library-specific log levels.

### Refactor
- 🧹 **Event Import Structure**: Streamlined the import paths for `AgentInTheLoop` events within `aihub_lib` for better code organization and clarity.
- 🗑️ **Codebase Cleanup**: Removed various unused imports across `aihub_api` and `aihub_bot` to reduce code clutter and improve maintainability.
- 📝 **Test Readability**: Enhanced the clarity and precision of test function names in `aihub_agent` playground tests.
- 📄 **Test Setup Simplification**: Simplified the `test_run` context manager usage in `aihub_agent` playground by removing an unused variable.

---



## [v0.89.0] - 2025-03-03 - Enhanced Agent Dispatcher for Idempotent Step Execution

### Added
- ✨ **Introduced Idempotent Step Execution:** The agent dispatcher now prevents redundant processing by ensuring that each step, when called with the exact same set of input control events within a run, is executed only once. This improves efficiency and consistency.
- 🚀 **New Step Store Event Tracking:** Implemented new capabilities within the `StepStore` to record and query previous step executions based on their specific input control events, supporting the new idempotency feature.

---



## [v0.88.0] - 2025-03-03 - NATS Reliability & Performance Enhancements

### Changed
- 🚀 **NATS JetStream Configuration:** Updated the **AgentRunner** to initialize NATS JetStream with a 60-second timeout and a maximum of 10,000 pending asynchronous publish messages, enhancing performance and reliability for high-volume event handling.
- 🔗 **Robust NATS Event Publishing:** Improved the **JSPublisher** to include automatic retries (up to 10 attempts), timeouts, and message deduplication via a unique `Nats-Msg-Id`. This significantly increases the reliability of event delivery and resilience to transient network issues.
- ⚙️ **Optimized NATS Stream Defaults:** Modified the **StreamManager** to configure new NATS streams with in-memory storage (instead of file-based) and introduced specific retention policies (1,000,000 max messages, 30-day max age, 1-hour duplicate window). This optimizes resource usage and ensures efficient message management.
- 📦 **Streamlined NATS Docker Image:** Switched the NATS service in `docker-compose.yml` to use the lighter `nats:alpine` Docker image, reducing image size and accelerating deployment times.

### Refactor
- 🧹 **Unified Development Workflow:** Standardized the order of `format` and `lint` commands in the `pr-ready` Makefile target across all microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_pipeline`) for consistent developer experience.

---



## [v0.87.0] - 2025-03-03 - Redis-Powered State Management and Workflow Optimizations

### Added
- ✨ **Redis Configuration**: Introduced a dedicated `RedisConfig` class to centralize Redis connection settings, enabling more straightforward configuration and management of distributed storage.

### Changed
- 🚀 **Redis for Distributed State Storage**: Migrated core distributed state management for agents from NATS JetStream Key-Value stores to Redis, significantly enhancing performance and scalability for event and step execution tracking.
- ⚡️ **Optimized Event Retrieval in Dispatcher**: The Dispatcher now employs more targeted event retrieval methods, fetching only necessary event types, which improves efficiency and reduces unnecessary data processing.
- ⚙️ **Enhanced NATS Stream Durability**: Configured NATS streams to utilize `FILE` storage by default instead of `MEMORY`, ensuring greater data persistence and reliability across system restarts.
- 🧹 **Development Workflow Enhancements**: Incorporated `lint` checks into the `pr-ready` Makefile targets across all microservices, raising the standard for code quality and consistency.

### Fixed
- 🐛 **Predictable `wait_for_event` Behavior**: The `AgentTestRunner`'s `wait_for_event` method now explicitly raises `StopIteration` when the anticipated event is not observed, providing clearer and more reliable test outcomes.

### Refactor
- 🔄 **Re-architected Event and Step Stores**: Overhauled the underlying `StoreBase`, `DistributedEventStore`, and `DistributedStepStore` implementations to leverage Redis, ensuring robust, race-condition-free event and step tracking by storing each event under a unique key.
- 🗑️ **Streamlined Import Statements**: Removed several unused `StartEvent` and other general import statements across various agents and libraries, contributing to a cleaner and more focused codebase.

---



## [v0.86.0] - 2025-03-03 - Core Version Alignment and Bot Refinements

### Changed
- 🔄 **Synchronized Core Library and Service Versions**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) and the `aihub_lib` dependency have been updated to version `v0.86.0`, ensuring consistent versioning across the platform.

### Refactor
- 🧹 **Streamlined Bot System Message Handling**: Removed redundant explicit calls to `get_system_message` within the `StreamAgentChatBot`, `OpenaiChatBot`, and `StreamOpenaiChatBot` implementations, simplifying the internal logic for chat prompt preparation.

---



## [v0.85.0] - 2025-02-28 - Core Library Synchronization and Compatibility Update

### Changed
- 🔄 **Core Library Synchronization:** Aligned all microservices (Agent, API, Bot, Pipeline) to use the latest `aihub-lib` version (`v0.85.0`), ensuring consistent functionality and access to the most recent enhancements across the platform.
- ⚙️ **Document Intelligence Loader Compatibility:** Updated the `DocumentIntelligenceLoader` within `aihub-lib` to adjust a parameter name (`analyze_request` to `body`) when calling the `begin_analyze_document` method, ensuring continued compatibility with the underlying Azure Document Intelligence SDK.

---



## [v0.84.0] - 2025-02-28 - Core Updates and Event Stream Refinements

### Removed
- 🗑️ **Deprecated `LimitChatHistoryWithContextEvent`:** Removed an event previously used for limiting chat history and context, streamlining event definitions within the basic `FewShotAgent`.

---



## [v0.83.0] - 2025-02-27 - Streamlined Data Storage and Internal Improvements

### Changed
- ⚡️ **Optimized NATS JetStream Storage**: Switched the default storage type for Key-Value (KV) stores and streams from file-based (`StorageType.FILE`) to in-memory (`StorageType.MEMORY`) across core components in `aihub_lib` and `aihub_agent`. This change significantly enhances performance and reduces disk I/O for temporary and context-specific data, such as run and thread contexts.
- 🔄 **Refined KV Store Initialization**: Improved the error handling logic during Key-Value store creation within `aihub_agent`. This enhancement ensures more robust and seamless operation by gracefully retrieving existing stores when a creation attempt fails.

---



## [v0.82.0] - 2025-02-27 - Core Enhancements: Caching, Dispatcher Logic, and Store Simplification

### Added
- ✨ **Introduced Caching for Event Store Data**: Implemented `TTLCache` in the `DistributedEventStore` to significantly improve performance when retrieving JSON values by caching frequently accessed data for 5 minutes.

### Changed
- 🔄 **Refined Step Execution Counting**: The dispatcher now precisely increments step execution counts only for methods explicitly configured with `_max_executions_per_run`, optimizing performance by avoiding unnecessary updates for steps without limits.

### Removed
- 🗑️ **Streamlined StoreBase Logic**: The generic `retry_operation` method has been removed from `StoreBase`, simplifying the base store implementation.
- 🧹 **Deprecated BaseContext Concurrency Primitives**: The `synchronized_update` method and associated mutex/retry logic have been removed from `BaseContext`, streamlining the NATS context and centralizing concurrency control where specifically required.

---



## [v0.81.0] - 2025-02-27 - Agent Stability and Concurrency Enhancements

### Refactor
- 🔄 **Re-engineered Distributed Event and Step Stores**: Implemented a new, highly concurrent storage model for events and step execution counts. This replaces the previous mutex-based synchronization with an append-only, unique-key per entry strategy, significantly improving reliability and eliminating race conditions in distributed environments.
- 🧹 **Optimized Event Fetching in Dispatcher**: Refactored the `Dispatcher` to pre-fetch all necessary events once per trigger cycle and pass them to subsequent step readiness checks and executions, reducing redundant calls to the event store and improving performance.

### Changed
- ⚡️ **Improved Key-Value Store Robustness**: Increased the maximum retry attempts and refined the backoff strategy for Key-Value store operations, enhancing resilience against transient network issues and concurrent access.
- 🐛 **Enhanced Key-Value Store Error Handling**: Added more specific error handling for Key-Value store creation and deletion, ensuring smoother operation and clearer logging for common scenarios.
- 📄 **Updated Example Agent Configuration**: Applied `max_executions_per_run=1` to a step in the `OptionalAgent` example, demonstrating the step execution limits feature and improving the example's clarity.

---



## [v0.80.0] - 2025-02-27 - Enhanced Internationalization Capabilities

### Changed
- 🌐 **Locale Handling Improvements**: The `LocaleHandler` now supports passing additional keyword arguments to the underlying internationalization function, enabling more dynamic and flexible message translation with embedded placeholders.

---



## [v0.79.0] - 2025-02-27 - Strengthened Data Integrity with Synchronized Updates

### Added
- 🛡️ **Introduced Synchronized Update Mechanism**: Added `synchronized_update` method to `StoreBase` and `BaseContext`, providing a robust mutex-based pattern to prevent race conditions during concurrent updates to key-value store entries.
- 🚀 **New KV Store Utility Methods**: Added `get_value`, `put_json_value`, `get_json_value`, and `atomic_operation` to `StoreBase` for more flexible, reliable, and convenient interaction with NATS JetStream Key-Value stores.
- ⚡️ **Configurable Retry Logic**: Implemented `max_retries` and `base_backoff` configurations in `StoreBase` and `BaseContext` to enable resilient operations with automatic retries for transient errors.

### Changed
- 🔄 **Improved Event and Step Stores**: Refactored `DistributedEventStore` and `DistributedStepStore` to leverage the new `synchronized_update` method, ensuring safe and consistent data operations (e.g., appending events, incrementing step counts) under concurrent access.
- 🧹 **Refined KV Data Retrieval**: Enhanced `get_all_events` in `DistributedEventStore` and `get_all` in `BaseContext` to automatically filter out internal mutex keys, providing cleaner and more relevant data results.
- 🐛 **Enhanced Crash Detection Reliability**: Updated `is_run_crashed` in `DistributedStepStore` to use the new generic `get_value` method, improving its robustness and consistency.

---



## [v0.78.0] - 2025-02-27 - Streamlined Azure AI Search Integration

### Changed
- ⚡️ **Improved Azure AI Search Vector Store Initialization:** Simplified the creation of Azure AI Search vector stores by automatically applying a default semantic configuration if none is explicitly provided, enhancing ease of use for semantic search capabilities.

---



## [v0.77.0] - 2025-02-26 - Enhanced NATS JetStream Reliability

### Changed
- 🚀 **Improved NATS JetStream Message Handling:** The JetStream subscriber (`JSSubscriber`) now explicitly acknowledges messages immediately upon receipt, simplifying the message flow and enhancing processing robustness. This change also includes handling for `MsgAlreadyAckdError` to prevent unexpected errors during acknowledgment.

---



## [v0.76.0] - 2025-02-26 - Enhanced Message Reliability and Core Updates

### Fixed
- 🐛 **Improved NATS JetStream Message Reliability:** Corrected the message acknowledgment order in `JSSubscriber` to ensure messages are only acknowledged *after* successful processing by the handler, preventing potential message loss and improving robustness in case of processing errors.

---



## [v0.75.0] - 2025-02-26 - Core Library Enhancements for NATS Subscribers

### Changed
- ⚡️ **Improved NATS Message Processing:** The `JSSubscriber` and `NCSubscriber` components have been updated to process incoming NATS messages asynchronously. This change prevents blocking of the main message loop, significantly enhancing the overall responsiveness and concurrency of event handling.
- 🔄 **Refactored NATS Subscriber Error Handling:** Message processing and acknowledgment within the NATS subscribers now occur in dedicated asynchronous tasks, ensuring more robust error handling and preventing transient issues from interrupting the continuous flow of incoming messages.

---



## [v0.74.0] - 2025-02-26 - Metadata Precision and Core Synchronization

### Fixed
- 🐛 **Improved Document Metadata Accuracy:** Addressed an issue in `RefDocDocument` where the document's URI was incorrectly used instead of the `DataLakeFile`'s URI when enriching metadata, ensuring proper title extraction from the correct source.

---



## [v0.73.0] - 2025-02-26 - Enhanced Core Stability

### Fixed
- 🐛 **Improved WebSocket Event Handling:** Implemented a more robust check within the WebSocket receiver to prevent potential errors when handling `start` events, ensuring that event messages are properly processed even if the `messages` attribute is not initially present.

---



## [v0.72.0] - 2025-02-26 - Enhanced Document Metadata for Improved RAG

### Added
- 📄 **Enriched Document Metadata**: The `RefDocDocument` now automatically extracts and includes the `SOURCE` (the original data lake URI) and `DOCUMENT_TITLE` (the filename extracted from the URI) in its metadata when documents are ingested. This enhancement improves the traceability and searchability of documents within the RAG system.

---



## [v0.71.0] - 2025-02-26 - Synchronized Core Services and Enhanced LLM Compatibility

### Changed
- ⚙️ **Synchronized Core Components**: All `aihub` microservices (`agent`, `api`, `bot`, `pipeline`) and the core `aihub-lib` have been updated and synchronized to version `v0.71.0`, ensuring consistent dependency management across the ecosystem.
- 💬 **Improved Self-Hosted LLM Compatibility**: Enhanced the tokenizer loading logic for self-hosted Large Language Models to correctly parse model names containing common quantization suffixes such as `-bnb` and `-4bit`.

---



## [v0.70.0] - 2025-02-26 - Enhanced Azure OpenAI Authentication Options

### Added
- ✨ **Azure OpenAI API Key Support:** Introduced the ability to authenticate Azure OpenAI Large Language Models using a direct API key, providing an alternative to Azure AD for improved configuration flexibility.

---



## [v0.69.0] - 2025-02-25 - Core Component Update and Build Process Improvements

### Changed
- 🔄 **Synchronized Core Components**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) and the shared **`aihub_lib`** have been updated to `v0.69.0`, ensuring consistent versioning and dependency alignment across the ecosystem.
- 🚀 **Enhanced CI/CD Workflow**: The GitHub Actions `add-tag.yml` workflow has been optimized for efficiency and reliability, including improved Python setup caching and more robust Poetry dependency installation steps (`poetry lock` and `poetry install`) for release automation.

---



## [v0.68.0] - 2025-02-25 - Enhanced Self-Hosted LLM Tokenization

### Fixed
- 🐛 **Improved Self-Hosted LLM Tokenizer Loading:** Resolved an issue where tokenizers for self-hosted Large Language Models (LLMs) might fail to load due to model name suffixes (e.g., `-GGUF`, `-AWQ`). The system now correctly extracts the base model name for accurate tokenizer retrieval and directly provides the encoding function, making it more robust and immediately usable.

---



## [v0.67.0] - 2025-02-25 - Development Workflow Updates and Script Refinements

### Changed
- ⚙️ **Enhanced Development Script Execution:** Updated `Makefile` commands to leverage `poetry run` when executing the dependency switching script, ensuring consistent execution within the Poetry-managed environment and streamlining developer workflows.

### Refactor
- 🧹 **Renamed Dependency Management Script:** The script responsible for switching between local and remote core dependencies has been renamed from `switch_dependency.py` to `switch_dependencies.py` for improved clarity and naming consistency.

---



## [v0.66.0] - 2025-02-25 - Revamped User Interface and Flexible Authentication

### Added
- ✨ **Enhanced User Information**: The API now provides richer user details, including profile images fetched directly from Azure AD, for a more personalized experience across the platform.
- 🚀 **Dynamic Authentication Strategy**: Introduced a new composite authentication handler (`TokenAndOauth2Handler`), allowing the API to seamlessly support multiple authentication methods simultaneously, such as OAuth2 (Azure AD) and API Tokens.
- 🖼️ **Modern Application Layout**: Implemented a new, intuitive default layout for the web application, featuring a dynamic sidebar for quick navigation, a comprehensive top bar with breadcrumbs and user details, and an improved overall user interface.
- 📊 **New OpenAPI Client SDK**: Integrated an auto-generated TypeScript SDK for the frontend, ensuring more robust, type-safe, and efficient communication with the backend API.
- 🔒 **Seamless Session Renewal**: Added support for silent OIDC token renewal in the web application, significantly improving user session management and reducing the frequency of login prompts.
- 👤 **User Data Persistence Layer**: Laid the foundational groundwork for future personalized features by introducing a dedicated entity for storing user-specific data in the backend.
- 🌐 **Open Web UI Integration Page**: Incorporated a new page specifically designed for seamlessly integrating and accessing the Open Web UI module directly within the application.
- 📈 **Standardized Health Check Response**: Introduced a new `HealthResponse` DTO to provide a consistent and explicit structure for the health check endpoint's output.

### Changed
- 🔄 **UI Framework Migration**: Completed the migration of the web application's core UI components from `shadcn/ui` to **PrimeVue**, resulting in a refreshed visual design, enhanced accessibility, and improved component functionality.
- ⚡️ **Improved API Authentication Integration**: Updated FastAPI endpoints to leverage the `Security` dependency for authentication, enabling more flexible and robust authentication flows.
- 🎨 **Login Page Redesign**: Overhauled the login experience with a modernized design and enhanced branding, providing a more professional and welcoming entry point.
- 📄 **API Operation ID Generation**: Configured API routes to automatically generate OpenAPI operation IDs, which improves API client generation and tooling support for developers.
- ℹ️ **User Information Retrieval Logic**: Refined the backend logic for fetching comprehensive user details, ensuring consistency and full utilization of the new profile image capabilities.

### Removed
- 🗑️ **Legacy UI Components**: Deprecated and removed all `shadcn/ui` components and their associated configurations, streamlining the frontend codebase following the UI framework migration.
- ❌ **Outdated Multi-Authentication Handler**: Replaced the previous generic `MultiAuthHandler` with the more specialized and integrated `TokenAndOauth2Handler`.

---



## [v0.65.0] - 2025-02-25 - Enhanced LLM Integration and Agent Flexibility

### Changed
- 🔄 **Expanded LLM Compatibility for `LLMWrappingAgent`**: The `LLMWrappingAgent` now utilizes a more generic `ChatLLMConfig`, enabling seamless integration with a broader array of Large Language Models beyond just Azure OpenAI.

---



## [v0.64.0] - 2025-02-24 - Core Synchronization and Dispatcher Improvement

### Changed
- ⚙️ **Improved Locale Retrieval:** Ensured that a default locale is always provided when retrieving locale information from the run context, enhancing robustness and preventing potential errors in agent execution.

### Refactor
- 🧹 **Internal Code Cleanup:** Reordered import statements within the dispatcher module for improved code consistency and readability.

---



## [v0.63.0] - 2025-02-21 - Core Library Updates and Guard Enhancements

### Changed
- ⚡️ **Improved `AgentTestRunner` Functionality:** Enhanced `get_events` and `get_events_of_type` methods in `AgentTestRunner` with an `event_filter` parameter, allowing for more precise event retrieval during testing.
- 🦾 **Refined Few-Shot Guard Prompting:** Updated the internal prompt for the **Few-Shot Guard** across all supported languages (DE, EN, FR, IT) to enforce a stricter and more reliable JSON output format from Large Language Models, improving the guard's robustness and parsing.
- 🔄 **Updated Core Library Dependencies:** All microservices have been updated to utilize the latest `v0.63.0` version of the `aihub_lib` core library, bringing in the latest improvements and fixes.

---



## [v0.62.0] - 2025-02-20 - Developer Experience Improvements and CI/CD Refinements

### Changed
- ⚙️ **Refined backend test workflow** in CI/CD, allowing Poetry dependency installation to proceed before Docker services are fully healthy, potentially speeding up test execution.
- ✨ **Simplified `NoAuthHandler` configuration** for local development by providing sensible default user values directly in the configuration, reducing the need for manual `.env` file setup in the playground environment.

---



## [v0.61.0] - 2025-02-20 - Major Pipeline Overhaul: Modular Resources and Simplified Configuration

### Refactor
- 🧹 **Pipeline Resource Restructuring:** Underwent a significant refactoring of pipeline resource management, replacing a generic `NamespaceResource` with more granular and specific `DataLakeResource` and `DocStoreResource` for clearer configuration and improved modularity.
- ⚙️ **Streamlined LLM Configuration:** Simplified the setup of Large Language Model (LLM) resources by removing the `LlmHandlerResource` and enabling direct configuration of `EmbeddingModelResource` and `LanguageModelResource` with their respective Azure OpenAI or self-hosted configurations.
- 🗄️ **Direct Data Store Configuration:** Updated Data Lake, Document Store, and Vector Store resources to accept explicit names (e.g., container, database, vector store names) directly, reducing reliance on a common "namespace" abstraction for better clarity and control.
- 🚀 **Simplified Pipeline Job Definitions:** Streamlined pipeline job naming and configurations by removing customer-specific prefixes, allowing for more generic and reusable job definitions.
- 🌐 **Improved MongoDB Connection:** Enhanced the MongoDB connection utility for greater flexibility and robustness by directly using provided database names and adding comprehensive error handling.
- 🔄 **Refined Import Paths:** Cleaned up and standardized import paths across several modules for better code organization and maintainability.

### Added
- 💾 **New `DataLakeResource`:** Introduced a dedicated resource (`DataLakeResource`) to explicitly define Data Lake container and directory names, centralizing data lake configuration.
- 📚 **New `DocStoreResource`:** Added a specialized resource (`DocStoreResource`) for clear configuration of document store database and namespace names.

### Changed
- 🧩 **Flexible Asset Factory Inputs:** Enhanced `documents_factory` and `nodes_factory` to accept `AssetKey` types for data lake and document inputs, providing greater flexibility in pipeline definitions.
- 💡 **Conditional Azure AI Search Configuration:** Improved the `AzureAISearchVectorStoreFactory` to intelligently apply semantic configuration only when specified, allowing for more flexible vector store creation.
- 📊 **Refined Data Lake Asset Metadata:** Updated Data Lake asset materialization events to provide more relevant metadata, focusing on file counts and total size, and improved conditional reporting.
- 📄 **Enhanced Milvus Vector Store Documentation:** Expanded the documentation and examples for `MilvusVectorStoreResource` to improve clarity and ease of use.
- 🛠️ **Dagster Sensor API Update:** Adapted to the latest Dagster sensor API, transitioning from `asset_selection` to `target` for automation condition sensors.
- 📝 **Improved Document Content Reporting:** Switched to using `get_content()` instead of `get_text()` for `RefDocDocument` metadata, providing more relevant document representation in pipeline events.

### Removed
- 🗑️ **Deprecated Namespace Abstraction:** Eliminated the `NamespaceResource` and related utility functions, simplifying resource management by moving away from a generic namespace abstraction.
- 🚫 **Removed LLM Handler:** Deprecated and removed the `LlmHandlerResource`, as LLM configuration is now managed directly by individual LLM resource definitions.
- 🧹 **Removed Legacy Utility Modules:** Cleaned up outdated utility modules (`namespace_util.py`, `partition_utils.py`) that are no longer necessary after the resource management overhaul.

---



## [v0.60.0] - 2025-02-20 - Build Action Refinement and Core Version Alignment

### Changed
- ⚙️ **Updated Build Image Action:** The `file` input for the `build_image` GitHub Action no longer provides a default path, allowing for more flexible Dockerfile location specification.

---



## [v0.59.0] - 2025-02-20 - Core Component Upgrades and Enhanced Test Visibility

### Changed
- 🚀 **Upgraded `llama.cpp` LLM Server:** The `llama.cpp` Docker image has been updated to the latest stable `server` tag, ensuring access to recent performance improvements and bug fixes for local Large Language Model inference.
- ⚙️ **Improved Backend Test Diagnostics:** Added a `docker compose ps` command to the backend test GitHub Action, enhancing visibility and troubleshooting capabilities for service health during automated testing.

---



## [v0.58.0] - 2025-02-20 - Enhanced Build Flexibility and Core Service Updates

### Added
- ✨ **Enhanced Build Action:** The `build_image` GitHub Action now supports specifying a custom **Dockerfile path**, offering greater flexibility for image builds.

### Changed
- 🚀 **Core Service Updates:** All primary microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) and the **`aihub_lib` core library** have been updated to `v0.58.0`, ensuring compatibility and incorporating the latest improvements.

---



## [v0.57.0] - 2025-02-20 - Enhanced User Context and Open WebUI Authentication

### Added
- ✨ **New Open WebUI Authentication Handler:** Introduced `OpenWebuiAuthHandler` to seamlessly integrate with Open WebUI, allowing user authentication via specific HTTP headers and bearer tokens.
- 📄 **Fake User Utility for Testing:** Added a `fake_user` utility in `aihub_lib.testing.auth_utils` to simplify the creation of authenticated user objects for various test scenarios.

### Changed
- 🚀 **Enriched `UserMessageEvent`:** The `UserMessageEvent` now explicitly includes the full `AuthenticatedUser` object, providing more comprehensive user context directly within the event.
- 🔄 **Standardized User Object Propagation:** API and Bot services now consistently pass the complete `AuthenticatedUser` object to chat interaction methods, replacing previous fragmented `user_oid` usage for better consistency.

### Security
- 🔑 **Enhanced Agent Access Control:** Agent discovery within the OpenAI API is now secured by user access permissions, ensuring users can only interact with agents they are authorized to use.

### Refactor
- 🧹 **Streamlined User Context Handling:** Refactored internal chat services and WebSocket receivers to directly utilize the `AuthenticatedUser` object, improving consistency and clarity in user context management across the platform.

---



## [v0.56.0] - 2025-02-20 - Streamlined Release: Version Synchronization and CI Improvements

### Changed
- 🔄 **Core Component Versioning:** Synchronized the core `aihub-lib` and all microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) to version `v0.56.0`, ensuring consistent versioning across the ecosystem.
- 🚀 **Dependency Alignment:** Updated all microservices to consume the latest `v0.56.0` of `aihub-lib` and `aihub-core` dependencies, ensuring they benefit from the most recent shared capabilities.

### Added
- ⚡️ **Automated Dependency Updates in CI:** Implemented a new step in the CI/CD pipeline to automatically update `aihub-lib` version tags within `poetry.lock` files, enhancing release consistency and reducing manual overhead.

---



## [v0.55.0] - 2025-02-20 - OpenAI API Alignment and Conversational Agent Refinement

### Added
- ✨ **OpenAI API Compatibility for Agents**: Introduced new endpoints (`/openai/models` and `/openai/chat/completions`) to seamlessly integrate AI-Hub conversational agents into the OpenAI API standard, allowing agents to be discovered and interacted with just like LLM models.
- 💬 **`UserMessageEvent` for Conversational Inputs**: A new dedicated event, `UserMessageEvent`, is now the standard for initiating conversational workflows, clearly separating user messages from generic start events.
- ℹ️ **`is_conversational` Flag for Agent Discovery**: Agent discovery responses now include an `is_conversational` flag, enabling clients to easily identify agents capable of chat-based interactions.

### Changed
- 🗑️ **`StartEvent` Simplification**: The `StartEvent` has been streamlined to serve as a generic workflow trigger, no longer directly carrying chat history or locale information, which are now exclusively part of `UserMessageEvent`.
- ⚙️ **Agent Input Event Types**: Agent steps that process conversational input now strictly type-hint `UserMessageEvent` instead of the broader `StartEvent | UserMessageEvent`, ensuring more precise event handling.
- 🚨 **Improved API Error Handling**: Model and agent lookup failures in the OpenAI API endpoints now raise standard `HTTPException` instead of `ValueError` for consistent error responses.

### Removed
- ❌ **Deprecated `/chat` API Endpoints**: The old `/chat` API endpoints and their associated internal services and DTOs have been removed, with their functionality migrated to the new OpenAI-compatible endpoints.

### Refactor
- 🧹 **Unified Conversational Event Logic**: All logic related to user query extraction, chat history, and locale for conversational contexts has been centralized within the `UserMessageEvent` for better maintainability and clarity.
- 📦 **Event Content Relocation**: Chat message content classes (`AssistantChatMessage`, `UserChatMessage`) have been logically moved from `control.start.content` to `user.content`.

---



## [v0.54.0] - 2025-02-19 - Deepening Integration: API Tokens, Chatbots, and Refined Authentication

### Added
- 🤖 **Chatbot Core (`aihub_bot`)**: Introduced a new module for integrating AI agents with chat interfaces via Azure Bot Service, enabling seamless conversational interactions across multiple channels (e.g., Slack, MS Teams, WebChat).
- 🔑 **API Token Management**: New API endpoints and services (`/tokens`) have been added to `aihub_api`, allowing users to create, list, and revoke API access tokens for programmatic interaction.
- 🔄 **Unified Authentication Strategy**: Implemented a new `AuthHandler` interface and a `MultiAuthHandler` in `aihub_lib`, enabling a flexible composite authentication system that can chain various strategies like OAuth2 and API tokens.
- 🧑‍💻 **Development User Information Provider**: Added `DevUserInformationProvider` to simplify local development by providing a fixed user identity without requiring external authentication setups.
- 🧪 **API Test Infrastructure**: Introduced `ASGIAdapter` and comprehensive Python-based integration tests for `aihub_api`, replacing older `.http` client scripts to improve test reliability and execution speed.
- 📄 **Chatbot Documentation**: A new `13_chatbots.md` document provides in-depth guidance on chatbot design, technical implementation, and deployment within the AI-Hub ecosystem.
- 🦾 **Agent Stop Events**: Agents can now declare specific "stop events" during discovery, enhancing control and visibility over their termination conditions within a workflow.
- 🔑 **"AllAgents" Role for Access Control**: Introduced an "AllAgents" role, granting authenticated users comprehensive access to all registered agents, simplifying role-based access management.

### Changed
- 🔒 **API Endpoint Security**: Integrated the new `AuthHandler` interface across all `aihub_api` controllers, standardizing authentication and enforcing granular access control for chat and thread operations.
- 🔍 **Agent Discovery Protocol**: The agent discovery response (AgentDTO) now includes a list of `stop_events`, providing more complete lifecycle information for discovered agents.
- 🏗️ **Configuration Management**: Refactored core configuration classes, separating general `AzureBaseConfig` from API-specific settings now managed by `ApiConfig` for improved clarity and modularity.
- 🧪 **Bot Test Runner**: Enhanced the `BotTestRunner` and `SimulatedAgentBotTestRunner` to leverage `ASGIAdapter` for internal HTTP requests, making chatbot integration tests faster and more robust by eliminating external network dependencies.
- 🧩 **User Information Retrieval**: The `UserService` in `aihub_api` now uses a `MultiStrategyUserInformationProvider` to dynamically fetch user details from Azure AD, API tokens, or a development mock, increasing flexibility.
- 🌐 **Internationalization Endpoint**: Simplified the `/i18n/my-locale` endpoint in `aihub_api` to streamline locale information retrieval.
- 🗓️ **Thread Entity Persistence**: Added a `created_at` timestamp to `ThreadEntity` in `aihub_lib` for better auditing and historical tracking of conversations.
- 🧹 **CI/CD Pipeline Optimization**: Updated `lint_backend` and `test_backend` GitHub Actions to use improved Poetry caching and installation methods for faster, more reliable CI/CD runs.

### Removed
- 🗑️ **Deprecated Authentication Dependency**: The `use_oauth2_user` and `use_no_auth_user` functions in `aihub_lib` have been removed, replaced by the more modular `OAuth2AuthHandler` and `NoAuthHandler` classes.
- 🗑️ **Old Access Token Model**: The `AccessToken` persistence model in `aihub_lib` has been replaced by the more robust `BearerToken` entity, which supports the new API token management.
- 🗑️ **Outdated HTTP Client Tests**: All `.http` client test files in `aihub_api/playground/testing/tests` have been removed, superseded by new, comprehensive Python-based integration tests.

### Refactor
- 🧹 **Project Structure Alignment**: Adjusted references across modules (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`, `aihub_lib`) to align with the new authentication handler and configuration structure.
- ⚙️ **Internal API Simplification**: Streamlined the `RefDoc` querying methods by removing redundant `organization_shortname` parameters, enhancing code clarity.


---



## [v0.53.0] - 2025-02-19 - Authentication Overhaul and API Testing Advancements

### Added
- ✨ **New API Token Management System:** Introduced dedicated endpoints (`/tokens`) and services for creating, listing, and revoking API tokens, enabling more flexible and secure access.
- 🔑 **Multi-Strategy Authentication Handler:** Implemented a new `MultiAuthHandler` that allows the API to seamlessly support multiple authentication mechanisms (e.g., OAuth2, API Tokens, development-mode authentication) concurrently, enhancing flexibility.
- 🦾 **Dedicated Development User Provider:** Introduced `DevUserInformationProvider` for simplified local development and testing, providing a fixed user identity based on environment configurations.
- 📄 **Comprehensive API Test Suite:** Added an extensive suite of Python-based integration tests covering agent discovery, chat interactions, health checks, localization, OpenAI endpoints, thread management, API tokens, and user profiles, significantly improving test coverage and reliability.
- 🚀 **API Token Generation Script:** Provided a new utility script (`generate_api_token.py`) to easily create API tokens for administrative or testing purposes, streamlining setup.
- 📈 **Stop Event Discovery for Agents:** Agents can now declare `StopEvent` types, enhancing their discoverability and allowing clients to understand how agent workflows naturally conclude.

### Changed
- 🔄 **Centralized API Configuration:** Consolidated general API-related configurations into a new `ApiConfig` class, clearly separating them from Azure-specific infrastructure settings for better organization.
- ⚡️ **Improved CI/CD Python Setup:** Updated GitHub Actions workflows to leverage more efficient Poetry caching and dependency resolution during linting and testing phases.
- 🔒 **Enhanced Agent Access Control:** Modified the `AuthenticatedUser` to allow users with the "AllAgents" role to access any agent, simplifying role management for administrators.
- 📊 **Auth-Protected Health Endpoint:** The health check endpoint (`/health`) is now protected by the authentication layer, allowing flexible integration with different auth strategies.
- 🧵 **Thread Creation Endpoint Path:** Adjusted the thread creation endpoint from a path parameter (`/{thread_id}`) to a base path (`/`) for better RESTful consistency.

### Refactor
- 🧹 **Standardized Authentication Handlers:** Replaced direct FastAPI `Depends` functions with a new `AuthHandler` interface and dedicated handler classes (`OAuth2AuthHandler`, `TokenAuthHandler`, `NoAuthHandler`) for a more modular and extensible authentication system.
- 🏗️ **Streamlined User Information Providers:** Consolidated user information retrieval into a multi-strategy provider, allowing fetching user details from various sources (e.g., Azure AD, API tokens, development config).
- ⚙️ **Optimized Test Runner HTTP Calls:** Implemented `ASGIAdapter` in test runners to route internal HTTP requests directly to the FastAPI application, significantly speeding up integration tests by avoiding actual network calls.
- 📦 **Consolidated API Environment Configuration:** Moved the API's development `.env` file to a more unified location (`aihub_api/.env`) for consistent environment setup.
- 🔗 **Simplified Reference Document Queries:** Removed the `organization_shortname` parameter from `RefDoc` query methods, aligning with a more centralized database access approach.

### Fixed
- 🐛 **RAG Agent Few-Shot Rejection Message:** Corrected a minor issue in the RAG Agent's response generation for few-shot rejections, ensuring the system message is properly formatted.

---



## [v0.52.0] - 2025-02-19 - Bot Reliability and Core Dependency Alignment

### Changed
- 🚀 **Updated Core Library Dependency**: All main modules, including `aihub_agent`, `aihub_api`, `aihub_bot`, and `aihub_pipeline`, have been updated to depend on the latest `aihub-lib` version, `v0.52.0`, ensuring alignment with the latest core functionalities.

### Fixed
- 🐛 **Improved Conversation Message Retrieval**: Enhanced the `get_messages_by_conversation_id` method within `aihub_bot` to explicitly convert retrieved messages to a list and handle cases where no messages are present, improving reliability and preventing potential errors in conversation context loading.

### Refactor
- 🧹 **Refined Conversation Entity Type Hint**: Updated the internal type hint for conversation messages in `ConversationEntity` to `ListField` for better consistency and accuracy with the underlying database model.

---



## [v0.51.0] - 2025-02-19 - AI-Hub Evolution: Refined Vision and Expanded Architecture

### Changed
- 🔄 **AI-Hub Vision Reworked:** Significantly updated the introductory documentation (Section 1.1) to present the AI-Hub as a dynamic, multi-tiered platform offering, clarifying its evolution from basic LLM access to custom assistants and fully autonomous agents.
- 📄 **Expanded AI Capabilities Overview:** Reimagined Section 1.2 to detail the distinct value propositions of direct LLM Access, reactive AI Assistants, and proactive AI Agents, emphasizing their progression and collaborative nature within enterprise workflows.
- 🏗️ **Architectural Diagram Updated:** Revised the high-level architecture diagram and descriptions (Section 1.3) to reflect the comprehensive platform, including new user interfaces and integration components.

### Added
- 🚀 **New Tiered AI-Hub Offerings:** Introduced a clear four-tier structure for AI-Hub services, ranging from basic LLM access to specialized Assistant and Agent packages, detailing their features and benefits.
- 💬 **Dedicated Chat UI:** Incorporated a new, open-source based Chat UI component within the architecture, providing an intuitive and feature-rich interface for user interactions.
- 🤖 **Bots Integration Module:** Added a new Bots component leveraging the Microsoft Azure Bot Framework to enable seamless AI-Hub integration with collaboration tools like Microsoft Teams, Slack, email, and SMS.
- 📊 **Agents Transparency Frontend:** Introduced a specialized UI for monitoring, auditing, and ensuring accountability of AI agent activities, enhancing trust and oversight.
- ⚙️ **Process Panel for Human-Agent Workflows:** Included a new Process Panel for modeling, visualizing, and managing collaborative workflows between humans and AI agents.
- 🌍 **Deployment Model Clarification:** Added details on the AI-Hub's hosting and deployment model, emphasizing in-customer-infrastructure deployment for security and compliance.

---



## [v0.50.0] - 2025-02-19 - Enhanced Slack Channel Interaction for Bots

### Changed
- 🚀 **Improved Slack Channel Bot Behavior:** Bots now only respond to messages in Slack channels when they are explicitly **mentioned**, significantly reducing channel noise and providing a more focused interaction experience. This change ensures that bots are more respectful of channel conversations and only engage when directly addressed.

### Added
- 🦾 **New Slack Message Utilities:** Introduced `is_slack_channel_message` and `is_bot_mentioned` helper functions to accurately identify Slack channel messages and detect when the bot has been mentioned, enabling the refined bot interaction logic.

---



## [v0.49.0] - 2025-02-19 - Revitalized Bot Platform with Streamlined Chat and Setup

### Added
- 🦾 **Introduced `AgentChatBot` and `StreamAgentChatBot`:** New bot classes now enable more robust interaction with AI Agents, supporting both single-response and real-time streaming capabilities.
- ⚡️ **New `OpenaiChatBot` and `StreamOpenaiChatBot`:** Dedicated bot classes for OpenAI LLMs provide enhanced chat experiences, offering immediate and streamed responses across various communication channels.
- 📄 **Configurable System Messages:** Bots can now be configured with custom system messages per path via the `PathEntity`, allowing for personalized instructions and behavior.
- 💬 **Enhanced Slack Thread Integration:** Improved handling of Slack conversation threads ensures proper context and continuous conversations by accurately managing and retrieving message history.
- 🚀 **Standardized Streaming Response Handling:** A common utility in the new base `Service` class facilitates efficient sending and updating of streamed responses, significantly improving user experience for long answers.

### Changed
- 💡 **Simplified Conversation Persistence:** The internal `ConversationEntity` model has been streamlined to focus purely on message history, leading to a cleaner and more efficient data structure.
- ⚙️ **Flexible Bot Deployment Script:** The `setup_azure_bot.py` script is now more versatile, capable of deleting existing bot resources and supporting direct MongoDB connection strings in addition to Cosmos DB.

### Refactor
- 🧹 **Overhauled Bot Core Architecture:** The entire bot framework has been re-engineered, consolidating common functionalities into a new base `Service` class and streamlining the `AgentChatBot` and `OpenaiChatBot` implementations.
- 🔄 **Restructured Bot Module Organization:** Directories and file paths related to bot functionalities have been renamed and reorganized for improved logical grouping and maintainability.

### Removed
- 🗑️ **Deprecated ChatBot Base Classes:** The legacy `ChatBot` and its specialized `Json/Stream` variants have been removed, replaced by the new, more modular bot architecture.
- ❌ **Echo Bot Functionality:** The basic "Echo Bot" and its associated routes and services have been retired.
- 🧹 **Outdated Conversation Persistence Methods:** Specific methods for user management and conversation deletion in `ConversationEntity` were removed, aligning with the simplified persistence model.

---



## [v0.48.0] - 2025-02-19 - Platform Release Synchronization and Test Enhancements

### Changed
- 🔄 **Synchronized Core Component Versions:** Aligned all core components, including **aihub-agent**, **aihub-api**, **aihub-bot**, **aihub-lib**, and **aihub-pipeline**, to `v0.48.0` for consistent platform releases and improved internal dependency management.
- ⚡️ **Updated SonarCloud Scan Action:** Upgraded the GitHub Action for SonarCloud scans to `v5`, ensuring compatibility with the latest analysis features and improved code quality checks in the CI/CD pipeline.

### Fixed
- 🐛 **Enhanced Bot Test Stability:** Increased wait times and retry attempts in **ChatBot** tests to improve reliability and reduce flakiness during automated testing scenarios.

---



## [v0.47.0] - 2025-02-18 - Streamlined Azure Configuration and Expanded Service Support

### Changed
- ⚙️ **Updated Azure Subscription Identification:** The system now directly uses `AZURE_SUBSCRIPTION_ID` (GUID) instead of `AZURE_SUBSCRIPTION_NAME` for identifying Azure subscriptions, simplifying credential management and enhancing reliability.
- 🏗️ **Simplified Azure Resource Naming:** Removed the `ENVIRONMENT` variable from Azure resource naming conventions, leading to shorter and more consistent resource group and service names for AI Search, Cognitive Services (Document Intelligence, Speech), Cosmos DB, and Data Lake.
- 🚀 **CI/CD Alignment:** Updated GitHub Actions to pass `AZURE_SUBSCRIPTION_ID` to backend tests, ensuring compatibility with new Azure configuration practices.

### Added
- ✨ **Expanded Azure Service Support:** Introduced new Azure management libraries (`azure-mgmt-cognitiveservices`, `azure-storage-file-datalake`, `adlfs`) to enhance interaction and management capabilities for Azure Cognitive Services and Data Lake Storage Gen2.

### Refactor
- 🧹 **Unified Cosmos DB Access:** Replaced the `CosmosConnectionStringSingleton` with `CosmosAccess` for a more consistent and robust way of managing Cosmos DB connections.
- 🔄 **Standardized Configuration Imports:** Adjusted internal import paths (e.g., `Configs` to `configs`, `vector_stores` to `stores`) for improved code consistency and maintainability across the codebase.

---



## [v0.46.0] - 2025-02-18 - Streamlined Azure Resource Management

### Changed
- ⚙️ **Azure Subscription Identification**: Migrated from using Azure subscription names to direct Azure subscription IDs (GUIDs) for more robust and reliable identification and access to Azure resources across all integrated services.
- 🧹 **Configuration Streamlining**: Simplified core configurations by removing the `ENVIRONMENT` variable from `BaseConfig` and from the default Azure resource naming conventions, leading to leaner and more consistent resource provisioning.
- ⚡️ **CI/CD Alignment**: Updated internal CI/CD workflows to leverage the new Azure subscription ID-based configuration, ensuring seamless and secure testing against Azure cloud resources.

### Refactor
- 🔄 **Azure Access Modules**: Overhauled the internal logic within various Azure service access modules (including AI Search, Cognitive Services, Cosmos DB, and Data Lake) to align with the new subscription ID-centric access pattern and simplified resource naming.
- 📄 **RAG Agent Imports**: Standardized the casing for import paths within RAG Agent configurations (`Configs` to `configs`) to improve code consistency and maintainability.

---



## [v0.45.0] - 2025-02-17 - Core System Updates and Dependency Alignments

### Changed
- ✨ **Updated Project Version**: The overall project version has been bumped to `v0.45.0`.
- 🔄 **Upgraded Poetry Dependency Manager**: The project's dependency management tool, Poetry, has been upgraded to version `2.1.1`, enhancing dependency resolution and management capabilities.
- ⚙️ **Revised CI/CD Dependency Locking**: The continuous integration pipeline now uses an updated Poetry lock command, streamlining dependency updates in the build process.
- 📦 **Synchronized Internal Library Version**: All sub-components (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`) now utilize the latest `aihub-lib` version `v0.45.0`.
- ⬆️ **Updated Core Dependencies**: Numerous underlying Python package dependencies across all modules have been updated, bringing improvements in stability, performance, and security.

### Refactor
- 🧹 **Standardized Dependency Grouping**: Poetry lock files now explicitly categorize dependencies into `main` and `dev` groups for clearer and more organized dependency management.

---



## [v0.44.0] - 2025-02-17 - Enhanced Bot Configuration and Core System Flexibility

### Added
- ✨ **Introduced Single-Tenant Bot Support**: The bot setup script and credential management now fully support Azure Bot Service applications configured as 'SingleTenant', allowing for more flexible deployments in specific Azure AD environments.
- ⚙️ **Extended Credential Configuration**: Added new fields (`APP_TYPE`, `APP_TENANTID`) to the bot's credential entity, enabling more detailed and versatile configuration options for different bot service types.
- 🚀 **OpenAI Chat Playground Example**: Included an example OpenAI chat controller in the development playground, simplifying the local testing and integration of Azure OpenAI models.

### Changed
- 🔄 **Dynamic Bot Adapter Retrieval**: The bot's adapter is now dynamically retrieved per request, enhancing support for multi-tenant scenarios and ensuring the correct bot configuration is used based on the incoming request path.
- 📄 **Standardized Request/Response Handling**: Updated all bot controllers to consistently use FastAPI's native `Request` and `Response` objects, improving API consistency and maintainability.
- 🧹 **Refined Credential Field Naming**: Renamed and made optional existing credential fields (`APP_ID`, `APP_PASSWORD`) for better clarity and alignment with new configuration options.

### Refactor
- 🛠️ **Improved Bot Setup Script**: Enhanced the `setup_azure_bot.py` script for more robust and configurable Azure Bot Service deployment, especially for handling different app registration types.

---



## [v0.43.0] - 2025-02-17 - Build System and CI/CD Enhancements

### Changed
- 🚀 **Updated CI/CD Workflows**: Upgraded the Poetry version used in GitHub Actions from `1.8.3` to `2.1.1`, enhancing the reliability and performance of automated builds and tests.
- ⚙️ **Modernized Build System Requirements**: Standardized `poetry-core` build system requirements across all components to `>=2.0.0,<3.0.0`, ensuring compatibility with the latest Poetry versions and adopting modern packaging practices.

---



## [v0.42.0] - 2025-02-17 - Library Refinement and Version Alignment

### Refactor
- 🧹 **Refined node post-processing:** Updated the `ScoreScalerPostProcessor` method name from `process` to `postprocess_nodes` in the `retrieve_nodes` utility for enhanced clarity and consistency in semantic hybrid retrieval operations.

---



## [v0.41.0] - 2025-02-17 - Improved Azure AI Search Semantic Capabilities

### Added
- ✨ **Azure AI Search Vector Store:** Introduced the ability to specify a `semantic_configuration_name` when creating an Azure AI Search vector store, allowing for the integration of advanced semantic search functionalities.

---



## [v0.40.0] - 2025-02-14 - Dynamic Bot Credentials and Streamlined Azure Setup

### Added
- ✨ **New `PathEntity` for Dynamic Credentials**: Introduced a new MongoDB entity (`PathEntity`) to store Azure Bot credentials (`app_id`, `app_password`) associated with specific API paths. This enables the bot to dynamically load authentication details based on the incoming request endpoint.
- 🚀 **Automated Azure Bot Setup Script**: Added `setup_azure_bot.py`, a new script to simplify and automate the deployment of Azure Bot resources. This includes Azure AD app registration, credential management, and saving these credentials directly into Cosmos DB, streamlining the setup process for new bot instances.

### Changed
- 🔄 **Dynamic Azure Bot Adapter Configuration**: The `CloudAdapter` for the Azure Bot Framework now dynamically loads credentials from the database based on the incoming request path. This significantly enhances multi-tenancy capabilities, allowing multiple Azure Bot registrations with different credentials to be served from the same API endpoint.
- ⚡️ **Updated Bot Controller Responses**: Bot controllers now return generic `Response` objects instead of `JSONResponse`, aligning with standard FastAPI practices and supporting the new dynamic adapter changes.

### Refactor
- 🧹 **Persistence Layer Restructuring**: The `aihub_bot/persistence/chat/entities` directory has been reorganized and renamed to `aihub_bot/persistence/entities` for a cleaner, more generalized structure of persistence entities.
- 🗑️ **Removed Static Bot Credentials from Configuration**: Azure Bot-specific credential fields (`APP_ID`, `APP_PASSWORD`, `APP_TENANTID`, `APP_TYPE`) have been removed from `BaseConfig` in `aihub_lib`, as these are now managed dynamically via the new `PathEntity` in `aihub_bot`.

---



## [v0.39.0] - 2025-02-14 - Improved Agent Context & Data Handling

### Changed
- 🔄 **RAG Agent Context Handling:** The RAG Agent now correctly incorporates the full limited chat history when processing rejected few-shot prompts, leading to more contextually relevant guardrail responses.

### Refactor
- 🧹 **Refined Timestamp Formatting Utility:** The internal utility for formatting Unix timestamps (`format_unix_timestamp`) has been improved to directly accept integer timestamps, enhancing the robustness and correctness of date metadata processing.

---



## [v0.38.0] - 2025-02-13 - Bot Reliability & API Streaming Enhancements

### Fixed
- 🐛 **Improved OpenAI Chat Role Handling:** Ensured the user role defaults to "user" in `JsonOpenaiChatBot` interactions, preventing potential issues when the role is not explicitly provided.
- ⚡️ **Enhanced OpenAI Streaming Stability:** Implemented robust checks for empty or null content chunks during OpenAI chat streaming, significantly improving the stability and reliability of real-time message delivery.

---



## [v0.37.0] - 2025-02-13 - Improved Internationalization and Advanced RAG Context Handling

### Added
- ✨ **Enhanced Localization Support:** Introduced comprehensive French and Italian translations for agent prompts and thought processes, broadening language capabilities.
- 📄 **New RAG Context Prompt:** Added a detailed and improved context prompt for RAG agents within `aihub_lib`, providing clearer instructions on processing structured documents and their associated metadata.
- 🦾 **Configurable Locale Paths:** Enabled dynamic specification of locale paths directly within the `AgentConfig`, offering increased flexibility and customizability for managing internationalization.

### Changed
- 🔄 **Centralized Core Prompts:** Migrated general agent prompts (such as `condenser` and RAG context prompts) from agent-specific configurations to a centralized location within `aihub_lib`, promoting reusability and consistency across agents.
- 📈 **Structured RAG Context Presentation:** Enhanced the formatting of RAG context documents to include rich metadata (e.g., source, namespace, type, version, timestamps) and adopted more descriptive `<DOCUMENT>` tags, aiding better LLM understanding of provided context.
- 📝 **Refined Condenser Prompts:** Updated standalone question prompts for condensers across all supported languages to improve context retention and clarity in conversational flows.

### Refactor
- 🧹 **Streamlined Prompt Management:** Decoupled core prompt definitions from individual agent configurations, allowing agents to dynamically retrieve prompts based on locale and their specific configuration.

---



## [v0.36.0] - 2025-02-13 - Core Enhancements and Configuration Flexibility

### Added
- 🔑 **Enhanced Azure Bot Service Configuration**: Introduced `APP_TYPE` and `APP_TENANTID` environment variables to `BaseConfig` for more comprehensive Azure Bot Service setup.

### Changed
- ⚡️ **Improved Chat Streaming Responsiveness**: Added `asyncio.sleep(0)` to the OpenAI chat service's streaming logic to prevent blocking and enhance real-time responsiveness during chat completions.
- ⚙️ **Flexible Self-Hosted LLM Configuration**: The `default_parameter` in `SelfHostedLLMConfig` is now optional, defaulting to an empty parameter set, which provides more flexibility in model setup.

### Refactor
- 🧹 **Simplified LLM Configuration Examples**: Streamlined LLM model configurations in the `aihub_bot` playground examples, removing verbose default parameter settings for a cleaner setup, and included `gpt-4o-mini` as a new example model.

---



## [v0.35.0] - 2025-02-12 - Enhanced Agent Control and Core Workflow Streamlining

### Added
- 🦾 **Introduced Few-Shot Guard for RAG Agent**: The RAG Agent now incorporates a configurable few-shot guard mechanism, allowing it to determine if a user query is within its allowed scope based on predefined examples. This enhances control over agent behavior and prevents it from answering out-of-scope questions.
- 💬 **Direct User Query Access**: A new `user_query` property has been added to the `StartEvent`, providing a more direct and centralized way to access the initial user message within agent workflows.
- 📝 **FewShotGuardExample Model**: A dedicated `FewShotGuardExample` data model was introduced to facilitate the clear and structured definition of examples for the new few-shot guard.

### Changed
- 🚀 **Streamlined Agent Data Flow**: Agents, including `FewShotAgent` and `RAGAgent`, no longer rely on `RunContext` for accessing core data like user queries and chat history. This information is now directly passed via event parameters or accessible from the `StartEvent`, simplifying data flow and reducing internal dependencies.
- 🗄️ **Standardized Common Event and Config Locations**: Moved general-purpose event and configuration files (e.g., `LimitChatHistoryEvent`, `StandaloneQuestionCondenserEvent`) from agent-specific `rag` directories to a more general `common` module, improving reusability and organizational clarity across different agent types.
- 🌐 **Centralized Condenser Prompt**: The prompt for condensing standalone questions has been moved from agent-specific translation files to the shared `aihub_lib` translations, making it a more consistent and reusable component across the system.
- ⚙️ **Updated Azure OpenAI API Version**: The Azure OpenAI API version used in tests has been updated to `2024-08-01-preview` to align with the latest available features and improvements.

### Refactor
- 🧹 **Refined Standalone Question Condensation**: The `condense_standalone_question` utility now intelligently excludes system messages from the chat history during the condensation process, which can lead to more accurate standalone question generation.
- 📁 **Improved RAG Agent File Structure**: Minor structural adjustments were applied to the RAG agent's configuration and event paths, standardizing folder names to `configs` and `events` for enhanced consistency.

---



## [v0.34.0] - 2025-02-11 - Unified Module Versions and Stability Improvements

### Changed
- ⚙️ **Synchronized Module Versions**: All core modules, including `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline`, have been updated to version `v0.34.0`. This ensures consistent internal dependency management and overall project alignment.
- ⬆️ **Dependency Updates**: Key dependencies such as `llama-index-readers-file` (to `0.4.5`), `pymongo` (to `4.11.1`), and various `dagster` related packages (to `1.9.13` and `0.25.13`) have been upgraded, contributing to enhanced stability and minor underlying improvements.

### Refactor
- 🧹 **OpenAI Chat Service Method Clarity**: The internal method for streaming OpenAI chat completions in `StreamOpenaiChatBot` was renamed from `stream_on_message` to `stream_on_message_completion` for better readability and semantic clarity.

### Removed
- 🗑️ **Outdated Local Configuration**: The `playground/testing/.env` file has been removed, streamlining the local development environment by deprecating an obsolete test configuration.

---



## [v0.33.0] - 2025-02-10 - Enhanced RAG with Contextual Node Retrieval

### Added
- ✨ **Introduced Contextual Node Retrieval for RAG Agent**: The RAG agent's retrieval step now supports fetching adjacent nodes (previous, next, or both) from the vector store, enabling richer context for generative responses.
- ⚙️ **New `VectorPrevNextPostProcessor`**: A new post-processor was added to the `aihub_lib` to manage the traversal and retrieval of linked nodes from vector stores, a core component of the new contextual retrieval feature.
- 📦 **`RetrievePrevNextConfig` for RAG**: A new configuration model has been added to allow precise control over how previous and next nodes are retrieved within the RAG agent's pipeline.

### Changed
- 🧪 **Updated Test Workflow for `aihub_lib`**: The `aihub_lib` test workflow now includes Milvus setup, providing comprehensive testing capabilities for vector store-related functionalities, including the new node traversal.

### Refactor
- 🧹 **Centralized Milvus Test Utilities**: Moved Milvus-related testing utilities to a shared `aihub_lib/testing` module, improving code reusability and test infrastructure consistency across projects.

---



## [v0.32.0] - 2025-02-10 - Flexible Chat Options: Direct OpenAI Support and Modular Agent Architecture

### Added
- ✨ **Direct OpenAI Model Integration**: Introduced new endpoints and bots for direct chat completions with OpenAI and Azure OpenAI models, supporting both JSON and streaming responses.
- ⚙️ **Centralized Bot Configuration**: Added `APP_ID` and `APP_PASSWORD` configuration fields to `aihub_lib.infrastructure.azure.BaseConfig`, streamlining bot service authentication setup.
- 🧪 **OpenAI Playground Examples**: Included new examples in the playground demonstrating the direct integration with various OpenAI and self-hosted language models.

### Changed
- 🔄 **Modular Chat Architecture**: Reworked the `aihub_bot` chat module, separating agent-based chat logic into a dedicated `agent/` subpackage and introducing a new `openai/` subpackage for direct OpenAI interactions. This improves modularity and maintainability.
- 🧹 **Refined Base Chat Services**: Simplified the core `ChatBot` and `ChatService` classes to serve as more generic foundations, with specific interaction logic now residing in specialized agent and OpenAI services.
- 🛡️ **Enhanced Conversation Persistence**: Improved the `ConversationEntity` to automatically initialize a new conversation if one does not exist when adding messages, enhancing robustness.
- 📝 **Updated Activity Model Types**: Corrected the type mapping for `object` in the activity model for improved type handling.

### Removed
- 🗑️ **Legacy Bot Configuration File**: Eliminated the `DefaultConfig.py` file from `aihub_bot` as its functionality has been migrated to the centralized `BaseConfig` in `aihub_lib`.

---



## [v0.31.0] - 2025-02-07 - Enhanced Tracing Capabilities

### Added
- 🔑 **Phoenix Tracing Authentication**: Introduced support for configuring an optional `PHOENIX_AUTH_TOKEN` to authenticate tracing data exports, enabling more secure integration with Phoenix tracing instances.

---



## [v0.30.0] - 2025-02-07 - Core Updates and Chat Service Refinements

### Changed
- ⚡️ **Enhanced Chat Event Creation:** Streamlined the internal handling of messages within the chat service, allowing `UserMessageEvent` to directly accept the complete message list for improved consistency and simplified event processing.

---



## [v0.29.0] - 2025-02-07 - Configurability and Workflow Updates

### Added
- 🚀 **Formalized `bots` scope support** in the semantic pull request workflow, enhancing CI/CD validation for bot-related changes.

### Changed
- ⚙️ **Updated NATS connection configuration** in the `aihub_bot` service to dynamically retrieve the endpoint from `NatsConfig`, replacing the previously hardcoded local address for improved deployment flexibility.

---



## [v0.28.0] - 2025-02-07 - Enhanced AI Capabilities and OpenAI API Compatibility

### Added
- 🚀 **OpenAI API Emulation**: Introduced a comprehensive `/openai` API endpoint in `aihub_api` that fully mirrors the OpenAI API. This allows for seamless integration with OpenAI SDKs and third-party tools like Open WebUI, supporting chat completions (including streaming responses), text embeddings, image generation (DALL-E), Speech-to-Text (STT) transcription, and Text-to-Speech (TTS) generation.
- 🖼️ **Image Model Configuration**: New configuration classes (`ImageModelConfig`, `AzureOpenaiImageModelConfig`) were added to explicitly define and manage image generation models, including DALL-E parameters.
- 🗣️ **Speech and Audio Model Configurations**: Implemented dedicated configuration classes for Speech-to-Text (`STTConfig`, `AzureOpenaiSTTConfig`) and Text-to-Speech (`TTSConfig`, `AzureOpenaiTTSConfig`) models, enabling robust integration of audio processing services.
- 📄 **Open WebUI Docker Compose Example**: A `docker-compose-open-webui.yml` file was provided to demonstrate how to easily integrate AI-Hub with Open WebUI using the new OpenAI API emulation.

### Changed
- ⚙️ **LLM Configuration Fields**: The `api_endpoint` field in LLM configurations has been consistently renamed to `base_url` for improved clarity and consistency across various generative AI resource types.

### Refactor
- 🔄 **Generative AI Resource Reorganization**: Performed a significant internal restructuring of the `aihub_lib.generative_ai` package. The `llms.models` and `llms.costs` modules have been consolidated and renamed to `resources.models` and `resources.costs` respectively. This foundational change unifies the definition and management of all generative AI capabilities (LLMs, embeddings, image, STT, TTS) under a consistent `ResourceConfig` hierarchy.
- 🧹 **Streamlined Azure OpenAI Resource Management**: Introduced `AzureOpenaiResourceConfig` as a new common base class to centralize client initialization and simplify configuration for all Azure OpenAI-backed models.
- ⬆️ **Core Library Update**: Updated `aihub-lib` to `v0.27.0` to incorporate the latest architectural improvements and new resource configurations.

---



## [v0.27.0] - 2025-02-06 - Enhanced Chat Interactions with Streaming Support and API Documentation

### Added
- ✨ **Streaming Chat Completions**: Introduced a new endpoint and dedicated bot (`StreamChatBot`) to provide real-time, streamed responses from AI agents, significantly enhancing the user experience for longer interactions.
- 🧱 **Specialized Chat Bots**: Created `JsonChatBot` and `StreamChatBot` as distinct classes to handle synchronous JSON-based and asynchronous streaming chat interactions, improving modularity and clarity of bot logic.
- 📄 **Improved API Documentation**: Integrated `ActivityModel` to dynamically generate Pydantic schemas for Bot Framework activities, providing more accurate and detailed OpenAPI documentation for all chat endpoints.

### Changed
- 🔄 **Test Runner Enhancements**: Updated the `BotTestRunner` to support `PUT` requests and return activity IDs in responses, which are essential for real-time updates of streamed bot responses.
- 📝 **Comprehensive OpenAPI Definitions**: Expanded the OpenAPI documentation for chat completion endpoints with detailed summaries, descriptions, and response examples, leading to better API understanding and usability.

### Refactor
- 🧹 **Chat Bot Logic Separation**: Refactored the core `ChatBot` by moving specific message handling logic into dedicated `JsonChatBot` and `StreamChatBot` classes, enabling a clearer separation of concerns and more maintainable code.

---



## [v0.26.0] - 2025-02-06 - Improved Event Management and Data Integrity

### Added
- ✨ **Enhanced Event Serialization**: Nested `BaseEvent` instances are now correctly serialized when converting events to a dictionary, preventing data loss and supporting more complex event structures.
- 📄 **Detailed Error Logging**: Implemented comprehensive logging for exceptions encountered during event storage and retrieval within the distributed event store, significantly improving debuggability and operational visibility.

### Changed
- 🔄 **Refactored Distributed Event Store Logic**: The `DistributedEventStore` now retrieves events by their class name string and utilizes a generic deserialization method (`ControlEvent.deserialize_event`). This change reduces coupling between the store and specific event types, enhancing flexibility and maintainability.

### Fixed
- 🐛 **Robust Event Retrieval**: Improved error handling in the distributed event store to specifically manage `KeyNotFoundError` when retrieving events, ensuring that missing keys are handled gracefully and preventing generic exceptions from disrupting event flows.

---



## [v0.25.0] - 2025-02-06 - Refined Agent Testing for Human-in-the-Loop Workflows

### Refactor
- 🔄 **Streamlined Human-in-the-Loop Workflow Tests:** Consolidated the multi-step human-in-the-loop agent tests into a single, comprehensive `pytest_asyncio` test function, simplifying test structure and execution.
- 🧹 **Migrated Test Framework:** Transitioned the testing approach for human-in-the-loop workflows from a Behavior-Driven Development (BDD) style using `pytest-bdd` to a more direct, programmatic `pytest_asyncio` implementation.

### Removed
- 🗑️ **Deprecated BDD Feature Files:** Removed `.feature` files and `pytest-bdd` integration associated with the multi-step human-in-the-loop agent tests as part of the transition to a direct testing methodology.

---



## [v0.24.0] - 2025-02-06 - Core Infrastructure Enhancements and Expanded Integrations

### Added
- ✨ **Introduced Text Embeddings Inference Integration**: Added `llama-index-embeddings-text-embeddings-inference` support, enabling more flexible text embedding generation using local or inference server models.
- 🚀 **Enhanced OpenTelemetry Export Capabilities**: Integrated `opentelemetry-exporter-otlp` and its associated protobuf components, providing robust support for OTLP-based telemetry export.
- 🦾 **Expanded LlamaIndex with Hugging Face Utilities**: Included `llama-index-utils-huggingface`, facilitating deeper integration with Hugging Face models and datasets within LlamaIndex workflows.
- 🔗 **Standardized Google APIs Common Protobufs**: Added `googleapis-common-protos` as a core dependency to support broader integration with Google APIs.
- ⚡️ **Formalized FastAPI Integration**: Explicitly included `fastapi` in core dependencies, reinforcing its role as a foundational element for the project's API layer.

### Changed
- 🔄 **Updated Core Project Dependencies**: Performed a comprehensive upgrade of various Python libraries across `aihub_agent`, `aihub_api`, `aihub_bot`, and `aihub_pipeline` modules. This includes updates to `aiohttp`, `beautifulsoup4`, `attrs`, `certifi`, `openai`, `pydantic`, `transformers`, `pymongo`, `motor`, and several `llama-index` components, improving overall stability, performance, and incorporating the latest features.
- ⚙️ **Streamlined CI Workflow for Backend Testing**: Transitioned from a remote GitHub Action to a local action for `test_backend` within the CI pipeline, enhancing control and reliability of the continuous integration process.
- 🧹 **Refined Poetry Dependency Management**: Updated the Poetry lock file version and removed redundant `groups` and `markers` definitions from package metadata, optimizing internal dependency resolution and clarity.

---



## [v0.23.0] - 2025-02-05 - AI Hub Expands: Introducing Bot Service and Enhancing Core Reusability

### Added
- 🤖 **Introduced `aihub_bot` module**: This new module enables the creation of AI-powered chatbots integrated with the Azure Bot Service, featuring conversational history persistence and flexible AI agent interactions.
- ⚡️ **Added a shared chat service to `aihub_lib`**: Extracted core chat interaction logic (including streaming and JSON response handling) into `aihub_lib`, allowing for greater reusability across different AI Hub frontends and bot integrations.
- 📁 **Introduced new package structures**: Established new package-level import mechanisms within `aihub_api` and `aihub_lib` to support improved modularity and reusability of components.

### Changed
- ⚙️ **Updated CI/CD pipelines and local tooling**: Integrated the new `aihub_bot` module into existing continuous integration, linting, testing (including SonarCloud analysis), and local development workflows.
- ⬆️ **Updated core dependencies**: Aligned all microservices to use `aihub_lib` version `v0.16.0` and updated various underlying Python packages (e.g., `attrs`, `certifi`, `openai`, `pydantic`, `httpx`, `grpcio`, `numpy`) for improved performance and stability.
- 🏷️ **Renamed API chat methods**: Updated method names in `aihub_api`'s chat controller to clarify their role as API-specific wrappers, differentiating them from the new shared chat service in `aihub_lib`.
- 🚨 **Improved thread access error handling**: Enhanced the `ThreadController` with dedicated exceptions for clearer error responses when users attempt unauthorized thread operations.
- 📦 **`aihub_lib` now depends on `FastAPI`**: The core library now directly includes `FastAPI` as a dependency, reflecting its expanded role in providing foundational web-related components.

### Removed
- 🗑️ **Deprecated `llama-index-embeddings-text-embeddings-inference` integration**: Removed support for this specific text embeddings inference, streamlining the embeddings landscape.
- 🧹 **Removed redundant OpenTelemetry exporter packages**: Streamlined OpenTelemetry setup by removing duplicate or unnecessary exporter packages, relying on a more consolidated approach.

### Refactor
- 🔄 **Consolidated shared components into `aihub_lib`**: Key components such as `AuthenticatedUser`, `use_nats`, base `Controller` classes, `HealthController`, `WSUserEvent`, and `WebSocketReceiver` have been moved to `aihub_lib` to centralize common functionalities and enhance code reusability across microservices.
- 🏗️ **Simplified Docker Compose file locations**: Moved common Docker Compose configuration files to the project root for easier management and accessibility.
- 🧹 **Refined backend testing action**: Streamlined the `test_backend` GitHub action by removing redundant working directory inputs, simplifying its configuration.

---



## [v0.22.0] - 2025-02-04 - Core Module Alignment and CI/CD Streamlining

### Changed
- 🔄 **Aligned Module Versions:** Updated core project modules (`aihub_agent`, `aihub_api`, `aihub_lib`, `aihub_pipeline`) and their internal `aihub-lib` dependencies to version `v0.22.0` for consistent releases and dependency management.
- 🚀 **Streamlined CI/CD Workflows:** Updated GitHub Actions across all workflows (testing, linting, code review) to consume actions directly from the `main` branch of `aihub-core`, enhancing the stability and maintainability of our continuous integration and delivery pipelines.

---



## [v0.21.0] - 2025-02-04 - Streamlined CI/CD with Reusable GitHub Actions

### Added
- ✨ **New `aihub_action` Directory:** Introduced a comprehensive suite of reusable GitHub Actions to centralize and standardize common CI/CD workflows, including:
    - 🦾 **Backend Linting (`lint_backend`)**: For consistent Python code formatting with Black.
    - 🖼️ **Frontend Linting (`lint_frontend`)**: For consistent Nuxt.js frontend code style with ESLint.
    - 🧪 **Backend Testing (`test_backend`)**: For running Python backend tests with coverage reporting and Docker Compose support.
    - 📄 **Pytest Coverage Comments (`pytest_coverage_comment`)**: To automatically post test coverage reports on pull requests.
    - 🔍 **SonarCloud Scanning (`sonarcloud_scan`)**: For comprehensive code quality and security analysis.
    - 🤖 **AI-Assisted PR Review (`review_pr`)**: To leverage PR Agent for automated code reviews.

### Refactor
- 🔄 **CI/CD Workflow Consolidation**: Re-architected existing GitHub workflows (`analyze-test-pr.yml`, `lint-pr.yml`, `review-pr.yml`) to utilize the newly introduced reusable actions, significantly reducing redundancy and improving maintainability. This includes:
    - Consolidating the `aihub_web` SonarCloud scan into the main `sonarcloud_scan` job matrix.
    - Replacing verbose, repeated steps with concise calls to the `bbvch-ai/aihub-core/aihub_action` actions.

### Changed
- ⚡️ **Standardized Pytest Markers**: Updated `aihub_agent` and `aihub_lib` test configurations to enforce strict pytest markers (e.g., `azure`, `slow`, `integration`), improving test organization and selection.

---



## [v0.20.0] - 2025-02-03 - Empowering Agents: New Few-Shot Capabilities and Robust Request Guarding

### Added
- ✨ **New Few-Shot Agent**: Introduced a dedicated `FewShotAgent` type, allowing agents to generate responses based on provided examples and condensed user queries, significantly enhancing conversational capabilities.
- 🔐 **Agent Description Guarding**: Implemented a new `agent_description_guard` mechanism, enabling agents to intelligently validate incoming user requests against their defined purpose, improving response relevance and system stability.
- 🛑 **Guard Rejection Event**: Added `GuardRejectionEvent` to explicitly signal when an agent rejects a request due to policy or relevance, providing clearer feedback.
- 📄 **Few-Shot Prompting Utilities**: Included new utilities (`FewShotExample`, `create_few_shot_messages`) to facilitate the creation and management of few-shot examples for LLM interactions.
- 🌍 **Localized Guard Prompts**: Added internationalization support for the new agent description guard, ensuring guard prompts and reasons are available in multiple languages.
- 🧪 **Few-Shot Agent Playground**: Provided comprehensive playground examples and BDD tests for the new `FewShotAgent`, demonstrating its capabilities and workflow.

### Changed
- ⚙️ **Flexible Test Filtering**: Updated the `Makefile` to use more flexible pytest filtering (`-k "not azure"`), allowing developers to easily skip specific test suites.
- 🏷️ **Test Environment Tagging**: Introduced `@azure` and `@self_hosted` tags in RAGAgent tests, enabling environment-specific test execution and clearer test organization.
- 📖 **Documentation Updates**: Revised `README.md` to reflect recent architectural changes, updated import paths, and clarified agent creation and testing instructions.

### Refactor
- 🔄 **Core Library Restructuring**: Performed a significant refactor of `aihub_lib`, moving core components like `AgentConfig` to `aihub_lib.agents` and `EventDisplayer` to `aihub_lib.displayers` for improved modularity and clearer separation of concerns across agent implementations.
- 🧹 **Centralized Tracing Management**: Adjusted tracing implementation by removing direct `@tracing` decorators from document loaders, indicating a more centralized or automated tracing approach within the framework.
- ⬆️ **Dependency Updates**: Upgraded various project dependencies (e.g., `beautifulsoup4`, `llama-index-llms-openai`, `marshmallow`, `openai`, `pypdf`) to their latest stable versions for performance improvements and bug fixes.
- ⬇️ **Milvus Dependency Adjustment**: Adjusted the `pymilvus` dependency version, likely to ensure compatibility or address specific integration requirements.

---



## [v0.19.0] - 2025-01-31 - Core Alignment and New Embedding Capabilities

### Added
- ✨ **Enhanced Embedding Options:** Integrated `llama-index-embeddings-text-embeddings-inference` to support a wider range of text embedding models, providing more flexibility for semantic search and retrieval tasks.

### Changed
- 🔄 **Core Library Alignment:** Synchronized `aihub_agent`, `aihub_api`, and `aihub_pipeline` modules with `aihub_lib v0.19.0`, ensuring all components utilize the latest core functionalities and improvements.
- ⚡️ **Upgraded Pipeline Orchestration:** Updated Dagster and its related components to `v1.9.11`, bringing general improvements and fixes to the data orchestration layer.
- 🚀 **Updated Hugging Face Hub Integration:** Upgraded `huggingface-hub` to `v0.28.1`, including dependency updates like `aiohttp` for inference, potentially improving performance and stability when interacting with Hugging Face models.
- ⚙️ **General Dependency Updates:** Performed numerous minor version updates across various Python packages to improve compatibility, stability, and leverage the latest upstream fixes.
- 🐛 **Improved Async Compatibility:** Adjusted `SQLAlchemy`'s `greenlet` dependency markers to enhance compatibility and stability in asynchronous environments.

---



## [v0.18.0] - 2025-01-31 - CI/CD Pipeline Refinements

### Refactor
- 🧹 **Optimized Release Tagging Workflow:** Reordered the SSH key cleanup step within the GitHub Actions workflow to enhance the robustness and reliability of the release tagging process.

---



## [v0.17.0] - 2025-01-31 - Empowering Agents: Introducing Delegation and Flexible AI Hosting

### Added
- 🦾 **Agent-in-the-Loop (AITL) Delegation**: Introduced a foundational capability enabling agents to delegate tasks to other specialized agents. This feature enhances complex workflow orchestration by allowing agents to pause, request external processing, and resume based on delegated results.
- 💬 **AITL Event Definitions**: Added new core event types (`AgentInTheLoopRequestEvent`, `AgentInTheLoopResponseEvent`, `AgentInTheLoopExceptionEvent`) to support robust agent-to-agent communication and error handling during delegation.
- 🌐 **Self-Hosted LLM and Embedding Support**: Extended the RAG agent and LLM configurations to seamlessly integrate with self-hosted Large Language Models (LLMs) and embedding models. This provides greater flexibility and control over AI infrastructure, enabling local model execution.
- 📦 **Milvus Vector Store Integration**: Introduced support for Milvus as a configurable vector store within the RAG agent, allowing for more diverse knowledge base integrations.
- 🔌 **Centralized NATS Configuration**: Added `NatsConfig` to centralize and simplify the management of NATS endpoint configurations across all modules.
- ⚙️ **Local Milvus and AI Model Docker Setup**: Provided `milvus-standalone-docker-compose.yml` and updated `docker-compose.yml` for simplified local setup of Milvus, `llama.cpp` (for LLMs), and Hugging Face TEI (for embeddings) in the playground, facilitating self-hosted AI development.
- ✅ **New BDD Test Suites**: Expanded the test coverage with new BDD scenarios for conditional workflows, context handling, fan-out patterns, semantic events, and crucial end-to-end tests for the new Agent-in-the-Loop feature.

### Changed
- 🔄 **Abstracted RAG Agent Vector Store**: The RAG agent's retrieval step now uses a generic `BasePydanticVectorStore` instead of a specific `index_name`, significantly improving flexibility and allowing different vector databases to be plugged in without code changes.
- ✏️ **Unified LLM Base URL Naming**: Renamed `api_endpoint` to `base_url` across all LLM and embedding configurations for consistent and clearer terminology.
- 📝 **Streamlined LLM Tokenization Logic**: Abstracted the tokenizer access within `ChatLLMConfig` to a property, simplifying token counting and history limiting logic across various LLM implementations.
- 🛠️ **Refined Agent Test Runner**: Enhanced `AgentTestRunner` by introducing distinct `test_run_start` and `test_run_stop` methods, providing more granular control over test execution and setup/teardown.
- 📂 **Organized Playground Workflows**: Restructured playground examples into more descriptive and logical workflow directories, improving discoverability and maintainability of examples.
- 📄 **Updated Documentation for Local Setup**: The `README.md` has been updated with clearer instructions for local Docker setup, including guidance on running self-hosted AI services.
- 🧹 **Improved Docker Health Checks**: Enhanced the robustness of Docker health checks for NATS and MongoDB services in the CI/CD pipeline, ensuring services are fully ready before tests begin.
- ➡️ **Updated CI/CD Workflows**: Modified `add-tag.yml` to trigger only on pushes to `main` and updated `analyze-test-pr.yml` to reflect new Docker Compose commands and test coverage reporting.
- 🤖 **Migrated AI Code Review Model**: Switched the `review-pr.yml` workflow to use `gpt-4o` with the latest Azure OpenAI API version for improved code review capabilities.
- ⚡️ **Enhanced Event Logging**: Improved internal event serialization logging for better debugging and visibility of event payloads.

### Fixed
- 🐛 **Robust Event Registration**: Implemented a check to prevent duplicate event class registrations, improving the stability of the NATS event system.

### Removed
- 🗑️ **Deprecated LLM Tokenizer Name**: Removed the `tokenizer_name` property from `SelfHostedLLMConfig` as tokenizer inference is now handled automatically.
- 🗑️ **Removed Specific Index Name from RAG Configuration**: The `index_name` parameter has been removed from `RetrieveStepConfig`, aligning with the more generalized `vector_store` integration.

---



## [v0.16.0] - 2025-01-22 - Empowering Local LLM Development and Streamlining CI/CD

### Added
- 🦾 **Enabled Self-Hosted LLMs**: The `LlamaIndexAgent` now supports integration with self-hosted Large Language Models, offering greater flexibility and control over AI agent deployments.
- 📄 **Configurable Tokenizer for Self-Hosted LLMs**: Introduced a `tokenizer_name` option in `SelfHostedLLMConfig`, allowing precise specification of the tokenizer to be used with custom models.
- 🧪 **New BDD Test Workflows**: Added comprehensive Behavior-Driven Development (BDD) test suites for `DisplayingAgent` and `LlamaIndexAgent` within the playground environment, enhancing test coverage and reliability.
- 🛠️ **Improved Agent Test Runner**: A new `get_start_event` utility method has been added to `AgentTestRunner`, simplifying access to initial events in agent test scenarios for easier validation.
- 🐳 **Integrated Ollama Service in Playground**: The `ollama` local LLM serving platform is now seamlessly integrated into the development `docker-compose` setup, facilitating local testing and experimentation with self-hosted models.

### Changed
- 🚀 **Enhanced CI/CD Workflow Robustness**: The auto-tagging and pull request testing workflows have been fortified with more resilient shell scripting for directory iteration and refined Git configuration, ensuring consistent and reliable bot operations.
- 🔗 **Streamlined Global Dependency Management**: Implemented new steps in the pull request analysis workflow to validate and install global Poetry dependencies, preventing conflicts and ensuring consistent build environments.
- 🤖 **Automated Ollama Model Pull**: The PR analysis workflow now automatically pulls the necessary Qwen2.5 model to the Ollama service during `aihub_agent` tests, guaranteeing immediate test readiness.
- ⬆️ **Dependency Updates**: Key dependencies across `aihub_lib`, `aihub_agent`, `aihub_api`, and `aihub_pipeline` have been updated for improved performance, stability, and security.

### Refactor
- 🏗️ **Evolved Project Structure**: Transitioned towards a Poetry workspace/monorepo architecture by introducing a root-level Poetry configuration, laying the groundwork for more efficient package management and development.
- 🔄 **Optimized CI/CD Tagging Logic**: The sequence of tag deletion and creation in the auto-tagging workflow has been reordered for improved logical flow and error handling.

### Removed
- 🗑️ **Deprecated Service Startup Script**: The standalone `start_service.sh` script has been removed, as its functionality has been integrated or superseded by other system improvements.

---



## [v0.15.0] - 2025-01-21 - Internal CI Workflow Refinements

### Changed
- ⚙️ **Improved CI workflow reliability** by explicitly defining the conditions for the Pytest coverage comment job to run solely on pull request events.

---



## [v0.14.0] - 2025-01-21 - Unified Testing, Streamlined Development, and Advanced Agent Capabilities

### Added
- ✨ **Automated Draft Pull Request Creation**: A new workflow automatically creates draft pull requests for new branches, streamlining the initial PR creation process.
- 🦾 **Enhanced Agent Test Runner**: The `AgentTestRunner` now supports observing agent discovery events and provides new utilities for awaiting specific events, significantly improving test reliability and expressiveness for agent interactions.
- 💡 **Expanded Agent Workflow Examples**: Introduced new playground examples showcasing advanced agent design patterns and capabilities, including `configured` agents for dynamic value injection, `discoverable` agents for self-registration, `human-in-the-loop` agents for human interaction, and `optional` event handling in agent steps.
- ✅ **Centralized Test Coverage Reporting**: `pytest-cov` has been integrated across all Python modules, enabling standardized coverage report generation and automated publishing of test results and coverage comments on pull requests.
- 🌐 **Frontend Linting with ESLint**: A new dedicated linting job has been introduced for the `aihub_web` frontend, ensuring consistent code quality and style.

### Changed
- 🚀 **Refined CI/CD Workflows**: Major enhancements and alignment across all GitHub Actions workflows (auto-tagging, testing, linting, and PR review) improve consistency, robustness, and trigger conditions, including support for `initiative/*` branches and `ready_for_review` pull request status.
- 🔄 **Centralized Version and Dependency Management**: The `aihub_lib` dependency for all Python modules (`aihub_agent`, `aihub_api`, `aihub_pipeline`) has been transitioned from local file paths to remote Git tag references, ensuring version consistency across the entire ecosystem.
- 📄 **Updated Package Management Documentation**: The `README.md` now includes a comprehensive new section detailing the package structure and the strategy for managing local and remote dependencies, significantly improving clarity for developers.
- ⬆️ **Dependency Updates**: Key project dependencies across various modules have been updated to their latest stable versions, enhancing overall stability and performance.

### Refactor
- 🧹 **Internal Code Reorganization**: Constants within `aihub_lib` have been moved to more logical locations, and internal `LocaleHandler` usage has been refined for improved maintainability.

### Fixed
- 🐛 **Corrected Black Version in pyproject.toml**: Fixed an incorrect version string for the `black` dependency in `aihub_lib/pyproject.toml`.

### Removed
- 🗑️ **Deprecated Test Scenarios**: Old and redundant simple agent test scenarios from the playground examples have been removed, streamlining the test suite.

---



## [v0.13.0] - 2025-01-17 - Workflow Refinements and Enhanced Debugging

### Added
- ⚡️ **Enhanced Step Debugging Visibility**: Integrated comprehensive debug logging into the `@step` decorator, offering detailed insights into how workflow step parameters and metadata are processed, aiding developers in troubleshooting.
- 📄 **Enabled Example Workflow Logging**: Activated logging in the `fan_out_workflow` example, providing immediate console feedback during execution for easier testing and demonstration of workflow behavior.

### Refactor
- 🧹 **Refined Custom List Type Handling**: Improved the internal representation and extraction of item types within `ListOfSize` and `FixedList` annotations, enhancing the robustness of type parsing for fixed-size event lists. This makes the system more resilient to internal Python version changes regarding generic type introspection.

---



## [v0.12.0] - 2025-01-17 - Enhanced Developer Experience and Core Updates

### Changed
- 📄 **Improved Backend Setup Guide**: The `README.md` now provides comprehensive and clearer instructions for setting up backend microservices, emphasizing the use of isolated Poetry environments to streamline the development workflow and prevent dependency conflicts.
- 🚀 **Updated Core Internal Library**: Upgraded the `aihub-lib` to version `v0.12.0` across dependent microservices, ensuring all components leverage the latest shared functionalities and improvements.

### Removed
- 🗑️ **Deprecated IDE Run Configurations**: Removed outdated IDE-specific run configurations, simplifying the project's root directory and reducing clutter.

---



## [v0.11.0] - 2025-01-16 - Agent Evolution and Core Infrastructure Refinements

### Added
- 🚀 **Introduced AI-Hub Agent Framework:** A foundational new module (`aihub_agent`) providing a structured and modular approach to building general-purpose AI agents with predefined workflows, steps, and event-driven communication.
- ✨ **New Retrieval-Augmented Generation (RAG) Agent:** Implemented a comprehensive RAG agent leveraging the new agent framework, capable of processing user input, retrieving relevant information, condensing questions, and generating LLM responses.
- 🛠️ **New Generative AI Utilities:** Added a suite of dedicated utilities to `aihub_lib` for RAG-specific tasks, including `ScoreScalerPostProcessor` for relevance score normalization, and functions for intelligent chat history management, query condensation, and ordered document combination.
- 🌍 **Enhanced Agent Localization:** Introduced localized internal "thought" messages and prompt templates for agents, improving transparency and multi-language support.
- 🧪 **Comprehensive Agent Testing Utilities:** Expanded the `AgentTestRunner` with BDD testing capabilities for both individual steps and full agent workflows, enabling robust and predictable agent behavior validation.

### Changed
- 🔄 **Refactored NATS Event System:** Significant reorganization and modularization of `aihub_lib`'s NATS event classes, leading to clearer event definitions and improved maintainability across the messaging infrastructure.
- 🧹 **Standardized Code Quality Tools:** Integrated and configured Black, isort, and Ruff across `aihub_agent` and `aihub_api` modules to enforce consistent code formatting and linting.
- 📄 **Updated Documentation Guidelines:** Enhanced agent development documentation within the `aihub_agent/README.md` to provide comprehensive guidance on creating, configuring, testing, and documenting new agents.
- ⚙️ **Pipeline I/O Managers Improvements:** Refined `DocStoreIOManager` and `VectorStoreIOManager` to better handle single or multiple document inputs, improving data processing flexibility.
- 📦 **Dependency Updates:** Updated various Python package dependencies across all modules, including new `llama-index` integrations for Azure OpenAI embeddings and MongoDB document storage.

### Refactor
- 🏗️ **Architectural Integration of New Modules:** Incorporated the new `aihub_agent` and `aihub_api` modules into the main `Makefile` for consistent CI/CD pipeline execution.
- ♻️ **Streamlined Playground Examples:** Refactored existing playground agent examples to align with the new agent framework's patterns and best practices.

---



## [v0.10.0] - 2025-01-16 - Enhanced Repository Governance and Stability

### Added
- 📄 **Introduced comprehensive branch protection rules:** Detailed new guidelines for `main` and `initiative/*` branches, enforcing strict policies on pushes, deletions, linear history, and pull request merging (including required approvals and squash merging) to enhance codebase integrity and promote collaborative development.

---



## [v0.9.0] - 2025-01-16 - Enhanced Setup Guidance

### Added
- 📄 **Updated README with Make Instructions:** Added detailed instructions for installing `make` on Windows to the `README.md`, ensuring smoother setup for development environments.

---



## [v0.8.0] - 2025-01-15 - Improved Setup Instructions

### Changed
- 📄 **Docker installation notes:** Added a helpful troubleshooting tip and reference link to the `README.md` for users experiencing `wsl --update` issues with Docker Desktop.

---



## [v0.7.0] - 2025-01-15 - Enhanced Development Workflow and Dependency Management

### Added
- ✨ **Streamlined Local Development Setup**: Introduced new IDE run configurations and a default `.env` file for the `LLMWrappingAgent` and `core-api` (development and testing), significantly simplifying the local environment setup and execution.
- 🚀 **Standardized Service Startup**: Added a `start_service.sh` script to unify how microservices are launched, improving consistency and ease of use.

### Changed
- 🔄 **Updated `aihub-lib` to v0.7.0**: Upgraded the shared `aihub-lib` to its latest version, incorporating its latest features and fixes across agent and API components.
- ⚙️ **Improved Dependency Management**: Upgraded Poetry to version `2.0.1` and refined dependency linking for `aihub_pipeline` to use local paths for `aihub_lib`, enhancing monorepo development.

### Removed
- 🗑️ **`bson` Dependency**: The `bson` library has been removed from core dependencies, reducing the overall project footprint.

---



## [v0.6.0] - 2025-01-13 - Agent Core Evolution: New Agent Types & Streamlined Playgrounds

### Added
- ✨ **New `LLMWrappingAgent`:** Introduced a foundational agent designed to seamlessly integrate Large Language Models into workflows, simplifying LLM integration and building LLM-powered applications.
- 📄 **Comprehensive BDD Testing Guide:** Added a detailed section to the `README.md` explaining our new Behavior-Driven Development (BDD) testing framework (`pytest-bdd`), including structure, Gherkin syntax, and benefits, to enhance developer understanding and testing practices.

### Changed
- 🔄 **Major Playground Reorganization:** Significantly restructured and renamed all playground examples for both agents and APIs into a more logical, workflow-centric directory structure (e.g., `minimal_workflow`, `agent`) to improve clarity, navigability, and maintainability.
- 📄 **Updated Agent Documentation:** Revised and expanded the `agents_in_detail.md` documentation to align with the new agent patterns and provide clearer explanations of core concepts, including context handling and semantic events.

### Removed
- 🗑️ **Outdated Playground Examples:** Eliminated various deprecated or unorganized agent and API playground examples that have been superseded by the new, structured examples, streamlining the codebase.

### Refactor
- 🧹 **Standardized Agent Naming:** Renamed the `DevAgent` to `LLMWrappingAgent` and relocated it into the `aihub_agent/agents/basic/` directory, improving consistency and discoverability within the core agent types.

---



## [v0.4.0] - 2025-01-07 - Improved Code Quality and Developer Onboarding

### Added
- ⚡️ **Enhanced Code Quality Scans**: Integrated **SonarCloud** into the CI/CD pipeline to automatically analyze code quality and security for core services including agents, API, libraries, pipelines, and web components.

### Changed
- 📝 **Revamped Developer Documentation**: Significantly expanded and restructured the main **README.md** to provide clearer guidance on repository structure, project and work management, branching strategy, and a comprehensive getting started guide for new developers.

---



## [v0.2.0] - 2025-01-07 - Core Component Linking and Documentation Refinements

### Changed
- 📄 **Documentation Clarity:** Clarified the behavior of Human-in-the-Loop (HITL) steps in agent documentation, emphasizing that the **RunContext** persists during pauses and can be used for state retention. A less relevant section on "Personalization & Customization" for **ThreadContext** was also removed for brevity.

### Refactor
- 🔄 **Core Library Linking:** Modified the **aihub_pipeline** project to reference **aihub_lib** via its published **Git tag** (v0.2.0) instead of a local filesystem path. This enhances build consistency and modularity across components.

---



