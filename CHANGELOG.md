# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.254.12] - 2025-12-03 - Enhanced Document Processing and Model Updates

### Added

- ✨ **Introduced Docling Standard Pipeline:** Added support for a new "Standard" Docling document processing pipeline,
  providing advanced control over OCR, table extraction, image handling, and more flexible output formats.
- ⚙️ **Configurable Docling Asynchronous Polling:** New environment variables (`DOCLING_POLL_INTERVAL`,
  `DOCLING_MAX_POLLS`) have been added to allow customization of the polling interval and maximum attempts for
  asynchronous Docling document processing tasks.

### Changed

- 🚀 **Upgraded Default RAG Embedding Model:** The default embedding model used by the RAG Agent has been updated from
  `embedding/small` to `embedding/large` to potentially improve retrieval quality and performance.
- 🔄 **Updated Azure OpenAI Model Reference:** LiteLLM configurations for `text-generation/mini` have been adjusted to
  use `azure/gpt-4o-mini` instead of `azure/gpt-5-mini`, aligning with recent Azure OpenAI API changes for model
  ingestion.
- branding **Updated OpenAI Compatibility Interface:** The AI Hub's OpenAI-compatible interface and web UI are now
  consistently branded as "Open WebUI," featuring updated icons for better recognition.

### Fixed

- 🐛 **Improved Document Parsing Robustness:** The Docling document loader now uses `html5lib` for parsing, enhancing its
  ability to handle malformed or complex HTML content and improving overall parsing reliability.

### Refactor

- 🧹 **Standardized Docling API Configuration:** The `DOCLING_API_ENDPOINT` environment variable has been renamed to
  `DOCLING_BASE_API_URL` across the codebase, improving clarity and consistency in Docling service configuration.

---

## [v0.254.11] - 2025-12-02 - Enhanced Document Intelligence Figure Extraction

### Changed

- 🖼️ **Document Intelligence Figure Handling:** Reworked the figure extraction and replacement mechanism within the
  `DocumentIntelligenceLoader` to leverage precise span offsets provided by the API, ensuring more accurate and robust
  figure integration into the document text.
- ⚡️ **Improved Figure Processing Robustness:** Implemented a new strategy for figure replacement that processes figures
  in reverse order of their appearance, mitigating issues related to text shifts and ensuring correct figure placement.
- 🐛 **Strengthened Figure Data Validation:** Introduced validation checks for figure span information to gracefully
  handle cases where span data is missing or out of bounds, preventing errors during document processing.

---

## [v0.254.10] - 2025-12-02 - AI-Powered Code Review and On-Demand Assistance with Claude

### Added

- ✨ **Automated AI Code Reviews:** Introduced a new GitHub Actions workflow to automatically run Claude AI code reviews
  on pull requests, providing comprehensive feedback on code quality, potential bugs, performance, security, and test
  coverage.
- 🤖 **On-Demand AI Assistant:** Added a new GitHub Actions workflow enabling direct interaction with Claude AI within
  issues, pull request comments, and reviews by tagging `@claude`. This facilitates on-demand code assistance,
  explanations, and insights.

---

## [v0.254.9] - 2025-12-02 - Unified File System Filtering with Flexible Patterns

### Refactor

- 🧹 **Unified Local File System Scanning:** Significant overhaul of `LocalFileSystemResource` to replace granular
  folder, subfolder, extension, and file-specific filters with a more flexible, unified `include_patterns` and
  `exclude_patterns` system, simplifying file discovery and filtering logic.
- 🔄 **Generic Source File Types:** Deprecated `LocalFile` and `MinimalLocalFile` types, transitioning to the more
  generic `SourceFile` and `MinimalSourceFile` types for local file system interactions. This removes file
  system-specific folder attributes (`source_folder`, `subfolder`) for broader applicability.
- ⚡️ **Improved Pattern Utility Functions:** Rewrote and enhanced pattern utility functions to support the new flexible
  `include_patterns` and `exclude_patterns` system, providing more robust and explicit ways to generate regex patterns
  for paths, folders, extensions, and substrings.

### Changed

- 📄 **Updated IO Manager and Ops:** The `LocalFileSystemIOManager` and related data versioning operations have been
  updated to align with the new `SourceFile` and `MinimalSourceFile` types and the simplified file system resource
  configuration.
- ⚙️ **Simplified Local-to-Datalake Definitions:** The `default_local_filesystem_to_datalake_definitions` utility now
  uses the streamlined `include_patterns` and `exclude_patterns` for configuring local file system scanning, making
  setup more intuitive.
- 📊 **Adjusted Metadata Tables:** Local file metadata tables (`local_file_metadata_table`) no longer display
  `source_folder` and `subfolder` information, reflecting the removal of these attributes from the underlying file
  objects.

### Removed

- 🗑️ **Deprecated LocalFile Types:** The specific `LocalFile` and `MinimalLocalFile` Python types have been removed in
  favor of the more generic `SourceFile` and `MinimalSourceFile` types.
- 🗑️ **Legacy File System Scan Configuration:** Eliminated various specific configuration parameters (e.g.,
  `include_folders`, `exclude_paths`, `include_extensions`) from `LocalFileSystemResource` and related utility
  functions, replaced by the unified pattern-based approach.

---

## [v0.254.8] - 2025-12-01 - Smarter Data Fetching for Enhanced UI Stability

### Added

- ✨ **Introduced `useRouteReady` Composable:** A new utility function to ensure that data fetching operations are only
  initiated once all required route parameters are fully resolved and valid, preventing queries from executing with
  incomplete or placeholder values during navigation.

### Refactor

- 🧹 **Optimized Data Query Activation:** Implemented the `useRouteReady` composable across various data fetching hooks,
  including those for **Agents**, **Documents**, **Evaluation Datasets** and **Experiments**, **Processes**, **Roles**,
  **Threads**, and **Users**. This change prevents API queries from running prematurely, leading to more stable UI
  states and improved application reliability during route transitions.

---

## [v0.254.7] - 2025-11-28 - New Service Integration: Attu Platform

### Added

- ✨ **Attu Service Integration:** Introduced the Attu service to the platform, enhancing capabilities (e.g., for data
  management).
- 🔑 **Secure Access for Attu:** Implemented OAuth2 Proxy for the Attu service, ensuring secure, group-based access for
  authorized users.
- 🚀 **Automated Routing for Attu:** Configured Traefik to provide automatic routing and SSL termination for the Attu
  service via a dedicated subdomain.

### Changed

- 📄 **Updated OAuth Configuration Documentation:** The quick start guide has been updated to include the required
  redirect URIs and platform type configurations for the new Attu service.
- ⚙️ **Deployment Configurations for Attu:** Modified various Docker Compose files and templates to incorporate the Attu
  service and its OAuth2 Proxy into the deployment stack.

---

## [v0.254.5] - 2025-11-24 - Platform Configuration Update and Docling Refinements

### Changed

- 📄 **Updated DNS Prerequisites:** Replaced the `datalake-api` subdomain requirement with `litellm.aihub.example.com`
  for the `litellm` proxy, streamlining API access configurations for the platform.

### Removed

- 🗑️ **Removed Docling Model Initialization Script:** The dedicated `init-models.sh` script, previously responsible for
  checking and downloading Docling models, has been removed, indicating an updated or integrated approach to model
  management.

---

## [v0.254.4] - 2025-11-21 - Internal Consistency Improvements

### Refactor

- 🧹 **Standardized `build_uri` parameter:** Updated the `data_lake_client.build_uri` method call within the data lake
  file removal process to use `file_path` instead of `path`, enhancing parameter naming consistency across the API.

---

## [v0.254.3] - 2025-11-18 - Unlocking Multi-Tenancy and Streamlined Onboarding with Enhanced Platform Clarity

### Added

- ✨ **Introduced comprehensive Multi-Tenancy documentation:** New sections detail the multi-tenancy concept, how to set
  up tenants, manage users and roles, and a technical reference for access control, providing clear guidance on
  organizational boundaries within a single platform instance.
- 🚀 **New Quick Start and One-Command Deployment guides:** Detailed documentation now covers prerequisites for both
  production and local deployments, Azure Entra ID setup, and a streamlined one-command deployment process for rapid
  platform setup.
- 📄 **Expanded manual Slack & Teams Bot Creation guide:** A new, in-depth guide is available for manually configuring
  bots, including Teams Developer Portal setup, MongoDB configuration, Slack API integration, app manifest examples, and
  troubleshooting.
- ⚙️ **Detailed RAG Ingestion Pipeline documentation:** New content explains the processing stages (parsing, chunking,
  embedding, linking, summarization), storage, document lifecycle, and benefits of the RAG ingestion pipeline.

### Changed

- 🔄 **Refined Language Model (LLM) integration documentation:** Updated content clarifies LLM proxy functions, model
  configuration, PII protection, and guardrail concepts, enhancing understanding of AI model interactions.
- 📈 **Improved Cost Control documentation:** Enhanced details on LiteLLM's user management for budgets and rate
  limiting, including configuration via environment variables, to provide better predictability and control over AI
  expenses.
- 📚 **Clarified deployment terminology:** Documentation for deployment options, backup & recovery, and updates &
  maintenance now explicitly differentiates between "Multi-Instancing" (hard infrastructure separation) and
  "Multi-Tenancy" (logical separation within an instance).
- 🦾 **Updated Agent documentation:** The fundamentals, RAG Agent, and Expert Asking Agent sections have been extensively
  rewritten to provide deeper insights into structured workflows, context management, and human-in-the-loop
  collaboration patterns.
- 💡 **Enhanced Data Pipeline and Knowledge Management documentation:** Rewritten sections offer improved clarity on
  pipeline fundamentals, workflow automation, and knowledge organization through "collections" (namespaces), detailing
  their structure, lifecycle, and integration.
- 🌐 **Updated main page and FAQ:** The main landing page and Frequently Asked Questions have been revised to reflect the
  latest platform features, documentation structure, and terminology.
- 🧹 **Standardized documentation terminology:** A new glossary has been added to the translation prompt to ensure
  consistent terminology usage across all localized documentation, especially for multi-tenancy and related concepts.

### Removed

- 🗑️ **Node.js dependencies:** The platform no longer includes Node.js packages, simplifying the dependency stack.

### Refactor

- 📁 **Restructured documentation directories:** Several top-level documentation directories (e.g.,
  `15_slack_teams_integrations` to `16_slack_teams_integrations`, `16_api` to `17_api`) have been renamed to accommodate
  the new Multi-Tenancy section and improve logical grouping.
- 🔗 **Updated internal documentation links:** All internal links within the documentation have been updated to reflect
  the new directory structure and ensure navigation consistency.
- 📦 **VitePress plugin import simplification:** Updated the import path for `CopyOrDownloadAsMarkdownButtons` in the
  documentation theme for better maintainability.

---

## [v0.254.2] - 2025-11-18 - New Service Integrations and Deployment Enhancements

### Added

- 🚀 **Gunicorn Dependency**: Incorporated Gunicorn, a robust WSGI HTTP server, into the project dependencies to bolster
  production deployment capabilities.
- 📄 **Docling Configuration**: Integrated new environment variables for **Docling** and **Hosted VLM** API endpoints,
  timeouts, and model specifics across all Docker Compose configurations, preparing the ground for advanced document
  processing and visual language model integrations.

---

## [v0.254.1] - 2025-11-18 - Milvus Partitioning for Memory Efficiency and System Enhancements

### Added

- ✨ **Milvus Manual Partitioning**: Introduced a new manual partitioning system for Milvus vector stores, enabling
  namespace-based data isolation. This allows for more targeted and memory-efficient loading of data during queries by
  only accessing relevant partitions.
- ⚙️ **`PartitionAwareMilvusVectorStore`**: A new Milvus vector store implementation that transparently routes data to
  specific, hashed partitions based on namespace metadata during insertion and queries, significantly improving memory
  management for RAG workloads.
- 🧪 **Comprehensive Milvus Partitioning Tests**: Added a new suite of behavioral tests to validate the correctness and
  efficiency of the Milvus manual partitioning and namespace routing logic.
- 🔑 **Azure OpenAI Base URL Configuration**: Added `AZURE_OPENAI_BASE_URL` to development environment configurations,
  providing greater flexibility for connecting to various Azure OpenAI service endpoints.
- 🔒 **Enhanced OAuth2 Proxy Scopes**: Expanded the requested scopes for OAuth2 Proxy to include `openid`, `email`, and
  `profile`, allowing for more comprehensive user information retrieval during authentication.

### Changed

- 🚀 **Optimized Milvus Memory Mapping (mmap)**: Updated Milvus query node configurations to broadly enable memory
  mapping for vector indexes, scalar fields, and growing data segments. This change improves disk I/O efficiency and
  reduces RAM footprint, with a potential slight increase in query latency for data not in memory cache.
- 🔄 **Milvus Vector Store Factory Streamlining**: The `create_milvus_vector_store` factory and its associated Dagster
  resources no longer require manual `num_partitions` or `enable_mmap` parameters, as partitioning is now automatically
  handled, simplifying vector store creation.
- 📦 **Dagster Pipeline Dockerfile Refinement**: Streamlined the Dagster pipeline Dockerfile by removing the `make` build
  tool dependency and explicitly defining entrypoints in Docker Compose, enhancing deployment clarity.

### Refactor

- 🧹 **Dagster Summary Nodes Asset Path**: Reorganized the asset key for summary nodes in Dagster pipelines, moving them
  into a more logical `datalake_to_vectorstore` subgroup for improved asset discoverability and organization.

### Removed

- 🗑️ **Redundant Dagster Volume Mounts**: Eliminated redundant `dagster-data` volume mounts from several Dagster-related
  services in Docker Compose configurations, reducing clutter and simplifying deployment setups.

---

## [v0.254.0] - 2025-11-18 - Enhanced Data Persistence and Pipeline Management

### Added

- ✨ **Persistent Data Storage for Dagster:** Implemented persistent volume mounts (`dagster-data`) for Dagster services,
  including `dagster-webserver`, `dagster-daemon`, and `default-rag-pipeline`. This change ensures that critical Dagster
  operational data, such as run history and event logs, is preserved across container restarts and updates.
- 🛠️ **`make` Utility in Dagster Pipelines:** The `make` utility is now installed within the `aihub_pipeline` Docker
  image, providing enhanced capabilities for scripting and managing pipeline operations.

### Changed

- 🔄 **Streamlined Dagster Webserver Entrypoint:** The `aihub_pipeline` Dockerfile now explicitly defines
  `make dagster-webserver` as its entrypoint, simplifying and standardizing the launch process for the Dagster webserver
  within the container.
- 🔒 **Simplified OAuth2 Proxy Configuration:** The explicit `OAUTH2_PROXY_SCOPE` setting has been removed from the
  OAuth2 proxy configuration, streamlining its setup while maintaining robust authentication flows.

---

## [v0.253.4] - 2025-11-18 - Next-Gen Process Management: Introducing Walkthroughs and Advanced Form Capabilities

### Added

- 🚀 **Detailed Process Walkthroughs API**: Introduced a new endpoint
  (`/processes/{process_class}/{process_id}/walkthroughs`) to retrieve paginated process walkthroughs with comprehensive
  step information, offering deep visibility into process execution.
- ✨ **Process Walkthrough Logic**: Implemented robust backend logic within `ProcessService` to aggregate and construct
  detailed `ProcessWalkthroughDTO` and `ProcessStepDTO` objects, including involved agents and humans, from raw event
  data.
- 📦 **New Process Input Specification DTOs**: Created specialized Data Transfer Objects (`AgentInDTO`, `HumanInDTO`,
  `ProgramInDTO`) for process input specifications, enhancing structure and type safety for API definitions.
- ✨ **Automatic Formkit Field Configuration**: Enhanced the `Form` class to automatically assign `id` and `required`
  properties to Formkit elements based on Pydantic field definitions, simplifying form creation.
- 🚀 **Extended Formkit Element Library**: Introduced a comprehensive suite of new Formkit elements (e.g., `DatePicker`,
  `MultiSelect`, `Slider`, `Password`, `InputMask`, `Knob`, `Rating`, `Textarea`, `Checkbox`, `RadioButton`, `Select`,
  `SelectButton`, `ToggleSwitch`, `InputNumber`, `InputOtp`, `CascadeSelect`), significantly expanding UI capabilities
  for user input.
- ✨ **Added `ref` to Formkit Elements**: Introduced a `ref` field (aliased as `id`) to `FormkitElement`, providing a
  unique identifier for better UI control and integration.
- 🔗 **Event Response Tracking**: Added an `in_response_to` field to `WorkEvent` and `Human` form submissions, improving
  the traceability and context of work events within process walkthroughs.
- 👤 **Agent Submission Tracking**: Introduced a `submitted_by` field in `AgentWorkEvent`, allowing clear identification
  of the agent responsible for submitting work.
- 📊 **Paginated Process Walkthrough Retrieval**: Implemented `get_paginated_walkthrough_events` to efficiently retrieve
  process walkthroughs with all their associated events, supporting pagination for large datasets.
- 🆕 **Process Card UI Component**: Introduced a new Vue component for displaying process information cards, enhancing
  the visual representation of available processes.
- 📝 **Reusable Formkit Form Component**: Developed a versatile Vue component (`Process/Form.vue`) for rendering dynamic
  Formkit schemas, complete with conditional field logic and label interpolation, enabling flexible user input.
- 🚀 **Process Start Forms Component**: Created a new UI component (`Process/Starts.vue`) to render and manage multiple
  start forms for a process, simplifying the initiation of new process runs.
- 📊 **Process Walkthrough List Component**: Implemented a new UI component (`Process/Walkthrough/List.vue`) to display
  paginated process walkthroughs, featuring details like creation/update times, involved entities, and step progress
  visualization.
- 💻 **`useProcessWalkthroughs` Composable**: Introduced a new Nuxt composable (`useProcessWalkthroughs`) for fetching
  and managing paginated process walkthrough data, simplifying data access in the frontend.
- 🚀 **`useSendProcessStartForm` Composable**: Created a new Nuxt composable (`useSendProcessStartForm`) to handle the
  submission of process start forms, integrating with the query cache for immediate UI updates.
- 🌐 **New Process Walkthrough Translations**: Added new English translations for process management and
  walkthrough-related UI elements.
- 🛠️ **Formkit PrimeVue Integration**: Integrated the `formkit-primevue` module and defined a comprehensive list of
  wrapped PrimeVue inputs, preparing for advanced form rendering capabilities.
- 🚀 **New Process Detail Pages**: Introduced a new set of pages for process details, including an overview, a dedicated
  "start run" form, and a list of walkthroughs, enhancing process management capabilities.
- ✨ **New `SubmittedCV` Human Start Event**: Introduced a new `SubmittedCV` event, acting as a human-initiated process
  start event with a rich set of Formkit input fields for comprehensive CV submission.
- 🚀 **Added Agentic CV Process Runner**: Introduced a dedicated runner (`run.py`) for the `AgenticCVProcess` playground
  example, facilitating easier local execution and testing of the workflow.

### Changed

- ⚙️ **Docker Compose Dev Configuration**: Updated the Docker Compose Dev run configuration to explicitly include `.env`
  file paths, ensuring environment variables are correctly loaded.
- 🔄 **Refined Process API Responses**: Applied `response_model_exclude_none=True` to several process-related endpoints,
  streamlining API responses by omitting null values.
- 📄 **Renamed Process DTOs**: Renamed `ProcessHumanInDto` to `HumanInDTO` for consistency and clarity in process input
  definitions.
- ⚙️ **Simplified Human Input Retrieval**: Refactored `get_process_start_forms` and `get_process_open_forms` to directly
  return `HumanInDTO` objects, simplifying the API and reducing data transformation.
- 📄 **Localized Process Configuration from Entity**: Added a new constructor to `ProcessConfigDTO` to facilitate
  creating localized process configurations directly from entity specifications.
- 🔄 **Standardized Process Input DTOs**: Migrated `ProcessDTO` to use new, specialized DTOs for human, program, and
  agent inputs (`HumanInDTO`, `ProgramInDTO`, `AgentInDTO`), enhancing type safety and clarity.
- 🔄 **Updated Formkit Element Usage**: Migrated `InputTextElement` to the new `InputText` class across various event
  definitions and process runners, aligning with the formkit refactor.
- ⚙️ **Refined Agent Work Event Creation**: Updated agent work event creation to include `submitted_by` information,
  enhancing event context.
- 📄 **Enhanced Process Entity Specifications**: Upgraded process entity specifications (`ProgramInSpecsEntity`,
  `HumanInSpecsEntity`, `AgentInSpecsEntity`) to accept type-hinted `specs` objects directly, improving type safety.
- 🌐 **Localized Process Configuration Persistence**: Updated `ProcessConfig` entity to persist `name` and `description`
  as `LocaleStringEntity`, enabling robust internationalization for process configurations.
- 🎨 **Updated Default Process Icon**: Changed the default icon for new processes to `carbon:ibm-event-processing`,
  providing a more relevant visual representation.
- 🏗️ **Simplified Dockerfile for Pipelines**: Streamlined the `Dockerfile` for pipelines by removing unnecessary `make`
  dependency and delegating entrypoint definition to Docker Compose, improving container efficiency.
- 🔗 **Improved Agent Delegator Event Tracking**: Enhanced `AgentDelegator` to include `in_response_to` and
  `submitted_by` in agent work events, and aligned `display_id` with the event's unique ID for consistent event tracing.
- 🤖 **Agentic CV Process Overhaul**: Significantly refactored the `AgenticCVProcess` playground example to utilize an
  expanded range of Formkit elements for initial human input, enhancing the interactive experience.
- 🔄 **Refined Agentic CV Process Logic**: Updated the `AgenticCVProcess` to align with new event tracking mechanisms and
  improved agent output parsing, ensuring smoother workflow execution.
- ⚙️ **Refined `AnalyzedCV` Event Structure**: Updated `AnalyzedCV` event to specifically use `LLMStopEvent` for agent
  work responses and removed the `cv_name` field for a more generic approach.
- ⚙️ **Restricted Human Output in Agent-to-Human Process**: Updated `AgentToHumanProcess` and `HumanOnlyProcess` to
  target the `AIHubAdmin` role for human output, enhancing control over human-in-the-loop interactions.
- 🖥️ **Updated Processes Overview**: Integrated the new `ProcessCard` component into the processes overview page,
  providing a visually enhanced list of available processes.
- ⚙️ **Enhanced PrimeVue Element Validation and Labeling**: Improved `PrimeVueElement` to automatically include
  `required` validation rules and append an asterisk (`*`) to the labels of required fields when localized.
- ⚙️ **Enhanced `useTimeAgo` Flexibility**: Updated the `useTimeAgo` composable to accept numeric timestamps
  (nanoseconds) in addition to strings and Date objects, increasing its versatility.
- ⚙️ **Optimized PrimeVue Auto-Import**: Configured PrimeVue to exclude `wrappedPrimeInputs` from auto-import, ensuring
  these components are managed through Formkit.
- 🛠️ **Extended API Endpoints for Process Walkthroughs**: Generated new API endpoints and types
  (`GetProcessWalkthroughsData`, `GetProcessWalkthroughsResponse`) to support fetching paginated process walkthrough
  data.
- 📦 **Comprehensive Formkit Element Schemas**: Added schemas for an extensive range of new Formkit elements, providing
  full API support for rich user input forms.
- 📄 **Source Origin Tracking for Ingested Nodes**: Introduced a `source_origin` field to `IngestedNode`, allowing better
  traceability of original document sources in data lake operations.
- 🔄 **Standardized Process Input Schemas**: Updated API schemas for process inputs to align with the new `AgentInDTO`,
  `HumanInDTO`, and `ProgramInDTO` structures.
- 🎙️ **Expanded Audio Voice Options**: Added new voice options (`marin`, `cedar`) to `ChatCompletionAudioParam`,
  offering more choices for audio generation.
- 🔑 **Enhanced OAuth2 Proxy Scopes**: Added `openid email profile` scopes to the `oauth2-proxy` configuration, improving
  user identity and profile information retrieval for Dagster.

### Fixed

- 🐛 **Temporarily Disabled Failing Test**: Commented out `test_walk_through_process_std_methods` in the API playground
  as it currently fails due to flawed logic, to be re-enabled after fix.
- 🧪 **Marked Flaky Test**: Added `@pytest.mark.flaky` to `test_stream_response` in `test_ChatBot.py` to identify and
  manage intermittent test failures.

### Refactor

- 🧹 **Import Reorganization**: Standardized import order across `DoclingController`, `DoclingService`,
  `EventController`, and Azure Data Lake resources for improved code consistency and readability.
- 🧹 **Import Normalization**: Converted relative imports to absolute imports within `OpenaiController` for improved
  modularity and clarity.
- 🧹 **Pydantic Model Validation Update**: Migrated event deserialization to use `.model_validate()` method for Pydantic
  models, enhancing strictness and correctness in data parsing.
- 🧹 **Simplified Logging in Process Runner**: Streamlined logging messages in `ProcessRunner` by removing redundant
  process ID information, making logs cleaner.
- 🧹 **Asynchronous Process Steps**: Converted `received_cv_2_analyzed_cv` to an asynchronous method, improving
  performance for I/O-bound operations.
- 🧹 **Documentation Formatting**: Applied minor formatting adjustments to the bot creation guide for improved
  readability.
- 🧹 **Standardized Agent Route Structure**: Refactored agent-related routes to use a more consistent
  `/[agent_class]-[agent_id]` format, improving URL readability and maintainability.

### Removed

- 🗑️ **Removed Redundant Human Input DTO**: Eliminated `ProcessHumanInDto` as its functionality is now covered by the
  more granular `HumanInDTO`.
- 🗑️ **Removed Program-Initiated `SubmittedCV` Event**: Deprecated and removed the program-initiated `SubmittedCV`
  event, transitioning the `AgenticCVProcess` to primarily use human-initiated start events.
- 🗑️ **Streamlined Dagster Volume Mounts**: Removed explicit volume mounts for Dagster data from `docker-compose`
  configurations, simplifying deployment and relying on other means for data persistence if needed.

---

## [v0.253.3] - 2025-11-16 - Deployment Configuration Refinements and Service Cleanups

### Changed

- ⚙️ **Adjusted SeaweedFS Volume Size Limit:** The default volume size limit for SeaweedFS has been reduced to 29GB
  (from 1TB) for non-development environments, optimizing storage resource allocation.
- 🔄 **Externalized API and OTel Version Configuration:** The `AIHUB_API_VERSION` and `OTEL_RESOURCE_SERVICE_VERSION` are
  now configurable via environment variables, providing greater flexibility for deployment and consistent version
  management across services.

### Removed

- 🗑️ **Disabled Automatic Speaches Model Downloads:** The `speaches` service no longer automatically downloads models on
  container startup. This change requires models to be provisioned manually or via an alternative mechanism.
- 🗑️ **Deprecated Dagster Pipeline Configuration:** The `default_rag_pipeline` configuration for Dagster has been
  removed, streamlining the Dagster workspace setup.

---

## [v0.253.2] - 2025-11-14 - Comprehensive Bot Setup Documentation

### Added

- 📄 **New Bot Creation Manual Setup Guide**: Introduced a comprehensive, step-by-step guide for manually creating and
  configuring bots with Microsoft Teams and Slack. This detailed resource covers everything from Azure Bot Framework and
  Teams Developer Portal setup to MongoDB configuration and Slack OAuth integration, complete with app manifest
  examples, key terminology, and troubleshooting tips.

### Changed

- 🔗 **Updated Chat Interface Documentation Link**: Corrected and updated an internal documentation link pointing to the
  chat interface feature overview, ensuring users are directed to the most current information.

---

## [v0.253.1] - 2025-11-14 - Robust Milvus Vector Store Configuration and CI/CD Streamlining

### Added

- ✨ **Introduced Advanced Milvus Vector Store Configuration:** The Milvus vector store factory now supports configurable
  index types (HNSW, DISKANN, IVF_FLAT, FLAT), enabling tailored performance and memory usage for different RAG
  workloads.
- 🚀 **Enabled Hybrid Search with BM25:** Milvus collections now support hybrid search by automatically creating sparse
  vector indexes (BM25) alongside dense embedding indexes, significantly improving retrieval relevance.
- 🔑 **Implemented Milvus Partition Keys:** Vector stores are now partitioned by namespace, enhancing data isolation and
  query performance for multi-tenant or multi-document RAG applications.
- ⚙️ **Added Memory Mapping (mmap) Option for HNSW:** Users can now enable mmap for HNSW indexes in Milvus to reduce RAM
  consumption, offloading data to the OS page cache for memory-constrained environments.
- 📄 **Added `regenerate_compose` CI/CD Input:** A new input allows explicit control over Docker Compose file
  regeneration in CI/CD workflows, optimizing build times when regeneration is not needed.

### Changed

- ⚙️ **Exposed Milvus Configuration in Dagster Resources:** Milvus vector store parameters like index type, mmap, and
  partitions are now exposed as configurable options in Dagster resources, allowing pipeline authors to fine-tune their
  RAG infrastructure.
- 🧪 **Improved Milvus Test Isolation:** Milvus test fixtures now ensure a clean state by dropping collections and
  clearing the Milvus vector store factory cache before each test run, enhancing test reliability.
- 🔄 **Optimized CI/CD Dependency Installation:** The order of global dependency installation in CI/CD has been adjusted
  to precede Docker Compose file generation, ensuring all prerequisites are met for a more robust build process.

### Refactor

- 🧹 **Refined Milvus Type Hints:** Updated internal type hints for Milvus vector store configurations, improving
  codebase clarity and maintainability.

---

## [v0.253.0] - 2025-11-14 - Unified Deployment, Local AI Power, and Docling VLM Integration

### Added

- ✨ **Dynamic Deployment System**: Introduced a new Jinja2-based templating system to generate Docker Compose and
  service configuration files dynamically across various stages (dev, local, build, nightly, latest) and hardware (CPU,
  GPU), replacing manual configurations for enhanced flexibility and maintainability.
- 🦾 **Local Inference Services**: Integrated new Docker services (`llama-cpp`, `llama-cpp-embedding`,
  `llama-cpp-reranker`, `vllm-docling`, `speaches`) to enable on-premise inference for Large Language Models, embedding
  models, reranker models, and audio models (SST/TTS), dynamically selected based on hardware and deployment stage.
- 🖼️ **Docling VLM Integration**: Implemented new API endpoints and a dedicated controller within `aihub_api` to support
  advanced document conversion to Markdown using Docling's Visual Language Model (VLM) capabilities.
- ⚙️ **IntelliJ Run Configurations**: Added new IntelliJ IDEA run configurations for Docker Compose (Build, Dev, Local
  with CPU/GPU options) to streamline local development setup and execution.
- 📄 **Deployment Documentation**: Created a new `README.md` within the `deployment` directory, providing comprehensive
  documentation for the different deployment configurations and Traefik setup.
- 🔑 **Hugging Face API Key Management**: Integrated Hugging Face API key support into CI workflows and LiteLLM
  configurations, enabling seamless access to models requiring authentication from Hugging Face Hub.

### Changed

- 🛠️ **Centralized Configuration**: Refactored core infrastructure service configurations (LiteLLM, Milvus, NATS,
  Dagster, OpenTelemetry, Traefik) into a centralized `compose-config.yml` for consistent and dynamic generation.
- 🚀 **LiteLLM Model Definitions**: Updated LiteLLM proxy to dynamically route to local inference services (llama-cpp,
  speaches) based on hardware availability and deployment stage, optimizing resource utilization.
- 🛡️ **LiteLLM Prompt Injection Detection**: Enhanced LiteLLM's prompt injection detection by disabling simple heuristic
  checks and enabling more robust similarity and LLM-based API checks with a refined system prompt.
- 📊 **OpenTelemetry Configuration**: Implemented conditional activation of OpenTelemetry exporters and processors,
  ensuring full observability pipelines are enabled only in non-development stages for optimized resource usage.
- 📦 **Milvus Configuration Tuning**: Adjusted Milvus logging levels, segment sizes, GPU memory pool settings, and
  default data handling policies for improved performance and consistency across environments.
- ⚡️ **NATS Performance Tuning**: Dynamically configured NATS server settings (payload limits, connections, JetStream
  storage) to align with specific stage requirements, optimizing performance for both development and production.
- 🌐 **Traefik Configuration**: Enhanced Traefik setup for dynamic TLS certificate resolution (Let's Encrypt for
  production, self-signed for local/build) and dashboard access based on the deployment stage.
- 📜 **Docling Loader Settings**: Simplified the `DoclingLoader` configuration by removing numerous granular settings,
  streamlining its integration into the document processing pipeline.
- 🧑‍💻 **OpenWebUI Image Generation Model**: Changed the default image generation model in OpenWebUI to a generic
  `"image-generation"` identifier for broader compatibility with various image generation services.

### Fixed

- 🐛 **Agent Test Reliability**: Improved the `AgentTestRunner` by introducing a `StopEvent` mechanism, allowing tests to
  complete more rapidly and reliably without relying solely on fixed delays.
- 🧪 **Removed Flaky Test Mark**: Removed the `@pytest.mark.flaky` decorator from a chatbot streaming test, indicating
  increased confidence in its stability and reliability.

### Removed

- 🗑️ **Deprecated API Keys**: Cleaned up the `.env.dev` file by removing `AZURE_OPENAI_KEY_IMAGE`,
  `AZURE_OPENAI_KEY_AUDIO`, and `HUGGINGFACE_API_KEY`, as these are now managed centrally or dynamically within the new
  configuration system.
- 🧹 **Legacy Docker Compose Files**: Eliminated redundant and outdated Docker Compose files, which are now replaced by
  the new dynamically generated configurations for improved maintainability.
- 📜 **Unused License Entries**: Updated `licenses.config.json` by removing entries for services no longer in use (e.g.,
  `rabbitmq`, `kafka`, `airflow`, `grafana`, `prometheus`, and various base image references), ensuring an accurate and
  up-to-date record of third-party licenses.

---

## [v0.252.2] - 2025-11-14 - Streamlined Docker Builds with Enhanced Security

### Security

- 🔑 **Enhanced Runtime Security:** Significantly improved container security across all services by removing `sudo`
  installation and privileges for the non-root user, minimizing potential attack vectors.
- 🔒 **Refined File Ownership:** Configured Docker builds to ensure all application files copied to the runtime image are
  explicitly owned by the non-root user, preventing permission issues and strengthening security best practices.

### Refactor

- ⚡️ **Optimized Docker Image Layers:** Consolidated multiple `RUN` commands into single instructions across all
  Dockerfiles, reducing the number of image layers for smaller image sizes and faster build times.
- 🧹 **Trimmed Runtime Dependencies:** Removed unnecessary system packages (`tree`, `vim`, `iputils-ping`, `libasound2`)
  from service runtime images, creating leaner and more efficient deployments.
- ⚙️ **Standardized Entrypoint Configuration:** Updated `ENTRYPOINT` definitions to the more robust "exec" form
  (`["sh", "-c", "..."]`) in Dockerfiles, enhancing command execution reliability and variable handling.
- 🎯 **Improved Variable Quoting:** Applied proper quoting for the `POETRY_VERSION` environment variable during Poetry
  installation commands, ensuring robustness and preventing potential parsing issues.
- 📁 **Centralized Dagster Home Management:** Standardized the `DAGSTER_HOME` directory for pipeline services to a
  dedicated, securely-owned location (`/dagster_home`), improving consistency and non-root user compatibility.
- 🛠️ **Adjusted Build Tool Availability:** Strategically included the `make` utility in the runtime images for
  `aihub_api`, `aihub_bot`, and `aihub_pipeline` services, ensuring necessary build tools are available only where
  required.
- 📦 **Precise Environment PATH:** Adjusted the `PATH` environment variable for the `default_rag_pipeline` to more
  accurately reference its virtual environment, enhancing environment isolation and reliability.

---

## [v0.252.1] - 2025-11-14 - Strengthened Data Integrity and Pipeline Organization

### Fixed

- 🐛 Corrected the description for the **AIHubUser role**, clarifying that it grants global user access instead of
  administrative access within AI-Hub.

### Changed

- 🛡️ Implemented stricter validation and automatic sanitization for **Namespace and Folder names** in the RAG datalake.
  Names will now be restricted to alphanumeric characters, hyphens, and underscores, enhancing data integrity and system
  compatibility.
- 🔄 Restructured **data pipeline asset keys** by introducing clearer intermediate path segments (e.g.,
  `datalake_to_vectorstore`, `sharepoint_to_datalake`), improving the organization and clarity of data ingestion and
  processing workflows.

### Refactor

- 🧹 Streamlined internal dependencies by updating the import path for **OpenAILike** to directly reference
  `llama_index.llms.openai_like`.

---

## [v0.252.0] - 2025-11-12 - Broadening Horizons: Local Filesystem Integration and Generalized Data Sources

### Added

- 🚀 **New Local Filesystem Ingestion Pipeline**: Introduced a complete pipeline, resource, and I/O manager for
  seamlessly integrating and syncing files from local or network file systems to the data lake, supporting flexible
  regex-based filtering.
- ⚙️ **Generic Source File Abstraction**: Implemented a new `SourceFile` interface and generic factories/operations,
  enabling the pipeline to ingest data from any source system that adheres to this standard, making it highly
  extensible.
- 🏷️ **Pytest `flaky` Marker**: Added official `flaky` marker definition to `pyproject.toml` and applied it to
  unreliable tests, improving test suite clarity and stability by allowing flaky tests to be excluded from CI.
- ➕ **Regex Pattern Utilities**: Introduced helper functions for generating powerful regex patterns, used by the new
  local filesystem resource for flexible file and folder filtering.

### Changed

- 🗓️ **Standardized Source File Timestamps**: Converted all file creation and modification timestamps in source file
  models (e.g., SharePoint) to Unix timestamps (`int`) for consistency and easier processing.
- 🔓 **Relaxed Namespace Naming Constraints**: Removed restrictive regex validation for NamespaceEntity names, allowing
  more flexibility in naming conventions.
- 📈 **Enhanced Metadata Display**: Updated metadata tables to reflect new data structures and added detailed metadata
  display for local filesystem files in the Dagster UI.
- 🔧 **Pipeline Definition Parameters**: Adjusted `default_definitions` to remove the explicit `figures_directory_name`
  parameter and introduced `vector_store_dimensions` and `auto_sync` for more flexible configuration.

### Refactor

- 🗄️ **Abstracted Data Lake Client Operations**: Replaced specific data lake client implementations (Azure, S3) with an
  `AbstractDataLakeClient` interface, standardizing URI construction, file deletion, and directory operations across
  different storage backends.
- ♻️ **Consolidated Source-to-Data Lake Logic**: Replaced SharePoint-specific data lake transformation and cleanup
  factories/operations with new generic `source_to_data_lake` counterparts, reducing code duplication and improving
  maintainability.
- 🖼️ **Simplified Document Loader Configuration**: Streamlined `DoclingLoader` and `DocumentIntelligenceLoader` by
  removing the explicit `figures_directory_name` parameter, making figure directory handling internal and consistent.
- 🔗 **Decoupled Azure Search Metadata Definitions**: Removed Azure Search specific metadata field definitions,
  decoupling the core metadata handling from particular vector store implementations.

### Removed

- 🗑️ **Deprecated SharePoint-Specific Factories**: Eliminated older factories dedicated solely to SharePoint-to-Data
  Lake transformations, superseded by the new generic source ingestion framework.
- ❌ **Legacy SharePoint-Specific Operations**: Removed individual operations for extracting content, metadata, and URIs
  specific to SharePoint files, which are now replaced by their generic `SourceFile` counterparts.

---

## [v0.251.4] - 2025-11-11 - Azure Integration Overhaul and Infrastructure Simplification

### Removed

- 🗑️ **Infrastructure-as-Code (IaC) Module:** The `aihub_iac` module, which provided Pulumi-based Azure infrastructure
  definitions, has been entirely removed from the project, streamlining deployment and management.
- 🗑️ **Azure AI Search Vector Store Integration:** Direct support for Azure AI Search as a vector store option for the
  RAG agent has been removed, simplifying the vector store ecosystem and reducing dependencies.
- 🗑️ **Azure Blob Storage for Anonymous File Access:** The Azure Blob Storage implementation for anonymous file access
  has been removed, standardizing anonymous file access across the platform to S3-compatible services.
- 🗑️ **Azure Cosmos DB for Bot Credentials Setup:** The setup process for Azure Bots no longer supports saving
  credentials to Azure Cosmos DB, exclusively using MongoDB-compatible storage (e.g., FerretDB).
- 🗑️ **Legacy Azure Data Lake (ADLS2) Integration:** Older integration components for Azure Data Lake (ADLS2) and
  associated Dagster resources have been removed, transitioning to a modern, connection string-based approach.
- 🗑️ **Direct Azure Service Integration Clients:** Several direct integration clients and settings for Azure services
  (e.g., Azure Cognitive Search, Blob Storage, Speech Service) have been removed from `aihub_lib/infrastructure/azure`,
  simplifying the core library.
- 🗑️ **Azure-Specific Test Tags and Scenarios:** `@azure` pytest markers and associated test scenarios have been removed
  from agent tests, decoupling the test suite from specific Azure infrastructure components.

### Changed

- 🔄 **Azure Document Intelligence Configuration:** The configuration for Azure Document Intelligence now explicitly
  requires a service endpoint URL and an API key, providing more direct and transparent authentication.
- 🔄 **Azure Data Lake Storage Authentication:** Azure Data Lake Storage integration within pipelines now exclusively
  uses an explicit connection string for authentication, enhancing configuration clarity and security.
- 🔄 **Default Vector Store in Pipeline Examples:** The default and recommended vector store resource used in pipeline
  examples has shifted from Azure AI Search to Milvus, reflecting updated recommendations.
- 🔄 **S3 Anonymous File Access Service Clarification:** The S3 anonymous file access service now explicitly mentions
  SeaweedFS as a compatible backend, clarifying its S3-compatible nature.

### Refactor

- 🧹 **Python Generics Syntax Modernization:** Updated generic type hint syntax across several NATS event and
  publisher/subscriber classes to align with Python 3.12+ features, improving type safety and code readability.
- 🧹 **Centralized Azure Document Intelligence Client Access:** Simplified the method for accessing the Document
  Intelligence client, replacing a custom singleton with direct instantiation using new explicit settings.
- 🧹 **Unified Anonymous File Access Implementation:** The internal implementation of the anonymous file access service
  has been unified to solely rely on S3-compatible storage, removing conditional logic for multiple cloud providers.
- 🧹 **Agent Testing Infrastructure:** The testing setup for agents has been refactored to remove Azure-specific
  configurations and dependencies, making tests more portable and less coupled to particular cloud providers.
- 🧹 **Azure Configuration Reorganization:** Azure-related settings (e.g., Document Intelligence, Data Lake) have been
  reorganized into more specific top-level modules within `aihub_lib/infrastructure/`, improving module clarity.
- 🧹 **Workflow Visualizer Event Naming:** Minor adjustment to the string slicing logic in the workflow visualizer for
  more accurate extraction of event names.

---

## [v0.251.3] - 2025-11-11 - Enhanced Multilingual Documentation and Content Synchronization

### Added

- 📄 **Introduced Multilingual Code Deep Dive**: Added dedicated English and German index pages for the new "Code Deep
  Dive" documentation section, which dynamically pulls READMEs, changelogs, and licenses directly from the codebase.
- 🌍 **Expanded Multilingual Support for Core Documentation**: Implemented automatic generation of both English and
  German versions for the changelog and license documentation, improving accessibility for diverse audiences.

### Changed

- ⚡️ **Optimized LLM Documentation Generation**: Adjusted the process for generating documentation used by Large
  Language Models to exclude the "Code Deep Dive" section from the full content output (`llms-full.txt`), while
  retaining it within the table of contents.
- 🖼️ **Improved Documentation Readability**: Applied minor formatting and line break adjustments across several
  quick-start and architectural decision documents for enhanced clarity.

### Refactor

- 🔄 **Refined Documentation Synchronization Script**: Updated the `sync-docs.sh` script to intelligently manage
  multilingual documentation, ensuring correct cleanup of synced files and automatic duplication of English content to
  German for the "Code Deep Dive" section.

---

## [v0.251.2] - 2025-11-11 - Quick Start Guide Enhancements: Clearer Conversations and Deeper Insights

### Added

- 🎬 **New Video Tutorials:** Introduced two new video tutorials in the "Your First Conversation" guide, visually
  demonstrating how to initiate conversations via the main chat interface and directly through an agent.

### Changed

- 📄 **Revamped "Your First Conversation" Guide:** Significantly expanded and clarified the guide on starting
  conversations with agents, detailing two primary methods and highlighting key features of the chat interface (Open
  WebUI), along with options for model and agent selection.
- 📖 **Enhanced "Your First Insights" Documentation:** Updated the guide to provide comprehensive explanations of
  "Traceability" and "Document Retrieval (RAG)" features, illustrating how users can gain deeper insights into agent
  interactions directly from the chat interface.
- 📝 **Refined "What Just Happened?" Section:** Improved the introductory text and streamlined descriptions for
  navigation options in the quick start summary, enhancing overall readability and guidance.

---

## [v0.251.1] - 2025-11-10 - Streamlined AI Assistant Integration via AGENTS.md Documentation

### Added

- 🦾 **Introduced Comprehensive AI Agent Developer Guides (`AGENTS.md`):** New, in-depth documentation files have been
  added at the project root and within each core Python package (e.g., `aihub_action`, `aihub_agent`, `aihub_api`).
  These guides provide detailed context for AI assistants and developers on package purpose, tech stack, architecture,
  and development workflows.
- ⚙️ **Configured Gemini AI Assistant Context:** A new `.gemini/settings.json` file has been added to explicitly
  instruct the Gemini AI assistant to use the new `AGENTS.md` files for codebase context, ensuring more relevant
  assistance.

### Changed

- 🔄 **Updated Claude AI Assistant Context References:** Existing `CLAUDE.md` configuration files across the repository
  have been updated to reference the new, more specific `AGENTS.md` documentation, enhancing Claude's understanding of
  each package's role and structure.

### Removed

- 🗑️ **Deprecated Generic Gemini Context Files:** The `GEMINI.md` files, which previously pointed to generic `README.md`
  documentation, have been removed from the root and all packages. Their functionality is now superseded by the new
  `.gemini/settings.json` and dedicated `AGENTS.md` files.

---

## [v0.251.0] - 2025-11-10 - NATS-Powered Eventing for Smarter Data Pipelines

### Added

- ✨ **Introduced Event-Driven Document Pipelines:** Implemented new capabilities to automatically trigger data ingestion
  pipelines via NATS events when documents are uploaded and validated.
- 🚀 **New NATS Poller Utility (`JSPoller`):** Added a robust and generic JetStream poller, simplifying asynchronous
  event processing and message acknowledgment from NATS.
- 📄 **`SourceUpdatedEvent` for Data Lake Changes:** Introduced a dedicated NATS event type to signal when a file has
  been updated or uploaded in the data lake, enabling reactive workflows.
- 📦 **Structured Pipeline Topic Managers:** Added `PipelineTopicManager` and `PipelineInstanceTopicManager` to
  standardize NATS subject naming conventions for pipeline-related events, enhancing routing and observability.
- 🚦 **NATS Document Upload Sensor for Dagster:** Integrated a new Dagster sensor that listens for `SourceUpdatedEvent`
  messages on NATS, automatically initiating pipeline runs for newly uploaded documents.
- 🏷️ **Customizable Dagster Schedule Names:** Enabled the ability to assign explicit names to Dagster schedules,
  improving identification and management of periodic tasks.
- 🔗 **NATS Endpoint Configuration for Dagster:** Configured Dagster services to connect to NATS, enabling seamless event
  communication within the pipeline ecosystem.

### Changed

- ⚡️ **Knowledge Document Upload Validation:** The API endpoint for validating document uploads now publishes a
  `SourceUpdatedEvent` to NATS upon successful verification, integrating with event-driven pipelines.

### Refactor

- 🧹 **Unified NATS Topic Manager Design:** Refactored all `TopicManager` classes to inherit from Pydantic's `BaseModel`,
  enhancing type safety, consistency, and data validation across NATS subject generation.
- 🔄 **Standardized Topic Manager Instantiation:** Updated constructors for `AgentClassTopicManager`,
  `AgentInstanceTopicManager`, `ProcessClassTopicManager`, and related classes to use keyword arguments, improving code
  clarity.
- 🦾 **Simplified JetStream Event Replay:** Replaced manual JetStream consumer creation and pull subscription logic in
  `JetStreamEventStore` with the new `JSPoller` utility, streamlining historical event replay.
- 🛡️ **Improved NATS Stream Management for Publishers:** Enhanced `JSPublisher` with a new `ensure_stream_exists`
  method, allowing publishers to proactively verify and create necessary JetStream streams.
- ⚙️ **Cleanup of `observable_data_lake_factory`:** Removed an unused `DataLakeResource` parameter from the
  `observable_data_lake_factory` asset, simplifying its signature.
- 📚 **Centralized Pipeline Constants:** Moved internal pipeline source and target names (e.g., 'datalake', 'knowledge')
  into dedicated constant files for better maintainability and consistency.
- 💬 **Clarified Process Topic Descriptions:** Updated comments for process-related NATS topics to accurately reflect
  their purpose, improving documentation.

---

## [v0.250.2] - 2025-11-07 - Streamlined Local Development and Documentation Clarity

### Added

- ✨ **New Local Development Option (Build from Source):** Introduced `docker-compose.build.yml` to allow developers to
  build and run the entire platform locally directly from source code, facilitating active development and debugging.
- 🎤 **Microphone Access for Open Web UI:** Enabled microphone permissions within the Open Web UI iframe, supporting
  voice-based interactions and features.
- 📄 **macOS mkcert Instructions:** Added specific installation instructions for `mkcert` on macOS to the local
  development prerequisites, improving setup guidance.
- 📊 **Deployment Comparison Summary:** Included a new summary table highlighting the key differences between production
  and local deployment configurations and purposes, enhancing clarity for users.

### Changed

- 🔄 **Refined Local Deployment Strategy:** Reworked local development guidance, clearly separating the use of
  `docker-compose.local.yml` for running with pre-built images (recommended for testing) from the new
  `docker-compose.build.yml` for building from source (for active development).
- 📄 **Enhanced Documentation Structure:** Significantly reorganized and updated the Prerequisites and One-Command
  Deployment documentation, providing clearer, distinct instructions and sections for production versus local
  deployments.
- 🔑 **Local Traefik SSL Configuration:** Modified the local Traefik setup (`docker-compose.local.yml`) to exclusively
  use self-signed SSL certificates via `tls=true` and dynamic file providers, removing the dependency on Let's Encrypt
  for local environments.
- 📋 **Version-Specific Traefik Middlewares:** Updated Traefik configurations for production and nightly builds to load
  middlewares from version-specific files, allowing for more granular control.
- 🛠️ **Improved Audio Transcription Filenaming:** Enhanced the internal logic for naming audio chunks during
  transcription to ensure more unique and descriptive filenames.
- 📝 **Updated Architecture Decisions:** The containerized deployment architecture documentation has been updated to
  reflect the new local development options and their corresponding Docker Compose files.

### Removed

- 🗑️ **Deprecated Central Traefik Middleware File:** The standalone `traefik/middlewares.yml` file has been removed, as
  middleware configurations are now dynamically loaded from specific `configs` directories for better modularity.

---

## [v0.250.1] - 2025-11-07 - Streamlined Deployment and Core Service Upgrades

### Added

- ✨ **Milvus UI Integration**: Introduced **Attu (Milvus UI)**, making vector database management more accessible via a
  dedicated subdomain (`attu.your-domain.com`).
- 🦾 **New RAG Agent**: Added a dedicated `rag_agent` service for enhanced Retrieval Augmented Generation capabilities,
  integrated with core platform services.
- 📄 **Dagster Workspace Configuration**: Introduced `workspace.yaml` files for Dagster, enabling dynamic pipeline
  loading from the `default_rag_pipeline` service.
- 🛡️ **Default Security Headers**: Implemented a new `security-headers` middleware in Traefik to enhance platform
  security by default.

### Changed

- ⚙️ **Refined Deployment Documentation**: Significantly updated and expanded the English prerequisites and one-command
  deployment guides, including detailed DNS, Azure Entra ID token version 2 requirement, and comprehensive app role
  setup instructions.
- 🚀 **Standardized Azure OpenAI Configuration**: Consolidated Azure OpenAI API key management and base URL configuration
  within LiteLLM, simplifying environment setup by using a single `AZURE_OPENAI_BASE_URL` and `AZURE_OPENAI_KEY`.
- 📊 **Updated OpenWebUI**: Upgraded OpenWebUI to `v0.6.28`, bringing various improvements and bug fixes, and updated its
  internal API endpoints to align with the platform's authentication and data access patterns.
- 🧹 **Improved Core Service Health Checks**: Adjusted Docker Compose healthcheck configurations for Phoenix, NATS,
  Valkey, and Milvus UI (Attu) to prevent false-negative restarts and improve startup reliability.
- 🔑 **Updated Authentication Configuration**: Enhanced authentication parameters within the API and Bot services,
  ensuring consistent propagation of OAuth and superuser credentials.
- ⚙️ **Enhanced Pipeline Configuration**: Explicitly passed numerous environment variables to the `default_rag_pipeline`
  service, improving its configurability and robustness.
- 🖼️ **Jupyter Lab Data Volume**: Changed the default data volume for Jupyter Lab from `llama-data` to `jupyter-data`
  for clearer separation of concerns.
- 🔐 **Traefik Dashboard Domain**: Switched the Traefik dashboard host rule from `traefik.localhost` to
  `traefik.${DOMAIN}` for consistent domain usage across the platform.
- 🛠️ **LiteLLM Guardrail Defaults**: Changed default `presidio-mask-guard` and `presidio-block-guard` settings to
  `default_on: false` in LiteLLM configurations, allowing for explicit enablement.
- 📦 **Docling Service Configuration**: Updated the Docling image to `v1.3.1` and refined its configuration with explicit
  artifact paths and model settings.

### Fixed

- 🐛 **Robust Makefile Sourcing**: Modified `aihub_bot/Makefile` to optionally include `.env` files, preventing build
  failures when the file is absent.
- 🩹 **Websocket Endpoint Correction**: Corrected the WebSocket endpoint URL for frontend services from
  `/api/v1/event/ws` to `/api/v1/events/ws` (plural).
- 🔒 **Docling Model Permissions**: Introduced a new `docling-model-permission` service to correctly set ownership for
  model volumes, resolving potential permission issues.
- 🛠️ **PostgreSQL Healthcheck User**: Updated the PostgreSQL healthcheck to use the configured `POSTGRES_USER` variable
  for improved flexibility and consistency.

### Removed

- 🗑️ **German Documentation**: Removed the German versions of the "Prerequisites" and "One-Command Deployment"
  documentation pages to streamline content.

### Refactor

- 🔄 **Centralized Traefik Configuration**: Streamlined Traefik configuration by moving some parameters directly into the
  `command` section and standardizing SSL certificate resolution with Let's Encrypt.

---

## [v0.250.0] - 2025-11-06 - Next-Gen Bot Framework: Microsoft Agents SDK Integration and Multi-Bot Capabilities

### Added

- ✨ **New Bot-in-the-Loop Start Event:** Introduced `BotInTheLoopAgentStartEvent` to provide a more flexible and
  validated way to initiate Bot-in-the-Loop workflows, supporting explicit Teams or Slack configurations from the agent.
- ⚙️ **Structured Slack Configuration:** Added `SlackConfig` within `BotInTheLoopRequestEvent` to enable robust and
  explicit configuration details when initiating Slack interactions.
- 🧪 **Comprehensive Testing Utilities:** Introduced new testing fixtures for mocking MSAL authentication and `aiohttp`
  requests, significantly enhancing test isolation and reliability for `aihub_bot` components.

### Changed

- 🚀 **Upgraded Bot Framework SDK:** Migrated `aihub_bot` components from the legacy `botbuilder` library to the new
  `microsoft-agents` SDK. This fundamental upgrade impacts bot hosting, authentication, activity handling, and overall
  integration with Microsoft Bot Framework channels.
- 🤝 **Enhanced Multi-Bot Conversation Management:** Conversation tracking and persistence (in `ConversationEntity` and
  `ConversationTracker`) now explicitly incorporate `bot_id`. This ensures robust data isolation and prevents collisions
  when multiple bot instances operate across various channels or environments.
- 👤 **Improved Teams User Identity Handling:** Enhanced the process of extracting user identity for Teams interactions,
  leading to more accurate retrieval of `aad_object_id`, email, and roles.
- 🤖 **Refined Bot-in-the-Loop Logic:** Updated the core logic for the `BotInTheLoopAgent` and its handler to seamlessly
  support multi-channel configurations (Teams and Slack) and streamline the sending of proactive messages using the new
  SDK.
- 📄 **Documentation Updates:** Minor updates to documentation `source_sha` values.

### Fixed

- 🐛 **NATS BaseEvent Serialization:** Corrected an issue in `BaseEvent` serialization to ensure all model fields are
  properly dumped during the process.

### Refactor

- 🧹 **Streamlined Bot Activity Models:** Removed the custom `ActivityModel` as the new `microsoft-agents` SDK provides
  direct, improved activity handling, simplifying controller definitions.
- 🔄 **Centralized Bot Message Handling:** Refactored common bot message processing logic into a shared `_handle_message`
  method, simplifying the distinction between direct and channel interactions for Teams and Slack.

---

## [v0.249.4] - 2025-11-06 - Refined Document Metadata for Clearer Source Tracking

### Added

- ✨ **Introduced `source_origin` field:** Documents and nodes now include a new `source_origin` field to explicitly
  store the original external URI (e.g., SharePoint URL) distinct from the data lake URI.

### Changed

- 🔄 **Clarified `source` field definition:** The `source` metadata field for ingested documents and nodes is now
  explicitly defined as the data lake URI.
- 🚀 **Improved document ingestion:** Pipelines for ingesting documents (e.g., from SharePoint, data lake) have been
  updated to correctly capture and differentiate between the data lake URI (now `source`) and the new `source_origin`.

### Removed

- 🗑️ **Deprecated `DATA_LAKE_URI` metadata field:** The `DATA_LAKE_URI` field has been removed to streamline and
  simplify document metadata, with its functionality now handled by the `source` field.

---

## [v0.249.3] - 2025-11-05 - Streamlined LiteLLM API Parameter Handling

### Changed

- 🔄 **Improved LiteLLM Model Parameter Handling:** Configured various LiteLLM models (e.g., `text-generation/mini`,
  `text-generation/small`, `text-generation/large`) across all environments (`dev`, `latest`, `local`, `nightly`) to
  automatically **drop extraneous parameters** from API requests, enhancing compatibility and robustness with underlying
  services.

---

## [v0.249.2] - 2025-11-05 - Enhanced Model Agnosticism and New Azure GPT-5 Series Integration

### Added

- ✨ **New Azure OpenAI GPT-5 Nano Integration**: Introduced direct support for Azure OpenAI GPT-5 Nano via the
  `text-generation/nano` alias, including a dedicated environment variable (`AZURE_OPENAI_KEY_NANO`) and specific
  default temperature settings for optimal performance.
- 🚀 **New Azure OpenAI GPT-5 Series Integration**: Expanded LLM capabilities with support for Azure OpenAI GPT-5 via the
  `text-generation/large` alias, providing access to more powerful generative models.

### Changed

- ⚙️ **Updated LiteLLM Proxy**: The internal LiteLLM dependency has been updated to `v1.77.7-stable`, bringing general
  improvements and stability fixes to the model proxy layer.
- 🤖 **Adjusted Default Fallback and Safety LLM Configuration**: The system's default fallback LLM and the prompt
  injection detection LLM now leverage the newly introduced `text-generation/nano` model alias.

### Refactor

- 🧹 **Standardized Model Aliases Across the Platform**: Implemented a consistent, provider-agnostic model naming scheme,
  replacing previous explicit model names (e.g., `azure/gpt-4o-mini`, `local/qwen-embedding`, `local/reranker`) with
  simplified aliases like `text-generation/mini`, `embedding/small`, `reranker`, `transcription`, `speech`, and
  `image-generation`. This refactoring significantly simplifies model configuration and enhances platform flexibility.
- 🔄 **Unified Model Configuration**: All agent definitions, API endpoints, infrastructure-as-code (IaC), and data
  pipeline configurations have been updated to utilize the new standardized model aliases, ensuring consistency and ease
  of maintenance.
- 📈 **Enhanced LLM Parameter Configuration**: Introduced capabilities for defining default parameters within
  `LLMConfig`, allowing for fine-grained control over model behavior for specific aliases, such as setting a default
  temperature for `text-generation/nano`.

---

## [v0.249.1] - 2025-11-04 - Enhanced Authentication Service Robustness

### Fixed

- 🐛 **Resolved intermittent connectivity issues** with external authentication and identity services (JWKS and Azure
  Graph API) by extending connection timeouts to better accommodate IPv6 fallback mechanisms.

---

## [v0.249.0] - 2025-11-04 - Streamlined Knowledge Management and Enhanced Security

### Added

- ✨ **Introduced Document Upload Endpoints:** Dedicated API endpoints are now available for initiating and validating
  document uploads directly within specific knowledge base databases and namespaces.
- 📄 **New Endpoint for Supported File Types:** A new API endpoint has been added to retrieve a list of supported file
  types for client-side validation of knowledge base document uploads.
- 🔑 **Granular Permissions for Knowledge Base:** Implemented fine-grained access control for knowledge base resources,
  allowing permissions to be defined per database and namespace for enhanced security.
- 🆔 **Added `database_id` to Namespace DTO:** The Namespace Data Transfer Object now includes a `database_id` to provide
  clearer data relationships and context.

### Changed

- 🔄 **Updated Knowledge Base API Routes:** Namespace creation and update endpoints, along with document retrieval, now
  utilize database and namespace names directly as path parameters for improved clarity and consistency.
- 🛠️ **Refined Database Listing for Users:** The `/databases` endpoint now dynamically filters displayed databases and
  namespaces based on the requesting user's granular access permissions, ensuring only accessible resources are shown.
- ⚙️ **Configured CORS for SeaweedFS:** The SeaweedFS S3 gateway now automatically configures Cross-Origin Resource
  Sharing (CORS) rules during initialization, improving compatibility for direct client-side file uploads.
- 🌐 **Web Client Adaptation:** The web application's document management components have been updated to seamlessly
  integrate with the new knowledge base API structure, including the revised document upload and namespace management
  flows.

### Removed

- 🗑️ **Deprecated Generic File Upload Endpoints:** Removed the standalone, generic file upload and validation endpoints
  from the `/files` API, centralizing all document-related uploads under the Knowledge Base domain for better
  organization.

### Refactor

- 🧹 **Centralized Document Upload Logic:** Consolidated all document upload and validation business logic and associated
  Data Transfer Objects (DTOs) from the generic `FileService` to the specialized `KnowledgeService`, enhancing
  modularity and maintainability.
- ♻️ **Renamed File Upload DTOs:** Data Transfer Objects related to file uploads (e.g., `FileUploadRequest` to
  `DocumentUploadRequest`) were renamed to better reflect their new purpose and scope within the Knowledge Base context.

---

## [v0.248.1] - 2025-11-03 - Enhanced Document Processing and Data Lake Organization

### Changed

- 🖼️ **Knowledge Interface Clarity**: The knowledge interface now automatically **excludes generated figure files**
  (artifacts from document processing) from display, providing a cleaner and more focused view of core documents.

### Refactor

- 🧹 **Centralized Figure Directory Management**: The **`__figures__` directory name** used for storing document figures
  has been centralized as a global constant, significantly improving consistency and maintainability across the system.
- 🔄 **Simplified Data Lake Operations**: Streamlined data lake client methods and operations by **removing the explicit
  `figures_directory_name` parameter**, as the directory name is now consistently managed internally.
- ⚙️ **Optimized Document Loaders**: Updated `DoclingLoader` and `DocumentIntelligenceLoader` to utilize the
  **centralized figure directory constant**, simplifying their API and ensuring consistent figure path generation.
- 🛠️ **Refined Resource and Pipeline Definitions**: Cleaned up various resource and pipeline definitions, including
  `DataLakeResource` and associated factories, by **removing redundant `figures_directory_name` parameters**.

### Removed

- 🗑️ **SonarLint Configuration**: Deleted an obsolete SonarLint project configuration file from the codebase.

---

## [v0.248.0] - 2025-11-03 - Smarter Document Understanding: Advanced Table Processing

### Added

- ✨ **Intelligent Table Splitting**: Introduced the capability to automatically split large tables into smaller,
  manageable chunks, ensuring better retrieval and processing of tabular data while respecting token limits.
- 🦾 **LLM-Powered Table Header Detection**: Implemented LLM-driven analysis to accurately identify multi-row table
  headers, improving the precision of table parsing and preserving hierarchical structures during splitting.
- 🧱 **New Dependency `lxml`**: Added `lxml` to enhance HTML parsing and manipulation capabilities, foundational for
  advanced table processing.

### Changed

- 🔄 **Advanced Table Conversion in DoclingLoader**: Modified `DoclingLoader` to now convert Markdown tables into
  structured HTML tables, improving their representation and downstream processing.
- ⚡️ **Optimized Document Intelligence Table Handling**: Streamlined table processing in `DocumentIntelligenceLoader` by
  removing redundant table reformatting, leveraging the new unified table parsing logic.
- 📄 **Improved Markdown Table Parsing**: Enhanced `MarkdownStructuralNodeParser` to intelligently process and chunk
  tables, ensuring headers are preserved and content fits within token limits for improved Retrieval-Augmented
  Generation (RAG) performance.
- 🚀 **Increased Agent Test Timeout**: Extended the `delay_before_stop` parameter in Retrieval Agent tests to provide
  more time for operations to complete, improving test stability.

### Removed

- 🗑️ **Deprecated `NODE_CONTENT_TYPE_TABLE`**: Removed the `NODE_CONTENT_TYPE_TABLE` metadata tag, as table content is
  now directly represented within HTML structures, simplifying content type management.
- 🧹 **Eliminated Redundant Table Reformatting**: The dedicated `reformat_tables` function in
  `DocumentIntelligenceLoader` has been removed, as its functionality is now integrated and optimized within the core
  parsing mechanisms.

---

## [v0.247.7] - 2025-11-03 - Enhanced RAG with Hybrid Search and Model Updates

### Added

- 🚀 **Introduced Hybrid Search Capability:** Enabled **Milvus vector stores** to perform hybrid search queries by
  integrating sparse embeddings and BM25 functionality, improving retrieval relevance.

### Changed

- 🔄 **Default Query Mode to Hybrid:** Updated the default query mode for **RAG and Retrieval agents** to `HYBRID`,
  leveraging the newly added hybrid search capabilities in Milvus for more comprehensive retrieval.
- ⬆️ **Updated Default LLM Model:** Switched the default Large Language Model in **RAG pipelines** from
  `gemma-3-multimodal-small` to `qwen-2.5-multimodal-small`, enhancing model performance and capabilities.

---

## [v0.247.6] - 2025-10-31 - Empowering Contributors with New Guidelines

### Added

- ✨ **Added a comprehensive `CONTRIBUTING.md` guide:** This new document provides clear instructions and best practices
  for anyone looking to contribute to the Swiss AI-Hub project, covering everything from code contributions to
  documentation, community engagement, and advocacy, fostering a more collaborative environment.

---

## [v0.247.5] - 2025-10-31 - Enhanced Security Measures

### Security

- 🔑 **Established comprehensive security policy:** Introduced a new `SECURITY.md` file, providing clear guidelines on
  how to report security vulnerabilities, outlining supported versions, and detailing the coordinated disclosure
  process.

---

## [v0.247.4] - 2025-10-31 - Community Guidelines Established

### Added

- 📄 **Introduced Code of Conduct**: Adopted the Contributor Covenant 3.0 to foster a welcoming, safe, and equitable
  community by outlining expected behaviors, restricted actions, and a clear process for reporting and addressing
  issues.

---

## [v0.247.3] - 2025-10-31 - Empowering Bots with Teams Integration and Enhanced Core Functionality

### Added

- ✨ **Microsoft Teams Support for Bot-in-the-Loop**: Expanded the Bot-in-the-Loop pattern to support Microsoft Teams,
  enabling agents to request human input directly within Teams channels.
- 🚀 **New Makefile Targets**: Introduced `up-dev` for easy development environment startup and `generate-api-token` for
  simplified API token generation. Also added an `agents-playground` target for starting Agents Playground with Azure
  OpenAI configuration.
- ⚙️ **CloudAdapter Caching**: Implemented caching for `CloudAdapter` instances to improve performance and reduce
  repeated authentication overhead in bot routes.
- 📄 **Bot-in-the-Loop Architectural Documentation**: Added a comprehensive explanation to the `README.md` detailing the
  "Handler vs Bot" separation of concerns for the Bot-in-the-Loop pattern.
- 👤 **TeamsConfig Model**: Introduced a `TeamsConfig` Pydantic model in `aihub_lib` to standardize configuration for
  Microsoft Teams interactions within Bot-in-the-Loop requests.
- 🔑 **Dynamic OpenAI Client Acquisition**: Integrated `LiteLLMService` to dynamically acquire the OpenAI client based on
  user identity, enhancing security and flexibility for chat completions.

### Changed

- 🔄 **Bot-in-the-Loop Agent Example**: Updated the `BotInTheLoopAgent` playground example to demonstrate the new
  `TeamsConfig` for multi-channel communication.
- 💬 **Enhanced Content Extraction for Teams**: Improved the `ContentExtractor` to correctly handle HTML content and
  emojis from Microsoft Teams messages, providing richer context to AI models.
- ⚙️ **Centralized Chat Completion Logic**: Refactored the `AgentChatController` and `OpenaiChatController` to
  centralize common request processing logic, improving code maintainability and consistency.
- 📄 **Generalization of Responder Information**: Renamed `SlackResponderInfo` to `BotInTheLoopResponderInfo` and added
  `aad_object_id` to support generic user information across multiple channels like Slack and Teams.
- 🚀 **Bot-in-the-Loop Thread Identification**: Generalized thread identification in `BotInTheLoopHandler` to use
  `thread_identifier` instead of `slack_thread_ts`, accommodating multi-channel requirements.

### Fixed

- 🐛 **Robust Tracing Output**: Ensured `AgentRunTracer` correctly serializes all output events by adding `default=str`
  to `json.dumps`, preventing serialization errors during tracing.
- 🐛 **Teams Conversation Deletion Logic**: Corrected the logic for deleting Teams conversations to prevent unintended
  deletions when a bot is added to a new team or channel.
- 🐛 **Content Extractor Attachment Handling**: Improved the `ContentExtractor` to intelligently skip non-file HTML
  content and emoji image attachments in Teams, preventing processing errors and focusing on relevant files.
- 🐛 **Bot-in-the-Loop Handler Path**: Corrected the base path for `BotInTheLoopHandler` to align with the `/api/v1`
  endpoint structure.

### Refactor

- 🧹 **Conversation Entity Management**: Renamed `delete_conversation` to `delete_conversation_if_exists` in
  `ConversationEntity` and added existence checks for more robust management.
- 🧹 **Internal Method Naming Consistency**: Standardized the naming convention of internal Slack-specific and
  conversation management methods to private (e.g., `_is_slack_channel_message`, `_add_messages_to_conversation`) for
  better encapsulation.

### Removed

- 🗑️ **Deprecated OpenAI Client Parameter**: Eliminated the direct `client` parameter from `OpenaiChatBot` and its
  completion methods, as client acquisition is now handled internally by `OpenaiCompletionHandler` using the new
  `LiteLLMService` integration.

---

## [v0.247.2] - 2025-10-31 - Optimized CI Documentation Builds

### Changed

- 🚀 **Streamlined CI documentation deployment:** Updated the GitHub Actions workflow for documentation deployment to
  utilize a new, optimized build script, enhancing efficiency and reducing build times in continuous integration
  environments.
- ⚙️ **Introduced dedicated `docs:build:ci` script:** Added a specialized `docs:build:ci` command to `package.json`,
  which supports the faster documentation building process for CI by omitting the translation step.

---

## [v0.247.1] - 2025-10-30 - Enhanced Documentation System and LLM Control

### Added

- ⚙️ **Automated Documentation Sync and Translation**: Implemented a new GitHub Actions workflow (`sync-docs`) to
  automatically synchronize and translate documentation during the release process, ensuring documentation is always
  up-to-date and available in multiple languages.
- 🤖 **LLM-Digestible Documentation Generation**: Introduced a new build step that generates consolidated, LLM-optimized
  Markdown files (`llms.txt`, `llms-full.txt`) for each language, enhancing the ability of internal AI tools and coding
  assistants to leverage platform documentation.
- 🇩🇪 **Expanded German Documentation Coverage**: Significantly increased the amount of available documentation in German
  across various platform features, security, and compliance topics.
- 🧰 **Markdown Copy/Download Buttons**: Integrated `vitepress-plugin-llms` to add convenient copy and download buttons
  to Markdown code blocks within the documentation, improving usability for developers.

### Changed

- 🔄 **Documentation Build System Overhaul**: Refactored the core documentation build process, externalizing sidebar
  generation logic to a dedicated module and integrating new plugins for improved maintainability and functionality.
- 🚀 **Documentation Deployment Trigger**: Modified the documentation deployment workflow to be triggered by a
  `release-ready` event from the main release pipeline, ensuring docs are deployed in sync with new software versions.
- 💰 **LLM Proxy Cost Control Configuration**: Activated and documented per-user budget, rate limiting (TPM, RPM), and
  parallel request limits for the LLM proxy, allowing administrators to configure and enforce spending controls via
  environment variables.
- 🌐 **Improved German Translation Guidelines**: Updated translation instructions for LLM models to better handle
  technical terms, avoid over-translation, and correctly manage absolute and relative links, leading to higher quality
  German documentation.
- 📝 **Streamlined RAG Agent Documentation**: Simplified and made more concise the explanation of the RAG Agent's
  principles and functionality in the English documentation.

### Fixed

- 🔗 **Documentation Internal Link Resolution**: Corrected relative and absolute internal links within various compliance
  and platform documentation pages to ensure accurate navigation across the multi-language site.
- 🧹 **Documentation Sync Script Exclusions**: Enhanced the documentation synchronization script to exclude additional
  irrelevant files (e.g., `__pycache__`, `.mypy_cache`) and prevent the creation of orphaned directories from deeply
  nested `README.md` files.

### Refactor

- 📦 **Modularized Sidebar Logic**: Moved the complex sidebar generation logic from `config.mts` to a new, dedicated ES
  module (`sidebar-logic.mjs`), improving modularity and maintainability of the documentation configuration.

### Removed

- 🗑️ **Outdated Deployment Documentation**: Removed redundant and outdated documentation related to OpenStack deployment
  and general code deep dive sections that no longer reflected current practices.
- 🗑️ **Deprecated RAG Pipeline Explanation**: Eliminated a specific RAG pipeline explanation
  (`docs/2_platform/6_pipelines/rag/index.en.md`) as its content has been integrated or superseded by other
  documentation.

---

## [v0.247.0] - 2025-10-29 - RAG Reranking and AI Model Updates

### Added

- ✨ **RAG Document Reranking**: Introduced a new, configurable step in the RAG agent workflow to re-rank retrieved
  documents using a dedicated reranking model (`local/reranker`). This significantly enhances the relevance of
  information provided to the LLM, leading to more accurate answers.
- 🦾 **Reranking Infrastructure**: Added `llama-cpp-reranker` as a new Docker Compose service to support on-premise
  reranking model inference, enabling efficient and localized document re-scoring.
- ⚙️ **Reranking Configuration**: Implemented a new `RerankingConfig` to allow users to easily enable/disable reranking
  and specify the reranking model and `top_n` results.
- 📄 **Reranking Documentation**: Updated the RAG Agent documentation to explain the new "Re-ranking for Relevance" step
  in the RAG Agent's workflow.
- 🧪 **Reranking Test Scenarios**: Added new test scenarios and BDD steps to validate the reranking functionality,
  ensuring its correctness and reliability.
- 🌐 **Reranking Localization**: Included new localization keys (`reranking_results`) across all supported languages for
  enhanced user experience during the reranking step.
- 🔄 **LlamaIndex Node Conversion**: Added a utility to seamlessly convert internal `IngestedNode` objects to LlamaIndex
  `NodeWithScore` objects, facilitating integration with LlamaIndex-based reranking.

### Changed

- ⚡️ **Updated Default AI Models**: Replaced `local/qwen3-small` and `local/gemma-3-multimodal-small` with
  `local/qwen-2.5-multimodal-small` as the default chat model in playground examples and infrastructure configurations,
  improving multimodal capabilities.
- ⚙️ **RAG Agent Workflow**: Modified the `order_nodes_by_documents_step` in the RAG Agent to process nodes after
  potential reranking, ensuring optimal context ordering.
- ⬆️ **LiteLLM Version**: Upgraded the LiteLLM proxy to version `v1.77.7-stable`, bringing the latest features and
  stability improvements.
- 📈 **Increased Token Context Window**: Adjusted the `llama-cpp` service configuration to support a larger context
  window (from 8196 to 16384 tokens) and increased max output tokens (from 4096 to 8196), enabling the processing of
  longer inputs and generation of more comprehensive responses.
- ⚙️ **LiteLLM Guardrail Settings**: Modified LiteLLM configurations to disable heuristic and similarity checks for
  prompt injection by default, while keeping LLM API-based checks enabled for robust security.
- 📊 **RAG Agent Retrieval Settings**: Updated RAG Agent playground configuration to use `index_namespaces=["simple"]`
  and increased `retrieve_k` from 5 to 20 to fetch more diverse initial results for reranking.
- 🩺 **Healthcheck Commands**: Switched `wget` to `curl` in several Docker Compose healthcheck commands for improved
  compatibility and robustness.
- 📄 **Documentation Refinements**: Applied minor formatting and content adjustments across various platform
  documentation pages to improve readability and consistency.

---

## [v0.246.12] - 2025-10-28 - Major Documentation Overhaul and Core Infrastructure Alignment

### Added

- ✨ **Introduced Multi-Language Documentation Support:** The documentation now fully supports English and German, with a
  new automated translation pipeline ensuring content consistency (`.en.md` and `.de.md` files, and `translate-docs.sh`
  script).
- 📄 **Expanded Platform Documentation:** Significant new sections have been added across the platform, covering:
  - **Chat Interface** functionality, observability, and strategic rationale.
  - **Access Management** details, including comprehensive RBAC implementation guidance.
  - **Auditing & Observability** with deep dives into OpenTelemetry and tracing.
  - **Language Models** proxy, anonymization, and input/output guards.
  - **Cost Control** mechanisms and optimization strategies.
  - **Slack & Teams Integrations** concepts and setup.
  - **API Interfaces**: OpenAI-compatible REST, Agent Interaction REST, WebSocket, and Model Context Protocol (MCP)
    servers.
  - **Security**: Detailed documentation on Authentication, Input Validation, Container Security, Network Security, and
    Data Encryption.
  - **Compliance**: Extensive coverage of Data Retention, GDPR, Swiss DSG, EU AI Act, Internationalization, and Data
    Subject Access Requests (DSAR).
  - **User Interface** overview with agent, thread, knowledge, process, and evaluation management.
  - **Agent Fundamentals**, **RAG Agent** mechanics, and **Expert Asking Agent** collaboration patterns.
  - **Pipeline Fundamentals** and the **RAG Ingestion Pipeline**.
  - **Agentic Processes** concepts.
  - **Knowledge Management** organization through namespaces.
  - **Agent Evaluations** for testing and measuring AI agent quality.
  - **External System Integrations** approaches.
- 📚 **New Internal Command for Solution Documentation:** Added a Claude command (`document-solution.md`) to streamline
  the creation and editing of high-level solution concepts.
- ⚙️ **Added Documentation Merger Script:** A new `combine_docs.py` script facilitates merging German markdown files
  from specific directories into a single DOCX document.
- 🔑 **Ensured `pipx` Availability for LLM Tools:** The deployment workflow now explicitly installs `pipx` to manage
  `llm` and `llm-gemini` for automated documentation translation.
- 🚀 **Integrated Gemini for Automated Documentation Translation:** The CI/CD process now leverages the `llm` command
  with the `llm-gemini` plugin for automated translation of documentation.
- 💡 **Introduced `encodings.xml` for IntelliJ Project Settings:** Added a new `.idea/encodings.xml` file to specify
  character encoding for certain project files.
- ☁️ **New Documentation for Openstack Deployment:** Added a new section for setting up and deploying to Openstack
  (`6_code_deep_dive/deployment/index.en.md`).

### Changed

- 🔄 **Updated Core Infrastructure Components:** Object storage was migrated from **MinIO to SeaweedFS**, the NoSQL
  database from **MongoDB to FerretDB**, and the in-memory cache from **Redis to Valkey** across the platform and
  relevant documentation.
- 📖 **Reworked Documentation Structure for Multi-Language Support:** Implemented a new directory structure (renaming
  `.md` files to `.en.md`) and updated VitePress configuration (`.vitepress/config.mts`) to support robust
  multi-language documentation, including dynamic sidebar generation and content rewrites.
- 🗺️ **Enhanced Sidebar Sorting Logic:** Improved documentation sidebar generation to sort entries numerically by prefix
  and then alphabetically, ensuring a more intuitive navigation experience.
- 🔒 **Updated `openssl` command for Key Generation:** Changed the quick start guide to use `openssl rand -hex 32` for
  generating secure random strings, enhancing clarity.
- ✅ **Refined CI/CD Documentation Build Process:** The `deploy-docs.yml` workflow now explicitly includes an automated
  translation step before the main documentation build.
- 📦 **Updated `packageManager` Version:** The `package.json` now specifies `pnpm@10.19.0` for package management.
- 🤖 **Adjusted Claude Command Paths:** Updated the internal `document-feature.md` Claude command to reflect the new
  documentation structure for SDK features (e.g., `3_sdk/1_feature_overview/` and `index.en.md`).

### Removed

- 🗑️ **Deprecated Legacy Feature Overview Sections:** Removed outdated or refactored feature overview documents and
  their respective files (e.g., `2_platform/5_feature_overview/*` and
  `3_sdk/6_feature_overview/expert-agents/index.md`), as content has been integrated into new, more granular sections.
- 🗑️ **Removed Redundant Security Model Documentation:** The dedicated
  `2_platform/2_architecture/4_security_model/index.md` file was removed, as its content is now covered by the expanded
  security documentation.
- 🗑️ **Retired Platform Customization Sections:** Several older customization documents (`2_platform/4_customization/*`)
  were removed as part of the broader documentation overhaul and refactoring into more specific areas.

---

## [v0.246.11] - 2025-10-27 - AI-Hub SDK Documentation: Clarity and Depth for Agent and Pipeline Development

### Added

- ✨ **New Pipeline Documentation Structure:** Introduced dedicated sections for **Pipeline Fundamentals**, **Core
  Pipeline Patterns**, and **Data Ingestion Pipeline**, providing a more structured learning path for building robust
  data workflows. These new guides cover essential concepts like assets, I/O managers, resources, and the two-stage
  ingestion architecture.

### Changed

- 📄 **Expanded Agent SDK Guides:** Significantly enhanced and reorganized documentation for **Quick Start**, **Agent
  Fundamentals**, **Core Workflow Patterns**, **Human in the Loop**, **Multi-Agent Systems**, and **Testing and
  Debugging**. These updates offer greater clarity, detailed explanations, new mermaid diagrams, and practical code
  examples to guide agent development.
- 🚀 **Improved Pipeline Automation Guide:** Rewrote the **Job Scheduling** documentation to clarify the hybrid
  automation strategy, emphasizing observable-driven and change-triggered processing for efficient pipeline automation.
- 🖼️ **Refined SDK Overviews:** Updated the main **Building Agents** and **Building Pipelines** overview pages to
  introduce key principles, simplified quick-start examples, and a more intuitive learning progression for new and
  experienced developers.
- ⚡️ **Minor Documentation Enhancements:** Updated the **Production Deployment** and **Agent Observation** documentation
  for title consistency and minor content additions.

### Removed

- 🗑️ **Deprecated Pipeline Documentation:** Removed outdated documentation pages for **Pipeline Patterns** and **Data
  Ingestion Pipeline**, replacing them with the new, restructured guides for improved clarity and accuracy.

---

## [v0.246.10] - 2025-10-24 - Enhanced Security and Access Control for Data Lake and Workflows

### Added

- 🔑 **New OAuth Configuration Options:** Introduced `OAUTH_TENANT_ID` and `OAUTH_COOKIE_SECRET` environment variables to
  provide more comprehensive control over OAuth2 authentication setups.
- 🔐 **Secure Access for SeaweedFS Filer:** Implemented a new `oauth2-proxy` service to enforce secure, authenticated
  access to the SeaweedFS Filer UI, safeguarding data lake management.
- 👥 **Group-Based Access for SeaweedFS:** Added `SEAWEEDFS_OAUTH_ALLOWED_GROUPS` environment variable, enabling specific
  group-based access control for the SeaweedFS Filer UI.
- 📄 **Expanded OAuth Scopes for Proxies:** Configured `openid`, `email`, and `profile` OAuth scopes for both Dagster and
  SeaweedFS authentication proxies, enhancing user information retrieval during login.
- ➡️ **Configured OAuth Redirect URLs:** Added explicit redirect URLs for both Dagster and SeaweedFS OAuth proxies,
  ensuring correct post-authentication routing.
- 🎨 **Customizable Sign-in Logo:** Enabled support for a custom sign-in logo (`OAUTH2_PROXY_CUSTOM_SIGN_IN_LOGO`) for
  OAuth2 proxies in production and nightly environments, allowing for branded user experiences.

### Changed

- 🔄 **Centralized SeaweedFS Filer Access Routing:** All direct access to the SeaweedFS Filer UI is now routed through
  the newly introduced `oauth2-proxy` service, ensuring a consistent and secure authentication layer.
- 📝 **Renamed Dagster OAuth Proxy:** The generic `oauth2proxy` service dedicated to Dagster has been renamed to
  `oauth2proxy-dagster` for clearer identification and separation of concerns.
- 🛡️ **Standardized Default Access Groups:** Updated the default allowed group for Dagster's OAuth proxy to
  `AIHubDeveloper`, standardizing access control with the `SEAWEEDFS_OAUTH_ALLOWED_GROUPS` variable and aligning with
  common roles.

### Refactor

- 🧹 **Refined OAuth Proxy Architecture:** Streamlined the deployment architecture by separating OAuth2 proxy
  configurations into distinct services for Dagster and SeaweedFS, improving modularity and maintainability.

---

## [v0.246.9] - 2025-10-22 - Streamlined DoclingLoader File Handling

### Refactor

- ⚡️ **Optimized `DoclingLoader` file content retrieval:** Improved the internal efficiency of `DoclingLoader` by
  switching to `fs.cat_file` for more direct and potentially faster reading of file contents.

---

## [v0.246.8] - 2025-10-21 - Core Bot Service Setup and Infrastructure Expansion

### Added

- 🚀 **Introduced a dedicated Bot service** to the core infrastructure, laying the groundwork for new bot functionalities
  and integrations.
- 🌐 **Configured Traefik routing** for the new Bot service, making its API accessible via `bot.<DOMAIN>/api/v1`
  endpoints across all deployment environments.
- ✨ **Added essential environment variables** for the Bot service, including development-only fake authentication
  settings, to streamline local and development deployments.
- 🦾 **Integrated a development-only authentication handler** into the Bot API's core controllers (`HealthController` and
  `OpenaiChatController`), simplifying local testing and development.
- 📦 **Included Gunicorn** as the production web server for the Bot service, optimizing its runtime performance and
  stability.

### Refactor

- 🧹 **Corrected module import paths** within the bot service's Makefile for improved consistency and robustness in
  production builds.

---

## [v0.246.7] - 2025-10-20 - Performance Optimizations and SeaweedFS Development Enhancements

### Added

- 🚀 **Implemented LiteLLM model info caching:** Introduced an LRU cache for LiteLLM model information retrieval, which
  significantly reduces redundant API calls and improves the performance of model lookups.
- ⚙️ **Enhanced SeaweedFS S3 gateway environment configuration:** Added specific environment variables for `S3_PORT`,
  `S3_FILER`, and `S3_BIND_IP`, providing more granular control over the S3 gateway service in the development
  environment.
- ➕ **Exposed SeaweedFS internal ports:** Explicitly exposed SeaweedFS master, volume, and filer gRPC and HTTP ports in
  `docker-compose-gpu.dev.yml` for improved diagnostics and integration.

### Changed

- ⚡️ **Improved asynchronous document loading performance:** Refactored the `DoclingLoader` to offload synchronous file
  reading and response processing to a dedicated thread, preventing event loop blocking and enhancing performance during
  large document ingestions.
- 🔄 **Centralized S3-compatible storage to SeaweedFS in development:** Updated `milvus` and `attu` services in
  `docker-compose-gpu.dev.yml` to depend on the `seaweedfs-s3` gateway instead of a separate MinIO instance,
  streamlining the local object storage setup.
- 💾 **Optimized SeaweedFS volume configuration:** Adjusted `seaweedfs-master` settings to use a `volumeSizeLimitMB` of
  512MB and disabled `volumePreallocate` for more efficient resource utilization in development.

---

## [v0.246.6] - 2025-10-15 - Improved CI/CD Tagging and Release Process

### Added

- 🚀 **Nightly Release Tagging:** Introduced automatic creation and pushing of a `nightly` git tag during the release
  process, which points to the same commit as the versioned release, streamlining access to the very latest builds.
- ⚡️ **Dedicated Docker Tagging Workflow:** Added a new `retag-docker` job to the `set-latest` workflow, allowing for
  more specialized and separated management of Docker image `latest` tags.
- 🛡️ **Source Tag Validation:** Implemented a robust check within the `set-latest` workflow to verify that the source
  tag exists before attempting to move the `latest` git tag, preventing potential errors during automated tagging.

### Refactor

- 🔄 **CI/CD Tagging Workflow Modularity:** Refactored the `set-latest` workflow by renaming the primary job to
  `retag-git` and introducing a new `retag-docker` job, significantly enhancing modularity and clarity in automated
  tagging processes.
- ⚙️ **Streamlined Git Tag Operations:** Updated the `retag-git` workflow with necessary `contents: write` permissions,
  a dedicated `actions/checkout` step, and bot user configuration to ensure secure, reliable, and explicit git tag
  manipulation.

---

## [v0.246.5] - 2025-10-14 - Refined S3 URI Handling in Data Lake Components

### Refactor

- 🧹 **Standardized S3 URI Parsing:** Replaced manual string slicing with the more robust `str.removeprefix()` method for
  parsing S3 URIs across `S3DataLakeIOManager` and `S3DataLakeClient`, enhancing reliability and code clarity.
- ⚡️ **Improved S3 Path Normalization:** Added `lstrip("/")` during S3 URI processing to ensure more consistent and
  robust path handling within the `S3DataLakeIOManager`.
- 📄 **Enhanced S3 Write Logging:** Updated the logging message for successful S3 writes to display the fully
  reconstructed S3 URI, improving clarity and debuggability.

---

## [v0.246.4] - 2025-10-13 - S3 Writing Efficiency and Document Parsing Simplification

### Changed

- 🔄 **Default Document Parser Loader:** The default document parsing loader in `DocumentParserResource` has been updated
  from a 'both' approach (combining Docling and Document Intelligence) to exclusively use **Docling**, providing a more
  predictable out-of-the-box experience.

### Removed

- 🗑️ **'Both' Loader Option for Document Parser:** The `BOTH` loader type option has been removed from
  `DocumentParserResource`, streamlining the configuration for document parsing to either `DOCLING` or
  `DOCUMENT_INTELLIGENCE`.

### Refactor

- ⚡️ **Optimized S3 Object Writing:** The `S3DataLakeIOManager` now writes S3 objects using a single `put_object` call,
  combining content, metadata, and content type settings for improved efficiency and atomic operations.

---

## [v0.246.3] - 2025-10-13 - Enhanced S3 URI Robustness

### Changed

- 🚀 **Improved S3 URI Parsing:** The `S3DataLakeClient` now intelligently handles S3 URIs, automatically prepending the
  "s3://" prefix when a URI starts directly with the configured container name, reducing errors and making input more
  flexible.

---

## [v0.246.2] - 2025-10-10 - Simplified Pipelines, Smarter SharePoint Sync

### Added

- ✨ **SharePoint Integration**: Introduced new `SharePointSettings` for externalizing SharePoint configuration and a new
  factory (`default_sharepoint_to_datalake_definitions`) for easily setting up SharePoint-to-DataLake pipelines.
- 🦾 **Standardized Data Lake Pipelines**: Added a `default_definitions` utility that provides a highly configurable and
  centralized way to define DataLake-to-VectorStore pipelines, promoting reusability and reducing boilerplate.
- ⚡️ **Flexible Data Lake Directory Management**: The `DataLakeResource` and related URI extraction logic now support an
  optional directory name, improving flexibility for data organization within containers.
- ⚙️ **Configurable Bucket Auto-Sync**: Enhanced bucket creation to allow explicit control over the `auto_sync` property
  for `BucketEntity` instances.

### Changed

- 🔄 **RAG Agent Defaults**: Updated the default RAG agent configuration to use a `default` index namespace and
  `defaultknowledge` collection name, streamlining out-of-the-box usage.
- 🔑 **Externalized SharePoint Settings**: SharePoint authentication details are now securely loaded from environment
  variables via `SharePointSettings` rather than being configured directly on the `SharePointResource`.
- 📄 **SharePoint File Type Filtering**: Modified the default `SharePointResource` behavior to include all file types if
  no specific patterns are provided, offering more permissive syncing by default.
- 🧹 **Simplified Data Lake IO Manager Configuration**: Streamlined the prefix generation for Azure Data Lake IO
  managers, making configuration more consistent with container names.

### Refactor

- 🏗️ **Centralized Pipeline Definitions**: Consolidated the definition logic for RAG pipelines into
  `definitions_util.py`, replacing scattered, repetitive configurations in `default_rag_pipeline` and `playground`
  applications.
- ⚡️ **Streamlined Resource Factories**: Refactored data lake and LLM resource factories to support more flexible
  configurations and direct instantiation, reducing complexity.

### Removed

- 🗑️ **Deprecated Data Lake Container Resource**: Eliminated the `DataLakeContainerResource` in favor of a more flexible
  `DataLakeResource` and consolidated pipeline definitions.
- 🗑️ **Redundant Pipeline Boilerplate**: Removed verbose, repetitive pipeline definitions from
  `app/default_rag_pipeline/__init__.py` and `aihub_pipeline/playground/__init__.py` by leveraging the new centralized
  definition utility.

---

## [v0.246.1] - 2025-10-09 - Retrieval Agent Context Customization

### Added

- ✨ **Configurable Context Prompt for Retrieval Agent:** Introduced a new `context_prompt` configuration option for the
  `RetrievalAgent`, allowing users to define a custom prompt that dictates how combined and ordered retrieved nodes are
  formatted.

---

## [v0.246.0] - 2025-10-07 - Modernizing Data Persistence: Introducing SeaweedFS, FerretDB, and Valkey

### Added

- ✨ **SeaweedFS for Scalable Object Storage:** Integrated SeaweedFS as the new S3-compatible distributed file system,
  providing robust and scalable object storage across all deployment environments.
- 💾 **FerretDB as MongoDB-compatible Database:** Introduced FerretDB, a high-performance, MongoDB-compatible database
  that leverages PostgreSQL as its backend, enhancing data flexibility and open-source alignment.
- ⚡️ **Valkey for High-Performance Caching:** Replaced Redis with Valkey, a Redis-compatible fork, for efficient
  in-memory caching and faster data retrieval.
- 🛡️ **Automatic S3 Bucket Configuration:** Enhanced the S3 data lake client to automatically ensure the existence of
  necessary buckets and configure Cross-Origin Resource Sharing (CORS) for seamless web access.
- 🚀 **Docker Compose Services for New Stack:** Added comprehensive Docker Compose services and initialization scripts to
  manage the lifecycle of SeaweedFS (master, volume, filer, S3 gateway), FerretDB (and its PostgreSQL backend), and
  Valkey.

### Changed

- 🔄 **Updated Core Data & Storage Stack:** Migrated the entire core infrastructure from MinIO, MongoDB, and Redis to
  SeaweedFS, FerretDB, and Valkey respectively.
- 📄 **Documentation and README Updates:** Revised `README.md` and quick start guides to reflect the new data persistence
  and caching technologies, including updated environment variables, service descriptions, and console links.
- 🔗 **Service Integration Updates:** Adjusted internal dependencies and connection strings for critical services like
  Milvus, OpenWebUI, and AI-Hub pipelines to seamlessly integrate with the new storage and database components.
- ✅ **Improved Licensing for Core Services:** Switched from AGPL/SSPL-licensed components (MinIO, MongoDB, Redis) to
  more permissively licensed alternatives (Apache-2.0 for SeaweedFS/FerretDB, BSD-3-Clause for Valkey), enhancing
  open-source compliance.

### Removed

- 🗑️ **MinIO S3 Storage Stack:** The entire MinIO setup, including its Docker Compose services, entrypoint scripts, and
  related configurations, has been deprecated and removed.
- ❌ **MongoDB Database:** The MongoDB service and all associated configurations have been entirely replaced and removed
  from the core infrastructure.
- 🚫 **Redis In-Memory Cache:** The Redis service has been replaced by Valkey and removed from all deployment
  configurations.

---

## [v0.245.9] - 2025-10-07 - Enhanced User Data Handling in Authentication

### Changed

- ⚡️ **Improved User Header Encoding**: Switched from Base64 to URL encoding for usernames in authentication headers and
  signatures, enhancing compatibility and robustness when handling special characters.

---

## [v0.245.8] - 2025-10-07 - Streamlined Data Lake Operations and Document Management

### Added

- ✨ **New `RefDoc.get_documents` method:** Introduced a more flexible way to fetch reference documents without requiring
  a namespace filter, enhancing document retrieval capabilities.

### Changed

- 🔄 **Namespace-Agnostic Document Removal:** The document removal process in data lake pipelines now uses the new
  `get_documents` method, making it more flexible and not bound to a specific namespace.
- ⚡️ **Enhanced MongoDB Connection Management:** Implemented explicit `disconnect()` calls in `finally` blocks across
  key utility functions and pipeline definitions, ensuring robust database connection cleanup after operations.
- 🧹 **Refined Bucket and Namespace Utilities:** The `get_db_name_from_bucket_name` and
  `get_or_create_namespace_for_directory` functions now include an `auto_sync` parameter, providing clearer
  differentiation for autoloading versus manual data ingestion pipelines.
- 🚀 **Simplified Pipeline Configurations:** Streamlined parameter passing for bucket and namespace information in
  default RAG and playground pipelines, allowing for direct use of container names and reducing redundant configuration.

### Refactor

- 🛠️ **Centralized Bucket and Namespace Logic:** Extracted and consolidated core bucket and namespace creation/retrieval
  logic into new internal helper functions within `bucket_utils`, improving code organization and reusability.
- 💡 **Optimized Store Name Retrieval:** Removed an unnecessary wrapper function for retrieving the store name in the
  default RAG pipeline, leading to more direct and efficient utilization of the `bucket_utils` functionality.

---

## [v0.245.7] - 2025-10-02 - Agent Guard Message Consistency

### Fixed

- 🐛 **Corrected RAGAgent guard rejection messaging:** Ensured the **RAGAgent** accurately formats system messages for
  guard rejections by using the correct reason property (`event.reason`), improving clarity and consistency in agent
  responses.

---

## [v0.245.6] - 2025-10-01 - Containerization of Aihub Bot for Enhanced Deployment

### Added

- ✨ **Introduced Dockerfile for Aihub Bot:** Added a comprehensive Docker configuration to containerize the Aihub Bot,
  enabling consistent and portable deployments across various environments.
- 🚀 **Streamlined Build and Runtime Environments:** Implemented a multi-stage Docker build process to optimize image
  size and efficiency, ensuring a lean runtime environment.
- 🔒 **Enhanced Operational Security and Dependency Management:** Configured a non-root user for improved security and
  integrated Poetry for robust Python dependency management within the container.

---

## [v0.245.5] - 2025-09-30 - Infrastructure and Developer Experience Enhancements

### Added

- ⚙️ **Introduced `set-latest` GitHub Action:** A new automated workflow for managing container image tags, ensuring the
  `latest` tag is correctly applied to published images, improving deployment consistency.

### Refactor

- 🧹 **Refined Model Data Fetching:** Updated the web application's SDK to use clearer `getModels` API calls and
  `ModelTypeGroupDtoReadable` types, enhancing code readability and maintainability.
- ⚡️ **Optimized ESLint Configuration:** Streamlined the ESLint setup by expanding global ignore rules to skip
  unnecessary files and simplifying plugin imports, leading to faster linting and a cleaner development environment.

---

## [v0.245.4] - 2025-09-30 - Internal Codebase Refinements

### Refactor

- 🧹 **Standardized Event Types:** Aligned internal naming conventions by updating the `ChunkEventReadable` type to
  `ChunkEvent` within the event component resolution logic, enhancing code consistency.

---

## [v0.245.3] - 2025-09-25 - LLM Event Metadata Refinement and Developer Experience Improvements

### Changed

- 🔄 **Updated LLM Event Logging:** Adjusted the **`LLMEvent`** to correctly capture the chat model name using the
  `model_name` property from the agent configuration, ensuring more accurate and consistent event metadata.

### Refactor

- 🧹 **Improved `.gitignore`:** Added a rule to ignore **GitHub Copilot** related files, streamlining the development
  environment setup and reducing repository clutter.

---

## [v0.245.2] - 2025-09-24 - Introducing Advanced Guardrails & Granular Event Visibility

### Added

- 🔑 **Sensitive Information Guard:** Introduced a new guard mechanism to detect and redact sensitive or confidential
  information from LLM responses, significantly enhancing data privacy and security.
- 🦾 **Granular Guard Events:** Implemented a comprehensive suite of new guard events, including
  `AgentSuitabilityAcceptEvent`, `AgentSuitabilityRejectEvent`, `ContextSufficientAcceptEvent`,
  `ContextInsufficientRejectEvent`, `FewShotAcceptEvent`, `FewShotRejectEvent`, `SensitiveInfoAcceptEvent`, and
  `SensitiveInfoRejectEvent`. These events provide detailed insights into guard decisions at various stages of agent
  execution.
- 📄 **Language Detection Event:** Introduced `LanguageEvent` to explicitly capture and signal the detected language of a
  user request, enabling more robust internationalization within agent workflows.
- 🖼️ **Raw Event Data Viewer:** Added the capability to view the raw JSON data for any event directly within the
  frontend, improving debugging and transparency for developers.
- 🧪 **Expanded Frontend Testing Agent:** The `FrontendTestingAgent` now includes new steps to demonstrate various guard
  mechanisms and common workflow events, making it a powerful tool for UI development and testing.
- 🚀 **New LLM Model Support:** Added support for the upcoming `gpt-5` series of models and `minimal` reasoning effort to
  the API models.
- ⚙️ **Enhanced Tool Calling Flexibility:** Introduced more flexible tool calling options, including custom tool
  definitions and explicit allowed tool choices for richer agent-LLM interactions.
- ⚡️ **LLM Stream Obfuscation Option:** Added an `include_obfuscation` option to LLM stream requests, allowing for more
  control over sensitive information during streaming.
- 🌐 **Comprehensive i18n for Guards and Events:** Extended internationalization support to cover all new guard events
  and significantly improved descriptions for various common events in multiple languages.

### Changed

- 🔄 **Standardized Agent Guard Integration:** The `FewShotAgent` and `RAGAgent` have been updated to utilize the new
  standardized `AgentSuitabilityAcceptEvent`, `AgentSuitabilityRejectEvent`, and other specific guard events, ensuring
  consistent guardrail application across agents.
- 🖼️ **Improved Source Node Display:** RAG agent's source node display in the frontend has been significantly improved,
  providing clearer grouping by document, chunk counts, and an explicit message when no relevant chunks are found.
- 💬 **Enhanced Chat History Event Display:** The `LimitChatHistoryEvent` now offers a more detailed and user-friendly
  display on the frontend, showing the limited messages clearly.
- ❓ **Refined Standalone Question Display:** The `StandaloneQuestionCondenserEvent` now has a dedicated and improved
  display in the UI, making the condensed question more prominent.
- 🔍 **Clearer Reranker Output:** The `RerankerEvent` display has been updated to explicitly highlight the `top_k`
  relevant documents chosen by the reranker.

### Fixed

- 🐛 **API Endpoint Duplication:** Addressed a minor issue in the API configuration where a `NotificationController`
  endpoint was inadvertently registered twice.

### Refactor

- 🧹 **Unified Guard Result Structure:** Introduced a base `GuardResult` model and refactored existing guards
  (`agent_description_guard`, `context_sufficient_guard`, `few_shot_guard`) to inherit from it, standardizing the output
  and improving maintainability.
- ⚡️ **Decoupled Guard Rejection:** The `GuardRejectionEvent` now correctly inherits from `GuardEvent` instead of
  `StopEvent`, providing a clearer separation of concerns between guard decisions and workflow control.
- 🗑️ **Internal Event Cleanup:** Removed deprecated `RightAgentEvent` and consolidated internal agent-specific guard
  event classes into the shared `aihub_lib`.
- ⚙️ **Refined Async Test Utility:** The `async_test` decorator in the testing utilities now correctly returns the
  result of the decorated asynchronous function, improving testing flexibility.

---

## [v0.245.1] - 2025-09-24 - LLM Preprocessing, Gemma 3 Support, and Core System Refinements

### Added

- ✨ **Anonymous File Access Storage Configuration:** Introduced a new environment variable,
  `ANONYMOUS_FILE_ACCESS_SERVICE_STORAGE_BACKEND`, to configure the storage backend for anonymous file access services.
- 🦾 **LLM Message Preprocessing:** Implemented automatic preprocessing for LLM messages with a new
  `PreprocessingOpenAILike` wrapper, enhancing model compatibility and performance by merging consecutive messages of
  the same role.
- 📄 **Summary Node Content Type Metadata:** Added `NODE_CONTENT_TYPE` metadata to summary nodes generated by the
  `RecursiveSummaryParser`, providing richer context and improving document structure representation.
- ✨ **Gemma 3 Multimodal Small Model Support:** Integrated comprehensive configuration for the
  `local/gemma-3-multimodal-small` model within LiteLLM, enabling its usage across various agents and pipelines.
- 🚀 **Llama-CPP Cache Volume:** Introduced a dedicated cache volume (`llamacpp-cache`) for the `llama-cpp` service to
  optimize performance and improve stability of local LLM inference.
- 🔑 **HuggingFace API Key for LiteLLM:** Added `HUGGINGFACE_API_KEY` to LiteLLM environment variables, facilitating
  seamless integration with HuggingFace models.
- 🛠️ **Docling Model Permission Helper:** Included a new `docling-model-permission` service to ensure correct file
  permissions for Docling models, improving container startup reliability.

### Changed

- 🔄 **Default LLM Model Update:** Switched the default Large Language Model from `local/qwen3-small` to
  `local/gemma-3-multimodal-small` across `LLMWrappingAgent`, `LlamaIndexAgent`, `RAGAgent`, WebUI, and the default RAG
  pipeline to leverage improved capabilities.
- ⚡️ **RAG Agent Retrieval Configuration:** Optimized retrieval parameters in the RAG Agent by setting
  `check_context_sufficiency` to `False` and reducing `retrieve_k` and `retrieve_prev_next.num_nodes` from 20/10 to 5,
  streamlining retrieval efficiency.
- ⚙️ **Pipeline Configuration Simplification:** Streamlined S3 data lake and Milvus vector store configurations within
  the playground pipeline by removing redundant `directory_name` and `namespace_name` parameters.
- 🚀 **Updated Llama-CPP Service and Configuration:** Upgraded the `llama-cpp` Docker image and updated its command-line
  arguments to officially support the `gemma-3-4b-it` model and enable Flash Attention (`--flash-attn on`) for enhanced
  inference speed.
- ⬇️ **Pinned LiteLLM Service Version:** Explicitly pinned the LiteLLM service to version `v1.50.0` for improved
  stability and compatibility across the system.

### Fixed

- 🐛 **Robust NATS Event Serialization:** Improved the serialization logic for NATS `BaseEvent` to ensure proper handling
  of nested `ChatMessage` and `BaseModel` instances, preventing potential serialization errors and enhancing data
  integrity.

### Refactor

- 🧹 **RAG Agent Test Setup:** Refactored the RAG Agent testing fixtures by introducing a dedicated `test_collection`
  setup and teardown, which improves test isolation and reliability for vector store operations.
- 🔄 **Pipeline Job Parameter Renaming:** Updated pipeline job definitions to use `source_location_name` instead of
  `namespace_name`, aligning with recent Dagster API changes for better clarity and consistency.

---

## [v0.245.0] - 2025-09-18 - Comprehensive Distributed Tracing with OpenTelemetry

### Added

- ✨ **Introduced Comprehensive Distributed Tracing:** Integrated OpenTelemetry across all AI-Hub services to provide
  end-to-end visibility into complex AI workflows.
- 🔭 **New OpenTelemetry Collector Service:** Added a dedicated OpenTelemetry Collector to the development environment,
  simplifying observability data ingestion and routing to various backends like Phoenix.
- ⚙️ **Centralized OpenTelemetry Configuration:** Implemented a new `OpenTelemetrySettings` module for unified
  management of tracing and logging providers across all Python services.
- 🏷️ **Explicit Function Tracing:** Introduced the `@trace_fn` decorator for explicit tracing of key service and
  persistence methods, automatically capturing their inputs and outputs.
- 🚫 **Selective Tracing Control:** Added the `@no_trace` decorator and `SmartTracer` to enable selective disabling of
  OpenTelemetry instrumentation for specific functions or modules, optimizing trace data for relevance.
- 📚 **Deep Observability Documentation:** Introduced new documentation for "Deep Observability with OpenTelemetry" and
  an Architectural Decision Record (ADR) detailing the rationale and implementation of end-to-end tracing.
- 📦 **Automated Library Instrumentation:** Implemented `AihubInstrumentor` for automatic instrumentation of critical
  libraries like `pymongo`, `milvus`, `redis`, `requests`, `httpx`, `aiohttp`, `jinja2`, `botocore`, `llama_index`, and
  `logging`, ensuring broad coverage without manual code changes.
- 📊 **LLM Client Trace Propagation:** Enhanced LLM client configurations to automatically propagate OpenTelemetry trace
  context to underlying model calls, enabling full traceability of generative AI interactions.

### Changed

- 🔄 **Updated NATS Client API for Observability:** Modified NATS `Publisher` and `Subscriber` constructors to require
  explicit naming, which improves trace readability and component identification in observability tools.
- 🚀 **Optimized NATS Development Configuration:** Adjusted NATS development server settings (e.g., `max_payload`,
  `max_connections`) for better performance and resource utilization in local environments.
- 🗺️ **Restructured Documentation Paths:** Updated documentation paths for feature overviews and internal command
  documentation, enhancing overall clarity and consistency.
- 📊 **Enabled OpenTelemetry for LiteLLM:** Configured LiteLLM to activate its native OpenTelemetry callback and
  telemetry, extending distributed tracing to all LLM router interactions.
- 🧩 **Enhanced FastAPI OpenTelemetry Integration:** Implemented FastAPI-specific OpenTelemetry instrumentation,
  including automatic span enrichment with user, service, and request context for API endpoints.

### Refactor

- 🧹 **Overhauled Agent Tracing Architecture:** Replaced the legacy `RunTraceCoordinator` with a new `AgentRunTracer` for
  more robust and flexible agent run and step tracing using a two-span approach.
- 📂 **Consolidated OpenTelemetry Infrastructure:** Centralized OpenTelemetry-related utilities and base instrumentation
  within `aihub_lib/infrastructure/opentelemetry` for improved modularity and maintainability.
- 🔗 **Streamlined Context Initialization:** Refactored `RunContext` and `ThreadContext` initialization in agents to use
  a new `for_topic` class method, simplifying context management from NATS topic information.

### Removed

- 🗑️ **Deprecated Legacy Tracing Modules:** Removed `RunTraceCoordinator` and the generic `tracing` decorator, which
  have been superseded by the new OpenTelemetry instrumentation framework.

---

## [v0.244.2] - 2025-09-16 - Specialized Image Processing and Loader Refinements

### Added

- ✨ **Introduced `ImageLoader`:** A new dedicated document loader for image files, designed to wrap images in HTML
  figure tags for pipeline ingestion, enabling specialized processing without performing OCR or detailed image analysis.
- 🚀 **Integrated `ImageLoader` into Document Parsing:** The new `ImageLoader` is now utilized within the
  `DocumentParserResource` to specifically handle a comprehensive range of image formats (`jpg`, `jpeg`, `png`, `gif`,
  `bmp`, `tiff`, `webp`, `tif`, `heif`).

### Removed

- 🗑️ **Deprecated Asynchronous Loading in Document Intelligence Loader:** The `aload_data` asynchronous method has been
  removed from the `DocumentIntelligenceLoader`, simplifying its API surface.
- 🗑️ **Image Support from Document Intelligence Settings:** Direct support for image file types (`jpg`, `jpeg`, `png`,
  `bmp`, `tiff`, `heif`) has been removed from `AzureDocumentIntelligenceSettings`, aligning the Document Intelligence
  loader's focus solely on structured document processing.
- 🗑️ **Image Support from Docling Settings:** Image-related file types (`image`, `jpg`, `jpeg`, `png`, `tif`, `tiff`,
  `bmp`, `webp`) have been removed from `DoclingSettings`, specializing the Docling loader for textual and specific
  document formats.

### Refactor

- 🔄 **Centralized Image File Handling:** The overall strategy for processing image files has been refactored, dedicating
  the new `ImageLoader` to all image formats and removing redundant image handling capabilities from
  `DocumentIntelligenceLoader` and `DoclingLoader`. This improves modularity and clarifies responsibility across
  document loaders.

---

## [v0.244.1] - 2025-09-16 - Persistence Layer Refinement

### Refactor

- 🧹 **Namespace Entity field renamed:** Renamed the `last_updated` field to `updated_at` in the `NamespaceEntity` for
  improved consistency and clarity in data lake persistence.

---

## [v0.244.0] - 2025-09-15 - Knowledge Base Evolution: Streamlined Uploads, Localized Collections, and Improved Pipeline Harmony

### Added

- 🚀 **Direct File Uploads API:** Introduced new API endpoints for initiating and validating direct file uploads to the
  datalake, and for retrieving a list of supported file types.
- 🖼️ **Frontend Document Upload Modal:** Implemented a new user interface component allowing drag-and-drop file uploads
  directly into knowledge collections.
- ✨ **Knowledge Collection Management API:** New API endpoints for creating and updating knowledge namespaces (now
  referred to as collections).
- 🎨 **Frontend Collection Management UI:** Added user interfaces for creating new knowledge collections and editing
  existing ones, including display names and descriptions.
- 🗄️ **Datalake Entity Models:** Introduced `BucketEntity` and `NamespaceEntity` for a more structured and persistent
  representation of datalake containers and their collections.
- 🗣️ **LLM-Powered Translation Service:** A new `TranslationService` to automatically localize collection display names
  and descriptions using an integrated Large Language Model.
- 📄 **Unified Document DTO:** Added `DocumentDTO` to consistently represent both fully ingested (processed) and
  in-progress (processing) documents across the API and UI.
- 🛡️ **File Type Configuration:** Implemented `FileTypeConfig` to centralize the management of supported file extensions
  and their corresponding MIME types, enhancing upload validation.
- ⚡️ **Knowledge Service Caching:** Integrated `ttl_cache` for efficient caching of knowledge service data, improving
  performance for database and document listings.
- 🌐 **Expanded Internationalization:** Added comprehensive French and Italian translations for core API prompts and all
  new user interface elements, alongside new i18n keys for better clarity.
- 🛠️ **Pipeline Bucket Utilities:** Introduced new utility functions (`bucket_utils`) to dynamically manage the mapping
  between datalake buckets/directories and knowledge base entities.
- 📦 **Container-Level Data Lake Resource:** Added `DataLakeContainerResource` to enable pipeline operations across
  entire datalake containers, supporting multi-namespace processing.
- 🤖 **Agent HITL Events:** Enhanced `AgentDTO` with `hitl_request_events` and `hitl_response_events` to support
  Human-in-the-Loop workflows for agents.

### Changed

- 📝 **Enhanced Knowledge Collection Listings:** The knowledge base now visually differentiates and lists both
  successfully ingested documents and those still undergoing processing.
- 📊 **Enriched Knowledge Base Metadata:** Knowledge databases (buckets) and collections (namespaces) now feature
  localized display names, descriptions, and an `auto_sync` status, providing more context in the UI.
- 🔄 **API Route Standardization:** Renamed `/file` API routes to `/files` for improved consistency across the API
  surface.
- ⚙️ **Refined Pipeline Operations:** RAG pipelines are now optimized to dynamically resolve namespaces and operate on a
  container-wide basis, adapting to the new structured datalake model.
- 💡 **Updated Default LLM Configurations:** Adjusted the default embedding and language model configurations within the
  RAG pipeline to better suit new requirements.
- 🌍 **Locale Handling Extension:** Updated `LocaleHandler` to seamlessly process `LocaleStringEntity` objects, improving
  i18n integration with persistent data.
- 🗃️ **Nullable Document Content:** The `content` field in `IngestedDocument` is now nullable, accommodating scenarios
  where document content may not always be present or fully parsed.

### Removed

- 🗑️ **Legacy Activity Tracking:** Eliminated deprecated endpoints and associated DTOs related to historical spending
  and activity tracking.
- 🧹 **Obsolete `gpt-5` Model References:** Removed `gpt-5` model names from the `ChatCompletionRequest` enum,
  streamlining model selection options.
- ✂️ **Simplified Tool Call Types:** Removed support for custom tool calls and simplified related types in the
  `ChatCompletion` API.
- 🚫 **Redundant Event Fields:** Removed `reasoning_content` from `ChunkEvent` and `ThoughtEvent` and
  `include_obfuscation` from `ChatCompletionStreamOptionsParam`.
- ⚠️ **`minimal` Reasoning Effort:** The `minimal` option for reasoning effort in `ChatCompletionRequest` has been
  removed.
- ❌ **Old Namespace Model:** The legacy `Namespace` Pydantic model has been replaced by the new `NamespaceEntity` and
  `NamespaceDTO`.
- ⛔ **`txt` from Docling Extensions:** Removed `.txt` from the Docling supported extensions list, deferring to the new
  `FileTypeConfig` for document type management.
- 🗺️ **Directory-Specific Data Lake Arguments:** Removed the `directory_name` argument from various Data Lake resources
  and operations, shifting to a more flexible, container-based processing model.
- 🗑️ **DocStore Namespace Configuration:** The `namespace_name` field has been removed from `DocStoreResource`,
  centralizing namespace management within the new datalake entities.

### Refactor

- 🦾 **Standardized Datalake Access:** Abstract `AnonymousFileAccessService` now includes generic methods for generating
  upload URLs, verifying file existence, and listing files, with concrete implementations for Azure and S3 services.
- 🔀 **Centralized Knowledge Listing Logic:** The `get_databases` logic in `KnowledgeService` has been thoroughly
  refactored to leverage the new `BucketEntity` and `NamespaceEntity` data models, providing a unified source of truth.
- 🌐 **Optimized i18n Translation Workflow:** Reorganized the i18n translation structure to seamlessly integrate with the
  new LLM-based translation service.
- ⚙️ **Streamlined Pipeline Resources:** Refactored pipeline asset factories and jobs to align with the new, simplified
  data lake resource model, reducing redundancy and improving maintainability.

---

## [v0.243.10] - 2025-09-13 - Quick Start Documentation Refinement

### Removed

- 🗑️ Removed the extensive **SDK Architecture documentation** from the Quick Start section, which previously detailed
  the `aihub_lib`, `aihub_agent`, `aihub_pipeline`, `aihub_process`, `aihub_api`, and `aihub_bot` packages, as well as
  cross-package integration patterns. This content, previously marked as Work In Progress (WIP), has been temporarily
  cleared.
- 🗑️ Removed the in-depth **"Why our SDK" documentation** from the Quick Start guides, which provided a comprehensive
  comparison with other AI frameworks and platforms. This content, previously marked as Work In Progress (WIP), has been
  temporarily cleared.

---

## [v0.243.9] - 2025-09-11 - Fine-Grained Control Over Document Image Extraction

### Added

- ⚙️ **`include_images` Configuration:** Introduced a new configurable option `include_images` in the
  `DocumentParserResource`, enabling users to specify whether images should be extracted and embedded during document
  parsing.
- 🖼️ **Image Inclusion Parameter:** Added `include_images` as a new parameter to both `DoclingLoader` and
  `DocumentIntelligenceLoader`, providing explicit control over image extraction at the individual loader level.
- 📄 **Figure Content Management:** Implemented the `remove_figure_tags_keep_content` utility within
  `DocumentIntelligenceLoader` to ensure textual content from figures is retained even when image embedding is disabled.

### Changed

- 🔄 **Conditional Image Processing:** Updated **DoclingLoader** and **DocumentIntelligenceLoader** to honor the new
  `include_images` setting, allowing for more flexible document processing where images can be optionally excluded from
  the final document content.
- ⚡️ **Pipeline Integration:** The `parse_document_from_data_lake` operation now passes the `include_images` setting
  from the `DocumentParserResource` to the document loaders, ensuring consistent behavior across the pipeline.

---

## [v0.243.8] - 2025-09-11 - Enhanced Asynchronous Document Loading and Docling Integration

### Added

- ⚡️ **Asynchronous Document Processing**: Introduced asynchronous `aload_data` methods to both `DoclingLoader` and
  `DocumentIntelligenceLoader`, enabling non-blocking document ingestion and improved concurrency.
- 🚀 **Asynchronous Docling API Interaction**: Implemented a comprehensive asynchronous client for the Docling API,
  including robust polling mechanisms for monitoring and retrieving results from long-running jobs.
- ⚙️ **Docling Polling Configuration**: Added new configuration settings, `POLL_INTERVAL` and `MAX_POLLS`, to allow
  fine-tuning the behavior of asynchronous Docling API polling.
- 🧹 **Internal Processing Helpers**: Introduced `_process_docling_response` and `_build_request_body` helper methods to
  encapsulate common logic and improve code clarity within the document loaders.

### Changed

- 🔄 **Async Data Lake Parsing**: The `parse_document_from_data_lake` operation in the data lake pipeline now leverages
  the new asynchronous document loading capabilities, improving overall pipeline efficiency.
- 📄 **Docling Output Streamlining**: The `DoclingLoader` now primarily requests `json` output from the Docling service,
  with Markdown content generated internally from the structured JSON for a more streamlined and flexible process.
- 🖼️ **Improved Docling Image Handling**: Enhanced the internal mechanism for exporting and embedding images into
  Markdown content generated by the `DoclingLoader`, delegating image-to-markdown conversion to the `Picture` object
  itself.

### Refactor

- 🦾 **Consolidated Loader Logic**: Extracted repetitive document processing steps into dedicated, internal helper
  methods across `DoclingLoader` and `DocumentIntelligenceLoader`, reducing code duplication and enhancing
  maintainability.

---

## [v0.243.7] - 2025-09-11 - Streamlined Release Tagging Workflow

### Refactor

- 🔄 **Refactored Release Tagging Workflow:** Improved the internal GitHub Actions workflow responsible for creating and
  pushing release tags. This update ensures that any last-minute changes are incorporated into the main release commit
  via an atomic amend operation, and utilizes a safer `force-with-lease` push strategy. Additionally, redundant tag
  verification steps have been removed to streamline the overall release process.

---

## [v0.243.6] - 2025-09-10 - Robust Release Tagging Workflow

### Fixed

- 🐛 **Corrected Tagging Reference:** Ensured that release tags consistently point to the correct merge commit or the
  latest `main` branch tip in GitHub Actions, particularly for squash and rebase merges, preventing tags from being
  created against incorrect SHAs.

### Changed

- 🚀 **Improved Tag Verification Process:** Enhanced the reliability and feedback of the post-push tag verification in
  GitHub Actions by directly fetching remote tags and performing a local check, providing clearer success and failure
  indications during the release tagging workflow.

---

## [v0.243.5] - 2025-09-09 - Enhanced CI/CD Tag Verification Reliability

### Changed

- ⚡️ **Improved Tag Verification Reliability:** The GitHub Actions workflow for adding release tags now includes
  multiple retry attempts with a brief delay, making the remote tag verification process more robust and resilient to
  transient network issues or eventual consistency delays.

---

## [v0.243.4] - 2025-09-09 - Documentation & Local Setup Enhancements

### Added

- 🏠 **Enhanced Local Development Setup:** Introduced comprehensive documentation for running the AI-Hub locally,
  including details on SSL support, custom domain routing, and configuration with `docker-compose.local.yml` for a more
  production-like development environment.
- 📄 **Expert-Agent Feature Overview:** Added a new documentation page providing an overview of the Expert-Agent
  capabilities within the SDK.

### Changed

- 🌐 **Documentation Navigation Improvements:** Updated numerous internal links throughout the SDK documentation from
  absolute to relative paths, enhancing navigation robustness and portability.

---

## [v0.243.2] - 2025-09-09 - Streamlined Release Process and Robust Tagging

### Changed

- ✅ **Enhanced Initial Tagging Robustness:** Implemented pre-checks to prevent duplicate tags and added explicit error
  handling during the initial tag creation and push, ensuring greater reliability.
- 🚀 **Improved Final Release Tagging:** Upgraded the final tag creation to use annotated tags and incorporated a robust
  verification step to confirm successful remote tag updates.
- 🔐 **Scoped Git Configuration:** Adjusted Git user configuration within workflow steps to use local scope, enhancing
  security and preventing unintended global state changes.

### Refactor

- 🧹 **Streamlined Release Workflow:** Consolidated various dependency management, version updating, and commit
  operations from a standalone job directly into the release finalization process, simplifying the overall workflow.
- 🔄 **Optimized Job Dependencies:** Removed an intermediate `update-and-dependencies` job, streamlining the flow between
  tag computation, changelog generation, license reporting, and final release actions.

---

## [v0.243.1] - 2025-09-03 - Advanced RAG Agent, Secure Local Dev & OpenWebUI Enhancements

### Added

- 🦾 **Advanced RAG Agent**: Introduced a new Retrieval Augmented Generation (RAG) agent, designed for sophisticated
  knowledge retrieval and integration into workflows.
- 🚀 **Secure Local Development Setup**: Implemented a comprehensive local development environment
  (`docker-compose.local.yml`) featuring Traefik, self-signed SSL certificates, and custom `nip.io` domains for a more
  realistic and secure local testing experience.
- 🔑 **`make local-cert` Command**: Added a convenient Makefile target to generate local SSL certificates effortlessly
  using `mkcert` for `localhost` and `nip.io` domains.
- 📄 **Expanded Local Development Documentation**: Provided extensive new documentation in the `README.md` to guide users
  through setting up the enhanced local AI-Hub stack with HTTPS.
- ⚡️ **OpenAI-Compatible OpenWebUI Pipeline**: Introduced a new OpenWebUI pipeline (`openai_pipeline.py`) that offers a
  standard OpenAI-compatible interface for accessing AI-Hub models, complementing the existing event-based agent
  integration.
- 🔔 **Notification System Foundation**: Added a new NotificationController to the API, laying the groundwork for future
  in-application notifications.
- ⚙️ **Dagster Local Workspace Configuration**: Included a `workspace.local.yaml` to simplify the setup and management
  of Dagster pipelines in local development environments.

### Changed

- 🔄 **Core Library Dependency Management**: Transitioned `aihub_lib` dependencies across all core projects (agent, API,
  bot, pipeline, process) from local paths to specific Git tags, ensuring more stable and versioned dependency
  resolution.
- 🛡️ **OpenWebUI API Key Security**: Enhanced security for OpenWebUI's RAG, Audio STT/TTS, and Image Generation API
  calls by switching to the `SUPERUSER_TOKEN`.
- 🌐 **Configurable Phoenix Endpoint**: Updated the Phoenix client to utilize a configurable endpoint, offering greater
  flexibility for integration with monitoring and evaluation systems.
- 📊 **Refined LiteLLM Guardrail Defaults**: Adjusted LiteLLM guardrail defaults for Presidio (mask and block) to be off
  by default and narrowed the default `presidio_language` to "de" for optimized control.
- 🧹 **Standardized Milvus Bucket Naming**: Aligned and standardized the default Milvus bucket name in MinIO
  configurations to "milvus" across environments.
- 📦 **Updated Docling Service**: Upgraded the Docling service to `v1.3.1` and refined its Docker Compose configuration
  for improved model loading and permission handling.
- 🚀 **OpenWebUI Version Update**: Upgraded the OpenWebUI image to `v0.6.22`, incorporating the latest features and bug
  fixes.
- 📝 **Streamlined AI-Hub API OpenAI Endpoints**: Simplified the API's OpenAI endpoints by consolidating methods like
  `get_models_with_assistants` to `get_models`, removing redundant "with assistants" naming.
- 🔒 **Enhanced User Header Encoding**: Implemented base64 encoding for the `X-OpenWebUI-User-Name` header in OpenWebUI
  interactions, improving security and compatibility.

### Removed

- 🗑️ **Deprecated Pipeline Runner Settings File**: Removed `PipelineRunnerSettings.py` to streamline configuration, with
  settings now primarily managed through environment variables.

---

## [v0.243.0] - 2025-09-02 - Refined Image Tagging for Build Action

### Changed

- ⚡️ **Improved Image Tagging:** The `build_image` GitHub Action has been updated to use comma-separated values for
  secondary image tags, ensuring more robust and widely compatible tag assignment for published images.

---

## [v0.242.0] - 2025-09-02 - New Model Catalog and Advanced AI Features

### Added

- 🚀 **Introduced a comprehensive Models overview**: Users can now browse and view detailed information about all
  available AI models, including their capabilities, pricing, and rate limits, through a new dedicated section in the
  application.
- 🦾 **New Model Information API**: A dedicated API endpoint now provides structured access to retrieve lists of AI
  models, grouped by type, and detailed information for individual models.
- 📈 **Core Spending and Activity Tracking DTOs**: Added new data transfer objects to support detailed tracking and
  breakdown of model usage, costs, and API activity.

### Changed

- 🤖 **Expanded Chat Completion Models and Parameters**: The chat completion API now supports new `gpt-5` series models
  and introduces a `minimal` option for reasoning effort, offering more flexibility in AI interactions.
- 💬 **Enhanced Event and Message Schemas**: Updated core event and message structures (`ChunkEvent`, `ThoughtEvent`,
  `UserMessageEvent`) to include additional context such as `reasoning_content` and `model_name`, improving traceability
  and debugging.
- ⬆️ **Dependency Updates**: Upgraded various internal and external dependencies to their latest versions, improving
  performance, stability, and security across the platform.
- 🌐 **Internationalization for Model Features**: Added new translations for German, English, French, and Italian to
  support the new model browsing experience.

### Removed

- 🗑️ **Streamlined Agent DTOs**: Removed `hitl_request_events` and `hitl_response_events` fields from the `AgentDto`
  schema, simplifying agent configuration related to human-in-the-loop interactions.

---

## [v0.241.2] - 2025-08-29 - Streamlined Builds, Dependencies, and Naming

### Added

- 🧰 **Introduced `format-md-win` Makefile target:** Provides a dedicated command for formatting Markdown files
  specifically for Windows development environments, enhancing cross-platform tooling.

### Changed

- 🚀 **Optimized Docker image builds:** Production Docker images for agents, APIs, and pipelines now install dependencies
  without development packages, significantly reducing image size and build times.
- 📦 **Promoted `tomlkit` to core dependency:** The `tomlkit` library is now a primary project dependency, reflecting its
  expanded use beyond development workflows.

### Refactor

- 🔄 **Standardized changelog file naming:** Renamed `changelog.md` to `CHANGELOG.md` across the repository for better
  consistency and adherence to common project conventions, affecting GitHub Actions, documentation scripts, and
  changelog generation.
- 🧹 **Streamlined `mdformat-vuepress` dependency:** The `mdformat-vuepress` plugin is now managed as a standard package
  rather than a local path dependency, simplifying project setup and maintenance.

### Removed

- 🗑️ **Deprecated local `mdformat-vuepress` plugin files:** Removed the now-obsolete local `mdformat-vuepress` source
  files as the plugin is integrated via a standard package manager.

---

## [v0.241.1] - 2025-08-28 - Enhanced Docker Image Tagging and Build Control

### Added

- ✨ **New `secondary_tag` input:** Introduced an optional `secondary_tag` input to all Docker image build workflows,
  enabling more flexible tagging for images (e.g., `latest`, `nightly`).

### Changed

- 🔄 **Conditional Docker Tagging Logic:** The image build action now intelligently applies secondary Docker tags only
  when a value is explicitly provided, preventing the creation of unwanted or empty tags.
- ⚙️ **Dynamic Secondary Tag Assignment:** Build workflows have been updated to dynamically assign secondary Docker tags
  based on the trigger event, defaulting to `nightly` for `repository_dispatch` events, or utilizing the user-specified
  `secondary_tag` input.

---

## [v0.241.0] - 2025-08-28 - Live Thinking Agents and Seamless Open-WebUI Streaming

### Added

- ✨ **Introduced Native Open-WebUI Integration**: A brand-new `aihub_integration` module enables seamless, event-driven
  communication with Open-WebUI via Server-Side Events (SSE), providing a richer and more interactive user experience.
- ⚡️ **Enabled Live Agent Thoughts**: The core streaming mechanism now parses `<think>` tags within LLM outputs,
  allowing agents to stream their internal reasoning ("thoughts") in real-time alongside regular content.
- 🦾 **Exposed Human-in-the-Loop (HITL) Events**: Agents can now declare and discover `HumanInTheLoopRequestEvent` and
  `HumanInTheLoopResponseEvent` types, enabling interactive workflows where human input is explicitly requested.
- 📄 **Dedicated SSE Streaming API Endpoints**: New API endpoints `/api/v1/agents/{class}/{id}/{event}/stream` are
  introduced to support Server-Sent Events, facilitating real-time updates and interactive agent experiences for
  external UIs like Open-WebUI.
- 📚 **Integrated Docling for Document Processing**: Switched to a new `DoclingLoader` for robust document parsing,
  enhancing the platform's ability to ingest and process various document formats.
- 🔑 **Configurable S3 URL Signing Secret**: Added `S3_STORAGE_URL_SIGNING_SECRET` environment variable for enhanced
  security when generating pre-signed URLs for S3 storage.
- ⚙️ **New Docling Service Initialization Script**: A dedicated entrypoint script for the Docling service now automates
  model downloading and ensures proper setup with correct permissions.
- 📊 **Added `aihub_integration` to Core Makefile Checks**: Ensured linting, formatting, and type-checking for the new
  `aihub_integration` module.
- 🚀 **New Open-WebUI Actions for Tracing and Sources**: Pipeline actions `source_action.py` and `tracing_action.py` are
  now integrated into the `aihub_integration` module, providing direct access to agent execution traces and document
  sources from within Open-WebUI.

### Changed

- 🔄 **Refactored Streaming Logic for Thought Events**: The `EventDisplayer` now uses a new `StreamProcessor` and
  `TagParser` to intelligently handle and display both regular and "thinking" content during LLM streaming.
- ⬆️ **Updated RAG Agent Configuration**: The default RAG agent now uses `local/qwen3-small` and an improved embedding
  model (`azure/text-embedding-3-large`), with enhanced retrieval settings (`retrieve_k` to 20, `node_types` to include
  "summary") and a comprehensive system prompt.
- 🚚 **Unified Docker Volume Paths**: Standardized local development/deployment volume paths from `local-volumes` to
  `.docker-volumes` across all Docker Compose configurations, improving consistency.
- 📦 **Upgraded Third-Party Docker Images**: Updated Open-WebUI to `v0.6.22`, Docling to `v1.3.1`, and `llama-cpp` to
  `server-cuda-b5490` with updated model configurations.
- 🔌 **Enhanced Open-WebUI Connection Parameters**: Added specific AI-Hub connection details (`AIHUB_BASE_URL`,
  `AIHUB_SUPERUSER_API_KEY`, etc.) and updated database/S3 endpoints in Open-WebUI Docker configurations for better
  integration.
- 🛡️ **Improved Authentication Strategy Order**: The `TokenAndOauth2Handler` now prioritizes bearer token authentication
  before OAuth2, ensuring more flexible and robust authentication flows.
- ⏳ **Increased Default LLM Request Timeout**: The default timeout for LLM API requests has been extended from 60 to 600
  seconds to accommodate longer processing times.
- 🗑️ **Simplified Chat Message Structure**: `AssistantChatMessage` and `UserChatMessage` are deprecated and replaced by
  the more generic `ChatMessage` from `llama_index.core.base.llms.types`, simplifying message handling across the
  platform.
- 🌐 **Improved Agent Discovery DTOs**: Agent DTOs (`AgentClassDTO`, `AgentDTO`, `AgentInstanceDTO`) now include
  `hitl_request_events` and `hitl_response_events`, providing more complete information about agent capabilities.
- 🎨 **Revised WebUI Styling**: Updated chat message background colors and event display headers for a more polished user
  interface.
- 🛠️ **Refined Docling API Integration**: The `DoclingLoader` now interacts with the Docling service using a revised API
  endpoint and request body format for more reliable document conversions.
- 📝 **Updated Event Display Components**: Frontend components for displaying events (`ChunkEvent`, `ThoughtEvent`,
  `RetrieverEvent`, etc.) have been updated to align with the latest event schema changes and improved user experience.
- 🔍 **Optimized Logging for Libraries**: Default logging level for third-party libraries is now set to `WARNING` during
  development/testing to reduce log verbosity.
- ♻️ **API Path Regex Syntax Fixed**: Corrected regex patterns for path and query parameters in API routes for
  consistency and proper validation.

### Removed

- 🗑️ **Deprecated Open-WebUI OpenAI Proxy Pipelines**: The legacy `aihub_connection.py` and
  `aihub_connection_with_file_sending.py` Open-WebUI pipelines, which mimicked the OpenAI API, have been removed in
  favor of the new, native SSE integration.
- 🧹 **Removed Redundant Chat Message Types**: Custom `AssistantChatMessage` and `UserChatMessage` definitions were
  removed, simplifying the messaging interface by using the universal `ChatMessage` type.
- 🗑️ **Consolidated LiteLLM Model Configurations**: The `local/qwen3-0.6b` and `local/text-embedding-gte` models have
  been removed from LiteLLM configurations, streamlining available model options.
- 🗑️ **Removed Reasoning Content from `ChunkEvent`**: The `reasoning_content` field has been removed from `ChunkEvent`,
  now being explicitly handled by the `ThoughtEvent`.

---

## [v0.240.6] - 2025-08-26 - S3 Security Hardening and Configuration Alignment

### Security

- 🔑 **Enhanced Secret Key Handling:** Updated S3 resource configurations to securely access secret keys using
  `.get_secret_value()`, reinforcing protection for sensitive credentials across S3 file access services and data lake
  clients.

### Changed

- 🔄 **Standardized S3 Endpoint Configuration:** Renamed the S3 configuration parameter `ENDPOINT_URL` to `ENDPOINT` for
  consistency across all related S3 services and resources, simplifying configuration management.

---

## [v0.240.5] - 2025-08-22 - Core Infrastructure Updates and Build System Refinements

### Changed

- 🚀 **Upgraded `aihub_pipeline` Docker images to Python 3.13** from 3.11, leveraging the latest language features and
  performance improvements for pipeline execution.
- ⚙️ **Enhanced CI/CD workflows to support private GitHub dependencies** by configuring SSH, facilitating more robust
  and secure access to internal repositories during automated builds.
- 📦 **Streamlined Docker build processes** by temporarily including the `mdformat-vuepress` module in several service
  images (`aihub_agent`, `aihub_api`, `aihub_pipeline`) to ensure internal tool compatibility.

---

## [v0.240.4] - 2025-08-15 - Enhanced CI/CD Actions with Python Version Flexibility

### Changed

- ⚡️ **Configurable Python Version for Backend Actions**: The `lint_backend` and `test_backend` GitHub Actions now
  support a new `python_version` input. This allows users to specify the Python version used for linting and testing
  within their workflows, providing greater flexibility while maintaining `3.13` as the default.

---

## [v0.240.3] - 2025-08-15 - Core Infrastructure Enhancements and Frontend Streamlining

### Added

- ⚙️ **New Infrastructure Components**: Introduced `Traefik` as an ingress controller and `OAuth2 Proxy` for
  authentication, enhancing deployment capabilities and security.
- 🚀 **Expanded Dagster Deployment Options**: Added new `dagster:latest` and `dagster:nightly` Docker images, providing
  more flexible options for pipeline orchestration.
- 🔒 **SSH Support for GitHub Actions**: Enabled SSH authentication within GitHub Actions to ensure more secure and
  reliable Git operations during release workflows.
- 🐍 **Python 3.13 Support in CI**: Updated GitHub Actions to utilize Python 3.13, aligning with the latest Python
  version for improved compatibility and future-proofing.

### Changed

- 🔄 **Updated Playwright Version**: Upgraded the `Playwright` Docker image to `v1.54.1-jammy`, incorporating the latest
  browser automation features and stability improvements.
- ⚡️ **Streamlined CI/CD Dependency Management**: Refactored Poetry installation and dependency management steps across
  GitHub Actions workflows for enhanced efficiency and consistency.

---

## [v0.240.2] - 2025-08-14 - Architectural Evolution: Containerized Deployment and New AI Capabilities

### Added

- 🦾 **Containerized Deployment Architecture**: Introduced comprehensive Docker Compose files
  (`docker-compose.latest.yml`, `docker-compose.nightly.yml`, `docker-compose-gpu.*.yml`) to enable multi-environment
  deployments for the entire AI-Hub platform, supporting local development, nightly builds, and production-ready setups.
- 📄 **Architectural Decision Records**: Added new documentation (`arc42/decisions`) detailing the rationale and design
  of the new containerized deployment and microservice build pipeline architectures.
- ⚙️ **Modular Dockerfiles for Services**: Introduced dedicated Dockerfiles for `api`, `bot`, `dagster`, `web`,
  `llm_wrapping_agent`, and `default_rag_pipeline` to enable component-specific image builds and deployments.
- ✨ **`LLMWrappingAgent`**: A new generic agent capable of wrapping and exposing Large Language Models as a service
  within workflows, simplifying LLM integration.
- ⚡️ **`DefaultRAGPipeline`**: A new default Retrieval-Augmented Generation (RAG) pipeline, providing out-of-the-box
  capabilities for knowledge retrieval and content generation.
- 🔑 **Milvus Configuration Settings**: Introduced a new `MilvusSettings` class to standardize Milvus database connection
  URL and embedding dimension configuration across the platform.
- 📦 **Multi-Environment Configuration Files**: Added environment-specific configuration files for Dagster, LiteLLM,
  Milvus, and NATS, allowing tailored setups for different deployment environments.

### Changed

- 🔄 **CI/CD Release Workflow Redesign**: Reworked the GitHub Actions release pipeline (`add-tag.yml`) to support a more
  granular, event-driven build and release process for individual microservices.
- 🚀 **Docker Image Build Action Enhancements**: Updated the shared `build_image` action to support secondary tags (e.g.,
  `nightly`) and passing version as a build argument, improving flexibility and versioning.
- 📈 **Agent Test Stability**: Increased `delay_before_stop` in agent test runs to enhance stability and reliability
  during asynchronous test execution.
- 🔒 **Web UI Container Security**: Hardened the Web UI Docker image by introducing a dedicated non-root user for
  improved security posture.
- 🧹 **Markdown Formatting Enforcement**: Integrated `mdformat` into PR readiness, changelog, and license check steps to
  ensure consistent Markdown formatting across the repository.
- 🔗 **Milvus Integration Update**: Updated API and pipeline configurations to leverage the new standardized
  `MilvusSettings`, ensuring consistent and configurable Milvus connectivity.

### Fixed

- 🐛 **API Dockerfile Path Fix**: Corrected a minor syntax error in the API Dockerfile's `PATH` environment variable,
  ensuring proper script execution.

### Refactor

- 📐 **Core Application Restructuring**: Restructured the main application entry points for `aihub_api` and `aihub_bot`
  into `app/main.py` files, improving modularity and maintainability.

---

## [v0.240.1] - 2025-08-13 - Enhanced Documentation Formatting and Tooling

### Added

- ✨ **Introduced Standardized Markdown Formatting**: Added `mdformat` and various plugins to enforce consistent and
  high-quality markdown formatting across all documentation files.
- ⚙️ **Custom VuePress Markdown Support**: Developed and integrated a new `mdformat-vuepress` plugin to ensure proper
  formatting and preservation of custom VuePress `:::` block syntax in documentation.
- 🚀 **New `format-md` Command**: Introduced a `make format-md` command to easily apply the new markdown formatting
  standards across the project.

### Refactor

- 🧹 **Unified Documentation Styling**: Applied a comprehensive set of markdown formatting rules across all documentation
  files, improving readability and consistency.

---

## [v0.240.0] - 2025-08-12 - Streamlined Setup with Superuser Authentication and Enhanced Security

### Added

- ✨ **Global Superuser Authentication**: Introduced a new superuser authentication system, enabling immediate API access
  for external services in containerized or backend-only deployments via a configurable environment variable token. This
  streamlines initial setup and simplifies service integration.
- 🦾 **Automatic Default Role Initialization**: Added the capability to automatically create standard AI-Hub roles (e.g.,
  `AIHubUser`, `AIHubAdmin`) during application startup, simplifying initial deployment and configuration steps.
- 📄 **Comprehensive Authentication Settings**: Introduced new environment variables and settings for general API access
  control, OpenWebUI signing secrets, and configurable OAuth identity provider selection, offering more granular control
  over authentication strategies.

### Changed

- 🔄 **Dynamic Authentication Handler Initialization**: Refactored the core authentication handler
  (`TokenAndOauth2Handler`) to dynamically configure available authentication strategies (superuser, token, OAuth2,
  OpenWebUI) based on environment settings, significantly streamlining setup and enabling more flexible deployments.
- ⚡️ **Enhanced OpenWebUI Authentication**: Improved the OpenWebUI authentication mechanism by migrating from a custom
  hashing scheme to a more robust HMAC-SHA256 signature verification, bolstering security against request tampering.
- 📝 **ADR Documentation Improvements**: Updated the Architecture Decision Records (ADR) process documentation with
  clearer guidance on focusing decisions and a simplified date format for new ADR files.

### Security

- 🔑 **Robust Secret Management**: Migrated the handling of all sensitive configuration parameters (e.g., API keys,
  connection strings, private tokens) to Pydantic's `SecretStr` type. This prevents accidental exposure of secrets in
  logs, debugging output, or system representations, significantly enhancing application security.

### Refactor

- 🧹 **Standardized Application Runner API**: Renamed the method for obtaining the application instance from `get_app()`
  to `create_app()` across all core runners (`ApiRunner`, `BotRunner`, and the base `Runner`), improving API consistency
  and clarity.
- 🔄 **Generalized Identity Provider Naming**: Renamed `MultiStrategyTokenIdentityProvider` to
  `MultiStrategyIdentityProvider` to accurately reflect its role in aggregating various identity provider types, not
  just token-based ones.

---

## [v0.239.0] - 2025-08-08 - Architectural Overhaul: Streamlined AI Integration and Enhanced Development Workflow

### Added

- ✨ **Unified Infrastructure Configuration**: Introduced a new `configs/` directory with `litellm/config.dev.yaml`,
  `milvus/milvus.dev.yaml`, `minio/minio-entrypoint.sh`, and `postgres/init-multiple-dbs.sh`, providing centralized and
  detailed configurations for LiteLLM, Milvus, MinIO, NATS, and PostgreSQL, enabling more flexible and powerful
  development environments.
- 🐳 **New Docker Compose Files for Development**: Added `docker-compose.dev.yml` (CPU) and `docker-compose-gpu.dev.yml`
  (GPU) for simplified local infrastructure setup, including services like LiteLLM, llama.cpp, HuggingFace TEI, and
  improved health checks.
- 📦 **Enhanced Frontend Build and Deployment**: Introduced a multi-stage Dockerfile, `nginx.conf`,
  `config.template.json`, and `plugins/config-loader.client.ts` for `aihub_web`, enabling production-ready Nginx-based
  serving with runtime environment variable injection.
- ⚙️ **Windows Image Mirroring Utility**: Added `mirror-image-win` target to `aihub_iac/Makefile` for convenient Docker
  image mirroring on Windows environments.
- 🧪 **Standardized Local Docker Run Configurations**: New `.idea/runConfigurations` XML files were added to streamline
  building specific Docker images (API, Bot, LLM Wrapping, RAG Pipeline) and running infrastructure on CPU/GPU directly
  from IntelliJ/PyCharm.
- 📄 **New Development Environment File**: Introduced a `.env.dev` file to standardize local development environment
  variables, including API keys and service endpoints.

### Changed

- 🚀 **Optimized CI/CD Backend Testing**: Refined GitHub Actions workflows for backend testing by updating runner types
  to `ubuntu-latest-8-cores`, switching to direct Docker Compose service specification, enabling comprehensive caching
  for Poetry and HuggingFace models, and implementing pre-pulling of Docker images for faster test runs.
- ⬆️ **Updated Python Requirement**: The core project now officially supports and recommends Python 3.13, and related
  documentation in `README.md` and `aihub_doc` has been updated.
- ⚡️ **Increased Test Stability**: Extended the timeout for Docker service health checks in CI/CD workflows to
  accommodate varying startup times and enhance test reliability.
- 🔒 **Flexible Image Build Authentication**: The SSH key requirement for the `aihub_action/build_image` workflow has
  been made optional, providing more flexibility in build environments.
- 🔄 **Refined Makefile Commands**: Added `run-prod` targets for `aihub_api` and `aihub_bot` for standardized
  Gunicorn-based production server startup, and introduced
  `use-local-core-without-install`/`use-remote-core-without-install` for more granular dependency switching.
- 🌐 **Web Frontend Application Structure**: Migrated the Nuxt.js frontend from a generic `.playground` to a dedicated
  `.app` directory, centralizing application-specific configurations and build artifacts.
- 📐 **Milvus Vector Store Dimension**: Increased the default embedding vector dimension for Milvus in agent and pipeline
  configurations from 768 to 1024 to support higher-dimension embedding models.

### Removed

- 🗑️ **Legacy Configuration Files**: Eliminated numerous outdated `.env` files from individual microservice playgrounds,
  centralizing environment variable management to the root `.env.dev` for consistency.
- 🧹 **Deprecated IntelliJ/PyCharm Run Configurations**: Removed old Docker run configurations (`Infra_CPU.xml`,
  `Infra_GPU.xml`, `Webui.xml`) that have been superseded by the new, more flexible configurations.

### Refactor

- 🏗️ **Comprehensive Settings System Overhaul**: Replaced the fragmented `*Config.py` and `*Access.py` classes (e.g.,
  `ApiConfig`, `CosmosAccess`, `NatsConfig`, `PhoenixConfig`, `RedisConfig`, `S3Config`, `DoclingConfig`) with a new,
  unified `EnvironmentSettings` hierarchy. This centralizes environment variable loading and makes configuration more
  consistent and maintainable across the entire platform.
- 🧠 **Unified AI Model Integration with LiteLLM**: Performed a significant architectural shift by refactoring all LLM,
  Embedding, Image Generation, Speech-to-Text, and Text-to-Speech model configurations (`ChatLLMConfig`,
  `EmbeddingLLMConfig`, `AzureOpenAILLMConfig`, `SelfHostedEmbeddingConfig`, `AzureImageModelConfig`, etc.) into a
  streamlined system (`LLMConfig`, `EmbeddingModelConfig`) that leverages **LiteLLM** as a central proxy. This greatly
  simplifies model management, enables dynamic model routing, and reduces hardcoded dependencies on specific AI
  providers within the codebase.
- 🧹 **Streamlined Frontend Scripts and Paths**: Updated `aihub_web/package.json` scripts and `.gitignore` to reflect the
  new `.app` directory structure, ensuring a cleaner and more organized frontend project.
- 🧽 **Cleaned Up `aihub_lib` Structure**: Removed various redundant or now obsolete model and infrastructure
  configuration files and their corresponding `__init__.py` files, significantly reducing complexity and improving code
  clarity in the core library.
- ⚙️ **Standardized Auth Settings Usage**: Migrated authentication logic across agents and API to consistently use the
  new `DangerousDevelopmentOnlyAuthSettings` and `OAuth2Settings`, ensuring uniform handling of fake users and OAuth2
  configurations.
- 📦 **Streamlined Poetry Dependency Management**: Modified `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`,
  and `aihub_process` `pyproject.toml` files to use local path dependencies for `aihub_lib`, simplifying local
  development and CI/CD builds.
- 🧪 **Optimized Agent Test Setup**: Improved agent test runners to copy `.env.dev` to `.env` for consistent environment
  loading during tests and streamlined Poetry dependency installation in CI without redundant `poetry lock` calls when
  using local cores.
- 💬 **Improved LLM Cost Reporting**: Updated `EventDisplayer` to use the `model_name` attribute from the new `LLMConfig`
  for more accurate and consistent cost reporting.

---

## [v0.238.1] - 2025-08-07 - Empowering Developers: New Documentation, Enhanced CI/CD, and AI Assistant Integration

### Added

- 📚 **Comprehensive Documentation System**: Introduced a completely new, structured documentation site using
  **VitePress**, replacing the old markdown files and setting up automated deployment to GitHub Pages. This includes a
  new dynamic sidebar and custom theming.
- 🧑‍💻 **AI Assistant Development Commands**: Added a suite of new commands for Claude Code (`.claude/commands/`),
  including **`create-pr`**, **`document-decisions`**, **`document-feature`**, **`explain`**,
  **`implement-feedback-from-pr`**, and **`update-doc`**, to streamline developer workflows.
- 🔗 **Model Context Protocol (MCP) Integration**: Implemented **MCP support** within the AI-Hub, enabling AI coding
  assistants to observe and interact with running services (API, Phoenix, MongoDB) for enhanced debugging and
  development.
- 🚦 **Automated Version Label Enforcement**: Introduced a new CI check to **enforce version bump labels** (`major`,
  `minor`, `patch`) on all pull requests targeting the `main` branch, ensuring release predictability.
- ⚙️ **PR Agent Configuration Customization**: Added a new **`.pr_agent.toml`** file for comprehensive customization of
  the PR agent's behavior, offering granular control over automated code reviews.
- 🤖 **Standardized AI Context Files**: New **`CLAUDE.md`** and **`GEMINI.md`** files were added across scopes to provide
  context for AI coding assistants.
- ✅ **Prohibited Force Pushes**: Added Git settings to **prohibit force pushes to the `main` branch**, enhancing
  codebase integrity.
- 🧪 **Consolidated Local Testing**: Added explicit `test` targets to `Makefiles` in core microservices (`aihub_agent`,
  `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_process`) for easier and consistent local test execution.

### Changed

- 🚀 **Streamlined CI/CD Versioning**: The automated release workflow now triggers only on **merged pull requests** to
  `main` and dynamically determines the version bump (`major`, `minor`, `patch`) based on PR labels, providing more
  granular control over releases.
- 🧠 **Updated AI Code Review Model**: The PR review workflow now utilizes the **`o4-mini` AI model** and updated API
  versions (`2024-12-01-preview`), enhancing performance and compatibility for automated code reviews.
- 📈 **Improved CI/CD Robustness**: Configured various GitHub Actions workflows to use **`fail-fast: false`**, allowing
  other jobs to continue execution even if one job fails, improving overall CI stability.
- 🔄 **Refined `ApiRunner` and `BotRunner`**: Restructured runners to consistently utilize **`Starlette`** as the base
  application, simplifying internal architecture and supporting multiple mounted applications like the new MCP server.
- 📦 **Standardized Monorepo Dependencies**: Shifted `aihub_lib` dependencies in microservices to **local path references
  (`develop = true`)** instead of Git tags, streamlining local development and cross-project dependency resolution.
- 🔑 **Simplified API Playground Authentication**: The default authentication in the `aihub_api` playground has been
  changed to `DangerousDevelopmentOnlyAuthHandler` for **easier local development setup**.
- 🐍 **Updated Python Action Examples**: Modified Python version in `aihub_action/README.md` examples from 3.13 to
  **3.11** for relevant actions.

### Removed

- 🗑️ **Deprecated Documentation System**: Eliminated the entire old documentation system (`aihub_doc/` markdown files
  and `arc42/` structure), replaced by the new VitePress-based system.
- 🧹 **Obsolete `gitkeep` Files**: Cleaned up empty `.gitkeep` files across the repository.
- ✂️ **Redundant PR Agent Hardcoded Settings**: Removed hardcoded PR agent auto-review settings from the GitHub Action,
  now managed via `.pr_agent.toml`.

### Refactor

- 📊 **Unified Python Testing**: Standardized `test` targets in Makefiles across all Python microservices, simplifying
  local test execution.
- 🎯 **Streamlined CI/CD Configuration**: Centralized PR agent settings into a dedicated `.pr_agent.toml` file, improving
  maintainability of automated review processes.
- 🏗️ **Refined API and Bot Runner Structures**: Simplified base application creation and mounting logic within
  `ApiRunner` and `BotRunner` for a cleaner architecture.

---

## [v0.238.0] - 2025-08-06 - Internal Version Alignment

### Changed

- ⬆️ **Internal Version Alignment:** Updated the version numbers across all core microservices (`aihub_agent`,
  `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and synchronized internal
  dependency tags to `v0.238.0`, ensuring consistent versioning for the new release.

---

## [v0.237.0] - 2025-08-06 - GitHub Action Streamlining

### Removed

- 🗑️ **Removed GitHub Release creation:** The automated step within the build image action that previously created a
  GitHub Release for the built Docker image has been removed.

---

## [v0.236.0] - 2025-08-06 - RAGAgent: Enhanced Control with System Prompts

### Added

- ✨ **System Prompt Configuration for RAGAgent**: Introduced the capability to configure the `RAGAgent` with a system
  prompt. This allows for more precise guidance of the underlying Large Language Model's behavior and responses, with
  built-in support for multi-language prompts using `LocaleString`.
- 🧪 **Comprehensive System Prompt Testing**: Added new test scenarios to validate the `RAGAgent`'s multi-language system
  prompt functionality, ensuring accurate prompt application and response generation.

### Changed

- 🔗 **Streamlined Monorepo Dependency Resolution**: Python microservices (`aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_pipeline`, `aihub_process`) now reference the `aihub_lib` core library using Git tags instead of local paths,
  simplifying CI/CD and enhancing production deployment consistency. This change affects how Python dependencies are
  reported in the `LICENSES.md` file.
- ⚡️ **Extended RAGAgent Test Timeout**: Increased the default delay before stopping RAGAgent test runs to provide more
  robustness and accommodate longer LLM response times.

### Refactor

- 🧹 **Optimized Test Fixture Scope**: Changed the `self_hosted_agent_config` pytest fixture to be session-scoped,
  improving test execution performance by setting up the configuration once per test session instead of per function.

---

## [v0.235.0] - 2025-08-06 - Platform Upgrade and Enhanced License Compliance

### Added

- ✨ **Automated License Compliance Reporting**: Introduced a new, comprehensive system to automatically scan,
  categorize, and report on all Python, Node.js, and Docker image dependencies, generating a detailed `LICENSES.md` file
  for improved transparency and compliance.
- 🔊 **Python 3.13 Audio Compatibility**: Added the `audioop-lts` dependency to the API service to ensure seamless audio
  processing compatibility with Python 3.13.

### Changed

- 🚀 **Python 3.13 Support**: Upgraded all core Python projects to officially support and leverage Python 3.13, enabling
  access to the latest language features and performance improvements.
- ⚙️ **Updated CI/CD Workflows**: Enhanced GitHub Actions workflows for tagging, linting, and testing to align with
  Python 3.13 and integrate the new license checking processes, improving build reliability and compliance checks on
  pull requests.
- 📄 **Documentation Updates**: Reflected the new Python 3.13 requirement in the main `README.md` and action
  documentation for clearer setup instructions.

### Refactor

- 🧹 **Type Hint Modernization**: Migrated `typing_extensions.override` annotations to Python's built-in
  `typing.override` for cleaner and more consistent type declarations, aligning with Python 3.13 standards.

---

## [v0.234.2] - 2025-08-07 - Enhanced PR Agent Configuration and Performance Updates

### Added

- ✨ **Introduced `pr_agent.toml` configuration file:** Enables comprehensive customization of the PR agent's behavior,
  including advanced settings for auto-approval, reasoning effort, code suggestions, and best practices, empowering
  users with greater control over automated reviews.

### Changed

- 🚀 **Updated AI Model and API Versions:** Upgraded the `review-pr` workflow to utilize the `o4-mini` AI model and the
  `2024-12-01-preview` API version, enhancing performance and ensuring compatibility with the latest service
  capabilities.

### Refactor

- 🧹 **Centralized PR Agent Settings:** Migrated several hardcoded PR agent configurations from `action.yml` into the new
  `pr_agent.toml` file, streamlining configuration management and improving overall maintainability.

---

## [v0.234.1] - 2025-08-07 - Platform Evolution: Python 3.13, Automated Compliance, and RAG Agent Enhancements

### Added

- ✨ **Automated License Compliance Reporting**: Introduced a comprehensive system to scan, categorize, and report on all
  Python, Node.js, and Docker image dependencies, generating a detailed `LICENSES.md` file for improved transparency and
  compliance.
- 🔊 **Python 3.13 Audio Compatibility**: Added the `audioop-lts` dependency to the API service to ensure seamless audio
  processing compatibility with Python 3.13.
- 🦾 **RAGAgent System Prompt Configuration**: Introduced the capability to configure the `RAGAgent` with a system
  prompt, allowing for more precise guidance of the underlying Large Language Model's behavior and responses. This
  includes support for multi-language prompts and comprehensive testing.
- 🛡️ **Enforced Main Branch Protection**: Implemented Git settings to explicitly prohibit force pushes to the `main`
  branch, enhancing codebase integrity and preventing accidental history rewrites.
- ✅ **Automated PR Version Label Check**: Introduced a new CI check that ensures all pull requests targeting `main` have
  a `major`, `minor`, or `patch` label, streamlining version management and release predictability.

### Changed

- ⬆️ **Python 3.13 Platform Upgrade**: All core Python projects and CI/CD workflows (`aihub_agent`, `aihub_api`,
  `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) have been upgraded to officially support and
  leverage Python 3.13, enabling access to the latest language features and performance improvements.
- ⚙️ **Refined CI/CD Versioning Strategy**: The automated release workflow now triggers only on *merged pull requests*
  to `main` and determines the version bump (major, minor, or patch) based on PR labels, providing more granular control
  over releases.
- ⚡️ **Increased RAGAgent Test Timeout**: Extended the default timeout for RAGAgent test runs to provide more stability
  and accommodate longer LLM response times in complex scenarios.
- 🔗 **Internal Dependency Tag Synchronization**: Synchronized all internal `aihub_lib` dependency tags across
  microservices to align with the latest versioning, ensuring consistent module integration.
- 🧪 **IntelliJ/PyCharm Test Runner Updates**: Updated various IntelliJ/PyCharm run configurations for Python tests,
  aligning them with `pytest` and modern Poetry virtual environment practices.
- 📝 **Documentation Python Version**: Updated `README.md` to reflect the new Python 3.13 requirement.
- 🌐 **Web Project Name**: Renamed the `aihub_web` project in `package.json` for consistency.

### Removed

- 🗑️ **Deprecated GitHub Release Creation**: Eliminated the automated step within the build image GitHub Action that
  previously created a GitHub Release for each built Docker image, streamlining CI/CD processes.

### Refactor

- 🧹 **Python 3.13 Type Hint Modernization**: Migrated `typing_extensions.override` annotations to Python's built-in
  `typing.override` and simplified `AsyncGenerator` type hints for cleaner and more consistent type declarations,
  aligning with Python 3.13 standards.
- 🧪 **Optimized Agent Test Fixture Scope**: Changed the `self_hosted_agent_config` pytest fixture to be session-scoped,
  improving test execution performance by setting up the configuration once per test session instead of per function.
- 📦 **Streamlined Poetry Setup in CI**: Refined the Poetry installation and caching steps in GitHub Actions workflows,
  improving CI efficiency and consistency.

---

## [v0.234.0] - 2025-08-04 - Major Notification System Overhaul and Web Experience Improvements

### Added

- 🚀 **Comprehensive User Notification System:** Introduced a robust notification system to keep users informed with
  real-time updates and an intuitive interface for managing alerts. This major addition includes:
  - ✨ **New Notification API Endpoints:** Established a full suite of API endpoints for retrieving paginated
    notifications, updating individual notification statuses, and performing bulk actions (e.g., marking multiple as
    read or done).
  - 🔔 **Dedicated Web User Interface:** Launched a new "Notifications" page on the web application, offering a
    centralized view with advanced filtering options (unread, to-do, all), pagination, and bulk management capabilities.
  - 🚨 **Real-time Notification Overlay and Poller:** Integrated a dynamic notification poller and an interactive overlay
    component (a bell icon with a counter badge) directly into the top navigation bar. New notifications are now
    highlighted via toast messages for immediate awareness and quick access.
  - 📚 **Persistent Notification Data Model:** Developed a new database entity and associated service logic for efficient
    storage and management of all user notifications.
- 🌍 **Expanded Internationalization for RAG Agent:** Added German, French, and Italian translations for the RAG Agent's
  name and description, broadening language support for core functionalities.
- ✅ **Enhanced Web Application Readiness Checks:** Incorporated `pnpm lint` into the `aihub_web` Makefile's `pr-ready`
  target, strengthening automated code quality and consistency checks for web changes.

### Changed

- 💬 **Improved API Error Messaging:** Enhanced the web client's error handling to provide more detailed and
  user-friendly error messages in toast notifications, pulling `detail` information directly from API responses.
- 🎨 **Refined Popover Component Styling:** Updated the visual styling of Popover components across the web UI to ensure
  a consistent and modern aesthetic.
- 🌐 **Improved User Experience and Accessibility for Top Bar:** Added tooltips and enhanced `aria-label` attributes to
  the dark mode toggle and notifications icon in the top navigation bar, improving user guidance and accessibility.

### Refactor

- 🔄 **Standardized Agent Event Topic Naming:** Renamed the `AgentTopic` schema and its associated types in the web SDK
  to `AgentInstanceTopic` for clearer terminology and improved consistency within the event topic structure.

### Fixed

- 📄 **Corrected Localization for Process Title:** Addressed an issue where the "Processes" heading on the user detail
  page was not correctly localized, ensuring proper display across all supported languages.

### Removed

- 🗑️ **Deprecated User Avatar Component:** Removed the standalone `User/Avatar.vue` component, as its functionality has
  been streamlined and integrated directly into the `User/Bar.vue` component for better modularity.

---

## [v0.233.0] - 2025-07-30 - Internal Dependency Enhancements

### Changed

- ⚡️ **Internal Dependency Updates:** Upgraded core libraries to enhance stability and prepare for future improvements.

---

## [v0.232.0] - 2025-07-29 - Enhanced Dashboard Trend Clarity

### Changed

- 💡 **Adjusted Trend Indicator Logic:** The trending up/down visual indicators for **Exception Events** on dashboards
  now correctly reflect their severity, displaying green for trending down (good) and red for trending up (bad) to
  provide more intuitive visual feedback.

---

## [v0.231.0] - 2025-07-29 - Enhanced Agent Testing with Custom Events

### Added

- 🚀 **Customizable Agent Simulation Events:** Introduced the ability to specify custom `start_events` and `stop_events`
  for the `SimulatedAgentApiTestRunner`, greatly expanding the flexibility for testing agent behavior and API
  interactions under diverse conditions.
- 🧪 **New Test Event Definitions:** Added `TestStartEvent` and `TestStopEvent` classes to facilitate the creation of
  unique testing scenarios for agent event processing.
- ✨ **Comprehensive Custom Event Test Suite:** Implemented a new test suite (`test_agent_api_with_custom_event.py`) to
  thoroughly validate the handling of custom start and stop events within the agent API, ensuring robust and predictable
  agent responses.

### Changed

- ⬆️ **Version Updates:** Bumped project versions across all core components (aihub_agent, aihub_api, aihub_bot,
  aihub_iac, aihub_lib, aihub_pipeline, aihub_process) and their internal `aihub_lib` dependencies to `v0.231.0`,
  ensuring consistent dependency alignment.

### Removed

- 🗑️ **Internal Claude AI Integration Scripts:** Removed development-specific scripts related to Claude AI integration,
  streamlining the project's internal tooling.

---

## [v0.230.0] - 2025-07-29 - NATS Topic Management and Refined Process Configurations

### Added

- ✨ **Introduced `WalkthroughContext` for Processes**: A new Redis-backed context specifically designed for process
  walkthroughs, enabling robust and persistent state management across complex, multi-step processes.
- 📦 **New Process Configuration Persistence Model**: Implemented dedicated persistence entities (`ProcessConfigEntity`,
  `ProcessConfigEntityDocument`, `ProcessConfigEntityEmbeddedDocument`) to support flexible storage and retrieval of
  process configurations. This includes both class-level defaults and instance-specific overrides stored in the
  database.
- 🚀 **`ProcessConfigSpecs` for Discovery**: Incorporated `ProcessConfigSpecs` into process discovery events, allowing
  clients to programmatically inspect the schema and parameters required for process configurations, enhancing dynamic
  integration.
- 💡 **Direct Event Creation Utilities**: Added `from_raw_data` class methods to `StartEvent` and `ProcessStartEvent`,
  simplifying the creation of these events from raw input data within API and runner contexts.
- ✅ **Comprehensive Process Dispatcher Tests**: Introduced a new, extensive test suite for `ProcessDispatcher` to ensure
  reliable event handling, configuration management, and step execution within processes.
- 🧪 **Enhanced Process Service Database Integration Tests**: Added new tests for `ProcessService` and `ProcessConfig`
  database operations, validating correct interactions with the new persistence model.
- 🤖 **API Endpoint for Agent `StartEvent`**: Exposed a new API endpoint enabling the direct sending of `StartEvent` to
  agents, which facilitates programmatically initiating agent runs with specified configurations.
- 🧪 **New Test Fixtures**: Added `cleanup_db_and_cache` fixtures for agent and process services to improve test
  isolation and ensure clean state in integration and unit tests.

### Changed

- 📈 **Refined Agent and Process API Discovery**: Updated the API discovery mechanisms in `AgentController` and
  `AgentService` to simplify agent listing, and revamped process discovery in `ProcessService` to provide more detailed
  and cache-aware retrieval of process instances and classes.
- 📄 **Event Deserialization Flexibility**: Modified `DispatchableWorkflow` to allow its `get_steps_waiting_for_event`
  method to accept `WorkEvent` types, broadening the dispatcher's capability to react to various process-related events.
- 🗄️ **Improved Event Persistence Logic**: Updated `PersistedAgentEventEntity` and `PersistedProcessEventEntity` to
  correctly utilize the new `AgentInstanceTopic` and `ProcessInstanceTopic` respectively, ensuring accurate data storage
  with the refined topic structure.
- 🧩 **Extended `WorkRequestEvent` with `process_id`**: Added a `process_id` field to `WorkRequestEvent` to enhance
  clarity and provide a direct association with the relevant process instance.
- ✍️ **Enhanced Logging for Subscribers**: Improved logging for `JSSubscriber` to provide more detailed information
  during subscription lifecycle events (start and stop).
- ⚙️ **Process Runner Configuration**: `ProcessRunner` now accepts `default_process_config` and dynamically handles
  process configuration loading, distinguishing between class and instance-specific settings.

### Refactor

- 🔄 **NATS Topic Hierarchy Refinement**: Restructured NATS topics for Agents and Processes to introduce clear
  distinctions between class-level and instance-level communication. This included renaming existing topics (e.g.,
  `AgentTopic` to `AgentInstanceTopic`, `ProcessTopic` to `ProcessInstanceTopic`) and introducing new ones
  (`AgentClassTopic`, `ProcessClassTopic`, `PartialProcessTopic`). Related `TopicManager` and `Subscriber` classes were
  updated to align with this new hierarchy.
- 🧹 **Streamlined Process Discovery Events**: Consolidated and refined process discovery events, replacing a monolithic
  `ProcessDiscoveryResponseEvent` with `ProcessClassDiscoveryResponseEvent` and `ProcessInstanceDiscoveryResponseEvent`
  for more granular information exchange during discovery.
- ⚡️ **Improved Dispatcher `stop` Method**: Enhanced `BaseDispatcher`'s `stop` method to ensure more robust cleanup of
  event stores upon dispatcher termination, improving resource management.
- ⚙️ **Centralized Process Configuration Handling**: Modified `ProcessDispatcher` to robustly manage process
  configurations by prioritizing explicit configurations provided in `ProcessStartEvent` and gracefully falling back to
  default process configurations, leveraging the new `WalkthroughContext`.
- 🏗️ **Core Context Relocation**: Relocated the foundational `BaseContext` class from `aihub_agent` to `aihub_lib`,
  promoting its reusability across all core service modules.
- 🗑️ **Delegator Topic Manager Alignment**: Refactored Agent and Process delegators to align their topic management with
  the new `ProcessClassTopicManager` and `ProcessInstanceTopicManager`, improving consistency and maintainability.
- 🧹 **Agent & Process Service Cleanup**: Streamlined internal methods in `AgentService` and `ProcessService` by adding
  `_` prefix to denote private helper methods and cleaning up redundant caching calls in tests.
- 🛠️ **Process Entity Persistence**: Updated `ProcessEntity` to use `ProcessConfigEntityDocument` for referenced
  configurations and `ProcessConfigEntityEmbeddedDocument` for default configurations, enhancing process config
  persistence.

### Removed

- 🗑️ **Deprecated Generic Discovery Events**: Eliminated the generic `DiscoveryRequestEvent` and the monolithic
  `ProcessTopic` class. These have been superseded by more specific and granular event and topic types, improving type
  safety and clarity in discovery and messaging workflows.
- 🧹 **Redundant Agent Config Start Event Test**: Removed a test file (`test_agent_config_start_event.py`) as its
  functionality is now fully covered by updated and more comprehensive dispatcher tests.

---

## [v0.229.0] - 2025-07-25 - Multi-Cloud Storage for Files and Pipelines

### Added

- ☁️ **Multi-Cloud Storage Abstraction:** Introduced a foundational `AbstractAnonymousFileAccessService` and concrete
  implementations for **Azure Blob Storage** and **S3/MinIO**, enabling consistent file access across various cloud
  providers.
- ⚙️ **Configurable File Access Service:** Added `FileAccessServiceConfig` to dynamically configure and instantiate the
  appropriate file access service based on environment settings, simplifying multi-cloud deployment.
- 🛠️ **S3/MinIO Data Lake Integration:** Implemented `S3DataLakeIOManager` and supporting `S3DataLakeClient` and
  `S3DataLakeFileSystem` resources for Dagster pipelines, bringing robust S3-compatible storage capabilities.
- 🏗️ **Abstracted Data Lake Clients:** Introduced base interfaces (`AbstractDataLakeClient`,
  `AbstractDataLakeClientResource`, `AbstractDataLakeFileSystemResource`) to standardize interactions with different
  data lake storage solutions.
- ⚙️ **S3 Configuration:** Added a new `S3Config` for centralizing MinIO/S3 connection parameters and credentials.

### Changed

- 🔄 **Unified File URL Generation:** Updated `aihub_api` and `aihub_lib` to leverage the newly introduced multi-cloud
  file access services for generating secure, temporary file URLs.
- 🖼️ **Enhanced Image Resolution:** Improved the `combine_nodes_in_order` utility in `aihub_lib` and the frontend image
  component to correctly resolve and display images from both Azure and S3/MinIO storage.
- 🚀 **Cloud-Agnostic Pipeline Operations:** Migrated core pipeline operations (e.g., fetching, deleting files) and their
  associated resources to utilize the new abstract data lake client, improving flexibility and maintainability.
- 🧪 **Playground Configuration:** Adjusted playground examples to showcase the new S3/MinIO data lake capabilities and
  switched the default document parser to `DOCUMENT_INTELLIGENCE`.
- ⬆️ **Dependency Updates:** Upgraded Dagster and related dependencies, and added `boto3` and `s3fs` to support
  comprehensive S3/MinIO integrations.

### Removed

- 🗑️ **Azure AI Search Vector Store:** Discontinued support for Azure AI Search as a vector store option within
  `aihub_pipeline`, streamlining the available vector store integrations.
- 🗑️ **Deprecated `DataLakeFile.from_uri` Static Method:** Removed the static method for creating `DataLakeFile` from a
  URI, as its logic is now encapsulated within cloud-specific `DataLakeClient` implementations.

### Refactor

- 🧹 **Infrastructure Configuration Restructure:** Moved `NatsConfig` and `RedisConfig` into dedicated `infrastructure`
  subpackages for clearer logical grouping and improved project structure.
- 📄 **Improved Docstring Clarity:** Cleaned up and removed redundant parameter descriptions from various
  Infrastructure-as-Code (IAC) and API test fixture docstrings.
- ⚙️ **Centralized DataLakeFile Creation:** Refactored the instantiation logic for `DataLakeFile` objects by moving the
  URI-based creation method into cloud-specific data lake client implementations for better encapsulation and
  maintainability.

---

## [v0.228.0] - 2025-07-25 - Azure Document Intelligence Key Access Alignment

### Refactor

- 🔄 **Updated Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure
  Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

---

## [v0.227.0] - 2025-07-23 - Improved Azure Identity Service Robustness

### Fixed

- 🖼️ **Azure User Profile Image Fetching**: Enhanced the retrieval of user profile images from the Azure Graph API to be
  more resilient to various API errors. The service now gracefully handles non-404 errors by logging warnings and
  consistently returns `None` when an image cannot be fetched, preventing unexpected exceptions and improving stability.

### Refactor

- 🧹 **Import Statement Placement**: Relocated the `asyncio` import to the top-level of the `AzureGraphService` module,
  aligning with best practices for improved code readability and organization.

---

## [v0.226.0] - 2025-07-22 - API Refinements and DTO Consolidation

### Refactor

- 🧹 **Consolidated Data Transfer Objects (DTOs):** Renamed `AgentClass` to `AgentClassDTO` and introduced
  `AgentInstanceDTO`, relocating all agent-related DTOs into a dedicated `dto` subdirectory for improved organization
  and clarity.
- 🔄 **Enhanced DTO Encapsulation:** `AgentInstanceDTO` now manages its own persistence by handling entity
  creation/updates and generating discovery response events directly, improving data model autonomy.
- 🗄️ **Decoupled Agent Persistence:** The `AgentEntity` creation and update logic was refactored to accept explicit
  parameters instead of DTO objects, enhancing the reusability and flexibility of the persistence layer.
- ⚙️ **Standardized Event Specification Handling:** Updated `EventSpec` creation methods to consistently use
  `EventSpecs` objects, improving internal data handling.
- 🔗 **Streamlined Topic Inheritance:** `AgentInstanceDiscoveryTopic` now correctly inherits from
  `AgentClassDiscoveryTopic`, reducing redundancy and clarifying topic structure.

### Changed

- 📄 **Agent Configuration Data Format:** The `ChatService` now passes agent configuration data as a dictionary instead
  of a Pydantic object when publishing `UserMessageEvent`, standardizing data exchange.

### Removed

- 🗑️ **Deprecated Agent DTO Files:** Removed the old `AgentInstance.py` and `aihub_api/aihub_api/agents/__init__.py`
  files as part of the DTO consolidation and relocation effort.
- 🧹 **Redundant NATS Topic Managers:** Cleaned up unused and overlapping topic management methods within
  `AgentClassTopicManager` for a leaner API.
- 🚫 **Transferred Discovery Event Logic:** Removed the `from_agent_instance` method from
  `AgentInstanceDiscoveryResponseEvent` as its functionality has been moved to the `AgentInstanceDTO` for better
  encapsulation.

---

## [v0.225.0] - 2025-07-21 - Enhanced Document Structure and Content Rendering

### Added

- ✨ **Hierarchical Document Headings**: Implemented the dynamic rendering of document headings (H1-H6) directly within
  the context. This provides a clearer hierarchical structure and significantly improves readability and navigation for
  complex documents by showing heading changes as content progresses.
- 📄 **Structured Content and Summary Tags**: Individual node content is now explicitly wrapped in XML-like tags
  (`<content>` or `<summary>`) based on its type. This provides more precise semantic context and better structural
  clarity for each block of text.
- 🔒 **HTML Escaping for Content**: Enhanced the integrity and security of rendered content by automatically escaping
  HTML special characters in both headings and content. This prevents unintended rendering issues and potential
  injection vulnerabilities in the generated output.

### Changed

- ⚙️ **Updated Default Document Language**: The default language for newly ingested nodes has been updated from English
  to German, better aligning with regional configurations.
- ⚡️ **Refined Node Sorting Logic**: Improved the internal sorting mechanism for nodes within a document. Nodes are now
  ordered more accurately based on their section start lines and type, which is crucial for the correct presentation of
  the new hierarchical structure.
- 🧹 **Streamlined Timestamp Handling**: An internal utility for formatting Unix timestamps has been removed, as date and
  time handling for document metadata is now managed more efficiently by the underlying system.

---

## [v0.224.0] - 2025-07-21 - Flexible Agent Configuration and Advanced Discovery

### Added

- ✨ **Dynamic Agent Configuration:** Agent configurations can now be dynamically provided via a `StartEvent` or loaded
  from a database, offering greater flexibility and allowing custom overrides of default agent settings.
- 🚀 **Enhanced Agent Discovery Mechanism:** Implemented granular discovery for agent *classes* and specific agent
  *instances*, enabling the system to distinguish between an agent's base definition and its runnable, configured
  versions.
- 🗄️ **Database Persistence for Agent Configurations:** Custom agent configurations can now be saved and retrieved from
  the database, enabling persistent and shareable agent setups across deployments.
- 🔌 **New Pydantic Models for Vector Store Configurations:** Introduced dedicated Pydantic configurations for
  `AzureAISearchVectorStore` and `MilvusVectorStore` (`AzureAISearchVectorStoreConfig`, `MilvusVectorStoreConfig`),
  allowing for direct embedding and validation of vector store settings within agent configs.
- 📈 **`agent_class` Field in `AgentConfig`:** A new `agent_class` field has been added to `AgentConfig` for consistent
  agent class identification throughout the system.
- 📄 **`save_config.py` Example:** A new example demonstrating how to persist agent configurations to the database for
  custom or production deployments.
- 🧪 **Comprehensive Tests for Agent Config/Discovery:** Added extensive new tests covering the new dynamic configuration
  and discovery mechanisms within the `AgentDispatcher` and `AgentService`.
- 🌐 **API Acts as a Discoverable Agent Instance:** The API now actively participates in the instance-level agent
  discovery, allowing it to expose configured agent instances dynamically.
- 🌍 **`LocaleStringEntity` for Database Localization:** Introduced a dedicated persistence entity for localized strings,
  enabling more robust internationalization within the database.

### Changed

- ⚙️ **Refined Agent Configuration Loading Logic:** The agent dispatcher now intelligently loads configurations,
  prioritizing those provided in a `StartEvent`, then database-persisted configurations, and finally falling back to the
  `default_agent_config` defined in the runner.
- 🏗️ **Updated Agent Runner Initialization:** Agent runners now explicitly accept a `default_agent_config` parameter,
  clearly defining the base configuration for new agent runs.
- 💡 **Improved Type Specificity for LLM and Embedding Configs:** Agent configurations (e.g., in `RAGAgent`) now utilize
  more precise type unions for LLMs and embedding models, enhancing type safety and clarity.
- 🔗 **Streamlined Vector Store Integration:** RAG and Retrieval agents now leverage the `.to_llama_index()` method
  directly from the new Pydantic vector store configurations for more consistent and encapsulated integration.
- ⚡️ **Enhanced Background Task Management:** Improved handling of `asyncio.Task` instances within dispatchers,
  subscribers, and tracers to ensure proper lifecycle management and prevent premature garbage collection.
- 🌐 **Revised API Agent Discovery:** The API now discovers and exposes full agent *instances* (including their specific
  configurations) instead of just class definitions, reflecting the new dynamic configuration capabilities.
- 📚 **Documentation Updates:** Agent examples in `aihub_doc/5_agents_in_detail.md` revised to reflect updated
  `AgentConfig` and removed `system_prompt`.
- 🏷️ **Agent Class Naming Consistency:** Agent class names are now consistently PascalCase in API tests for improved
  standardization.

### Fixed

- 🐛 **Robust Profile Image Fetching:** Improved `AzureGraphService` to gracefully handle 404 responses when fetching
  user profile images, preventing errors for users without an image.
- 📝 **Typo in Process Description:** Corrected a minor typo in the `ProcessDTOSchema` description within the web SDK.

### Refactor

- 🔄 **Consolidated Agent Configuration Management:** Standardized agent configuration handling across the system,
  enabling dynamic overrides and database persistence for agent instances.
- ✨ **Refined Agent and Event Discovery Architecture:** Overhauled the discovery mechanism to support both class-level
  and instance-level agent introspection, providing more granular control and information.
- 🏗️ **Reorganized API DTOs for Agent Representation:** Introduced dedicated DTOs (`AgentClass`, `AgentInstance`,
  `MinimalAgentDTO`) to clearly separate the concept of an agent's definition from its configured, runnable instances in
  the API.
- 📦 **Streamlined Vector Store Configuration:** Replaced direct factory calls for `MilvusVectorStore` and
  `AzureAISearchVectorStore` with new Pydantic-based `*VectorStoreConfig` models and their `to_llama_index()` method,
  simplifying configuration.
- 🧹 **Renamed Discovery Topic Types:** Renamed `DISCOVERY_TOPIC` to `INSTANCE_DISCOVERY_TOPIC` and added
  `CLASS_DISCOVERY_TOPIC` for clearer distinction in NATS topics.
- 🧹 **API Endpoint Path Naming:** Renamed `_get_endpoint_name` to `_get_endpoint_base_path` for clarity in API endpoint
  construction.
- 📁 **Project Structure Alignment:** Reorganized test file directories under `aihub_api/playground/testing/tests` for
  better logical grouping.

### Removed

- 🗑️ **Deprecated Configuration Fields:** The `system_prompt`, `color`, and `voice` fields have been removed from the
  base `AgentConfig` and `AgentConfigDTO`, streamlining the core configuration and allowing for more flexible,
  agent-specific prompt and UI customization to be defined in agent subclasses.

---

## [v0.223.0] - 2025-07-18 - Streamlined Pipeline Operations and Enhanced Robustness

### Added

- 🦾 **New Job Creation Utility**: Introduced `materialize_asset_job` to simplify the creation of jobs for materializing
  specific selections of assets.
- 📅 **Automated Playground Workflows**: Implemented new daily jobs and schedules within the playground environment to
  automatically observe source data and manage document removal processes.

### Changed

- ⚙️ **Refined Asset Automation**: Adjusted automation configurations for document and data lake file removal assets,
  transitioning from eager conditions to more explicit job-driven scheduling.
- 🔗 **Specialized I/O Manager**: Updated the SharePoint observable asset to utilize a dedicated `sharepoint_io_manager`,
  ensuring more appropriate handling of SharePoint data interactions.

### Fixed

- 🐛 **Robust Figure Deletion**: Improved the document figure deletion process to gracefully handle cases where
  associated figure directories do not exist, preventing unnecessary errors and log messages.

---

## [v0.222.0] - 2025-07-15 - Agentic Processes Go Live: Full Stack Support for Complex Workflows

### Added

- 🦾 **Introduced Agentic Process Management**: A major new capability enabling the definition, execution, and monitoring
  of complex, multi-step workflows involving humans, agents, and external programs.
- 🖼️ **Dynamic Form Generation for Human-in-the-Loop**: Processes can now define and expose forms (using Formkit
  elements) directly within their structure, allowing frontends to dynamically render UIs for human input, eliminating
  manual UI development for common interactions.
- ⚡️ **New Process API Endpoints**: A comprehensive set of new API endpoints under `/processes` for discovering
  available processes, retrieving their details, and submitting data via dynamic forms to start or continue process
  walkthroughs.
- 🔄 **Dedicated Process Event Persistence**: Implemented new database entities and services
  (`PersistedProcessEventEntity`, `ProcessEntity`) to durably store and manage all events and metadata related to
  agentic processes.
- 🚀 **Real-time Process Event Streaming**: Introduced new WebSocket event streams for processes, enabling real-time
  updates and visualization of process execution in client applications.
- 🏗️ **Generalized Endpoint Discovery Service**: A new abstract base class `EndpointsDiscoveryService` provides a
  reusable foundation for dynamically registering API endpoints based on discovered entities (like agents and
  processes).
- 🧪 **Comprehensive Process Testing Infrastructure**: Added `SimulatedProcessApiTestRunner` and enhanced
  `ProcessTestRunner` with capabilities to inject events and observe process behavior, facilitating robust testing of
  agentic processes.
- 📂 **Rich Process Playground Examples**: Included new, self-contained examples for various process interaction patterns
  (agent-only, human-only, agent-to-human, human-to-agent) to demonstrate the new capabilities.
- 📄 **Expanded Event Specifications (`EventSpecs`)**: Generalized event schema definitions for both agents and
  processes, enhancing reusability and clarity in API communication.
- 👥 **User Access to Processes in Dashboard**: Users can now view their access levels to specific processes directly
  within their dashboard interface.

### Changed

- 🎛️ **WebSocket Event Handling Refinement**: The main WebSocket endpoint (`/ws`) is now read-only for agent events,
  providing a more secure and streamlined channel for receiving real-time updates from agents. User-initiated agent
  events should now be sent through dedicated API endpoints.
- 🏷️ **Improved Event Naming Consistency**: Renamed `WsServerEvent` to `ContextualizedAgentEvent` and updated related
  API routes and client-side composables to clearly distinguish between agent and process events.
- 🚀 **Agent Discovery Caching Enhancement**: Increased the cache size for agent discovery responses, improving
  performance for frequently requested agent lists.
- 📚 **API Documentation Clarity**: Enhanced Pydantic annotations for various API DTOs and event models, providing more
  precise descriptions and examples in the OpenAPI documentation.
- 🌐 **Frontend Localization for Dynamic Forms**: Integrated Formkit's i18n capabilities to ensure dynamically rendered
  forms correctly reflect the user's selected locale.

### Fixed

- 🐛 **Robust Agent Retrieval**: Corrected agent retrieval logic in the persistence layer to gracefully handle cases
  where a specific agent might not be found.
- 🐞 **Process Event Persistence Accuracy**: Resolved issues ensuring that process-related events are correctly persisted
  with their associated process context.
- 📦 **NATS Topic Validation for Processes**: Stricter validation for NATS process discovery topics ensures that only
  correctly formatted subjects are processed.
- 🧰 **Improved Serialization of Nested Pydantic Models**: Enhanced event serialization to correctly handle nested
  Pydantic models and ChatMessages, especially when `serialize_as_any` is used, preventing data loss.

### Refactor

- 🧹 **Codebase Naming Alignment**: Standardized naming conventions across the codebase, particularly for "event
  distributors" (e.g., `ExternalEventDistributor` is now `ExternalAgentEventDistributor`), improving clarity and
  maintainability.
- 📄 **Documentation Cleanup**: Removed redundant or outdated comments and simplified docstrings in several core
  components, focusing on concise explanations.
- ⚙️ **Pydantic Model Default Handling**: Aligned Pydantic model definitions with best practices by moving default value
  assignments from `Field` annotations to direct attribute assignments.
- 🗂️ **Test Runner Restructuring**: Reorganized test runners into a more logical `simulation/agent` and
  `simulation/process` directory structure.
- ✂️ **Removed Redundant Health Page**: A basic placeholder health page in the frontend was removed.

---

## [v0.221.0] - 2025-07-14 - Prompt Refinements and Image Handling Improvements for RAG

### Changed

- 🔄 **Updated RAG Context Prompt Role:** The chat role for the RAG context prompt has been adjusted from `system` to
  `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering
  best practices and enhance model interpretation of contextual information.

### Fixed

- 🖼️ **Corrected Image URL Handling in RAG Prompts:** Resolved an issue in the English RAG context prompt where image
  URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly
  converting their URL object to a string representation.

---

## [v0.220.0] - 2025-07-11 - Enhanced SharePoint Integration Clarity and Data Lake Observability

### Refactor

- 🧹 **Standardized SharePoint Naming Conventions**: Refactored variable names, function parameters, and internal asset
  definitions across SharePoint-related assets, ops, and IO managers for improved consistency and readability (e.g.,
  `sharepoint_` was consistently renamed to `share_point_`).
- 🔄 **Updated SharePoint Asset Factories**: Renamed the `sharepoint_files_to_data_lake_files_factory` function and its
  internal parameters to align with the new, standardized naming conventions, enhancing code clarity.
- 📄 **Refined SharePoint IO Manager**: Updated the SharePoint IO Manager to use the new `share_point_client` resource
  name consistently, improving maintainability.
- 🧼 **Cleaned Up SharePoint Utilities**: Standardized naming within metadata utility functions related to SharePoint
  files, contributing to a more coherent codebase.

### Changed

- ⚡️ **Improved Data Lake Document Parsing Logging**: Added a new log statement to output the Data Lake file URI during
  the document parsing process, enhancing observability and assisting with debugging.

---

## [v0.219.0] - 2025-07-11 - Internal Workflow Automation Adjustment

### Removed

- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests
  for new branches has been removed.

---

## [v0.218.0] - 2025-07-11 - Enhanced API Configuration and Extensibility

### Added

- ✨ **Enabled custom environment variable configuration for API services:** This new capability allows users to define
  and inject additional environment variables, including secret references, directly into API deployments, significantly
  increasing configuration flexibility and integration possibilities.

---

## [v0.217.0] - 2025-07-10 - Automated Agent API Integration and Event Inheritance

### Added

- ✨ **Automated Agent API Endpoint Generation**: Introduced a new `AgentDiscoveryService` that dynamically discovers
  agents and registers corresponding API endpoints for their start events. This significantly streamlines the
  integration of new agents with the API, eliminating the need for manual endpoint configuration.
- 🦾 **Event Inheritance Tracking**: `EventSpecs` now include an `event_parents` field, providing a hierarchical view of
  event types. This new metadata enhances dynamic model generation and event handling capabilities.
- 📄 **EventSpecs Creation Helper**: Added a convenient `EventSpecs.from_event_class` method to simplify and standardize
  the generation of event specifications from event classes.
- 🔑 **Role Provisioning for API Tokens**: The `generate_api_token` script has been enhanced to automatically create
  specified roles if they do not already exist, improving the initial setup experience for new environments.
- ⚠️ **Refined Unauthorized Access Handling**: Introduced a specific HTTP exception to provide clearer and more precise
  error responses when a user lacks authorization to view a particular thread.

### Changed

- ⚡️ **Flexible Agent Event Dispatch**: The `AgentService.send_event` method now universally accepts any `BaseEvent` as
  input, offering greater flexibility in initiating diverse agent interactions.
- 🔄 **Dynamic Agent Endpoint Management**: Transitioned the agent event endpoint management from static, hardcoded
  definitions in `AgentController` to a dynamic, discovery-driven approach powered by the new `AgentDiscoveryService`.
- 📚 **Event Model Creation Encapsulation**: Internal methods within `EventModelCreationService` have been refactored for
  improved code organization and clearer encapsulation.
- 🏗️ **API State Access for Services**: The `ApiRunner` now stores the `AgentController` and API application instance
  directly in FastAPI's state, enabling seamless access for new services like `AgentDiscoveryService`.

### Refactor

- 🧹 **Unified Event Specification Creation**: Standardized the process of creating `EventSpecs` across `AgentRunner` and
  `SimulatedAgentBotTestRunner` to consistently use the new `EventSpecs.from_event_class` helper.
- 🏷️ **Agent Configuration Entity Renaming**: The `AgentConfig` embedded document within the persistence layer was
  renamed to `AgentConfigEntity` for improved naming consistency across the codebase.
- ✂️ **Base Event Serialization Helper**: Extracted common item dumping logic into a dedicated static method
  `_item_dump` within `BaseEvent` for improved code cleanliness.

### Removed

- 🗑️ **Static Agent Event Endpoint Configuration**: Eliminated the manual and hardcoded API endpoint generation logic
  for agent events from `AgentController` and related playground examples, fully transitioning to the dynamic agent
  discovery service.

---

## [v0.216.0] - 2025-07-08 - Foundational Polish: Modernizing Python Syntax and Enhancing Type Safety

### Added

- ✨ **Deprecated `AgentConfig` Fields:** Introduced deprecation warnings for `color`, `voice`, and `system_prompt`
  fields within `AgentConfig`, guiding users to define these properties directly in agent subclasses for better
  customization.

### Changed

- 🔄 **Standardized Datetime Handling:** Updated datetime operations to consistently use timezone-aware UTC for improved
  time-based accuracy and consistency across the platform.
- 🔄 **Improved Subprocess Execution:** Enhanced `subprocess.run` calls in internal scripts for more robust and secure
  execution, particularly within bot setup processes.
- 🔄 **`jambo` Library Update:** Upgraded the `jambo` schema conversion library to `v0.4.0`, bringing internal
  improvements for dynamic model creation and API event handling.
- 📄 **Refined Docstrings and Comments:** Various docstrings and inline comments across the codebase were updated for
  greater clarity and precision, especially concerning complex components like dispatchers and service methods.

### Fixed

- 🐛 **Clarified Error Messages:** Enhanced error messages in several API endpoints (e.g., thread and role management) to
  provide more informative feedback to users.
- 🐛 **Robust Type Parsing:** Corrected and improved the internal parsing of type annotations for event and parameter
  extraction, ensuring more reliable and accurate workflow dispatching.

### Refactor

- 🧹 **Type Hint Modernization:** Performed a comprehensive refactoring across the entire codebase to leverage native
  Python type hints (e.g., `list`, `dict`, `set`, `tuple`, `X | None`) for improved readability, maintainability, and
  static analysis.
- 🧹 **Linting and Formatting Overhaul:** Consolidated and enhanced code quality checks by deprecating `isort` and
  configuring `ruff` to handle import sorting and enforce stricter linting rules.

---

## [v0.215.0] - 2025-07-08 - Granular Access Control and Enhanced User Management

### Security

- 🔑 **Introduced Hierarchical Role-Based Access Control (RBAC)**: Implemented a new, comprehensive RBAC system that
  supports hierarchical access rules with granular control over services, agents, and processes.
- 🔐 **Enforced Granular Endpoint Permissions**: All major API endpoints across agents, evaluations, events, files, i18n,
  knowledge, OpenAI, threads, and tokens now utilize the new RBAC, ensuring fine-grained access based on user roles and
  specific resource permissions.
- 🔒 **Restricted Knowledge Base Access**: Access to knowledge bases, including databases, documents, and nodes, is now
  limited to users with administrative privileges.
- 🛡️ **Enhanced Thread Management Security**: Improved security checks for thread creation, viewing, and modification,
  including verifying user and agent access, and preventing unauthorized changes to process-owned threads.
- 👁️ **Refined Event Visibility**: The general event retrieval endpoint has been removed, and access to thread-specific
  events and event timeseries is now strictly controlled by user permissions.

### Added

- 🗄️ **Role Management API**: Introduced a new API (`/roles`) enabling administrators to create, list, retrieve, update,
  and delete custom roles with associated hierarchical access rules.
- 📋 **User Management API for Administrators**: New API endpoints (`/users`, `/users/{user_id}`) provide administrators
  with the ability to list all users and retrieve detailed information for specific users, including their assigned
  roles and granular access levels across services, agents, and processes.
- 👤 **Minimal User DTO**: Introduced a lightweight `MinimalUserDTO` for contexts where only essential user information
  is required, improving API efficiency.
- 📊 **Paginated User Listing**: Administrators can now retrieve a paginated list of all users via the API, enhancing
  user management capabilities.
- 👑 **User Access Details in User Profile**: Users can now view their specific access levels for different services,
  agents, and processes directly in their profile (visible to admins).
- 💬 **Process-Associated Thread Metadata**: Added `process_class`, `process_id`, and `process_walkthrough_id` to
  `ThreadDTO` for better contextualization of threads initiated by processes.
- 🤖 **Agent Metadata in Model Details**: `agent_class` and `agent_id` fields were added to `ModelDetails` to provide
  clearer context for AI-Hub agents exposed as OpenAI models.
- ⌛ **User-Friendly Time Ago Display**: Implemented a new composable for displaying relative time (e.g., "Last hour",
  "Last week") with severity indicators in the UI.
- 💥 **Global HTTP Error Toasts**: Configured the frontend client to display informative toast messages for HTTP response
  errors, improving user feedback.
- 🛠️ **New UI Components for Role Management**: Introduced dedicated components for creating, editing, and displaying
  roles, enhancing the administrative user experience.
- 👨‍💻 **New UI Components for User Management**: Added new components to list users and display their detailed access
  information for administrators.

### Changed

- 🔄 **Updated Role Naming Convention**: The `AllAgents` role has been renamed to `TestOnlyFullAdminAccess` for clearer
  intent and consistency with the new access control model.
- 🛣️ **Streamlined Frontend Routing**: All previously "admin" specific routes (e.g., `/admin/agents`) have been unified
  under a `/service/` prefix, aligning with the new granular access control model where permissions define access rather
  than a fixed "admin" route.
- 🌐 **Refined Internationalization Endpoint Access**: The `/i18n/my-locale` endpoint now requires a general user
  permission.
- 📂 **File Access Endpoints**: Access to logged-in file URLs is now managed by the new permission system.
- 📈 **Dashboard Event Labels**: Improved clarity of labels for various event types displayed in dashboard widgets.
- 🎨 **Service Selection Layout**: Adjusted the layout of the service selection component for improved visual
  consistency.

### Refactor

- 🧹 **Centralized Access Control Logic**: All access validation logic has been consolidated into the new `AccessChecker`
  class within `aihub_lib`, removing redundant checks from individual controllers and DTOs.
- ⚙️ **Refined Controller Initialization**: The `Controller` base class now uses a more flexible
  `additionally_required_permission` parameter instead of a simple `is_admin_only` flag.
- 🚀 **Optimized Service Layer Dependencies**: Removed direct `IdentityProvider` dependencies from several service
  methods, pushing identity retrieval and access checks to higher layers or internal `UserEntity` management.
- 📦 **Consolidated User DTOs**: Simplified the user data transfer object hierarchy by replacing `MyUserDTO` with a more
  comprehensive `UserDTO` that includes roles and dashboard configurations, and introducing `MinimalUserDTO` for basic
  user representation.
- 🧪 **Improved Testing Infrastructure**: Enhanced test client fixtures and introduced dedicated mock fixtures for
  `RoleEntity` and `UserEntity` methods, making authentication and data-related tests more robust and easier to set up.
- ⏱️ **Standardized Caching Durations**: Updated `staleTime` configurations across multiple composables to use
  `date-fns` `minutesToMilliseconds` for better readability and consistency.

---

## [v0.214.0] - 2025-07-08 - Streamlined Event Model Handling and Enhanced Developer Experience

### Added

- ✨ **New Event Model Creation Service**: Introduced `EventModelCreationService` to provide a unified and robust
  mechanism for generating Pydantic models from event classes or JSON schemas, enabling dynamic and consistent API model
  definitions.
- 🧪 **Comprehensive Event Model Tests**: Added extensive test suites for the new `EventModelCreationService`, including
  complex nested models, union types, and list structures, to ensure the reliability and correctness of dynamically
  generated event models.
- 🛠️ **Standardized IDE Inspection Profiles**: Integrated new IntelliJ IDEA inspection profiles and scopes (`Core.xml`,
  `ExcludeJambo.xml`) to enforce consistent code quality standards and improve developer experience.
- 📦 **Jambo Dependency**: Introduced `jambo` as a new dependency to support advanced JSON schema to Pydantic model
  conversion within the new event model creation service.

### Changed

- 🚀 **CI/CD Workflow Enhancements**: Updated the `analyze-test-pr.yml` GitHub Actions workflow to include SSH setup and
  cleanup steps, facilitating secure interactions with private Git repositories during testing.
- 🔄 **API Endpoint and Test Integration**: Migrated existing agent API endpoints and their associated tests to utilize
  the new `EventModelCreationService`, ensuring all model generation leverages the centralized logic.

### Removed

- 🗑️ **Deprecated Event Model Functions**: Removed the standalone `create_input_model` and `create_output_model`
  functions, as their functionality has been absorbed and improved by the new `EventModelCreationService`.

---

## [v0.213.0] - 2025-07-07 - New Retrieval Agent for Focused Data Access

### Added

- ✨ **Introduced `RetrievalAgent`**: A new, specialized agent designed to streamline information retrieval from
  knowledge bases. This agent focuses solely on fetching and organizing relevant context, enabling more flexible and
  modular Retrieval-Augmented Generation (RAG) workflows.
- 📄 **Dedicated Configuration for Retrieval Agent**: Added `RetrievalAgentConfig` to provide comprehensive configuration
  options for customizing retrieval behavior, including specifying embedding models, vector stores, and various node
  retrieval strategies.
- ⚡️ **New Event Types for Retrieval Workflows**: Implemented `QuestionStartEvent` for clear initiation of retrieval
  queries and `RetrievalResponseEvent` to encapsulate the retrieved and ordered context, facilitating seamless
  integration with subsequent processing steps.
- 🧪 **Comprehensive Test Coverage for `RetrievalAgent`**: Included a full suite of BDD (Behavior-Driven Development)
  tests to ensure the robust and reliable operation of the new `RetrievalAgent`, validating its ability to accurately
  retrieve and combine relevant documents.

---

## [v0.212.0] - 2025-07-03 - Flexible OpenAI Authentication & Resource Management

### Added

- ✨ **Flexible OpenAI Resource Authentication**: Introduced the ability to authenticate with Azure OpenAI resources
  using either an API Key or Azure AD credentials, providing greater flexibility in deployment environments.
- 🔑 **Centralized OpenAI API Key Configuration**: Added a new base `OpenaiResourceSettings` class for consistent
  management of OpenAI API keys across different services and environments.

### Changed

- 🔄 **Generalized Resource Configuration**: Extended the base `ResourceConfig` to include an optional `api_key` field,
  enabling API key authentication for all derived generative AI resource configurations.
- 🚀 **Improved Azure OpenAI Client Initialization**: Updated the Azure OpenAI client instantiation logic to
  intelligently use either an API key or Azure AD token provider based on the provided configuration, simplifying setup.
- 📄 **Updated Development Playground Models**: Renamed the `o1-mini` model to `gpt-4o-mini` in the development
  environment configuration for improved clarity and alignment with current model names.

### Refactor

- 🧹 **Streamlined API Key Definitions**: Removed redundant `api_key` fields from specific model configurations (e.g.,
  chat LLMs, embedding LLMs, image models) as they are now managed centrally by the generalized `ResourceConfig`.

---

## [v0.211.0] - 2025-07-03 - Enhanced RAG Context and Workflow Streamlining

### Added

- ✨ **Introduced Parent Summary Node Retrieval:** The RAG Agent can now retrieve relevant parent summary nodes from the
  knowledge base, providing richer context and improving the quality of generated answers.
- ⚙️ **Configurable Parent Summary Retrieval:** Added a new `retrieve_summaries` configuration option to the
  `RetrieveStepConfig` for RAG agents, allowing users to specify the maximum hierarchical levels for parent summary
  retrieval.
- 🚀 **Improved Agent Step Metadata:** Enhanced the `@step()` decorator in the RAG Agent to include explicit `name` and
  `description` fields, improving clarity and introspection for agent workflows.

### Changed

- ⚡️ **Streamlined LLM Response Workflow:** The RAG Agent's LLM response step now directly signals the completion of the
  workflow, simplifying internal event handling and removing the need for a separate `StopEvent`.

---

## [v0.210.0] - 2025-07-03 - SharePoint Ingestion and Pipeline Structure Enhancements

### Added

- ✨ **Introduced SharePoint Integration**: A comprehensive new set of assets, operations, and resources for ingesting
  documents directly from SharePoint into the data lake. This includes robust capabilities for fetching, transforming,
  and managing files, ensuring your knowledge base is kept up-to-date with SharePoint content.
- 🚀 **New Azure OpenAI Model Configurations**: Added dedicated configuration classes (`EmbeddingModelConfig` and
  `LanguageModelConfig`) to simplify the setup and management of Azure OpenAI embedding and language models, enabling
  clearer model definitions.
- ⚙️ **Flexible Pipeline Scheduling**: Enhanced scheduling utilities to allow for more granular control over pipeline
  execution times, including a new `daily_schedule_at` function for precise timing.
- 📄 **SharePoint IO Manager**: Implemented a new I/O manager specifically for SharePoint, streamlining the process of
  loading files from SharePoint into pipeline assets.
- 📊 **SharePoint Metadata Utilities**: Introduced helper functions to generate rich metadata tables for SharePoint
  files, improving observability and insights into ingested data.

### Refactor

- 🧹 **Pipeline Asset Reorganization**: Restructured the pipeline's asset factories into more logical subdirectories
  (`data_lake_to_vector_store` and `share_point_to_data_lake`) to improve modularity, readability, and maintainability.
- 🔄 **Centralized SharePoint Utilities**: Consolidated SharePoint-related operations, resources, and data types into
  dedicated modules for better code organization and clarity, preparing for future expansions.

---

## [v0.209.0] - 2025-07-03 - Automated PR Readiness Checks with Claude Integration

### Added

- 🦾 **Automated Subproject PR Readiness:** Introduced a new intelligent script that automatically identifies the root of
  a subproject based on edited files and executes `make pr-ready`, standardizing pre-PR checks and ensuring code
  quality.
- ⚡️ **Claude Post-Edit Automation:** Configured Claude to automatically trigger the new PR readiness script immediately
  after any file modifications (Write, Edit, MultiEdit), providing instant feedback on code quality and readiness within
  the development workflow.

---

## [v0.208.0] - 2025-07-03 - Refined Context Metadata for Generative AI

### Changed

- 📄 **Streamlined RAG Context Metadata**: The **`document_title`** is now explicitly included in the metadata when
  combining nodes for Retrieval Augmented Generation (RAG) contexts, providing more direct document identification
  within prompts.
- 🗑️ **Consolidated Node Metadata Fields**: To simplify and optimize the context provided to generative AI models, the
  `namespace`, `type`, and `content_type` fields are no longer emitted as part of the combined node metadata.

---

## [v0.207.0] - 2025-07-01 - Streamlined Release Tagging

### Removed

- 🗑️ **Streamlined Release Tagging**: Removed the redundant step of deleting existing Git tags in the CI/CD workflow,
  simplifying the release automation process.

### Changed

- 🔄 **Platform Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`,
  `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to
  `v0.207.0`, ensuring a unified and consistent release across the entire platform.

---

## [v0.206.0] - 2025-07-01 - Core System Modernization: Enhanced Model Definitions

### Refactor

- 🧹 **Updated Pydantic Model Definitions**: Migrated numerous internal data models across all core services
  (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`,
  `webui_pipelines`) to leverage Pydantic v2's `Annotated` type hint and explicit default value assignments. This
  enhances code clarity, type safety, and aligns the codebase with modern Python best practices.

---

## [v0.205.0] - 2025-07-01 - Core Module Version Synchronization

### Changed

- 🔄 **Core Module Version Alignment**: All internal microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`,
  `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their `aihub_lib` dependencies have been updated to `v0.205.0`,
  ensuring consistent versioning across the platform.
- ⚙️ **Build Tag Update**: The default build tag in the `Makefile` has been updated to `v0.205.0` to reflect the latest
  release version.

---

## [v0.204.0] - 2025-07-01 - Release Workflow Enhancements and Changelog Automation Robustness

### Added

- ✨ **Robust Changelog Generation:** Implemented error handling within the changelog generation script, allowing the
  release process to continue gracefully even if the Large Language Model fails to produce an entry.
- 📝 **Detailed Changelog Logging:** Enhanced logging in the CI/CD pipeline to provide clearer feedback on whether the
  `changelog.md` file was successfully updated or skipped during the automated generation process.

### Changed

- ⚡️ **CI/CD Workflow Resilience:** The automated tag and release workflow now allows the changelog generation step to
  `continue-on-error`, prioritizing the overall release completion over a potential failure in AI-powered changelog
  creation.
- 🔄 **Conditional Changelog Commit:** The final commit of the `changelog.md` file is now dependent on the successful
  execution of the changelog generation step, preventing the amendment of the release commit with an incomplete or
  erroneous changelog.
- ⚙️ **Gemini API Key Command:** Updated the command-line syntax for setting the Gemini API key in the CI/CD pipeline to
  use the `--value` flag, aligning with the `llm` tool's latest requirements.

### Refactor

- 🧹 **Python Poetry Cache Removal:** Streamlined the GitHub Actions Python setup by removing the explicit Poetry cache
  configuration, potentially improving caching efficiency or addressing previous issues.

---

## [v0.203.0] - 2025-06-30 - Automated Changelog Generation & Enhanced Release Workflow

### Added

- ✨ **Automated Changelog Generation**: Introduced a new system to automatically generate changelog entries for
  releases, leveraging an LLM to summarize git diffs. This includes a dedicated script (`generate-changelog.sh`), an LLM
  prompt file (`changelog-prompt.md`), and a new `make changelog` target.
- 📄 **Centralized Changelog File**: A new `changelog.md` file is now part of the repository, serving as the official
  documentation for all notable changes in a standardized format, automatically updated during the release process.

### Changed

- 🚀 **Enhanced Release Automation Workflow**: The GitHub Actions workflow (`add-tag.yml`) has been significantly
  upgraded to seamlessly integrate the new automatic changelog generation, ensuring comprehensive release notes are
  created and committed as a core part of the tagging and release process.
- ⚙️ **Streamlined CI/CD Setup**: Improved the efficiency and robustness of Python and Poetry setup within the CI/CD
  pipeline, including a more reliable method for installing Poetry via `pipx` and consolidating global dependency
  installation steps.
- 🔄 **Refined Commit and Tagging Logic**: The release workflow now intelligently handles version updates and changelog
  changes, amending the previous commit with generated changelog entries and ensuring more robust force pushes for tags.

### Refactor

- 🧹 **Optimized CI/CD Workflow Steps**: Internal steps within the `add-tag.yml` workflow have been reorganized and
  renamed for better clarity and maintainability, streamlining the automated release pipeline.

---

## [v0.202.0] - 2025-06-30 - Unified Identity & Auth: Stronger, Smarter, Safer

### Refactor

- 🧹 **Unified User Identity Management:** Replaced the disparate `AuthenticatedUser` model and various API-specific user
  information providers with a new, centralized `UserIdentity` model and a consistent `IdentityProvider` framework
  within `aihub_lib`. This significantly improves modularity, consistency, and extensibility for handling user
  identities across all services (`aihub_api`, `aihub_bot`).
- 🧹 **Streamlined Authentication Handlers:** Refactored core authentication handlers (`AuthHandler`,
  `OAuth2AuthHandler`, `TokenAuthHandler`, `OpenWebuiAuthHandler`, `TokenAndOauth2Handler`) to seamlessly integrate with
  the new `IdentityProvider` framework, simplifying their internal logic and promoting dependency injection for clearer
  authentication flows.
- 🧹 **Renamed Development-Only Authentication:** Renamed `NoAuthHandler` and its associated configurations to
  `DangerousDevelopmentOnlyAuthHandler` and `DangerousDevelopmentOnlyAuthConfig` respectively. This clearer naming
  strictly communicates that these components are intended for development and testing environments only, preventing
  their accidental use in production.

### Changed

- 🔄 **Updated User Representation in API & UI:** The `preferredUsername` field in various API responses and UI
  components (such as chat messages and event displays) has been consistently renamed to `email` to more accurately
  reflect the user's email address.
- ⚙️ **API Controllers Initialization Refinement:** All API controllers now explicitly require an `AuthHandler` during
  initialization, enforcing clearer dependency management and simplifying security configuration across the application.
- 📄 **Refined Image Description Prompting:** The internal prompt used for generating figure descriptions has been
  updated with more precise instructions on how to leverage surrounding text for context without altering the factual,
  visual description of the image.

### Fixed

- 🐛 **Improved Figure Description Generation Robustness:** Enhanced the image description generation process in the data
  pipeline with robust error handling for `BadRequestError` (often triggered by content safety filters). The system now
  automatically retries generating descriptions without surrounding text and falls back to an empty string if necessary,
  preventing pipeline failures.

### Added

- ✨ **Introduced `by_email` User Lookup:** Added a new `by_email` class method to `UserEntity`, enabling direct and
  efficient retrieval of user entities by their email address from the database.
- 🚀 **Enhanced OAuth2 Token Verification Caching:** Implemented internal caching mechanisms for JWKS (JSON Web Key Sets)
  and RSA keys within `OAuth2AuthHandler`, significantly improving the performance and reducing external API calls
  during OAuth2 token validation.

### Removed

- 🗑️ **Deprecated `AuthenticatedUser` Model:** The `AuthenticatedUser` data model has been entirely removed, succeeded
  by the more versatile and centrally managed `UserIdentity` model.
- 🗑️ **Removed Redundant Identity Provider Implementations:** Obsolete, API-specific identity provider implementations
  (`ApiTokenUserInformationProvider`, `AzureUserInformationProvider`, `DevUserInformationProvider`) have been removed,
  replaced by the new, unified `IdentityProvider` framework in `aihub_lib`.
- 🗑️ **Unauthenticated Health Endpoint:** The health endpoint no longer requires user authentication, simplifying its
  use for external readiness and liveness probes.

---

## [v0.201.0] - 2025-06-30 - Unified User Identity & Authentication Overhaul

### Refactor

- 🔄 **Unified User Identity Management**: Implemented a comprehensive overhaul of user identity handling, centralizing
  the **`UserIdentity`** model in `aihub_lib` and replacing the deprecated `AuthenticatedUser` across all services
  (`aihub_api`, `aihub_agent`, `aihub_bot`). This standardizes how user information is represented and accessed.
- 🧹 **Decoupled Authentication from Identity Resolution**: Introduced a new **`IdentityProvider`** interface and various
  concrete implementations (e.g., `AzureIdentityProvider`, `TokenIdentityProvider`). Authentication handlers
  (`OAuth2AuthHandler`, `TokenAuthHandler`, `OpenWebuiAuthHandler`) now leverage these providers, significantly
  improving modularity and allowing for easier integration of new identity sources.
- 🔐 **Enhanced Security Development Experience**: Renamed `NoAuthHandler` to **`DangerousDevelopmentOnlyAuthHandler`**
  and introduced a dedicated **`DangerousDevelopmentOnlyIdentityProvider`** to clearly delineate and manage
  authentication in non-production environments, making it more explicit when security is bypassed for development.

### Changed

- ⚡️ **Standardized Controller Initialization**: The **`auth`** parameter in all `Controller` constructors is now a
  required keyword-only argument, promoting clearer and more consistent API initialization.
- 🚀 **Unauthenticated Health Checks**: The **health check endpoint** (`/health`) no longer requires authentication,
  making it easier to monitor service availability.
- 📄 **API Token Generation Improvements**: Updated the **`generate_api_token.py`** script with clearer CLI parameter
  names (`--token-path`, `--token-url`) to better reflect their purpose.
- 🛣️ **Bot API Path Update**: Changed the base API path for **bot-in-the-loop interactions** from `/api/v1` to
  `/bearer_token/v1` in `aihub_bot` to align with specific authentication routing.
- 🌐 **Frontend User Profile Update**: Renamed the **`preferredUsername`** property to **`email`** in frontend user
  components and SDK schemas to align with the new `UserIdentity` model, reflecting a more direct and generic user email
  representation.

### Removed

- 🗑️ **Deprecated User Information Providers**: Eliminated several specific user information provider classes from
  `aihub_api` (`BaseUserInformationProvider`, `MultiStrategyUserInformationProvider`, `ApiTokenUserInformationProvider`,
  `AzureUserInformationProvider`, `DevUserInformationProvider`) as their functionality is now superseded by the new
  **`IdentityProvider`** architecture in `aihub_lib`.
- 🗑️ **Legacy `AuthenticatedUser` Model**: The outdated **`AuthenticatedUser`** model has been fully removed from
  `aihub_lib`, completing the transition to `UserIdentity`.

---

## [v0.200.0] - 2025-06-30 - Process Orchestration and Core Refinements for Enhanced Modularity

### Added

- 🦾 **Introduced Agentic Processes (`aihub_process`)**: A new top-level module is added to enable sophisticated
  orchestration of work across diverse entities, including AI agents, human collaborators, programs, and even other
  processes. This foundational change allows for building complex, multi-entity workflows.
- ⚡️ **Generic Dispatcher (`BaseDispatcher`)**: A new abstract base class `BaseDispatcher` is introduced in `aihub_lib`,
  centralizing common logic for handling events, managing execution contexts, and executing workflow steps across all
  dispatchable entities (agents and processes).
- ⚙️ **Generalized Event and Step Stores**: Core event storage (`JetStreamEventStore`) and step execution tracking
  (`StepStore`) are moved and refactored into `aihub_lib`, providing a unified, distributed persistence layer for all
  workflow types.
- 🔗 **New Event Types for Process Communication**: A comprehensive set of `WorkEvent` and `WorkRequestEvent` hierarchies
  are introduced (`AgentWorkEvent`, `HumanWorkEvent`, `ProgramWorkEvent`, `ProcessWorkEvent` and their `WorkRequest`
  counterparts) to standardize how different entities interact within a process.
- 📚 **Process-Specific Topics and Subscribers**: Dedicated topic managers (`ProcessTopicManager`,
  `ProcessInstanceTopicManager`, `ProcessWalkthroughTopicManager`) and NATS subscribers (`ProcessJSSubscriber`,
  `ProcessNCSubscriber`) are added to define and manage communication channels for process-specific events.
- 📝 **Process Configuration (`ProcessConfig`)**: A new configuration class is introduced to define metadata and settings
  for process instances, enabling flexible deployment and management.
- 🌐 **Process Locale Support**: New localization files are added to support process-related terms and messages.

### Changed

- 🔄 **Unified Workflow Base (`DispatchableWorkflow`)**: The `Agent` class now inherits from `DispatchableWorkflow`,
  establishing a common architectural pattern for all event-driven entities and centralizing step discovery and event
  handling logic.
- 🧹 **Refactored Agent Dispatcher**: The `AgentDispatcher` is renamed and refactored to extend the new `BaseDispatcher`,
  streamlining its implementation by leveraging shared core dispatcher functionalities.
- 🧩 **Modularized NATS Communication Components**: `TopicManager`, `JSPublisher`, and `NCPublisher` are refined into
  more generic base classes, while agent-specific logic is migrated to new, dedicated `AgentTopicManager` and
  `AgentNCSubscriber`/`AgentJSSubscriber` classes for better modularity.
- 🛠️ **Updated CI/CD and Build Configuration**: GitHub Actions workflows and the main `Makefile` are updated to
  incorporate linting, testing, and deployment steps for the new `aihub_process` module.
- 📦 **API and Bot Module Alignments**: The `aihub_api` and `aihub_bot` modules are updated to utilize the new
  `ExternalAgentEventDistributor` and other agent-specific communication components, ensuring compatibility with the
  refined messaging architecture.
- 🎨 **Enhanced `LocaleString` Flexibility**: `display_name` and `display_description` fields in display events now
  support `None` values in `LocaleString`, providing greater flexibility in event schema definition.
- 🚧 **Agent Configuration Enhancements**: Improved validation for `agent_id` with regex pattern constraints. `color`,
  `voice`, and `system_prompt` fields in `AgentConfig` are deprecated, encouraging more granular, domain-specific
  configuration for agents.
- 📄 **Documentation Updates**: The agent documentation is updated to reflect the `AgentDispatcher` renaming and the new
  architectural patterns.

### Fixed

- 🐛 **API Typecheck Issue**: Corrected a typo in the `aihub_api/Makefile` to ensure proper type checking for the
  `aihub_api` module.
- 🔒 **Database Uniqueness Constraints**: Added `unique=True` indexes to `conversation_id` in `ConversationEntity` and
  `path` in `PathEntity` within `aihub_bot`, and `email` in `UserEntity` to enforce data integrity and improve query
  performance.

### Refactor

- 🧹 **Consolidated Context Management**: `RunContext` and `ThreadContext` are moved to `aihub_agent/context`, making
  their scope agent-specific and aligning with the new modular structure.
- 🏷️ **Explicit External Event Naming**: `ExternalEvent` and `ExternalEventDistributor` are renamed to
  `ExternalAgentEvent` and `ExternalAgentEventDistributor` respectively, clarifying their specific role in handling
  external communication for agents.
- 🧹 **Streamlined Type Extraction**: The `extract_event_classes` utility is enhanced to properly unwrap `Annotated`
  types, ensuring more accurate type introspection for workflow steps.
- 🗑️ **Cleaned Up `Topic` Hierarchy**: The base `Topic` class is made abstract, and `TopicManager` is stripped down to
  its core, generic functionality, with all agent-specific topic logic moving to the new `AgentTopicManager` and its
  subclasses.

---

## [v0.199.0] - 2025-06-27 - Enhanced Document Processing and New Docling Integration

### Added

- ✨ **Introduced Docling Document Loader:** Added a new `DoclingLoader` to integrate with the Docling API, expanding
  support for parsing various document types including PDFs, office documents, and images.
- 🦾 **LLM-Powered Figure Description Generation:** Implemented a new pipeline operation (`generate_figure_descriptions`)
  that uses Large Language Models to automatically create detailed, accessible alt-text descriptions for figures within
  documents.
- ⚙️ **Configurable Document Parsing Engines:** Introduced `LoaderType` in `DocumentParserResource`, allowing explicit
  selection between Docling, Azure Document Intelligence, or using both for document processing, providing greater
  flexibility.
- 📚 **Docling API Integration:** Added core components (`DoclingAccess` and `DoclingConfig`) for seamless interaction
  and configuration with the Docling document conversion API.
- 📄 **Expanded Document Intelligence Supported Formats:** Configured the `DocumentIntelligenceLoader` with an explicit
  list of supported file extensions, enhancing its capability to parse various document formats.

### Changed

- 🔄 **Streamlined Document Intelligence Processing:** The `DocumentIntelligenceLoader` now directly handles table
  reformatting and figure extraction/saving, simplifying the document processing flow by embedding this logic within the
  loader itself.
- 💬 **Updated Figure Description Prompts:** Revised the prompt structure for figure description generation to better
  leverage multi-modal LLMs and improve the quality of generated alt-text.
- 📝 **Simplified Figure Metadata:** The `FigureMetadata` model has been streamlined by removing the `figure_url` field,
  focusing on essential file path information.
- 🚧 **Playground Default Loader:** Updated the playground environment to default to the `DoclingLoader`, showcasing the
  new integration.

### Refactor

- 🧹 **Optimized Document Processing Pipeline:** Significantly refactored the document processing asset graph by removing
  redundant intermediate operations and consolidating logic directly within document loaders for a more efficient and
  cleaner pipeline.
- 📦 **Reorganized Path Utilities:** Moved and renamed the `path_utils` module from `aihub_pipeline` to `aihub_lib` and
  updated function names for better modularity and broader utility across the `aihub_lib`.

### Removed

- 🗑️ **Deprecated Document Processing Operations:** Eliminated several no-longer-needed pipeline operations, including
  `doc_with_figures_to_ref_doc`, `inject_figures`, `reformat_tables`, and `save_figures_to_data_lake`, as their
  functionalities have been integrated directly into document loaders.

---

## [v0.198.0] - 2025-06-24 - Pipeline Embedding Enhancements

### Changed

- 🦾 Improved **node embedding content** within pipelines by transitioning from `get_text()` to
  `get_content(metadata_mode=MetadataMode.EMBED)` for extracting text. This ensures that relevant metadata is also
  considered, leading to potentially richer and more accurate vector embeddings.

---

## [v0.197.0] - 2025-06-24 - Enhanced Infrastructure with Azure Data Lake Storage Support

### Added

- ✨ **Introduced Azure Data Lake Storage Management:** Added new Infrastructure as Code (IaC) components to provision
  and manage Azure Data Lake Storage accounts, expanding the platform's data storage capabilities.
- 🔑 **New Azure Data Lake Roles:** Incorporated specific Azure role definitions (`Storage Blob Data Reader` and
  `Storage Blob Delegator`) to facilitate secure and controlled access to data within Data Lake Storage.
- 🦾 **Automated Data Lake Role Assignment:** Implemented a new method within `UserAssignedIdentity` to automatically
  assign the necessary permissions for Data Lake Storage, specifically enabling the generation of Shared Access
  Signatures (SAS) tokens for temporary data access.
- 📄 **Standardized Data Lake Naming:** Defined a consistent naming convention for Azure Data Lake Storage resources,
  improving resource organization and clarity within the infrastructure.

---

## [v0.196.0] - 2025-06-20 - Automation Enhancements and Version Synchronization

### Added

- ✨ **Enhanced Automated Pull Request Creation:** Improved the CI/CD workflow for generating automatic draft pull
  requests by incorporating full Git history fetching and enabling automatic population of PR descriptions from commit
  messages, streamlining development processes.

### Changed

- 🔄 **Project Version Synchronization:** Aligned all microservices and core libraries, including `aihub_agent`,
  `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, and `aihub_pipeline`, to version `v0.196.0` for consistent
  dependency management and release coordination.

---

## [v0.195.0] - 2025-06-20 - Enhanced Pipeline Efficiency

### Changed

- ⚡️ **Optimized Dynamic Partition Management**: The `replace_partition_keys` utility in the pipeline core has been
  significantly improved to efficiently add and delete only the necessary dynamic partitions, thereby reducing
  unnecessary operations and enhancing overall performance for data pipeline execution.

---

## [v0.194.0] - 2025-06-19 - Core System Alignment and Pipeline Operation Streamlining

### Changed

- 🔄 **Core Service Version Alignment:** Updated internal dependency versions across all `aihub_` services (agent, api,
  bot, iac, lib, pipeline) and the Makefile to `v0.194.0` for consistent build and deployment.

### Refactor

- 🧹 **Simplified Data Lake File Fetching:** Refactored `fetch_all_files_in_data_lake` operations within the pipeline
  module to remove direct `OpExecutionContext` dependency and internal logging, promoting cleaner, more focused data
  retrieval logic.

---

## [v0.193.0] - 2025-06-19 - Enhanced Draft PR Automation with Structured Branching

### Added

- ✨ **New Branch Naming Conventions:** Implemented strict `base/scope` naming validation for new branches, ensuring
  consistency and clarity. This includes a predefined list of allowed scope prefixes.
- 🔒 **Improved GitHub App Token Usage:** Switched to using a dedicated GitHub App Token for creating draft pull
  requests, enhancing security and permissions management for automated workflows.
- 🚀 **Duplicate PR Prevention:** Added a check to prevent the creation of redundant draft pull requests if one already
  exists for the branch, streamlining workflow execution.

### Changed

- ⚙️ **Dynamic Draft PR Titles:** Automated draft pull requests now generate more informative titles, incorporating the
  parsed `base` and `scope` from the branch name, along with the author's username, for immediate context.
- ➡️ **Default Base Branch for Draft PRs:** Standardized the base branch for automatically created draft pull requests
  to `main`, simplifying the initial setup for new feature or bugfix branches.
- 🧹 **Streamlined Workflow Authentication:** The workflow now utilizes a more secure and efficient method for
  authenticating with the GitHub API.

---

## [v0.192.0] - 2025-06-18 - Streamlined Branch Naming and Project Alignment

### Changed

- 🔄 **Relaxed Branch Naming Conventions:** Updated the semantic PR GitHub workflow to allow more flexible and generic
  branch names (e.g., `feature/my-feature`, `bugfix/issue-123`) by replacing specific initiative branch patterns with a
  broader regular expression. This simplifies development workflows and enhances consistency.
- ⬆️ **Project Version Alignment:** Aligned all internal project and library dependencies across microservices
  (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`) to the new `v0.192.0` release
  tag, ensuring consistent versioning throughout the codebase.

---

## [v0.191.0] - 2025-06-18 - LLM Event Reporting Enhancements

### Added

- ✨ **Improved LLM Event Reporting**: Introduced a new `from_chat_response` method to `LLMEvent` for easier creation of
  LLM events directly from LlamaIndex chat responses, automatically capturing token usage for enhanced observability.

---

## [v0.190.0] - 2025-06-16 - Core Updates and Path Robustness

### Fixed

- 🐛 **Enhanced Data Lake Path Generation:** Improved the utility for creating data lake figure folder names by
  transitioning to a more robust file name parsing method (`os.path.splitext`), ensuring accurate and reliable folder
  structures regardless of complex file naming conventions.

---

## [v0.189.0] - 2025-06-16 - Multimodal RAG and Enhanced File Access

### Added

- ✨ **Multimodal RAG Capabilities**: The RAG Agent now supports incorporating images alongside text in its context,
  enabling it to answer questions that require visual information. This includes the dynamic generation of secure,
  time-limited URLs for embedded figures.
- 🔗 **Extended Anonymous File Link Lifetime**: Anonymous file sharing links can now be configured to remain valid for up
  to 30 days, providing increased flexibility for long-term access to shared content.

### Changed

- 🦾 **Improved RAG Agent System Prompt**: The RAG Agent's core instructions have been refined to enhance its ability to
  analyze and provide detailed answers using both document and image context, and to explicitly state when it cannot
  find an answer.
- 🔄 **Standardized Anonymous File Access**: The generation and validation of secure, temporary file URLs have been
  centralized and streamlined within the `AnonymousFileAccessService`, improving consistency and security for file
  access.
- 📄 **Enhanced Document Parsing for Multimodal Content**: The Markdown parser now intelligently identifies and
  categorizes content within documents as text, figures, or tables, enriching the metadata for RAG processing.
- 🧩 **Updated RAG Node Data Model**: The `IngestedNode` data model now includes explicit `content_type` fields (text,
  figure, table) to support the new multimodal RAG capabilities, ensuring detailed content classification.
- 📝 **Modernized RAG Context Prompt Templating**: RAG context prompts now leverage a more advanced templating system
  (`RichPromptTemplate`) to natively support the inclusion of both text and image blocks, improving prompt construction
  and multimodal reasoning.
- ⚙️ **Refined Figure and Table Injection in Pipelines**: Document processing pipelines now inject figures and tables
  into markdown using specific XML-like tags (`<figure>` and `<table>`), enabling the downstream RAG system to correctly
  identify and process these content types.
- 🧹 **Centralized ChatMessage Serialization**: Serialization logic for `ChatMessage` objects, particularly for handling
  URLs in image and audio blocks, has been consolidated into the `BaseEvent` model for improved consistency across all
  events.

### Refactor

- 📦 **Reorganized File Access Logic**: The internal logic for generating and validating anonymous file signatures and
  SAS tokens has been refactored and moved to dedicated services for better module separation and maintainability.

---

## [v0.188.0] - 2025-06-13 - Advanced Document Handling: Secure Access & Improved Markdown Rendering

### Added

- ✨ **Secure File Access API:** Introduced new API endpoints (`/file`) for secure access to files stored in Azure Blob
  Storage, supporting both logged-in users and temporary anonymous sharing via signed URLs.
- 📄 **Azure Blob Storage Integration:** Added core services and configuration for seamless integration with Azure Blob
  Storage, enabling centralized and secure file management across the platform.
- 🚀 **Anonymous File Access Service:** Implemented a new service to generate secure, time-limited URLs for anonymous
  file sharing, enhancing the platform's ability to share documents securely.
- 🖼️ **Markdown Rich Content Components:** Introduced dedicated Vue components (`MarkdownFigure`, `MarkdownTable`) to
  significantly improve the rendering and styling of figures and tables within markdown content.
- 🔗 **Dynamic Image Resolution for Markdown:** Added a `ResolveImageComponent` to dynamically fetch and display images
  from secure internal storage within markdown content using signed URLs.
- ⬇️ **Document Download Capability:** Enabled users to download original documents directly from the knowledge base
  list in the web interface, improving usability and accessibility.
- 📝 **File Attachment Support:** Extended API schemas to allow attaching files to `Metadata` and `UserMessageEvent` for
  richer interaction capabilities with agents.

### Changed

- 🔄 **Event Schema Refinement:** Refactored event schemas into `Readable` and `Writable` types to provide clearer
  distinctions between data models for API input and output, enhancing type safety and API clarity.
- 📊 **Knowledge Base Document Display:** Adjusted the web interface display for knowledge base documents to prominently
  feature the number of pages and improved column ordering for better readability.
- 📄 **Figure Reference Handling:** Updated the document processing pipeline to handle figure references using file paths
  instead of direct URLs, aligning with the new on-demand URL generation for secure access.
- 🎨 **Markdown Styling Enhancements:** Refined markdown rendering styles, including adjusted heading margins and link
  appearances, for a more consistent and polished visual experience.
- 📚 **Ingested Document Metadata:** Enhanced the `IngestedDocument` model to accurately capture and display the
  `number_of_pages` from source document metadata, providing more comprehensive document details.
- 📦 **New Dependency:** Added `lxml` to the pipeline dependencies, which is likely used for improved parsing and
  processing of document structures, supporting richer content extraction.

### Refactor

- 🧹 **Azure Storage Access Standardization:** Centralized Azure Blob Storage access through a new singleton
  `BlobStorageAccess` class, ensuring consistent and maintainable interactions with storage services.

### Fixed

- 🐛 **API Base URL Configuration:** Ensured correct API base URL configuration for the web client, standardizing API
  access and preventing potential routing issues.

---

## [v0.187.0] - 2025-06-12 - Core Refinements and Stability Updates

### Fixed

- 🐛 **Document Parsing Robustness:** Enhanced the Markdown structural node parser to gracefully handle empty content,
  preventing potential processing errors during document ingestion.
- 🛡️ **Table Reformatting Stability:** Improved the document table reformatting process within the pipeline to prevent
  errors when encountering documents with missing or empty text content.

### Changed

- ⚙️ **Pipeline Function Clarity:** Updated function calls within the `documents_factory` in the pipeline to
  consistently use keyword arguments, improving code readability and maintainability.

---

## [v0.186.0] - 2025-06-12 - Enhanced Data Flexibility and Azure AI Integration

### Changed

- 🔄 **Improved Document Metadata Handling:** The `IngestedBase` and `IngestedNode` document types now dynamically
  capture and retain all additional, non-standardized metadata fields present in source documents, significantly
  enriching the information available for RAG pipelines.
- 🔑 **Enhanced Azure OpenAI Embedding Authentication:** Explicitly enabled Azure Active Directory (AAD) authentication
  for Azure OpenAI embedding models, providing more secure and robust integration with Azure environments.

---

## [v0.185.0] - 2025-06-11 - Internal Updates and CI/CD Streamlining

### Refactor

- 🧹 **Optimized Build Process:** Removed the explicit code checkout step within the `build_image` GitHub Action,
  streamlining the image building process and potentially reducing redundant operations.

---

## [v0.184.0] - 2025-06-11 - Web UI Streamlining and Configuration Updates

### Changed

- 🔄 **Web UI Default Development Port**: Updated the default local development port for the Web UI from `5173` to `8080`
  in `docker-compose-webui.yml`, affecting local setup and direct access URLs.
- ⚙️ **OIDC Configuration Management**: Removed hardcoded OIDC client and tenant IDs from `nuxt.config.ts`, indicating a
  shift towards more dynamic or externalized authentication configuration.

### Refactor

- 🧹 **`useRouteQuery` Hook Usage**: Refactored the usage of `useRouteQuery` in Web UI composables and pages to
  explicitly pass `route` and `router` instances, aligning with recommended practices and improving compatibility.

### Removed

- 🗑️ **Storybook Integration**: Completely removed Storybook development tooling and all related configurations from the
  web UI project, streamlining the frontend development environment.
- 🗑️ **Deprecated `shad` Makefile Command**: Removed the `shad` command from the `aihub_web` Makefile, simplifying build
  scripts.

---

## [v0.183.0] - 2025-06-11 - Smarter Document Summarization and Enhanced Data Traceability

### Added

- 📄 **Introduced `document_store_name` Metadata:** Nodes now include `document_store_name` metadata, enhancing
  traceability and organization by indicating their origin.
- 🔗 **Integrated `document_store_name` into Chunking Pipeline:** The document chunking process now automatically
  populates the `document_store_name` metadata field for all generated nodes.

### Changed

- 🧠 **Revamped Recursive Summary Parser:** A major overhaul of the recursive summary parser to generate more logical and
  accurate document summaries. This includes improved content grouping, robust handling of sequential sections, and
  precise relationship management between original and summary nodes.
- 🌳 **Enhanced Summary Node Relationships:** Summary nodes now maintain a more coherent hierarchical context within the
  document structure, including new `PREVIOUS` and `NEXT` pointers, and refined `PARENT`/`CHILD` relationships.
- 📝 **Improved Summary Prompting:** The underlying prompt for summarization has been updated across multiple languages
  (DE, EN, FR, IT) to generate more concise, direct, and "TL;DR" style summaries.
- ⚡️ **Updated Playground Environment Configuration:** Internal variable names have been updated for clarity, and
  default settings now utilize "papers" for data lake containers and namespaces, streamlining demonstration and testing.
- 🚀 **Switched Playground LLM to `gpt-4o-mini`:** The default language model for the playground environment has been
  updated to `gpt-4o-mini`, potentially offering more cost-effective or faster experimentation.

### Fixed

- 🐛 **Improved Empty Text Handling in Summarizer:** The LLM summarizer now gracefully handles empty or whitespace-only
  input, returning an empty string to prevent potential errors or irrelevant output.

### Refactor

- 🧹 **Cleaned `RecursiveSummaryParser` Internals:** Streamlined internal logic by integrating previously separate helper
  methods directly, improving code readability and maintainability.

---

## [v0.182.0] - 2025-06-11 - Enhanced Bot Responsiveness

### Fixed

- 🐛 **Resolved Bot Typing Behavior:** Corrected the timing of the bot's "typing" indicator to ensure it only appears
  when the bot is actively processing a response, preventing misleading indicators for interactions the bot is
  configured not to respond to (e.g., expired conversations).

---

## [v0.181.0] - 2025-06-10 - Core Enhancements and Stability Improvements

### Changed

- 🚀 **Enhanced Agent Event Distribution:** The `AgentCompletionHandler` now supports a custom `display_id` for agent
  events, providing greater flexibility in event tracking and display.
- 💬 **Flexible OpenAI Completion Parameters:** OpenAI completion methods (`get_completion`, `get_stream_completion`)
  have been extended to accept additional keyword arguments, allowing for more diverse model interactions.
- 🌍 **Localized Error Handling:** Integrated `LocaleHandler` into the `OpenaiCompletionHandler`'s exception handling,
  paving the way for more user-friendly and localized error messages.

### Fixed

- 🐛 **Improved Content Type Robustness:** Added checks for `file_info.content_type` in the `ContentExtractor` to prevent
  potential errors when processing file attachments with undefined or missing content types.

### Refactor

- 🧹 **Streamlined Completion Handler Calls:** Removed redundant `service` parameters from `get_stream_completion` and
  `get_completion` calls within the `BaseChatBot`, simplifying internal API usage.
- 🔄 **Centralized Completion Handler Import:** Adjusted import paths for the `CompletionHandler` to reflect its
  dedicated module, improving code organization and maintainability.
- ⚙️ **Standardized Channel ID Usage:** Replaced a hardcoded string with the `Channels.webchat` constant in
  `StreamAgentChatBot` for improved consistency and maintainability.

---

## [v0.180.0] - 2025-06-10 - Enhanced Bot Robustness and Core Version Alignment

### Fixed

- 🐛 **Improved Chat Bot Locale Handling:** Addressed an issue in the `BaseChatBot` to gracefully handle scenarios where
  user locale information might be missing, ensuring robust locale resolution by falling back to a default.

---

## [v0.179.0] - 2025-06-10 - Next-Gen Chat: File Uploads & Seamless WebUI Integration

### Added

- ✨ Introduced comprehensive **file upload support** for chat completion requests, enabling richer contextual
  interactions with AI agents.
- 📝 Defined a new `**UserUploadedFile**` data model to standardize the representation of uploaded files across the
  platform.
- 🌐 Launched a new **Open WebUI pipeline** that seamlessly integrates file sending to AI-Hub assistants and visualizes
  retrieved sources within the UI.

### Changed

- 🔄 Extended **core chat services** (`ChatService` and `OpenaiService`) to process and manage user-uploaded files within
  conversations.
- ⚡️ Enhanced **internal event handling** to propagate `UserUploadedFile` data, ensuring consistent context across
  agents and services.

### Fixed

- 🛠️ Addressed a compatibility issue in the **API token generation script** (`generate_api_token.py`) for improved
  reliability with Azure CLI.

---

## [v0.178.0] - 2025-06-05 - Infrastructure Control and WebUI Scalability

### Added

- ✨ **Introduced `webui_secret_key`**: A new secret key can now be configured for OpenWebUI, enhancing security for the
  user interface.
- 🚀 **Configurable WebUI Scaling**: Enabled configuration of minimum and maximum replicas for the WebUI container,
  allowing for more flexible resource allocation and scalability.

### Changed

- ⚙️ **Azure Container Apps Subnet Delegation**: Implemented subnet delegations for Dagster and WebUI modules, improving
  integration with Azure Container Apps managed environments.
- 💾 **Dagster PostgreSQL Data Retention**: Configured the Dagster PostgreSQL database to retain data upon deletion,
  preventing accidental data loss during infrastructure changes.
- ⚡️ **WebUI Performance Optimizations**: Enhanced WebUI performance by dynamically setting UVicorn workers and thread
  pool size based on allocated CPU, and integrated the new `WEBUI_SECRET_KEY` and Redis URL.
- 📊 **Managed Environment Workload Profiles**: Defined explicit workload profiles for Azure Container Apps, optimizing
  resource allocation and cost efficiency.

### Refactor

- 🧹 **Codebase Cleanup**: Removed several unused imports across Agent, API, Bot, and WebUI configurations for cleaner
  and more efficient code.

---

## [v0.177.0] - 2025-06-04 - Enhanced Document Processing with AI-Powered Figure & Table Management

### Added

- ✨ **Automated Figure Description Generation:** Introduced AI-powered generation of detailed alt text for figures in
  documents, leveraging vision models to describe visual content for improved accessibility.
- 🖼️ **Figure and Table Extraction in Document Processing:** Implemented robust extraction and handling of figures and
  tables from documents, allowing them to be processed as distinct, enriched content elements.
- 📄 **Page Number Metadata:** Added functionality to extract and store page numbers as metadata for document nodes,
  significantly improving context and precise referencing within documents.
- 🗑️ **Figure Cleanup for Deleted Documents:** Introduced automatic deletion of associated figure data from the data
  lake when reference documents are removed, ensuring data consistency and storage efficiency.
- ⚡️ **Prompt for Figure Description Generation:** Added new multi-language prompts specifically designed for generating
  high-quality, accessible descriptions for figures.

### Changed

- 🔄 **Enhanced Document Processing Pipeline:** Significantly restructured and enhanced the document ingestion pipeline
  to support comprehensive figure and table extraction, reformatting, and injection of AI-generated descriptions.
- 📈 **Improved Table Reformatting:** Updated the pipeline to convert HTML tables within documents to Markdown format,
  improving readability and data consistency for processed content.
- 🗣️ **Summarizer Prompt Language Consistency:** Modified summarization prompts to explicitly ensure the output summary
  is generated in the same language as the input text.
- ⚙️ **Data Lake Resource Configuration:** Updated data lake resources to include dedicated directories for storing
  extracted figures, streamlining content organization.

### Refactor

- 🧹 **Centralized Azure Suffix Constants:** Moved various Azure resource suffix constants into a single, dedicated
  constant file for improved maintainability and consistency across Infrastructure as Code (IAC) modules.
- 🗂️ **Refactored Document Parsing Logic:** Reworked the core document parsing operations to support the new figure and
  table extraction capabilities, separating concerns more clearly for better modularity.

### Fixed

- 🐛 **Typo in Document Store Removal Logic:** Corrected a minor typo in the logic for fetching reference documents to be
  removed from the document store.

---

## [v0.176.0] - 2025-06-04 - Introducing Advanced Document Intelligence with Visual Content Processing

### Added

- 🖼️ **Multimodal Document Processing**: Introduced the capability to extract figures from documents, generate detailed
  alt-text descriptions using an AI vision model (GPT-4o), and re-inject these descriptions and image URLs back into the
  document content.
- ⚡️ **Table Reformatting**: Added functionality to automatically convert HTML tables within documents into a structured
  Markdown format for improved readability and processing.
- 📄 **Page Number Metadata**: Document nodes now include a `page` metadata field, enabling precise contextual retrieval
  based on original page numbers.
- ✨ **Dedicated Figure Storage**: Implemented a dedicated directory in the data lake for storing extracted raw figure
  data, ensuring efficient management of visual assets.
- 🦾 **New Prompt Templates for Figure Descriptions**: Added specialized prompt templates to guide the AI vision model in
  generating high-quality, accessible alt-text for figures.

### Changed

- 🔄 **Revamped Document Processing Pipeline**: The entire document ingestion pipeline has been significantly refactored
  to support multimodal capabilities, including new stages for figure extraction, description generation, and table
  reformatting.
- 🧠 **Upgraded Language Model**: The default language model for the playground environment has been upgraded to
  `gpt-4o`, enhancing its capabilities, especially for vision-related tasks.
- 🧹 **Refined Data Lake File Handling**: Updated the logic for fetching files from the data lake to exclude figure
  directories, streamlining document processing.
- 🌍 **Improved Summarizer Localization**: The summarizer prompt now explicitly instructs the model to generate summaries
  in the same language as the input text, improving language consistency.

### Refactor

- ⚙️ **Modularized Document Parsing**: The core document parsing operation was refactored to separate the initial
  parsing from the final `RefDocDocument` creation, improving pipeline clarity and flexibility for multimodal steps.
- 🗑️ **Automated Figure Cleanup**: Implemented automatic deletion of associated figure data from the data lake when a
  document is removed, ensuring data hygiene.

---

## [v0.175.0] - 2025-06-02 - Refined OpenAI Integrations and Infrastructure Control

### Refactor

- 🦾 **Improved OpenAI API Integration:** Centralized and streamlined how request parameters are handled for OpenAI SDK
  calls (Chat Completions, Image Generation, Text-to-Speech). This enhancement intelligently filters and prepares
  arguments from Pydantic models, ensuring robust and error-free communication with the OpenAI API.
- ⚡️ **Enhanced Internal API Consistency:** API controllers now directly pass full Pydantic request models to service
  layers, improving type safety and internal consistency across the codebase.

### Changed

- 🔄 **Updated Core Docker Images:** Switched `docker-compose` configurations to utilize custom-built `ghcr.io` images
  for **PostgreSQL with PgVector** and **Open WebUI**, providing greater control and consistency over deployment
  environments.

---

## [v0.174.0] - 2025-05-30 - Infrastructure Constant Refinement

### Refactor

- 🧹 **Centralized Document Store Suffix:** Extracted the `DEFAULT_DOCSTORE_SUFFIX` constant from the `StoresConfig`
  module into a new, dedicated constants file, enhancing code organization and maintainability within the infrastructure
  components.

---

## [v0.173.0] - 2025-05-30 - Infrastructure Enhancements: Cosmos DB Document Store Support

### Added

- ✨ **Cosmos DB Document Store Integration:** Introduced full support for provisioning and managing Cosmos DB as a
  document store within the Azure Infrastructure as Code (IaC) layer.
- 🚀 **Standardized Cosmos DB Naming:** Implemented a new utility to ensure consistent and predictable naming conventions
  for Cosmos DB document store instances.
- 🔑 **Automated Identity Permissions for Cosmos DB:** Enhanced user-assigned identity management to automatically assign
  the necessary roles for secure interaction with Cosmos DB document stores.

---

## [v0.172.0] - 2025-05-28 - Revolutionizing LLM Evaluation: New Suite, API Refinements, and Core Infrastructure Upgrades

### Added

- ✨ **Comprehensive LLM Evaluation Suite**: Introduced a new, full-fledged module for evaluating Large Language Models
  (LLMs) and agents. This includes dedicated API endpoints, backend services, LLM-based judging (via Arize Phoenix), and
  a complete user interface.
- 🦾 **LLM-Powered Evaluation Judges**: Integrated an LLM-powered judging mechanism for automated evaluation of agent
  responses on dimensions such as correctness, completeness, and conciseness, configurable via internationalization
  (i18n) prompts.
- 📄 **Multilingual Evaluation Prompts**: Added new i18n translations for LLM judge prompts, enabling multilingual
  evaluation capabilities for agent responses and ensuring broader applicability.
- 🚀 **Arize Phoenix Integration**: Integrated Arize Phoenix as the core framework for managing and visualizing LLM
  evaluation datasets and experiment results, providing powerful insights into agent performance.
- 📚 **New UI Components for Evaluation**: Introduced a suite of new user interface components to support the evaluation
  module, including intuitive cards for datasets and experiments, and detailed results views for comprehensive analysis.
- ⚙️ **New UI Composables for Evaluation**: Added dedicated Vue composables to streamline data fetching and mutation for
  the new evaluation features, simplifying frontend development and maintenance.
- 📦 **Core Dependency: `arize-phoenix`**: Incorporated `arize-phoenix` as a primary dependency, providing the underlying
  capabilities for robust LLM evaluation.

### Changed

- 🌐 **API Route Pluralization**: Renamed key API routes (e.g., `/agent` to `/agents`, `/thread` to `/threads`, `/event`
  to `/events`, `/suite` to `/suites`, `/user` to `/users`) for improved consistency and clarity across the API surface.
- 🖥️ **UI Navigation and Path Updates**: Aligned frontend navigation paths and URLs with the new pluralized API routes,
  ensuring a consistent user experience.
- ⚡️ **Infrastructure Component Upgrades**: Updated Docker images for core services, including Phoenix (to v10.0.4),
  NATS (to 2.11.4), Redis (to 8.0.1), Mongo (to 8.0.9), Llama.cpp, HuggingFace TEI, and Attu, enhancing overall
  stability and performance.
- 🛡️ **GitHub Actions Permissions**: Refined GitHub Actions workflows to use specific `PAT_GITHUB_READ_PACKAGES` for
  package access, improving security and clarity in CI/CD processes.
- ✅ **Enhanced Docker Health Checks**: Added or improved health checks for several Docker services (Phoenix, Mongo,
  Llama.cpp, HF-TEI, Attu) to ensure better service readiness and reliability.
- 💾 **Persistent Data Volumes for Databases**: Configured data volumes for Redis and MongoDB in Docker Compose files,
  ensuring data persistence across container restarts.
- 🎨 **UI Theming Consistency**: Updated the primary color scheme in the UI theme to leverage `surface` colors, promoting
  a more cohesive and modern visual design.
- 📈 **Improved Dashboard Layout Responsiveness**: Adjusted grid column layouts in the dashboard for enhanced
  responsiveness on a wider range of screen sizes.
- 🔄 **Asynchronous Context Handling in Playground**: Applied `nest_asyncio` in the API playground to better manage
  asynchronous contexts, improving the local development experience.
- 📝 **Updated Localization Strings**: Revised several localization strings across German, French, and Italian
  translations for improved clarity and consistency, including a change from "Rounds" to "Turns" for thread
  interactions.

### Refactor

- 🧹 **Centralized Phoenix Configuration**: Relocated the `PhoenixConfig` module from `aihub_agent` to `aihub_lib`,
  centralizing infrastructure-related configurations for better maintainability.
- ♻️ **Improved i18n Object Loading**: Refactored the `LocaleHandler`'s `t_object` method to dynamically use configured
  load paths, making i18n resource loading more flexible and robust.
- 🌱 **LlamaIndex Schema Alignment**: Updated the `VectorPrevNextPostProcessor` tests to replace `Document` with
  `TextNode`, aligning with recent schema changes in the LlamaIndex library.

---

## [v0.171.0] - 2025-05-27 - Granular Network Control and Performance Boosts

### Added

- ✨ **Introduced `Storage Blob Data Contributor` Role**: A new Azure built-in role is now available, enabling
  fine-grained permissions for blob storage.
- 🗺️ **Defined Dedicated Subnet CIDRs**: Explicit CIDR blocks for Dagster, NATS, Phoenix, WebUI, and core data stores
  (Cosmos DB, Search, PostgreSQL) have been added, improving network segmentation.
- 🔑 **Granted Storage Blob Access to Dagster**: The Dagster identity is now explicitly assigned the
  `Storage Blob Data Contributor` role, ensuring proper access to its data lake.

### Changed

- 🚀 **Increased Resource Allocations**:
  - The **Dagster webserver** now benefits from increased CPU (from 0.5 to 1.5 cores) and memory (from 1Gi to 3Gi) for
    enhanced performance.
  - The **PostgreSQL database** has been upgraded with larger storage capacity (from 32GB to 64GB) and a more powerful
    SKU (`Standard_B1ms` to `Standard_B2s`) to support demanding workloads.
- 🌐 **Refined Network Provider Initialization**: Network providers now receive more comprehensive location details for
  improved consistency and accuracy in resource deployment.

### Refactor

- 🧹 **Decentralized Subnet and NSG Management**: The logic for creating subnets and Network Security Groups (NSGs) has
  been moved from the central `Network` module into the respective application modules (Dagster, NATS, Phoenix, Stores,
  WebUI). This change promotes more localized and application-specific network configurations, making the overall
  infrastructure more modular and easier to manage.
- ⬆️ **Pulumi Azure Native Provider Updates**: Updated internal Pulumi provider imports for Cosmos DB (now using
  `cosmosdb` instead of `documentdb`) and Private DNS zones (now using `privatedns` instead of `network`), aligning with
  the latest provider structure.
- ⚙️ **Improved Resource Dependency Handling**: Enhanced the provisioning logic for storage accounts and private
  endpoints to ensure robust and correct dependency resolution during deployment.
- 🔄 **Standardized NATS File Share Naming**: Corrected the file share name used for NATS to align with its intended
  purpose, improving clarity and maintainability.

### Fixed

- 🐛 **Resolved Storage Account Name Resolution**: Addressed an issue in file share creation where the storage account
  name might not be fully resolved, ensuring reliable provisioning.

---

## [v0.170.0] - 2025-05-26 - Infrastructure Tooling Enhancements

### Added

- 🚀 **New `mirror-image` Makefile Target:** Introduced a utility in `aihub_iac` to easily pull, retag, and push Docker
  images between registries, streamlining image management and distribution for internal consumption.

---

## [v0.169.0] - 2025-05-26 - Enhanced DataLakeFile Handling

### Fixed

- 🐛 **Improved DataLakeFile Owner Detection**: Enhanced the logic for determining the owner of a `DataLakeFile` to be
  more robust across different environments. The system now checks the `USER` environment variable (Unix), `USERNAME`
  environment variable (Windows), and falls back to a default `pipeline-user` if no specific user is found, ensuring
  proper ownership assignment in varied execution contexts.

---

## [v0.168.0] - 2025-05-24 - Infrastructure Refinements for Enhanced Stability

### Changed

- 🔄 **NATS Container IP Address**: Assigned a fixed private IP address to the NATS container instance in Azure
  deployments. This enhancement improves network stability and predictability for NATS within the infrastructure.

---

## [v0.167.0] - 2025-05-23 - Knowledge Base and RAG System Evolution

### Added

- ✨ **Knowledge Base Management UI**: Introduced a comprehensive new section in the Admin UI for managing and viewing
  ingested documents, their individual nodes (chunks), and generated summaries, providing deep insights into RAG data.
- 📄 **Standardized Ingested Data Models**: Implemented new Pydantic models (`IngestedDocument`, `IngestedNode`) to
  provide a consistent and rich structure for all ingested data and its metadata, improving data quality and UI display
  capabilities.
- 🚀 **Milvus Vector Store Integration**: Added explicit support and resources for Milvus as a vector store option within
  the ingestion pipelines, enhancing flexibility for vector database choices.
- 🤖 **Agent Card Component**: Introduced a new UI component for displaying agents in a card format, improving the visual
  presentation and navigation of available agents.
- 🖼️ **Dedicated Markdown Renderer**: Added a new UI component for rendering markdown content, enhancing readability and
  consistency across the application, especially for LLM responses and document nodes.
- ⚡️ **Open WebUI Actions**: Implemented new actions (`Sources` and `Tracing`) for Open WebUI, allowing users to
  directly navigate from Open WebUI conversations to detailed source documents and event traces in the AI-Hub Suite.
- 🛠️ **`attu` Service**: Included the `attu` service in the Milvus Docker Compose setup, providing a web-based GUI for
  Milvus for easier management and debugging.
- 🧩 **Pipeline Metadata Operations**: Added new pipeline operations to ensure default metadata compatibility for
  `RefDoc` documents and `TextNode` objects, standardizing data during ingestion.

### Changed

- 🔄 **Core RAG Data Model**: Renamed and restructured internal data types from generic `Document` to more granular
  `IngestedNode` across RAG agents, retriever, and reranker events, providing more precise information about retrieved
  content.
- 📖 **Context Prompt Format**: Updated the RAG agent's context prompt format from `<DOCUMENT [metadata]>` to
  `<REFERENCE_DOCUMENT [metadata]>` for clearer demarcation of contextual information from retrieved sources.
- 📈 **Enriched Document & Node Metadata**: Expanded the metadata stored with documents and nodes to include fields like
  `number_of_pages`, `document_title`, `language`, and more detailed timestamp information, improving data richness for
  UI and analytics.
- ⚙️ **Configurable Document Store Connection**: Separated and standardized the CosmosDB connection for the document
  store, allowing for more robust configuration and isolation from other database connections.
- 🔑 **API Token Controller Permissions**: Adjusted permissions for the API Token Controller, making it accessible to a
  wider range of users instead of being admin-only.
- 🔗 **Data Lake Authentication**: Added support for authentication towards Azure Data Lake using an account key,
  providing an alternative to implicit Azure login for pipeline operations.
- 🌐 **Localization Updates**: Comprehensive updates to French, German, and Italian translations to reflect new features
  and terminology across the application.
- 📊 **Agent & Thread List Enhancements**: Implemented selection and visual highlighting for agents and threads in their
  respective lists within the Admin UI, improving user navigation and context.
- ⚡️ **Azure Document Intelligence API Version**: Updated the default API version for Azure Document Intelligence to
  `2024-11-30`.

### Fixed

- 🐛 **Event ID Uniqueness in Distribution**: Ensured that distributed events to multiple agents in a thread receive
  unique event IDs, preventing potential tracing inaccuracies and improving the reliability of event tracking.
- 📏 **Metrics Accuracy in Event Summaries**: Corrected the aggregation logic for run summaries in `PersistedEventEntity`
  to accurately count `StartEvent`s and `control_events`, ensuring more precise event statistics.

### Refactor

- 🧹 **Unified MongoDB Connection Handling**: Consolidated MongoDB connection logic across the API, Agent, and Lib
  components to consistently use `ApiConfig().DB_NAME` and `CosmosDocstoreAccess`, simplifying database access
  management.
- ♻️ **Modular Pipeline Resources**: Reorganized pipeline resource factories into more modular functions (e.g.,
  `mongo_document_store_resource`, `milvus_vector_store_resource`) to improve clarity and reusability.
- 🗑️ **Removed `Document` Class**: Deprecated and removed the generic `Document` data model in
  `aihub_lib/nats/events/semantic/retriever`, standardizing on the new `IngestedNode` for all retrieval and reranking
  contexts.
- ⚙️ **UI Component Specificity**: Refined CSS class names and component structure in the web UI for better styling
  consistency and maintainability.
- 🗑️ **Removed RAG Agent Trigger Script**: Removed an outdated trigger script for the RAG agent in the playground
  environment.

---

## [v0.166.0] - 2025-05-20 - Enhanced RAG Pipelines and System Reliability

### Added

- 🦾 **Introduced Dedicated Summary Nodes Processing:** A new `summary_nodes_factory` asset has been added to provide a
  dedicated, modular pipeline for generating, embedding, and storing summary nodes, enhancing the flexibility of RAG
  workflows.
- ⚡️ **Convenience Target for Dagster Playground:** A new `playground` target was added to the Makefile, simplifying the
  setup and execution of the Dagster development environment.

### Changed

- 🔄 **Refactored Node Generation Workflow:** The primary `nodes_factory` asset no longer directly creates summary nodes,
  instead delegating this specialized task to the new `summary_nodes_factory` for improved modularity and clarity.
- ⚙️ **Updated Playground Configurations:** Adjusted default directory, namespace, and vector/document store names
  within the playground environment for better organization and consistency.

### Fixed

- 🐛 **Improved Azure Data Lake Authentication:** Corrected an issue where `DataLakeAccess` was not always passing
  credentials to `AzureBlobFileSystem`, ensuring more reliable access to Azure Data Lake resources.
- 🐞 **Ensured Document ID Filterability in Azure AI Search:** Fixed an oversight by guaranteeing that the `DOCUMENT_ID`
  field is always included in filterable metadata for Azure AI Search vector stores, enabling consistent
  document-specific queries.
- 📈 **Enhanced Vector Store Query Reliability:** Implemented a retry mechanism within `VectorStoreIOManager` when
  fetching nodes, making the pipeline more robust against transient issues and improving data retrieval stability.

---

## [v0.165.0] - 2025-05-16 - Enhanced User Experience with Dashboards and Revamped Identity Management

### Added

- ✨ **Introduced Customizable User Dashboards:** Users can now personalize their home screen with interactive widgets
  (number, line chart, and bar chart) to visualize key event timeseries data and track agent performance.
- 🚀 **New `UserEntity` for Comprehensive User Profiles:** A dedicated persistence layer has been added to store detailed
  user information, including names, emails, roles, profile images, and favorite modules, ensuring consistent data
  across the platform.
- 🔑 **Centralized Azure Graph Service:** A new service (`AzureGraphService`) is introduced to streamline asynchronous
  interactions with Microsoft Graph API, providing robust and cached retrieval of user profiles, images, and
  app-specific roles for improved performance and reliability.
- 📄 **New Localization Strings:** Added translations for new dashboard, chart, and time range terminology to support
  multi-language environments.

### Changed

- 🔄 **Revamped User Identity Retrieval:** The system now prioritizes fetching user details from the new `UserEntity` for
  faster access, falling back to external identity providers (like Azure AD) and updating the `UserEntity` as needed,
  ensuring user data is always fresh and complete.
- ⚡️ **Optimized Asynchronous API Operations:** Numerous API service and controller methods across agent, OpenAI, and
  thread management functionalities have been updated to use the `async/await` pattern, significantly improving
  application responsiveness and resource utilization.
- 🤖 **Flexible API Token Management:** API tokens no longer directly store user roles, enhancing security and allowing
  roles to be dynamically retrieved from the user's primary identity source during authentication.
- 🔒 **Improved OpenWebUI Authentication Integration:** The `OpenWebuiAuthHandler` now leverages the new
  `AzureGraphService` to fetch richer user data, including roles, directly from Azure AD, and updated its hash
  validation mechanism for enhanced security.
- 🧩 **Extensible Multi-Authentication Handler:** The `TokenAndOauth2Handler` now supports a list of authentication
  handlers for both Bearer and OAuth2 types, allowing for more flexible and layered authentication strategies.
- ⚡️ **Enhanced UI Responsiveness for Thread Updates:** The frontend now invalidates relevant queries for thread lists
  and details upon `StopEvent` or `ExceptionEvent`, ensuring immediate reflection of thread status changes in the user
  interface.
- 📊 **Dynamic Event Timeseries Filtering:** Event timeseries queries in the frontend now support optional filtering by
  `agentClass` and `agentId`, enabling more granular insights on dashboard widgets and analytics views.
- 📄 **Updated CLI Token Generation:** The `generate_api_token.py` script has been updated to use Azure CLI for fetching
  current user information and integrates with the new token creation service, aligning with the revamped token
  management.

### Refactor

- 🧹 **Unified Internal User Representation:** Introduced a new `UserIdentity` object to serve as the canonical internal
  representation of a user, decoupling it from external DTOs and internal API token structures for cleaner code and
  better maintainability.
- 🗑️ **Centralized Token User Data:** Removed the embedded `ApiUser` document and `roles` field directly from the
  `BearerToken` entity, streamlining token data to only store the `user_oid` and relying on the `UserEntity` for
  comprehensive user details.

### Removed

- 🗑️ **Direct User Details in Bearer Tokens:** The practice of embedding full user details and roles within
  `BearerToken` documents has been removed, enhancing data normalization and security by centralizing user information
  in the new `UserEntity`.

---

## [v0.164.0] - 2025-05-15 - Dependency and Infrastructure Alignment

### Refactor

- 🔄 **Refined Infrastructure Type Definitions:** Updated environment variable argument types in the Azure Container
  Instance module for improved consistency and clarity in infrastructure-as-code deployments.

---

## [v0.163.0] - 2025-05-15 - Enhanced Agent Configuration and Infrastructure Tools

### Added

- ✨ **Flexible Agent Environment Variables**: Introduced support for defining `additional_env_vars` in agent
  configurations within the Infrastructure as Code (IAC), allowing users to pass custom environment variables, including
  secret references, to agent containers for greater operational control.
- 🛠️ **Improved IAC Development Experience**: Integrated new development dependencies such as `pytest`, `ruff`, `mypy`,
  and `isort` into the `aihub_iac` project to enhance code quality, testing, and overall developer workflow.

### Refactor

- ⚙️ **IAC Resource Naming Refinement**: Updated the internal logic for generating AI search resource names within the
  IAC module for improved consistency.

---

## [v0.162.0] - 2025-05-14 - Enhanced Azure Bot Setup for Improved Integration

### Added

- ⚙️ **Azure Bot Setup**: The `setup_azure_bot.py` script now automatically creates a service principal for Azure AD app
  registrations, streamlining the setup process and ensuring smoother integration with Azure resources.

---

## [v0.161.0] - 2025-05-13 - Streamlined Admin Experience & Data Lake Optimization

### Added

- ✨ **Agent Listing Component**: Introduced a new component to display available agents in a sortable table, including
  their name, description, conversational status, and online status.
- ✨ **Display List Component**: Added a new component for listing thread displays, offering statistics such as start
  time, duration, event count, and overall status.
- 🏗️ **Column Layout Component**: Implemented a reusable `Structural/Column` component to provide a consistent visual
  structure for content columns across the application, including loading indicators and titles.
- 🖥️ **Screen Layout Component**: Introduced a new `Structural/Screen` component to standardize the overall screen
  layout and background for administrative pages.
- 📄 **Thread Details Component**: Added a dedicated component to consolidate and present comprehensive thread details,
  including integrated display selection and event lists.
- 🚀 **Infinite Thread Scrolling**: Introduced a new composable for managing infinite scrolling of threads, complementing
  the existing standard pagination logic.
- 🌐 **New Translations**: Added new internationalization strings for agent lists and thread display details across all
  supported languages (German, English, French, Italian).

### Changed

- ⚙️ **Refined Admin Interface Navigation**: Overhauled navigation and layout for Agent and Thread administration pages,
  leveraging new structural components and a `SelectButton` for sub-navigation, enhancing consistency and user
  experience.
- 🔗 **Updated Thread Display URLs**: Modified the URL structure for navigating to specific thread displays, improving
  consistency and clarity (e.g., from `/events` to `/display/[display_id]`).
- 🎨 **Improved Service Selection UI**: Enhanced the visual design and layout of the service selection popover for a more
  polished appearance and better usability.
- 💅 **Minor UI Adjustments**: Applied various small visual tweaks to component layouts, including panel headers, text
  sizes, and item alignment for improved aesthetics across the application.
- 🔄 **Switched Thread Display Component**: Replaced the direct use of `EventList` with the new `ThreadDetails` component
  for OpenAI service thread views, ensuring consistent feature presentation.
- 📈 **Timeseries Chart Library**: Switched to `VueApexChart` for event timeseries visualizations, providing enhanced
  charting capabilities.

### Refactor

- ⚡️ **Optimized Data Lake Access**: Refactored `DataLakeAccess` to cache the `AzureBlobFileSystem` client, reducing
  redundant object creation and improving performance when interacting with Azure Data Lake Storage.
- 🧹 **Streamlined Event List Component**: Simplified the `EventList` component by externalizing display selection logic
  into a parent component, making it more focused and reusable.
- 🔄 **Thread List Pagination Refactor**: Reworked the `useThreads` composable to use standard pagination instead of
  infinite scrolling for the main thread list, improving control and user experience for large datasets.
- 🗺️ **Dynamic Breadcrumb Generation**: Refactored the default layout to dynamically generate breadcrumbs based on the
  current route path, providing more accurate and flexible navigation.
- 🧹 **Standardized I18n Keys**: Performed a significant cleanup and restructuring of internationalization keys across
  all language files for better consistency and maintainability.
- 📄 **I18n Usage Consistency**: Standardized the way internationalization functions are called (from `$t()` to `t()`)
  throughout numerous web components and pages for improved consistency.

---

## [v0.160.0] - 2025-05-13 - Refined Embedding Model Configuration

### Changed

- 🔄 **Enhanced Azure OpenAI Embedding Parameter Handling:** The `dimensions` parameter for Azure OpenAI embeddings now
  robustly supports the `NotGiven` type, enabling more precise control over API requests and aligning better with the
  underlying OpenAI library's parameter conventions.

### Refactor

- 🧹 **Streamlined Embedding Model Configuration:** The `dimensions` parameter has been moved from the generic embedding
  model configuration to specific provider configurations, improving modularity and ensuring parameters are only present
  where relevant.

---

## [v0.159.0] - 2025-05-13 - Enhanced LLM Embeddings and Event Query Performance

### Added

- ✨ **Enhanced Embedding LLM Configuration:** Introduced support for specifying the `dimensions` parameter in embedding
  LLM configurations, allowing for more control over the output vector size, particularly for models like
  `text-embedding-3` and later.
- ⚡️ **Improved Event Persistence Querying:** Added a new index on `event_data.created_at` for `PersistedEventEntity`,
  significantly enhancing the performance of time-based queries on persisted event data.

---

## [v0.158.0] - 2025-05-12 - Core API Simplifications

### Refactor

- 🧹 **Streamlined Pydantic Model Creation**: Removed redundant `__base__=BaseModel` arguments from `create_model` calls
  in the API event model generation, simplifying the code while maintaining full functionality.

---

## [v0.157.0] - 2025-05-08 - Infrastructure Enhancements for WebUI Deployment

### Refactor

- 🧹 **Refined WebUI API Key Configuration**: Explicitly set optional API key fields to `None` by default in
  `OpenWebUIConfig` for improved clarity in infrastructure deployments.
- ⚙️ **Standardized WebUI Container Naming**: Renamed an internal method to `container_app_name` within `WebUIConfig`
  for consistent resource naming conventions.
- 🔗 **Integrated Registry Settings for WebUI**: Added `RegistrySettings` to `WebUIConfig`, allowing for more robust and
  configurable container registry management for WebUI deployments.

---

## [v0.156.0] - 2025-05-08 - Introducing Comprehensive Event Statistics & UI Overhaul

### Added

- ✨ **Event Timeseries API**: Introduced a new API endpoint (`/event/timeseries/{time_range}`) to retrieve time-based
  statistics for events, allowing for detailed analysis of event counts over various periods (1h, 24h, 30d, 365d) with
  adaptive resolution.
- 📊 **Dynamic Event Charts**: Implemented new UI components and composables (`EventStatistics`, `EventTimeseries`) to
  visualize event data, including agent invocations, end events (success, human/bot/agent in the loop, errors), and
  delegations, with interactive time range selection.
- 📈 **Core Timeseries Aggregation**: Added robust MongoDB aggregation logic within `aihub_lib` to efficiently calculate
  event counts across defined time buckets, supporting the new analytics capabilities.
- 🗺️ **Localization for Analytics**: Extended internationalization support to include new translation keys for event
  statistics chart titles and metrics (costs, duration).
- 🎨 **Charting Library Integration**: Incorporated ApexCharts into the web UI, enabling rich and interactive data
  visualizations.

### Changed

- 💅 **Improved Chat Message Styling**: Enhanced the visual presentation of user chat messages for better readability and
  distinction.
- 🚀 **Overhauled Agent & Thread Overview Pages**: Redesigned the agent and thread overview pages to prominently feature
  new event statistics, duration, and cost metrics, replacing older status indicators with more comprehensive data.
- ⏱️ **Adjusted Thread Data Stale Time**: Increased the cache stale time for thread data fetching to 5 minutes,
  improving performance by reducing redundant API calls for frequently accessed thread information.
- 🔄 **Refined Thread Event Updates**: Optimized thread event fetching and added cache invalidation on `StopEvent` or
  `ExceptionEvent` to ensure more immediate updates for thread status and statistics.
- 🗓️ **Standardized Date Handling**: Improved date formatting and ensured consistent UTC ISO format with timezone
  awareness for all thread-related timestamps in API responses.
- ↔️ **Enhanced Thread Panel UX**: Adjusted the positioning and styling of the thread panel close button for improved
  user experience and accessibility.

### Fixed

- 🐛 **Corrected Event Aggregation Logic**: Resolved an issue in `PersistedEventEntity`'s aggregation pipeline to ensure
  accurate counting of events by de-duplicating entries, leading to more reliable run statistics.

### Refactor

- 🧹 **Terminology Standardization**: Renamed "latency" to "**duration**" across the API DTOs, database models, and UI
  components for clearer and more consistent terminology.
- ⚙️ **Centralized Thread Access Checks**: Refactored user access validation for threads into a dedicated utility method
  within `ThreadService`, promoting code reusability and maintainability.
- 🔄 **Updated Query Naming Conventions**: Standardized query keys and transitioned from `isLoading` to `isPending` in
  various Vue composables for consistency with `pinia/colada`'s query state management.

---

## [v0.155.0] - 2025-05-08 - Enhanced Speech-to-Text Capabilities and Infrastructure Updates

### Added

- 🚀 **Enhanced Speech-to-Text (STT)**: Introduced intelligent audio chunking to seamlessly process and transcribe large
  audio files by splitting them at silence points and merging the results, overcoming typical API size limitations. This
  significantly improves the reliability and reach of STT services.
- 📦 **FFmpeg Requirement**: Integrated the necessary `pydub` library and **FFmpeg** installation steps within
  `aihub_api` and the CI/CD pipeline to support advanced audio processing functionalities.
- 💾 **Persistent MongoDB Data**: Ensured data durability for **MongoDB** by adding a persistent volume to the
  `docker-compose.yml` configuration, preventing data loss across container restarts.
- 🧪 **Comprehensive Audio Tests**: Added extensive test coverage for the new audio chunking and transcription merging
  functionalities to guarantee robust performance and accuracy.

---

## [v0.154.0] - 2025-05-08 - Streamlined Versioning and IAC Integration

### Changed

- 🔄 **Automated Versioning Scope**: The `aihub_iac` project has been fully integrated into the automated version tagging
  workflow, ensuring consistent release management and version alignment across all core components.

---

## [v0.153.0] - 2025-05-08 - Internal Tooling and CI/CD Scope Expansion

### Changed

- ⚙️ **Expanded Semantic PR Scopes:** Added `iac` (Infrastructure as Code) and `ci-cd` as recognized scopes for semantic
  pull requests, enhancing consistency and automation for relevant contributions.

---

## [v0.152.0] - 2025-05-08 - Introducing Comprehensive Azure Infrastructure as Code

### Added

- ✨ **Comprehensive Azure IaC Module**: Introduced `aihub_iac`, a new Pulumi-based Infrastructure as Code module for
  deploying the entire AIHub platform on Azure. This enables consistent, automated, and version-controlled provisioning
  of all necessary cloud resources.
- 🚀 **Modular and Secure Infrastructure Deployment**: The new IaC module features a component-based design with
  dedicated providers for network, identity, and resource creation, ensuring modularity, reusability, and secure private
  networking for core services.
- 🌐 **Automated Microservice Deployment**: Integrated Pulumi resources for automated deployment of all AIHub
  microservices, including **API**, **Bot**, and **Phoenix** (as Azure App Services) and **Agents**, **NATS**,
  **Redis**, **Dagster**, and **OpenWebUI** (as Azure Container Instances or Container Apps).
- 💾 **Managed Data Stores**: Provisioned and configured managed data services, including **Azure Cognitive Search** for
  vector capabilities, **Azure Cosmos DB** for document and API storage, and **Azure PostgreSQL Flexible Server** with
  `pgvector` extension for relational and vector data.
- ⚙️ **Core Infrastructure Services**: Established foundational infrastructure components such as a private **Virtual
  Network** with segmented subnets, **Network Security Groups**, and **Private Endpoints** to enhance security and
  isolation.
- 📄 **Expanded On-Premises Technology Overview**: Enhanced the `README.md` to reflect the newly supported and integrated
  on-premises technologies, specifically detailing **Postgres (SQL DB)**, **PG-vector** for vector capabilities, and
  **Docker** for application environments.

---

## [v0.151.0] - 2025-05-06 - Comprehensive Thread Management & Enhanced Agent Insights

### Added

- ✨ **Comprehensive Thread Statistics**: Introduced detailed metrics for each thread, including event counts,
  conversation turns, pending operations, error states, total LLM costs, and interaction latency. These statistics are
  aggregated per display and individual runs for granular insights.
- 🦾 **Agent Persistence**: Agents are now persisted in the database, allowing for discovery and retrieval of both online
  and offline agents and their configurations.
- 📄 **Paginated Thread Views**: New API endpoints and UI sections to retrieve paginated lists of threads associated with
  users and specific agents, improving navigability for large datasets.
- 🔄 **Thread History Reconstruction**: Enabled the API to reconstruct full chat message history for OpenAI API calls
  based on persisted thread events, facilitating seamless conversation continuity.
- 🗺️ **Workflow Hierarchy Visualization**: Introduced a new visual component to display the hierarchical structure of
  thread executions, illustrating how displays and runs are nested.
- 🌐 **Locale-Aware Event Display**: Implemented internationalization for event names and descriptions in the UI,
  ensuring that event details are displayed in the user's preferred language.
- 💬 **Multimodal Chat Message Support**: Extended the backend and frontend to properly handle and display chat messages
  containing various content types, including images and audio.
- 🛡️ **`GuardEvent` for Tracing**: A new event type (`GuardEvent`) has been added to provide better tracing and
  visibility into security and policy guardrail evaluations within agent workflows.
- 🚦 **`RouterEvent` for Decision Visibility**: Introduced `RouterEvent` to clearly mark and visualize points in the
  workflow where an LLM makes a decision on the optimal next path.
- 💥 **`ExceptionEvent` as Semantic Event**: The `ExceptionEvent` now inherits from `SemanticEvent`, enabling its data to
  be reported to OpenInference-compatible tracing systems for enhanced error monitoring.
- 🧪 **Playground Testing Agents**: Added new test agents in the playground to demonstrate and validate complex workflow
  patterns, including explicit routing and bot-in-the-loop interactions.
- 🧩 **`ControlAndDisplayEvent` Base Class**: Introduced a new helper base class to simplify the creation of events that
  serve both as workflow control signals and user-facing display messages.
- 👤 **New UI Components**: Added dedicated UI components for displaying Agent and User Avatars, enhancing visual
  consistency and clarity.

### Changed

- 🧹 **Internal i18n Key Refactoring**: Standardized internationalization keys across agents from `agents.<scope>` to
  `agent.<scope>` for improved consistency.
- ⚡️ **Optimized Agent Workflow Control**: Refactored `ExpertGroundedAgent` and `LLMWrappingAgent` to return direct
  `StopEvent` or `AgentInTheLoop.request` where appropriate, streamlining their workflow integration.
- 🚀 **Streamlined API Thread Operations**: Refactored thread management operations in `aihub_api` to directly interact
  with the persistence layer (MongoDB), removing NATS as an intermediary for these specific tasks, which simplifies the
  architecture and improves performance.
- 🌐 **Improved WebSocket Locale Handling**: The WebSocket connection now explicitly extracts the user's locale from
  request headers for more accurate language presentation of real-time events.
- 🧰 **Updated UI Components**: Enhanced existing UI components, including `ChatMessage`, `CostsTable`, and event display
  components, to integrate with new data structures and internationalization.
- 📦 **Dependency Updates**: Updated numerous core dependencies, including OpenTelemetry, LlamaIndex, and OpenAI
  libraries, for improved performance, stability, and new features.
- 🧹 **Refactored Frontend Data Management**: Migrated existing Pinia stores to use `@pinia/colada` queries and standard
  Nuxt composables for a more modern and efficient data fetching and state management pattern.
- 📈 **Enhanced Logging**: Replaced numerous `logger.error` calls with `logger.exception` across the codebase to ensure
  full stack trace capture for better debugging.

### Fixed

- 🐛 **Robust Event Deserialization**: Improved the `BaseEvent` deserialization logic to more accurately handle events
  with multiple inheritance paths, preventing potential data interpretation issues.
- 🪲 **AnyUrl Serialization in Events**: Addressed an issue where `AnyUrl` fields within chat messages were not correctly
  serialized in `UserMessageEvent`, ensuring proper display of embedded URLs.

### Removed

- 🗑️ **Deprecated Thread & Agent UI Pages**: Replaced outdated thread and agent management pages with new, more robust,
  and feature-rich implementations.
- 🗑️ **Redundant Playground Components**: Removed legacy playground components like `UserMessageEvent` form and
  `Thread/Chat` that are superseded by new UI and testing features.

---

## [v0.150.0] - 2025-05-04 - LLM Evolution: Introducing Gemini and Intelligent Content Summarization

### Added

- ✨ **Google Gemini LLM Support**: Introduced `GeminiLLMConfig` and integrated Google Gemini models into the `aihub_api`
  and `aihub_lib`, allowing for more diverse LLM choices.
- 📄 **Recursive Document Summarization**: Added a new `RecursiveNodeSummarizer` and integrated it into the RAG pipeline
  (`aihub_pipeline`), enabling hierarchical summarization of documents to improve retrieval and context understanding.
- 🚀 **New Pipeline Playground**: A comprehensive Dagster pipeline playground (`aihub_pipeline/playground`) was
  introduced to facilitate testing and development of RAG ingestion workflows with new features like recursive
  summarization.

### Changed

- 🦾 **Stricter Agent Description Guard Prompt**: Updated the prompt for the agent description guard across all languages
  to enforce a stricter JSON output format, ensuring more reliable structured responses.
- ⚡️ **Improved Recursive Summarization Parameters**: Adjusted the minimum summarization length and enhanced locale
  handling within the `RecursiveNodeSummarizer` for more flexible and accurate document summaries.

### Refactor

- 🔄 **Standardized OpenAI-like LLM Naming**: Renamed `SelfHostedLLMConfig` and `SelfHostedLLMParameter` to
  `OpenaiLikeLLMConfig` and `OpenaiLikeLLMParameter` across the codebase. This standardizes the configuration for models
  that adhere to the OpenAI API specification but are hosted locally or externally.
- 🧹 **Internal Module Reorganization**: Reorganized internal imports and module structures within `aihub_agent` and
  `aihub_bot` to improve code clarity and maintainability.

---

## [v0.149.0] - 2025-05-04 - Enhanced LLM Flexibility with Gemini Support

### Added

- ✨ **Google Gemini LLM Support**: Introduced `GeminiLLMConfig` and associated configurations, enabling seamless
  integration and usage of Google Gemini chat models via their OpenAI-compatible API.

### Refactor

- 🧹 **Standardized OpenAI-like LLM Configuration**: Renamed `SelfHostedLLMConfig` to `OpenaiLikeLLMConfig` to more
  accurately reflect its compatibility with various OpenAI-like API endpoints, improving clarity and broad applicability
  across the codebase.
- 🔄 **Updated RAG Agent Module Path**: The `RAGAgent` and its related configuration files have been reorganized and
  moved to a new, more logical module path (`aihub_agent.agents.RagAgent`), streamlining the internal structure of agent
  implementations.

---

## [v0.148.0] - 2025-04-24 - Enhanced RAG Agent Context Sufficiency

### Changed

- 🦾 Refined **RAG Agent's context handling**: The RAG Agent now provides more precise information to its context
  sufficiency guard regarding the availability of further retrieval attempts (hops), allowing for more informed
  decision-making.
- ⚙️ Improved **Context Sufficiency Guard**: The guard's response structure and internal logic now adapt dynamically
  based on whether more retrieval hops are available. This leads to more accurate reasoning and a tailored output,
  providing clearer indications when the maximum retrieval attempts have been reached or when further queries are still
  possible.

---

## [v0.147.0] - 2025-04-24 - Enhanced Azure AI Search Vector Store Configuration

### Added

- ✨ **Configurable Azure AI Search Embedding Dimensions:** Introduced a new `dimensions` parameter for Azure AI Search
  vector stores, allowing users to specify the embedding dimensionality (defaulting to 3072). This feature ensures
  better compatibility and performance by enabling the vector store to precisely match the output dimensions of
  different embedding models used for RAG operations. This enhancement is available through `aihub_lib` and integrated
  into `aihub_pipeline` resources and definitions for seamless configuration.

---

## [v0.146.0] - 2025-04-17 - Enhanced Conversation Management and Bot Persistence

### Added

- ✨ **Introduced Conversation Tracking**: Added a new `ConversationTracker` entity to distinguish between conversations
  that automatically expire due to inactivity and those explicitly deleted by users (e.g., in Microsoft Teams).
- 💾 **Configurable Conversation Time-To-Live (TTL)**: Implemented MongoDB TTL indexing for `ConversationEntity` based on
  conversation inactivity, allowing for automatic cleanup of old conversations.
- 🗣️ **Expired Conversation Notification**: Bots now inform users when they resume an expired conversation, providing
  clarity that previous messages are no longer available.
- ⚙️ **Customizable Typing Indicator Timeout**: Added a `typing_timeout_seconds` parameter, allowing configuration of
  how long the bot's "typing" indicator is shown before it times out.

### Changed

- ⏱️ **Conversation Inactivity Tracking**: The `ConversationEntity` now automatically updates a `last_activity`
  timestamp with every user message, crucial for the new TTL mechanism.
- 🚀 **Bot Runner Configuration**: The `BotRunner` now accepts a `conversation_ttl_days` parameter to easily configure
  conversation persistence across all mounted bots.
- 💬 **Bot Route Configuration**: Agent and OpenAI chat controllers now allow specifying `typing_timeout_seconds` for
  fine-grained control over the typing indicator behavior for specific chat endpoints.
- 🧹 **Conversation Reset Logic**: Improved handling of conversation resets in platforms like Microsoft Teams by
  explicitly marking conversations as deleted when a user initiates a new chat session with the same conversation ID.

---

## [v0.145.0] - 2025-04-16 - Streamlined AI Hub Connections and Agent Playgrounds

### Added

- ✨ **New Long-Running Agent Example:** Introduced a new playground example demonstrating how to create and manage
  agents that stream output incrementally over an extended period, showcasing real-time progress.

### Changed

- 🔄 **Improved AI Hub Connection Handling:** The `pipe` function in `webui_pipelines/aihub_connection.py` now dispatches
  to dedicated handlers for streaming and non-streaming chat completion requests, ensuring more robust and explicit
  management of different response types.
- 📈 **Enhanced Model Fetching Error Reporting:** Improved error handling and reporting when fetching available models
  from the AI Hub API, providing clearer feedback on connection issues.

### Refactor

- 🧹 **Asynchronous HTTP Client Migration:** Switched the underlying HTTP client in `webui_pipelines/aihub_connection.py`
  from `requests` to `httpx.AsyncClient` for improved asynchronous performance and reliability in handling API requests.
- ⚡️ **Consistent Source Event Retrieval:** Refactored the logic to consistently query and emit source events (retrieved
  documents) after both streaming and non-streaming chat completions are finished, providing more reliable RAG context
  in the UI.
- ⚙️ **Stream and Non-Stream Request Specialization:** Separated the core logic for handling streaming and non-streaming
  chat completion requests into distinct, specialized functions (`pipe_stream` and `pipe_non_stream`) for better code
  organization and maintainability.

---

## [v0.144.0] - 2025-04-15 - Introducing Adaptive Context Retrieval for RAG Agents

### Added

- ✨ **Introduced Multi-Hop Retrieval for RAG Agents:** RAG agents can now perform multiple retrieval attempts (hops)
  with dynamically generated and refined queries if the initial context is insufficient, significantly improving the
  chances of finding relevant information.
- 📄 **New `ContextInsufficientWithQueryEvent`:** This event has been added to facilitate the multi-hop retrieval process
  by carrying a revised query for subsequent retrieval attempts when the initial context is deemed insufficient.

### Changed

- 🔄 **Enhanced Context Sufficiency Guard:** The `context_sufficient_guard` now intelligently generates new, distinct
  queries for further context retrieval. It considers previous query attempts to avoid repetition and guides the LLM to
  explore higher-level conceptual hierarchies when direct approaches fail.
- 📈 **Increased LLM Context Window:** The default context size for self-hosted LLMs (e.g., Llama-3.2-1B-Instruct-GGUF)
  in `docker-compose` configurations and tests has been significantly increased from 512 to 8192 tokens, enabling the
  processing of more extensive context.
- ⚙️ **RAG Agent Configuration for Hops:** A `max_hops` configuration option has been added to `RAGAgentConfig`,
  allowing users to control the maximum number of retrieval attempts the RAG agent will perform.
- 🧪 **Updated RAG Agent Playground:** The RAG Agent playground now defaults to using Azure OpenAI LLM and includes a new
  scenario demonstrating the multi-hop retrieval capability.

### Refactor

- 🧹 **Refined Guard Result Naming:** Renamed the `GuardResult` class to `ContextGuardResult` within `aihub_lib` for
  improved clarity and semantic consistency.
- 🗑️ **Cleaned Azure OpenAI Embedding Parameters:** Removed the `dimensions` field from `AzureOpenAIEmbeddingParameter`
  for schema simplification, as it was not actively used.

---

## [v0.143.0] - 2025-04-11 - Agent Evolution, Advanced Routing, and Integration Enhancements

### Added

- ✨ **Expert-Asking Agent**: Introduced a new agent that automates posing questions to designated experts via Slack,
  manages follow-up questions for insufficient answers, and stores sufficient responses as knowledge snippets in
  OpenWebUI.
- 🦾 **Expert-Grounded Agent**: Added a new agent that leverages existing context and conversation history to answer user
  queries. If knowledge is insufficient, it intelligently prompts the user for consent to consult a human expert via the
  new Expert-Asking Agent.
- 🚀 **OpenWebUI SDK Integration**: Integrated a comprehensive Software Development Kit (SDK) for OpenWebUI within
  `aihub_lib`, enabling direct programmatic interaction with OpenWebUI's chat, file management, and knowledge base
  functionalities.
- ⚡️ **LLM-Based Routing Framework**: Implemented a new dynamic routing mechanism that allows agents to use Large
  Language Models (LLMs) to make intelligent decisions on the next step in a workflow, enhancing agent adaptability and
  complexity.
- 📈 **RAG Embedding Batch Size Configuration**: Added a new configuration option for the RAG agent within
  `docker-compose-webui.yml` to specify the batch size for embedding generation, potentially improving performance.
- 📦 **New Dependency**: Included the `stringcase` library to support advanced string manipulation for improved filename
  generation in agents.

### Changed

- 🌐 **Enhanced Internationalization (i18n) Support**: Improved locale handling across the API, bot, and pipeline
  components, allowing user language preferences to be passed consistently to agents for more localized responses.
- 🔄 **LLM API Version Update**: Updated the Azure OpenAI LLM API version to `2024-12-01-preview` across all
  configurations and playground examples for improved compatibility and access to the latest features.
- 🚨 **Improved Error Logging**: Replaced `traceback.print_exc()` with `logger.exception(e)` for more structured and
  robust error logging within the dispatcher and NATS subscribers, enhancing debugging and system stability.
- 📄 **Displayable Workflow Events**: Made key internal workflow events, such as **Limit Chat History** and **Standalone
  Question Condenser**, displayable in the user interface to provide greater transparency into agent processing. The
  **Start Event** is also now explicitly displayable.
- 🛑 **Streamed LLM Responses**: Enhanced the LLM event displayer to allow streamed Large Language Model responses to
  directly signal the conclusion of a workflow run, streamlining agent completion.
- 🔧 **Agent Runner Validation**: Added robust type and subclass validation for agent types during initialization of the
  `AgentRunner`, preventing common misconfigurations.
- ⚙️ **OpenWebUI Docker Compose Configuration**: Modified default OpenWebUI settings in `docker-compose-webui.yml` to
  disable automatic configuration resets and channels on startup, and enabled API key authentication by default.
- 📝 **Context Event Documentation**: Updated the `ContextInsufficientEvent` and `ContextSufficientEvent` with clearer
  docstrings and improved field definitions for better understanding and usage.
- 💬 **Playground BotInTheLoopAgent Update**: Updated the playground `BotInTheLoopAgent` to explicitly include the Slack
  channel ID when invoking bot interactions.

### Refactor

- 🧹 **Agent Base Class Simplification**: The core `Agent` base class has been moved and simplified, removing its
  previous `abstract` categorization for a more direct and accessible inheritance model.
- 📂 **Agent Directory Restructuring**: Reorganized agent modules and their associated files (e.g., `FewShotAgent`,
  `LLMWrappingAgent`, `RagAgent`, `WebuiAgent`) into flatter, more intuitive directory structures for improved
  discoverability and maintainability.
- 📦 **Centralized Common Events**: Relocated frequently used control events, such as `LimitChatHistoryEvent` and
  `StandaloneQuestionCondenserEvent`, from `aihub_agent` to `aihub_lib` to centralize common event definitions and
  promote reuse across components.
- 🏷️ **Prompt Template Naming Consistency**: Renamed the `user_question` variable to `user_query` within prompt
  templates for better consistency and clarity.
- 🔗 **Robust Event Serialization**: Improved the event serialization and deserialization logic to correctly handle lists
  containing embedded event or model instances, enhancing the reliability of complex event structures.

### Fixed

- 🐛 **Thought Event Formatting**: Corrected an issue where `ThoughtEvent` content might have leading/trailing whitespace
  in display tests, ensuring consistent formatting.
- 🛠️ **Event Naming Consistency**: Rectified an inconsistency in event naming for `HumanInTheLoopResponseEvent` within
  the chat service, improving internal consistency.

---

## [v0.142.0] - 2025-04-10 - Streamlined Bot-in-the-Loop Interactions and Improved Azure Bot Setup

### Changed

- 🔄 **Bot-in-the-Loop Request API Update:** The `BotInTheLoop.invoke` method now exclusively requires the **Slack
  channel ID** (e.g., `C08MCK6LEBY`) instead of the full conversation ID. The bot automatically derives the complete
  conversation identifier, simplifying agent configuration.
- ⚙️ **Internal Slack Conversation ID Management:** The bot now dynamically retrieves and caches Slack bot and team IDs
  using the `auth.test` API, which are then used to construct full conversation identifiers. This enhances flexibility
  and reduces manual configuration requirements.
- 🧹 **Refined Bot-in-the-Loop Thread Tracking:** Internal thread management for Bot-in-the-Loop interactions now
  utilizes Slack's `thread_ts` (timestamp) for more robust and accurate tracking of conversations.
- 🛠️ **Improved Azure Bot Setup Script Robustness:** The `setup_azure_bot.py` script now automatically checks for
  existing Azure AD app registrations, parses command output more robustly, and includes auto-confirmation for
  deletions, streamlining the Azure Bot deployment process.

### Added

- 🗣️ **Responder Information in Bot-in-the-Loop Responses:** `BotInTheLoop.response` events now include an optional
  `responder` field, providing details such as `user_id` and `user_name` of the Slack user who provided the input,
  enabling better accountability and context.
- 📄 **New Slack Utilities Module:** Introduced `SlackUtils` to encapsulate logic for interacting with the Slack API,
  specifically for fetching essential bot and team IDs, supporting the new conversation ID management.

---

## [v0.141.0] - 2025-04-09 - Enhanced Test Infrastructure and Core Library Updates

### Changed

- 🚀 **Improved CI/CD Docker Health Checks:** Enhanced the GitHub Actions backend test workflow with more robust Docker
  service health checks. This includes added timeout mechanisms, checks for Docker availability, and clearer
  diagnostics, leading to greater test reliability and better troubleshooting.
- ⬆️ **Upgraded `llama-index-vector-stores-milvus`:** Updated the core `aihub_lib` dependency for Milvus vector store
  integration from version `0.6.0` to `0.7.3`, incorporating upstream improvements and increased stability.

### Fixed

- 🐛 **Stabilized Milvus Vector Store Tests:** Addressed intermittent test failures related to Milvus vector store
  operations by introducing a small, strategic delay after data ingestion, ensuring that the vector store is fully ready
  for subsequent test queries.

---

## [v0.140.0] - 2025-04-09 - Enhanced Agent-Bot Interaction with Bot-in-the-Loop Capabilities

### Added

- 🤖 **Bot-in-the-Loop (BiTL) Workflows**: Introduced a powerful new capability allowing agents to pause execution and
  solicit direct input or approval from human operators via a bot, currently integrated with Slack.
- ✨ **New `BotInTheLoopAgent`**: A dedicated agent now available in the playground to demonstrate and initiate these
  interactive Bot-in-the-Loop requests.
- 💬 **`BotInTheLoopBot`**: A specialized bot has been added to handle and relay responses from human operators back into
  ongoing agent workflows, ensuring seamless interaction.
- 📬 **BiTL Event Framework**: Implemented new NATS event types (`BotInTheLoopRequestEvent` and
  `BotInTheLoopResponseEvent`) within `aihub_lib` to standardize communication for human intervention steps.
- 🚀 **Core System Support for BiTL**: Updated the agent dispatcher and external event distributor to fully support the
  routing and processing of Bot-in-the-Loop events.
- ⚙️ **IntelliJ Run Configuration for BiTL Agent**: Added a convenient run configuration for developers to easily run
  and debug the `BotInTheLoopAgent` within IntelliJ.

### Refactor

- 🧹 **Unified Chat Bot Architecture**: Reorganized the `aihub_bot`'s internal structure by consolidating chat-related
  bots (Agent and OpenAI) into a new `chat` subdirectory, enhancing code organization and maintainability.
- ♻️ **Routes Service Enhancements**: Minor internal refactoring within `RoutesService` to streamline credential
  retrieval.

### Changed

- 🛠️ **Improved Dependency Management**: The `switch_dependencies.py` script now automatically runs `poetry install`
  after `poetry lock`, simplifying environment setup for developers.

---

## [v0.139.0] - 2025-04-08 - Visualizing Agent Journeys: UI Refresh and Event System Evolution

### Added

- ✨ **Enhanced Frontend Event Visualization:** Introduced a comprehensive set of new Vue components
  (`AgentInTheLoopRequestEvent`, `ChunkEvent`, `EmbeddingEvent`, `LLMCostEvent`, `LLMEvent`, `RerankerEvent`,
  `RetrieverEvent`, `ThoughtEvent`, `ToolEvent`, `UserMessageEvent`, `StopEvent`, `HumanInTheLoopRequestEvent`,
  `HumanInTheLoopResponseEvent`, and more) to provide rich, type-safe, and user-friendly displays for various event
  types in the UI, offering deeper insights into agent behavior.
- 🚀 **Integrated Open WebUI as a Core Frontend:** Shipped a full integration of Open WebUI as a powerful chat interface,
  including dedicated Docker Compose configurations (`docker-compose-webui.yml`) and pipeline scripts
  (`webui_pipelines/aihub_connection.py`, `webui_pipelines/suite_connection.py`) to connect it to the AI-Hub backend.
- 📈 **New Event Tracing & Source Display:** Implemented a new "Sources" drawer in the UI (accessible via Open WebUI
  integration) that visualizes detailed backend events (like retrieved documents) for any given chat session,
  significantly improving observability and debugging capabilities.
- 🦾 **Dedicated Frontend Testing Agent:** Introduced `FrontendTestingAgent` and its associated configurations, providing
  a specialized agent to simplify and accelerate the development and testing of new frontend event display features.
- 🔑 **Azure AD Integration for Open WebUI Users:** Enhanced Open WebUI authentication to leverage Azure Active Directory
  for user and role information, providing more robust security and role-based access control.
- ⚡️ **Performance Improvements for User & Thread Data:** Added caching for Azure AD user information and thread-user
  lookups, reducing database load and improving response times for common operations.
- 📚 **Comprehensive Product Pitch Documentation:** Included a new `0_product_pitch.md` document along with supporting
  media, offering a high-level overview of the AI-Hub's vision, architecture, and benefits.
- 🔌 **Standardized WebSocket Dependencies:** Introduced new dependency injection utilities (`use_ws_manager_ws`,
  `use_ws_sender_ws`, `use_external_event_distributor_ws`, `use_nats_ws`) to streamline the integration of NATS,
  WebSocket management, and external event distribution in WebSocket contexts.

### Changed

- 🔄 **Core Event System Revitalization:** Undertook a major refactor of the internal event system across `aihub_agent`
  and `aihub_lib`, standardizing event identification using `event_name` (string identifier) and `event_class` (Python
  type). This improves clarity, consistency, and robustness in event processing and serialization.
- 🛡️ **Refined `AuthHandler` for WebSocket Authentication:** Updated the `AuthHandler` interface to include a direct
  `authenticate_token` method, improving flexibility and consistency for WebSocket connections and other non-HTTP
  authentication scenarios.
- 🧹 **Unified ID Conversion Utility:** Centralized string-to-ObjectId conversion into a new `str_to_object_id` utility,
  eliminating redundant logic in `ThreadEntity` and other modules.
- 💬 **Enhanced Chat Service Context Handling:** Improved the chat service's ability to handle and pass `thread_id` and
  `display_id` for better context tracking in conversational flows.
- 🧠 **Structured Reasoning Content in Responses:** Modified `ChunkEvent` to include an optional `reasoning_content`
  field and updated the chat service to expose this in responses, allowing for streaming of internal agent thoughts
  directly to the frontend.
- 📊 **Granular Event Filtering for API:** Expanded the `GET /event/` API endpoint to support filtering by `thread_id`,
  `display_id`, and `event_class`, enabling more precise retrieval of historical events.
- 📦 **API Payload Structure for WS Events:** Reworked the `WSServerEvent` payload to use a polymorphic `event` field
  instead of a generic `event_data` dictionary, providing strong typing and easier consumption for frontend clients.
- 🐛 **Fixed Duplicate Agent Discovery Entries:** Addressed an issue where agent discovery could lead to duplicate agent
  entries in the API response.
- 📃 **Updated Documentation Examples:** Aligned code examples in `aihub_doc/5_agents_in_detail.md` to reflect the new
  `event.event_name` property usage.
- 🚀 **Improved Frontend Serving:** Enhanced the `Runner.mount_frontend` method to better serve Nuxt.js SPAs, including
  specific handling for `_nuxt` and `_fonts` static assets and a catch-all route for client-side routing.
- ⚙️ **Development Environment Updates:** Updated `CLIENT_ID` in development environment configurations and adjusted
  OpenAI base URLs.

### Removed

- 🗑️ **Deprecated Open WebUI Page:** Removed the previous `aihub_web/pages/module/webui/index.vue` page, replaced by the
  new, more robust integration.
- 🗑️ **Redundant `ThreadEntity.to_thread_id`:** Eliminated the now-obsolete `to_thread_id` method from `ThreadEntity`
  following the introduction of a centralized ID conversion utility.
- 🗑️ **Consolidated `ExternalEvent` Export:** Removed a redundant `__init__.py` file related to `ExternalEvent` as its
  definition is now centrally managed.
- 🗑️ **Outdated WebSocket Receiver Modules:** Cleaned up and removed old `aihub_api/aihub_api/sockets/receiver` modules,
  replaced by the new, refactored WebSocket architecture.

---

## [v0.138.0] - 2025-04-07 - Core Infrastructure and Testing Improvements

### Changed

- 🚀 **Upgraded Milvus Vector Store Integration:** Updated the `llama-index-vector-stores-milvus` dependency from `0.3.0`
  to `0.6.0`, bringing the latest enhancements and fixes for vector store operations.
- 🧪 **Enhanced Asynchronous Test Stability:** Introduced session-scoped asyncio event loops within test fixtures to
  ensure more reliable and consistent execution of asynchronous tests.
- ⚙️ **Streamlined Local Development Setup:** Refined the NATS service configuration in `docker-compose.yml` by removing
  the health check, which helps optimize the local development environment startup.

---

## [v0.137.0] - 2025-04-07 - Core Event System Enhancements

### Changed

- 🔄 **Improved Human-in-the-Loop (HITL) Event Handling:** Enhanced the serialization and deserialization of
  `HumanInTheLoopResponseEvent` within the chat service to ensure proper type information is consistently included,
  leading to more robust and reliable event processing.

---

## [v0.136.0] - 2025-04-02 - Improved LLM Guarding and Structured Output

### Refactor

- 🧹 **Refactored `ContextSufficientGuard`**: The internal implementation of the `context_sufficient_guard` has been
  updated to leverage `llm.structured_predict` for more robust and localized structured output parsing, enhancing the
  reliability of context sufficiency checks.
- ⚙️ **Modernized LLM Interaction**: Switched from `LLMTextCompletionProgram` to direct `llm.structured_predict` calls,
  improving how structured data is extracted from LLM responses and enabling dynamic Pydantic model generation for
  better internationalization.

### Changed

- 📄 **Updated Internationalization Definitions**: Adjusted translation files for `context_sufficient_guard` to support
  the new structured output fields and streamline prompt templates, improving clarity and consistency across languages.

---

## [v0.135.0] - 2025-04-01 - Bot Core Overhaul: Architecture Refinements and Localized Messaging

### Refactor

- 🧹 **Unified Bot Logic with `BaseChatBot`:** Introduced a new base class, `BaseChatBot`, to centralize and standardize
  common functionalities across all chatbot types, including message processing, typing indicators, and conversation
  management.
- 🔄 **Redesigned Completion Handling:** Refactored the core `Service` into a more abstract `CompletionHandler` to
  implement a strategy pattern, streamlining how different AI models (e.g., Agents, OpenAI) generate responses.
- 🚚 **Restructured Bot Modules:** Reorganized bot-related files and modules (e.g., `ContentExtractor`,
  `AgentChatService`, `OpenaiChatService`) into a clearer, more maintainable directory structure.
- 🧹 **Streamlined Bot Implementations:** Simplified `AgentChatBot`, `StreamAgentChatBot`, `OpenaiChatBot`, and
  `StreamOpenaiChatBot` classes by migrating shared logic to the new `BaseChatBot`.
- ⚙️ **Standardized Database Naming:** Aligned database and collection names for bot paths (`aihub_bot` to `aihub`,
  `paths` to `bot_paths`) for consistency.

### Added

- 🌍 **Internationalization for Bot Error Messages:** Implemented support for localized error messages, providing users
  with clearer and more relevant feedback in their preferred language.

### Fixed

- 🐛 **Improved OpenAI API Error Handling:** Enhanced the `OpenaiCompletionHandler` to specifically catch and display
  detailed error messages from OpenAI's API, offering better transparency for API-related issues.

### Changed

- 📝 **Flexible Locale Handling:** Updated `LocaleHandler.t_object` to allow optional locale arguments, providing more
  flexible usage when retrieving translated objects.

---

## [v0.134.0] - 2025-04-01 - Core Component Synchronization

### Changed

- 🔄 **Synchronized Component Versions:** All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_pipeline`) and the shared `aihub_lib` have been updated to `v0.134.0`, ensuring consistent internal dependency
  alignment across the platform.
- ⚙️ **Makefile Tag Update:** The `Makefile`'s default `TAG` for remote core operations has been updated to `v0.134.0`
  to reflect the new coordinated release version.

---

## [v0.133.0] - 2025-04-01 - Improved API Error Handling with Custom Status Codes

### Added

- ✨ **`ExceptionEvent` Custom Status Code:** Introduced a new `http_status_code` field to the `ExceptionEvent` to allow
  services to specify precise HTTP status codes for exceptions.

### Changed

- 🚀 **API Error Response Precision:** The API now leverages the `http_status_code` from `ExceptionEvent` to return more
  accurate and specific HTTP status codes to clients, enhancing error visibility beyond a generic 500 internal server
  error.
- 🔄 **Agent Service Error Propagation:** The `AgentService` has been updated to explicitly allow the return of an
  `ExceptionEvent`, ensuring more detailed error information is propagated from agent operations.

---

## [v0.132.0] - 2025-04-01 - Improved Chatbot Reliability and User Feedback

### Changed

- 🔄 **Enhanced Chatbot Error Handling:** Standardized and centralized the handling of unexpected errors across all
  chatbot types (Agent and OpenAI, streaming and non-streaming) to provide more consistent user feedback and better
  internal logging.
- ⚡️ **Introduced Response Timeout for Chatbots:** Chatbots now detect and notify users if a response takes an unusually
  long time, preventing indefinite waiting and indicating potential issues.
- 🔗 **Improved Internal Exception Propagation:** Enhanced the system's ability to propagate specific `ExceptionEvent`
  types from core services, allowing for more precise and robust error management within the chatbot framework.

---

## [v0.131.0] - 2025-04-01 - Enhanced Markdown Parsing Accuracy

### Fixed

- 🐛 **Markdown Parsing:** Improved the accuracy of Markdown document parsing by automatically unescaping HTML entities,
  ensuring that content extracted from Markdown files is correctly represented without escaped characters.

---

## [v0.130.0] - 2025-03-31 - Visual Workflows, Dynamic APIs, and UX Polish

### Added

- ✨ **Agent Workflow Visualization**: Introduced a comprehensive system for visualizing agent workflows, including
  detailed step information, input/output events, and event flow. This is exposed via the API and rendered in the web
  UI.
- 🦾 **Dynamic Service Discovery**: A new `/suite` API endpoint and associated DTOs allow frontends to dynamically
  discover and display all available services (e.g., Agents, Threads, Tokens) with their localized names, descriptions,
  and icons.
- 🖼️ **Agent Icon Support**: Agents can now define a specific icon in their configuration, which is displayed in the UI
  and discovery endpoints.
- 📄 **New Admin Agent Page**: A dedicated administration page for agents has been added to the web UI, allowing users to
  browse and inspect discovered agents and their workflows.
- ⚙️ **Refined Controller Metadata**: All API controllers now include localized names, descriptions, and icons,
  enhancing discoverability and documentation in the OpenAPI specification.
- 🖥️ **Workflow Visualization Components**: New UI components (`EventEdge`, `StartNode`, `StepNode`, `StopNode`,
  `Visualization`) have been added to render interactive agent workflow graphs in the web application.
- 📝 **`UserMessageEvent` Form Component**: A dedicated component for rendering `UserMessageEvent` forms in the web UI
  has been introduced.
- 👤 **User Settings Component**: A new `UserSettings` component in the web UI provides quick access to user-specific
  options, including logout.
- ⚡️ **Health Service Page**: A basic health service page has been added to the web UI.

### Changed

- 🔄 **Unified Runner Architecture**: The `ApiRunner` and `BotRunner` now inherit from a new abstract `Runner` base
  class, centralizing core application setup and lifecycle management for better consistency.
- 🌐 **Enhanced Locale Handling in API**: Agent and Thread services now consistently pass `LocaleHandler` to DTOs,
  ensuring localized data for agent names, descriptions, and other metadata is correctly returned to clients.
- 🗂️ **Improved Module Organization**: Renamed the `EventPersister` module for better code structure and clarity.
- 🧩 **Updated Agent DTOs**: The `AgentDTO` now utilizes a new `AgentConfigDTO` and incorporates the `network_graph` for
  a more comprehensive representation of agent capabilities.
- 🧑‍💻 **User Data Structure**: The DTO for logged-in users has been renamed from `UserDTO` to `MyUserDTO` for clearer
  distinction and specificity.
- 🎨 **UI Theme Colors**: Adjusted primary colors in the AI Hub theme for a refreshed visual appearance.
- 📊 **UI Agent List**: The agent list in the web UI now dynamically adapts its display (table or data view) based on
  available screen width, and explicitly shows agent icons and conversational status.
- 🚀 **OIDC Authentication Flow**: Improved OIDC silent renewal and error handling in the web application for a more
  robust and seamless authentication experience.
- 📦 **Dependency Updates**: Updated numerous dependencies across `aihub_agent`, `aihub_api`, `aihub_bot`, and
  `aihub_web` for improved performance, security, and stability.

### Fixed

- 🐛 **Robust Authentication Handling**: Improved the `TokenAndOauth2Handler` to be more resilient to non-401 HTTP
  exceptions from individual authentication strategies, ensuring more graceful fallback and user experience.

### Refactor

- 🧹 **Codebase Simplification**: Removed outdated or redundant event and agent type definitions in the web UI,
  streamlining the codebase and relying more heavily on OpenAPI-generated types for consistency.
- 🧹 **Web UI Component Capitalization**: Standardized component naming by changing `thread/Chat.vue` to
  `Thread/Chat.vue` and `thread/ThreadList.vue` to `Thread/ThreadList.vue` for consistency.
- ⚙️ **Decorator Metadata Extraction**: Refactored internal `step` and `precondition` decorators to accurately extract
  output events and step icons from agent methods.

### Removed

- 🗑️ **Deprecated Workflow Visualizer**: Removed the old `NetworkXVisualizer` class, which has been entirely superseded
  by the new, more capable `WorkflowVisualizer`.

---

## [v0.129.0] - 2025-03-28 - Introducing Bounded Loop Workflows and Enhanced Agent Examples

### Added

- ✨ **Introduced `BoundedLoopAgent`:** A new example agent demonstrating a controlled, iterative workflow that loops a
  configurable number of times, showcasing advanced agent design patterns.
- 📄 **Added `BoundedLoopAgentConfig`:** Provides a dedicated configuration class for the `BoundedLoopAgent`, enabling
  easy customization of the loop's maximum iterations.
- ⚙️ **Defined Custom Events for Loop Control:** Introduced `BeginEvent`, `ProcessEvent`, and `DecisionEvent` to
  meticulously manage the state and flow within the `BoundedLoopAgent`'s iterative process.
- 🧪 **Implemented BDD Tests for Bounded Loop Workflow:** Comprehensive behavior-driven development tests were added to
  ensure the precise functioning and iterative behavior of the `BoundedLoopAgent`.
- 🚀 **Provided a `trigger.py` example:** A simple script to easily run and observe the `BoundedLoopAgent` in action,
  aiding in understanding and demonstration.

---

## [v0.128.0] - 2025-03-27 - Improved Embedding Reliability

### Fixed

- 🐛 **Enhanced Embedding Robustness**: Implemented a recursive batch splitting strategy within the embedding process to
  gracefully handle validation errors that might occur during batch embedding generation, improving the reliability of
  vector generation for large inputs.

---

## [v0.127.0] - 2025-03-25 - Enhanced Bot Chat Interactions

### Changed

- ⚡️ **Enhanced Typing Indicators**: Implemented continuous and stoppable typing indicators for agent and OpenAI chat
  bots, providing a more responsive and fluid user experience during bot message processing.

---

## [v0.126.0] - 2025-03-24 - Enhanced LLM Call Reliability

### Added

- ✨ **Configurable LLM Request Timeout:** Introduced a new `timeout` parameter in `ChatLLMConfig`, enabling users to
  specify a maximum duration for chat-based Large Language Model requests, with a default of 30 seconds.
- ⚙️ **Applied Timeout to Chat LLM Implementations:** The newly added timeout configuration is now actively utilized by
  both **Azure OpenAI** and **Self-Hosted LLM** integrations, providing greater control and improved reliability for API
  call durations.

---

## [v0.125.0] - 2025-03-21 - Introducing WebUI Agent and API Modernization

### Added

- ✨ **New WebUI Agent**: Introduced a new `WebuiAgent` enabling seamless integration with OpenAI-compatible Web UI APIs,
  supporting streaming chat responses and configurable features like web search.
- ⚡️ **WebUI Agent Utilities**: Added dedicated utility functions and configuration for the `WebuiAgent` to handle
  Server-Sent Events (SSE) streaming and flexible setup.
- 📚 **WebUI Agent Playground**: Included a new playground example to demonstrate the `WebuiAgent`'s functionality and
  ease of use.
- 📦 **OpenAI Library Dependency**: Incorporated the `openai` library into `aihub_lib` to support new integrations and
  future features.

### Changed

- 🔄 **OpenAI API `chat_id` Handling**: Modified `ChatCompletionRequest` to move the `chat_id` from a top-level field
  into the `metadata` dictionary, aligning with broader API conventions.
- 🚫 **Recursive Agent Exclusion**: Enhanced the `/models` endpoint in the OpenAI API to allow excluding `WebuiAgent`
  types, preventing potential recursive loops during agent discovery.
- 🖼️ **Default Image Model Update**: Updated the default image generation model to DALL-E 3 for improved quality and
  capabilities.
- 🚀 **Azure OpenAI API Version**: Upgraded the Azure OpenAI API version in development environments to
  `2025-01-01-preview` for access to the latest features.
- 📊 **Performance Report Enhancement**: Improved performance test reporting by adding an explicit 'Error' column,
  providing clearer insights into test failures.

### Refactor

- 🧹 **Function Argument Cleaning**: Refactored internal handling of function arguments to filter out `None` values,
  improving robustness and consistency.
- ⚙️ **Internal Model Naming**: Streamlined the derivation of `model_name` within the chat service for better clarity
  and maintainability.
- 📄 **Type Hint Refinement**: Improved type annotations for `asturn_llm_for_cost_reporting` to enhance code clarity and
  correctness.

---

## [v0.124.0] - 2025-03-21 - Core Service Refinements and Enhanced Agent Interactions

### Changed

- 🚀 **Streamlined Agent Event Processing:** Relaxed the validation for external agent events, allowing for more flexible
  event distribution to agents without requiring explicit listing within a thread's agent list, enhancing dynamic agent
  interactions.

### Refactor

- 🧹 **Unified Bot Database Structure:** Standardized MongoDB collection names to `bot_conversations` and `bot_paths` and
  unified the database name to `aihub` for the bot service. This improves database organization and consistency across
  services.

---

## [v0.123.0] - 2025-03-21 - Enhanced Document Processing and Metadata Management

### Added

- ✨ **Introduced `MetadataExtractor` Interface:** Added a new abstract class (`MetadataExtractor`) that allows for
  custom logic to extract and enrich metadata from document splits during processing, enabling more flexible and
  powerful document understanding.
- 🏷️ **Extended Node Metadata:** New metadata fields, **`REFERENCE_NAME`** and **`REFERENCE_URL`**, have been added to
  document nodes, facilitating richer attribution and precise source linking for retrieved content.

### Changed

- 📄 **Improved Markdown Parser Extensibility:** The `MarkdownStructuralNodeParser` now integrates the new
  `MetadataExtractor`, allowing for a pluggable approach to extracting detailed metadata directly during markdown
  content parsing.
- 📊 **Updated Metadata Table Display:** The nodes metadata table now includes the newly introduced `REFERENCE_NAME` and
  `REFERENCE_URL` fields, providing comprehensive insights into document sources and references.

### Refactor

- 🧹 **Module Reorganization for `Split` Class:** The `Split` dataclass, a core component in document parsing, has been
  moved to its own dedicated file for improved modularity and code clarity.
- ⚙️ **Pydantic v2 Migration:** The `MarkdownStructuralNodeParser` has been updated to align with Pydantic v2, enhancing
  type handling and configuration management for improved stability and future compatibility.

---

## [v0.122.0] - 2025-03-21 - Enhanced Error Handling and System Stability

### Added

- ✨ **Introduced Robust Exception Handling:** The system now proactively captures and processes `ExceptionEvent`s
  originating from core services, enhancing error propagation and system stability.
- 🚀 **Improved API Error Reporting:** The Agent API (`aihub_api`) now correctly translates internal `ExceptionEvent`s
  received from agent operations into HTTP 500 errors, providing clearer feedback on operational failures.
- 🛡️ **Enhanced Chat Service Reliability:** The Chat Service (`aihub_lib`) now gracefully terminates ongoing chat
  operations when an `ExceptionEvent` is encountered, preventing stalled processes and ensuring consistent state.

### Changed

- 🔄 **Extended Event Handling Signature:** The `stop_event` mechanism within the Chat Service (`aihub_lib`) has been
  updated to explicitly recognize and store `ExceptionEvent`s, allowing for more comprehensive error state management.

---

## [v0.121.0] - 2025-03-20 - Enhanced Event Causality and Dispatching Reliability

### Changed

- 🔄 **Improved Event Ordering and Filtering**: The system now utilizes JetStream's native sequence numbers instead of
  event creation timestamps for filtering and retrieving events. This change significantly enhances the precision and
  reliability of event causality, ensuring steps are triggered based on the exact sequence of events in the workflow.

### Refactor

- ⚙️ **Core Event Store Logic Update**: The internal logic within the `Dispatcher`, `JetStreamEventStore`, and
  `RunEventStore` has been updated to fully leverage JetStream sequence numbers for all event-related operations. This
  provides a more robust and accurate foundation for event processing.
- 📚 **Event Metadata Enrichment**: All base events now automatically store their corresponding JetStream sequence number
  upon reception, providing a foundational improvement for strictly ordered event processing and dependency resolution
  within the agent framework.

---

## [v0.120.0] - 2025-03-20 - Introducing Language Detection for Enhanced Processing

### Added

- ✨ **Introduced Language Detection**: A new utility has been added to automatically detect the language (German,
  English, French, Italian, or other) of user queries using an LLM, enabling more language-aware processing
  capabilities.

### Refactor

- 🧹 **Streamlined IDE Module Configuration**: Optimized internal `.idea` project files to improve module referencing and
  overall development environment setup.

---

## [v0.119.0] - 2025-03-19 - API Routing Improvements

### Changed

- 🔄 **Enhanced dynamic route naming for agent event controllers** to incorporate a route postfix, which improves the
  uniqueness and clarity of dynamically generated API endpoints.

---

## [v0.118.0] - 2025-03-19 - Improved Event Handling and Core Updates

### Added

- ✨ **Enhanced Event Serialization:** Introduced a new `model_dump_json` method within `BaseEvent` to provide robust
  serialization of event data to JSON strings, ensuring all data, including previously unknown fields, is fully
  preserved.

### Changed

- 🧹 **Refined Event Method Overrides:** Added the `@override` decorator to the `model_dump` method in `BaseEvent` for
  improved code clarity and maintainability.

---

## [v0.117.0] - 2025-03-19 - Empowering Custom Workflow Control

### Added

- ✨ **Custom Start and Stop Event Support**: Introduced the ability to define and utilize custom `StartEvent` and
  `StopEvent` types, enabling more tailored and application-specific workflow initiation and termination for agents.
- 🚀 **New Playground Example for Custom Events**: Added a comprehensive playground example (`CustomStartStopEventAgent`)
  that demonstrates how to implement and integrate custom start and stop events into agent workflows, providing a
  practical guide for developers.
- 🧪 **Dedicated Tests for Custom Workflows**: Included new BDD tests to validate the functionality of custom start and
  stop events, ensuring reliability and providing a robust example for extending agent capabilities.

---

## [v0.116.0] - 2025-03-19 - Enhanced Chat Control and Event Visibility

### Added

- ✨ **Enhanced Chat Interaction Control:** Introduced a new `subscribe_to_thread` parameter in chat services, allowing
  users to choose between subscribing to events only from specific agents or all events within a thread for
  comprehensive visibility.

### Changed

- 🔄 **Broadened Default Chat Visibility:** Streaming and JSON chat interactions now default to subscribing to all events
  within a thread, providing a more complete view of multi-agent conversations without explicit configuration.
- 🚀 **Contextualized JSON Event Interactions:** The `start_json_event_interaction` API now explicitly receives
  `agent_class` and `agent_id`, allowing for more contextual and precise handling of JSON-based conversations.
- ⚡️ **Refined Interaction Termination Logic:** Chat interactions now precisely terminate only when the *primary* agent
  sends a stop event, preventing premature endings in complex multi-agent scenarios where multiple agents might be
  active.
- 🏷️ **Dynamic Model Naming for JSON Interactions:** The reported model name for JSON interactions now dynamically
  reflects the specific `agent_class/agent_id`, providing clearer identification in logs and metrics.
- 📄 **Improved Human-in-the-Loop Event Handling:** Enhanced the deserialization of Human-in-the-Loop request events for
  increased robustness and accuracy in handling user interventions.

### Fixed

- 🐛 **Corrected `display_id` for Human-in-the-Loop:** Ensured that `display_id` for Human-in-the-Loop (HITL) response
  events correctly reuses the `display_id` from the original HITL request, maintaining conversation context.

### Refactor

- 🧹 **Streamlined NATS Event Imports:** Cleaned up and reorganized NATS event-related imports in
  `ExternalEventDistributor` and `OpenaiService` for improved code clarity and maintainability.

---

## [v0.115.0] - 2025-03-19 - Enhanced Event Distribution

### Refactor

- 🔄 **Unified External Event Handling:** The core mechanism for processing incoming user events has been significantly
  refactored. The `WebSocketReceiver` component and `WSUserEvent` have been renamed to `ExternalEventDistributor` and
  `ExternalEvent`, respectively. This change broadens the system's capability to handle user events originating from
  diverse external sources, including APIs, bot frameworks, and WebSockets, moving beyond a WebSocket-specific focus.
- 🧹 **Reorganized Event Distribution Modules:** Related modules and dependencies for external event distribution have
  been moved from the legacy `sockets` package into a new, more logically structured `nats/distributor` pathway. This
  improves the architectural clarity and modularity of the event handling system.
- 🦾 **Updated API and Bot Integrations:** All API endpoints and bot services responsible for receiving and processing
  user input have been updated to seamlessly integrate with the new `ExternalEventDistributor`, ensuring consistent and
  channel-agnostic event flow across the platform.

---

## [v0.114.0] - 2025-03-19 - Enhanced Event Robustness and API Output Control

### Added

- 🛡️ **Robust Event Deserialization**: Introduced a new mechanism for deserializing NATS events that allows a receiving
  application to process events even if their exact class is not locally registered. This enhances forward compatibility
  and inter-service communication by intelligently falling back to the most specific known parent class and preserving
  unknown data.
- ⚙️ **Event Utility Functions**: Added `get_inheritance_depth` and `get_parent_classes_until_base` to precisely
  determine event hierarchies, critical for the new robust deserialization logic.
- 📤 **Dynamic API Output Model Generation**: Implemented `create_output_model` to dynamically generate Pydantic models
  for API responses, ensuring cleaner and more controlled exposure of event data by filtering internal metadata.

### Changed

- 🔄 **Standardized Event Type Checking**: Refactored all event type checks across the codebase from
  `isinstance(event, EventType)` to explicit `event.is_event_type` properties (e.g., `event.is_start_event`,
  `event.is_control_event`) on `BaseEvent`. This improves code readability and leverages the new robust deserialization.
- 📄 **API Event Response Refinement**: API endpoints now utilize the new output model generation to present a more
  focused and cleaner representation of event data in responses.
- 🛠️ **Pydantic Model Configuration**: Updated `BaseEvent` Pydantic configuration to allow extra fields, supporting the
  new robust deserialization of unknown event types without validation errors.

### Refactor

- 🧹 **Internal Event Type Handling**: Consolidated and improved the internal handling of event types across dispatchers,
  tracing coordinators, and publishers to align with the new property-based type checking.

---

## [v0.113.0] - 2025-03-17 - Enhanced Event Persistence and Querying

### Added

- ✨ **Event Inheritance Tracking**: Introduced a new `_parent_class_names` computed field in `BaseEvent` to
  automatically capture the inheritance hierarchy of each event, providing deeper introspection capabilities.
- 📄 **Persisted Event Parentage**: Added an `event_parents` field to `PersistedEventEntity` to store the inheritance
  chain of events, enabling more flexible and robust querying based on event types.

### Changed

- 🚀 **Robust Event Querying**: Updated event retrieval methods in `PersistedEventEntity` to leverage the new
  `event_parents` field, allowing queries to filter events based on their entire class hierarchy, leading to more
  resilient and accurate results.
- ⚙️ **Simplified Local API Development**: The `aihub_api` playground environment now defaults to using `NoAuthHandler`,
  simplifying local development and testing by removing authentication requirements.

### Refactor

- 🧹 **Streamlined Event Persistence**: The core logic for persisting events has been moved from `EventPersister` to a
  new class method `PersistedEventEntity.persist_event`, centralizing persistence responsibilities within the entity
  itself.

---

## [v0.112.0] - 2025-03-17 - Deeper Conversations: Human-in-the-Loop and Extended API Capabilities

### Added

- ✨ **Introduced Human-in-the-Loop (HITL) Capabilities**: Seamlessly integrate human intervention into AI conversations,
  allowing for pauses to gather user input and resume interactions with the provided response.
- 💬 **Expanded OpenAI Chat Completion Parameters**: Added support for a comprehensive set of OpenAI Chat Completion
  request parameters, including `chat_id`, `user`, `audio`, `frequency_penalty`, `function_call`, `functions`,
  `logit_bias`, `logprobs`, `max_completion_tokens`, `max_tokens`, `metadata`, `modalities`, `n`, `parallel_tool_calls`,
  `prediction`, `presence_penalty`, `reasoning_effort`, `response_format`, `seed`, `service_tier`, `stop`, `store`,
  `stream_options`, `temperature`, `tool_choice`, `tools`, `top_logprobs`, and `top_p`.
- 🖼️ **Extended OpenAI Image Generation Parameters**: Enabled additional options for image generation requests,
  including `n`, `quality`, `response_format`, `size`, and `style`.
- 🏷️ **Explicit Thread ID Assignment**: Added the ability to assign explicit thread IDs when creating new conversation
  threads, allowing for more precise control over conversation history and state.
- 📈 **New Human-in-the-Loop Event Retrieval**: Introduced dedicated methods to retrieve specific Human-in-the-Loop
  request and response events from persisted history.

### Changed

- 🔄 **Refined Chat Conversation Management**: Updated the core chat service logic to better handle conversation threads,
  supporting the continuation of existing chats and more robust linking of bot interactions to specific threads.
- 👤 **Improved User Context in Chat Completions**: Automatically populates the `user` field in OpenAI chat completion
  requests, enhancing user traceability and context within conversations.
- 📊 **Enhanced Message History Reconstruction**: Modified the process for building message history to accurately include
  and display Human-in-the-Loop interactions, providing a more complete conversation log.
- ⚡️ **Streamlined OpenAI API Request Arguments**: Optimized the handling of chat completion arguments by removing
  redundant `chat_id` from core function arguments before passing to the OpenAI client.
- 🗣️ **Unified Content Building for Responses**: Updated response content building to integrate potential
  Human-in-the-Loop questions into the final output when a stop event is triggered by an HITL request.

### Fixed

- ⏱️ **Corrected Chronological Ordering of Display Events**: Ensured all persisted display events, including chat
  messages and Human-in-the-Loop requests, are retrieved and ordered chronologically for accurate conversation playback.

---

## [v0.111.0] - 2025-03-17 - Optimized NATS Message Routing for Display Events

### Changed

- ⚡️ **WebSocketReceiver** now leverages both NATS core and JetStream publishers, routing display events through NATS
  core for enhanced real-time performance and reduced latency.
- 🔄 Updated **API** and **Bot** services to align with the new **WebSocketReceiver** architecture, passing the NATS
  client instance during initialization.

---

## [v0.110.0] - 2025-03-14 - Improved Bot Message Handling with Dedicated Content Extraction

### Added

- 🚀 **Unified Message Content Handling:** Introduced a new **`ContentExtractor`** module that centralizes and
  standardizes the processing of diverse incoming message content, including text, images, and various file types from
  platforms like Slack and Microsoft Teams.
- 🖼️ **Enhanced File and Image Attachment Support:** The bot can now more reliably process and normalize attached files
  and images, converting images to base64 data URLs and handling text files to ensure seamless integration into
  conversations.
- 📄 **Standardized File Information Model:** Implemented a **`FileInfo`** model to provide a consistent representation
  of file details across different communication channels, improving the robustness of content ingestion.

### Refactor

- 🧹 **Refactored Bot Content Processing:** Extracted all message content extraction logic from the main `Service` module
  into a dedicated `ContentExtractor` class, significantly improving code modularity, readability, and maintainability
  within the bot service.

---

## [v0.109.0] - 2025-03-14 - Enhanced Chat Bot Interactions and Attachment Processing

### Fixed

- 🐛 **Resolved MS Teams Conversation Context Issues:** Implemented logic to automatically clear previous conversation
  context for bots in Microsoft Teams when the bot is added to a new or existing chat, ensuring a fresh start and
  preventing stale interactions.

### Changed

- 🖼️ **Improved Image Attachment Handling:** Switched to fetching and base64 encoding image attachments from Slack and
  Microsoft Teams. This enhancement ensures images are consistently processed as data URLs, improving compatibility and
  reliability for multimodal model interactions.

### Refactor

- 🧹 **Streamlined Attachment Processing:** Introduced a new internal utility method `_fetch_and_encode_to_base64` to
  centralize and simplify the fetching and encoding of file attachments, leading to cleaner and more maintainable code
  for handling various file types.

---

## [v0.108.0] - 2025-03-13 - Asynchronous Preconditions for Flexible Workflow Control

### Changed

- ⚡️ **Enhanced Workflow Preconditions**: Step precondition functions (`precondition` argument in `@step` decorator) can
  now be asynchronous (`async def`). This allows for more dynamic and non-blocking checks before a workflow step
  executes, such as waiting for external events or performing asynchronous data lookups.
- 🔄 **Updated Dispatcher Logic**: The internal dispatcher has been updated to correctly handle and await asynchronous
  precondition functions, ensuring seamless integration and execution of the new capability.

---

## [v0.107.0] - 2025-03-13 - API Enhancements and Internal Utilities

### Added

- ✨ **Introduced `clear_cache` method for `AgentService`:** A new static method has been added to allow clearing
  in-memory caches used for agent discovery, primarily beneficial for testing purposes to ensure fresh discovery
  requests.

---

## [v0.106.0] - 2025-03-11 - Core Event System Refinements

### Refactor

- 🔄 **Promoted `LLMStopEvent` to Core Library**: The `LLMStopEvent` has been moved from the `playground` experimental
  area into the central `aihub_lib.nats.events` module, making it a fully integrated and accessible part of the core
  event system.
- 🧹 **Formalized `GuardRejectionEvent` Exposure**: The `GuardRejectionEvent` is now directly exposed and importable from
  `aihub_lib.nats.events`, improving consistency and ease of use for guard-related event handling.
- ⚡️ **Streamlined Event Imports**: Optimized internal import paths within `aihub_lib.nats.events` to centralize and
  simplify how various event types are accessed throughout the codebase.

### Removed

- 🗑️ **Deprecated Playground Event Files**: The `LLMStopEvent` file and its associated `__init__.py` have been removed
  from the `playground` directory, reflecting its migration to the core `aihub_lib`.

---

## [v0.105.0] - 2025-03-11 - Core Component Version Alignment and Documentation Refinement

### Changed

- 🔄 **Component Version Synchronization**: All core components, including **aihub_agent**, **aihub_api**, **aihub_bot**,
  **aihub_lib**, and **aihub_pipeline**, have been updated and synchronized to version `v0.105.0`.
- 📄 **Documentation Formatting**: Minor cosmetic adjustments were made to the Mermaid flowchart syntax within the
  introduction documentation for improved clarity.

---

## [v0.104.0] - 2025-03-10 - Enhanced Bot Attachment Handling and Slack Integration

### Added

- ✨ **Introduced Slack File Attachment Support:** Bots can now process image and text file attachments from Slack
  messages by utilizing a configured Slack OAuth token, significantly enhancing conversational capabilities with files.
- 🚀 **Enabled Microsoft Teams File Attachment Handling:** The bot now intelligently processes file attachments
  (including images and text files) from Microsoft Teams conversations, ensuring richer interactions.
- 🔑 **Added Slack Token Configuration:** A new `slack_token` field has been introduced to the bot's path-specific
  configuration, allowing for persistent and secure storage of Slack OAuth tokens.
- ⚙️ **New CLI Option for Slack Token Setup:** The `setup_azure_bot.py` script now includes a `--slack-token` option,
  simplifying the configuration of Slack OAuth tokens during bot deployment.

### Changed

- 🔄 **Refactored Conversation Message Handling:** The `path` parameter is now consistently passed to methods responsible
  for adding user and bot messages to conversations, enabling more granular and path-specific message processing and
  credential retrieval.
- 🧹 **Improved Attachment Processing Robustness:** The bot's attachment handling has been enhanced to provide clearer
  logging and error handling for various attachment types, including explicitly ignoring redundant HTML attachments from
  Teams and warning about unsupported file types.

---

## [v0.103.0] - 2025-03-10 - Streamlined Agent Interactions: API Endpoints and Event System Enhancements

### Added

- 🚀 **New Agent Interaction API:** Introduced a new API endpoint (`POST /agent/{agent_class}/{agent_id}/send_event`)
  that allows external systems to directly initiate conversations with specific agents by sending a `StartEvent` and
  receiving a corresponding `StopEvent`.
- ⚙️ **Dynamic Input Model Generation:** Added a utility (`create_input_model`) to dynamically create Pydantic input
  models for API endpoints, automatically excluding generated event fields (like IDs and timestamps) for cleaner API
  usage.

### Changed

- 🔄 **Refined LLM Stop Event Handling:** The `LLMWrappingAgent` now utilizes a more specific **`LLMStopEvent`** to
  signal the completion of LLM interactions, providing richer context than the generic `StopEvent`.
- 💬 **Expanded WebSocket Event Support:** The WebSocket receiver now supports **`StartEvent`** payloads within
  `WSUserEvent`, enabling more diverse interaction initiation patterns from the client side for agent interactions.
- ⚡️ **Improved Event Signal Management:** Internal **`ChatService`** logic was updated to clearly distinguish between
  an asynchronous stop signal (`stop_signal`) and the final received stop event object (`stop_event`), enhancing clarity
  and control over event streams.

### Refactor

- 🧹 **Event Stop Signal Renaming:** Renamed internal `_stop_event` variables to `_stop_signal` across agent runners and
  performance tests for improved clarity and consistency in signaling asynchronous task completion.
- 📦 **Centralized LLMStopEvent:** Moved the **`LLMStopEvent`** definition from agent-specific folders to the `aihub_lib`
  package under a new `semantic/llm` namespace, centralizing event definitions and improving modularity.

---

## [v0.102.0] - 2025-03-07 - Enhanced Document Metadata Handling

### Fixed

- 🐛 **RefDocDocument**: Improved robustness of metadata property access (e.g., `namespace`, `hash`, `uri`, `updated`) by
  transitioning from direct dictionary access to using `.get()` methods with default fallback values, preventing
  potential `KeyError` exceptions for missing metadata.

### Changed

- ⚡️ **RefDocDocument**: Enhanced the **metadata enrichment process** from `DataLakeFile` objects to intelligently
  prioritize existing metadata fields and gracefully fall back to default attributes when populating document properties
  like `namespace`, `hash`, `updated`, `source`, and `document title`.

---

## [v0.101.0] - 2025-03-07 - Next-Gen Event Persistence and Workflow Control

### Added

- ✨ **Introduced JetStream Event Store:** Replaced the Redis-based event storage with a robust NATS JetStream
  implementation, enabling durable, consistent, and replayable control event persistence for workflows. This
  significantly improves data reliability and recovery.
- 🚦 **New Workflow Precondition Decorator (`@precondition`):** Allows agents to define complex, data-driven
  preconditions for workflow steps, ensuring steps only execute when all necessary criteria are met. This enables more
  sophisticated and reliable workflow orchestration.
- 🚀 **Comprehensive Performance Testing Framework:** Added a dedicated playground and tools for benchmarking agent event
  processing, including raw NATS JetStream performance and full system throughput, providing crucial insights for
  scalability and optimization.
- 📁 **Dedicated NATS Server Configuration:** Included a `nats.conf` file for more controlled and robust NATS server
  deployments within Docker environments.
- 📊 **New Redis List and Counter Utilities:** Added helper methods for appending to Redis lists and atomically
  incrementing counters, improving data management within agent state.

### Changed

- 🔄 **Refined NATS Eventing Strategy:** Separated event publishing and subscribing into distinct NATS Core (for
  display/ephemeral events) and JetStream (for durable control events) channels, optimizing performance and reliability
  based on event criticality.
- 💾 **Enhanced JetStream Stream Durability:** Configured JetStream streams to use file storage instead of memory,
  significantly increasing message retention and persistence.
- ⚙️ **Optimized JetStream Stream Parameters:** Increased maximum messages capacity and reduced the duplicate window for
  JetStream streams, improving overall stream management.
- 🧹 **Improved Agent Step Discovery Performance:** Applied caching to agent methods responsible for discovering workflow
  steps and events, reducing overhead and speeding up agent initialization.
- ⚡️ **Optimized Step Execution Counting:** Transitioned step execution counting in the `StepStore` to use Redis atomic
  increment operations, boosting efficiency and accuracy.
- 🔑 **More Robust Event Parameter Keying:** Implemented MD5 hashing for event parameter keys in the `StepStore`,
  ensuring more unique and reliable identification of step calls with specific event sets.
- 🔗 **Updated Docker Compose NATS Configuration:** Modernized NATS setup in Docker Compose files, utilizing a dedicated
  configuration file for better control and health checks.

### Removed

- 🗑️ **Deprecated Redis Event Store:** The `DistributedEventStore` (Redis-based) has been removed, replaced entirely by
  the new JetStream-based event persistence.

### Fixed

- 🐛 **Graceful Shutdown for Multiprocess Agents:** Improved signal handling (`SIGTERM`, `SIGINT`) in
  `MultiprocessAgentRunner` to ensure a more robust and graceful shutdown of agent processes.
- 🐞 **Robust NATS Unsubscription:** Enhanced `NCSubscriber` to gracefully handle `ConnectionDrainingError` during
  unsubscription, preventing potential errors during NATS client shutdown.
- 🛠️ **Consistent Resource Cleanup:** Ensured all dispatcher and subscriber resources are properly stopped and cleaned
  up during agent shutdown for better stability.

---

## [v0.100.0] - 2025-03-07 - Enhanced Bot Setup and Structural Refinements

### Added

- ✨ **System Message Configuration for Azure Bots:** Introduced the capability to define and store a default
  `system_message` during Azure bot setup, enabling better initial bot personality or instructional guidance. This
  message is now saved to the connected MongoDB or Cosmos DB instance.

### Refactor

- 🧹 **Relocated Azure Bot Setup Script:** The `setup_azure_bot.py` script has been moved into its own dedicated
  subdirectory (`aihub_bot/aihub_bot/`), improving the overall organization and clarity of the bot module.

---

## [v0.99.0] - 2025-03-07 - Enhanced Chat Context and Resilience

### Added

- ✨ **Enabled OpenAI Message Naming:** Implemented support for passing a `name` field with chat messages to OpenAI,
  allowing the model to distinguish between different participants (e.g., specific users or tools) in a conversation.
  Names are automatically cleaned to meet API requirements.

### Changed

- 📝 **Standardized Message Naming:** Messages now consistently include the sender's `name` property (user, bot, system)
  in the conversation history to improve context for advanced AI features.
- 📄 **Enriched System Messages:** System messages can now dynamically include the assistant's name using a new
  `{assistant_name}` placeholder, enabling more personalized interactions.
- 🤖 **Agent Message Refinements:** Ensured agent chat messages properly include the sender's `name` for better context
  in multi-agent or tool-using scenarios, aligning with the new message structure.

### Fixed

- 🐛 **Improved OpenAI Error Handling:** Gracefully handles `BadRequestError` responses from OpenAI API calls, sending
  the detailed error message back to the user instead of failing silently.

---

## [v0.98.0] - 2025-03-06 - Next-Gen Chat: Multimodal Support and Enhanced Slack Integration

### Added

- ✨ **Multimodal Message Support**: Introduced the ability for the bot to process and respond to messages containing
  various content types, including plain text, image URLs, and content from attached text files, enabling richer and
  more versatile conversations.
- 💬 **`Content` Data Model**: A new `Content` embedded document was added to the conversation message structure,
  allowing messages to store multiple content blocks with distinct types (e.g., `text`, `image_url`).
- 🚀 **Slack Direct Message Detection**: Implemented new logic to accurately distinguish between direct messages and
  channel messages in Slack, improving the bot's contextual awareness for responses.
- 📌 **Conversation Mention Tracking**: Introduced an `is_mentioned` flag within conversation entities to track whether
  the bot has been explicitly mentioned in a Slack channel, enabling more intelligent and targeted responses.

### Changed

- 🔄 **Standardized Slack Message Handling**: Refactored the core Slack message processing logic across all bot types
  into a unified service method (`handle_slack_message`), which now orchestrates the handling of direct messages,
  channel mentions, and continued conversations.
- 📄 **Core Message Structure**: Updated the internal `Message` entity to support a list of `Content` objects, replacing
  the previous single string content field, which is foundational for multimodal input capabilities.
- 🗣️ **LLM Integration for Multimodal Input**: Modified the integration layers for both Agent and OpenAI bots to
  correctly parse and pass multimodal content (text and images) from user messages to the underlying Large Language
  Model services.

### Refactor

- 🧹 **Centralized Slack Logic**: Consolidated various Slack-specific checks and message preparation steps into a single,
  comprehensive `handle_slack_message` function, enhancing code clarity and maintainability.
- ⚙️ **Internal Helper Renames**: Renamed several internal message conversion helper methods to follow private naming
  conventions (e.g., `message_to_chat_message` to `_message_to_chat_message`), improving encapsulation.

---

## [v0.97.0] - 2025-03-06 - LLM Configuration Enhancements

### Added

- ✨ **Enhanced LLM System Prompt Control:** The `cost_reporting_llm` context manager in `ChatLLMConfig` now supports an
  optional `system_prompt` parameter, allowing for direct configuration of system messages for Large Language Models
  within cost-tracked sessions.

---

## [v0.96.0] - 2025-03-06 - Enhanced Bot Message Handling

### Fixed

- 🐛 **Improved Bot Message Sending:** The bot service now gracefully handles empty message buffers, preventing
  unnecessary activity updates and enhancing the reliability of message delivery.

---

## [v0.95.0] - 2025-03-06 - Improved Chatbot Interactions and Streamlined Environment Setup

### Added

- 📄 **Standardized Testing Environment Configurations**: Introduced new `.env` files for testing environments, ensuring
  consistent setup alongside development.

### Changed

- 💬 **Enhanced Chatbot User Feedback**: Implemented "typing" indicators for all chatbot types (Agent, Stream Agent,
  OpenAI, and Stream OpenAI), providing real-time feedback during response generation.
- ⚙️ **Refined Development Environment Variables**: Updated the structure of development `.env` files to directly use
  `AZURE_SUBSCRIPTION_ID` for more explicit Azure resource identification.

### Refactor

- 🧹 **Optimized Chat Service Message Sending**: Inlined the text sending logic within the `send_response_stream` method,
  improving the internal organization and maintainability of the chat service.

---

## [v0.94.0] - 2025-03-05 - Enhanced Bot Streaming and Configuration Flexibility

### Changed

- ✨ **Improved Bot Streaming Response Handling**: Enhanced the bot's ability to send long streaming responses by
  introducing a more robust chunking and update mechanism, including graceful handling for messages that exceed length
  limits to ensure continuous user experience.
- 🔧 **Flexible Azure App Naming**: The `APP_NAME` configuration for Azure deployments now supports hyphens, providing
  greater flexibility for naming conventions.

### Fixed

- 🐛 **Agent Stream Timeout Robustness**: Resolved an issue where agent streaming responses could lead to indefinite
  waits by implementing a timeout mechanism with graceful handling for stream termination, improving overall stability.

---

## [v0.93.0] - 2025-03-05 - Core Component Version Alignment

### Changed

- 🔄 **Component Version Synchronization**: Updated the project version and internal `aihub_lib` dependency tags across
  all `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline` components to `v0.93.0` to ensure full
  system compatibility and release alignment.

---

## [v0.92.0] - 2025-03-05 - Intelligent Context Handling for RAG Agents

### Added

- 🦾 **Introduced Context Sufficiency Guard:** A new `context_sufficient_guard` has been implemented to assess whether
  the retrieved context is adequate for answering a user's query within RAG agents. This enhances response quality by
  identifying and managing cases where context is insufficient.
- ⚙️ **Configurable Context Sufficiency Check:** Added a new `check_context_sufficiency` option to the `RAGAgentConfig`,
  allowing users to enable or disable the context sufficiency guard based on their requirements.
- 💬 **New Context State Events:** Introduced `ContextSufficientEvent` and `ContextInsufficientEvent` to clearly signal
  the outcome of the context sufficiency check within the agent's workflow.
- 🌐 **Internationalized Context Guard Prompts:** Added multi-language support (German, English, French, Italian) for the
  new context sufficiency guard's prompts, improving global accessibility.
- 🚀 **Agent-in-the-Loop Event Categories:** New event categories have been introduced under
  `aihub_lib/aihub_lib/nats/events/agent_in_the_loop` for managing exceptions, requests, and responses related to
  agent-in-the-loop functionality, laying groundwork for advanced human-in-the-loop workflows.

### Changed

- 🔄 **Improved RAG Agent Fallback Behavior:** The `RAGAgent` now gracefully handles scenarios where the retrieved
  context is deemed insufficient by providing a fallback response, ensuring a more robust user experience.
- ✨ **Streamlined Few-Shot Guard Acceptance:** Simplified the `FewShotAcceptEvent` creation in the
  `few_shot_guard_step`, removing redundant `success=True` parameter as it is implied by the event type.

---

## [v0.91.0] - 2025-03-05 - Parallel Agents, GPU Support, and Enhanced Observability

### Added

- 🚀 **Multiprocess Agent Runner:** Introduced a new `MultiprocessAgentRunner` to enable horizontal scaling and true
  parallelism for agents by running multiple instances across separate processes.
- ⚡️ **GPU-Accelerated Local Development:** Added `docker-compose-gpu.yml` to facilitate local development and testing
  with GPU-enabled infrastructure, including local LLM and embedding models.
- ⚙️ **Developer Convenience Configurations:** Included new PyCharm run configurations to simplify the setup and
  execution of tests and core components (API, Agent, Bots, Lib) for an improved developer experience.

### Changed

- 🔄 **Event Store Caching Improvement:** Refined the `DistributedEventStore` to directly cache and retrieve deserialized
  `ControlEvent` objects, enhancing type safety and internal consistency.
- 📈 **Enhanced Logging Format:** Updated the default logging formatter to include timestamps with milliseconds,
  providing more precise temporal context for debugging and monitoring.
- 📊 **Tracing Span Management:** Adjusted the tracing logic for successful agent steps, allowing for more flexible span
  management and potentially richer trace data capture.

### Fixed

- 🐛 **Semantic Event Serialization:** Corrected an issue where optional attributes in semantic tracing events were not
  properly omitted if `None`, and ensured `LLM_INVOCATION_PARAMETERS` are correctly serialized to JSON.
- 🪄 **Bot Module Import:** Fixed a minor import path for `OpenaiChatController` in the `aihub_bot` playground.

### Removed

- 🗑️ **Deprecated Docker Compose File:** Removed the non-functional `docker-compose-open-webui.yml`, cleaning up the
  project structure.

---

## [v0.90.0] - 2025-03-04 - Improved Observability and Code Structure

### Added

- ⚙️ **Configurable Logging Levels:** Introduced `LoggingConfig` in `aihub_lib` to allow setting log levels dynamically
  via environment variables, enhancing debugging and operational control.
- ⚡️ **Automatic Playground Logging:** Enabled `enable_logging()` by default in `aihub_api` and `aihub_bot` playground
  environments, providing immediate visibility into test and development flows.

### Changed

- 🚀 **Optimized Trace Export:** Switched OpenTelemetry trace export from `SimpleSpanProcessor` to `BatchSpanProcessor`
  in `aihub_agent`, significantly improving trace reliability and performance by batching exports.
- 📈 **Enhanced Logging Configuration:** The `enable_logging` function now supports an additional `lib_level` argument
  and respects environment variable overrides for log levels, offering more granular control over library logging.

### Refactor

- 🧹 **API Import Cleanup:** Removed numerous unused imports across various `aihub_api` controllers and DTOs, reducing
  clutter and improving code readability.
- 🧪 **Test Suite Clarity:** Renamed test functions in `FewShotAgent` and `AgentInTheLoopAgent` playgrounds for improved
  clarity and maintainability of test scenarios.
- 🔄 **Standardized OpenAI URLs:** Centralized OpenAI base URLs in `aihub_api` playground configuration for easier
  management and consistency.
- 📄 **Simplified NATS Event Imports:** Refactored the import structure for `AgentInTheLoop` events within
  `aihub_lib.nats.events` to streamline access and reduce nesting.

### Removed

- 🗑️ **Redundant NATS Event Modules:** Deleted empty `__init__.py` files previously used for re-exporting
  `AgentInTheLoop` events, simplifying the module structure.

---

## [v0.89.0] - 2025-03-03 - Enhanced Agent Dispatching with Idempotency

### Added

- ✨ **Introduced Idempotent Agent Step Execution:** Agent steps now include a robust mechanism to prevent duplicate
  executions within the same run when called with identical input events. This significantly enhances the reliability
  and efficiency of agent dispatching by avoiding redundant processing.

---

## [v0.88.0] - 2025-03-03 - Streamlined Communication and Resource Management

### Changed

- 🚀 **Improved NATS JetStream Configuration:** Enhanced the NATS JetStream client setup in `AgentRunner` with a
  60-second timeout and increased `publish_async_max_pending` to 10,000 messages, boosting communication robustness for
  event publishing.
- ⚡️ **Enhanced NATS Publishing Reliability:** Implemented a robust retry mechanism with timeouts and message
  deduplication (using `Nats-Msg-Id` headers) for all NATS JetStream publications, significantly improving the
  reliability of event delivery.
- ⚙️ **Optimized NATS Stream Management:** Configured NATS streams to use `MEMORY` storage instead of `FILE` for
  improved performance. New policies for message limits (`1,000,000`), discarding old messages, a 30-day message age
  limit, and a 1-hour duplicate window were also introduced, optimizing resource usage and data retention.
- 🐳 **Updated NATS Docker Image:** Switched the NATS service in `docker-compose.yml` from `nats:latest` to the more
  lightweight `nats:alpine` image, reducing resource consumption for local deployments.

### Refactor

- 🧹 **Standardized Pre-Commit Hook Order:** Reordered the `pr-ready` Makefile target across all core services
  (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_pipeline`) to consistently run formatting before
  linting, streamlining development workflows.

---

## [v0.87.0] - 2025-03-03 - Infrastructure Upgrade: Redis for Distributed State & Workflow Optimizations

### Added

- ✨ **Redis for Distributed State**: Integrated Redis as the primary backend for distributed event and step storage
  across agents, significantly enhancing performance, scalability, and simplifying state management.
- ⚙️ **Redis Configuration**: Introduced a new `RedisConfig` class within `aihub_lib` for streamlined management of
  Redis connection settings.
- 💾 **Redis Docker Service**: Added a dedicated Redis service to the `docker-compose.yml` for easier local development
  and testing environment setup.
- 🚀 **Telemetry Header Caching**: Implemented a `TTLCache` in the `Dispatcher` to cache telemetry headers, optimizing
  performance by reducing redundant data fetches during step execution.

### Changed

- 🛠️ **CI/CD Linting Step**: Incorporated a `lint` command into the `pr-ready` Makefile targets for all microservices,
  reinforcing code quality standards prior to pull requests.
- 📈 **NATS Stream Durability**: Switched NATS stream storage from in-memory (`MEMORY`) to file-based (`FILE`), improving
  data durability and persistence for event streams.
- 🐳 **NATS Docker Image Update**: Updated the NATS Docker image to `nats:latest` and enabled verbose/debug logging
  (`-D`, `-V`) for better operational insights.

### Refactor

- 🧹 **Unified State Management Logic**: Reworked core components including `StoreBase`, `DistributedEventStore`,
  `StepStore`, and various `Context` classes (`BaseContext`, `RunContext`, `ThreadContext`) to unify their distributed
  state management under Redis, simplifying the overall architecture.
- 🧰 **Optimized Step Readiness Check**: Enhanced the `Dispatcher`'s step readiness logic to precisely retrieve only the
  necessary input events for step execution, leading to more efficient data fetching.
- 🔄 **Streamlined Agent Event Imports**: Cleaned up various agent files by removing explicit `StartEvent` imports where
  not directly consumed, reflecting a more consolidated approach to initial event handling within the agent framework.

---

## [v0.86.0] - 2025-03-03 - Streamlined Bot Services

### Refactor

- 🧹 **Refined Bot System Message Retrieval:** Removed redundant calls to `get_system_message` from `StreamAgentChatBot`,
  `OpenaiChatBot`, and `StreamOpenaiChatBot` to centralize and simplify how system messages are handled within bot
  services.

---

## [v0.85.0] - 2025-02-28 - Core Component Alignment and API Refinements

### Changed

- 🔄 **Updated Core Component Versions**: Synchronized the versions of `aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_lib`, and `aihub_pipeline` to `v0.85.0` for consistent deployment and development.
- 📄 **Enhanced Document Intelligence Loader**: Adapted the **Document Intelligence Loader** to align with the latest API
  specifications by updating the parameter name from `analyze_request` to `body` for improved compatibility.

---

## [v0.84.0] - 2025-02-28 - Minor Refinements and Event Stream Optimization

### Removed

- 🗑️ **Removed `LimitChatHistoryWithContextEvent`:** The event previously used for explicitly limiting chat messages and
  context within the `FewShotAgent` has been removed.

---

## [v0.83.0] - 2025-02-27 - Core Performance and Stability Improvements

### Changed

- ⚡️ **Optimized NATS JetStream Storage:** Switched the default storage type for all NATS JetStream Key-Value stores
  (including run and thread contexts) and general streams from file-based (`FILE`) to in-memory (`MEMORY`). This change
  significantly enhances performance and responsiveness of context and stream operations.
- ⚙️ **Enhanced KV Store Creation Robustness:** Improved the error handling for Key-Value store creation, ensuring that
  the system more gracefully attempts to retrieve an existing store if creation fails, leading to increased stability.

---

## [v0.82.0] - 2025-02-27 - Core Optimizations and Logic Refinements

### Added

- ✨ Implemented **caching for event store lookups** within the `DistributedEventStore`, significantly improving
  performance by reducing redundant data fetches for frequently accessed run-specific information.

### Changed

- ⚡️ Refined the **step execution count logic** in the `Dispatcher` to conditionally increment based on the presence of
  a `_max_executions_per_run` attribute, allowing for more precise control over step retries and execution limits.

### Removed

- 🗑️ Deprecated and removed the **`retry_operation` method** from `StoreBase`, streamlining the core store interface.
- 🧹 Removed **mutex-based synchronization and retry configuration** attributes (`max_retries`, `base_backoff`, and
  `synchronized_update` method) from `BaseContext`, simplifying the underlying NATS context management.

---

## [v0.81.0] - 2025-02-27 - Enhanced Reliability and Concurrency

### Changed

- ⚡️ **Overhauled event and step execution management** for enhanced concurrency and data consistency in distributed
  environments. This new approach leverages unique key storage in NATS JetStream, effectively eliminating race
  conditions previously addressed with mutexes.
- 🔄 **Optimized event access within the Dispatcher** by pre-fetching all relevant events before checking step readiness
  and executing steps, improving performance and ensuring consistent state snapshots.

### Fixed

- 🐛 **Improved handling for existing NATS JetStream KeyValue stores** by explicitly catching "already in use" errors
  during store creation, preventing exceptions in high-concurrency scenarios.

### Refactor

- ⚙️ **Strengthened NATS JetStream KeyValue store resilience** by increasing maximum retry attempts (from 5 to 10) and
  fine-tuning the backoff strategy for transient connection or operation errors.
- 🧹 **Enhanced internal `StoreBase` utilities**, introducing a dedicated method for storing raw byte values and
  generalizing the retry mechanism for various operations across the agent.

---

## [v0.80.0] - 2025-02-27 - Enhanced Localization Capabilities

### Changed

- 🌍 **Improved Internationalization (i18n)**: The `LocaleHandler` now supports passing additional arguments for dynamic
  content interpolation within translated strings, enabling more flexible and context-aware localized messages.

---

## [v0.79.0] - 2025-02-27 - Enhanced Data Consistency with Atomic Store Operations

### Added

- ✨ **Introduced Atomic and Synchronized Updates:** Implemented new `atomic_operation` and `synchronized_update` methods
  in `StoreBase` and `BaseContext` to ensure safe, concurrent data modifications in JetStream KV stores, effectively
  preventing race conditions.
- ⚙️ **Utility Methods for KV Stores:** Added `get_value`, `put_json_value`, and `get_json_value` to `StoreBase`,
  simplifying common data retrieval and storage patterns with optional transformations and JSON handling.

### Changed

- 🔄 **Improved Event Store Concurrency:** The `DistributedEventStore` now leverages the new synchronized update
  mechanisms for adding events, significantly improving reliability and data consistency under concurrent operations.
- ⚡️ **Enhanced Step Execution Tracking:** The `DistributedStepStore` now uses synchronized updates for
  `increment_execution_count` and simplified checks for `is_run_crashed`, ensuring accurate and reliable tracking of
  step executions in highly concurrent environments.
- 🧹 **Refined KV Store Key Retrieval:** Key-value store listing methods across `StoreBase` and `BaseContext` now
  automatically filter out internal mutex keys, providing cleaner and more relevant results.

---

## [v0.78.0] - 2025-02-27 - Streamlined Azure AI Search Configuration

### Changed

- ⚡️ **Simplified Azure AI Search Vector Store Creation:** The `create_azure_ai_search_vector_store` function now
  utilizes a default value for `semantic_configuration_name`, which streamlines the configuration process and simplifies
  the internal logic for setting up Azure AI Search vector stores.

---

## [v0.77.0] - 2025-02-26 - Enhanced Message Processing Reliability

### Refactor

- ⚡️ **Improved NATS JetStream Message Acknowledgment:** Refactored the `JSSubscriber` to acknowledge messages
  immediately upon receipt, preventing re-delivery of messages if subsequent processing tasks encounter issues. This
  enhances the reliability and predictability of message consumption.

---

## [v0.76.0] - 2025-02-26 - NATS Message Processing Refinement

### Changed

- 🔄 **Adjusted NATS JetStream Acknowledgment Logic:** The order of message acknowledgment has been updated in the
  `JSSubscriber` to occur *before* the message handler is executed. This change optimizes message flow and prevents
  potential re-delivery of messages in scenarios where the handler might encounter an error after initial processing has
  begun.

---

## [v0.75.0] - 2025-02-26 - Enhanced Asynchronous NATS Message Processing

### Changed

- ⚡️ **Improved NATS JetStream Message Processing:** The `JSSubscriber` now handles incoming messages asynchronously by
  creating a separate task for each message. This prevents the main message loop from being blocked by slow handlers,
  significantly enhancing concurrency and system resilience.
- 🚀 **Optimized NATS Core Message Handling:** The `NCSubscriber` has been updated to process incoming messages in a
  non-blocking fashion. This change ensures that message handling is more robust and efficient, improving overall system
  responsiveness.

---

## [v0.74.0] - 2025-02-26 - Enhanced Document Metadata Handling

### Fixed

- 🐛 **Corrected Document Title Extraction:** Ensured that the document title is accurately extracted from the
  **DataLakeFile** URI when enriching **RefDocDocument** metadata, preventing incorrect title assignments.

---

## [v0.73.0] - 2025-02-26 - Core Stability Enhancements and Version Alignment

### Fixed

- 🐛 **WebSocket Message Handling:** Enhanced robustness of the `WebSocketReceiver` to gracefully handle cases where a
  start event might not contain a `messages` attribute, preventing potential runtime errors.

### Changed

- 🔄 **Project-wide Version Bump:** Aligned all core microservices and internal dependencies to version `v0.73.0` for
  consistent build and deployment.

---

## [v0.72.0] - 2025-02-26 - Enhanced Document Metadata for RAG

### Added

- ✨ **Enriched `RefDocDocument` Metadata**: Improved document processing in the pipeline by automatically extracting and
  adding the **document title** and **source URI** to `RefDocDocument` instances. This enhancement provides richer, more
  granular context for Retrieval-Augmented Generation (RAG) applications.

---

## [v0.71.0] - 2025-02-26 - Improved Self-Hosted LLM Compatibility

### Changed

- ⚙️ **Enhanced Self-Hosted LLM Tokenizer Compatibility:** Updated the self-hosted LLM configuration to correctly infer
  base model names by stripping additional suffixes (`-bnb` and `-4bit`), improving compatibility with various quantized
  model formats for tokenization.

---

## [v0.70.0] - 2025-02-26 - Expanded Azure OpenAI Authentication Options

### Changed

- 🔑 **Enhanced Azure OpenAI LLM Authentication:** Enabled direct API key authentication for **Azure OpenAI Large
  Language Models**, providing a flexible alternative to Azure AD for resource access.

---

## [v0.69.0] - 2025-02-25 - Enhanced Build Stability and CI Efficiency

### Changed

- ⚡️ **Optimized CI Workflow:** Reordered Python and Poetry setup steps and introduced Poetry caching in the
  `add-tag.yml` GitHub Actions workflow to significantly improve build times and efficiency.
- 🦾 **Strengthened Dependency Management in CI:** Added explicit `poetry lock` and `poetry install` steps to GitHub
  Actions workflows, ensuring consistent and reliable dependency resolution and installation across all CI runs.
- 🧹 **Streamlined Build Dependencies:** Removed direct `pip install` commands for global tools like `tomlkit` in CI, now
  relying entirely on Poetry for comprehensive dependency management.

---

## [v0.68.0] - 2025-02-25 - Enhanced Self-Hosted LLM Configuration

### Changed

- ⚡️ **Improved Self-Hosted LLM Tokenizer Loading:** Enhanced the `tokenizer` property within `SelfHostedLLMConfig` to
  correctly load tokenizers for various self-hosted models by stripping common suffixes (like `-GGUF` and `-AWQ`) from
  model names and ensuring the proper encoding function is returned.

---

## [v0.67.0] - 2025-02-25 - Build System Enhancements and Poetry Integration

### Refactor

- 🧹 **Renamed Dependency Management Script:** The script for switching between local and remote cores has been renamed
  from `switch_dependency.py` to `switch_dependencies.py` for improved clarity.
- ⚡️ **Poetry Integration for Development Scripts:** Updated Makefile commands to utilize `poetry run` for executing
  core dependency switching scripts, streamlining the development workflow and aligning with Poetry's project management
  practices.

---

## [v0.66.0] - 2025-02-25 - Enhanced Authentication, UI Overhaul, and API Clarity

### Added

- 🖼️ **User Profile Images**: Implemented fetching and displaying user profile images from Azure AD, enhancing the user
  experience in the UI.
- 🔑 **Flexible Authentication Handler**: Introduced `TokenAndOauth2Handler` to enable combined use of Bearer token and
  OAuth2 authentication strategies, offering more versatile security configurations.
- 💾 **Persistent User Preferences**: Added `UserEntity` for storing user-specific data like favorite modules, laying the
  groundwork for personalized experiences.
- ⚡️ **Client SDK Generation**: Integrated OpenAPI-TS to automatically generate a robust TypeScript SDK for the
  frontend, streamlining API interactions and ensuring type safety.
- 🎨 **New Application Layouts**: Designed and implemented new `default` and `anonymous` Nuxt layouts, providing a more
  structured and visually consistent user interface.
- 👤 **User Bar Component**: Introduced a dedicated user bar component in the UI, displaying user information and
  integrating a dark mode toggle.
- 🚀 **Redesigned Login Experience**: Overhauled the login page with a modern, two-panel design and prominent Microsoft
  login integration.
- 🔄 **OIDC Silent Token Renewal**: Added support for silent token renewal in OpenID Connect (OIDC) to maintain seamless
  user sessions without visible re-authentication.
- 🌐 **Open Web UI Integration**: Enabled direct embedding of Open Web UI as an iframe within the application, providing
  a unified access point.
- 📊 **User Data Store**: Created a new Pinia store for managing user-related data, including profile information fetched
  via the API.
- 📄 **Structured Health Response**: Defined a `HealthResponse` DTO for the API's health endpoint, providing a clearer
  and standardized contract.

### Changed

- 🔒 **Standardized Security Dependencies**: Migrated API routes to use FastAPI's `Security` instead of `Depends` for
  authentication, improving consistency and clarity in security definitions.
- 🛠️ **Refined User Information Retrieval**: Updated the API's `get_user` endpoint to leverage a dedicated service
  method for fetching comprehensive user details, including the newly added profile image.
- 💅 **UI Framework Transition**: Transitioned the web application's primary styling and component library from Shadcn UI
  to PrimeVue, resulting in a refreshed look and feel.
- 🏗️ **Nuxt Layout Integration**: Refactored the web application to fully utilize Nuxt Layouts, establishing a
  consistent structural foundation across pages.
- 📈 **Improved OpenAPI Generation**: Enhanced OpenAPI schema generation to include `operation_id` for API routes,
  facilitating more accurate and usable client SDKs.
- 🎨 **Updated PrimeVue Theme**: Applied a new `zinc` color palette and configured dark mode for the PrimeVue theme,
  aligning with updated branding and improving visual consistency.

### Removed

- 🗑️ **Deprecated Multi-Authentication Handler**: Removed the generic `MultiAuthHandler` in favor of the more
  specialized and explicit `TokenAndOauth2Handler`.
- 🧹 **Shadcn UI Components**: Eliminated all Shadcn UI components, styling, and related configurations from the web
  application as part of the UI framework transition.
- 📦 **Unused BSON Dependency**: Cleaned up the `aihub_agent` module by removing an unused `bson` dependency.

### Refactor

- ⚙️ **Component Organization**: Reorganized and renamed the chat component (`Chat.vue` to `ThreadChat.vue`) and moved
  it into a dedicated `thread` subdirectory for better module clarity.

---

## [v0.65.0] - 2025-02-25 - Core Agent LLM Flexibility

### Changed

- 🔄 **Enhanced LLMWrappingAgent Configuration:** The `LLMWrappingAgentConfig` has been updated to use the more generic
  `ChatLLMConfig` instead of the provider-specific `AzureOpenAILLMConfig`. This modification provides greater
  flexibility, enabling the LLM Wrapping Agent to integrate seamlessly with a broader range of chat LLM providers.

---

## [v0.64.0] - 2025-02-24 - Improved Core Robustness and System Alignment

### Fixed

- 🐛 **Enhanced Locale Handling:** Ensured that the system's locale context reliably defaults to a predefined value when
  no specific locale is provided, improving overall stability and preventing potential issues.

---

## [v0.63.0] - 2025-02-21 - Refined Guards and Enhanced Testability

### Changed

- 🔄 **Improved Few-Shot Guard Prompting:** The `Few-Shot Guard` has been updated with a refined internal prompt that
  strictly enforces JSON-formatted output for guard responses, enhancing their reliability and programmatic parsing.
- ⚡️ **Enhanced `AgentTestRunner`:** The `get_events` and `get_events_of_type` methods in `AgentTestRunner` now support
  an `event_filter` parameter, allowing for more granular observation and testing of events based on their specific
  event type.

---

## [v0.62.0] - 2025-02-20 - Streamlined Development and Enhanced CI/CD

### Changed

- 🚀 **Improved CI/CD Stability**: The Docker service health check in the backend test action has been reordered to occur
  after Python dependency installation, enhancing the reliability of automated tests.
- ✨ **Simplified NoAuth Configuration**: The `NoAuthHandler` now provides default values for user `NAME`, `EMAIL`, and
  `ROLES`, reducing the need for explicit configuration in local development environments.

---

## [v0.61.0] - 2025-02-20 - Major Pipeline Configuration Overhaul

### Added

- ✨ **Explicit Data Lake Resource**: Introduced the `DataLakeResource` to clearly define and manage data lake container
  and directory configurations within pipelines, enhancing configuration clarity.
- ➕ **Dedicated Document Store Resource**: Added the `DocStoreResource` to provide explicit configuration for document
  store names and associated namespaces, improving resource management.

### Changed

- 💡 **Flexible Asset Key Inputs**: Asset factories for `documents` and `nodes` now support `AssetKey` objects as input
  for their respective data lake and document keys, providing greater flexibility in asset dependency definition.
- ⚙️ **Azure AI Search Configuration**: Enhanced the `AzureAISearchVectorStoreFactory` to correctly handle `None` values
  for `semantic_configuration_name`, allowing for more flexible vector store deployments without unnecessary parameters.
- 📄 **Document Content Representation**: Updated the display of `RefDocDocument` metadata to consistently use
  `get_content()` instead of `get_text()`, ensuring a more accurate representation of indexed document content in
  pipeline lineage.
- ⬆️ **Improved Milvus Vector Store Documentation**: Added comprehensive documentation, including detailed examples and
  docstrings, to the `MilvusVectorStoreResource` for clearer usage guidelines.

### Refactor

- 🔄 **Centralized Resource Configuration**: Overhauled resource definitions by removing the generic `NamespaceResource`
  and introducing dedicated, explicit resources like `DataLakeResource` and `DocStoreResource`, enhancing clarity and
  maintainability of pipeline configurations.
- 🧹 **Simplified LLM Integration**: Streamlined the setup for Large Language Models and Embedding Models by removing the
  `LlmHandlerResource` and enabling direct configuration via specific configuration objects (e.g.,
  `AzureOpenAILLMConfig`).
- 🏗️ **Improved Pipeline Naming**: Simplified job and asset naming conventions by removing the `customer_name`
  parameter, making asset and job names more concise and consistent.
- ⚙️ **Refined Data Lake Operations**: Updated data lake fetching and versioning operations to directly use container
  and directory names, aligning with the new explicit resource configuration model.
- 🔗 **Modernized MongoDB Connection**: The MongoDB connection utility now directly accepts a specific database name,
  improving connection clarity and robustness.

### Removed

- 🗑️ **Deprecated Generic Namespace Resource**: Eliminated the overarching `NamespaceResource`, simplifying the resource
  dependency graph and enforcing more specific resource configurations.
- ➖ **Removed LLM Handler Abstraction**: The `LlmHandlerResource` was removed, favoring a direct, configurable approach
  to LLM and embedding model instantiation.
- 🧹 **Obsolete Utility Functions**: Discarded various utility functions related to customer and namespace path handling,
  streamlining the codebase after the resource configuration overhaul.

---

## [v0.60.0] - 2025-02-20 - Build Action Configuration Update

### Changed

- 🔄 **Adjusted `build_image` GitHub Action:** The `file` input for the `build_image` action no longer has a default
  value. This change requires users to explicitly specify the Dockerfile path, promoting clearer and more explicit build
  configurations.

---

## [v0.59.0] - 2025-02-20 - Minor Infrastructure Enhancements

### Changed

- 🛠️ **Improved Backend Testing Visibility:** Added `docker compose ps` command to the backend test action, providing
  better insights into service health during automated testing workflows.
- 🔄 **Updated LLM Inference Server:** Upgraded the `llama.cpp` Docker image to the latest `server` tag, ensuring access
  to the most recent optimizations and features from the underlying LLM inference backend.

---

## [v0.58.0] - 2025-02-20 - Enhanced Image Building Flexibility

### Added

- ✨ **Improved `build_image` GitHub Action:** The `build_image` action now supports specifying a custom `Dockerfile`
  path via a new `file` input, providing greater flexibility for projects with non-standard Dockerfile locations.

---

## [v0.57.0] - 2025-02-20 - Enhanced User Authentication and Context Management

### Added

- ✨ **OpenWebUI Authentication Handler:** Introduced a new authentication handler (`OpenWebuiAuthHandler`) for seamless
  integration with the OpenWebUI frontend, providing robust user identity management for deployments utilizing
  OpenWebUI.
- 🧪 **Fake User Utility for Testing:** Added a `fake_user()` utility to simplify the creation of authenticated user
  contexts, streamlining development and testing of agents and services.

### Changed

- 🔄 **Enhanced User Context Propagation:** Updated the `UserMessageEvent` and core chat services (`ChatService`,
  `WebSocketReceiver`) to pass a rich `AuthenticatedUser` object instead of a simple user ID, providing more
  comprehensive user information throughout the system.
- ⚡️ **API Playground Default Authentication:** The `aihub_api` development playground now defaults to using the
  `OpenWebuiAuthHandler`, demonstrating its integration with the new authentication method.

---

## [v0.56.0] - 2025-02-20 - Unified Core Version Update and Release Automation

### Changed

- 🚀 **Core Component Version Upgrade**: All core components, including `aihub_lib`, `aihub_agent`, `aihub_api`,
  `aihub_bot`, and `aihub_pipeline`, have been updated to version `v0.56.0`, ensuring consistency across the ecosystem.
- 🔗 **Dependency Alignment**: Microservices now depend on the latest `aihub_lib` version `v0.56.0`, ensuring all
  services benefit from the most recent library improvements.
- ⚙️ **Streamlined Release Automation**: The release workflow (`add-tag.yml`) has been enhanced to automatically update
  `poetry.lock` files and commit `Makefile` changes, improving the robustness and consistency of new releases.
- 🛠️ **Updated Default Remote Core Tag**: The `Makefile` now defaults to `v0.56.0` for the remote core tag, simplifying
  setup for new environments.

---

## [v0.55.0] - 2025-02-20 - Unified AI-Hub API: OpenAI Standard for Agents and Enhanced Conversational Flows

### Added

- 🚀 **OpenAI API Compatibility for Agents**: AI-Hub agents can now be discovered and interacted with using standard
  OpenAI API endpoints (`/openai/models` and `/openai/chat/completions`). This allows for seamless integration of AI-Hub
  agents into existing OpenAI-compatible applications and workflows.
- 💡 **Conversational Agent Identification**: A new `is_conversational` flag has been added to agent discovery responses,
  allowing client applications to easily identify agents designed for chat-based interactions.
- ✨ **Dedicated User Message Event**: Introduced `UserMessageEvent` as a specific event type for user-initiated
  conversational inputs. This event now encapsulates chat messages and locale settings, providing a clearer and more
  structured way to handle user queries.

### Changed

- 🔄 **Agent Input Event Types**: Agent workflow steps that process user conversational input have been updated to
  exclusively accept `UserMessageEvent`, ensuring consistency and clarity in handling user messages.
- ⚡️ **Enhanced User Query Tracing**: The tracing system now directly utilizes the `user_query` property of
  `UserMessageEvent` for improved accuracy and readability of span information in conversational turns.

### Removed

- 🗑️ **Deprecated Chat Endpoints**: The standalone `/chat/completions` API endpoints have been removed. All chat
  interaction functionality is now consolidated under the new OpenAI-compatible API endpoints.

### Refactor

- 🧹 **Refined Start Event**: The `StartEvent` has been streamlined to serve as a generic workflow trigger, decoupling it
  from chat-specific message content and locale.
- 📂 **Logical Chat Message Grouping**: `AssistantChatMessage` and `UserChatMessage` definitions have been relocated to
  `aihub_lib/nats/events/user/content` for better logical organization.

---

## [v0.54.0] - 2025-02-19 - Unified Authentication, API Tokens, and Chatbot Expansion

### Added

- 🦾 **New `aihub_bot` Module**: Introduced a dedicated module for **Azure Bot Service integration**, enabling AI agents
  to be seamlessly exposed and interacted with through various chat channels like Microsoft Teams, Slack, and WebChat.
- ✨ **API Token Management**: Launched new API endpoints (`/tokens`) and backend services to allow users to **create,
  list, and revoke API tokens** for secure and granular access control.
- 🔑 **Flexible Authentication Architecture**: Implemented a new abstract `AuthHandler` and `MultiAuthHandler` to support
  **multiple authentication strategies** (OAuth2, API Tokens, Development/NoAuth) within the API, significantly
  improving extensibility and security.
- 🛠️ **Development User Information Provider**: Added `DevUserInformationProvider` for simplified user authentication in
  development and testing environments, making local setup more convenient.
- 🧪 **Comprehensive API Test Suite**: Introduced extensive new **pytest-based integration and unit tests** across core
  API functionalities (agents, chat, authentication, threads, tokens, users, health, internationalization), replacing
  outdated `.http` client test files and enhancing API reliability.
- 🚀 **Enhanced Simulated Agent Test Runners**: Improved both API and Bot test runners to better simulate agent behavior,
  including the handling of `stop_events`, for more robust and accurate testing environments.
- ⚙️ **API-Specific Configuration**: Introduced `ApiConfig` for managing API-specific settings independently from
  general Azure configurations, resulting in a cleaner and more modular setup.
- 🔗 **ASGI Request Adapter for Testing**: Added `ASGIAdapter` to enable seamless internal HTTP requests within test
  environments for FastAPI applications, which significantly improves test reliability and speed by avoiding actual
  network calls.
- 📄 **Utility for API Token Generation**: Provided a new Python script (`generate_api_token.py`) to easily generate API
  tokens for administrative or internal use.

### Changed

- 🔄 **Standardized Agent Event Specifications**: Renamed `StartEventSpecs` to `EventSpecs` and extended the agent
  discovery mechanism to include **`stop_events`**, providing a more complete and accurate representation of agent
  lifecycle.
- 🔒 **Agent Access Control**: Enhanced the `AuthenticatedUser` model to allow users with the "AllAgents" role to
  **access any agent**, simplifying permission management for administrators.
- 🗺️ **Updated Architectural Overview**: Revised documentation (in `aihub_doc`) to explicitly reflect the **integration
  of Chatbots** as a core interface layer within the AI-Hub architecture, outlining their design and technical
  implementation.
- 🔗 **Thread Creation API Route**: Modified the API route for **creating threads** from `/{thread_id}` to `/`, aligning
  with RESTful design principles for improved consistency.
- 👤 **User Information Retrieval**: Updated the user information retrieval mechanism in `aihub_api` to leverage a
  **multi-strategy provider**, enabling fetching user details from Azure AD, API tokens, or development configurations
  based on the active authentication.
- 🛂 **Health Endpoint Authentication**: The health endpoint (`/health`) now requires **authentication**, leveraging the
  new flexible authentication handlers to ensure consistency across API endpoints.

### Fixed

- 🐛 **MongoDB Connection Closing**: Ensured that the MongoDB connection is **properly disconnected** in the API runner's
  `lifetime_manager`, preventing potential resource leaks during application shutdown.
- 🐞 **Thread User ID Access**: Corrected a minor bug in thread management where user IDs were inconsistently accessed as
  `user_id` instead of `id`.

### Refactor

- 🧹 **Unified Authentication Dependency**: Replaced specific `use_oauth2_user` and `use_no_auth_user` FastAPI
  dependencies with a **generic `AuthHandler` interface**, providing a consistent and extensible way to integrate
  various authentication methods across API controllers.
- 📦 **Authentication Module Restructuring**: Reorganized and renamed authentication-related modules (e.g., `no_auth` to
  `NoAuthHandler`, `oauth2` to `OAuth2AuthHandler`) for **improved clarity and maintainability** within the
  authentication system.
- ⚙️ **Core Configuration Separation**: Separated general Azure base configuration (`AzureBaseConfig`) from API-specific
  settings (`ApiConfig`) to create a **more modular and explicit configuration structure**, enhancing manageability.
- 🗃️ **Simplified Document Database Access**: Streamlined database access for `RefDoc` entities by **removing the
  redundant `organization_shortname` parameter** from query methods, simplifying how reference documents are retrieved.
- 🧹 **CI/CD Workflow Adjustments**: Performed minor adjustments to GitHub Actions workflows, including Python dependency
  caching and poetry lock behavior, for **improved reliability and performance** of backend linting and testing
  processes.

### Removed

- 🗑️ **Deprecated Authentication Dependencies**: Eliminated the outdated `use_oauth2_user` and `use_no_auth_user`
  functions, which have been fully superseded by the new modular authentication handler system.
- 🗑️ **Legacy API Token Entity**: Removed the old `AccessToken` database entity, which has been replaced by the more
  robust and flexible `BearerToken` model for API token persistence.
- 🗑️ **Outdated HTTP Client Tests**: Removed several legacy `.http` client test files from the `aihub_api` playground,
  as their functionality is now covered by the new, comprehensive `pytest` test suite.

---

## [v0.53.0] - 2025-02-19 - Enhanced Security & Scalable Platform Foundations

### Added

- ✨ **New API Token Management:** Introduced comprehensive API endpoints and a dedicated `BearerToken` entity for
  creating, listing, and revoking API tokens, enabling secure programmatic access to the platform.
- 🚀 **Flexible Authentication Strategies:** Implemented a new `AuthHandler` abstraction and a `MultiAuthHandler`
  composite, allowing the API to support multiple authentication methods (e.g., OAuth2, API tokens, or no-auth for
  development) seamlessly.
- 🧪 **Enhanced Testing Infrastructure:** Added `ASGIAdapter` to enable direct in-memory testing of HTTP requests within
  the ASGI application, significantly enhancing test reliability and performance.
- 📄 **Dedicated API Configuration:** Introduced `ApiConfig` to centralize API-specific settings, separating them from
  general Azure infrastructure configurations for clearer management.
- 🛠️ **Developer User Information Provider:** Added `DevUserInformationProvider` to simplify local development and
  testing by providing a configurable user identity without requiring external authentication services.

### Changed

- 🔄 **Extended Agent Discovery:** Agent discovery responses now include `stop_events` alongside `start_events`,
  providing a more complete picture of an agent's lifecycle and supported termination events. The corresponding
  `StartEventSpecs` type was renamed to `EventSpecs` for broader applicability.
- 🗓️ **Thread Creation Timestamp:** Thread entities now automatically record their `created_at` timestamp upon creation,
  improving traceability and data management.
- ⚙️ **Updated CI/CD Workflows:** Adjusted backend linting and testing actions, including the `aihub_api` Docker Compose
  configuration and Poetry lock command, for improved reliability and efficiency in continuous integration.

### Fixed

- 🐛 **Refined Azure User Information Error Handling:** Improved error handling in `AzureUserInformationProvider` to
  raise a `ValueError` for failed user information fetches from Microsoft Graph, providing more precise feedback.
- 🐞 **Corrected Thread User ID Access:** Addressed an issue where thread access checks incorrectly used `user_id`
  instead of `id` for user validation within thread operations.

### Security

- 🔑 **Enhanced Agent Access Control:** The `AuthenticatedUser` now properly recognizes the `AllAgents` role, providing
  more flexible and robust permissions for agent interactions.
- 🔒 **Authenticated Health Checks:** The `/health` endpoint now requires proper authentication, preventing unauthorized
  access to application status information and ensuring a more secure deployment.
- 🛡️ **Agent Access Validation for Chat:** Chat completion endpoints now perform explicit authorization checks, ensuring
  users only communicate with agents they are permitted to access.

### Refactor

- 🧹 **Streamlined Authentication Modules:** Restructured and consolidated authentication-related modules, moving core
  components to `aihub_lib` and adopting a unified `AuthHandler` interface across the application. This includes the
  removal of legacy `use_oauth2_user` and `use_no_auth_user` dependencies.
- 🗑️ **Removed Legacy AccessToken System:** The outdated `AccessToken` persistence entity and its associated code have
  been removed in favor of the new, more flexible `BearerToken` system.
- 📦 **Centralized API Testing:** Migrated various `.http` integration test files to comprehensive Python-based `pytest`
  suites, improving test maintainability, automation, and reliability.
- 🧹 **Simplified MongoDB Document Access:** Refactored `RefDoc` querying methods to remove the `organization_shortname`
  parameter, streamlining data access and consistency.
- ⚙️ **Improved Configuration Clarity:** Renamed `BaseConfig` to `AzureBaseConfig` and adjusted its usage to better
  reflect its Azure-specific nature, separating it from general `ApiConfig`.
- 🧹 **General Code Cleanup:** Removed extraneous SonarLint settings from project files and performed minor import
  reordering for better code hygiene.

---

## [v0.52.0] - 2025-02-19 - Bot Reliability and Code Clarity Improvements

### Fixed

- 🐛 **Improved Conversation Message Retrieval:** Enhanced the conversation message retrieval mechanism to consistently
  return a list, ensuring more robust handling of conversation history within the bot service.

### Refactor

- 🧹 **Refined Conversation Entity Type Hinting:** Updated internal type hints for conversation message access, providing
  a more accurate representation of the data structure and improving code clarity.

---

## [v0.51.0] - 2025-02-19 - Unveiling the Future of AI-Hub: Tiered Services and Enhanced Architectural Clarity

### Added

- ✨ **Introduced Multi-Tiered AI-Hub Offering:** Detailed the new tiered approach to AI-Hub services, encompassing Basic
  LLM Access, Basic+ Integrations, Custom AI Assistants, and Autonomous AI Agents.
- 🦾 **Dedicated Sections for AI Capabilities:** Added comprehensive explanations for **LLM Access**, **AI Assistants**,
  and **AI Agents**, outlining their distinct roles, use cases, and benefits within the AI-Hub ecosystem.
- 📈 **Formalized New Architectural Components:** Explicitly documented **Bots module** (for communication channel
  integration), **Chat UI**, **Agents Transparency Frontend**, and **Process Panel** as core components of the AI-Hub
  architecture.

### Changed

- 🔄 **Revamped AI-Hub Introduction:** The foundational documentation for AI-Hub has been significantly rewritten to
  reflect its evolution into a comprehensive, multi-tiered platform.
- 📄 **Updated High-Level Architecture Diagram:** The architectural overview diagram now clearly illustrates the expanded
  ecosystem of AI-Hub components, including new user interfaces and integration points.

---

## [v0.50.0] - 2025-02-19 - Smarter Slack Bot Responses in Channels

### Changed

- 🤖 **Improved Slack Channel Interaction**: Bots, including both Agent and OpenAI variants, now intelligently respond in
  Slack channels only when explicitly mentioned. This change significantly enhances bot etiquette by preventing
  unnecessary responses in shared conversations.

### Added

- ✨ **Introduced Slack Interaction Utilities**: New helper functions, `is_slack_channel_message` and `is_bot_mentioned`,
  have been added to accurately detect Slack channel messages and identify when the bot is mentioned. These utilities
  are crucial for enabling the new, more selective response behavior in Slack.

---

## [v0.49.0] - 2025-02-19 - Enhanced Bot Architecture and Flexible Deployments

### Added

- ✨ **Configurable System Messages**: Bots can now be configured with specific system messages directly from the
  database, allowing for more tailored and dynamic bot behaviors.
- 💬 **Improved Slack Integration**: Enhanced handling of Slack threads, ensuring bots respond in the correct context and
  fetch full conversation history from channels.
- 🚀 **Centralized Streaming Responses**: A new common service now handles streaming responses for all bot types, leading
  to more consistent and efficient real-time user experiences.
- 💾 **Robust Conversation Persistence**: Conversation history management has been improved to support bulk message
  additions and automatically create conversations if they don't exist.
- 🛠️ **MongoDB Setup Option**: The Azure Bot setup script now explicitly supports direct MongoDB connection strings,
  offering more deployment flexibility.
- ⚙️ **Flexible Azure Bot Configuration**: The `setup_azure_bot.py` script now allows for more granular configuration of
  API URLs and paths, and supports specifying the Azure Bot SKU.

### Changed

- 🔄 **Stricter Conversation Schema**: The conversation entity schema has been made stricter (`strict=True`), ensuring
  data integrity and consistency in stored conversations.
- ⚡️ **Enhanced Azure Bot Setup**: The `setup_azure_bot.py` script now includes pre-emptive deletion of existing bots
  and improved error handling for a smoother deployment process.

### Refactor

- 🧹 **Unified Bot Services**: Major internal restructuring of bot logic, moving common functionalities like conversation
  management, system message retrieval, and activity processing into a shared `Service` base class.
- 🦾 **Specialized Bot Implementations**: Old generic chat bots have been replaced with specialized `AgentChatBot` and
  `OpenaiChatBot` classes (and their streaming counterparts), improving modularity and clarity.
- 📦 **Reorganized Bot Modules**: Bot and route modules have been reorganized and renamed to reflect the new, more
  logical architecture, improving code maintainability.
- 📖 **Simplified Conversation Entity**: The `ConversationEntity` has been streamlined by removing user-specific
  tracking, focusing solely on message history tied to a conversation ID.

### Removed

- 🗑️ **Deprecated Chat Bots**: The generic `ChatBot` and `EchoBot` implementations have been removed, superseded by the
  new specialized bot architecture.
- 🚫 **User Tracking in Conversations**: Direct user tracking fields have been removed from the `ConversationEntity` to
  simplify the database schema and conversation management.

---

## [v0.48.0] - 2025-02-19 - Enhanced Test Stability and Build System Updates

### Changed

- 🚀 Updated the **SonarCloud scan GitHub Action** to v5, improving the CI/CD pipeline's analysis capabilities and
  ensuring compatibility with the latest SonarCloud features.

### Fixed

- 🐛 Improved **chatbot test stability** by significantly extending timeouts for asynchronous operations, which helps
  prevent flaky test failures related to health checks and streaming response validations.

---

## [v0.47.0] - 2025-02-18 - Streamlined Azure Integrations and Core Refinements

### Added

- 🔗 **Expanded Azure SDK Support**: Integrated new Azure SDK dependencies, including `azure-mgmt-cognitiveservices`,
  `azure-storage-file-datalake`, and `adlfs`, to support enhanced Azure service interactions and data lake
  functionalities.
- 🧪 **CI/CD Azure Credential Injection**: Enabled the injection of `AZURE_SUBSCRIPTION_ID` into the CI/CD test
  environment, ensuring robust authentication for automated testing of Azure-dependent components.

### Changed

- 🚀 **Azure Subscription Identification**: Transitioned from referencing Azure subscriptions by display name to using
  the direct Azure Subscription ID (GUID), enhancing precision and reliability in resource management.
- ⚙️ **Standardized Azure Resource Naming**: Implemented a simplified naming convention for various Azure resources
  (e.g., Cognitive Search, Document Intelligence, Speech Service, Cosmos DB, and Data Lake), removing
  environment-specific suffixes for a cleaner and more consistent infrastructure.
- ✨ **Optimized Azure Service Authentication**: Streamlined the authentication process for Azure management clients by
  directly utilizing the Azure Subscription ID, which removes the need for redundant subscription lookups.

### Refactor

- 🧹 **Module Structure Modernization**: Performed internal refactoring of module structures and import paths (e.g.,
  `Configs` to `configs` and `vector_stores` to `stores`) to improve code organization and maintainability.
- 🔄 **Cosmos DB Access Consolidation**: Replaced the `CosmosConnectionStringSingleton` with `CosmosAccess` for a more
  consistent approach to managing Cosmos DB connections.
- 🗑️ **Configuration Cleanup**: Removed the `ENVIRONMENT` variable from `BaseConfig` as part of the broader effort to
  streamline Azure infrastructure configuration.

---

## [v0.46.0] - 2025-02-18 - Streamlined Azure Integration and Configuration

### Changed

- 🔄 **Azure Subscription Identification:** Transitioned all Azure infrastructure access from using Azure Subscription
  Names to more robust and direct Azure Subscription IDs, enhancing reliability and security.
- ⚡️ **Azure Resource Naming Convention:** Simplified the naming convention for Azure resources by removing the
  environment-specific slug, promoting a cleaner and more consistent resource management approach.

### Refactor

- 🧹 **Configuration Base Class:** Restructured the `BaseConfig` by removing the explicit `ENVIRONMENT` field,
  streamlining the configuration process and abstracting environment specificity across the platform.
- ⚙️ **Azure Service Access Logic:** Refactored the internal logic for accessing various Azure services (AI Search,
  Cognitive Services, Cosmos DB, Data Lake) to directly utilize Azure Subscription IDs, improving efficiency and
  removing reliance on potentially ambiguous subscription name lookups.
- 🗂️ **Internal Module Naming:** Standardized internal module naming conventions for configuration files from `Configs`
  to `configs` (lowercase) for improved consistency within the codebase.

### Added

- ⬆️ **Azure Management Dependencies:** Incorporated new `azure-mgmt-cognitiveservices`, `azure-storage-file-datalake`,
  and `adlfs` dependencies to support the updated Azure integration patterns and access methods.
- 🔐 **CI/CD Azure Subscription ID Support:** Updated CI/CD workflows to pass the `AZURE_SUBSCRIPTION_ID` secret,
  ensuring alignment of testing environments with the new Azure configuration standards.

---

## [v0.45.0] - 2025-02-17 - Internal Workflow Enhancements

### Changed

- 🔄 **Updated CI/CD Dependency Locking:** The GitHub Actions workflow now utilizes `poetry lock` instead of
  `poetry lock --no-update` for dependency management, ensuring more current dependency resolution during build
  processes.

---

## [v0.44.0] - 2025-02-17 - Flexible Azure Bot Deployments and Development Enhancements

### Added

- 🦾 **Introduced Single-Tenant Azure Bot Support:** The setup script now allows for the creation and configuration of
  Azure AD application registrations and Azure Bot resources specific to a single tenant, providing greater deployment
  flexibility.
- ⚡️ **Enabled Azure OpenAI Chatbot in Playground:** The development playground can now run and test OpenAI chat bots
  directly integrated with Azure OpenAI services, facilitating easier development and experimentation.
- 📄 **Expanded Credential Storage Schema:** New fields, including `APP_TYPE` and `APP_TENANTID`, have been added to the
  `Credentials` entity within `PathEntity` to support more diverse authentication types and tenant-specific
  configurations for bots.

### Changed

- 🔄 **Dynamic Bot Adapter Retrieval:** The `Service.get_adapter` method now directly accepts the FastAPI `Request`
  object, enabling more contextual and robust retrieval of the appropriate bot adapter.
- 🔑 **Updated Credential Field Names:** The `PathEntity` for credentials now uses `APP_ID` and `APP_PASSWORD` instead of
  the previous `app_id` and `app_password`, aligning with the new tenant-aware configuration.
- 🛠️ **Enhanced Azure Bot Setup Script:** The `setup_azure_bot.py` script has been significantly updated to manage
  single/multi-tenant bot configurations, including app registration logic and streamlined Cosmos DB credential storage.

### Refactor

- 🧹 **FastAPI Import Consolidation:** Standardized the import of `Request` and `Response` objects to use `fastapi`
  directly across all controllers, improving code consistency.
- 🗑️ **Streamlined Cosmos DB Configuration:** Removed the hardcoded Cosmos DB connection string from the development
  `.env` file, promoting more secure and dynamic environment variable management.
- ⚙️ **Optimized Cosmos DB ID Generation:** The `setup_azure_bot.py` script no longer explicitly generates object IDs
  for Cosmos DB entries, allowing the database to handle ID assignment automatically.

---

## [v0.43.0] - 2025-02-17 - Core Tooling and Build System Enhancements

### Changed

- 🚀 **Updated Poetry Version:** Upgraded the Poetry dependency management tool in GitHub Actions workflows from v1.8.3
  to v2.1.1, ensuring compatibility with the latest features and improved build processes.
- ⚙️ **Refined Poetry Core Requirements:** Standardized and updated the `poetry-core` build system requirements across
  all `pyproject.toml` files to `>=2.0.0,<3.0.0`, enhancing build stability and future compatibility.

---

## [v0.42.0] - 2025-02-17 - Internal API Refinement

### Refactor

- 🧹 **Updated Node Post-processing**: Renamed the `process` method to `postprocess_nodes` within
  `ScoreScalerPostProcessor` for better clarity and consistency in node manipulation utilities.

---

## [v0.41.0] - 2025-02-17 - Enhanced Azure AI Search Capabilities

### Added

- ✨ **Expanded Azure AI Search Configuration:** Introduced the ability to specify a `semantic_configuration_name` when
  creating Azure AI Search vector stores, providing more control over semantic search behavior and relevance tuning.

---

## [v0.40.0] - 2025-02-14 - Enhanced Azure Bot Management and Multi-Tenancy

### Added

- ✨ **Dynamic Bot Credential Storage**: Introduced a new `PathEntity` in `aihub_bot.persistence.entities` to securely
  store Azure Bot credentials, enabling flexible per-path bot configurations.
- ⚙️ **Azure Bot Setup Utility**: A new `setup_azure_bot.py` script simplifies the setup process for Azure Bots,
  automating Azure AD app registration, credential management, and their storage within Cosmos DB.

### Changed

- 🔄 **Multi-Tenancy for Azure Bots**: The `aihub_bot` framework now supports running multiple Azure Bots from a single
  application instance, each with its own credentials and accessible via distinct API paths.
- 🚀 **Dynamic Adapter Management**: The `Service` class no longer uses a static global adapter, instead providing a
  `get_adapter` method to dynamically create `CloudAdapter` instances based on the request path, retrieving
  corresponding credentials from the new `PathEntity`.
- ⚡️ **Controller Response Types**: Bot controllers now return `Response` objects instead of `JSONResponse` for broader
  compatibility in processing bot activities.

### Refactor

- 🧹 **Persistence Module Restructure**: The `aihub_bot` persistence entities have been reorganized by moving
  `ConversationEntity` and associated files to a more general `aihub_bot.persistence.entities` module.
- 🧹 **Centralized Bot Configuration**: Removed static Azure Bot credentials (`APP_ID`, `APP_PASSWORD`, `APP_TENANTID`)
  from `aihub_lib.infrastructure.azure.BaseConfig`, as these are now dynamically managed via the `PathEntity` for
  enhanced security and flexibility.
- 🧹 **Streamlined Service Class**: The `on_error` handler and static `ADAPTER` have been removed from the general
  `Service` class, contributing to a cleaner and more focused design for bot service routing.

---

## [v0.39.0] - 2025-02-14 - Improved RAG Agent Rejection Handling and Data Consistency

### Changed

- 💬 **Enhanced RAG Agent Rejection Responses:** The `RAGAgent` now includes the limited chat history (without context)
  when generating responses for rejected queries. This provides the Large Language Model (LLM) with more comprehensive
  context to explain the reasons for rejection, leading to more informative and relevant user messages.

### Refactor

- ⚙️ **Standardized Timestamp Processing:** The internal utility for formatting Unix timestamps has been updated to
  explicitly expect and handle integer timestamps, improving the robustness and consistency of date-time metadata
  processing across the system. This refactor includes corresponding updates to test cases to align with the new integer
  type expectation for metadata fields such as `inserted_at`, `updated_at`, and `created_at`.

---

## [v0.38.0] - 2025-02-13 - Bot Stability and OpenAI Integration Enhancements

### Fixed

- 🐛 **Improved Robustness for Chat Roles**: Ensured that chat message roles default to "user" if not explicitly
  provided, preventing potential issues with `None` values in bot interactions.
- ⚡️ **Enhanced OpenAI Streaming Reliability**: Added robust error handling for OpenAI chat completions, ensuring the
  stream continues smoothly even if content chunks are empty or null.

---

## [v0.37.0] - 2025-02-13 - Enhanced RAG Context and Expanded Localization

### Added

- ✨ **Expanded Localization Support:** Introduced French and Italian translations for agent rejection messages and agent
  thoughts, improving multi-lingual capabilities.
- ⚙️ **Configurable Locale Paths:** Added the ability to specify locale paths dynamically through agent configuration,
  increasing flexibility for internationalization.
- 📄 **Rich RAG Context Metadata:** Enhanced the format of RAG context documents to include comprehensive metadata (e.g.,
  source, namespace, language, version, timestamps), providing more detailed context to the LLM.
- 💡 **New Default RAG Context Prompt:** Introduced a standardized, detailed prompt for RAG agents within the `aihub_lib`
  for consistent context presentation.

### Changed

- 🔄 **Centralized Core Prompts:** Moved `condenser` and RAG-related context prompts from individual agents to the
  `aihub_lib` for better reusability and maintainability.
- 📝 **Improved Condenser Prompt Wording:** Refined the language of the `condenser.standalone_question` prompt across all
  supported locales for greater clarity and accuracy.

### Removed

- 🗑️ **Redundant Agent Prompts:** Removed specific `condenser` and `rag_agent` prompts from `aihub_agent`'s internal
  translations, as they are now managed centrally in `aihub_lib`.
- 🗑️ **Outdated Test Prompts:** Removed `test` prompts from agent translation files in `aihub_agent`.

---

## [v0.36.0] - 2025-02-13 - Streamlined Configuration & Azure Bot Service Enhancements

### Added

- ⚙️ **Extended Azure Bot Service Configuration**: Introduced new `APP_TYPE` and `APP_TENANTID` fields within the
  `BaseConfig` to provide more comprehensive configuration options for Azure Bot Service deployments.

### Changed

- ⚡️ **Improved Streaming Chat Completion Responsiveness**: Enhanced the `OpenaiChatService` to ensure smoother and more
  responsive streaming of chat completions by optimizing event loop handling.
- 🔄 **Streamlined Self-Hosted LLM Configuration**: The `SelfHostedLLMConfig` now automatically initializes its
  `default_parameter` if not explicitly provided, simplifying model setup and reducing boilerplate for developers.
- 🧪 **Updated Playground LLM Configurations**: The `main.py` playground example in `aihub_bot` has been updated to
  reflect the streamlined LLM configuration and now includes `gpt-4o-mini` as an example Azure OpenAI model.

---

## [v0.35.0] - 2025-02-12 - Agent Intelligence Boost: Few-Shot Guarding and Workflow Optimization

### Added

- ✨ **Few-Shot Guarding for RAGAgent:** Introduced a new mechanism to filter user queries based on predefined few-shot
  examples. This allows RAG agents to explicitly accept or reject requests with specific reasons, significantly
  enhancing control over agent scope. New configuration options (`few_shot_guard_examples`) and events
  (`FewShotAcceptEvent`, `FewShotRejectEvent`) support this feature.
- 🦾 **Direct User Query Access:** Added a convenient `user_query` property to the `StartEvent`, providing a
  straightforward way to access the last user message sent, simplifying agent workflow logic.
- 📄 **Localized Few-Shot Guard Prompts:** Included comprehensive internationalized prompts for the new few-shot guard,
  ensuring consistent and flexible agent behavior across various locales.
- 🚀 **Rejected Query Responses:** Implemented logic within the RAGAgent to automatically provide the user with a
  specific, configurable reason when a query is rejected by the few-shot guard.

### Changed

- 🔄 **RAG Agent Workflow Integration:** Modified the RAGAgent's processing flow to seamlessly integrate the new few-shot
  guard. This ensures that knowledge retrieval and subsequent responses are contingent on the initial query's
  acceptance.
- ⚙️ **Optional RAGAgent Prompts:** Made `condense_question_prompt` and `context_prompt` optional in `RAGAgentConfig`,
  offering greater flexibility for agent configuration and allowing default prompts to be used if not specified.
- 🧹 **Improved Standalone Question Condensation:** Enhanced the `condense_standalone_question` utility to explicitly
  filter out system messages from the chat history, leading to more accurate and focused standalone question generation.

### Refactor

- 📦 **Centralized Agent Utilities:** Reorganized common agent events and configurations (like `LimitChatHistoryEvent`
  and `StandaloneQuestionCondenserEvent`) by moving them into a new `aihub_agent/agents/common` directory, improving
  modularity and reusability across different agent types.
- 🔗 **Decoupled Agent Logic from `RunContext`:** Refactored both `FewShotAgent` and `RAGAgent` to directly pass
  essential data (such as user query and chat history) via event objects. This reduces reliance on the `RunContext` for
  state management, simplifying method signatures and improving code clarity.
- 🌎 **Moved Condenser Prompt Translations:** Relocated the standalone question condenser prompt translations from
  `aihub_agent` to `aihub_lib`, centralizing common prompt templates within the core library for better management.
- 📁 **Standardized Directory Naming:** Renamed `Configs` to `configs` and `Events` to `events` within the `rag` agent
  modules for consistent lowercase naming conventions across the project.

---

## [v0.34.0] - 2025-02-11 - Introducing `aihub_bot` and Core Project Enhancements

### Added

- ✨ **Introduced `aihub_bot` module**: A new core module dedicated to bot functionalities, enabling new conversational
  AI capabilities within the platform.

### Refactor

- 🧹 **Refined OpenAI Chat Service API**: The internal method for streaming OpenAI chat completions within
  `StreamOpenaiChatBot` has been renamed to `stream_on_message_completion` for better clarity and consistency with
  OpenAI's API.
- ⚙️ **Streamlined Project Configuration**: Updated internal IDE configuration files across all modules to improve
  project structure definition and ensure a consistent development environment setup.

### Removed

- 🗑️ **Removed Playground Environment Configuration**: The dedicated `.env` file for the bot playground testing has been
  deleted, streamlining local environment management.

---

## [v0.33.0] - 2025-02-10 - Enhanced RAG Agent with Contextual Node Retrieval

### Added

- ✨ **Introduced Contextual Node Retrieval for RAG Agent:** The RAG agent now supports fetching adjacent (previous and
  next) nodes from the vector store based on the initial retrieved results, significantly enhancing the contextual
  understanding for generated responses.
- ⚙️ **New `RetrievePrevNextConfig` Option:** A new configuration option has been added to the RAG agent's
  `RetrieveStepConfig`, allowing users to control the behavior of contextual node retrieval, including the number of
  nodes and traversal direction (previous, next, or both).
- 🛠️ **Developed `VectorPrevNextPostProcessor`:** A new internal post-processor and associated utility functions were
  introduced to efficiently manage the traversal and retrieval of related nodes in vector stores.
- 🧪 **Expanded CI/CD for `aihub_lib`:** The CI/CD workflow for the `aihub_lib` module now includes Milvus standalone
  docker-compose, enabling more robust and comprehensive testing for vector store-related functionalities.

### Refactor

- 🧹 **Centralized Milvus Test Utilities:** The `milvus_vector_store_content` module, containing utilities for Milvus
  vector store content management, has been moved from the RAG agent's playground to `aihub_lib/aihub_lib/testing` to
  improve organization and reusability across the platform.

---

## [v0.32.0] - 2025-02-10 - Expanded Bot Capabilities: OpenAI Integration and Refined Agent Interactions

### Added

- ✨ **OpenAI Chat Integration:** Introduced new controllers and services to allow direct chat interactions with OpenAI
  and Azure OpenAI models, supporting both JSON and streaming responses.
- 🚀 **Centralized Bot Authentication:** Added `APP_ID` and `APP_PASSWORD` fields to `BaseConfig` in `aihub_lib`,
  centralizing Azure Bot Service authentication configuration.

### Refactor

- 🧹 **Agent Chat Module Reorganization:** Extracted and moved agent-specific chat logic into a dedicated
  `aihub_bot/bots/chat/agent` and `aihub_bot/routes/chat/agent` package structure, including `JsonAgentChatBot`,
  `StreamAgentChatBot`, and `AgentChatService` for clearer separation of concerns.
- 🔄 **Generalized `ChatBot`:** The `ChatBot` class in `aihub_bot` has been refactored to serve as a more generic base
  class, removing agent-specific dependencies from its core.
- ⚡️ **Consolidated Bot Configuration:** Replaced module-specific `DefaultConfig` with the centralized `BaseConfig` from
  `aihub_lib` in the `aihub_bot` module, streamlining configuration management.

### Changed

- ↔️ **Agent Chat Endpoint Paths:** The API endpoints for agent-based chat completions have been updated from `/chat` to
  `/agent/chat` to reflect the new modular structure.
- ⏳ **Stream Response Timeout:** Increased the timeout for receiving chunks in stream responses from 0.5 to 1 second for
  improved robustness.

### Fixed

- 🐛 **Robust Conversation Creation:** Ensured that a new conversation is automatically created if it doesn't exist when
  adding a message, preventing potential errors during the first interaction.
- 🤖 **Improved Bot Message Role Assignment:** Enhanced the logic for assigning the 'bot' role to outgoing messages to
  ensure consistency.
- ⚙️ **Corrected Activity Model Type Mapping:** Adjusted the internal type mapping for `object` in activity models for
  improved data handling.

---

## [v0.31.0] - 2025-02-07 - Enhanced Tracing Authentication

### Added

- ✨ **Introduced Phoenix Tracing Authentication**: Added support for configuring and using a `PHOENIX_AUTH_TOKEN` to
  authenticate tracing data sent to the Phoenix endpoint, enhancing the security and control over your observability
  data.

---

## [v0.30.0] - 2025-02-07 - Improved Chat Event Handling

### Changed

- 🔄 **Streamlined User Message Event Creation:** Simplified the construction of `UserMessageEvent` within the
  `ChatService` by directly providing the full list of messages, enhancing consistency and streamlining how user message
  events are handled.

---

## [v0.29.0] - 2025-02-07 - Enhanced Bot Connectivity and Development Workflow

### Changed

- ⚡️ **Improved NATS Connectivity for Bots:** The `aihub_bot` now dynamically retrieves its NATS endpoint from
  `NatsConfig`, enhancing deployment flexibility and making the connection environment-agnostic.
- 📄 **Updated Semantic PR Workflow:** Added `bots` as a recognized type in the semantic PR workflow, standardizing and
  streamlining the development process for bot-related contributions.

---

## [v0.28.0] - 2025-02-07 - OpenAI API Emulation and Unified AI Resource Management

### Added

- 🚀 **OpenAI API Emulation**: Introduced a comprehensive OpenAI API-compatible endpoint suite, enabling seamless
  integration with existing OpenAI SDKs for various generative AI tasks. This includes:
  - 🤖 **Chat Completions**: Interact with configured chat models using the `/openai/chat/completions` endpoint,
    supporting both JSON and streaming responses.
  - 🔍 **Embeddings**: Generate text embeddings via `/openai/embeddings` for various models.
  - 🖼️ **Image Generation**: Create images using models like DALL-E through the `/openai/images/generations` endpoint.
  - 🎤 **Speech-to-Text (STT)**: Transcribe audio files to text using `/openai/audio/transcriptions`.
  - 🗣️ **Text-to-Speech (TTS)**: Convert text into natural-sounding speech through `/openai/audio/speech`.
  - 📄 **Model Management**: List and retrieve details for available models via `/openai/models` and
    `/openai/models/{model_name}`.
- ✨ **New AI Resource Configurations**: Expanded `aihub_lib` with dedicated configuration classes for different
  generative AI resource types:
  - `ImageModelConfig` and `AzureOpenaiImageModelConfig` for image generation models.
  - `STTConfig` and `AzureOpenaiSTTConfig` for speech-to-text models.
  - `TTSConfig` and `AzureOpenaiTTSConfig` for text-to-speech models.
- ⚙️ **Open WebUI Docker Compose Example**: Provided a `docker-compose-open-webui.yml` example to demonstrate
  integration with Open WebUI, leveraging the new OpenAI API emulation.

### Refactor

- 🔄 **Unified Generative AI Resource Structure**: Performed a significant refactoring of `aihub_lib.generative_ai.llms`
  into `aihub_lib.generative_ai.resources`, introducing a more generic and extensible structure for managing all AI
  model types (LLMs, Embeddings, Images, STT, TTS).
  - 🧹 **Centralized Base Configurations**: Introduced `ResourceConfig` as the new base class for all AI resource
    configurations, along with `AzureOpenaiResourceConfig` for Azure-specific models, promoting consistent configuration
    patterns.
  - 🧹 **Consistent Parameter Naming**: Standardized the `api_endpoint` parameter to `base_url` across all model
    configurations for clarity and consistency.
  - 🧹 **Parameter Class Renaming**: Renamed `ModelParameter` to `LLMModelParameter` (and its specialized versions like
    `ChatLLMParameter` and `EmbeddingLLMParameter`) to better align with the new resource hierarchy.

### Changed

- 🦾 **Agent Configuration Updates**: Updated `FewShotAgent`, `LLMWrappingAgent`, and `RAGAgent` configurations to
  utilize the new `aihub_lib.generative_ai.resources` paths and the `base_url` parameter, reflecting the core library's
  refactor.
- 💬 **Chat Service Updates**: Adjusted the internal `ChatService` in `aihub_api` to align with the new generative AI
  resource paths.

---

## [v0.27.0] - 2025-02-06 - Introducing Chat Streaming and Enhanced API Definitions

### Added

- ✨ **Asynchronous Chat Streaming**: Implemented new capabilities for streaming chat responses from AI agents to users,
  providing real-time updates as content is generated. This allows for a more dynamic and responsive user experience.
- 📄 **Dynamic OpenAPI Schema Generation**: Introduced a new model to dynamically generate OpenAPI schemas for `Activity`
  payloads, significantly improving API documentation and ensuring robust request validation for bot interactions.
- ⚡️ **Streaming Endpoint for Agent Interactions**: A new `/completions/{agent_class}/{agent_id}/stream` endpoint was
  added to support real-time, chunked responses from AI agents, specifically designed for streaming interactions.

### Changed

- 🚀 **Synchronous Chat Endpoint Updates**: The existing synchronous chat endpoint
  (`/completions/{agent_class}/{agent_id}/json`) now leverages the refactored `JsonChatBot` and includes enhanced
  OpenAPI documentation for better clarity and consistency.

### Refactor

- 🧹 **Bot Logic Decoupling**: Refactored the core `ChatBot` by extracting specific message handling logic into dedicated
  `JsonChatBot` and `StreamChatBot` classes. This enhances modularity, improves maintainability, and allows for distinct
  chat interaction patterns (e.g., JSON vs. streaming).
- 🔄 **Bot Service Endpoint Update Handling**: Updated the test runner and the main bot service endpoint to correctly
  process `PUT` requests, which is essential for updating message activities during streamed responses to users.
- 🧹 **Minor Code Enhancements**: Applied `@override` decorators for clarity and adherence to best practices, along with
  minor formatting adjustments.

---

## [v0.26.0] - 2025-02-06 - Robust Event Management and Enhanced Data Persistence

### Added

- ✨ **Enabled Recursive Event Serialization**: The `BaseEvent` model_dump method now intelligently serializes nested
  `BaseEvent` instances, ensuring comprehensive and accurate data persistence for complex event structures.

### Changed

- 🔄 **Enhanced Event Deserialization**: The `DistributedEventStore` has been updated to fetch and deserialize events
  more flexibly by using event class names directly and leveraging a generic `ControlEvent.deserialize_event` method.
  This improves support for polymorphic event types and simplifies retrieval logic.

### Fixed

- 🐛 **Improved Error Handling in Event Store**: Refined error handling within the `DistributedEventStore` to
  specifically catch `KeyNotFoundError` when retrieving events and added comprehensive logging for other exceptions,
  enhancing the store's reliability and diagnostic capabilities.

---

## [v0.25.0] - 2025-02-06 - Enhanced Testing Framework

### Refactor

- 🧹 **Refactored `MultistepHumanInTheLoopAgent` Tests:** Streamlined the test suite by consolidating multiple BDD-style
  test steps into a single, cohesive `pytest` function for improved clarity and maintainability.
- 🔄 **Migrated Test Implementation:** Transitioned the `MultistepHumanInTheLoopAgent` tests from a `pytest-bdd` driven
  approach to a direct `pytest` implementation, enhancing test maintainability and reducing boilerplate.

### Removed

- 🗑️ **Deprecated `pytest-bdd` Feature Files:** Removed the dedicated `pytest-bdd` feature file
  (`multistep_human_in_the_loop_agent.feature`) and its associated `pytest-bdd` imports and decorators from the
  `MultistepHumanInTheLoopAgent` test suite.

---

## [v0.24.0] - 2025-02-06 - Core Module Synchronization and CI/CD Enhancements

### Changed

- ✨ **Synchronized Core Module Versions**: All `aihub` core modules (`aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_lib`, `aihub_pipeline`) and their internal `aihub_lib` dependencies have been consistently updated to
  `v0.24.0`, ensuring full compatibility and alignment across the ecosystem.

### Refactor

- 🧹 **Streamlined CI/CD Test Workflow**: The GitHub Actions test workflow now references the `test_backend` action
  locally within the repository, improving build reliability and simplifying the continuous integration setup.

---

## [v0.23.0] - 2025-02-05 - Empowering Chatbots with New Bot Service and Enhanced Core Reusability

### Added

- 🤖 **New AI Hub Bot Service:** Introduced a dedicated `aihub_bot` component for seamless integration with Azure Bot
  Service, enabling conversational AI capabilities.
- 💬 **Chatbot and Echo Bot Implementations:** Shipped initial `ChatBot` for managing AI agent interactions and an
  `EchoBot` for basic conversational responses within the new bot service.
- 💾 **Conversation History Persistence:** Implemented `ConversationEntity` within the bot service to store and retrieve
  chat history, providing context for ongoing conversations.
- 🚀 **Bot Application Runners and Test Utilities:** Added `BotRunner`, `BotTestRunner`, and
  `SimulatedAgentBotTestRunner` to facilitate streamlined development, testing, and deployment of bot applications.
- 🌐 **Static Frontend for Bot Testing Playground:** Included basic static web files to enable local testing and
  interaction with the new bot service.

### Changed

- ⚙️ **Renamed API Chat Endpoints:** Renamed chat-related methods in `aihub_api` (e.g.,
  `start_api_stream_chat_interaction`) to clarify their role as API-specific entry points, distinguishing them from core
  logic now in `aihub_lib`.
- 🛡️ **Improved Thread Authorization Error Handling:** Enhanced error messages and consistency for unauthorized thread
  access and modification in the `aihub_api`'s thread controller.
- 🛠️ **Updated CI/CD and Build Configurations:** Modified GitHub Actions workflows and the Makefile to integrate the new
  `aihub_bot` component into linting, testing, and deployment processes.
- 🔄 **Dependency Management Script Update:** The `switch_dependency.py` script now supports managing `aihub_lib`
  dependencies within the `aihub_bot` project.

### Refactor

- 📦 **Core Component Reusability (aihub_lib):** Moved several foundational components (e.g., `AuthenticatedUser`,
  `Controller`, `HealthController`, NATS dependencies, WebSocket receiver components, and core chat service logic) from
  `aihub_api` into the shared `aihub_lib`. This significantly improves modularity and reduces duplication across
  services.
- 🚚 **Centralized Docker Compose Files:** Moved `docker-compose.yml` and `milvus-standalone-docker-compose.yml` to the
  project root, making them accessible and standard for all microservices.

---

## [v0.22.0] - 2025-02-04 - Internal System Alignment and Workflow Stabilization

### Changed

- 🔄 **Updated Core Dependency Versions:** Synchronized all core modules (aihub_agent, aihub_api, aihub_pipeline) to
  utilize the latest `v0.22.0` release of `aihub_lib`, ensuring consistent functionality and compatibility across the
  system.
- ⚙️ **Refined CI/CD Workflow References:** Updated GitHub Actions workflows (analyze, lint, review) to reference the
  stable `main` branch of AIHub Core actions, enhancing the reliability and consistency of automated checks.

---

## [v0.21.0] - 2025-02-04 - CI/CD Modernization: Streamlined Workflows with Reusable Actions

### Added

- 🚀 **Introduced Reusable GitHub Actions:** A new `aihub_action` directory has been added, containing a suite of modular
  and reusable GitHub Actions. These actions encapsulate common CI/CD tasks such as backend testing, linting (backend
  and frontend), SonarCloud scanning, pytest coverage commenting, and PR review, significantly streamlining workflow
  definitions and promoting reusability.
- 📄 **New Actions Documentation:** A `README.md` file is now available in the `aihub_action` directory, providing
  comprehensive documentation for all new reusable GitHub Actions and their usage.
- 🏷️ **Enhanced Pytest Markers:** New Pytest markers (`azure`, `self_hosted`, `slow`, `integration`, `experimental`)
  have been added and strict marker usage enforced in `aihub_agent` and `aihub_lib` for improved test organization and
  filtering.

### Refactor

- 🔄 **Centralized CI/CD Workflows:** The existing `.github/workflows` have been extensively refactored to leverage the
  newly introduced reusable GitHub Actions. This significantly reduces redundancy, improves maintainability, and
  standardizes CI/CD practices across the repository.
- 🧹 **Unified SonarCloud Scans:** The SonarCloud scanning process has been unified, integrating the `aihub_web` scan
  into the primary `sonarcloud-scan` job for a more cohesive analysis pipeline.

---

## [v0.20.0] - 2025-02-03 - Introducing Few-Shot Agents and Core System Improvements

### Added

- 🦾 **Few-Shot Agent**: A new agent type has been introduced, enabling agents to generate responses based on provided
  examples, significantly enhancing their learning capabilities for specific tasks.
- 🚧 **Agent Description Guard**: A new utility has been added that uses an LLM to evaluate if a user's query aligns with
  an agent's defined purpose, improving intelligent request routing and guardrail mechanisms.
- 🛑 **Guard Rejection Event**: A new event, `GuardRejectionEvent`, is now emitted when an agent's internal guardrail
  system rejects a request, providing a clear reason for the rejection to the client.
- 📚 **Few-Shot Prompting Utilities**: New models and functions (`FewShotExample`, `create_few_shot_messages`) have been
  added to the `aihub_lib` to standardize and simplify the creation of few-shot messages for LLMs.
- 🌍 **Localized Translation Strings**: New localized messages have been added to support the newly introduced Few-Shot
  Agent and the Agent Description Guard, ensuring multilingual support.
- 🧪 **Few-Shot Agent Playground Examples**: Comprehensive examples and tests for the new Few-Shot Agent have been added
  to the playground, demonstrating its capabilities and usage.

### Changed

- ⚙️ **Test Command Filtering**: The `Makefile` in `aihub_agent` has been updated to exclude Azure-specific tests from
  the default test command, allowing for more granular control over test execution.
- 📄 **Documentation Clarity**: The `README.md` has been updated to provide clearer guidance on agent creation and
  testing methodologies, distinguishing between `run.py` for continuous execution and `trigger.py` for limited runtime
  scenarios.
- 🏷️ **RAG Agent Test Categorization**: RAG Agent tests are now tagged with `@azure` and `@self_hosted` to facilitate
  better test organization and selective execution in CI/CD pipelines.

### Refactor

- 🔄 **Core Library Consolidation**: Fundamental components like `AgentConfig` and `EventDisplayer` have been relocated
  from `aihub_agent` to `aihub_lib`. This centralizes common functionalities, promotes reusability, and streamlines
  dependencies across agent and API projects, requiring numerous import path updates.
- 🧹 **Tracing Decorator Removal**: The `@tracing()` decorator has been removed from specific document loaders
  (`DocumentIntelligenceLoader`, `RawLoader`), indicating a shift towards a more integrated or alternative approach to
  tracing within the library.
- 🌲 **New Package Structures**: New package directories have been introduced across `aihub_agent` and `aihub_lib` to
  support a more organized and modular architecture for new features and existing components.
- ⬆️ **Document Intelligence Integration**: The `DocumentIntelligenceLoader` has been updated to align with the latest
  `DocumentContentFormat` enum from Azure's SDK, ensuring compatibility with updated dependency APIs.

---

## [v0.19.0] - 2025-01-31 - Core Component Release Synchronization

### Changed

- 🔄 **Component Version Alignment:** All core components, including `aihub_agent`, `aihub_api`, `aihub_lib`, and
  `aihub_pipeline`, have been synchronized and updated to version `v0.19.0`. This ensures all projects utilize the
  latest features and improvements from `aihub_lib`.

---

## [v0.18.0] - 2025-01-31 - Refined Release Workflow

### Refactor

- 🧹 **Improved Release Tagging Workflow:** Reordered the SSH key cleanup step in the GitHub Actions workflow to ensure
  it executes consistently after all tagging operations, enhancing the robustness of the release process.

---

## [v0.17.0] - 2025-01-31 - Enhanced Agent Orchestration, Flexible LLM Integration, and Developer Experience Boost

### Added

- 🦾 **Agent-in-the-Loop (AITL) Delegation**: Implemented a new mechanism for agents to delegate tasks to other
  specialized agents, enabling complex, collaborative workflows. This includes new event types for requests, responses,
  and exceptions during delegation.
- ✨ **Self-Hosted LLM and Embedding Support**: Introduced configurations and examples for integrating self-hosted Large
  Language Models (via `llama.cpp`) and embedding models (via Hugging Face Text Embeddings Inference) into agents and
  the local development environment.
- 🚀 **Milvus Vector Store Integration**: Added support for Milvus as a vector store backend for RAG agents, complete
  with local Docker Compose setup and utilities for content management.
- 🖼️ **Project-Wide IDE Configuration**: Included `.idea` files for consistent PyCharm project settings and improved
  developer experience, ensuring these files are automatically ignored by Git.
- ⚙️ **NATS Configuration Management**: Introduced a dedicated `NatsConfig` for centralizing NATS endpoint configuration
  via environment variables, enhancing flexibility for various deployment environments.
- 📝 **Comprehensive Test Coverage for Core Workflows**: Added new BDD test scenarios and corresponding test files for
  conditional, context, fan-out, multi-locale, and semantic event workflows, ensuring robustness and clarity of agent
  behaviors.
- 🔗 **`to_subject` Method for `PartialAgentTopic`**: Added a utility method to `PartialAgentTopic` for easier generation
  of NATS subjects from partial topic information.

### Changed

- 🔄 **Generalized LLM and Embedding Configurations**: Refactored `RAGAgentConfig` to use more abstract `ChatLLMConfig`
  and `EmbeddingLLMConfig`, allowing for greater flexibility in LLM and embedding model choices beyond Azure OpenAI.
- ⚡️ **Flexible Vector Store Integration in RAG**: Updated `RetrieveStepConfig` to directly accept a generic
  `BasePydanticVectorStore` instance, replacing the explicit `index_name` and allowing seamless integration of various
  vector database solutions like Milvus or Azure AI Search.
- 🐳 **Improved Docker Compose Setup for Development**: Migrated `aihub_agent`'s local Docker setup to `docker compose`
  (v2) syntax, replaced Ollama with `llama.cpp` and HF TEI for self-hosted LLM/embedding, and enhanced health checks for
  NATS and MongoDB, including new Milvus services.
- 📄 **Standardized Test Coverage in Makefiles**: Updated `Makefile` targets across all services (`aihub_agent`,
  `aihub_api`, `aihub_lib`, `aihub_pipeline`) to use `--cov=.` for more comprehensive and consistent local test coverage
  reporting.
- 🌐 **API Endpoint Naming Convention**: Standardized LLM and embedding model configurations to use `base_url` instead of
  `api_endpoint` for consistency across different LLM providers.
- 🧩 **Recursive Event Deserialization**: Enhanced `BaseEvent` deserialization to correctly handle nested event
  structures, improving the robustness of event processing.
- 🚀 **Git Auto-Tagging Workflow Refinement**: Streamlined the auto-tagging GitHub Actions workflow to trigger only on
  `main` branch pushes.
- ⬆️ **CI/CD Model and API Version Updates**: Upgraded the `review-pr.yml` GitHub Actions workflow to use `gpt-4o` and a
  newer Azure OpenAI API version (`2024-08-01-preview`) for PR reviews, alongside updated secret and variable names.
- 🪢 **Agent `tokenizer` Abstraction**: Introduced a `tokenizer` property in `ChatLLMConfig` and updated its usage in
  `limit_chat_history_with_context`, allowing for more flexible tokenization based on the configured LLM.

### Refactor

- 🧹 **Consolidated Playground Workflow Examples**: Reorganized and renamed various minimal workflow examples within the
  `playground` directory for better categorization and clarity.
- 💅 **Minor Code Formatting and Linting**: Applied consistent code formatting and linting rules across the codebase,
  including the adoption of `black` for Python code.
- 🗑️ **Removed Redundant `clean` Makefile Targets**: Eliminated duplicate `clean` targets from individual microservice
  `Makefiles`, as general project cleaning is now handled at the root level.

### Removed

- 🗑️ **Deprecated `ollama` Service**: Removed the `ollama` Docker service from the `aihub_agent` playground, replaced by
  more specific self-hosted LLM inference solutions (`llama.cpp` and HF TEI).
- 🧹 **Specific LLM Stop Event**: Removed the `LLMStopEvent` class, streamlining event handling as `LLMEvent` and
  `StopEvent` can be used directly or composed for similar functionality.

---

## [v0.16.0] - 2025-01-22 - Unleashing Self-Hosted LLMs and Bolstering CI/CD

### Added

- ✨ **New `DisplayingAgent` Example:** Introduced a new example agent (`DisplayingAgent`) with comprehensive BDD tests
  to showcase event display capabilities within agent workflows.
- 🦙 **Ollama Integration for Local Development:** Added `ollama` as a service in the `docker-compose.yml` for simplified
  local setup and testing of self-hosted Large Language Models.
- ⚙️ **Flexible Tokenizer Configuration for Self-Hosted LLMs:** Enhanced `SelfHostedLLMConfig` with a new
  `tokenizer_name` field, allowing precise specification of the tokenizer for self-hosted models, improving
  compatibility and performance.
- 🧪 **New BDD Tests for `LlamaIndexAgent`:** Implemented new BDD tests to validate the `LlamaIndexAgent`'s
  functionality, specifically with self-hosted LLM configurations.
- 🔍 **Direct StartEvent Retrieval:** Added a `get_start_event` method to `AgentTestRunner` for easier access to the
  initial start event during agent testing.

### Changed

- 🔄 **Expanded LLM Support for `LlamaIndexAgent`:** The `LlamaIndexAgent` now supports `SelfHostedLLMConfig`, providing
  the flexibility to integrate with a wider range of self-hosted Large Language Models alongside Azure OpenAI.
- 🚀 **Improved CI/CD Workflow Reliability:** Updates to `add-tag.yml` and `analyze-test-pr.yml` workflows, including
  refined git configurations, explicit user/email settings for bot commits, and improved dependency management, ensuring
  more robust and consistent automated tagging and testing.
- ⏱️ **Enhanced Test Setup with Ollama Readiness Checks:** Added readiness checks for the `ollama` service in CI/CD
  tests, ensuring that self-hosted LLM services are fully available before test execution.
- 📦 **Streamlined Global Dependency Management:** Introduced steps to validate and install global poetry dependencies
  and use local core, making the CI/CD test environment more consistent and efficient.

### Refactor

- 🧹 **Monorepo Project Structure:** Adopted a global `pyproject.toml` at the root for better management of the monorepo,
  simplifying project-wide dependency and tool configurations.
- 🗑️ **Removed `start_service.sh`:** The dedicated `start_service.sh` script has been removed, indicating a shift
  towards more standardized `poetry run` commands for service startup and local development.
- 🛠️ **Refined CI/CD Script Logic:** Updated the method for iterating over directories and reordered the tag deletion
  process within the auto-tagging workflow for improved script robustness and clarity.

---

## [v0.15.0] - 2025-01-21 - Workflow Refinements

### Changed

- ⚙️ **CI/CD Workflow Stability:** Enhanced the Pytest coverage comment job within pull requests to ensure it
  exclusively triggers on pull request events, improving workflow reliability.

---

## [v0.14.0] - 2025-01-21 - Streamlined Workflows and Robust Testing

### Added

- 🚀 **Automated Draft PR Creation**: Introduced a new GitHub Actions workflow that automatically creates a draft pull
  request when a new branch is pushed, streamlining early-stage development.
- 🧪 **Comprehensive Module Testing**: Implemented granular `make test-cov` commands and integrated `pytest-cov` across
  `aihub_agent`, `aihub_api`, `aihub_lib`, and `aihub_pipeline`, enabling detailed test coverage reporting for each
  module.
- 📊 **Automated Pytest Coverage Comments**: Added a new GitHub Actions job to automatically publish Pytest and coverage
  results as comments on pull requests, providing immediate feedback on test status.
- 🔎 **Generalized SonarCloud Scans**: Refactored SonarCloud analysis workflows to use a matrix strategy for all Python
  modules, streamlining code quality checks across the entire codebase.
- 🌐 **Frontend Linting Workflow**: Introduced a dedicated GitHub Actions workflow for linting the `aihub_web` (frontend)
  code using ESLint, ensuring consistent code style and quality.
- 📚 **Package Management Documentation**: Added a comprehensive "Package Management" section to the `README.md`,
  detailing the multi-package structure, versioning, and internal dependency referencing.
- ✨ **Agent Discovery Test Enhancements**: Expanded `AgentTestRunner` with new properties and a `wait_for_event` method
  to facilitate robust testing of agent discovery events and asynchronous workflows.
- ⚙️ **Enhanced Agent Workflow Examples**: Introduced new and expanded BDD test scenarios for configured, discoverable,
  human-in-the-loop, and optional workflow agents, showcasing more complex and configurable agent interactions.
- 🌍 **Multilingual Support Placeholders**: Added new empty translation files as placeholders for future French and
  Italian language support.

### Changed

- 🔄 **Internal Dependency Management**: Switched internal module dependencies (e.g., `aihub_agent` depending on
  `aihub_lib`) from local file paths to Git tags, enhancing consistency and simplifying deployments.
- ⚙️ **CI/CD Trigger Conditions**: Adjusted various GitHub Actions workflows (AI Code Review, Semantic PR checks) to
  prevent execution on draft pull requests, reducing unnecessary CI runs.
- 🌐 **Nuxt.js Configuration**: Updated the Nuxt.js configuration for the frontend, including enabling SSR (`ssr: false`)
  and integrating `@nuxt/eslint` for improved linting.
- 🧹 **`LocaleHandler` Usage**: Modified `LocaleHandler` in `aihub_lib` to be instantiated for better object-oriented
  practice in translation handling.
- 📄 **`switch_dependency.py` Script**: Improved the `switch_dependency.py` script by adding `develop: True` for local
  path dependencies, streamlining local development setup.

### Fixed

- 🐛 **Storybook Path Correction**: Corrected relative paths in `aihub_web/.storybook/main.ts` from `..\stories` to
  `../stories`, resolving potential issues with Storybook loading.

### Refactor

- ♻️ **CI/CD Version Bumping**: Overhauled the `add-tag.yml` workflow to generalize the version bumping process for
  `pyproject.toml` files across multiple directories and update the `Makefile` tag, making releases more reliable.
- 🏗️ **Centralized Test & Analyze Workflow**: Consolidated multiple SonarCloud jobs into a unified `test-modules` and
  `sonarcloud-scan` workflow, improving efficiency and maintainability of the CI/CD pipeline.
- 🧹 **Backend Linting Generalization**: Refactored the backend linting workflow to apply `black` and `isort` across all
  Python modules using a matrix strategy, ensuring consistent code style.
- 📂 **Internal Module Path Restructuring**: Moved node metadata constants from `aihub_lib.constants` to
  `aihub_lib.persistence.rag.vectors.node_metadata`, improving logical organization within the library.
- ⚙️ **Frontend Build System**: Migrated `tailwind.config.js` to `tailwind.config.mjs` and updated import statements for
  ES module compatibility in the frontend.
- 💡 **Playground Workflow Renaming**: Renamed `discovery_workflow` to `discoverable_workflow` for clearer semantic
  meaning, alongside renaming some associated test files and agent types.

---

## [v0.13.0] - 2025-01-17 - Enhanced Workflow Observability and Type System Robustness

### Added

- ✨ **Enhanced Step Debugging Capabilities**: Introduced comprehensive debug logging for workflow steps, providing more
  detailed insights into their configuration and event mappings for easier troubleshooting.
- ⚡️ **Enabled Logging in Playground Example**: Activated logging within a minimal workflow example to assist with
  debugging and understanding runtime behavior.

### Refactor

- 🧹 **Improved Type Extraction for Fixed-Size Lists**: Refactored the internal mechanism for extracting item types from
  `FixedList` annotations, leading to more robust and explicit type handling within the workflow system.

---

## [v0.12.0] - 2025-01-17 - Streamlined Development Environment & Setup

### Changed

- 🔄 **Improved PyCharm Development Setup:** The `README.md` now provides revised and clearer instructions for setting up
  multi-microservice projects in PyCharm. The new recommended approach leverages PyCharm's "Attach Project" feature,
  allowing developers to manage all `aihub-core` microservices within a single PyCharm window while maintaining separate
  and isolated Poetry environments for each service, significantly enhancing the developer experience for complex
  projects.

### Removed

- 🗑️ **Obsolete PyCharm Run Configurations:** Removed outdated PyCharm run configuration files (`.run/*.xml`) that are
  no longer necessary following the revised development environment setup instructions.

---

## [v0.11.0] - 2025-01-16 - Smart Agents Get Smarter: RAG Capabilities & Enhanced Developer Experience

### Added

- ✨ **Introduced RAG Agent**: A new, full-fledged **Retrieval-Augmented Generation (RAG) agent**, `RAGAgent`, is now
  available, enabling knowledge-aware conversational AI.
- 🛠️ **RAG Utilities**: A suite of new utilities has been added for RAG workflows, including functions to **combine
  nodes in order**, **condense standalone questions**, **limit chat history with context**, and **retrieve nodes**,
  facilitating advanced contextual processing.
- 📊 **Score Scaling Post-processor**: A `ScoreScalerPostProcessor` has been introduced to **normalize retrieval
  scores**, improving the relevance ranking of retrieved information.
- 📖 **Agent Development Guide**: A comprehensive `README.md` for `aihub_agent` now provides **detailed guidance on
  developing, testing, and documenting new AI agents**.
- 🗣️ **Localized Prompts & Thoughts**: New **localized prompt and thought messages** have been added for the RAG agent,
  improving multi-language support and user experience.

### Changed

- 🧹 **Code Quality Enforcement**: Integrated **`ruff`, `isort`, and `black` configurations** into `aihub_agent` and
  `aihub_api` projects, along with a new `pr-ready` Makefile target, to ensure consistent code style and quality.
- 🏷️ **Enhanced Step Metadata**: The `@step` decorator now supports **`name` and `description` parameters**, allowing
  for more detailed and localized metadata for workflow steps.
- 📈 **Improved Workflow Visualization**: The `NetworkXVisualizer` has been enhanced to **leverage new step metadata**,
  providing richer and more informative workflow diagrams.
- 🔗 **Event System Refinements**: Refined **event handling logic and structure** across various `nats.events` classes,
  including additions for `Document` and `RetrieverEvent` to support advanced data flow in RAG workflows.

### Refactor

- 🧪 **Refactored `AgentTestRunner`**: The `AgentTestRunner` has been refactored to **improve test environment control**,
  including new context managers for streamlined agent testing.
- ⚙️ **Internal Build Process Updates**: Updated internal dependency references and `Makefile` structures to streamline
  **build and test processes** for `aihub_agent` and `aihub_api`.

---

## [v0.10.0] - 2025-01-16 - Introducing Robust Branch Protection Policies

### Added

- 🛡️ **Implemented Comprehensive Branch Protection Policies:** New documentation has been added to the README, detailing
  robust branch protection rules for `main` and `initiative` branches. These rules enforce restricted direct pushes,
  prevent deletions and force pushes, require a linear commit history, and mandate pull requests with specific approval
  processes (including squashed merges), significantly enhancing codebase stability and integrity.

---

## [v0.9.0] - 2025-01-16 - Enhanced Windows Setup Documentation

### Added

- 📄 **Improved Windows Setup Guide**: Added specific instructions for installing and verifying `make` on Windows,
  streamlining the prerequisite setup for Windows users.

---

## [v0.8.0] - 2025-01-15 - Documentation Enhancements and Version Update

### Changed

- 📄 **Improved Docker Setup Guide:** Added troubleshooting information and a helpful resource link in the `README.md` to
  assist users with common Docker Desktop WSL update issues during setup.

---

## [v0.7.0] - 2025-01-15 - Enhanced Local Development Experience

### Added

- ✨ **Introduced IntelliJ/PyCharm Run Configurations** for `LLMWrappingAgent`, core API development, and core API
  testing, simplifying local setup and execution of key components.
- 🚀 **Implemented a standardized `start_service.sh` script** to streamline the local execution and setup of various
  microservices (e.g., agents, API), ensuring consistent dependency management and startup procedures.
- 📄 **Created a dedicated `.env` file** for the API development playground, simplifying local environment configuration
  and connection details for testing and development.

### Refactor

- 🔄 **Updated `aihub_pipeline`'s dependency** on `aihub_lib` to use a local path reference instead of a Git tag,
  facilitating monorepo development and simplifying inter-project dependency management.

### Removed

- 🗑️ **Dropped the `bson` dependency** from `aihub_lib`, streamlining the library's overall dependencies.

---

## [v0.6.0] - 2025-01-13 - Agent Workflow Refinements, New LLM Agent, and Comprehensive Testing

### Added

- 🦾 **New LLM Wrapping Agent:** Introduced `LLMWrappingAgent`, a basic agent designed to simplify the integration and
  usage of Large Language Models within agent workflows, including cost reporting capabilities.
- 📄 **Comprehensive Testing Documentation:** Added a detailed "Testing" section to the `README.md`, outlining the use of
  `pytest` and `pytest-bdd` for behavior-driven development (BDD) and structured testing of agents.

### Changed

- 🔄 **Restructured Playground Examples:** Reorganized existing agent examples into a new `minimal_workflow` directory
  structure (e.g., `conditional_workflow`, `context_workflow`, `simple_workflow`) to improve clarity, consistency, and
  ease of understanding for different agent patterns.
- 📝 **Enhanced Agent Documentation:** Significantly revised and expanded Chapter 5 of the documentation
  (`5_agents_in_detail.md`) for improved readability and deeper explanations of agent concepts, context handling, and
  multi-agent coordination.
- 🧹 **API Playground Reorganization:** Consolidated and reorganized `aihub_api/playground` examples into clearer
  `development` and `testing` directories, streamlining API testing setups.

### Refactor

- ⚡️ **Unified LLM Agent Example:** The previous `DevAgent` playground example has been refactored and integrated into
  the new `LLMWrappingAgent` within the `basic` agents directory, providing a standardized LLM interaction pattern.
- ⬆️ **Improved Gitignore:** Updated `.gitignore` to include common Python build artifacts, enhancing repository
  cleanliness.

### Removed

- 🗑️ **Deprecated Playground Agents and APIs:** Removed several older, individual playground agent implementations and
  their corresponding API examples, streamlining the codebase by eliminating redundant or outdated examples.

---

## [v0.4.0] - 2025-01-07 - Improved Onboarding and Automated Code Analysis

### Added

- ✨ **Introduced Comprehensive Code Quality Scans**: Integrated SonarCloud into the CI/CD pipeline for the `Agent`,
  `API`, `Lib`, `Pipeline`, and `Web` core components, enabling automated code quality and security analysis.
- 🚀 **New CI/CD Workflow for Analysis and Testing**: Established a dedicated GitHub Actions workflow to automatically
  run SonarCloud scans on pull requests and pushes to `main`, enhancing continuous quality assurance and feedback.

### Changed

- 📄 **Expanded Developer Documentation**: Significantly updated the main `README.md` with a detailed table of contents,
  extensive sections on project structure, repository types, branching strategy, and a comprehensive "Getting Started"
  guide, greatly improving developer onboarding and project clarity.

---

## [v0.2.0] - 2025-01-07 - Enhanced Context Understanding and Pipeline Alignment

### Changed

- 📄 **Documentation Clarity**: Clarified the behavior of **RunContext** during Human-in-the-Loop (HITL) pauses,
  emphasizing that it remains open to preserve agent state.
- 🔄 **Context Utilization**: Updated documentation to reflect that both **RunContext** and **ThreadContext** can be
  leveraged for maintaining agent state during HITL steps.

### Refactor

- 🧹 **Dependency Management**: Transitioned **aihub_pipeline**'s dependency on **aihub_lib** from a local path to a
  direct Git repository reference, streamlining module integration and future releases.

---
