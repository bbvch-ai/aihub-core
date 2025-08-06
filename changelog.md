# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.235.0] - 2025-08-06 - Python 3.13 Upgrade and Enhanced License Management

### Added
- 📄 **Introduced Comprehensive License Management**: A new framework to automatically scan and report on all third-party licenses across Python, Node.js, and Docker components, generating the `LICENSES.md` file to enhance transparency and compliance.
- ⚙️ **New `make license-check` Target**: Added a Makefile target and GitHub Actions job to easily trigger the license scanning and report generation process as part of continuous integration.

### Changed
- 🚀 **Upgraded Python to Version 3.13**: All backend services (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`) and associated development environments/GitHub Actions have been updated to utilize Python 3.13, leveraging the latest language features and performance improvements.
- 🛠️ **Updated Python Tooling Configurations**: Development tools such as Ruff and Black have been configured to align with Python 3.13, ensuring consistent code formatting and linting practices.
- 🔗 **Streamlined Monorepo Dependency Management**: Python packages within the monorepo now use local path references (`path = "..."`, `develop = true`) instead of Git tags, simplifying local development and cross-project dependency resolution.
- ✨ **Improved Python Type Hinting**: Refined `AsyncGenerator` type hints in Python code for better clarity and compatibility with Python 3.11+ features, removing the need for `typing_extensions.override`.
- 🧪 **Adjusted PyCharm Test Runner Configurations**: Updated IntelliJ/PyCharm run configurations to explicitly use `pytest` as the test factory, improving test execution reliability within the IDE.
- 📦 **Added Python 3.13 Compatibility Shim**: Included `audioop-lts` in `aihub_api` to ensure audio processing compatibility with Python 3.13, which removed the native `audioop` module.
- 🌐 **Renamed Web Project Package**: The `aihub_web` package name in `package.json` was updated for internal consistency.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction**: Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service**: Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration**: Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients**: Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🚀 **Implemented Dagster Build & Release Workflow**: A new GitHub Actions workflow has been added to automate the Docker image build and release process for Dagster, enabling triggers from new tags, manual dispatch, and specific feature branches.
- 🚀 **Implemented Pipelines Build & Release Workflow**: A new GitHub Actions workflow has been added to automate the Docker image build and release process for pipelines, enabling triggers from new tags, manual dispatch, and specific feature branches.
- 🛠️ **Added IDE Run Configurations**: New IntelliJ IDEA run configurations have been added for directly building Docker images for `aihub_pipeline` and `default_rag_pipeline` from their respective Dockerfiles, simplifying local development.
- ✨ **Added `StartEvent.from_raw_data` Factory**: Implemented a new class method `from_raw_data` for `StartEvent`, providing a standardized way to construct the event from raw input data, user identity, and agent configuration.
- ⚡️ **Added `ProcessInstanceDiscoveryResponseEvent`**: Introduced a new event specifically for responses to process instance discovery requests, detailing the process ID and its specific configuration.
- ✨ **Enhanced `ProcessStartEvent` with Configuration**: Added a `process_config` field and a `from_raw_data` factory method to `ProcessStartEvent`, enabling explicit configuration during process initiation.
- 🛠️ **Introduced `AgentClassTopic`**: Added a new NATS topic model representing events scoped to an agent *class*, distinct from specific agent instances, enabling more granular topic management.
- 🛠️ **Introduced `ProcessClassDiscoveryTopic`**: Added a new NATS topic model for discovery requests and responses pertaining to process *classes*, providing a structured way to query process definitions.
- 🛠️ **Introduced `PartialProcessTopic`**: Added a new NATS topic model for partially qualified process events, allowing for flexible subscriptions to broad categories of events.
- 🛠️ **Introduced `ProcessClassTopic`**: Added a new NATS topic model for process events scoped to a process *class*, providing a clearer hierarchy for event routing.
- 🛠️ **Introduced `ProcessInstanceTopic`**: Added a new NATS topic model for process events specific to a process *instance*, ensuring precise event routing for active processes.
- 🗄️ **Added Agent Config Deletion Utility**: Implemented `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument`, providing a convenient method for cleaning up specific agent configurations in tests.
- 🗄️ **Introduced `ProcessConfigEntity`**: Added a new base class for storing process configurations in the database, defining common fields and methods for persistence.
- 🗄️ **Created `ProcessConfigEntityDocument`**: Implemented a new MongoDB Document for persisting process configurations as a standalone collection, including methods for finding and deleting configurations.
- 🗄️ **Added `ProcessConfigEntityEmbeddedDocument`**: Introduced an embedded MongoDB Document for storing process configurations within other documents, suchs as `ProcessEntity`, for default settings.
- 📦 **Introduced Dagster Webserver Dockerfile**: Added a new Dockerfile for building the Dagster webserver, including multi-stage build optimization and configuration for PostgreSQL.
- 🛠️ **Implemented `AzureDataLakeClient`**: Provided a concrete Azure-specific implementation of `AbstractDataLakeClient`, wrapping `FileSystemClient` to offer a cloud-agnostic interface for Azure Data Lake Storage.
- 🛠️ **Introduced `S3DataLakeClientResource`**: Added a new Dagster resource for providing a `boto3` S3 client, specifically designed for interacting with S3-compatible storage like MinIO within pipelines.
- 🛠️ **Introduced `S3DataLakeFileSystemResource`**: Added a new Dagster resource for providing an `s3fs` file system client, enabling seamless interaction with S3-compatible storage like MinIO within pipelines as if it were a local file system.
- 📦 **Added Pipeline App Package**: Created an `app` package within `aihub_pipeline` to organize and modularize specific pipeline applications.
- 📦 **Introduced Default RAG Pipeline Dockerfile**: Added a new Dockerfile for building the `default_rag_pipeline`, including multi-stage build optimization and configuration for specific pipeline execution.
- 🛠️ **Configured Default RAG Pipeline**: Added Dagster definitions for the `default_rag_pipeline`, including asset factories, S3 data lake resources, Mongo/Milvus storage, and Azure OpenAI LLM/embedding models, setting up a complete RAG workflow.
- 🛠️ **Implemented `WalkthroughContext`**: Added a new context class `WalkthroughContext` for managing and persisting state specific to individual process walkthroughs using Redis.
- 🧪 **Added Process Configuration Database Tests**: Implemented new unit tests for `ProcessConfigEntityDocument` to ensure correct persistence, retrieval, and override behavior of process configurations in the database.
- 🧪 **Introduced Process Service Database Integration Tests**: Added comprehensive integration tests for `ProcessService` to verify its interaction with the database, ensuring correct loading, caching, and precedence logic for process configurations.
- 🧪 **Added Process Service Unit Tests**: Implemented new unit tests for `ProcessService`, covering process discovery, event sending, and cache management, ensuring the service's core functionalities work as expected.
- 🧪 **Added Comprehensive Process Dispatcher Tests**: Implemented new unit and integration tests for `ProcessDispatcher`, covering configuration handling, context management with `WalkthroughContext`, event processing, and error handling, ensuring the core process execution logic is robust.
- 📦 **Added Dagster Configuration File**: Introduced `dagster.yaml` to configure Dagster's run, event log, and schedule storage to use PostgreSQL, along with a queued run coordinator and disabled telemetry.
- 🛠️ **Introduced `ProcessClassTopicManager`**: Added a new topic manager responsible for generating NATS subjects specific to process *classes*, enabling class-level event routing and subscriptions.
- 📄 **Added `MinimalProcessDTO`**: Introduced a new data transfer object for representing core process information in lightweight API responses, improving efficiency and clarity.
- 📄 **Introduced `ProcessClassDTO`**: Added a new DTO to encapsulate process class information received from discovery events, including configuration specifications and default process configurations.
- 📄 **Created `ProcessInstanceDTO`**: Introduced a new DTO to represent specific process instances, including their unique ID and configuration, and added methods for conversion to discovery events and entity creation.
- 📈 **Enhanced Dispatcher Logging and Shutdown**: Improved `BaseDispatcher` shutdown logic with explicit logging and added detailed debug logs for message handling, enhancing operational visibility.

### Changed
- ⬆️ **Updated Default Remote Core Tag**: The default version tag used in `Makefile` for switching to remote core dependencies has been updated to `v0.229.0`.
- 🐳 **Enhanced Dockerfile for LLM Wrapping Agent**: Updated the `llm_wrapping_agent` Dockerfile to use an `AGENT_NAME` environment variable for dynamic naming and `exec` in the entrypoint for improved process management.
- ⚙️ **Refined LLM Wrapping Agent Startup**: Updated the `LLMWrappingAgent`'s main entry point to use `NatsConfig` and `RedisConfig` from their new `infrastructure` locations, and now explicitly passes connection details to the `AgentRunner` for improved clarity. Also corrected the Azure OpenAI API key setting.
- ⬆️ **Dependency Updates**: Updated `aihub_agent`'s version to `v0.229.0` and aligned `aihub_lib` dependency tag.
- 🌐 **Streamlined Agent Discovery in API Controller**: Updated `AgentController` to leverage the enhanced `AgentService.discover_agents` method, which now directly returns `AgentDTO` instances for simplified API responses.
- ☁️ **Integrated Multi-Cloud File Access in API**: Updated `FileController` to leverage the new `FileAccessServiceConfig` for generating secure, temporary file URLs, enabling multi-cloud storage support.
- ☁️ **Adopted Multi-Cloud File Access in File Service**: Migrated `FileService` to utilize `FileAccessServiceConfig` for generating temporary file URLs and retrieving URL signing secrets, supporting cloud-agnostic file operations. Updated docstrings for clarity.
- ⚙️ **Enhanced Process Form Submission**: Updated `ProcessController` to explicitly discover the process instance and pass its `process_config` during form submission, ensuring accurate context for process initiation.
- ⚙️ **Adjusted API Process Controller Routing**: Reordered `ProcessController` method calls in `playground/development/main.py` for a more logical flow of process-related endpoints.
- 🧪 **Improved Agent API Test Fixtures**: Added a `cleanup_db_and_cache` fixture to `test_agent_api.py` to ensure a clean state for agent-related tests, improving test reliability.
- 🧪 **Enhanced Agent Config Database Tests**: Introduced a `cleanup_db_and_cache` fixture to `test_agent_config_database_operations.py` for consistent testing by clearing caches before and after runs.
- 🧪 **Refined Agent Service Database Integration Tests**: Added a `cleanup_db_and_cache` fixture and adjusted mock targets (`_discover_agent_class`) in `test_agent_service_database_integration.py` for improved test reliability and alignment with internal service changes.
- 🧪 **Updated Agent Service Unit Tests**: Introduced a `cleanup_db_and_cache` fixture and adjusted mock targets (e.g., `_discover_agent_classes`, `_discover_agent_class`, `_send_event`, `_clear_cache`) in `test_agent_service_unit_tests.py` to reflect service refactorings and improve test consistency.
- 🧪 **Added Custom Agent Config Test for OpenAI Endpoint**: Included a new test in `test_openai_with_assistants.py` to verify that the OpenAI chat completions endpoint correctly utilizes custom agent configurations persisted in the database.
- 🧪 **Improved Process API Test Fixtures and Routes**: Added a `cleanup_db_and_cache` fixture to `test_process_api.py` for consistent testing and reordered `ProcessController` methods to match the updated routing logic.
- ⬆️ **Dependency Updates**: Updated `aihub_api`'s version to `v0.229.0` and aligned `aihub_lib` dependency tag.
- ⬆️ **Dependency Updates**: Updated `aihub_bot`'s version to `v0.229.0` and aligned `aihub_lib` dependency tag.
- ⬆️ **Dependency Updates**: Updated `aihub_iac`'s version to `v0.229.0`.
- 🖼️ **Enhanced Image Resolution in Document Context**: Updated `combine_nodes_in_order` to use the new `FileAccessServiceConfig` and correctly resolve image URLs from both Azure and S3/MinIO storage, supporting `s3://` URIs.
- 📈 **Improved Event Store Debugging**: Enhanced `JetStreamEventStore` message handler with more verbose debug logging and explicit exception logging for better troubleshooting.
- 📦 **Updated Discovery Event Imports**: Aligned `discovery` package imports to reflect the new `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent` hierarchy.
- 📦 **Updated Process Discovery Event Imports**: Aligned imports within the `process` discovery events package to reflect the new `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent` hierarchy.
- ⚙️ **Added `process_id` to `WorkRequestEvent`**: Included a `process_id` field in `WorkRequestEvent` to ensure consistent identification of the target process instance for work requests.
- 📈 **Enhanced JetStream Subscriber Debugging**: Improved `JSSubscriber`'s `subscribe` method by explicitly passing parameters and added debug logging for `unsubscribe` operations, increasing visibility.
- ⚙️ **Added Agent Class Wildcard Subject**: Introduced a new private method `_get_subject_for_all_events_in_agent_class` to `AgentClassTopicManager`, providing a wildcard subject for subscribing to all events within a specific agent class.
- 📦 **Updated NATS Topic Imports**: Aligned top-level NATS topic imports to reflect the new `AgentInstanceTopic`, `ProcessInstanceDiscoveryTopic`, and `ProcessInstanceTopic` hierarchy.
- 📦 **Updated Agent Topics Imports**: Aligned agent topics imports to reflect the `AgentInstanceTopic` naming.
- 📦 **Updated Discovery Topics Imports**: Aligned discovery topics imports to reflect the `ProcessInstanceDiscoveryTopic` naming.
- 📦 **Updated Process Discovery Topics Imports**: Aligned process discovery topics imports to reflect the `ProcessInstanceDiscoveryTopic` naming.
- 📦 **Updated Process Topics Imports**: Aligned process topics imports to reflect the `ProcessInstanceTopic` naming.
- 📦 **Updated Process Persistence Imports**: Aligned imports within the `persistence.process` package to expose the new `ProcessConfigEntity`.
- ⚙️ **Enhanced `ProcessConfig` with Class and Entity Conversion**: Added a `process_class` field to `ProcessConfig` for clearer identification and implemented a `from_entity` class method to facilitate conversion from database entities, improving persistence integration.
- ⚙️ **Migrated Azure Data Lake IO Manager to New Client**: Updated `AzureDataLakeIOManager` to use the new `AzureDataLakeClient` for file system interactions, encapsulating Azure-specific details and streamlining `DataLakeFile` creation.
- 🚀 **Cloud-Agnostic Data Lake File Fetching**: Updated `fetch_all_files_in_data_lake` operation to utilize the new `AbstractDataLakeClient`, enabling cloud-agnostic fetching of files from data lake storage.
- 🚀 **Cloud-Agnostic Figure Deletion**: Modified `delete_figures_for_many_ref_doc` to use the new `AbstractDataLakeClient` for directory and file operations, enabling cloud-agnostic deletion of figures from the data lake.
- 🚀 **Cloud-Agnostic Data Lake File Removal Logic**: Updated `fetch_data_lake_files_to_remove` to utilize the new `AbstractDataLakeClient`, streamlining the process of identifying and removing files no longer present in SharePoint.
- 🛠️ **Expanded Resource Factory for Multi-Cloud Pipelines**: Introduced `s3_data_lake_resources` and `default_io_manager_s3_datalake_resources` factory functions to support S3/MinIO storage integrations. Updated existing Azure Data Lake resource factories to align with new naming conventions and removed `aisearch_vector_store_resource` and `mongo_aisearch_storage_context_resources` to streamline vector store options.
- 🧪 **Updated Pipeline Playground to S3/MinIO and Document Intelligence**: Migrated the `playground` pipeline configuration to use S3/MinIO data lake resources and switched the default document parser to `DOCUMENT_INTELLIGENCE`, aligning with new multi-cloud capabilities.
- ⬆️ **Dependency Updates for Pipelines**: Updated `aihub_pipeline`'s version to `v0.229.0`, upgraded Dagster-related dependencies, and added `dagster-aws`, `s3fs`, and `boto3` to support comprehensive S3/MinIO integrations.
- ⚙️ **Enhanced Process Dispatcher with Config and Context Management**: Overhauled `ProcessDispatcher` to integrate `WalkthroughContext` for dynamic process configuration storage and retrieval. It now correctly derives `ProcessInstanceTopic` from `ProcessClassTopic`, supports `process_config` injection into step methods, and refines event publishing to align with the updated process hierarchy.
- ⚙️ **Updated Process Runner for New Config and Topic Hierarchy**: Refactored `ProcessRunner` to use `default_process_config` and `ProcessClassTopicManager`, adapting to `ClassDiscoveryRequestEvent` and `ProcessClassDiscoveryResponseEvent` for process class discovery. It now initializes the `ProcessDispatcher` with the default configuration, ensuring consistency across the new process architecture.
- 🧪 **Enhanced Process Test Runner**: Updated `ProcessTestRunner` to align with the new `default_process_config` and `ProcessInstanceTopic` hierarchy, and adjusted NATS discovery observation to support both process class and instance discovery events from their new `infrastructure` locations.
- ⚙️ **Updated Agent-Only Process Runner Config**: Modified `agent_only_process/run.py` to use `default_process_config` and explicitly set `process_class` in `ProcessConfig`, adhering to the new process configuration structure.
- 🧪 **Updated Agent-Only Process Tests**: Adjusted `test_AgentOnlyProcess.py` to use `default_process_config`, include `process_class` in `ProcessConfig` initialization, and enabled logging for better test debugging.
- ⚙️ **Updated Agent-Only Process Trigger Config**: Modified `agent_only_process/trigger.py` to use `default_process_config` and explicitly set `process_class` in `ProcessConfig`, adhering to the new process configuration structure.
- 🧪 **Updated Agent-to-Human Process Tests**: Adjusted `test_AgentToHumanProcess.py` to use `default_process_config` and include `process_class` in `ProcessConfig` initialization.
- 🧪 **Updated Fan-Out Process Tests**: Adjusted `test_FanOutProcess.py` to use `default_process_config` and include `process_class` in `ProcessConfig` initialization.
- ⚙️ **Updated Fan-Out Process Trigger Config**: Modified `fan_out_process/trigger.py` to use `default_process_config` and explicitly set `process_class` in `ProcessConfig`, adhering to the new process configuration structure.
- ⚙️ **Updated Human-Only Process Runner Config**: Modified `human_only_process/run.py` to use `default_process_config` and explicitly set `process_class` in `ProcessConfig`, adhering to the new process configuration structure.
- 🧪 **Updated Human-Only Process Tests**: Adjusted `test_HumanOnlyProcess.py` to use `default_process_config` and include `process_class` in `ProcessConfig` initialization.
- 🧪 **Updated Human-to-Agent Process Tests**: Adjusted `test_HumanToAgentProcess.py` to use `default_process_config` and include `process_class` in `ProcessConfig` initialization.
- 🧪 **Updated Multi-Input Process Tests**: Adjusted `test_MultiInputProcess.py` to use `default_process_config` and include `process_class` in `ProcessConfig` initialization.
- ⚙️ **Updated Multi-Input Process Trigger Config**: Modified `multi_input_process/trigger.py` to use `default_process_config` and explicitly set `process_class` in `ProcessConfig`, adhering to the new process configuration structure.
- 🧪 **Updated Process Sequence Tests**: Adjusted `test_ProcessSequence.py` to use `default_process_config` and include `process_class` in `ProcessConfig` initialization for both initial and subsequent processes.
- ⚙️ **Updated Process Sequence Trigger Config**: Modified `process_sequence/trigger.py` to use `default_process_config` and explicitly set `process_class` in `ProcessConfig` for both initial and subsequent processes, adhering to the new process configuration structure.
- ⬆️ **Dependency Updates**: Updated `aihub_process`'s version to `v0.229.0` and aligned `aihub_lib` dependency tag.
- 🖼️ **Enabled S3 Image Support in Frontend**: Updated `ResolveImageComponent.vue` to correctly parse and display images from S3-compatible URLs (e.g., `s3://bucket/path`), ensuring multi-cloud image rendering on the frontend.
- 🌐 **Updated Generated SDK Schemas**: Regenerated client SDK schemas to reflect latest API changes, including updated default timestamps for model details.
- 🐳 **Comprehensive Docker Compose Updates for Multi-Cloud and Dagster**: Upgraded MinIO image and configured Traefik for MinIO access. Integrated Dagster into the PostgreSQL setup and added a complete Dagster stack (webserver, daemon, OAuth2 proxy) to `docker-compose.latest.yml`, enhancing the full local environment. Removed Phoenix prefix stripping.

### Fixed
- 🐛 **Resolved Circular Dependency in `UserWithAccessDTO`**: Addressed a circular import issue by moving the `ProcessService` import into the `from_user_entity` method, improving module load order.

### Removed
- 🗑️ **Removed Obsolete Agent Config Test**: Deleted `test_agent_config_start_event.py`, as its functionality has been integrated or superseded by other test suites.
- 🗑️ **Removed Generic `DiscoveryRequestEvent`**: Eliminated `DiscoveryRequestEvent`, which has been replaced by more granular `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent` for specific discovery needs.
- 🗑️ **Removed Generic `ProcessTopic`**: Eliminated `ProcessTopic`, which has been superseded by the more granular `ProcessClassTopic` and `ProcessInstanceTopic` for improved topic hierarchy.
- 🗑️ **Removed Azure AI Search Vector Store Resource**: Discontinued `AzureAISearchVectorStoreResource` from `aihub_pipeline`, streamlining the available vector store integrations.

### Refactor
- 🧹 **Consolidated Base Context**: Moved `BaseContext` from `aihub_agent` to `aihub_lib/aihub_lib/context`, centralizing core context management.
- 🔄 **Refined Agent Topic Handling in Dispatcher**: Updated `AgentDispatcher` to align with the new `AgentClassTopic` and `AgentInstanceTopic` hierarchy, ensuring more precise event routing and context management.
- 🧹 **Updated Runner Imports**: Adjusted `AgentTestRunner` imports to reflect the new `NatsConfig` and `RedisConfig` locations under `aihub_lib.infrastructure`. Also updated topic types to `AgentInstanceTopic`.
- 🧹 **Updated Tracing Coordinator Imports and Topics**: Adjusted `RunTraceCoordinator` imports for `BaseContext` and updated topic types to `AgentInstanceTopic`.
- 🧹 **Updated Playground Runner Imports**: Adjusted `FrontendTestingAgent`'s runner imports to reflect the new `NatsConfig` and `RedisConfig` locations.
- 🧹 **Updated Performance Test Imports**: Adjusted performance test script imports to reflect the new `NatsConfig` and `RedisConfig` locations.
- 🔄 **Adapted Agent Dispatcher Tests**: Updated `AgentDispatcher` unit tests to use `AgentInstanceTopic` and improved type hints for agent configurations.
- 🔄 **Updated Event Persister Topics**: Adjusted `EventPersister` to use the new `ProcessInstanceTopic` and `AgentInstanceTopic` for event persistence.
- 🧹 **Refined Agent Service Logic and API**: Performed extensive refactoring in `AgentService` to privatize internal discovery methods (`_discover_agent_class`, `_discover_agent_classes`) and the generic event sender (`_send_event`). Introduced a new public `send_agent_start_event` method for clearer API interaction and aligned all topic usage with `AgentInstanceTopic`.
- 🏗️ **Re-architected Process Discovery and Management**: Performed a significant overhaul of `ProcessService` to introduce a clear distinction between process classes and instances, utilizing new `ProcessClassDTO` and `ProcessInstanceDTO`. This refactoring privatized internal discovery methods (`_discover_process_class`, `_discover_process_classes`) and the event sending logic (`_send_event`), standardized config loading with `ProcessConfigEntityDocument`, and streamlined process entity creation. The service now directly handles `ProcessConfig` objects, enhancing type safety and consistency.
- 🔄 **Updated `ProcessDTO` Hierarchy**: Refactored `ProcessDTO` to inherit from `MinimalProcessDTO` and streamlined its `from_entity` and `from_instance` methods to directly use `ProcessConfig` for improved data consistency.
- 🧹 **Updated API Lifetime Manager Imports**: Adjusted `lifetime_manager` imports to reflect the new `NatsConfig` location.
- 🧹 **Refined Simulated Agent API Runner**: Updated `SimulatedAgentApiTestRunner` to use `NatsConfig` from its new location, aligned topic types with `AgentInstanceTopic`, and adjusted subscriber methods for control events.
- 🧹 **Updated Simulated Process API Runner**: Adjusted `SimulatedProcessApiTestRunner` to reflect the new `NatsConfig` location, incorporate `ClassDiscoveryRequestEvent` and `ProcessClassDiscoveryResponseEvent` for discovery, align topic types with `ProcessInstanceTopic`, and adapt to `ProcessConfig` changes including `process_config_specs`.
- 🧹 **Refactored Agent Endpoint Discovery**: Privatized `_discovery_handler` and `_create_endpoint` in `AgentEndpointsDiscoveryService` and updated event sending logic to use the new `AgentService.send_agent_start_event`, improving encapsulation and modularity.
- 🏗️ **Comprehensive Process Endpoint Refactoring**: Significantly refactored `ProcessEndpointsDiscoveryService` to implement a new process instance discovery mechanism (`_discovery_handler`), privatized all endpoint creation methods (`_create_form_get_endpoint_process_start`, etc.), and updated form submission logic to explicitly pass `process_config`, enhancing modularity and data flow.
- 🔄 **Updated WebSocket Manager Topic**: Changed `WebSocketManager` to use `AgentInstanceTopic` for improved consistency with the new agent topic hierarchy.
- 🔄 **Updated WebSocket Sender Topic**: Changed `WebSocketSender` to use `AgentInstanceTopic` for improved consistency with the new agent topic hierarchy.
- 📄 **Cleaned Up API Client Fixture Docstrings**: Removed redundant `Args` sections from API client fixture docstrings for improved clarity.
- 🔄 **Updated Bot-in-the-Loop Handler Topics**: Changed `BotInTheLoopHandler` to use `AgentInstanceTopic` for consistency with the new agent topic hierarchy.
- 🔄 **Updated Simulated Agent Bot Runner Topics**: Changed `SimulatedAgentBotTestRunner` to use `AgentInstanceTopic` for consistency with the new agent topic hierarchy.
- 🧹 **Updated Bot Lifetime Manager Imports**: Adjusted `lifetime_manager` imports to reflect the new `NatsConfig` location.
- 📄 **Cleaned Up Network Provider Docstrings**: Removed redundant parameter descriptions from `NetworkProvider` docstrings for improved clarity.
- 📄 **Simplified Resource Namer Docstrings**: Removed redundant `Args` and `Returns` descriptions from `ResourceNamer` docstrings.
- 📄 **Streamlined Storage Resource Factory Docstrings**: Removed verbose `Args` and `Returns` explanations from `StorageResourceFactory` docstrings.
- 🧹 **Centralized Base Context**: Moved `BaseContext` to `aihub_lib/aihub_lib/context`, making it a shared core library component.
- 🔄 **Updated Azure Document Intelligence Key Access**: Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent Azure SDK API changes (`keys.primary_key` to `keys.key1`).
- 🧹 **Restructured Infrastructure Configurations**: Moved `NatsConfig` into the new `aihub_lib.infrastructure.nats` package and `RedisConfig` into `aihub_lib.infrastructure.redis` package for improved logical grouping and project structure.
- 🔄 **Updated Agent-in-the-Loop Event Topics**: Adjusted `AgentInTheLoopRequestEvent` to use `AgentInstanceTopic` for consistency with the new agent topic hierarchy.
- 🔄 **Updated Bot-in-the-Loop Event Topics**: Adjusted `BotInTheLoopRequestEvent` to use `AgentInstanceTopic` for consistency with the new agent topic hierarchy.
- 🔄 **Updated Human-in-the-Loop Event Topics**: Adjusted `HumanInTheLoopRequestEvent` to use `AgentInstanceTopic` for consistency with the new agent topic hierarchy.
- 🔄 **Updated `ProcessExceptionEvent` Inheritance**: Changed `ProcessExceptionEvent` to inherit from `WorkEvent`, aligning it with the updated event hierarchy.
- 🔄 **Refactored `ProcessStopEvent`**: Updated `ProcessStopEvent` to inherit from `WorkEvent` and removed the redundant `process_id` field for a leaner model.
- 🔄 **Refined Agent JetStream Subscribers**: Updated `AgentJSSubscriber` to consistently use `AgentInstanceTopic` and replaced the generic `for_agent_instance_events` with the more specific `for_agent_instance_control_events` for clearer intent.
- 🔄 **Updated Agent NATS Subscribers**: Aligned `AgentNCSubscriber` methods to consistently use the new `AgentInstanceTopic` and `AgentClassDiscoveryTopic` for enhanced type safety and clarity in agent event subscriptions.
- 🔄 **Refactored Process JetStream Subscribers**: Overhauled `ProcessJSSubscriber` to introduce explicit subscriptions for process *class* work events (`for_process_class_work_events`) and refined instance-level subscriptions to focus on *work events* (`for_process_instance_work_events`), aligning with the new hierarchical topic model.
- 🔄 **Overhauled Process NATS Subscribers**: Revamped `ProcessNCSubscriber` to support new `ProcessClassDiscoveryTopic` and `ProcessInstanceDiscoveryTopic` for discovery requests and responses. Renamed and updated existing subscription methods to align with the new class- and instance-level process topics, and refined work event type filtering.
- 🔄 **Refactored `ProcessInstanceTopicManager` Inheritance**: Updated `ProcessInstanceTopicManager` to inherit from `ProcessClassTopicManager`, simplifying its implementation and consolidating stream management to the parent class.
- 🔄 **Revamped Process Topic Manager**: Overhauled `ProcessTopicManager` to introduce distinct methods for process *class* and *instance* discovery subjects, aligning with the new topic hierarchy. Also added a `WORK_EVENT` constant and refined control event subject generation.
- 🔄 **Refactored Process Walkthrough Topic Manager**: Updated `ProcessWalkthroughTopicManager` to inherit from `ProcessClassTopicManager`, making `process_id` optional for broader applicability, and introduced `from_process_class_topic_manager` for more flexible instantiation.
- 🧹 **Restructured IO Managers**: Introduced a `base` subpackage under `aihub_pipeline/io` for shared IO manager abstractions.
- 🧹 **Renamed `DataLakeClientResource` to `AzureDataLakeClientResource`**: Moved and renamed the Azure Data Lake client resource to explicitly reflect its cloud provider and align with the new resource hierarchy.
- 🧹 **Renamed `DataLakeFileSystemResource` to `AzureDataLakeFileSystemResource`**: Moved and renamed the Azure Data Lake file system resource to explicitly reflect its cloud provider and align with the new resource hierarchy.
- 🧹 **Centralized `DataLakeFile` Creation**: Removed the static `from_uri` method from `DataLakeFile`, delegating URI-based instantiation to cloud-specific data lake client implementations for better encapsulation.
- 🧹 **Introduced Process Context Package**: Created a dedicated `context` package within `aihub_process` for organizing process-related context management.
- 🔄 **Refactored Abstract Entity Delegator**: Updated `AbstractEntityDelegator` to align with the new `ProcessClassTopic` hierarchy, removed `process_id` from its initialization, and introduced a private `_publish_work_event` method for streamlined internal event publishing.
- 🔄 **Updated Agent Delegator for Process Hierarchy**: Refactored `AgentDelegator` to operate with the new `ProcessClassTopicManager` and `AgentInstanceTopic`, leveraging the internal `_publish_work_event` method for consistent event handling within the updated process hierarchy.
- 🔄 **Refined Process Delegator Logic**: Updated `ProcessDelegator` to align with the new `ProcessInstanceTopic` hierarchy, streamline event handling with the internal `_publish_work_event` method, and adjust subscription methods for specific work events.
- 🗄️ **Re-architected Process Entity Persistence**: Overhauled `ProcessEntity` to support a flexible process configuration strategy, using `ProcessConfigEntityDocument` as a reference for dynamic configurations and embedding `ProcessConfigEntityEmbeddedDocument` for default settings. This refactoring also streamlined creation and update methods.
- 📄 **Cleaned Up User Mock Docstrings**: Removed redundant `Args` sections from `user_mocks` docstrings for improved clarity.
- 🧹 **Introduced Process Testing Package**: Created a `testing` package within `aihub_process/playground` to centralize process-related testing utilities and fixtures.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📦 **S3/MinIO Configuration:** Added `S3Config` for managing connection parameters for S3-compatible storage services.
- 🎯 **Process Configuration Specificity:** Added `process_class` field to `ProcessConfig` and `process_config_specs` to `ProcessClassDiscoveryResponseEvent` for clearer process definition and discovery.
- 📄 **Structured Process Discovery Events:** Introduced new event types (`ProcessConfigSpecs`, `ProcessInstanceDiscoveryResponseEvent`, `ProcessClassDiscoveryResponseEvent`) for more detailed process discovery.
- ✨ **Process Walkthrough Context:** Implemented `WalkthroughContext` for managing transient state within individual process walkthroughs in Redis.
- 🧪 **Comprehensive Process Testing:** Added extensive unit and integration tests for `ProcessDispatcher`, `ProcessConfigEntityDocument`, and `ProcessService`, improving test coverage for process orchestration and persistence.
- 🗄️ **Database Persistence for Process Configurations:** Introduced `ProcessConfigEntity`, `ProcessConfigEntityDocument`, and `ProcessConfigEntityEmbeddedDocument` to enable persistent storage and retrieval of process configurations.
- 📚 **Test Cleanup Fixtures:** Added `cleanup_db_and_cache` fixtures to various API test modules for consistent database and cache state management.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⚙️ **Process Dispatcher Logic:** Refined the `ProcessDispatcher` to dynamically load `ProcessConfig` and manage `WalkthroughContext`, ensuring accurate process execution and state management.
- 🏷️ **NATS Topic Hierarchy for Processes:** Overhauled NATS topic managers and subscribers for processes to distinguish between class-level and instance-level topics, providing more granular event routing.
- 🌐 **API Process Discovery and Submission:** Updated API endpoints for process discovery and form submission to align with the new `ProcessClassDTO`, `ProcessInstanceDTO`, and persistence models.
- ⚡️ **Event Model Enhancements:** Added `process_config` to `ProcessStartEvent` and `process_id` to `WorkRequestEvent` for richer event data, and adjusted `ProcessExceptionEvent` and `ProcessStopEvent` inheritance.
- 🤖 **Agent Dispatcher Topic Handling:** Updated the `AgentDispatcher` to use the new `AgentClassTopic` and `AgentInstanceTopic` for improved clarity and consistency in agent event routing.
- 🏷️ **NATS Topic Hierarchy for Agents:** Updated agent-related NATS topic managers and subscribers to reflect the new `AgentClassTopic` and `AgentInstanceTopic` hierarchy.
- 📊 **Dagster Persistence Configuration:** Updated `dagster.yaml` to explicitly define run, event log, and schedule storage configurations for PostgreSQL and increased `max_concurrent_runs` for improved concurrency.
- 🐳 **Dagster Dockerfile:** Adjusted `DAGSTER_HOME` and entrypoint in the Dagster Dockerfile for potentially more flexible deployments.

### Fixed
- 🐛 **Base Dispatcher Stop Issue:** Ensured the `BaseDispatcher.stop()` method correctly handles uninitialized states, preventing potential errors during shutdown.
- 🐞 **JetStream Event Store Logging:** Improved logging in `JetStreamEventStore` for better debugging of message reception and errors.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Old Process Topic Model:** Removed the generic `ProcessTopic` model in `aihub_lib`, replaced by the more specific `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic`.
- 🗑️ **Deprecated `DiscoveryRequestEvent`:** Removed the general `DiscoveryRequestEvent` from `aihub_lib`, replaced by more specific class- and instance-level discovery requests.
- 🗑️ **Obsolete Agent Test File:** Removed `aihub_agent/playground/testing/tests/test_agent_config_start_event.py` as it is no longer relevant due to changes in agent config handling.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🧹 **Internal API Service Renaming:** Renamed internal methods in `AgentService` and `ProcessService` (e.g., `discover_agent_class` to `_discover_agent_class`) to clearly indicate their internal-only usage.
- 🔄 **Agent Topic Model Renaming:** Renamed `AgentTopic` to `AgentInstanceTopic` in `aihub_lib` and updated its inheritance to `AgentClassTopic` for a more logical topic hierarchy.
- 🧹 **Process Dispatcher Context:** Refactored `ProcessDispatcher` to use `WalkthroughContext` and a new `_build_method_kwargs` for argument injection, enhancing clarity and maintainability.
- 🔄 **Process Topic Model Renaming:** Renamed `ProcessDiscoveryTopic` to `ProcessInstanceDiscoveryTopic` in `aihub_lib` and updated its inheritance to `ProcessClassDiscoveryTopic`.
- 🧹 **Persistence Entity Renaming:** Renamed `from_dto` methods to `from_specs` in process input entities (`HumanInSpecsEntity`, `ProgramInSpecsEntity`, `AgentInSpecsEntity`) for consistency.
- 🔄 **Azure Document Intelligence Key Access:** Updated the method for retrieving primary keys from Azure Document Intelligence services to align with current API practices (`keys.key1`).

---



## [v0.226.0] - 2025-07-25 - API & Pipeline Overhaul: Consolidating DTOs, Streamlining Messaging, and Enhancing Azure Integration

### Added
- ✨ **Generic Discovery Request Event**: Introduced `DiscoveryRequestEvent` to serve as a base for all system-wide discovery queries, enabling more consistent event handling.
- 📈 **Azure AI Search Vector Store**: Re-introduced and provided a dedicated factory for Azure AI Search as a vector store option within pipelines.
- 🧪 **Agent Configuration Test Coverage**: Added comprehensive tests for agent configuration precedence logic, ensuring `StartEvent` configurations correctly override default settings.

### Changed
- ⚙️ **Streamlined Process Discovery**: `ProcessDiscoveryResponseEvent` now directly includes `process_id` and the full `ProcessConfig`, simplifying the information provided during process discovery.
- 🔄 **Updated Process Stop Event**: `ProcessStopEvent` now inherits from `WorkRequestEvent` and includes a `process_id` field for improved context.
- 🎛️ **Consolidated Agent Service API**: Agent discovery methods in `AgentService` now return raw agent instances, with DTO conversion handled at the controller level for improved API separation.
- 📄 **Simplified `StartEvent` Handling**: The logic for creating `StartEvent` and `ProcessStartEvent` is now handled more directly in API endpoints, removing dedicated `from_raw_data` methods from the event classes themselves.
- 📊 **Adjusted Pipeline Defaults**: The default RAG pipeline now utilizes Azure Data Lake resources, uses the `DOCLING` document parser, and sets hardcoded namespace and store names for clarity in playground environments.
- 🐳 **Updated Docker `DAGSTER_HOME`**: Changed the default `DAGSTER_HOME` path within Dagster Docker images for consistency with common deployment practices.
- ⬆️ **Azure Document Intelligence Key Access**: Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.
- 📝 **Refined Docstrings**: Improved clarity and conciseness of docstrings for IAC resources and authentication client fixtures.
- 📉 **Dagster Version Downgrade**: Updated Dagster and related dependencies to a lower version (e.g., from `1.11.2` to `1.9.6`).

### Fixed
- 🐞 **Robust Directory Deletion**: Enhanced data lake directory deletion operations in pipelines by using `FileSystemClient.get_directory_client().exists()` for more reliable checks before deletion.
- 💬 **JetStream Logging Reduction**: Reduced verbose debug logging in `JetStreamEventStore` for clearer operational insights.

### Removed
- 🗑️ **Multi-Cloud Storage Abstraction**: Eliminated the `AbstractAnonymousFileAccessService` and its Azure- and S3-specific implementations (`AzureAnonymousFileAccessService`, `S3AnonymousFileAccessService`), simplifying file access to a direct static utility.
- 🗑️ **S3/MinIO Data Lake Support**: Removed all S3-compatible data lake clients, file system resources, IO managers, and related dependencies (`boto3`, `s3fs`) from the pipeline and infrastructure layers, focusing the data lake integration on Azure.
- 🗑️ **Process Configuration Persistence Entities**: Discontinued separate MongoDB persistence entities for process configurations (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`), streamlining configuration storage.
- 🗑️ **Process Walkthrough Context**: Removed the `WalkthroughContext` component from `aihub_process`, simplifying how per-walkthrough state is managed.
- 🗑️ **Redundant Process DTOs**: Consolidated process Data Transfer Objects (DTOs) by removing `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO`, with `ProcessDTO` now serving as the single, comprehensive representation.
- 🗑️ **Legacy Process NATS Topics & Managers**: Eliminated outdated process-related NATS topic classes (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) and their corresponding topic managers (`ProcessClassTopicManager`), unifying them under a simplified hierarchy.
- 🗑️ **Deprecated Agent NATS Topics**: Removed `AgentClassTopic` as part of the consolidation to a single `AgentTopic`.
- 🗑️ **Extensive Process Test Suite**: Removed numerous unit tests specifically for `ProcessDispatcher` and `ProcessService` database integration, likely due to component consolidation and shift in testing strategy.
- 🗑️ **Unused Agent Configuration Utility**: Removed `delete_if_exists_for_class_and_id` from `AgentConfigEntityDocument`.
- 🗑️ **Legacy OpenAI Agent Config Test**: Removed a specific test case for custom agent configuration with OpenAI chat completions.

### Refactor
- 🔄 **Consolidated NATS Topics**: Streamlined NATS messaging by introducing unified `AgentTopic` and `ProcessTopic` classes, simplifying event routing and topic management across the system.
- ⚙️ **Streamlined Process Configuration**: `ProcessConfig` is now a leaner model, no longer containing `process_class` as a direct field and decoupled from persistence entities.
- 🏗️ **Simplified Data Lake Resources**: Refactored Azure Data Lake resources to directly expose Azure SDK clients (`FileSystemClient`, `AzureBlobFileSystem`), removing intermediate wrapper classes and abstract base interfaces.
- 🧹 **Centralized `DataLakeFile` Creation**: Moved the logic for creating `DataLakeFile` instances from URIs into a static method on the `DataLakeFile` class, promoting reusability.
- 📦 **Infrastructure Config Path Cleanup**: Moved `NatsConfig` and `RedisConfig` to `aihub_lib/nats` and `aihub_lib/` respectively, flattening the `infrastructure` directory structure.
- 🧹 **Agent & Process Dispatcher Simplification**: Refactored `AgentDispatcher` and `ProcessDispatcher` to streamline internal logic, remove redundant setup, and simplify event publishing by delegating to dedicated methods.
- 🔗 **Refined NATS Subscriber Hierarchy**: Consolidated and renamed various NATS JetStream and NATS Core subscriber methods for agents and processes, aligning them with the new topic hierarchy and providing more general subscription options.
- 🧹 **Cleaned `BaseDispatcher` Stop Logic**: Simplified the `stop` method in `BaseDispatcher` by removing redundant initialization checks and logging.
- 📁 **Module Structure Adjustment**: Adjusted the import paths for several modules (e.g., `BaseContext` from `aihub_lib` to `aihub_agent`) to align with a more modular codebase organization.
- 🖼️ **Simplified Image URL Resolution**: Refactored frontend image resolution logic to directly use `props.src` for splitting container and file paths, streamlining the process.
- 🧹 **General Code Cleanup**: Removed various unused imports, commented-out code, and minor redundant type hints across the codebase for improved readability and maintainability.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage and Process Orchestration Refinements

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` with concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🚀 **Process Walkthrough Context:** Added `WalkthroughContext` for managing per-process run state in Redis, enhancing the robustness of long-running workflows.
- ✨ **New Process Discovery Details:** Introduced `ProcessConfigSpecs` for describing the schema of process configurations, enabling dynamic UI generation for process setup.
- 📦 **Granular Process DTOs:** Added `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to provide clearer, more structured representations of processes in API responses.
- 🔄 **Structured Process Persistence:** Implemented new persistence entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) for robust storage and retrieval of process configurations.
- 🔗 **Hierarchical NATS Topics for Processes:** Introduced a new, refined NATS topic hierarchy for processes (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) for improved event routing and clarity.
- 🧪 **Comprehensive Process Dispatcher Tests:** Added new unit and integration tests for `ProcessDispatcher`, ensuring reliable process execution and configuration handling.
- ➕ **Agent Configuration Deletion Utility:** Added a utility method `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument` for cleaner management of agent configurations.
- 🏗️ **Dagster Infrastructure Deployment:** Integrated `dagster-webserver`, `dagster-daemon`, and `oauth2proxy` services into `docker-compose.latest.yml`, simplifying the deployment of the Dagster stack.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- 🌐 **API Process Discovery:** The API's process discovery now returns richer `ProcessDTO` objects, derived from the new `ProcessInstanceDTO` structure.
- ⚙️ **Process Configuration Handling:** `ProcessDispatcher` and `ProcessRunner` now use `default_process_config` and dynamically load specific configurations, enhancing flexibility.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies (webserver, postgres, azure), and added `dagster-aws`, `boto3`, and `s3fs` to support comprehensive S3/MinIO integrations.
- 🔒 **Enhanced Container Security:** Postgres, NATS, and Redis services in `docker-compose.latest.yml` no longer expose their ports externally, improving security by limiting direct external access.
- 🎛️ **Dagster Configuration:** Updated `dagster.yaml` to specify Postgres storage for all Dagster components and increased `max_concurrent_runs` for improved concurrency.
- 📦 **Container Path Standardization:** Changed `DAGSTER_HOME` and entrypoint paths in `aihub_pipeline/Dockerfile` for better consistency in container deployments.
- 📄 **Process Start Event Data:** `ProcessStartEvent` now includes `process_config` and can be constructed directly from raw data via a new `from_raw_data` class method.
- 💬 **Work Event Type Acceptance:** `DispatchableWorkflow.get_steps_waiting_for_event` now correctly accepts `WorkEvent` types, broadening its applicability.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Deprecated Agent Config Test:** Removed the outdated test file `test_agent_config_start_event.py` as its logic is now covered by more integrated tests.
- 🗑️ **Generic Discovery Event:** Removed `DiscoveryRequestEvent` as it has been superseded by more specific class and instance discovery events.
- 🗑️ **Old Process Topic Structure:** Eliminated `ProcessTopic` and its related files, replaced by the new hierarchical `ProcessInstanceTopic`, `ProcessClassTopic`, and `PartialProcessTopic`.
- 🗑️ **Redundant DataLakeFile Method:** Removed the `from_uri` static method from `DataLakeFile`, centralizing its creation within data lake client implementations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages (`aihub_lib/infrastructure/nats`, `aihub_lib/infrastructure/redis`) for clearer logical grouping.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations (`AzureDataLakeClient`, `S3DataLakeClient`) for better encapsulation and maintainability.
- 🔄 **Standardized Data Lake Resources:** Renamed `DataLakeClientResource` and `DataLakeFileSystemResource` to `AzureDataLakeClientResource` and `AzureDataLakeFileSystemResource` respectively, and introduced abstract base classes to formalize the multi-cloud data lake resource structure.
- 🧹 **Agent and Process Dispatcher Logic:** Streamlined the internal logic of `AgentDispatcher` and `ProcessDispatcher`, including argument injection, topic management, and event processing, to align with the new topic hierarchies and config loading mechanisms.
- 🗂️ **NATS Topic Hierarchy for Agents:** Fully refactored NATS topics for agents from a flat structure to a hierarchical one (`AgentInstanceTopic` inheriting from `AgentClassTopic`), and updated all related topic managers and subscribers.
- ⚙️ **Process Entity Persistence:** Overhauled `ProcessEntity` to use `ReferenceField` for user-defined `process_config` and `EmbeddedDocumentField` for `default_process_config`, enhancing data relationships and flexibility.
- 🔄 **Internal API Method Renaming:** Standardized naming conventions for internal API service methods (e.g., `_discover_agent_class`, `_send_event`, `_create_endpoint`) for improved consistency and clarity.
- 🧹 **NATS Subscriber Refinements:** Enhanced `JSSubscriber` with explicit subscription parameters and improved logging for clarity and reliability.
- 🛠️ **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

---



## [v0.226.0] - 2025-07-24 - Agent Configuration Revolution: Dynamic Overrides, Enhanced Discovery, and Structured RAG

### Added
- ✨ **Dynamic Agent Configuration:** Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Enhanced Agent Discovery Mechanism:** Implemented granular discovery for agent *classes* and specific agent *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations:** Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups across deployments.
- 🔌 **New Pydantic Models for Vector Store Configurations:** Introduced dedicated Pydantic configurations for `AzureAISearchVectorStore` and `MilvusVectorStore` (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`), allowing for direct embedding and validation of vector store settings within agent configs.
- ✨ **Hierarchical Document Headings:** Implemented the dynamic rendering of document headings (H1-H6) directly within the context. This provides a clearer hierarchical structure and significantly improves readability and navigation for complex documents by showing heading changes as content progresses.
- 📄 **Structured Content and Summary Tags:** Individual node content is now explicitly wrapped in XML-like tags (`<content>` or `<summary>`) based on its type. This provides more precise semantic context and better structural clarity for each block of text.
- 🔒 **HTML Escaping for Content:** Enhanced the integrity and security of rendered content by automatically escaping HTML special characters in both headings and content. This prevents unintended rendering issues and potential injection vulnerabilities in the generated output.
- 🦾 **New Job Creation Utility:** Introduced `materialize_asset_job` to simplify the creation of jobs for materializing specific selections of assets.
- 📅 **Automated Playground Workflows:** Implemented new daily jobs and schedules within the playground environment to automatically observe source data and manage document removal processes.
- 🧪 **New Comprehensive Unit and Integration Tests:** Added extensive test suites for the Agent Dispatcher, Agent Config handling, and Agent Service interactions with the database, significantly improving test coverage and reliability.
- 🌐 **New Configuration Options for API Services**: New environment variables for CosmosDB connections and Azure AD client details have been added, enhancing deployment flexibility.

### Changed
- ⚙️ **Refined Agent Configuration Loading Logic:** The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization:** Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 💡 **Improved Type Specificity for LLM and Vector Store Configs:** Agent configurations (e.g., in `RAGAgent`) now utilize more precise type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration:** RAG and Retrieval agents now leverage the `.to_llama_index()` method directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- ⚡️ **Enhanced Background Task Management:** Improved handling of `asyncio.Task` instances within dispatchers and subscribers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Revised API Agent Discovery:** The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- ⚙️ **Updated Default Document Language:** The default language for newly ingested nodes has been updated from English to German, better aligning with regional configurations.
- ⚡️ **Refined Node Sorting Logic:** Improved the internal sorting mechanism for nodes within a document. Nodes are now ordered more accurately based on their section start lines and type, which is crucial for the correct presentation of the new hierarchical structure.
- ⚙️ **Refined Asset Automation:** Adjusted automation configurations for document and data lake file removal assets, transitioning from eager conditions to more explicit job-driven scheduling.
- 🔗 **Specialized I/O Manager:** Updated the SharePoint observable asset to utilize a dedicated `sharepoint_io_manager`, ensuring more appropriate handling of SharePoint data interactions.
- 📄 **Agent Configuration Data Format:** The `ChatService` now passes agent configuration data as a dictionary instead of a Pydantic object when publishing `UserMessageEvent`, standardizing data exchange.
- 🐳 **Docker Build Process for API**: Updated `Dockerfile` to include `poetry install` directly in the build step, ensuring dependencies are properly set up.
- 📊 **OpenAPI Schema Generation**: `ModelCreationService` (formerly `EventModelCreationService`) now correctly excludes `agent_config` from input event schemas to prevent circular references in generated OpenAPI documentation.
- 🚀 **New API Controllers**: New controllers for `Process`, `Token`, `Role`, and `Suite` are now mounted in the API application.
- 🔑 **Enabled OAuth2AuthHandler**: The `OAuth2AuthHandler` is now explicitly enabled in the API's authentication stack.
- 🏷️ **Renamed API Event Routes**: Event API routes for getting events in a thread and event timeseries have been renamed for clarity (`get_events_in_thread` to `get_agent_events_in_thread`).

### Fixed
- 🐛 **Robust Profile Image Fetching:** Corrected an issue in `AzureGraphService` to gracefully handle cases where a user's profile image is not found (404), preventing errors during identity resolution.
- 🐛 **Robust Figure Deletion:** Improved the document figure deletion process to gracefully handle cases where associated figure directories do not exist, preventing unnecessary errors and log messages.
- 💬 **Typo in Process DTO Description**: Corrected a minor typo in the `ProcessDTO` description, enhancing the accuracy of generated SDK documentation.

### Removed
- 🗑️ **Deprecated Configuration Fields:** The `system_prompt`, `color`, and `voice` fields have been all removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration and allowing for more flexible, agent-specific prompt and UI customization to be defined in agent subclasses.
- 🧹 **Streamlined Timestamp Handling:** An internal utility for formatting Unix timestamps (`format_unix_timestamp`) has been removed, as date and time handling for document metadata is now managed more efficiently by the underlying system.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul:** Performed a major refactor of the `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management.
- 🔄 **Unified Agent Discovery:** Consolidated and streamlined the agent discovery mechanism by merging class and instance-level discovery events and topic managers into a single, consistent model.
- 🗄️ **Centralized Agent Configuration Persistence:** Re-architected agent configuration persistence by introducing a base `AgentConfigEntity` and specialized `AgentConfigEntityDocument` (for main persistence) and `AgentConfigEntityEmbeddedDocument` (for default/embedded configs), enhancing data co-location and simplifying object relationships.
- 📦 **Streamlined Vector Store Configuration Handling:** Replaced explicit vector store configuration objects (`MilvusVectorStore`, `AzureAISearchVectorStore`) with the new unified Pydantic models (`MilvusVectorStoreConfig`, `AzureAISearchVectorStoreConfig`) and their `.to_llama_index()` methods, providing a cleaner and more consistent approach.
- 📁 **Test Runner Restructuring:** Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure, improving test organization and clarity.
- 🧹 **Internal API Naming Consistency:** Renamed the internal `_get_endpoint_name` to `_get_endpoint_base_path` in endpoint discovery services for improved clarity and consistency.
- 🧹 **Renamed `EventModelCreationService` to `ModelCreationService`:** This service has been renamed to reflect its broader utility beyond just event models, with adjustments to excluded fields to accommodate the new `agent_config`.
- 📝 **Updated Agent Examples**: The `README.md` and playground examples for agents (`run.py`, `trigger.py`, `test_*.py` files) have been updated to reflect the changes in `AgentConfig` (e.g., `default_agent_config` and removal of `system_prompt`).
- 🧹 **Consolidated Data Transfer Objects (DTOs)**: Renamed `AgentClass` to `AgentClassDTO` and introduced `AgentInstanceDTO`, relocating all agent-related DTOs into a dedicated `dto` subdirectory for improved organization and clarity.
- 🔄 **Enhanced DTO Encapsulation**: `AgentInstanceDTO` now manages its own persistence by handling entity creation/updates and generating discovery response events directly, improving data model autonomy.
- 🗄️ **Decoupled Agent Persistence**: The `AgentEntity` creation and update logic was refactored to accept explicit parameters instead of DTO objects, enhancing the reusability and flexibility of the persistence layer.
- ⚙️ **Standardized Event Specification Handling**: Updated `EventSpec` creation methods to consistently use `EventSpecs` objects, improving internal data handling.
- 🔗 **Streamlined Topic Inheritance**: `AgentInstanceDiscoveryTopic` now correctly inherits from `AgentClassDiscoveryTopic`, reducing redundancy and clarifying topic structure.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🐳 **New Docker Compose Configurations**: Introduced `docker-compose.latest.yml`, `docker-compose.dev.yml`, `docker-compose-gpu.*.yml`, and `swiss-aihub.local.docker-compose.yml` for simplified deployment and environment setup, including Milvus, NATS, and Postgres initialization scripts.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📦 **Docker Build Process Streamlining**: Optimized Dockerfiles for API and Bot services by removing redundant virtual environment copying, leading to more efficient image builds.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- ⚙️ **Human Process Entity Definition**: Reworked the `Human` process entity to allow specifying users by ID, email, or role, and to enable optional notifications, offering more granular control over human-in-the-loop interactions.
- 📊 **Database Indexing Enhancements**: Added new indexes to `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.
- 💅 **Markdown Renderer CSS Consistency**: Addressed minor CSS inconsistencies in the Markdown renderer to ensure uniform display.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🚫 **Deprecated Mount-based Docker Compose**: Removed the `docker-compose-mnt.yml` file, simplifying deployment options.
- ⛔ **Redundant WebSocket Event Distributor Dependency**: Removed the `use_external_event_distributor.py` file, as its functionality has been replaced by more specific agent- and process-focused distributors.
- 🧹 **Obsolete Frontend Health Page**: A basic placeholder health page in the frontend was removed.
- ✂️ **Unused Frontend Configuration**: Removed the `.playground/app.config.ts` file from the frontend.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🔄 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related components for improved consistency and readability.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🐳 **New Docker Compose Configurations**: Introduced comprehensive Docker Compose files (`docker-compose.latest.yml`) for setting up a full AI Hub deployment with integrated services like MinIO, Milvus, PostgreSQL, OpenWebUI, NATS, Redis, MongoDB, and Traefik.
- ✨ **API Configuration Extensibility**: Enabled dynamic injection of additional environment variables into API deployments via the `ApiConfig` module, increasing configuration flexibility.
- 🛠️ **New Docker Utility Files**: Added `.dockerignore` for optimized web image builds and helper scripts (`init-multiple-dbs.sh`) for PostgreSQL setup.
- ⚙️ **Initial GPU Support Placeholders**: Added placeholder Docker Compose files for future GPU-accelerated deployments.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main API WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses (from 1 to 100), improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🗄️ **Optimized Dockerfiles**: Streamlined Dockerfiles for API and Bot services by refining virtual environment handling and build steps, resulting in smaller image sizes.
- 📦 **API and Bot Packaging**: Added `gunicorn` as a dependency for the API and Bot services, typically used for production deployments.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices.
- 🪵 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability.
- 🚅 **NATS Topic Validation for Processes**: Tightened internal topic validation for process discovery subjects, ensuring only correctly formatted subjects are processed.
- 🧮 **Database Index Optimizations**: Added new database indexes to `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found, returning `None` instead of raising an exception.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Ensured image URLs are correctly processed in RAG context prompts by explicitly converting their URL object to a string representation.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 📦 **Frontend `is_online` Field**: Corrected `AgentDTO` schema to mark `is_online` as optional, reflecting its correct behavior in API responses.
- ⏲️ **OAuth2 JWKS Cache**: Increased the max size of the JWKS cache from 1 to 100 for improved authentication performance.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related components (`sharepoint_` to `share_point_`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments where appropriate.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.
- 📦 **Frontend Directory Restructuring**: Migrated Nuxt application source from `.playground` to `.app` for cleaner project structure.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Docker Compose File**: Removed the `docker-compose-mnt.yml` file, as its functionalities are now integrated into the main Docker Compose configurations.

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

### Refactor
- 🔄 **Standardized Agent Event Topic Naming:** Renamed the `AgentTopic` schema and its associated types in the web SDK to `AgentInstanceTopic` for clearer terminology and improved consistency within the event topic structure.

### Fixed
- 📄 **Corrected Localization for Process Title:** Addressed an issue where the "Processes" heading on the user detail page was not correctly localized, ensuring proper display across all supported languages.

### Removed
- 🗑️ **Deprecated User Avatar Component:** Removed the standalone `User/Avatar.vue` component, as its functionality has been streamlined and integrated directly into the `User/Bar.vue` component for better modularity.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🚀 **Automated Dagster Builds:** Added a new GitHub Actions workflow to automate the Docker image build and release process for the Dagster webserver and daemon, streamlining deployment.
- ⚙️ **Automated Pipeline Builds:** Implemented a new GitHub Actions workflow to automate the Docker image build and release process for specific pipelines (e.g., `default_rag_pipeline`), enhancing CI/CD.
- 💡 **IntelliJ IDEA Run Configurations:** Included new `.idea` run configurations to simplify local Docker image builds for `aihub_pipeline` and `default_rag_pipeline` within IntelliJ IDEA.
- ✨ **Standardized `StartEvent` Creation:** Added a `from_raw_data` class method to `StartEvent`, providing a standardized way to construct start events from raw data, improving API consistency.
- ✨ **Granular Process Discovery Events:** Introduced `ProcessConfigSpecs`, `ProcessClassDiscoveryResponseEvent`, and `ProcessInstanceDiscoveryResponseEvent` to provide more detailed and structured information during process discovery.
- ✨ **Dynamic Process Configuration:** Enhanced `ProcessStartEvent` with a `process_config` field and a `from_raw_data` class method, allowing process configurations to be dynamically passed at the start of a walkthrough.
- 📄 **Structured Process Topics:** Introduced `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` to create a more granular and hierarchical structure for NATS topics related to processes.
- 🗄️ **Persistent Process Configurations:** Implemented new MongoDB entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to enable saving and retrieving process configurations, supporting persistent and shareable process setups.
- 🧪 **Comprehensive Process Dispatcher Tests:** Added new unit and integration tests for `ProcessDispatcher`, focusing on its configuration loading, context management, and event handling logic.
- 🧪 **Comprehensive Process Service Tests:** Introduced new integration and unit tests for `ProcessService` and `ProcessConfig` database operations, ensuring robust data persistence and retrieval.
- ✨ **Process Walkthrough Context:** Implemented `WalkthroughContext` as a dedicated Redis-backed context for managing state specific to a single process execution, improving modularity and isolation.
- 🧹 **Database Cleanup Utility:** Added `delete_if_exists_for_class_and_id` method to `AgentConfigEntityDocument`, allowing programmatic cleanup of specific agent configurations for testing or re-initialization.
- 🧪 **Agent API Test Cleanup:** Added `cleanup_db_and_cache` fixture to ensure a clean database and cache state before and after agent API tests.
- 🧪 **Agent Config Test Cleanup:** Added `cleanup_db_and_cache` fixture to ensure a clean database and cache state before and after agent config tests.
- 🧪 **Agent Service Test Cleanup:** Added `cleanup_db_and_cache` fixture to ensure a clean database and cache state before and after agent service tests.
- 🧪 **Process API Test Cleanup:** Added `cleanup_db_and_cache` fixture to ensure a clean database and cache state before and after process API tests.
- 🧪 **Custom Agent Config Test:** Added `test_chat_completions_json_with_custom_agent_config` to verify the application of custom agent configurations during chat completions.
- 🐳 **Dagster Integration in Docker Compose:** Fully integrated the Dagster stack (webserver, daemon, and OAuth2 Proxy for authentication) into `docker-compose.latest.yml`, enabling complete pipeline orchestration and observation.
- 🐳 **Dagster PostgreSQL Configuration:** Added `dagster.yaml` to centralize Dagster's persistence configuration using PostgreSQL for run, event log, and schedule storage.

### Changed
- 📦 **Dynamic Agent Docker Entrypoint:** Modified the `LLMWrappingAgent` Dockerfile to use an environment variable for the agent name in its entrypoint, enhancing flexibility.
- ⚙️ **Explicit AgentRunner Configuration:** Updated `LLMWrappingAgent` to explicitly pass NATS server and Redis URL configurations to `AgentRunner`, improving clarity and control over environment-specific setups.
- 📦 **Streamlined Docker Builds:** Simplified Python Docker image builds by installing Poetry directly in the final runtime image and removing redundant intermediate virtual environment copying.
- 🚀 **Agent Controller Discovery:** Streamlined agent discovery in `AgentController` to directly consume `AgentDTO` objects from the `AgentService`, centralizing DTO conversion in the service layer.
- 🖼️ **Universal Image Resolution:** Improved `combine_nodes_in_order` and the frontend image component to correctly resolve and display images from both Azure Blob Storage and S3/MinIO by supporting `s3://` URIs.
- ⚙️ **Pipeline `DataLakeFile` Creation:** Refactored `AzureDataLakeIOManager` to delegate `DataLakeFile` instantiation to the new `AzureDataLakeClient` abstraction, encapsulating cloud-specific logic.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core data lake operations (fetching, deleting files, removing) in pipeline ops to utilize the new `AbstractDataLakeClient` interface, enhancing cloud provider flexibility.
- ⚙️ **Process Controller Configuration:** Updated `ProcessController` to dynamically fetch process instance configurations before submitting start forms, ensuring the correct configuration is applied.
- ⚙️ **Explicit `WorkRequestEvent` Process ID:** Re-added the `process_id` field to `WorkRequestEvent` to explicitly associate work requests with specific process instances.
- 🔍 **Enhanced JetStream Logging:** Added debug log statements for received and deserialized messages in `JetStreamEventStore`, improving visibility into NATS JetStream event processing.
- ⚙️ **Broader Dispatchable Workflow Events:** Expanded `DispatchableWorkflow` to allow steps to wait for and dispatch both `ControlEvent` and general `WorkEvent` types, increasing workflow flexibility.
- ⚙️ **Process Configuration in `ProcessEntity`:** Updated `ProcessEntity` to store `ProcessConfig` as a reference to `ProcessConfigEntityDocument` for custom configs and an embedded `ProcessConfigEntityEmbeddedDocument` for default configs, enhancing data modeling.
- ⚙️ **ProcessConfig Enhancements:** Added `process_class` field to `ProcessConfig` for clearer identification and introduced a `from_entity` class method for seamless conversion from persistence entities.
- ⚙️ **Process Delegator Adaptations:** Updated agent and process delegators to align with the new process class/instance distinction and new topic management hierarchy.
- ⚙️ **Process Runner Updates:** Adapted `ProcessRunner` to the new process class/instance model, supporting class-based discovery and using a `default_process_config`.
- ⚙️ **Process Dispatcher Logic:** Overhauled `ProcessDispatcher` to dynamically load `ProcessConfig` via `WalkthroughContext`, manage process class/instance topic conversions, and refine event publishing based on `WorkEvent` and `WorkRequestEvent` types.
- 🧪 **Playground Data Lake Configuration:** Switched the `playground` Dagster definitions to use S3/MinIO data lake resources and configured `DocumentParserResource` to use `DOCUMENT_INTELLIGENCE` by default.
- ⬆️ **Dependency Updates:** Updated `dagster-webserver`, `dagster-postgres`, `dagster-azure` to newer versions and added `boto3` and `s3fs` for S3 support.
- ⬆️ **Generated SDK Schema Update:** Updated the default `created` timestamp in `ModelDetailsSchema` in the generated SDK.
- ⬆️ **MinIO and Postgres Docker Image Updates:** Updated MinIO Docker image to a newer release and configured MinIO with Traefik labels for external exposure via a domain.
- 🔒 **Internal Service Port Concealment:** Removed external port mappings for PostgreSQL, NATS, and Redis in `docker-compose.latest.yml`, enhancing security by limiting external access to these internal services.

### Fixed
- 🐛 **Circular Import Resolution:** Moved `ProcessService` import within `UserWithAccessDTO` to resolve a potential circular dependency.
- 🖼️ **Frontend Image Path Resolution:** Corrected `ResolveImageComponent` in `aihub_web` to properly handle image source paths with `://` prefixes, ensuring images are consistently resolved and displayed.
- 🐛 **Dispatcher Shutdown Logging:** Added an explicit return for `BaseDispatcher`'s `stop` method if not initialized to prevent errors during shutdown.
- 🐛 **Event Handler Acknowledgment:** Ensured `JetStreamEventStore` always attempts to acknowledge messages, even after an error in the handler, to prevent redelivery loops.

### Refactor
- 🧹 **Centralized Contexts:** Moved `BaseContext` from `aihub_agent` to `aihub_lib`, promoting code reuse across microservices.
- 🔄 **Refined Agent Topic Hierarchy:** Restructured agent NATS topics to explicitly distinguish between `AgentClassTopic` (for class definitions) and `AgentInstanceTopic` (for running instances), enhancing message routing granularity.
- 🧹 **Unified Infrastructure Imports:** Relocated `NatsConfig` and `RedisConfig` into a new `aihub_lib.infrastructure` package for clearer logical grouping and improved project structure.
- 📄 **Docstring Cleanup:** Removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) docstrings and client fixture docstrings.
- 🔄 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services (`keys.primary_key` to `keys.key1`) with recent API changes, ensuring robust and consistent authentication.
- 🗑️ **Deprecated Discovery Event Removal:** Removed the generic `DiscoveryRequestEvent` as it is replaced by more specific class and instance discovery request events.
- 🔄 **Refined Process Event Type Hierarchy:** Updated `ProcessExceptionEvent` and `ProcessStopEvent` to inherit directly from `WorkEvent` for a cleaner event type hierarchy.
- 🧹 **Streamlined JSSubscriber Subscriptions:** Removed the generic `for_agent_instance_events` from `AgentJSSubscriber` in favor of more specific control event subscriptions.
- 🔄 **Process Subscription Refinement:** Restructured `ProcessJSSubscriber` and `ProcessNCSubscriber` methods to align with the new process class/instance distinction and clearer `WorkEvent` types.
- 🏗️ **Streamlined Process Topic Management:** Refactored `ProcessInstanceTopicManager` and `ProcessWalkthroughTopicManager` to inherit from `ProcessClassTopicManager`, simplifying their structure and promoting reuse.
- 🗑️ **Deprecated Process Topic Removal:** Removed the old `ProcessTopic` as it is superseded by the new hierarchical `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic`.
- 🔄 **Refined Event Persistence Topics:** Updated `PersistedAgentEventEntity` and `PersistedProcessEventEntity` to use the new `AgentInstanceTopic` and `ProcessInstanceTopic` for improved data consistency.
- 🗄️ **Decoupled Process Persistence:** Refactored `ProcessEntity` to use explicit parameters for creation and update, handling persistence of `ProcessConfigEntityDocument` and `ProcessConfigEntityEmbeddedDocument` directly, improving reusability.
- ⚙️ **Centralized `DataLakeFile` Creation:** Moved the URI-based `DataLakeFile` creation logic from the `DataLakeFile` class into the cloud-specific `AbstractDataLakeClient` implementations for better encapsulation.
- 🏗️ **Refactored Azure Data Lake Resources:** Renamed `DataLakeClientResource` to `AzureDataLakeClientResource` and `DataLakeFileSystemResource` to `AzureDataLakeFileSystemResource`, and updated their inheritance to new abstract base classes, aligning with multi-cloud strategy.
- 🗑️ **Removed Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline` resources.
- 🧹 **Agent Playground Cleanup:** Cleaned up various agent playground examples to align with new configuration models.
- 🧹 **Process Playground Cleanup:** Cleaned up various process playground examples to align with new configuration models.
- 🗑️ **Removed Test Files:** Deleted outdated test files (`test_agent_config_start_event.py`) as their logic is now covered by other, more integrated tests or made obsolete by architectural changes.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🧩 **Enhanced Process Context Management:** Added `WalkthroughContext` for dedicated per-walkthrough state storage in agentic processes, improving process state management.
- 🗄️ **Persistent Process Configurations:** Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to allow custom process configurations to be saved and retrieved.
- 🏷️ **Hierarchical Process Data Transfer Objects (DTOs):** Implemented `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to provide a clear, layered representation of process information in API responses.
- 🔗 **Granular Agent and Process Topics:** Introduced new hierarchical NATS topic models (`AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassDiscoveryTopic`, `ProcessInstanceDiscoveryTopic`, `PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) for more precise event routing and subscription.
- 🚀 **Standardized Event Creation:** Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent`, providing consistent and simplified event instantiation from raw data.
- 🧰 **Database Cleanup Utility:** Added `delete_if_exists_for_class_and_id` method to `AgentConfigEntityDocument` for cleaner test setups and configuration management.
- 📊 **Integrated Dagster Stack:** Incorporated `oauth2proxy`, `dagster-webserver`, and `dagster-daemon` services into `docker-compose.latest.yml`, providing a complete local environment for pipeline development and execution.
- 🧪 **Comprehensive Process Dispatcher Testing:** Added extensive unit and integration tests for `ProcessDispatcher`, ensuring robust handling of process events and configurations.
- ➕ **Event Data Field:** Added a `process_id` field to `WorkRequestEvent` for improved traceability in process orchestration.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- ⚙️ **Dynamic Process Configuration Loading:** `ProcessDispatcher` now dynamically loads process configurations from `ProcessStartEvent` or `WalkthroughContext`, enabling custom overrides and consistent runtime settings.
- 📈 **Refined Process Dispatching and Delegation:** `ProcessRunner`, `ProcessDispatcher`, and delegators now primarily operate at the `ProcessClass` level, with `ProcessInstance` resolution handled dynamically, enhancing scalability and modularity.
- 📊 **Updated Dagster Storage Configuration:** Modified `dagster.yaml` to use separate Postgres storage configurations for runs, event logs, and schedules, and increased `max_concurrent_runs` for improved pipeline concurrency.
- 🐳 **Streamlined Pipeline Deployment:** Changed `DAGSTER_HOME` path and Dagster entrypoint in `aihub_pipeline` Dockerfiles for better container optimization and module resolution.
- 🧪 **Default Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⚡️ **Refined NATS/Redis Security:** Removed external port exposures for NATS and Redis services in `docker-compose.latest.yml`, enhancing security by limiting direct external access.
- 🌐 **Simplified Phoenix Traefik Routing:** Updated Traefik configuration in `docker-compose.latest.yml` for Phoenix, simplifying its ingress rules.
- 🔑 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.
- 📝 **Process Data Structure:** Removed the `process_id` field from `ProcessStopEvent` to streamline process event data.
- 🎯 **Broadened Event Handling:** The `DispatchableWorkflow.get_steps_waiting_for_event` method now accepts both `ControlEvent` and `WorkEvent` types, allowing more diverse event triggers.
- 📦 **API Agent Discovery:** Changed `AgentController` and `AgentService` to directly return `AgentDTO` instances from discovery, simplifying API responses.
- 📌 **Pipeline Resource Defaults:** `NAMESPACE_NAME` and `STORE_NAME` in `aihub_pipeline` now dynamically derive from `DATALAKE_DIRECTORY_NAME` and `DATALAKE_CONTAINER_NAME` for more consistent resource naming.
- 🏷️ **Process Configuration Field:** The `ProcessConfig` model now includes an explicit `process_class` field for better process identification.

### Removed
- 🗑️ **Obsolete Test Files:** Removed `test_agent_config_start_event.py` as its functionality is now covered by more integrated tests or made obsolete by architectural changes.
- 🗑️ **Generic Discovery Event:** Removed `DiscoveryRequestEvent` as it has been superseded by more specific class and instance discovery events.
- 🗑️ **Legacy Process Topic:** Eliminated `ProcessTopic` as it was replaced by a new hierarchical topic model (`ProcessInstanceTopic`, `ProcessClassTopic`).
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 🔄 **Consolidated Base Context:** Moved `BaseContext` from `aihub_agent` to `aihub_lib`, making it a core, reusable library component across microservices.
- ⚙️ **Refined NATS Topic Management:** Overhauled agent and process NATS topic management to align with the new class/instance hierarchy, impacting dispatchers, runners, delegators, and subscribers.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- 🧪 **Standardized Test Fixtures:** Introduced new test fixtures for database and cache cleanup in `aihub_api` for both agents and processes, ensuring consistent test environments.
- 📦 **Streamlined Event Hierarchy:** Changed `ProcessExceptionEvent` and `ProcessStopEvent` to inherit directly from `WorkEvent`, simplifying the event inheritance hierarchy.
- 💡 **Unified `DataLakeFile` Instantiation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🧹 **Cleanup of `BaseDispatcher`:** Removed redundant explicit `_background_tasks` sets from `BaseDispatcher` as `asyncio.Task` instances are now managed more implicitly.
- ✏️ **Standardized Persistence Entity Methods:** Renamed `from_dto` to `from_specs` in various persistence entities for naming consistency and clarity.

---



## [v0.226.0] - 2025-07-25 - Focused Evolution: Azure Specialization and Core Unification

### Added
- ✨ **Unified Process Topic Model**: Introduced a new `ProcessTopic` model that consolidates previous process topic structures, simplifying NATS subject parsing and generation for processes.
- ✨ **New `DiscoveryRequestEvent`**: A new base class for all discovery requests, enhancing consistency across agent and process discovery.
- 📈 **Azure AI Search Vector Store Re-enabled**: Re-introduced `AzureAISearchVectorStoreResource` and a corresponding factory function, providing support for Azure AI Search as a vector store option.
- 🧪 **Agent Config Precedence Tests**: Added new tests to validate `AgentConfig` precedence, ensuring configurations from `StartEvent` or database are prioritized over defaults.
- 📊 **`DataLakeFile.from_uri` Static Method**: Added a new static method to `DataLakeFile` for simplified creation directly from a URI, streamlining data lake interactions.
- 🏗️ **`mongo_aisearch_storage_context_resources` Factory**: A new factory function to simplify the setup of MongoDB document store with Azure AI Search vector store.
- 📊 **Walkthrough-Scoped Event Subscription**: Added a new method in `ProcessWalkthroughTopicManager` for more granular event observation within a process walkthrough.

### Changed
- ⚙️ **Consolidated Agent & Process NATS Topics**: Agent and Process NATS topic hierarchies have been significantly streamlined, replacing separate instance-specific topics with unified `AgentTopic` and `ProcessTopic` models, simplifying topic management and event routing.
- ⬆️ **Dependency Version Rollback**: Rolled back versions of `dagster-webserver`, `dagster-postgres`, and `dagster-azure`, and adjusted the `aihub_lib` dependency tag, aligning project versions.
- 💡 **Streamlined Agent Config Loading**: `AgentDispatcher` now has simplified internal config loading logic, and `AgentRunner` initializes with a single `process_config` parameter. Delegators are now initialized with explicit process IDs.
- ⚡ **Enhanced Exception Handling for Agents & Processes**: `AgentDispatcher` and `ProcessDispatcher` now explicitly mark an execution context as "crashed" upon `ExceptionEvent`, ensuring no further steps are executed in a failed run.
- 🔌 **Simplified API Agent Discovery**: The API's `AgentService` and `AgentEndpointsDiscoveryService` now use a simplified agent discovery method and directly convert discovered agents to `AgentDTO`s, streamlining agent exposure.
- 🌐 **Refined API Process Discovery**: The API's `ProcessService` and `ProcessEndpointsDiscoveryService` now use a unified `discover_processes` method and `ProcessDTO`, simplifying the process discovery mechanism and removing several intermediate DTOs.
- 🛠️ **Unified Event Creation for API Endpoints**: Agent `StartEvent`s and process `WorkEvent`s are now constructed directly from raw data via `BaseEvent.deserialize_event`, standardizing event creation from API endpoints.
- 🖼️ **Simplified Image URL Generation**: The `combine_nodes_in_order` utility for RAG contexts no longer has special handling for S3-specific prefixes and uses a unified file access service for image URLs.
- ⚙️ **Standardized Data Lake Client Usage**: Operations in `aihub_pipeline` now directly use the native Azure `FileSystemClient` instead of an abstract wrapper, simplifying data lake interactions and removing intermediate client classes.
- 📦 **Docker Environment Path Adjustments**: Updated `DAGSTER_HOME` environment variable and `ENTRYPOINT` paths in Dagster Dockerfiles, aligning with containerization best practices.
- 📊 **Process Discovery Response Content**: `ProcessRunner`'s discovery response (`ProcessDiscoveryResponseEvent`) now directly includes `process_id` and `process_config`, simplifying the configuration specification in discovery.
- ⚙️ **Process Dispatcher Event Publication**: `ProcessDispatcher` now strictly enforces that it only publishes `WorkRequestEvent`, `ProcessExceptionEvent`, or `ProcessStopEvent`, streamlining its outgoing event types.
- 📝 **Clarified File Access Service Descriptions**: File-related API endpoint descriptions (`FileService`) now explicitly mention Azure Blob Storage/Data Lake, reflecting the current cloud provider focus.
- 🚀 **Process Runner Default Configuration**: `ProcessRunner` now uses `DOCLING` as the default document parser instead of `DOCUMENT_INTELLIGENCE`, influencing default RAG pipeline behavior.
- 🗺️ **Playground Namespace & Store Names**: `NAMESPACE_NAME` and `STORE_NAME` in the `default_rag_pipeline` playground have been changed to generic "test" values.
- ⚙️ **Dagster Storage Configuration**: Dagster's storage configuration updated to use `storage.postgres` syntax and environment variables for credentials, and adjusted the maximum concurrent runs.
- 🐳 **Postgres Port Exposure**: Postgres port 5432 is now explicitly exposed in `docker-compose.latest.yml` for direct access, and the `dagster` database is no longer managed by the multi-database initialization script.

### Fixed
- 🐛 **Process Delegator Thread Validation**: `AgentDelegator` now includes an explicit check for `thread.process_id` in addition to `thread.process_class` to ensure agent events are correctly routed to the relevant process walkthrough.
- 🐞 **API Endpoint Duplication**: Removed a duplicated call to `.get_process_open_forms()` in the API development playground, resolving a minor configuration oversight.

### Refactor
- 🧹 **Unified Agent Topic Model**: Consolidated `AgentClassTopic` and `AgentInstanceTopic` into a single `AgentTopic` model, simplifying agent-related NATS topic management.
- 🔄 **Module Restructuring for Core Context & Configs**: Moved `BaseContext`, `NatsConfig`, and `RedisConfig` into more appropriate module locations within `aihub_agent` and `aihub_lib`, respectively, improving logical grouping and consistency.
- ⚙️ **Streamlined NATS Topic Manager Hierarchy**: Re-architected process topic managers to simplify their inheritance structure, promoting clearer relationships and reducing redundancy.
- 🏗️ **Simplified Data Lake Client Resources**: Refactored Azure Data Lake client and file system resources (`DataLakeClientResource`, `DataLakeFileSystemResource`) to directly return the native Azure SDK clients, removing intermediate wrapper classes.
- 🧹 **Direct File Access Service Usage**: `FileController` and `FileService` now directly use `AnonymousFileAccessService` methods, simplifying file access logic and removing an intermediate configuration factory.
- 🔄 **API Process DTO Consolidation**: Consolidated `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` into a single, comprehensive `ProcessDTO`, simplifying API data representation for processes.
- 🧹 **Renamed Internal API Methods**: Renamed private API service methods (e.g., `_discover_agent_class` to `discover_agent_class`, `_send_event` to `send_event`) to reflect their public utility and improve API discoverability.
- 🗂️ **Test Fixture Documentation**: Added explicit `Args` documentation to API test client fixtures for improved clarity and maintainability.
- 🧹 **Logging Refinement**: Simplified logging statements within `JetStreamEventStore` by removing redundant debug messages and making exception messages more direct.
- ⚙️ **Dispatcher Lifecycle Management**: `BaseDispatcher`'s `stop` method no longer explicitly sets an initialization flag or logs, indicating its lifecycle management might be external or implicitly handled.
- 📄 **Docstring Enhancements**: Improved docstrings in IAC resources for better clarity on arguments and return types.
- 🧹 **Dagster Home Path Standardization**: Standardized `DAGSTER_HOME` paths in Dagster Dockerfiles to a more conventional `/opt/dagster/dagster_home`, promoting consistency across deployments.

### Removed
- 🗑️ **Multi-Cloud Data Lake Abstraction (S3/MinIO Support)**: Removed generic interfaces (`AbstractDataLakeClient`, `AbstractAnonymousFileAccessService`) and all concrete implementations for S3/MinIO storage (`S3DataLakeIOManager`, `S3DataLakeClient`, `S3DataLakeFileSystem`) from pipelines and core libraries. This simplifies the data lake layer to focus on Azure.
- 🗑️ **Process Configuration Persistence (Dedicated Entities)**: Eliminated `ProcessConfigEntity` and its document/embedded subclasses, streamlining how process configurations are stored by embedding them directly within `ProcessEntity`.
- 🗑️ **Agent-Specific Start Event Construction**: Removed the `from_raw_data` method from `StartEvent`, standardizing how agent start events are created.
- 🗑️ **Process-Specific Start Event Construction**: Removed the `process_config` field and `from_raw_data` method from `ProcessStartEvent`, simplifying its structure as a general work event.
- 🗑️ **Process Walkthrough Context**: Removed `WalkthroughContext` and its related files, indicating a change in how process-specific runtime state is managed.
- 🗑️ **Deprecated NATS Topics & Managers**: Removed `AgentClassTopic`, `ProcessClassTopic`, `ProcessInstanceTopic` and their corresponding topic managers (`ProcessClassTopicManager`), simplifying the NATS topic hierarchy for agents and processes.
- 🗑️ **Extensive Test Files**: Deleted numerous test files related to agent configuration, agent service database integration, and process dispatcher, simplifying and consolidating the test suite.
- 🗑️ **Agent Configuration Deletion Utility**: Removed the `delete_if_exists_for_class_and_id` method from `AgentConfigEntityDocument`.
- 🗑️ **General Event Dispatcher Methods**: Removed the `_publish_work_event` method from `AbstractEntityDelegator`, as event publishing is now handled more directly within specific delegators.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📦 **Dagster Deployment Stack:** Integrated **Dagster Webserver, Daemon, and OAuth2 Proxy** into `docker-compose.latest.yml`, enabling a full Dagster deployment for pipeline orchestration.
- 📄 **New Process Configuration Entities:** Added `ProcessConfigEntity`, `ProcessConfigEntityDocument`, and `ProcessConfigEntityEmbeddedDocument` for robust database persistence of process configurations.
- ⚙️ **Process Configuration Specifications:** Introduced `ProcessConfigSpecs` to formally define the schema of process configurations, aiding dynamic UI generation and validation.
- ⚡️ **Walkthrough Context:** Added `WalkthroughContext` in `aihub_process` for managing per-walkthrough state, improving process execution isolation and robustness.
- 🧪 **Extensive Process Tests:** Added new, comprehensive unit and integration tests for `ProcessService`, `ProcessDispatcher`, and process config database operations.
- 📊 **New Process DTOs:** Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` for a more granular and organized representation of process information in the API.
- 🗑️ **Agent Config Cleanup Utility:** Added `delete_if_exists_for_class_and_id` method to `AgentConfigEntityDocument` for better lifecycle management of agent configurations.
- ⚙️ **Start Event Utility:** Added `from_raw_data` class method to `StartEvent` and `ProcessStartEvent` for streamlined event creation from raw input data.
- 📦 **S3 Configuration:** Added `S3Config` for managing S3-compatible storage service settings across the platform.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded **Dagster** (`dagster-webserver`, `dagster-postgres`, `dagster-azure`) and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- 🛡️ **Internalized Core Services:** **Postgres, NATS, Redis, and MongoDB** services in `docker-compose.latest.yml` are no longer exposing their ports externally, enhancing security by limiting external access within the Docker network.
- ⚙️ **Dagster Infrastructure Configuration:** Updated `dagster.yaml` to use explicit `dagster_postgres` classes for storage and increased `max_concurrent_runs` from 3 to 10 for better concurrency.
- ⚙️ **Process Dispatcher & Runner:** Major overhaul of `ProcessDispatcher` and `ProcessRunner` to utilize the new hierarchical process topic structure, handle `default_process_config`, and inject `ProcessConfig` into steps.
- ⚙️ **Process Event Structure:** Modified `ProcessStartEvent` to include `process_config` and refactored `ProcessStopEvent` by moving `process_id` to its parent `WorkRequestEvent` for consistency.
- ⚙️ **Agent Dispatcher & Runner:** Updated to use `AgentClassTopic` and `AgentInstanceTopic` for NATS messaging, and streamlined agent discovery and event handling.
- 📚 **Agent/Process Discovery Logic:** Refined discovery services in `aihub_api` to expose `AgentInstanceDTO` and `ProcessInstanceDTO` reflecting the configured agent/process instances, rather than just class definitions.
- ⚙️ **Process Delegation Logic:** Updated `AbstractEntityDelegator`, `AgentDelegator`, and `ProcessDelegator` to align with the new process topic hierarchy (`ProcessClassTopic`, `ProcessInstanceTopic`) and `WalkthroughContext`.
- ⚙️ **Azure Data Lake IO Manager:** Updated `AzureDataLakeIOManager` to interact with the new `AzureDataLakeClient` and leverage its `create_data_lake_file_from_uri` method.
- 📦 **Dagster Dockerfiles:** Adjusted `DAGSTER_HOME` and entry points in `aihub_pipeline` Dockerfiles.
- ⚙️ **Image Resolution in Web UI:** Updated `ResolveImageComponent.vue` to handle `s3://` URLs.
- ℹ️ **Improved NATS Message Logging:** Enhanced `JetStreamEventStore` to include more detailed logging for received messages.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for **Azure AI Search** as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Deprecated `DiscoveryRequestEvent`:** Removed `DiscoveryRequestEvent` as it has been superseded by more specific discovery event types (`ClassDiscoveryRequestEvent`, `InstanceDiscoveryRequestEvent`).
- 🗑️ **Obsolete Process Topic:** Removed the generic `ProcessTopic` in favor of more granular `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic`.
- 🗑️ **Redundant Agent Event Subscriber:** Removed `for_agent_instance_events` from `AgentJSSubscriber` as its functionality is now covered by more specific control event subscriptions.
- 🗑️ **Legacy Process Test File:** Deleted `test_agent_config_start_event.py` from `aihub_agent` playground, as its logic is now covered by other tests or architectural changes.
- 🗑️ **Deprecated `DataLakeFile.from_uri`:** Removed the `from_uri` static method from `DataLakeFile` as its logic is now encapsulated within cloud-specific `AbstractDataLakeClient` implementations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages (`nats` and `redis`) for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- 🧹 **Centralized `BaseContext`:** Moved `BaseContext` from `aihub_agent` to `aihub_lib` for broader reusability across agent and process domains.
- 🔄 **Hierarchical NATS Topic Structure:** Major refactoring of NATS topics and topic managers for both agents and processes, introducing `AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`, and `PartialProcessTopic` for a more explicit and scalable hierarchy.
- ⚙️ **Unified DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🧹 **API Endpoint Discovery Services:** Renamed internal endpoint creation methods (`create_endpoint`, `create_form_get_endpoint`) to private (`_create_endpoint`, `_create_form_get_endpoint`) for better encapsulation.
- 🧹 **API Cache Management:** Made `clear_cache` methods in API services private (`_clear_cache`) as they are primarily for internal testing/development.
- 🧹 **Process Persistence Entities:** Restructured `ProcessEntity` to reference external `ProcessConfigEntityDocument` for configured processes and embed `ProcessConfigEntityEmbeddedDocument` for default configurations, improving data modeling.
- 🧹 **Test File Organization:** Consolidated new process-related test files into a single `playground/testing/tests/test_ProcessDispatcher.py`.

---



## [v0.226.0] - 2025-07-24 - Flexible Agents: Dynamic Configurations and Enhanced Discovery

### Added
- 🦾 **Dynamic Agent Configuration:** Agents can now receive custom configurations directly via a `StartEvent` or load them from a database, enabling dynamic overrides of default settings for each run.
- 🚀 **Granular Agent Discovery:** Introduced a refined discovery mechanism that distinguishes between agent *classes* and specific agent *instances*, allowing more detailed introspection and management of agent definitions and their configured deployments.
- 🗄️ **Persistent Agent Configurations:** Custom agent configurations can now be stored in and retrieved from the database, enabling persistent, shareable, and versionable agent setups across deployments.
- 🔌 **Standardized Vector Store Configurations:** Implemented dedicated Pydantic models (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`) for defining and validating vector store settings directly within agent configurations.
- ✨ **Hierarchical Document Headings in RAG Context:** Enhanced RAG context generation to dynamically render document headings (H1-H6) and explicit content/summary tags, providing richer structural information for Large Language Models.
- 🔒 **HTML Escaping for RAG Content:** Implemented automatic HTML escaping for headings and content within RAG context to prevent rendering issues and enhance security.
- 📦 **New Core Persistence Entities:** Introduced `AgentConfigEntity`, `AgentConfigEntityDocument`, and `AgentConfigEntityEmbeddedDocument` for robust management of agent configurations in MongoDB.
- ⚙️ **Refined Model Creation Service:** Added `ModelCreationService` with utilities for dynamically creating Pydantic models from event schemas and agent configuration specifications.
- 🧪 **Comprehensive Test Suites:** Expanded test coverage with new unit and integration tests for `AgentDispatcher`, `AgentService`, and agent configuration database operations, improving reliability.
- 🛠️ **Pipeline Job Utility:** Introduced `materialize_asset_job` to simplify the creation of jobs for materializing specific asset selections in data pipelines.
- 📅 **Automated Pipeline Workflows:** Implemented new daily scheduled jobs for observing source data and managing document removal processes within the pipeline playground.
- 🌐 **Integrated Web Frontend Deployment:** Added a new `web` service to `docker-compose.latest.yml`, including its Docker image, environment variables, and Traefik rules, for streamlined full-stack deployment.

### Changed
- ⚙️ **Streamlined Agent Configuration Loading:** The agent dispatcher now prioritizes configurations from the `StartEvent`, then from the database, finally falling back to the `default_agent_config` defined in the runner.
- 🔄 **Unified LLM and Vector Store Configuration Types:** Agent configurations now use more specific type unions for LLMs and embedding models, and concrete vector store configuration objects, enhancing type safety and clarity.
- 📄 **API Event Models Update:** `StartEvent` and `UserMessageEvent` models in the API now include an optional `agent_config` field to support dynamic configuration overrides.
- 📊 **Pipeline Automation Strategy:** Document and data lake file removal assets transitioned from eager automation to job-driven scheduling for more controlled execution.
- 🎛️ **SharePoint I/O Manager:** The SharePoint observable asset now uses a dedicated `sharepoint_io_manager` for more appropriate data handling.
- 🇩🇪 **Default Ingested Node Language:** The default language for newly ingested nodes has been updated from English to German.
- 🐳 **Service Configurations:** Adjusted environment variables and Traefik rules for various services in `docker-compose.latest.yml` to support the new web service and enhanced security.

### Fixed
- 🐛 **Graceful Missing Profile Image Handling:** Corrected `AzureGraphService` to handle missing user profile images (404 response) more gracefully, preventing unnecessary warnings.
- 🐞 **Robust Figure Deletion in Pipelines:** Improved the data lake figure deletion process to prevent errors when associated figure directories do not exist.
- 💬 **SDK Typo Correction:** Corrected a minor typo in the `ProcessDTO` description within the generated SDK.

### Removed
- 🗑️ **Deprecated AgentConfig Fields:** The generic `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO` classes, allowing for more flexible, agent-specific prompt and UI customization in subclasses.
- 🗑️ **Redundant Timestamp Utility:** The `format_unix_timestamp` utility function has been removed as date and time handling for document metadata is now managed more efficiently by the underlying system.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul:** Major refactoring of `AgentDispatcher` and `AgentRunner` for streamlined internal logic, simplified argument injection, and explicit background task management.
- 🔄 **Unified Agent Discovery Architecture:** Consolidated agent discovery into a more consistent model by abstracting class-level and instance-level discovery concepts across NATS events, topics, and DTOs.
- 🗄️ **Centralized Agent Configuration Persistence:** Re-architected agent configuration persistence by introducing new core entities and allowing `AgentEntity` to reference or embed configurations, enhancing data co-location and object relationships.
- 📦 **Streamlined LLM and Vector Store Integrations:** Replaced generic LLM/embedding configuration types with concrete implementations and simplified vector store instantiation through dedicated configuration objects and conversion methods.
- 📁 **Enhanced Project Structure:** Reorganized test runners into `simulation/agent` and `simulation/process` directories, and renamed `aihub_web/.playground` to `aihub_web/.app` for better project organization.
- ⚙️ **API Endpoint Generation:** The API now dynamically generates endpoints for agent instances, supporting the injection of agent configurations into `StartEvent` payloads.
- 📄 **API DTO Hierarchy:** Introduced a more granular DTO hierarchy for agent representation (`AgentClassDTO`, `AgentInstanceDTO`, `MinimalAgentDTO`), improving API clarity and consistency.
- 🧹 **Internal Naming Consistency:** Standardized various internal naming conventions, such as renaming `EventModelCreationService` to `ModelCreationService` and `_get_endpoint_name` to `_get_endpoint_base_path`.
- 🧹 **Asyncio Task Management:** Implemented consistent `asyncio.Task` handling across dispatchers and subscribers to ensure proper lifecycle management and prevent premature garbage collection.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🐳 **Docker Build and Nginx Configuration for Web**: Added a new Dockerfile and Nginx configuration for building and serving the web application.
- 🔌 **Client-Side Configuration Loader**: Implemented a new plugin for dynamically loading runtime configuration on the client-side, improving deployment flexibility.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Agent Event API Routes Renamed**: Agent-specific event API routes for threads and timeseries were renamed (e.g., `/events/agents/threads`, `/events/agents/timeseries`) for clarity.
- 📚 **RAG Context Prompt Role Updated**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages.
- 💬 **`WorkEvent` Enhancements**: `WorkEvent` and its subclasses (e.g., `HumanWorkEvent`) now include default display names and descriptions, and `HumanWorkEvent` has been extended to support dynamic form definitions.
- 🎯 **`HumanWorkRequestEvent` Improvements**: Enhanced with detailed user targeting (user IDs, emails, roles), notification options, and robust validation for dynamically generated forms.
- 💾 **Database Indexing Enhancements**: Improved database indexing for `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` to optimize query performance.
- 🪵 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue where image URLs in RAG prompts were not consistently processed, ensuring images are correctly referenced.
- 🛡️ **Judge Output Schema Modification Prevented**: Implemented deep copying of the `JudgeOutput` schema to prevent unintended modifications during evaluation.
- ⏱️ **Process Test Runner Timeout Logging**: Enhanced timeout logging in the `ProcessTestRunner` to provide more detailed diagnostic information.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and WebSocket event classes (`WsServerEvent` to `ContextualizedAgentEvent`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🎨 **Frontend Project Restructuring**: The web application's main source code was moved from `.playground` to a new `.app` directory, streamlining the development setup.
- 🔄 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related components for improved consistency.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that automatically created draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Frontend Playground**: The `.playground` directory for the web application has been removed following the restructuring to `.app`.
- 🗑️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled custom environment variable configuration for API services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 📦 **Automated Web Image Build and Release Workflow**: Introduced a new GitHub Actions workflow for building and releasing web images, triggered by tag creation, manual dispatch, or specific branch pushes.
- 🏗️ **Improved Frontend Docker Build**: Implemented a new client-side configuration loader and integrated Nginx for the web application, optimizing Docker build contexts and ensuring dynamic environment variable injection in containerized deployments.
- ⚡️ **Enhanced Process Event Payloads**: Extended process-specific event payloads (e.g., `AnalyzedCV`) to include more relevant data points like `cv_name`, improving data context within workflows.

### Changed
- ⚙️ **Comprehensive Local Deployment Overhaul**: Replaced the previous single Docker Compose file with a set of modular files (`docker-compose.latest.yml`, `docker-compose.dev.yml`, etc.) and introduced new core services (Postgres, OpenWebUI, Traefik, Milvus) for a more robust and scalable local development and deployment environment.
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.
- 📦 **API/Bot Service Production Dependency**: Added Gunicorn as a production dependency for the API and Bot services, enabling robust WSGI server capabilities.
- ⚡️ **Enhanced Event Query Performance**: Added new database indexes to `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity`, significantly improving query performance for event and user retrieval.
- 🚀 **Authentication Cache Improvement**: Increased the maximum size of the JWKS (JSON Web Key Set) cache in the OAuth2 authentication handler, reducing repetitive external requests and improving authentication performance.
- 🧰 **Deserialization Flexibility**: Adjusted external agent event deserialization to be more lenient with missing `thread_id` and `display_id`, allowing for broader compatibility with incoming event formats.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Evaluation Schema Immutability**: Ensured that the LLM judge's output schema is deeply copied before use, preventing unintended modifications to the shared schema object during evaluation runs.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🐛 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🐛 **Human Work Request Validation**: Implemented a Pydantic validator for human work requests, ensuring that the provided forms precisely match the expected work event options.
- 🐞 **Minor Localization Fix**: Added a missing Italian localization label for `ExceptionEvent`.
- 💅 **Minor UI Polish**: Adjusted CSS for heading spacing in Markdown renderer for improved visual consistency.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🏗️ **Optimized Docker Build for API/Bots**: Streamlined the Dockerfiles for API and Bot services by removing redundant virtual environment copying and poetry installation steps, improving build efficiency.
- 🧹 **Agent Event Sending Scope**: Relocated the `send_event` method from the core `AgentRunner` to `AgentTestRunner`, streamlining the production runner and centralizing test-specific event injection.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).
- 🔄 **Updated SharePoint Asset Factories**: Renamed the `sharepoint_files_to_data_lake_files_factory` function and its internal parameters to align with the new, standardized naming conventions, enhancing code clarity.
- 📄 **Refined SharePoint IO Manager**: Updated the SharePoint IO Manager to use the new `share_point_client` resource name consistently, improving maintainability.
- 🧼 **Cleaned Up SharePoint Utilities**: Standardized naming within metadata utility functions related to SharePoint files, contributing to a more coherent codebase.
- 🧹 **Minor Error Message Refinement**: Clarified a 404 error message in the base runner for API path routing.
- 🧹 **Improved Type Clarity**: Refined type hints for ClassVars in process event definitions, enhancing code readability and maintainability.
- 🗂️ **Frontend Application Restructuring**: Renamed the primary frontend application directory from `.playground` to `.app`, reflecting its role as the main application source.

---



## [v0.233.0] - 2025-07-30 - Internal Dependency Enhancements

### Changed
- ⚡️ **Internal Dependency Updates:** Upgraded core libraries to enhance stability and prepare for future improvements.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage & Orchestration: Unified File Handling and Enhanced Process Management

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🚀 **Implemented Dagster Build & Release Workflow**: A new GitHub Actions workflow has been added to automate the Docker image build and release process for Dagster, enabling triggers from new tags, manual dispatch, and specific feature branches.
- 🚀 **Implemented Pipelines Build & Release Workflow**: A new GitHub Actions workflow has been added to automate the Docker image build and release process for pipelines, supporting matrix builds for multiple pipeline images.
- ⚙️ **Added IntelliJ/PyCharm Run Configurations**: Provided new run configurations for Dockerfiles related to `aihub_pipeline` and `default_rag_pipeline` to streamline local development.
- 🚀 **Simplified Start Event Creation:** Added a new `from_raw_data` class method to `StartEvent`, streamlining its instantiation from raw input data.
- 📄 **Introduced `ProcessConfigSpecs`:** Added a new model to define the schema and parameters of process configurations, enhancing clarity for external consumers.
- 📄 **Defined `ProcessInstanceDiscoveryResponseEvent`:** A new event type for detailed discovery responses, providing specific instance IDs and configurations for processes.
- ➕ **Added `process_id` to Work Request Event:** Included a `process_id` field in `WorkRequestEvent` to enhance traceability for work requests within process contexts.
- 🗄️ **Added Agent Config Deletion Utility:** Implemented `delete_if_exists_for_class_and_id` in `AgentConfigEntityDocument` for more controlled cleanup of agent configurations.
- 🗄️ **Introduced Base Process Config Entity:** Defined `ProcessConfigEntity` as a common base class for storing process configurations in MongoDB, supporting both document and embedded document forms.
- 🗄️ **Added Process Config Document Entity:** Implemented `ProcessConfigEntityDocument` for persisting standalone process configurations in MongoDB, including utilities for retrieval and deletion.
- 🗄️ **Introduced Embedded Process Config Entity:** Defined `ProcessConfigEntityEmbeddedDocument` for embedding process configurations within other MongoDB documents.
- ⚙️ **Enhanced Process Configuration Model:** `ProcessConfig` now includes a `process_class` field and `model_config` for better Pydantic handling, alongside a new `from_entity` constructor for database integration.
- 🚀 **Implemented Dagster Service Dockerfile:** Added a new multi-stage Dockerfile for `aihub_pipeline`, enabling robust build and runtime environments for Dagster services.
- 🚀 **Implemented Default RAG Pipeline Dockerfile:** Added a new Dockerfile specifically for the `default_rag_pipeline`, enabling dedicated container builds for this core RAG service.
- ⚙️ **Introduced S3 Configuration:** Added `S3Config` to manage connection parameters for S3-compatible storage services like AWS S3 and MinIO.
- 🗄️ **Introduced `WalkthroughContext`:** Added a new per-walkthrough context for processes, enabling state management and configuration persistence throughout a process execution.
- 🧪 **Added Agent Service Cache Cleanup:** Introduced an `autouse` fixture to clear `AgentService` caches before and after agent API tests, ensuring test isolation and reliability.
- 🧪 **Ensured Agent Config Test Isolation:** Added an `autouse` fixture to clear `AgentService` caches for agent config database operation tests, preventing cross-test interference.
- 🧪 **Enhanced Agent Service DB Integration Tests:** Introduced a cache-clearing fixture and updated mocks to reflect internal `_discover_agent_class` renaming, improving test reliability.
- 🧪 **Improved Agent Service Unit Test Reliability:** Implemented `autouse` cache clearing and updated mocks for internal `AgentService` methods (e.g., `_discover_agent_classes`, `_send_event`), ensuring consistent test environments.
- 🧪 **Added Custom Agent Config Test for OpenAI Integration:** Introduced a new test to verify that the OpenAI chat completions API correctly utilizes custom agent configurations stored in the database.
- 🧪 **Added Process Service Cache Cleanup:** Introduced an `autouse` fixture to clear `ProcessService` caches before and after process API tests, ensuring test isolation and reliability.
- 🧪 **Introduced Process Config Database Tests:** Added comprehensive unit tests for `ProcessConfigEntityDocument` and `ProcessConfig` entity conversions, ensuring robust database interactions for process configurations.
- 🧪 **Implemented Process Service Database Integration Tests:** Added new tests to validate `ProcessService`'s interactions with the database for process instance discovery and configuration overriding.
- 🧪 **Created Process Service Unit Tests:** Added extensive unit tests for `ProcessService`, covering process discovery, event handling, and cache management.
- 🧪 **Added Process Dispatcher Tests:** Introduced comprehensive unit and integration tests for `ProcessDispatcher`, verifying its handling of process configurations, events, and lifecycle management.
- ⚙️ **Added Dagster Configuration File:** Introduced a new `dagster.yaml` file to configure run, event log, and schedule storage using PostgreSQL, along with run coordination and compute logs.
- 🚀 **Added `send_agent_start_event`:** Implemented a new utility method in `AgentService` to specifically handle sending `StartEvent`s to agents, encapsulating the event creation and publishing logic.
- 🦾 **Centralized Process Endpoint Discovery:** Introduced `ProcessEndpointsDiscoveryService` to dynamically register API endpoints for processes, enabling real-time exposure of process capabilities.
- 📄 **Introduced `MinimalProcessDTO`:** Added a new data transfer object for lightweight process representations, used in API responses that require only core process identification.
- 📄 **Defined `ProcessClassDTO`:** A new DTO to encapsulate metadata for a process class, including its configuration specifications and default settings, enabling better discoverability and API clarity.
- 📄 **Introduced `ProcessInstanceDTO`:** A new DTO for representing specific process instances, inheriting class-level metadata and including instance-specific configuration and persistence utilities.
- 📄 **Introduced `AgentClassTopic`:** A new NATS topic model representing agent class-level events, providing clearer subject structuring for agent definitions.
- 📄 **Defined `ProcessClassDiscoveryTopic`:** A new NATS topic model for process class discovery, enabling targeted queries for process definitions.
- 📄 **Introduced `PartialProcessTopic`:** Added a new NATS topic model for representing partially defined process event subjects, useful for broad subscriptions where some topic fields may be wildcards.
- 📄 **Defined `ProcessClassTopic`:** A new NATS topic model specifically for process class-level events, providing more structured subjects for process definitions.
- 📄 **Introduced `ProcessInstanceTopic`:** A new NATS topic model for representing specific process instance events, building on class-level topics for granular event routing.
- 🏗️ **Implemented Azure Data Lake Client:** Added `AzureDataLakeClient`, a concrete implementation of `AbstractDataLakeClient` that wraps Azure's `FileSystemClient` to provide cloud-agnostic data lake operations.
- 🛠️ **Added S3 Data Lake Client Resource:** Implemented `S3DataLakeClientResource` to provide a configured `boto3` S3 client resource for Dagster pipelines.
- 🛠️ **Added S3 Data Lake File System Resource:** Implemented `S3DataLakeFileSystemResource` to provide a configured `s3fs.S3FileSystem` resource for Dagster pipelines, enabling file-system like interactions with S3.
- 🚀 **Defined Default RAG Pipeline:** Introduced `default_rag_pipeline` including its asset definitions, resources (S3 data lake, embedding/LLM models, document parsers), and automated jobs/schedules.

### Changed
- ⚙️ **Standardized Docker Entrypoint:** Updated `llm_wrapping_agent` Dockerfile to use `AGENT_NAME` and `exec` in its entrypoint, improving consistency and process management within the container.
- ⚙️ **Refined Agent Runner Configuration:** `LLMWrappingAgent`'s main entrypoint now explicitly passes `redis_url` and NATS `servers` to `AgentRunner`, centralizing infrastructure configuration.
- 🔑 **Updated API Key Setting:** Changed `MODEL_API_KEY` to `MODEL_SUI_API_KEY` in `LLMWrappingAgent`'s main application for more specific key management.
- 🔄 **Streamlined Agent Discovery in API:** `AgentController` now directly uses `AgentService.discover_agents` which returns pre-formatted `AgentDTO`s, simplifying API responses.
- ☁️ **Integrated Multi-Cloud File Access:** `FileController` now uses `FileAccessServiceConfig` for generating signed file URLs, leveraging the new cloud-agnostic file access layer.
- ⚙️ **Enhanced Process Start Form Submission:** `ProcessController` now explicitly discovers the process instance and passes its `process_config` when submitting start forms, ensuring accurate configuration.
- ⚡️ **Improved Dispatcher Shutdown:** Enhanced `BaseDispatcher`'s `stop` method to prevent re-initialization on multiple calls and log its shutdown status for better operational clarity.
- ⚡️ **Enhanced Event Store Logging:** Improved `JetStreamEventStore` logging to include full message subjects and event data on receipt, and more detailed error messages for better debugging.
- ⚡️ **Improved JS Subscriber Logging:** Added debug logs for `JSSubscriber` unsubscribe actions and made subscription arguments explicit for better readability.
- ⚙️ **Expanded Dispatchable Workflow Event Handling:** `DispatchableWorkflow` now supports waiting for both `ControlEvent` and `WorkEvent` types, increasing flexibility for workflow orchestration.
- ⚙️ **Enhanced Process Start Event:** Added a `process_config` field and a `from_raw_data` class method to `ProcessStartEvent`, enabling more dynamic process initialization.
- ⚙️ **Streamlined Process Entity Creation/Update:** Updated `ProcessEntity` creation and update methods to accept explicit configuration and specification objects, simplifying persistence logic.
- ⚙️ **Standardized Docker Entrypoint:** Updated `llm_wrapping_agent` Dockerfile to use `AGENT_NAME` and `exec` in its entrypoint, improving consistency and process management within the container.
- ☁️ **Adapted Azure Data Lake IO Manager:** `AzureDataLakeIOManager` now utilizes the new `AzureDataLakeClient` and its `raw_client` property, centralizing `DataLakeFile` creation for enhanced maintainability.
- 🚀 **Cloud-Agnostic File Fetching:** `fetch_all_files_in_data_lake` now uses the `AbstractDataLakeClient` interface, enabling consistent file retrieval across different cloud providers.
- 🚀 **Unified Figure Deletion Logic:** `delete_figures_for_many_ref_doc` now uses the `AbstractDataLakeClient` for directory and file operations, ensuring consistent figure cleanup across cloud storage.
- 🚀 **Cloud-Agnostic File Removal Detection:** `fetch_data_lake_files_to_remove` and its helper functions now leverage `AbstractDataLakeClient` for fetching files, standardizing removal detection across data lake types.
- ⚙️ **Refactored Data Lake Resource Factories:** Updated `azure_data_lake_resources` to reflect new Azure resource names and introduced a new `s3_data_lake_resources` factory for S3/MinIO integration.
- 🛠️ **Added S3/MinIO Default IO Manager:** Introduced `default_io_manager_s3_datalake_resources` to simplify the setup of S3-compatible storage as the default IO manager in Dagster pipelines.
- ⚙️ **Enhanced Process Dispatcher Configuration:** `ProcessDispatcher` now manages process configuration via `WalkthroughContext`, supports dynamic `ProcessConfig` injection into steps, and ensures proper cleanup on process stop.
- ⚙️ **Redesigned Process Runner Initialization:** `ProcessRunner` now uses `default_process_config` to define the base process configuration and initializes `ProcessClassTopicManager`, simplifying process setup.
- ⚙️ **Updated Playground Process Config:** Adjusted `agent_only_process`, `agent_to_human_process`, `fan_out_process`, `human_only_process`, `human_to_agent_process`, `multi_input_process`, and `process_sequence` run/test configurations to use `default_process_config` and include `process_class` for improved consistency.
- 🖼️ **Enhanced Image URL Handling in Web UI:** Updated `ResolveImageComponent.vue` to correctly parse and resolve image URLs containing protocol prefixes (e.g., `s3://`), ensuring images load properly from various sources.
- 🐳 **Enhanced Docker Compose for Dagster Integration:** Updated `docker-compose.latest.yml` to include a full Dagster stack (webserver, daemon, OAuth2 proxy), reconfigured PostgreSQL for Dagster database, and adjusted MinIO environment variables.
- 🔒 **Improved Internal Service Security:** Removed external port mappings for PostgreSQL and NATS in `docker-compose.latest.yml`, limiting access to these services to internal Docker networks.
- 🌐 **Exposed MinIO Dashboard via Traefik:** Added Traefik labels to the MinIO service in `docker-compose.latest.yml` to expose its dashboard via a secure hostname.
- ⚙️ **Refined Process Discovery Flow:** `ProcessService` now uses `_discover_agent_classes` and `_discover_agent_instance` internally, and `discover_agents` directly constructs `AgentDTO`s from discovered instances, simplifying the data flow.
- 🚀 **Streamlined Process Start Event Sending:** Refactored `send_process_start_event` to directly construct and send `ProcessStartEvent` with relevant `human_in` and `process_config` data, simplifying external process initiation.
- ⚙️ **Updated Playground Configuration:** Switched the default pipeline configuration in the playground to use S3/MinIO data lake resources and `DOCUMENT_INTELLIGENCE` as the document parser, showcasing new capabilities.
- ⬆️ **Upgraded Pipeline Dependencies:** Updated Dagster and related packages, and added `dagster-aws` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⬆️ **Updated Core Dependencies:** Added `boto3` to support new S3-compatible storage integrations.

### Refactor
- 🧹 **Consolidated Base Context:** The `BaseContext` class was moved from `aihub_agent` to `aihub_lib`, centralizing common context functionalities within the core library.
- 🔄 **Refined Agent NATS Topics:** Updated `AgentDispatcher` to use new `AgentClassTopic` and `AgentInstanceTopic` models, providing a more precise and hierarchical NATS topic structure for agent events.
- 🧹 **Reorganized Infrastructure Imports:** Moved `NatsConfig` and `RedisConfig` into their respective `aihub_lib.infrastructure` subpackages for better module organization.
- 🔄 **Updated Agent Test Runner Topics:** Aligned `AgentTestRunner` with the new `AgentInstanceTopic` for consistent agent event handling during tests.
- 🧹 **Internal API Method Renaming:** Renamed several `AgentService` methods (e.g., `discover_agent_class` to `_discover_agent_class`) to indicate their internal-only usage.
- 📄 **Standardized File Access Parameter Descriptions:** Updated docstrings for file access parameters to be cloud-agnostic, referring to "container/bucket name" instead of "blob container name."
- 🔄 **Overhauled Process Discovery and Configuration:** `ProcessService` underwent a significant refactor, introducing explicit `ProcessClassDTO` and `ProcessInstanceDTO` for clearer separation of process definitions and instances.
- 🗄️ **Improved Process Caching Strategy:** Implemented more granular caching (`DISCOVER_PROCESSES_CACHE`, `GET_PROCESS_INSTANCE_CACHE`, `GET_PROCESS_CLASS_CACHE`) to optimize process discovery and retrieval performance.
- 🧹 **Internal Process Service Method Renaming:** Renamed methods like `discover_process` to `discover_process_instance` and prefixed internal helpers with `_` (e.g., `_discover_process_class`), for improved clarity and encapsulation.
- 🔄 **Refined `ProcessDTO` Inheritance:** `ProcessDTO` now inherits from `MinimalProcessDTO`, streamlining its structure and improving consistency across process-related DTOs.
- 🧹 **Optimized Process Service Import:** Moved `ProcessService` import into a method in `UserWithAccessDTO` to avoid circular dependencies and improve load times.
- 🧹 **Internal API Endpoint Renaming:** Renamed `AgentEndpointsDiscoveryService`'s internal `discovery_handler` and `create_endpoint` methods with a `_` prefix, reinforcing their private nature.
- 🔄 **Aligned Agent Endpoints with New Topics:** `AgentEndpointsDiscoveryService` now uses `AgentInstanceTopic` and `AgentInstanceDiscoveryTopic`, reflecting the refined agent topic structure.
- ⚙️ **Enhanced Dynamic Form Endpoints:** Process endpoints now explicitly pass `process_config` when submitting forms, ensuring forms are processed within the correct process context.
- 🔄 **Refined Process Endpoint Registration:** The service now leverages `ProcessInstanceDTO` and `ProcessClassTopicManager` for more precise registration of human and program interaction endpoints.
- 📄 **Cleaned Up Test Client Fixture Docstrings:** Removed redundant `Args` sections from test client fixture docstrings to improve clarity.
- 🧹 **Adjusted Process Controller Routes:** Minor reordering of process-related routes in `playground/development/main.py` for logical grouping.
- 🧪 **Enhanced Agent Service DB Integration Tests:** Updated mocks to reflect internal `_discover_agent_class` renaming, improving test reliability.
- 🧪 **Improved Agent Service Unit Test Reliability:** Updated mocks for internal `AgentService` methods (e.g., `_discover_agent_classes`, `_send_event`), ensuring consistent test environments.
- 🧪 **Adjusted Process Controller Test Routes:** Minor reordering of process-related routes in `test_process_api.py` for logical grouping.
- 📄 **Cleaned Up IAC Docstrings:** Removed redundant parameter descriptions from `NetworkProvider` docstrings to improve clarity.
- 📄 **Refined ResourceNamer Docstrings:** Removed redundant parameter descriptions from `ResourceNamer` docstrings to enhance clarity.
- 📄 **Streamlined Storage Resource Factory Docstrings:** Removed redundant parameter descriptions from `StorageResourceFactory` docstrings for better readability.
- 🔄 **Aligned Document Intelligence Key Access:** Updated the method for retrieving primary keys from Azure Document Intelligence services to use `keys.key1`, ensuring compatibility with recent API changes.
- 🔄 **Realigned Process Exception Event:** Changed `ProcessExceptionEvent` to inherit directly from `WorkEvent`, streamlining the process event hierarchy.
- 🔄 **Streamlined Process Stop Event:** Changed `ProcessStopEvent` to inherit from `WorkEvent` and removed the redundant `process_id` field for a leaner event structure.
- 🔄 **Restructured Process JS Subscriptions:** Refactored `ProcessJSSubscriber` methods to align with the new process class and instance topic hierarchy, providing clearer distinctions for work event subscriptions.
- 🔄 **Expanded Process NC Subscriptions:** `ProcessNCSubscriber` now supports distinct subscriptions for process *class* and *instance* discovery requests and responses, enhancing control over process communication.
- 🧹 **Refined Agent Class Topic Stream:** `AgentClassTopicManager` now uses a dedicated internal method to define the subject for all events within an agent class, improving stream configuration clarity.
- 🔄 **Realigned Process Instance Topic Manager:** `ProcessInstanceTopicManager` now inherits from `ProcessClassTopicManager`, streamlining its hierarchy and delegating stream management to the parent class.
- 🔄 **Enhanced Process Discovery Topic Management:** `ProcessTopicManager` now provides distinct methods for managing NATS subjects for process *class* and *instance* discovery requests and responses, improving granularity.
- 🔄 **Updated Process Walkthrough Topic Manager:** `ProcessWalkthroughTopicManager` now builds on `ProcessClassTopicManager` and allows optional `process_id`, providing more flexibility for topic generation across process hierarchies.
- 🔄 **Refactored Agent Instance Topic:** Renamed `AgentTopic` to `AgentInstanceTopic` and made it inherit from `AgentClassTopic`, streamlining the agent topic hierarchy and introducing a `from_agent_class_topic` constructor.
- 🔄 **Refactored Process Instance Discovery Topic:** Renamed `ProcessDiscoveryTopic` to `ProcessInstanceDiscoveryTopic` and updated its inheritance from `ProcessClassDiscoveryTopic`, clarifying its role in process instance discovery.
- 🗄️ **Refactored Process Entity Storage:** `ProcessEntity` now stores process configurations as a `ReferenceField` to `ProcessConfigEntityDocument` and introduces `default_process_config` as an `EmbeddedDocumentField`, enhancing database schema flexibility.
- 🧹 **Centralized `DataLakeFile` Creation:** Removed the static `from_uri` method from `DataLakeFile`, delegating its instantiation to cloud-specific data lake client implementations for better encapsulation.
- 🔄 **Realigned Azure Data Lake Client Resource:** Renamed `DataLakeClientResource` to `AzureDataLakeClientResource` and updated it to implement `AbstractDataLakeClientResource`, returning a wrapped `AzureDataLakeClient`.
- 🔄 **Realigned Azure Data Lake File System Resource:** Renamed `DataLakeFileSystemResource` to `AzureDataLakeFileSystemResource` and updated it to implement `AbstractDataLakeFileSystemResource`, providing a standardized interface for Azure Blob File System.
- 🔄 **Refactored Entity Delegator:** `AbstractEntityDelegator` was refactored to align with the new process topic hierarchy (`ProcessClassTopic`), removed redundant `process_id` in its `__init__`, and introduced a private `_publish_work_event` utility.
- 🔄 **Streamlined Agent Delegator:** `AgentDelegator` was updated to use the new `ProcessClassTopicManager` and the private `_publish_work_event` method, simplifying its internal logic and improving alignment with the process topic hierarchy.
- 🔄 **Revised Process Delegator:** `ProcessDelegator` was refactored to use the new `ProcessClassTopicManager` and `_publish_work_event` for consistency, removing redundant `process_id` handling.
- 🔄 **Unified Process Event Publishing:** `ProcessDispatcher`'s `publish_event` method was refactored to handle both `WorkRequestEvent` and `WorkEvent` types, standardizing process event emission.
- 🗄️ **Integrated Walkthrough Context:** The dispatcher now uses `WalkthroughContext` to store and retrieve runtime `process_config`, ensuring stateful process execution.
- 🧪 **Updated Process Test Runner:** `ProcessTestRunner` was updated to reflect the new process topic hierarchy (`ProcessInstanceTopic`, `ProcessClassDiscoveryTopic`) and to align with `default_process_config` usage.

### Removed
- 🗑️ **Removed Generic Discovery Request Event:** Eliminated `DiscoveryRequestEvent`, streamlining discovery event hierarchy in favor of more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent`.
- 🗑️ **Removed Redundant Agent JS Subscriber Method:** Eliminated `for_agent_instance_events` from `AgentJSSubscriber`, streamlining subscription options to focus on control events.
- 🗑️ **Removed Generic Process Topic:** Eliminated `ProcessTopic` in favor of more granular `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` models.
- 🗑️ **Removed Obsolete Test File:** Deleted `test_agent_config_start_event.py` as its functionality is now covered by other tests or made redundant by recent architectural changes.
- 🗑️ **Removed Azure AI Search Vector Store:** Discontinued support for Azure AI Search by removing its related resource factories and resource file.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage & Refined Agent/Process Architecture

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📝 **Streamlined Event Creation:** Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent` to centralize and simplify the creation of these initial events.
- 🗄️ **Process Configuration Persistence:** Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to support flexible storage of process configurations, including referenced and embedded options.
- 🎯 **Granular Process Discovery:** Implemented `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent`, along with their corresponding topics and NATS subscribers, enabling more precise discovery of process definitions and instances.
- ⚙️ **Process Configuration Specification:** Added `ProcessConfigSpecs` to clearly define the schema of process configurations, enhancing interoperability.
- 📦 **Dagster Orchestration Setup:** Integrated Dagster services (`dagster-webserver`, `dagster-daemon`, `oauth2proxy`) into the Docker Compose stack for unified deployment and management of data pipelines.
- 📊 **Dedicated Process Walkthrough Context:** Introduced `WalkthroughContext` in `aihub_process` to manage transient state specific to a single process execution, improving isolation and clarity.
- 🗑️ **Agent Config Deletion Utility:** Added `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument` for cleaner management of agent configurations.
- 🧪 **Comprehensive Process Testing:** Introduced new dedicated test files (`test_ProcessDispatcher.py`, `test_process_config_database_operations.py`, `test_process_service_database_integration.py`, `test_process_service_unit_tests.py`) for robust validation of process-related components.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage, supporting S3 URI formats.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⚙️ **Agent and Process Config Handling:** Dispatchers and runners now explicitly manage `default_agent_config` and `default_process_config`, enabling dynamic overrides from incoming events or persistent storage.
- 💡 **Refined Topic Hierarchy and Naming:** Migrated all agent and process topics to a new, clearer hierarchical structure (`Partial...Topic` -> `...ClassTopic` -> `...InstanceTopic`), impacting dispatchers, runners, subscribers, and publishers across all services.
- 🔗 **Process Delegation Scope:** `AbstractEntityDelegator`, `AgentDelegator`, and `ProcessDelegator` now operate at the process *class* level, dynamically inferring or receiving instance-specific details for improved flexibility.
- 📦 **Process Event Type Alignment:** `ProcessStopEvent` and `ProcessExceptionEvent` now inherit from `WorkEvent`, standardizing event types for process-internal logic.
- 📊 **Dagster Infrastructure Scalability:** Updated Dagster configuration to use more granular run, event, and schedule storage settings, and increased `max_concurrent_runs` for improved pipeline execution capacity.
- 🛡️ **Docker Compose Security Enhancements:** Internalized ports for Postgres, NATS, and Redis services in `docker-compose.latest.yml`, limiting external access and enhancing security.
- 🌐 **API Agent and Process Discovery:** The API now exposes more detailed agent and process information, distinguishing between class definitions and runnable instances, providing richer metadata for clients.
- 📝 **Agent/Process Runner Config Parameter:** Agent and Process runners now explicitly accept `default_agent_config` and `default_process_config` parameters, standardizing base configurations.
- 📚 **Process Config Model Enhancement:** The `ProcessConfig` model now includes a `process_class` field and a `from_entity` class method for better integration with database persistence.
- ⚡️ **Workflow Event Triggering:** `DispatchableWorkflow.get_steps_waiting_for_event` can now be triggered by `WorkEvent` in addition to `ControlEvent`, enhancing process flexibility.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Generic Discovery Event:** Eliminated the `DiscoveryRequestEvent` in favor of more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent`.
- 🗑️ **Monolithic Process Topic:** Removed the old `ProcessTopic` as it has been replaced by the new hierarchical process topic structure.
- 🗑️ **Redundant Agent Event Subscription:** Removed `AgentJSSubscriber.for_agent_instance_events` for better specificity in event subscriptions.
- 🗑️ **Unused Process Topic Manager Methods:** Cleaned up `ProcessWalkthroughTopicManager.get_subject_for_all_event_in_walkthrough`.
- 🗑️ **Obsolete Test Files:** Deleted `aihub_agent/playground/testing/tests/test_agent_config_start_event.py` due to refactored testing approach.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages (`aihub_lib/infrastructure/nats`, `aihub_lib/infrastructure/redis`) for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🔄 **Refined Topic Management Hierarchy:** Streamlined topic managers for agents and processes to align with the new class/instance topic hierarchy, reducing redundancy and improving consistency.
- 🧹 **Internal API Service Method Encapsulation:** Made several methods in agent and process endpoint discovery services (e.g., `_discovery_handler`, `_create_endpoint`) private to encapsulate internal logic.
- ⚡️ **Improved Dispatcher Lifecycle Management:** Enhanced `BaseDispatcher` to ensure proper stopping of the event store and clear initialization/de-initialization logging.
- 🧪 **Test Fixture Consistency:** Added `cleanup_db_and_cache` fixtures to several API test modules to ensure a clean state before and after tests.
- 🗺️ **Pipeline Dockerfile Paths:** Adjusted `DAGSTER_HOME` and entrypoint paths in `aihub_pipeline` Dockerfiles for consistency.
- 🗂️ **Process Context Location:** Moved `BaseContext` from `aihub_agent` to `aihub_lib` and introduced a dedicated `walkthrough` subpackage for `WalkthroughContext` in `aihub_process`.
- ✏️ **Standardized Persistence Field Naming:** Changed `from_dto` to `from_specs` in process persistence entities for consistency.
- 🔄 **Process Config Persistence Strategy:** Updated `ProcessEntity` to use a `ReferenceField` for `process_config` and an `EmbeddedDocumentField` for `default_process_config`, allowing for both user-defined and default configurations to be managed.

---



## [v0.226.0] - 2025-07-25 - Streamlined Core Architecture: Process Refinements & Cloud Alignment

### Added
- ✨ **Agent Configuration Precedence Test Suite**: Introduced a comprehensive test suite (`test_agent_config_start_event.py`) to validate the precedence logic for agent configurations provided via `StartEvent`s and default settings.
- ⚙️ **Generic `DiscoveryRequestEvent`**: A new foundational event (`DiscoveryRequestEvent`) has been added to standardize discovery requests across various system components.
- 📚 **Unified `ProcessTopic`**: A new NATS topic model (`ProcessTopic`) has been introduced to consolidate and simplify process-related topic definitions, replacing several older, more granular topic types.
- 📊 **Azure AI Search Vector Store Resource**: Integrated a new resource (`AzureAISearchVectorStoreResource`) and supporting factory functions, enabling Azure AI Search as a vector store option for pipelines.
- 🚀 **Generalized Agent Event Subscription**: Added a new class method (`for_agent_instance_events`) to `AgentJSSubscriber` to allow subscribing to all events within an agent instance, enhancing observability and flexibility.

### Changed
- ⚙️ **Docker Compose Postgres Port Exposure**: The `postgres` service in `docker-compose.latest.yml` now explicitly exposes port `5432` to the host, facilitating external connections and removing `dagster` from its managed databases.
- 🔄 **Dagster Configuration and Version Rollback**: The `dagster.yaml` configuration reverts to a consolidated `storage: postgres` setup from separate storage types, and Dagster dependencies are rolled back to earlier versions, aligning with the removal of the Dagster stack from the main Docker Compose file.
- 🖼️ **Image URL Handling Reversion**: Frontend image resolution and RAG context generation now exclusively expect `container/path` format for image URIs, removing support for `s3://` prefixes, aligning with the discontinuation of multi-cloud storage abstraction.
- 🏷️ **AIHub Service Version Rollback**: The project versions for `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, and `aihub_process` are reverted to `v0.226.0` from `v0.229.0`, indicating a version rollback.
- 📁 **Standardized Dagster Home Path**: The `DAGSTER_HOME` environment variable in `aihub_pipeline` Dockerfiles is standardized to `/opt/dagster/dagster_home` for consistent deployments.
- 💡 **Process Runner Configuration**: The `ProcessRunner` and `ProcessTestRunner` now accept a direct `process_config` parameter instead of `default_process_config`, streamlining how process configurations are initialized and managed.
- 💬 **AIHub Web SDK Model Timestamp Default**: The default `created` timestamp in the `ModelDetailsSchema` within the generated SDK has been updated to an earlier date.
- 🤖 **Default RAG Pipeline Configuration**: The default RAG pipeline now uses `LoaderType.DOCLING` instead of `DOCUMENT_INTELLIGENCE` and adjusts default namespace and store names for consistency.

### Fixed
- 🐛 **Azure Document Intelligence Key Retrieval**: The method for retrieving primary keys from Azure Document Intelligence services has been corrected to use `keys.primary_key` instead of the deprecated `keys.key1`, ensuring robust authentication.

### Refactor
- 🧹 **Consolidated Agent NATS Topics**: Agent-related NATS topic models (`AgentClassTopic`, `AgentInstanceTopic`) have been consolidated into a single, simplified `AgentTopic` for clearer communication patterns.
- 📦 **Simplified Data Lake Client Resources**: The data lake client and file system resources (`AzureDataLakeClientResource`, `AzureDataLakeFileSystemResource`) have been streamlined to directly provide raw Azure SDK clients, removing intermediate wrapper classes and simplifying their usage in pipelines.
- ⚙️ **Overhauled Process Dispatcher**: Significant internal refactoring of the `ProcessDispatcher` removed explicit `WalkthroughContext` management, simplified process configuration handling, and streamlined event publishing logic, making the dispatcher leaner and more focused.
- 🗄️ **Streamlined Process Configuration Persistence**: The persistence model for process configurations has been simplified in `ProcessEntity`, which now directly embeds `ProcessConfig` instead of relying on separate configuration documents, enhancing data co-location.
- 🚀 **NATS Subscriber and Topic Manager Alignments**: Extensive refactoring and renaming of NATS subscribers and topic managers were performed to align with the new, simplified agent and process topic hierarchies and event types.
- 📄 **Centralized `DataLakeFile` Creation**: The logic for instantiating `DataLakeFile` objects from URIs has been moved into a static `DataLakeFile.from_uri` method, centralizing its creation and allowing direct interaction with the raw file system client.
- 📁 **Flattened Infrastructure Configuration Modules**: NATS and Redis configuration modules were moved to a top-level `infrastructure` package for a flatter, more intuitive directory structure.
- 🏷️ **Consistent Service Method Naming**: Internal methods across `AgentService` and `ProcessService` (e.g., `_send_event` to `send_event`, `_clear_cache` to `clear_cache`) were renamed for improved consistency and clarity.
- 🗑️ **Removed `StartEvent` Helper Method**: The `from_raw_data` class method was removed from `StartEvent`, promoting more direct construction of event instances.
- 💡 **Simplified Process Endpoint Discovery**: `ProcessEndpointsDiscoveryService` was refactored to simplify its internal lifecycle management and streamline its endpoint creation functions, adapting to the new process DTO and unified discovery.

### Removed
- 🗑️ **Multi-Cloud Storage Abstraction**: The entire multi-cloud file access abstraction layer, including generic service interfaces, specific Azure/S3 implementations (`AbstractAnonymousFileAccessService`, `FileAccessServiceConfig`, `S3AnonymousFileAccessService`, `AzureAnonymousFileAccessService`), and related S3/MinIO data lake components (`S3Config`, `S3DataLakeIOManager`, `S3DataLakeClient`, `S3DataLakeFileSystem`), has been eliminated.
- 🗑️ **Dagster Stack from Main Docker Compose**: The `oauth2proxy`, `dagster-webserver`, and `dagster-daemon` services are no longer included in `docker-compose.latest.yml`, indicating a shift in Dagster's deployment strategy within the environment.
- 🗑️ **Explicit Process Configuration Entities**: Dedicated database entities for process configurations (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) have been removed, simplifying process configuration storage directly within `ProcessEntity`.
- 🗑️ **Legacy Process Discovery DTOs**: Obsolete process Data Transfer Objects (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`) have been removed, consolidating process representation under a new, simplified `ProcessDTO`.
- 🗑️ **Specific NATS Topic Managers for Processes**: The `ProcessClassTopicManager` and related granular process discovery topics (`ProcessClassDiscoveryTopic`, `ProcessInstanceDiscoveryTopic`) have been removed, streamlining NATS topic management for processes.
- 🗑️ **Agent Configuration Persistence Helper**: The `delete_if_exists_for_class_and_id` method was removed from `AgentConfigEntityDocument`, streamlining test cleanup.
- 🗑️ **Obsolete Process Test Files**: Several test files related to the previous process dispatcher, configuration, and service database integration (`test_ProcessDispatcher.py`, `test_process_config_database_operations.py`, `test_process_service_database_integration.py`, `test_process_service_unit_tests.py`) have been removed due to extensive refactoring and simplification of the process core.
- 🗑️ **Empty Context and Infrastructure Packages**: Several empty or redundant `__init__.py` files and corresponding directories under `aihub_lib/context`, `aihub_lib/infrastructure/nats`, `aihub_lib/infrastructure/redis`, `aihub_lib/infrastructure/s3`, `aihub_pipeline/io/base`, `aihub_pipeline/resources/data_lake/azure`, `aihub_pipeline/resources/data_lake/s3`, `aihub_pipeline/resources/data_lake/base`, `aihub_process/context`, and `aihub_process/context/walkthrough` have been removed.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage and Orchestration Enhancements

### Added
- ☁️ **Multi-Cloud Storage Abstraction**: Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service**: Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration**: Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients**: Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🐳 **Dagster Orchestration in Docker Compose**: Added `dagster-webserver` and `dagster-daemon` services to `docker-compose.latest.yml`, integrating Dagster into the main deployment stack for robust pipeline orchestration.
- 🗄️ **Database Persistence for Process Configurations**: Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to enable persistent and dynamic configuration for agentic processes.
- 🧪 **Comprehensive Process Dispatcher Testing**: Added new dedicated test files (`test_ProcessDispatcher.py`, `test_process_config_database_operations.py`, `test_process_service_database_integration.py`, `test_process_service_unit_tests.py`) for robust validation of process dispatcher and service logic.
- 📋 **Process Walkthrough Context**: Implemented `WalkthroughContext` in `aihub_process` for managing state and configurations specific to individual process walkthroughs.
- ➕ **New NATS Topic Managers for Processes**: Introduced `ProcessClassTopicManager` to manage topics for process classes, enhancing the granularity of process event routing.
- 🚀 **Utility for Start Event Creation**: Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent` for simplified event construction from raw data.
- 📦 **S3 Configuration Model**: Implemented `S3Config` for managing connection parameters for S3-compatible storage services.

### Changed
- 🔄 **Unified File URL Generation**: Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution**: Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations**: Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- ⚙️ **Process Orchestration Refinements**: Refactored process dispatcher to manage `ProcessConfig` via `WalkthroughContext`, enabling dynamic config injection into process steps. Process runners now use `default_process_config` and deploy at the class level.
- ⚡️ **Dagster Concurrency**: Increased `max_concurrent_runs` in `dagster.yaml` from 3 to 10 to allow for more parallel pipeline executions.
- 📦 **Dagster Docker Configuration**: Updated `DAGSTER_HOME` path and `dagster.yaml` to align with the new Dagster service setup in Docker Compose.
- 🧪 **Playground Configuration**: Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates**: Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- 🔐 **Internalized Service Ports**: NATS and Postgres services in `docker-compose.latest.yml` no longer expose their ports externally, enhancing security by limiting external access to these internal components.

### Fixed
- 🐛 **Azure Document Intelligence Key Access**: Aligned the method for retrieving primary keys from Azure Document Intelligence services (`keys.primary_key` to `keys.key1`) with recent API changes, ensuring robust and consistent authentication.
- 🐞 **JetStream Event Store Logging**: Enhanced `JetStreamEventStore` to include full exception details in logs and explicitly ack messages even on error to prevent redelivery issues.
- ✅ **JSSubscriber Parameter Explicitly Set**: Made `subject`, `stream`, `queue` explicit parameters for `js.subscribe` in `JSSubscriber` for clarity and correctness.

### Removed
- 🗑️ **Azure AI Search Vector Store**: Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Deprecated Generic Discovery Event**: Removed the generic `DiscoveryRequestEvent` as more specific class- and instance-level discovery events are now used.
- 🗑️ **Obsolete Process Topic**: Eliminated the `ProcessTopic` model in `aihub_lib` in favor of the new hierarchical `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` models.
- 🗑️ **Redundant Agent Config Test File**: Deleted `aihub_agent/playground/testing/tests/test_agent_config_start_event.py` as its logic is covered or superseded by new dynamic config handling.
- 🗑️ **Legacy DataLakeFile Creation Method**: Removed the `from_uri` static method from `DataLakeFile` as its logic has been moved into cloud-specific data lake client implementations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure**: Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages (`aihub_lib/aihub_lib/infrastructure/nats` and `aihub_lib/aihub_lib/infrastructure/redis`) for clearer logical grouping and improved project structure.
- 🔄 **Unified NATS Topic Hierarchy**: Overhauled NATS topic models and managers for both agents and processes, introducing `AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`, and their corresponding managers for a more granular and consistent routing structure.
- 📄 **Improved Docstring Clarity**: Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings, improving conciseness.
- ⚙️ **Centralized DataLakeFile Creation**: Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🗄️ **Refined Process Entity Persistence**: Re-architected `ProcessEntity` to use `ReferenceField` for `process_config` and introduce an embedded `default_process_config`, enhancing data relationships and flexibility.
- 🧹 **Internal API Service Renaming**: Renamed internal API service methods (e.g., `_send_event`, `_clear_cache`) to private for better encapsulation.
- 📦 **API DTO Reorganization for Processes**: Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to provide a clearer, more granular representation of process information in API responses.
- 🧹 **Test Fixture Cleanup**: Added `autouse` fixtures to clear caches in agent and process API tests, ensuring isolated test runs.
- 🐍 **Python Module Imports Standardization**: Consolidated `BaseContext` import locations to `aihub_lib`.
- ⚙️ **Dagster Storage Configuration**: Updated `dagster.yaml` to use explicit storage classes and environment variables for PostgreSQL configuration, aligning with best practices.

---



## [v0.226.0] - 2025-07-24 - Advanced Agent Management, Structured RAG Context, and Enhanced Pipeline Automation

### Added
- ✨ **Dynamic Agent Configuration:** Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Enhanced Agent Discovery Mechanism:** Implemented granular discovery for agent *classes* and specific agent *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations:** Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups across deployments.
- 🔌 **New Pydantic Models for Vector Store Configurations:** Introduced dedicated Pydantic configurations for `AzureAISearchVectorStore` and `MilvusVectorStore`, allowing for direct embedding and validation of vector store settings within agent configs.
- 📈 **`agent_class` Field in `AgentConfig`:** A new `agent_class` field has been added to `AgentConfig` for consistent agent class identification throughout the system.
- 📄 **`save_config.py` Example:** A new example demonstrating how to persist agent configurations to the database for custom or production deployments.
- 🦾 **New Job Creation Utility:** Introduced `materialize_asset_job` to simplify the creation of jobs for materializing specific selections of assets within pipelines.
- 📅 **Automated Playground Workflows:** Implemented new daily jobs and schedules within the playground environment to automatically observe source data and manage document removal processes.
- 🧪 **Comprehensive Agent Dispatcher Testing:** New test files have been added to rigorously validate the agent dispatcher's logic, particularly regarding agent configuration handling.

### Changed
- ⚙️ **Refined Agent Configuration Loading Logic:** The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization:** Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 💡 **Improved Type Specificity for LLM and Vector Store Configs:** Agent configurations (e.g., in `RAGAgent`) now utilize more precise type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration:** RAG and Retrieval agents now leverage the `.to_llama_index()` method directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- ⚡️ **Enhanced Background Task Management:** Improved handling of `asyncio.Task` instances within dispatchers and subscribers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Revised API Agent Discovery:** The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- ⚙️ **Updated Default Document Language:** The default language for newly ingested nodes has been updated from English to German.
- ⚡️ **Refined Node Sorting Logic:** Improved the internal sorting mechanism for nodes within a document to correctly present hierarchical structures.
- 🔗 **Specialized I/O Manager in Pipelines:** Updated the SharePoint observable asset in pipelines to utilize a dedicated `sharepoint_io_manager`, ensuring more appropriate handling of SharePoint data interactions.
- ⚙️ **Refined Asset Automation in Pipelines:** Adjusted automation configurations for document and data lake file removal assets in pipelines, transitioning from eager conditions to more explicit job-driven scheduling.
- 📈 **Generated SDK Updates:** The generated client SDK for the web frontend now reflects the updated `AgentConfigDTO` (removal of deprecated fields) and includes the new `agent_config` field in `StartEvent` and `UserMessageEvent`.

### Fixed
- 🐛 **Robust Figure Deletion in Pipelines:** Improved the data lake figure deletion process in pipelines by adding an existence check, preventing errors when a figures directory is already absent.
- 💬 **Localization for Process DTO:** Corrected a minor typo in the `ProcessDTO` description in the generated SDK.
- 🐞 **Minor Typo in Makefile:** Corrected a minor typo in the `Makefile` import path.

### Removed
- 🗑️ **Deprecated Configuration Fields:** The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration and allowing for more flexible, agent-specific prompt and UI customization to be defined in agent subclasses.
- 🗑️ **Legacy Discovery Events and Topic Managers:** Old class- and instance-specific discovery events and topic managers were removed, unifying agent discovery under a single, simplified model.
- 🗑️ **Obsolete Model Creation Service:** The generic `ModelCreationService` (formerly `EventModelCreationService`) has been removed, as its specific functionalities have been integrated into a new, broader service.
- 🗑️ **Dedicated Locale String Entity:** The `LocaleStringEntity` has been removed, indicating that localized strings are now handled more directly within other models or through alternative mechanisms.
- 🗑️ **Legacy `save_config.py` Example:** The `save_config.py` example script has been removed, as direct saving of agent configurations to the database via this script is no longer the intended approach.
- 🗑️ **Outdated Test Files:** Cleaned up several old test files related to agent dispatcher, agent config, and agent service database integration, as their functionalities are now covered by more integrated tests or made obsolete by architectural changes.
- 🧹 **Streamlined Timestamp Handling:** An internal utility for formatting Unix timestamps has been removed from RAG context processing.

### Refactor
- 🔄 **Consolidated Agent Configuration Management:** Standardized agent configuration handling across the system, enabling dynamic overrides and database persistence for agent instances.
- ✨ **Refined Agent and Event Discovery Architecture:** Overhauled the discovery mechanism to support both class-level and instance-level agent introspection, providing more granular control and information.
- 🏗️ **Reorganized API DTOs for Agent Representation:** Introduced dedicated DTOs (`AgentClassDTO`, `AgentInstanceDTO`) to clearly separate the concept of an agent's definition from its configured, runnable instances in the API.
- 🧹 **Agent Dispatcher & Runner Overhaul:** Performed a major refactor of the `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management.
- 🗄️ **Embedded Agent Persistence:** Re-architected agent configuration persistence by embedding agent configuration directly within `AgentEntity`, enhancing data co-location and simplifying object relationships.
- 📦 **Streamlined Vector Store Configuration:** Replaced explicit vector store configuration objects with direct factory functions for cleaner instantiation and use.
- 📁 **Project Structure Alignment:** Renamed `aihub_web/.playground` to `aihub_web/.app` to better reflect its role as the primary application directory, alongside other minor file reorganizations across the codebase.
- 📄 **Structured Content and Summary Tags:** Individual node content is now explicitly wrapped in XML-like tags (`<content>` or `<summary>`) based on its type within the RAG context.
- 🔒 **HTML Escaping for Content:** Enhanced the integrity and security of rendered content by automatically escaping HTML special characters in both headings and content within RAG context.
- 🧹 **Internal API Naming Consistency:** Renamed the internal `_get_endpoint_name` to `_get_endpoint_base_path` in endpoint discovery services for improved clarity and consistency.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- 📂 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📚 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled custom environment variable configuration for API services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 🐳 **Standardized Docker Compose Files**: Introduced a comprehensive set of Docker Compose configurations (`.latest.yml`, `.dev.yml`, `.nightly.yml`, and GPU variants) for various deployment and development environments, simplifying setup and management.
- ⚙️ **Core Infrastructure Configuration**: Added standard configuration files for Milvus, NATS, and PostgreSQL, ensuring consistent and optimized setup for these core services.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🌐 **Frontend Configuration Loading**: Updated the frontend application to load runtime configuration from a `config.json` file in production environments, allowing for dynamic environment variable injection at container startup.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices.
- 📈 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 📦 **Docker Build Process Optimization**: Streamlined Dockerfile builds for API and Bot services by optimizing Poetry installation and virtual environment handling, leading to smaller and more efficient images.
- 🌍 **Frontend Internationalization (i18n) Integration**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- ℹ️ **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 📊 **Database Indexing for Performance**: Added new indexes to `PersistedAgentEventEntity`, `PersistedProcessEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance.
- 🗣️ **Human Work Request Specification**: Human work requests (`HumanWorkRequestEvent`) now include fields for specifying target users (by ID, email, or role) and a list of forms that define the expected human input.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context in the database.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring images are correctly referenced.
- 🧪 **Evaluation Judge Schema Copying**: Ensured that the judge output schema is deep-copied before use in evaluation, preventing unintended modifications of the original schema definition.
- 📃 **Pydantic Model Default Value Alignment**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and web-facing event models (`WsServerEvent` to `ContextualizedAgentEvent`), improving clarity and maintainability.
- 📝 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components and API DTOs, focusing on concise explanations.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🏷️ **Frontend Component Naming**: Renamed client-side components and composables related to agent events to use consistent `WsServerAgentEventReadable` and `getAgentEventsInThread`/`getAgentEventTimeseries` naming.
- 🧽 **SharePoint Integration Naming**: Standardized naming conventions across SharePoint-related assets, ops, and IO managers for improved consistency (e.g., `sharepoint_` renamed to `share_point_`).

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🚫 **Deprecated `docker-compose-mnt.yml`**: Removed the old, mounting-based Docker Compose file in favor of the new, standardized volume-based configurations.
- 🗑️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.
- ✂️ **Old External Event Distributor Dependency**: The generalized `use_external_event_distributor` dependency was removed, replaced by specific agent and process distributors.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🐳 **Modernized Docker Compose Stacks**: Introduced new `docker-compose.latest.yml` and related files, providing a comprehensive and updated setup for various services including MinIO, Milvus, PostgreSQL, NATS, Redis, and more.
- ⚙️ **External Tool Configurations**: Added new configuration files for Milvus (`milvus.yaml`), NATS (`nats.conf`), and PostgreSQL (`init-multiple-dbs.sh`), improving external service setup and customization.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📦 **Streamlined Docker Builds**: Simplified Dockerfile build stages for API and Bot services, reducing image size and build times by optimizing virtual environment handling.
- 📄 **RAG Prompt Role Adjustment**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages for better model interpretation.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🔄 **Updated Frontend Paths**: Changed internal frontend build and development paths from `.playground` to `.app`, standardizing the project structure.
- 💾 **Enhanced Database Indexing**: Added new indexes to `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Ensured image URLs are consistently processed in RAG context prompts by explicitly converting their URL object to a string representation.
- 💅 **Frontend CSS Consistency**: Corrected minor CSS syntax errors in markdown renderer components.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related components, improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Docker Compose Setup**: The `docker-compose-mnt.yml` file has been removed, replaced by more comprehensive and modern Docker Compose configurations.

---



## [v0.232.0] - 2025-07-29 - Enhanced Dashboard Trend Clarity

### Changed
- 💡 **Adjusted Trend Indicator Logic:** The trending up/down visual indicators for **Exception Events** on dashboards now correctly reflect their severity, displaying green for trending down (good) and red for trending up (bad) to provide more intuitive visual feedback.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction**: Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service**: Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration**: Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients**: Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📚 **New Process-related DTOs**: Added `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to provide a clear and granular representation of process definitions and instances within the API.
- ⚙️ **Dynamic Process Endpoint Registration**: Introduced `ProcessEndpointsDiscoveryService` to automatically discover and register API endpoints for processes, including those for retrieving and submitting dynamic forms, enhancing process-API decoupling.
- 🧪 **New Comprehensive Test Suites**: Added extensive unit and integration tests for `AgentService`, `ProcessService`, `ProcessConfigEntityDocument`, and `ProcessDispatcher`, improving test coverage for agent and process components.
- 🗄️ **New Process Configuration Entities**: Introduced `ProcessConfigEntity`, `ProcessConfigEntityDocument`, and `ProcessConfigEntityEmbeddedDocument` for robust and flexible storage of process configurations in the database.
- 🗄️ **New Process Walkthrough Context**: Implemented `WalkthroughContext` for managing state and configuration specific to an individual process walkthrough, leveraging Redis for distributed storage.
- 📚 **New Granular NATS Topic Managers and Topics**: Introduced `ProcessClassTopicManager`, `AgentClassTopic`, `ProcessClassDiscoveryTopic`, `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` to enable more precise NATS event routing and subscriptions for agent and process classes and instances.
- 🐳 **New Dagster Pipeline Dockerfiles**: Introduced dedicated `Dockerfile`s for the `aihub_pipeline` and `default_rag_pipeline`, enabling robust containerization and deployment of Dagster services and specific pipelines.
- ⚙️ **Dagster PostgreSQL Configuration**: Added `dagster.yaml` to configure Dagster's run, event log, and schedule storage to use PostgreSQL, streamlining persistence setup.
- 🚀 **Automated Build & Release Workflows**: Introduced new GitHub Actions workflows for building and releasing Dagster and general pipeline Docker images, automating deployment based on tags and manual triggers.
- 🛠️ **IDE Run Configurations**: Added new IntelliJ IDEA run configurations for pipeline Dockerfiles, streamlining local development.

### Changed
- 🔄 **Unified File URL Generation**: Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution**: Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations**: Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- ⚙️ **Granular Process Discovery in API**: `ProcessService` and `ProcessEndpointsDiscoveryService` now support distinct discovery and caching mechanisms for `ProcessClassDTO` (process definitions) and `ProcessInstanceDTO` (configured processes), improving API accuracy and performance.
- ⚙️ **Dynamic Process Configuration Handling**: `ProcessDispatcher` and `ProcessRunner` now dynamically manage and inject process-specific configurations via `WalkthroughContext` and updated event structures, enabling flexible overrides and robust event routing.
- ⚙️ **Refined Agent Service Methods**: Renamed internal agent discovery and event sending methods (e.g., `discover_agent_class` to `_discover_agent_class`, `send_event` to `_send_event`) for clarity, and added a dedicated `send_agent_start_event` method.
- ⚙️ **Standardized Agent/Process Topic References**: Updated various dispatchers, subscribers, and delegators across agent and process modules to align with the new `AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` hierarchy, ensuring consistent NATS topic management.
- 📈 **Enhanced Logging and Debugging**: Added more detailed debug logging to `JetStreamEventStore` and `JSSubscriber`, improving observability of message flows.
- 📄 **Simplified Event Creation**: Streamlined the creation of `StartEvent` and `ProcessStartEvent` with new `from_raw_data` class methods, simplifying event instantiation.
- ⚙️ **Refined `WorkEvent` and `ProcessStopEvent`**: `ProcessStopEvent` now inherits from `WorkEvent` and a `process_id` field has been added to `WorkRequestEvent` for clearer event structure and context.
- ⚙️ **Dagster Integration in Docker Compose**: Integrated `dagster-webserver` and `dagster-daemon` services into `docker-compose.latest.yml`, along with `oauth2proxy` for access control and a new PostgreSQL database for Dagster's metadata, providing a comprehensive local pipeline environment.
- 🐳 **Updated MinIO Configuration**: Upgraded MinIO Docker image, standardized its environment variables, and added Traefik labels for secure external access, improving its integration into the Docker Compose stack.
- 🔑 **Updated LLM API Key Reference**: Corrected the LLM API key reference in `LLMWrappingAgent` to use `MODEL_SUI_API_KEY`, ensuring proper authentication with Azure OpenAI.
- ⚙️ **Playground Configuration**: Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates**: Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.

### Removed
- 🗑️ **Azure AI Search Vector Store**: Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Obsolete Agent Config Test**: Eliminated `test_agent_config_start_event.py` as its validation logic is now covered by more integrated tests or made obsolete by architectural changes.
- 🗑️ **Generic Discovery Request Event**: Eliminated the broad `DiscoveryRequestEvent` (and its related topic), replaced by more specific class- and instance-level discovery request events for better granularity.
- 🗑️ **Legacy Process Topic**: Eliminated the older `ProcessTopic`, replaced by the more granular `ProcessClassTopic` and `ProcessInstanceTopic` for better event routing and clarity.

### Refactor
- 🧹 **Infrastructure Configuration Restructure**: Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity**: Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation**: Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🔄 **Updated Azure Document Intelligence Key Access**: Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.
- 🧹 **Standardized Internal Method Naming**: Renamed various internal methods across dispatchers, services, and topic managers (e.g., `_create_endpoint`, `_discover_agent_class`) for improved consistency and clarity.
- 🧹 **Improved Module Structure**: Added `__init__.py` files to numerous new and existing directories (`aihub_lib/context`, `aihub_lib/infrastructure/nats`, etc.) for better Python package organization.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📂 **Process Walkthrough Context:** Introduced a new `WalkthroughContext` to manage state and configurations specific to individual process executions, improving isolation and traceability of long-running workflows.
- 🏷️ **Hierarchical Process Topics:** Added new NATS topic structures (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) to enable more granular and type-safe routing of process-related events.
- 💾 **Persistent Process Configurations:** Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to allow custom process configurations to be saved and retrieved from the database.
- 💡 **Process Instance DTOs:** Added `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to provide clear data transfer objects for representing process definitions and their configured instances.
- 🔗 **Hierarchical Agent Topics:** Introduced `AgentClassTopic` to create a more formal and hierarchical structure for agent-related NATS topics, improving event routing clarity.
- ✅ **Agent Configuration Cleanup Utility:** Added a utility method `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument` for more controlled cleanup of agent configurations in the database.
- 📊 **Dagster Infrastructure:** Integrated the full Dagster stack (webserver, daemon) into `docker-compose.latest.yml`, including OAuth2 proxy for secure access and PostgreSQL for persistent storage, facilitating robust data pipelines.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files, IO management) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⚙️ **Dagster Persistence and Concurrency:** Modified `dagster.yaml` to use separate PostgreSQL storage for runs, events, and schedules, and increased `max_concurrent_runs` for improved pipeline scalability.
- ⚡️ **Dynamic Process Configuration Injection:** The `ProcessDispatcher` now dynamically injects `ProcessConfig` objects into process steps based on the current process walkthrough's configuration, allowing for flexible process behavior.
- 📝 **Streamlined Event Creation:** Simplified the creation of `StartEvent` and `ProcessStartEvent` by introducing `from_raw_data` class methods, reducing boilerplate in API event generation.
- ⬆️ **Event Hierarchy Alignment:** Aligned `ProcessExceptionEvent` and `ProcessStopEvent` to inherit from `WorkEvent` for a more consistent event hierarchy, and moved the `process_id` field to `WorkRequestEvent`.
- 🌐 **Refined Agent and Process Discovery:** The API's agent and process discovery mechanisms now explicitly distinguish between class-level and instance-level information, providing more precise details on available configurations.
- 🐳 **Pipeline Dockerfile Paths:** Adjusted `DAGSTER_HOME` and entrypoint paths in pipeline Dockerfiles for consistency and better integration within the Docker environment.

### Fixed
- 🔑 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🚫 **Deprecated Discovery Event:** Removed the generic `DiscoveryRequestEvent`, replaced by more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent`.
- 🗑️ **Outdated Test File:** Eliminated `test_agent_config_start_event.py`, as its test logic is now covered by updated and more comprehensive test suites.
- ✂️ **Redundant Process Topic File:** Removed the old `ProcessTopic.py` file, as its functionality is now replaced by the new hierarchical process topic structure.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized `DataLakeFile` Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🔄 **Base Context Relocation:** Moved `BaseContext` from `aihub_agent` to `aihub_lib`, promoting reusability across different services.
- ⚡️ **Improved Dispatcher Lifecycle Management:** Enhanced the `BaseDispatcher.stop()` method to explicitly stop the event store and reset the initialization flag, ensuring cleaner shutdowns.
- 🔄 **Agent and Process Topic Hierarchy:** Significantly refactored NATS topic models (`AgentTopic` to `AgentInstanceTopic`, and new process topic hierarchy) and their corresponding topic managers and subscribers for clearer event routing and type safety.
- 🗄️ **Process Persistence Modernization:** Refactored `ProcessEntity` to use `ReferenceField` for process configurations and introduced `EmbeddedDocumentField` for default configurations, improving data modeling and relationships.
- 🧹 **Internal Service Method Renaming:** Renamed several internal methods in `AgentService`, `ProcessService`, and `EndpointDiscoveryServices` (e.g., `discover_agents` to `_discover_agents`, `create_endpoint` to `_create_endpoint`) for improved consistency and to distinguish public APIs from internal helpers.
- 🧽 **Test Fixture Caching:** Added `_clear_cache` calls in test fixtures for `AgentService` and `ProcessService` to ensure a clean state between tests, preventing cross-test pollution from in-memory caches.

---



## [v0.226.0] - 2025-07-25 - Strategic Reversion: Streamlined Core Services and Data Lake Simplification

### Removed
- 🗑️ **Multi-Cloud Storage Abstraction:** Eliminated the multi-cloud file access service abstraction, including dedicated implementations for Azure Blob Storage, S3, and MinIO, along with their associated configuration. This simplifies the file access layer by focusing on a single cloud provider.
- 🗄️ **S3/MinIO Data Lake Support:** Discontinued support for S3-compatible data lake storage (MinIO) in Dagster pipelines, removing its IO manager, client, and file system resources, and their related dependencies.
- 📄 **Legacy Process Configuration Persistence:** Removed outdated database entities and mechanisms for managing and persisting process configurations, streamlining the process persistence layer.
- 🏷️ **Old Agent and Process Discovery Models:** Consolidated and removed various class-level and instance-specific discovery events and topic models for agents and processes, simplifying the event and topic architecture.
- 🚶 **Process Walkthrough Context:** Deprecated and removed the `WalkthroughContext` from `aihub_process`, streamlining how process state is managed during execution.
- 📦 **Granular Process API DTOs:** Consolidated process-related Data Transfer Objects (DTOs) in `aihub_api` by removing `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO`.
- ❌ **Agent Config Persistence Tests:** Removed specific test cases related to agent configuration persistence via OpenAI integration.
- 🧹 **Internal API Cache Clearing:** Discontinued the internal cache clearing utilities (`AgentService._clear_cache`, `ProcessService._clear_cache`) from the API service.
- ⚙️ **Process Work Event Publishing Helper:** Removed the internal `_publish_work_event` helper from `AbstractEntityDelegator`, streamlining event publishing logic in processes.
- 🧪 **Process Dispatcher Tests:** Removed dedicated test files for `ProcessDispatcher` and process configuration database operations.

### Changed
- ⬇️ **Version Rollback:** Reverted the project's core versioning and `aihub_lib` dependency tags from `v0.229.0` to `v0.226.0` across all services (agent, API, bot, pipeline, IAC), indicating a return to an earlier, stable baseline.
- 🐳 **Docker Deployment Paths:** Adjusted the `DAGSTER_HOME` path and entrypoint in pipeline Dockerfiles for consistency and deployment.
- 📦 **Pipeline Dependency Downgrade:** Reverted Dagster and its related Azure dependencies to earlier versions, and removed `s3fs` and `boto3` libraries.
- 🔗 **Data Lake Interaction Logic:** Modified `AzureDataLakeIOManager` and pipeline operations to directly utilize the Azure SDK's `FileSystemClient`, replacing a previous internal abstraction.
- ⚙️ **Process Configuration Handling:** The `ProcessDispatcher` no longer explicitly manages process configurations; instead, configurations are expected to be part of the initial incoming event. Correspondingly, `ProcessService` methods for form submission no longer accept a separate `process_config` parameter.
- 📄 **Process Start Event Creation:** Simplified the creation of process start events in `ProcessService` by using a more generic `WorkEvent.deserialize_event` method.
- 🎯 **Agent Start Event Payload:** Agent `StartEvent` now passes agent configuration data as a plain dictionary instead of a Pydantic object when published by the `AgentEndpointsDiscoveryService`.
- 💥 **Agent Dispatcher Robustness:** Enhanced `AgentDispatcher` to include explicit cleanup of run-specific data on stop events and to mark execution contexts as crashed upon receiving exception events, improving state management.
- 🎛️ **Default Document Parser:** Switched the default document parser for the `default_rag_pipeline` from `DOCUMENT_INTELLIGENCE` to `DOCLING`.
- 🧪 **Pipeline Playground Configuration:** Hardcoded `NAMESPACE_NAME` and `STORE_NAME` to "test" within the pipeline playground environment.
- 🔌 **Postgres Port Exposure:** Postgres service in `docker-compose.latest.yml` now explicitly exposes port `5432` externally.
- ⚙️ **Process Runner/Delegator Queue Groups:** Updated the naming convention for queue groups in process runners and delegators to include the specific `process_id`, enhancing clarity and isolation.
- 🛠️ **Process Discovery Event Details:** The `ProcessRunner`'s discovery handler now includes `process_id` in its checks and passes the `process_config` directly within the `ProcessDiscoveryResponseEvent`.

### Added
- ✨ **Unified Discovery Request Event:** Introduced `DiscoveryRequestEvent` as a new, generic event for all discovery queries, centralizing the request mechanism.
- 🔗 **Consolidated Process Topic Model:** Added `ProcessTopic` as a new, unified topic model for all process-related events, simplifying topic structure.
- 🏞️ **Data Lake File URI Instantiation:** Implemented a `from_uri` static method in `DataLakeFile` for creating instances directly from a URI using the underlying file system client.
- 🔍 **Azure AI Search Vector Store Integration:** Re-enabled and added back the `AzureAISearchVectorStoreResource` and its associated factory functions for integration into pipelines, providing a vector store option.
- 📝 **Agent Config Start Event Tests:** Added new test files to cover the precedence logic of agent configurations provided via `StartEvent`.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `BaseContext`, `NatsConfig`, and `RedisConfig` into more concise paths within `aihub_lib` and `aihub_agent` for a cleaner package structure.
- 🔄 **Unified Topic Naming:** Renamed several topic classes (e.g., `AgentInstanceTopic` to `AgentTopic`, `ProcessClassDiscoveryResponseEvent` to `ProcessDiscoveryResponseEvent`) to align with a unified topic naming convention.
- 📦 **API Process DTO Consolidation:** Streamlined process DTOs in `aihub_api`, removing redundant intermediate DTOs and consolidating their fields into a single `ProcessDTO`.
- ⚙️ **Service Method Renaming:** Renamed internal helper methods in `AgentService` and `ProcessService` (e.g., `_discover` to `discover`, `_send_event` to `send_event`) for a more consistent public API surface.
- 📚 **Improved Docstring Clarity:** Enhanced the clarity and completeness of docstrings across various components, including IAC resources.
- 🧪 **Test Fixture Documentation:** Added explicit argument descriptions to `client_fixtures` for better readability and understanding.
- 🧹 **Process Model Simplification:** Simplified the `ProcessConfig` model by removing the `process_class` field as a required attribute, promoting more flexible process definitions.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage and Advanced Process Configuration

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- ✨ **Process Configuration Persistence:** Enabled saving and retrieving custom process configurations from the database via new entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`), allowing for persistent and shareable process setups.
- 🚀 **Process Walkthrough Context:** Introduced `WalkthroughContext` to manage per-walkthrough state and configuration, ensuring robust process execution.
- ⚡️ **Dynamic Process Configuration Injection:** Process steps can now receive `ProcessConfig` dynamically, either from the initial `ProcessStartEvent` or retrieved from the `WalkthroughContext`.
- 🚀 **Process Endpoint Dynamic Registration:** Added `ProcessEndpointsDiscoveryService` to dynamically register API endpoints for processes based on discovered process classes and instances, simplifying API exposure for new processes.
- 🧪 **Dedicated Process Configuration Tests:** Added comprehensive test suites to validate the new process configuration persistence and retrieval logic, as well as database integration for process services.
- 🛠️ **Agent Config Deletion Utility:** Added `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument` for more robust testing and management of agent configurations.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies (`dagster-webserver`, `dagster-postgres`, `dagster-azure`), and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⚙️ **Dagster Configuration Refinement:** Updated `dagster.yaml` to use direct `dagster_postgres` modules for storage, simplified database naming, and increased `max_concurrent_runs` for improved performance.
- 🐳 **Internalized Core Services in Docker Compose:** NATS, Redis, and MongoDB services in `docker-compose.latest.yml` no longer expose their ports externally, enhancing security by limiting external access to these internal components.
- 📦 **Dagster Stack Integration in Docker Compose:** Added full Dagster webserver and daemon services, along with an OAuth2 proxy, to `docker-compose.latest.yml`, streamlining local deployment of the data pipeline stack.
- ⚙️ **Process Configuration Handling:** Overhauled how process configurations are managed, prioritizing configurations provided in `ProcessStartEvent`, then database-persisted configurations, and finally falling back to the `default_process_config` defined in the runner.
- 🚀 **Process Discovery Enhancement:** Revised process discovery to distinguish between process *classes* and *instances*, providing richer metadata including `ProcessConfigSpecs` and `default_process_config`.
- 🦾 **Agent/Process Delegator Refinement:** Simplified the initialization of `AgentDelegator` and `ProcessDelegator` by removing `process_id` and adjusting topic managers to align with the new process class/instance hierarchy.
- 🔗 **NATS Topic Structure Refinement:** Introduced a more granular topic hierarchy for processes (e.g., `ProcessClassTopic`, `ProcessInstanceTopic`, `PartialProcessTopic`) and agents (`AgentClassTopic`, `AgentInstanceTopic`), replacing monolithic `ProcessTopic` and `AgentTopic` for improved clarity and routing.
- 📄 **Process Event Field Updates:** `ProcessStartEvent` now includes `process_config`, and `ProcessStopEvent` no longer requires `process_id` as it's derived from the topic, streamlining event payloads.
- ⚙️ **Process Runner Initialization:** `ProcessRunner` now explicitly accepts a `default_process_config` and uses `ProcessClassTopicManager` for broader scope management.
- 📈 **Process Service API Changes:** `ProcessService` methods (e.g., `discover_process`, `get_processes`) were updated to reflect the new process class/instance distinction and now return `ProcessInstanceDTO` or lists of `ProcessDTOs` derived from instances.
- ⚡️ **Base Dispatcher Robustness:** Enhanced `BaseDispatcher`'s `stop` method to ensure proper cleanup of event stores upon shutdown, improving application stability.
- 💬 **JetStream Logging:** Added more detailed logging for messages received by `JetStreamEventStore` for better debugging.

### Fixed
- 🐛 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes (`keys.primary_key` to `keys.key1`), ensuring robust and consistent authentication.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Old Process Topic Structure:** Removed the monolithic `ProcessTopic` and `DiscoveryRequestEvent` classes, replaced by the more granular `ProcessClassTopic`, `ProcessInstanceTopic`, `ClassDiscoveryRequestEvent`, and `InstanceDiscoveryRequestEvent`.
- 🗑️ **Deprecated Agent/Process Config Test Files:** Cleaned up outdated test files related to agent and process configuration in `aihub_agent/playground/testing` and `aihub_api/playground/testing`, as their functionalities are now covered by more integrated tests or made obsolete by architectural changes.
- 🗑️ **Removed Old Event and Topic Managers:** Removed `for_agent_instance_events` from `AgentJSSubscriber` and various overlapping methods from topic managers to streamline the NATS communication layer.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized `DataLakeFile` Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🔄 **Consolidated Context Base Class:** Moved `BaseContext` from `aihub_agent` to `aihub_lib` to centralize common context management functionality across all microservices.
- ✨ **Refined Agent and Process Discovery Architecture:** Overhauled the discovery mechanisms to support both class-level and instance-level introspection, providing more granular control and information through new DTOs and topic managers.
- 🏗️ **Reorganized API DTOs for Processes:** Introduced a new hierarchy of DTOs (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`) to clearly separate the concept of a process's definition from its configured, runnable instances in the API, and refactored `ProcessDTO` to inherit from this hierarchy.
- 🧹 **Standardized Persistence for Processes:** Refactored process entity persistence (`ProcessEntity`) to use references and embedded documents for `ProcessConfigEntity` types, providing a more robust and flexible data model.
- 🧹 **Standardized `from_specs` Methods:** Renamed `from_dto` to `from_specs` in `ProgramInSpecsEntity`, `HumanInSpecsEntity`, and `AgentInSpecsEntity` for consistency when converting from event specifications.
- 🧹 **Test Cleanup:** Added `_clear_cache` calls in test fixtures for various `AgentService` and `ProcessService` tests to ensure proper test isolation and a clean state before each test run.

---



## [v0.226.0] - 2025-07-24 - Dynamic Agent Configuration and Structured Knowledge Enhancements

### Added
- ✨ **Dynamic Agent Configuration**: Introduced the ability to dynamically provide agent configurations via `StartEvent` payloads or load them from a new database persistence layer, allowing flexible overrides of default settings.
- 🚀 **Granular Agent Discovery**: Implemented new mechanisms for discovering both agent *classes* (definitions) and specific agent *instances* (configured, runnable versions) through dedicated NATS events and DTOs (`AgentClassDTO`, `AgentInstanceDTO`).
- 🗄️ **Database Persistence for Agent Configurations**: Agent configurations can now be explicitly saved to and retrieved from a MongoDB database, enabling persistent and shareable agent setups across deployments.
- 📄 **New Pydantic Models for Vector Store Configuration**: Introduced dedicated Pydantic models (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`) for configuring vector stores directly within agent configurations, enhancing type safety.
- 🏗️ **New `ModelCreationService`**: A consolidated service for dynamically generating Pydantic models from event and configuration schemas, replacing the previous `EventModelCreationService`.
- 📊 **Hierarchical Document Headings in RAG**: RAG outputs now dynamically render hierarchical document headings (H1-H6) and explicitly tag content with `<content>` or `<summary>`, greatly improving context readability.
- 🔒 **HTML Escaping for Rendered Content**: Headings and content in RAG outputs are now automatically HTML-escaped, enhancing security and preventing rendering issues.
- 🧪 **Comprehensive Agent Dispatcher Tests**: Added new unit and integration tests for the `AgentDispatcher` to ensure robust handling of dynamic agent configurations and context management.
- 📦 **Pipeline Job for Asset Materialization**: Introduced a new `materialize_asset_job` utility to simplify creating jobs for specific asset selections in data pipelines.
- 📅 **Automated Playground Pipeline Workflows**: Implemented new daily schedules for the playground environment to automate source observation and document removal processes.

### Changed
- ⚙️ **Refined Agent Configuration Loading**: The Agent Dispatcher now intelligently prioritizes agent configurations from `StartEvent` payloads, then database-persisted settings, and finally falls back to the `default_agent_config` defined in the runner.
- 💡 **Updated LLM and Vector Store Configurations**: Agent configurations (e.g., `RAGAgent`, `ExpertAskingAgent`) now leverage more precise type unions for LLMs (Azure OpenAI, Gemini, OpenAI-like) and dedicated Pydantic models for vector stores.
- 🔗 **Streamlined Vector Store Integration**: RAG and Retrieval agents now convert vector store configurations to LlamaIndex-compatible objects using a new `to_llama_index()` method.
- 🔄 **Agent Runner Initialization**: Agent runners (`AgentRunner`, `AgentTestRunner`, `MultiprocessAgentRunner`) now explicitly accept a `default_agent_config` parameter.
- 🌐 **API Agent Discovery**: The Agent API now discovers and returns full agent *instances* (including their specific configurations) instead of just class definitions.
- 💬 **`ChatService` Configuration Passing**: `ChatService` now passes agent configuration data as a dictionary within `UserMessageEvent` for new conversations.
- ⚡️ **Improved Background Task Management**: Dispatchers and subscribers (e.g., `AgentDispatcher`, `JetStreamEventStore`, `JSSubscriber`, `NCSubscriber`, `ProcessDispatcher`, `ProcessRunner`) now explicitly track their `asyncio.Task` instances for more robust lifecycle management.
- 📄 **Agent Documentation Updates**: Documentation for agents has been updated to reflect the new `default_agent_config` parameter, the mandatory `agent_class` field, and the removal of the `system_prompt` field.
- 🏷️ **NATS Discovery Topic Naming**: NATS discovery topics have been renamed (`INSTANCE_DISCOVERY_TOPIC`, `CLASS_DISCOVERY_TOPIC`) to clearly differentiate between instance and class discovery.
- 🌍 **Default Ingested Node Language**: The default language for newly ingested nodes is now German.
- ⚙️ **Pipeline Automation Scheduling**: Removed eager automation conditions for `removed_documents_factory` and `removed_data_lake_files_factory`, shifting to explicit job-driven scheduling.
- 📦 **SharePoint I/O Manager**: The SharePoint observable asset (`observable_share_point_factory`) now uses a dedicated `sharepoint_io_manager`.
- 💻 **Environment Configuration**: Updated environment variables for CosmosDB and Azure AD connections in development setups.

### Fixed
- 🐛 **Robust Figure Deletion in Pipelines**: Improved the data lake figure deletion process in pipelines by checking for directory existence before attempting deletion.
- 🖼️ **Azure Graph Service Image Retrieval**: Enhanced user profile image retrieval to explicitly handle 404 responses from Azure Graph API.
- 🐞 **API Gunicorn Entry Point**: Corrected the Gunicorn entry point in the API Makefile.
- 💬 **Process DTO Description**: Fixed a minor typo in the `ProcessDTO` description in the generated SDK.

### Removed
- 🗑️ **Deprecated Agent Configuration Fields**: Eliminated the `system_prompt`, `color`, and `voice` fields from `AgentConfig` and `AgentConfigDTO` (they were previously marked as deprecated).
- 🗑️ **Legacy Agent Configuration Persistence**: Removed older standalone and embedded MongoDB documents for agent configurations, consolidating persistence under the new `AgentConfigEntity` model.
- 🗑️ **Obsolete `format_unix_timestamp` Utility**: Removed an internal utility for formatting Unix timestamps, as date handling is now managed by the underlying system.
- 🗑️ **Redundant Process Discovery Methods**: Removed duplicate process discovery subject methods from `ProcessInstanceTopicManager`.

### Refactor
- 🧹 **Agent Dispatcher and Runner Overhaul**: Performed a major refactor of `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management.
- 🔄 **Unified Agent Discovery Architecture**: Consolidated and streamlined agent discovery by merging class and instance-level events and topic managers into a single, consistent model.
- 🗄️ **Decoupled Agent Configuration Persistence**: Re-architected agent configuration persistence by introducing `AgentConfigEntity` as a base, enabling `AgentEntity` to reference custom configurations and embed default ones.
- 📦 **Streamlined Vector Store Integration**: Replaced explicit vector store configuration objects in agent configs with abstract base classes and factory functions for cleaner instantiation.
- 📁 **DTO Consolidation**: Consolidated agent-related Data Transfer Objects (DTOs) into a dedicated `dto` subdirectory, introducing `AgentClassDTO`, `AgentInstanceDTO`, and `MinimalAgentDTO` for clearer agent representation.
- ⚙️ **Renamed `EventModelCreationService`**: Renamed to `ModelCreationService` to reflect its broader utility beyond just event models.
- 🧹 **Codebase Naming Alignment**: Standardized `_get_endpoint_name` to `_get_endpoint_base_path` in endpoint discovery services and updated `AGENT_CLASS` casing in test files.
- 📄 **Improved EventSpec Handling**: Updated `EventSpec` creation to consistently use `EventSpecs` objects, improving internal data handling.
- 🧪 **Test Suite Restructuring**: Relocated and reorganized internal test files for agent configuration and service logic to align with new architectural patterns.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs. This includes new API endpoints, DTOs, persistence models, and event streaming.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 📦 **New Docker Infrastructure Components**: Added `Dockerfile` for the web UI, `nginx.conf`, `config.template.json`, and new `docker-compose` files to support various deployment scenarios for the entire stack.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Agent API Route Renaming**: Renamed agent-related API paths (e.g., `/events/threads` to `/events/agents/threads`) for clearer distinction from process-related events.
- 📚 **Prompt Refinements and Image Handling**: Adjusted the RAG context prompt role from `system` to `user` and fixed image URL processing for consistency across languages.
- ⚡️ **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📦 **Docker Build Optimization**: Streamlined the Docker build process for Python services (`aihub_api`, `aihub_bot`) by simplifying virtual environment handling.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 👥 **Human Delegator Enhancements**: The `Human.In` and `Human.Out` process delegators now support more granular user targeting (e.g., by user ID, email, or role) and allow defining start forms directly within the process definition.
- ⚙️ **Process Dispatcher Logic**: Updated the process dispatcher to correctly map and utilize the new human targeting fields.
- 🔍 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context in the database.
- 🔒 **NATS Topic Validation for Processes**: Implemented stricter validation for NATS process discovery topics to ensure only correctly formatted subjects are processed, preventing misrouted messages.
- 💾 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), event objects (`WsServerEvent` to `ContextualizedAgentEvent`), and SharePoint-related assets for improved clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.

---



## [api-v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- ✨ **Introduced `LLMWrappingAgent`:** A new agent designed to wrap and interact with Large Language Models, providing a flexible interface for LLM integrations, complete with its dedicated Dockerfile and configuration settings.
- 🚀 **Automated Build & Release Workflows:** New GitHub Actions workflows now automate Docker image builds and releases for agents, Dagster, and pipelines, triggered by new tags, manual dispatch, and specific feature branches.
- 📄 **Centralized Event Creation:** Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent`, centralizing the creation logic for these events.
- 🗄️ **Database Persistence for Process Configurations:** Introduced new entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to allow custom process configurations to be saved, retrieved, and embedded in the database.
- 👥 **Granular Process Discovery DTOs:** Added new Data Transfer Objects (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`) to represent process information at different levels of detail, supporting the new hierarchical discovery model.
- 🚀 **Dynamic Process API Endpoint Registration:** Implemented `ProcessEndpointsDiscoveryService` to dynamically register API endpoints for processes based on discovered configurations, enhancing API flexibility.
- 🧪 **Comprehensive Process Testing:** Introduced new unit and integration tests for `ProcessDispatcher`, `ProcessConfig` persistence, and `ProcessService` database interactions, ensuring robust process management.
- 📦 **Dagster Integration:** Added `dagster.yaml` for Dagster configuration and integrated `dagster-webserver` and `dagster-daemon` services into the main Docker Compose stack.
- 🔐 **Secure MinIO Dashboard Access:** Configured Traefik rules to expose the MinIO dashboard securely via `datalake.${DOMAIN}` in the Docker Compose setup.
- 🔑 **OAuth2 Proxy for Dagster:** Integrated `oauth2proxy` with Traefik to provide secure OAuth2 authentication for the Dagster webserver.
- 📚 **`process_class` in `ProcessConfig`:** A new `process_class` field has been added to `ProcessConfig` for consistent process class identification.
- 📝 **Per-Walkthrough Context:** Introduced `WalkthroughContext` for per-walkthrough state storage within processes, enabling more granular control and data management for complex workflows.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs, abstracting away cloud-specific implementations.
- 🖼️ **Enhanced Image Resolution:** Improved `combine_nodes_in_order` in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage, handling `s3://` URIs.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client interfaces, improving flexibility and maintainability.
- ⚙️ **Refined Agent Configuration Loading Logic:** The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 💡 **Updated NATS Topic Hierarchy:** Refactored NATS topic structures for both agents and processes to introduce a clearer hierarchy, distinguishing between class-level and instance-level topics (e.g., `AgentTopic` is now `AgentInstanceTopic`).
- 📈 **API Agent Discovery Return Type:** The API's agent discovery endpoints now directly return `AgentDTO` objects instead of raw `AgentInstanceDTO`s, simplifying API consumption.
- 🌐 **Process API Configuration Handling:** The process API now explicitly retrieves and passes `process_config` when submitting forms, ensuring correct process instantiation and continuation.
- 🧪 **Pipeline Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- 📊 **Enhanced NATS Server Logging:** Increased the default logging level for the NATS server in `nats.conf` to include `debug` and `trace` information, improving operational visibility.
- 💾 **NATS JetStream Persistence:** Changed the JetStream store directory to a persistent volume in `docker-compose.latest.yml`, ensuring data durability across container restarts.
- 📈 **API Service Logging:** The `aihub_api` service's logging level in `docker-compose.latest.yml` has been set to `DEBUG`, providing more verbose output for development and troubleshooting.
- ⚙️ **`DispatchableWorkflow` Event Acceptance:** `DispatchableWorkflow.get_steps_waiting_for_event` now accepts `WorkEvent` types, enabling broader event handling in workflows.
- 📦 **Dagster Dependency Updates:** Upgraded Dagster and related dependencies, and added `dagster-aws`, `s3fs`, and `boto3` to support comprehensive S3/MinIO integrations.

### Fixed
- 🐛 **Process Work Event `process_id` Assignment:** Ensured that `process_id` is correctly assigned to `WorkEvent`s before publishing in the `SimulatedProcessApiTestRunner` to maintain proper event context.
- 🔑 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.
- 🐛 **MinIO Environment Variable Names:** Corrected the environment variable names for MinIO root user and password in `docker-compose.latest.yml` to match the updated MinIO image requirements.

### Removed
- 🗑️ **Deprecated `AnonymousFileAccessService`:** The old generic `AnonymousFileAccessService` has been removed, replaced by the new multi-cloud `FileAccessServiceConfig` abstraction.
- 🗑️ **Generic `DiscoveryRequestEvent`:** The generic `DiscoveryRequestEvent` has been removed, superseded by more specific class- and instance-level discovery events.
- 🗑️ **Old `ProcessTopic` Hierarchy:** The legacy `ProcessTopic` has been removed, replaced by a new, more granular hierarchy of process topics (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`).
- 🗑️ **`process_id` from `ProcessStopEvent`:** The `process_id` field has been removed from `ProcessStopEvent`, as this information is now managed by the process context.
- 🗑️ **Deprecated AgentJS Subscriber Method:** The `for_agent_instance_events` method in `AgentJSSubscriber` has been removed due to refactored agent topic structures.
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining available vector store integrations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `BaseContext`, `NatsConfig`, and `RedisConfig` into dedicated `infrastructure` subpackages within `aihub_lib` for clearer logical grouping and improved project structure.
- 🔄 **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- ⚙️ **NATS Topic Manager Simplification:** Streamlined various NATS topic managers (`AgentClassTopicManager`, `AgentThreadTopicManager`, `ProcessTopicManager`, `ProcessWalkthroughTopicManager`) to align with the new, more explicit class- and instance-level topic hierarchy.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- 🌐 **Process Dispatcher Context Management:** Introduced `WalkthroughContext` for per-walkthrough state management and refined how process configurations are loaded and managed within the `ProcessDispatcher`.
- 🐳 **Docker Compose Internal Port Management:** Removed explicit port exposures for internal services like Milvus, Postgres, NATS, Redis, and MongoDB in `docker-compose.latest.yml`, enhancing security by limiting external access to these internal components.
- 📦 **Docker Image Build Optimization:** Removed `ca-certificates` from the `aihub_api` Dockerfile for a slightly leaner runtime image.
- 🧹 **Internal API Service Method Renaming:** Renamed internal API service methods (e.g., `discover_agent_class` to `_discover_agent_class`) and adjusted cache clearing to be private for better encapsulation.
- ⚙️ **Process `ProcessEntity` Schema Update:** Updated the `ProcessEntity` schema to use `ReferenceField` for `process_config` and added an `EmbeddedDocumentField` for `default_process_config`, aligning with the new configuration persistence model.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications via `ContextualizedProcessEvent`.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled Custom Environment Variable Configuration for API Services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 🐳 **New Docker Compose Configurations**: Introduced `docker-compose.latest.yml` and other environment-specific Docker Compose files, providing structured setups for various deployments including MinIO, Milvus, Postgres, NATS, Redis, MongoDB, and CPU-based LLM inference services.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses (from 1 to 100), improving performance for frequently requested agent lists.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📚 **Pydantic Model Default Handling**: Updated numerous Pydantic model definitions to assign default values directly to attributes instead of using `Field(default=...)`, aligning with best practices for Pydantic V2.
- 📦 **API Runtime Dependency**: Added `gunicorn` as a dependency for both `aihub_api` and `aihub_bot` to enable production-ready WSGI serving.
- ⚙️ **SharePoint Client Configuration**: Refined the SharePoint resource configuration to explicitly set `target_folders` and `exclude_folders` to `None` by default, improving clarity.
- 💬 **Example Process Dynamic Forms**: Updated `AgenticCVProcess` to demonstrate the use of dynamic forms for human interaction steps, allowing for more flexible UI generation.
- 🐍 **Example Event Structures**: Modified various playground events (`AnalyzedCV`, `AcceptCV`, `RejectCV`) to incorporate dynamic form elements and enhance data structures for process examples.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer (`AgentEntity`) to gracefully handle cases where a specific agent might not be found by returning `None` instead of raising an exception.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context in `PersistedProcessEventEntity`.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed, preventing potential routing errors.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced `BaseEvent`'s `model_dump` and `model_dump_json` to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Image URL Handling in RAG Prompts**: Corrected an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring images are now correctly referenced and displayed.
- 🔗 **Makefile Version Alignment**: Updated the `Makefile` to reflect the current project version.
- 💾 **Frontend CSS Minor Fix**: Corrected minor CSS formatting in the Markdown renderer to ensure proper rendering.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow (`auto-draft-pr.yml`) that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Docker Compose File**: The `docker-compose-mnt.yml` file has been removed, superseded by the new, more structured Docker Compose configurations.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend (`pages/service/health.vue`) was removed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor` and `ExternalProcessEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components (`ThreadContext`, `RunTraceCoordinator`, `AgentService`, `EventPersister`, `AgentDTO`, `OpenaiController`, `ThreadController`, `ExternalAgentEventDistributor`), focusing on concise explanations.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure, enhancing test suite organization.
- 📦 **Dockerfile Optimization**: Streamlined Dockerfiles for `aihub_api` and `aihub_bot` by optimizing dependency installation and virtual environment management across build stages.
- 🔄 **SharePoint Naming Standardization**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).
- 📌 **Pydantic Field Annotations**: Updated `Field` annotations in several Pydantic models across the codebase to provide more precise descriptions and align with updated schema generation.
- 💬 **Improved Internal Logging**: Enhanced logging in the `parse_document_from_data_lake` operation to output the Data Lake file URI, improving observability for data processing.
- 🌐 **Web App Directory Structure**: Restructured the core web application directory from `.playground` to `.app`, centralizing application files for clearer separation from project root.

---



## [web-v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🦾 **Introduced `LLMWrappingAgent`**: A new agent designed to wrap and interact with Large Language Models, providing a flexible interface for LLM integrations. This includes its dedicated Dockerfile, configuration settings, and main application entry point.
- 🚀 **Automated CI/CD Workflows**: Added new GitHub Actions workflows to automate Docker image builds and releases for agents, Dagster, and pipelines, improving deployment efficiency and consistency.
- 🗄️ **Process Configuration Persistence**: Introduced `ProcessConfigEntity`, `ProcessConfigEntityDocument`, and `ProcessConfigEntityEmbeddedDocument` to enable robust storage and retrieval of process configurations in the database.
- 🧪 **Comprehensive Test Utilities**: Added extensive new unit and integration tests for agent and process dispatchers and services, enhancing test coverage and ensuring reliability.
- ⚙️ **Dagster Configuration**: Added `dagster.yaml` for configuring Dagster's run, event log, and schedule storage to use PostgreSQL, and setting up a queued run coordinator.
- 🗄️ **Process Walkthrough Context**: Introduced `WalkthroughContext` to provide dedicated storage and retrieval for state and configuration specific to a process walkthrough.
- 🔗 **New Process Topic Hierarchy**: Introduced `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` to provide a more structured and granular representation of NATS subjects for process-related events.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- 🔗 **Refined NATS Topic Hierarchy**: Updated agent and process dispatchers, runners, subscribers, and delegators to leverage the new `AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` for more precise event routing and identification.
- 🌐 **Enhanced Agent & Process Discovery**: Major overhaul of discovery mechanisms to distinguish between *class* and *instance* levels, providing more granular control and comprehensive responses, including `ProcessConfigSpecs`.
- 🐳 **Comprehensive Docker Compose Update**: Significant updates to `docker-compose.latest.yml`, including:
    *   Updated MinIO configuration and added Traefik labels.
    *   Added `dagster` database to PostgreSQL and removed external port exposure for internal services (Postgres, Milvus, Prometheus, Grafana, Phoenix, NATS, Redis, MongoDB), enhancing security.
    *   Introduced a new **Dagster stack** (webserver, daemon, and OAuth2 Proxy integration).
    *   Set API `LOG_LEVEL` to `DEBUG` for increased verbosity.
- ⚙️ **NATS Operational Enhancements**: Enabled debug and trace logging for NATS and configured JetStream to use a persistent store directory, improving operational visibility and data durability.
- 🛠️ **Dynamic Process Config Injection**: Implemented logic to inject `ProcessConfig` into process steps at runtime, allowing steps to access the current process configuration.
- ⬆️ **SDK Schema Update**: Updated the generated SDK schema for `ModelDetailsSchema` to reflect a new default timestamp.

### Fixed
- 🐛 **Improved Dispatcher Shutdown**: Ensured `BaseDispatcher`'s `stop` method correctly handles uninitialized states, preventing errors during shutdown.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Replaced Legacy File Access Service**: Deprecated `AnonymousFileAccessService` in favor of the new, more flexible multi-cloud `FileAccessServiceConfig` and its specialized implementations.
- 🗑️ **Removed Generic Discovery Event**: Eliminated the broad `DiscoveryRequestEvent` in favor of more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent` for clearer discovery patterns.
- 🗑️ **Removed Legacy Process Topic**: Eliminated the old `ProcessTopic` in favor of the new hierarchical topic models (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`).
- 🗑️ **Removed Redundant Agent Event Subscriber**: Eliminated `for_agent_instance_events` from `AgentJSSubscriber` to streamline subscriptions to control events.
- 🗑️ **Removed Redundant Agent Config Tests**: Eliminated outdated test files related to agent configuration handling in `StartEvent`, as this logic is now integrated and tested elsewhere.

### Refactor
- 🧹 **Infrastructure Configuration Restructure**: Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity**: Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation**: Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🔄 **Updated Azure Document Intelligence Key Access**: Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.
- 🧹 **Consolidated Base Context**: Moved `BaseContext` from `aihub_agent` to `aihub_lib` for better reusability across different modules.
- 🏗️ **Reorganized API DTOs**: Introduced dedicated DTOs (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`) for process representation to clearly separate concept definition from instances in the API.
- 🗄️ **Enhanced Process Entity Management**: Updated `ProcessEntity` to use the new `ProcessConfigEntityDocument` and `ProcessConfigEntityEmbeddedDocument` for managing process configurations, and refactored `create_or_update` for clearer parameter handling.

---



## [v0.231.0] - 2025-07-29 - Enhanced Agent Testing with Custom Events

### Added
- 🚀 **Customizable Agent Simulation Events:** Introduced the ability to specify custom `start_events` and `stop_events` for the `SimulatedAgentApiTestRunner`, greatly expanding the flexibility for testing agent behavior and API interactions under diverse conditions.
- 🧪 **New Test Event Definitions:** Added `TestStartEvent` and `TestStopEvent` classes to facilitate the creation of unique testing scenarios for agent event processing.
- ✨ **Comprehensive Custom Event Test Suite:** Implemented a new test suite (`test_agent_api_with_custom_event.py`) to thoroughly validate the handling of custom start and stop events within the agent API, ensuring robust and predictable agent responses.

### Removed
- 🗑️ **Internal Claude AI Integration Scripts:** Removed development-specific scripts related to Claude AI integration, streamlining the project's internal tooling.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction**: Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service**: Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration**: Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients**: Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- ⚙️ **S3/MinIO Configuration**: Added `S3Config` to manage connection parameters for S3-compatible storage services, supporting new data lake integrations.
- 🚀 **Dagster and Pipeline Build Workflows**: New GitHub Actions workflows automate the Docker image build and release process for Dagster and pipelines.
- 🛠️ **IDE Docker Run Configurations**: Added new IntelliJ IDEA run configurations for building Dagster and pipeline Docker images, streamlining local development.
- 🏗️ **Standardized `StartEvent` Creation**: Added a new `from_raw_data` class method to `StartEvent`, simplifying its creation from raw API inputs and ensuring consistent event instantiation.
- 📄 **Process Configuration Specifications**: Introduced `ProcessConfigSpecs` to provide a clear schema and parameters for process configurations during discovery, aiding external consumers.
- 🚀 **Process Instance Discovery Response**: Added `ProcessInstanceDiscoveryResponseEvent` to provide detailed information about specific process instances, including their configuration, during discovery.
- 🗄️ **Process Configuration Persistence**: Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to enable persistent storage and retrieval of process configurations, supporting both standalone and embedded document patterns.
- 🗄️ **Agent Config Deletion Utility**: Added `delete_if_exists_for_class_and_id` method to `AgentConfigEntityDocument` for targeted cleanup of agent configurations in the database.
- 🧪 **Tested Custom Agent Configurations**: Added a new test case to verify that custom agent configurations are correctly applied during chat completions.
- 🧪 **New Process Configuration and Service Tests**: Introduced comprehensive unit and integration tests for process configuration database operations and process service logic, ensuring robustness and correctness.
- 🧪 **New Process Dispatcher Tests**: Introduced comprehensive unit and integration tests for `ProcessDispatcher`, covering `WalkthroughContext` integration and dynamic configuration handling.
- 🏗️ **Process Walkthrough Context**: Introduced `WalkthroughContext` to manage state and configuration specifically for individual process walkthroughs, enhancing process execution isolation.
- ⚙️ **Dagster PostgreSQL Configuration**: Added a default `dagster.yaml` to configure Dagster to use PostgreSQL for run, event, and schedule storage.
- 🐳 **Docker Compose Updates**: Added new services for **Dagster webserver** and **daemon**, integrated **OAuth2 Proxy** for Dagster.
- 🏗️ **Process Class Topic Manager**: Introduced `ProcessClassTopicManager` to manage event subjects at the process class level, enabling more granular topic hierarchy.
- ⚙️ **Enhanced Process Discovery Topic Management**: Introduced new methods (`get_process_class_discovery_subject_request`, `get_process_class_discovery_subject_response`) to `ProcessTopicManager`, enabling distinct class-level process discovery.
- 🏗️ **New Agent Class Topic**: Introduced `AgentClassTopic` to define subjects at the agent class level, complementing `AgentInstanceTopic` for a clearer agent topic hierarchy.
- 🏗️ **New Process Class Discovery Topic**: Introduced `ProcessClassDiscoveryTopic` for class-level process discovery requests and responses, providing a more granular discovery mechanism.
- 🏗️ **New Hierarchical Process Topics**: Introduced a comprehensive topic hierarchy for processes with `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic`, replacing the single `ProcessTopic` for more precise subject management.

### Changed
- 🔄 **Unified File URL Generation**: Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution**: Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations**: Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration**: Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates**: Upgraded Dagster and related dependencies (`dagster-webserver`, `dagster-postgres`, `dagster-azure`), and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⚙️ **Dockerfile Entrypoint Update**: Modified `LLMWrappingAgent`'s Dockerfile to use an `AGENT_NAME` environment variable and `exec` for improved process management.
- ⚙️ **Process Start Form Enhancements**: Updated `ProcessController` to fetch the process configuration from discovered instances and pass it during submission of start forms, improving data flow.
- ⚙️ **Added `process_id` to Work Request Events**: Included a `process_id` field in `WorkRequestEvent` to ensure proper identification of the associated process instance.
- ⚙️ **Process Configuration Enhancements**: Added a `process_class` field to `ProcessConfig` for better identification and introduced a `from_entity` method to facilitate conversion from database entities.
- ⚙️ **Improved Dispatcher Shutdown**: Enhanced `BaseDispatcher`'s `stop` method to prevent redundant shutdowns and provide clearer logging.
- ⚙️ **Process Runner Modernization**: Updated `ProcessRunner` to use `default_process_config` and `ProcessClassTopicManager`, enabling class-level process discovery via `ProcessClassDiscoveryResponseEvent` and simplifying queue group naming.
- ⚙️ **Expanded Dispatchable Workflow Trigger Events**: Updated `DispatchableWorkflow` to allow steps to be triggered by both `ControlEvent` and `WorkEvent` types, increasing flexibility for process automation.
- ⚙️ **Enhanced Process Start Event**: Added `process_config` field and `from_raw_data` method to `ProcessStartEvent`, enabling dynamic configuration at process initiation.
- 🐳 **Docker Compose Updates**: Upgraded MinIO configuration and its image tag, added new services for **Dagster webserver** and **daemon**, integrated **OAuth2 Proxy** for Dagster, removed direct PostgreSQL port exposure for enhanced security, and refined Traefik labels.
- 📈 **Enhanced Event Store Logging**: Added detailed debug logging to `JetStreamEventStore` for received messages and deserialized events, improving observability and troubleshooting.
- 📈 **Improved JetStream Subscriber**: Added debug logging for unsubscription and switched to named parameters for subscription calls, enhancing clarity and observability.
- 🐛 **API Endpoint Reordering**: Minor reordering of API endpoints in the development playground for consistency.
- ⬆️ **SDK Schema Update**: Updated the default `created` timestamp in `ModelDetailsSchema` within the generated SDK.

### Fixed
- 🐛 **Azure Document Intelligence Key Access**: Aligned the method for retrieving primary keys from Azure Document Intelligence services (`keys.key1` instead of `keys.primary_key`) with recent API changes.
- 🐛 **Fixed Circular Dependency**: Resolved a circular import issue in `UserWithAccessDTO` by lazy-loading the `ProcessService` import.
- 🧹 **Standardized Agent Runner Initialization**: Corrected the Azure OpenAI API key reference in `LLMWrappingAgent`'s main entry point.

### Removed
- 🗑️ **Azure AI Search Vector Store**: Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Removed Obsolete Test File**: Deleted `test_agent_config_start_event.py` as its functionality is now covered by other tests or made obsolete by architectural changes.
- 🗑️ **Removed Generic Discovery Event**: Eliminated the broad `DiscoveryRequestEvent`, replaced by more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent` for clearer discovery patterns.
- 🗑️ **Streamlined Agent JetStream Subscriber**: Removed redundant `for_agent_instance_events` method, simplifying the agent subscription API.
- 🗑️ **Deprecated Process Topic**: Eliminated the single `ProcessTopic` in favor of a new hierarchical structure.

### Refactor
- 🧹 **Consolidated Base Context**: Moved `BaseContext` from `aihub_agent` to `aihub_lib` for improved reusability and architectural clarity.
- 🧹 **Standardized Package Structure**: Added `__init__.py` files to various new or reorganized packages (`aihub_lib.context`, `aihub_lib.infrastructure.nats`, `aihub_lib.infrastructure.redis`, `aihub_lib.infrastructure.s3`, `aihub_pipeline.io.base`, `aihub_pipeline.resources.data_lake.azure`, `aihub_pipeline.resources.data_lake.base`, `aihub_pipeline.resources.data_lake.s3`, `aihub_pipeline.app`, `aihub_process.context`, `aihub_process.context.walkthrough`, `aihub_process.playground.testing`, `aihub_process.playground.testing.tests`).
- 🧹 **Infrastructure Configuration Restructure**: Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 🧹 **Docstring Cleanup**: Removed redundant parameter descriptions from various Infrastructure-as-Code (IaC) and API test fixture docstrings.
- 🧹 **Centralized `DataLakeFile` Creation**: Removed the `from_uri` static method from `DataLakeFile`, delegating its instantiation based on URI to cloud-specific data lake client implementations for better encapsulation.
- 🧹 **Streamlined Process Event Hierarchy**: Refactored `ProcessExceptionEvent` and `ProcessStopEvent` to directly inherit from `WorkEvent`, simplifying the event hierarchy and removing a redundant `process_id` field from `ProcessStopEvent`.
- 🔄 **Updated Agent Topic Hierarchy**: Refactored `AgentDispatcher` to align with new topic naming conventions, using `AgentClassTopic` and `AgentInstanceTopic` from `aihub_lib` for clearer subject management.
- 🔄 **Comprehensive Process Discovery Overhaul**: Implemented a new hierarchical process discovery mechanism (`_discover_process_class`, `discover_process_instances_by_class`, `discover_process_instances`), aligning with agent discovery changes to support both class-level and instance-level process configurations. This includes updated caching strategies, new private helper methods (`_send_event`, `_clear_cache`), and refined process start form submissions.
- 🔄 **Simplified Agent Discovery API Response**: The `discover_agents` API endpoint now directly returns `AgentDTO` objects, streamlining the response and reducing redundant DTO conversions.
- 🔄 **Process Simulation Alignment**: Updated `SimulatedProcessApiTestRunner` to match the new `aihub_lib` process discovery events (`ProcessClassDiscoveryResponseEvent`, `ProcessInstanceDiscoveryResponseEvent`), topic naming, and now uses `default_process_config` for clarity.
- 🔄 **Process Endpoint Discovery Enhancement**: Significantly refactored `ProcessEndpointsDiscoveryService` to leverage the new hierarchical process configuration, privatized internal endpoint creation methods, and now passes `process_config` to form submission logic.
- 🔄 **Azure Data Lake IO Manager Updates**: Refactored `AzureDataLakeIOManager` to leverage the new `AzureDataLakeClient` abstraction, improving file handling and metadata operations within pipelines.
- 🔄 **Process Dispatcher Overhaul**: Reworked `ProcessDispatcher` to integrate `WalkthroughContext` for per-walkthrough state, enable dynamic process configuration injection into steps, and align with the new hierarchical process topic structure (`ProcessClassTopic`, `ProcessInstanceTopic`).
- 🔄 **Updated NATS Topic Exports**: Aligned `aihub_lib.nats.topics` exports to reflect the new, refined topic hierarchy, including `AgentInstanceTopic`, `ProcessInstanceTopic`, and `ProcessInstanceDiscoveryTopic`.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📄 **New Process DTOs:** Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to provide clearer and more granular representations of process information within the API.
- 🏷️ **Hierarchical NATS Topic Models:** Added new NATS topic models (`AgentClassTopic`, `ProcessClassDiscoveryTopic`, `ProcessInstanceTopic`, `ProcessClassTopic`, `PartialProcessTopic`) to establish a more structured and hierarchical topic system for agents and processes.
- 🔄 **Walkthrough Context:** Introduced `WalkthroughContext` to provide dedicated per-walkthrough state storage for process execution.
- 🗄️ **Utility for Agent Config Deletion:** Added `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument` for cleaner management of agent configurations.
- 🚀 **Event Creation Utilities:** Implemented `from_raw_data` class methods for `StartEvent` and `ProcessStartEvent` to streamline event instantiation from raw input data.
- 💬 **Process ID in Work Events:** Added a `process_id` field to `WorkRequestEvent` to enhance traceability of work requests within processes.
- 🗄️ **Process Configuration Entities:** Introduced new persistence entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) for robust storage and management of process configurations.
- 🏷️ **Process Class in Process Config:** Added a `process_class` field to `ProcessConfig` for more explicit process classification.
- 📦 **S3 Client Dependencies:** Included `boto3` and `s3fs` as new Python dependencies to support S3/MinIO integration in pipelines.
- 🐳 **Dagster Docker Integration:** Integrated Dagster services (`oauth2proxy`, `dagster-webserver`, `dagster-daemon`) into the `docker-compose.latest.yml` for unified deployment.
- 🧪 **Comprehensive Process Testing:** Added new test files for `ProcessConfig` database operations, `ProcessService` database integration, and `ProcessDispatcher` unit tests to ensure robust process management.
- 🎛️ **Process Class Topic Manager:** Introduced `ProcessClassTopicManager` and associated methods to support class-level process topic management.
- 🚀 **Delegator Event Publishing Helper:** Added `_publish_work_event` helper method to `AbstractEntityDelegator` for standardized work event publishing.
- 🧪 **Test Cache Cleanup:** Added explicit `_clear_cache` methods to `AgentService` and `ProcessService` for improved test isolation and cleanup.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⚙️ **Process API Flow:** `ProcessService` now fetches `ProcessInstanceDTO` including its configuration when submitting forms, ensuring the correct process config is used for new walkthroughs.
- 💬 **Workflow Event Handling:** `DispatchableWorkflow.get_steps_waiting_for_event` now accepts `WorkEvent` types, increasing flexibility in workflow step triggering.
- ⚙️ **Dispatcher Robustness:** Enhanced `BaseDispatcher.stop` method for more robust shutdown handling.
- 📈 **JetStream Event Logging:** Added more detailed debug logging to `JetStreamEventStore` for received and deserialized messages, improving observability.
- 📝 **JSSubscriber Clarity:** Improved clarity in `JSSubscriber` by explicitly passing `subject` and `queue` arguments to `js.subscribe`.
- 🧪 **Simulated Process Runner:** Updated `SimulatedProcessApiTestRunner` to handle `WorkEvent` types for simulating process execution and to include `process_config` in `ProcessStartEvent`.
- ⚙️ **Process Runner Initialization:** `ProcessRunner` now accepts a `default_process_config` and operates more explicitly at the process class level for discovery and delegator initialization.
- ⚙️ **Process Dispatcher Logic:** `ProcessDispatcher` now utilizes `WalkthroughContext` for state management, injects dynamic process configurations into steps, and ensures proper cleanup on process stop.
- 📊 **Dagster Configuration:** Updated `dagster.yaml` to explicitly define `run_storage`, `event_log_storage`, and `schedule_storage`, and increased `max_concurrent_runs` for improved performance.
- 🐳 **Dagster Docker Paths:** Adjusted `DAGSTER_HOME` and entrypoint paths in Dagster Dockerfiles for consistency.
- 🧪 **Test Cache Cleanup Automation:** Added `cleanup_db_and_cache` fixtures to various API and process test files for automatic database and cache clearing.
- 🌐 **API and Process DTOs:** Agent and Process controllers and services now utilize the newly introduced NATS topic models and DTOs for improved clarity and consistency in API communication.

### Fixed
- 🐛 **JetStream Message Handling:** Improved error logging in `JetStreamEventStore`'s message handler for better debugging.
- 🔑 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services (`keys.key1` instead of `keys.primary_key`), ensuring robust and consistent authentication.

### Removed
- 🗑️ **Deprecated Test File:** Removed `aihub_agent/playground/testing/tests/test_agent_config_start_event.py`, as its functionality is now covered by more integrated tests.
- 🗑️ **Generic Discovery Event:** Removed `DiscoveryRequestEvent` as a general NATS event, replaced by more specific class and instance discovery events.
- 🗑️ **Old Process Discovery Event:** Removed `ProcessDiscoveryResponseEvent` in favor of more granular `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent`.
- 🗑️ **Deprecated Process Topic:** Removed the generic `ProcessTopic` in favor of more specific and hierarchical topic models.
- 🗑️ **Agent Event Subscriber:** Removed the `for_agent_instance_events` method from `AgentJSSubscriber`, streamlining agent event subscription.
- 🗑️ **Azure AI Search Vector Store Support:** Discontinued `aisearch_vector_store_resource` and `mongo_aisearch_storage_context_resources` from the pipeline factory, streamlining vector store integrations.
- 🗑️ **Data Lake File Creation Method:** Removed the `from_uri` method from `DataLakeFile`, centralizing URI-based file creation within specific `DataLakeClient` implementations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `BaseContext`, `NatsConfig`, and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 🔄 **NATS Topic Model Overhaul:** Performed a comprehensive refactoring of NATS topic models for both agents and processes, introducing a hierarchical structure (`AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) and updating their usage across all relevant services.
- 🧹 **API Service Refinements:** Refactored `AgentService` and `ProcessService` discovery methods by making internal helpers private (e.g., `_discover_agent_class`) and creating public methods that return the new, granular DTOs.
- ⚙️ **Cloud-Agnostic File Access:** Rearchitected `FileController` and `FileService` to leverage the new `AbstractAnonymousFileAccessService` abstraction, enabling multi-cloud storage support.
- 🏗️ **API Process DTO Hierarchy:** Restructured API Process DTOs into a more organized hierarchy (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`) for better data representation.
- 📝 **API Endpoint Naming Consistency:** Renamed internal API endpoint creation methods to use `_create_endpoint` for improved naming consistency.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Process Delegator Scoping:** Refactored `ProcessDelegator` and `AgentDelegator` to operate at the process class level initially, simplifying their initialization and logic.
- 🧹 **Process Dispatcher Internal Logic:** Major refactoring of `ProcessDispatcher` to integrate `WalkthroughContext`, manage dynamic configuration injection, and align with the new topic hierarchy.
- 📦 **Data Lake Client Abstraction:** Migrated `DataLakeIOManager` and related pipeline operations (`fetch_all_files_in_data_lake`, `delete_figures_for_many_ref_doc`, `fetch_data_lake_files_to_remove`) to use the new `AbstractDataLakeClient` abstraction.
- 🏷️ **Azure Data Lake Resource Renaming:** Renamed Azure Data Lake-specific resources (e.g., `DataLakeClientResource` to `AzureDataLakeClientResource`) and introduced a `base` package for abstract data lake clients and resources.
- 🗄️ **Process Configuration Persistence:** Rearchitected process configuration persistence in `ProcessEntity` to utilize new `ProcessConfigEntityDocument` and `ProcessConfigEntityEmbeddedDocument` for better data management.
- ⚙️ **Process Configuration Model:** Added `process_class` to `ProcessConfig` and included a `from_entity` method for consistent object creation from persistence entities.

---



## [v0.226.0] - 2025-07-25 - Focused Core Alignment and Data Ecosystem Streamlining

### Added
- ✨ **Consolidated Process Topic**: Introduced a new `ProcessTopic` model to unify and simplify the representation of process-related event topics, improving message routing clarity.
- ✨ **Generalized Discovery Request Event**: Added `DiscoveryRequestEvent` as a universal base class for all discovery-related queries, promoting consistency across system discovery mechanisms.
- ✨ **Streamlined `DataLakeFile` Instantiation**: Implemented a static `from_uri` method on `DataLakeFile` for direct creation from URIs using the `FileSystemClient`, simplifying file object construction.
- ✨ **Agent Configuration Precedence Tests**: Included `test_agent_config_start_event.py` to thoroughly validate the priority and application of `AgentConfig` provided via `StartEvent`.
- ✨ **Azure AI Search Vector Store Support**: Re-integrated `AzureAISearchVectorStoreResource` and its factory functions, enabling pipelines to utilize Azure AI Search as a vector store backend.

### Changed
- ⚡️ **Refined Process Dispatcher Event Publishing**: The `ProcessDispatcher` now strictly enforces that only `WorkRequestEvent`, `ProcessExceptionEvent`, or `ProcessStopEvent` types can be published, ensuring a more predictable event flow.
- ⚙️ **Dagster Concurrency Adjustment**: Reduced the maximum concurrent runs in Dagster's `QueuedRunCoordinator` from 10 to 3, potentially optimizing resource allocation and stability for pipeline executions.
- ⚙️ **Simplified Process Discovery Response**: Updated the `ProcessDiscoveryResponseEvent` schema to directly include `process_id` and `process_config`, removing older, less direct fields like `process_config_specs` and `default_process_config`.
- ⚙️ **Direct Data Lake Client Usage in Pipelines**: Modified pipeline operations and resources to directly utilize the `azure.storage.filedatalake.FileSystemClient`, removing an intermediate abstraction layer and simplifying data lake interactions.
- ⚙️ **Default Document Parser in Pipelines**: Changed the default `loader_type` for the `document_parser` in `default_rag_pipeline` from `DOCUMENT_INTELLIGENCE` to `DOCLING`.
- ⚙️ **Namespace Naming Convention**: Updated `NAMESPACE_NAME` and `STORE_NAME` in the default RAG pipeline to use generic "test" values instead of deriving from data lake container/directory names, promoting cleaner separation.
- 🌐 **Frontend Image URL Resolution**: Adjusted the `ResolveImageComponent.vue` to handle image URLs more directly, reflecting the streamlined file access strategy.
- ⚙️ **Agent Dispatcher Initialization**: The `AgentDispatcher` now initializes with `PartialAgentTopic` for its base class, aligning with the new consolidated agent topic structure.

### Removed
- 🗑️ **Multi-Cloud Data Lake Abstraction**: Removed the generic `AbstractDataLakeClient` and `AbstractDataLakeFileSystemResource` interfaces, along with their S3/MinIO-specific implementations (`S3DataLakeIOManager`, `S3DataLakeClient`, `S3DataLakeFileSystemResource`), streamlining the data lake strategy to focus on Azure Data Lake Storage.
- 🗑️ **Generic File Access Service**: Discontinued the multi-cloud `FileAccessServiceConfig` and its related `AbstractAnonymousFileAccessService`, `S3AnonymousFileAccessService` components, standardizing file URL generation on Azure Blob Storage.
- 🗑️ **Legacy Process Configuration Management**: Eliminated the independent `ProcessConfigEntity` system, including `ProcessConfigEntityDocument` and `ProcessConfigEntityEmbeddedDocument`, simplifying how process configurations are stored and managed.
- 🗑️ **Old Process Topic Models**: Removed `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic`, replaced by a single, consolidated `ProcessTopic`.
- 🗑️ **Deprecated Process Discovery Topics**: Discontinued `ProcessClassDiscoveryTopic` and `ProcessInstanceDiscoveryTopic` for a unified `ProcessDiscoveryTopic`.
- 🗑️ **Redundant Process Topic Managers**: Removed `ProcessClassTopicManager` and streamlined other process topic managers.
- 🗑️ **Python S3 Dependencies**: Removed `boto3` and `s3fs` libraries, reflecting the shift away from S3/MinIO storage support.
- 🗑️ **Agent Config Deletion Utility**: Removed `AgentConfigEntityDocument.delete_if_exists_for_class_and_id`.
- 🗑️ **Deprecated Test Cases**: Cleaned up various outdated or superseded test cases, including a chat completions test with custom agent config and specific process service database tests.

### Refactor
- 🧹 **Internal Context Relocation**: Moved `BaseContext` from the general `aihub_lib` to the more specific `aihub_agent` module, improving package cohesion.
- 🔄 **Unified Agent Topic Handling**: Streamlined agent topic management by consolidating `AgentClassTopic` and `AgentInstanceTopic` into flexible `AgentTopic` and `PartialAgentTopic` models across agent dispatchers and NATS interactions.
- 🧹 **Infrastructure Configuration Import Consolidation**: Standardized import paths for `NatsConfig` and `RedisConfig` across services and playground examples.
- 🧹 **Internal Service Method Renaming**: Standardized naming for various internal service methods (e.g., `_discover_agent_class` to `discover_agent_class`, `_send_event` to `send_event`) within `AgentService` and `ProcessService` for improved consistency.
- 🧹 **Agent Runner Cleanup**: Removed explicit `_background_tasks` sets from agent dispatchers and runners, as task management is now handled more implicitly by `asyncio.Task`.
- 🧹 **Simplified `ProcessConfig` Structure**: Removed the `process_class` field from `ProcessConfig`, along with its `from_entity` and `update_from_process_config` methods, promoting a more focused data model.
- 🧹 **Consolidated NATS Process Topics**: Replaced a hierarchy of `Process` NATS topic models with a single, unified `ProcessTopic`, simplifying topic construction and parsing.
- 🧹 **Streamlined Process Configuration Persistence**: `ProcessEntity` now directly embeds `ProcessConfig` instead of using a reference to a separate document, simplifying the persistence model.
- 🧹 **Simplified `ProcessDispatcher` Initialization**: The `ProcessDispatcher` no longer requires a `default_process_config` parameter, as process configuration handling has been refined to be more dynamic.
- 🧹 **Decoupled Process Runner Initialization**: `ProcessRunner` now accepts `process_config` directly instead of `default_process_config`, aligning with the streamlined process configuration approach.
- 🧹 **Dagster Storage Configuration Unification**: Unified Dagster's storage configuration in `dagster.yaml` by using a single `storage.postgres` block instead of separate entries for run, event, and schedule storage.
- 🧹 **Python Project Version Alignment**: Explicitly set project versions in `pyproject.toml` files to `v0.226.0` for various modules, aligning dependencies and ensuring consistency.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🧪 **Enhanced Process Dispatcher Testing:** Added comprehensive unit and integration tests for `ProcessDispatcher`, covering configuration handling, event triggering, and error scenarios.
- 🗄️ **Database Persistence for Process Configurations:** Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) for robustly storing and managing process configurations.
- ✨ **Process Walkthrough Context:** Added `WalkthroughContext` for managing per-walkthrough state within agentic processes.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- ⚙️ **Refined Process Configuration Loading:** The `ProcessDispatcher` now dynamically loads and injects process configurations, prioritizing those from `ProcessStartEvent` or falling back to defaults.
- 💡 **Streamlined NATS Topic Hierarchy:** Overhauled NATS topics and their managers across agents and processes, introducing clearer `Class`, `Instance`, and `Partial` distinctions (e.g., `AgentTopic` -> `AgentInstanceTopic`, `ProcessTopic` -> `ProcessInstanceTopic`).
- 📚 **Process Entity Configuration Model:** `ProcessEntity` now uses reference fields for process configurations and supports a dedicated `default_process_config`.
- 🚀 **Dagster Infrastructure Updates:** Updated Dagster's Dockerfile paths, `dagster.yaml` for Postgres storage and run concurrency, and adjusted the default pipeline playground to use S3/MinIO.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⚙️ **Dispatcher Shutdown Logic:** Improved `BaseDispatcher` to ensure proper shutdown of event stores during a stop operation.
- 📦 **Process Event Inheritance:** `ProcessExceptionEvent` and `ProcessStopEvent` now directly inherit from `WorkEvent`, streamlining the process event hierarchy.

### Fixed
- 🔄 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Deprecated Discovery Events:** Removed generic `DiscoveryRequestEvent` and older `ProcessDiscoveryResponseEvent`, replaced by more granular class- and instance-specific discovery events.
- 🗑️ **Obsolete File Access Service:** Removed the monolithic `AnonymousFileAccessService` in favor of the new, more modular and cloud-agnostic file access abstraction.
- 🗑️ **Redundant Process Topic:** Removed the old `ProcessTopic` class, superseded by the new hierarchical topic structure.
- 🗑️ **Outdated Agent Configuration Test:** Removed `test_agent_config_start_event.py` as its logic is covered by the refined agent dispatcher tests.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🧹 **Standardized Persistence Entity Naming:** Renamed `from_dto` to `from_specs` in process-related persistence entities (`ProgramInSpecsEntity`, `HumanInSpecsEntity`, `AgentInSpecsEntity`) for consistency.

---



## [bot-v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🚀 **New LLM Wrapping Agent:** Introduced the `LLMWrappingAgent` with its dedicated Dockerfile, configuration, and main entry point, providing a flexible interface for LLM integrations.
- ✨ **Enhanced Process Configuration Persistence:** Added new persistence entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) for storing process configurations in MongoDB.
- 📄 **Structured Process Discovery DTOs:** Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` for clearer, hierarchical representation of process information.
- 🔗 **Hierarchical NATS Process Topics:** Implemented new NATS topic models (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) to support a more granular and flexible topic hierarchy for processes.
- 🛠️ **Process Class Topic Manager:** Added `ProcessClassTopicManager` to streamline NATS subject management for process classes.
- 🚀 **Automated Build & Release Workflows:** New GitHub Actions workflows (`build-agents.yml`, `build-dagster.yml`, `build-pipelines.yml`) automate Docker image builds and releases for agents, Dagster, and pipelines, supporting multiple trigger types.
- ⚙️ **Dagster Configuration for Postgres:** Added `dagster.yaml` for PostgreSQL-backed run, event log, and schedule storage in Dagster.
- 🧪 **Comprehensive Process Testing:** Introduced extensive unit and integration tests for `ProcessService` and `ProcessDispatcher`, improving test coverage and reliability for process configuration and management.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⚙️ **Docker Compose Enhancements:** MinIO environment variables updated, Postgres now includes `dagster` database, and crucial services (Postgres, NATS, Redis, Mongo) no longer expose their ports externally, enhancing security. Dagster services are now integrated into the `docker-compose.latest.yml`.
- 📊 **NATS Logging & Persistence:** Increased NATS `debug`, `trace`, and `trace_verbose` logging levels and configured JetStream to use persistent storage at `/data/nats/js-store`.
- 💡 **API Log Level:** Increased `aihub_api` service's default logging level to `DEBUG` in `docker-compose.latest.yml` for more verbose output.
- 🚀 **Agent Service API Refinements:** Agent discovery and event sending in `aihub_api` updated to use new internal helpers and return `AgentDTO` directly, streamlining API interactions.
- ⚙️ **Process Management Overhaul:** `ProcessService` and `ProcessController` in `aihub_api` underwent significant changes, adopting new DTOs and distinguishing between class-level and instance-level process discovery and management, including passing `process_config` for start forms.
- 🚦 **Event Structure & Handling:** `StartEvent` and `ProcessStartEvent` now include `from_raw_data` methods for easier construction. `ProcessStopEvent` and `ProcessExceptionEvent` now derive from `WorkEvent`, with the `process_id` field moved to `WorkRequestEvent` for improved consistency.
- 🔗 **NATS Topic & Subscriber Alignment:** Extensive changes across NATS subscribers and topic managers to align with the new hierarchical topic structure for both agents and processes.
- 🏃 **Process Runner & Dispatcher Setup:** `ProcessRunner` now uses `default_process_config` and `ProcessClassTopicManager`, with delegators and the dispatcher deriving instance-specific details at runtime.
- ⚙️ **Process Configuration Schema:** `ProcessConfig` now includes a `process_class` field.
- 🗄️ **Process Entity Persistence Model:** `ProcessEntity` now uses reference fields to `ProcessConfigEntityDocument` and embedded fields for `ProcessConfigEntityEmbeddedDocument` for a more flexible persistence model.
- 🧪 **Test Suite Enhancements:** Added `cleanup_db_and_cache` fixtures for agent and process API tests to ensure clean database states.
- 🚀 **StartEvent Utility:** `StartEvent` now includes a `from_raw_data` class method for easier construction.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Legacy Discovery Events:** Removed `DiscoveryRequestEvent` and `ProcessTopic` files, as their functionalities are superseded by new, hierarchical discovery and topic models.
- 🗑️ **Redundant Agent JSSubscriber:** Removed `AgentJSSubscriber.for_agent_instance_events` as its functionality is now covered by other, more specific subscription methods.
- 🗑️ **Obsolete Agent Test File:** Cleaned up `aihub_agent/playground/testing/tests/test_agent_config_start_event.py`, as its test logic is now integrated or obsolete.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🧹 **Docker Image Optimization:** Removed `ca-certificates` from the `aihub_api` Dockerfile for a slightly leaner runtime image.
- 🔄 **Topic Naming Standardization:** Consistent renaming of NATS topics, topic managers, and subscribers (e.g., `AgentTopic` to `AgentInstanceTopic`, `ProcessTopic` to `ProcessInstanceTopic`) to clearly differentiate between class-level and instance-level topics.
- 🪵 **Enhanced Logging:** Added more detailed debug logging in the NATS dispatcher and JetStream event store for improved observability.
- ⚙️ **Azure Key Access Alignment:** Updated `DocumentIntelligenceAccess` to use `keys.key1` instead of `keys.primary_key` for retrieving primary keys.
- 🧹 **Internal API Naming Conventions:** Renamed internal methods in `AgentEndpointsDiscoveryService` and `ProcessEndpointsDiscoveryService` (e.g., `create_endpoint` to `_create_endpoint`) for better clarity.
- 🧹 **Pydantic Configuration Best Practices:** Added `model_config` to `ProcessConfig` for Pydantic V2 compatibility and improved consistency.

---



## [v0.226.0] - 2025-07-24 - Next-Gen Agents: Dynamic Configuration, Granular Discovery, and Rich Document Rendering

### Added
- ✨ **Dynamic Agent Configuration:** Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Granular Agent Discovery:** Implemented distinct discovery mechanisms for agent *classes* and specific agent *instances*, enabling systems to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Persistent Agent Configurations:** Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups across deployments.
- 📄 **Structured Document Rendering:** Implemented the dynamic rendering of hierarchical document headings (H1-H6) and content wrapped in semantic tags (`<content>`, `<summary>`) directly within the RAG context, significantly improving readability and structural clarity.
- 🔌 **Standardized Vector Store Configurations:** Introduced dedicated Pydantic configuration models (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`) for vector stores, allowing direct embedding and validation of retrieval settings within agent configurations.
- 🧪 **Expanded Testing Infrastructure:** Added comprehensive unit and integration tests for `AgentDispatcher`, agent configuration precedence, and `AgentService` database integration, enhancing system robustness.
- 🦾 **New Pipeline Job Utility:** Introduced `materialize_asset_job` to simplify the creation of jobs for materializing specific selections of assets within pipelines.
- 🐳 **Comprehensive Docker Compose Setup:** A new `docker-compose.latest.yml` now provides a complete, integrated setup for all core AI Hub services, including authentication and the web UI, for streamlined local and production deployments.

### Changed
- ⚙️ **Refined Agent Configuration Loading:** The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 💡 **Improved Type Specificity for LLM/Embedding Models:** Agent configurations now utilize more precise type unions for LLMs and embedding models (e.g., `AzureOpenAILLMConfig | GeminiLLMConfig | OpenaiLikeLLMConfig`), enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration:** RAG and Retrieval agents now leverage the `.to_llama_index()` method directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- 🌐 **Updated API Agent Discovery:** The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- ⚙️ **Updated Default Document Language:** The default language for newly ingested nodes has been updated from English to German, better aligning with regional configurations.
- ⚡️ **Pipeline Automation Strategy:** Document and data lake file removal assets (`removed_documents_factory`, `removed_data_lake_files_factory`) now transition from eager conditions to more explicit job-driven scheduling.
- 💻 **Web UI SDK Updates:** The generated API SDK has been updated to reflect changes in `AgentConfigDTO` (removal of fields, addition to events) and fix a typo in `ProcessDTO` description.
- 📜 **Agent Documentation Alignment:** Agent examples in the documentation have been revised to reflect the updated `AgentConfig` and `default_agent_config` usage.

### Fixed
- 🐛 **Robust Figure Deletion:** Improved the data lake figure deletion process in pipelines to gracefully handle cases where associated figure directories do not exist, preventing unnecessary errors.
- 💬 **SDK Description Typo:** Corrected a minor typo in the `ProcessDTO` description within the generated SDK schema, improving clarity.
- ℹ️ **Azure Profile Image Fetching:** Enhanced error handling for fetching Azure user profile images to specifically log non-404 errors, making debugging more effective.

### Removed
- 🗑️ **Deprecated Agent Configuration Fields:** The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration and allowing for more flexible, agent-specific customization in subclasses.
- 🗑️ **Legacy Discovery Event Types:** Old class- and instance-specific discovery events and topic managers have been removed, unifying agent discovery under a single, simplified model.
- 🗑️ **Direct Agent Config Persistence Script:** The `save_config.py` example script has been removed, as the new dynamic configuration and database persistence mechanisms are now integrated into the core framework.
- 🗑️ **Dedicated Locale String Persistence Entity:** `LocaleStringEntity` has been removed, implying localized string persistence is now handled more directly within other models or through generic data structures.
- 🗑️ **Unused Timestamp Formatting Utility:** An internal utility for formatting Unix timestamps has been removed from RAG context generation, as date and time handling is now managed by the underlying system.

### Refactor
- 🧹 **Agent Orchestration Overhaul:** Performed a major refactor of `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management across all dispatchers and subscribers.
- 🔄 **Unified Agent Persistence Layer:** Re-architected agent configuration persistence using new base `AgentConfigEntity` and specialized `AgentConfigEntityDocument`/`AgentConfigEntityEmbeddedDocument`, enabling a clear separation of default and overridden configurations stored in the database.
- 📦 **Consolidated API DTOs:** Restructured agent-related Data Transfer Objects (DTOs) in the API, introducing `AgentClassDTO` and `AgentInstanceDTO` to clearly separate the concept of an agent's definition from its configured, runnable instances.
- 📁 **Centralized Model Creation Service:** Renamed `EventModelCreationService` to `ModelCreationService` and expanded its scope to include creating models for agent configurations, centralizing schema-based model generation.
- 🔗 **Streamlined Topic Management:** Overhauled NATS topic management for agents, introducing a hierarchical structure with `AgentClassTopicManager` and `AgentInstanceTopicManager` to align with the new class/instance discovery paradigm.
- 💻 **Standardized Project Structure:** Renamed `aihub_web/.playground` to `aihub_web/.app` for clearer project organization and moved shared testing utilities from `aihub_api` to `aihub_agent`.
- ⚙️ **Optimized Build Processes:** Streamlined Dockerfiles and Makefiles for API and Bot services, improving build efficiency and consistency.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🐳 **Full Deployable Stack with Docker Compose**: Introduced a comprehensive `docker-compose.latest.yml` providing a complete local development and production-ready environment including MinIO, Milvus, Postgres, OpenWebUI, Nats, Redis, Mongo, API, and a Traefik reverse proxy.
- 🗄️ **Database Setup Utilities and Configurations**: Added scripts for initializing multiple PostgreSQL databases and new configuration files for Milvus and NATS.
- ✨ **Custom Environment Variable Configuration for API**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 🖥️ **Web Docker Image for Production**: A new multi-stage Dockerfile for the web application with Nginx serving static files and runtime configuration injection via `envsubst`, enabling robust production deployments.
- 🧑‍💻 **Local Web Development Docker Compose**: Added `swiss-aihub.local.docker-compose.yml` for simplified local development of the web frontend.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- ⚙️ **RAG Context Prompt Role Update**: The `chat` role for RAG context prompts has been adjusted from `system` to `user` across all supported languages (German, English, French, Italian) for improved model interaction.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🌐 **Web UI Configuration Loading**: Updated the Nuxt.js web application to load runtime configuration from environment variables during development and from a `config.json` file in production, enabling more flexible deployment.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Image URL Handling in RAG Prompts**: Corrected an issue where image URLs were not consistently processed in English RAG prompts, ensuring images are properly referenced.
- ⚠️ **Minor CSS in Markdown Renderer**: Removed a trailing semicolon in CSS that could cause linting issues.
- 📝 **Typo in Process Topic Manager Docstring**: Corrected a typo from "all processs" to "all processes".

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure within the API project.
- ♻️ **SharePoint Integration Naming Consistency**: Standardized naming conventions for all SharePoint-related assets, operations, and I/O managers, enhancing readability and maintainability across the data pipeline.
- 🐳 **Docker Image Optimization**: Streamlined Dockerfiles for `aihub_api` and `aihub_bot` by removing unnecessary virtual environment copying and simplifying `poetry install` steps.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.
- 🗂️ **Frontend Project Structure**: Restructured the Nuxt.js application from a `.playground` directory to a more standard `.app` directory, simplifying development and deployment workflows.
- 🛠️ **Agent Runner Event Responsibility**: Refactored the `send_event` method from the generic `AgentRunner` to `AgentTestRunner`, centralizing event injection logic specifically for testing scenarios.

### Removed
- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Old Generic Event Distributor Dependency**: Removed the `use_external_event_distributor.py` file, as its functionality has been replaced by more specific agent and process event distributors.
- 🗑️ **Old Docker Compose File**: Removed `docker-compose-mnt.yml`, which has been superseded by new and more comprehensive Docker Compose configurations.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage & Dynamic Process Orchestration

### Added
- 🚀 **Automated Docker Image Build & Release Workflows:** Introduced new GitHub Actions workflows (`build-agents.yml`, `build-dagster.yml`, `build-pipelines.yml`) to automate the Docker image build and release process for agents, Dagster, and pipelines upon new tags, manual dispatch, or specific feature branch pushes.
- ✨ **Introduced `LLMWrappingAgent`:** A new agent designed to wrap and interact with Large Language Models, including its dedicated Dockerfile, configurable settings (`LLMWrappingAgentSettings`), and main application entry point.
- ⚙️ **Configurable LLM Wrapping Agent Settings:** Introduced `LLMWrappingAgentSettings` to manage LLM-related configurations such as API URL, key, and model name, enhancing agent flexibility.
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** (`AzureAnonymousFileAccessService`) and **S3/MinIO** (`S3AnonymousFileAccessService`), enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- ⚙️ **S3 Configuration Settings:** Introduced `S3Config` to centralize and manage connection parameters for S3-compatible storage services, including MinIO and AWS S3.
- 🛠️ **S3/MinIO Data Lake IO Manager:** Implemented `S3DataLakeIOManager` for Dagster pipelines, providing robust loading and storage of files from S3-compatible storage with metadata awareness.
- 🏗️ **Abstract Data Lake Client Interface:** Introduced `AbstractDataLakeClient` to define a cloud-agnostic interface for interacting with various data lake services (Azure, S3, MinIO), ensuring consistent file operations.
- 🏗️ **Abstract Data Lake Client Resource:** Introduced `AbstractDataLakeClientResource` as a base class for Dagster data lake client resources, providing a unified interface for different cloud providers.
- 🏗️ **Abstract Data Lake File System Resource:** Introduced `AbstractDataLakeFileSystemResource` as a base class for Dagster data lake file system resources, enabling a common interface for cloud file systems.
- 🏗️ **Azure Data Lake Client Implementation:** Introduced `AzureDataLakeClient` as a concrete implementation of `AbstractDataLakeClient`, providing Azure-specific methods for file operations and metadata retrieval.
- 🏗️ **S3 Data Lake Client Implementation:** Introduced `S3DataLakeClient` as a concrete implementation of `AbstractDataLakeClient`, providing S3-specific methods for file operations and metadata retrieval using `boto3`.
- 🛠️ **S3 Data Lake Client Resource:** Added `S3DataLakeClientResource` to provide a `boto3` S3 client as a Dagster resource, enabling granular control over S3 storage operations within pipelines.
- 🛠️ **S3 Data Lake File System Resource:** Introduced `S3DataLakeFileSystemResource` to provide an `s3fs` file system as a Dagster resource, allowing pipelines to interact with S3-compatible storage as a local file system.
- ⚙️ **S3 Data Lake Resource Factories:** Introduced `s3_data_lake_resources` and `default_io_manager_s3_datalake_resources` factory functions to simplify configuration of S3-compatible data lake resources for Dagster pipelines.
- 🚀 **New Dagster Pipeline Dockerfile:** Introduced a dedicated Dockerfile for `aihub_pipeline`, enabling its containerization for Dagster deployments and streamlining the build process.
- 🚀 **New Default RAG Pipeline Dockerfile:** Introduced a dedicated Dockerfile for the `default_rag_pipeline`, enabling its containerization for independent deployment.
- 🤖 **New Default RAG Pipeline Definition:** Introduced the `default_rag_pipeline` application, defining its Dagster assets, jobs, resources, and schedules for automated RAG processes.
- ⚙️ **S3/MinIO Integration in Default Pipeline:** Configured the `default_rag_pipeline` to use S3/MinIO for data lake resources and `DOCUMENT_INTELLIGENCE` for document parsing.
- ⚙️ **New Process Walkthrough Context:** Introduced `WalkthroughContext` to manage state and configuration specific to individual process walkthroughs, improving process state management.
- 🏗️ **New Process Class Topic Manager:** Introduced `ProcessClassTopicManager` to manage NATS subjects at the process class level, enabling broader subscriptions and broadcasts for all instances of a given process type.
- 🏗️ **New Agent Class Topic:** Introduced `AgentClassTopic` to represent NATS event topics at the agent class level, enabling event routing and subscription for all instances of a given agent type.
- 📦 **New Process Instance Discovery Response Event:** Introduced `ProcessInstanceDiscoveryResponseEvent` to provide specific details about individual process instances, including their unique ID and configuration.
- 📄 **New Process Configuration Specifications:** Introduced `ProcessConfigSpecs` to define the schema and parameters of process configurations, enabling external consumers to understand and validate process settings.
- 🏗️ **New Process Class Discovery Topic:** Introduced `ProcessClassDiscoveryTopic` to represent NATS subjects for discovering process class information, enabling broader discovery requests.
- 🏗️ **New Partial Process Topic:** Introduced `PartialProcessTopic` to represent partially defined NATS event topics for processes, accommodating subscriptions with wildcards.
- 🏗️ **New Process Class Topic:** Introduced `ProcessClassTopic` to represent NATS event topics at the process class level, enabling event routing for all instances of a given process type.
- 🏗️ **New Process Instance Topic:** Introduced `ProcessInstanceTopic` to represent fully defined NATS event topics for specific process instances, inheriting from `ProcessClassTopic`.
- 🗄️ **New Process Configuration Entity Base Class:** Introduced `ProcessConfigEntity` as a foundational class for storing process configurations, promoting reusability across different persistence strategies.
- 🗄️ **New Process Configuration Document:** Added `ProcessConfigEntityDocument` for persisting process configurations as a standalone MongoDB collection, supporting discoverable and customizable process instances.
- 🗄️ **New Embedded Process Configuration Document:** Introduced `ProcessConfigEntityEmbeddedDocument` for embedding process configurations within other documents (e.g., `ProcessEntity`), useful for default configurations.
- 🗄️ **New Agent Configuration Deletion Method:** Added `delete_if_exists_for_class_and_id` to `AgentConfigEntityDocument`, enabling more precise cleanup of agent configurations from the database.
- 🧪 **New Process Configuration Database Tests:** Added comprehensive tests for `ProcessConfig` database operations, ensuring correct persistence, retrieval, and override logic for process configurations.
- 🧪 **New Process Service Database Integration Tests:** Implemented integration tests for `ProcessService` focusing on how process instances and classes interact with database-persisted configurations and caching.
- 🧪 **New Process Service Unit Tests:** Added detailed unit tests for `ProcessService`, covering process discovery, event handling, and cache management.
- 🧪 **New Process Dispatcher Tests:** Added comprehensive unit and integration tests for `ProcessDispatcher`, verifying its handling of process configurations, lifecycle events, and step execution.
- ⚙️ **Dagster PostgreSQL Storage Configuration:** Introduced `dagster.yaml` to configure Dagster to use PostgreSQL for run, event log, and schedule storage, enhancing data persistence for pipelines.

### Changed
- 🛠️ **Improved Local Docker Development Setup:** Added new IDE run configurations for building individual Docker images for pipelines (Dagster, `default_rag_pipeline`) and agents (`llm_wrapping_agent`), streamlining local development workflows.
- 🌐 **Simplified Agent Discovery API:** The agent discovery endpoint (`AgentController`) now directly returns `AgentDTO` objects, streamlining API responses by removing a redundant conversion step.
- 🚀 **Enhanced Agent Start Event Handling:** Introduced `send_agent_start_event` in `AgentService` to streamline the process of initiating agent runs with specific configurations and user context.
- 🌐 **Refined Agent Discovery Logic:** Improved the internal agent discovery flow in `AgentService` by reorganizing methods and adjusting caching, leading to more precise and performant agent retrieval.
- ☁️ **Cloud-Agnostic File URL Generation:** Updated `FileController` to use the new `FileAccessServiceConfig` for generating signed file URLs, enabling multi-cloud storage support.
- ☁️ **Unified File Access Service Integration:** Migrated `FileService` to leverage the new `FileAccessServiceConfig` for all temporary file URL generation and signature handling, supporting diverse storage backends.
- ⚙️ **Process Configuration during Start:** Modified `ProcessController` to explicitly discover and pass the `process_config` to the `submit_process_start_form` endpoint, ensuring correct process initialization.
- 🔄 **Enhanced Process Discovery and Configuration Management:** Overhauled `ProcessService` to introduce distinct `ProcessClassDTO` and `ProcessInstanceDTO` for more granular process discovery, alongside improved caching strategies and configuration loading from the database.
- 🚀 **Streamlined Process Start Event Creation:** Updated `submit_process_start_form` in `ProcessService` to utilize `ProcessStartEvent.from_raw_data`, simplifying event object creation.
- ⚙️ **Cloud-Agnostic Azure Data Lake IO Manager:** Updated `AzureDataLakeIOManager` to use the new `AzureDataLakeClient` interface, abstracting away direct Azure SDK calls and aligning with multi-cloud strategy.
- 🚀 **Cloud-Agnostic Data Lake File Fetching:** Migrated `fetch_all_files_in_data_lake` to use the `AbstractDataLakeClient` interface, making the operation cloud-agnostic and more maintainable.
- 🚀 **Cloud-Agnostic Figure Deletion:** Updated `delete_figures_for_many_ref_doc` to use the `AbstractDataLakeClient` interface, ensuring cloud-agnostic deletion of figures from the data lake.
- 🚀 **Cloud-Agnostic File Removal Logic:** Migrated `fetch_data_lake_files_to_remove` to utilize the `AbstractDataLakeClient`, enabling cloud-agnostic determination of files no longer present in SharePoint.
- ⚙️ **Unified Data Lake Resource Configuration:** Updated resource factories to use the new `AzureDataLakeClientResource` and `AzureDataLakeFileSystemResource` names, ensuring consistent naming across the pipeline.
- ⚙️ **Process Runner Configuration Refinement:** Updated `ProcessRunner` to accept `default_process_config`, enabling a base configuration while allowing dynamic overrides.
- 🚀 **Streamlined Process Discovery:** Enhanced `ProcessRunner` to use `ProcessClassDiscoveryResponseEvent` and `ProcessConfigSpecs`, providing more detailed process class information during discovery.
- ⚙️ **Streamlined Delegator Initialization:** Refactored delegator instantiation within `ProcessRunner` by removing redundant `process_id` arguments and updating queue group naming.
- ⚙️ **Process Test Runner Configuration Update:** Modified `ProcessTestRunner` to use `default_process_config` and explicitly set `ProcessInstanceTopicManager`, aligning with new process configuration patterns.
- 🧪 **Enhanced Process Test Observation:** Updated test runner to observe both `ProcessClassDiscoveryRequestEvent` and `ProcessClassDiscoveryResponseEvent`, providing more granular insights into process discovery during testing.
- ⚙️ **Playground Process Configuration Update:** Updated all playground process examples to use `default_process_config` and explicitly include `process_class` in `ProcessConfig`, aligning with new configuration requirements.
- ⚙️ **Pipeline Playground Migration to S3/MinIO:** Updated the pipeline playground to default to S3/MinIO data lake resources and `DOCUMENT_INTELLIGENCE` for document parsing, showcasing multi-cloud capabilities.
- 💬 **Configurable Cloud Provider Comment:** Added a comment to the pipeline playground configuration, guiding users on how to switch between cloud providers.
- ⬆️ **Updated Pipeline Dependencies:** Upgraded Dagster and Dagster-postgres versions, and added `s3fs` and `boto3` to support S3-compatible data lake integrations.
- ⚙️ **Enhanced Entity Delegator Flexibility:** Updated `AbstractEntityDelegator` to use `ProcessClassTopicManager` and `ProcessClassTopic`, improving flexibility in process type handling and enabling internal `_publish_work_event` calls.
- ⚙️ **Streamlined Agent Delegator Event Publishing:** Refactored `AgentDelegator` to use the new `_publish_work_event` helper, centralizing work event publishing logic.
- ⚙️ **Dynamic Process ID in Agent Delegation:** Updated agent delegator to use the `process_id` from the incoming event when creating threads, ensuring dynamic and accurate process associations.
- ⚙️ **Streamlined Process Delegator Event Publishing:** Refactored `ProcessDelegator` to use the new `_publish_work_event` helper, centralizing work event publishing logic.
- ⚙️ **Dynamic Process Configuration Loading:** Implemented dynamic loading of `ProcessConfig` in `ProcessDispatcher`, prioritizing configurations from `ProcessStartEvent` or `WalkthroughContext`.
- 🚀 **New Process Lifecycle Management:** Enhanced `ProcessDispatcher` to manage process lifecycle events (`ProcessStopEvent`, `ProcessExceptionEvent`) by cleaning up `WalkthroughContext` and stores.
- ⚙️ **Flexible Step Argument Injection:** Introduced `_build_method_kwargs` to enable dynamic injection of `ProcessConfig` objects into process steps based on their type hints.
- 💬 **Dual Event Publishing for Processes:** Updated `ProcessDispatcher` to publish both `WorkRequestEvent` and generic `WorkEvent` types, accommodating diverse event patterns within processes.
- ⚙️ **New Process Class Field in Configuration:** Added `process_class` to `ProcessConfig` for clearer identification of the process type.
- ⚙️ **Enhanced ProcessConfig Flexibility:** Introduced `model_config` with `extra="allow"` and added a `from_entity` class method to `ProcessConfig`, enabling more robust deserialization and extensibility.
- ⚙️ **Broadened Workflow Event Handling:** Expanded `DispatchableWorkflow` to allow `process_steps` to respond to both `ControlEvent` and `WorkEvent` types, increasing workflow flexibility.
- 🗄️ **Enhanced Process Entity Configuration:** Reworked `ProcessEntity` to support both referenced (`process_config`) and embedded (`default_process_config`) process configurations, enabling flexible override mechanisms and database persistence for discoverable processes.
- ⚙️ **Explicit JetStream Subscription Arguments:** Updated `JSSubscriber` to explicitly pass `subject`, `stream`, and `queue` to `js.subscribe`, improving clarity and robustness.
- 💬 **Enhanced NATS Debugging and Persistence:** Enabled detailed debugging and tracing in NATS configuration and set up persistent storage for JetStream data, improving operational visibility and data durability.
- 🐳 **Comprehensive Docker Compose Stack Update:** Significantly updated `docker-compose.latest.yml` to:
    - Use a newer MinIO image and updated environment variable names for authentication.
    - Integrate MinIO with Traefik for external access.
    - Include Dagster services (`dagster-webserver`, `dagster-daemon`) and PostgreSQL database for Dagster.
    - Add `oauth2proxy` for Dagster authentication.
    - Set `api` service log level to `DEBUG` for more verbose logging.
    - Corrected NATS endpoint format for `api` service.
- 🖼️ **Enhanced Image Resolution for Multi-Cloud:** Updated `combine_nodes_in_order` and `ResolveImageComponent` (frontend) to correctly parse and resolve image URLs from both Azure and S3/MinIO storage, ensuring proper display of embedded images.

### Fixed
- 🧪 **Improved Agent Test Isolation:** Introduced `cleanup_db_and_cache` fixtures in `aihub_api` agent tests to ensure isolated execution by clearing database and in-memory caches.
- 🧪 **Expanded OpenAI Assistant Tests:** Added new test cases for OpenAI assistant interactions to verify custom agent configurations are correctly loaded and applied from the database.
- 🧪 **Improved Process Test Isolation:** Introduced a `cleanup_db_and_cache` fixture in `aihub_api` process tests to ensure isolated execution by clearing database and in-memory caches.

### Removed
- 🗑️ **Obsolete Agent Configuration Test:** Removed `test_agent_config_start_event.py`, as its functionality is now covered by more integrated tests.
- 🗑️ **Azure AI Search Vector Store Deprecation:** Removed `aisearch_vector_store_resource` and `mongo_aisearch_storage_context_resources` from `aihub_pipeline`, discontinuing support for Azure AI Search as a vector store.
- 🗑️ **Removed Generic Discovery Request Event:** Eliminated `DiscoveryRequestEvent` from `aihub_lib`, which is now superseded by more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent`.
- 🗑️ **Removed Redundant Agent Instance Event Subscriber:** Eliminated `for_agent_instance_events` from `AgentJSSubscriber`, as its functionality is covered by other, more specific control event subscriptions.
- 🗑️ **Removed Old Process Topic:** Eliminated the old `ProcessTopic` from `aihub_lib` as it has been replaced by the more granular `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic`.

### Security
- 🔒 **Internalized Core Services in Docker Compose:** Removed external port mappings for NATS, Redis, and MongoDB in `docker-compose.latest.yml`, enhancing security by limiting direct external access to these internal components.

### Refactor
- 🧹 **Improved Local Docker Development Setup:** Updated SDK name in `.idea/misc.xml` for `aihub_agent` for consistency.
- 🧹 **Consolidated Base Context:** Moved the core `BaseContext` class from `aihub_agent` to `aihub_lib` for better reusability across agent and process modules.
- 🔄 **Refined Agent Topic Hierarchy:** Updated `AgentDispatcher`, `AgentTestRunner`, `RunTraceCoordinator`, `AgentJSSubscriber`, `AgentNCSubscriber`, `AgentThreadTopicManager`, `AgentInTheLoopRequestEvent`, `BotInTheLoopRequestEvent`, `HumanInTheLoopRequestEvent`, `WebSocketManager`, `WebSocketSender`, and NATS `topics` exports to align with the new, more granular `AgentClassTopic` and `AgentInstanceTopic` structure.
- 🧹 **Minor Docker Image Optimization:** Removed `ca-certificates` from the `aihub_api` Dockerfile for a slightly leaner runtime image.
- 🔄 **Refined Topic Type Usage in Event Persistence:** Updated `EventPersister` in `aihub_api` to use `AgentInstanceTopic` and `ProcessInstanceTopic`, aligning with the new granular topic structure.
- 🧹 **Standardized Cache Management:** Renamed internal caches and introduced `_clear_cache` methods across agent and process services (`AgentService`, `ProcessService`) for consistency in cache invalidation.
- 🧹 **Internal Method Renaming:** Renamed `send_event` to `_send_event` and `discovery_handler` to `_discovery_handler` in various services (`AgentService`, `ProcessService`, `AgentEndpointsDiscoveryService`, `ProcessEndpointsDiscoveryService`) to signify their internal helper nature.
- 🏗️ **Introduced Minimal Process DTO:** Added `MinimalProcessDTO` for lightweight process information transfer, improving API response efficiency.
- 🏗️ **New Process Class DTO:** Introduced `ProcessClassDTO` to represent process class definitions, including configuration specifications and input types, for clearer API communication.
- 🏗️ **Refined Process DTO Hierarchy:** Restructured `ProcessDTO` to inherit from `MinimalProcessDTO` and added `from_instance` and updated `from_entity` methods, improving data model consistency.
- 🏗️ **New Process Instance DTO:** Introduced `ProcessInstanceDTO` to represent specific process instances, including their unique ID and configuration, enhancing the granularity of process data.
- 🔄 **Encapsulated Process Instance Logic:** Added methods to `ProcessInstanceDTO` for converting to discovery events and managing persistence (`create_or_update_process_entity`), centralizing data model responsibilities.
- 🧹 **Circular Dependency Resolution:** Moved `ProcessService` import within `UserWithAccessDTO` to resolve a circular dependency, improving module load order.
- 🔄 **Refined Process Topic Hierarchy:** Updated process test runner, process subscriber, and process topic managers (`ProcessTopicManager`, `ProcessInstanceTopicManager`, `ProcessWalkthroughTopicManager`) to align with new topic hierarchy (`ProcessClassDiscoveryTopic`, `ProcessInstanceTopic`).
- ⚙️ **Refined Agent Subscriber Naming:** Renamed `for_agent_instance_events` to `for_agent_instance_control_events` in `AgentJSSubscriber` for clearer intent on which event types are handled.
- 🔄 **Streamlined Process Exception Event:** Changed `ProcessExceptionEvent` to inherit directly from `WorkEvent`, simplifying its hierarchy and aligning with general event patterns.
- 🔄 **Streamlined Process Stop Event:** Changed `ProcessStopEvent` to inherit directly from `WorkEvent` and removed the redundant `process_id` field, as it's now handled by the topic context.
- ⚙️ **Centralized DataLakeFile Creation:** Moved the URI-based `from_uri` creation method for `DataLakeFile` into specific cloud data lake client implementations (`AzureDataLakeClient`, `S3DataLakeClient`), improving encapsulation.
- 🔄 **Refined Azure Data Lake Client Resource:** Renamed `DataLakeClientResource` to `AzureDataLakeClientResource` and updated its inheritance to `AbstractDataLakeClientResource`, aligning with the new multi-cloud data lake architecture.
- 🔄 **Refined Azure Data Lake File System Resource:** Renamed `DataLakeFileSystemResource` to `AzureDataLakeFileSystemResource` and updated its inheritance to `AbstractDataLakeFileSystemResource`, aligning with the new multi-cloud data lake architecture.
- 🔄 **Refined Event Persistence Topic Types:** Updated `PersistedAgentEventEntity` and `PersistedProcessEventEntity` to use `AgentInstanceTopic` and `ProcessInstanceTopic` respectively, ensuring data consistency with the new topic models.
- ⚙️ **Streamlined Process Entity Management:** Refactored `ProcessEntity` to use new `create_or_update` methods and standardized `from_specs` conversions, improving data handling and consistency.
- 💬 **Improved Logging:** Added `logging` import to `AbstractEntityDelegator` for better internal debugging.
- 🔄 **Refined Agent Delegator Topic Handling:** Updated agent delegator to align with `AgentInstanceTopic` and `ProcessClassTopic`, improving type safety and topic consistency.
- 🔄 **Refined Process Delegator Topic Handling:** Updated process delegator to align with `ProcessInstanceTopic` and `ProcessClassTopic`, improving type safety and topic consistency.
- 🔄 **Refined Process Dispatcher Topic Handling:** Updated `ProcessDispatcher` to align with the new `ProcessClassTopic`, `ProcessInstanceTopic`, and `ProcessWalkthroughTopicManager` for improved topic management and event routing.
- 🔄 **Refined Process Runner Topic Management:** Updated `ProcessRunner` to align with `ProcessClassTopicManager` and `ProcessClassDiscoveryTopic`, improving topic handling and event subscriptions.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings for better readability.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 📦 **New Docker Compose Setups**: Introduced new comprehensive `docker-compose.latest.yml` and other environment-specific compose files (`docker-compose.dev.yml`, `docker-compose-gpu.*.yml`, `swiss-aihub.local.docker-compose.yml`) along with supporting configs (`milvus.yaml`, `nats.conf`, `init-multiple-dbs.sh`) for a complete local deployment stack, enhancing ease of setup and development.
- 🐳 **Web UI Dockerfile**: Added a dedicated `Dockerfile` for the web user interface, streamlining its build and deployment process.
- ⚙️ **Web UI Nginx Configuration**: Included a `nginx.conf` and `config.template.json` for the web UI, enabling robust serving of static assets and dynamic environment variable injection in production.
- 🗂️ **New `.dockerignore` for Web UI**: Added a `.dockerignore` file to optimize Docker builds for the web UI by excluding unnecessary files.
- ✨ **API Configuration Extensibility**: Enabled custom environment variable configuration for API services, allowing users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📦 **Docker Build Process Optimization**: Optimized Dockerfiles for API and Bot services by removing redundant `poetry install` steps and virtual environment copying, leading to faster and more efficient image builds.
- ⚙️ **Agent Runner `send_event` Relocation**: The `send_event` method was moved from `AgentRunner` to `AgentTestRunner`, centralizing testing-specific event sending logic.
- 🔌 **Internal Naming Consistency**: Standardized internal variable and parameter names, such as renaming `external_event_distributor` to `external_agent_event_distributor` across various services and handlers for improved clarity.
- 📈 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🎨 **Frontend Markdown Rendering**: Corrected CSS styling for `h3` through `h6` headings in the Markdown renderer, ensuring consistent and visually appealing content display.
- 🌐 **Frontend i18n for ExceptionEvent**: Added a missing `label` for `ExceptionEvent` in the Italian localization, improving clarity in error messages for Italian users.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🧹 **Old Docker Compose Mount File**: The `docker-compose-mnt.yml` file, likely an older or temporary setup, has been removed.
- ✂️ **Redundant Frontend Health Page**: A basic placeholder health page in the frontend was removed.
- 🗑️ **Deprecated External Event Distributor**: The `use_external_event_distributor.py` file and its related dependencies were removed, replaced by more specific external agent and process event distributors.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🔄 **Frontend Application Structure**: Migrated the Nuxt.js application from the `.playground` directory to a new `.app` directory, standardizing the project structure for clearer development and deployment.
- 🔄 **Optimized Error Message for SPA Routes**: Improved the error message returned when a static file request unexpectedly hits an API route in the Single Page Application (SPA) runner.
- 🧹 **Cleaned Up SharePoint Utilities**: Standardized naming within metadata utility functions related to SharePoint files, contributing to a more coherent codebase.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🚀 **Pipeline Build & Release Workflows:** New GitHub Actions workflows now automate Docker image builds and releases for **agents**, **pipelines**, and the new **LLM Wrapping Agent**, streamlining CI/CD.
- 📦 **Dagster Deployment Stack:** Added a comprehensive Dagster stack to `docker-compose.latest.yml`, including `dagster-webserver`, `dagster-daemon`, and `oauth2proxy` for a complete local pipeline orchestration environment.
- 🗄️ **Persistent Dagster Metadata:** Introduced `configs/dagster/dagster.yaml` to configure **Postgres-backed storage** for Dagster run, event, and schedule metadata, ensuring data durability and history.
- 📂 **Process Configuration Persistence:** Implemented new persistence entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to allow **process configurations** to be saved and retrieved from the database.
- ✨ **New LLM Wrapping Agent:** Introduced the `LLMWrappingAgent` including its **Dockerfile**, **configuration settings**, and application entry point, providing a flexible interface for LLM integrations.
- 🧪 **New Test Fixtures:** Added `cleanup_db_and_cache` fixtures for agent and process services to **improve test isolation** and ensure clean state in integration and unit tests.
- 📝 **Process Dispatcher Tests:** Comprehensive new test suites for `ProcessDispatcher` covering **event handling**, **configuration precedence**, **context cleanup**, and **error handling**.
- 💡 **IDE Docker Run Configurations:** Added new `.idea/runConfigurations` XML files to simplify **Docker image building directly from IDE** for agents and pipelines.
- 📈 **Process Configuration Tests:** New test files for **process configuration database operations** and **process service database integration** to ensure robust persistence and retrieval of process settings.
- 📝 **Process Service Unit Tests:** New **unit tests for `ProcessService`** methods, including discovery, event sending, and cache management.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced **multi-cloud file access services** for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from **both Azure and S3/MinIO storage**.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new **abstract data lake client**, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted pipeline playground examples to showcase the new **S3/MinIO data lake capabilities** and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- 🛡️ **Internalized Docker Compose Ports:** NATS, Redis, and Postgres services in `docker-compose.latest.yml` no longer expose their ports externally, **enhancing security** by limiting external access to internal components.
- 📝 **Increased API Logging Verbosity:** The `aihub_api` service's `LOG_LEVEL` in `docker-compose.latest.yml` has been set to `DEBUG`, providing more **verbose output** for development and troubleshooting.
- ⚙️ **NATS Persistent Storage & Logging:** Configured NATS to use a **persistent store directory** for JetStream data (`/data/nats/js-store`) and enabled **verbose debug/trace logging** in `nats.conf`, improving operational visibility and data durability.
- 📦 **MinIO Environment Variables:** Updated `minio` service in `docker-compose.latest.yml` to use `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`, aligning with **newer MinIO image configurations**.
- 🌐 **Process Controller Submission:** Process start form submissions in the API now dynamically retrieve and pass the **process configuration from the discovered process instance**, ensuring consistency.
- 📊 **Workflow Event Dispatching:** `DispatchableWorkflow` now dispatches based on a broader range of `WorkEvent` types, **increasing flexibility** in defining process steps.
- ⚙️ **Process Runner Configuration:** `ProcessRunner` now accepts `default_process_config` and dynamically handles **process configuration loading**, distinguishing between class and instance-specific settings.
- 💬 **NATS Subscriber Debugging:** Added detailed **debug logging** to `JetStreamEventStore` for incoming messages and deserialized events, and improved exception logging, enhancing observability.
- 🏷️ **Process ID in Work Events:** The `process_id` field has been moved from `ProcessStopEvent` to the more general `WorkRequestEvent`, improving **event data consistency** for process tracking.
- 🚀 **Dagster Version Update:** Upgraded Dagster to version 1.11.2, bringing **latest features and improvements** to the pipeline orchestration framework.

### Fixed
- 🐞 **Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services to `keys.key1`, ensuring **robust and consistent authentication**.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages (`aihub_lib/infrastructure/nats` and `aihub_lib/infrastructure/redis`) for **clearer logical grouping** and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed **redundant parameter descriptions** from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into **cloud-specific data lake client implementations** for better encapsulation and maintainability.
- 🔄 **NATS Topic Model Evolution:** Significant refactoring of NATS topic hierarchy for **agents** and **processes**, introducing `AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`, and `PartialProcessTopic` for more granular and consistent messaging.
- 🧹 **Unified Base Context:** Moved the common `BaseContext` class from `aihub_agent` to `aihub_lib` for **centralized management** and reusability across services.
- 🏗️ **Agent and Process Dispatcher Overhaul:** Major refactoring of `AgentDispatcher` and `ProcessDispatcher` to align with the new NATS topic hierarchy, improve **parameter injection**, and streamline event handling logic.
- 📦 **Agent & Process Service Cleanup:** Streamlined internal methods in `AgentService` and `ProcessService` by adding `_` prefix to denote **private helper methods** and cleaning up redundant caching calls in tests.
- 🛠️ **Process Entity Persistence:** Updated `ProcessEntity` to use `ProcessConfigEntityDocument` for referenced configurations and `ProcessConfigEntityEmbeddedDocument` for default configurations, enhancing **process config persistence**.
- 💡 **Process Runner Initialization:** Refined `ProcessRunner` initialization to better leverage the new **process class/instance topic managers** and pass explicit default configurations.
- 🧹 **Docker Image Optimization:** Removed `ca-certificates` from `aihub_api` Dockerfile for a slightly **leaner runtime image**.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for **Azure AI Search** as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Obsolete NATS Events & Topics:** Removed generic `DiscoveryRequestEvent` and the old `ProcessTopic` as they have been **superseded by new, more granular event and topic models**.
- 🗑️ **Deprecated Test Files:** Cleaned up outdated test files related to **agent config start event handling** that are now covered by more integrated tests.

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

### Changed
- 📈 **Refined Agent and Process API Discovery**: Updated the API discovery mechanisms in `AgentController` and `AgentService` to simplify agent listing, and revamped process discovery in `ProcessService` to provide more detailed and cache-aware retrieval of process instances and classes.
- 📄 **Event Deserialization Flexibility**: Modified `DispatchableWorkflow` to allow its `get_steps_waiting_for_event` method to accept `WorkEvent` types, broadening the dispatcher's capability to react to various process-related events.
- 🗄️ **Improved Event Persistence Logic**: Updated `PersistedAgentEventEntity` and `PersistedProcessEventEntity` to correctly utilize the new `AgentInstanceTopic` and `ProcessInstanceTopic` respectively, ensuring accurate data storage with the refined topic structure.
- 🧩 **Extended `WorkRequestEvent` with `process_id`**: Added a `process_id` field to `WorkRequestEvent` to enhance clarity and provide a direct association with the relevant process instance.
- ✍️ **Enhanced Logging for Subscribers**: Improved logging for `JSSubscriber` to provide more detailed information during subscription lifecycle events (start and stop).

### Refactor
- 🔄 **NATS Topic Hierarchy Refinement**: Restructured NATS topics for Agents and Processes to introduce clear distinctions between class-level and instance-level communication. This included renaming existing topics (e.g., `AgentTopic` to `AgentInstanceTopic`, `ProcessTopic` to `ProcessInstanceTopic`) and introducing new ones (`AgentClassTopic`, `ProcessClassTopic`, `PartialProcessTopic`). Related `TopicManager` and `Subscriber` classes were updated to align with this new hierarchy.
- 🧹 **Streamlined Process Discovery Events**: Consolidated and refined process discovery events, replacing a monolithic `ProcessDiscoveryResponseEvent` with `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent` for more granular information exchange during discovery.
- ⚡️ **Improved Dispatcher `stop` Method**: Enhanced `BaseDispatcher`'s `stop` method to ensure more robust cleanup of event stores upon dispatcher termination, improving resource management.
- ⚙️ **Centralized Process Configuration Handling**: Modified `ProcessDispatcher` to robustly manage process configurations by prioritizing explicit configurations provided in `ProcessStartEvent` and gracefully falling back to default process configurations, leveraging the new `WalkthroughContext`.
- 🏗️ **Core Context Relocation**: Relocated the foundational `BaseContext` class from `aihub_agent` to `aihub_lib`, promoting its reusability across all core service modules.
- 🗑️ **Delegator Topic Manager Alignment**: Refactored Agent and Process delegators to align their topic management with the new `ProcessClassTopicManager` and `ProcessInstanceTopicManager`, improving consistency and maintainability.

### Removed
- 🗑️ **Deprecated Generic Discovery Events**: Eliminated the generic `DiscoveryRequestEvent` and the monolithic `ProcessTopic` class. These have been superseded by more specific and granular event and topic types, improving type safety and clarity in discovery and messaging workflows.
- 🧹 **Redundant Agent Config Start Event Test**: Removed a test file (`test_agent_config_start_event.py`) as its functionality is now fully covered by updated and more comprehensive dispatcher tests.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- ⚙️ **S3 Configuration:** Added `S3Config` to centralize environment-based configuration for S3-compatible storage services.
- ✨ **Event Construction Utilities:** Implemented new `from_raw_data` class methods for `StartEvent` and `ProcessStartEvent`, simplifying event creation from raw data with injected context.
- ✨ **Enhanced Process Discovery Events:** Introduced `ProcessConfigSpecs`, `ProcessInstanceDiscoveryResponseEvent`, and `ProcessClassDiscoveryResponseEvent` to provide more granular and structured information during process discovery.
- ✨ **Detailed Process DTOs:** Added new Data Transfer Objects (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`) to represent process information with enhanced clarity and detail in API responses.
- ✨ **Agent Config Deletion Utility:** Implemented `delete_if_exists_for_class_and_id` in `AgentConfigEntityDocument` for more controlled cleanup of agent configurations in the database.
- ✨ **Process Configuration Persistence:** Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to enable persistent storage and retrieval of process configurations.
- ✨ **Process Config Conversion:** Added a `from_entity` class method to `ProcessConfig`, facilitating seamless conversion from database entities.
- ✨ **Dagster Deployment Tools:** Introduced new Dockerfiles for Dagster and default RAG pipelines, along with a comprehensive `dagster.yaml` for production-ready Dagster deployments via PostgreSQL.
- ✨ **Process Walkthrough Context:** Implemented `WalkthroughContext` to manage transient, per-walkthrough state within agentic processes using Redis.
- ✨ **New Process Topic Managers & Topics:** Added `ProcessClassTopicManager` and new NATS topic classes (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) for a more hierarchical and granular process messaging structure.
- ✨ **New Agent Topic Class:** Introduced `AgentClassTopic` to represent agent definitions at a class level within NATS messaging.
- 🧪 **Comprehensive Test Coverage:** Added extensive unit and integration tests for `ProcessDispatcher`, `ProcessService`, and related database operations, significantly improving testing robustness for agentic processes.
- 🧪 **Test Utilities:** Introduced new fixtures (`cleanup_db_and_cache`) to streamline database and cache cleanup in API tests, ensuring isolated test environments.
- 📦 **Dagster Services in Docker Compose:** Integrated `oauth2proxy`, `dagster-webserver`, and `dagster-daemon` as new services in `docker-compose.latest.yml` for a complete local Dagster stack.

### Changed
- ⚙️ **CI/CD Workflows:** Updated GitHub Actions to use new dedicated workflows for building and releasing Dagster and pipeline Docker images.
- ⚙️ **Agent Dispatcher Logic:** Refined agent dispatcher to dynamically inject `process_config` into steps, and adapted to the new NATS topic hierarchy for `AgentClassTopic` and `AgentInstanceTopic`.
- ⚙️ **Runner Initialization:** Updated `AgentRunner`, `ProcessRunner`, and `ProcessTestRunner` to accept `default_process_config` and utilize the new topic hierarchy for improved clarity and flexibility.
- ⚙️ **LLM Wrapping Agent Deployment:** Minor improvements to the LLM Wrapping Agent's Dockerfile entrypoint and `main.py` runner initialization for better containerization.
- ⚙️ **API Agent Discovery:** `AgentController` and `AgentService` now use `discover_agents` which directly returns `AgentDTO` instances, reflecting richer discovered data.
- ☁️ **Unified File Access in API:** `FileController` and `FileService` now leverage the new multi-cloud `FileAccessServiceConfig` for generating secure, temporary file URLs, abstracting storage backend details.
- ⚙️ **Process Form Submission:** `ProcessController` and `ProcessService` now pass `process_config` to `submit_process_start_form`, ensuring process-specific configurations are respected.
- ⚙️ **Dispatcher Shutdown:** Improved the `stop()` method in `BaseDispatcher` for more robust shutdown sequences, including explicit event store stopping.
- ⚡️ **Enhanced Event Logging:** Increased verbosity and clarity of logging in `JetStreamEventStore` for better debugging of NATS message handling.
- ⚙️ **Process Event Fields:** `ProcessStartEvent` now includes an optional `process_config` field, and `WorkRequestEvent` re-includes the `process_id` field for better data propagation.
- ⚙️ **JSSubscriber Robustness:** Improved `JSSubscriber` with explicit keyword arguments for subscriptions and added debug logs for lifecycle events.
- ⚙️ **Flexible Workflow Step Inputs:** `DispatchableWorkflow.get_steps_waiting_for_event` now correctly identifies and accepts `WorkEvent` types as valid triggers for workflow steps.
- ⚙️ **ProcessConfig Enhancements:** Added a `process_class` field to `ProcessConfig` for better identification and updated the Pydantic model configuration for improved compatibility and flexibility.
- ⚙️ **Cloud-Agnostic Data Lake I/O:** `AzureDataLakeIOManager` was updated to use the new `AzureDataLakeClient` interface for unified file operations, and `DataLakeFile.from_uri` creation logic was centralized into data lake clients.
- ⚙️ **Cloud-Agnostic Pipeline Operations:** Core pipeline operations (`fetch_all_files_in_data_lake`, `delete_figures_for_many_ref_doc`, `fetch_data_lake_files_to_remove`) now utilize the `AbstractDataLakeClient` interface, enabling seamless switching between Azure and S3/MinIO.
- ⚙️ **Playground Configuration:** `aihub_pipeline/playground/__init__.py` now defaults to S3/MinIO data lake resources and uses `DOCUMENT_INTELLIGENCE` as the default document parser.
- ⬆️ **Dependency Updates:** Upgraded `dagster-webserver`, `dagster-postgres`, `dagster-azure`, and added `dagster-aws`, `s3fs`, and `boto3` to `aihub_pipeline/pyproject.toml` for expanded cloud support.
- ⚙️ **Delegator Logic:** `AgentDelegator` and `ProcessDelegator` adjusted to rely on `process_class` for delegation logic and adapted to the new NATS topic hierarchy.
- ⚙️ **Process Dispatcher Orchestration:** `ProcessDispatcher` significantly updated to leverage `WalkthroughContext` for state management, dynamically inject `process_config`, and convert topics to `ProcessInstanceTopic` for execution.
- 🖼️ **Frontend Image Resolution:** The `ResolveImageComponent.vue` now correctly handles `s3://` prefixed URLs for image display, ensuring compatibility with S3-based storage.
- ⬆️ **Docker Compose Infrastructure:** Updated MinIO image and its environment variables, configured PostgreSQL to support Dagster, and internalized NATS/Redis ports within `docker-compose.latest.yml` for enhanced security.

### Fixed
- 🔄 **Azure Document Intelligence Key Access:** Aligned the retrieval of primary keys from Azure Document Intelligence services to `keys.key1`, ensuring robust authentication.

### Removed
- 🗑️ **Outdated Test File:** Deleted `aihub_agent/playground/testing/tests/test_agent_config_start_event.py`, as its functionality is now covered by more integrated tests.
- 🗑️ **Deprecated Discovery Event:** Removed `DiscoveryRequestEvent` from `aihub_lib`, replaced by more specific class- and instance-level discovery requests.
- 🗑️ **Redundant Agent Subscriber Method:** Eliminated `for_agent_instance_events` from `AgentJSSubscriber`, streamlining agent event subscription.
- 🗑️ **Legacy Process Topic:** Removed the old `ProcessTopic` class, superseded by the new hierarchical process topic model.
- 🗑️ **Azure AI Search Integration:** Discontinued support for Azure AI Search as a vector store by removing its associated resources and factory functions (`aisearch_vector_store_resource`, `mongo_aisearch_storage_context_resources`).

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `BaseContext`, `NatsConfig`, and `RedisConfig` into dedicated `infrastructure` subpackages within `aihub_lib` for clearer logical grouping.
- 🔄 **Unified NATS Topic Hierarchy:** Overhauled agent and process NATS topics, transitioning from generic `AgentTopic` and `ProcessTopic` to granular `AgentInstanceTopic` and `ProcessInstanceTopic`, and introducing `*ClassTopic` concepts for improved messaging structure.
- 🧹 **Consolidated API DTOs:** Streamlined the API's process-related DTOs into a more consistent hierarchy (`MinimalProcessDTO`, `ProcessClassDTO`, `ProcessInstanceDTO`).
- ⚙️ **Centralized DataLakeFile Creation:** Refactored `DataLakeFile` instantiation by moving URI-based creation logic into cloud-specific `DataLakeClient` implementations for better encapsulation and maintainability.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- 🧹 **Internal API Method Naming:** Renamed several internal API service methods (e.g., `_discover_agent_class`, `_send_event`, `_clear_cache`) for improved consistency and clarity.
- 🔄 **Streamlined Subscriber Methods:** Renamed and reorganized various NATS subscriber methods (e.g., `for_process_instance_work_events` to `for_process_class_work_events`) to align with the new topic hierarchy.
- 🧹 **Pipeline Project Structure:** Reorganized `aihub_pipeline/app` and `aihub_pipeline/resources/data_lake` into more logical subpackages (`azure`, `s3`, `base`) for enhanced modularity.
- 🔄 **Process Persistence Rearchitecture:** Refactored process configuration persistence in `aihub_lib/persistence/process` to use a more robust reference model (`ProcessConfigEntityDocument`) and embedded defaults (`ProcessConfigEntityEmbeddedDocument`).
- 🧹 **Unified Type Hinting:** Updated numerous type hints across `aihub_agent`, `aihub_api`, `aihub_bot`, and `aihub_process` to reflect the new topic and configuration models, improving type safety.
- ⚙️ **Process Dispatcher Event Emission:** Adjusted the process dispatcher's `publish_event` method to explicitly emit events based on specific event types (work request or work events) for clearer control flow.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🐳 **Dagster Orchestration Stack:** Integrated the **Dagster webserver and daemon** into `docker-compose.latest.yml`, allowing for robust pipeline orchestration directly within the unified deployment.
- 🗄️ **Process Configuration Persistence:** Implemented new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to allow **process configurations to be saved and retrieved**, supporting persistent and shareable process setups.
- 🧪 **Comprehensive Test Coverage:** Added **extensive unit and integration tests** for `ProcessDispatcher`, `ProcessService`, and `ProcessConfig` database operations, ensuring the reliability of new process management features.
- 🧩 **Hierarchical NATS Topics for Agents and Processes:** Introduced a **new hierarchy of NATS topic models** (`AgentClassTopic`, `AgentInstanceTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`, `PartialProcessTopic`) and corresponding topic managers, enabling more granular event routing and discovery.
- ✨ **Process Walkthrough Context:** Added a dedicated `WalkthroughContext` for managing **per-walkthrough state and configuration** in process execution, improving state isolation and management.
- 🚀 **New Process Event Fields:** Enhanced `ProcessStartEvent` to explicitly include `process_config` and `WorkRequestEvent` to include `process_id`, improving clarity and data flow in process events.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating **secure, temporary file URLs**.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display **images from both Azure and S3/MinIO storage**.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new **abstract data lake client**, improving flexibility and maintainability.
- ⚙️ **Process Dispatcher Logic Refinement:** The `ProcessDispatcher` now dynamically resolves **process configurations** from `ProcessStartEvent` or `WalkthroughContext`, and integrates with the new topic hierarchy for more robust event handling.
- 🧑‍💻 **Delegator Operations at Class Level:** Agent and Process delegators now primarily operate at the **process class level**, supporting dynamic process instance resolution and utilizing a new `_publish_work_event` utility for consistent event publishing.
- ⬆️ **Dagster Dependency Updates:** Upgraded **Dagster and related dependencies** (e.g., `dagster-webserver`, `dagster-postgres`, `dagster-azure`), and added `dagster-aws` to support comprehensive S3/MinIO integrations.
- 🌐 **Internal Port Exposure for Core Services:** **NATS, Redis, and Postgres services** in `docker-compose.latest.yml` no longer expose their ports externally, enhancing security by limiting external access to internal components within the Docker network.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- 📊 **Dagster Concurrency Increase:** Increased `max_concurrent_runs` in Dagster from 3 to 10 in `configs/dagster/dagster.yaml`, allowing for higher parallel execution of pipelines.
- 📝 **Improved Debug Logging for NATS:** Enhanced logging for `JetStreamEventStore` and `JSSubscriber` to provide **more detailed debug information** on received messages and subscription lifecycles.

### Fixed
- 🐛 **Process Thread Entity Creation:** Corrected `AgentDelegator` to correctly pass the `process_id` when **creating new `ThreadEntity` instances**, ensuring proper association of delegated agents with their originating processes.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for **Azure AI Search** as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🚫 **Generic Discovery Event:** Removed the generic `DiscoveryRequestEvent` in favor of more specific `ClassDiscoveryRequestEvent` and `InstanceDiscoveryRequestEvent`, streamlining discovery patterns.
- 🗑️ **Outdated Process Topic Model:** Eliminated the old `ProcessTopic` model, which has been superseded by the new hierarchical topic structure (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`).
- 🧹 **Redundant Test Files:** Deleted `test_agent_config_start_event.py` from `aihub_agent` playground tests as its logic is now covered by more integrated tests.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into **cloud-specific data lake client implementations** for better encapsulation and maintainability.
- 🔄 **Unified Base Context Location:** Moved `BaseContext` from `aihub_agent` to `aihub_lib`, promoting its reuse as a common utility across modules.
- 🛠️ **Agent & Process Topic Renaming:** Standardized naming of NATS topics and their associated types (e.g., `AgentTopic` to `AgentInstanceTopic`, `ProcessDiscoveryTopic` to `ProcessInstanceDiscoveryTopic`) across `aihub_agent`, `aihub_api`, `aihub_bot`, and `aihub_lib` for improved clarity and consistency.
- 🗄️ **Agent & Process Service Interface Simplification:** Refactored `AgentService` and `ProcessService` in `aihub_api` to use private helper methods (e.g., `_discover_agent_class`, `_send_event`, `_clear_cache`) and return DTOs directly from public discovery methods, simplifying their public interfaces.
- ⚙️ **Event Construction Delegation:** Delegated the construction of `StartEvent` and `ProcessStartEvent` from raw data to their respective class methods, simplifying event generation logic in API services.
- 🔄 **Azure Document Intelligence Key Access:** Updated the method for retrieving primary keys from Azure Document Intelligence services to `keys.key1`, aligning with recent API changes.
- 📦 **Dagster `DAGSTER_HOME` Path:** Optimized the `DAGSTER_HOME` path within Dockerfiles for Dagster pipelines, leading to cleaner container setups.
- 🧹 **API Endpoint Discovery Refinement:** Refactored endpoint creation and registration logic in `AgentEndpointsDiscoveryService` and `ProcessEndpointsDiscoveryService` to use private helper methods (e.g., `_create_endpoint`, `_register_human_endpoint`) for better modularity.
- 🧪 **Enhanced Test Hygiene:** Implemented automated **cache clearing fixtures** for `AgentService` and `ProcessService` in API tests, ensuring isolated and reliable test runs.

---



## [v0.226.0] - 2025-07-25 - Core Platform Streamlining: NATS, Process, and Data Lake Refinements

### Added
- ✨ **Unified Process Topic Model:** Introduced a new `ProcessTopic` model and `DiscoveryRequestEvent` to consolidate all process-related messaging, simplifying topic management and discovery for agentic processes.
- 🔗 **Direct File Access Service:** Implemented `AnonymousFileAccessService` for direct generation of secure, temporary file URLs, streamlining multi-cloud file access logic by removing the previous configurable service.
- 📊 **Azure AI Search Vector Store Resource:** Re-introduced and provided a dedicated `AzureAISearchVectorStoreResource` and its associated IO Manager for pipeline integration.
- 🧪 **Agent Configuration Precedence Test:** Added a new test to validate the precedence logic for agent configurations when provided via a `StartEvent` or loaded from defaults.

### Changed
- 🔄 **Unified Agent and Process Messaging Topics:** Overhauled NATS topic structures, consolidating `AgentClassTopic` and `AgentInstanceTopic` into `AgentTopic`, and similarly for processes (`ProcessTopic`), resulting in a simpler and more consistent messaging architecture.
- ⚙️ **Streamlined Agent and Process Configuration Handling:** Refined how agent and process configurations are managed, simplifying dispatcher logic by removing the separate `WalkthroughContext` and externalizing `StartEvent` construction.
- 🚀 **Simplified Agent and Process Discovery:** Simplified discovery responses (`ProcessDiscoveryResponseEvent` no longer contains detailed `ProcessConfigSpecs` or `default_process_config`) to reflect a unified model where process configuration is directly included within the entity.
- 🗄️ **Embedded Process Configuration:** Process configurations (`ProcessConfig`) are now directly embedded within the `ProcessEntity` in the database, simplifying data relationships and removing the need for separate configuration documents.
- 🛠️ **Refined Data Lake File Management:** Replaced abstract data lake client interfaces and S3/MinIO-specific implementations with direct Azure SDK usage for file operations within pipelines. `DataLakeFile.from_uri` is now a static method, centralizing URI parsing.
- 📦 **Dagster Deployment Configuration:** Simplified Dagster's `dagster.yaml` storage configuration and reduced the default maximum concurrent runs. The `DAGSTER_HOME` path in Dockerfiles has been updated.
- 🐳 **Docker Compose Simplification:** Removed the entire Dagster stack (webserver, daemon, oauth2proxy) from `docker-compose.latest.yml`, streamlining the default local deployment setup. Postgres `dagster` database is no longer initialized.
- 🖼️ **Consolidated Image URL Resolution:** The frontend image component and backend `combine_nodes_in_order` utility now rely solely on `AnonymousFileAccessService` for URL generation, removing S3-specific logic.
- ⚡️ **Optimized Dispatcher Stopping:** Streamlined the dispatcher's stop logic by removing redundant initialization checks.
- 📦 **Python Dependency Alignment:** Dagster and its Postgres/Azure dependencies were downgraded to align with a previous version (`v0.226.0`), and several S3-related Python packages were removed. The default document parser for pipelines was changed from `DOCUMENT_INTELLIGENCE` to `DOCLING`.
- ⚙️ **Process Runner Queue Groups:** Process runner queue groups now include the `process_id` for more specific identification.

### Fixed
- 🐛 **Azure Document Intelligence Key Access:** Corrected the method for retrieving primary keys from Azure Document Intelligence services, ensuring robust authentication.
- 🧹 **Minor Logging Cleanup:** Removed excessive debug logging in `JetStreamEventStore` for cleaner logs.

### Removed
- 🗑️ **S3/MinIO Data Lake Support:** Eliminated all S3/MinIO-specific data lake IO managers and resources from the pipeline, as well as related S3 configuration and client implementations.
- 🗑️ **Deprecated Process/Agent Topic Managers & DTOs:** Removed `ProcessClassTopicManager`, `ProcessConfigSpecs`, `PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`, and `AgentClassTopic` as they are superseded by the unified `ProcessTopic` and `AgentTopic` models.
- 🗑️ **Legacy Process/Agent Persistence Models:** Removed `ProcessConfigEntity`, `ProcessConfigEntityDocument`, and `ProcessConfigEntityEmbeddedDocument`, consolidating `ProcessConfig` directly into `ProcessEntity`.
- 🗑️ **Redundant `WalkthroughContext`:** The Redis-backed `WalkthroughContext` for process dispatchers has been removed, simplifying process state management.
- 🗑️ **Direct Agent/Process Start Event Construction:** Removed `from_raw_data` methods from `StartEvent` and `ProcessStartEvent`, centralizing event construction logic.
- 🗑️ **Obsolete Test Files:** Cleaned up various outdated test files related to process dispatcher, process config, and agent/process service database integrations that are no longer relevant after architectural changes.
- 🗑️ **Direct Agent Config Deletion Utility:** Removed `AgentConfigEntityDocument.delete_if_exists_for_class_and_id`.
- 🗑️ **Abstract File Access Services:** Removed `AbstractAnonymousFileAccessService`, `AzureAnonymousFileAccessService`, `S3AnonymousFileAccessService`, and `FileAccessServiceConfig`, streamlining to a direct `AnonymousFileAccessService` implementation.
- 🗑️ **Abstract Data Lake Clients:** Removed `AbstractDataLakeClient` and its resource/filesystem resource abstractions, simplifying data lake interaction patterns.

### Refactor
- 🧹 **Unified Context and Infrastructure Module Paths:** Consolidated `aihub_lib`'s `context` and `infrastructure` subpackages, streamlining import paths and logical grouping of common utilities.
- ✏️ **Improved Docstrings for IAC Resources:** Added more detailed and helpful docstrings to Azure IAC networking and storage resource factories.
- 🧹 **Centralized `DataLakeFile` Creation:** Moved `create_data_lake_file_from_uri` logic into a static method on `DataLakeFile` itself for better encapsulation.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- ✅ **Dagster Orchestration Integration:** Integrated Dagster's webserver and daemon into the main Docker Compose setup, allowing for centralized orchestration and monitoring of data pipelines alongside other AI Hub services.
- 📄 **Process Configuration Persistence:** Introduced new database entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) for robustly storing and managing custom process configurations in MongoDB.
- ✨ **Process Walkthrough Context:** Added `WalkthroughContext` in `aihub_process` to manage per-walkthrough state, ensuring consistent configuration and data flow for process instances.
- 💡 **NATS Process Class/Instance Topics:** Implemented new NATS topics (`ProcessClassDiscoveryTopic`, `ProcessInstanceDiscoveryResponseEvent`, `PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`) to support granular discovery and messaging for process classes and instances.
- 🔑 **NATS Agent Class Topic:** Introduced `AgentClassTopic` in `aihub_lib` to support class-level discovery and routing for agents.
- 🧪 **New Process Dispatcher Tests:** Added a comprehensive test suite for `ProcessDispatcher` to ensure robust handling of process configurations and event processing.
- 🧪 **New Process Config Database Tests:** Included new tests for process configuration database operations and service-level integration, verifying persistence and retrieval logic.

### Changed
- 🚀 **Multi-Cloud File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs, abstracting away cloud-specific implementations.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- ⚙️ **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability across cloud providers.
- ⬆️ **Dependency Updates:** Upgraded Dagster to `1.11.2` and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- 📦 **Internalized Core Services in Docker Compose:** NATS, Redis, and MongoDB services in `docker-compose.latest.yml` no longer expose their ports externally, enhancing security by limiting external access to these internal components.
- 📝 **Adjusted API and Bot Logging:** The default `LOG_LEVEL` for `aihub_api` and `aihub_bot` services in `docker-compose.latest.yml` has been set to `WARNING`, reducing log verbosity for clearer operational insights.
- 🔄 **Refined NATS Topic Hierarchy:** Agent (`AgentTopic` to `AgentInstanceTopic`) and Process (`ProcessTopic` to `ProcessInstanceTopic`) topics and their respective managers, subscribers, and publishers have been heavily refactored to explicitly distinguish between 'class' and 'instance' levels, improving clarity and modularity.
- ⚙️ **Dynamic Process Configuration Handling:** `ProcessDispatcher` and `ProcessRunner` now dynamically manage process configurations, prioritizing configurations provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the default process configuration.
- 💡 **Centralized StartEvent Creation:** Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent` for standardized event creation from raw data.
- ⚙️ **API Process Discovery:** The API's process discovery (`ProcessService`) now aligns with the new class/instance model, exposing `ProcessInstanceDTO` and `ProcessClassDTO` for more granular information.
- 📦 **Dockerfile Paths:** Adjusted `DAGSTER_HOME` and `ENTRYPOINT` paths in `aihub_pipeline` Dockerfiles for improved consistency and deployment.
- 🧪 **Playground Defaults:** The `aihub_pipeline` playground now defaults to using S3 resources and the `DOCUMENT_INTELLIGENCE` parser, showcasing new multi-cloud capabilities.
- 🗄️ **Process Persistence Schema:** The `ProcessEntity` schema has been updated to use `ProcessConfigEntityDocument` (ReferenceField) for custom configurations and embed `ProcessConfigEntityEmbeddedDocument` for default configurations, enhancing data modeling flexibility.
- ⚡️ **Concurrency in Dagster:** Increased `max_concurrent_runs` in `dagster.yaml` from 3 to 10, allowing for more concurrent pipeline executions.
- 🤖 **Bot Service Logging:** Reduced the default logging level for the bot service to `WARNING` in Docker Compose configurations.

### Fixed
- 🐛 **Azure Document Intelligence Key Access:** Corrected the method for retrieving primary keys from Azure Document Intelligence services to use `keys.key1` instead of `keys.primary_key`, ensuring robust and consistent authentication.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline` by removing its related resources and factory functions.
- 🗑️ **Generic Discovery Event:** The generic `DiscoveryRequestEvent` has been removed from `aihub_lib.nats.events.discovery`, as discovery mechanisms are now more specialized.
- 🗑️ **Legacy Process Topic:** The `ProcessTopic` has been removed from `aihub_lib.nats.topics.process`, superseded by the new hierarchical process topics.
- 🗑️ **Legacy Anonymous File Access Service:** The `AnonymousFileAccessService` has been removed from `aihub_lib.generative_ai.document.accessor`, replaced by the new multi-cloud abstraction.
- 🗑️ **Redundant DataLakeFile Creation Method:** The static `from_uri` method has been removed from `DataLakeFile` as its logic is now encapsulated within specific `AbstractDataLakeClient` implementations.
- 🗑️ **Obsolete Test File:** The `test_agent_config_start_event.py` test file has been removed, as its functionality is now covered by more integrated tests or made obsolete by architectural changes.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** `NatsConfig` and `RedisConfig` have been moved into dedicated `infrastructure` subpackages within `aihub_lib` for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings for better readability.
- ⚙️ **Centralized DataLakeFile Creation:** The logic for creating `DataLakeFile` objects from URIs has been refactored and moved into cloud-specific data lake client implementations, ensuring better encapsulation and maintainability.
- 🔄 **Consolidated NATS Topic Managers:** `ProcessInstanceTopicManager` and `ProcessWalkthroughTopicManager` now inherit from `ProcessClassTopicManager`, streamlining the topic manager hierarchy for processes.
- 📦 **API DTO Hierarchy:** The API's Data Transfer Objects (DTOs) for processes have been reorganized into a clearer hierarchy, with `ProcessDTO` now inheriting from `MinimalProcessDTO`, and new `ProcessClassDTO` and `ProcessInstanceDTO` introduced for explicit representation.
- 🧹 **Test Runner Simplification:** Test runners and their associated imports have been updated to align with the new NATS topic hierarchy and the restructured `infrastructure` modules.

---



## [dagster-v0.226.0] - 2025-07-25 - API & Core Simplification: Streamlined Topics, Unified Discovery & Azure-Only Storage

### Added
- ✨ **Azure AI Search Vector Store Re-integration**: Re-enabled Azure AI Search as a vector store option within the pipeline, including new factory functions for its setup (`aisearch_vector_store_resource`, `mongo_aisearch_storage_context_resources`).
- 🚀 **Agent Instance Event Subscription**: Introduced a new class method `for_agent_instance_events` to `AgentJSSubscriber`, enabling more granular subscriptions to all events within a specific agent instance.

### Changed
- ⬆️ **Dagster Version Rollback**: Downgraded core Dagster, PostgreSQL, and Azure dependencies to align with an earlier version (e.g., `dagster-webserver` from `1.11.2` to `1.9.6`).
- ⚙️ **Dagster Home Path**: Updated the default `DAGSTER_HOME` path in Dockerfiles from `/app/aihub_pipeline` to `/opt/dagster/dagster_home` for improved consistency with Dagster best practices.
- ⚡️ **Process Stop Event Information**: The `ProcessStopEvent` now explicitly includes the `process_id` field for better traceability.
- ⚙️ **Docker Compose Postgres Port Exposure**: The PostgreSQL service in `docker-compose.latest.yml` now explicitly exposes port `5432` to the host.
- ⚙️ **Dagster Postgres Storage Configuration**: Simplified the `dagster.yaml` configuration for PostgreSQL storage, transitioning from explicit `run_storage`, `event_log_storage`, and `schedule_storage` definitions to a consolidated `storage.postgres` entry.
- ⚙️ **Dagster Concurrent Runs Limit**: Reduced the `max_concurrent_runs` for the Dagster queued run coordinator from `10` to `3`.
- ⚙️ **Default Document Parser in Pipeline**: Changed the default document parser from `DOCUMENT_INTELLIGENCE` to `DOCLING` in the default RAG pipeline.
- 🧪 **Playground `ProcessConfig` Instantiation**: Updated playground examples to align with the simplified `ProcessConfig` structure, removing the `process_class` parameter from its instantiation.

### Removed
- 🗑️ **Multi-Cloud Data Lake Support (S3/MinIO)**: Completely removed the multi-cloud data lake abstraction layer, including all S3/MinIO-specific IO managers and client resources for Dagster pipelines, along with related `boto3`, `s3fs`, and `S3Config` dependencies. This change streamlines data lake integration to focus solely on Azure.
- 🗑️ **Process Configuration Persistence Entities**: Eliminated dedicated MongoDB entities and collections (`ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) previously used for process configurations. Process configurations are now directly embedded within the `ProcessEntity` for simplified data management.
- 🗑️ **Deprecated NATS Topic Managers and Topics**: Removed redundant and overlapping NATS topic managers (`ProcessClassTopicManager`, `AgentClassTopic`) and their corresponding topic models (`ProcessClassTopic`, `ProcessInstanceTopic`, `AgentClassTopic`, `PartialProcessTopic`, `ProcessInstanceDiscoveryTopic`). This streamlines event routing and simplifies the topic hierarchy.
- 🗑️ **`WalkthroughContext`**: The Redis-backed `WalkthroughContext` for process walkthrough state management has been removed from `aihub_process`, simplifying process dispatcher state handling.
- 🗑️ **Obsolete `from_raw_data` Event Constructors**: Removed the `from_raw_data` class methods from `StartEvent` and `ProcessStartEvent`, centralizing event construction logic and promoting generic event deserialization.
- 🗑️ **Redundant Test Files**: Cleaned up various obsolete unit and integration test files related to agent and process services and dispatchers.

### Refactor
- 🧹 **Unified NATS Topic Structure**: Consolidated `AgentInstanceTopic` into a single `AgentTopic` and `ProcessInstanceTopic` into a single `ProcessTopic`, providing a comprehensive topic model for event subjects. This includes updated references throughout `aihub_agent`, `aihub_api`, and `aihub_process`.
- 🔄 **Streamlined NATS Discovery Events**: Consolidated various process discovery request and response events (e.g., `ProcessClassDiscoveryResponseEvent`, `ProcessInstanceDiscoveryResponseEvent`) into a single `ProcessDiscoveryResponseEvent` and introduced a generic `DiscoveryRequestEvent`, simplifying the discovery mechanism across services.
- ⚙️ **Simplified Data Lake Client Integration**: Replaced custom data lake client wrappers (`AzureDataLakeClient`, `AbstractDataLakeClient`) with direct usage of the Azure SDK's `FileSystemClient` in Dagster resources and operations. The `DataLakeFile.from_uri` method was also made static for centralized instantiation.
- 🔗 **Refined Process Event Dispatching**: The `ProcessDispatcher` no longer directly manages `WalkthroughContext` and has simplified its event publishing and argument injection logic by removing `_build_method_kwargs` and `_publish_work_event`.
- 📦 **Core Infrastructure Package Restructure**: Relocated `NatsConfig` and `RedisConfig` to the top-level `aihub_lib/infrastructure` package for a cleaner and more centralized configuration structure.
- 🧹 **DTO Consolidation**: Consolidated `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` into a single, comprehensive `ProcessDTO`, streamlining data transfer objects in the API.
- ⚙️ **Process Configuration Simplification**: `ProcessConfig` no longer includes `process_class` and its `from_entity` method has been removed, making it a pure instance-specific configuration.
- 🧹 **Test Runner Organization**: Refactored test runner and playground directory structures for better modularity and clarity.
- 📄 **Docstring Enhancements**: Improved clarity and conciseness in various docstrings across IAC and API components.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 🦾 **Introduced `LLMWrappingAgent`**: A new agent designed to wrap and interact with Large Language Models, providing a flexible interface for LLM integrations. This includes its dedicated Dockerfile, configuration settings, and main application entry point.
- 🚀 **Implemented Agent, Dagster, and Pipeline Build & Release Workflows**: New GitHub Actions workflows automate Docker image builds and releases for agents, Dagster, and pipelines, enabling triggers from new tags, manual dispatch, and specific feature branches.
- 🗄️ **Database Persistence for Process Configurations**: New document and embedded document classes (`ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) allow process configurations to be saved and retrieved from the database, enabling persistent process setups.
- 🧪 **Comprehensive Process Dispatcher Testing**: Added new unit and integration tests for the `ProcessDispatcher`, ensuring robust handling of process configurations, event flow, and context management.
- 📦 **Dagster Configuration**: Introduced a new `dagster.yaml` configuration file to define PostgreSQL-based storage for runs, events, and schedules, streamlining Dagster deployments.
- ⚙️ **S3/MinIO Configuration**: Added a new `S3Config` class for centralizing S3-compatible storage connection parameters, supporting both AWS S3 and MinIO.
- 📋 **Process DTOs**: Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` for clearer representation of process information in API responses and internal data transfer.
- 📚 **Process Configuration Specifications**: Added `ProcessConfigSpecs` to define and expose the schema of process configurations during discovery.
- 🚶 **Process Walkthrough Context**: Introduced `WalkthroughContext` for managing process-specific state and configuration within individual process walkthroughs using Redis.
- 🏷️ **New NATS Topic Managers and Topics**: Implemented `ProcessClassTopicManager`, `ProcessClassTopic`, `ProcessInstanceTopic`, and `PartialProcessTopic` to establish a clearer and more granular hierarchy for NATS process subjects.
- 🏷️ **Agent Class Topic**: Introduced `AgentClassTopic` to provide a class-level abstraction for agent topics in NATS, enhancing topic hierarchy.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⚙️ **Refined Agent/Process Configuration Loading Logic**: Dispatchers now intelligently load configurations, prioritizing those provided in a `StartEvent` or `ProcessStartEvent`, then database-persisted configurations, and finally falling back to the `default_config` defined in the runner.
- 🚀 **Enhanced Agent Discovery Mechanism**: The API and internal agent services now use a more granular discovery mechanism, distinguishing between agent *classes* and specific agent *instances* (including their specific configurations).
- 💡 **Improved Type Specificity for Topics**: Updated numerous type hints across agent and process components (`AgentTopic` to `AgentInstanceTopic`, `ProcessTopic` to `ProcessInstanceTopic` or `ProcessClassTopic`) to align with the new NATS topic hierarchy.
- 🔄 **Process Runner and Dispatcher Overhaul**: Significant refactoring of process runners and dispatchers to align with the new process configuration handling, topic hierarchy, and walkthrough context.
- ⚡️ **Improved Dispatcher Robustness**: The base dispatcher's `stop` method now checks for initialization status and explicitly marks itself as stopped, ensuring proper shutdown.
- 📈 **Enhanced NATS Debugging and Persistence**: NATS server configuration in `nats.conf` now enables detailed debugging and tracing, and `store_dir` is configured for persistent JetStream storage.
- 🛡️ **Internalized Core Services in Docker Compose**: NATS, Redis, and MongoDB services in `docker-compose.latest.yml` are no longer exposing their ports externally, enhancing security by limiting external access to these internal components within the Docker network.
- 🐳 **Dagster Stack in Docker Compose**: Added a complete Dagster stack (`dagster-webserver`, `dagster-daemon`) to `docker-compose.latest.yml`, integrated with OAuth2 Proxy for secure access.
- 📝 **Increased AIHub API Logging**: The `aihub_api` service's logging level in `docker-compose.latest.yml` has been set to `DEBUG`, providing more verbose output for development and troubleshooting.
- ⚙️ **MinIO Credentials in Docker Compose**: Updated MinIO environment variables in `docker-compose.latest.yml` to use `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` for new MinIO versions.
- 📦 **Playground Dockerfiles**: Added new Dockerfiles for `aihub_pipeline` and `default_rag_pipeline`, streamlining their containerization.
- 💬 **Improved Event Debugging**: Added more debug logging for message handling in `JetStreamEventStore` for enhanced observability.
- 📄 **New `from_raw_data` for Start Events**: `StartEvent` and `ProcessStartEvent` now include a factory method `from_raw_data` for more convenient creation from raw input.
- 📚 **Expanded Dispatchable Workflow Event Acceptance**: `DispatchableWorkflow` now accepts `WorkEvent` types in `get_steps_waiting_for_event`, allowing workflow steps to be triggered by a broader range of events.
- ➕ **Process ID in WorkRequestEvent**: Added `process_id` field to `WorkRequestEvent` for enhanced traceability of work requests within a process.
- 🛠️ **Process Entity Persistence Overhaul**: The `ProcessEntity` now stores a reference to `ProcessConfigEntityDocument` for its primary configuration and an embedded `ProcessConfigEntityEmbeddedDocument` for its default configuration, improving persistence flexibility.
- ⚙️ **ProcessConfig Enhancements**: `ProcessConfig` now includes a `process_class` field and `model_config` for Pydantic v2 compatibility, along with a `from_entity` factory.

### Fixed
- 🔄 **Updated Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Deprecated Test Files**: Cleaned up outdated test files related to agent and process configuration and dispatcher behavior, as their functionality is now covered by new, more integrated tests.
- 🗑️ **Redundant NATS Discovery Event**: Removed `DiscoveryRequestEvent` and `ProcessTopic`, replaced by a more granular and hierarchical set of new topics.
- 🗑️ **Legacy `from_uri` Method**: The static `from_uri` method has been removed from `DataLakeFile`, as its logic has been moved into cloud-specific data lake client implementations for better encapsulation.
- 🗑️ **Old Process Topic**: The generic `ProcessTopic` has been removed, replaced by `ProcessClassTopic` and `ProcessInstanceTopic` for clearer subject semantics.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- 🧹 **Minor Docker Image Optimization**: Removed `ca-certificates` from the `aihub_api` Dockerfile for a slightly leaner runtime image.
- 🔄 **Agent/Process Service Internal Naming**: Renamed many internal methods in `AgentService` and `ProcessService` (e.g., `discover_agent_class` to `_discover_agent_class`, `send_event` to `_send_event`) for better encapsulation and clarity.
- 🧹 **API Endpoint Discovery Renaming**: Renamed endpoint creation methods in `AgentEndpointsDiscoveryService` and `ProcessEndpointsDiscoveryService` (e.g., `create_endpoint` to `_create_endpoint`) to signify their internal utility.
- 📦 **Consolidated Base Context**: The `BaseContext` class was moved from `aihub_agent` to `aihub_lib`, centralizing common context management logic.
- ⚙️ **Streamlined NATS Subscription Logic**: `JSSubscriber`'s `stop` method and `subscribe` call now include more explicit logging and parameter passing for improved clarity.
- 📚 **Process Persistence Entities**: Renamed `from_dto` to `from_specs` for consistency in `HumanInSpecsEntity`, `ProgramInSpecsEntity`, and `AgentInSpecsEntity`.
- ⚙️ **Process Delegator Updates**: `AbstractEntityDelegator` and its subclasses (AgentDelegator, ProcessDelegator) were refactored to use the new process topic hierarchy and a new internal `_publish_work_event` method.
- 🧹 **NATS Topic Manager Cleanup**: Streamlined various topic manager methods to align with the new, more granular topic hierarchy.
- 🗂️ **New Python Package Structures**: Added new `__init__.py` files to reflect new module structures (e.g., `aihub_lib/generative_ai/document/accessor`, `aihub_lib/infrastructure/nats`, `aihub_pipeline/resources/data_lake/base`).

---



## [v0.226.0] - 2025-07-24 - Dynamic Agent Configurations and Richer RAG Context

### Added
- ✨ **Dynamic Agent Configuration**: Agents can now be dynamically configured through the `StartEvent` payload, allowing for custom overrides of default agent settings at runtime.
- 🚀 **Granular Agent Discovery**: Implemented new class-level and instance-level discovery mechanisms for agents, enabling systems to distinguish between an agent's abstract definition and its specific runnable configurations.
- 🗄️ **Persistent Agent Configurations**: Introduced the ability to save and load custom agent configurations directly from the database, allowing for persistent and shareable agent setups.
- 🔌 **Standardized Vector Store Configurations**: Added new Pydantic configurations for `AzureAISearchVectorStore` and `MilvusVectorStore`, enabling direct embedding and validation of vector store settings within agent configurations.
- 📄 **`agent_class` Field in `AgentConfig`**: A new `agent_class` field has been added to `AgentConfig` for consistent agent class identification across the system.
- 🧪 **Comprehensive Agent Configuration Tests**: New tests have been added to validate the dynamic agent configuration, database persistence, and discovery logic.
- 💻 **`save_config.py` Example**: A new example script demonstrates how to persist custom agent configurations to the database.
- 📈 **Hierarchical Document Headings in RAG**: RAG context now dynamically renders document headings (H1-H6) and wraps content with `<content>` or `<summary>` tags for clearer hierarchical structure and improved model interpretation.
- 🔒 **HTML Escaping for RAG Content**: HTML special characters in RAG context headings and content are now automatically escaped for enhanced integrity and security.

### Changed
- ⚙️ **Refined Agent Configuration Loading**: The agent dispatcher now prioritizes configurations provided in a `StartEvent`, falling back to database-persisted configurations, and then to the `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization**: Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 💡 **Improved LLM and Vector Store Type Specificity**: Agent configurations now use more precise type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration**: RAG and Retrieval agents now leverage a new `.to_llama_index()` method directly from their Pydantic vector store configurations for consistent integration.
- 🌐 **API Agent Discovery**: The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- 🌎 **Updated Default Ingested Node Language**: The default language for newly ingested nodes has been updated from English to German.
- ⚡️ **Improved `asyncio.Task` Management**: Enhanced handling of `asyncio.Task` instances within dispatchers and subscribers to ensure proper lifecycle management.
- 📄 **`StartEvent` Carries Agent Configuration**: The `StartEvent` now includes an `agent_config` dictionary, allowing it to carry the specific configuration for a given agent run.
- 🗎 **Gunicorn Module Path Correction**: Corrected the Gunicorn module path in the API Makefile for accurate application serving.

### Fixed
- 🐛 **Robust Profile Image Fetching**: Corrected the logic for fetching user profile images from Azure Graph Service, improving error handling for missing images.
- 🐞 **Process DTO Description Typo**: Corrected a minor typo in the `ProcessDTO` description in the generated SDK.

### Removed
- 🗑️ **Deprecated `system_prompt`, `color`, `voice` from `AgentConfig`**: These fields have been removed from the base `AgentConfig` and `AgentConfigDTO` to streamline core configuration, allowing for agent-specific prompt and UI customizations in subclasses.
- 🗑️ **Legacy Agent Configuration Persistence Classes**: Eliminated standalone MongoDB documents (`AgentConfigEntityDocument`) and embedded documents (`AgentConfigEntityEmbeddedDocument`) used for agent configurations, consolidating persistence directly within the `AgentEntity` via references.
- 🗑️ **Dedicated `LocaleStringEntity`**: The `LocaleStringEntity` used for persisting localized strings has been removed, as localization is now handled more directly within other models.
- 🗑️ **Obsolete `EventModelCreationService`**: Replaced by `ModelCreationService` for broader utility.
- 🗑️ **Redundant RAG Context Timestamp Formatting**: An internal utility for formatting Unix timestamps has been removed from the RAG context combination logic.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul**: Major refactor of `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and improving background task management.
- 🔄 **Unified Agent Discovery Architecture**: Overhauled the discovery mechanism, merging class and instance-level discovery events and topic managers into a single, consistent model.
- 🗄️ **Streamlined Agent Persistence**: Re-architected agent configuration persistence by storing a reference to standalone `AgentConfigEntityDocument` for user-defined configs and an embedded `AgentConfigEntityEmbeddedDocument` for default configs within `AgentEntity`.
- 📦 **Consolidated API DTOs for Agents**: Introduced dedicated DTOs (`AgentClassDTO`, `AgentInstanceDTO`, `MinimalAgentDTO`) to clearly separate agent definitions from their configured instances and minimal representations in the API.
- 🧹 **Renamed Model Creation Service**: `EventModelCreationService` was renamed to `ModelCreationService` to reflect its broader scope.
- 📁 **Test and Playground Restructuring**: Reorganized test runners into `simulation/agent` and `simulation/process` directories, and moved/renamed the web application's `.playground` to `.app`.
- ⚙️ **Refined RAG Node Sorting**: Improved the internal sorting mechanism for nodes within a document based on section start lines and node type.
- 📦 **Standardized Docker Builds**: Streamlined Dockerfiles for API and Bot services, ensuring dependencies are installed efficiently and reducing image sizes.
- 🧹 **Codebase Naming Consistency**: Renamed internal `_get_endpoint_name` to `_get_endpoint_base_path` in endpoint discovery services for improved clarity.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled custom environment variable configuration for API services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📦 **Docker Build Process Simplification**: Streamlined Dockerfiles for API and Bot services by removing redundant virtual environment copying, leading to more efficient builds.
- ⚙️ **Docker Compose Configurations**: Updated Docker Compose configurations, including a new `docker-compose.latest.yml` for comprehensive service deployment and streamlined local development setup.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages for better model interpretation.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue where image URLs in RAG prompts were not consistently processed, ensuring images are now correctly referenced and displayed.
- 🐛 **`JudgeOutput` Schema Immutability**: Ensured the `JudgeOutput` schema is deeply copied before being passed to LLM for structured prediction, preventing unintended mutations.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.
- 🗑️ **Deprecated Docker Compose for Mounted Volumes**: Removed `docker-compose-mnt.yml` as part of streamlining Docker Compose strategy.

---



## [v0.229.0] - 2025-07-28 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.
- 📦 **New Docker Infrastructure Configuration:** Added `dagster.yaml` for Dagster's persistent storage setup, enabling more robust pipeline execution.
- 🚀 **Automated Build & Release Workflows:** New GitHub Actions workflows have been added to automate the Docker image build and release process for **Agents**, **Dagster**, and **Pipelines**, enabling triggers from new tags, manual dispatch, and specific feature branches.
- ✨ **Introduced `LLMWrappingAgent`:** A new agent designed to wrap and interact with Large Language Models, complete with its Dockerfile, configuration settings, and main application entry point, providing a flexible interface for LLM integrations.
- 🗄️ **Database Persistence for Process Configurations:** Custom process configurations can now be saved and retrieved from the database via new entities (`ProcessConfigEntity`, `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`), enabling persistent and shareable process setups.
- 🧪 **Comprehensive Process Testing Infrastructure:** Added extensive unit and integration tests for `ProcessDispatcher` and `ProcessService`, focusing on new configuration loading logic, discovery, and database interactions.
- 📄 **Process Configuration Schema Definition:** Introduced `ProcessConfigSpecs` to define the schema of process configurations, enabling dynamic form generation for process inputs in the API.
- 👥 **New Process DTOs:** Introduced `MinimalProcessDTO`, `ProcessClassDTO`, and `ProcessInstanceDTO` to clearly distinguish between process definitions and their configured, runnable instances in the API.
- 📚 **New Context Scope for Processes:** Added `WalkthroughContext` for managing per-walkthrough state in Redis, allowing processes to maintain state across execution steps.

### Changed
- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted pipeline playground examples to showcase the new S3/MinIO data lake capabilities and switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support comprehensive S3/MinIO integrations.
- ⚙️ **Refined Agent Discovery and Event Dispatch:** Updated agent dispatchers, test runners, and delegators to align with the new `AgentInstanceTopic` hierarchy, enhancing consistency and clarity in event routing.
- ⚙️ **Process Configuration Loading Logic:** The process dispatcher now intelligently loads configurations, prioritizing those provided in a `ProcessStartEvent` or from `WalkthroughContext`, falling back to `default_process_config`.
- 🌐 **Revised API Process Discovery:** The API now discovers and exposes full process *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- 🛡️ **Internalized Core Services in Docker Compose:** NATS, Redis, MongoDB, and Postgres services in `docker-compose.latest.yml` are no longer exposing their ports externally, enhancing security by limiting external access to these internal components within the Docker network.
- 📝 **Increased AIHub API Logging:** The `aihub_api` service's logging level in `docker-compose.latest.yml` has been set to `DEBUG`, providing more verbose output for development and troubleshooting.
- 💡 **Updated NATS Configuration:** The NATS server configuration now explicitly enables `debug`, `trace`, and `trace_verbose` logging, and uses a persistent `store_dir` for JetStream data, improving operational visibility and data durability.
- 🚀 **Dagster Deployment in Docker Compose:** Integrated Dagster webserver and daemon into `docker-compose.latest.yml`, enabling full Dagster functionality within the stack, including S3-compatible object storage via Traefik.
- 🔑 **MinIO Authentication:** Updated MinIO environment variables to `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` for consistency with recent MinIO versions.

### Fixed
- 🐛 **Robust Dispatcher Logging:** Enhanced JetStream event store message handling to log exceptions properly without re-raising, ensuring message acknowledgment and preventing redelivery loops.
- 🐛 **Dockerfile Optimization:** Removed redundant `ca-certificates` package from `aihub_api` Dockerfile for a slightly leaner image.

### Removed
- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Generic Discovery Events:** Removed generic `DiscoveryRequestEvent` and old `ProcessDiscoveryResponseEvent` as they have been superseded by more specific class and instance discovery events.
- 🗑️ **Obsolete Process Topic:** The generic `ProcessTopic` has been removed, replaced by a more granular hierarchy of process topics (`PartialProcessTopic`, `ProcessClassTopic`, `ProcessInstanceTopic`).
- 🗑️ **Old Agent Config Test File:** Removed `test_agent_config_start_event.py` as its logic is now covered by more comprehensive tests or integrated into core components.
- 🗑️ **Deprecated DataLakeFile Creation:** The `DataLakeFile.from_uri` static method was removed, with its functionality now handled by cloud-specific data lake client implementations.

### Refactor
- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure` subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the URI-based creation method into cloud-specific data lake client implementations for better encapsulation and maintainability.
- ⚙️ **Updated Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.
- 🧹 **Centralized Base Context:** Moved `BaseContext` from `aihub_agent` to `aihub_lib`, promoting reusability and reducing duplication across service cores.
- 🔄 **Streamlined Agent Topic Hierarchy:** Refactored agent NATS topics (`AgentTopic` renamed to `AgentInstanceTopic`) and introduced `AgentClassTopic` to establish a clearer hierarchy between agent classes and instances.
- 🔄 **Streamlined Process Topic Hierarchy:** Refactored process NATS topics, introducing `PartialProcessTopic`, `ProcessClassTopic`, and `ProcessInstanceTopic` for a more granular and consistent topic structure.
- ⚙️ **Unified Event Creation for Start Events:** Consolidated `StartEvent` and `ProcessStartEvent` creation logic into `from_raw_data` class methods, improving consistency and encapsulation.
- 🧹 **Standardized Internal Method Naming:** Renamed several internal `AgentService` and `ProcessService` methods (e.g., `discover_agent_class` to `_discover_agent_class`, `send_event` to `_send_event`) to explicitly mark them as private.
- 🧹 **Cleaned up Internal Dispatcher State:** Removed explicit `_initialized` and `_init_lock` flags from `BaseDispatcher` as their management is now handled implicitly by context managers or other lifecycle hooks.
- 🧹 **Streamlined Dispatcher Shutdown:** Improved `BaseDispatcher.stop()` to explicitly stop the event store and update its initialization flag, ensuring a clean shutdown.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled custom environment variable configuration for API services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 💡 **New Docker Infrastructure Components**: Added `docker-compose.latest.yml` and related configurations for Milvus, NATS, and PostgreSQL, providing a streamlined and comprehensive deployment environment.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.
- ✨ **Enhanced `Human` Delegator in Processes**: Refined input/output specifications for the `Human` delegator, adding support for initial forms (`start_form`) and more granular user targeting (e.g., `user_ids`, `user_emails`).
- 📈 **Improved Database Indexing**: Added new database indexes to `PersistedAgentEventEntity`, `PersistedProcessEventEntity`, `ThreadEntity`, and `UserEntity` for enhanced query performance.
- 📊 **Enhanced Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- ✂️ **Deprecated Health Service Page**: A basic placeholder health page in the frontend was removed.
- 🗑️ **Outdated Docker Compose Configuration**: Removed the old `docker-compose-mnt.yml` file, which has been superseded by a more comprehensive and updated `docker-compose.latest.yml`.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related assets, improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- ✂️ **Streamlined Dockerfiles**: Optimized Dockerfiles for various services by removing redundant `poetry install` and virtual environment copy steps, resulting in smaller and more efficient images.
- 🗂️ **Web Application Structure**: Restructured the Nuxt.js development environment from `.playground` to `.app` for better organization and consistency.

---



## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added
- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`, `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different data lake storage solutions.

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



## [llm_wrapping_agent-v0.226.0] - 2025-07-25 - Introducing the LLM Wrapping Agent and CI/CD Enhancements

### Added
- ✨ **Introduced `LLMWrappingAgent`**: A new agent designed to wrap and interact with Large Language Models, providing a flexible interface for LLM integrations. This includes its dedicated Dockerfile, configuration settings, and main application entry point.
- 🚀 **Implemented Agent Build & Release Workflow**: A new GitHub Actions workflow has been added to automate the Docker image build and release process for agents, enabling triggers from new tags, manual dispatch, and specific feature branches.

### Changed
- ⚙️ **Updated NATS Configuration**: The NATS server configuration now includes enhanced debugging and tracing capabilities, and utilizes persistent storage for JetStream data, improving operational visibility and data durability.
- 🛡️ **Internalized Core Services in Docker Compose**: NATS, Redis, and MongoDB services in `docker-compose.latest.yml` are no longer exposing their ports externally, enhancing security by limiting external access to these internal components within the Docker network.
- 📝 **Increased AIHub API Logging**: The `aihub_api` service's logging level in `docker-compose.latest.yml` has been set to `DEBUG`, providing more verbose output for development and troubleshooting.

### Refactor
- 🧹 **Minor Docker Image Optimization**: Removed `ca-certificates` from the `aihub_api` Dockerfile for a slightly leaner runtime image.

---



## [v0.226.0] - 2025-07-22 - Agent Configuration Overhaul and Enhanced Document Context

### Added
- ✨ **Dynamic Agent Configuration**: Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Enhanced Agent Discovery Mechanism**: Implemented granular discovery for agent *classes* and specific agent *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations**: Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups across deployments.
- 🔌 **New Pydantic Models for Vector Store Configurations**: Introduced dedicated Pydantic configurations for `AzureAISearchVectorStore` and `MilvusVectorStore`, allowing for direct embedding and validation of vector store settings within agent configs.
- 📈 **`agent_class` Field in `AgentConfig`**: A new `agent_class` field has been added to `AgentConfig` for consistent agent class identification throughout the system.
- ✨ **Hierarchical Document Headings**: Implemented the dynamic rendering of document headings (H1-H6) directly within the context, providing clearer hierarchical structure and improved readability.
- 📄 **Structured Content and Summary Tags**: Individual node content is now explicitly wrapped in XML-like tags (`<content>` or `<summary>`) based on its type, providing more precise semantic context.
- 🔒 **HTML Escaping for Content**: Enhanced the integrity and security of rendered content by automatically escaping HTML special characters in both headings and content, preventing unintended rendering issues.
- 🦾 **New Job Creation Utility**: Introduced `materialize_asset_job` to simplify the creation of jobs for materializing specific selections of assets within pipelines.
- 📅 **Automated Playground Workflows**: Implemented new daily jobs and schedules within the playground environment to automatically observe source data and manage document removal processes.
- 📚 **New Database Entities for Localization**: Introduced `LocaleStringEntity` for standardizing the storage of localized strings in the database.

### Changed
- ⚙️ **Refined Agent Configuration Loading Logic**: The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization**: Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 💡 **Improved Type Specificity for LLM and Vector Store Configs**: Agent configurations now utilize more precise type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration**: RAG and Retrieval agents now leverage the `.to_llama_index()` method directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- ⚡️ **Enhanced Background Task Management**: Improved handling of `asyncio.Task` instances within dispatchers and subscribers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Revised API Agent Discovery**: The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- ⚙️ **Updated Default Document Language**: The default language for newly ingested nodes has been updated from English to German, better aligning with regional configurations.
- ⚡️ **Refined Node Sorting Logic**: Improved the internal sorting mechanism for nodes within a document. Nodes are now ordered more accurately based on their section start lines and type.
- ⚙️ **Refined Asset Automation**: Adjusted automation configurations for document and data lake file removal assets, transitioning from eager conditions to more explicit job-driven scheduling.
- 🔗 **Specialized I/O Manager**: Updated the SharePoint observable asset to utilize a dedicated `sharepoint_io_manager`, ensuring more appropriate handling of SharePoint data interactions.
- 📄 **Agent Configuration Data Format**: The `ChatService` now passes agent configuration data as a dictionary instead of a Pydantic object when publishing `UserMessageEvent`, standardizing data exchange.

### Fixed
- 🐛 **Robust Figure Deletion in Pipelines**: Improved the data lake figure deletion process in pipelines by adding an existence check, preventing potential errors when a figures directory is already absent.
- 🖼️ **Robust User Profile Image Retrieval**: Enhanced `AzureGraphService` to gracefully handle cases where a user's profile image is not found, preventing errors.

### Refactor
- 🔄 **Consolidated Agent Configuration Management**: Standardized agent configuration handling across the system, enabling dynamic overrides and database persistence for agent instances.
- ✨ **Refined Agent and Event Discovery Architecture**: Overhauled the discovery mechanism to support both class-level and instance-level agent introspection, providing more granular control and information.
- 🏗️ **Reorganized API DTOs for Agent Representation**: Introduced dedicated DTOs (`AgentClassDTO`, `AgentInstanceDTO`, `MinimalAgentDTO`) to clearly separate the concept of an agent's definition from its configured, runnable instances in the API.
- 🧹 **Internal API Service Renaming**: Renamed `EventModelCreationService` to `ModelCreationService` to reflect its broader utility beyond just event models.
- 🧹 **Standardized Agent Configuration Model**: Revised `AgentConfig` by removing deprecated fields (`system_prompt`, `color`, `voice`) and promoting its general use across agent and process configurations.
- 🧹 **Streamlined Timestamp Handling**: Removed an internal utility for formatting Unix timestamps as date and time handling for document metadata is now managed more efficiently by the underlying system.
- 🧹 **Consolidated Data Transfer Objects (DTOs)**: Relocated all agent-related DTOs into a dedicated `dto` subdirectory for improved organization and clarity.
- 🔄 **Enhanced DTO Encapsulation**: `AgentInstanceDTO` now manages its own persistence by handling entity creation/updates and generating discovery response events directly, improving data model autonomy.
- 🗄️ **Decoupled Agent Persistence**: The `AgentEntity` creation and update logic was refactored to accept explicit parameters instead of DTO objects, enhancing the reusability and flexibility of the persistence layer.
- ⚙️ **Standardized Event Specification Handling**: Updated `EventSpec` creation methods to consistently use `EventSpecs` objects, improving internal data handling.
- 🔗 **Streamlined Topic Inheritance**: `AgentInstanceDiscoveryTopic` now correctly inherits from `AgentClassDiscoveryTopic`, reducing redundancy and clarifying topic structure.

### Removed
- 🗑️ **Deprecated Configuration Fields**: The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration.
- 🗑️ **Direct Agent Config Persistence Example**: Eliminated `save_config.py` from playground examples, indicating a shift away from direct saving of agent configurations to the database via this script.
- 🗑️ **Obsolete Test Files**: Cleaned up several outdated test files related to agent dispatcher, agent config, and agent service database integration.
- 🧹 **Redundant NATS Topic Managers**: Cleaned up unused and overlapping topic management methods within `AgentClassTopicManager` for a leaner API.
- 🚫 **Transferred Discovery Event Logic**: Removed the `from_agent_instance` method from `AgentInstanceDiscoveryResponseEvent` as its functionality has been moved to the `AgentInstanceDTO` for better encapsulation.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled Custom Environment Variable Configuration for API Services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 📦 **New Docker Infrastructure Configuration**: Added new `docker-compose.latest.yml` providing a complete, ready-to-run local environment including Milvus, OpenWebUI, Phoenix, Postgres, NATS, Redis, MongoDB, and Traefik.
- 📦 **New Web Image Build Workflow**: Added a new GitHub Actions workflow to build and release the web frontend Docker image, streamlining deployment processes.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses and JWKS keys, improving performance for frequently requested agent lists and authentication.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.
- 📦 **Updated Python Dependency Management**: Migrated Python Docker image builds from a `poetry install --no-root` and virtual environment copy approach to a simpler `poetry install` directly in the final runtime image, reducing build complexity and image size.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Docker Compose Setup**: Removed the `docker-compose-mnt.yml` file, which has been superseded by a more comprehensive and updated Docker Compose setup.
- 🗑️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.
- 🗑️ **Old Frontend Playground**: The `.playground` directory for frontend development has been removed, replaced by the standardized `.app` directory.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enhanced API Configuration and Extensibility**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 🐳 **Comprehensive Docker Compose Deployment**: Introduced a new `docker-compose.latest.yml` for unified deployment of all core AI Hub services, including Milvus, Postgres, OpenWebUI, Phoenix, and API, simplifying local and production setups.
- 📦 **Optimized Web Application Deployment**: Introduced a new multi-stage `Dockerfile` for the web application, optimizing build times and final image size, along with `nginx.conf` and `config.template.json` for robust production serving.
- ⚙️ **New Infrastructure Configuration Files**: Added new configuration files for Milvus (`milvus.yaml`), NATS (`nats.conf`), and PostgreSQL initialization (`init-multiple-dbs.sh`), streamlining infrastructure setup.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated all related API routes and frontend client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 🧑‍💻 **Enhanced Human-in-the-Loop Interactions**: Significantly redesigned human interaction mechanisms, enabling granular targeting of users (`user_ids`, `user_emails`, `user_roles`) for work requests, and introduced the ability to define and render dynamic forms for human input directly within process steps.
- 📊 **Expanded Process Discovery Information**: Enhanced `ProcessDiscoveryResponseEvent` and `ProcessRunner` to provide a richer set of details on human, program, and agent inputs for each process, including dynamic form schemas for human interactions.
- 📝 **Improved Work Event Traceability**: Integrated `HumanWorkEvent` with the new `Form` base class for dynamic UI generation and extended both `HumanWorkEvent` and `ProgramWorkEvent` to include `submitted_by` user information for enhanced traceability.
- 📈 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.
- 📦 **Frontend Build and Dependency Updates**: Updated build scripts and integrated new Formkit-related modules and dependencies to support the new dynamic form generation and improved localization capabilities.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic to gracefully handle cases where a specific agent might not be found in the database, ensuring `is_online` status is accurately reflected.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context and that NATS process discovery topics are strictly validated.
- 🧰 **Improved Serialization and Schema Handling**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, preventing data loss, and ensured deep copying of schemas in the evaluation framework to avoid unintended modifications.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure for better modularity.
- 🌐 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related components for improved consistency and readability.
- 🏠 **Frontend Directory Renaming**: Renamed the primary frontend application directory from `.playground` to `.app` to better distinguish it as the main application source, updating all related configurations.
- 🐳 **Optimized Dockerfiles**: Streamlined API and `aihub_bot` Dockerfiles by removing redundant virtual environment copying and poetry installation steps, leading to smaller and faster image builds.

### Removed
- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Docker Compose for Mounted Volumes**: Removed `docker-compose-mnt.yml` as it is superseded by updated Docker Compose strategies that better handle volume management and local development.
- 🗑️ **Deprecated Event Distributor Dependency**: Removed the generic `use_external_event_distributor` dependency helper, which is now replaced by more specific `use_external_agent_event_distributor` and `use_external_process_event_distributor`.
- ✂️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.

---



## [web-v0.227.0] - 2025-07-23 - Configuration Adjustments

### Changed
- ⚡️ **Adjusted Default Log Level:** Set the default `LOG_LEVEL` for the API service in the `latest` Docker Compose configuration from `DEBUG` to `WARNING` to reduce log verbosity and focus on more critical messages.

---



## [web-v0.226.0] - 2025-07-24 - Advanced Agent Management & Structured RAG Output

### Added
- ✨ **Dynamic Agent Configuration**: Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default settings.
- 🚀 **Hierarchical Agent Discovery**: Implemented granular discovery for agent *classes* and specific agent *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations**: Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups.
- 📚 **Structured RAG Context Output**: Introduced hierarchical heading rendering (H1-H6) and explicit `<content>` / `<summary>` tags for RAG nodes, significantly improving the readability and structure of contextual information.
- 🔐 **Secure HTML Escaping in RAG Context**: Automatically escapes HTML special characters in rendered RAG context (headings and content) to prevent rendering issues and potential injection vulnerabilities.
- 🔗 **Standardized Vector Store Configurations**: Introduced new Pydantic configurations (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`) for vector stores, enabling their direct embedding and validation within agent configs.
- 🧩 **Modular API Controllers**: Exposed new API controllers for `Suite`, `Token`, and `Role` management, expanding the system's external capabilities.
- 📄 **New Persistence for Localized Strings**: Introduced `LocaleStringEntity` for storing localized strings in the database, enhancing internationalization support.
- 🧪 **Pipeline Job Creation Utility**: Added `materialize_asset_job` to simplify the creation of jobs for materializing specific selections of assets.
- ⏱️ **Automated Pipeline Schedules**: Implemented new daily jobs and schedules within the playground environment to automatically observe source data and manage document removal processes.

### Changed
- ⚙️ **Refined Agent Configuration Loading Logic**: The agent dispatcher now prioritizes `StartEvent` configurations, then database-persisted configurations, and finally falls back to the `default_agent_config` defined in the runner.
- 🔄 **Updated Agent Runner Initialization**: Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 🎯 **Precise LLM & Vector Store Typing**: Agent configurations now use more specific type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔄 **Streamlined Vector Store Integration**: RAG and Retrieval agents now convert vector store configurations to LlamaIndex objects via a `.to_llama_index()` method, ensuring consistent integration.
- 🚀 **Enhanced Asynchronous Task Management**: Improved handling of `asyncio.Task` instances across dispatchers and subscribers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Granular API Agent Discovery**: The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- ⚙️ **Updated Default RAG Language**: The default language for newly ingested RAG nodes has been changed from English to German.
- 📊 **Pipeline Automation Conditions**: Adjusted automation configurations for document and data lake file removal assets from eager conditions to job-driven scheduling.
- 🔗 **Dedicated SharePoint I/O Manager**: The SharePoint observable asset now utilizes a dedicated `sharepoint_io_manager` for more appropriate data handling.
- 🖼️ **Graceful User Profile Image Fetching**: Enhanced `AzureGraphService` to gracefully handle cases where user profile images are not found (HTTP 404), preventing unnecessary warnings.
- 🏷️ **API Endpoint Renaming for Agent Events**: Renamed API endpoints for agent events (e.g., `/events/threads` to `/events/agent/threads`) for clearer distinction.
- 📦 **Docker Compose and Environment Updates**: Updated `docker-compose.latest.yml` with more comprehensive service configurations, including environment variables for OAuth, improved Traefik rules, and web service.

### Fixed
- 🐛 **Robust Pipeline Figure Deletion**: Improved the data lake figure deletion process in pipelines by adding an explicit directory existence check, preventing errors when figures directories are absent.
- 💬 **API SDK Typo**: Corrected a minor typo in the `ProcessDTO` description in the generated SDK, changing "processis" to "process is online".

### Removed
- 🗑️ **Deprecated Agent Configuration Fields**: The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration.
- 🗑️ **Legacy Discovery Events and Topic Managers**: Removed old class- and instance-specific discovery events and topic managers, unifying agent discovery under a new, hierarchical model.
- 🗑️ **Outdated Unix Timestamp Formatting Utility**: The internal `format_unix_timestamp` utility for RAG context has been removed.

### Refactor
- 🔄 **Consolidated Agent Configuration Management**: Standardized agent configuration handling across the system, enabling dynamic overrides and database persistence for agent instances.
- ✨ **Refined Agent Discovery Architecture**: Overhauled the discovery mechanism to support both class-level and instance-level agent introspection, providing more granular control and information.
- 🏗️ **Reorganized API DTOs for Agent Representation**: Introduced dedicated DTOs (`AgentClassDTO`, `AgentInstanceDTO`, `MinimalAgentDTO`) to clearly separate the concept of an agent's definition from its configured, runnable instances in the API.
- 📦 **Streamlined Vector Store Configuration**: Replaced direct usage of `llama_index` vector store objects with internal Pydantic configuration objects that can convert to `llama_index` types.
- 🧹 **Test File Reorganization**: Reorganized API test runners and related test files into more logical `simulation/agent` and `simulation/process` directories.
- 🧹 **Internal API Naming Consistency**: Renamed the internal `_get_endpoint_name` to `_get_endpoint_base_path` in endpoint discovery services for improved clarity and consistency.
- 🧹 **API Service Renaming**: Renamed `EventModelCreationService` to `ModelCreationService` to reflect its broader utility beyond just event models.
- 🧹 **Python Module Import Consistency**: Corrected `gunicorn` entrypoint in `Makefile` from `app/main:app` to `app.main:app` for standard Python module import.
- 🧹 **Cleaned up Agent Playground Examples**: Updated various agent playground examples to align with the new `default_agent_config` and the removal of deprecated fields.

---



## [v0.228.0] - 2025-07-25 - Azure Document Intelligence Key Access Alignment

### Refactor
- 🔄 **Updated Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

---



## [bot-v0.227.0] - 2025-07-23 - Operational Adjustments

### Changed
- ⚙️ **Optimized Default Logging Level:** Reduced the default log verbosity for the bot service from `DEBUG` to `WARNING` in the `docker-compose.latest.yml` configuration, leading to less noise in logs and improved operational clarity.

---



## [v0.226.0] - 2025-07-24 - Next-Gen Agent Management & Data Context

### Added
- ✨ **Dynamic Agent Configuration:** Agent configurations can now be dynamically provided via `StartEvent` or loaded from the database, enabling custom overrides of default agent settings for flexible deployments.
- 🗄️ **Persistent Agent Configurations:** Introduced new database entities (`AgentConfigEntityDocument`, `AgentConfigEntityEmbeddedDocument`) to allow custom agent configurations to be saved and retrieved, enhancing reusability.
- 🚀 **Granular Agent Discovery:** Implemented explicit discovery mechanisms for both agent *classes* (`ClassDiscoveryRequestEvent`, `AgentClassDiscoveryResponseEvent`) and specific agent *instances* (`InstanceDiscoveryRequestEvent`, `AgentInstanceDiscoveryResponseEvent`), providing richer metadata.
- ⚙️ **Typed Vector Store Configurations:** Introduced dedicated Pydantic configuration models (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`) for vector stores, enabling their direct embedding and validation within agent configurations.
- 📄 **Structured Document Rendering:** Enhanced `combine_nodes_in_order` to dynamically render hierarchical headings (H1-H6) and semantic tags (`<content>`, `<summary>`) for improved RAG context readability.
- 🔒 **Secure Content Escaping:** Implemented automatic HTML escaping for text within rendered headings and content blocks, preventing unintended rendering issues and potential injection vulnerabilities.
- 🧪 **Comprehensive Agent Testing:** Added extensive unit and integration tests for `AgentDispatcher` and `AgentService`, focusing on new configuration loading logic, discovery, and database interactions.
- 🏭 **Pipeline Job Factory:** Introduced `materialize_asset_job` utility to simplify creating jobs for specific asset materialization in data pipelines.
- 🗓️ **Automated Pipeline Workflows:** Implemented new daily jobs and schedules in the pipeline playground for automated data processing and document cleanup.
- ➕ **New API Controllers:** Expanded the API with new controllers for `Suite`, `Process`, `Token`, and `Role` management, diversifying available endpoints.
- 🐳 **Enhanced Docker Compose Stack:** Updated `docker-compose.latest.yml` to include the `web` service and more comprehensive environment variables for API and Phoenix, providing a more integrated deployment experience.

### Changed
- 🔄 **Agent Configuration Handling:** Agent configuration is now dynamically resolved at runtime (from `StartEvent`, database, or default), and `AgentRunner` uses a `default_agent_config` parameter.
- 🏷️ **Agent Config Schema Refinement:** `AgentConfig` now includes an explicit `agent_class` field and applies a stricter regex pattern to `agent_id` for enhanced validation.
- 💧 **LLM and Embedding Model Specificity:** Agent configurations now use more precise type unions for LLMs and embedding models, improving type safety and clarity.
- 📚 **API Discovery Response:** The API now discovers and exposes full agent *instances* (including their specific configurations) rather than just class definitions.
- 🗺️ **Default Ingested Language:** The default language for newly ingested nodes is now German (`de`).
- 🧭 **API Route Renaming:** Event retrieval API routes have been renamed to explicitly refer to agent events (e.g., `get_agent_events_in_thread`).
- 🌐 **Web SDK Updates:** Generated SDK schemas for `AgentConfigDTO` reflect the removal of deprecated fields, and `StartEvent` and `UserMessageEvent` now include the new `agent_config` field.
- ⚡ **Pipeline Automation Strategy:** Document and data lake file removal assets transitioned from eager automation conditions to job-driven scheduling.
- 📦 **SharePoint IO Manager:** The SharePoint observable asset in pipelines now uses a dedicated `sharepoint_io_manager`.
- 🔐 **OAuth2 Integration:** The API's OAuth2 authentication now supports `OAuth2AuthHandler`.
- 🧪 **Test Runner Configuration:** Agent and process playground examples and their test runners have been updated to align with the new `default_agent_config` and `agent_class` fields.

### Fixed
- 🐛 **Robust Figure Deletion:** Improved the data lake figure deletion process in pipelines by adding a check for directory existence, preventing unnecessary errors.
- 🖼️ **Image Loading in RAG Prompts:** Corrected the image URL handling in RAG prompts within `combine_nodes_in_order`, ensuring images are correctly referenced.
- 🐞 **Gunicorn Path:** Corrected the Gunicorn application path in the Makefile.
- 💬 **SDK Description Typo:** Fixed a minor typo in the `ProcessDTO` description within the generated SDK.
- 📸 **User Profile Image Fetching:** Improved error handling for fetching user profile images from Azure Graph, gracefully handling 404 responses.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul:** Major refactoring of `AgentDispatcher` and `AgentRunner` components to streamline internal logic, simplify argument injection, and refine background task management.
- 🔄 **Unified Agent Discovery Architecture:** Streamlined the agent discovery mechanism by merging class and instance-level discovery concepts into a more consistent model, centralizing logic in new topic managers.
- 🗄️ **Decoupled Agent Persistence:** Re-architected agent configuration persistence to use a reference model (`AgentConfigEntityDocument`) and an embedded default (`AgentConfigEntityEmbeddedDocument`), enhancing data co-location and simplifying relationships.
- 📦 **Streamlined Vector Store Integration:** Standardized vector store integration using the new Pydantic configuration models' `.to_llama_index()` method for cleaner instantiation.
- 📁 **Project Structure Alignment:** Reorganized testing directories for `aihub_agent` and `aihub_api` for better module structure.
- ✏️ **Service Naming Consistency:** `EventModelCreationService` was renamed to `ModelCreationService` to reflect its broader utility beyond just event models.
- 🧹 **Codebase Naming Alignment:** Standardized field names (`name`, `description`, `icon`) in `AgentConfig` and refactored internal endpoint path generation methods for clarity.

### Removed
- 🗑️ **Deprecated Agent Config Fields:** Eliminated `system_prompt`, `color`, and `voice` fields from the base `AgentConfig` and `AgentConfigDTO`, allowing for more flexible, agent-specific prompt and UI customization in subclasses.
- 🗑️ **Legacy Discovery Methods:** Removed old generic `discover_agent` and `discover_agents` methods in `AgentService` in favor of the new, more granular discovery.
- 🗑️ **Timestamp Formatting Utility:** Removed the internal `format_unix_timestamp` utility from `combine_nodes_in_order`.
- 🗑️ **Redundant Topic Management:** Cleaned up unused and overlapping topic management methods in `AgentInstanceTopicManager` and `ProcessInstanceTopicManager`.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 📦 **Local Development & Deployment Configurations**: Added new Docker Compose files (`milvus.yaml`, `nats.conf`, `init-multiple-dbs.sh`, `docker-compose-gpu.*`, `docker-compose.dev.yml`, `docker-compose.nightly.yml`, `swiss-aihub.local.docker-compose.yml`) for setting up local development and production-like environments, including configurations for Milvus, NATS, and PostgreSQL.
- ✨ **Enabled Custom API Environment Variables**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, increasing configuration flexibility.
- 🐳 **Web Application Dockerfile and Nginx Setup**: Introduced a new Dockerfile, Nginx configuration (`nginx.conf`), and client-side configuration loader (`config-loader.client.ts`) for building and serving the web UI, optimizing deployment and environment variable handling.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- ⚙️ **Optimized Docker Build Processes**: Improved Dockerfile efficiency for `aihub_api` and `aihub_bot` by streamlining Poetry installation and virtual environment handling.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🧰 **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments for improved consistency.
- 👥 **Expanded Human Delegator Definition**: Enhanced the `Human` delegator to allow requesting work from specific user IDs, emails, or roles, and to define whether notifications should be sent.
- 📈 **Database Indexing Enhancements**: Added new indexes to `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance and data retrieval efficiency.
- 📦 **Unified Docker Compose for Latest Release**: Significantly refactored `docker-compose.latest.yml` to consolidate and centralize the deployment of core services, including MinIO, Milvus, PostgreSQL, OpenWebUI, NATS, Redis, MongoDB, and the AI Hub API, along with Traefik for routing.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found by using `.first()` instead of `.get()`.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context in `PersistedProcessEventEntity`.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Ensured that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation in RAG prompts.
- 🔐 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🎨 **Frontend Markdown Renderer Styling**: Applied a minor CSS fix to the Markdown renderer for improved display consistency.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🧹 **Deprecated Docker Compose File**: The `docker-compose-mnt.yml` file, which was used for mounting local volumes, has been removed.
- ⛔ **Old External Event Distributor Dependency**: The `use_external_event_distributor` dependency file has been removed as it has been superseded by more specific agent and process event distributors.
- 📄 **Redundant Frontend Health Page**: A basic placeholder health page (`pages/service/health.vue`) in the frontend was removed.
- 🏷️ **Obsolete WebSocket Event Type**: The `WsServerEvent` type has been removed from the SDK, replaced by the more semantically clear `ContextualizedAgentEvent` to better distinguish event origins.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related assets for improved clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components (`ThreadContext`, `RunTraceCoordinator`, `AgentService`, `EvaluationService`, `EventService`, `OpenaiController`, `OpenaiService`, `ExternalAgentEventDistributor`, `WebSocketManager`, `WebSocketSender`, `AgentDiscoveryTopic`, `ProcessDiscoveryTopic`), focusing on concise explanations.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure for better organization and clarity.
- 🔄 **Frontend Playground Folder Renaming**: The `.playground` folder in `aihub_web` has been renamed to `.app` to better reflect its purpose as the primary application source.
- 📦 **SharePoint Integration Naming Consistency**: Standardized naming conventions across SharePoint-related assets, ops, and IO managers to `share_point_` for improved consistency and readability.
- 🔗 **API External Event Deserialization**: Simplified the deserialization logic for external agent events by removing redundant `thread_id` and `display_id` validation.

---



## [api-v0.227.0] - 2025-07-23 - Operational Refinements

### Changed
- ⚙️ Optimized the **default log level** in `docker-compose.latest.yml` from `DEBUG` to `WARNING`, reducing log verbosity and improving clarity in standard operational environments.

---



## [api-v0.226.0] - 2025-07-24 - Unlocking Agent Flexibility: Dynamic Configurations, Enhanced Knowledge Context, and Structured Discovery

### Added
- ✨ **Dynamic Agent Configuration**: Introduced the ability to dynamically provide agent configurations via a `StartEvent` or load them from the database, offering greater flexibility and custom overrides for default agent settings.
- 🚀 **Granular Agent Discovery**: Implemented distinct discovery mechanisms for agent *classes* and specific agent *instances*, allowing the system to differentiate between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations**: Enabled custom agent configurations to be saved and retrieved from the database, allowing for persistent and shareable agent setups.
- 📄 **Structured RAG Context**: Enhanced the RAG context generation to include hierarchical headings (H1-H6) and explicitly tag content with `<content>` or `<summary>` tags, significantly improving prompt quality and model understanding.
- 🔒 **HTML Escaping for Context Content**: Implemented automatic HTML escaping for content within RAG context documents, preventing rendering issues and potential injection vulnerabilities.
- 🦾 **New Vector Store Configuration Models**: Introduced dedicated Pydantic models for `AzureAISearchVectorStoreConfig` and `MilvusVectorStoreConfig`, allowing direct embedding and validation of vector store settings within agent configurations.
- ⚙️ **Pipeline Job Utility**: Added the `materialize_asset_job` utility to simplify the creation of jobs for materializing specific asset selections in the pipeline.
- 📅 **Automated Pipeline Workflows**: Implemented new daily jobs and schedules within the playground environment to automatically observe source data and manage document removal processes.
- ✨ **Agent Class Identification**: A new `agent_class` field has been added to `AgentConfig` for consistent agent class identification throughout the system.

### Changed
- ⚙️ **Refined Agent Configuration Loading**: The agent dispatcher now prioritizes configurations provided in a `StartEvent`, then database-persisted configurations, and finally falls back to the `default_agent_config` defined in the runner.
- 💡 **Improved LLM and Embedding Model Specificity**: Agent configurations (e.g., in `RAGAgent`) now utilize more precise type unions for LLMs and embedding models, enhancing type safety and clarity.
- 📈 **API Agent Discovery**: The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- 📄 **Updated RAG Context Language Default**: The default language for newly ingested nodes has been updated from English to German, better aligning with regional configurations.
- ⚡️ **Pipeline Asset Automation**: Automation configurations for document and data lake file removal assets were adjusted from eager conditions to more explicit job-driven scheduling.
- 🔗 **Specialized SharePoint I/O Manager**: The SharePoint observable asset now uses a dedicated `sharepoint_io_manager`, ensuring more appropriate handling of SharePoint data interactions.
- 📚 **Documentation Examples**: Revised agent examples in `aihub_doc/5_agents_in_detail.md` to reflect the updated `AgentConfig` structure and removed `system_prompt`.
- 🔄 **Event Data Flow**: `ChatService` now passes agent configuration data as a dictionary within `UserMessageEvent` for standardized data exchange.
- 🌐 **SDK Updates**: Generated SDK schemas and types now reflect the updated agent configuration model, including removed and added fields.
- 🐛 **ProcessDTO Description**: Corrected a minor typo in the `ProcessDTO` description in the generated SDK.

### Fixed
- 🐛 **Robust Figure Deletion**: Improved the data lake figure deletion process in pipelines by adding an existence check for figures directories, preventing unnecessary errors and log messages when a directory is already absent.
- 🐞 **Azure Profile Image Retrieval**: Corrected error handling when fetching user profile images from Azure Graph Service to gracefully handle 404 responses.
- 📦 **Gunicorn Path in Dockerfile**: Fixed the path to `app.main:app` in `aihub_api/Makefile` for Gunicorn, ensuring correct application startup.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul**: Performed a major refactor of the `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management.
- 🔄 **Consolidated Agent Discovery Architecture**: Unified and streamlined the agent discovery mechanism by introducing distinct class-level and instance-level concepts and consolidating events and topic managers into a single, consistent model.
- 🗄️ **Embedded Agent Configuration Persistence**: Re-architected agent configuration persistence by embedding agent configuration details directly within `AgentEntity` and introducing a reference to `AgentConfigEntityDocument`, enhancing data co-location and simplifying object relationships.
- 📦 **Streamlined Vector Store Integration**: Replaced direct vector store instantiation with a standardized approach using Pydantic configuration models that expose a `.to_llama_index()` method for cleaner integration.
- ⚡️ **Improved Background Task Management**: Centralized management of `asyncio.Task` instances within dispatchers and subscribers to ensure proper lifecycle management and prevent premature garbage collection.
- 🧹 **Renamed Core Services**: Renamed `EventModelCreationService` to `ModelCreationService` and updated its excluded fields to reflect broader utility beyond just event models.
- 🧹 **Consolidated Agent DTOs**: Relocated all agent-related Data Transfer Objects (DTOs) into a dedicated `dto` subdirectory for improved organization and clarity, along with refinements to their encapsulation and persistence logic.
- ⚙️ **Standardized Event Specification Handling**: Updated `EventSpec` creation methods to consistently use `EventSpecs` objects, improving internal data handling.
- 🔗 **Streamlined Topic Inheritance**: `AgentInstanceDiscoveryTopic` now correctly inherits from `AgentClassDiscoveryTopic`, reducing redundancy and clarifying topic structure.
- 🧹 **Cleaned Up Topic Managers**: Removed unused and overlapping topic management methods within `AgentClassTopicManager` for a leaner API.
- 📁 **Test Runner Restructuring**: Reorganized API test runners into a more logical `simulation/agent` and `simulation/process` directory structure.

### Removed
- 🗑️ **Deprecated Agent Configuration Fields**: The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO` as they are now intended to be defined in agent subclasses if needed.
- 🗑️ **Outdated Discovery Events and Topic Managers**: Eliminated legacy class- and instance-specific discovery events and topic managers, as their functionality has been superseded by a new, unified model.
- 🗑️ **Legacy Agent Configuration Persistence Scripts**: Removed the `save_config.py` example script, as direct saving of agent configurations to the database is now handled internally.
- 🗑️ **Redundant Locale String Entity**: Eliminated `LocaleStringEntity`, as localized strings are now managed directly within other persistence models.
- 🗑️ **Specific Pipeline Materialization Jobs**: Removed the `materialize_asset_job` utility from the pipeline factory to simplify job creation and encourage asset-level automation.
- 🗑️ **Outdated Test Files**: Cleaned up several old test files related to agent dispatcher, agent config, and agent service database integration, as their functionalities are now covered by more integrated tests or made obsolete by architectural changes.
- 🗑️ **Redundant `_background_tasks` Sets**: Explicit `_background_tasks` sets were removed from various dispatchers and subscribers as task management is now handled more implicitly by `asyncio.create_task`.
- 🗑️ **Transferred Discovery Event Logic**: Removed the `from_agent_instance` method from `AgentInstanceDiscoveryResponseEvent` as its functionality has been moved to the `AgentInstanceDTO` for better encapsulation.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🐳 **Comprehensive Docker Compose Setups**: Introduced new `docker-compose` files for various deployment environments (e.g., GPU, dev, latest, nightly, local), providing a more flexible and production-ready infrastructure.
- 📦 **New Core Configurations**: Added default configurations for essential services like Milvus, NATS, and PostgreSQL, simplifying environment setup.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- ⚙️ **Streamlined Python Docker Builds**: Optimized Dockerfiles for Python services by refining virtual environment handling and build processes.
- 🌐 **RAG Prompt Enhancements**: Updated the chat role for RAG context prompts from `system` to `user` and corrected image URL handling in English prompts for better model interpretation.
- 💬 **`WorkEvent` Display Handling**: Improved how `WorkEvent` details are displayed by adding new class methods for `display_name` and `display_description`.
- 👥 **`HumanWorkEvent` Overhaul**: Redefined `HumanWorkEvent` to support dynamic form generation and user attribution, enabling more flexible human-in-the-loop interactions.
- 💻 **`ProgramWorkEvent` Attribution**: Added user attribution to `ProgramWorkEvent` for better tracking of who initiated a programmatic action.
- 📈 **Database Indexing Improvements**: Added new database indexes for agent events, thread agents, and user names, enhancing query performance for these entities.
- 📄 **Clarified HTTP 404 Messages**: Updated HTTP 404 error messages for API paths to provide more specific debugging information.
- 📊 **Enhanced Data Lake Logging**: Added a new log statement to output the Data Lake file URI during document parsing, improving observability.
- 📦 **Frontend Dependencies and Build Process**: Updated frontend `package.json` with new Formkit dependencies and adjusted build commands to align with the new `.app` directory structure.
- 🇮🇹 **Italian Localization**: Improved the Italian localization for `ExceptionEvent` messages in the frontend.
- 🌍 **Formkit Locale Integration**: Ensured that dynamically rendered Formkit forms in the frontend correctly reflect the user's selected locale.
- 🚀 **API Deployment with Gunicorn**: Integrated `gunicorn` as a dependency for API and bot services, suggesting a shift towards more robust production server setups.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found, preventing errors.
- 🐞 **Schema Immutability in Evaluation**: Ensured that the `JudgeOutput` schema is deep-copied during evaluation to prevent unintended mutations.
- 💾 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization in `BaseEvent` to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- ✅ **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context, and improved query methods for open work requests.
- 🚦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🧹 **Deprecated Docker Compose File**: An older `docker-compose` file for volume mounting (`docker-compose-mnt.yml`) has been removed.
- ✂️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🌐 **Frontend Directory Rename**: Renamed the internal web development directory from `.playground` to `.app` for consistency.
- 🧽 **Standardized SharePoint Naming**: Consistently renamed variables, parameters, and asset definitions related to SharePoint for improved consistency and readability.
- 🎛️ **Clarified Delegator Fields**: Enhanced Pydantic annotations for delegator fields in `aihub_process` for better clarity.

---



## [v0.227.0] - 2025-07-23 - Improved Azure Identity Service Robustness

### Fixed
- 🖼️ **Azure User Profile Image Fetching**: Enhanced the retrieval of user profile images from the Azure Graph API to be more resilient to various API errors. The service now gracefully handles non-404 errors by logging warnings and consistently returns `None` when an image cannot be fetched, preventing unexpected exceptions and improving stability.

### Refactor
- 🧹 **Import Statement Placement**: Relocated the `asyncio` import to the top-level of the `AzureGraphService` module, aligning with best practices for improved code readability and organization.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Custom Environment Variables for API Deployments**: Enabled custom environment variable injection for API deployments in Azure IaC, allowing users to define and inject additional environment variables, including secret references.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes (e.g., `/events/threads` to `/events/agents/threads`) and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses from 1 to 100 entries, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 📦 **Docker Compose Refinements**: Introduced a new comprehensive `docker-compose.latest.yml` file, consolidating service definitions and streamlining local deployments with various service dependencies.
- 💡 **Adjusted RAG Context Prompt Role**: Changed the chat role for RAG context prompts from `system` to `user` in all supported languages for better model interpretation.
- 🐍 **Python Dependency for Production**: Added `gunicorn` as a direct dependency for API and Bot services, supporting robust production deployments.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer (`AgentEntity`) to gracefully handle cases where a specific agent might not be found, preventing exceptions.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context in `PersistedProcessEventEntity`.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed by `ProcessDiscoveryTopic`.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization in `BaseEvent` to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring images are now correctly referenced and displayed.
- 📝 **External Event Deserialization Robustness**: Improved deserialization logic for `ExternalAgentEvent` to directly extract `thread_id` and `display_id`, enhancing robustness against malformed data.
- 🚧 **Human Delegator Validation**: Implemented validation in `Human.Out` to ensure at least one user targeting method (ID, email, or role) is specified when requesting human input, preventing invalid configurations.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments where appropriate, improving code consistency and Pydantic v2 compatibility.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure for improved test organization.
- 🏗️ **Web UI Project Structure**: Restructured the web UI source code from a generic `.playground` to a more semantically clear `.app` directory for better organization.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Generic External Event Distributor Dependency**: Removed the generic `use_external_event_distributor` dependency, replacing it with more specific agent and process event distributors for clearer separation of concerns.
- 🗑️ **Outdated Docker Compose Mounting File**: Removed `docker-compose-mnt.yml` file, as its functionality is now superseded by new Docker Compose patterns for volume management.
- 🗑️ **Redundant Frontend Health Page**: Removed a basic placeholder health page from the frontend, as core health checks are handled at the API level.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs. This includes new API endpoints for discovery and interaction, dedicated persistence, and real-time event streaming for processes.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Custom Environment Variable Configuration for API Services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 🚀 **New Web Image Build and Release Workflow**: A new GitHub Actions workflow has been added to automate the building and releasing of web application Docker images.
- 📄 **New Infrastructure Configuration Files**: Added new configuration files for Milvus, NATS, and PostgreSQL, enhancing control and configurability of infrastructure deployments.
- 📦 **Simplified Local Production Deployments**: Introduced `docker-compose.latest.yml` for unified, production-ready local deployments, bundling key services.
- 🌐 **Local Development Docker Compose**: Added `swiss-aihub.local.docker-compose.yml` for specific local development environment configurations, including the frontend web service.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses from 1 to 100, improving performance for frequently requested agent lists.
- 🐳 **Streamlined Dockerfile Builds**: Optimized API and Bot Dockerfiles by removing redundant virtual environment copying and internal Poetry installation steps, resulting in more efficient container builds.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages to better align with prompt engineering best practices.
- 📚 **Enhanced API Documentation Clarity**: Improved Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- ⚙️ **Refined `Human` Delegator for Process Interactions**: Expanded the `Human` delegator to support more granular user targeting (by ID, email, role) and notification options for human work requests in agentic processes.
- 🚦 **`ProcessRunner` Now Exposes Detailed Discovery Information**: The `ProcessRunner` has been enhanced to include comprehensive specifications for human, program, and agent inputs (including form definitions) in its `ProcessDiscoveryResponseEvent`.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found, returning `None` instead of raising an exception.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context, including accurate topic field mappings.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization in `BaseEvent` to correctly handle nested Pydantic models and `ChatMessage` objects, preventing data loss or incorrect data transfer.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring images are now correctly referenced and displayed.
- 💅 **Minor CSS and Docstring Typo Fixes**: Corrected a minor CSS syntax issue in the Markdown renderer and fixed a typo in `ProcessTopicManager` docstrings.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🧹 **Deprecated External Event Distributor Dependencies**: Removed outdated `use_external_event_distributor` dependencies, replaced by more specific agent-focused ones.
- 📦 **Removed Old Docker Compose File**: The `docker-compose-mnt.yml` file has been removed, simplifying the local development environment setup.
- ✂️ **Removed Redundant Frontend Health Page**: A basic placeholder health page in the frontend was removed.
- 🗂️ **Deprecated Frontend Playground Directory**: The `.playground` directory and its configuration files have been removed, as the main frontend application now resides in a streamlined `.app` directory.

### Refactor
- 🧹 **Simplified Docstrings Across Components**: Docstrings in numerous core components have been simplified and cleaned up, focusing on concise explanations rather than extensive examples or "why" sections.
- ⚙️ **Pydantic Model Default Handling Alignment**: Aligned Pydantic model definitions across various components (e.g., `QuestionStartEvent`, `CreateRoleRequest`, `JudgeOutput`, Open WebUI SDK models, `DoclingConfig`, `SharePointResource`, `SharePointFile`) by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🔄 **Codebase Naming Standardization**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related assets (`sharepoint_` to `share_point_`), improving clarity and maintainability.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure for better organization and clarity.
- 📚 **Centralized `EventSpecs` Definition**: The `EventSpecs` class has been moved to a more general location in `aihub_lib.nats.events.discovery`, promoting reusability and reducing duplication.
- 🪞 **Refined `AcceptRejectRequest` Type Specificity**: Made class variable types more specific (`AcceptCV` instead of generic `HumanWorkEvent`) in `AcceptRejectRequest` for improved type safety and clarity.
- 🌐 **Frontend Application Directory Restructuring**: Migrated the main frontend application from the `.playground` directory to a new, streamlined `.app` directory for improved project structure.

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



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled custom environment variable configuration for API services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 🚀 **Web Image Build and Release Workflow**: Introduced a new GitHub Actions workflow for building and releasing the web image, improving CI/CD.
- 📦 **New Core Service Configurations**: Added comprehensive configuration files for Milvus and NATS, alongside a PostgreSQL initialization script, facilitating easier deployment and setup of core services.
- 🐳 **New Comprehensive Docker Compose for Latest Deployments**: Introduced a new `docker-compose.latest.yml` file, providing a complete, integrated setup for all core AI Hub services, including MinIO, Milvus, PostgreSQL, OpenWebUI, Phoenix, NATS, Redis, MongoDB, API, and optional LLM/embedding models.
- ⚡️ **Performance Enhancements**: Added new database indexes for agent event, thread, and user entities to improve query performance for common event retrieval patterns.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Caching Enhancements**: Increased the cache size for agent discovery responses and OAuth JSON Web Key Set (JWKS) cache, improving performance for frequently requested data.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related components, improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 📦 **Optimized Docker Image Builds**: Streamlined the Dockerfile for API and Bot services by directly copying the virtual environment from the build stage, reducing image size and build time.
- 🔄 **Frontend Directory Renaming**: Renamed the `.playground` directory to `.app` in the web frontend for clearer project structure.

---



## [bot-v0.217.0] - 2025-07-18 - Consolidating the Platform: Focus on Agent-Centric Workflows

### Added
- 🚀 **Automated Draft PR Creation**: Introduced a new GitHub Actions workflow to automatically create draft pull requests for new branches, streamlining the development process.
- ⚡️ **Added `send_event` to AgentRunner**: Enabled external code to directly trigger new agent runs by sending `StartEvent`s via the `AgentRunner`, simplifying programmatic initiation.
- ✨ **Introduced Unified External Event Distributor**: Added new dependency injection functions (`use_external_event_distributor` and `_ws`) for the consolidated `ExternalAgentEventDistributor`, simplifying its usage.
- ⚡️ **Enabled Two-Way WebSocket Communication**: The `/events/ws` endpoint now supports bidirectional messaging, allowing users to send `ExternalAgentEvent`s in addition to receiving real-time event streams.
- ⚡️ **Implemented WebSocket Event Handling**: Introduced `handle_external_event` to `EventService`, enabling the processing of user-sent WebSocket events and immediate error feedback.
- ✨ **Introduced New LLM Stop Event Output**: Added `LLMStopEventOutput` and `UserMessageEventInput` schemas for richer event details and user input structures in the API.
- ✨ **Added Basic Health Service Page**: Introduced a new `/service/health` page in the web UI for basic service health checks.

### Changed
- 📦 **Optimized Docker Builds for API**: Implemented multi-stage Docker builds for the API service, enhancing build efficiency and reducing image size by copying the virtual environment. Removed `gunicorn` as web server.
- 📈 **Adjusted Agent Discovery Cache Size**: Modified the in-memory cache for discovered agents to `maxsize=1`, impacting how frequently the entire agent list is re-fetched.
- 🔄 **Streamlined Event API Routes**: Renamed `/agents/threads` to `/threads` and `/agents/timeseries` to `/timeseries`, simplifying event-related API paths.
- 📈 **Optimized JWKS Cache for OAuth2**: Adjusted the JWKS cache size in `OAuth2AuthHandler` to `maxsize=1`, focusing on caching the most recently used JWKS.
- 🔄 **Adjusted RAG Context Prompt Role**: Changed the chat role for RAG context prompts from `user` to `system` across all languages for improved model interpretation.
- 🔒 **Stricter Validation for ExternalAgentEvent**: Introduced a mandatory `thread_id` check during deserialization of `ExternalAgentEvent`, improving data integrity.
- 🔄 **Centralized EventSpecs Definition**: The `EventSpecs` class, which defines event schemas, has been moved and is now part of `AgentDiscoveryResponseEvent` for a more logical grouping.
- 🗄️ **Optimized Event Persistence Indexes**: Removed specific database indexes on `display_id` and compound `thread_id`/`event_type`/`event_parents` fields in `PersistedAgentEventEntity`, potentially improving write performance.
- 🗄️ **Optimized Thread Entity Indexes**: Removed the compound index on `agents.agent_id` and `agents.agent_class` in `ThreadEntity`, potentially improving write performance.
- 🗄️ **Optimized User Entity Indexes**: Removed the index on the `name` field in `UserEntity`, potentially improving write performance.
- 📦 **Optimized Docker Builds for Bots**: Implemented multi-stage Docker builds for the Bot service, enhancing build efficiency and reducing image size. Removed `gunicorn`.
- 📈 **Optimized JWKS Cache for OAuth2**: Adjusted the JWKS cache size in `OAuth2AuthHandler` to `maxsize=1`, focusing on caching the most recently used JWKS.
- 📦 **Optimized Docker Builds for Bots**: Implemented multi-stage Docker builds for the Bot service, enhancing build efficiency and reducing image size.
- 🔄 **Refined Chat Message Schemas**: Introduced distinct `_Input` and `_Output` suffixes for `AssistantChatMessage`, `ChatMessage`, and `UserChatMessage` to clearly delineate their usage contexts.
- ⚙️ **Updated Web UI Development Scripts**: Modified `dev`, `build`, and `preview` scripts to target the new `.playground` directory.
- ⬆️ **Updated Frontend Peer Dependencies**: Bumped `primevue` and `vue` peer dependency versions for the web UI.

### Fixed
- 🖼️ **Fixed Image Path in English RAG Prompt**: Corrected the image rendering logic in the English RAG context prompt to use `block.path` for accurate image display.
- 🐛 **Improved Event Serialization Consistency**: Ensured consistent serialization of events to JSON by directly using `json.dumps(event.model_dump())`, which was previously causing issues with `serialize_as_any`.
- 🐛 **Improved Event Serialization for Testing**: Updated test cases to use `json.dumps(event.model_dump())` for event serialization, ensuring accurate and consistent behavior during testing.
- 🐛 **Stricter Agent Retrieval**: Changed agent retrieval from `first()` to `get()` in `AgentEntity`, ensuring an error is raised if a specific agent is not found, preventing unexpected `None` returns.
- 🐛 **Corrected Process Pluralization**: Fixed a minor typo in docstrings by changing "all processes" to "all processs" for pluralization consistency.

### Removed
- 🗑️ **Removed Dedicated Web Build Workflow**: Deprecated the standalone `build-web.yml` workflow, indicating a consolidation or update of the web image build and release process.
- 🗑️ **Removed Gunicorn Dependency**: Eliminated the `gunicorn` dependency from `aihub_api` and `aihub_bot`, as it is no longer used for serving the applications.
- 🗑️ **Removed Process Management API**: Fully deprecated and removed the `/processes` API endpoints and `ProcessController`, indicating a shift away from direct external interaction with process orchestration via the API.
- 🗑️ **Removed Process Service Logic**: Eliminated `ProcessService`, which previously handled business logic for process discovery, form management, and event distribution.
- 🗑️ **Removed Process-Related DTOs**: Deleted all Data Transfer Objects (DTOs) specifically designed for process management, including `ProcessConfigDTO`, `ProcessDTO`, `ProcessHumanInDto`, and `SubmittedFormDTO`.
- 🗑️ **Removed Process Access from User Dashboard**: User access levels for processes are no longer displayed in the `UserWithAccessDTO`, aligning with the deprecation of direct process API interaction.
- 🗑️ **Removed Process Controller Integration**: The `ApiRunner` no longer initializes or integrates the `ProcessController`, aligning with the deprecation of direct process API endpoints.
- 🗑️ **Removed Process Simulation Infrastructure**: Eliminated the entire `simulation/process` directory, including `SimulatedProcessApiTestRunner` and its associated mock event definitions, as direct process API interaction has been deprecated.
- 🗑️ **Removed Generic Endpoint Discovery Service**: Deprecated and removed the `EndpointsDiscoveryService` abstract base class, as its functionality has been integrated directly into specific discovery services.
- 🗑️ **Removed Process Endpoint Discovery Service**: Eliminated `ProcessEndpointsDiscoveryService`, which handled dynamic registration of API endpoints for processes, aligning with the deprecation of direct process API interaction.
- 🗑️ **Removed Process-Specific WebSocket Event Model**: Eliminated `ContextualizedProcessEvent`, consolidating all server-to-user WebSocket events under a single, unified agent event model.
- 🗑️ **Removed External Agent Event Distributor Dependencies**: Eliminated the specific dependency injection functions for `ExternalAgentEventDistributor` as part of the refactoring to a unified distributor.
- 🗑️ **Removed External Process Event Distributor**: Eliminated `ExternalProcessEventDistributor`, which previously handled distributing external events to processes, as this functionality is no longer directly exposed.
- 🗑️ **Removed External Process Event Distributor Dependencies**: Eliminated dependency injection functions for `ExternalProcessEventDistributor` due to its removal.
- 🗑️ **Removed External Process Event Model**: Eliminated `ExternalProcessEvent` as part of the deprecation of direct process API interaction.
- 🗑️ **Removed Specific Work Event Properties**: Eliminated `is_human_work_event` and `is_program_work_event` properties from `BaseEvent`.
- 🗑️ **Relocated EventSpecs Definition**: The `EventSpecs` model has been moved and is now defined directly within `AgentDiscoveryResponseEvent` for better contextualization.
- 🗑️ **Simplified Process Discovery Response**: Removed `human_inputs`, `program_inputs`, and `agent_inputs` fields from `ProcessDiscoveryResponseEvent`, streamlining the process discovery response.
- 🗑️ **Removed Process Input Specification Models**: Eliminated `AgentInSpecs`, `HumanInSpecs`, and `ProgramInSpecs` models, which defined how different entities could provide input to processes.
- 🗑️ **Removed Dynamic Form Generation**: Deprecated and removed the entire dynamic form generation capability, including `Form` models and `Formkit` elements, which previously allowed processes to define and expose forms for human input.
- 🗑️ **Removed Process Discovery Response Subscriber**: Eliminated the `for_process_discovery_response_events` subscriber, as process discovery responses are no longer handled as distinct events.
- 🗑️ **Removed Process Entity Models**: Eliminated `ProcessEntity` and all its associated embedded document models, completely deprecating the direct persistence of process definitions in the database.
- 🗑️ **Removed Process Management Composables**: Eliminated `useProcess` and `useProcesses` composables, aligning with the deprecation of direct process API interaction.
- 🗑️ **Removed Formkit Locale Integration**: Eliminated Formkit-specific locale change logic from `UserSettings.vue`, aligning with the deprecation of Formkit from the web UI.
- 🗑️ **Removed Formkit Nuxt Module**: Eliminated the `@sfxcode/formkit-primevue-nuxt` module integration from `nuxt.config.ts`, completing the deprecation of Formkit in the web UI.
- 🗑️ **Removed Formkit Dependencies**: Eliminated Formkit-related development dependencies from `package.json`, confirming its removal.
- 🗑️ **Removed Custom API Environment Variables**: Deprecated and removed the `additional_env_vars` configuration from `ApiConfig`, which previously allowed injecting custom environment variables into API deployments.
- 🗑️ **Removed Process API Test Suite**: Eliminated the entire test suite for process API interactions, including fixtures and scenario tests, aligning with the deprecation of direct process API endpoints.
- 🗑️ **Removed Process-Specific Query Methods**: Eliminated `get_open_human_work_requests` and `find_request_for_work_event` methods, as process-specific event querying is no longer supported.
- 🗑️ **Removed Playground-Specific Work Events**: Eliminated `AgentAWorkRequest`, `HumanAWork`, `HumanBWork`, and `HumanBWorkRequest` events from the playground examples, as their underlying models have been simplified or deprecated.
- 🗑️ **Removed Agent-Only Process Runner**: Eliminated the `agent_only_process` playground runner, as its example scenario is no longer relevant to the simplified process interaction model.
- 🗑️ **Removed Legacy Process Interaction Examples**: Eliminated `agent_to_human_process`, `human_only_process`, and `human_to_agent_process` examples and their associated test suites, as they are no longer compatible with the simplified process interaction model.
- 🗑️ **Removed Frontend Config Loader**: Eliminated the client-side configuration loader and its related `config.json` and `config.template.json` files, simplifying frontend environment management.
- 🗑️ **Removed Nginx Configuration for Web UI**: Deprecated and removed the Nginx configuration file for serving the web UI, indicating a shift in deployment strategy.
- 🗑️ **Removed Formkit Configuration**: Eliminated `formkit.config.ts`, confirming the removal of Formkit-based dynamic forms from the web user interface.
- 🗑️ **Removed Processes Overview Page**: Eliminated the `/service/processes` page from the web UI, as direct process management through the UI has been deprecated.

### Refactor
- ⚙️ **Refined Default Locale Handling**: Explicitly set the default locale to "en" within `QuestionStartEvent` using Pydantic's `default` argument for clarity.
- 📄 **Enhanced ThreadContext Documentation**: Added detailed explanations to the `ThreadContext` class, clarifying its purpose, features, and providing usage examples.
- 🧹 **Consolidated Event Sending Logic**: Moved the `send_event` method from `AgentTestRunner` to its parent class `AgentRunner` to centralize event sending functionality.
- 📄 **Improved RunTraceCoordinator Documentation**: Enhanced the docstrings for `RunTraceCoordinator` to better explain its role in OpenTelemetry-based tracing and its key features.
- 🧹 **Standardized EventSpecs Import**: Updated `EventModelCreationService` to import `EventSpecs` from the centralized `AgentDiscoveryResponseEvent` module for consistency.
- 📄 **Enhanced EventPersister Documentation**: Added detailed docstrings to `EventPersister`, explaining its purpose, features, and usage for clearer understanding.
- ✂️ **Simplified Event Persistence**: Consolidated event persistence logic under a single `persist_event` method, removing the distinction between agent and process events in the API's persistence layer.
- 🧹 **Streamlined AgentDTO Conversion**: Removed the `is_online` parameter from `AgentDTO` factory methods, simplifying the data transfer object creation.
- 📄 **Enhanced AgentService Documentation**: Improved `AgentService` docstrings with detailed explanations of its purpose, operations, and caching mechanisms.
- 🧹 **Standardized EventSpecs Import**: Updated `AgentDTO` to import `EventSpecs` from the centralized `AgentDiscoveryResponseEvent` module.
- 📄 **Improved AgentDTO Documentation**: Added docstrings to `AgentDTO` explaining its purpose in standardizing API responses.
- 🧹 **Renamed External Event Distributor Dependency**: Updated imports and parameter names from `use_external_agent_event_distributor` to `use_external_event_distributor` for consistency.
- 📄 **Enriched EvaluationController Documentation**: Added detailed docstrings outlining the controller's purpose and authentication requirements.
- 🧹 **Standardized External Event Distributor Usage**: Renamed `external_agent_event_distributor` to `external_event_distributor` in `EvaluationService` for consistent API usage.
- 📄 **Comprehensive EvaluationService Documentation**: Added detailed docstrings and section headers to `EvaluationService`, improving clarity on its responsibilities and internal organization.
- 📄 **Enhanced EventController Documentation**: Added detailed docstrings to `EventController`, explaining its dual role in historical and real-time event management.
- 🔄 **Unified WebSocket Event Types**: Updated `get_user_events` and `event_websocket_connection` to use `WSServerEvent`, standardizing event representation for WebSocket clients.
- 📄 **Improved EventService Documentation**: Provided comprehensive docstrings for `EventService`, detailing its role in event retrieval, external event handling, and error management.
- 🧹 **Standardized External Event Distributor Usage**: Renamed `use_external_agent_event_distributor` to `use_external_event_distributor` in `OpenaiController` for consistent dependency injection.
- 📄 **Expanded OpenaiController Documentation**: Added detailed docstrings to `OpenaiController`, clarifying its purpose in emulating the OpenAI API and its key design intentions.
- 📄 **Clarified OpenaiService Purpose**: Added docstrings to `OpenaiService` detailing its core operations and mirroring of OpenAI's API functionality.
- ⚙️ **Refined Role Creation Defaults**: Explicitly set the default for `access_rules` in `CreateRoleRequest` to an empty list, improving API schema clarity.
- 📄 **Comprehensive ThreadController Documentation**: Added detailed docstrings to `ThreadController`, explaining its purpose, specific endpoints, authentication model, and providing usage examples.
- 📄 **Improved ThreadService Documentation**: Provided detailed docstrings for `ThreadService`, clarifying its business logic and responsibilities within thread operations.
- 🧹 **Standardized WebSocket Event Types**: Updated event conversion in `thread_as_message_history` to use `WSServerEvent` for consistency.
- 🧹 **Renamed Agent Simulation Runner**: Moved and renamed `SimulatedAgentApiTestRunner` to a more central location.
- 🧹 **Updated Agent Discovery Service Reference**: Aligned usage with the renamed `AgentDiscoveryService` for consistency.
- 🧹 **Consolidated Event Distributors**: Replaced `ExternalProcessEventDistributor` with `ExternalAgentEventDistributor` to unify event distribution.
- 🧹 **Unified Event Persistence**: Migrated process event persistence to use `AgentNCSubscriber`, storing all events as agent events.
- 🧹 **Renamed and Refactored Agent Discovery Service**: `AgentEndpointsDiscoveryService` was renamed to `AgentDiscoveryService` and refactored to encapsulate its own discovery loop logic, removing its dependency on the now-removed `EndpointsDiscoveryService`.
- 🧹 **Renamed WebSocket Event Model**: `ContextualizedAgentEvent` was renamed to `WSServerEvent` to reflect its broader role as a generic server-to-user event container.
- 📄 **Enhanced WSServerEvent Documentation**: Added detailed docstrings to `WSServerEvent`, explaining its purpose and conversion from persisted events.
- 🧹 **Standardized WebSocket Event Types in Manager**: Updated `WebSocketManager` to use `WSServerEvent` and renamed `send_agent_event` to `send_event` for consistency.
- 📄 **Improved WebSocketManager Documentation**: Added comprehensive docstrings, including explanations of its purpose, usage, and examples.
- 🧹 **Standardized External Event Distributor Import**: Updated `WebSocketManager` dependencies to use the new `use_external_event_distributor` name.
- 🧹 **Standardized WebSocket Event Types in Sender**: Updated `WebSocketSender` to use `WSServerEvent` for consistent event handling.
- 📄 **Improved WebSocketSender Documentation**: Added detailed docstrings, explaining its purpose, event flow, and providing usage examples.
- 🧹 **Updated Simulated Agent Runner Imports**: Test files referencing `SimulatedAgentApiTestRunner` were updated to reflect its new location.
- ⚙️ **Refined JudgeOutput Default**: Explicitly set the default for the `error` field in `JudgeOutput` to `False` using Pydantic's `default` argument.
- 🧹 **Standardized External Event Distributor Usage**: Renamed `external_agent_event_distributor` to `external_event_distributor` within `PhoenixExperimentEvaluator` for consistent dependency naming.
- ⚙️ **Optimized Schema Copying**: Removed unnecessary `deepcopy` calls for `JudgeOutput` schema, improving efficiency.
- ⚙️ **Clarified Optional Fields in OpenAPI Models**: Explicitly added `default=None` or `default=False` to numerous optional fields across Open WebUI SDK models (chats, files, knowledge, users), enhancing clarity in the generated OpenAPI schema.
- ⚙️ **Refined DoclingConfig Defaults**: Explicitly set default values for `DOCLING_IMAGE_EXPORT_MODE`, `DOCLING_DO_OCR`, and `DOCLING_FORCE_OCR` in `DoclingConfig` for clearer configuration.
- 📄 **Comprehensive ExternalAgentEventDistributor Documentation**: Added detailed docstrings to `ExternalAgentEventDistributor`, outlining its purpose, key responsibilities, event flow, and providing usage examples.
- 🧹 **Standardized Pydantic Annotations**: Updated `event_id` and `created_at` to use `Annotated` for consistency.
- 🧹 **Streamlined WorkEvent Definition**: Simplified `WorkEvent` by removing specific default value setters and display name/description class methods, making it a more focused base class.
- 🧹 **Simplified HumanWorkEvent**: Removed `Form` inheritance and the `submitted_by` field from `HumanWorkEvent`, making it a simpler, more abstract work event base, aligning with the removal of dynamic form generation.
- 🧹 **Simplified ProgramWorkEvent**: Removed the `submitted_by` field from `ProgramWorkEvent`, streamlining its definition.
- 🧹 **Simplified HumanWorkRequestEvent**: Removed complex form validation and fields (`endpoint`, `method`, `user_emails`, `user_roles`, `notify`, `forms`), streamlining `HumanWorkRequestEvent` to a simpler event marker.
- 🧹 **Simplified ProgramWorkRequestEvent Fields**: Made `endpoint` and `method` fields optional in `ProgramWorkRequestEvent`, reducing their strictness.
- 📄 **Improved AgentDiscoveryTopic Documentation**: Added detailed docstrings to `AgentDiscoveryTopic`, clarifying its purpose in agent-specific discovery.
- 🧹 **Simplified ProcessDiscoveryTopic**: Removed extensive docstrings and adjusted internal assertions to rely on a more generic `TopicManager`, streamlining its definition.
- 🧹 **Re-purposed Process Event Persistence Entity**: `PersistedProcessEventEntity` has been re-purposed to store events using agent-centric topic details, effectively consolidating process events under the agent event model.
- ⚙️ **Refined SPA Route Not Found Message**: Simplified the HTTP 404 detail message for SPA routes to "Not Found" for better consistency.
- 🧹 **Standardized SharePoint Naming**: Renamed client, file, and function parameters from `share_point_` to `sharepoint_` within `observable_share_point_factory` for naming consistency.
- 🧹 **Standardized SharePoint Naming**: Renamed factory function and file parameters from `share_point_` to `sharepoint_` within `sharepoint_files_to_data_lake_files_factory` for naming consistency.
- 🧹 **Standardized SharePoint Naming**: Renamed client and file parameters from `share_point_` to `sharepoint_` within `SharePointIOManager` for naming consistency.
- ⚙️ **Refined Data Lake Parsing Logging**: Removed a redundant log statement for Data Lake file URI during document parsing to streamline logging output.
- 🧹 **Standardized SharePoint Naming**: Renamed file parameters and metadata table function from `share_point_` to `sharepoint_` within `data_version_by_partition_for_share_point_files_no_op` for naming consistency.
- 🧹 **Standardized SharePoint Naming**: Renamed file parameter from `share_point_file` to `sharepoint_file` within `extract_content_from_share_point_file` for naming consistency.
- 🧹 **Standardized SharePoint Naming**: Renamed file and parameter from `share_point_` to `sharepoint_` within `extract_metadata_from_sharepoint_file` for consistent naming.
- ⚙️ **Refined SharePointResource Defaults**: Explicitly set default `None` values for `target_folders` and `exclude_folders` in `SharePointResource` for clearer configuration.
- ⚙️ **Refined SharePointFile Defaults**: Explicitly set default `None` values for `content_type` and `download_url` in `SharePointFile` for clearer type definitions.
- 🧹 **Standardized SharePoint Naming**: Renamed functions from `share_point_` to `sharepoint_` within metadata utility functions for naming consistency.
- 🧹 **Simplified Agent Delegator Definitions**: Streamlined `Agent.In` and `Agent.Out` class attributes by removing verbose `Annotated` and `Field` declarations, and condensed docstrings for brevity.
- 🧹 **Simplified Human Delegator Definitions**: Drastically streamlined `Human.In` and `Human.Out` classes by removing explicit form handling, user/role targeting, and notification configurations, reducing complexity.
- 🧹 **Simplified Process Delegator Definitions**: Streamlined `Process.In` and `Process.Out` class attributes by removing verbose `Annotated` and `Field` declarations.
- 🧹 **Streamlined Human Work Request Dispatching**: Simplified the dispatching of `HumanWorkRequestEvent` by consolidating user targeting to a single `event.users` field, aligning with the updated `Human.Out` definition.
- 🧹 **Simplified ProcessRunner Discovery Responses**: Streamlined the `ProcessRunner`'s discovery handler by removing detailed input specifications (`human_inputs`, `program_inputs`, `agent_inputs`), aligning with the simplified process API.
- 🧹 **Streamlined ProcessTestRunner**: Drastically simplified `ProcessTestRunner` by removing redundant event sending methods (`send_event`, `send_event_from_topic`) and topic-centric event retrieval, streamlining test capabilities.
- 🧹 **Simplified AgenticCVProcess Steps**: Updated `AgenticCVProcess` to align with the streamlined `Human.Out` definition, removing explicit form instantiation and related `InputTextElement` usage.
- 🧹 **Simplified AnalyzedCV Event**: Removed the `cv_name` field from the `AnalyzedCV` event, streamlining its data structure.
- 🧹 **Simplified Human Response Events**: Streamlined `AcceptCV` and `RejectCV` events by changing the `reason` field type to a simple string, aligning with the removal of explicit form elements.
- 🧹 **Generalized AcceptRejectRequest**: Updated `AcceptRejectRequest` to use a more generic `HumanWorkEvent` type for its `accept` and `reject` class variables, enhancing flexibility.
- 🧹 **Standardized SharePoint Naming**: Renamed file and parameter from `share_point_` to `sharepoint_` within `extract_metadata_from_sharepoint_file` for consistent naming.
- 🧹 **Updated Gitignore for Playground Directory**: Modified `.gitignore` to exclude build artifacts from the new `.playground` directory.
- 🧹 **Standardized WebSocket Event Types in UI Components**: Updated numerous Vue components to consistently use `WsServerEventReadable` instead of `WsServerAgentEventReadable`, reflecting the unified server-to-user WebSocket event model.
- 🧹 **Standardized WebSocket Event Types in Composables**: Updated `useAgentIconFromThread` and `useEventComponent` composables to consistently use `WsServerEventReadable`.
- 🧹 **Standardized Event Timeseries API Usage**: Updated `useEventTimeseries` composable to use the new `/events/timeseries` endpoint, reflecting the simplified event API.
- 🧹 **Standardized Thread Events API Usage**: Updated `useThreadEvents` composable to use `getEventsInThread` and `WsServerEventReadable`, reflecting the unified event API.
- 🧹 **Standardized WebSocket Event Types in Thread Utilities**: Updated `useThreadUtils` composable to consistently use `WsServerEventReadable`.
- ⚙️ **Refined ExceptionEvent Localization**: Removed a redundant label for `ExceptionEvent` in the Italian localization file.
- 🧹 **Standardized WebSocket Event Types in Sources Page**: Updated the sources page to consistently use `WsServerEventReadable` for event data.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled Custom Environment Variable Configuration for API Services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 📦 **New Docker Compose Files and Configurations**: Introduced new Docker Compose files for more structured and flexible development and deployment setups, including new default configurations for Milvus, NATS, and PostgreSQL.
- 🐳 **New Web Dockerfile and Nginx Setup**: Added a new multi-stage Dockerfile for the web application and an Nginx configuration, optimizing web deployment.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- ⚙️ **Optimized Dockerfile for Microservices**: Streamlined Dockerfiles for `aihub_api` and `aihub_bot` by refining virtual environment handling during build.
- ⚙️ **Enhanced Logging for Data Lake Document Parsing**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- ⚙️ **Refined `WorkEvent` Default Handling**: Enhanced `WorkEvent` with a model validator to automatically set display metadata and new properties for clearer event classification.
- ⚙️ **Improved `Human` Delegator Configuration**: Enhanced the `Human` delegator to support detailed audience targeting (user IDs, emails, roles), notification options, and the inclusion of an initial form for process start events.
- ⚙️ **Updated `ProcessDispatcher` for Human Inputs**: Updated `ProcessDispatcher` to correctly assign new user targeting and notification parameters for `HumanWorkRequestEvent`.
- ⚙️ **Expanded Process Runner for Discovery**: Extended `ProcessRunner` to dynamically generate and include detailed human, program, and agent input specifications in `ProcessDiscoveryResponseEvent`.
- ⚙️ **Enhanced `HumanWorkRequestEvent` Validation**: Significantly enhanced `HumanWorkRequestEvent` to support detailed audience targeting and dynamic form definitions, ensuring strict validation against expected work event types.
- ⚙️ **Improved Agent Entity Persistence**: Ensured `network_graph` is always stored as a dictionary in `AgentEntity`.
- ⚙️ **Enhanced Database Indexes**: Added new database indexes across `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance.
- ⚙️ **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly converting their URL object to a string representation.
- 🐞 **Missing Italian Translation for ExceptionEvent**: Added missing translation for the `ExceptionEvent` label in Italian.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), event types, and associated components, improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.
- 📦 **Frontend Application Directory Restructure**: Migrated Nuxt application configuration and source from `.playground` to a new `.app` directory for production readiness.

### Removed
- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Generic Event Distributor**: Removed the generic `use_external_event_distributor` in favor of more specific agent and process-scoped distributors.
- 🗑️ **Old Docker Compose Mount Configuration**: Removed the `docker-compose-mnt.yml` file, likely superseded by new, more structured Docker Compose configurations.

---



## [web-v0.222.0] - 2025-07-21 - Full-Stack Deployment and Streamlined Agent Architecture

### Added
- 🚀 **Full-Stack Containerization**: Introduced comprehensive Docker Compose configurations for streamlined deployment of API, Bot, and Web components, including MinIO, Milvus, PostgreSQL, Redis, MongoDB, and NATS.
- ⚙️ **New Service Dockerfiles**: Added dedicated Dockerfiles for building production-ready Docker images of API, Bot, and Web services using multi-stage builds and Gunicorn for Python services.
- 🌐 **Web Frontend Production Setup**: Implemented a robust Nginx-based Docker setup for the web UI, enabling static file serving, runtime configuration loading, and optimized caching.
- 📦 **Core Component Applications**: Introduced `app/main.py` entrypoints and new settings classes (`ApiRunnerSettings.py`, `BotRunnerSettings.py`) for API and Bot services, centralizing application bootstrapping and configuration.
- 📄 **New Database & Messaging Configurations**: Included detailed configuration files for Milvus (`milvus.yaml`), NATS (`nats.conf`), and a PostgreSQL initialization script (`init-multiple-dbs.sh`), supporting the new Docker Compose environments.
- 🧪 **OpenWebUI Integration for Local Dev**: Added a `docker-compose-webui-mnt.yml` for simplified local development of OpenWebUI with volume mounts.
- 🚀 **Automated Build Workflows**: Introduced new GitHub Actions workflows (`build-api-and-bot.yml`, `build-web.yml`) to automate the build and release of Docker images for API, Bot, and Web services.

### Changed
- ⚙️ **Refined Agent Configuration Model**: Revised the `AgentConfig` structure by removing the `agent_class` field, making `agent_id` the primary instance identifier. Added `system_prompt`, `color`, and `voice` attributes to the base configuration for broader applicability (though deprecated for future removal).
- 💡 **Unified LLM and Vector Store Configurations**: Agent configurations now utilize consolidated base types (`ChatLLMConfig`, `EmbeddingLLMConfig`, `BasePydanticVectorStore`) for LLMs, embedding models, and vector stores, enhancing type safety and abstraction.
- 🚧 **Streamlined StartEvent**: The `StartEvent` no longer directly carries agent configuration, simplifying event payload and centralizing configuration management within the agent dispatcher.
- 🔗 **Simplified RAG Node Combining**: The `combine_nodes_in_order` utility for RAG context now omits HTML-like tags (e.g., `<h1>`, `<content>`) and uses simpler text formatting, reducing prompt complexity.
- ⚡️ **CI/CD Workflow Enhancements**: Updated GitHub Actions build workflows for Docker images to allow optional `ssh_key` usage.
- 📚 **Documentation and SDK Updates**: Revised agent examples in documentation and updated the generated API SDK to reflect the new `AgentConfig` structure, including the removal of `agent_class` and the addition of `system_prompt`, `color`, and `voice`.
- 📊 **Pipeline Automation Triggers**: Updated pipeline assets for document and data lake file removal to use `AutomationCondition.eager()`, ensuring data cleanup tasks are triggered more responsively.
- 📦 **Pipeline I/O Manager**: The SharePoint observable asset now uses `data_lake_io_manager` for more consistent interaction with the data lake.
- 🌐 **Web Frontend Build Configuration**: The Nuxt build configuration was moved and adjusted to explicitly differentiate development and production runtime configurations for OIDC, WebUI, and WebSocket endpoints.
- ⬆️ **Dependency Updates**: Updated `primevue` and `vue` versions in the web application's `package.json`.

### Fixed
- 🐛 **Robust Figure Deletion in Pipelines**: Improved the data lake figure deletion process in pipelines by removing a redundant existence check, preventing potential errors when a figures directory is already absent.
- 💬 **Localization for Exception Events**: Added a missing translation label for `ExceptionEvent` in the Italian locale.
- ℹ️ **Process DTO Description Typo**: Corrected a minor typo in the `ProcessDTO` description in the generated SDK.

### Removed
- 🗑️ **Legacy Agent Configuration Persistence**: Eliminated standalone MongoDB documents and embedded documents for agent configurations, consolidating persistence directly within the `AgentEntity`. Also removed the `save_config.py` example script.
- 🗑️ **Deprecated Discovery Events and Topic Managers**: Removed old class- and instance-specific discovery events and topic managers, unifying agent discovery under a single, simplified model.
- 🗑️ **Legacy Pydantic Vector Store Configs**: Removed explicit Pydantic models for vector store configurations, which are now replaced by direct factory functions.
- 🗑️ **Obsolete Model Creation Service**: Removed `ModelCreationService`, replaced by `EventModelCreationService` for a more focused approach to event model generation.
- 🗑️ **Dedicated Locale String Entity**: Removed `LocaleStringEntity`, as localized strings are now handled more directly within other models.
- 🗑️ **Specific Pipeline Jobs**: Removed the `materialize_asset_job` utility from the pipeline factory and associated playground jobs, simplifying job creation and encouraging asset-level automation.
- 🗑️ **Outdated Test Files**: Cleaned up several old test files related to agent dispatcher, agent config, and agent service database integration, as their functionalities are now covered by more integrated tests or made obsolete by architectural changes.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul**: Performed a major refactor of the `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management by removing explicit `_background_tasks` sets.
- 🔄 **Unified Agent Discovery**: Consolidated and streamlined the agent discovery mechanism by merging class and instance-level discovery events and topic managers into a single, consistent model.
- 🗄️ **Embedded Agent Persistence**: Re-architected agent configuration persistence by embedding agent configuration directly within `AgentEntity`, enhancing data co-location and simplifying object relationships.
- 📦 **Streamlined Vector Store Integration**: Replaced explicit vector store configuration objects with direct factory functions for cleaner instantiation and use.
- 📁 **Project Structure Alignment**: Renamed `aihub_web/aihub_web/.playground` to `aihub_web/aihub_web/.app` to better reflect its role as the primary application directory. Also reorganized API test runners into `simulation/agent` and `simulation/process` directories.
- 🧹 **Internal API Naming Consistency**: Renamed the internal `_get_endpoint_base_path` to `_get_endpoint_name` in endpoint discovery services for improved clarity and consistency.

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



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled custom environment variable configuration for API services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.
- 📦 **Complete Local Deployment Stack**: Added new `docker-compose.latest.yml` providing a full local deployment including MinIO, Milvus, Postgres, OpenWebUI, and AI Hub services.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🐳 **Improved Docker Build Processes**: Refactored Dockerfiles for `aihub_api` and `aihub_bot` to optimize image size and build efficiency, including using `gunicorn` for serving and streamlining dependency installation.
- ⚙️ **Process Delegator Configuration**: Updated `Human` delegator configuration to support richer user-based targeting (user IDs, emails, roles) and notification options for human-in-the-loop requests.
- 📈 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices and enhance model interpretation of contextual information.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 💅 **Frontend Markdown Renderer Styling**: Corrected minor CSS issues in the Markdown renderer to ensure consistent display of headings.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue where image URLs in RAG prompts were not consistently processed, ensuring images are correctly referenced.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- ✂️ **Frontend Build Environment Migration**: Migrated the frontend development and build environment from `.playground` to `.app`, streamlining project structure.
- 🧼 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Docker Compose File**: Removed the `docker-compose-mnt.yml` file, simplifying local deployment options.
- 🗑️ **Redundant Frontend Health Page**: A basic placeholder health page (`pages/service/health.vue`) in the frontend was removed.

---



## [v0.217.0] - 2025-07-18 - Agent-Centric Refocus & Infrastructure Streamlining

### Added
- ✨ **Automated Draft Pull Request Creation**: Introduced a new GitHub Actions workflow to automatically create draft pull requests for new branches, streamlining development and ensuring consistent PR titles.
- ⚡️ **External Event Triggering for Agent Runs**: Implemented a new `send_event` method in `AgentRunner` to allow external systems to programmatically initiate agent runs with a `StartEvent`.
- ✨ **Introduced Generalized External Event Distributor Dependency**: Created a new `use_external_event_distributor` dependency for consistent access to event distribution functionality across the API and bots.
- 🚀 **Real-time User Event Processing**: Transformed the API's event WebSocket endpoint (`/ws`) to support bi-directional communication, enabling users to send commands and receive real-time event streams from agents.
- 🚀 **Self-Managing Agent Endpoint Discovery**: The `AgentDiscoveryService` now autonomously discovers and registers/deregisters agent API endpoints on a periodic interval, improving API dynamism.
- ✨ **Added Basic Health Service Page**: Introduced a new, simple health service page in the frontend for basic status checks.
- ✨ **New Consolidated Local Development Environment**: Introduced a new `docker-compose-mnt.yml` for local development, providing persistent volume mounts for all core services including Phoenix, NATS, Redis, Mongo, and local LLM/embedding models.
- 🚀 **Introduced Dynamic Agent Event Sending**: Added a new client endpoint for sending events to dynamically discovered agent endpoints, enabling more direct interaction from the frontend.

### Changed
- 📚 **Enhanced Documentation Across Core Components**: Significantly improved docstrings and inline comments for various services and models including `ThreadContext`, `RunTraceCoordinator`, `AgentService`, `EvaluationService`, `EventController`, `ThreadController`, `ExternalAgentEventDistributor`, `AgentDiscoveryTopic`, `AgentDiscoveryService`, `WebSocketManager`, and `WebSocketSender` for better clarity and understanding.
- 📦 **Optimized Docker Images**: Reworked Dockerfiles for API and Bot services (`aihub_api` and `aihub_bot`) to install Poetry dependencies `--no-root` and copy the virtual environment, leading to smaller and more efficient container images.
- ⚡️ **Adjusted Agent Discovery Caching**: Modified the `DISCOVER_AGENTS_CACHE` max size to potentially increase the frequency of agent re-discovery, aiming for quicker reflection of live agent status.
- ⚡️ **Improved Agent Status Reflection**: Adjusted `AgentDTO` creation to accurately reflect the `is_online` status of agents, removing redundant explicit `False` assignments in `AgentService`.
- ⚡️ **Optimized JWKS Caching**: Reduced `_jwks_cache` size to 1 in `OAuth2AuthHandler`, ensuring more frequent fetching of JSON Web Key Sets for enhanced security and freshness.
- 🔄 **Updated RAG Context Prompt Role**: Changed the chat role for the RAG context prompt from `user` to `system` in all supported languages (German, English, French, and Italian) for better alignment with prompt engineering practices.
- 🔒 **Strict Validation for External Agent Events**: Added a mandatory check for `thread_id` during `ExternalAgentEvent` deserialization to ensure proper event routing and prevent errors.
- 📚 **Simplified API Route Not Found Message**: Shortened the HTTP 404 detail message for API routes in `Runner`, making it more generic.
- 💥 **Stricter Agent Retrieval Behavior**: Modified `AgentEntity.get_agent` to use `get()` which raises an exception if an agent is not found, providing clearer error handling.
- 🔄 **Flexible Agent Network Graph Storage**: Changed `network_graph` in `AgentEntity` to be stored as a flexible dictionary rather than a rigid embedded document, improving adaptability.
- ⚙️ **Standardized Frontend Configuration**: Updated the Nuxt.js configuration in the new `.playground` directory to directly use environment variables and hardcode local endpoints for development simplicity.
- ⚡️ **Client-Side Rendering Enabled**: Configured Nuxt.js for client-side rendering only (`ssr: false`), optimizing frontend load.

### Fixed
- 🐛 **Fixed RAG Image URL Handling**: Corrected an issue in the English RAG context prompt (`en.yml`) to ensure image URLs are properly referenced using `block.path`, resolving image display problems.
- 🐛 **Corrected Pluralization in Process Topic Docstrings**: Fixed a minor typo in `ProcessTopicManager` docstrings, ensuring consistent pluralization of "process."

### Removed
- 🗑️ **Deprecated Legacy Web Build Workflow**: The `build-web.yml` GitHub Actions workflow for building and releasing web images has been removed, simplifying CI/CD processes.
- 🗑️ **Removed Direct Process Management API**: Eliminated the entire `/processes` API endpoints and associated services (`ProcessController`, `ProcessService`, DTOs), streamlining the API surface and focusing on agent-centric interactions.
- 🗑️ **Removed Process Event Persistence**: Discontinued the persistence of process-specific events and entities, unifying event storage under agent-centric models.
- 🗑️ **Removed Process-Related API Schemas and Frontend Components**: Drastically reduced the API surface and frontend footprint by removing schemas, pages, and composables related to process management and dynamic form generation.
- 🗑️ **Removed Dynamic Form Generation Models**: Eliminated all `Formkit` and `PrimeVue` related models for dynamic UI generation (e.g., `Form`, `InputTextElement`), streamlining the event schema and decoupling form definitions from core events.
- 🗑️ **Removed Process-Related Lifetime Management**: Eliminated all process-related setup and shutdown logic from the API's `lifetime_manager`, including event distributors, subscribers, and discovery services.
- 🗑️ **Removed Process Simulation Runners and Tests**: Deprecated and removed the entire process simulation infrastructure from the API, including `SimulatedProcessApiTestRunner` and mock process events, along with all process-related API tests.
- 🗑️ **Removed `ExternalProcessEventDistributor`**: Eliminated the external event distributor for processes, aligning with the deprecation of direct process interactions.
- 🗑️ **Removed Redundant Work Event Properties**: Eliminated `is_human_work_event` and `is_program_work_event` properties from `BaseEvent`, simplifying event type checks.
- 🗑️ **Simplified Process Discovery Response**: Streamlined `ProcessRunner`'s discovery response to no longer include detailed `human_inputs`, `program_inputs`, or `agent_inputs` specifications, reducing overhead.
- 🗑️ **Removed `gunicorn` Dependency**: `gunicorn` has been removed from `aihub_api` and `aihub_bot` dependencies, simplifying the production deployment stack.
- 🗑️ **Simplified Docker Compose Landscape**: Drastically reduced the number of `docker-compose` files (e.g., removed `*-dev.yml`, `*-latest.yml`, `*-gpu.yml` variants) and associated service configurations (Milvus, PostgreSQL initialization scripts, NATS config, Nginx web serving), streamlining the deployment infrastructure.
- 🗑️ **Removed OpenWebUI and Traefik Integration**: Discontinued direct integration with OpenWebUI and Traefik in the consolidated Docker Compose setup, allowing for more flexible external UI and ingress solutions.
- 🗑️ **Removed Milvus Stack**: The entire Milvus vector database stack and its related configurations have been removed from the standard `docker-compose` setup.

### Refactor
- 🧹 **Pydantic Model Default Value Alignment**: Aligned numerous Pydantic model definitions (e.g., `QuestionStartEvent`, `CreateRoleRequest`, `JudgeOutput`, `DoclingConfig`, `SharePointResource`, `SharePointFile`, OpenWebUI SDK models) to explicitly use the `default` argument within `Field` for consistency and clarity.
- 🧹 **Consolidated `EventSpecs` Definition**: Centralized the `EventSpecs` model definition within `AgentDiscoveryResponseEvent` to improve discoverability and reduce redundancy.
- 🧹 **Unified Event Persistence**: Renamed `persist_agent_event` to `persist_event` in `EventPersister` and updated the API's `lifetime_manager` to use this unified method for all agent event persistence.
- 🧹 **Standardized External Event Distributor Naming**: Renamed `external_agent_event_distributor` to `external_event_distributor` across various components and dependencies (e.g., `AgentService`, `EvaluationService`, `OpenaiService`, `BotInTheLoopBot`, `AgentChatBot`, `AgentCompletionHandler`, `AgentChatController`, `BotInTheLoopController`, `lifetime_manager`, `AgentDiscoveryService`, `ChatService`, `WebSocketManager`, `WebSocketSender`) for improved consistency.
- 🧹 **Unified WebSocket Event Typing**: Renamed `ContextualizedAgentEvent` to `WSServerEvent` and updated all relevant API components, frontend components, and composables to use this new type for consistent server-to-user event communication over WebSockets.
- 🧹 **Refactored Agent Discovery Service**: Significantly refactored the agent discovery mechanism into a new `AgentDiscoveryService` class, making it standalone, self-managing its discovery loop, and aligning its internal naming conventions.
- 🧹 **Streamlined Event Serialization**: Optimized event serialization logic in `BaseEvent` and `test_Events` by removing unnecessary `**kwargs` and `serialize_as_any=True` from `model_dump` calls for cleaner Pydantic v2 compatibility.
- 🧹 **Standardized SharePoint Naming**: Conducted a broad refactoring effort to standardize naming conventions for SharePoint-related assets, ops, IO managers, and utility functions from `share_point_` to `sharepoint_` across the `aihub_pipeline` project for improved consistency and readability.
- 🧹 **Streamlined Process Delegator Definitions**: Simplified Pydantic field definitions in `Agent`, `Human`, and `Process` delegators (`aihub_process/delegators`) by removing redundant `Annotated` and `Field` usages.
- 🧹 **Refactored `aihub_process` Test Runner**: Streamlined `ProcessTestRunner` by removing redundant event sending methods and simplifying event observation for clearer API and easier test assertions.
- 🧹 **Refined `aihub_process` Playground Examples**: Simplified and updated the remaining `AgenticCVProcess` example to align with the new human delegator and work event models.
- 🧹 **Restructured Frontend Development Environment**: Migrated Nuxt configuration and app settings from a legacy `.app` directory to a new `.playground` directory for better project organization and updated associated package.json scripts and gitignore rules.
- 📦 **Version Alignment**: Synchronized the version tags across `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, and `aihub_pipeline` to `v0.217.0` for consistent releases.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs. This includes new API endpoints for discovery, interaction, and data submission.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose interactive forms (using Formkit elements) directly within their structure, allowing frontend applications to dynamically render UIs for human input, eliminating the need for manual UI development for common interactions.
- ⚡️ **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes, ensuring historical traceability.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications, similar to existing agent event streams.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes), promoting architectural consistency.
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust and isolated testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities and serve as starting points.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication and external integrations.
- 👥 **User Access to Processes in Dashboard**: Users can now view their granular access levels to specific processes directly within their dashboard interface, improving transparency and control.
- 🐳 **New Docker Build for Frontend**: Introduced a dedicated Dockerfile and Nginx configuration for building and serving the frontend application, streamlining deployment of the web UI.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance and reducing NATS load for frequently requested agent lists.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's internationalization capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🚦 **RAG Context Prompt Role Adjustment**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages to better align with prompt engineering best practices.
- 📊 **Database Indexing Improvements**: Added new indexes to `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved query performance and data retrieval efficiency.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found, preventing potential errors.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context, improving data integrity.
- 📦 **NATS Topic Validation for Processes**: Implemented stricter validation for NATS process discovery topics, ensuring that only correctly formatted subjects are processed and preventing malformed messages.
- 🛠️ **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing unintended data loss.
- 🏞️ **Image URL Handling in RAG Prompts**: Corrected an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring images are now correctly referenced and displayed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and frontend display event components, improving clarity and maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components and API DTOs, focusing on concise explanations of purpose and functionality.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by standardizing how default values are assigned, in line with Pydantic v2 conventions.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure, enhancing test organization.
- 🔄 **SharePoint Naming Consistency**: Standardized variable names, function parameters, and internal asset definitions across SharePoint-related components for improved consistency and readability.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed, streamlining development processes.
- ✂️ **Redundant Health Page**: A basic placeholder health page in the frontend was removed.

---



## [v0.224.0] - 2025-07-21 - Comprehensive Agent Rework and Production-Ready Deployment

### Added
- 🚀 **Full-Stack Containerization**: Introduced comprehensive Dockerfiles and multi-service Docker Compose configurations for streamlined deployment of API, Bot, and Web components, including MinIO, Milvus, PostgreSQL, Redis, MongoDB, and NATS.
- ⚙️ **New Configuration Settings**: Added dedicated `ApiRunnerSettings` and `BotRunnerSettings` for externalizing and managing core API and Bot configurations, such as model URLs and API keys.
- 🌐 **Web Frontend Production Setup**: Implemented a robust Nginx-based Docker setup for the web UI, enabling static file serving, runtime configuration loading, and optimized caching for production environments.
- 📦 **Core Component Applications**: Introduced `app/main.py` entrypoints for API and Bot services, standardizing their application bootstrapping and controller mounting.
- 📄 **New Database & Messaging Configurations**: Included detailed configuration files for Milvus (`milvus.yaml`), NATS (`nats.conf`), and a PostgreSQL initialization script (`init-multiple-dbs.sh`), supporting the new Docker Compose environments.

### Changed
- ♻️ **Unified Agent Configuration Model**: Revised the `AgentConfig` structure, removing the `agent_class` field, and adding `system_prompt`, `color`, and `voice` attributes, providing a more consistent and flexible agent definition.
- 🚧 **StartEvent Structure**: The `StartEvent` no longer carries agent configuration directly, simplifying event payload and centralizing configuration management within the agent dispatcher.
- ⚡️ **CI/CD Workflow Enhancements**: Updated GitHub Actions workflows for building and releasing Docker images, including more flexible `ssh_key` handling and explicit triggers for API, Bot, and Web builds.
- 🗃️ **Agent & Process DTOs**: Modified API-facing Data Transfer Objects (DTOs) for agents and processes to align with internal refactoring, including `AgentConfigDTO` with new fields.
- 📊 **Pipeline Automation Conditions**: Updated pipeline assets (`removed_documents_factory`, `removed_data_lake_files_factory`) to leverage `AutomationCondition.eager()`, influencing how data cleanup tasks are triggered.
- 📚 **Documentation Updates**: Revised agent examples in `aihub_doc/5_agents_in_detail.md` to reflect the updated `AgentConfig` and `system_prompt` usage.

### Fixed
- 🐛 **Robust Figure Deletion in Pipelines**: Improved the data lake figure deletion process in pipelines by removing a redundant existence check, preventing potential errors when a figures directory is already absent.

### Refactor
- 🧹 **Agent Dispatcher & Runner Overhaul**: Performed a major refactor of the `AgentDispatcher` and `AgentRunner` components, streamlining internal logic, simplifying argument injection, and refining background task management.
- 🔄 **Simplified Agent Discovery**: Unified the agent discovery mechanism by merging class and instance-level discovery events and topic managers into a single, more consistent model (`AgentDiscoveryResponseEvent`, `DiscoveryRequestEvent`).
- 🗄️ **Embedded Agent Persistence**: Re-architected agent configuration persistence by embedding `AgentConfigEntity` directly within `AgentEntity` and removing standalone `AgentConfigEntityDocument` and `AgentConfigEntityEmbeddedDocument`, enhancing data co-location and simplifying object relationships.
- 📦 **Streamlined Vector Store Configuration**: Replaced explicit `MilvusVectorStoreConfig` and `AzureAISearchVectorStoreConfig` objects with factory functions (`create_milvus_vector_store`, `create_azure_ai_search_vector_store`), simplifying vector store instantiation.
- 🗑️ **Removed Legacy Model Creation Service**: Deprecated and removed `ModelCreationService`, replaced by `EventModelCreationService` for cleaner event model generation.
- 🎛️ **Centralized Task Management**: Removed `_background_tasks` collections from various dispatchers and subscribers, opting for direct `asyncio.create_task` calls for more straightforward background task initiation.
- 📁 **Project Structure Alignment**: Renamed `aihub_web/.playground` to `aihub_web/.app` to better reflect its role as the primary application directory, alongside other minor file re-organizations across the codebase.
- 🗑️ **Removed Obsolete Tests**: Cleaned up and removed several outdated test files related to agent dispatcher, agent config, and agent service database integration, as their functionalities are now covered by more integrated tests or made obsolete by architectural changes.

### Removed
- 🗑️ **Direct Agent Config Persistence Logic**: Eliminated `save_config.py` from playground examples, indicating a shift away from direct saving of agent configurations to the database via this script.
- 🗑️ **Dedicated Locale String Entity**: Removed `LocaleStringEntity`, implying that localized strings are now handled more directly within relevant models or through other mechanisms.
- 🗑️ **Explicit Pipeline Materialization Jobs**: Removed the `materialize_asset_job` utility from the pipeline factory, simplifying job creation and encouraging asset-level automation.

---



## [v0.224.0] - 2025-07-21 - Flexible Agent Configuration and Advanced Discovery

### Added
- ✨ **Dynamic Agent Configuration:** Agent configurations can now be dynamically provided via a `StartEvent` or loaded from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Enhanced Agent Discovery Mechanism:** Implemented granular discovery for agent *classes* and specific agent *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured versions.
- 🗄️ **Database Persistence for Agent Configurations:** Custom agent configurations can now be saved and retrieved from the database, enabling persistent and shareable agent setups across deployments.
- 🔌 **New Pydantic Models for Vector Store Configurations:** Introduced dedicated Pydantic configurations for `AzureAISearchVectorStore` and `MilvusVectorStore` (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`), allowing for direct embedding and validation of vector store settings within agent configs.
- 📈 **`agent_class` Field in `AgentConfig`:** A new `agent_class` field has been added to `AgentConfig` for consistent agent class identification throughout the system.
- 📄 **`save_config.py` Example:** A new example demonstrating how to persist agent configurations to the database for custom or production deployments.

### Changed
- ⚙️ **Refined Agent Configuration Loading Logic:** The agent dispatcher now intelligently loads configurations, prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization:** Agent runners now explicitly accept a `default_agent_config` parameter, clearly defining the base configuration for new agent runs.
- 💡 **Improved Type Specificity for LLM and Vector Store Configs:** Agent configurations (e.g., in `RAGAgent`) now utilize more precise type unions for LLMs, embedding models, and vector stores, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration:** RAG and Retrieval agents now leverage the `.to_llama_index()` method directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- ⚡️ **Enhanced Background Task Management:** Improved handling of `asyncio.Task` instances within dispatchers and tracers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Revised API Agent Discovery:** The API now discovers and exposes full agent *instances* (including their specific configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- 🧹 **Renamed `EventModelCreationService` to `ModelCreationService`:** This service has been renamed to reflect its broader utility beyond just event models, with adjustments to excluded fields to accommodate the new `agent_config`.

### Refactor
- 🔄 **Consolidated Agent Configuration Management:** Standardized agent configuration handling across the system, enabling dynamic overrides and database persistence for agent instances.
- ✨ **Refined Agent and Event Discovery Architecture:** Overhauled the discovery mechanism to support both class-level and instance-level agent introspection, providing more granular control and information.
- 🏗️ **Reorganized API DTOs for Agent Representation:** Introduced dedicated DTOs (`AgentClass`, `AgentInstance`) to clearly separate the concept of an agent's definition from its configured, runnable instances in the API.

### Removed
- 🗑️ **Deprecated Configuration Fields:** The `system_prompt`, `color`, and `voice` fields have been removed from the base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration and allowing for more flexible, agent-specific prompt and UI customization to be defined in agent subclasses.

---



## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- ✨ **Enabled Custom Environment Variable Configuration for API Services**: This new capability allows users to define and inject additional environment variables, including secret references, directly into API deployments, significantly increasing configuration flexibility and integration possibilities.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 📦 **Optimized Docker Image Builds**: Streamlined Dockerfiles for `aihub_api` and `aihub_bot` services, resulting in smaller image sizes and faster build times.
- 📊 **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.
- ⚙️ **Prompt Engineering Adjustment**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering best practices.
- 🔑 **OAuth2 JWKS Cache Improvement**: Increased the maximum size of the JSON Web Key Set (JWKS) cache to `100` entries, which can improve performance and reliability for authentication lookups.
- 🛡️ **External Agent Event Deserialization**: Adjusted the deserialization logic for external agent events to no longer perform implicit validation of `thread_id` and `display_id`, expecting these to always be present in incoming data for stricter contract enforcement.
- 🔄 **Human Workflow Request Refinement**: The `HumanWorkRequestEvent` now uses explicit `user_ids`, `user_emails`, and `user_roles` for more granular targeting of human participants in workflows, replacing the previous generic `users` field.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization (`BaseEvent.model_dump`) to correctly handle nested Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.
- 🖼️ **Corrected Image URL Handling in RAG Prompts**: Resolved an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring that images are now correctly referenced and displayed.
- 🧪 **Phoenix Experiment Evaluator Robustness**: Fixed a potential bug in `PhoenixExperimentEvaluator` by ensuring that `JudgeOutput.model_json_schema()` is deep-copied before modification, preventing unintended side effects.
- 💬 **Open WebUI i18n Fix**: Corrected a missing translation label for `ExceptionEvent` in the Italian locale.

### Removed
- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- 🗑️ **Deprecated Health Page**: A basic placeholder health page in the frontend was removed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and maintainability. This includes renaming `WsServerEvent` and associated frontend components/composables.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g., `sharepoint_` was consistently renamed to `share_point_`).

---



## [v0.217.0] - 2025-07-10 - Streamlined Platform: Agent-Centric Workflows and API Unification

### Added
- 🚀 **Introduced Automatic Draft PRs**: A new GitHub Actions workflow automatically creates draft pull requests upon new branch creation, streamlining the development and review process.
- 👂 **Enabled Two-Way WebSocket Communication**: The `/events/ws` endpoint now supports sending user-originated events (`ExternalAgentEvent`) to the system, transforming it into a full two-way communication channel for real-time interaction.
- 🔌 **New Dynamic Agent Endpoint**: A new dynamically generated API endpoint (`/agents/l_l_m_wrapping_agent/dev_agent/send_event`) is now available, allowing direct communication with specific agent instances.
- ⚙️ **Introduced `docker-compose-mnt.yml` for Volume Mounting**: A new Docker Compose configuration is available, simplifying local development by explicitly mounting volumes for all core services, ensuring data persistence and easier management.
- 🌐 **Configured WebUI Development Defaults**: Updated `nuxt.config.ts` in the playground to explicitly define local development URLs for OIDC, WebUI, and WebSocket endpoints, simplifying local setup.
- 🩺 **Added Health Service Page**: A new health service page has been introduced in the frontend for monitoring system status.

### Changed
- 📝 **Improved Documentation Across Core Components**: Enhanced docstrings for `ThreadContext`, `RunTraceCoordinator`, `AgentService`, `EventPersister`, `ThreadController`, `ThreadService`, `ExternalAgentEventDistributor`, `AgentDiscoveryService`, and `AgentDiscoveryResponseEvent` for better clarity and understanding.
- ⚡️ **Optimized Core Caching and Indexing**: Adjusted caching for agent discovery and streamlined database indexes in `PersistedAgentEventEntity`, `ThreadEntity`, and `UserEntity` for improved performance.
- 🗄️ **Stricter Agent Retrieval**: Modified `AgentEntity`'s `get_agent` method to use `.get()` instead of `.first()`, ensuring that attempts to retrieve non-existent agents now raise an exception.
- 🖼️ **Refined RAG Image Path Handling**: Adjusted image path references in English RAG context prompts, improving image rendering consistency.
- 🔄 **Reverted RAG Context Prompt Role**: The chat role for RAG context prompts has been reverted from `user` back to `system` across all languages, restoring previous prompt engineering best practices.
- 📦 **Optimized Docker Image Builds**: Refactored API and Bot Dockerfiles to leverage multi-stage builds and virtual environment copying, resulting in more efficient and smaller production images.

### Fixed
- 🐛 **Improved `ExternalAgentEvent` Deserialization**: Added validation to ensure `thread_id` is present during `ExternalAgentEvent` deserialization, preventing errors for missing thread identifiers.

### Removed
- 🗑️ **Deprecated Process Management**: The entire suite of process management features has been removed, including:
    - Dedicated `/processes` API endpoints and their associated controllers, services, and DTOs (`ProcessController`, `ProcessService`, `ProcessDTO`, `ProcessHumanInDto`, `SubmittedFormDTO`).
    - Process-specific persistence entities (`ProcessEntity`, `PersistedProcessEventEntity`'s process-specific methods).
    - Related NATS components for process discovery and event distribution (`ExternalProcessEventDistributor`, `ProcessNCSubscriber` methods).
    - Playground examples and test infrastructure for processes (`SimulatedProcessApiTestRunner`, `HumanWorkEvent` forms).
- 🗑️ **Removed Legacy Build & Deployment Configurations**: Eliminated outdated Docker Compose files (`docker-compose.latest.yml`, `docker-compose.dev.yml`, `docker-compose-gpu.*.yml`), legacy Nginx configs, and environment loading plugins.
- 🗑️ **Removed `gunicorn` Dependency**: The `gunicorn` dependency has been removed from `aihub_api` and `aihub_bot`.
- 🗑️ **Removed Legacy Web Build Workflow**: The old GitHub Actions workflow for building and releasing web Docker images has been deprecated.
- 🗑️ **Removed Custom API Environment Variable Configuration**: The ability to define and inject additional environment variables directly into API deployments has been removed.

### Refactor
- 🧹 **Consolidated Event Distribution Logic**: Centralized event distribution and handling, renaming `ExternalAgentEventDistributor` to `ExternalEventDistributor` and standardizing its usage across the API and Bot services.
- 🧹 **Streamlined Event Persistence**: Unified event persistence in `EventPersister` to a single `persist_event` method for agent events, and re-purposed `PersistedProcessEventEntity` for agent-centric workflows.
- 🧹 **Unified WebSocket Event Types**: Standardized the event types sent over WebSocket connections from `ContextualizedAgentEvent` to `WSServerEvent` for better frontend consistency.
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions for many classes, methods, and parameters (e.g., `AgentEndpointsDiscoveryService` to `AgentDiscoveryService`, `share_point_` to `sharepoint_`).
- 🧹 **Refined Pydantic Model Definitions**: Aligned Pydantic model definitions with best practices by explicitly setting `default` values within `Field` for optional attributes and streamlining `BaseEvent` serialization.
- 🧹 **Simplified `HumanWorkEvent` Structure**: Restructured `HumanWorkEvent` by removing its direct integration with form elements and user-targeting specifics, making it a pure data event.
- 🧹 **Test Runner Simplification**: Refactored `AgentTestRunner` and `ProcessTestRunner` by consolidating `send_event` methods into base classes and simplifying event retrieval for clearer testing.
- 🧹 **Frontend Structure Adjustment**: Renamed `.app` directory to `.playground` in the web application for clearer separation of development environments.

---



## [v0.222.0] - 2025-07-21 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added
- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering available processes, retrieving their details, and submitting data via dynamic forms to start or continue process walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly within their dashboard interface.
- 🌐 **Web Build and Deployment Infrastructure**: New Dockerfile, Nginx configuration, and dynamic config loading for the `aihub_web` application, streamlining production deployments.
- ✨ **Custom Environment Variables for API**: Enabled the definition and injection of additional environment variables, including secret references, directly into API deployments.

### Changed
- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events, providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered forms correctly reflect the user's selected locale.
- 🔄 **Updated RAG Context Prompt Role**: The chat role for the RAG context prompt has been adjusted from `system` to `user` across all supported languages to better align with prompt engineering best practices.
- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during the document parsing process, enhancing observability and assisting with debugging.

### Fixed
- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested Pydantic models and ChatMessages, preventing data loss.
- 🖼️ **Image URL Handling in RAG Prompts**: Corrected an issue in the English RAG context prompt where image URLs were not consistently processed, ensuring images are correctly referenced.
- 🚦 **ExternalAgentEvent Deserialization**: Adjusted validation logic during deserialization of `ExternalAgentEvent` to prevent premature errors.

### Removed
- 🗑️ **Automatic Draft PR Workflow**: The GitHub Actions workflow that previously created automatic draft pull requests for new branches has been removed.
- ✂️ **Deprecated Frontend Health Page**: A basic placeholder health page in the frontend was removed.

### Refactor
- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`) and SharePoint-related components.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and `simulation/process` directory structure.
- 🧹 **Dockerfile Streamlining**: Cleaned up Dockerfiles for API and Bot services, removing redundant steps.
- 💻 **Frontend Project Structure**: Renamed the main Nuxt application directory from `.playground` to `.app`.

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
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time updates and visualization of process execution in client applications.
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
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.

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



