# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.235.0] - 2025-08-06 - Python 3.13 Upgrade & Enhanced License Compliance

### Added
- 🛡️ **Comprehensive License Compliance**: Introduced a new automated system to scan, categorize, and report licenses for all Python, Node.js, and Docker dependencies. This system generates a detailed `LICENSES.md` report, ensuring better adherence to license policies and supply chain security.
- 🚀 **Dedicated License Check CI/CD**: Implemented a new CI/CD job that automatically verifies license compliance on pull requests and during release tagging, enhancing overall project governance.
- 🎶 **Python 3.13 Audio Compatibility**: Included the `audioop-lts` dependency in the API service to maintain full audio processing functionality after the Python 3.13 migration.

### Changed
- 🐍 **Python Version Upgrade to 3.13**: All backend services (Agent, API, Bot, IAC, Lib, Pipeline, Process) have been migrated to Python 3.13, leveraging the latest language features and performance improvements.
- ⚙️ **CI/CD and Development Environment Updates**: Updated all CI/CD workflows and local development setup instructions (e.g., in `README.md` and GitHub Actions) to align with Python 3.13 requirements.
- 🛠️ **Improved IDE Test Configurations**: Updated IntelliJ/PyCharm run configurations for Python tests (e.g., API Tests, Agent Tests) to explicitly use `py.test` as the test factory for enhanced compatibility and reliability.
- 📦 **Python Development Tooling Updates**: Various Python development dependencies, including `pytest`, `ruff`, and `black`, have been updated and configured for Python 3.13 compatibility.
- 🌐 **Web Project Identity**: The internal name of the web project in `package.json` has been updated for clearer identification.

### Refactor
- 🧹 **Modernized Python Type Hinting**: Standardized the use of the `typing.override` decorator and simplified `AsyncGenerator` type hints across the codebase, taking advantage of new Python 3.13 features for cleaner and more explicit code.
- 🔗 **Monorepo Dependency Management**: Adjusted internal Python service dependencies (e.g., `aihub_lib`) to reference local monorepo paths, streamlining the local development experience.

---



## [v0.234.0] - 2025-08-04 - Major Notification System Overhaul and Web Experience Improvements

### Added
- 🚀 **Comprehensive User Notification System:** Introduced a robust notification system to keep users informed with real-time updates and an intuitive interface for managing alerts. This major addition includes:
    - ✨ **New Notification API Endpoints:** Established a full suite of API endpoints for retrieving paginated notifications, updating individual notification statuses, and performing bulk actions (e.g., marking multiple as read or done).
    - 🔔 **Dedicated Web User Interface:** Launched a new "Notifications" page on the web application, offering a centralized view with advanced filtering options (unread, to-do, all), pagination, and bulk management capabilities.
    - 🚨 **Real-time Notification Overlay and Poller:** Integrated a dynamic notification poller and an interactive overlay component (a bell icon with a counter badge) directly into the top navigation bar. New notifications are now highlighted via toast messages for immediate awareness and quick access.
    - 📚 **Persistent Notification Data Model:** Developed a new database entity and associated service logic for efficient storage and management of all user notifications.
- 🌍 **Expanded Internationalization for RAG Agent:** Added German, French, and Italian translations for the RAG Agent's name and description, broadening language support for core functionalities.
- ✅ **Enhanced Web Application Readiness Checks:** Incorporated `pnpm lint` into the `aihub_web` Makefile's `pr-ready` target, strengthening automated code quality and consistency checks for web changes.

### Changed
- 💬 **Improved API Error Messaging:** Enhanced the web client's error handling to provide more detailed and user-friendly error messages in toast notifications, pulling `detail` information directly from API responses.
- 🎨 **Refined Popover Component Styling:** Updated the visual styling of Popover components across the web UI to ensure a consistent and modern aesthetic.

### Fixed
- 📄 **Corrected Localization for Process Title:** Addressed an issue where the "Processes" heading on the user detail page was not correctly localized, ensuring proper display across all supported languages.

### Refactor
- 🔄 **Standardized Agent Event Topic Naming:** Renamed the `AgentTopic` schema and its associated types in the web SDK to `AgentInstanceTopic` for clearer terminology and improved consistency within the event topic structure.

### Removed
- 🗑️ **Deprecated User Avatar Component:** Removed the standalone `User/Avatar.vue` component, as its functionality has been streamlined and integrated directly into the `User/Bar.vue` component for better modularity.

---



## [v0.233.0] - 2025-07-30 - Internal Dependency Enhancements

### Changed
- ⚡️ **Internal Dependency Updates:** Upgraded core libraries to enhance stability and prepare for future improvements.

---



## [v0.232.0] - 2025-07-29 - Enhanced Dashboard Trend Clarity

### Changed
- 💡 **Adjusted Trend Indicator Logic:** The trending up/down visual indicators for **Exception Events** on dashboards now correctly reflect their severity, displaying green for trending down (good) and red for trending up (bad) to provide more intuitive visual feedback.

---



## [v0.231.0] - 2024-07-29 - Enhanced Agent Testing with Custom Events

### Added
- 🚀 **Customizable Agent Simulation Events:** Introduced the ability to specify custom `start_events` and `stop_events` for the `SimulatedAgentApiTestRunner`, greatly expanding the flexibility for testing agent behavior and API interactions under diverse conditions.
- 🧪 **New Test Event Definitions:** Added `TestStartEvent` and `TestStopEvent` classes to facilitate the creation of unique testing scenarios for agent event processing.
- ✨ **Comprehensive Custom Event Test Suite:** Implemented a new test suite (`test_agent_api_with_custom_event.py`) to thoroughly validate the handling of custom start and stop events within the agent API, ensuring robust and predictable agent responses.

### Changed
- ⚙️ **Flexible Agent Test Runner Configuration:** The `SimulatedAgentApiTestRunner` now allows for optional, custom `start_events` and `stop_events`, falling back to default event types if none are specified, enhancing testing versatility.

### Removed
- 🗑️ **Internal Claude AI Integration Scripts:** Removed development-specific scripts related to Claude AI integration, streamlining the project's internal tooling.

---



## [v0.230.0] - 2025-07-29 - NATS Topic Management and Refined Process Configurations

### Added
- ✨ **Introduced `WalkthroughContext` for Processes**: A new Redis-backed context specifically designed for process walkthroughs, enabling robust and persistent state management across complex, multi-step processes.
- 📦 **New Process Configuration Persistence Model**: Implemented dedicated persistence entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to support flexible storage and retrieval of process configurations. This includes both class-level defaults and instance-specific overrides stored in the database.
- 🚀 **`ProcessConfigSpecs` for Discovery**: Incorporated `ProcessConfigSpecs` into process discovery events, allowing clients to programmatically inspect the schema and parameters required for process configurations, enhancing dynamic integration.
- 💡 **Direct Event Creation Utilities**: Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent`, simplifying the creation of these events from raw input data within API and runner contexts.
- ✅ **Comprehensive Process Dispatcher Tests**: Introduced a new, extensive test suite for `ProcessDispatcher` to ensure reliable event handling, configuration management, and step execution within processes.
- 🧪 **Enhanced Process Service Database Integration Tests**: Added new tests for `ProcessService` and `ProcessConfig` database operations, validating correct interactions with the new persistence model.
- 🤖 **API Endpoint for Agent `StartEvent`**: Exposed a new API endpoint enabling the direct sending of `StartEvent` to agents, which facilitates programmatically initiating agent runs with specified configurations.
- 🧹 **Agent Config Deletion Utility**: Implemented `delete_if_exists_for_class_and_id` in `AgentConfigEntityDocument` for more controlled cleanup of agent configurations in the database.
- 👥 **New Process DTOs**: Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` for clearer representation of process information in API responses and internal data transfer.
- 🧪 **New Test Fixtures**: Added `cleanup_db_and_cache` fixtures for agent and process services to improve test isolation and ensure clean state in integration and unit tests.
- 📝 **Process Service Unit Tests**: New unit tests for `ProcessService` methods, including discovery, event sending, and cache management.

### Changed
- 📈 **Refined Agent and Process API Discovery**: Updated the API discovery mechanisms in `AgentController` and `AgentService` to simplify agent listing, and revamped process discovery in `ProcessService` to provide more detailed and cache-aware retrieval of process instances and classes.
- 📄 **Event Deserialization Flexibility**: Modified `DispatchableWorkflow` to allow its `get_steps_waiting_for_event` method to accept `WorkEvent` types, broadening the dispatcher's capability to react to various process-related events.
- 🗄️ **Improved Event Persistence Logic**: Updated `PersistedAgentEventEntity` and `PersistedProcessEventEntity` to correctly utilize the new `AgentInstanceTopic` and `ProcessInstanceTopic` respectively, ensuring accurate data storage with the refined topic structure.
- 🧩 **Extended `WorkRequestEvent` with `process_id`**: Added a `process_id` field to `WorkRequestEvent` to enhance clarity and provide a direct association with the relevant process instance.
- ✍️ **Enhanced Logging for Subscribers**: Improved logging for `JetStreamEventStore` to provide more detailed information during subscription lifecycle events and improved exception logging, and for `JSSubscriber` to provide more detailed information during subscription lifecycle events (start and stop).
- ⚙️ **Process Controller Submission**: Process start form submissions in the API now dynamically retrieve and pass the process configuration from the discovered process instance, ensuring consistency.
- ⚙️ **Process Runner Configuration**: `ProcessRunner` now accepts `default_process_config` and dynamically handles process configuration loading, distinguishing between class and instance-specific settings.

### Refactor
- 🔄 **NATS Topic Hierarchy Refinement**: Restructured NATS topics for Agents and Processes to introduce clear distinctions between class-level and instance-level communication. This included renaming existing topics (e.g., `AgentTopic` to `AgentInstanceTopic`, `ProcessTopic` to `ProcessInstanceTopic`) and introducing new ones (`AgentClassTopic`, `ProcessClassTopic`, `PartialProcessTopic`). Related `TopicManager` and `Subscriber` classes were updated to align with this new hierarchy.
- 🧹 **Streamlined Process Discovery Events**: Consolidated and refined process discovery events, replacing a monolithic `ProcessDiscoveryResponseEvent` with `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent` for more granular information exchange during discovery.
- ⚡️ **Improved Dispatcher `stop` Method**: Enhanced `BaseDispatcher`'s `stop` method to ensure more robust cleanup of event stores upon dispatcher termination, improving resource management.
- ⚙️ **Centralized Process Configuration Handling**: Modified `ProcessDispatcher` to robustly manage process configurations by prioritizing explicit configurations provided in `ProcessStartEvent` and gracefully falling back to default process configurations, leveraging the new `WalkthroughContext`.
- 🏗️ **Core Context Relocation**: Relocated the foundational `BaseContext` class from `aihub_agent` to `aihub_lib`, promoting its reusability across all core service modules.
- 🗑️ **Delegator Topic Manager Alignment**: Refactored Agent and Process delegators to align their topic management with the new `ProcessClassTopicManager` and `ProcessInstanceTopicManager`, improving consistency and maintainability.
- 🧹 **Streamlined Agent & Process Service Cleanup**: Internal methods in `AgentService` and `ProcessService` were streamlined by adding a `_` prefix to denote private helper methods.
- 📦 **Consolidated API DTOs**: The API's process-related DTOs were reorganized into a clearer hierarchy (`ProcessDTO` now inheriting from `MinimalProcessDTO`, and new `ProcessClassDTO` and `ProcessInstanceDTO` introduced).
- ⚙️ **Process Entity Persistence**: Updated `ProcessEntity` to use `ProcessConfigEntityDocument` for referenced configurations and `ProcessConfigEntityEmbeddedDocument` for default configurations, enhancing process config persistence.

### Removed
- 🗑️ **Deprecated Generic Discovery Events**: Eliminated the generic `DiscoveryRequestEvent` and the monolithic `ProcessTopic` class. These have been superseded by more specific and granular event and topic types, improving type safety and clarity in discovery and messaging workflows.
- 🧹 **Redundant Agent Config Start Event Test**: Removed a test file (`test_agent_config_start_event.py`) as its functionality is now fully covered by updated and more comprehensive dispatcher tests.
- 🗑️ **Obsolete Agent Subscriber Method**: Eliminated `for_agent_instance_events` from `AgentJSSubscriber`, streamlining agent event subscription.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 💾 **S3 Configuration Settings:** Added `S3Config` for managing connection parameters to S3-compatible storage backends.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.

---



## [v0.228.0] - 2025-07-25 - Azure Document Intelligence Key Access Alignment

### Refactor
- 🔄 **Updated Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

---



## [v0.227.0] - 2025-07-23 - Improved Azure Identity Service Robustness

### Fixed
- 🖼️ **Azure User Profile Image Fetching Robustness**: Enhanced the retrieval of user profile images from the Azure Graph API to be more resilient to various API errors. The service now logs warnings for unexpected API issues (non-404 errors) and consistently returns `None` when an image cannot be fetched, preventing unhandled exceptions and improving application stability.

### Refactor
- 🧹 **Import Statement Placement**: Relocated the `asyncio` import to the top-level of the `AzureGraphService` module, aligning with best practices for improved code readability and organization.

---



## [v0.226.0] - 2025-07-22 - API Refinements and DTO Consolidation

### Refactor
- 🧹 **Consolidated Data Transfer Objects (DTOs):** Renamed `AgentClass` to `AgentClassDTO` and introduced `AgentInstanceDTO`, relocating all agent-related DTOs into a dedicated `dto` subdirectory for improved organization and clarity.
- 🔄 **Enhanced DTO Encapsulation:** `AgentInstanceDTO` now manages its own persistence by handling entity creation/updates and generating discovery response events directly, improving data model autonomy.
- 🗄️ **Decoupled Agent Persistence:** The `AgentEntity` creation and update logic was refactored to accept explicit parameters instead of DTO objects, enhancing the reusability and flexibility of the persistence layer.
- ⚙️ **Standardized Event Specification Handling:** Updated `EventSpec` creation methods to consistently use `EventSpecs` objects, improving internal data handling.
- 🔗 **Streamlined Topic Inheritance:** `AgentInstanceDiscoveryTopic` now correctly inherits from `AgentClassDiscoveryTopic`, reducing redundancy and clarifying topic structure.

### Changed
- 📄 **Agent Configuration Data Format:** The `ChatService` now passes agent configuration data as a dictionary instead of a Pydantic object when publishing `UserMessageEvent`, standardizing data exchange.

### Removed
- 🗑️ **Deprecated Agent DTO Files:** Removed the old `AgentInstance.py` and `aihub_api/aihub_api/agents/__init__.py` files as part of the DTO consolidation and relocation effort.
- 🧹 **Redundant NATS Topic Managers:** Cleaned up unused and overlapping topic management methods within `AgentClassTopicManager` for a leaner API.
- 🚫 **Transferred Discovery Event Logic:** Removed the `from_agent_instance` method from `AgentInstanceDiscoveryResponseEvent` as its functionality has been moved to the `AgentInstanceDTO` for better encapsulation.

---



## [v0.225.0] - 2025-07-21 - Enhanced Document Structure and Content Rendering

### Added
- ✨ **Hierarchical Document Headings**: Implemented the dynamic rendering of document headings (H1-H6) directly within the context. This provides a clearer hierarchical structure and significantly improves readability and navigation for complex documents by showing heading changes as content progresses.
- 📄 **Structured Content and Summary Tags**: Individual node content is now explicitly wrapped in XML-like tags (`<content>` or `<summary>`) based on its type. This provides more precise semantic context and better structural clarity for each block of text.
- 🔒 **HTML Escaping for Content**: Enhanced the integrity and security of rendered content by automatically escaping HTML special characters in both headings and content. This prevents unintended rendering issues and potential injection vulnerabilities in the generated output.

### Changed
- ⚙️ **Updated Default Document Language**: The default language for newly ingested nodes has been updated from English to German, better aligning with regional configurations.
- ⚡️ **Refined Node Sorting Logic**: Improved the internal sorting mechanism for nodes within a document. Nodes are now ordered more accurately based on their section start lines and type, which is crucial for the correct presentation of the new hierarchical structure.
- 🧹 **Streamlined Timestamp Handling**: An internal utility for formatting Unix timestamps has been removed, as date and time handling for document metadata is now managed more efficiently by the underlying system.

---



## [v0.224.0] - 2025-07-21 - Flexible Agent Configuration and Advanced Discovery

### Added
- ✨ **Dynamic Agent Configuration**: Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Enhanced Agent Discovery Mechanism**: Implemented granular discovery for agent *classes* and specific agent *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations**: Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups across deployments.
- 🔌 **New Pydantic Models for Vector Store Configurations**: Introduced dedicated Pydantic configurations for `AzureAISearchVectorStore` and `MilvusVectorStore` (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`), allowing for direct embedding and validation of vector store settings within agent configs.
- 📈 **`agent_class` Field in `AgentConfig`**: A new `agent_class` field has been added to `AgentConfig` for consistent agent class identification throughout the system.
- 📄 **`save_config.py` Example**: A new example demonstrating how to persist agent configurations to the database for custom or production deployments.
- 🧪 **Comprehensive Unit and Integration Tests**: Added extensive new tests for agent dispatcher logic, agent configuration precedence, and database persistence, ensuring the robustness and correctness of new features.
- 🌐 **Locale String Entity**: Introduced `LocaleStringEntity` for improved persistence of localized strings within database models.
- ⚙️ **New Configuration Settings**: Added new environment variables to the `LLMWrappingAgent` playground, indicating new configuration requirements for deployment.

### Changed
- ⚙️ **Refined Agent Configuration Loading Logic**: The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization**: Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 💡 **Improved Type Specificity for LLM and Vector Store Configs**: Agent configurations (e.g., in `RAGAgent`) now utilize more precise type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration**: RAG and Retrieval agents now leverage the `.to_llama_index()` method directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- ⚡️ **Enhanced Background Task Management**: Improved handling of `asyncio.Task` instances within dispatchers and tracers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Revised API Agent Discovery**: The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- 🧹 **Renamed `EventModelCreationService` to `ModelCreationService`**: This service has been renamed to reflect its broader utility beyond just event models, with adjustments to excluded fields to accommodate the new `agent_config`.
- 💬 **ChatService includes `agent_config` in `UserMessageEvent`**: `ChatService` now attempts to fetch and include the `AgentConfig` in the `UserMessageEvent` if available in the database, providing agents with more context.
- 🚧 **StartEvent Structure**: The `StartEvent` now includes an optional `agent_config` field, allowing for dynamic override of agent configurations at runtime.

### Refactor
- 🔄 **Consolidated Agent Configuration Management**: Standardized agent configuration handling across the system, enabling dynamic overrides and database persistence for agent instances.
- ✨ **Refined Agent and Event Discovery Architecture**: Overhauled the discovery mechanism to support both class-level and instance-level agent introspection, providing more granular control and information.
- 🏗️ **Reorganized API DTOs for Agent Representation**: Introduced dedicated DTOs (`AgentClass`, `AgentInstance`) to clearly separate the concept of an agent's definition from its configured, runnable instances in the API.
- 🗄️ **Refined Agent Configuration Persistence**: Reworked agent configuration persistence in the database, transitioning to a model that references external `AgentConfigEntityDocument` for user-defined configurations and embeds `AgentConfigEntityEmbeddedDocument` for default settings, allowing for more flexible and discoverable agent setups.
- 📁 **Project Structure Alignment**: Reorganized playground test directories for agent and event models to improve logical grouping and clarity.

### Fixed
- 🐛 **Graceful handling of missing profile images**: Improved the Azure Graph Service to gracefully handle 404 responses when fetching user profile images, preventing errors for users without a profile picture.
- 🐞 **Frontend Process DTO Typo**: Corrected a minor typo in the `ProcessDTO` schema in the web frontend SDK.

### Removed
- 🗑️ **Deprecated Configuration Fields**: The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration and allowing for more flexible, agent-specific prompt and UI customization to be defined in agent subclasses.

---



## [v0.223.0] - 2025-07-18 - Streamlined Pipeline Operations and Enhanced Robustness

### Added
- 🦾 **New Job Creation Utility**: Introduced `materialize_asset_job` to simplify the creation of jobs for materializing specific selections of assets.
- 📅 **Automated Playground Workflows**: Implemented new daily jobs and schedules within the playground environment to automatically observe source data and manage document removal processes.

### Changed
- ⚙️ **Refined Asset Automation**: Adjusted automation configurations for document and data lake file removal assets, transitioning from eager conditions to more explicit job-driven scheduling.
- 🔗 **Specialized I/O Manager**: Updated the SharePoint observable asset to utilize a dedicated `sharepoint_io_manager`, ensuring more appropriate handling of SharePoint data interactions.

### Fixed
- 🐛 **Robust Figure Deletion**: Improved the document figure deletion process to gracefully handle cases where associated figure directories do not exist, preventing unnecessary errors and log messages.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event structures (`ContextualizedProcessEvent`) for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🎯 **Granular Human Targeting in Processes**: The `Human.Out` process delegator now uses more specific `user_ids`, `user_emails`, and `user_roles` fields, replacing the broader `users` list for better control over human-in-the-loop requests.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- ✂️ **Unified Chat Message Models**: Combined `_Input` and `_Output` variants of ChatMessage and AssistantChatMessage models into single, unified models for simpler API consumption.

### Removed
- 🗑️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.

---



## [v0.221.0] - 2025-07-14 - Prompt Refinements and Image Handling Improvements for RAG

### Changed
- 🔄 **Updated RAG Context Prompt Role:** The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.

### Fixed
- 🖼️ **Corrected Image URL Handling in RAG Prompts:** Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.

---



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
- 📄 **Refined Docstrings and Comments:** Various docstrings and inline comments across the codebase were updated for greater clarity and precision, especially concerning complex components like dispatchers and service methods.

### Fixed
- 🐛 **Clarified Error Messages:** Enhanced error messages in several API endpoints (e.g., thread and role management) and the process dispatcher to provide more informative feedback to users.
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

### Removed
- 🗑️ **Deprecated Event Retrieval Endpoint**: The broad `/events` API endpoint, which returned all persisted events visible to the user, has been removed in favor of more granular thread-specific event retrieval.

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



## [v0.206.0] - 2025-07-01 - Pydantic V2 Modernization and Core System Alignment

### Changed
- 🔄 **Platform Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to `v0.206.0`, ensuring a unified and consistent release across the entire platform.

### Refactor
- 🧹 **Pydantic Model Modernization**: Migrated numerous Pydantic models across the codebase to leverage `Annotated` for `Field` definitions and streamline default value assignments, enhancing type clarity and aligning with Pydantic v2 best practices. This involved updating syntax for lists, dictionaries, and optional fields.

---



## [v0.205.0] - 2025-07-01 - Cross-Service Version Alignment

### Changed
- 🔄 **Core Service Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to version `v0.205.0`, ensuring consistent and current builds across the platform.

---



## [v0.204.0] - 2025-07-01 - Enhanced Release Workflow Reliability

### Changed
- 🚀 **Improved Release Workflow Resilience**: The automated tagging and release GitHub Actions workflow (`add-tag.yml`) now gracefully handles failures during changelog generation, ensuring that the version tag is always finalized even if the changelog script encounters an issue.
- ⚙️ **Robust Changelog Script Execution**: The `generate-changelog.sh` script has been enhanced with error handling for the LLM command, preventing script termination on LLM failures and providing clear warnings in the output.
- 🔑 **Updated Gemini API Key Configuration**: The method for setting the Gemini API key in the CI/CD pipeline has been updated to align with the latest `llm` CLI syntax, utilizing the `--value` flag for improved clarity and consistency.
- 🧹 **Streamlined CI/CD Python Setup**: Removed the explicit Poetry cache configuration within the GitHub Actions Python setup step, optimizing the workflow's efficiency.
- 🔄 **Conditional Changelog Amendment**: The final commit for release now intelligently amends the `changelog.md` file only if the changelog generation step was successful, preventing incomplete or erroneous changelog entries from being committed.

---



## [v0.203.0] - 2025-06-30 - Introducing AI-Powered Changelog Automation

### Added
- ✨ **Automated Changelog Generation**: A new GitHub Actions workflow is introduced to automatically generate changelog entries based on `git diff` using an LLM, enhancing release documentation.
- 🚀 **LLM-Driven Release Notes**: Implemented a dedicated script and a detailed LLM prompt file to enable the automated creation of clear and structured changelog entries.
- 📝 **`changelog.md` Tracking**: A new `changelog.md` file is now automatically maintained and updated with notable changes for each release.
- ⚙️ **Makefile Integration**: A new `changelog` target is added to the Makefile, providing a convenient way to trigger the automated changelog generation process.

### Changed
- 🔄 **Refined CI/CD Workflow**: The main GitHub Actions workflow for versioning and tagging has been updated to seamlessly integrate the new changelog generation process, ensuring release consistency.
- 📦 **Streamlined Dependency Setup**: Python and Poetry installation steps within the CI workflow have been consolidated for a more efficient and robust build environment.

### Refactor
- 🧹 **Workflow Step Optimization**: Internal steps within the GitHub Actions workflow, such as SSH key setup and dependency installations, have been reordered and simplified for improved clarity and efficiency.

---



## [v0.202.0] - 2025-06-30 - Enhanced User Identity and Authentication Framework

### Added
- ✨ **Unauthenticated Health Check Endpoint**: The `/health` endpoint now allows unauthenticated access, simplifying integration with load balancers and monitoring systems for application status verification.
- 🔑 **Centralized JWKS and RSA Key Caching**: Introduced robust caching for JSON Web Key Sets (JWKS) and RSA keys within the OAuth2 authentication handler, significantly reducing external calls and improving the performance of token validation.
- 🧑‍💻 **Direct User Entity Lookup by Email**: Added a `by_email` method to `UserEntity`, enabling direct and efficient retrieval of user information using their email address.

### Changed
- 📄 **Clarified Figure Description Prompting**: Revised the prompt for generating figure descriptions to ensure that surrounding text is used strictly to understand the image's role, preventing the AI from altering factual visual descriptions.
- 🤖 **Updated Bot API Paths for Token Authentication**: Adjusted API endpoint paths within the `aihub_bot` (e.g., from `/api/v1` to `/bearer_token/v1`) and related setup scripts to explicitly reflect the use of bearer tokens for bot interactions, enhancing clarity and security.
- 🖥️ **UI Updates for User Identity Display**: Modified frontend components to correctly display user information using the new `email` property from the `UserIdentity` model, replacing the `preferredUsername` property.

### Fixed
- 🐛 **Improved Image Description Robustness**: Implemented a retry mechanism for image description generation in the data pipeline to handle `BadRequestError` (often caused by content safety filters), allowing retries without surrounding text to prevent complete processing failures.

### Removed
- 🗑️ **Deprecated User Identity Modules**: Eliminated redundant files such as `AuthenticatedUser`, `BaseUserInformationProvider`, `MultiStrategyUserInformationProvider`, and various specific user information providers, as their functionalities are now integrated into the new identity framework.
- 🗑️ **Obsolete Development HTTP Client**: Removed `playground/development/generate_auth_token.http` as it is no longer relevant with the new authentication setup.

### Refactor
- 🔄 **Revamped User Identity and Authentication System**: Introduced a new, more flexible `IdentityProvider` abstraction layer, replacing the monolithic `AuthenticatedUser` and `UserInformationProvider` classes with a modular design. This streamlines integration with various identity sources (Azure AD, API tokens, development mocks) and enhances maintainability.
- 🧹 **Consolidated Azure Graph Service**: Moved and refactored Azure Graph API interactions into a dedicated `AzureGraphService` within the `AzureIdentityProvider`, ensuring a cleaner separation of concerns and improved performance with robust caching.
- ⚡️ **Enhanced Token and OAuth2 Handlers**: Updated authentication handlers (`TokenAuthHandler`, `OAuth2AuthHandler`, `OpenWebuiAuthHandler`, `TokenAndOauth2Handler`) to leverage the new `IdentityProvider` framework, simplifying their logic and making them more extensible.
- ⚙️ **Updated Core Controllers and Services for New Identity**: Adapted all relevant API controllers and services to seamlessly integrate with the new `UserIdentity` model and `IdentityProvider` dependencies, involving widespread changes to method signatures and user information access patterns.
- 🗑️ **Streamlined Development-Only Authentication**: Replaced `NoAuthHandler` with `DangerousDevelopmentOnlyAuthHandler` and `DangerousDevelopmentOnlyIdentityProvider` to explicitly mark development-only authentication as unsuitable for production and to align with the new identity architecture.

---



## [v0.200.0] - 2025-06-30 - Introducing Process Automation and Core Infrastructure Generalization

### Added
- 🚀 **New `aihub_process` Microservice**: Introduced a dedicated microservice for advanced process orchestration, enabling the chaining and coordination of diverse entities including AI agents, human experts, and external programs into structured workflows.
- 🏗️ **Generalized Workflow Dispatching**: Introduced `DispatchableWorkflow` as a new abstract base class in `aihub_lib`, providing a unified foundation for all event-driven workflows (e.g., agents and processes), complemented by a `BaseDispatcher` for generic execution management.
- 📬 **Process-Specific Event System**: Added a comprehensive set of new event types (e.g., `ProcessEvent`, `WorkEvent`, `WorkRequestEvent`) and NATS topic structures (`ProcessTopic`, `ProcessDiscoveryTopic`) to enable robust communication within process workflows.
- 🤝 **Entity Delegation Framework**: Implemented abstract and concrete delegators (`AgentDelegator`, `ProcessDelegator`) that seamlessly translate process work requests into entity-specific actions (e.g., agent `StartEvent`) and entity work outputs into process-consumable `WorkEvent`s.
- ⚙️ **Process Configuration and Runtime**: Introduced `ProcessConfig` for structured process instance configuration and provided `ProcessRunner` and `ProcessTestRunner` for simplified deployment and testing of process automation.
- 🎯 **Declarative Process Step Definition**: Implemented the `@process_step` decorator, enabling a declarative approach to defining process steps with strict validation of input and output entity delegations.
- 🗺️ **Internationalization for Processes**: Integrated new localization files and a `ProcessLocaleHandler` to support multi-language messages and descriptions throughout process workflows.
- 🧪 **Extensive Process Examples**: Provided a wide array of new playground examples (`AgentOnlyProcess`, `FanOutProcess`, `MultiInputProcess`, `ProcessSequence`) and their respective tests to showcase various process orchestration patterns.
- 💡 **New `Infra GPU` Development Configuration**: Added a new run configuration for deploying and debugging GPU-enabled infrastructure components within the development environment.

### Changed
- 🔄 **Refactored Agent Core**: The `aihub_agent` microservice's core `Agent` class now inherits from `DispatchableWorkflow`, and its `Dispatcher` has been renamed to `AgentDispatcher` and now extends the new `BaseDispatcher`, aligning with the generalized architecture.
- 📦 **Agent Context Relocation**: Agent-specific context classes (`RunContext`, `ThreadContext`) have been moved from `aihub_lib` to `aihub_agent` to improve module separation and reduce inter-service coupling.
- ⚙️ **Streamlined Agent Configuration**: The `color`, `voice`, and `system_prompt` fields in `AgentConfig` have been deprecated to promote more flexible and custom agent configurations in subclasses.
- 📈 **Improved Database Indexing**: Enhanced database indexes for `ConversationEntity`, `PathEntity`, and `UserEntity` in `aihub_bot` and `aihub_lib` to significantly boost query performance and enforce data uniqueness.
- 📄 **Updated Documentation**: Modified existing agent documentation to reflect the new `AgentDispatcher` terminology and updated the `aihub_lib` module's IntelliJ IDEA configuration for better project management.
- 🏷️ **Version Updates**: All microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_pipeline`, `aihub_lib`, `aihub_process`) have been bumped to `v0.200.0`, along with their inter-service dependency tags, reflecting the new release.
- 🛠️ **Unified CI/CD Integration**: Updated GitHub Actions workflows and Makefiles across the repository to seamlessly integrate and manage the new `aihub_process` microservice in linting, testing, and tagging pipelines.
- 🌐 **Refined OpenAPI Schema Generation**: Adjusted the OpenAPI schema generation for `LocaleString` to correctly reflect optional fields and refined generated TypeScript SDK types for ingested documents/nodes to include metadata and explicit content types.
- 📊 **Generalized Event Persistence**: Refactored `aihub_lib`'s event persistence layer to differentiate between and store `agent_events` and new `process_events` distinctly, preparing for comprehensive event logging for both workflow types.
- 💬 **Thread Entity Enhancements**: Extended `ThreadEntity` in `aihub_lib` with new fields and methods to explicitly associate conversational threads with process walkthroughs, enabling processes to manage their own conversational contexts.
- 🔗 **Updated NATS Client SDK**: The `aihub_web` frontend's generated TypeScript SDK has been updated to reflect backend API changes, including the removal of a deprecated bot endpoint and schema adjustments.
- 🏷️ **Agent ID Validation**: Added a regular expression pattern validation to the `agent_id` field in `AgentConfig` to enforce consistent naming conventions.

### Fixed
- 🐛 **API Typecheck Issue**: Corrected a build script error in the `aihub_api` Makefile that incorrectly targeted `aihub_agent` for type checking, ensuring `aihub_api`'s type integrity.
- 🐞 **Playground Example Naming**: Renamed `ProcessEvent` to `BoundedLoopAEvent` within a playground example for improved clarity and adherence to naming conventions.

### Removed
- 🗑️ **Deprecated Bot Endpoint**: The `sendEventToBotInTheLoopAgentBotInTheLoopAgentSendEvent` endpoint has been removed from the `aihub_api`'s generated client SDK, indicating its deprecation and removal from service.

---



## [v0.199.0] - 2025-06-27 - Enhanced Document Processing and Accessibility

### Added
- ✨ **New Docling Integration**: Introduced `DoclingLoader` and `DoclingAccess` for enhanced document parsing capabilities, supporting a wider range of document formats and robust figure extraction directly within the parsing process.
- ⚙️ **Configurable Document Parsers**: Added a new `LoaderType` enum and enhanced the `DocumentParserResource` to allow flexible selection between Docling, Document Intelligence, or a combination of both parsers based on specific document processing requirements.
- 📄 **Dynamic Figure Description Generation**: Implemented a new `generate_figure_descriptions` operation that leverages Large Language Models to automatically create detailed alt-text for figures, significantly improving document accessibility and searchability.
- ➕ **Extended Document Intelligence Support**: Added configurable file extensions to the `DocumentIntelligenceConfig`, allowing administrators to specify which file types are supported for processing by Azure Document Intelligence.

### Changed
- 🔄 **Revamped Document Ingestion Pipeline**: Significantly refactored the core document ingestion pipeline, streamlining the process of parsing, figure extraction, and table reformatting by integrating these functionalities directly into the document loaders.
- 📊 **Improved Table Handling**: Document Intelligence Loader now directly converts HTML tables to Markdown, and tables processed by the new Docling Loader are also correctly tagged, ensuring consistent and structured table representation across all processed documents.
- 🖼️ **Streamlined Figure Extraction**: Figure extraction and saving to the data lake are now handled directly within the respective document loaders (`DoclingLoader` and `DocumentIntelligenceLoader`), simplifying the overall workflow for handling visual content.
- 💬 **Updated Figure Description Prompts**: Adjusted internal prompt templates used for figure description generation to utilize `RichPromptTemplate` and `ChatML` format, enhancing model instruction and output quality.

### Refactor
- 🧹 **Centralized Path Utilities**: Moved the `create_data_lake_figures_folder_name` utility to `aihub_lib` and renamed it to `create_figures_folder_name`, promoting code reuse and consistency across different microservices.

### Removed
- 🗑️ **Deprecated Figure URL in Metadata**: Removed the `figure_url` field from `FigureMetadata` as figures are now directly referenced by their blob storage path, simplifying metadata management and avoiding redundant URLs.
- ⛔ **Redundant Pipeline Operations**: Eliminated several now-redundant pipeline operations (`doc_with_figures_to_ref_doc`, `inject_figures`, `reformat_tables`, `save_figures_to_data_lake`) as their functionalities have been seamlessly integrated into the enhanced document loaders and the new `generate_figure_descriptions` operation.

---



## [v0.198.0] - 2025-06-24 - Pipeline Embedding Enhancements

### Changed
- ✨ **Improved Text Embedding:** Updated the `embed_nodes` operation in the pipeline to utilize `get_content(metadata_mode=MetadataMode.EMBED)` for nodes, ensuring that vector embeddings are generated with more comprehensive contextual information, leading to enhanced embedding quality.

---



## [v0.197.0] - 2025-06-24 - Azure Data Lake Storage Integration

### Added
- ✨ **Azure Data Lake Storage Resource:** Introduced a new Infrastructure-as-Code (IaC) resource definition for deploying Azure Data Lake Storage accounts.
- 🔑 **Data Lake Role Assignments:** Added functionality to assign necessary roles (`Storage Blob Data Reader`, `Storage Blob Delegator`) to user-assigned identities, enabling secure and granular access to Data Lake Storage.
- ⚙️ **Data Lake Naming Convention:** Established a default naming suffix for Azure Data Lake Storage resources to ensure consistent deployments.

---



## [v0.196.0] - 2025-06-20 - Enhanced Pull Request Automation

### Changed
- 🚀 **Streamlined Pull Request Creation**: The automated draft Pull Request workflow now automatically populates the PR description with commit messages, significantly improving efficiency for contributors.
- ⚙️ **Workflow Reliability**: The internal `auto-draft-pr.yml` workflow now includes a standard checkout step, enhancing its stability and ensuring proper execution.

---



## [v0.195.0] - 2025-06-20 - Optimized Partition Management

### Refactor
- ⚡️ **Improved Dynamic Partition Management**: Optimized the `replace_partition_keys` utility in the pipeline core to intelligently update dynamic partitions by only adding or removing keys that have genuinely changed, leading to enhanced efficiency and reduced unnecessary operations.

---



## [v0.194.0] - 2025-06-19 - Internal Pipeline Refinements

### Refactor
- 🧹 **Streamlined Data Lake File Fetching:** Removed the unused `context` parameter and associated logging from `fetch_all_files_in_data_lake` operations, enhancing code clarity and reducing unnecessary dependencies in the pipeline.

---



## [v0.193.0] - 2025-06-19 - Enhanced Branching Workflow and PR Automation

### Added
- 🚀 **Structured Branch Naming Enforcement:** Introduced a new validation step for branch names, requiring them to adhere to a `base/scope` format. This ensures greater consistency and clarity across development branches.
- ⚙️ **Predefined Development Scopes:** Implemented a list of allowed project scopes (e.g., `agent-custom`, `workflows`, `chat-backend`) that branches must conform to, standardizing how work areas are identified.
- 📝 **Contextualized Draft PR Titles:** Automatically generated draft pull requests now include the parsed `base` and `scope` from the branch name in their titles, providing immediate and detailed context for work in progress.

### Changed
- ⚡️ **Enhanced Draft PR Automation:** The GitHub Actions workflow for creating draft pull requests has been significantly improved for robustness and security, including a check to prevent duplicate PRs and the use of a dedicated GitHub App token.
- ✅ **Refined Workflow Triggers:** Streamlined the workflow trigger logic to ensure the automation specifically activates on new branch creations, making the process more precise.

---



## [v0.192.0] - 2025-06-18 - Streamlined Development Workflow

### Changed
- 🎨 **Updated Branch Naming Conventions:** Streamlined the branch naming validation in pull request workflows, now supporting a more flexible `[type]/[name]` pattern (e.g., `feat/my-feature`, `bug/fix-issue`) for enhanced development agility.

---



## [v0.191.0] - 2025-06-18 - Enhanced LLM Event Reporting

### Added
- ✨ **Enhanced LLM Event Creation:** Introduced a new factory method `LLMEvent.from_chat_response` to simplify the creation of LLM events directly from LlamaIndex chat responses, including automatic token counting and integration with agent configurations.

---



## [v0.190.0] - 2025-06-16 - Improved File Path Handling

### Fixed
- 🐛 **Improved file path handling** in pipeline utilities to correctly parse filenames with multiple extensions (e.g., `document.v2.pdf`), ensuring accurate folder creation in the data lake.

---



## [v0.189.0] - 2025-06-16 - Multimodal RAG & Secure File Sharing Advancements

### Added
- 🖼️ **Multimodal RAG Capabilities**: Enabled the RAG system to process and embed figures and tables into prompts, allowing Large Language Models to analyze content from both text and images for comprehensive answers.
- 🔗 **Secure Anonymous File Sharing**: Introduced a new public method for `FileService` to generate secure, time-limited URLs for anonymous access to blob storage files, enhancing external sharing capabilities.
- 📄 **Extended Ingested Document Metadata**: Added support for including additional, unstructured metadata for ingested documents, providing greater flexibility for storing document properties.

### Changed
- ⏱️ **Dynamic SAS Token Lifetime for Anonymous URLs**: Enhanced anonymous file URLs to support dynamic SAS token lifetimes, allowing the generated links to expire precisely when intended.
- 💬 **RAG Agent Prompt Enhancement**: Updated the RAG Agent's system prompt to explicitly inform the LLM about its ability to process both document and image context, improving its response generation.

### Fixed
- 🐛 **Multimodal Chat Message Serialization**: Resolved an issue where multimodal chat messages (containing image or audio URLs) were not correctly serialized, ensuring reliable event transmission across services.

### Refactor
- 🧹 **Centralized SAS URL Generation**: Refactored the underlying SAS URL generation logic into `AnonymousFileAccessService`, promoting reusability and simplifying `FileService`.
- ⚙️ **Standardized Node Content Type Tagging**: Implemented standardized tagging of figures and tables within processed documents using dedicated HTML-like tags, improving internal parsing and node creation for multimodal content.
- 🦾 **Simplified RAG Agent Context Handling**: Streamlined the RAG Agent's internal handling of run context and locale, reducing complexity and improving code clarity.

---



## [v0.188.0] - 2025-06-13 - Unlock Secure File Access and Richer Document Views

### Added
- 🔐 **Introduced Secure File Access and Sharing**: A comprehensive new system for secure, time-limited access to files stored in Azure Blob Storage. This includes API endpoints for both logged-in and anonymous users to retrieve signed URLs or be redirected directly to files, offloading bandwidth and enhancing data security.
- 📤 **Enabled File Attachments in Messages**: Extended core data models for messages and metadata to support attaching files, paving the way for richer interactions and enhanced content sharing.
- 🖼️ **Added Dedicated Markdown Components**: New Markdown components (`MarkdownFigure`, `MarkdownTable`, `ResolveImageComponent`) were introduced to improve rendering and securely load images and figures from cloud storage directly within document content.
- 📄 **Integrated Azure Blob Storage Infrastructure**: New underlying infrastructure components for seamless access and configuration of Azure Blob Storage, providing robust support for secure file operations.

### Changed
- 📈 **Enhanced Document List Display**: The knowledge base document list now includes a "Number of Pages" column and a direct download button, improving usability and quick access to original documents.
- 🎨 **Refined Markdown Styling and Rendering**: Updated the markdown renderer for improved visual consistency and readability, including better spacing for headings and refreshed link styles within documents.
- 🔄 **Updated Figure Referencing in Pipelines**: Modified how figures are referenced within data ingestion pipelines, moving towards internal paths to leverage the new secure file access system.

### Refactor
- 🧹 **Standardized Internal API Client Configuration**: Streamlined the base URL configuration for the internal API client, improving maintainability and consistency across the frontend.

---



## [v0.187.0] - 2025-06-12 - Enhanced Document Processing Reliability

### Fixed
- 🐛 **Improved Markdown Parsing Robustness:** Enhanced the Markdown structural node parser to gracefully handle empty content, preventing errors and improving parsing reliability.
- 🛠️ **Strengthened Table Reformatting:** Added a check to prevent errors when reformatting tables in documents that lack text content, making the process more robust.

### Refactor
- 🧹 **Refined Document Processing Pipeline:** Updated internal document factory calls to use keyword arguments for improved clarity and maintainability, especially for figure injection and saving.

---



## [v0.186.0] - 2025-06-12 - Enhanced Document Ingestion and Azure AD Support

### Changed
- 💾 **Enhanced Document Ingestion**: Improved the `IngestedNode` and `IngestedBase` models to automatically preserve and store any additional, non-standard metadata from source documents, ensuring higher data fidelity and flexibility in RAG pipelines.
- 🔑 **Improved Azure OpenAI Embedding Authentication**: Explicitly enabled Azure AD authentication for Azure OpenAI embedding models, ensuring secure and proper token-based access.

---



## [v0.185.0] - 2025-06-11 - Release Sync and Build Optimization

### Refactor
- 🚀 **Optimized GitHub Action for Image Builds:** The `build_image` GitHub Action no longer performs a redundant code checkout, streamlining the CI/CD build process for improved efficiency.

---



## [v0.184.0] - 2025-06-11 - Web UI Modernization and Development Environment Refinements

### Removed
- 🗑️ **Storybook Development Environment**: Eliminated Storybook and all associated configurations and dependencies from the web UI, streamlining the frontend development setup.
- 🗑️ **Shadcn-Vue Makefile Command**: Removed the `shadcn-vue` component generation command from the web UI's Makefile.

### Changed
- ⚡️ **Default Web UI Local Port**: Updated the default local development port for the web UI from `5173` to `8080` within `docker-compose-webui.yml`, standardizing the development environment.
- 📦 **PrimeVue Dependency Management**: Adjusted PrimeVue's dependency handling by transitioning it to `peerDependencies` in the web UI's `package.json`, offering greater flexibility for project integration.

### Refactor
- 🔄 **`useRouteQuery` Hook Usage**: Standardized the usage of the `useRouteQuery` composable across the web UI, now explicitly passing `route` and `router` instances for improved clarity and consistency.
- 🧹 **OIDC Configuration Management**: Cleaned up the Nuxt configuration by removing hardcoded OIDC client and tenant IDs, allowing for more flexible and dynamic runtime configuration.

---



## [v0.183.0] - 2025-06-11 - Enhanced Document Summarization and Metadata Management

### Added
- 📄 **Node Metadata Fields**: Introduced `DOCUMENT_STORE_NAME` and `INDEX` to node metadata, allowing for better organization, traceability, and ordering of document chunks and summaries.

### Changed
- 🧠 **Recursive Summarization Logic**: Significantly improved the `RecursiveSummaryParser` to create more coherent and hierarchically linked summaries by establishing better parent-child and sibling relationships between summary nodes and grouping content under common headings.
- 🗣️ **Summarizer Prompts**: Updated summarizer prompts across German, English, French, and Italian to generate more concise, direct, and "TL;DR" style summaries.
- ⚙️ **Markdown Structural Node Parsing**: Enhanced the Markdown structural node parser to automatically embed the document's store name into node metadata, improving document traceability within pipelines.
- 🤖 **Playground Language Model**: Switched the default language model in the playground environment from `gpt-4o` to `gpt-4o-mini`, optimizing for cost-effective experimentation.

### Refactor
- 🧹 **Playground Data Lake Configuration**: Renamed and updated data lake container and directory variables within the playground environment for clearer distinction (e.g., from `test` to `papers`).

---



## [v0.182.0] - 2025-06-11 - Bot Typing Indicator Refinement

### Fixed
- 🐛 **Bot Typing Behavior:** The bot's typing indicator is now sent more intelligently, ensuring it only appears when a response is intended. This prevents unnecessary typing indicators, especially when an expiration message or other internal processing occurs first.

---



## [v0.181.0] - 2025-06-10 - Enhanced Bot Interactions and System Stability

### Fixed
- 🐛 **Improved Content Extraction Robustness:** Enhanced file content extraction in `ContentExtractor` to gracefully handle cases where content types might be undefined, preventing potential errors during file processing.
- 🐛 **Corrected Agent Display ID:** Addressed an issue where the `display_id` for agent messages was incorrectly set to the `thread_id` in `AgentCompletionHandler`, ensuring accurate message attribution and display.

### Changed
- ⚙️ **Flexible OpenAI Completion Calls:** The `OpenaiCompletionHandler` now accepts additional keyword arguments (`**kwargs`) for `get_completion` and `get_stream_completion`, providing greater extensibility and flexibility for future model interactions.
- 🌐 **Internationalization for Exception Handling:** Integrated `LocaleHandler` into the `OpenaiCompletionHandler`'s exception handling, laying the groundwork for providing localized error messages and improving global user experience.

### Refactor
- 🧹 **Streamlined Completion Handler Calls:** Removed redundant `service` arguments from `CompletionHandler` method calls in `BaseChatBot`, simplifying the API and improving code cleanliness.
- 🔄 **Standardized Channel ID Usage:** Updated `StreamAgentChatBot` to utilize the `Channels.webchat` constant for channel ID comparisons, enhancing code clarity and maintainability by replacing a magic string.
- 🧹 **Reorganized Completion Handler Module:** The `CompletionHandler` module's import path was updated across bot components, signifying a general reorganization for improved code structure and maintainability.

---



## [v0.180.0] - 2025-06-10 - Bot Robustness and Core Version Synchronization

### Fixed
- 🐛 **Improved Chatbot Locale Handling:** Enhanced the `BaseChatBot` to gracefully manage situations where an activity's locale is not specified, ensuring a fallback to a default locale instead of encountering an error.

---



## [v0.179.0] - 2025-06-10 - Unlock Multimodal AI with File Uploads and Rich WebUI Feedback

### Added
- 🚀 **Multimodal Input Support**: Introduced the capability for users to include files (e.g., images, documents) directly within chat requests, enabling richer, multimodal interactions with AI-Hub assistants.
- ✨ **Open WebUI Pipeline for File Sending**: A new pipeline has been added to facilitate seamless integration with Open WebUI, allowing users to attach and send files directly to AI-Hub assistants from the WebUI.
- 📄 **Enhanced Open WebUI Source Display**: Improved the Open WebUI integration to display detailed retrieved sources (e.g., from RAG operations) within the chat interface, providing better transparency and context for AI responses.
- ⚙️ **Core File Data Model**: Introduced a new `UserUploadedFile` data model to standardize the representation and handling of user-uploaded file data across the system.

### Fixed
- 🐛 **API Token Generation Compatibility**: Resolved an issue in the **API token generation script** by ensuring Azure CLI commands execute correctly across various operating system environments.

---



## [v0.178.0] - 2025-06-05 - Enhanced Infrastructure and Scalability for Core Services

### Added
- 🦾 Enabled Azure Container Apps environment delegation for **Dagster** and **WebUI** subnets, enhancing integration with Container Apps.
- 🔑 Introduced a **secret key configuration** for OpenWebUI, improving security.
- ⚡️ Configured **OpenWebUI** with explicit Redis URL for WebSocket management and optimized **Uvicorn workers** and thread pool sizes for improved performance.
- ⚙️ Introduced configurable **minimum and maximum replicas** for OpenWebUI, allowing for dynamic scaling.
- 🚀 Implemented **workload profiles** (`Consumption` and `general-D4`) within the Azure Container Apps managed environment, providing dedicated compute resources for specific services.

### Changed
- 🛡️ Updated **Dagster PostgreSQL database** configuration to `retain_on_delete=True`, preventing accidental database deletion during infrastructure teardown.
- 🔄 Updated **OpenWebUI scaling** to leverage new `min_replicas` and `max_replicas` configurations for more flexible deployment.

### Refactor
- 🧹 Cleaned up **IAC configuration files** by removing unused import statements, improving code clarity.

---



## [v0.177.0] - 2025-06-04 - Advanced Document Parsing and AI-Powered Figure Descriptions

### Added
- ✨ **Intelligent Figure and Table Extraction:** The document processing pipeline now accurately extracts and saves figures and tables separately, enriching document understanding.
- 🖼️ **AI-Powered Figure Description Generation:** Leveraging a vision-enabled LLM, the system now automatically generates descriptive alt-text for figures, improving accessibility and searchability.
- 🗄️ **Dedicated Figure Storage:** Extracted figures are now persistently stored in Azure Data Lake, ensuring their availability for further processing and referencing.
- 📄 **Enhanced Document Metadata:** Document nodes now include `page` number metadata, providing finer-grained structural context.
- 🗑️ **Automated Figure Cleanup:** When documents are removed, their associated figures in the data lake are now automatically deleted, maintaining data hygiene and optimizing storage.

### Changed
- 🔄 **Redesigned Document Processing Workflow:** The entire document ingestion workflow has been overhauled to seamlessly integrate figure extraction, description generation, and table reformatting.
- 📝 **Advanced Markdown Parsing:** The Markdown structural node parser now robustly handles page breaks and intelligently converts HTML tables and figures into distinct, Markdown-formatted nodes.
- 🌐 **Improved Multilingual Summarization:** Summarization prompts now explicitly guide the LLM to generate summaries in the same language as the input text, enhancing consistency for diverse content.
- 🚀 **Upgraded Language Model (Playground):** The default language model in the playground environment has been updated to `gpt-4o`, offering enhanced performance and capabilities.

### Refactor
- 🧹 **Consolidated Azure Resource Naming:** Azure Infrastructure-as-Code (IaC) configurations have been refactored to centralize resource naming suffixes, improving consistency and simplifying future deployments.

---



## [v0.175.0] - 2025-06-02 - Improved API Robustness and Infrastructure Alignment

### Changed
- 🔄 **Updated Core Docker Images**: Switched the `pgvector` and `Open WebUI` Docker images to use organization-specific registry paths and stable version tags, enhancing consistency and control over the development and deployment environments.

### Refactor
- 🧹 **Streamlined OpenAI API Call Handling**: Refactored the internal mechanism for processing OpenAI API requests (Chat Completion, Image Generation, Text-to-Speech) to intelligently filter and pass only valid arguments to the OpenAI SDK. This improvement enhances the API's robustness, prevents errors from unrecognized parameters, and simplifies future maintenance.

---



## [v0.174.0] - 2025-05-30 - Azure IaC Constant Centralization

### Refactor
- 🧹 **Centralized Azure IaC Constants**: Moved the `DEFAULT_DOCSTORE_SUFFIX` constant to a new dedicated module, enhancing code organization and reusability for Azure infrastructure definitions.

---



## [v0.173.0] - 2025-05-30 - Expanded Azure IaC with Cosmos DB Integration

### Added
- ✨ **Introduced Cosmos DB Document Store Management**: Added a new module (`CosmosDocstore`) within the Azure Infrastructure as Code (IaC) to define and manage Cosmos DB instances as a document store option.
- 🦾 **Automated Cosmos DB Role Assignment**: Enhanced user-assigned identity management in Azure IaC to automatically assign necessary contributor and account roles for Cosmos DB document stores, streamlining access control for new document storage resources.

---



## [v0.172.0] - 2025-05-28 - Empowering AI Evaluation and Streamlining API Endpoints

### Added
- ✨ **New LLM Evaluation Feature**: Introduced a comprehensive evaluation system for AI assistants, allowing users to create datasets, define experiments, and evaluate agent responses based on correctness, completeness, and conciseness using an LLM-based judge. This includes:
    -   A dedicated **Evaluation API Controller** and **Service** for managing evaluation datasets and experiments.
    -   New **Pydantic models (DTOs)** for structured evaluation data, datasets, and experiment definitions.
    -   An **`PhoenixExperimentEvaluator`** to orchestrate agent interactions, LLM-based judging, and result logging to Arize Phoenix.
    -   New **UI pages and components** for creating, viewing, and managing evaluation datasets and experiments.
    -   Localized **LLM judge prompts** in English, German, French, and Italian for consistent, automated evaluations.
    -   Integration of `arize-phoenix` library for robust experiment tracking and visualization.
- 📈 **Enhanced Infrastructure Stability**: Added `healthcheck` configurations to core Docker Compose services (Phoenix, Redis, Mongo, Llama.cpp, HF-TEI, Attu) for improved service monitoring and reliability.
- 💾 **Persistent Data Volumes for Databases**: Introduced named Docker volumes for Redis and MongoDB in `docker-compose.yml` files, ensuring data persistence across container restarts.

### Changed
- 🔄 **API Route Pluralization**: Renamed several core API endpoints and their corresponding UI routes from singular to plural (e.g., `/agent` to `/agents`, `/event` to `/events`, `/thread` to `/threads`, `/user` to `/users`, `/suite` to `/suites`) for improved consistency and RESTfulness.
- 📄 **CI/CD Permissions Update**: Updated GitHub Actions workflows to use more granular `PAT_GITHUB_READ_PACKAGES` for package access, enhancing security.
- 🌐 **Improved Internationalization (i18n) Logic**: Refined the `LocaleHandler` to more flexibly load translation objects, improving i18n resource management.
- 🎨 **UI Structural Enhancements**: Modified the `Structural/Screen` component to support more flexible content layouts, improving the overall adaptability of admin pages.
- 🖼️ **Updated Core Docker Images**: Upgraded various Docker images for backend services (Phoenix, NATS, Redis, Mongo, Llama.cpp, HF-TEI, Open-WebUI, Etcd, Minio, Milvus, Attu) to newer versions, improving performance and stability.

### Refactor
- 🧹 **Centralized Phoenix Configuration**: Moved `PhoenixConfig` from `aihub_agent` to `aihub_lib` to centralize infrastructure configurations within the shared library.
- ⚙️ **Updated LlamaIndex Schema Usage**: Switched from `Document` to `TextNode` in vector processing tests to align with newer LlamaIndex API standards, improving internal code consistency.

---



## [v0.171.0] - 2025-05-27 - Strategic Infrastructure Refinement and Performance Upgrades

### Refactor
- 🧹 **Infrastructure Re-architecture**: Decoupled and delegated the creation and management of service-specific network subnets and Network Security Groups (NSGs) from the central Network module to their respective service modules (e.g., Dagster, Nats, Phoenix, Stores, WebUI). This enhances modularity and clarifies resource ownership within the Azure infrastructure code.
- 🔄 **Pulumi Azure SDK Upgrade**: Updated various Pulumi Azure Native resource definitions to utilize newer, more specific modules (e.g., `cosmosdb` replacing `documentdb`, `privatedns` for private DNS zones) for improved consistency and future compatibility.
- 🔗 **Enhanced Resource Dependency Management**: Implemented more robust handling of resource dependencies within Pulumi, particularly for storage accounts and private endpoints, to ensure proper sequencing and reliable deployment.
- ⚙️ **Centralized NSG Creation**: Moved Network Security Group creation logic to the `NetworkProvider`, promoting reusability and a unified approach to network security rule definition.

### Added
- ✨ **New Azure Role Definition**: Introduced the `STORAGE_BLOB_DATA_CONTRIBUTOR` role in Azure constants, enabling fine-grained access control for blob storage.
- 🔑 **Dagster Datalake Permissions**: Automatically assigns the `STORAGE_BLOB_DATA_CONTRIBUTOR` role to the Dagster managed identity, providing necessary permissions for blob storage interactions within the data pipeline.
- 🌐 **Dedicated Subnet CIDR Ranges**: Defined specific CIDR blocks for various service subnets (Dagster, Nats, Phoenix, Stores, WebUI), optimizing network segmentation and planning.

### Changed
- 🚀 **Dagster Webserver Performance Boost**: Increased CPU allocation from 0.5 to 1.5 cores and memory from 1Gi to 3Gi for the Dagster webserver, improving its responsiveness and stability under load.
- 📈 **PostgreSQL Database Scaling**: Upgraded the PostgreSQL database SKU from `Standard_B1ms` to `Standard_B2s` and doubled storage from 32GB to 64GB, providing enhanced performance and capacity for data persistence.

---



## [v0.170.0] - 2025-05-26 - Docker Image Mirroring Utility

### Added
- 🚀 **New Docker Image Mirroring Utility:** Introduced a new `mirror-image` command within the `aihub_iac` Makefile, enabling simplified mirroring of Docker images from a source to a target registry. This utility automates the login, pull, tag, and push operations, streamlining image management workflows.

---



## [v0.169.0] - 2025-05-26 - Enhanced DataLake File Metadata Robustness

### Changed
- ⚙️ **Improved `DataLakeFile` Owner Resolution:** Enhanced the logic for determining the owner of a `DataLakeFile` by introducing a more robust fallback mechanism. This now attempts to read the owner from `USER` or `USERNAME` environment variables before defaulting to "pipeline-user", improving compatibility across various execution environments.

---



## [v0.168.0] - 2025-05-24 - Infrastructure Stability Enhancements

### Changed
- ⚙️ **NATS IP Address Assignment**: Configured the NATS server to use a static IP address (`10.0.1.4`) within Azure Container Instances, enhancing network stability and predictability for service communication.

---



## [v0.167.0] - 2025-05-23 - Empowering Knowledge Discovery with Enhanced RAG and UI, Featuring a New Knowledge Base

### Added
- ✨ **New Knowledge Base Feature**: Introduced a comprehensive knowledge management system allowing users to browse ingested documents, their chunks, and summaries through a dedicated API and intuitive UI.
- 🆕 **Structured Data Models for RAG**: Implemented new `IngestedBase`, `IngestedDocument`, and `IngestedNode` data models to provide a standardized and richer representation of documents and their constituent nodes for RAG pipelines and UI display.
- 🚀 **Enhanced Pipeline Operations**: Added `ensure_refdoc_default_metadata` and `ensure_node_default_metadata` pipeline steps to automatically enrich document and node metadata, ensuring compatibility with new structured data models.
- 🔌 **Milvus Vector Store Integration for Pipelines**: Introduced a dedicated Milvus vector store resource, expanding storage options for ingested data in the pipeline.
- 🖥️ **Milvus GUI (`attu`) Integration**: Included `attu`, a graphical user interface for Milvus, in the Docker Compose setup for easier vector store management and inspection.
- 🔗 **Direct Source and Tracing Views from Open WebUI**: Enabled new actions in Open WebUI to directly open detailed "Sources" and "Tracing" views within the AI-Hub frontend, streamlining the debugging and understanding of RAG processes.
- 🔑 **Data Lake Account Key Authentication**: Added support for authenticating with Azure Data Lake using an account key, providing an alternative to implicit Azure login.
- 📄 **Refined Node Metadata**: Introduced new, more granular metadata fields for nodes, including number of pages, heading levels, and improved timestamp handling, enhancing data richness and UI presentation.
- 💬 **Markdown Rendering for Chat Messages**: Implemented Markdown rendering for chat message content in the UI, allowing for richer and more formatted responses.
- 👥 **Improved Agent Overview**: Introduced new agent cards in the UI for a more visually appealing and informative overview of available agents.
- 🤝 **Expanded Token Management Access**: The token management endpoint is now accessible to non-admin users by default, broadening API access control.

### Changed
- 🔄 **RAG Agent Configuration Update**: Updated RAG agent configurations to leverage Azure OpenAI models for embeddings and chat, alongside the introduction of `retrieve_prev_next` for more context-aware retrieval.
- 📝 **Standardized RAG Context Prompt Format**: Modified the RAG context prompt template to use `<REFERENCE_DOCUMENT>` tags instead of `<DOC_START>`, providing a more consistent and semantically clear structure.
- 🧹 **Unified RAG Data Types**: Replaced the generic `Document` type with the more specialized `IngestedNode` across Retriever and Reranker events and their processing logic, ensuring a consistent and richer data flow.
- ⚙️ **Streamlined MongoDB Connection Handling**: Refactored MongoDB connection string handling across services to use `ApiConfig().DB_NAME` for improved consistency and maintainability.
- 📊 **Enhanced Event Tracking Statistics**: Improved the event aggregation logic to provide more accurate run statistics, especially for identifying `StartEvent` origins.
- ⚡️ **Improved UI List Selections**: Agent and Thread lists in the UI now maintain their selection state for a better user experience.
- 🌐 **Internationalized Admin UI Navigation**: Updated navigation titles for Agent and Thread sections in the Admin UI to support multiple languages.

### Removed
- 🗑️ **Deprecated RAG Agent Trigger Script**: Removed an outdated trigger script for the RAG Agent, streamlining the playground environment.
- 🚫 **Legacy Document Type**: The generic `Document` type in `aihub_lib.nats.events.semantic.retriever` has been removed, as its functionality is now superseded by `IngestedNode`.
- 🧹 **Simplified Environment Variables**: Removed redundant `AZURE_SUBSCRIPTION_NAME` and `ENVIRONMENT` variables from various `.env` files for cleaner configuration.

### Refactor
- 🏗️ **Dedicated CosmosDB Document Store Configuration**: Separated CosmosDB configuration specifically for the document store, improving clarity and modularity of persistence layers.
- 🔀 **Renamed Open WebUI Action for Clarity**: The `suite_connection.py` action has been renamed to `tracing_action.py` to better reflect its purpose of opening the AI-Hub tracing view.
- ♻️ **Frontend Structural Component Restructuring**: Refactored core UI structural components, including the replacement of `SourceDocument` with `SourceNodes`, and the introduction of `StructuralSubstructure` for more flexible layouts.

### Security
- 🔒 **Restricted Health Endpoint Access**: The health endpoint (`/health`) is now configured to be accessible by administrators only, enhancing application security.

---



## [v0.166.0] - 2025-05-20 - Enhanced Data Ingestion and Pipeline Robustness

### Added
- ✨ **Introduced Dedicated Summary Node Generation:** A new `summary_nodes_factory` has been added, allowing for the independent creation and management of summary nodes within the data ingestion pipeline.
- 🚀 **Added Playground Development Command:** A new `poetry run dagster dev -m playground` command is now available for easily launching the Dagster development environment, streamlining local testing and development.

### Changed
- 🛡️ **Improved Azure Data Lake Authentication:** The `DataLakeAccess` now explicitly passes credentials to `AzureBlobFileSystem`, enhancing security and reliability of data lake connections.
- 🔍 **Ensured Document ID Filterability in Azure AI Search:** The `AzureAISearchVectorStoreFactory` now guarantees that the `DOCUMENT_ID` field is always included as a filterable metadata field, crucial for precise document management and retrieval.
- 🔄 **Refactored Node Generation Pipeline:** The core `nodes_factory` has been refactored to separate the generation of summary nodes into a dedicated asset, improving pipeline modularity and clarity.
- 🦾 **Enhanced Vector Store Node Retrieval with Retries:** The `VectorStoreIOManager` now includes a retry mechanism when fetching nodes from the vector store, significantly improving pipeline robustness against transient data availability issues.
- ⚙️ **Updated Playground Configurations:** The playground environment now integrates the new summary node generation asset and features updated default directory and store names for better organization.

---



## [v0.165.0] - 2025-05-16 - Dashboard Unveiled: A Leap in User Control & Core System Robustness

### Added
- ✨ **New User Dashboard**: Introduced a customizable dashboard for the index page, allowing users to personalize their view with various widgets displaying key metrics and events.
- 🖼️ **Dashboard Widgets**: Added new Vue components for dashboard widgets, including `Number`, `Line Chart`, and `Bar Chart`, enabling visual representation of event statistics.
- 🚀 **`AzureGraphService`**: A new, dedicated service to centralize and enhance interactions with the Microsoft Graph API, providing more robust user profile, image, and application-specific role retrieval capabilities.
- 📄 **`UserIdentity` Data Model**: Introduced a new internal `UserIdentity` dataclass to provide a clearer, more secure representation of user information, including roles and profile images, separate from public DTOs.
- 📈 **Event Timeseries Statistics**: Added new composables to calculate sum and trend information for event timeseries data, powering the new dashboard widgets.
- 🌐 **Internationalization for Dashboard**: Expanded i18n support with new translations for time ranges, chart messages, and dashboard-specific event labels.

### Changed
- 🔄 **Enhanced User Information Management**: Refactored the internal user data handling to use a dedicated `UserEntity` for persistence, ensuring user details (name, email, roles, profile image, dashboard settings) are consistently managed and updated from identity providers like Azure AD.
- 🔑 **Streamlined API Token Management**: The API token creation and management process has been simplified; tokens now link directly to a `user_oid` in the `UserEntity` instead of embedding user details or managing roles directly, aligning with the centralized user data approach.
- 🛡️ **Improved OpenWebUI Authentication**: The `OpenWebuiAuthHandler` now leverages the `AzureGraphService` for more reliable user information and application-specific role retrieval, and validates user identification headers using secure hashing for enhanced security.
- ⚡ **Flexible Multi-Authentication**: The `TokenAndOauth2Handler` now accepts a list of authentication handlers, allowing for more versatile combinations of bearer and OAuth2 authentication strategies.
- 📊 **Agent-Specific Event Timeseries**: The event timeseries API and UI components now support filtering data by specific agents, providing more granular insights for dashboard widgets.
- ⚙️ **Refined `MyUserDTO`**: The `MyUserDTO` now includes comprehensive user-specific configurations such as dashboard settings, favorite modules, and roles.
- 🛠️ **API Token Generation Script**: The `generate_api_token.py` script has been updated to reflect the new token and user management changes, fetching user details from Azure CLI and leveraging the new `TokenService`.
- 🧪 **Test Suite Alignment**: Authentication test suites have been updated to reflect the new user and token management architectures, ensuring robust testing of the revised authentication flows.
- ⏱️ **Real-time Event Invalidation**: Improved caching invalidation logic for threads on `StopEvent` and `ExceptionEvent` to ensure quicker UI updates.

### Refactor
- 🧹 **Asynchronous API Operations**: Converted numerous API endpoints and underlying service methods (`AgentService`, `OpenaiService`, `ThreadController`, `ThreadService`) to asynchronous operations, significantly improving performance and scalability.
- 🗄️ **Centralized User Persistence**: Consolidated user data storage into a new `UserEntity` in the `aihub_lib`, moving away from embedded user documents within `BearerToken` entities.

---



## [v0.164.0] - 2025-05-15 - Infrastructure Correctness and Minor Refinements

### Fixed
- 🐛 **Corrected Environment Variable Argument Type:** Updated the Azure Container Instance environment variable arguments in the IAC module to use the accurate `EnvironmentVariableArgs` type, resolving a previous type mismatch.

---



## [v0.163.0] - 2025-05-15 - Enhanced Agent Configuration and Deployment Flexibility

### Added
- 🚀 Allow passing **additional environment variables and secret references** to deployed agents through Infrastructure as Code (IaC) configurations, providing greater flexibility for custom agent setups.

### Fixed
- 🐛 Corrected **AI Search resource naming logic** in IaC to properly invoke the resource namer function, ensuring accurate resource identification.

---



## [v0.162.0] - 2025-05-14 - Streamlined Azure Bot Deployment

### Added
- ✨ **Enhanced Azure Bot Setup**: The `setup_azure_bot.py` script now automatically creates a service principal for new Azure AD application registrations, streamlining the deployment process for Azure Bots.

---



## [v0.161.0] - 2025-05-13 - Revamped User Interface and Improved Data Access

### Added
- ✨ **Enhanced Display and List Components**: Introduced dedicated components for listing agents and thread displays (`Agent/List`, `Display/List/DisplayList`), enabling a more organized and detailed overview within the administrative UI.
- 🏗️ **Core Structural Components**: Added `Structural/Column` and `Structural/Screen` components to establish a consistent, flexible, and modern multi-column layout across the application, centralizing common UI patterns.
- 📄 **Thread Details View**: A new `Thread/Details` component was added to consolidate various thread-related information into a cohesive tabbed interface.
- ⚡️ **Infinite Thread Loading Composable**: Introduced `useThreadsInfinite` to support more dynamic and performant loading of large thread lists in specific contexts.

### Changed
- 🚀 **Unified UI Layout**: Migrated administrative pages (Agent and Thread views) to a new consistent multi-column layout, replacing previous navigation components with `SelectButton` for sub-navigation, significantly enhancing user experience and clarity.
- 📊 **Thread Listing to Pagination**: Transitioned the primary thread listing from an infinite scroll mechanism to a paginated approach, providing users with better control and navigation over thread data.
- 💾 **Optimized Data Lake Access**: Implemented lazy initialization and caching for the Azure Data Lake file system client, improving performance and resource utilization for data operations.
- 🌐 **Internationalization (i18n) Structure**: Refactored and standardized i18n keys for events, statistics, and thread utilities, ensuring consistency across all supported languages.
- 🧩 **Event Display Routing**: Updated the routing structure for thread events, moving them under a new "Display" sub-route for better organization and navigation within specific thread runs.
- 🎨 **UI Refinements**: Applied various styling and structural improvements to existing components like `Event/Display/Base`, `Costs/Table`, and `Service/Selection` for a more polished appearance and improved readability.

### Refactor
- 🧹 **Internal UI Component Reorganization**: Restructured internal UI components and their usage to align with the new structural patterns, improving maintainability and component reusability.

---



## [v0.160.0] - 2025-05-13 - Refined Embedding Model Configuration

### Refactor
- ⚙️ **Refined Embedding Model Configuration**: The handling of the `dimensions` parameter for embedding LLMs has been improved. It was re-scoped from a generic embedding parameter to a specific configuration for **Azure OpenAI embedding models**. This change allows for more precise control over embedding vector dimensions (e.g., for `text-embedding-3` models) and enhances the accuracy and flexibility of embedding model configurations.

---



## [v0.159.0] - 2025-05-13 - Enhanced Core Capabilities and Embedding Model Configuration

### Added
- ✨ **Enhanced Embedding LLM Configuration:** Introduced a `dimensions` parameter for `EmbeddingLLMParameter`, allowing users to specify the desired output vector size for compatible embedding models (e.g., `text-embedding-3`).

### Changed
- ⚡️ **Improved Event Data Query Performance:** Added an index to the `event_data.created_at` field for `PersistedEventEntity`, significantly improving the performance of queries based on event creation timestamps.

---



## [v0.158.0] - 2025-05-12 - Core API Refinements

### Refactor
- 🧹 **Streamlined Event Model Creation:** Simplified the internal logic for dynamically creating Pydantic input and output models for events within the API, leading to cleaner and more robust code.

---



## [v0.157.0] - 2025-05-08 - Configuration Refinements and Infrastructure Enhancements

### Changed
- ✨ **Refined Web UI Configuration Defaults:** Explicitly set `None` as the default for optional API key fields within the Open Web UI configuration, improving clarity and robustness of configuration handling.
- 🔄 **Integrated Registry Settings in Web UI Configuration:** The Web UI configuration now incorporates `RegistrySettings`, allowing for better management and access to container registry-related parameters.

### Refactor
- 🧹 **Improved Resource Naming Consistency:** Renamed the `container_app` method to `container_app_name` within resource naming utilities for clearer and more consistent naming conventions.

---



## [v0.156.0] - 2025-05-08 - Enhanced Metrics and Performance Insights

### Added
- ✨ **Event Timeseries Statistics**: Introduced a new API endpoint and database aggregation logic to provide detailed time-based event counts for threads, agents, or specific events. This includes customizable time ranges (1h, 24h, 30d, 365d) and resolutions (1-minute, 1-hour, 1-day, 1-week buckets).
- 📈 **Event Statistics Visualizations**: Implemented new frontend components (`EventStatistics`, `EventTimeseries`) to visualize agent invocations, end events (success, human/bot/agent in the loop, errors), and delegated tasks over time using interactive charts.
- 🎨 **Time Range Selection for Metrics**: Added an interactive time range selector (1h, 24h, 30d, 365d) to the agent and thread overview pages, allowing users to dynamically view performance statistics.
- 📦 **Charting Library Integration**: Integrated `apexcharts` and `vue3-apexcharts` as new dependencies to power the new time-series charting capabilities in the web UI.

### Changed
- 🚀 **Redesigned Overview Pages**: Significantly improved the layout and information display on both the agent and thread overview pages, providing a more intuitive user experience and integrating the new event statistics charts seamlessly.
- 📊 **Updated Thread Information Display**: Replaced the `Pending` and `Status` tags with more precise `Duration` and `Costs` summaries on the thread overview, offering clearer insights into thread performance.
- 💬 **Enhanced Chat Message Styling**: Applied distinct background styling to user messages within the chat interface for improved readability and visual differentiation.
- ⚙️ **Event List Tab Scrollability**: Enabled horizontal scrollability for tabs in the event list, improving navigation and usability when dealing with numerous displays.
- 🔄 **Frontend Query Terminology**: Updated internal query composables to use `isPending` instead of `isLoading`, aligning with more precise state representation for asynchronous operations.
- 📄 **API Documentation Clarity**: Clarified the descriptions for the `getAgents` and `discoverAgents` API endpoints to differentiate between retrieving all agents versus only online (discoverable) agents.

### Fixed
- 🐛 **Consistent Timezone Handling**: Corrected timezone handling for `created_at`, `started_at`, and `ended_at` timestamps across various API DTOs and database persistence layers, ensuring accurate and consistent time representation globally.
- 🛠️ **Run Statistics Accuracy**: Implemented a crucial deduplication step within the MongoDB aggregation pipeline for run statistics, resolving issues of overcounting events and leading to more precise metric calculations.
- 📊 **Complete Timeseries Data**: Enhanced the event timeseries aggregation to automatically "fill in" periods with zero events, ensuring that charts provide a continuous and comprehensive visualization of data, even during inactive intervals.
- 🖼️ **Chat Panel Positioning**: Adjusted the positioning of the thread closing button in the chat view for improved responsiveness and a more stable user experience.

### Refactor
- 🧹 **Metric Renaming**: Renamed the `latency` metric to `duration` across the API, database persistence, and frontend DTOs for improved clarity and more accurate representation of the measured time.
- 🔄 **Centralized Thread User Check**: Centralized the logic for verifying if a user is a member of a thread into a new, reusable static method `ThreadService.user_in_thread`, enhancing code maintainability.
- ⚡️ **Optimized Timestamp Conversion**: Simplified the conversion of nanosecond timestamps to milliseconds using `1e9` for better readability and consistency in calculations.
- 🔗 **Frontend Query Key Consistency**: Refined frontend query keys for thread and event data for improved consistency and more efficient cache management.
- 💨 **Dynamic Cache Invalidation**: Implemented dynamic cache invalidation for thread and agent queries upon `StopEvent` or `ExceptionEvent` occurrences, ensuring that data displayed to users is always up-to-date.
- 📂 **IAC Code Cleanup**: Performed minor cleanup including import reordering and formatting adjustments within the Infrastructure as Code (IAC) modules.

---



## [v0.155.0] - 2025-05-08 - Large Audio File Transcription Support and Infrastructure Improvements

### Added
- ✨ **Intelligent Audio Chunking Service**: Introduced a new core service (`AudioChunkingService`) to intelligently split large audio files into smaller segments. This service identifies silence points and adds overlaps, ensuring seamless and accurate transcription by respecting API size limitations (e.g., OpenAI's 25MB limit).
- 📦 **FFmpeg and `pydub` Support**: Integrated `pydub` as a new dependency and established `ffmpeg` as a required tool for robust audio processing. This includes adding automatic `ffmpeg` installation steps to the `aihub_api` test workflows and local development environment.
- 🧪 **Comprehensive Audio Processing Tests**: Added a dedicated test suite for the new audio chunking logic and an integration test for the enhanced Speech-to-Text service, ensuring reliability and correctness of large audio file handling.
- 💾 **MongoDB Data Persistence**: Configured a Docker volume for the `mongodb` service in `docker-compose.yml`, guaranteeing that database data persists across container restarts.

### Changed
- 🚀 **Enhanced Speech-to-Text (STT) Service**: The `OpenaiService`'s Speech-to-Text endpoint (`/openai/audio/transcriptions`) now automatically utilizes the new intelligent audio chunking service. This enables the transcription of audio files that previously exceeded API size limits, significantly improving the service's capability.
- ⚠️ **Improved Large File STT Handling**: When transcribing large audio files that require chunking, the STT service will now return merged plain text for `srt` and `vtt` response formats. Full support for `srt` and `vtt` formats with detailed timestamps across merged chunks will be integrated in future releases.

---



## [v0.154.0] - 2025-05-08 - Core Service Alignment and IAC Integration

### Changed
- 🔄 **Integrated `aihub_iac` into Release Workflow**: The `aihub_iac` component is now included in the automated GitHub Actions tagging process, ensuring its versioning aligns with other core services.
- ⬆️ **Synchronized Versioning Across Microservices**: All core `aihub` microservices (`agent`, `api`, `bot`, `pipeline`, `lib`, and `iac`) have been updated to `v0.154.0`, ensuring consistent dependencies across the platform.

---



## [v0.153.0] - 2025-05-08 - Refining Internal Development Workflows

### Changed
- ⚙️ **Enhanced Semantic PR Checks**: Expanded the scopes for semantic pull request validation to include `iac` (Infrastructure as Code) and `ci-cd` related changes, promoting more consistent and descriptive commit messages for these domains.

---



## [v0.152.0] - 2025-05-08 - Paving the Way for Scalable Deployments: Azure IaC and Core Service Deployments

### Added
- 🚀 **New `aihub_iac` Module:** Introduced a dedicated Infrastructure as Code (IaC) module using Pulumi for defining and managing Azure cloud resources. This enables reproducible and scalable deployments of the AIHub platform.
- 🏗️ **Modular IaC Architecture:** Implemented a component-based design, provider pattern, and layered configuration system for robust, maintainable, and extensible infrastructure definitions.
- 🌐 **Comprehensive Network Setup:** Automated the creation of an Azure Virtual Network (VNet) with multiple dedicated subnets (for agents, APIs, databases, container apps) and configured Network Security Groups (NSGs) for enhanced security.
- 💾 **Managed Data Store Provisioning:** Added support for provisioning Azure Cognitive Search (vector database), Cosmos DB (NoSQL document and API stores), and PostgreSQL (relational database) with the **PG-vector** extension, all with private endpoint connectivity.
- 📧 **Integrated Messaging and Caching:** Included the automated deployment of **NATS** (messaging) and **Redis** (caching) services within a secure container group, ensuring efficient inter-service communication.
- 🔄 **Dagster Orchestration Deployment:** Enabled deployment of **Dagster** webserver and daemon as Azure Container Apps, facilitating robust data orchestration and workflow management.
- 💻 **AIHub Microservice Deployments:** Introduced Pulumi-based deployments for AIHub **Agents** (Azure Container Instances), **API** (Azure App Service), **Bot** (Azure App Service), and **Phoenix** (Azure App Service).
- 🎨 **OpenWebUI Deployment:** Added the capability to deploy **OpenWebUI** as an Azure Container App, providing a powerful and customizable web interface for interacting with the AIHub platform.
- 🔑 **Secure Identity Management:** Implemented User-Assigned Managed Identities and automated Azure RBAC assignments to ensure secure and granular access control for deployed services.
- 📈 **Centralized Application Logging:** Integrated Azure Log Analytics Workspace with Container App environments for centralized collection and analysis of application logs.
- ⚙️ **Automated Private Endpoint Setup:** Streamlined the creation of private endpoints for secure, private connectivity to all deployed database and search services.

### Changed
- 📄 **Updated On-Premises Technology Documentation:** Expanded the `README.md` to list additional supported on-premises technologies, including **PG-vector** for PostgreSQL and **Docker** for application environments, alongside clearer database categorizations.

---



## [v0.151.0] - 2025-05-06 - Enhanced Observability and Comprehensive UI Overhaul

### Added
- ✨ **Rich Thread Statistics**: Introduced comprehensive statistics for threads, including total events, turns, LLM costs, and status indicators for pending actions (Human-in-the-Loop, Bot-in-the-Loop, Agent-in-the-Loop) and errors.
- 📊 **Detailed Thread & Run Overview**: New API endpoints and UI components have been added to display paginated lists of threads and provide detailed overviews of individual threads, runs, and displays, offering deeper insights into agent interactions.
- 🌳 **Interactive Thread Hierarchy Visualization**: A new hierarchical view has been implemented for threads, visually representing the nested structure of displays and runs within a conversation for enhanced debugging and understanding.
- 💬 **Dedicated Thread Chat View**: A specific chat interface is now available for threads, allowing users to review conversations and interact with agents within an existing thread.
- 🤖 **Agent Persistence and Management**: Agents are now persisted in the database upon discovery, enabling the retrieval of agent information even when they are offline, complemented by new API endpoints for listing all agents and their associated threads.
- 🖼️ **Multimodal Message Handling**: Enhanced event DTOs and associated utilities to support rich multimodal content (text, images, audio) in LLM interactions, improving the expressiveness of agent conversations.
- 🏷️ **Localized Event Display**: Events now include internationalized display names and descriptions, ensuring a consistent and user-friendly experience across different languages in the user interface.
- 🚀 **Real-time Event Updates via WebSockets**: Integrated WebSocket support with the Open WebUI pipeline, enabling instant, live updates of agent events in the frontend.
- 🛡️ **`GuardEvent` Type**: A new semantic event type, `GuardEvent`, has been introduced for explicit tracing and visibility of guardrail checks within workflows.
- 🧭 **Enhanced Agent Management UI**: New dedicated pages have been added for agent overview, chat, threads, and workflow visualization, improving the management experience.
- 🧩 **Frontend Composables**: Migrated core frontend data fetching logic to new composables using Pinia Colada, standardizing cached data retrieval and enhancing developer experience.

### Changed
- ♻️ **Refactored Internationalization Paths**: Standardized translation keys from `agents.` to `agent.` across the codebase for improved consistency and maintainability.
- 🧹 **Streamlined `LLMWrappingAgent` Output**: The `LLMWrappingAgent` now directly produces an `LLMStopEvent`, simplifying the agent's internal workflow and reducing intermediate steps.
- 📈 **Improved LLM Interaction Tracing**: The `RunTraceCoordinator` has been enhanced to include `project_name`, enabling better organization and identification of runs in tracing systems like Phoenix.
- ⚠️ **Refined Error Handling and Logging**: Numerous `logger.error` calls have been replaced with `logger.exception` to ensure stack traces are consistently logged, significantly improving debuggability.
- ⚡️ **Optimized Database Indexes**: New indexes have been added to `ThreadEntity`, `PersistedEventEntity`, and `BearerToken` collections for improved database query performance.
- 🗄️ **API Endpoint Restructuring**: Several OpenAI-related API endpoints (e.g., `chatCompletion`) have been renamed to reflect broader AI Hub assistant integration and clearer functionality.
- 🗺️ **Frontend Navigation Structure**: The frontend features a new navigation system with dedicated `NavigationLeft` and `NavigationTop` components, providing a more intuitive user experience.

### Fixed
- 🌐 **WebSocket Locale Handling**: Resolved an issue where WebSocket connections were not correctly propagating locale information, ensuring consistent internationalization for real-time events.
- 🐞 **Thread History Reconstruction**: Implemented robust logic to correctly reconstruct chat history for agents based on thread events when requested, ensuring accurate context for ongoing conversations.
- 🐛 **Multimodal Message Serialization**: Corrected the serialization of `AnyUrl` within `UserMessageEvent` messages, preventing data loss or corruption for multimodal content.
- 🚦 **Event Deserialization Robustness**: Improved the event deserialization logic to handle complex inheritance scenarios, such as `ControlAndDisplayEvent`, ensuring unknown event types are correctly mapped to their closest known parent classes.
- ⚠️ **Display ID Defaulting**: Ensured that `display_id` is always set to a unique value when not explicitly provided in `ExternalEvent`, preventing potential display inconsistencies.
- 🌐 **Internationalization Middleware**: Corrected the `I18nMiddleware` for WebSocket requests to accurately extract locale information from various headers and parameters.
- 🔄 **Human-in-the-Loop Status**: Human-in-the-Loop requests now correctly indicate their pending status in the UI, providing clearer visual cues for user interaction requirements.

### Removed
- 🗑️ **Legacy Frontend Stores**: Deprecated and removed older Pinia stores (`useAgentsStore`, `useEventsStore`, `useThreadStore`, `useUserStore`) in favor of a new, unified composable-based data management approach using Pinia Colada.
- 🧹 **Outdated Playground Components**: Cleaned up and removed several legacy playground components and examples that were no longer actively maintained or relevant after major refactoring efforts.
- 🧮 **Google Gemini Playground Integration**: Removed direct integration and configuration for Google Gemini models from the playground environment.

---



## [v0.150.0] - 2025-05-04 - Expanding LLM Horizons: Gemini, Smarter Summaries, and Core Refinements

### Added
- ✨ **Introduced Google Gemini LLM Support**: New configurations (`GeminiLLMConfig`, `GeminiLLMParameter`) and infrastructure (`GeminiConfig`) enable seamless integration and utilization of Google Gemini models.
- 📄 **Implemented Recursive Document Summarization**: Added a new recursive summarization parser and pipeline operations to generate hierarchical summaries for document nodes, significantly improving context and retrieval capabilities in RAG workflows.
- 🚀 **New Dagster Playground Environment**: A new playground setup for Dagster pipelines has been added, showcasing the updated document processing and summarization capabilities.
- 🌍 **Internationalized Summarizer Prompts**: Included new translations for the summarizer prompt in German, English, French, and Italian, ensuring broader language support.

### Changed
- 🔒 **Refined Agent Description Guard Prompt**: Enhanced the prompt for the `AgentDescriptionGuard` to explicitly enforce a strict JSON output format, ensuring more reliable and predictable responses.
- ⚡️ **Adjusted Recursive Summarization Threshold**: The minimum character length required for text summarization has been reduced from 500 to 250, allowing for more granular and frequent summary generation.
- ⏱️ **Increased RAG Agent Test Timeout**: The `delay_before_stop` in the RAG agent's test runner was extended to 40 seconds, providing more resilience against potential timeouts during complex test scenarios.

### Refactor
- 🔄 **Renamed `SelfHostedLLMConfig` to `OpenaiLikeLLMConfig`**: Standardized the naming convention for self-hosted or local LLM configurations to `OpenaiLikeLLMConfig` and `OpenaiLikeLLMParameter` across the entire codebase (agents, API, bot, library, pipeline) to better reflect their OpenAI-compatible API structure.
- 🧹 **Centralized Common NATS Events**: Moved `LimitChatHistoryEvent` and `StandaloneQuestionCondenserEvent` from agent-specific locations to the core library (`aihub_lib`), promoting reusability and a cleaner architecture.
- 📁 **Organized RAG Agent Structure**: Renamed the `rag` directory to `RagAgent` within `aihub_agent` for improved consistency and clarity in module organization.

---



## [v0.148.0] - 2025-04-24 - Enhanced Multi-Hop RAG Agent Logic

### Changed
- 🦾 **Improved RAGAgent Context Evaluation**: The RAGAgent now provides more granular information to the context sufficiency guard, explicitly indicating whether further "hops" (iterative retrieval attempts) are available, which refines the agent's decision-making process.
- ⚙️ **Context-Aware Guard Feedback**: The `context_sufficient_guard` now offers more dynamic and precise feedback, tailoring its output and reasoning based on the availability of additional retrieval "hops," enabling the agent to make more informed decisions when further investigation is possible or not.

---



## [v0.147.0] - 2025-04-24 - Enhanced Azure AI Search Vector Store Configuration

### Added
- ✨ **Configurable Azure AI Search Embedding Dimensions**: Introduced a new `dimensions` parameter for the Azure AI Search vector store, allowing users to explicitly define the embedding dimensionality, which is crucial for optimizing vector search and RAG operations.

---



## [v0.146.0] - 2025-04-17 - Introducing Conversation Time-to-Live and Enhanced Chat Management

### Added
- 💾 **Conversation Time-to-Live (TTL) Management:** Introduced automatic cleanup of inactive conversations in the database based on a configurable duration, improving data management and efficiency.
- 💬 **Intelligent Conversation Tracking:** Implemented a new `ConversationTracker` to accurately distinguish between conversations that expire due to inactivity and those explicitly reset or deleted by users (e.g., in Microsoft Teams), ensuring precise user feedback.
- ⏱️ **Configurable Typing Indicator Timeout:** Added a `typing_timeout_seconds` parameter to chat bot routes, allowing administrators to customize how long the bot displays a "typing..." status.
- ✅ **Comprehensive TTL Test Suite:** Included new tests to validate the robustness and correctness of the conversation Time-to-Live and tracking features.

### Changed
- ⏳ **Dynamic Conversation Expiration Messaging:** The bot now explicitly informs users when a conversation has expired after prolonged inactivity, providing clear context for new interactions.
- 🔄 **Updated Conversation Activity Tracking:** Conversation `last_activity` timestamps are now consistently updated upon message receipt, ensuring accurate TTL calculations for inactive conversation removal.
- 🚀 **Typing Indicator Behavior:** The duration of the "typing..." indicator is now dynamically controlled by the new `typing_timeout_seconds` configuration.

### Refactor
- ⚙️ **Centralized Conversation TTL Configuration:** The `BotRunner` now serves as the central point for configuring conversation Time-to-Live, streamlining application setup and management.

---



## [v0.145.0] - 2025-04-16 - Asynchronous API Enhancements and Agent Streaming Example

### Added
- 🦾 **Long-Running Agent Example**: Introduced a new playground example that demonstrates how to create and manage an agent that streams continuous output to the user over an extended period.

### Changed
- 🚀 **Enhanced Model Fetching Robustness**: Improved the error handling and validation when retrieving available models from the AI Hub API, providing more reliable model discovery.

### Refactor
- 🧹 **Asynchronous API Call Modernization**: The `aihub_connection` module now leverages `httpx` for all HTTP requests, enabling fully asynchronous communication with the AI Hub API for enhanced performance and responsiveness.
- 🔄 **Streamlined Chat Completion Handling**: Refactored the internal logic for chat completions to clearly differentiate and robustly manage both streaming and non-streaming responses, ensuring a smoother user experience.
- ⚡️ **Consistent Retrieval Source Emission**: Ensured that retrieved sources (e.g., from RAG processes) are consistently and accurately emitted after the completion of both streaming and non-streaming chat responses.

---



## [v0.144.0] - 2025-04-15 - Enhanced RAG Agent with Multi-Hop Retrieval

### Added
- ✨ **Introduced Multi-Hop Retrieval for RAG Agent:** The RAG Agent can now perform multiple retrieval attempts, generating new queries based on context insufficiency to find more relevant information.
- ⚙️ **Configurable Retrieval Hops:** A new `max_hops` configuration option allows users to control the maximum number of retrieval attempts the RAG Agent will make.
- 💡 **Context-Aware Query Generation:** The `ContextSufficientGuard` now intelligently suggests new, conceptually different queries when the current context is insufficient, improving the agent's ability to self-correct and deepen its search.
- 📄 **New `ContextInsufficientWithQueryEvent`:** A new event type was introduced to facilitate the communication of new query suggestions for subsequent retrieval hops.

### Changed
- 🚀 **Increased Self-Hosted LLM Context Size:** The default context size for self-hosted LLMs in the playground test environment has been significantly increased from 512 to 8192 tokens, allowing for more comprehensive interactions.
- 🧹 **Simplified Azure OpenAI Embedding Parameters:** Removed the redundant `dimensions` parameter from `AzureOpenAIEmbeddingParameter` for cleaner configuration.
- 🔒 **Updated Azure AI Search Configuration:** The test setup for Azure AI Search vector store now includes `semantic_configuration_name` for a more robust and accurate configuration.
- 🔄 **Refined Context Guarding Logic:** The RAG Agent's `guard_context_sufficiency_step` now integrates with the multi-hop mechanism, deciding whether to stop or initiate a new retrieval hop based on context.

### Refactor
- 🧹 **Renamed Context Guard Result Model:** The data model for the context sufficiency guard result was renamed from `GuardResult` to `ContextGuardResult` for clarity.
- ⚙️ **Consolidated NATS Event Imports:** Streamlined NATS event imports in the RAG Agent for improved code readability.

---



## [v0.143.0] - 2025-04-11 - Advanced Agent Capabilities and Core Refinements

### Added
- 🦾 **New Expert Collaboration Agents:** Introduced `ExpertAskingAgent` to facilitate human-in-the-loop expert interactions via Slack, and `ExpertGroundedAgent` to ensure answers are context-grounded while offering escalation to experts when knowledge is insufficient.
- 🔗 **OpenWebUI Integration SDK:** A new Python SDK (`aihub_lib/generative_ai/open_webui/sdk`) has been added to seamlessly interact with the OpenWebUI API, enabling programmatic management of knowledge bases, including uploading and retrieving knowledge snippets.
- 🚦 **LLM-Powered Event Routing:** Implemented a new intelligent routing mechanism (`aihub_lib/generative_ai/routing`) that allows Large Language Models to dynamically determine the next step in a workflow based on contextual understanding, enhancing workflow flexibility.
- ⚡️ **Enhanced Event Display for Frontend:** `LimitChatHistoryEvent` and `StandaloneQuestionCondenserEvent` are now exposed and displayable in the user interface, providing more transparency into agent processing.

### Changed
- ⚙️ **Unified Azure OpenAI API Version:** Updated the API version for Azure OpenAI LLM and Embedding configurations to "2024-12-01-preview" across the platform, ensuring compatibility with the latest features.
- 🌐 **Improved Locale Handling:** Enhanced the system's ability to extract and propagate user locale information throughout the API and agent interactions, supporting better internationalization.
- 📄 **Direct Agent Stop from LLM Stream:** The `display_llm_stream` method now supports directly signaling an agent stop upon completion of LLM response streaming, streamlining specific workflow patterns.
- 🛠️ **Refined Docker Compose Configuration:** Adjusted several default settings in `docker-compose-webui.yml`, including enabling API keys and setting a default RAG embedding batch size.

### Refactor
- 🧹 **Streamlined Agent Directory Structure:** Agents previously organized under `basic/` and `rag/` subdirectories have been moved to the top-level `agents/` folder, simplifying import paths and improving overall organization.
- 🔄 **Centralized Common Events:** Key common events like `LimitChatHistoryEvent` and `StandaloneQuestionCondenserEvent` have been relocated to the `aihub_lib` for improved reusability and dependency management.
- 🛡️ **Consistent Error Logging:** Standardized error logging across the `Dispatcher` and NATS subscribers to use `logger.exception`, providing more detailed and consistent error traces.
- ♻️ **Simplified Base Agent Import:** The core `Agent` class can now be imported directly from `aihub_agent.agents.Agent`, removing the `abstract` subdirectory.

### Fixed
- 🐛 **Robust Event Serialization:** Resolved an issue with deserialization and serialization of events containing nested `BaseEvent` or `BaseModel` objects, improving data integrity.
- 🐞 **Test Stability for Thought Events:** Corrected a test for `ThoughtEvent` content to ensure reliable validation regardless of minor formatting variations.
- 🔑 **Accurate Human-in-the-Loop Event Naming:** Fixed an incorrect property access when retrieving `HumanInTheLoopResponseEvent` names in the `ChatService`, ensuring proper event handling.

---



## [v0.142.0] - 2025-04-10 - Enhanced Human-in-the-Loop and Azure Bot Management

### Added
- 🚀 **Dynamic Slack ID Fetching:** Introduced a new utility to automatically retrieve Slack bot and team IDs using the `auth.test` API, streamlining Bot-in-the-Loop configurations.
- 👤 **Responder Information in BITL Responses:** Added `responder` details (including user ID and name) to `BotInTheLoopResponseEvent` to track who provided human-in-the-loop responses.
- ⚡️ **Slack ID Caching:** Implemented a caching mechanism for Slack bot and team IDs to optimize API calls and improve performance for Bot-in-the-Loop requests.

### Changed
- 🦾 **Simplified Bot-in-the-Loop Agent Invocation:** Agents now only need to provide the Slack channel ID when invoking a Bot-in-the-Loop request, as bot and team IDs are automatically resolved.
- ⚙️ **Improved Azure Bot Setup Script:** Enhanced the `setup_azure_bot.py` script for greater robustness, including idempotent app registration creation and more reliable command output parsing.
- 🔄 **Updated Internal Slack ID Handling:** Modified the `BotInTheLoopHandler` to align with the simplified agent input, dynamically constructing full Slack conversation IDs.

### Refactor
- 🧹 **Refined Bot-in-the-Loop Thread Management:** Updated the internal `BotInTheLoopThread` model for clearer representation of Slack conversation and thread information (`conversation_id` and `slack_thread_ts`).

---



## [v0.141.0] - 2025-04-09 - Enhanced CI/CD Reliability and Test Stability

### Changed
- 🚀 **Improved Backend Test Action**: The GitHub Action for backend tests now features significantly more robust Docker service health checks, including explicit Docker daemon verification, detailed container status reporting, and a comprehensive timeout mechanism to prevent hung workflows.

### Fixed
- 🐛 **Milvus Test Stability**: Addressed an intermittent test failure in the Milvus vector store by introducing a small delay after data ingestion, ensuring data is fully synchronized before subsequent test operations.

---



## [v0.140.0] - 2025-04-09 - Introducing Bot-in-the-Loop for Enhanced Agent Interaction

### Added
- ✨ **Introduced Bot-in-the-Loop (BiTL) Functionality:** Enabled agents to pause workflows and request input from a bot, providing a mechanism for human-guided decisions and approvals. This includes new `BotInTheLoopRequestEvent` and `BotInTheLoopResponseEvent` types.
- 🦾 **Added `BotInTheLoopAgent` Example:** Provided a new playground agent demonstrating how to integrate and use the Bot-in-the-Loop interaction pattern within agent workflows.
- 🔌 **Integrated BiTL into Bot Services:** Developed the `BotInTheLoopBot` and `BotInTheLoopHandler` to manage and process bot-in-the-loop requests and responses, specifically supporting Slack channels.
- 🚀 **Enhanced Dispatcher and Event Distribution:** Updated the `Dispatcher` to correctly handle `BotInTheLoopRequestEvent` and the `ExternalEventDistributor` to process `BotInTheLoopResponseEvent`, ensuring seamless communication within the system.
- 📄 **Added IntelliJ Run Configuration:** Included a pre-configured run configuration for the `BotInTheLoopAgent` to streamline local development and testing.

### Refactor
- 🧹 **Restructured Bot Module Architecture:** Reorganized the `aihub_bot` package by moving core chat components, agents, and OpenAI-specific bots into a new `chat` subdirectory, improving modularity and clarity.
- 🔄 **Centralized Credential Retrieval:** Refactored `RoutesService` to centralize credential retrieval, enhancing maintainability and consistency for bot authentication.

### Fixed
- 🐛 **Ensured Database Disconnection on Bot Shutdown:** Implemented proper disconnection from Mongoengine in the bot's `lifetime_manager` to prevent potential resource leaks during application shutdown.
- ✅ **Corrected Agent Event Creation:** Adjusted the order of parameters in `AgentController` during event creation to ensure proper handling of user and input data.

---



## [v0.139.0] - 2025-04-08 - Enhanced Observability and Seamless Frontend Integration

### Added
- ✨ **Introduced Deep OpenWebUI Integration:** Seamlessly connect OpenWebUI as a powerful frontend for AI-Hub agents. This includes new Docker Compose configurations (`docker-compose-webui.yml`), OpenWebUI-specific pipelines (`webui_pipelines/aihub_connection.py`, `webui_pipelines/suite_connection.py`), and dedicated API routes to support chat interactions, event tracing, and a rich user experience within the OpenWebUI environment.
- 🚀 **New Frontend Testing Agent:** A specialized agent (`FrontendTestingAgent`) has been added to the playground to simplify frontend development and testing by demonstrating various event types and interaction patterns.
- 📄 **Comprehensive Product Pitch Documentation:** A detailed product pitch document (`0_product_pitch.md`) outlining the vision, core concepts, and architecture of the AI-Hub has been added to the documentation, accompanied by new visual assets.
- ⚡️ **WebSocket Support for API Dependencies:** New dependency injection functions (`use_locale_ws`, `use_nats_ws`, `use_external_event_distributor_ws`, `use_ws_manager_ws`, `use_ws_sender_ws`) enable WebSocket connections to directly leverage core API services.
- 🔑 **Extended Authentication Interfaces:** The abstract `AuthHandler` now includes an `authenticate_token` method, providing a standardized interface for direct token-based authentication, enhancing flexibility for WebSocket and other non-HTTP contexts.
- 💡 **Centralized `str_to_object_id` Utility:** A new utility function `str_to_object_id` provides a consistent and robust way to convert string IDs to MongoDB `ObjectId`s, including hashing for non-standard formats, centralizing ID conversion logic.
- 📈 **Azure User Info Caching:** User information retrieved from Azure AD in the `AzureUserInformationProvider` is now cached using `TTLCache`, significantly improving performance for identity lookups.
- 🖼️ **Extensive Frontend Event Display Components:** A comprehensive suite of new Vue components has been added to the frontend (`components/Event/Display/*`, `components/Event/List/EventList.vue`), enabling detailed and type-aware visualization of a wide range of agent events in a timeline view.
- 📊 **New Frontend Cost Display Component:** A dedicated `Costs/Table.vue` component has been introduced to the frontend for clearly displaying LLM-related costs.
- 💬 **New Frontend Chat Message Component:** A reusable `Chat/Message.vue` component has been added to the frontend for consistent display of chat messages.
- 📚 **New Frontend Source Document Component:** A `Chat/SourceDocument.vue` component has been introduced to the frontend for structured display of retrieved documents in RAG workflows.
- 🔗 **Dynamic Event Component Resolution:** A new `useEventComponent` composable in the frontend allows for dynamically resolving and rendering the correct Vue component for any given `WsServerEvent` type, improving maintainability and extensibility of event visualization.

### Changed
- 🔄 **Refined `BaseEvent` Structure and Naming:** The core `BaseEvent` class and its subclasses have undergone a significant internal refactoring, transitioning from `_type` to `_event_name` and `_parent_class_names` to `_parent_event_names` for clearer and more consistent event identification and hierarchy across the entire system.
- 🛠️ **Updated Agent Test Runner API:** The `AgentTestRunner` methods for querying events (`get_events_of_type`, `has_event_of_type`, `get_event_of_type`, etc.) have been updated to use `event_class` and `exact` parameters, offering more precise and type-safe control in tests.
- 💬 **Enhanced Chat Service Content Handling:** The `ChatService` now returns a structured `ChatContent` object that includes `reasoning_content` alongside the main message, enabling richer display of agent thought processes and supporting granular UI updates.
- ✅ **Improved API Event Filtering and Retrieval:** The `/event` API endpoint now supports filtering by `thread_id`, `display_id`, and `event_class` as query parameters, allowing clients to retrieve more specific event subsets for enhanced debugging and tracing.
- 🛡️ **Advanced OpenWebUI User Authentication:** The `OpenWebuiAuthHandler` now dynamically fetches user roles from Azure AD (including directory roles, app role assignments, and security groups) and includes header hash validation for increased security.
- 🩺 **More Detailed Health Check Response:** The `/health` endpoint now returns an HTTP status code as part of its response for clearer health monitoring.
- 📦 **Optimized WebSocket Event Payloads:** WebSocket server-to-user events (`WSServerEvent`) now utilize a discriminated union for the `event` payload, providing stricter type safety and enabling dynamic, rich frontend display components to directly consume event data.
- ⚙️ **Simplified External Event Deserialization:** The `ExternalEvent` deserialization logic has been streamlined to leverage the generalized `BaseEvent.deserialize_event` method, reducing complexity and improving maintainability.
- 📦 **Frontend Assets Mounting:** The main API runner now includes enhanced logic to mount the Nuxt frontend's static assets (`_nuxt`, `_fonts`) and handle client-side routing more robustly.
- 📊 **Thread and Display ID Handling in Bots:** The `BaseChatBot` and `AgentCompletionHandler` now consistently use `ObjectId` for thread and display IDs, ensuring type consistency across the system.
- 🎨 **Updated UI Theming:** The `aihub-theme.ts` has been updated with new `surface` colors for improved visual consistency across light and dark modes.
- 📝 **Documentation Examples Updated:** Code examples in `aihub_doc/5_agents_in_detail.md` have been updated to reflect the new `event.event_name` property.
- ⚙️ **SonarQube Exclusions:** The `sonar-project.properties` file has been updated to exclude generated SDK files from SonarQube analysis, improving code quality metrics.

### Refactor
- 🧹 **Consolidated Thread ID Logic:** The `to_thread_id` method has been moved from `ThreadEntity` to a new `persistence.utils` module, centralizing ID conversion logic.
- 📂 **Standardized Event Type Naming:** Internal event-related logic, parameter names, and file paths (e.g., in `extractors`, `visualizers`, `dispatcher`, and various playground agents and API modules) have been consistently updated to use "event name" or "event class" terminology, aligning with the `BaseEvent` refactor.
- 🗑️ **Removed Redundant WebSocket Modules:** Obsolete `aihub_api/sockets/receiver` and `aihub_api/sockets/events/user_to_server` modules have been removed, streamlining the WebSocket communication architecture.
- 🎨 **Unified UI Component Directory Structure:** Frontend `components/user` directory has been renamed to `components/User` for consistent casing.

---



## [v0.138.0] - 2025-04-07 - Enhanced Test Reliability and Core Dependency Updates

### Changed
- 🧪 **Improved Asynchronous Test Stability:** Enhanced test suite reliability by introducing dedicated `asyncio` event loop management for tests, specifically benefiting `RAGAgent` and `VectorPrevNextPostProcessor` component tests.
- ⬆️ **Upgraded Milvus Vector Store Integration:** Updated the `llama-index-vector-stores-milvus` library from version `0.3.0` to `0.6.0`, bringing potential performance improvements and bug fixes for vector store operations.
- 🛠️ **Streamlined Local NATS Service Setup:** Removed redundant health check configuration for the `NATS` service in `docker-compose.yml` to simplify local development environments.

---



## [v0.137.0] - 2025-04-07 - Improved Human-in-the-Loop Event Processing

### Fixed
- 🐛 **Addressed Event Deserialization Fidelity:** Enhanced the robust reconstruction of `HumanInTheLoopResponseEvent` instances, ensuring accurate preservation of event type and class hierarchy during human-in-the-loop interactions. This improves the reliability of event processing and communication flows.

---



## [v0.136.0] - 2025-04-02 - Context Guard Refinement and i18n Improvements

### Refactor
- 🚀 **Improved Context Sufficient Guard Logic**: The `context_sufficient_guard` has been refactored to utilize `llm.structured_predict` for more robust and flexible guard execution, enhancing compatibility with various Large Language Model types.
- 🌐 **Enhanced Guard Result Localization**: The `context_sufficient_guard` now dynamically generates its output model (`GuardResult`) with localized descriptions for its fields (`reasoning`, `success`) and its docstring, significantly improving internationalization support for guard results.

### Changed
- ⚙️ **Updated Internationalization Files for Guards**: Adjusted the structure of i18n translation files for guards, removing redundant prompt elements and adding new keys to support the enhanced localized output of the `context_sufficient_guard`.

### Fixed
- 🐛 **Corrected German Translation Typo**: Fixed a minor typo in the German translation of the `agent_description_guard` docstring.

---



## [v0.135.0] - 2025-04-01 - Streamlined Bot Interactions and Multi-Language Support

### Added
- 🦾 **New `BaseChatBot` Class:** Introduced a foundational `BaseChatBot` class to centralize common chatbot functionalities, including conversation updates, message processing, typing indicators, and robust error handling.
- ⚡️ **Dedicated `RoutesService`:** Implemented a new `RoutesService` to consolidate and manage route-specific utility methods, improving separation of concerns within the bot architecture.
- 🌎 **Multi-language Error Messages:** Expanded the internationalization (i18n) capabilities to include translated error messages for bots (German, English, French, Italian), enhancing the user experience across different locales.

### Refactor
- 🧹 **Unified Chatbot Architecture:** Refactored the core bot logic by introducing a `CompletionHandler` interface and migrating `AgentChatBot` and `OpenaiChatBot` (and their streaming counterparts) to inherit from the new `BaseChatBot`, simplifying their implementations and promoting code reuse.
- 🔄 **Renamed and Reorganized Modules:** Key bot service modules (e.g., `Service`, `AgentChatService`, `OpenaiChatService`) were renamed to `CompletionHandler` and their responsibilities redefined, aligning with a new strategy pattern for handling chat completions.
- 📄 **Improved Path and Adapter Management:** Relocated common path and adapter retrieval logic to the new `RoutesService`, centralizing these utilities and improving modularity.

### Changed
- 🐛 **Enhanced OpenAI Error Handling:** Improved the bot's ability to handle specific `APIStatusError` exceptions from OpenAI, providing more informative error messages to the user.
- ⚙️ **Configurable Database Connections:** Updated the CosmosDB connection to use a configurable database name (`ApiConfig().DB_NAME`), increasing flexibility for deployment environments.
- 🗄️ **Standardized MongoDB Collection Names:** Adjusted the MongoDB collection for bot paths to use `bot_paths` instead of `paths` and the database name to `aihub`, ensuring consistency across the application.
- 🌍 **Flexible Locale Handling:** Enhanced the `LocaleHandler` to allow for more flexible locale argument passing in translation lookups.

---



## [v0.134.0] - 2025-04-01 - Unified Core Release and Version Alignment

### Changed
- 🔄 **Unified Versioning**: Synchronized all microservice components (Agent, API, Bot, Pipeline) and the `aihub_lib` to version `v0.134.0`, ensuring consistent internal dependency tagging and preparing for the new release.

---



## [v0.133.0] - 2025-04-01 - Refined API Error Handling and Event Propagation

### Added
- ✨ **ExceptionEvent HTTP Status Code:** Introduced a new `http_status_code` field to the `ExceptionEvent`, enabling NATS-driven exception events to carry specific HTTP response codes for more granular error reporting.

### Changed
- 🔄 **Dynamic API Error Responses:** The API now leverages the `http_status_code` embedded within `ExceptionEvent` instances, providing more precise HTTP status codes in responses rather than a generic 500 for all exceptions.
- 📡 **Expanded Agent Service Return Types:** The `AgentService` methods are now capable of returning `ExceptionEvent` objects, ensuring that detailed error information can be propagated and utilized by API consumers.

---



## [v0.132.0] - 2025-04-01 - Robust Error Handling and Enhanced Chatbot Responsiveness

### Changed
- 🛡️ **Enhanced Chatbot Error Handling**: Implemented comprehensive exception handling across agent and OpenAI chatbots. This includes a new centralized exception handler in `Service.py` and improved propagation of errors originating from downstream services via NATS `ExceptionEvent`, leading to more resilient bot responses and clearer feedback to users.
- ⏱️ **Introduced Typing Activity Timeout**: Added a timeout mechanism for the bot's "typing" indicator. If the bot takes too long to respond, it will now inform the user, preventing indefinite typing states and improving overall user experience.

---



## [v0.131.0] - 2025-04-01 - Enhanced Document Parsing Robustness

### Fixed
- 🐛 **Improved Markdown Document Parsing:** Ensured correct interpretation of HTML entities within Markdown content by unescaping them before processing, leading to more accurate document parsing.

---



## [v0.130.0] - 2025-03-31 - Workflow Visualization, API Hub, & Core Refinements

### Added
- 📈 **Agent Workflow Visualization**: Agents now expose a detailed network graph of their internal workflow via the API, allowing developers and users to visually understand event flow, steps, inputs, and outputs in the new UI.
- 🏢 **Centralized API Service Discovery**: A new `/suite` API endpoint has been introduced, offering a comprehensive list of all available API controllers/services with their localized names, descriptions, and icons, enhancing discoverability for frontends.
- ⚙️ **Admin UI for Agents**: New administration pages have been added to the web UI, enabling users to discover, inspect, and manage agents, including viewing their detailed configurations and interactive workflow visualizations.
- 📊 **Agent Step Metadata**: Individual agent steps can now include localized names, descriptions, and icons, improving clarity and enabling richer UI representations for workflow visualization.
- 📝 **Event Form Components**: New Vue components, such as `UserMessageEvent.vue`, have been added to facilitate the creation and interaction with specific event types in the UI.
- 🛠️ **User Settings Component**: A dedicated component for user settings (e.g., logout functionality) has been added to the web UI for improved user experience.

### Changed
- 🌐 **API Internationalization**: API controllers and services now support localized names and descriptions, providing a more tailored experience across different languages and improving OpenAPI documentation.
- 🔌 **Standardized API Controllers**: All API and bot controllers have been updated with standardized metadata (`name`, `description`, `icon`) and `is_admin_only` flags, improving API documentation and role-based access control.
- 🔗 **Unified Runner Architecture**: Introduced a new `Runner` abstract base class, standardizing the application setup and lifecycle management across API and Bot services for a more consistent and maintainable codebase.
- 🎨 **Revamped UI Navigation**: The main web application layout has been significantly updated to integrate the new service discovery features, providing a more intuitive and visually appealing navigation experience.
- 🛡️ **Enhanced Authentication Robustness**: The OIDC client and authentication middleware have been improved with better error handling, silent token renewal, and detailed logging for a more stable and secure user login experience.
- 💡 **Refined User DTO**: The `UserDTO` for the authenticated user has been refined into a more specific `MyUserDTO`, providing a clearer data contract.
- 🚀 **Updated Dependency Versions**: Upgraded numerous Python and Node.js dependencies across core services for improved performance, security, and access to the latest features.
- 🎨 **Theming Update**: The default UI theme's primary color palette has been updated from `zinc` to `red` and `stone` for a refreshed look.

### Refactor
- 🧹 **Centralized Event Persistence**: The `EventPersister` module has been reorganized within the `aihub_api` for better logical grouping and maintainability.
- 📦 **Consolidated Type Definitions**: Frontend TypeScript types have been removed in favor of direct generation from the OpenAPI schema, significantly reducing manual type maintenance and ensuring API contract consistency.
- 🔄 **Component Naming Consistency**: Renamed several Vue components (e.g., `thread/Chat.vue` to `Thread/Chat.vue`) to adhere to consistent naming conventions.

### Removed
- 🗑️ **Legacy Workflow Visualizer**: The old `NetworkXVisualizer` in `aihub_agent` has been completely removed, superseded by the new, more advanced `WorkflowVisualizer`.

---



## [v0.129.0] - 2025-03-28 - New Iterative Agent Workflow Example

### Added
- ✨ **Introduced `BoundedLoopAgent`:** A new example agent showcasing the implementation of configurable iterative loops and state management within agent workflows using `RunContext`.
- 🔄 **Enhanced Workflow Patterns:** Added a comprehensive playground example for building agents that perform bounded iterative processes, complete with state tracking and conditional step execution.
- 💬 **Workflow-Specific Events:** Defined new custom events (`BeginEvent`, `ProcessEvent`, `DecisionEvent`) to facilitate structured control flow and state transitions within complex agent sequences.
- 🧪 **Agent Testing Example:** Included a dedicated test suite using `AgentTestRunner` and BDD features, demonstrating best practices for testing agents that manage state and execute iterative logic.

---



## [v0.128.0] - 2025-03-27 - Enhanced Embedding Stability

### Fixed
- 🐛 **Improved Embedding Process**: Implemented a recursive retry mechanism within the `embed_nodes` operation to gracefully handle `ValidationError` exceptions during batch embedding, ensuring more robust and reliable generation of text embeddings, especially for larger inputs.

---



## [v0.127.0] - 2025-03-25 - Improved Typing Indicator Functionality

### Changed
- ⚡️ **Enhanced Typing Indicators**: Chat bots now feature a more persistent and dynamically controlled typing indicator, ensuring users are better informed when a response is being generated. This includes an updated internal mechanism to continuously send typing updates until a full response is ready.

---



## [v0.126.0] - 2025-03-24 - Enhanced LLM Control with Configurable Timeouts

### Added
- ✨ **Introduced LLM Request Timeout:** Added a new configurable `timeout` parameter to `ChatLLMConfig` (defaulting to 30 seconds) to control the maximum duration for LLM model requests. This enhancement provides better control over long-running or unresponsive model calls for both Azure OpenAI and self-hosted LLM configurations.

---



## [v0.125.0] - 2025-03-21 - WebUI Agent Integration and API Enhancements

### Added
- 🦾 **Introduced WebUI Agent:** A new agent that allows seamless integration with OpenAI-compatible APIs, such as Open WebUI, enabling more flexible model deployment.
- 🧪 **WebUI Agent Playground:** Added a dedicated playground environment for easy testing and development of the new WebUI Agent.
- 📦 **OpenAI Library Dependency:** Included the `openai` library as a core dependency to support expanded OpenAI API interactions.

### Changed
- 🖼️ **Default DALL-E 3 Image Generation:** Updated the default model for image generation to DALL-E 3, leveraging the latest capabilities.
- 💬 **Flexible Chat ID Handling:** The `chat_id` for chat completions is now supported within the `metadata` field of the request, aligning with broader API standards.
- 📈 **Enhanced Performance Output:** Added an "Error" column to performance test results, providing more detailed feedback on test failures.

### Fixed
- 🚫 **Prevented Recursive Agent Listing:** Implemented logic to prevent WebUI agents from recursively listing themselves as available models, avoiding potential loops in model discovery.
- ⚙️ **Robust Function Argument Processing:** Improved the handling of function call arguments by explicitly filtering out `None` values for cleaner requests.
- 🐛 **Chat Service Model Name Resolution:** Corrected an internal model name assignment in the chat service for improved robustness.

### Refactor
- 📄 **Type Hint Refinement:** Updated type hints for `ChatLLMConfig` to accurately reflect its asynchronous context manager behavior.

---



## [v0.124.0] - 2025-03-21 - Service Refinements and Persistence Alignment

### Changed
- ⚙️ **Refined External Event Distribution Logic**: Removed an overly strict validation check to improve robustness and flexibility in how agents handle external events.

### Refactor
- 🧹 **Consolidated Bot Database Naming**: Standardized the MongoDB database connection name from `aihub_bot` to `aihub` and updated collection names (e.g., `conversations` to `bot_conversations`, `paths` to `bot_paths`) within the bot service for improved consistency and clarity.
- 🔄 **Streamlined Chat Message Content Access**: Updated internal chat service logic to access message content directly via attributes (`.content`) instead of dictionary keys, enhancing type safety and code readability.

---



## [v0.123.0] - 2025-03-21 - Advanced Document Processing: Custom Metadata and Richer Node Details

### Added
- ✨ **Introduced `MetadataExtractor` Interface:** A new abstract class `MetadataExtractor` is available, enabling custom logic for extracting additional metadata from document splits during parsing.
- 🔗 **Enhanced RAG Node Metadata:** Added new `REFERENCE_NAME` and `REFERENCE_URL` fields to RAG node metadata, allowing for richer contextual information and source attribution.
- ⚙️ **Configurable Node Relationships:** The `MarkdownStructuralNodeParser` now supports an `include_prev_next_rel` option to optionally generate previous/next node relationships, offering more control over the generated graph structure.

### Changed
- 📈 **Extended Metadata Table Utility:** The `nodes_metadata_table` utility now includes the newly introduced `REFERENCE_NAME` and `REFERENCE_URL` fields, providing more comprehensive insights into node metadata.

### Refactor
- 🧹 **Improved Document Split Management:** The `Split` dataclass was moved to its own dedicated file (`Split.py`) for better modularity and clearer code organization.
- ⬆️ **Pydantic Model Enhancements:** Updated `MarkdownStructuralNodeParser` to leverage modern Pydantic features (e.g., `model_validator`) for more robust and cleaner initialization logic.

---



## [v0.122.0] - 2025-03-21 - Enhanced Error Handling and API Robustness

### Changed
- ⚡️ **Improved Agent Error Reporting in API:** The API now gracefully converts `ExceptionEvent`s received from agent interactions into HTTP 500 responses, providing clearer error messages and better visibility for agent failures.
- 🐞 **Robust Exception Handling in Chat Service:** The `ChatService` now actively processes and responds to `ExceptionEvent`s, ensuring that chat sessions terminate gracefully and report errors when underlying components (like agents or LLMs) encounter exceptions.

---



## [v0.121.0] - 2025-03-20 - Robust Event Ordering with JetStream Integration

### Added
- ✨ **JetStream Sequence Number Tracking**: Event objects now capture and expose their NATS JetStream sequence number, providing a robust, ordered identifier for each event as it is received and stored.

### Changed
- ⚡️ **Enhanced Event Filtering Precision**: The dispatcher and internal event stores now leverage JetStream sequence numbers for all event filtering and retrieval. This ensures more accurate and reliable processing, as events are ordered and selected based on their exact sequence in the stream rather than potentially inconsistent timestamps.

---



## [v0.120.0] - 2025-03-20 - Core Language Detection Capability Added

### Added
- ✨ **Introduced LLM-based Language Detection:** A new utility in `aihub_lib` that accurately identifies the language of user queries (German, English, French, Italian, or other) using Large Language Models, enabling more intelligent multilingual processing.

---



## [v0.119.0] - 2025-03-19 - Enhanced API Routing and Event Naming

### Changed
- ⚡️ **Improved Dynamic Event Naming for Agents:** Event names generated for agent interactions via the API now incorporate a unique postfix based on the route, enhancing clarity and specificity in event identification and routing.

---



## [v0.118.0] - 2025-03-19 - Enhanced Event Serialization and Core Updates

### Added
- ✨ **Introduced `model_dump_json` for `BaseEvent`**: Events can now be directly serialized to a JSON string using the new `model_dump_json` method, ensuring all event data, including any unknown fields, is comprehensively preserved.

### Refactor
- 🧹 **Improved Code Clarity with `@override`**: The `@override` decorator has been added to key methods within `BaseEvent` for better readability and to explicitly mark method overrides, enhancing code maintainability.

---



## [v0.117.0] - 2025-03-19 - Enhanced Workflow Flexibility with Custom Events

### Added
- ✨ **Introduced support for Custom Start and Stop Events:** Agents can now be configured to use custom event types as their workflow's initial trigger and final output, providing greater flexibility in designing and integrating workflows.
- 📄 **New Playground Example for Custom Start/Stop Events:** A comprehensive example (`CustomStartStopEventAgent`) has been added to showcase the implementation and usage of custom start and stop events within an agent workflow.

---



## [v0.116.0] - 2025-03-19 - Improved Agent Chat and Event Subscription

### Added
- ✨ **Enhanced Chat Event Subscription:** Introduced a new option to subscribe to all events within a chat thread, providing a more comprehensive view of multi-agent interactions.

### Changed
- 🔄 **Streaming Interaction Default:** Streaming chat interactions now default to subscribing to all thread events, offering a complete real-time feed of activity.
- 📄 **Dynamic Model Naming for JSON Interactions:** The model name reported for JSON-based agent interactions now dynamically reflects the specific agent (`agent_class/agent_id`) that processed the request, improving traceability.
- ⚙️ **Improved Event Deserialization:** Enhanced the deserialization process for Human-in-the-Loop request events, making it more robust.

### Fixed
- 🐛 **Robust Multi-Agent Stop Handling:** Resolved an issue where chat streams and JSON interactions could prematurely stop if a non-primary agent sent a stop event in a multi-agent thread. Interactions now correctly terminate only when the primary agent signals completion.

### Refactor
- 🧹 **NATS Event Import Optimization:** Streamlined and cleaned up NATS event imports across various services for better code organization.

---



## [v0.115.0] - 2025-03-19 - Unified External Event Processing for Enhanced Flexibility

### Refactor
- 🔄 **Unified Event Distribution Mechanism:** Reworked the `WebSocketReceiver` into a more generic `ExternalEventDistributor`. This fundamental change allows the system to process and distribute user input from various external sources, including WebSockets, bot frameworks, and APIs, via NATS, significantly enhancing architectural flexibility and future integration capabilities.
- 🧹 **Decoupled User Event Types:** Renamed the `WSUserEvent` to `ExternalEvent` and relocated it to a more central `nats.distributor.events` package. This change reflects its expanded role in representing user interactions from any external system, moving beyond a WebSocket-specific context.
- ⚙️ **Streamlined Dependency Injection:** Updated dependency injection points across various `aihub_api` and `aihub_bot` services to consistently utilize the new `ExternalEventDistributor`, ensuring a centralized and more robust event handling process throughout the applications.
- 📁 **Reorganized Event Modules:** Restructured file paths and module organization related to event handling and distribution within `aihub_lib` to align with the new, more generalized architecture.

### Changed
- ⚡️ **Improved Bot Framework Integration:** Modified `aihub_bot` components to seamlessly integrate with the new `ExternalEventDistributor`, simplifying the flow of messages from bot frameworks into the core system's event processing pipeline.
- 🚀 **Updated API Event Handling:** Adjusted `aihub_api` event and agent controllers to leverage the `ExternalEventDistributor`, providing a more unified and robust approach to processing incoming user events from the API.

---



## [v0.114.0] - 2025-03-19 - Smarter Events: Robust Deserialization & Refined API Interactions

### Refactor
- 🧹 **Unified Event Type Checks**: Replaced direct `isinstance()` checks with dedicated `is_*` properties (e.g., `event.is_start_event`, `event.is_control_event`) on `BaseEvent`, making event type determination more consistent and robust across dispatchers, tracers, publishers, and other core components.
- 🔄 **Advanced Event Deserialization**: Reworked `BaseEvent` deserialization to intelligently handle unknown event types, ensuring that events can be consumed even if their exact class is not registered in the current process by falling back to the most specific known parent class and preserving original data.
- ⚙️ **Flexible Event Schema**: Updated `BaseEvent` Pydantic configuration to allow extra fields during deserialization, enhancing compatibility with future or unknown event structures.
- 🌳 **Event Utility Consolidation**: Moved core event utility functions like `get_parent_classes_until_base` and introduced `get_inheritance_depth` to a dedicated `utils.py` module for better organization and reusability.

### Added
- ✨ **API Output Model Generation**: Introduced `create_output_model` utility to dynamically generate Pydantic models for API responses, enabling fine-grained control over exposed event data and excluding internal metadata.
- 🧪 **Comprehensive Event Test Suite**: Added extensive unit tests for the new event deserialization logic and `is_*` properties, ensuring reliability and robustness of event handling.
- 📝 **Enhanced Playground Logging**: Enabled logging for minimal workflow playground triggers to facilitate easier debugging and observation of event flows.

### Changed
- 📄 **Streamlined API Event Responses**: The `send_event_to_agent` API endpoint now returns a simplified and cleaner event model, exposing only relevant data for external consumption.
- ⚡️ **Standardized Workflow Triggers**: Adjusted optional workflow playground examples to use the generic `StartEvent` for initiation, promoting consistency across test setups.

### Fixed
- 🐛 **Resilient Event Handling**: Improved the system's ability to gracefully process events from external services or agents where the exact event type might not be locally registered, ensuring workflows continue without interruption and preventing crashes from unknown event structures.

---



## [v0.113.0] - 2025-03-17 - Improved Event Persistence and API Development Workflow

### Added
- 🧪 **Simplified Local Development Authentication**: A new `NoAuthHandler` has been introduced for the `aihub_api` development playground, allowing for easier local testing by bypassing authentication requirements.
- 🌳 **Enhanced Event Inheritance Tracking**: Events now record their full class inheritance hierarchy, enabling more robust and flexible querying of event types. This is stored in a new `event_parents` field on persisted events.

### Changed
- 🔍 **Improved Event Querying**: Event retrieval methods in `PersistedEventEntity` have been updated to utilize the new event inheritance tracking, allowing for more accurate and powerful filtering of events based on their class hierarchy rather than just exact names.

### Refactor
- 🧹 **Centralized Event Persistence Logic**: The event persistence logic has been moved from `EventPersister` directly into the `PersistedEventEntity` as a class method, improving encapsulation and maintainability.

---



## [v0.112.0] - 2025-03-17 - Enhanced Chat Capabilities and Human-in-the-Loop Integration

### Added
- 🖼️ **Extended Image Generation Options:** Added support for additional parameters (e.g., `n`, `quality`, `response_format`, `size`, `style`) in image generation requests, offering more control over generated images.
- 🔗 **Consistent Thread ID Generation:** Introduced a new utility to deterministically generate thread IDs from external context identifiers (e.g., conversation IDs from bots), improving chat history continuity and persistence.
- 📄 **Human-in-the-Loop History Retrieval:** Added new methods to retrieve specific Human-in-the-Loop request and response events from thread history.

### Changed
- ✨ **Enhanced Human-in-the-Loop (HITL) Integration:** Significantly improved the handling of HITL requests and responses across chat services, including proper termination of agent responses, comprehensive history persistence, and the inclusion of HITL questions in final streaming outputs.
- 💬 **Expanded OpenAI Chat Completion Parameters:** Updated the chat completion request Data Transfer Object (DTO) to support a wider range of OpenAI API parameters, providing greater flexibility for model interactions.
- 👤 **Automatic User Association for Chat:** Ensured that chat completion requests automatically associate with the authenticated user, enhancing traceability and security.
- 🚀 **Improved Chat Thread Management:** Refined the creation and retrieval of chat threads to support pre-existing thread IDs and enforce user access controls, ensuring chat history is correctly managed and secured.
- 🔄 **Standardized Message History Ordering:** Updated message history queries to consistently order events chronologically, providing a more accurate and readable chat log.
- 💡 **Refined Chat Response Content Building:** Modified how chat response content is assembled, especially for JSON and streaming, to correctly include information from `StopEvent` and `HumanInTheLoopRequestEvent` types.

---



## [v0.111.0] - 2025-03-17 - Optimized Event Delivery for Real-time Updates

### Changed
- ⚡️ **Enhanced WebSocket Event Handling:** The internal `WebSocketReceiver` has been refined to optimize message delivery. `DisplayEvent` messages are now published directly via NATS for improved real-time performance, while other critical events continue to leverage JetStream for reliable persistence.
- 🔄 **Updated Messaging Client Configuration:** `WebSocketReceiver` now requires both NATS and JetStream contexts during initialization, providing more granular control over event publishing channels and supporting the optimized delivery strategy.

---



## [v0.110.0] - 2025-03-14 - Unified Content Handling & Bot Enhancements

### Added
- ✨ **New Content Extractor:** Introduced a dedicated `ContentExtractor` class to centralize and standardize the processing of messages and file attachments from various platforms, including Slack, Teams, and generic sources.
- 🖼️ **Robust Attachment Handling:** Enhanced the bot's capability to process diverse file attachments, now supporting automatic conversion of images to data URLs, inline display of text files, and clearer identification for unsupported file types like PDFs.

### Refactor
- 🧹 **Streamlined Bot Service Logic:** The `BotService` has been significantly refactored by externalizing all content processing logic into the new `ContentExtractor` class, greatly improving code modularity and maintainability.
- 🔄 **Codebase Consistency:** Performed minor clean-up and reordering of imports across several core modules to enhance consistency and readability.

---



## [v0.109.0] - 2025-03-14 - Enhanced Bot Intelligence & Multi-modal Input

### Added
- ✨ **Improved Microsoft Teams Integration**: Automatically clear previous conversation history when the bot is re-added or engaged in a Microsoft Teams chat, ensuring fresh and contextually relevant interactions.
- 🖼️ **Enhanced Multi-modal Attachment Handling**: Implemented a more robust method for processing image attachments from various channels (e.g., Slack, Microsoft Teams) by converting them into base64 data URLs. This change improves compatibility and reliability when providing multi-modal inputs to AI models.

---



## [v0.108.0] - 2025-03-13 - Enhanced Workflow Preconditions with Asynchronous Support

### Changed
- ⚡️ **Asynchronous Preconditions**: Workflow step precondition functions can now be defined as `async` functions, enabling complex readiness checks that involve asynchronous operations like network requests or database interactions.

---



## [v0.107.0] - 2025-03-13 - Agent Service Enhancements

### Added
- ✨ **Introduced Agent Cache Clearing:** Added a new static method to `AgentService` for clearing in-memory caches related to agent discovery, which is useful for testing and ensuring fresh data in development environments.

---



## [v0.106.0] - 2025-03-11 - Streamlined Event Handling and Core Library Refinements

### Refactor
- 🔄 **Standardized Core Events:** Relocated key NATS events, including `LLMStopEvent` and `GuardRejectionEvent`, from example-specific modules into the central `aihub_lib.nats.events` package. This change standardizes their availability and simplifies import paths across the entire codebase for enhanced consistency and maintainability.
- 🧹 **Improved Internal Event Imports:** Adjusted internal import mechanisms within `aihub_lib` for better alignment with the new, consolidated event structure.

### Removed
- 🗑️ **Deprecated Playground Event Definitions:** Eliminated the `LLMStopEvent` definition and its containing directory from the `aihub_agent/playground` section, as it has now been officially integrated into the core `aihub_lib`.

---



## [v0.105.0] - 2025-03-11 - Core Version Synchronization

### Changed
- ⚡️ **Project Version Synchronized:** All core components, including `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline`, have been updated to `v0.105.0` to align with the new release tag.

---



## [v0.104.0] - 2025-03-10 - Enhanced File Handling and Bot Configuration

### Added
- ✨ **Expanded File Attachment Support:** Bots can now process and include file attachments from both **Slack** (images and text files via OAuth token) and **Microsoft Teams** (images and text files via download URLs) within conversations, improving multi-modal interaction capabilities.
- ⚙️ **Slack Token Configuration:** Introduced a new `slack_token` field in `PathEntity` and a corresponding `--slack-token` CLI argument in `setup_azure_bot.py`, allowing administrators to securely configure Slack OAuth tokens for bots to enable advanced Slack features like file downloads.

### Changed
- 🔄 **Bot Conversation Context:** The internal bot service methods for adding user and bot messages to conversations (`add_user_message_to_conversation` and `add_bot_message_to_conversation`) now require a `path` parameter, providing more contextual information for operations like file handling.
- 📄 **Improved Attachment Logging:** Added more informative logging for unsupported attachment types in bot conversations, aiding in troubleshooting and development.

### Refactor
- 🧹 **Unified Text File Processing:** Consolidated the logic for handling text file content from attachments into a reusable internal helper method (`_text_file_content`), improving code clarity and maintainability.

---



## [v0.103.0] - 2025-03-10 - Direct Agent Communication & Event System Refinements

### Added
- 🚀 **New Agent API Endpoint:** Introduced a new API endpoint (`/agent/{agent_class}/{agent_id}/send_event`) allowing direct communication with specific agents. This enables sending any `StartEvent` (e.g., `UserMessageEvent`) to an agent and receiving its corresponding `StopEvent` in response, streamlining integration for external applications.
- ⚙️ **Dynamic Event Input Models:** Added a utility (`create_input_model`) to dynamically generate Pydantic input models for events, simplifying API request validation by automatically excluding internal or generated fields like `event_id` and `created_at`.

### Changed
- 🦾 **LLM Wrapping Agent Event Handling:** The `LLMWrappingAgent` now emits the more specific `LLMStopEvent` instead of a generic `StopEvent`, providing richer semantic information upon LLM completion.
- 🔄 **Expanded WebSocket User Event (`WSUserEvent`):** The `WSUserEvent` can now encapsulate any `StartEvent` type, making it more versatile for initiating various agent interactions beyond just user messages.
- 🧪 **Improved Simulated Agent API Testing:** The `SimulatedAgentApiTestRunner` has been updated to fully support the new semantic `LLMStopEvent` and `UserMessageEvent`, enhancing the fidelity and realism of API integration tests.

### Refactor
- 🧹 **Standardized Stop Signal Handling:** Renamed internal `_stop_event` to `_stop_signal` across runners and services to clearly distinguish between the asynchronous signal for termination and the actual `StopEvent` payload object, improving code clarity and robustness.
- 📄 **Promoted `LLMStopEvent` to Core Library:** The `LLMStopEvent` has been moved from an agent-specific directory to the core `aihub_lib` package, establishing it as a standard semantic event for LLM interactions across the platform.
- ♻️ **Refined Chat Service Event Processing:** The `ChatService` now explicitly separates the `stop_signal` (an `asyncio.Event`) from the received `StopEvent` object within its resource handling, allowing for more precise control and data management during agent interactions.

---



## [v0.102.0] - 2025-03-07 - Enhanced Document Metadata Handling

### Changed
- 🔄 **Flexible Document Metadata Assignment**: Updated the `RefDocDocument.add_metadata_from_data_lake_file` method to prioritize existing metadata from the data lake file's metadata dictionary, allowing for more granular control over how document attributes are populated.

### Fixed
- 🐛 **Improved Document Metadata Robustness**: Enhanced `RefDocDocument` properties (`namespace`, `hash`, `uri`, `updated`) to safely retrieve metadata using default fallback values, preventing potential errors when specific metadata keys are missing.
- 📄 **Minor Docstring Correction**: Corrected a grammatical error in the `RefDocDocument` docstring for improved clarity.

---



## [v0.101.0] - 2025-03-07 - Enhanced Reliability and Workflow Control

### Added
- ✨ **JetStream Event Store**: Introduced a new event store powered by NATS JetStream, significantly enhancing event persistence, durability, and replay capabilities across distributed agent runs. This replaces the previous Redis-based solution for more robust event management.
- 🦾 **Workflow Preconditions**: Implemented a new `@precondition` decorator, allowing developers to define sophisticated readiness checks for workflow steps. Steps will now only execute when all specified preconditions are met, enabling more precise control over workflow progression.
- 🧪 **Performance Testing Framework**: Added a dedicated performance testing playground, complete with specialized agents and benchmarking tools. This enables comprehensive measurement of system throughput, latency, and event processing efficiency.

### Changed
- 🚀 **Optimized Event Publishing**: Reworked the event publishing mechanism to leverage **JetStream for control events** (ensuring durable delivery) and **NATS Core for display events** (optimizing for high-volume, real-time data).
- ⚙️ **NATS Stream Configuration**: Updated JetStream stream settings to use **file-based storage** for enhanced durability, increased maximum message capacity to **10 million messages**, and refined the **duplicate message window to 1 minute** for improved deduplication.
- ⚡️ **Performance Enhancements**: Applied **caching to frequently accessed agent methods** (`get_steps`, `get_input_events`, etc.) and optimized **step execution counting** in the `StepStore` for improved workflow processing speed.
- 🔄 **NATS Subscriber Refinements**: Refactored NATS subscriber implementations to enhance **distributed event consumption** through better queue group management and clearer topic handling, improving overall system scalability.
- 📄 **Dispatcher Lifecycle Management**: Integrated explicit `start()` and `stop()` methods into the `Dispatcher` for **controlled initialization and graceful shutdown** of event processing within agent runners.

### Fixed
- 🐛 **Graceful Multiprocess Shutdown**: Introduced **signal handling** in the `MultiprocessAgentRunner` to ensure that agent processes terminate gracefully, enhancing stability and resource cleanup during deployment.

### Removed
- 🗑️ **Legacy Event Store**: Deprecated and removed the **Redis-based `DistributedEventStore`**, which has been fully superseded by the new JetStream event store.

---



## [v0.100.0] - 2025-03-07 - Enhanced Bot Configuration and Module Organization

### Added
- ✨ **Bot System Message Configuration**: Introduced the capability to define a system message for Azure bots during the setup process. This allows for pre-setting custom instructions or initial context, configurable via direct argument (`--system-message`) or from a file (`--system-message-file`).

### Refactor
- 🧹 **Bot Setup Script Relocation**: The `setup_azure_bot.py` script has been moved to a more logical location within the `aihub_bot/aihub_bot/` directory, improving module organization and overall project structure.

---



## [v0.99.0] - 2025-03-07 - Enhanced Chat Capabilities and Robust Error Handling

### Fixed
- 🐛 **Improved OpenAI Error Handling:** Chatbots now gracefully handle and display `BadRequestError` messages directly to the user from OpenAI API responses, providing clearer feedback when a request to the AI model fails.

### Changed
- ⚡️ **Enhanced Message Metadata with `name` Field:** Introduced a new `name` field for all conversation messages (user, bot, system), allowing for more specific identification of participants in interactions. This enhancement is crucial for enabling advanced AI features like tool use and multi-agent conversations.
- ⚙️ **Advanced OpenAI API Integration:** The new `name` field is now correctly passed to the OpenAI API, providing richer context for chat completions and enabling more precise control over how messages are interpreted, especially for function calling.
- 🧹 **Automated Name Sanitization for OpenAI:** Implemented automatic cleaning and sanitization of participant names (e.g., removing accents, replacing special characters) to ensure compliance with OpenAI API's strict naming conventions.
- 🔄 **Dynamic System Message Personalization:** The system message now supports a new `{assistant_name}` placeholder, allowing for more personalized and context-aware introductions or instructions from the bot.

---



## [v0.98.0] - 2025-03-06 - Enhanced Slack Integration and Multimodal Chat Capabilities

### Added
- 🖼️ **Multimodal Input Support:** Messages can now include richer content beyond plain text, such as images and attached text files, enabling more dynamic and versatile conversations.
- 💬 **Smarter Slack Channel Interactions:** Introduced advanced logic for Slack, allowing the bot to intelligently determine when to respond in channels based on direct mentions or ongoing conversational threads.

### Changed
- 🔄 **Updated Conversation Data Model:** The internal conversation entity has been revamped to store structured content, laying the groundwork for multimodal communication.
- 🗣️ **Improved Slack Message Handling:** Refined the way Slack messages are processed, differentiating between direct messages, channel mentions, and continued conversations, to ensure more accurate and relevant bot responses.

### Refactor
- 🧹 **Consolidated Slack Logic:** Centralized Slack-specific message processing into a dedicated `handle_slack_message` service method for improved modularity and maintainability.
- ⚙️ **Standardized Internal Methods:** Renamed internal content conversion methods for clarity and consistency.

---



## [v0.97.0] - 2025-03-06 - Enhanced LLM System Prompt Configuration

### Changed
- 🚀 **Improved LLM Parameterization:** The `cost_reporting_llm` context manager now accepts an optional `system_prompt`, enabling more dynamic and precise control over the system-level instructions provided to Large Language Models during operation, especially when tracking costs.

---



## [v0.96.0] - 2025-03-06 - Bot Service Stability and Core Updates

### Fixed
- 🐛 **Improved Bot Message Handling:** The `_send_or_update_activity` method in the bot service now gracefully handles empty message buffers, preventing unnecessary activity updates and enhancing overall stability.

---



## [v0.95.0] - 2025-03-06 - Improved Bot Responsiveness and Configuration

### Changed
- 💬 **Improved Bot Responsiveness**: All bot types, including Agent and OpenAI, and their streaming versions, now display a "typing" indicator while generating responses. This enhancement provides immediate feedback and a more interactive experience for users.
- ⚙️ **Updated Development Environment Configuration**: Modified `development/.env` variables to align with current Azure subscription and application naming conventions, streamlining development setups.

### Added
- 🧪 **Standardized Testing Environment Configuration**: Introduced dedicated `.env` files for testing playgrounds (`aihub_bot/playground/testing`), ensuring consistent environment setup across various test scenarios.

### Refactor
- 🧹 **Refactored Internal Text Sending Logic**: The `send_text` helper function within the bot service (`aihub_bot/aihub_bot/routes/Service.py`) was refactored into a nested method within `send_response_stream`, enhancing code encapsulation and maintainability.

---



## [v0.94.0] - 2025-03-05 - Enhanced Bot Communication and Configuration Flexibility

### Changed
- ✨ **Enhanced Streamed Chat Responses:** Significantly improved the handling of long, continuously updated messages in chat bots, including automatic splitting of responses to comply with platform length limits and prevent truncation.
- ⚙️ **Flexible Azure App Naming:** Updated the `AzureBaseConfig` to allow hyphens in Azure application names, providing greater flexibility for deployment configurations.

### Fixed
- 🐛 **Resolved Agent Chat Timeout:** Corrected an issue where the agent chat stream could experience unnecessary timeouts, ensuring smoother and more reliable message delivery.

---



## [v0.93.0] - 2025-03-05 - Core Component Alignment and Version Synchronization

### Changed
- 🚀 **Synchronized Core Components**: Updated version numbers across all `aihub_` components (agent, api, bot, lib, pipeline) and their inter-dependencies to `v0.93.0`, ensuring consistent release alignment.

### Refactor
- 🧹 **Import Statement Reorganization**: Reordered import statements within the `OpenaiChatController` for enhanced code readability and adherence to established coding standards.

---



## [v0.92.0] - 2025-03-05 - Enhanced RAG Agent with Context Sufficiency Guard

### Added
- ✨ **Introduced Context Sufficiency Guard**: A significant enhancement to the RAG Agent, this new guard evaluates whether the retrieved context is sufficient to answer a user's query. This prevents the agent from providing answers based on irrelevant or incomplete information, leading to more precise and helpful responses.
- ⚙️ **Configurable Context Sufficiency Check**: A new `check_context_sufficiency` option has been added to `RAGAgentConfig`, allowing users to enable or disable the context sufficiency guard based on their application's needs.
- 💬 **New Context Outcome Events**: Implemented `ContextSufficientEvent` and `ContextInsufficientEvent` to clearly signal the result of the context sufficiency check within the agent's processing workflow.

### Changed
- 🔄 **Refined RAG Agent Response Flow**: The RAG Agent's response generation step has been updated to intelligently handle scenarios where the context is deemed insufficient by the new guard. In such cases, the agent will now respond without relying on the poor context, aiming for a more appropriate and reliable answer.

### Refactor
- 🧹 **Streamlined Few-Shot Accept Event**: The `FewShotAcceptEvent` constructor has been cleaned up by removing the redundant `success=True` argument, simplifying event handling.
- 📂 **Prepared Agent-in-the-Loop Event Structure**: New foundational package structures have been set up for future agent-in-the-loop events, laying the groundwork for more advanced interactive agent capabilities.

---



## [v0.91.0] - 2025-03-05 - Scaling Agents and Enhancing Developer Experience

### Added
- 🚀 **Multiprocess Agent Runner:** Introduced a new `MultiprocessAgentRunner` to enable horizontal scaling of agents by running multiple instances in separate processes, significantly improving performance and throughput.
- ⚡️ **GPU-Accelerated Infrastructure:** Added a `docker-compose-gpu.yml` file to provide a quick setup for GPU-enabled services, including `llama.cpp` and HuggingFace Text Embeddings Inference, streamlining local development with powerful models.
- ⚙️ **Developer Run Configurations:** Included pre-configured IntelliJ IDEA run configurations for easier execution of API, Agent, Bot, and Library tests, as well as simplified local API and Bot service startups.

### Changed
- 📈 **Enhanced CI/CD Reporting:** Updated GitHub Actions for backend tests and Pytest coverage to provide more detailed and unique reports for different working directories.
- ⏱️ **Improved Logging Output:** Added timestamps with millisecond precision to all log messages for better debugging and event correlation.
- 🔗 **Agent Runner Redis Requirement:** The `AgentRunner` now explicitly requires a `redis_url` configuration, aligning with its distributed event store capabilities.

### Fixed
- 🐛 **Accurate Tracing Spans:** Corrected the lifecycle management of OpenTelemetry tracing spans in `RunTraceCoordinator` to ensure complete and accurate capture of agent step executions.
- 🧹 **Robust Semantic Convention Handling:** Improved the serialization of OpenTelemetry semantic convention attributes (e.g., LLM invocation parameters) and ensured that `None` values are correctly filtered, leading to cleaner and more precise trace data.

### Removed
- 🗑️ **Non-Functional Docker Compose:** Removed the `docker-compose-open-webui.yml` file, which was identified as non-functional, to streamline the project's infrastructure configurations.

### Refactor
- 🔄 **Optimized Distributed Event Store:** Refactored the `DistributedEventStore` to directly cache and retrieve deserialized `ControlEvent` objects, enhancing performance and type safety.
- 📄 **Playground Example Cleanup:** Cleaned up the `FanOutAgent` playground example by removing extraneous timing logic and unused variable assignments.

---



## [v0.90.0] - 2025-03-04 - Platform Stability and Developer Experience Improvements

### Added
- ✨ **Introduced Configurable Logging**: Added `LoggingConfig` to allow setting the global log level via environment variables (`LOG_LEVEL`), enhancing debugging flexibility.
- 📄 **Enabled Structured Logging**: Integrated `enable_logging` in API and Bot playground tests for improved debugging and monitoring capabilities.

### Changed
- ⚡️ **Improved OpenTelemetry Span Exporting**: Switched from `SimpleSpanProcessor` to `BatchSpanProcessor` with optimized batching settings, enhancing tracing performance and reducing overhead for production environments.
- ⚙️ **Enhanced Logging Configuration**: The `enable_logging` utility now supports overriding default log levels for libraries and the main application via environment variables, providing more granular control over logging output.

### Fixed
- 🐛 **Clarified Test Naming**: Renamed a test function in `FewShotAgent` to accurately reflect its validation of `GuardRejectionEvent` presence, improving test suite clarity.
- 🐛 **Enhanced Test Precision**: Renamed ambiguous test steps for `AgentInTheLoopResponse` events to distinguish between successful results and exceptions, improving test readability and reliability.

### Removed
- 🗑️ **Removed Unused Chat Controller**: The `ChatController` is no longer imported or used in the API testing playground, simplifying its setup.
- 🗑️ **Removed Redundant Event Init Files**: Deleted unnecessary `__init__.py` files from `agent_in_the_loop` event subdirectories, streamlining the event module structure.

### Refactor
- 🧹 **Cleaned Up Test Run Context**: Removed unused `topic` variable from `runner.test_run()` in the discoverable workflow trigger, simplifying the test setup.
- 🧹 **Removed Unused Imports**: Cleaned up unnecessary `Callable` import in `AgentController`.
- 🧹 **Cleaned Up Event Controller**: Removed unused imports (`Any`, `Callable`) and simplified exception handling in `EventController`.
- 🧹 **Streamlined I18n Controller**: Removed unused imports (`Any`, `Callable`, `User`) from `I18nController`.
- 🧹 **Optimized I18n Service**: Removed unused `User` import from `I18nService`.
- 🧹 **Refined OpenAI Controller**: Removed unused imports (`Any`, `Callable`) in `OpenaiController`.
- 🧹 **Updated Thread Controller**: Removed unused imports (`Any`, `Callable`) in `ThreadController`.
- 🧹 **Simplified Thread Response DTO**: Streamlined `ThreadResponse` by removing unnecessary imports of `ThreadEntity`, `NATS`, `AgentService`, and `UserService`, indicating a cleaner data structure.
- 🧹 **Cleaned Up Token Controller**: Removed unused `datetime` and `timezone` imports from `TokenController`.
- 🧹 **Centralized OpenAI Endpoint Configuration**: Consolidated Azure OpenAI service URLs into a single `OPENAI_URL` constant within the API playground, enhancing configurability and maintainability.
- 🧹 **Cleaned Up OAuth2 API Tests**: Removed unused `os` import from OAuth2 API tests.
- 🧹 **Refined Thread API Tests**: Removed unused `ObjectId` import from thread API tests.
- 🧹 **Streamlined Bot Runner**: Removed unused `AzureBaseConfig` import from `BotRunner`.
- 🧹 **Cleaned Up Azure Bot Setup**: Removed unused imports (`webbrowser`, `SubscriptionClient`) from the Azure bot setup script.
- 🧹 **Improved Test Code Style**: Added `noqa` annotations to test functions in `MultiAuthHandler` to resolve static analysis warnings related to forward references.
- 🧹 **Refined NATS Event Imports**: Updated import paths for `AgentInTheLoop` exception, request, and response events within the NATS event package for better module organization.

---



## [v0.89.0] - 2025-03-03 - Enhanced Agent Dispatching and Step Execution Management

### Added
- ✨ **Introduced Idempotent Step Execution:** The agent dispatcher now prevents redundant re-execution of a step within the same run if it has already been called with the exact same input control events, improving overall efficiency and reliability of agent workflows.

---



## [v0.88.0] - 2025-03-03 - Core Messaging System Enhancements and Workflow Refinements

### Changed
- 🚀 **Improved NATS Message Publishing Reliability:** Enhanced the `JSPublisher` with built-in retry mechanisms, timeouts, and message deduplication (using `Nats-Msg-Id` headers) to ensure more robust event delivery.
- ⚙️ **Optimized NATS JetStream Configuration for Agents:** Configured the Agent Runner's JetStream context with explicit timeouts (60s) and increased asynchronous publish pending limits (10,000 messages) for better performance and stability.
- 💾 **Refined NATS Stream Management:** Default NATS stream storage now uses `MEMORY` instead of `FILE` for improved performance. Streams are also configured with a maximum of 1,000,000 messages, a 30-day age limit, and a 1-hour duplicate window for efficient retention and deduplication.
- 🐳 **Switched to Alpine-based NATS Docker Image:** Updated the `docker-compose` configuration to use the `nats:alpine` image, reducing the overall image size and potentially improving deployment speed.

### Refactor
- 🧹 **Streamlined Development Workflow:** Reordered the `format` and `lint` steps in the `pr-ready` Makefile target across all services, improving the consistency of pre-commit checks.

---



## [v0.87.0] - 2025-03-03 - Unleashing Performance: Redis Integration for Agent Workflows

### Added
- 🚀 **Redis Infrastructure:** Introduced Redis as a new core dependency, providing a high-performance, in-memory data store for transient agent states and event logs.
- ⚡️ **Telemetry Header Caching:** Implemented in-memory caching for telemetry headers within the Dispatcher to reduce redundant data retrievals and improve performance.
- 📄 **Redis Configuration:** A new `RedisConfig` class has been added to centralize Redis connection settings.

### Changed
- 🔄 **Persistence Layer Migration:** The underlying persistence mechanism for Dispatcher, Event Store, Step Store, RunContext, and ThreadContext has been migrated from NATS JetStream Key-Value stores to Redis, significantly enhancing performance and scalability for agent state management.
- 💾 **Durable NATS Streams:** NATS streams now default to file-based storage (`StorageType.FILE`) instead of memory, ensuring greater data durability for event streams.
- 🧹 **Code Quality Standards:** Added `lint` to the `pr-ready` Makefile targets across all microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_pipeline`) to enforce consistent code quality checks.
- ⚙️ **Optimized Event Retrieval:** The Dispatcher's event handling for step readiness has been refined to efficiently retrieve specific input event types, reducing unnecessary data loading.
- 🧪 **Streamlined Agent Initialization:** Various playground examples and agent implementations have been updated to remove direct `StartEvent` dependencies where a `UserMessageEvent` is more semantically appropriate, simplifying initial event processing.

### Refactor
- 🛠️ **Storage Abstraction Redesign:** The `StoreBase` and its derived classes (`DistributedEventStore`, `DistributedStepStore`) have been re-architected to seamlessly integrate with Redis, providing a more robust and performant storage solution.
- 🏗️ **Context Management Overhaul:** `BaseContext`, `RunContext`, and `ThreadContext` have been refactored to leverage Redis for their state management, improving consistency and performance across agent runs and threads.

### Removed
- 🗑️ **Redundant StartEvent Imports:** Explicit `StartEvent` imports have been removed from several agent and playground implementations where the event was not actively consumed, streamlining code.
- 🎯 **Generic Event Retrieval:** The less specific `get_all_events` method has been removed from `DistributedEventStore`, favoring more targeted and efficient type-specific event retrieval methods.

---



## [v0.86.0] - 2025-03-03 - Bot Logic Streamlining and Internal Improvements

### Refactor
- 🧹 Streamlined **Bot Chat Logic** by removing redundant system message retrieval calls from `StreamAgentChatBot`, `OpenaiChatBot`, and `StreamOpenaiChatBot`, simplifying internal communication flows.

---



## [v0.85.0] - 2025-02-28 - Document Intelligence Loader Compatibility Update

### Changed
- 🔄 **Updated Document Intelligence Loader**: Aligned the document analysis request parameter (`analyze_request` to `body`) within the `DocumentIntelligenceLoader` to ensure compatibility with the latest Azure Document Intelligence client API.

---



## [v0.84.0] - 2025-02-28 - Streamlined Event Handling

### Removed
- 🗑️ **Deprecated `LimitChatHistoryWithContextEvent`:** Removed an internal event previously used for limiting chat history and context based on token counts, streamlining the event handling mechanism.

---



## [v0.83.0] - 2025-02-27 - Performance Boost: NATS JetStream Defaults to Memory Storage

### Changed
- ⚡️ **Optimized NATS JetStream Storage:** Switched the default storage type for **Key-Value stores** (including `StoreBase`, `RunContext`, and `ThreadContext`) and **NATS streams** from `FILE` to `MEMORY`. This change significantly enhances performance by keeping data in-memory, reducing disk I/O for ephemeral or short-lived data.
- 🔄 **Improved KV Store Initialization:** Enhanced the reliability of Key-Value store creation by refining the error handling to gracefully retrieve existing stores, preventing redundant creation attempts and improving robustness.

---



## [v0.82.0] - 2025-02-27 - Agent Core Refinements and Performance Boosts

### Added
- ⚡️ **Introduced Event Store Caching:** Implemented a Time-To-Live (TTL) cache for retrieving JSON values from the distributed event store, significantly boosting performance for frequently accessed data by reducing repeated lookups.

### Changed
- ⚙️ **Refined Step Execution Counting:** The dispatcher's step execution counter now conditionally increments only for methods explicitly configured with a maximum execution limit per run, providing more precise tracking and control.

### Removed
- 🗑️ **Streamlined Internal Store Logic:** Deprecated and removed generic retry operation and synchronization methods (`retry_operation`, `synchronized_update`) from the base store and NATS context classes, simplifying the core architecture and centralizing retry patterns where appropriate.

---



## [v0.81.0] - 2025-02-27 - Improved Event Handling and Step Execution Reliability

### Changed
- 🚀 **Revamped Distributed Event and Step Stores:** Significant architectural changes to the underlying storage mechanisms for events and step execution counts. This eliminates race conditions by storing each event and execution as a unique, individually addressable record, rather than relying on shared lists or counters, leading to more reliable state management in concurrent environments.
- ⚡️ **Optimized Dispatcher Event Retrieval:** The Dispatcher now fetches all necessary run events once per trigger cycle, passing them efficiently to step readiness checks and execution. This reduces redundant data store calls and improves overall performance.
- 🛡️ **Strengthened NATS JetStream Resilience:** Increased retry attempts and refined backoff strategies for Key-Value store operations, along with improved error handling for store creation and deletion. This enhances the system's robustness against transient network issues and concurrent store access.
- 📄 **Updated Optional Workflow Example:** The `optional_step` in the minimal workflow example now demonstrates the use of the `max_executions_per_run` constraint.

### Refactor
- 🧹 **Removed Custom Mutex Logic:** The custom `synchronized_update` method, which previously used a mutex pattern for atomic operations, has been removed, replaced by the new race-condition-free storage strategies.
- 🔄 **Consolidated Key-Value Operations:** Introduced a `put_value` helper method within `StoreBase` to streamline raw byte storage operations, improving internal consistency.

---



## [v0.80.0] - 2025-02-27 - Enhanced Localization Capabilities

### Changed
- 🌍 **Improved Localization:** The `LocaleHandler` for internationalization (i18n) now supports passing additional keyword arguments (`**kwargs`) to the underlying translation function, enabling more flexible dynamic string formatting and variable interpolation within translated texts.

---



## [v0.79.0] - 2025-02-27 - Robust Data Integrity with Synchronized Distributed Stores

### Added
- ✨ **Introduced Synchronized Update Mechanism:** Implemented `synchronized_update` methods in `StoreBase` and `BaseContext` to provide robust, mutex-based concurrency control for critical data operations in JetStream Key-Value stores, preventing race conditions in distributed environments.
- ⚙️ **New KV Store Utility Methods:** Added helper methods like `get_value`, `put_json_value`, and `get_json_value` to `StoreBase`, simplifying common data interactions and improving code readability for distributed storage.
- 🚀 **Atomic Operation Retries:** Implemented an `atomic_operation` utility with exponential backoff and retry logic in `StoreBase` to enhance resilience against transient network or system errors during critical operations.

### Changed
- 🔄 **Improved Event Storage Concurrency:** The `DistributedEventStore` now leverages the new synchronized update mechanism to safely append events, ensuring data consistency and preventing duplicates, even under high concurrency.
- 📊 **Robust Step Count Management:** The `DistributedStepStore` now utilizes synchronized updates for `increment_execution_count`, ensuring accurate and reliable tracking of step executions across distributed agents.
- 🧹 **Cleaned Up Key Listings:** KV store `keys()` and `get_all()` operations now automatically filter out internal mutex keys, providing cleaner and more relevant results when inspecting store contents.

---



## [v0.78.0] - 2025-02-27 - Streamlined Azure AI Search Configuration

### Changed
- ⚙️ **Azure AI Search Vector Store**: The `semantic_configuration_name` parameter in the `AzureAISearchVectorStoreFactory` now defaults to `"mySemanticConfig"`, simplifying the creation of vector stores with built-in semantic search capabilities and streamlining the underlying configuration logic.

---



## [v0.77.0] - 2025-02-26 - Streamlined Message Acknowledgment

### Changed
- ⚡️ **Optimized NATS JetStream Message Handling:** Messages are now acknowledged immediately upon reception and successful deserialization, improving reliability by preventing message re-delivery issues, especially for long-running or error-prone processing tasks.

---



## [v0.76.0] - 2025-02-26 - Reliable NATS Message Processing

### Changed
- ⚡️ **Improved NATS JetStream Subscriber Acknowledgment:** The order of operations in the `JSSubscriber` has been updated to acknowledge messages *before* their respective handlers are executed. This modification enhances message processing reliability by ensuring that messages are promptly acknowledged, preventing redelivery in scenarios where the message handler might encounter an error.

---



## [v0.75.0] - 2025-02-26 - Improved Asynchronous Message Handling for NATS Subscribers

### Refactor
- ⚡️ **Enhanced NATS Subscriber Concurrency**: Refactored the `JSSubscriber` and `NCSubscriber` components to process incoming NATS messages asynchronously. This change ensures that the main message listener remains non-blocking, significantly improving overall system responsiveness and reliability when handling message streams.

---



## [v0.74.0] - 2025-02-26 - Refined Document Metadata Extraction

### Fixed
- 🐛 **Corrected document metadata enrichment** for `RefDocDocument` objects. The process now accurately extracts the document title and ID from the `DataLakeFile`'s URI, ensuring consistency and correctness when processing files from the data lake.

---



## [v0.73.0] - 2025-02-26 - Core Stability Update

### Fixed
- 🐛 **Resolved WebSocket message handling:** Implemented a robust check to ensure the existence of the `messages` attribute before accessing it, preventing potential errors during WebSocket event processing, especially when handling start events for threads.

---



## [v0.72.0] - 2025-02-26 - RAG Document Metadata Enrichment

### Added
- ✨ **Enhanced RAG Document Metadata**: Automatically extract and store the `DOCUMENT_TITLE` from the data lake URI and explicitly include the `SOURCE` URI in the metadata for reference documents, improving content traceability and discoverability within the RAG system.

---



## [v0.71.0] - 2025-02-26 - Enhanced Self-Hosted LLM Support

### Changed
- ⚙️ **Improved Self-Hosted LLM Compatibility**: Enhanced the tokenizer loading logic for self-hosted LLMs to correctly handle models with `-bnb` and `-4bit` suffixes, enabling broader support for quantized model variations.

---



## [v0.70.0] - 2025-02-26 - Flexible Azure OpenAI Authentication

### Added
- ✨ **Azure OpenAI API Key Support:** Introduced the option to authenticate with Azure OpenAI models using a direct API key, providing an alternative to Azure AD-based authentication for enhanced flexibility.

---



## [v0.69.0] - 2025-02-25 - Build System Enhancements

### Changed
- ⚡️ **Improved CI/CD Workflow Efficiency:** Optimized the `add-tag` GitHub Actions workflow by introducing Poetry caching and explicit steps for validating and installing global dependencies, leading to more reliable and faster builds.

---



## [v0.68.0] - 2025-02-25 - Improved LLM Model Compatibility

### Changed
- 🚀 **Enhanced Self-Hosted LLM Tokenization:** The `tokenizer` property for self-hosted Large Language Models now intelligently infers the base model name by removing common suffixes (like `-GGUF` or `-AWQ`). This change ensures more robust tokenizer loading for various model variants and directly provides the encoding function for streamlined text processing.

---



## [v0.67.0] - 2025-02-25 - Enhanced Dependency Management Tooling

### Refactor
- 🧹 **Renamed Dependency Management Script:** The internal script used for switching between local and remote core dependencies has been renamed from `switch_dependency.py` to `switch_dependencies.py` for improved clarity and alignment with its function.
- ⚡️ **Standardized Script Execution:** Updated `Makefile` commands to consistently use `poetry run` when executing dependency switching scripts, ensuring they run within the project's isolated Poetry environment for better reliability and dependency management.

---



## [v0.66.0] - 2025-02-25 - Streamlined User Experience & Secure Authentication

### Added
- 🔑 **Introduced Hybrid Authentication**: The API now supports simultaneous OAuth2 and Bearer token authentication, offering greater flexibility for various client types.
- 🖼️ **User Profile Image Support**: User profiles fetched from Azure AD now include a base64-encoded profile image, which is displayed in the frontend.
- 📄 **New User Data Persistence**: Implemented `UserEntity` to store user-specific preferences and data, paving the way for personalized experiences.
- 💡 **OpenAPI Client SDK Generation**: Automated the generation of a TypeScript client SDK for the frontend, simplifying API interactions for developers.
- ⚙️ **Modular UI Layout System**: Introduced a new default layout with a collapsible sidebar for streamlined navigation and an anonymous layout for public pages.
- 🌙 **Dynamic Dark Mode Toggle**: Added a toggle to easily switch between light and dark themes, enhancing user comfort.
- 🌐 **Open Web UI Module Integration**: The frontend now includes a dedicated module page to embed and access Open Web UI via an iframe.
- ⚡️ **Silent OIDC Token Renewal**: Implemented silent token renewal for OAuth2, ensuring continuous user sessions without visible re-authentication prompts.
- ✅ **Standardized Health Check Response**: A new `HealthResponse` DTO provides a structured format for API health check endpoints.

### Changed
- 🎨 **Revamped User Interface**: Migrated from ShadCN UI components to PrimeVue, resulting in a cleaner design and improved consistency across the application.
- 🔄 **Authentication Dependency Management**: Updated API route authentication to use FastAPI's `Security` dependency for better integration and future extensibility.
- 📈 **Improved API Documentation**: Configured API routes to automatically generate `operation_id` for enhanced OpenAPI documentation and client SDK clarity.
- 🛠️ **Refined User Data Retrieval**: Adjusted internal user data fetching logic in the API to retrieve comprehensive user profiles, including new profile image capabilities.
- 💅 **Enhanced Frontend Styling**: Updated core CSS to use Roboto font and refined PrimeVue theme presets for a cohesive design.

### Removed
- 🗑️ **Removed Legacy UI Components**: Deprecated and removed ShadCN UI components and related styling configurations as part of the migration to PrimeVue.
- 🧹 **Deprecated Multi-Authentication Handler**: Replaced the previous generic `MultiAuthHandler` with a more specialized `TokenAndOauth2Handler` to align with the new authentication strategy.

---



## [v0.65.0] - 2025-02-25 - Enhanced LLM Configuration and Core Updates

### Changed
- 🔄 **Improved LLM Configuration Flexibility:** The `LLMWrappingAgent` now utilizes a more generalized `ChatLLMConfig` for its Large Language Model setup, allowing for broader compatibility and easier integration with various chat-based LLM providers.

---



## [v0.64.0] - 2025-02-24 - Robustness Improvements and Core Updates

### Changed
- 🦾 **Improved Locale Handling in Dispatcher:** The `Dispatcher` now gracefully defaults to a standard locale when no specific locale is found in the run context, enhancing system robustness and preventing potential errors.

---



## [v0.63.0] - 2025-02-21 - Enhanced Guardrail Precision and Testing Capabilities

### Changed
- ⚡️ **Enhanced `AgentTestRunner`:** Improved the `get_events` and `get_events_of_type` methods in `AgentTestRunner` by adding a new `event_filter` parameter, enabling more precise retrieval of observed events based on their topic's specific event type.
- 📄 **Improved Few-Shot Guard Prompt:** Updated the prompt and internationalization strings for the `Few-Shot Guard` to provide clearer instructions to Large Language Models, ensuring more reliable and structured JSON output for guardrail decisions.

---



## [v0.62.0] - 2025-02-20 - Streamlined Development and Enhanced Testing Stability

### Changed
- 🚀 **Improved GitHub Action Stability:** The `test_backend` GitHub Action now waits for Docker services to become healthy *after* installing Python dependencies. This change enhances the stability and reliability of automated tests in CI/CD pipelines.

### Refactor
- 🧹 **Streamlined Local Development Setup:** Simplified the configuration for the `NoAuthHandler` by embedding default user details (name, email, and roles) directly within the `NoAuthConfig` class. This reduces boilerplate configuration in local development environments and makes initial setup more seamless.

---



## [v0.61.0] - 2025-02-20 - Streamlined Pipeline Configuration and Enhanced LLM Integration

### Refactor
- 🧹 **Unified Resource Management**: Reworked core pipeline resources by replacing the generic `NamespaceResource` with more specific and explicit resources such as `DataLakeResource` and `DocStoreResource`. This simplifies configuration and improves clarity.
- ⚙️ **Direct LLM Configuration**: Streamlined the integration of Large Language Models (LLMs) by allowing `EmbeddingModelResource` and `LanguageModelResource` to be configured directly via their respective model configurations, eliminating the need for an intermediate `LlmHandlerResource`.
- 🔄 **Decoupled Data Store Resources**: Refactored `DataLakeClientResource`, `MongoDocumentStoreResource`, and `AzureAISearchVectorStoreResource` to accept direct configuration parameters (e.g., `container_name`, `document_store_name`, `vector_store_name`) instead of relying on the removed `NamespaceResource`.
- 🚀 **Simplified Pipeline Definitions**: Updated pipeline definitions and job factories to align with the new resource structure, reducing reliance on the `customer_name` parameter for job naming and asset key generation.
- 🗄️ **Explicit Data Lake Paths**: Enhanced data lake operations by explicitly defining container and directory names, moving away from a general namespace concept for file handling.
- 🛡️ **Improved MongoDB Connection**: Strengthened MongoDB connection logic by ensuring connections are always made to a specific database name and incorporating robust error handling.

### Changed
- 🦾 **Flexible Azure AI Search Vector Store**: Enabled the creation of Azure AI Search Vector Stores without requiring a semantic configuration name, providing greater flexibility for various use cases.
- 📄 **Enhanced Asset Input Flexibility**: Asset factories for documents, nodes, and removed documents now support `AssetKey` objects in addition to strings for input keys, improving asset graph definition.
- 🌐 **Dynamic Git Linkage**: Adjusted pipeline code reference linking to dynamically point to customer-specific GitHub repositories and use the `main` branch, improving code traceability.
- 📖 **Clarified Milvus Vector Store Docs**: Updated docstrings and examples for `MilvusVectorStoreResource` to provide clearer guidance and usage examples.
- 📈 **Refined Asset Metadata Reporting**: Adjusted metadata reported for data lake assets, focusing on file count and size, and made reporting conditional on the presence of files.

### Removed
- 🗑️ **Deprecated Namespace Resource**: Eliminated the `NamespaceResource` and related utility functions, simplifying the overall resource hierarchy.
- ❌ **Removed LLM Handler Resource**: Discontinued the `LlmHandlerResource` as LLM configurations are now handled directly by individual model resources.

---



## [v0.60.0] - 2025-02-20 - Core Version Alignment and Action Flexibility

### Changed
- 📄 **GitHub Actions**: Removed the default Dockerfile path from the `build_image` action input, providing greater flexibility for specifying the Dockerfile location during image builds.

---



## [v0.59.0] - 2025-02-20 - Infrastructure Refinements and Test Visibility

### Changed
- 🔄 Updated the **`llama.cpp` Docker image** in `docker-compose.yml` to the latest stable `server` tag, ensuring access to recent LLM serving capabilities and improvements.
- 🛠️ Enhanced the **backend testing GitHub Action** by adding a `docker compose ps` command, providing improved visibility and debugging capabilities during service startup.

---



## [v0.58.0] - 2025-02-20 - Build Action Enhancements

### Changed
- ✨ **GitHub Build Action**: Enhanced the `build_image` action by adding support for specifying a custom **Dockerfile** path, providing greater flexibility for building container images.

---



## [v0.57.0] - 2025-02-20 - Enhanced User Context and Open-WebUI Integration

### Added
- ✨ **New Open-WebUI Authentication Handler:** Introduced a dedicated `OpenWebuiAuthHandler` to streamline user authentication when integrating with the Open-WebUI frontend.
- 🧪 **Testing Utility for Fake Users:** Added a `fake_user()` helper function within `aihub_lib` to simplify the creation of authenticated user objects in test scenarios.

### Changed
- 🔄 **Centralized User Information in Messages:** Modified `UserMessageEvent` to directly include a comprehensive `AuthenticatedUser` object, replacing the previous user OID string, ensuring richer user context across agent interactions.
- 🚀 **Enhanced Chat Service User Context:** Updated core `ChatService` and `WebSocketReceiver` methods to accept `AuthenticatedUser` objects instead of just user OIDs, improving security and contextual awareness in chat interactions.
- 🔑 **Agent Access Control for OpenAI API:** Implemented user-role-based access control for agents exposed via the OpenAI API endpoints, ensuring users only discover and interact with agents they are authorized to use.
- ⚙️ **Updated Playground Agent Triggers:** Adjusted all playground agent test runners and trigger scripts to utilize the new `AuthenticatedUser` object within `UserMessageEvent`.
- 🌐 **Defaulted to Open-WebUI Authentication:** The development playground now defaults to using the new `OpenWebuiAuthHandler` for authentication, facilitating easier testing and integration.

---



## [v0.56.0] - 2025-02-20 - Core Component Version Update and Release Automation

### Added
- ⚙️ **Automated Dependency Tagging**: Introduced a new GitHub Actions step to automatically update the `aihub-lib` version tag within `poetry.lock` files, enhancing consistency in dependency management during releases.

### Changed
- 🚀 **Core Component Version Update**: All core components, including `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline`, have been updated to version `v0.56.0`.
- 🔗 **Dependency Alignment**: The internal `aihub_lib` dependency tag has been synchronized to `v0.56.0` across all consuming microservices to ensure consistent versioning.

---



## [v0.55.0] - 2025-02-20 - Unified Chat: Agents Now Speak OpenAI & Dedicated User Messages

### Added
- 🚀 **OpenAI API Compatibility for Agents**: Introduced new endpoints (`/openai/models` and `/openai/chat/completions`) in the API to expose ai-hub agents directly through an OpenAI-compatible interface, simplifying integration for client applications.
- 💬 **Dedicated `UserMessageEvent`**: A new event type (`UserMessageEvent`) has been added to specifically handle user conversational input, providing clearer semantics for initiating chat-based agent workflows.
- 🔍 **Conversational Flag in Agent Discovery**: Agents can now explicitly declare their conversational capabilities via an `is_conversational` flag in the agent discovery response, allowing clients to easily identify chat-enabled agents.

### Changed
- 🔄 **Agent Input Event Types**: Various conversational agents (e.g., FewShotAgent, RAGAgent, LLMWrappingAgent) now exclusively use the new `UserMessageEvent` for initial conversational input, deprecating the use of the generic `StartEvent` for this purpose.
- ⚙️ **API Endpoint Restructuring**: The primary API endpoints for chat interactions have been migrated and consolidated under the OpenAI-compatible `/openai` path, streamlining the API surface.
- 📄 **Updated Playground Examples and Tests**: All relevant playground examples and unit tests have been updated to reflect the new `UserMessageEvent` and the consolidated OpenAI API endpoints, ensuring consistency and proper usage.
- ✨ **Improved Tracing for User Input**: The run trace coordinator now directly leverages the `user_query` property of `UserMessageEvent` for more accurate and direct extraction of user input in tracing.

### Removed
- 🗑️ **Deprecated `/chat` API Endpoints**: The standalone `/chat/completions/stream` and `/chat/completions/json` API endpoints have been removed, as their functionality is now fully integrated into the OpenAI-compatible `/openai/chat/completions` endpoint.
- 🧹 **`StartEvent` Conversational Context**: The generic `StartEvent` no longer carries message history or locale information; these conversational details are now exclusively part of the new `UserMessageEvent`.

---



## [v0.54.0] - 2025-02-19 - Unifying Access & Chat: Major AI Hub Enhancements

### Added
- 🔑 Introduced comprehensive **API Token Management** with new endpoints for creating, listing, and revoking bearer tokens, enabling granular access control.
- 🔑 Implemented **`AuthHandler`** as an abstract base class, providing a standardized interface for authentication strategies.
- 🔑 Developed **`MultiAuthHandler`** to support chaining multiple authentication strategies, enabling flexible and robust authentication flows.
- 🔑 Introduced **`TokenAuthHandler`** for robust bearer token authentication, including validation against the database.
- 🔑 Added **`DevUserInformationProvider`** and **`ApiTokenUserInformationProvider`** to support multi-strategy user information retrieval.
- 🤖 Integrated a new **`aihub_bot` module** to enable chatbot functionalities, serving as a unified interface between users and AI agents.
- 📄 Provided extensive **documentation for Chatbots**, detailing their architecture, technical implementation, and deployment process.
- ⚙️ Created **`ApiConfig`** to centralize API-specific settings, including the database name and debug mode.
- 🧪 Introduced a comprehensive suite of **Python-based integration tests** for Agent, Auth (Bearer & OAuth2), Chat, Health, Locale, OpenAI, Threads, Token, and User API endpoints.
- 🧪 Developed **`ASGIAdapter`** to enable direct, in-process HTTP requests to FastAPI applications during testing, significantly improving test reliability and speed.
- 🛑 Introduced a new abstract method `get_stop_events()` in the **`Agent` base class** to define and retrieve events that signify workflow termination.
- 💬 Added `created_at` timestamp to **Thread entities** for better tracking and auditability.
- 🔑 Provided a new **utility script `generate_api_token.py`** for programmatic creation of API bearer tokens.
- ⚙️ Expanded `.env` configurations in `aihub_api` and `aihub_bot` development playgrounds with default user details for local testing.
- 🧪 Included a new **HTTP test file** to simplify API token creation and testing in development.

### Changed
- 🔑 Standardized **authentication handler types** across all API controllers, ensuring consistent security practices and improved maintainability.
- 🔑 Enhanced **Agent Discovery** responses to include `stop_events`, providing more comprehensive agent lifecycle information.
- 🔑 Enhanced **`AuthenticatedUser`** to grant access to agents if the user holds the "AllAgents" role, simplifying role management.
- 🔑 Enhanced **User Service** to support a multi-strategy approach for fetching user information, integrating development, Azure AD, and API token providers.
- 🔑 Implemented **agent access control** in `ChatController`, ensuring users can only interact with agents they are authorized to use.
- ⚙️ Adjusted **thread creation endpoint** to use a cleaner root path (`/threads/`) for new threads.
- ⚙️ Configured MongoDB connection to use `ApiConfig().DB_NAME` for database name and added explicit disconnection on shutdown.
- ⚙️ Updated CI/CD configurations for `aihub_api` module, now requiring `docker-compose.yml` for testing and analysis to support new service dependencies.
- ⚙️ Modified Poetry lock file validation in CI/CD to use `poetry lock` instead of `--no-update`, ensuring lock file consistency.
- ⚙️ Updated database connection utility in pipelines to use the new `ApiConfig().DB_NAME` for consistency.
- 📄 Updated **Introduction** and **Architectural Overview** documentation to reflect the new Chatbots component and its role in the AI-Hub.
- 🌐 Redefined frontend `StartEventSpecs` to a more generic **`EventSpecs`** type, and extended `Agent` type to include `stop_events`.
- ⬆️ Updated **Poetry project versions** across all modules to `v0.54.0`.

### Fixed
- 🐛 Corrected a minor typo in `RAGAgent`'s message generation logic for few-shot rejection events.
- 🐛 Improved error handling in `AzureUserInformationProvider` by raising `ValueError` instead of a generic `Exception` for failed user info fetches.

### Removed
- 🗑️ Removed the standalone `use_oauth2_user` dependency function, integrating its logic into a new, more modular authentication handler.
- 🗑️ Deprecated `AccessToken` entity, replaced by the more comprehensive `BearerToken` for API token management.
- 🗑️ Removed deprecated `.http` test files in favor of the new, more robust Python integration test suite.

### Refactor
- 🧹 Re-architected **OAuth2 authentication** into a dedicated `OAuth2AuthHandler` module within `aihub_lib`, enhancing reusability and testability.
- 🧹 Restructured and introduced **`NoAuthHandler`** as a dedicated authentication strategy for development and testing environments, replacing the previous helper function.
- 🧹 Reorganized application configuration by replacing `BaseConfig` with new `ApiConfig` and `AzureBaseConfig` for better separation of concerns.
- 🧹 Cleaned up `.idea` project files by removing unused SonarLint module settings.
- 🧹 Applied minor formatting and style improvements across various modules, including reordering imports for better readability.
- 🧹 Streamlined docstrings in `EventPersister` and `BaseUserInformationProvider` for conciseness.
- 🧹 Updated **thread management logic** to consistently use `user.id` for user identification within threads.
- 🧹 Simplified `RefDoc` query methods and `fetch_ref_docs_to_remove` operation by removing redundant `organization_shortname` parameters.
- 🧹 Modernized **ChatBot tests** to leverage `httpx`, `asgi-lifespan`, and `requests.Session` patching for improved isolation and reliability.

---



## [v0.52.0] - 2025-02-19 - Core Service Refinements and Bot Stability

### Changed
- 🔄 **Refined conversation message retrieval:** Updated the internal type handling for conversation messages to ensure better compatibility and consistency when fetching historical chat data.
- ⚡️ **Enhanced bot conversation context:** Improved the robustness of how conversation messages are retrieved and provided to the bot's context, ensuring a reliable and standard list format is always returned.

---



## [v0.51.0] - 2025-02-19 - Unveiling the Tiered AI-Hub: Expanded Vision and Enhanced Architecture

### Added
- ✨ **Introduced Tiered AI-Hub Offering:** The AI-Hub now defines a clear four-tiered approach: Basic LLM Access, Basic+ Integrations, Custom AI Assistants, and Autonomous AI Agents, providing a structured path for AI adoption.
- 🖼️ **New Architectural Components:** Documented the addition of key architectural components including a dedicated **Bots module** (leveraging Azure Bot Framework) for seamless communication channel integration, an intuitive **Chat UI**, an **Agents Transparency Frontend** for detailed monitoring and auditing, and a **Process Panel** for visualizing human-agent workflows.
- 📄 **Dedicated LLM Access and AI Assistant Sections:** Added comprehensive explanations of direct **LLM Access** as a foundational tier and **AI Assistants** as context-aware, reactive solutions, clarifying their distinct roles within the AI-Hub ecosystem.
- ☁️ **Hosting and Deployment Details:** Included a new section outlining the on-premise hosting strategy for the AI-Hub, emphasizing data security and compliance within the customer's infrastructure.

### Changed
- 🔄 **Revamped AI-Hub Introduction:** The core introduction of the AI-Hub has been significantly rewritten to align with the new tiered service offering and emphasize its comprehensive platform capabilities, showcasing its evolution from a code repository to a multi-tiered platform.
- ⚙️ **Updated High-Level Architecture Diagram:** The architectural overview now includes the newly defined components (Bots, Chat UI, Transparency UI, Process Panel) and their interconnections, providing a clearer visual representation of the AI-Hub's comprehensive structure.
- 💡 **Refined AI Agent Explanation:** The purpose and positioning of **AI Agents** have been re-contextualized within the broader tiered framework, emphasizing their role in collaborative and autonomous process automation.

### Refactor
- 🧹 **Restructured Introduction Documentation:** The entire `1_introduction.md` file has undergone a significant organizational refactor, clarifying core concepts, improving the overall readability, and enhancing the flow of the AI-Hub's foundational documentation.

---



## [v0.50.0] - 2025-02-19 - Smarter Slack Bot Responses and Control

### Added
- ✨ **Slack Message Filtering Utilities**: Introduced new helper methods to accurately identify Slack channel messages and detect when the bot is directly mentioned in conversations.

### Changed
- 🤖 **Refined Slack Bot Interaction Logic**: Bots will now only process and respond to messages in Slack channels where they are explicitly mentioned. This change improves the relevance of bot responses and reduces noise in multi-user channels for all Agent and OpenAI bots, including their streaming variants.

### Refactor
- 🧹 **Optimized Slack Turn Context Handling**: The internal logic for processing and updating Slack turn contexts has been streamlined and simplified by integrating the new message filtering utilities, leading to cleaner and more robust Slack integration.

---



## [v0.49.0] - 2025-02-19 - Architectural Overhaul for Enhanced Bot Interactions

### Added
- ✨ **New Agent Chat Bot**: Introduced a dedicated bot (`AgentChatBot`) to handle interactions with AI agents, supporting various communication channels.
- 🚀 **Streaming Agent Chat**: Added `StreamAgentChatBot` to provide real-time, streaming responses from AI agents, significantly enhancing the user experience in supported chat platforms.
- ✨ **New OpenAI Chat Bot**: Implemented a specific bot (`OpenaiChatBot`) for direct interactions with OpenAI Large Language Models, enabling seamless chat completions.
- 🚀 **Streaming OpenAI Chat**: Enabled streaming responses for OpenAI LLMs via `StreamOpenaiChatBot`, allowing users to see responses as they are generated.
- 🦾 **Centralized Agent Chat Logic**: Created `AgentChatService` to consolidate and manage the core logic for agent chat interactions, including message processing and streaming capabilities.
- 🦾 **Centralized OpenAI Chat Logic**: Introduced `OpenaiChatService` to centralize the logic for OpenAI LLM chat completions, encompassing client management and message conversion.
- 📄 **Bot System Message Configuration**: Added a `system_message` field to `PathEntity`, enabling administrators to configure personalized system instructions for each bot endpoint.

### Changed
- 📝 **Simplified Conversation Entity**: Streamlined the `ConversationEntity` by removing user management and associated methods, focusing purely on message persistence for improved clarity and efficiency.
- 🔄 **Refactored Bot Service Core**: Overhauled the base `Service` class to centralize common bot functionalities such as adapter retrieval, system message handling, Slack-specific context updates, and conversation message persistence, resulting in more modular and maintainable bot implementations.
- ⚙️ **Enhanced Azure Bot Deployment Script**: Improved the Azure Bot setup script (`setup_azure_bot.py`) to support flexible database configurations (Cosmos DB or local MongoDB), include an option for Azure Bot SKU, and ensure idempotency by deleting existing bots before creation.

### Refactor
- 🧹 **Bot Directory Restructuring**: Reorganized the bot directory structure from a generic "chat" classification to more specific "agent" and "openai" categories, improving separation of concerns.
- 🧹 **Controller Path Restructuring**: Renamed and moved chat controllers to align with the new bot directory structure, enhancing the logical grouping and organization of API endpoints.

### Removed
- 🗑️ **Deprecated Generic Chat Bot**: Removed the generic `ChatBot` as its functionalities have been absorbed and refined by the new, specialized `AgentChatBot` and `OpenaiChatBot` implementations.
- 🗑️ **Removed Echo Bot**: The basic echo bot functionality has been deprecated and removed.
- 🗑️ **Removed Outdated Chat Services**: Replaced old, fragmented chat service implementations with new, centralized `AgentChatService` and `OpenaiChatService` classes.

---



## [v0.48.0] - 2025-02-19 - Core Updates and Testing Resilience

### Changed
- 🚀 **Updated SonarCloud GitHub Action:** Upgraded the SonarCloud scan GitHub Action to `v5` to leverage the latest features and ensure compatibility with SonarCloud analysis.
- ⚡️ **Enhanced Test Stability and Reliability:** Increased timeouts and retries in chat bot integration tests to improve robustness against service startup delays and ensure complete reception of streaming responses.

---



## [v0.47.0] - 2025-02-18 - Streamlined Azure Integrations and Configuration

### Refactor
- ✨ **Standardized Azure Subscription Identification:** Switched from using a subscription display name (`AZURE_SUBSCRIPTION_NAME`) to the more robust and standard Azure Subscription ID (GUID format) across all Azure service configurations.
- 🧹 **Streamlined Azure Resource Naming:** Removed the dependency on an explicit `ENVIRONMENT` field in default Azure resource naming conventions for services like AI Search, Cognitive Services, Cosmos DB, and Data Lake, leading to simpler and more consistent resource identification.
- 🔄 **Improved Cosmos DB Connection Management:** Refactored the internal handling of Cosmos DB connection strings, consolidating logic into the `CosmosAccess` class for enhanced maintainability.
- 📂 **Standardized Internal Module Paths:** Updated directory casing for configuration and vector store modules (e.g., `Configs` to `configs`, `vector_stores` to `stores`) to ensure consistent naming conventions throughout the codebase.

### Changed
- ⚙️ **Updated CI/CD for Azure Authentication:** Modified the `analyze-test-pr.yml` GitHub Actions workflow to pass `AZURE_SUBSCRIPTION_ID` as an environment variable, ensuring correct authentication for Azure-dependent tests.

### Added
- 📦 **Expanded Azure Data Lake Integration:** Introduced `azure-storage-file-datalake` and `adlfs` dependencies, enabling advanced interaction with Azure Data Lake Storage Gen2 for pipelines and data operations.
- 📈 **Enhanced Azure Cognitive Services Management:** Added `azure-mgmt-cognitiveservices` dependency, providing capabilities for programmatic management and interaction with Azure Cognitive Services.

---



## [v0.45.0] - 2025-02-17 - Core Component Synchronization and Build Process Refinement

### Changed
- 🔄 Synchronized **all core components** (Agent, API, Bot, Library, and Pipeline) to version `v0.45.0`, ensuring consistent internal dependency alignment across the suite.
- ⚙️ Updated **CI/CD build workflows** to allow `poetry.lock` file updates during automated runs, enhancing dependency management and freshness.

---



## [v0.44.0] - 2025-02-17 - Flexible Bot Configuration and Improved Azure Integration

### Added
- ✨ **New Bot Configuration Fields:** Introduced `APP_TYPE` and `APP_TENANTID` to the `Credentials` entity, enabling more flexible setup for various Azure Bot types, including single-tenant applications.
- 🚀 **Single-Tenant Azure Bot Support:** The `setup_azure_bot.py` script now supports creating and configuring Azure Bots for single-tenant applications via a new `--tenant-id` argument, enhancing security and deployment options.
- 🧪 **OpenAI Chat Playground Example:** Added an `OpenaiChatController` example to the local development playground, simplifying testing and integration with OpenAI chat models.

### Changed
- 🔄 **Standardized Credential Field Names:** Renamed credential fields in `PathEntity` to uppercase (`APP_ID`, `APP_PASSWORD`) for improved consistency across the application.
- 🔌 **Dynamic Adapter Retrieval:** The `get_adapter` method now accepts the full FastAPI `Request` object, allowing for more dynamic and context-aware adapter instantiation based on incoming requests across services and controllers.
- 📦 **Cosmos DB Upsert Logic:** The `setup_azure_bot.py` script now uses upsert functionality when saving credentials to Cosmos DB, ensuring idempotency and cleaner updates for bot configurations.

### Refactor
- 🧹 **API Request/Response Standardization:** Migrated controllers to use native `fastapi.Request` and `fastapi.Response` objects, streamlining API handling and improving consistency.
- ⚙️ **Flexible Echo Service Adapter:** The Echo service now dynamically retrieves its adapter per request, enabling more sophisticated multi-tenant configurations and reducing static dependencies.

### Removed
- 🗑️ **Simplified Development Environment:** Removed the `COSMOS_CONNECTION_STRING` from the local development `.env` file, streamlining local setup by relying on other configuration methods.

---



## [v0.43.0] - 2025-02-17 - Enhanced Build System and Tooling Compatibility

### Changed
- 🚀 **Upgraded Poetry Version:** The build system and CI/CD workflows have been updated to utilize Poetry version `2.1.1`, with `poetry-core` requirements adjusted to `>=2.0.0,<3.0.0` across all `pyproject.toml` files. This ensures improved compatibility, stability, and leverages the latest features in dependency management and package building.

---



## [v0.42.0] - 2025-02-17 - Core Library Refinements

### Refactor
- 🧹 **`ScoreScalerPostProcessor` Method Renamed**: Renamed the internal `process` method to `postprocess_nodes` within the `ScoreScalerPostProcessor` for improved clarity and naming consistency in generative AI utilities.

---



## [v0.41.0] - 2025-02-17 - Enhanced Azure AI Search Capabilities

### Added
- ✨ **Improved Azure AI Search Vector Store**: Added support for specifying a **semantic configuration name** when creating an `AzureAISearchVectorStore`, enabling more refined search capabilities for RAG applications.

---



## [v0.40.0] - 2025-02-14 - Dynamic Bot Authentication and Streamlined Setup

### Added
- ✨ **New `PathEntity` for Dynamic Authentication**: Introduced a new `PathEntity` in the persistence layer to store Azure Bot Service credentials (App ID, App Password) linked to specific API paths. This enables the support of multiple bot instances with distinct authentication on a single deployment.
- 🚀 **Azure Bot Setup Automation Script**: A new `setup_azure_bot.py` script has been added to automate the end-to-end process of setting up Azure Bot resources. This includes creating Azure AD app registrations, configuring Azure Bots, and persisting their credentials directly into Cosmos DB for path-based authentication.

### Changed
- 🔄 **Dynamic Bot Adapter Configuration**: The core `Service` logic has been refactored to dynamically retrieve and configure the `CloudAdapter` based on the incoming request's API path. This significantly enhances support for running multiple distinct bot instances with separate credentials within the same API application.
- 🧹 **Updated Bot Controllers for Dynamic Adapters**: All bot controllers (for Agent and OpenAI chat) now utilize the new dynamic adapter retrieval mechanism, ensuring that each bot instance correctly authenticates based on its configured API path.

### Removed
- 🗑️ **Global Bot Authentication Configuration**: The static `APP_ID`, `APP_PASSWORD`, and `APP_TENANTID` fields have been removed from `BaseConfig`, transitioning to a more flexible and scalable path-based authentication model.
- 🚫 **Generic Error Handling from Base Service**: The `on_turn_error` handler was removed from the base `Service` class, promoting more specific and context-aware error management within individual bot implementations.

### Refactor
- 🧹 **Persistence Entity Relocation**: The `ConversationEntity` and related persistence files were moved from `aihub_bot/aihub_bot/persistence/chat/entities` to a more generalized `aihub_bot/aihub_bot/persistence/entities` directory. This improves organization and lays groundwork for future expansion of persistence models beyond chat.

---



## [v0.39.0] - 2025-02-14 - Enhanced RAG Agent Context and Robust Timestamp Handling

### Changed
- 🦾 **Improved RAG Agent Rejection Handling**: The `RAGAgent` now utilizes a more comprehensive chat history when generating LLM responses for `FewShotRejectEvent` scenarios, ensuring better contextual understanding for rejection reasoning.
- ⚡️ **Refined Timestamp Utility**: Updated the `format_unix_timestamp` utility to directly accept and validate integer timestamps, enhancing the robustness and correctness of date formatting from metadata.

---



## [v0.38.0] - 2025-02-13 - Chat Bot Reliability Updates

### Fixed
- 🐛 **Improved User Message Role Assignment:** Ensured that user messages consistently default to the "user" role if not explicitly provided by the activity, enhancing message handling reliability within the `JsonOpenaiChatBot`.
- ⚡️ **Enhanced OpenAI Chat Streaming Robustness:** Added safeguards to gracefully handle and skip empty or null content chunks during OpenAI chat streaming, preventing potential interruptions and improving stability for streamed responses.

---



## [v0.37.0] - 2025-02-13 - RAG Context Revamp and Expanded Localization

### Added
- ✨ **Introduced Comprehensive RAG Document Metadata:** Enhanced RAG context documents to include rich metadata such as `namespace`, `type`, `language`, `version`, and timestamps (`created_at`, `updated_at`, `inserted_at`), providing more detailed source information.
- 🌐 **Expanded Internationalization:** Added French and Italian translations for agent guard prompts and core agent thought processes, significantly enhancing multi-language support.
- ⚙️ **Dynamic Locale Path Configuration:** Implemented a `locale_path` configuration option for agents, enabling dynamic retrieval of localized strings directly from agent configurations, improving flexibility for multi-locale workflows.

### Changed
- 🔄 **Standardized RAG Context Document Format:** The internal format for RAG context documents has been updated to a more structured `<DOCUMENT [metadata]>` tag, ensuring clearer delineation and better integration of rich metadata.
- 📄 **Improved Prompt Clarity:** Refined the `condenser.standalone_question` prompt in core libraries for improved rephrasing of follow-up questions while retaining original context.
- 🦾 **Centralized RAG Prompt Management:** RAG context prompts are now managed centrally within `aihub_lib`, ensuring consistency and simplifying prompt updates across all agents.

### Removed
- 🗑️ **Deprecated Agent-Specific Prompts:** Removed redundant RAG-related prompts from `aihub_agent` translations, as these functionalities are now consolidated and provided by the `aihub_lib` module.

---



## [v0.36.0] - 2025-02-13 - LLM Flexibility and Azure Bot Service Enhancements

### Added
- ✨ **Expanded Azure Bot Service Configuration:** Introduced new environment variables (`APP_TYPE`, `APP_TENANTID`) in the base configuration, enabling more granular control and improved integration for Azure Bot Service deployments.

### Changed
- ⚡️ **Improved OpenAI Chat Streaming Stability:** Enhanced the `OpenaiChatService` by adding an `asyncio.sleep(0)` call within the streaming loop, preventing potential blocking and ensuring smoother, non-blocking chat completions.
- 🔄 **Streamlined Self-Hosted LLM Configuration:** Made the `default_parameter` field optional in `SelfHostedLLMConfig` with an automatic default factory, simplifying the setup and configuration of self-hosted large language models.
- 🧹 **Refined Playground LLM Examples:** Updated the `playground` test environment to align with the new, more flexible LLM configuration approach, simplifying the definition of chat models and removing redundant parameters.

---



## [v0.35.0] - 2025-02-12 - Smarter Agent Interactions with New Guardrails and Core Refinements

### Added
- 🛡️ **New Few-Shot Guard Mechanism:** Introduced a powerful new guard mechanism in `aihub_lib` that allows agents, specifically integrated into the `RAGAgent`, to validate user queries against predefined few-shot examples, enhancing control over agent scope.
- ⚙️ **Configurable Few-Shot Guard Examples:** The `RAGAgentConfig` now includes a `few_shot_guard_examples` field, enabling easy configuration of allowed and disallowed query patterns.
- 💬 **Intelligent Guard Rejection Responses:** Agents can now generate specific responses when a user query is rejected by the few-shot guard, providing clear reasons to the user.
- 📄 **Convenient User Query Access:** Added a `user_query` property to `StartEvent` for easier extraction of the latest user message from the chat history.
- 📢 **New Guard-related Events:** Introduced `FewShotAcceptEvent` and `FewShotRejectEvent` to explicitly manage the workflow paths based on guard outcomes.

### Changed
- ✏️ **Flexible RAG Agent Prompts:** Made `condense_question_prompt` and `context_prompt` optional in `RAGAgentConfig`, providing more flexibility for agent prompt customization.
- 🧠 **Improved Standalone Question Condensation:** The `condense_standalone_question` utility now intelligently excludes system messages from chat history during condensation, leading to more accurate and concise standalone questions.

### Refactor
- 🧹 **Streamlined Agent Workflow Data Flow:** Reduced dependency on `RunContext` in `FewShotAgent` and `RAGAgent` by explicitly passing `StartEvent` and `LimitChatHistoryEvent` data, leading to clearer data flow and improved testability.
- 📦 **Consolidated Common Agent Components:** Moved shared events and configurations (like `LimitChatHistoryEvent` and `StandaloneQuestionCondenserEvent`) into a new `common` directory, improving modularity and reusability across agents.
- 🔄 **Standardized Prompt Location:** Relocated the `standalone_question` prompt for the condenser from agent-specific translations to the `aihub_lib` level, centralizing common prompt definitions.
- 🏷️ **Refined Event Naming:** Renamed `StandaloneQuestionCondenserEvent` to `FewShotStandaloneQuestionCondenserEvent` within the `FewShotAgent` scope for enhanced clarity and specificity.

---



## [v0.34.0] - 2025-02-11 - Introducing the AI Hub Bot Module & Internal Refinements

### Added
- ✨ **Introduced `aihub_bot` module:** A new core module dedicated to building and managing AI chatbot functionalities, enabling more robust conversational AI experiences.

### Refactor
- 🧹 **Standardized Internal Project Configurations:** Streamlined IntelliJ IDEA (`.idea`) project configurations across all modules for improved development environment consistency.
- 🔄 **Refined OpenAI Chat Service API Naming:** Renamed the `stream_on_message` method to `stream_on_message_completion` within the OpenAI Chat Service for clearer representation of its purpose and better alignment with OpenAI's API terminology.

### Removed
- 🗑️ **Removed outdated development environment file:** Cleaned up a specific `.env` file from the bot playground testing directory.

---



## [v0.33.0] - 2025-02-10 - RAG Agent Context Expansion and Testing Infrastructure

### Added
- ✨ **Introduced `VectorPrevNextPostProcessor`**: A new post-processor enabling the retrieval of adjacent (previous and next) nodes from vector stores, significantly enhancing contextual understanding for RAG agents.
- ⚙️ **Added `RetrievePrevNextConfig`**: A new configuration model to precisely control the behavior of previous and next node retrieval for RAG agents.
- 🚀 **RAG Agent Contextual Retrieval**: The RAG agent now fully supports fetching previous and next nodes based on retrieved content, improving the depth and relevance of context for generating responses.
- 🧪 **Enhanced Test Environment**: The CI/CD workflow for `aihub_lib` now includes Milvus standalone, improving the reliability and scope of vector store-related feature testing.

### Refactor
- 🧹 **Centralized Testing Utilities**: Moved common Milvus vector store content utilities to `aihub_lib/testing`, promoting code reuse and maintainability across various projects.

---



## [v0.32.0] - 2025-02-10 - Direct OpenAI Integration and Modular Bot Architecture

### Added
- ✨ **Direct OpenAI Chat Integration**: Introduced new endpoints and bot types (`JsonOpenaiChatBot`, `StreamOpenaiChatBot`) for direct interaction with OpenAI and Azure OpenAI models, supporting both JSON and streaming responses.
- 🦾 **OpenAI Chat Controllers and Services**: Added dedicated `OpenaiChatController` and `OpenaiChatService` to manage OpenAI chat completions and stream responses, facilitating easy integration of various OpenAI-compatible LLMs.
- 📄 **Centralized Azure Bot Service Configuration**: Moved `APP_ID` and `APP_PASSWORD` to `aihub_lib`'s `BaseConfig`, streamlining configuration for Azure Bot Service credentials across the application.

### Refactor
- 🔄 **Modular Chat Bot Architecture**: Restructured the `aihub_bot`'s chat module into distinct `agent` and `openai` sub-packages, enhancing modularity and separating concerns for agent-based and OpenAI-based chat functionalities.
- 🧹 **Generic Chat Bot and Service Abstractions**: Refactored the core `ChatBot` and `ChatService` classes to be more generic, removing agent-specific dependencies and moving specialized logic into their respective new `AgentChatBot` and `AgentChatService` implementations.
- 🗑️ **Removed `DefaultConfig`**: Eliminated the `DefaultConfig` class in `aihub_bot` in favor of the centralized `BaseConfig` from `aihub_lib`.

### Fixed
- 🐛 **Robust Conversation Handling**: Ensured that conversations are automatically created if they do not already exist when adding new messages, preventing potential errors during the first interaction.
- ⚡️ **Improved Bot Role Fallback**: Added a fallback mechanism to default the recipient's role to "bot" if it's not explicitly defined in an activity, improving robustness in message handling.
- ⏱️ **Adjusted Stream Timeout**: Increased the timeout for streaming chat responses to prevent premature disconnections during longer AI generation processes.

---



## [v0.31.0] - 2025-02-07 - Enhanced Tracing with Phoenix Authentication

### Added
- ✨ **Added `PHOENIX_AUTH_TOKEN` Configuration:** Introduced a new optional configuration setting, `PHOENIX_AUTH_TOKEN`, allowing users to provide an authentication token for the Phoenix tracing endpoint.
- 🔑 **Enhanced Phoenix Tracing Authentication:** Integrated support for sending authentication tokens with trace data to the Phoenix endpoint, improving security and access control for trace submissions.

---



## [v0.30.0] - 2025-02-07 - Core Updates and Streamlined Message Events

### Changed
- 🔄 **Streamlined `UserMessageEvent` handling:** The internal construction of `UserMessageEvent` now uniformly uses the complete message list, simplifying how chat messages are processed and passed within events.

---



## [v0.29.0] - 2025-02-07 - System Enhancements and Configurability

### Changed
- ⚙️ **Improved Bot NATS Configuration**: The `aihub_bot` service now dynamically resolves its NATS endpoint using `NatsConfig`, enhancing deployment flexibility and external configuration.
- 📄 **Expanded Semantic PR Type Coverage**: The semantic pull request workflow has been updated to include `bots` as a recognized change type, streamlining PR categorization for bot-related contributions.

---



## [v0.28.0] - 2025-02-07 - Enhanced Generative AI Capabilities with OpenAI API Emulation

### Added
- ✨ **OpenAI API Emulation**: Introduced a comprehensive OpenAI-compatible API layer in `aihub_api`, allowing seamless integration with OpenAI SDKs for various generative AI tasks.
- 🖼️ **Image Generation Support**: Added configuration and API endpoints for DALL-E image generation models, enabling image creation via the new OpenAI API.
- 🎙️ **Speech-to-Text (STT) Functionality**: Integrated support for transcribing audio into text, complete with Azure OpenAI STT model configurations and a dedicated API endpoint.
- 🔊 **Text-to-Speech (TTS) Functionality**: Implemented capabilities for generating audio from text, including Azure OpenAI TTS model configurations and a new API endpoint.
- 📄 **Open WebUI Docker Compose Example**: Provided a `docker-compose` file to demonstrate how to integrate AI Hub with Open WebUI, leveraging the new OpenAI API emulation.
- 📦 **New Dependencies**: Added `llama-index-embeddings-text-embeddings-inference` and `python-multipart` to support the expanded generative AI functionalities.

### Changed
- 💡 **Default Model Parameters**: Adjusted default parameters for Azure OpenAI LLMs and Embedding models, and Self-Hosted LLMs, to provide more robust and sensible initial configurations.
- 📚 **Documentation Updates**: Updated documentation to reflect the new `base_url` parameter and general changes stemming from the generative AI resource refactoring.

### Refactor
- 🔄 **Generative AI Resource Unification**: Restructured the core `generative_ai` modules in `aihub_lib` to introduce a more generic and extensible `resources` hierarchy, consolidating LLM, embedding, image, STT, and TTS configurations under a unified system.
- 🧹 **Standardized Resource Configuration**: Introduced new base classes like `ResourceConfig` and `AzureOpenaiResourceConfig` to standardize how generative AI models are configured, improving modularity and maintainability across all resource types.
- ⚙️ **Updated Model Parameter Handling**: Renamed and refactored model parameter classes (e.g., `ModelParameter` to `LLMModelParameter`) and adjusted default parameter handling to align with the new resource configuration system.
- ♻️ **Consistent API Endpoint Naming**: Standardized `api_endpoint` to `base_url` across model configurations for better consistency and clarity.

---



## [v0.27.0] - 2025-02-06 - Real-time Chat Streaming and Modular Bot Architecture

### Added
- ✨ **New Streaming Chat Capabilities:** Introduced `StreamChatBot` and a new `/completions/{agent_class}/{agent_id}/stream` endpoint, enabling real-time, chunked responses from AI agents.
- 📄 **Dynamic Activity Model Generation:** Added `activity_model.py` to dynamically create Pydantic models for Bot Framework activities, enhancing OpenAPI documentation and request validation.

### Changed
- 🚀 **Refined Chat Bot Architecture:** The base `ChatBot` has been refactored to be more generic, with synchronous `on_message_activity` logic moved to a new `JsonChatBot` subclass.
- ⚡️ **Improved API Documentation:** Enhanced the OpenAPI documentation for chat completion endpoints (`/completions`) with clearer summaries, descriptions, and response examples.
- 🔄 **Bot Test Runner Updates:** The `BotTestRunner` now supports `PUT` requests on the service endpoint, which is essential for processing activity updates used in streaming responses.

### Refactor
- 🧹 **Modularized Chat Bot Implementations:** Split the `ChatBot` functionality into a base class and two specialized subclasses (`JsonChatBot` and `StreamChatBot`) to improve code organization and support different chat interaction types.

---



## [v0.26.0] - 2025-02-06 - Enhanced Event Management and Data Integrity

### Changed
- 🔄 **Refactored Distributed Event Storage:** The `DistributedEventStore` now dynamically deserializes events by their class name, improving flexibility and extensibility by removing the need for pre-registered event types during retrieval.
- ⚡️ **Improved Event Store Robustness:** Enhanced error handling in the `DistributedEventStore` includes specific handling for `KeyNotFoundError` and comprehensive logging for better operational insights.

### Fixed
- 🐛 **Corrected Nested Event Serialization:** Ensured that nested `BaseEvent` instances are properly serialized within parent events when using `model_dump`, preventing data loss for complex event structures.

---



## [v0.25.0] - 2025-02-06 - Test Suite Streamlining

### Refactor
- 🧹 **Streamlined Multistep Human-in-the-Loop Agent Tests:** Refactored the tests for the `MultistepHumanInTheLoopAgent` from a `pytest-bdd` driven approach to a standard, more direct `pytest.mark.asyncio` test structure, enhancing test readability and maintainability.

### Removed
- 🗑️ **Deprecated Multistep Human-in-the-Loop Feature File:** Eliminated the `multistep_human_in_the_loop_agent.feature` file, aligning with the refactoring of its corresponding Python test to a standard `pytest` format.

---



## [v0.24.0] - 2025-02-06 - Unified Core Release and CI/CD Streamlining

### Changed
- 🚀 **Unified Component Versioning**: All core `aihub` components, including `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline`, have been updated to a synchronized `v0.24.0` release. This ensures consistent versions and improved compatibility across the entire ecosystem.

### Refactor
- ⚙️ **Streamlined CI/CD Test Workflow**: The pull request analysis and testing workflow has been refactored to utilize a local, self-contained `test_backend` action. This change enhances the reliability and maintainability of our continuous integration pipelines.

---



## [v0.23.0] - 2025-02-05 - Paving the Way for Chatbots: New Bot Service and Core Refinements

### Added
- ✨ **New `aihub_bot` Microservice**: Introduced a dedicated microservice for integrating AI Hub agents with external chatbot platforms, starting with Azure Bot Service.
- 🤖 **ChatBot and EchoBot Implementations**: Provided initial bot implementations for conversation handling (`ChatBot`) and basic interaction testing (`EchoBot`) within the `aihub_bot` service.
- 💬 **Conversation Persistence**: Added `ConversationEntity` to the `aihub_bot` service, enabling persistent storage and retrieval of chat history for contextual bot interactions.
- 🛠️ **Bot Testing Utilities**: Included `BotTestRunner` and `SimulatedAgentBotTestRunner` to facilitate robust testing of bot functionalities and simulated agent responses.

### Refactor
- 🔄 **Core Library Consolidation**: Key components such as `AuthenticatedUser`, `Controller` base classes, NATS dependencies, and WebSocket receiver logic were extracted from `aihub_api` into `aihub_lib`. This enhances reusability and modularity across microservices.
- 📦 **Centralized Chat Service Logic**: The fundamental `ChatService` logic for handling chat interactions (streaming, JSON responses, event aggregation) has been moved from `aihub_api` into `aihub_lib`, providing a unified chat interface for various frontends.
- 🗄️ **Unified Development Environment Configuration**: Moved `docker-compose.yml` files to the repository root, centralizing local development environment setups for `aihub_agent`.

### Changed
- 🚀 **API Service Adaption**: The `aihub_api` service has been updated to utilize the newly centralized components from `aihub_lib`, streamlining its architecture and reducing internal redundancy.
- ✅ **CI/CD Pipeline Expansion**: Expanded GitHub Actions workflows (`add-tag`, `analyze-test-pr`, `lint-pr`, `semantic-pr`) and the `Makefile` to include support for the new `aihub_bot` microservice, ensuring comprehensive testing and linting.
- 🛡️ **Improved Thread Authorization Error Handling**: Standardized and improved error handling for unauthorized thread access and modification in `aihub_api`'s `ThreadController`.
- ⚙️ **Updated Test Backend Action**: Modified the `aihub_action/test_backend` to enhance its flexibility by removing rigid working directory requirements.

---



## [v0.22.0] - 2025-02-04 - Streamlined Development Workflows

### Changed
- ⚙️ **Updated CI/CD Workflows**: Migrated core GitHub Actions for testing, linting, code coverage, and pull request reviews from a temporary `hotfix` branch to the stable `main` branch, ensuring more consistent and reliable development processes.

---



## [v0.21.0] - 2025-02-04 - Streamlined CI/CD Workflows and Enhanced Test Management

### Added
- ✨ **New Reusable GitHub Actions:** Introduced a dedicated `aihub_action` module containing a suite of reusable GitHub Actions for common CI/CD tasks, including backend testing, linting (Python and JavaScript), SonarCloud scanning, and AI-assisted pull request review. This centralizes and standardizes workflow definitions across the repository.
- 🏷️ **Enhanced Pytest Markers:** Implemented new Pytest markers (`azure`, `self_hosted`, `slow`, `integration`, `experimental`) and enforced strict marker usage in backend modules, allowing for more granular control and organization of tests.

### Refactor
- 🔄 **Centralized CI/CD Workflows:** Migrated existing `.github/workflows` for testing, linting, and pull request review to utilize the newly introduced reusable GitHub Actions, significantly improving maintainability, consistency, and reusability of CI/CD logic.
- 🧹 **Consolidated SonarCloud Scanning:** Unified SonarCloud analysis for all modules (including `aihub_web`) under a single, streamlined workflow definition within the new reusable actions, enhancing code quality gate management.

---



## [v0.20.0] - 2025-02-03 - Introducing Few-Shot Agent and Core Library Modernization

### Added
- ✨ **New Few-Shot Agent:** Introduced a `FewShotAgent` that leverages few-shot examples and a new agent description guard to generate LLM responses, providing a powerful pattern for structured and constrained outputs.
- 🛡️ **Agent Description Guard:** Added a new `agent_description_guard` utility to validate user queries against an agent's intended description, preventing out-of-scope requests and improving agent relevancy.
- 📄 **Few-Shot Prompting Utilities:** Implemented new `FewShotExample` and `create_few_shot_messages` utilities to streamline the creation of few-shot prompts for LLMs, enhancing agent prompt engineering capabilities.
- 🛑 **Guard Rejection Event:** Introduced `GuardRejectionEvent` to clearly signal when a user request is rejected by an agent's guard, including the reason for rejection.
- 📊 **OTLP Exporter for Tracing:** Added support for OTLP (OpenTelemetry Protocol) exporter, enabling more flexible and standardized trace data export to various monitoring systems.
- 🧪 **Few-Shot Agent Playground Examples:** Provided new playground examples and BDD tests to demonstrate the implementation and testing of the `FewShotAgent` workflow.

### Changed
- ⚙️ **Refined Test Execution Filters:** Updated the test execution command in the `Makefile` to use a more flexible filter (`-k "not azure"`), allowing specific tests (e.g., non-Azure dependent tests) to be easily excluded from runs.

### Refactor
- 🔄 **Centralized Agent Configuration:** Relocated `AgentConfig` and `StepConfig` from `aihub_lib.generative_ai.agent` to the more general `aihub_lib.agents` module, streamlining configuration definitions across the system and improving module organization.
- 🧹 **Relocated Event Displayer:** Moved the `EventDisplayer` component from `aihub_agent` to `aihub_lib` to consolidate common display utilities within the core library, improving reusability and reducing redundant code.
- 🛠️ **Unified Workflow Decorators:** Standardized workflow decorators by moving the `@step` decorator from `aihub_agent.workflow.decorators` to `aihub_lib.workflow.decorators`, centralizing workflow annotations and simplifying agent development.
- ✏️ **Renamed Document Intelligence Content Format:** Updated the `ContentFormat` enum to `DocumentContentFormat` within `DocumentIntelligenceLoader` for improved clarity and consistency with Azure SDKs.
- 🚫 **Streamlined Tracing Implementation:** Removed explicit `@tracing()` decorators from `DocumentIntelligenceLoader` and `RawLoader`, indicating an internal improvement in how tracing is managed and applied to these components.

---



## [v0.19.0] - 2025-01-31 - Unified Version Release

### Changed
- 🔄 **Core Component Version Alignment:** All core packages (`aihub_agent`, `aihub_api`, `aihub_lib`, and `aihub_pipeline`) have been updated and synchronized to version `v0.19.0`, ensuring compatibility and consistency across the ecosystem.

---



## [v0.18.0] - 2025-01-31 - Internal Workflow Streamlining

### Refactor
- 🧹 **Refined Tagging Workflow Cleanup:** The GitHub Actions workflow for tag creation has been streamlined by relocating the SSH key cleanup step to execute after all Git operations are complete, ensuring a more robust and logical cleanup sequence.

---



## [v0.17.0] - 2025-01-31 - Unleashing Agent-in-the-Loop: Smarter Delegation & Flexible RAG

### Added
- 🦾 **Agent-in-the-Loop (AITL) Delegation:** Introduced a powerful new mechanism allowing agents to delegate tasks to other specialized agents within a workflow, fostering complex, collaborative AI systems.
- ⚙️ **Milvus Vector Store Integration:** Added support for Milvus as a vector store option for RAG (Retrieval-Augmented Generation) agents, enhancing flexibility in data storage choices.
- ✨ **Self-Hosted LLM and Embedding Support:** Expanded the RAG agent's capabilities to utilize self-hosted Large Language Models (LLMs) and Embedding models (e.g., via `llama.cpp` and Hugging Face's Text Embeddings Inference), enabling greater control and cost-efficiency.
- 📄 **NATS Configuration Centralization:** Introduced `NatsConfig` in `aihub_lib` to centralize and simplify the management of NATS endpoint configurations across microservices.
- 🧪 **Comprehensive Workflow Test Coverage:** Added new BDD feature files and tests for conditional, context, fan-out, multi-locale, multi-step Human-in-the-Loop (HITL), semantic event, and Agent-in-the-Loop (AITL) workflows, significantly improving test reliability and demonstrating agent capabilities.
- 🚀 **PyCharm Project Configuration:** Included `.idea` files for core, agent, API, lib, and pipeline modules, providing out-of-the-box PyCharm project setup for improved developer experience.

### Changed
- 🔄 **Generalized LLM and Embedding Configurations:** Refactored `RAGAgentConfig` and `RetrieveStepConfig` to use more generic `ChatLLMConfig` and `EmbeddingLLMConfig` interfaces, promoting a backend-agnostic approach to LLM and embedding integration.
- ⚡️ **Flexible Node Retrieval:** Overhauled the node retrieval logic to directly interact with various vector stores, removing previous `llama_index.core` dependencies and enhancing adaptability.
- 💬 **Improved Tokenizer Handling:** Updated chat history limitation utility to accept a direct tokenizer function, providing more flexible and accurate token counting for diverse LLMs.
- 📈 **Robust Docker Compose Health Checks:** Enhanced Docker Compose configurations for NATS and MongoDB with more reliable health checks, improving local development environment stability.
- 🐳 **Shifted Local LLM Setup:** Replaced the `ollama` Docker service with `llama.cpp` and `hf-TEI` (Text Embeddings Inference) for local self-hosted LLM and embedding testing, offering a more modular local AI development environment.
- 📝 **API `base_url` for LLM Configurations:** Renamed `api_endpoint` to `base_url` across LLM and Embedding configurations for consistency and clarity.
- 📖 **Updated README Instructions:** Refreshed documentation to include steps for adding `aihub_lib` as a dependency and updated Docker Compose commands to reflect recent changes.
- 🪚 **Refined Test Coverage Scope:** Modified `Makefile` targets to apply test coverage reporting broadly across each microservice directory, improving accuracy.
- 🪵 **Enhanced Event Logging:** Implemented more detailed event logging for NATS publishers and base events, including recursive deserialization, which aids in debugging and monitoring.

### Refactor
- 🧹 **IDE Project Structure:** Reorganized `.idea` files for better multi-module project handling in IDEs like PyCharm, streamlining development workflows.
- 🧩 **Standardized Test Runner Utilities:** Improved `AgentTestRunner` methods for starting and stopping test runs, providing more control and consistency for asynchronous testing.

---



## [v0.16.0] - 2025-01-22 - Empowering Self-Hosted LLMs and CI/CD Pipelines

### Added
- ✨ **New Agent Test Utility**: Introduced a `get_start_event` method in `AgentTestRunner` for easier retrieval and testing of the initial `StartEvent` within agent test scenarios.
- ⚙️ **Monorepo Poetry Configuration**: Added a root `pyproject.toml` file to centralize and streamline Poetry dependency management across all sub-packages in the monorepo.
- 🐳 **Ollama Support in Development Environment**: Integrated the Ollama service into `aihub_agent`'s `docker-compose.yml`, simplifying local development and testing with self-hosted Large Language Models.
- 🧪 **Self-Hosted LLM Testing in CI**: Introduced new CI steps to automatically pull the `Qwen2.5` model for `aihub_agent` tests, enabling comprehensive and automated testing with self-hosted language models.
- 🚀 **Displaying Agent Workflow Example**: Added a new `DisplayingAgent` workflow example, complete with BDD tests, to demonstrate how agents can emit various event types like `ThoughtEvent` and `ChunkEvent` for enhanced user feedback.
- 📄 **Llama Index Agent Test Coverage**: Included comprehensive BDD tests for the `LlamaIndexAgent`, ensuring robust functionality and interaction with configured Large Language Models.
- 📦 **New Core Dependencies**: Added `llama-index-llms-openai-like` and `transformers` to `aihub_lib`'s dependencies, enabling broader compatibility and functionality with self-hosted and OpenAI-like LLMs.

### Changed
- 🛠️ **Automated Tagging Workflow Enhancements**: Improved the `add-tag.yml` GitHub Actions workflow for increased reliability and flexibility, including explicit Git user configuration, refined directory parsing, and manual trigger support.
- ⚡️ **CI/CD Testing Pipeline Robustness**: Enhanced the `analyze-test-pr.yml` workflow to include waiting for the Ollama service, standardized Git authentication, and robust global/local Poetry dependency management for more consistent and reliable test environments.
- 🔄 **Flexible Self-Hosted LLM Tokenizer Configuration**: Updated `SelfHostedLLMConfig` to allow specifying a separate `tokenizer_name`, providing greater flexibility when integrating and configuring self-hosted LLMs.
- 💡 **Expanded Llama Index Agent LLM Options**: Modified `LlamaIndexAgentConfig` to support both `SelfHostedLLMConfig` and `AzureOpenAILLMConfig`, allowing agents to seamlessly switch between different LLM providers based on configuration.
- Example: 🔄 **Updated Llama Index Agent Trigger**: The example `trigger.py` for `LlamaIndexAgent` now defaults to using a self-hosted LLM (Qwen2.5), showcasing the new flexible LLM configuration.

### Removed
- 🗑️ **Deprecated Service Start Script**: The `start_service.sh` script has been removed, as project initiation and service management are now handled by Poetry or other standardized methods.

---



## [v0.15.0] - 2025-01-21 - CI/CD Workflow Stability Improvements

### Changed
- ⚡️ **Improved CI/CD Workflow Triggering**: Refined the conditions for the Pytest coverage comment job in pull requests to ensure it runs more reliably and only on relevant events, enhancing build process stability.

---



## [v0.14.0] - 2025-01-21 - Enhanced Automation & Core System Overhaul

### Added
- 🚀 **Automated Draft PR Creation:** A new GitHub Actions workflow has been introduced to automatically create draft pull requests upon new branch creation, streamlining the initial development process.
- 🧪 **Comprehensive Test Coverage Reporting:** Integrated `pytest-cov` and new `make test-cov` targets across all Python modules (`aihub_agent`, `aihub_api`, `aihub_lib`, `aihub_pipeline`) to generate detailed test coverage and JUnit XML reports.
- 👁️ **Agent Discovery Test Utilities:** Enhanced the `AgentTestRunner` with new capabilities to observe agent discovery events and a `wait_for_event` utility, enabling more robust and reliable agent testing.
- 📄 **Detailed Package Management Documentation:** Extensive documentation has been added to `README.md` explaining the project's package structure, the mechanisms for local versus remote dependency referencing, and deployment considerations.
- ✨ **New & Refactored Agent Workflow Examples:** Introduced new and improved examples for configured, discoverable, human-in-the-loop, and optional agent workflows within the `aihub_agent` playground, enhancing clarity and demonstrating advanced patterns.
- 🌐 **Frontend Linting Workflow:** A dedicated GitHub Actions workflow has been implemented to lint the `aihub_web` frontend using ESLint, ensuring code quality and consistency.
- 🌍 **Internationalization Placeholders:** Added new empty translation files for French (fr) and Italian (it) in `aihub_lib` to prepare for future internationalization efforts.

### Changed
- 🔄 **Centralized `aihub_lib` Dependency Management:** All Python modules (`aihub_agent`, `aihub_api`, `aihub_pipeline`) now reference `aihub_lib` via a Git tag directly from the GitHub repository instead of a local path, ensuring consistent and reproducible builds.
- ⚙️ **CI/CD Workflow Logic:** Updated pull request triggering events to include `ready_for_review` and added conditions to skip certain CI checks (e.g., semantic linting, AI code review) for draft PRs, optimizing CI pipeline execution.
- ⬆️ **Nuxt.js Configuration Updates:** Applied various updates to the Nuxt.js configuration in `aihub_web`, including enabling `ssr: false`, setting a `compatibilityDate`, and integrating the `@nuxt/eslint` module.
- 🛠️ **Local Development Dependency Switching:** The `switch_dependency.py` script now explicitly sets `develop=True` when configuring local `aihub_lib` paths, improving the local development experience with editable installs.

### Refactor
- 🧹 **Unified CI/CD Testing & Analysis:** Consolidated separate SonarCloud scan jobs into a single, matrix-based workflow and restructured test execution for all Python modules, significantly streamlining the CI pipeline.
- ♻️ **Automated Version Bumping Workflow:** The version tagging and `pyproject.toml` update workflow has been re-architected to automatically increment versions, apply changes across all relevant modules, and push tags more reliably.
- 📝 **Consolidated Python Linting:** The Python linting workflow has been refactored to use a matrix strategy, applying `black` consistently across `aihub_agent`, `aihub_api`, `aihub_lib`, and `aihub_pipeline` more efficiently.
- 📦 **Agent Example Restructuring:** The `discovery_workflow` directory has been renamed to `discoverable_workflow`, and internal event names and structures within the `configured_workflow` and `optional_workflow` examples have been updated for improved clarity and consistency.
- 🏗️ **Web Build System Modernization:** The `tailwind.config.js` file has been migrated to `tailwind.config.mjs` to adopt ES Module syntax, aligning with modern JavaScript best practices.

### Removed
- 🗑️ **Deprecated Simple Agent Tests:** Outdated simple agent playground tests have been removed, as their functionality is now covered by the more comprehensive and refactored workflow examples.

---



## [v0.13.0] - 2025-01-17 - Workflow Debugging and Type System Refinements

### Added
- 📄 **Enhanced Step Decorator Debugging**: Introduced comprehensive debug logging within the `step` decorator to provide clearer insights into how workflow steps are configured and processed, aiding in development and troubleshooting.
- ⚡️ **Enabled Playground Workflow Logging**: Activated detailed logging for a minimal workflow example, making it easier to trace execution and debug behavior in development environments.

### Refactor
- 🔄 **Refined `FixedList` and `ListOfSize` Type Handling**: Improved the internal mechanism for identifying and extracting event types from fixed-size list annotations, making the type system more robust and reliable.

---



## [v0.12.0] - 2025-01-17 - Streamlined Developer Setup and Configuration

### Changed
- ⚙️ **Enhanced Backend Service Setup:** Updated the **README** to provide a clearer, more robust PyCharm setup guide for backend microservices. The new instructions recommend attaching individual microservice folders (`aihub_api`, `aihub_lib`, etc.) as separate projects within the main workspace, each with its own isolated Poetry environment, improving dependency management and overall development experience.

### Removed
- 🗑️ **Deprecated IDE Run Configurations:** Removed outdated **IntelliJ/PyCharm run configurations** (`.run/` files) as the new recommended project setup outlined in the README simplifies and standardizes the development environment.

---



## [v0.11.0] - 2025-01-16 - Introducing AI-Hub Agents and Enhanced RAG Capabilities

### Added
- ✨ **Introduced AI-Hub Agents Framework:** A foundational new module (`aihub_agent`) providing a robust framework for developing general-purpose AI agents with predefined, workflow-driven steps, events, and configurations.
- 🦾 **New Retrieval-Augmented Generation (RAG) Agent:** Shipped a powerful RAG agent capable of processing user input, retrieving relevant information from knowledge bases, condensing questions, and generating context-aware responses.
- 🧰 **Comprehensive Generative AI Utilities:** Added several core utility functions within `aihub_lib/generative_ai/utils` to support advanced LLM workflows, including:
    - 📄 **Contextual Node Combination:** A utility to combine retrieved nodes in a structured, ordered manner, enhancing the relevance of contextual information provided to LLMs.
    - 💬 **Standalone Question Condensation:** A utility to rephrase follow-up questions into standalone queries, improving retrieval accuracy in conversational contexts.
    - 📏 **Dynamic Chat History Limiting:** Utilities to manage and limit chat history based on token counts, optimizing cost and preventing context overflow for LLM interactions.
    - 🔍 **Efficient Node Retrieval:** A dedicated utility for retrieving relevant nodes from vector stores, incorporating advanced filtering and querying options.
- ⚙️ **Score Scaling Post-Processor:** Implemented a new `ScoreScalerPostProcessor` in `aihub_lib` to normalize retrieval scores, ensuring consistent relevance ranking.
- 🧪 **Expanded Agent Testing Capabilities:** Enhanced the `AgentTestRunner` with improved event observation, enabling more comprehensive and reliable testing of agent workflows.
- 🌐 **Internationalization Support for Agents:** Added new localized prompts and thought messages, providing better multi-language support for agent interactions.
- 🏗️ **Automated Build and Quality Checks:** Integrated the new `aihub_agent` and `aihub_api` modules into the top-level Makefiles, enabling comprehensive linting, formatting, type-checking, and `pr-ready` checks across all core components.

### Changed
- 🛠️ **Refined Dispatcher Logic:** Improved the core `Dispatcher` in `aihub_agent` for more robust handling of step parameters, event readiness, and run context management, leading to more reliable agent execution.
- ⚡ **Event System Enhancements:** Updated the event handling logic within `aihub_lib/nats/events`, including an improved `RetrieverEvent` creation from `llama-index` nodes for smoother data flow.
- 🧹 **Standardized Code Formatting and Linting:** Unified `ruff`, `isort`, and `black` configurations across all `pyproject.toml` files, ensuring consistent code style and higher code quality.

### Refactor
- 🗑️ **Streamlined Imports:** Cleaned up import statements across various modules in `aihub_agent` and `aihub_lib` for better code organization and readability.
- 📈 **Updated Dependency Versions:** Aligned and updated several key dependencies, including `llama-index` related packages, to leverage the latest features and improvements.
- 📄 **Improved Docstrings and Pydantic Descriptions:** Enhanced clarity and detail in docstrings for agent classes, workflow steps, and Pydantic field descriptions, providing better developer guidance.

---



## [v0.10.0] - 2025-01-16 - Enhanced Repository Guidelines

### Added
- 📄 **Introduced comprehensive Branch Protection Guidelines:** Added a new section to the `README.md` detailing the branch protection rules for `main` and `initiative/*` branches. These guidelines cover restrictions on direct pushes, deletions, and force pushes, and enforce linear history and mandatory pull requests with specific approval and squash merge policies to ensure codebase stability and integrity.

---



## [v0.9.0] - 2025-01-16 - Improved Setup Instructions

### Added
- 📄 **Enhanced Windows Prerequisite Guidance:** Added clear instructions in the `README.md` for Windows users on how to install and configure `make`, streamlining the development environment setup.

---



## [v0.8.0] - 2025-01-15 - Enhanced Setup Documentation

### Changed
- 📄 **Improved Docker Setup Guide:** Added important troubleshooting information and a reference link to the `README.md` for resolving common Docker Desktop WSL update issues, streamlining the initial setup process.

---



## [v0.7.0] - 2025-01-15 - Streamlined Development Experience and Setup

### Added
- ✨ **Developer Run Configurations:** Introduced pre-configured IntelliJ IDEA run configurations for **`LLMWrappingAgent`**, **`core-api development`**, and **`core-api testing`**, significantly streamlining local environment setup and service startup for developers.
- 📄 **Local Development Environment File:** Included a default **`.env`** file for **`aihub_api`** development, simplifying the initial local configuration for new contributors.

### Changed
- 📦 **Monorepo-Style Dependency Management:** Updated **`aihub_pipeline`** to reference **`aihub_lib`** as a local path dependency, facilitating a more integrated and faster development workflow when working on inter-package changes.

### Refactor
- ⚡️ **Standardized Service Startup Script:** Introduced a common **`start_service.sh`** script to centralize and simplify the initiation process for various **AI Hub** microservices, improving consistency and ease of use.

---



## [v0.6.0] - 2025-01-13 - Enhanced Agents and Streamlined Workflows

### Added
- 🦾 **Introduced `LLMWrappingAgent`**: A new foundational agent designed for directly interacting with Large Language Models, simplifying LLM integration into agent workflows.
- 📄 **New Testing Documentation**: A comprehensive "Testing" section has been added to the `README.md`, detailing the project's approach to `pytest` and behavior-driven development with `pytest-bdd`.
- ⚡️ **Dedicated Playground Triggers**: New `trigger.py` scripts have been added for various playground examples, simplifying the process of initiating and testing agent workflows.

### Changed
- 🔄 **Revamped Project Structure**: Significant reorganization of the `aihub_agent/playground` and `aihub_api/playground` directories into more structured and descriptive categories (`minimal_workflow`, `agent`, `development`, `testing`), enhancing clarity and maintainability.
- ⚙️ **Formalized LLM Integration Agent**: The experimental `DevAgent` has been formalized and renamed to `LLMWrappingAgent`, along with its configuration, providing a clearer and more general purpose for a basic LLM interaction agent.

### Refactor
- 🧹 **Consolidated Playground Examples**: All individual agent and API examples from the `playground` root have been meticulously moved into logical, nested directories, creating a more organized and intuitive layout for developers.
- 🌐 **Standardized Workflow Execution**: Replaced various `main.py` entry points for playground examples with consistent `run.py` (for infinite runners) and `trigger.py` (for single-shot execution) scripts, improving development consistency.

### Removed
- 🗑️ **Outdated Playground Agent Implementations**: Deprecated and unstructured agent examples, along with their associated entry point scripts, have been removed from the `playground` root as part of the comprehensive refactoring.
- 🗑️ **Redundant API Playground Entrypoints**: Various `main.py` files previously used for API playground examples have been removed, superseded by the new consolidated `development` and `testing` directories and their respective entry points.

---



## [v0.4.0] - 2025-01-07 - Enhanced Developer Experience and Quality Assurance

### Added
- 🚀 **Implemented Comprehensive CI/CD Workflow:** Introduced a new GitHub Actions workflow to automatically analyze and test code on every pull request and push to main, ensuring higher code quality and faster feedback loops.
- 🔑 **Integrated SonarCloud for Code Quality:** Added SonarCloud configuration across all core modules (Agent, API, Lib, Pipeline, Web) to enable continuous code quality and security analysis.

### Changed
- 📄 **Revamped Developer Documentation:** Completely overhauled the `README.md` to provide an in-depth developer introduction, comprehensive getting started guide, detailed repository structure, project management, and branching strategy, significantly improving developer onboarding and clarity.
- ⬆️ **Updated Core Module Versions:** Bumped the version of core modules, including **`aihub_lib`** and **`aihub_pipeline`**, to `v0.4.0` to align with the latest release.

---



## [v0.2.0] - 2025-01-07 - Enhanced Context Management and Pipeline Reliability

### Changed
- 📄 Clarified **Human-in-the-Loop (HITL)** behavior in the documentation, detailing that **RunContext** remains active during pauses and emphasizing the utility of both **RunContext** and **ThreadContext** for maintaining state during human interventions.
- 🚀 Improved **`aihub_lib` dependency management** for the `aihub_pipeline` by switching from a local path reference to a precise Git tag, enhancing build consistency and reliability.

---



