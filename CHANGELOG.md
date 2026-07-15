# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.310.1] - 2026-07-15 - Streamlined Manual Release Process

### Added

- ✨ **Introduced Manual Release Workflow:** A new GitHub Actions workflow (`release-manual.yml`) has been added to
  provide maintainers with enhanced control and flexibility over the release process. This workflow allows for the
  manual creation of releases with a specified `vMAJOR.MINOR.PATCH` version tag from any arbitrary branch, which is
  particularly useful for hotfixes or special-purpose releases. It fully automates critical steps such as changelog
  generation, version bumping, and dispatching all downstream build, release, and publishing workflows (e.g., Docker
  images, npm, PyPI), while ensuring release safety by preventing tag overwrites and keeping the source branch pristine.

______________________________________________________________________

## [v0.310.0] - 2026-07-15 - Agents Gain IMAP Read Capability with Secure S3 Attachment Handling

### Added

- ✨ **Introduced IMAP Read Capability for Agents**: Agents can now connect to IMAP inboxes, list unread messages, and
  fetch selected messages along with their attachments. This foundational capability enables agents to interact with
  email workflows.
- 🦾 **New IMAP Agent Demonstrator**: A new `ImapAgent` (non-conversational) has been added to the playground, showcasing
  how to list unread mail and fetch messages with S3-referenced attachments.
- 📦 **Core IMAP Configuration and Event Types**: Added `ImapClientConfig` for configuring IMAP connections, and new
  event types like `UnreadMailListedEvent`, `MailFetchedEvent`, `MailAttachmentRef`, and `UnreadMailSummary` for
  structured communication of IMAP data.
- ☁️ **S3 Integration for Agent Attachments**: The agent runtime now includes native S3 client integration, allowing
  mail attachments to be stored securely in S3 and referenced by `file_id` within agent events, preventing event bloat.
- 🔒 **Configurable Message Size Limits**: Implemented deployment-fixed caps for raw message size, body size, and
  attachment size to protect agents from hostile or oversized emails and prevent exceeding message-size limits in the
  audit trail and WebSocket streams.
- 🌍 **Internationalization for IMAP Features**: Added translations for IMAP configuration fields and new IMAP-related
  events in German, English, French, and Italian.
- 📄 **Architectural Decision Record for IMAP**: A new ADR documents the design decisions behind the agent's IMAP read
  capability, covering exposure, event handling, and attachment storage.

### Changed

- 🚀 **Agent Runtime Dependency on S3**: The agent runtime now depends on S3 for storing mail attachments, expanding its
  infrastructure requirements.
- 📡 **IMAP Events Exposed via WebSocket**: `UnreadMailListedEvent` and `MailFetchedEvent` are now included in the
  `DisplayEvents` type, making them visible in the frontend's event timeline via WebSocket.
- 🧩 **Filename Sanitization for Attachments**: Improved security by sanitizing attachment filenames to prevent path
  traversal vulnerabilities.

### Security

- 🔑 **HTML Body Exclusion from Events**: The raw HTML body of fetched emails is deliberately *not* surfaced in
  `MailFetchedEvent` (which is persisted and streamed to the frontend) to mitigate Cross-Site Scripting (XSS) risks from
  hostile sender markup.

______________________________________________________________________

## [v0.308.2] - 2026-07-14 - Enhanced OpenWebUI Model Availability and Access

### Added

- ⚙️ **New `list_base_models` method:** Introduced a new client method in `OpenWebuiClient` to retrieve OpenWebUI
  registry entries for raw provider models (those without a `base_model_id`), enabling more comprehensive model
  management.

### Fixed

- 🐛 **Resolved OpenWebUI model access denials:** Fixed an issue where users were unable to access certain workspace
  models in OpenWebUI, encountering "Model not found" errors even when the models were visible. This occurred when an
  underlying raw LiteLLM model was inadvertently registered, creating a "shadowing" entry that blocked user access.
- 🛡️ **Automated removal of shadowing base models:** Implemented an automatic cleanup process during OpenWebUI model
  synchronization to detect and remove these problematic "shadowing" base model registry entries, ensuring consistent
  and correct user access to all provisioned models.

______________________________________________________________________

## [v0.308.1] - 2026-07-14 - Refined Function Registration and Default Status

### Changed

- ⚙️ **Adjusted Default Function Activation:** Modified the initial setup process to register core functions like
  **`source_action.py`**, **`tracing_action.py`**, and **`memory_action.py`** as *inactive* by default, providing
  administrators with greater control over initial system capabilities.

______________________________________________________________________

## [v0.309.4] - 2026-07-14 - Improved Event Context Resolution for Enhanced UI Navigation

### Added

- ✨ **New Thread Resolution API:** Introduced a dedicated API endpoint
  (`/api/v1/active/events/agents/displays/{display_id}/thread`) allowing the UI to dynamically resolve the correct
  conversation thread from a display ID, streamlining navigation to related traces, sources, or memories.
- 📄 **Thread Reference DTO:** Added a new `ThreadReference` data transfer object to structure the API responses for
  thread resolution.
- 📚 **Core Persistence Support:** Implemented a new method within the `PersistedAgentEventEntity` to efficiently query
  and retrieve the thread ID associated with any given display ID from the persistence layer.
- 🧪 **Robust API Testing:** Included comprehensive new tests for the `resolve_thread_for_display` API endpoint,
  validating correct thread resolution across various scenarios, including AI-Hub Traceability Layer (AITL) delegation.

### Changed

- 🔄 **Synchronized Event ID Hashing:** Updated the `_str_to_object_id` function in OpenWebUI actions (memory, source,
  tracing) to precisely match the hashing logic used by AI-Hub's event production, ensuring consistent `display_id`
  generation for accurate event linking.
- 🚀 **Dynamic UI Panel Navigation:** Enhanced the OpenWebUI frontend to dynamically fetch the associated **thread ID**
  using the new API when users click "show traces," "show sources," or "show memories," providing a more resilient and
  decoupled approach to navigating contextual panels.
- 🗑️ **Optimized Cross-Window Communication:** Removed the direct `thread_id` from `postMessage` payloads originating
  from OpenWebUI functions, as the frontend now handles its resolution, simplifying the data passed between the embedded
  UI and the parent application.

### Refactor

- 🧹 **Standardized Error Messaging:** Consolidated the "access denied" error message for HTTP 403 responses within the
  `EventController` into a reusable constant, improving consistency and maintainability.

______________________________________________________________________

## [v0.309.3] - 2026-07-13 - Deployment Configuration & Documentation Enhancements

### Changed

- ⚙️ **Standardized MongoDB Connection String:** Explicitly configured the `MONGO_CONNECTION_STRING` across all Docker
  Compose deployment environments, ensuring consistent and clear database connectivity for all services.
- 📄 **Updated Environment Variable Documentation:** Ensured the `memory_writer_agent` is correctly listed in the
  environment variables documentation, reflecting its operational dependencies on MongoDB, NATS, and Neo4j.

______________________________________________________________________

## [v0.309.2] - 2026-07-13 - Empowering Expert Agents with Advanced Memory Capabilities

### Added

- 🦾 **Enhanced Expert Agent Capabilities:** The `expert_asking_agent` and `expert_rag_agent` services are now fully
  configured to integrate with **Mem0** for advanced LLM, embedding, and reranking functionalities, and **Neo4j** for
  organizational memory graph storage, significantly boosting their intelligence and knowledge retention.

### Changed

- 📄 **Updated Environment Variable Documentation:** The documentation for environment variables has been updated to
  reflect the expanded utilization of **Mem0** and **Neo4j** settings by the `expert_asking_agent` and
  `expert_rag_agent`.

### Removed

- 🗑️ **Streamlined CI/CD Workflow:** An extraneous Docker login step has been removed from the `test-backup-e2e` GitHub
  Actions workflow, contributing to a more efficient build process.

______________________________________________________________________

## [v0.309.1] - 2026-07-13 - Enhanced Memory Protection and Agent Isolation

### Added

- ✅ **New Tests for Memory Scoping Logic**: Dedicated unit tests were introduced to validate the correct implementation
  and behavior of agent-specific memory isolation within the Mem0 service.

### Changed

- 🔐 **Improved Agent Memory Isolation**: User memories in Mem0 are now natively scoped to the writing agent during
  reconciliation, preventing one agent from modifying or deleting another agent's user-specific data. Organization
  memories continue to be tenant-shared as intended.

______________________________________________________________________

## [v0.309.0] - 2026-07-09 - UX Boost: Asynchronous User Memory & Graph Store Optimization

### Added

- 🦾 Introduced the **`MemoryWriterAgent`**, a new dedicated system agent for asynchronously persisting user memories,
  significantly improving chat responsiveness by decoupling memory writes from the critical path.
- ✨ Implemented a **`discoverable` flag** on the base `Agent` class, enabling programmatic control over which agents
  appear in the Admin UI.
- 💬 Added new **event types** (`MemoryStorageRequestedEvent`, `StoreUserMemoryRequestedEvent`, `MemoryStoredStopEvent`)
  to orchestrate the new asynchronous memory storage workflow.
- ⚙️ Introduced a new configuration option, **`enable_async_memory_storage`**, for RAG and ExpertRAG agents, allowing
  administrators to enable or disable asynchronous user memory persistence.

### Changed

- ⚡️ Drastically **improved chat user experience** by making user memory persistence asynchronous; the "thinking"
  indicator now clears immediately after an agent answers, without waiting for memory storage.
- 🚀 **Optimized user memory save performance** by disabling the Neo4j graph store for user memory, reducing save latency
  by approximately 73% (from ~66s to ~17.5s) per turn. Organization memory retains graph store capabilities.
- 🔄 Enhanced **cross-agent user memory sharing** by routing user memory queries through the vector store, allowing
  agents to access all user memories regardless of the originating agent.
- 📈 Expanded **Langfuse tracing** to correctly attribute asynchronous `MemoryWriterAgent` runs to the original user
  query and context.
- 📦 Updated **deployment configurations** to include the new `MemoryWriterAgent` service across all Docker Compose
  variants.

### Refactor

- 🧹 Redesigned **`AgentMemory` architecture** to use separate, lazily-built Mem0 services for user and organization
  memory, enabling distinct and optimized storage configurations for each.
- 🛠️ Modernized **Mem0 integration** to gracefully handle disabled graph stores, preventing errors and ensuring robust
  memory operations when graph data is not present.
- ⚙️ Introduced an **`enable_graph` parameter** to `Mem0Settings.get_config` for fine-grained control over graph store
  inclusion, enabling performance optimizations per memory type.

______________________________________________________________________

## [v0.308.0] - 2026-07-08 - Dynamic LLM Access and Robust Role Management

### Added

- ✨ **Dynamic LLM Model Discovery and Provisioning**: Introduced automatic discovery of LiteLLM chat models and their
  provisioning as workspace models in OpenWebUI, allowing users to select and interact with available LLMs.
- 🦾 **"Use All Models" Access Preset**: Added a new access preset to quickly grant users permission to utilize all
  available LLM models.
- 📂 **Model Capabilities in Access Editor**: Integrated a dedicated 'Models' category into the Role Access Rules editor,
  enabling fine-grained control over model permissions.

### Fixed

- 🐛 **Reliable Role Access Updates**: Corrected the role update mechanism to ensure that changes to access rules trigger
  proper re-synchronization of OpenWebUI access grants.
- 🔒 **Normalized Model Access Rules**: Addressed an issue where model names containing dots (e.g., `Kimi-K2.6`) were not
  correctly normalized in access rules, preventing proper matching and access grants. This applies to both role and
  tenant access rules.
- 🩹 **Persistent Access Change Hooks**: Fixed a regression where internal signal subscriptions for access changes were
  prematurely garbage-collected, ensuring that OpenWebUI re-syncs are reliably triggered.
- 🔑 **Improved Cross-Tenant Role Isolation**: Resolved a bug that could cause access rules for roles with the same name
  across different tenants to collide, ensuring each tenant's roles maintain their distinct access permissions.

### Changed

- 🔄 **Unified OpenWebUI Model Management**: OpenWebUI provisioning now seamlessly manages both AI-Hub agent models and
  newly introduced LLM workspace models, each with distinct prefixes and tailored access grant computations.
- 🖼️ **Enhanced Role Access Editor UI**: The Role Access Rules editor now features a dedicated "Models" category,
  providing a clearer and more intuitive interface for managing model-related permissions.

### Refactor

- 🧹 **Clearer OpenWebUI Model Prefixes**: Renamed the OpenWebUI model prefix for agents (`AIHUB_MODEL_PREFIX` to
  `AIHUB_AGENT_PREFIX`) to improve clarity and distinguish it from the new prefix used for LLM models.

______________________________________________________________________

## [v0.307.1] - 2026-07-07 - Seamless Multi-Agent Conversations: Dedicated Thread Contexts

### Fixed

- 🐛 **Multi-Agent Chat Context Interference**: Resolved an issue where multiple agents participating in the same chat
  session could inadvertently share or overwrite each other's conversation context, leading to incorrect or mixed-up
  responses.
- 🐛 **Agent-Specific Event Routing**: Corrected the internal event distribution logic to ensure messages are now
  precisely routed to the intended agent instance within a chat, preventing cross-agent communication mix-ups.

### Added

- ✨ **Multi-Agent Routing Tests**: Introduced new comprehensive tests to validate that distinct agents in a shared chat
  thread correctly maintain their separate contexts and respond independently.

### Changed

- 🔄 **Thread ID Salting for Agents/Models**: Updated the ID generation mechanism for chat threads to include agent or
  model identifiers as a "salt." This ensures unique thread IDs for each agent's or model's interaction within a single
  chat session, effectively isolating their operational context.
- ⚡️ **Targeted Event Distribution**: Modified the core event distributor to explicitly direct events to a specific
  `target_agent` when provided, enhancing precision and control over agent interactions and preventing unintended event
  broadcasts.

______________________________________________________________________

## [v0.307.0] - 2026-07-07 - Enhanced Model Access Control and Granular Permissions

### Added

- ✨ **New Model Permission Rules**: Introduced canonical permission rule builders and normalization logic within
  `AccessChecker` to precisely define and manage access to individual models and model capabilities.
- 🚀 **Centralized Model Access Guard**: Added new `_assert_model_access` and `_has_model_access` helper methods to
  `OpenaiService`, ensuring all model invocations enforce user permissions consistently at the service layer.
- 🧪 **Comprehensive Model Access Tests**: Added extensive unit tests for both `ModelService` and `OpenaiService` to
  validate the new granular model and assistant access control mechanisms.

### Security

- 🔑 **Granular Model Access Enforcement**: Implemented strict access control checks across all OpenAI API service
  methods (Chat Completions, Embeddings, Speech-to-Text, Text-to-Speech, Image Generation) to ensure users only access
  models for which they have explicit permissions.
- 🔐 **Filtered Model Listings**: The `/v1/models` and `ModelService` listing endpoints now filter available models based
  on the requesting user's granted permissions, only showing models they are authorized to use.
- 🛡️ **Improved Assistant Access Logic**: Refined the `chat_completion_with_assistants` and `get_model_with_assistants`
  endpoints to correctly differentiate and apply access checks for both models and assistants, raising `403 Forbidden`
  for unauthorized access.
- 🚫 **Prevented Permission Masking**: Modified model lookup fallback logic in `OpenaiService` so that only
  `404 Not Found` errors will trigger a search for an assistant; any other error, such as `403 Forbidden`, is now
  propagated directly.

### Refactor

- 🧹 **Centralized Access Control Logic**: Moved model and assistant access validation logic from the `OpenaiController`
  to the `OpenaiService`, ensuring a single source of truth for permission checks and simplifying controller logic.

______________________________________________________________________

## [v0.306.2] - 2026-07-06 - Refined LLM Parameter Defaults

### Changed

- ⚙️ **LLM parameter default value:** Adjusted the default value for a specific LLM parameter (e.g., temperature) from
  `0.1` to `0.0` to refine model configuration defaults and potentially promote more deterministic initial outputs.

______________________________________________________________________

## [v0.306.1] - 2026-07-02 - Improved Agent Form Reliability

### Fixed

- 🐛 **Agent configuration forms** now reliably preserve unsaved edits, preventing data loss even during background data
  refreshes or transient loading states.
- 🧩 **Agent creation forms** no longer reset user input when the selected agent class data is refreshed, ensuring a
  smoother creation process.
- 🔄 **Enhanced form stability** by preventing automatic refetches of agent class and instance data on window focus,
  safeguarding ongoing user input.

______________________________________________________________________

## [v0.306.0] - 2026-07-02 - Major Upgrade: Secure Open Terminal for OpenWebUI Code Interpreter

### Added

- 🦾 **Open Terminal Service**: Introduced a new `open-terminal` service dedicated to sandboxed code execution for
  OpenWebUI's plain LLM models. This new service offers per-user isolation and downloadable file output.
- 🔑 **`OPEN_TERMINAL_API_KEY`**: Added a new environment variable for authenticating OpenWebUI's connections to the Open
  Terminal sandbox, enhancing security.
- 🌐 **`code-sandbox` Network Zone**: Established a new, isolated Docker network specifically for the `open-terminal`
  sandbox and its direct callers (OpenWebUI), preventing lateral reach to other backend or data services.
- 📄 **Architectural Decision Record**: A detailed ADR (`2026_06_22_openwebui_code_execution_open_terminal.md`) was added
  to document the architectural shift from Jupyter to Open Terminal, outlining the rationale, decision, and
  consequences.
- ⚙️ **Open Terminal Dockerfile & Build Process**: Added a custom Dockerfile for `open-terminal` to include essential
  document-processing libraries (reportlab, fpdf2) and integrated its build and push into the deployment Makefile.

### Changed

- 🔄 **OpenWebUI Code Execution Backend**: OpenWebUI now exclusively uses the new `open-terminal` service for
  model-driven code execution, replacing the previous Jupyter integration.
- 📄 **Jupyter Role Clarification**: The Jupyter service is now explicitly designated as "retained in stack but no longer
  the OpenWebUI code path," signifying its deprecation for this use case.
- 🗺️ **Network Topology**: Updated the system's network architecture from five to six isolated Docker networks to
  incorporate the new `code-sandbox` zone, enhancing overall system isolation.
- 📚 **Documentation Updates**: Comprehensive revisions across the project documentation (skills, README, architecture,
  deployment guides, environment variables) to reflect the integration of Open Terminal, its features, and the updated
  network and deployment model.
- 🚦 **OpenWebUI Service Dependencies**: Changed OpenWebUI's health check dependency from `jupyter` to the new
  `open-terminal` service.

### Security

- 🔒 **Enhanced Code Execution Isolation**: Arbitrary user-submitted code executed via Open Terminal now runs in a
  dedicated `code-sandbox` network, which is internal (no outbound internet in non-dev stages) and only allows
  communication with its direct callers, significantly reducing the blast radius in case of a sandbox escape.
- 🛡️ **Per-User Sandbox Isolation**: The Open Terminal service is configured for multi-user support, providing separate
  Linux accounts and home directories for each user, improving data privacy and preventing users from accessing each
  other's files within the sandbox.

______________________________________________________________________

## [v0.305.8] - 2026-07-01 - Enhanced Mem0 Milvus Filtering

### Added

- ✨ Introduced **`PatchedMilvusDB`** to extend the filtering capabilities of mem0's Milvus vector store, enabling more
  complex query operations.
- 🧪 Added comprehensive **unit tests** for `PatchedMilvusDB` to ensure accurate and robust generation of Milvus query
  filters, especially for advanced operators.

### Fixed

- 🐛 Resolved an issue where **`mem0`'s MilvusDB vector store** failed to correctly process advanced metadata filters,
  particularly the `in` operator, which led to Milvus query parsing errors.

### Changed

- 🔄 The **`Mem0Service`** now integrates the `PatchedMilvusDB` wrapper for its internal Milvus vector store,
  transparently applying the enhanced filter logic.

______________________________________________________________________

## [v0.305.7] - 2026-07-01 - Streamlined Dataset Details UI

### Removed

- 🗑️ **Dataset Details Page:** Removed an unnecessary `ConfirmPopup` component from the dataset details view,
  simplifying the UI.

______________________________________________________________________

## [v0.305.6] - 2026-06-30 - Enhanced Document Processing and User Experience

### Added

- ✨ **Enhanced Document Page Counting:** The MarkItDown loader now accurately determines the page count for Microsoft
  Word (.docx), PowerPoint (.pptx), and Excel (.xlsx) files, providing more precise document metadata.
- 🚀 **Implemented File Upload Progress Tracking:** Users will now see real-time progress indicators during document
  uploads, improving visibility and user experience, especially for larger files.

______________________________________________________________________

## [v0.305.5] - 2026-06-30 - Enhanced CI/CD Workflow Resilience

### Fixed

- 🐛 **CI Workflow Failures:** Prevented potential CI/CD pipeline failures during Docker image pre-pull login by ensuring
  that an expired or absent GitHub token no longer causes the job to fail, significantly improving overall workflow
  stability.

### Changed

- 🔄 **Best-Effort Docker Login:** Modified the `ghcr.io` Docker login process in CI workflows to be best-effort; if
  authentication fails (e.g., due to an expired token), the system will now proceed with anonymous pulls for public
  images, guaranteeing job continuity.
- 📄 **Internal Documentation:** Updated internal documentation for GitHub Actions (`CLAUDE.md`) to explicitly reflect
  the new best-effort login behavior and its rationale, providing clearer guidance for pipeline operations.

______________________________________________________________________

## [v0.305.4] - 2026-06-30 - Improved Agent Configuration Stability

### Fixed

- 🐛 **Agent ID Immutability:** Corrected an issue where changes to an agent's **agent ID** during an update could lead
  to silent failures in real-time communication (SSE). The system now explicitly ensures the agent ID remains immutable,
  aligning with the instance key and preventing chat completion issues.
- 🖼️ **UI Enhancement:** Disabled the **agent ID** field in the agent configuration form on the web interface, clearly
  indicating its immutable nature and preventing users from inadvertently attempting to change it when editing an
  existing agent.

______________________________________________________________________

## [v0.305.3] - 2026-06-29 - Fortifying AI Agents Against Flaky LLM Structured Output

### Added

- 🦾 **Introduced `ResilientOpenAILike` for Robust LLM Interactions**: A new wrapper for `OpenAILike` models that
  automatically retries structured prediction calls multiple times. This significantly improves the reliability of
  agents interacting with Large Language Models (LLMs) that may intermittently produce malformed structured output.
- 📄 **New Architecture Decision Record (ADR) on Reasoning Model Resilience**: Documented the challenges with structured
  output from specific reasoning models (Kimi-K2.6, Qwen3.5) on Infomaniak and detailed the architectural decisions to
  mitigate these issues, including the adoption of plain-text verdicts and retry mechanisms.
- ⚡️ **New `text_verdict` Utility Module**: A dedicated module providing helpers for requesting and parsing plain-text
  verdicts from LLMs, which is now used by several guard and detection functions for improved reliability and speed.

### Changed

- 🔄 **Relevance Guards Now Use Plain-Text Verdicts**: The `agent_description_guard`, `few_shot_guard`, and
  `context_sufficient_guard` have been converted from expecting structured JSON output to requesting and parsing simple
  plain-text verdicts (e.g., `ALLOW`/`BLOCK`, `SUFFICIENT`/`INSUFFICIENT`). This change dramatically increases their
  reliability with reasoning models.
- 🚀 **Faster and More Reliable Meta-Question Detection**: The `detect_meta_question` function now uses a streamlined,
  single-token plain-text classification (e.g., `NORMAL`, `META_IDENTITY`) with reasoning disabled, reducing latency
  from ~4-5 seconds to sub-second on reasoning models without compromising accuracy.
- 🛡️ **Guards Fail Open on Unrecognizable Responses**: Relevance guards (`agent_description_guard`, `few_shot_guard`,
  `context_sufficient_guard`) now gracefully degrade by accepting a request if the LLM returns an unparseable verdict,
  preventing agent crashes and improving user experience.
- 💬 **Strict System Message Placement for Qwen3.5 Compatibility**: The `do_answer_meta_question` and `RAGAgent`'s
  guard-reject branch now ensure that system messages always lead the message list, resolving a
  `400 - System message must be at the beginning` error with Qwen3.5.
- ⚙️ **Centralized Retry Mechanism for All Structured Predictions**: All structured prediction calls are now routed
  through the new `ResilientOpenAILike` wrapper by default, providing a single point of failure mitigation for all
  agents without requiring individual call-site changes.

### Fixed

- 🐛 **Resolved Agent Crashes Due to Flaky LLM Structured Output**: Addressed a critical issue where agents would crash
  when reasoning models like Kimi-K2.6 or Qwen3.5 failed to produce reliably parseable structured output (e.g., empty
  tool calls, malformed JSON).
- 🔒 **Prevented Sensitive Information Leaks in Guard Logs**: Guard-failure logs no longer include raw model output,
  queries, or retrieved context, enhancing privacy and security.

______________________________________________________________________

## [v0.305.2] - 2026-06-29 - Enhanced Stability and Reliability

### Fixed

- 🐛 **Resolved infinite render loop** in the `DynamicConfiguration` component, preventing UI freezes and ensuring stable
  form interaction after data updates.
- ⏱️ **Improved `FewShotAgent` test reliability** by extending the test runner's delay, preventing premature test
  termination and accommodating longer execution times, especially in self-hosted LLM environments.

______________________________________________________________________

## [v0.305.1] - 2026-06-29 - Enhanced Form Data Stability

### Fixed

- 🐛 **Resolved dynamic form data mutation issues:** Implemented deep cloning during data hydration in the
  `DynamicConfiguration` component. This prevents FormKit's write-backs from inadvertently mutating shared cached
  objects (e.g., from Pinia-Colada) and eliminates potential infinite reactivity loops, leading to more stable and
  predictable form behavior.

______________________________________________________________________

## [v0.305.0] - 2026-06-26 - Simplifying Agent Workflows: Meta-Question Detection Removed

### Removed

- 🗑️ **Meta-question detection and answering functionality** has been completely removed from all agents (Expert RAG,
  Few-Shot, LLM Wrapping, MCP React, Namespace Selection, and RAG agents). This simplifies their internal architecture
  and streamlines execution by removing the initial classification step.
- 🗑️ **Associated event types and internal logic** related to meta-question handling, such as
  `MetaQuestionDetectedEvent` and `NotAMetaQuestionEvent`, have been deprecated from core agent events and the
  self-awareness module.
- 🗑️ **Dedicated test infrastructure** for meta-question routing, including specific feature scenarios and integration
  tests, has been removed in alignment with the deprecation of this functionality.

### Refactor

- 🧹 **Agent preconditions** for various steps (e.g., memory retrieval, chat history management) have been simplified by
  removing their dependency on meta-question detection logic, leading to more direct and efficient workflow execution.

______________________________________________________________________

## [v0.304.1] - 2026-06-26 - Temporary Adjustment to Agent Metadata Features

### Changed

- 🔄 **Conversation Metadata Generation Temporarily Disabled:** To enable further investigation and refinement, the
  automatic generation of conversation titles and follow-up questions has been temporarily paused across `RAGAgent`,
  `ExpertRAGAgent`, `FewShotAgent`, `LLMWrappingAgent`, and `McpReactAgent`. This aims to ensure a more robust and
  reliable agent experience in future iterations.

______________________________________________________________________

## [v0.304.0] - 2026-06-25 - Empowering Access Management: Introducing the Dynamic Capability Catalog

### Added

- ✨ **Dynamic Access Capability Catalog**: Introduced a powerful new system that generates a human-readable catalog of
  grantable capabilities directly from API endpoint permissions at runtime. This ensures that the displayed permissions
  always match what the system enforces, eliminating drift and simplifying authorization management for operators.
- 🔑 **Access Presets**: Added a curated library of common access rule combinations (presets) to facilitate one-click
  assignment of broad permissions like "Use everything" or "Administer all agents."
- 🦾 **`@access_catalog_entry` Decorator**: New decorator for API controllers, allowing endpoints to easily opt into the
  access capability catalog by providing localized labels and descriptions. The actual access rule is derived from the
  endpoint's `user_with_permission` guard, making divergence structurally impossible.
- ⚙️ **`AIHUB_INTERNAL_API_BASE_URL` Configuration**: Introduced a new environment variable and Docker Compose
  configuration to specify the internal base URL of the main platform API. This enables server-to-server communication,
  crucial for the sysadmin plane to proxy the full access capability catalog.
- 🧭 **Canonical Access Rule Builders**: Added static helper methods (`process_user_rule`, `service_admin_rule`, etc.) to
  `AccessChecker` for consistently building common permission templates, improving clarity and reducing errors.
- 📄 **New Architecture Decision Record (ADR)**: Documented the rationale and design behind the "Runtime-Derived Access
  Capability Catalog" to provide comprehensive context on this significant feature.
- 🌐 **Comprehensive Localization for Access Management**: Added extensive internationalization (i18n) support for the
  new access capabilities and presets, ensuring a localized experience for role and tenant-ceiling editors.
- 🧪 **Dedicated Access Capability Tests**: Introduced a new suite of unit and API tests to thoroughly validate the
  functionality and security of the access capability catalog, including sysadmin and tenant ceiling considerations.

### Changed

- 🔄 **Redesigned Role and User Access Views**: The UI for managing roles and viewing user access now leverages the new
  dynamic capability catalog, providing a detailed, hierarchical, and interactive representation of permissions instead
  of a flat list of rules.
- 🖼️ **User Access Information**: The `UserWithAccessDTO` now includes the user's resolved `access_rules` and utilizes
  the new `AccessCatalogService` to provide a more granular and accurate overview of effective access.
- 📚 **Documentation Updates**: Clarified guidelines for creating epics in the `write-issue` skill documentation and
  updated `CLAUDE.md` regarding generated files, reflecting recent development practices.
- 📝 **Agent, Process, Knowledge, and Memory Endpoints**: Existing controller methods across various services (e.g.,
  Agent, Process, Knowledge, Organization Memory, User Memory) have been updated with `@access_catalog_entry` decorators
  to expose their operations in the new access capability catalog.

### Refactor

- 🧹 **Unified User Access Logic**: Refactored the internal logic for building user access information, moving it into a
  dedicated `AccessCatalogService` to centralize and improve the consistency of access evaluation across different UI
  components.
- ⚙️ **Core AccessChecker Enhancements**: Updated `AccessChecker` to use new canonical rule-building methods, improving
  maintainability and consistency in permission checks.

______________________________________________________________________

## [v0.303.1] - 2026-06-24 - Superuser Configuration Streamlining

### Changed

- 📄 **Clarified Superuser Account Configuration:** The platform's superuser account now consistently uses
  `SUPERUSER_EMAIL` as its Keycloak username, aligning with Keycloak's `registrationEmailAsUsername` enforcement for
  login. The `SUPERUSER_USERNAME` variable has been re-designated as a log-only label for internal tracking, removing
  its previous role in setting the Keycloak username. This update simplifies superuser provisioning and enhances clarity
  in documentation across deployment guides and access control sections.

______________________________________________________________________

## [v0.303.0] - 2026-06-24 - Enhanced Image Generation Capabilities with Cloud Integration

### Added

- 🖼️ **New Cloud Image Generation Model:** Integrated the `image-generation/flux` model, enabling cloud-based image
  generation capabilities via the Swiss LLM Cloud.
- ⚙️ **Swiss LLM Cloud Image API Configuration:** Added new environment variables (`SWISS_LLM_CLOUD_IMAGE_API_BASE_URL`,
  `SWISS_LLM_CLOUD_IMAGE_API_KEY`) to configure access to the new image generation service.

### Changed

- 🚀 **Image Generation Model Prioritization:** Updated Docker Compose configurations to prioritize the new cloud-based
  `image-generation/flux` model for non-GPU environments.
- 📝 **Image Prompt Expansion Logic:** Disabled LLM-powered prompt expansion for image generation when using the `flux`
  model to accommodate its prompt length restrictions, ensuring raw prompts are passed directly.

### Removed

- 🗑️ **GPU-Specific Image Generation Model Placeholder:** Removed the generic `IMAGE_GENERATION_MODEL` setting from GPU
  deployment configurations, streamlining image generation to utilize the new cloud model for non-GPU stages while GPU
  stages await dedicated local integration.

______________________________________________________________________

## [v0.302.0] - 2026-06-24 - Smarter Conversations: Agents Now Generate Titles and Follow-up Questions

### Added

- 🦾 **Agent-Generated Conversation Metadata:** Agents now autonomously generate concise **conversation titles** (once
  per thread, when a clear topic emerges) and **suggested follow-up questions** (after each response), enriching the
  user experience by providing more contextual chat summaries and interaction prompts.
- 📄 **Architectural Decision Record for Conversation Metadata:** A new ADR
  (`2026_06_18_conversation_metadata_as_explicit_per_agent_steps.md`) has been added, detailing the design and
  implementation strategy for agents producing conversation titles and follow-up questions.
- ✨ **New Display Events for Conversation Metadata:** Introduced `ConversationTitleEvent` and `FollowUpQuestionsEvent`
  to transmit agent-generated metadata, ensuring these insights are seamlessly communicated through the event pipeline.
- 🚀 **Integration Across Key Agents:** The new conversation metadata generation has been integrated into several core
  conversational agents, including **RAGAgent**, **ExpertRAGAgent**, **LLMWrappingAgent**, **FewShotAgent**, and
  **McpReactAgent**, making these features widely available.
- 🌍 **Multilingual Prompts and UI Elements for Metadata:** Added comprehensive internationalization support for the new
  conversation metadata features, including prompts for title and follow-up question generation, and localized display
  names for the events in the UI.
- 🖼️ **Web UI Components for Conversation Metadata:** New web UI components (`ConversationTitleEvent.vue`,
  `FollowUpQuestionsEvent.vue`) have been added to visually display the agent-generated conversation titles and
  suggested follow-up questions to users.

### Changed

- 🔄 **Dynamic Thread Naming:** Conversation threads are now dynamically named by observing agent-generated
  `ConversationTitleEvent`s, replacing generic "chat" names with topic-relevant titles derived from the conversation
  content.
- ⚡️ **Enhanced Agent Workflows for Metadata:** Existing agent workflows have been updated to incorporate conversation
  metadata generation, either through dedicated `step` decorators for non-terminal LLM answers or inline calls for
  terminal stop events, ensuring robust, best-effort generation.
- 📡 **API and WebSocket Event Schema Updates:** The API and WebSocket event schemas have been extended to include the
  new `ConversationTitleEvent` and `FollowUpQuestionsEvent` within the `DisplayEvents` discriminated union, ensuring
  proper serialization and deserialization.

______________________________________________________________________

## [v0.301.7] - 2026-06-24 - Enhancements to Data Handling and Integration Consistency

### Fixed

- 🐛 **Improved Dataset Query Robustness:** Enhanced the dataset fetching logic to prevent errors by ensuring a dataset
  ID is present before attempting to retrieve data, leading to a more stable user experience.

### Refactor

- 🧹 **Standardized Langfuse Configuration:** Aligned the Langfuse integration with the latest SDK conventions by
  updating the host parameter name, improving internal consistency and maintainability.

______________________________________________________________________

## [v0.301.6] - 2026-06-23 - Improved OpenWebUI SCIM Client for Complete Data Sync

### Fixed

- 🐛 **Incomplete OpenWebUI SCIM Data Retrieval:** Resolved an issue where the OpenWebUI client would only retrieve the
  first page of users or groups from the SCIM API, leading to incomplete data synchronization. The client now correctly
  fetches all resources across multiple pages.

### Added

- ✨ **SCIM Pagination Mechanism:** Introduced a robust pagination logic (`_query_all`) for the OpenWebUI SCIM client,
  ensuring all users and groups are retrieved, even when they span multiple pages.
- 🧪 **Comprehensive SCIM Pagination Tests:** Added new unit tests to thoroughly validate the SCIM pagination logic,
  covering multi-page retrieval, server-capped page sizes, and scenarios where `totalResults` is omitted.

### Changed

- 🔄 **Updated SCIM Resource Listing:** Modified `list_users` and `list_groups` methods to leverage the new pagination
  mechanism, ensuring they always return a complete list of all users and groups from OpenWebUI.
- 🔒 **Idempotent Group Creation Scan:** Enhanced the `create_group` method's check for existing groups to scan across
  all SCIM pages, preventing duplicate group creation when the target group resides on a subsequent page.

______________________________________________________________________

## [v0.301.5] - 2026-06-22 - Agent Event API Refinements and Structural Updates

### Changed

- 🔄 **Event API Streamlining:** Refactored the core event system, consolidating various agent-related events such as
  `UserMessageEvent`, `LLMStopEvent`, `StopEvent`, `RetrieverEvent`, and `BotInTheLoop` into a unified
  `swiss_ai_hub.core.events.agent` module for improved organization and discoverability.
- ⚡️ **Enhanced Guard Event Clarity:** Renamed `ContextSufficientEvent` to **`ContextSufficientAcceptEvent`** and
  `ContextInsufficientEvent` to **`ContextInsufficientRejectEvent`** to explicitly communicate their acceptance or
  rejection semantics, making agent logic clearer.
- 📂 **Module Structure Alignment:** Relocated core components like `AgentConfig` and `KnowledgeRetriever` to more
  logical paths within the `swiss_ai_hub.core` and `swiss_ai_hub.core.generative_ai` modules, respectively, enhancing
  the overall package structure.
- 📄 **Updated Documentation Examples:** Modified the `README.md` example to reflect the latest event names and module
  paths, ensuring up-to-date guidance for agent development.

______________________________________________________________________

## [v0.301.4] - 2026-06-22 - Enhanced Infrastructure Image Sourcing and Configuration

### Added

- ✨ **Introduced `Open WebUI Init` Service Configuration:** Added explicit image tag definition and usage for the
  `Open WebUI Init` service, enabling central management of its PostgreSQL base image.

### Changed

- 🔄 **Standardized Third-Party Image Sourcing:** Implemented consistent registry prefixing for several critical
  third-party Docker images, including **`OpenTelemetry Collector`**, **`rclone`**, **`Speaches`**, and
  **`Docker Socket Proxy`**, to ensure all images are sourced from the designated internal registry.
- ⚡️ **Updated `OpenTelemetry Collector` Image:** Pinned the `OpenTelemetry Collector` image to a specific version
  (`0.154.0`) for improved stability and security.
- 📄 **Refined `OpenWebUI Init` License Alias:** Updated the internal license alias mapping for the `OpenWebUI Init`
  service to accurately reflect its `postgres` base image.

### Refactor

- 🧹 **Standardized `Keycloak Config CLI` Variable Name:** Renamed the internal configuration variable for
  `Keycloak Config CLI` to `keycloak_config_cli` (snake_case) for improved consistency across the deployment
  configuration.

______________________________________________________________________

## [v0.301.3] - 2026-06-22 - Keycloak Superuser Configuration Alignment

### Changed

- ⚙️ **Keycloak Superuser Configuration:** Standardized the superuser's username in Keycloak realms and bootstrap
  configurations to consistently use the `SUPERUSER_EMAIL` environment variable instead of `SUPERUSER_USERNAME`.

______________________________________________________________________

## [v0.301.2] - 2026-06-22 - Default Chat TTS Permission Adjustment

### Changed

- 🎚️ **Updated Default Chat TTS Permission:** The default setting for Text-to-Speech (TTS) functionality in chat has
  been changed from enabled (`True`) to disabled (`False`) across all Docker Compose configurations. Users can still
  explicitly enable this permission if desired.

______________________________________________________________________

## [v0.301.1] - 2026-06-19 - Enhanced Router Stability and Dependency Management

### Fixed

- 🐛 **Ensured `vue-router` Consistency:** Addressed critical runtime errors, such as
  `TypeError: Invalid value used as weak map key` and `useRouter()` returning `undefined`, which occurred due to
  `@vueuse/router` resolving to a different major version of `vue-router` than the Nuxt application. This is resolved by
  explicitly declaring `vue-router@4.6.4` as a direct dependency, guaranteeing consistent injection keys.
- 📄 **Updated `vue-router` Pinning Guidance:** Significantly updated the `README.md` with crucial instructions on how to
  reliably pin `vue-router` as a direct dependency. This new guidance clarifies why previous override methods were
  insufficient and provides a robust solution to prevent dependency resolution conflicts and ensure application
  stability.

______________________________________________________________________

## [v0.301.0] - 2026-06-19 - Enhanced OpenWebUI Agent Display Names with Locale Support

### Added

- ✨ **New Environment Variable `OPENWEBUI_MODEL_NAME_LOCALE`**: Introduced to allow configuring the preferred locale for
  displaying agent names within OpenWebUI, providing a more localized user experience.
- 🌍 **Locale-Aware Agent Display Names**: Implemented the ability for OpenWebUI to resolve and display agent names based
  on the configured locale, with intelligent fallbacks to other available translations or the agent ID.
- 🔄 **OpenWebUI Workspace Model Update Capability**: Added functionality to the OpenWebUI provisioner to update existing
  workspace models, specifically enabling seamless name changes in response to agent renames or locale adjustments.

### Changed

- 🚀 **OpenWebUI Agent Discovery Language Negotiation**: The OpenWebUI `aihub_pipeline` now includes an `Accept-Language`
  header during agent discovery API calls, ensuring that agent details are fetched in the configured locale.
- 📡 **Robust Agent Name Synchronization**: The agent synchronization mechanism has been enhanced to detect and propagate
  changes to agent names, ensuring that OpenWebUI workspace models accurately reflect the latest, locale-resolved agent
  names.
- 🛠️ **Agent Hash Calculation**: The algorithm for computing agent hashes now incorporates the agent's display name,
  making synchronization more sensitive to name-only changes and preventing stale entries in OpenWebUI.

### Refactor

- 🧹 **Streamlined OpenWebUI Model Reconciliation**: The logic for determining changes in OpenWebUI workspace models has
  been refined to explicitly distinguish between models that need to be created, updated, or deleted, improving
  provisioning efficiency and clarity.

______________________________________________________________________

## [v0.300.4] - 2026-06-18 - Improved Data Lake Partition Naming for Enhanced Isolation

### Fixed

- 🐛 **Resolved `DynamicPartitionsDefinition` Name Collisions**: Updated the `default_rclone_to_datalake_definitions`
  utility to dynamically generate unique names for `DynamicPartitionsDefinition` instances. This prevents unintended
  sharing of partition state when multiple rclone-backed sources are registered in the same Dagster instance, ensuring
  proper data isolation.

### Added

- 📄 **Documented Partition Naming Conventions**: Added clear guidelines for `DynamicPartitionsDefinition` naming,
  emphasizing the importance of deriving unique names from the data lake container and source to prevent state
  collisions.
- 🧪 **Introduced Partition Naming Regression Test**: Added a new test case to verify that
  `default_rclone_to_datalake_definitions` correctly produces distinct partition definition names, safeguarding against
  future naming conflicts.

______________________________________________________________________

## [v0.300.3] - 2026-06-18 - Package Version Synchronization

### Changed

- 🔄 **Synchronized Package Versions:** All core Python packages (`agent`, `api`, `backup`, `bot`, `core`, `meta`,
  `pipeline`, `process`, `sysadmin-api`) and JavaScript packages (`sysadmin-web`, `web`) have been updated to
  `v0.300.3`. This ensures consistent versioning across the entire Swiss AI Hub platform.

______________________________________________________________________

## [v0.300.2] - 2026-06-18 - Homepage Navigation Refinement

### Changed

- 📄 **Updated Platform Overview Navigation:** Streamlined the "Platform Overview" link on the homepage for both English
  and German versions, directing users to the broader architecture section for an improved overview of platform
  documentation.

______________________________________________________________________

## [v0.300.1] - 2026-06-17 - Enhanced User Interface Accessibility

### Changed

- ♿️ **Improved UI Accessibility:** Added `aria-label` attributes to numerous interactive components across the
  application, including various `Select` dropdowns, `Textarea` inputs, `InputText` fields, and file upload inputs. This
  enhancement significantly improves the experience for users relying on screen readers and other assistive technologies
  by providing clearer context for UI elements.
- ⚙️ **Refined Form Element Identification:** Updated and added `id` attributes to select form components, ensuring
  better programmatic identification and improved accessibility.
- 🌐 **Expanded Internationalization:** Introduced new placeholder translations for chat inputs
  (`thread.chat.placeholder`) across multiple languages (German, English, French, Italian) to support enhanced UI
  descriptions.

______________________________________________________________________

## [v0.300.0] - 2026-06-17 - Streamlined Agent Instance Management with Auto-Granted Creator Access

### Added

- 🚀 **Automated Creator Access for Agent Instances**: Tenant administrators can now create agent instances and
  immediately gain full admin access (open, edit, delete, chat) without requiring manual intervention from a sysadmin.
  This significantly improves the self-service capabilities for agent instance management.
- 📄 **Architectural Decision Record (ADR)**: A new ADR has been added, documenting the decision for automatically
  granting per-instance access to creators and detailing the context, drivers, decision, and consequences.
- 🔑 **New Access Control Helpers**: Introduced dedicated `AccessChecker` methods (`agent_instance_admin_rule`,
  `agent_instance_user_rule`, `rules_grant_admin_to_agent_instance`) to precisely manage and evaluate instance-level
  permissions.
- 🦾 **Persistence Utilities for Access Management**: Added robust utility methods including
  `TenantMetadataEntity.grant_access_rule`, `TenantMetadataEntity.revoke_access_rule_from_all_tenants`, and
  `RoleEntity.delete_role_from_all_tenants` for managing tenant access ceilings and dedicated per-instance roles.
- ✅ **Comprehensive Test Coverage**: Included extensive unit and integration tests to ensure the reliability and
  correctness of the new auto-grant and cleanup mechanisms for agent instance access.

### Changed

- 🔄 **Updated Agent Instance Lifecycle in API**: The `AgentService` now orchestrates the automatic granting of
  per-instance admin access during agent instance creation and performs thorough cleanup of associated access rules and
  roles upon deletion, including a rollback mechanism for failed grants.
- ⚡️ **Improved Frontend Cache Synchronization**: Frontend components now automatically invalidate relevant caches
  (agent instances, tenant roles, user profiles) after creating or deleting agent instances, ensuring immediate
  reflection of access changes in the UI.
- 🖼️ **Enhanced Agent List Display Logic**: Refined the display of agent groups and empty states on the agents page,
  improving user experience when applying filters or viewing available agent classes.

### Refactor

- 🧹 **Standardized Agent Rule Generation**: The `AccessChecker` now uses dedicated helper methods to generate canonical
  user and admin rules for agent instances, improving consistency and maintainability of access control logic.

______________________________________________________________________

## [v0.299.0] - 2026-06-17 - Streamlined Keycloak Management and Expanded LLM Support

### Added

- ✨ New LLM models, **Fable** and **Fable 1M**, are now available for use.
- 🚀 A new `keycloak-config` service has been introduced to enable declarative, idempotent management of Keycloak realm
  configurations, ensuring consistency across deployments.
- 📄 A new Architecture Decision Record (ADR) detailing the **Declarative Keycloak Realm Reconciliation** outlines the
  strategy for the updated configuration management system.
- 📦 Keycloak configuration templates are now organized into `bootstrap/` (first-start only) and `managed/` (reconciled
  on every start) directories for clearer lifecycle management.

### Changed

- 🔄 The **Keycloak configuration management** workflow has been fundamentally revised, transitioning from mixed
  first-start imports and imperative `kcadm` scripts to a fully declarative approach using the new `keycloak-config`
  service.
- 📄 **Keycloak documentation** has been extensively updated to clearly define the new two-phase configuration lifecycle
  (bootstrap vs. managed) and its implications for operators, including how changes are applied and maintained.
- 🔑 **Azure Entra ID setup instructions** for platform roles have been clarified, specifying that `AIHubAccess` and
  `AIHubSysAdmin` are the only Keycloak realm roles to be mapped from the Identity Provider. Other platform roles are
  now explicitly stated to be managed internally by the platform.
- 🔐 Access to **SeaweedFS Filer** and other admin tool UIs now consistently requires the `AIHubSysAdmin` realm role,
  enhancing security and aligning access control across administrative interfaces.
- 📚 The **Environment Variables documentation** has been thoroughly revised to reflect the new Keycloak configuration
  structure and the services consuming each variable.
- 📝 German documentation for **Platform vs. SDK** and the **Ecosystem Model** has been updated with minor wording
  improvements and corrected license references to `AGPL-3.0-or-later`.

### Removed

- 🗑️ The monolithic `keycloak-realm.json.j2` and `keycloak-identity-providers.json.j2` templates have been retired,
  replaced by the new modular `bootstrap/` and `managed/` Keycloak configuration files.
- 🗑️ Imperative `kcadm` commands for identity provider and Langfuse sysadmin gate reconciliation have been removed from
  the `keycloak-entrypoint.sh` script, as these are now handled declaratively by the `keycloak-config` service.

### Refactor

- 🧹 The **Keycloak entrypoint script (`keycloak-entrypoint.sh`)** has been significantly simplified by delegating
  managed configuration reconciliation to the `keycloak-config` service.
- 🛠️ The internal `generate_compose.py` tooling has been refactored to support the new modular Keycloak configuration
  structure, including logic to merge bootstrap and managed documents for the initial realm import.
- ⚙️ Keycloak's realm definition has been restructured across multiple, smaller JSON files within `bootstrap/` and
  `managed/` to improve modularity and maintainability.

______________________________________________________________________

## [v0.298.3] - 2026-06-16 - Configuration Forms: Robustness and User Experience Improvements

### Fixed

- 🐛 **Configuration Form Defaults:** Resolved an issue where nullable fields with default values were not correctly
  initialized on new form creation, leading to silent data loss of defaults. Forms now consistently apply declared
  default values, ensuring a predictable user experience.
- 🐛 **Repeater Row Stability:** Eliminated data corruption and UI inconsistencies in repeater components by implementing
  stable, unique keys for each row. This prevents issues caused by re-indexing when non-last rows are removed from a
  list.
- 🐛 **Fractional Input Fields:** Corrected the behavior of numeric input fields (`InputNumber`) to properly accept and
  display decimal values for fractional properties (e.g., LLM `temperature`), which previously rejected decimal points.
- 🐛 **Form Rendering Robustness:** Enhanced the dynamic form builder to handle malformed schema elements gracefully. A
  single invalid field will now be skipped and logged without causing the entire form section to disappear or become
  unusable.
- 🐛 **UI Performance & Stability:** Addressed intermittent blank or broken form displays by refactoring label and option
  resolvers to use synchronous case conversion, eliminating reactive effect leakage and improving rendering stability.

### Changed

- 🔄 **Unified Form Data Handling:** The agent and process configuration forms now utilize a single, consistent pipeline
  for hydrating initial data and serializing submissions. This ensures identical behavior and data integrity across both
  creation and editing workflows.
- 📄 **Nullable Field Toggle Logic:** Extended the backend form schema to include a `default_enabled` flag for nullable
  elements. This accurately indicates whether a field with a non-null default value should appear enabled by default on
  a fresh form.
- ⚡️ **Symmetric Backend Normalization:** Agent and process creation endpoints now apply the same server-side
  configuration normalization as update operations. This prevents internal UI artifacts (like FormKit `__validate__`
  keys) from persisting in the configuration data.

### Refactor

- 🧹 **Case Conversion Utility:** Replaced the `useChangeCase` composable with a direct, synchronous `capitalCase`
  utility across various UI components, contributing to the overall stability and performance of form rendering.

______________________________________________________________________

## [v0.298.2] - 2026-06-16 - Documentation Site Migration to Custom Domain

### Added

- 📄 **Custom Domain Configuration:** Integrated support for a custom domain (`docs.ai-hub.bbv.ch`) for the documentation
  site, enhancing branding and direct access.
- 🌐 **Sitemap Generation:** Enabled sitemap generation for the documentation portal, improving search engine
  optimization and content discoverability.
- 🤖 **Crawler Access:** Updated the `robots.txt` file to allow web crawlers to access and index the entire documentation
  site.

### Changed

- 🚀 **Documentation Base Path:** Modified the documentation site's base path to be served from the root `/` (instead of
  `/aihub-core/`), aligning with the new custom domain setup.
- 🔗 **Live URL and Deployment Details:** Revised internal configuration and documentation to reflect the new live URL
  (`https://docs.ai-hub.bbv.ch/`) and updated deployment specifics.

______________________________________________________________________

## [v0.298.1] - 2026-06-16 - Enhanced Agent List Display and Filtering

### Changed

- 🖼️ **Refined Agent Group Display:** The Agents page now intelligently shows or hides agent group headers based on
  active filters. When filters are applied, only groups with instances matching the criteria will display a header,
  providing a cleaner and more relevant overview. When no filters are active, all available agent classes will show
  their headers.

______________________________________________________________________

## [v0.298.0] - 2026-06-16 - Introducing Document Deletion and Enhanced Management for Knowledge Bases

### Added

- ✨ **Document Deletion API Endpoints:** Introduced new API endpoints for deleting individual documents and performing
  batch deletions from knowledge bases.
- 🗑️ **Core S3 File Deletion:** Added foundational S3 service capabilities to permanently remove source files from data
  lakes as part of the document deletion process.
- 🚀 **Asynchronous Document Cleanup:** Implemented service logic to schedule the cleanup of document and vector stores
  via pipeline reconciliation after a document's source file is removed.
- 📄 **Batch Deletion Data Transfer Objects:** Introduced new DTOs for requests and responses to support the new batch
  document deletion functionality, providing clear status for each document.
- 🖼️ **Interactive Document Deletion UI:** Added user interface elements to the document list for both single and
  multi-select document deletion, including confirmation dialogs and progress indicators.
- ⚡️ **Real-time Deletion Status Tracking:** Developed front-end composables to manage the state of scheduled document
  deletions, providing visual feedback to users even after page refreshes.
- 🌐 **Localized Deletion Messages:** Integrated comprehensive localization for all new document deletion features across
  multiple languages.
- 🧪 **Extensive Deletion Service Tests:** Added a new suite of unit tests to ensure the reliability and correctness of
  the knowledge document deletion service.

### Fixed

- 🐛 **Robust Metadata Table Generation:** Corrected an issue in the pipeline's metadata utility to ensure consistent and
  valid table structures when displaying heterogeneous document metadata, preventing errors in Dagster reports.

### Changed

- 🔄 **Updated Document List Experience:** Enhanced the document list to clearly indicate documents pending deletion and
  integrated hooks for refreshing data after deletion events.
- ✍️ **Clarified Source Update Event Purpose:** Updated the documentation for the `SourceUpdatedEvent` to explicitly
  state its role in triggering both ingestion and cleanup processes within the pipeline.

### Refactor

- 🧹 **Standardized S3 URI Handling:** Centralized the definition and usage of the S3 URI scheme within the knowledge
  service for improved consistency and maintainability.

______________________________________________________________________

## [v0.297.9] - 2026-06-16 - Streamlined Agent Evaluations with Enhanced Langfuse Integration

### Changed

- 🔄 **Updated Agent Evaluation Workflow:** The agent evaluation process has been re-architected to deeply integrate with
  **Langfuse**, establishing it as the primary platform for conducting experiments and managing evaluators. The Swiss AI
  Hub now auto-provisions all necessary components for a seamless Langfuse experience.
- 📄 **Revised Evaluation Documentation:** The comprehensive documentation for agent evaluations has been completely
  updated to guide users through the new Langfuse-centric workflow, detailing how to create datasets, configure
  evaluators, and execute experiments effectively.
- ⚡️ **Simplified Evaluator Configuration:** The documentation for creating evaluators has been streamlined, emphasizing
  recommended scoring dimensions and highlighting the auto-provisioned LLM connection for judge models directly within
  Langfuse.

### Removed

- 🗑️ **Deprecated Experiment UI Images:** Outdated screenshots depicting the previous in-platform UI for running
  experiments have been removed to align with the new Langfuse-based evaluation workflow.

______________________________________________________________________

## [v0.297.8] - 2026-06-16 - Refined Localization and Translation Capabilities

### Changed

- ✨ **Enhanced Locale String Handling:** The `LocaleString` utility has been significantly improved with a more robust
  `in_locale` method, now offering intelligent fallback logic to ensure the best available translation is always
  retrieved. This includes prioritizing the exact requested locale, falling back to a default, and then to other
  available languages.
- 🔄 **Precision in Translation Service:** The `TranslationService` now explicitly requests translations for the exact
  source locale without automatic fallbacks, ensuring greater control and precision in the translation process,
  leveraging the new `LocaleString` enhancements.

### Added

- ✅ **Expanded Unit Tests for Localization:** New, comprehensive unit tests have been introduced for the `LocaleString`
  class, rigorously validating the new fallback logic and precise locale retrieval mechanisms to ensure the reliability
  of internationalization features.

______________________________________________________________________

## [v0.297.7] - 2026-06-16 - Dashboard UI and Chart Display Improvements

### Fixed

- 🖼️ **Dashboard Grid Filters:** Resolved potential display and layering issues for dropdown menus within the
  **Dashboard Grid** by ensuring proper rendering of event data type and agent selection options.
- 📈 **Event Timeseries Chart:** Enhanced the visual layout and readability of the **Event Timeseries Chart** by
  fine-tuning chart and data label vertical positioning, including responsive adjustments for smaller screens.

______________________________________________________________________

## [v0.297.6] - 2026-06-16 - Strengthened OpenWebUI Group Management and Sync Reliability

### Added

- 📄 **Improved logging:** Added logging capabilities to the OpenWebUI client for better operational visibility during
  interactions with the OpenWebUI API.

### Fixed

- 🐛 **Prevented duplicate OpenWebUI groups:** The `create_group` operation is now idempotent. It intelligently reuses an
  existing OpenWebUI group if one with the same display name is found, preventing the creation of duplicate groups that
  could disrupt role-to-group synchronization.
- 🔐 **Enhanced group synchronization reliability:** Implemented a dedicated, blocking Redis lock for OpenWebUI group
  reconciliation. This prevents concurrent synchronization processes from creating duplicate groups or causing
  inconsistent states, ensuring robust group management.
- ⚡️ **Increased group sync lock timeout:** The maximum duration for the group synchronization lock has been
  significantly extended from 60 to 600 seconds. This prevents premature lock expiration for potentially long-running
  group reconciliation operations on large tenants.

### Changed

- 🔄 **Improved Redis lock robustness:** The Redis lock acquisition and release mechanism has been enhanced to gracefully
  handle scenarios where a lock auto-expires before it can be explicitly released. This prevents failures and provides
  warnings for better operational insights.

### Refactor

- 🧹 **Refactored group synchronization logic:** The core group reconciliation logic within the provisioner has been
  extracted into a new method (`_sync_groups_locked`), improving code clarity and better isolating the critical section
  protected by the dedicated synchronization lock.

______________________________________________________________________

## [v0.297.5] - 2026-06-15 - Enhanced Error Reporting for Clearer Notifications

### Fixed

- 🐛 **Improved Error Message Display:** Enhanced the client-side error handling to correctly parse and display detailed
  error messages received as arrays, ensuring users receive comprehensive and readable notifications in toast alerts.

______________________________________________________________________

## [v0.297.4] - 2026-06-15 - Enhanced Empty State Feedback

### Added

- ✨ **Improved Empty State Feedback:** Introduced clear "no results" messages for the Processes, Memory Graph, and
  Memory List pages, ensuring users receive visual feedback when no items are available.
- 📄 **New Localization Strings:** Added new translation keys for "no results" messages across multiple languages
  (German, English, French, Italian) to support the improved empty state feedback.

______________________________________________________________________

## [v0.297.3] - 2026-06-15 - Streamlined Sysadmin Tenant Routing

### Changed

- 🔄 **Simplified Sysadmin Tenant Paths:** The `/sysadmin` URL prefix has been removed from all tenant administration
  routes. Sysadmin functionality is now directly accessible under `/tenants`, making the URL structure more concise and
  aligned with the sysadmin application's primary function.
- 🧹 **Refined `useTenantPath` Logic:** The `useTenantPath` composable now explicitly focuses on generating paths for
  tenant-scoped `/[tenant]/...` routes. Sysadmin routes (`/tenants/...`) are now treated as absolute and no longer
  require dynamic tenant injection through this composable, clarifying and streamlining path generation logic.
- 📄 **Updated Sysadmin Documentation:** The project documentation has been updated to reflect the new, simplified
  sysadmin routing structure, providing clearer guidance on tenant administration paths.

______________________________________________________________________

## [v0.297.2] - 2026-06-15 - Improved LiteLLM User & Key Management

### Fixed

- 🐛 **Enhanced LiteLLM provisioning resilience:** Improved the user and API key generation process to gracefully handle
  concurrent requests and race conditions by treating `409 Conflict` responses for user or key creation as successful,
  pre-existing entities. This makes the service more robust in high-concurrency environments.

### Refactor

- 🧹 **Streamlined LiteLLM key provisioning:** The internal logic for managing LiteLLM users and API keys has been
  refactored into distinct, more focused methods (`_create_user_if_absent`, `_generate_key`) to improve clarity,
  maintainability, and error handling.

### Added

- 🧪 **Comprehensive LiteLLM service unit tests:** Introduced a new suite of unit tests for the `LiteLLMService` covering
  various scenarios, including existing users, new user creation, and handling of concurrency conflicts during user and
  key provisioning.

______________________________________________________________________

## [v0.297.1] - 2026-06-15 - Stricter Langfuse Access Control and Local Dev Setup Enhancements

### Security

- 🔑 **Restricted Langfuse UI Access:** Implemented Keycloak-level access control for the Langfuse UI, ensuring that only
  users with the `AIHubSysAdmin` realm role can log in. This prevents unauthorized users from viewing sensitive trace
  data by denying access directly at the Keycloak login flow.
- 🔑 **Idempotent Keycloak Flow Reconciliation:** Added robust scripting to the Keycloak entrypoint that idempotently
  applies authentication flow configurations, including the new Langfuse access gate, on every container start. This
  ensures security policies are consistently enforced across all deployments, especially existing ones.
- 📄 **Documented Langfuse Sysadmin Gate:** Introduced new architecture decision records (ADRs) and comprehensive
  deep-dive documentation explaining the detailed mechanism, rationale, and structural rules for the Langfuse sysadmin
  gate within Keycloak.
- 📄 **Updated Observability and Authentication Documentation:** Enhanced platform documentation in both English and
  German to clearly reflect the new Langfuse access restrictions and the role of the `AIHubSysAdmin` in controlling
  access to administrative tools.

### Fixed

- 🐛 **Langfuse OIDC Callback in Local Environments:** Resolved an issue where Langfuse's OIDC backchannel to Keycloak
  would fail in local and build environments when using self-signed `mkcert` certificates. The Langfuse container now
  correctly trusts the `mkcert` root CA, allowing successful OIDC authentication.

### Added

- 🛠️ **Automated `mkcert` Root CA Copy:** The `make local-cert` command now automatically copies the `mkcert` root CA
  certificate into the Traefik certificates directory, streamlining local development setup for secure communication.
- 📄 **Keycloak Configuration Deep-Dive:** Added new, comprehensive documentation sections providing an overview of the
  `aihub` Keycloak realm, including its clients, scopes, roles, tenant groups, identity brokering, and the mechanisms by
  which configuration changes are applied to running instances.

### Changed

- ⚙️ **Keycloak Realm Configuration Update:** Modified the Keycloak realm configuration across all deployment stages to
  bind a custom browser flow and introduce a new marker client scope (`langfuse-sysadmin-gate`), enabling the
  conditional access denial logic for Langfuse.
- 🧹 **Documentation Sync Exclusions:** Updated the documentation synchronization script and `.gitignore` to specifically
  preserve hand-authored Keycloak configuration deep-dive documentation sections during automated content updates.

### Refactor

- 📄 **Minor Documentation Adjustments:** Performed various minor formatting and wording adjustments across several
  existing documentation files to improve clarity and readability.

______________________________________________________________________

## [v0.297.0] - 2026-06-15 - Self-Aware Agents: Sm🧠rter Conversations and Robust Workflows

### Added

- 🦾 **Agent Self-Awareness Feature:** Introduced the ability for conversational agents to detect and answer
  meta-questions about themselves (e.g., "What can you do?", "Who are you?") based on their identity, capabilities, and
  behavior, instead of running their normal pipeline.
- ✨ **New Self-Awareness Events:** Created `MetaQuestionDetectedEvent` to signal when a user's query is a meta-question
  about the agent, and `NotAMetaQuestionEvent` to act as an "all-clear" gate, releasing the agent's normal workflow.
- 💬 **Localized Meta-Question Handling:** Added comprehensive i18n support for self-awareness steps, detection prompts,
  and answer prompts, enabling agents to respond to meta-questions in multiple languages.
- 📄 **Workflow Mermaid Flowchart Generation:** Implemented a new utility to generate Mermaid flowcharts of an agent's
  workflow (excluding self-awareness steps) to help ground the agent's answers to meta-questions about its processes.
- 🧪 **Comprehensive Self-Awareness Testing:** Introduced a suite of unit and integration tests, including a compliance
  test, to ensure self-awareness features are correctly wired into conversational agents and prevent common pitfalls
  like race conditions.
- 🖼️ **UI Support for Meta-Question Events:** Added a new Vue component to display `MetaQuestionDetectedEvent` in the
  UI, providing visual feedback when an agent is handling a meta-question.

### Changed

- 🔄 **Conversational Agents Integrated with Self-Awareness:** The `RAGAgent`, `ExpertRAGAgent`, `FewShotAgent`,
  `LLMWrappingAgent`, `McpReactAgent`, and `NamespaceSelectionAgent` blueprints now explicitly define steps for
  detecting and answering meta-questions, and their entry points are gated to prevent conflicts.
- 📝 **Updated Agent Documentation and Guidance:** Refreshed the `SKILL.md` and `CLAUDE.md` documents with detailed
  guidelines on integrating and testing self-awareness in new and existing conversational agents.

### Fixed

- 🐛 **Robust Chat History Limiting:** Enhanced the chat history limiting mechanism to proactively filter out empty chat
  messages, preventing potential 400 errors from LLM providers and improving overall agent reliability.

### Refactor

- 🧹 **Decoupled Self-Awareness Implementation:** Architecturally decided to implement self-awareness as explicit,
  per-agent steps rather than a shared base-class mixin. This keeps agent workflows transparent and avoids invasive
  changes to core `Agent` machinery, ensuring cleaner integration and easier debugging.

______________________________________________________________________

## [v0.296.5] - 2026-06-15 - Improved RAG Agent Context Persistence for Follow-up Questions

### Fixed

- 🐛 **RAG Agent follow-up context loss**: Addressed a critical bug where the RAG agent would fail to answer affirmative
  replies to offered follow-up questions due to the loss of essential grounding context between conversation turns.

### Added

- ✨ **Grounding node persistence**: Introduced a new mechanism to automatically persist and carry over the most relevant
  grounding documents from a previous turn into the current conversation turn, ensuring continuous context for follow-up
  questions.
- 📄 **`grounding_nodes` to `InOrderNodeCombinerEvent`**: Added a new field to the `InOrderNodeCombinerEvent` to
  explicitly track and expose the complete set of nodes (comprising both fresh retrieval and carried prior-turn nodes)
  that collectively ground the agent's answer.
- 🚀 **Dedicated RAG agent steps**: Implemented new workflow steps (`persist_grounding_nodes_step`,
  `do_read_carried_grounding_nodes`, `do_persist_grounding_nodes`) within the RAG agent to manage the lifecycle and
  integration of carried grounding nodes.
- 🧪 **Regression test for follow-up affirmation**: Introduced a comprehensive regression test to validate the fix and
  prevent future regressions related to context retention in multi-turn follow-up scenarios.

### Changed

- 🔄 **Enhanced context combination logic**: Modified the `order_nodes_by_documents_step` to seamlessly integrate carried
  grounding nodes alongside newly retrieved content, creating a more robust and complete context for generating
  responses to follow-up questions.

______________________________________________________________________

## [v0.296.4] - 2026-06-15 - Enhanced LLM Parameter Precision

### Changed

- 🎨 Improved the display precision of the **LLM temperature parameter** slider in the UI, ensuring it shows a maximum of
  one decimal place for better readability and user experience.

______________________________________________________________________

## [v0.296.3] - 2026-06-15 - Enhanced Prompt Configuration for Agents and Steps

### Changed

- 🔗 **Mandatory System Prompts:** The `system_prompt` field for both the **`LLMWrappingAgent`** and **`FewShotStep`** is
  now mandatory, ensuring that these components always have a defined behavioral context.
- 📄 **LLMWrappingAgent Prompt Clarity:** The description for the **`LLMWrappingAgent`'s system prompt** has been updated
  to more accurately reflect its purpose in setting the agent's behavior for the wrapped LLM.

______________________________________________________________________

## [v0.296.2] - 2026-06-12 - Expanded Security Configuration for Backup Services

### Added

- 🔑 **Added Keycloak OAuth2 Proxy Secret for Backup Service:** Introduced support for a new
  `KEYCLOAK_OAUTH2_PROXY_BACKUP_SECRET` environment variable across all Docker Compose configurations, enabling secure
  access to a dedicated backup service via Keycloak OAuth2 Proxy.

______________________________________________________________________

## [v0.296.1] - 2026-06-11 - Deployment: Enhanced Traefik Network Integration

### Changed

- 🌐 **Enhanced Traefik network configuration:** Explicitly assigned the Langfuse service to the `proxy` network for
  Traefik, improving routing and integration in self-hosted Docker deployments.

______________________________________________________________________

## [v0.296.0] - 2026-06-11 - Empowering Data Discovery: Advanced Filtering, Search, and Sorting for Agents and Threads

### Added

- ✨ **Agent Instance Filtering and Search:** Introduced new API capabilities and corresponding UI elements allowing
  users to filter agent instances by **class** and search by **name**, significantly improving agent discovery.
- 🚀 **Advanced Thread Management:** Implemented comprehensive filtering options for threads, including search by
  **name**, filtering by associated **agent ID**, specific **user ID**, run **status** (active, completed, failed), and
  a flexible **date range**.
- 📈 **Thread Sorting Capabilities:** Added the ability to sort threads by **name** or **creation date** in both
  ascending and descending order, providing more control over how threads are organized and viewed.
- 🦾 **Thread Status Classification:** Introduced robust backend logic to accurately classify threads into `active`,
  `completed`, or `failed` states based on their agent event history, enabling precise status filtering.

### Changed

- 🔄 **API Query Parameter Expansion:** The `getAllAgentInstances` and `getPaginatedThreadsForUser` API endpoints have
  been extended to support the new filtering, searching, and sorting parameters, providing more powerful data retrieval.
- 🌐 **UI Enhancements for Agents and Threads:** The web interface for both Agent Instances and Threads has been
  significantly updated to expose and utilize all new filtering, search, and sorting functionalities, improving user
  experience and data navigation.

### Refactor

- 🧹 **Optimized Agent Configuration Search:** Refactored the agent configuration search logic to support multilingual,
  case-insensitive substring matching for agent names, enhancing search flexibility.
- ⚙️ **Streamlined Thread Query Logic:** Introduced dedicated helper methods (`_apply_filters`, `get_order_by`) within
  the `ThreadEntity` for more modular, efficient, and maintainable query construction.

______________________________________________________________________

## [v0.295.4] - 2026-06-11 - Improved Authentication Flow and Persistent User Sessions

### Added

- ✨ **Architectural Decision Record for Keycloak Sessions:** Documented the rationale, drivers, and implementation
  details for extending Keycloak Single Sign-On (SSO) session lifespans, outlining the benefits for user experience and
  system behavior.
- ⚙️ **Centralized Keycloak Session Configuration:** Introduced new configuration parameters (`sso_session_idle_timeout`
  and `sso_session_max_lifespan`) in `compose-config.yml`, providing a single source of truth for Keycloak realm session
  settings.

### Changed

- 🚀 **Extended Keycloak SSO Session Lifespans:** Increased Keycloak SSO session idle timeout to 5 days and maximum
  lifespan to 30 days. This significantly reduces the frequency of forced re-logins, allowing users to stay logged in
  across nights and weekends for a smoother experience.
- 🔄 **Automatic Keycloak Session Lifespan Migration:** Implemented logic within the Keycloak entrypoint script to
  automatically update SSO session lifespans for existing deployments. This ensures that environments originally
  configured with Keycloak's default short lifespans are automatically upgraded to the new, longer durations without
  overwriting manual operator customizations.
- ⚡️ **Optimized Home Page Redirection:** Enhanced the login experience by implementing smart redirection. Users are now
  automatically directed to their last active tenant after successful login or silent token renewal, leveraging
  persisted active tenant information.

______________________________________________________________________

## [v0.295.3] - 2026-06-11 - Improved Streaming State and Richer Responses

### Refactor

- 🧹 **Enhanced Streaming State Management Initialization:** The `StreamingStateManager` is now initialized earlier in
  the processing pipeline, ensuring comprehensive state capture from the very beginning of a request.

### Changed

- ⚡️ **Richer Output for Successful Operations:** The pipeline now consistently returns serialized HTML content from the
  streaming state manager upon successful completion, providing more detailed and structured results to the user
  interface.
- 📄 **Contextual Error Reporting:** Error messages now include any available partial streaming state (serialized as
  HTML) alongside the error details. This provides users with more context and partial results, making it easier to
  understand and debug issues.

______________________________________________________________________

## [v0.295.2] - 2026-06-11 - Improved Tenant Management and Documentation Clarity

### Added

- 🖼️ **New Visual Aids for Tenant Creation:** Integrated several new screenshots to provide clear, step-by-step guidance
  for Keycloak group creation and navigating the Tenant Administration UI.
- 🔑 **Dedicated `AIHubSysAdmin` Role:** Introduced the `AIHubSysAdmin` Keycloak realm role, which is now required for
  creating and configuring tenants, enhancing security and control over multi-tenancy lifecycle management.

### Changed

- 📄 **Revamped Tenant Creation Documentation:** The "Creating Tenants" guide has been significantly updated with a
  detailed, step-by-step process, clarifying the interplay between Keycloak groups and platform metadata, tenant states,
  and in-tenant role assignments.
- 📚 **Enhanced German Architecture Documentation:** Made minor textual improvements and clarifications across various
  German architecture documents, including system context, containers, and package-centric views, for improved
  readability and accuracy.

______________________________________________________________________

## [v0.295.1] - 2026-06-11 - Enhanced AI-Driven GitHub Issue Management

### Added

- ✨ **New AI Skill: `write-issue`**: Introduced a powerful new AI skill that enables automated authoring, creation, and
  management of GitHub issues within the `bbvch-ai/aihub-core` repository. This skill ensures adherence to established
  project conventions for titles, body structure, labels, and project board integration.
- 📄 **Comprehensive Issue Creation Guidelines**: Detailed a comprehensive set of conventions and steps for drafting
  GitHub issues, covering everything from title formatting (Epic/Story vs. Task/Bug), structured body content
  (`In scope`, `Out of scope`, `Accepted when`), required `area:*` and optional `version` labels, to setting project
  board fields like Item Type, Priority, and Status.
- ⚙️ **Automated Issue Validation Script**: Implemented a new Bash script (`validate-issue.sh`) to automatically verify
  that newly created GitHub issues conform to project standards. This script checks for correct labeling, the presence
  of specific body sections, checkbox acceptance criteria, and proper placement on the AI-Scrum board with an assigned
  Item Type.

______________________________________________________________________

## [v0.295.0] - 2026-06-11 - Streamlined Bot Setup and Clearer User Provisioning

### Added

- ✨ **New Architecture Decision Record (ADR)**: Documented the decision to prevent bot-first Keycloak provisioning,
  requiring users to log in to the web portal once before interacting with the bot. This clarifies the user onboarding
  process and ensures consistent identity management.
- 🦾 **`UserNotProvisionedError`**: Introduced a specific exception for users attempting to interact with the bot before
  their Keycloak account has been provisioned via web login, allowing for targeted error handling.
- 📄 **Localized Bot Messages**: Added new internationalized messages across German, English, French, and Italian,
  providing clear and actionable guidance to users who are not yet provisioned in Keycloak.
- ⚙️ **`BOT_DEV_FAKE_EMAIL` Environment Variable**: Introduced a new environment variable for local development to
  simulate user identity for the bot, bypassing the Teams connector and enabling comprehensive testing of authentication
  flows without Azure.
- ⚡️ **`primary_frontend_origin` Setting**: Added a convenience property to `AIHubSettings` to easily retrieve the
  primary web portal URL, used for directing unprovisioned users to the login page.

### Changed

- 🚀 **Overhauled Bot Local Development Setup**: Significantly revised the local development documentation for the bot,
  providing detailed, step-by-step instructions for using the Bot Framework Emulator, including support for WSL2 and
  anonymous authentication.
- 🔄 **Bot User Identity Resolution**: Modified the bot's identity resolution logic to raise a specific
  `UserNotProvisionedError` when a user's email is not found in Keycloak, replacing a generic `ValueError`.
- 💬 **Actionable Error Handling for Unprovisioned Users**: The bot now gracefully handles `UserNotProvisionedError` by
  replying with a clear, localized message instructing users to perform a one-time web portal login, rather than
  displaying an opaque error.
- 🌎 **WSL2 Compatibility for Local Bot Runner**: Updated the local bot runner (`main.py`) to bind to `0.0.0.0:8001`,
  enabling seamless connectivity from the Bot Framework Emulator running on Windows when the bot is hosted in WSL2.
- 🔑 **Anonymous Authentication for Local Bot Runner**: The local bot runner now monkeypatches the Microsoft Agents SDK
  to force unauthenticated mode, allowing the Bot Framework Emulator to drive the bot without requiring Azure
  credentials.

### Removed

- 🗑️ **Bot-Driven User Provisioning Capability**: The `create_user` method in `KeycloakAdminService` and its
  corresponding integration test were removed, aligning with the architectural decision to exclusively provision
  Keycloak users via the web portal's first-broker-login flow.

______________________________________________________________________

## [v0.294.0] - 2026-06-11 - Swiss AI Hub Now Fully Open-Source with AGPL-3.0-or-later Sysadmin Plane

### Added

- 📄 **New Architectural Decision Record (ADR):** Introduced a comprehensive ADR detailing the strategic decision to
  relicense the multi-tenant administration plane to AGPL-3.0-or-later, outlining its context, decision drivers, and
  consequences.

### Changed

- 🔄 **Relicensed Multi-Tenant Administration Plane:** The `packages/sysadmin-api` and `packages/sysadmin-web`
  components, previously proprietary, are now open-source under the **GNU Affero General Public License v3.0 or later
  (AGPL-3.0-or-later)**. This change completes the transition of Swiss AI Hub to a fully open-source platform.
- 🔑 **Updated Licensing Model Documentation:** All project documentation, including the root `README.md`, `LICENSES.md`,
  `CONTRIBUTING.md`, and internal architecture documents, has been thoroughly revised to reflect the new dual-license
  model (Apache-2.0 for backend/SDK and AGPL-3.0-or-later for UI/administration).
- ⚡️ **Refined Sysadmin Package Rationale:** The justification for `sysadmin-api` and `sysadmin-web` existing as
  separate packages now focuses purely on architectural and security boundaries, rather than licensing, as both the main
  application and administration plane share the AGPL-3.0-or-later license.
- ⚙️ **Deployment Configuration Updates:** Docker Compose templates and generation scripts have been updated to reflect
  the AGPL-3.0-or-later license for `sysadmin-api` and `sysadmin-web`, ensuring accurate license annotations in
  deployment artifacts.

### Removed

- 🗑️ **Deprecated Proprietary License Identifiers:** All per-file `SPDX-License-Identifier` headers denoting proprietary
  licenses have been removed from source files within `packages/sysadmin-api` and `packages/sysadmin-web` for
  consistency with the rest of the monorepo, which relies on package-level `LICENSE` files.
- 🗑️ **Removed Proprietary Tags from Architecture:** The `#proprietary` tag has been eliminated from architecture
  specifications and container definitions, aligning these views with the platform's fully open-source status.

______________________________________________________________________

## [v0.293.2] - 2026-06-10 - Improved Configuration Generation and Placeholders

### Added

- ✨ **Introduced UUID generation for environment setup:** Added a new `gen_uuid` function and `REPLACE_WITH_RANDOM_UUID`
  placeholder to the `setup-env.sh` script, enabling automatic generation of UUIDs for configuration values.

### Changed

- 🔄 **Updated Rclone RC credential placeholders:** Renamed the default placeholders for Rclone RC user and password in
  `.env.prod` to `REPLACE_WITH_RANDOM_STRING` for consistency and clarity with the automated generation process.

______________________________________________________________________

## [v0.293.0] - 2026-06-10 - Enhanced Version Visibility for API and UI

### Added

- ✨ **Service Version Reporting**: The API's `/health` and `/ready` endpoints now include the running service version in
  their responses, improving operational visibility.
- ✨ **UI Version Display**: The web application now fetches and displays both its own and the API's service versions in
  the user settings, clearly indicating if the UI and API are running on different versions.
- ✨ **OpenAPI Version Documentation**: The API's OpenAPI specification has been updated to include the service version,
  making it programmatically accessible for clients.

### Changed

- 🔄 **Health Response Structure**: The core `HealthResponse` data transfer object has been extended to include a
  dedicated `version` field.
- 🔄 **Web Build Process**: The web application's Dockerfile and Nuxt configuration have been updated to bake the service
  version into the static bundle during build time, ensuring accurate version reporting.

______________________________________________________________________

## [v0.292.3] - 2026-06-10 - Enhanced Reliability for Agent Event Streams

### Fixed

- 🐛 Resolved a race condition that could cause **agent output streaming chunks** to be dropped, leading to incomplete or
  blank answers in chat clients. This fix ensures all `DisplayEvent`s are processed before consumer teardown.
- 🔗 Guaranteed the **delivery of complete agent answers** by implementing a durable backstop that reconciles any missing
  content from the final stop event, preventing empty assistant turns and associated errors.

### Added

- ✨ Introduced shared utility methods, **`iter_streamed_display_events`** and **`wait_for_stop_then_drain`**, in
  `ChatService` to ensure all display events are gracefully drained and processed after an agent run completes.
- 📄 Documented the architectural decision for robust streaming in a new ADR: **"Drain Display-Event Streams Before
  Consumer Teardown"**.
- 🧪 Added new **unit tests** to validate the correctness and resilience of the event draining and answer reconciliation
  logic.

### Changed

- 🔄 Refactored **all streaming event consumers** (including OpenAI SSE, JSON, and native event streams) to utilize the
  new graceful draining mechanisms, improving the consistency and reliability of agent output.
- 🚀 Updated **final content resolution** for OpenAI and JSON responses to include delta reconciliation, using the
  terminal `StopEvent` as a source of truth to complete partially streamed or lost answers.

______________________________________________________________________

## [v0.292.2] - 2026-06-09 - Infrastructure Network Enhancements

### Changed

- 🚀 **Improved Backend Network Connectivity:** The core backend services are now connected to a dedicated `egress`
  network across all deployment configurations, enhancing support for secure and managed outbound connections.

______________________________________________________________________

## [v0.292.0] - 2026-06-08 - Streamlined Python Distribution: PyPI Launch and Enhanced Documentation

### Added

- 🚀 **PyPI Publishing Workflow:** Introduced a new automated GitHub Actions workflow for building and publishing all
  public Python SDK packages to PyPI, enabling wider distribution and easier installation.
- 🔐 **Distribution Artifact Validation:** Added a new Python script (`check_dist.py`) to enforce namespace integrity,
  prevent secret leaks, and flag unexpectedly large files within PyPI packages, significantly enhancing release security
  and quality.
- 📦 **`swiss-ai-hub` Meta-Package:** A new meta-package, `swiss-ai-hub`, has been added to simplify the installation of
  the entire Swiss AI Hub Python SDK with a single command.
- 📄 **Package License Files:** Explicit `LICENSE` files have been added to each Python package (`agent`, `api`, `bot`,
  `core`, `meta`, `pipeline`, `process`), ensuring clear license compliance for distributed artifacts (Apache-2.0 for
  most, AGPL-3.0-or-later for `backup`).

### Changed

- 📝 **Comprehensive Package READMEs:** The `README.md` files for all Python SDK packages have been significantly
  expanded and improved to provide detailed purpose, installation, usage, development, and production guidance, tailored
  for PyPI consumers.
- ⚙️ **Standardized PyPI Metadata:** All `pyproject.toml` files across the Python SDK packages have been enhanced with
  detailed descriptions, relevant PyPI classifiers, and comprehensive project URLs (Homepage, Repository, Documentation,
  Issues) for improved discoverability and information.
- 🔗 **Pinned Internal Dependencies:** Python `pyproject.toml` files now explicitly pin inter-package dependencies (e.g.,
  `swiss-ai-hub-agent` depending on `swiss-ai-hub-core`) to their exact version, ensuring consistent and predictable
  builds.
- 🛠️ **Build System Configuration:** Adjusted `uv_build` settings in `pyproject.toml` for all Python packages to
  correctly handle PEP 420 native namespaces during artifact creation, ensuring proper module loading.
- 🌐 **Public Image URLs in README:** All image references in the root `README.md` have been updated to use absolute
  GitHub raw URLs, guaranteeing they display correctly on external platforms like PyPI.
- 🔒 **NPM Publish Workflow Environment:** The `publish-npm.yml` GitHub Actions workflow now uses an explicit `npm`
  environment for enhanced security context during package publication.
- 📖 **Environment Variables Documentation:** The formatting and readability of the environment variables reference
  documentation have been updated for better clarity.
- ⬆️ **Core Dependency Updates:** Several key dependencies in `swiss-ai-hub-core` have been upgraded, including
  `mem0ai`, `langchain-neo4j`, `neo4j`, `rank-bm25`, and `starlette` (with a security floor to `1.0.1`), enhancing
  functionality and addressing known vulnerabilities.
- 🐍 **`jambo` Internal Dependency:** The `jambo` dependency in `swiss-ai-hub-api` has been migrated to
  `swiss-ai-hub-jambo`, reflecting an internal packaging change for consistent namespace usage.
- ⚡️ **Version Bump Script:** The `Makefile`'s `version-bump` target now correctly updates inter-package dependencies to
  ensure all internal `swiss-ai-hub-*` packages reference the new version.

### Refactor

- 🧹 **Form Default Seeding Logic:** The web UI's `seedFormDefaults` function has been refactored by extracting dedicated
  helper functions for handling group and repeater elements, improving code clarity and maintainability.

______________________________________________________________________

## [v0.291.13] - 2026-06-08 - Enhanced OpenAI Service Iframe Permissions

### Changed

- ⚡️ **Expanded OpenAI service iframe capabilities:** The embedded OpenAI service now supports additional browser
  features such as **clipboard access**, **camera**, **screen capture**, **fullscreen mode**, **geolocation**, and
  **autoplay**, alongside refined **microphone access**.

______________________________________________________________________

## [v0.291.12] - 2026-06-08 - Refined Skill Permissions for Enhanced Control

### Changed

- ⚡️ **Refined Skill Permissions:** The broad `mcp__*` skill wildcard has been replaced with a specific, enumerated list
  of allowed `mcp` skills, enhancing control and clarity over which tools are accessible.

______________________________________________________________________

## [v0.291.11] - 2026-06-08 - Enhanced Changelog Documentation

### Changed

- ⚡️ **Improved Changelog Documentation Handling**: The documentation build script now correctly processes changelog
  content by wrapping its body in a `v-pre` container. This change prevents build errors caused by special syntax (e.g.,
  GitHub Actions expressions) within release notes, ensuring that content is rendered verbatim on the documentation site
  while preserving the functionality of dynamic elements like copy/download buttons.

______________________________________________________________________

## [v0.291.10] - 2026-06-08 - Enhanced Security and Code Quality

### Added

- ✨ **Introduced CodeQL Analysis workflow:** A new GitHub Actions workflow has been added to perform automated static
  code analysis, enhancing the security and overall code quality of the Python and JavaScript/TypeScript codebases.

______________________________________________________________________

## [v0.291.9] - 2026-06-08 - Simplified Access Control and Enhanced Identity Provider Setup

### Added

- 📄 **New Identity Provider Setup Documentation**: Introduced comprehensive guides for connecting external identity
  providers to the Swiss AI Hub via Keycloak, starting with detailed instructions for Microsoft Entra ID (Azure AD).
- 🔐 **Azure App Registration Guide**: Provided step-by-step documentation for configuring Azure App Registrations,
  including redirect URIs, required API permissions (`openid`, `email`, `profile`), and client secret management.
- 👥 **Azure User and Role Management Guide**: Added clear instructions on defining and assigning `AIHubAccess`
  (mandatory for platform login) and `AIHubSysAdmin` app roles within Azure Entra ID to control user access.

### Changed

- 🔑 **Updated Superuser Role Configuration**: Modified default superuser roles (`SUPERUSER_ROLES_JSON`) to explicitly
  include `AIHubAccess` as the base role for platform usage, aligning with the refined access control model.
- 📖 **Enhanced Authentication & Authorization Documentation**: Significantly updated the security documentation to
  clarify the distinction between Keycloak Realm roles (`AIHubAccess`, `AIHubSysAdmin`) and platform-managed
  tenant-scoped roles, providing a clearer understanding of the permission hierarchy.

### Removed

- 🗑️ **Streamlined Keycloak Realm Roles**: Deprecated and removed `AIHubAdmin`, `AIHubUser`, and `AIHubDeveloper` from
  the Keycloak realm configuration. These roles are now intended to be managed as tenant-specific roles within the
  platform's internal access management system.
- 🧹 **Simplified Identity Provider Mappers**: Removed corresponding identity provider mappers for the deprecated
  `AIHubAdmin`, `AIHubUser`, and `AIHubDeveloper` roles, streamlining the IdP integration process.

______________________________________________________________________

## [v0.291.8] - 2026-06-08 - Streamlined Initial Navigation and Enhanced Authentication

### Added

- ✨ **Seamless Initial Navigation:** Introduced a new, dedicated middleware for the home route (`/`) to intelligently
  determine and redirect users to their appropriate tenant, tenant selection, or previously visited page immediately
  after login, ensuring a smoother start to their session.
- 🚀 **Global Loading Overlay:** Implemented a full-screen loading spinner that instantly appears when the initial
  navigation logic is resolving, eliminating content flicker and providing clear visual feedback during critical
  redirects.
- ⚙️ **Centralized Home Resolution State:** Added a shared state management system and client-side plugin to accurately
  manage the global loading indicator, ensuring it correctly displays during initial route resolution and dismisses on
  navigation completion or errors.

### Changed

- 🛡️ **Robust Authentication Handling:** Enhanced the authentication flow to automatically invalidate and remove
  problematic user sessions when silent sign-in or token renewal encounters errors, improving stability and preventing
  repeated authentication failures.

### Refactor

- 🧹 **Refined Initial Login Flow:** Streamlined the application's startup by relocating the logic for checking and
  renewing user sessions from the OIDC client plugin to a global authentication middleware, allowing for more efficient
  and non-blocking initialization.
- ⬆️ **Modernized Homepage Implementation:** Replaced the client-side `onMounted` logic for tenant fetching and
  redirection on the homepage with a server-side (or early client-side) middleware, significantly improving the
  responsiveness and consistency of the initial user experience.

______________________________________________________________________

## [v0.291.7] - 2026-06-03 - Enhanced Model Cost Reporting and API Robustness

### Added

- ✨ **Introduced Granular Search Context Cost Reporting:** Added a new data transfer object
  (`SearchContextCostPerQueryDTO`) to capture and display search context costs broken down by low, medium, and high
  context sizes, providing more detailed pricing information.
- 🦾 **Enhanced API Robustness for Model Information:** Implemented a new data validation mechanism that gracefully
  handles unexpected data shapes in external model metadata feeds by logging warnings and dropping malformed fields,
  preventing parsing failures for the entire model information.

### Changed

- 📊 **Updated Model Details Panel:** The **Model Details Panel** now presents search context costs with a more granular
  breakdown (low, medium, and high context sizes), offering clearer insights into model pricing.
- 🌍 **Localized Search Context Cost Labels:** Updated internationalization files to include specific labels for low,
  medium, and high search context costs in various languages (English, German, French, Italian).
- 🔄 **Revised Model Information Schema:** Modified the **`ModelInfoDTO`** to incorporate the new granular
  `SearchContextCostPerQueryDTO` for search context costs and made the `mode` field optional, reflecting more flexible
  model metadata.

______________________________________________________________________

## [v0.291.6] - 2026-06-03 - Core System Refinements and Performance Enhancements

### Changed

- 🚀 **Enhanced LLM Guard Performance:** Switched agent description and few-shot guards to use asynchronous structured
  prediction, improving responsiveness and concurrency with Large Language Models.
- ⚡️ **Improved Concurrency for Reranking Nodes:** Blocking reranking operations are now offloaded to a separate thread
  using `asyncio.to_thread`, preventing event loop starvation and boosting application performance.
- 📄 **Refined Error Logging:** Updated `MineruLoader` and Redis request hooks to use `logger.exception`, ensuring
  comprehensive exception details are automatically included in logs for better debugging.
- 🛠️ **Corrected OpenTelemetry HTTPX Instrumentation:** Ensured asynchronous HTTPX request and response hooks are
  properly defined as coroutine functions, enabling full observability for async HTTP communications.

### Refactor

- 🧹 **Optimized Dispatcher Event Handling:** The `_build_event_kwargs` method in agent and process dispatchers, as well
  as the base dispatcher, has been made synchronous, streamlining event argument construction.
- 🔄 **Standardized Access Rule Prefixes:** Consolidated `aihub.admin` and `aihub.user` access rule prefixes into
  dedicated constants, enhancing maintainability and clarity across authentication logic.
- 🔑 **Centralized Authentication Error Messages:** Moved common error messages in the authentication handler to
  constants, improving consistency and simplifying future updates.
- ☁️ **Standardized S3 Service Error Messages:** Consolidated error messages for S3 anonymous file access service
  operations into constants, improving consistency and maintainability.
- ⚙️ **Refined SonarQube Configuration:** Added specific ignore rules to `sonar-project.properties` to suppress
  `python:S1192` (duplicated string literals) warnings for known-good patterns, such as lazy imports and MongoDB query
  syntax, reducing false positives in code quality scans.
- 📝 **Improved RPC Success Attribute Handling:** Standardized the `rpc.success` attribute for NATS requester tracing
  using a dedicated constant.
- 📚 **Improved Test Mock Clarity:** Added `noqa` comments to asynchronous mock methods in authentication utilities and
  Milvus vector store tests to explicitly state why they remain async for testing purposes, improving code clarity for
  linters.
- 🧹 **Minor Python Idiom Improvements:** Updated set creation from `set(generator_expression)` to `{comprehension}` in
  `base_event` and `dispatchable_workflow` for more idiomatic Python.

______________________________________________________________________

## [v0.291.5] - 2026-06-02 - Enhanced FormKit Data Handling for Stability

### Changed

- 🔄 **Refined `getNestedValue` utility:** The `getNestedValue` function has been refactored to operate as a pure
  read-only function, specifically for retrieving nested arrays. This change prevents unintended mutations of form data
  during render-time and mitigates potential recursive render loops in reactive contexts. It now strictly returns an
  array or an empty array if the specified path does not lead to an array.

### Fixed

- 🛠️ **Improved Repeater Initialization:** FormKit repeater fields now correctly materialize as an empty array during
  form loading if their default value is `undefined`. This proactive initialization ensures a consistent array structure
  for repeaters, preventing unexpected behavior and improving stability in reactive render contexts.

______________________________________________________________________

## [v0.291.4] - 2026-06-02 - Enhanced Prompt Reliability for Image Rendering

### Fixed

- 🐛 **Image Rendering in Prompts**: Resolved a Jinja `SecurityError` that occurred when attempting to render image URLs
  (`pydantic.AnyUrl`) within RAG agent and guard context prompts. The rendering now correctly uses the `| string` filter
  to safely convert URLs, ensuring images are displayed as intended across all supported languages.

______________________________________________________________________

## [v0.291.3] - 2026-06-02 - Stricter OAuth Role Defaults

### Changed

- 🔑 **Updated OAuth Allowed Roles Default:** The default `OAUTH_ALLOWED_ROLES` configuration for Open WebUI has been
  updated across all deployment configurations. It now explicitly requires `AIHubAccess` and any configured admin roles
  (`${OAUTH_ADMIN_ROLES_OPENWEBUI}`) instead of a wildcard (`*`), enhancing access control and improving the security
  posture for OAuth integrations.

______________________________________________________________________

## [v0.291.2] - 2026-06-02 - GitHub Actions Reliability Improvement

### Fixed

- 🐛 **Corrected GitHub Actions `if` condition parsing:** Ensured proper evaluation of the `claude-code-review`
  workflow's trigger conditions by explicitly wrapping the complex expression in `${{ ... }}`.

______________________________________________________________________

## [v0.291.1] - 2026-06-02 - Improved Code Quality Checks with SonarCloud Action v6

### Changed

- 🚀 **Updated SonarCloud Scan Action:** The GitHub Action for running SonarCloud code quality scans has been upgraded to
  `v6.0.0`, enhancing reliability and ensuring compatibility with the latest SonarCloud features.
- 📄 **Documentation Refresh:** Internal documentation (`CLAUDE.md`) was updated to reflect the new version of the
  SonarCloud scan action used in CI/CD workflows.

______________________________________________________________________

## [v0.291.0] - 2026-06-02 - 🚀 Web Package Stability, Deployment, and Publishing Overhaul

### Added

- 🚀 **Automated npm publishing workflow**: Introduced a dedicated GitHub Actions workflow (`publish-npm.yml`) to
  streamline and automate the publishing of the `@swiss-ai-hub/web` package to npm, utilizing OIDC trusted publishing
  for enhanced security.
- 🧪 **Web package build and pack verification**: Added a new GitHub Actions workflow (`verify-web-package.yml`) to
  automatically build and validate the packaging of `@swiss-ai-hub/web` on every pull request, ensuring package
  integrity and publishability before merge.

### Changed

- ⚙️ **Streamlined CI/CD branch triggering**: Modified several core CI/CD workflows (`analyze-test-pr`, `lint-pr`,
  `semantic-pr`, `test-backup-e2e`) to exclusively trigger on the `main` branch, simplifying branching strategy and
  pipeline execution.
- 📄 **Enhanced web package installation and dependency management documentation**: Significantly updated the
  `packages/web/README.md` with detailed guidance on required dependency overrides (specifically for `vue` and
  `primevue`) to prevent common runtime issues caused by multiple framework instances.
- 🔄 **Redesigned runtime configuration for static builds**: Introduced a new, more robust runtime configuration
  mechanism for the `@swiss-ai-hub/web` layer, moving away from `NUXT_PUBLIC_*` environment variables to a dynamic
  `/config.js` file generated at container startup, offering greater deployment flexibility for static single-page
  applications.
- 🐳 **Updated Dockerfile and deployment examples**: Provided comprehensive and up-to-date Dockerfile and
  `nuxt.config.ts` examples in the `packages/web/README.md` that reflect the new best practices for building, serving,
  and configuring the static web package in production environments.
- ✨ **Integrated FormKit PrimeVue**: Added `@sfxcode/formkit-primevue` as a new dependency within the `packages/web`
  package, enhancing its form building capabilities with PrimeVue components.
- ⬆️ **Updated PrimeVue peer dependency**: Bumped the recommended `primevue` peer dependency version to `4.5.5` to
  ensure compatibility and leverage the latest updates for the UI component library.

______________________________________________________________________

## [v0.290.13] - 2026-06-02 - OAuth Default Role Access Update

### Added

- ✨ **Introduced `OAUTH_ALLOWED_ROLES` configuration:** Added the `OAUTH_ALLOWED_ROLES` environment variable, set to `*`
  by default across Docker Compose configurations, to explicitly allow all roles from the OAuth provider, simplifying
  initial setup for role-based access.

______________________________________________________________________

## [v0.290.12] - 2026-06-02 - Documentation Refinements and Link Consistency

### Changed

- 🔗 **Updated External README Links:** Transformed relative paths for licenses and contributing guidelines in the main
  `README.md` to absolute GitHub URLs, ensuring links function correctly across all platforms.
- 📄 **Minor Documentation Formatting:** Improved the display of the Dagster UI URL in the `packages/backup` README for
  better readability.

### Refactor

- 🧹 **Standardized Internal Documentation Paths:** Performed a comprehensive review and adjustment of numerous relative
  links throughout the German and English documentation, enhancing navigation and consistency within the platform guides
  and SDK.
- 📚 **Streamlined Authentication Documentation:** Removed outdated architectural decision record (ADR) links from
  authentication-related documentation, simplifying the content and focusing on current implementation details.

______________________________________________________________________

## [v0.290.11] - 2026-06-01 - Enhanced Documentation and Licensing Clarity

### Added

- 📄 **New API Tokens Documentation**: A dedicated guide has been added explaining how to generate, use, and revoke
  personal API tokens for REST API authentication, including steps within the Swagger UI.
- ✨ **Comprehensive SDK Licensing Rationale**: New documentation now details the platform's mixed-license model,
  clarifying the rationale behind using Apache 2.0 for the backend and AGPLv3 for the user interface, and its
  implications for proprietary agent development and community contributions.
- 📄 **Licensing Clarifications**: The `LICENSES.md` and `README.md` files have been updated with explicit explanations
  of the mixed-license model, emphasizing the permissive backend and copyleft UI.
- 🔑 **UI Extensibility Licensing Note**: A new licensing note has been added to the UI extensibility documentation,
  explicitly detailing the AGPL-3.0 implications for modifying and offering the UI as a network service.

### Changed

- 🔄 **Refined Ecosystem Model Documentation**: The documentation for the ecosystem model has been significantly revised
  to provide a clearer and more in-depth explanation of the platform's collaborative approach and licensing strategy.
- 📝 **Clarified Agent Behaviors**: Extensive updates have been made across several agent documentation pages (**Company
  Knowledge Agent**, **Instructed Assistant**, **Teachable Assistant**, **Retrieval Agent**, **Document Navigation
  Assistant**, and **MCP Tool Agent**) to provide clearer descriptions of their purpose, workflows, capabilities,
  limitations, and setup instructions.
- 📝 **Improved UI Extensibility Guide**: The UI extensibility documentation has been substantially rewritten to offer
  more detailed insights into architectural foundations, custom service implementation, development workflows,
  deployment, and strategic value.
- 📝 **Updated MCP Tools Usage in SDK**: The SDK documentation for using MCP tools has been rephrased for better clarity,
  particularly regarding connection configuration and authentication modes.
- 📄 **Minor Documentation Updates**: Small adjustments and rephrasing have been applied to the **Web Search** and
  **Environment Variables** documentation pages for improved readability and consistency.
- 📝 **API Tokens Documentation Enhancement**: The English version of the API Tokens documentation has been updated to
  include the revoke endpoint in its lifecycle table.

______________________________________________________________________

## [v0.290.10] - 2026-06-01 - Enhancing Project Governance: CLA and Contributor Guidelines

### Added

- ✨ **Contributor License Agreement (CLA):** Introduced a formal Individual Contributor License Agreement
  (`CONTRIBUTOR_AGREEMENT.md`) to clarify intellectual property rights for contributions.
- 🚀 **Automated CLA Checks:** Implemented a new GitHub Actions workflow (`cla.yml`) to automatically verify CLA
  signatures for pull requests, streamlining the contribution process.
- 📄 **Pull Request Template:** Added a standard pull request template (`pull_request_template.md`) to guide contributors
  in providing necessary information, improving PR quality and review efficiency.

### Changed

- ✍️ **Updated Contributing Guidelines:** Expanded `CONTRIBUTING.md` with a new section detailing the Contributor
  License Agreement process and instructions for signing it.
- ⚖️ **Refined Licensing Notice:** Updated the project's `NOTICE` file to provide a more general description of the
  mixed-license model, referencing `LICENSES.md` for full details.

______________________________________________________________________

## [v0.290.9] - 2026-06-01 - Next-Gen Agents and Operational Excellence

### Added

- 🦾 **New Agent Blueprints**: Introduced a suite of powerful, pre-built agent blueprints for diverse use cases:
  - 📄 **Document Intelligence Assistant**: A highly configurable Retrieval-Augmented Generation (RAG) agent that answers
    questions from internal documents with citations, replacing the previous generic RAG agent with advanced
    capabilities including context-sufficiency guards and user/organization memory.
  - 🤝 **Company Knowledge Agent**: An extension of the Document Intelligence Assistant that incorporates
    human-in-the-loop for user consent and bot-in-the-loop for expert consultation, capturing human replies as
    organizational knowledge.
  - 🧑‍💻 **Expert Coordinator Agent**: Designed to relay questions to human experts via Slack or Teams, verify their
    responses, and store them as reusable organizational knowledge. Channel configuration is now managed directly within
    the agent's profile.
  - 🧠 **Instructed Assistant**: A foundational chat assistant that follows plain-text system prompts for focused tasks
    like drafting, translation, or style-guided responses without document retrieval.
  - 📚 **Teachable Assistant**: An agent that learns behavior from a few examples (few-shot prompting), making it ideal
    for tasks requiring specific response styles or formats.
  - 🔍 **Retrieval Agent**: A headless, composable building block that performs document retrieval from a knowledge base
    without generating an answer, providing raw context for custom workflows.
  - 🧭 **Document Navigation Assistant**: A routing agent that intelligently identifies the most relevant knowledge
    bases/namespaces for a user's question, confirms the selection with the user, and then delegates to a RAG agent.
  - 🛠️ **MCP Tool Agent**: Enables agents to connect to external Model Context Protocol (MCP) servers and execute
    actions in other systems, such as creating tickets, querying databases, or sending messages.
- ⚙️ **Automated PostgreSQL Maintenance**: Integrated continuous weekly cleanup and monthly repack jobs for the Dagster
  PostgreSQL database, ensuring long-term operational stability by managing log growth and freeing disk space.
- 📄 **Comprehensive Environment Variable Reference**: Added a new, automatically generated documentation page listing
  all environment variables, their purpose, and consumer services, clarifying setup and configuration.
- 🌐 **Self-Hosted Web Search**: Documented the new privacy-focused web search feature, powered by a self-hosted SearXNG
  meta-search instance for Open-WebUI, including its default search engine list and customization options.
- 🔗 **MCP Tooling for SDK Agents**: Provided detailed SDK guidance on connecting custom agents to external MCP servers
  and invoking their tools, including `McpClientConfig` and various authentication modes.
- 💬 **External Tool Connectivity Overview**: Expanded the Agents overview documentation to include a new section
  explaining how agents can interact with external systems using the Model Context Protocol (MCP).

### Changed

- 🔄 **Updated Documentation Structure**: Significantly reorganized the agent documentation, reordering blueprint pages
  for improved logical flow and discoverability.
- 📝 **Refined German Translations**: Numerous minor textual and stylistic improvements across German documentation for
  enhanced clarity and consistency.
- 🔑 **Clarified Tenant Deletion Rules**: Updated multi-tenancy documentation to state that any tenant can be deleted as
  long as at least one remains, clarifying the lack of special deletion protection for the initial startup tenant.
- ⚙️ **Standardized Startup Tenant Variables**: Renamed environment variables related to initial tenant configuration
  (e.g., `AIHUB_DEFAULT_TENANT_NAME` to `AIHUB_STARTUP_TENANT_NAME`) for clearer semantics.
- 🌐 **Updated Network Egress Requirements**: Removed Jina AI from the list of external service dependencies in the
  network requirements documentation.
- 📄 **Improved Main Page Tagline**: Updated the tagline on the main documentation landing page for better clarity and
  impact.
- 🔄 **Refined Docs Sync Script**: Improved the `sync-docs.sh` script to precisely control which `README.md` files are
  synchronized into the `docs/6_code_deep_dive` section, preventing unintended content.

### Removed

- 🗑️ **Deprecated Agent Documentation**: Removed the outdated "RAG Agent" and "Expert Asking Agent" documentation, as
  their functionalities have been superseded and enhanced by the new agent blueprints.
- 🗑️ **Removed Internal Tooling Documentation**: Cleaned up documentation pages previously generated from internal
  `.claude`, `.github/actions`, and `infra/deployment` directories, streamlining the documentation scope.

______________________________________________________________________

## [v0.290.8] - 2026-06-01 - Introducing a Mixed-License Model and Enhanced Contribution Guidelines

### Added

- 📄 **New `NOTICE` File:** Introduced a new `NOTICE` file to formally outline the project's mixed-license model,
  providing clear attribution and a detailed license breakdown for different components.
- 👨‍💻 **Author Information for Web Package:** Explicitly added the author (`bbv Software Services AG`) to the
  `packages/web/package.json` metadata.

### Changed

- ⚖️ **Revised Project Licensing Model:** The project now operates under a mixed-license model; `packages/web` and
  `packages/backup` are explicitly licensed under AGPL-3.0-or-later, while most other packages remain Apache-2.0 and
  `sysadmin-*` packages are proprietary.
- 📝 **Updated Contribution Guidelines:** The `CONTRIBUTING.md` file has been significantly updated to reflect the new
  mixed-license model, detailing that contributions are subject to the target package's license and requiring
  contributors to sign a Contributor License Agreement (CLA).
- 📅 **Extended Copyright Information:** Updated the root `LICENSE` file and relevant package `README.md` files to extend
  the copyright period to `2026` and specify `bbv Software Services AG` as the copyright holder.
- 🔗 **Enhanced License Documentation:** `CLAUDE.md`, `LICENSES.md`, `packages/backup/README.md`, and
  `packages/web/README.md` have been updated to accurately reflect and reference the detailed per-package licensing
  matrix and the new `NOTICE` file, ensuring greater transparency.

______________________________________________________________________

## [v0.290.7] - 2026-05-29 - Introducing API Token Management and Documentation

### Added

- 📄 **New Documentation for API Tokens:** Added comprehensive documentation guiding users on how to generate, manage,
  and use personal API tokens (`sk-`) for authenticating REST API requests, ensuring secure and long-lived access for
  scripts and integrations.

______________________________________________________________________

## [v0.290.6] - 2026-05-29 - Backup Service Refinements and Code Quality Enhancements

### Changed

- 📄 **Refined SonarQube Configurations:** Updated SonarQube issue suppression rules for backup services (Neo4j, Valkey,
  Milvus) to accurately reflect intentional design patterns and improve the clarity of code quality analysis.

### Refactor

- 🧹 **Optimized Regular Expressions:** Streamlined regex patterns in ClickHouse and PostgreSQL backup services by
  adopting `\w` shorthand and the `re.ASCII` flag, enhancing readability and precision.
- ⚡️ **Enhanced Milvus Backup Selection:** Improved the efficiency of Milvus backup selection logic by replacing
  `sorted()[-1]` with `max()`, leading to a more direct and performant approach for identifying the latest backup.

______________________________________________________________________

## [v0.290.5] - 2026-05-28 - Dependency Security Enhancement

### Security

- 🔑 **Bolstered Dependency Security:** Introduced a minimum version constraint for the `starlette` dependency
  (`>=1.0.1`) to mitigate a known vulnerability in earlier versions and enhance overall project security.

______________________________________________________________________

## [v0.290.4] - 2026-05-27 - Development Environment Update

### Changed

- ⚡️ **Upgraded `pnpm` Package Manager:** The monorepo's package management tool has been updated to `pnpm` version
  `10.20.0`, enhancing dependency resolution and optimizing the overall development workflow.

______________________________________________________________________

## [v0.290.3] - 2026-05-27 - Platform Refinements and Developer Experience Improvements

### Added

- 🦾 **Backup Service SonarCloud Analysis:** Enabled SonarCloud scanning for the `backup` package to improve code quality
  and maintainability.
- 📄 **Backup Service SonarCloud Configuration:** Introduced `sonar-project.properties` for the `packages/backup`
  service, configuring its code analysis.

### Changed

- ⚙️ **SonarCloud Rule Exclusions:** Updated SonarCloud configuration to exclude a rule
  (`Web:ItemTagNotWithinContainerTagCheck`) for `Notification/Item.vue` to accommodate new semantic HTML structures.

### Refactor

- ✨ **Enhanced Accessibility for Input Components:** Improved form accessibility across various components by adding
  explicit `input-id` attributes to input fields and `for` attributes to their corresponding labels. This includes:
  - Agent Selector
  - Chips Input
  - Vector Store Input
  - Knowledge Namespace Create and Edit Modals
  - Memory Edit components
  - User Settings Language Selector
- 🚀 **Optimized Data Retrieval Performance:** Improved the efficiency of identifying active items and filtering events
  by transitioning from array `filter` and `includes` methods to more performant `find` and `Set.has` operations,
  notably in:
  - Tenant details page navigation
  - Event list filtering
  - Agent, Knowledge document, and Thread navigation composables
- 🧹 **Codebase Modernization and Cleanup:**
  - Modernized asynchronous operations and error handling in core functionalities, including the application's health
    check and authentication callbacks, by adopting `async/await` syntax.
  - Replaced `window.location.origin` and `window.localStorage` with `globalThis` for improved cross-environment
    compatibility in the OIDC client plugin.
  - Standardized Node.js built-in module imports (`node:url`) in Nuxt configuration.
  - Streamlined conditional checks with optional chaining syntax for better readability.
  - Removed redundant or empty CSS selectors and unnecessary empty `<style scoped>` blocks from various web components
    to reduce bundle size and improve code clarity.
- semantic **Improved Semantic HTML Structure:** Refined the HTML structure in several components for better
  accessibility and semantic correctness, including:
- Converting non-interactive `<label>` elements to `<p>` tags for displaying static information (e.g., tenant ID,
  knowledge document upload location, memory details).
- Transforming Notification Item from a `div` to a semantically correct `<li>` element, and its interactive area from a
  `div` with `role="link"` to a `button`, along with converting the Notification Overlay and main notifications list
  containers to `<ul>` elements.

______________________________________________________________________

## [v0.290.2] - 2026-05-27 - Introducing Comprehensive User Role Management

### Added

- ✨ **New User Role Management API Endpoints:** Introduced `assign_role` and `revoke_role` API endpoints within the
  `UserController`, enabling robust management of tenant-scoped user roles.
- 🦾 **Service Layer for Role Actions:** Implemented core service and persistence logic for assigning and revoking user
  roles, including validation for tenant membership and role existence.
- 🧪 **Dedicated API Test Suite:** Added a comprehensive test suite to ensure the reliability and correctness of the new
  user role assignment and revocation APIs.
- 🖼️ **Interactive User Role Chips Component:** Introduced a new `UserRoleChips` Vue component for the frontend,
  providing an intuitive interface to display, assign, and revoke user roles directly within user lists.
- 🚀 **Frontend Composables for Role Management:** Developed new composables (`useAssignRoleToUser`,
  `useRevokeRoleFromUser`) to streamline role management actions within the web application.
- 🌐 **Internationalization Support for Role Management:** Added new localization strings across supported languages to
  provide a consistent user experience for the new role management features.
- ⚙️ **Centralized OpenAPI Schema Service:** Introduced `OpenApiSchemaService` in `packages/core` to centralize and
  standardize the injection of `tenant_id` path parameters into OpenAPI schemas, improving SDK generation.

### Changed

- 🔄 **Integrated Role Management in User Controllers:** The `UserController` in both the main API and the Sysadmin API
  now includes the new `assign_role` and `revoke_role` endpoints.
- 🤝 **Shared OpenAPI Schema Generation:** Both `ApiRunner` and `SysadminApiRunner` now leverage the new
  `OpenApiSchemaService` to ensure correct and consistent OpenAPI schema generation, especially for tenant-scoped paths.
- 📊 **Enhanced User List Component:** Updated the `UserList` component to seamlessly integrate the new `UserRoleChips`
  for interactive role display and management.
- 📦 **Updated API Client SDK:** The `sysadmin-web` and `web` API client SDKs have been regenerated to include the new
  role management methods and to accurately reflect `tenant_id` as a required path parameter for all tenant-scoped
  endpoints.
- ⚡️ **Broader Cache Invalidation for Roles:** Modified role-related mutations (create, update, delete) to trigger a
  broader cache invalidation, ensuring up-to-date data after changes.
- 📄 **Documentation Updates:** Revised `CLAUDE.md` and `README.md` in `packages/sysadmin-api` to reflect the adoption of
  `OpenApiSchemaService` and the extended functionality of the re-mounted `UserController`.

### Refactor

- 🧹 **Centralized OpenAPI Schema Logic:** The logic for injecting `tenant_id` into OpenAPI schemas has been refactored
  from `ApiRunner` into the new `OpenApiSchemaService` for better modularity and reusability across runners.

### Security

- 🔑 **License Change for Web Package:** The license for `packages/web` has been updated from Apache 2.0 to
  **AGPL-3.0-or-later**.

______________________________________________________________________

## [v0.290.1] - 2026-05-27 - Enhanced Dependency Stability and Configuration Flexibility

### Added

- ✨ **Introduced strict peer dependency enforcement:** A new `.npmrc` file has been added to enforce strict peer
  dependency rules, improving consistency and preventing potential dependency conflicts during development.
- 🚀 **Refined Pnpm dependency overrides:** New `pnpm.overrides` have been added for `@vueuse/router` to specifically pin
  `vue-router` to a compatible version, enhancing overall project stability.
- 📄 **Configured Pnpm peer dependency allowances:** Explicitly allowed specific versions of peer dependencies for key
  packages like `@nuxt/schema`, `apexcharts`, and `magicast`, addressing potential installation warnings or conflicts.

### Removed

- 🗑️ **Removed explicit package manager version lock:** The `packageManager` field has been removed from the `web`
  package, allowing for more flexible package manager usage and reducing configuration overhead.

______________________________________________________________________

## [v0.290.0] - 2026-05-27 - Multi-Tenancy Expansion and Frontend Monorepo Standardization

### Added

- 🛡️ **Introduced proprietary Sysadmin Plane:** New `packages/sysadmin-api` (backend) and `packages/sysadmin-web`
  (frontend) services have been added for multi-tenant administration, now shipped under a commercial license.
- 📄 **New `LICENSES.md` for explicit mixed-license model:** A dedicated document now clearly outlines the licensing for
  each package (Apache-2.0, AGPL-3.0-or-later, and Proprietary terms), significantly enhancing legal clarity.
- 🐳 **Dedicated Docker ignore file (`.dockerignore`):** A new `.dockerignore` file has been added at the repository root
  to improve Docker image build efficiency and reduce image size by excluding unnecessary development and build
  artifacts.
- 🚀 **New GitHub Actions workflow for Sysadmin Builds:** A dedicated workflow (`build-sysadmin.yml`) automates the build
  and release process for the new `sysadmin-api` and `sysadmin-web` Docker images, ensuring consistent deployment.
- 🔑 **Enhanced API `get_my_identity` endpoint:** A lightweight user identity endpoint has been introduced in the API
  (`/{tenant_id}/my-account/identity`) that omits the full access matrix, making it suitable for quick sysadmin role
  checks across different API runners.
- ⚙️ **Centralized Frontend Runtime Configuration:** A new Nuxt plugin (`0.runtime-config.client.ts`) implements
  synchronous loading of runtime configurations (OIDC, WebSocket, sysadmin URL) from a global `window.__AIHUB_CONFIG__`
  object, improving reliability and performance.
- 🤝 **Centralized Frontend API Client Configuration:** A new Nuxt plugin (`api-client.client.ts`) configures the SDK
  client globally, ensuring consistent token injection and error handling across the main and extended frontend
  applications.
- 📝 **Architectural Decision Records (ADRs) for Sysadmin Plane:** New ADRs document the rationale and consequences of
  splitting the sysadmin plane into separately licensed proprietary packages, ensuring transparency and future
  maintainability of architectural decisions.
- 💻 **IDE Run Configurations for Sysadmin Services:** Added new IntelliJ/VS Code run configurations to streamline local
  development, testing, and deployment of the `sysadmin-api` and `sysadmin-web` services.
- 🏷️ **Automated License Annotation in Docker Compose:** Generated Docker Compose files now include inline license
  comments for each service, improving license transparency directly within the deployment configuration.

### Changed

- 📦 **Frontend Monorepo Restructuring:** The main frontend application's root directory has been refactored from
  `packages/web/swiss_ai_hub_web` to `packages/web`, simplifying paths and improving monorepo consistency.
- 🛠️ **Updated Frontend Tooling Configuration:** Paths and configurations across build scripts, ESLint, Dependabot, and
  SDK generation have been adjusted to align with the new `packages/web` structure and pnpm workspace setup.
- 🔒 **Keycloak Integration for Sysadmin Plane:** Keycloak realm configurations have been updated to support Single
  Sign-On (SSO) for the new `sysadmin.${DOMAIN}` subdomain, enabling seamless authentication between the main and
  sysadmin UIs.
- 🧹 **Centralized `.gitignore` for Node.js modules:** The exclusion of `node_modules` has been moved to the repository
  root `.gitignore` for better consistency and maintainability across the monorepo.
- 📖 **Updated Documentation for Mixed Licensing:** All relevant documentation (README, arc42, user guides) has been
  revised to reflect the new mixed-license model and refer to the `LICENSES.md` for detailed terms.
- 📦 **Frontend `package.json` Updates:** The `package.json` for the `web` package has been modified to reflect its new
  name (`@swiss-ai-hub/web`), new AGPL-3.0-or-later license, and alignment with the pnpm workspace.
- ⚙️ **Frontend Docker Image Configuration:** The Dockerfile and Nginx configuration for the `web` service have been
  updated, including health checks, changing the default port to 8080, and implementing the new runtime config loading
  mechanism (`config.json` to `config.js`).

### Removed

- 🗑️ **Deprecated `TenantAdminController` from Main API:** The tenant administration API endpoints have been entirely
  migrated from the main `packages/api` to the new proprietary `packages/sysadmin-api` service.
- 🔄 **Obsolete `config-loader.client.ts` plugin:** This plugin, responsible for fetching runtime configuration, has been
  replaced by the new, more efficient `0.runtime-config.client.ts` plugin.
- 🧹 **Removed redundant Frontend `pnpm-workspace.yaml`:** The pnpm workspace configuration for the frontend is now
  consolidated at the monorepo root.
- 🚫 **Removed dedicated `sysadmin` middleware from `packages/web`:** Its functionality has been moved to the new
  `packages/sysadmin-web` service to ensure proper confinement and role-gating within the proprietary plane.
- 🗑️ **Deleted frontend `config.template.json`:** This configuration template was replaced by `config.template.js` as
  part of the new runtime configuration loading mechanism.

______________________________________________________________________

## [v0.289.23] - 2026-05-27 - API Refinements and Stability Improvements

### Refactor

- 🧹 **Centralized API Routes:** Standardized and centralized the definition of API routes for agent, process, role, and
  tenant management endpoints, improving consistency and maintainability.
- 🔄 **Enhanced Multimodal Content Handling:** Refactored the internal logic for processing multimodal chat completion
  messages, leading to clearer, more robust content resolution for OpenAI API interactions.
- ⚡️ **Modularized OpenAI Streaming:** Split the OpenAI chat completion streaming event generation into dedicated,
  reusable helper methods for improved readability and easier maintenance.
- 📄 **Standardized Error Messages:** Centralized common error messages, such as "Not authorized to view this database,"
  "Role not found," and "Tenant not found," ensuring consistent error responses across the API.
- 🧹 **Constants for Code Clarity:** Introduced dedicated constants for frequently used strings like UTC offset suffixes
  and i18n paths, enhancing code clarity and reducing magic string usage.

### Changed

- 🩹 **Improved Websocket Error Logging:** Upgraded websocket disconnection error handling to include full traceback
  information, aiding in faster diagnosis and debugging.
- 🛡️ **Centralized Role Service Error Handling:** Shifted specific error handling for missing roles from controllers to
  the `RoleService`, streamlining API responses and improving error consistency.

### Fixed

- 🐛 **Corrected Model Creation Timestamps:** Ensured that `ModelDetails` for OpenAI responses generate unique creation
  timestamps for each instance by using a default factory.

______________________________________________________________________

## [v0.289.22] - 2026-05-26 - Secure MCP Tool Integration and Robust CI/CD Pinning

### Added

- 🔑 **Introduced User-Token Passthrough for MCP Clients:** Agents can now securely connect to external Model Context
  Protocol (MCP) servers using the requesting user's bearer token, ensuring proper attribution and per-user
  authorization in external systems.
- 📄 **New Documentation on MCP Client Authentication:** Detailed guides and architecture decision records explain the
  new `auth_mode` options (`none`, `api_key`, `user_token`) for MCP connections.
- 🔒 **GitHub Actions Pinning Enforcement:** A new CI/CD job and configuration (`pinact.yml`) have been added to
  automatically verify and enforce that all GitHub Actions are pinned to specific commit SHAs, enhancing workflow
  security and stability.
- 🧪 **Comprehensive Unit Tests for MCP Authentication:** New test suites ensure the correct behavior and robust error
  handling of MCP client authentication mechanisms.

### Changed

- ⚙️ **Refined MCP Client Configuration:** The `McpClientConfig` now includes an explicit `auth_mode` field, offering
  clear choices for authentication (none, API key, user token), with improved UI presentation for the API key.
- 🔄 **`McpReactAgent` Updated for User-Token Authentication:** The core `McpReactAgent` now leverages the new
  `McpAuthResolver` to pass user tokens to MCP servers when configured for `user_token` authentication.
- 📚 **GitHub Actions README Updated:** The documentation for GitHub Actions best practices has been updated to recommend
  pinning to 40-character commit SHAs for increased stability.

### Refactor

- 🛡️ **Pinned GitHub Actions to Specific SHAs:** All GitHub Actions used in workflows and custom actions have been
  updated from major version tags to immutable 40-character commit SHAs, significantly improving the security and
  reliability of the CI/CD pipeline.
- 🧹 **Improved MCP Client Factory Logic:** The `McpClientFactory` has been refactored to support the new authentication
  modes, including explicit error handling for misconfigured connections (e.g., missing API key or user token).
- ⚡️ **Frontend Composable Optimization:** Several frontend composables have been refactored to streamline data
  fetching, removing redundant imports and simplifying their implementation.
- 🛠️ **Internal Process Dispatcher Refinement:** Logic for binding configuration to events within the process dispatcher
  has been extracted into a dedicated static method for better code organization.

______________________________________________________________________

## [v0.289.21] - 2026-05-26 - Enhanced Workflow Security and Robustness

### Refactor

- 🔒 **Improved GitHub Actions Script Security**: Refactored all CI/CD workflows to use explicit environment variables
  for GitHub event contexts, significantly enhancing script execution safety and mitigating potential command injection
  vulnerabilities.
- 🧹 **Standardized Workflow Variable Handling**: Streamlined the access of GitHub event inputs and context within
  workflow scripts, resulting in a cleaner, more consistent, and robust implementation for automated processes.

______________________________________________________________________

## [v0.289.20] - 2026-05-26 - Core Refinements and Enhanced Event Handling

### Added

- 🧪 **Comprehensive NATS Sensor Tests:** Introduced new unit tests for the **NATS Document Uploaded Sensor**,
  specifically for the event consumption logic, to ensure reliable and correct processing of messages.

### Refactor

- 🧹 **Improved S3 Error Logging:** Switched to using `logger.exception` for directory existence and listing failures in
  the **S3 Data Lake Client**, providing more detailed stack trace information for easier debugging.
- 🔄 **Streamlined SharePoint Retry Logic:** Extracted asynchronous retry and backoff logic into a dedicated helper
  method within the **SharePoint resource**, enhancing code readability and maintainability.
- ⚡️ **Modularized NATS Sensor Event Processing:** Refactored the **NATS Document Uploaded Sensor** to abstract event
  consumption, validation, and acknowledgment into a new, dedicated function, leading to clearer, more robust event
  handling.

______________________________________________________________________

## [v0.289.19] - 2026-05-26 - Improved Tenant-Aware Document Source Retrieval

### Changed

- 🚀 **Document Source Retrieval**: Updated the generation of document source URLs to explicitly include the `tenantId`,
  ensuring accurate and tenant-specific access to original documents within a multi-tenant environment.

______________________________________________________________________

## [v0.289.18] - 2026-05-22 - Enhanced Tenant Management and Robust Initialization

### Added

- 🚀 **Superuser Active Tenant Initialization:** The active tenant for the superuser is now automatically ensured during
  the database initialization process, making the initial setup more robust and consistent.

### Changed

- ⚡️ **Improved Error Logging:** Critical database initialization steps, such as role, bucket, and namespace creation,
  now utilize `logger.exception` to automatically include detailed stack trace information when errors occur,
  significantly improving diagnostic capabilities.
- 🔄 **Refined Default Tenant Selection Fallback:** The fallback logic for automatically selecting an active tenant has
  been updated to reliably choose an available tenant ID, ensuring a consistent active tenant assignment even under
  specific edge cases.

### Refactor

- 🧹 **Centralized Active Tenant Management Logic:** The core logic responsible for automatically selecting and ensuring
  a user's active tenant has been moved from `KeycloakAuthHandler` to the `KeycloakAdminService`, enhancing modularity
  and centralizing Keycloak-related administrative functions.

______________________________________________________________________

## [v0.289.17] - 2026-05-22 - OpenWebUI Upgrade and Backend Reliability Enhancements

### Changed

- ⬆️ **Upgraded OpenWebUI:** Updated the integrated OpenWebUI platform to version `v0.9.5`, incorporating its latest
  features and stability improvements across all deployment configurations.

### Fixed

- ⚡️ **Improved UI Context Synchronization:** Enhanced the reliability of UI context updates by switching from two-way
  `event_caller` to one-way `event_emitter` for JavaScript execution. This change prevents potential deadlocks that
  could occur in distributed OpenWebUI environments with Redis-coordinated session pools, ensuring smoother and more
  stable user experience.

### Removed

- 🗑️ **Cleaned Up Development Certificates:** Removed legacy `dev-cert.pem` and `dev-key.pem` files from the Traefik
  configuration, streamlining the development environment setup.

______________________________________________________________________

## [v0.289.16] - 2026-05-22 - Improved Pipeline Scheduling and Path Safety

### Added

- ✨ **Introduced `run_after_success_sensor`:** A new Dagster sensor enabling jobs to be automatically triggered upon the
  successful completion of another job, streamlining pipeline workflows and ensuring proper sequencing.
- 🚀 **New Development Workflow Commands:** Added `down-dev` to easily stop the Docker Compose development environment
  and `playground` to quickly launch the Dagster pipeline SDK demo.

### Changed

- 🔄 **Refined Pipeline Job Scheduling:** Cleanup (`remove`) jobs are now automatically triggered via a new sensor after
  their corresponding observation (`observe`) jobs succeed. This replaces their previous independent daily schedules,
  ensuring more timely and dependent cleanup operations.
- 📄 **Updated Documentation for Pipeline Triggers:** The `CLAUDE.md` documentation has been updated to describe the new
  run-status chaining mechanism for job automation.
- 🛡️ **Improved Path Traversal Prevention:** The `create_figures_folder_name` utility now includes enhanced validation
  to explicitly prevent path traversal attempts using `.` or `..` as filenames, increasing system robustness.

### Removed

- 🗑️ **Deprecated `remove_job_hour` and `remove_job_minute` parameters:** These scheduling parameters have been removed
  from various pipeline `default_definitions` as cleanup jobs are now dynamically triggered by the success of
  observation jobs.
- 🧹 **Eliminated Redundant IDE Configuration:** Removed the `.idea/modules.xml` file, streamlining repository setup for
  development environments.

______________________________________________________________________

## [v0.289.15] - 2026-05-22 - Enhanced User Identity Resolution and Teams Bot Fixes

### Fixed

- 🐛 **Teams Bot User Lookup:** Resolved a critical issue (#1314) where the Teams bot failed to authenticate users whose
  display name in Teams did not directly match their Keycloak email, by correctly resolving the user's true email via
  the Teams connector.

### Added

- ✨ **Centralized User Identity Resolution:** Introduced new `resolve_user_email` and `resolve_user_identity` methods in
  the base `CompletionHandler`. This provides a robust and consistent mechanism to determine a user's email from various
  chat platforms (e.g., Teams) and resolve their Keycloak-backed identity across all bot types.
- 🧪 **Comprehensive User Identity Tests:** Added extensive unit tests for user email and identity resolution, covering
  various scenarios and edge cases to ensure the reliability and correctness of user authentication flows.

### Refactor

- 🧹 **Unified User Identity Logic:** Consolidated the user identity resolution logic into the shared
  `CompletionHandler`, moving it from the `AgentCompletionHandler` and `OpenaiCompletionHandler`. This improves code
  reusability, maintainability, and ensures consistent user authentication across all bot implementations.

______________________________________________________________________

## [v0.289.14] - 2026-05-22 - Enhanced AI Workflow Security

### Security

- 🔒 **Strengthened Claude Code Review Workflow Security:** The automated Claude AI code review workflow is now
  restricted to run exclusively for pull requests from within the same repository and initiated by trusted contributors
  (Owners, Members, or Collaborators).
- 🔑 **Improved Claude Bot Interaction Control:** Access to trigger the Claude AI bot via comments or issues (using
  `@claude`) has been limited to repository Owners, Members, and Collaborators, enhancing control and preventing
  unauthorized invocations.

______________________________________________________________________

## [v0.289.13] - 2026-05-22 - Securely Propagate User Identity to Agents

### Added

- 🔑 **Introduced `X-AIHub-*` Header Propagation:** Implemented a new mechanism to securely propagate `X-AIHub-*`
  identity headers from incoming API requests through the NATS event bus to agent `RunContext`. This allows agents to
  perform actions on behalf of the originating user, supporting use cases like delegated authentication.
- 🔐 **`_aihub_headers` Attribute to Base Events:** Added a private attribute `_aihub_headers` to the `BaseEvent` class,
  enabling temporary storage of untrusted `X-AIHub-*` headers received from NATS messages for subsequent processing and
  validation by agent steps.
- ⚡️ **New `NATSMessageHeaders` Utilities:** Introduced `with_aihub_headers` for filtering and merging `X-AIHub-*`
  headers onto outgoing NATS messages, and `extract_aihub_headers` for safely extracting and standardizing these headers
  from incoming messages.
- 🧪 **Comprehensive Unit Tests for Header Handling:** Added new unit tests to ensure the robust and secure handling of
  `X-AIHub-*` headers across publishers and the `NATSMessageHeaders` utility.

### Changed

- 🔄 **API Request Header Extraction:** Modified the OpenAI API controller to extract `X-AIHub-*` headers from incoming
  HTTP requests, ensuring they are captured early in the request lifecycle.
- 🚀 **Event Distributor Header Forwarding:** Updated the event distributor to forward `X-AIHub-*` headers onto NATS
  control-path events (`StartEvent`, HITL/BITL responses) while intentionally excluding them from observability-only
  display events to prevent credential over-sharing.
- 📦 **Agent `RunContext` Identity Storage:** Enhanced the `AgentDispatcher` to persist extracted `X-AIHub-*` headers
  into the agent's `RunContext`, making them accessible to agent steps that require user identity for delegated
  operations.
- 📡 **NATS Publisher and Subscriber Integration:** Integrated `X-AIHub-*` header processing into both NATS Core and
  JetStream publishers and subscribers, enabling seamless propagation and extraction of these headers across the event
  bus.

______________________________________________________________________

## [v0.289.12] - 2026-05-22 - Timestamp Precision and Code Refinements

### Changed

- ⚙️ Enhanced **conversation timestamp accuracy** by switching to timezone-aware UTC datetime objects for
  `last_activity` records, ensuring more consistent timekeeping.

### Refactor

- 🧹 Streamlined **content type checks** within the content extractor, consolidating multiple `startswith` conditions for
  improved code readability.
- ⚡️ Optimized **Slack ID retrieval** by making the `_get_slack_ids` method synchronous, simplifying its execution flow.

______________________________________________________________________

## [v0.289.11] - 2026-05-22 - Core Agent Refinements and Dispatcher Improvements

### Refactor

- 🧹 **Streamlined Agent Dispatching Logic:** Extracted event normalization and handling into dedicated helper methods
  within the `AgentDispatcher` for improved modularity, readability, and maintainability of event processing.
- ⚙️ **Enhanced Multiprocess Runner Stability:** Centralized and improved the graceful shutdown mechanism for
  `MultiprocessAgentRunner` to ensure more robust and consistent stopping of agent processes.
- 🔄 **Simplified RAG Agent Preconditions:** Refined the `context_ready_for_history_limit` precondition in the RAG agent
  by removing an unnecessary parameter, leading to cleaner code.
- 📄 **Improved Module Import Clarity:** Introduced module constants for lazy imports in the MCP module, enhancing code
  readability and reducing string literal duplication.

### Changed

- 📝 **Clarified Event Tracing Behavior:** Added a comment to explain that `EventDisplayer` arguments are intentionally
  excluded from tracing, improving code documentation.

______________________________________________________________________

## [v0.289.10] - 2026-05-21 - Workflow Optimization and Release Tagging Enhancements

### Fixed

- 🔑 **Resolved Release Tagging Permissions:** Addressed an issue in the `set-latest` workflow that prevented `latest`
  git tags from being moved when workflow files were modified, by leveraging an SSH deploy key for proper
  authentication.

### Refactor

- 🧹 **Streamlined CI/CD YAML Parsing:** Replaced Python-based YAML parsing with `yq` and `jq` in the `build-agents`,
  `build-pipelines`, and `set-latest` workflows. This change utilizes pre-installed tools on the `ubuntu-slim` runner,
  enhancing workflow reliability and reducing external dependencies.

______________________________________________________________________

## [v0.289.9] - 2026-05-20 - Infrastructure Maintenance

### Changed

- ⚙️ **Updated Playwright Docker image to v1.60.0:** Upgraded the underlying browser automation engine to leverage the
  latest features, bug fixes, and performance improvements for services utilizing Playwright.

______________________________________________________________________

## [v0.289.8] - 2026-05-20 - Optimized CI/CD Workflows for Enhanced Performance

### Refactor

- 🚀 **Upgraded CI/CD Runners:** Migrated a wide range of GitHub Actions workflows from generic `ubuntu-latest` to more
  specialized and performant runners like `ubuntu-slim` and `ubuntu-24.04-arm`. This optimization targets improved
  execution speed, resource efficiency, and broader compatibility across various build and test environments.
- ⚙️ **Enhanced Test Module Flexibility:** Introduced support for matrix-based runner selection in the `Test Modules`
  workflow, enabling dynamic allocation of testing environments for different modules. This change also transitions
  testing for these modules from a dedicated `ubuntu-latest-8-cores` instance to a more standard `ubuntu-latest` (via
  matrix configuration), paving the way for future environment customizations.
- ⚡️ **Accelerated Build and Release Processes:** Key workflows such as release creation, changelog generation, license
  reporting, environment documentation, and documentation deployment are now running on `ubuntu-24.04-arm`, resulting in
  faster completion times.
- 🧹 **Streamlined Development Feedback Loops:** Linting, branch/PR semantic checks, and AI-assisted code review
  workflows have been moved to `ubuntu-slim` runners, providing quicker feedback on code quality and PR readiness.

______________________________________________________________________

## [v0.289.7] - 2026-05-20 - Improved Workflow Resilience with Configured Timeouts

### Changed

- ⚡️ **Enhanced CI/CD Job Stability:** Introduced explicit `timeout-minutes` configurations across numerous GitHub
  Actions workflows, ensuring that jobs terminate gracefully and preventing prolonged or stuck executions.

______________________________________________________________________

## [v0.289.6] - 2026-05-20 - Enhanced LLM Ecosystem and Robust Dependency Management

### Added

- 📦 **Introduced `pnpm-workspace.yaml` configurations** across frontend and documentation projects, leveraging `pnpm`'s
  native `minimumReleaseAge` for enhanced supply-chain security and consistent dependency management.
- ⚙️ Added **`onlyBuiltDependencies` configurations** for selected frontend packages to ensure compatibility with
  `pnpm 10`'s stricter default behavior regarding dependency build scripts.
- 🧪 Implemented a new **integration test suite** for LiteLLM text generation models, dynamically verifying the
  functionality and responsiveness of all advertised models on the Swiss LLM Cloud proxy.

### Changed

- 🧠 Updated the **default text generation LLM** for agents and pipelines to `text-generation/gemma-4-31B-it`, replacing
  the retired `gpt-oss-120b` for improved performance and access to the latest models.
- 🚀 Expanded the **Swiss LLM Cloud model catalog** in LiteLLM, incorporating new models such as `Kimi-K2.6`,
  `Ministral-3-14B-Instruct-2512`, and `Qwen3.5-122B-A10B-FP8`, and updating cost metrics for `gemma-4-31B-it`.
- 🔄 Enhanced **CI/CD frontend linting workflows** to utilize `corepack` for `pnpm` installation, ensuring a more
  consistent and robust dependency setup across development and automated testing environments.
- ⬆️ Upgraded the pinned **`pnpm` package manager version** to 10.20.0, contributing to improved build process stability
  and security.

### Fixed

- 🐛 Resolved **Dependabot CI failures** stemming from `pnpm` incompatibilities with Dependabot's `cooldown` mechanism by
  transitioning to `pnpm`'s native `minimumReleaseAge` feature.
- 📄 Corrected and updated **documentation** across `README.md` and `arc42` decisions to accurately reflect the latest
  available LLM models on the Swiss LLM Cloud and their usage in the platform.

______________________________________________________________________

## [v0.289.5] - 2026-05-19 - Refined Dependabot Cooldowns

### Changed

- 🔄 **Streamlined Dependabot Cooldowns:** Corrected Dependabot configurations for **Docker** and **GitHub Actions**
  ecosystems by removing unsupported `semver-minor-days` and `semver-patch-days` cooldown settings. These ecosystems
  exclusively support `default-days`, as their tags are not semver-decomposable, ensuring more accurate and effective
  dependency update management.

______________________________________________________________________

## [v0.289.4] - 2026-05-19 - Fortified Repository with Codeowners and Tuned Dependabot

### Security

- 🔑 **Implemented `CODEOWNERS` for Critical Paths:** Enforced mandatory reviews from core maintainers for changes to
  critical areas like CI/CD, deployment infrastructure, shared core packages, and security policies, significantly
  enhancing repository security and integrity.

### Changed

- ⚙️ **Refined Dependabot Update Strategy:** Overhauled Dependabot configuration to improve stability and reduce PR
  noise by switching to monthly update intervals, introducing cooldown periods for new releases, and intelligently
  grouping version and security updates.
- 📄 **Updated Contribution Guidelines:** Added clear guidance to `CONTRIBUTING.md` outlining the new `CODEOWNERS` review
  requirements for sensitive parts of the codebase.

### Refactor

- 🧹 **Adjusted Dockerfile Path in Dependabot:** Corrected the directory reference for the Playwright Docker deployment
  within the Dependabot configuration.

______________________________________________________________________

## [v0.289.3] - 2026-05-12 - Dynamic Forms and Stability Enhancements

### Fixed

- 🐛 **Fixed Number Input Validation:** Ensured FormKit validation for **`InputNumber`** elements correctly handles large
  and small decimal bounds by preventing scientific notation in validation rules.
- 🐛 **Corrected `ChipsInput` Required Logic:** Prevented **`ChipsInput`** elements from being automatically marked as
  required, acknowledging that an empty list is a valid "unset" state for list-collecting inputs.
- 🚫 **Hard-Pinned Nuxt.js to 3.21.0:** Temporarily reverted Nuxt.js to version **3.21.0** to mitigate a `vite-node` IPC
  regression that caused hangs and module resolution errors in development mode.

### Added

- ✨ **Introduced `FormKitDynamicConfiguration` Component:** Added a new, reusable Vue component to centralize dynamic
  form rendering logic, including repeater handling and locale string support, for consistent UI across agent and
  process configurations.
- 🦾 **New `seedFormDefaults` Helper:** Implemented a new composable function to recursively apply backend Pydantic
  default values to form data, ensuring fields are correctly pre-filled upon initialization.
- 🧪 **Expanded Form Validation Tests:** Added comprehensive unit tests for **`InputNumber`** validation bounds
  (integers, floats, large, and small decimals) and verified **`ChipsInput`** requirement logic, improving form
  reliability.
- 📄 **Documented Nuxt Hard-Pin Decision:** Added an Architecture Decision Record (ADR) explaining the rationale,
  consequences, and exit criteria for hard-pinning Nuxt.js to version 3.21.0.

### Refactor

- 🔄 **Streamlined Agent and Process Configurations:** Replaced internal form handling logic in `Agent/Configuration.vue`
  and `Process/Configuration.vue` with the new reusable **`FormKitDynamicConfiguration`** component, reducing code
  duplication.
- ⚡️ **Enhanced Dynamic Form Stability:** Implemented `preserve: true` and unique `key` attributes across FormKit groups
  and inputs to prevent data loss and improve rendering stability during conditional display or re-rendering.
- 🧹 **Optimized Form Instance Data Initialization:** Refined the data hydration and default seeding logic when creating
  new agent or process instances, ensuring consistent and correct form state.

______________________________________________________________________

## [v0.289.2] - 2026-05-12 - Refined Backup Orchestration and CI Scopes

### Fixed

- 🐛 **Dagster Backup Asset Dependencies:** Corrected the execution order of Dagster backup maintenance assets to ensure
  the `postgres_autovacuum_tune` process runs after `postgres_indexes`, preventing potential deadlocks and enhancing the
  reliability of backup workflows.

### Changed

- ⚙️ **CI/CD Semantic Commit Scope:** Added `backup` as an allowed scope for semantic commit messages within CI/CD
  workflows, enabling clearer categorization and validation of changes related to the backup system.
- 📄 **Developer Documentation:** Updated the `CLAUDE.md` documentation to reflect the newly introduced `backup` scope
  for semantic commit messages, guiding developers on proper commit conventions.
- 🧪 **Backup Maintenance Tests:** Updated unit tests to accurately validate the corrected dependency ordering of backup
  maintenance handlers, including the new dependency of `postgres_autovacuum_tune` on `postgres_indexes`.

______________________________________________________________________

## [v0.289.1] - 2026-05-12 - Dependency Management & Stability Enhancements

### Changed

- 📄 Streamlined **Dependabot configuration** by excluding Python base images from automatic major version bumps,
  allowing for more deliberate and controlled updates of core environments.
- 🔄 Relaxed the **Llama-index-core dependency constraint** in the core package to permit compatible minor version
  updates, providing greater flexibility for patch releases.
- ⬆️ Updated the **Hugging Face Hub dependency** for development tools, streamlining its integration and removing an
  unnecessary `[cli]` extra.

### Fixed

- 🐛 Introduced a **pnpm override for @ungap/structured-clone** across documentation and web packages to ensure specific,
  stable versions of transitive dependencies are utilized, enhancing overall stability.

______________________________________________________________________

## [v0.289.0] - 2026-05-12 - Next-Gen Memory Scoping and Agent Templates for Expert Agents

### Added

- ✨ **Agent Templates**: Introduced a new templating system for `ExpertAskingAgent` and `ExpertRAGAgent`, making it
  easier to deploy and configure specialized agents for various use cases.
- 🦾 **Engineering Expert Agent Templates**: Shipped default `Engineering Expert` and `Engineering Expert RAG` agent
  templates, providing ready-to-use configurations for escalating and answering technical questions.
- ⚙️ **Granular Organization Memory Scoping**: Added new configuration objects (`OrgMemoryReadConfig`,
  `OrgMemoryWriteConfig`) allowing agents to define `default_tenant_namespace` and `allowed_tenant_namespaces` for
  precise control over knowledge access.
- 📝 **Configurable Organization Memory Format**: `ExpertAskingAgent` now supports a configurable `org_memory_format`
  template, enabling custom Q&A snippets to be stored in organization memory.
- 🎛️ **New Form Components**: Introduced `ChipsInput` for intuitive list input (e.g., allowed namespaces) and
  `OrgMemoryTenantInput` which integrates built-in authorization checks for organization memory fields directly into the
  UI.
- 🔑 **Authorization for Organization Memory**: Implemented client-side configuration authorization checks for
  organization memory settings, ensuring users only configure resources they have access to.
- 📄 **Detailed Environment Variable Descriptions**: Added comprehensive descriptions and default values for many backup,
  Milvus, NATS, Redis, and S3 storage-related environment variables in the deployment guide, improving clarity.

### Changed

- 🔄 **Refined Organization Memory APIs**: Updated internal organization memory APIs and event structures to support
  granular namespace lists, moving from a single `tenant_namespace` string to a list of `tenant_namespaces` for search
  and a specified singular namespace for writes.
- 🧹 **Streamlined Reranking Configuration**: Simplified the configuration for document reranking in RAG agents, making
  it more straightforward to enable or disable the feature.
- 📋 **Environment Variable Renaming for Consistency**: Renamed several backup-related environment variables (e.g.,
  `DAGSTER_DB` to `BACKUP_DAGSTER_DB`) to ensure consistent naming conventions across the platform and documentation.
- 🖼️ **Vector Store UI Improvement**: Refactored the "Allowed metadata filter fields" input in the vector store
  configuration to utilize the new `ChipsInput` component for a more user-friendly experience.

### Refactor

- 🗑️ **Consolidated Memory Configuration**: The `MemoryConfig` class has been removed and its functionality split into
  `UserMemoryConfig` and `OrgMemoryReadConfig`/`OrgMemoryWriteConfig` for clearer separation and management of
  user-scoped and organization-scoped memory settings.
- ⚙️ **Internal `.gitignore` Enhancements**: Added `.claude/*.lock` to `.gitignore` to prevent unnecessary lock files
  from being tracked.

______________________________________________________________________

## [v0.288.1] - 2026-05-11 - Streamlined Environment Configuration and Validation

### Added

- 📄 **Introduced a comprehensive, auto-generated environment variables reference page** in the documentation, providing
  a single source of truth for all configurable settings.
- 🚀 **Implemented automated consistency checks** for environment variables against Docker Compose configurations and
  Pydantic settings during PR analysis and release workflows, enhancing deployment reliability.
- 🔑 **Integrated Keycloak OAuth2 Proxy client for the Backup Dagster UI**, enabling secure, centrally managed access to
  backup management interfaces.
- 💾 **Added explicit support for Azure Data Lake Storage, Azure Document Intelligence, and SharePoint** by introducing
  dedicated environment variables for their configurations, facilitating data ingestion from these sources.
- 🔐 **Introduced new internal environment variables for NATS and Redis/Valkey tokens**, improving security and granular
  configuration control for these messaging and caching services.
- 👷‍♀️ **New `check-env` and `generate-env-docs` Makefile targets** for manual execution of environment validation and
  documentation generation.

### Changed

- 📝 **Reorganized the `.env.dev` file structure**, moving host-side development overrides to a dedicated section for
  improved clarity and maintainability.
- 🔄 **Standardized OAuth2 Proxy provider display names to "Keycloak"** across various services in Docker Compose
  templates, ensuring a consistent user experience.
- ⚙️ **Made Mem0 model names fully configurable** via environment variables (`MEM0_LLM_NAME`,
  `MEM0_EMBEDDING_MODEL_NAME`, `MEM0_RERANKING_MODEL_NAME`) in Docker Compose, offering greater flexibility for AI model
  selection.
- 🔄 **Updated the default `AIHUB_STARTUP_TENANT_ID`** from `'swiss_ai_hub'` to `'default'` for a more generic initial
  platform setup.
- 🔒 **Hardcoded the Langfuse `NEXTAUTH_URL`** directly within Docker Compose templates based on the deployment stage
  (dev/prod), simplifying configuration by removing reliance on an `.env` variable for this specific setting.
- 📈 **Fixed pgbouncer pool size values** to constant values within Docker Compose, removing optional environment
  variable overrides for these specific parameters.
- 📚 **Improved documentation comments** within `.env.dev` to more clearly explain sections and variable usage.
- 🧹 **Added root-level Ruff configuration** to `pyproject.toml` for consistent code formatting across repository-level
  scripts.

### Removed

- 🗑️ **Removed the redundant `WEBUI_SECRET_KEY` environment variable**, as its functionality is now consolidated under
  `OPENWEBUI_SECRET_KEY`.
- ❌ **Eliminated deprecated fake authentication variables** (`DANGEROUS_DEV_ONLY_AUTH_FAKE_*`) previously used for
  development-only testing.
- 🗑️ **Removed the explicit `AIHUB_CREATE_DEFAULT_ROLES` environment variable**, as role creation now defaults to `True`
  within the application code.
- 🗑️ **Removed `OAUTH_AUTHORITY_URL`** from `.env.prod`.

### Refactor

- 🧹 **Centralized environment variable management logic** into new Python modules (`env_check.py`, `env_docs.py`,
  `env_inventory.py`) to streamline validation, documentation generation, and overall configuration handling.

______________________________________________________________________

## [v0.288.0] - 2026-05-11 - Streamlined Optional Form Fields and Configuration Management

### Refactor

- 🔄 **Revised Form Optionality Handling:** Overhauled how optional form fields are managed, replacing explicit
  `enabled: bool` flags with Pydantic's `T | None` annotations for improved data model clarity and consistency. This
  architectural change is documented in `2026_05_07_nullable_form_fields_over_enabled_toggle.md`.
- 🦾 **Unified UI Toggle Management:** Integrated UI toggle logic directly into the form framework, automatically
  generating enable/disable checkboxes for nullable fields and groups. This standardizes the user experience and
  significantly reduces boilerplate for optional settings.

### Changed

- ⚡️ **Simplified Agent Reranking Configuration:** Updated RAG and Expert RAG agents to leverage the new nullable field
  system, removing the dedicated `enabled` field from `RerankingConfig` and simplifying internal logic to check for
  `is not None`.
- 🧹 **Cleaned Agent Configuration Data:** Agent configurations now store `null` for disabled optional sub-forms, leading
  to smaller, more readable persisted data by eliminating stale default values.
- 🚀 **Enhanced Frontend Form Data Processing:** Introduced new `seedNullableToggles` and `coerceNullableToggles`
  functions to intelligently initialize and submit form data, correctly managing the state of auto-generated nullable
  field toggles in the UI.

### Removed

- 🗑️ **Eliminated Redundant `enabled` Fields:** The dedicated `enabled` boolean fields in `RerankingConfig` and other
  optional sub-configurations have been removed, as their functionality is now implicitly handled by the form framework
  based on `T | None` annotations.
- 📄 **Deprecated Reranking UI Conditions and Translations:** Removed `condition_if` properties that previously linked to
  the `reranking_config_enabled` field, along with their associated internationalization strings, simplifying the UI
  schema.

______________________________________________________________________

## [v0.287.3] - 2026-05-11 - Improved Memory Management API

### Refactor

- 🧹 **Streamlined Memory Operations:** Refactored memory update and delete functions to automatically derive the
  **tenantId** from the application context, simplifying API calls and improving consistency for developers.

______________________________________________________________________

## [v0.287.2] - 2026-05-11 - RAG Agents: Richer Context with Image Support

### Changed

- 🖼️ **Enhanced Context Sufficiency Guard**: RAG agents now pass the full `ChatMessage` objects, including images and
  other rich content, to the context sufficiency guard, allowing Large Language Models (LLMs) to process multimodal
  information more effectively.
- 💬 **Improved Chat History Forwarding**: The chat history sent to the context sufficiency guard now retains its full
  `ChatMessage` structure, enabling more accurate and rich conversational context for LLMs.

### Refactor

- 🧹 **Updated Guard Prompting Mechanism**: Switched the internal context sufficiency guard from `PromptTemplate` to
  `RichPromptTemplate` to support dynamic rendering of multimodal `ChatMessage` objects within LLM prompts.
- ⚙️ **Standardized Context Parameter**: Refactored the `do_context_sufficient_guard` function across RAG agents to
  consistently accept a `ChatMessage` object for context, rather than a flattened string.

______________________________________________________________________

## [v0.287.1] - 2026-05-11 - Optimized Vector Store Queries with Namespace Scoping

### Changed

- ⚡️ **Optimized Vector Store Node Retrieval:** Enhanced the efficiency of node retrieval across the platform by
  propagating **namespace** information down to the vector store. This change, applied in the **Knowledge Service**,
  **Parent Summary Post-Processor**, and **Vector Previous/Next Post-Processor**, ensures that queries are scoped to
  specific data partitions, significantly improving performance and data isolation in multi-tenant environments.
- 🔄 **Updated `PartitionAwareMilvusVectorStore`:** The `get_nodes` method in the `PartitionAwareMilvusVectorStore` now
  explicitly accepts a `namespaces` argument, allowing for more precise and efficient querying within designated data
  partitions.

### Added

- ✅ **Introduced Namespace Filter Propagation Tests:** Added new unit tests to verify the correct forwarding and
  application of namespace filters within vector store post-processors, ensuring the reliability of partition-aware data
  retrieval.

______________________________________________________________________

## [v0.287.0] - 2026-05-11 - Enhanced Memory Configuration for RAG Agents

### Added

- ✨ **Granular Memory Reranking Control**: Introduced new configuration options to enable or disable reranking
  specifically for both **organization memory** and **user memory** searches. This provides greater control over
  retrieval relevance and performance, allowing users to optimize for latency or accuracy as needed.

### Refactor

- 🧹 **Consolidated RAG Agent Memory Configuration**: Centralized all memory-related settings (including organization
  memory enablement, user memory retrieval/storage, tenant ID, and namespace) into a new, dedicated **`MemoryConfig`
  object**. This significantly streamlines agent configuration, improves readability, and simplifies future
  enhancements.
- 🔄 **Updated Agent Memory Access**: RAG agents and their preconditions now access all memory-related settings through
  the consolidated `MemoryConfig` object, ensuring consistent and organized handling of memory configurations across the
  system.

______________________________________________________________________

## [v0.286.8] - 2026-05-08 - Internal Maintenance

______________________________________________________________________

## [v0.286.7] - 2026-05-08 - Streamlined OAuth Configuration and Enhanced Tenant Setup

### Added

- ⚙️ **Introduced Startup Tenant Configuration:** New environment variables (`AIHUB_STARTUP_TENANT_ID`,
  `AIHUB_STARTUP_TENANT_NAME`, `AIHUB_STARTUP_TENANT_DESCRIPTION`, `AIHUB_STARTUP_TENANT_ACCESS_RULES`) have been added
  to support initial setup and management of a default "startup tenant", providing more granular control over Keycloak
  realm integration.

### Changed

- 🔄 **Standardized OAuth Authority URL Configuration:** The `OAUTH_AUTHORITY_URL` is now dynamically configured based on
  the deployment stage. It automatically points to `http://localhost:8180/realms/aihub` for development environments and
  `https://auth.${DOMAIN}/realms/aihub` for all other stages, simplifying setup and reducing manual configuration.

______________________________________________________________________

## [v0.286.6] - 2026-05-08 - Enhanced Backup Robustness and Configurability

### Added

- ✨ **Configurable PostgreSQL Backup Timeout**: Introduced `BACKUP_POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` (defaulting to 6
  hours) to allow operators to adjust the timeout for PostgreSQL dump and restore operations, preventing failures on
  large databases.
- ⚡️ **NATS Subprocess Retry Mechanism**: Implemented retry logic for NATS CLI commands within the backup process,
  enhancing resilience against transient connection issues or server restarts.

### Changed

- 🔄 **Standardized Backup Service Environment Variables**: All environment variables specific to the backup service are
  now explicitly prefixed with `BACKUP_` in Docker Compose configurations for clearer separation and identification.
- 🦾 **Improved NATS Readiness Probing**: The NATS readiness check now probes JetStream's `stream list` command instead
  of a basic RTT, providing a more accurate assessment of NATS service availability before proceeding with backups.
- 📄 **Updated Backup Container Exclusion List**: Added `oauth2proxy` services to the list of containers that remain
  running during a backup, ensuring the backup Dagster UI remains accessible through OAuth.

### Fixed

- 🐛 **Resolved PostgreSQL Backup Timeout Issues**: Addressed scenarios where PostgreSQL backups of large databases could
  time out due to a previously fixed 5-minute subprocess limit, which is now configurable via the new
  `BACKUP_POSTGRES_SUBPROCESS_TIMEOUT_SECONDS` environment variable.
- 🐛 **Mitigated Transient NATS Connection Failures**: Enhanced NATS operations with retry logic, reducing backup
  failures caused by temporary NATS server unavailability during runs.

### Refactor

- 🧹 **Streamlined Internal Backup Settings Handling**: The internal `BackupSettings` class now automatically handles the
  `BACKUP_` prefix for environment variables, improving consistency and reducing boilerplate in the configuration.

______________________________________________________________________

## [v0.286.5] - 2026-05-06 - Enhanced Dependency Update Management

### Changed

- 🚫 **Disabled Automatic Major Dependency Updates:** Configured Dependabot to explicitly ignore major version bumps
  across all dependencies, ensuring that significant upgrades are handled with deliberate, planned migrations rather
  than automatically.
- 🔄 **Streamlined Dependabot Grouping and Logic:** Consolidated Python and Web dependency update groups and standardized
  grouping patterns across all ecosystems for minor and patch updates, reducing PR noise and clarifying update bundles.
- 📝 **Enhanced Dependabot Configuration Documentation:** Updated comments within the `dependabot.yml` file to provide
  clearer explanations of Dependabot's grouping behavior, uniqueness enforcement, and the updated major version update
  policy.

______________________________________________________________________

## [v0.286.4] - 2026-05-06 - Optimized Milvus Vector Store for Scalable RAG

### Added

- 🧪 **Unit Tests for Filter Logic:** Introduced comprehensive unit tests for the namespace filter extraction logic
  within the `PartitionAwareMilvusVectorStore`, ensuring its correctness and robustness for partition-aware operations.

### Changed

- 🚀 **Enhanced Milvus Partition Loading:** Optimized the `PartitionAwareMilvusVectorStore` to intelligently load only
  necessary Milvus partitions during `add`, `query`, `get_nodes`, and `delete` operations. This significantly reduces
  memory consumption and improves performance for large-scale RAG systems by avoiding full collection loads.

### Fixed

- 🐛 **Robust Namespace Filter Extraction:** Addressed an issue in the `PartitionAwareMilvusVectorStore` where nested
  `MetadataFilters` might not have been correctly parsed, potentially leading to inefficient full collection loads
  during queries. Namespace extraction is now more robust, ensuring precise partition targeting.

### Refactor

- 🧹 **Project Structure Modularization:** The IntelliJ IDEA project configuration has been updated to reflect a more
  modular structure, with separate module files for different components like agent, api, core, and pipeline.

______________________________________________________________________

## [v0.286.3] - 2026-05-05 - Build Process Modernization and Dependency Streamlining

### Changed

- ⚡️ **Updated Node.js Base Image:** Migrated the Docker build environment from the Long-Term Support (LTS) Node.js
  version to the latest Node.js v25, enabling access to current features and performance enhancements.

### Refactor

- 🧹 **Modernized Corepack and pnpm Setup:** Re-engineered the Dockerfile's dependency management strategy to explicitly
  install Corepack and leverage its `corepack install` command, ensuring the use of the exact pnpm version defined in
  `package.json` for improved consistency.
- 🔑 **Improved Build Environment Security:** Enhanced the build process by pinning Corepack to a specific version and
  removing potential conflicts from pre-shipped Yarn shims, contributing to a more secure and reliable build.

______________________________________________________________________

## [v0.286.2] - 2026-05-05 - Streamlined Release Promotion and Smart Versioning

### Added

- ✨ **New Release Promotion Workflow:** Introduced a dedicated GitHub Actions job to explicitly promote pre-releases to
  full "latest" status, ensuring consistency across Git tags, Docker images, and GitHub Releases.

### Changed

- 🚀 **Phased GitHub Releases:** New GitHub releases are now initially marked as pre-releases, allowing for a controlled
  testing period before official promotion to "latest."
- 🔍 **Smarter Installer Version Resolution:** The `install.sh` script now intelligently distinguishes between official
  "latest" releases and pre-releases, prioritizing promoted versions while gracefully falling back to the most recent
  pre-release if no official "latest" is yet available.

______________________________________________________________________

## [v0.286.1] - 2026-05-05 - Enhanced Build Stability and Dependency Optimization

### Changed

- 🛡️ **Strengthened Agent Build Validation:** The CI/CD pipeline now enforces stricter validation for agent builds. All
  individual agent builds within a matrix must successfully complete for the entire workflow to pass, preventing silent
  partial failures.

### Fixed

- 🐛 **Resolved `apache-age-python` Dependency Issue:** Eliminated an unnecessary transitive dependency on
  `apache-age-python` (pulled by `mem0ai[graph]`), which previously caused build complications due to its `psycopg2`
  requirement for system libraries. This improves build reliability and streamlines dependency management.

______________________________________________________________________

## [v0.286.0] - 2026-05-04 - Infrastructure Modernization and Dependency Upgrades

### Changed

- 🛠️ **Modernized CI/CD Infrastructure**: Upgraded core GitHub Actions, including `checkout`, `setup-python`,
  `setup-node`, and artifact management, to enhance build reliability, performance, and security across all workflows.
- 🚀 **Advanced Platform Technologies**: Updated Node.js runtime versions across development environments and Docker
  images, providing a more current and efficient foundation for frontend services and CI processes.
- ✨ **Enhanced Web Application Dependencies**: Performed comprehensive updates to key frontend libraries and frameworks,
  including significant version bumps for `FormKit` and `Pinia Colada`, ensuring the web application benefits from the
  latest features and stability.
- 🧩 **Improved Development and Testing Toolchain**: Upgraded essential development dependencies such as `pytest`,
  `ruff`, and `Playwright`, leading to a more robust testing framework and optimized code quality checks.
- 📄 **Modernized Documentation Dependencies**: Updated various documentation-related packages like `vitepress`,
  `mermaid`, and `cytoscape` to ensure the documentation platform remains current and performant.

### Refactor

- 🔄 **Refined Test Mocking**: Enhanced the flexibility of `aiohttp` request mocks in bot playground tests to improve
  test resilience and adaptability to evolving API interactions.
- 🔒 **Standardized Dependency Constraints**: Applied a precise version constraint for the `mem0ai[graph]` dependency to
  ensure compatibility and prevent unintended breaking changes from future major releases.

______________________________________________________________________

## [v0.285.4] - 2026-05-04 - Enhanced Authentication Robustness and Performance

### Fixed

- 🐛 **Resolved OpenWebUI authentication issue (Issue #1050):** Fixed a bug where authentication failed for proxied users
  if the underlying bearer token was owned by a service account without tenant membership, even when the proxied user
  had valid tenant associations. Token verification is now correctly decoupled from the token owner's tenant context.
- ✅ **Added comprehensive regression tests:** New end-to-end tests for the OpenWebUI authentication handler confirm the
  fix for issue #1050, and additional unit tests for `TokenAuthHandler` ensure robust token verification.

### Changed

- ⚡️ **Optimized user and role retrieval:** Keycloak calls for fetching user details and realm roles in
  `TokenAuthHandler` are now executed concurrently using `asyncio.gather`, improving authentication performance.

### Refactor

- 🧹 **Decoupled token verification:** The authentication process has been refactored to clearly separate the initial
  validation of a bearer token from the subsequent resolution of the associated user's details and tenant context,
  enhancing modularity and robustness.
- 🔄 **Renamed `BearerAuthHandler` to `TokenAuthHandler`:** The core bearer authentication handler has been renamed for
  improved clarity and consistency across the codebase.

______________________________________________________________________

## [v0.285.3] - 2026-05-04 - Refined Image Management for Deployment Builds

### Refactor

- 🧹 **Streamlined Image Configuration**: Simplified the `compose-config.yml` by removing redundant `build: localbuild`
  directives and stage-specific image tags for project-managed images like **Postgres** and **Playwright**. These images
  are now consistently referenced by their pinned, pre-built tags across all deployment stages.
- 🔄 **Enhanced Image Tagging Automation**: Refined the internal logic for identifying and tagging images during
  releases, ensuring that only actively rebuilt **application images** (those marked for per-release publishing) are
  updated with the `:latest` tag. Project-managed base images with specific version pins are now explicitly excluded
  from this automatic retagging process.
- 📦 **Reorganized Playwright Dockerfile**: Moved the **Playwright Dockerfile** to a more logical and standardized
  location within the `infra/deployment/docker` directory, improving project structure and maintainability.
- ⚙️ **Simplified Docker Compose Generation**: The internal templates for generating Docker Compose files have been
  updated, removing conditional build instructions for **Postgres** and **Playwright** services. These services now
  uniformly pull their pre-built, version-pinned images from the registry.

### Changed

- 📄 **Clarified Postgres Image Documentation**: Updated the documentation for the **Postgres image** within `CLAUDE.md`
  to explicitly describe it as a project-managed image that is published out-of-band and consumed with a pinned tag,
  providing clearer guidance on its lifecycle.

______________________________________________________________________

## [v0.285.2] - 2026-05-04 - Enhanced Release Workflow for Protected Branches

### Changed

- ⚙️ **Streamlined Release Finalization**: The `add-tag.yml` GitHub Actions workflow now utilizes a dedicated deploy key
  for repository checkout. This enhancement ensures the workflow can successfully amend merge commits and force-push to
  the protected `main` branch, improving the reliability and integrity of the release finalization process.

______________________________________________________________________

## [v0.285.1] - 2026-05-04 - Automated Dependency Management and CI/CD Streamlining

### Added

- ✨ **Automated Dependency Management:** Introduced **Dependabot** configuration to automatically detect and create pull
  requests for dependency updates across Python, Node.js (frontend, docs, E2E), Docker base images, and GitHub Actions,
  significantly enhancing project maintainability and security.

### Changed

- 📄 **Improved Documentation:** Updated the description for the `github_token` input in the backend linting action,
  clarifying its specific use by **reviewdog** for posting review comments.

### Refactor

- 🧹 **Optimized Pull Request Checks:** Configured **semantic PR checks** to bypass title linting and version label
  requirements specifically for Dependabot-generated pull requests, streamlining the process for automated dependency
  updates.

### Removed

- 🗑️ **Streamlined CI/CD Workflows:** Eliminated explicit **Git SSH key configuration** steps from various GitHub
  Actions workflows, simplifying pipeline setup and reducing configuration overhead.

______________________________________________________________________

## [v0.285.0] - 2026-04-29 - Introducing Self-Hosted Web Search (SearXNG) and Playwright Update

### Added

- ✨ **Self-Hosted Web Search with SearXNG:** Integrated a self-hosted [SearXNG](https://docs.searxng.org/) meta-search
  instance, providing privacy-aware web search capabilities directly within the platform. This offers greater control,
  eliminates per-query costs, and ensures auditable egress for web queries.
- 📄 **Comprehensive Web Search Documentation:** Added a new, detailed documentation guide explaining how Open-WebUI
  leverages SearXNG for web search, including the curated list of privacy-first search engines, customization options,
  and instructions on how to disable the feature.
- 🔑 **New `SEARXNG_SECRET_KEY` Environment Variable:** Introduced a new environment variable to secure the self-hosted
  SearXNG instance, enhancing operational security.

### Changed

- 🔄 **Switched Web Search Provider to SearXNG:** The platform's web search functionality now exclusively uses the
  integrated SearXNG service, transitioning away from the previous Jina AI integration.
- 🌐 **Updated Network Requirements for Web Search:** The documentation for network requirements has been updated to
  reflect the new set of upstream search engines (e.g., Brave, DuckDuckGo, Mojeek, Qwant, Startpage, Wikidata,
  Wikipedia) queried by SearXNG.
- 🚀 **Playwright Updated to v1.58.0:** Upgraded the Playwright browser automation library to version `v1.58.0`, ensuring
  compatibility with the latest browser features and security updates for web browsing services.

### Removed

- 🗑️ **Removed Jina AI Integration:** The dependency on Jina AI for web search has been entirely removed from the
  platform, including its associated API key configuration.

______________________________________________________________________

## [v0.284.2] - 2026-04-29 - API Documentation Refinements and Localization Improvements

### Changed

- ✨ **Enhanced OpenAPI Tag Generation:** The API documentation (Swagger UI) now comprehensively includes tags for all
  mounted controllers and intelligently prevents duplicate tag entries, providing a more complete and accurate overview
  of available API endpoints.
- 🌍 **Localized API Endpoint Tags:** Switched API endpoint tags from hardcoded strings to dynamically generated,
  internationalized strings, significantly improving multi-language support and consistency for API documentation.

______________________________________________________________________

## [v0.284.1] - 2026-04-28 - Optimized LiteLLM Logging for Pipeline Efficiency

### Added

- ✨ **Introduced pipeline LLM message redaction:** Significantly reduces LiteLLM spend log database size by redacting
  message content from pipeline-originated LLM calls (e.g., embeddings) while preserving essential cost and token
  tracking. This prevents database bloat from high-volume, reproducible pipeline traffic.
- 📄 **Documented LiteLLM message redaction decision:** Added an Architecture Decision Record (ADR) detailing the
  rationale, drivers, and consequences of implementing pipeline message redaction.

### Changed

- 🚀 **Upgraded LiteLLM proxy version:** Updated the LiteLLM proxy to `v1.83.10-stable` to enable the new message
  redaction header and incorporate other upstream improvements.
- 🔄 **Enhanced LLM configuration flexibility:** Core LLM and Embedding Model configurations now support injecting custom
  HTTP headers, enabling fine-grained control over LiteLLM proxy interactions for specific call types.
- ⚙️ **Applied redaction to pipeline LLM resources:** Configured all pipeline-related LLM, embedding, and table
  refinement resources to automatically send message redaction headers, ensuring efficient log management for data
  processing workflows.

### Fixed

- 🐛 **Resolved LiteLLM user service compatibility:** Adjusted user key retrieval logic to correctly handle HTTP 404
  responses from the updated LiteLLM proxy when a user does not exist, ensuring robust user management.

______________________________________________________________________

## [v0.284.0] - 2026-04-28 - Introducing Continuous Postgres Maintenance for Dagster

### Added

- ✨ **Automated Dagster Database Maintenance:** Launched a comprehensive subsystem within the existing backup Dagster
  instance to keep the `dagster` database bounded and healthy over long-running deployments. This includes:
  - 🧹 **Weekly Log Cleanup:** A new `dagster_cleanup_job` that automatically prunes verbose Python logs (DEBUG, INFO,
    WARNING) and transient framework-internal events (e.g., `HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`) from the
    `event_logs` table, based on configurable retention policies.
  - 📦 **Monthly Disk Space Reclamation:** A `postgres_repack_job` that runs `pg_repack` on heavy tables like
    `event_logs`, `runs`, and `job_ticks` to physically return unused disk pages to the operating system.
  - 🛡️ **UI-Safe Pruning Guarantees:** The cleanup process is meticulously designed to *never* delete critical data
    required by the Dagster UI, such as asset materializations, step success/failure records, run history, or asset
    catalog entries.
  - ⚙️ **Configurable Retention & Batch Limits:** New environment variables (`DAGSTER_DEBUG_LOG_RETENTION_DAYS`,
    `DAGSTER_INFO_LOG_RETENTION_DAYS`, `DAGSTER_WARNING_LOG_RETENTION_DAYS`, `DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS`,
    `DAGSTER_CLEANUP_BATCH_LIMIT`, `MAINTENANCE_DISABLED`) provide fine-grained control over retention windows, cleanup
    performance, and a kill switch for maintenance.
- 🐳 **Custom Postgres Image with `pg_repack`:** Integrated a project-managed Postgres Docker image
  (`pgvector-repack:pg17`) that extends the base `pgvector` image with the `postgresql-17-repack` extension, a
  prerequisite for efficient disk space reclamation.
- ✅ **Extensive Testing for Database Maintenance:** Added new layers of unit and integration tests, including SQL
  contract tests against a real Postgres instance, to ensure the correctness and safety of the new maintenance
  subsystem.

### Changed

- 🔄 **Serialized Postgres Operations:** Implemented tag-based concurrency limits using Dagster's `QueuedRunCoordinator`
  for all Postgres-affecting jobs (backup, restore, cleanup, and repack). This ensures these critical operations run
  sequentially, preventing conflicts and improving system reliability.
- 📄 **Enhanced Documentation for Data Retention & Maintenance:** Updated architecture decision records (`arc42`) and
  user guides with detailed explanations of the new continuous Postgres maintenance subsystem, covering its purpose,
  configuration, safety guarantees, and operational implications.
- 🕰️ **Dagster Tick History Retention:** Configured automatic retention policies for Dagster job and sensor tick history
  in both the main and backup Dagster instances, preventing unbounded growth of internal tick metadata.
- ⚙️ **Streamlined Image Management:** Updated internal infrastructure configurations and `Makefile` targets for
  building and publishing project-managed Docker images (Postgres and Playwright), allowing for local builds in
  development and consistent pulls in other stages.

______________________________________________________________________

## [v0.283.0] - 2026-04-28 - Smarter Image Handling with Perceptual Deduplication

### Added

- ✨ **Introduced Perceptual Deduplication for Images:** Implemented new logic to perceptually hash images during
  document processing, enabling the identification and reuse of identical or near-identical figures (e.g., logos) to
  significantly reduce storage and upload overhead.
- 🧮 **Enabled Content-Addressed Filenaming:** Uploaded image files are now named using a SHA256 content hash, which
  ensures idempotency and automatically collapses bytewise duplicate images.
- 🖼️ **Enhanced Image Format Detection:** Improved the mechanism for determining appropriate image file extensions,
  leveraging data URI MIME types, original filenames, and robust PIL sniffing.
- 🧪 **Added Comprehensive Image Processing Tests:** A new dedicated test suite ensures the reliability and correctness
  of image extraction, hashing, and upload functionalities.

### Changed

- 🚀 **Optimized Image Upload Workflow:** The `extract_and_upload_images` utility now intelligently processes images,
  checking for perceptual matches against previously uploaded figures before initiating new S3 uploads.
- 📄 **Standardized Markdown Figure Tags:** Markdown image references are now consistently wrapped in `<figure>` tags
  after being uploaded to S3, improving semantic structure.

______________________________________________________________________

## [v0.282.0] - 2026-04-28 - Granular RAG Execution Outcomes for Better Visibility and Control

### Added

- ✨ **Introduced Granular RAG Stop Events:** New event types (`RAGSuccessStopEvent`, `RAGFailureStopEvent`, and
  `RAGStopEvent` as their common ancestor) and an associated `RAGFailureReason` enumeration have been added. These
  provide detailed and specific outcomes for Retrieval-Augmented Generation (RAG) agent runs, distinguishing between
  successful responses and various failure conditions.
- 🦾 **Implemented `do_finalize_rag_stop` Logic:** A new step function, `do_finalize_rag_stop`, was introduced to
  intelligently determine the final RAG outcome. It consolidates information from the LLM's response and any prior
  rejection events (such as few-shot rejection, insufficient context, or expert decline/error) to emit the most
  appropriate RAG stop event.
- 🌐 **Integrated RAG Outcome Display in UI:** Dedicated UI components and internationalized messages have been added to
  visually represent RAG success and various failure events within the application, offering clearer, contextualized
  feedback to users.

### Changed

- 🔄 **Updated RAG Agent Termination Flow:** Both the RAG and Expert RAG agents now utilize the new `RAGSuccessStopEvent`
  or `RAGFailureStopEvent` for run termination, replacing the generic `StopEvent`. This change provides richer, more
  contextualized information about the completion status of agent runs.
- 💬 **Improved Expert RAG Agent Error Handling:** The Expert RAG agent's internal response paths for when an expert
  declines to answer or encounters an error now explicitly emit a `RAGFailureStopEvent` with a specific reason,
  enhancing the clarity of situations where a grounded answer could not be produced.
- 🛠️ **Refined Context Sufficiency Guard Logic:** The `do_context_sufficient_guard` step has been updated to correctly
  emit a `ContextInsufficientRejectEvent` when the maximum number of retrieval hops is exhausted, ensuring accurate
  reporting for ungrounded answers due to insufficient context.

______________________________________________________________________

## [v0.281.1] - 2026-04-28 - Routine Version Increment

### Changed

- 🔄 **Version alignment:** Updated the main project and all associated packages (agent, api, backup, bot, core,
  pipeline, process, web) to version `0.281.1`.

______________________________________________________________________

## [v0.281.0] - 2026-04-27 - Enhanced Dagster Data Lifecycle Management

### Added

- ✨ **Introduced Dedicated `dagster` Bucket:** A new S3 bucket named `dagster` is now automatically provisioned during
  infrastructure setup, specifically for storing Dagster's intermediate operational data.
- ⏳ **Automated Expiration for Intermediate Data:** The newly created `dagster` bucket is configured with a 1-day
  time-to-live (TTL) policy, ensuring automatic cleanup of temporary pipeline execution data to optimize storage.

### Changed

- 🔄 **Optimized Dagster Intermediate Storage:** The `S3PickleIOManager` used by
  `default_io_manager_s3_datalake_resources` now directs all intermediate pipeline data to the dedicated `dagster`
  bucket, utilizing a streamlined `container_name/` prefix for improved organization and adherence to the new lifecycle
  management.
- 📄 **Updated Resource Documentation:** Documentation for `default_io_manager_s3_datalake_resources` has been updated to
  clarify that intermediate data is now stored in the `dagster` bucket with a 1-day expiration policy, providing
  accurate information on data persistence.

### Refactor

- 🧹 **Improved Intermediate I/O Manager Naming:** The internal variable for the `S3PickleIOManager` was renamed to
  `op_intermediates_io_manager` for enhanced clarity and better reflection of its purpose within the pipeline resources.

______________________________________________________________________

## [v0.280.1] - 2026-04-27 - Precision Testing: Unit/Integration Split & Keycloak Validation

### Added

- ✨ **Enhanced Pytest Utilities**: Introduced new generic utilities (`mark_tests_by_directory`,
  `attach_fixtures_to_items`) to automatically categorize tests as `unit` or `integration` and explicitly manage fixture
  application, significantly improving test suite organization.
- 🔑 **Robust Keycloak Integration Tests**: Implemented comprehensive integration tests for the `KeycloakAdminService`,
  covering user management, tenant group operations, and active tenant attribute handling to ensure reliable interaction
  with Keycloak.
- 🛠️ **Real Keycloak Admin Client Utility**: Provided a new utility function to easily create and configure real
  Keycloak Admin clients for dedicated use in integration testing environments.

### Changed

- 🚀 **Expanded CI/CD Test Environments**: Updated GitHub Actions workflows to include a Keycloak service in the test
  environments for the `core` and `api` packages, enabling more thorough integration testing.
- ⚡️ **Improved Test Execution Commands**: Introduced granular `Makefile` targets (`test`, `test-integration`,
  `test-all`) in the `backup` and `core` packages, allowing developers to run specific sets of unit or integration
  tests.
- 🏷️ **Standardized Pytest Markers**: Defined official `unit` and `integration` pytest markers in `pyproject.toml` files
  for the `backup` and `core` packages, replacing previous conventions for clearer test categorization.

### Refactor

- 🧹 **Comprehensive Test Suite Restructuring**: Performed a significant overhaul of the entire test suite, relocating
  numerous test files across `agent`, `api`, `backup`, `bot`, `core`, `pipeline`, and `process` packages into dedicated
  `unit/` and `integration/` subdirectories for clearer separation and management.
- 🔄 **Unified Fixture Management**: Transitioned many fixtures (including database isolation, Keycloak mocks, tenant
  mocks, role mocks, MSAL/aiohttp mocks) from implicit `autouse=True` to explicit attachment via
  `pytest_collection_modifyitems` hooks and `pytestmark` in `conftest.py` files, offering more granular control over
  test setup.
- 📄 **Minor Configuration Description Clarity**: Adjusted the prompt description for `context_insufficient_prompt` in
  the agent's `ContextSufficientGuardStepConfig` for improved readability.

______________________________________________________________________

## [v0.280.0] - 2026-04-27 - Proactive Pipeline Monitoring with Apprise Notifications

### Added

- ✨ **Introduced Pipeline Run-Failure Notifications:** A new, comprehensive system leveraging `dagster-apprise` to
  provide immediate alerts for failed pipeline runs across all code locations. This includes failures in both explicit
  jobs and automatically materialized assets, ensuring better visibility into pipeline health.
- ⚙️ **Configurable Notification Settings:** Added new environment variables (`NOTIFICATION_URLS`,
  `NOTIFICATION_DAGSTER_UI_BASE_URL`, `NOTIFICATION_TITLE_PREFIX`, `NOTIFICATION_MIN_INTERVAL_SECONDS`) to easily
  configure diverse notification channels (e.g., Slack, Teams, email, PagerDuty) and customize notification behavior.
- 📚 **Integrated `NotificationSettings` Module:** A new Pydantic-based settings module was added to centralize and
  robustly parse, validate, and manage all notification-related environment variables.
- 🔗 **Automatic Sensor Wiring for Default Pipelines:** Default pipeline definitions now automatically include the
  run-failure notification sensor when configured via environment variables, ensuring broad coverage without requiring
  manual code changes for standard deployments.
- 📄 **New Architectural Decision Record (ADR):** A detailed ADR documenting the rationale, design choices, and
  trade-offs of the new pipeline run-failure notification system has been added to the documentation.
- 📖 **Updated Pipeline Documentation:** The pipeline documentation (`CLAUDE.md`) has been updated with a dedicated
  section explaining the new run-failure notification capabilities, including configuration and usage.
- 📦 **Added `dagster-apprise` and `apprise` Dependencies:** Integrated the necessary libraries to power the
  multi-channel notification system.

### Changed

- 🔄 **Deployment Configuration Updates:** Docker Compose templates and generated files have been updated to dynamically
  provision the new notification-related environment variables to pipeline services, streamlining deployment setup for
  the new feature.

### Refactor

- 🧹 **Improved Makefile Declarations:** Added `.PHONY` declarations to the pipeline Makefile, enhancing clarity and
  reliability for build and test commands.

______________________________________________________________________

## [v0.279.2] - 2026-04-27 - Enhanced Organization Memory Sharing

### Changed

- ✨ **Improved Organization Memory Accessibility:** RAG agents and the core `AgentMemory` service now default to
  tenant-wide retrieval for organization memory by explicitly passing `user_id=None` and `agent_id=None` to the
  underlying search function. This change ensures that knowledge stored in organization memory is fully shared and
  broadly accessible across all agents within a tenant, promoting consistent information access.
- 📄 **Expanded Memory Scoping Documentation:** Updated the `AgentMemory` service documentation with detailed
  explanations on how organization memory is shared across agents and how to control `user_id` scoping for either fully
  shared tenant-wide or user-specific retrieval.

______________________________________________________________________

## [v0.279.1] - 2026-04-24 - Core Agent Refinements and New Shared Knowledge Capabilities

### Added

- 🧠 **New Shared Knowledge Agents:** Introduced `Shared Knowledge Selector` and `Shared Knowledge RAG` agent templates,
  enabling agents to intelligently route and retrieve information from designated shared knowledge buckets.
- 🛡️ **Dedicated Context Sufficiency Guard Configuration:** A new `ContextSufficientGuardStepConfig` allows for granular
  control over how agents verify if retrieved context is adequate to answer a user's query, improving response accuracy.
- 💬 **Chat History Formatting Utility:** Added `format_chat_history` to consistently present conversation history for
  LLM prompts, enhancing the context provided to AI models.

### Changed

- ⚙️ **Refined RAG Agent Configuration:** The RAG and Expert RAG agent configurations now embed context sufficiency
  guard settings within the new `ContextSufficientGuardStepConfig`, streamlining agent setup.
- 🔍 **Enhanced Context Guard Logic:** The core context sufficiency guard now utilizes the full chat history, including
  organizational memory, to make more informed decisions about whether sufficient information is available.
- 📝 **Updated Context Guard Prompts:** Adjusted the internal prompts for the context sufficiency guard across all
  supported languages to incorporate chat history for better decision-making.

### Fixed

- 🐛 **Improved UI Form Hydration:** Resolved an issue where agent and process creation forms failed to hydrate correctly
  when nested optional configurations were explicitly `null`, enhancing the reliability of agent management in the UI.
- 📦 **Robust Human-in-the-Loop Dispatch:** Enhanced the chat service's ability to correctly identify and dispatch
  appropriate Human-in-the-Loop (HITL) response events based on the type of HITL request, preventing potential
  interaction errors.

### Refactor

- 🔄 **Standardized Agent Template Loading:** Refactored how templates for Few-Shot and LLM-Wrapping agents are loaded,
  moving from static `TEMPLATE` variables to dynamic `build()` functions for greater flexibility and maintainability.
- 🧹 **Centralized Context Sufficiency Settings:** Consolidated all configurations related to context sufficiency checks
  into the new `ContextSufficientGuardStepConfig`, simplifying agent codebases and improving modularity.

______________________________________________________________________

## [v0.279.0] - 2026-04-24 - Advanced RAG Filtering and Configuration Management

### Added

- ✨ **Introduced Per-Run RAG Metadata Filtering**: Publishers can now supply `additional_filters` with `RAGStartEvent`
  to dynamically narrow retrieval results based on metadata keys, allowing for more granular control over RAG contexts.
- 🦾 **New `RetrievalRuntimeConfig` Model**: A new plain Pydantic `BaseModel` (`RetrievalRuntimeConfig`) has been added
  to cleanly separate design-time agent configuration from per-run runtime overrides. This enhances modularity and
  security by preventing publisher-only fields from appearing in the Admin UI.
- ⚙️ **Configurable Allowed Metadata Filter Fields**: Agent administrators can now define a whitelist of metadata keys
  (`allowed_metadata_filter_fields`) within the `MilvusVectorStoreConfig` for each retriever, ensuring publishers can
  only filter on explicitly permitted fields.
- 🌐 **Admin UI for Allowed Filter Fields**: The Admin UI's `VectorStoreInput` now includes a dedicated control for
  specifying `allowed_metadata_filter_fields`, making this powerful new RAG filtering capability easy to configure.
- 📊 **Display of RAG Start Event Filters**: The agent event stream now visually presents `additional_filters` and
  `selected_namespaces` when a `RAGStartEvent` occurs, providing better visibility into retrieval parameters.
- 📄 **Architectural Decision Record**: A new architectural decision record (`2026_04_22_form_runtime_config_wrapper.md`)
  has been added, documenting the rationale and pattern for separating design-time configurations from runtime
  overrides.

### Changed

- 🔄 **Updated RAG Retrieval Logic**: The internal RAG retrieval steps now leverage the new `RetrievalRuntimeConfig`
  wrapper, allowing for the application of per-run `additional_metadata_filters` directly during the node retrieval
  process.
- 🚀 **Optimized API Event Payloads**: `StartEvent` input data in agent discovery services now uses `exclude_none=True`
  when dumping models to JSON, resulting in smaller and more efficient wire payloads.
- 📚 **Refined Event Protocol Documentation**: Examples in the Swiss AI Agent Protocol documentation were updated to
  reflect the use of message `blocks` instead of plain `content` for `UserMessageEvent`s.

### Refactor

- 📦 **Relocated `RAGStartEvent`**: The `RAGStartEvent` has been moved to the `core` package
  (`swiss_ai_hub.core.events.agent.control.start`) to make it more broadly accessible across the application.
- 🧹 **Replaced Namespace Filtering Utility**: The `filter_retrievers_by_namespace` utility has been replaced by the more
  comprehensive `narrow_retrievers` function, which now handles both namespace narrowing and
  `additional_metadata_filters` validation.

### Removed

- 🗑️ **Deprecated `filter_retrievers_by_namespace`**: The previous utility for filtering retrievers by namespace has
  been removed, as its functionality is superseded by the new `narrow_retrievers` mechanism.

______________________________________________________________________

## [v0.278.1] - 2026-04-23 - Strengthened Event Serialization for HITL Subtypes

### Fixed

- 🐛 **Resolved Human-in-the-Loop (HITL) Event Downcasting**: Fixed a critical bug where specific HITL event subclasses
  (such as input, confirmation, and chat requests and their corresponding responses) were silently downcasted to their
  parent event types during WebSocket serialization. This ensures that the frontend now receives accurate and specific
  HITL event types.
- ⚡️ **Corrected Event Discriminator Logic**: Enhanced the `DisplayEvents` union to correctly discriminate between
  agent-specific HITL request and response event subclasses, preserving their distinct type information when events are
  broadcast over WebSockets.

### Added

- ✅ **Comprehensive Event Serialization Tests**: Introduced new unit tests to rigorously validate that Human-in-the-Loop
  event subclasses are properly discriminated and their precise type is preserved throughout the WebSocket serialization
  and deserialization process, preventing future regressions.

### Changed

- 📄 **Updated Event Serialization Guidelines**: Added crucial documentation to `CLAUDE.md` files in both `api` and
  `core` packages, providing clear guidance on how to correctly add new event subclasses to the `DisplayEvents` union to
  prevent silent downcasting during WebSocket serialization.

______________________________________________________________________

## [v0.278.0] - 2026-04-21 - Next-Gen Multi-Tenancy: Keycloak-First Identity & Admin Workflows

### Added

- 🦾 **Dedicated Sysadmin Tenant Management API**: Introduced a new set of API endpoints (`/admin/tenants`) for system
  administrators to manage tenant metadata, including listing, configuring, updating, and deleting tenants.
- 🔑 **`AIHubSysAdmin` Keycloak Realm Role**: A new Keycloak realm role, `AIHubSysAdmin`, now designates platform
  administrators, granting implicit admin-level access within any tenant they are a member of.
- 🆕 **`TenantMetadataEntity` for Tenant Display Information**: A new database entity `TenantMetadataEntity` is
  introduced to store display-related tenant information (name, description, access rules), complementing Keycloak as
  the authoritative source for tenant existence.
- 🧪 **`TestAuthHandler` for Development & Testing**: A dedicated authentication handler (`TestAuthHandler`) replaces the
  `DangerousDevelopmentOnlyAuthHandler`, ensuring a clearer separation between test utilities and production code and
  simplifying local development setup.
- 🔄 **Automatic Superuser Membership in New Tenants**: The platform's superuser account (now a regular Keycloak user) is
  automatically added to every new tenant's Keycloak group upon creation, ensuring immediate and explicit access for
  platform administration.
- 📄 **New Architectural Decision Records (ADRs)**: Multiple new ADRs have been added to thoroughly document the
  rationale and implementation details of significant architectural changes in multi-tenancy, authorization, and token
  management.

### Changed

- 🔑 **Superuser Identity Transition**: The global superuser is no longer a synthetic identity but a regular Keycloak
  user, identified by `SUPERUSER_USERNAME` and `SUPERUSER_EMAIL`, simplifying identity management and leveraging
  Keycloak as the single source of truth.
- ⚙️ **`SUPERUSER_TOKEN` Repurposed**: The `SUPERUSER_TOKEN` now serves as a static bearer token, bound to the Keycloak
  superuser, enabling internal services to authenticate against the API through the standard `TokenAuthHandler`.
- 🚀 **`StartupTenantSettings` Introduced**: The previous `AIHUB_DEFAULT_TENANT_ID` and related settings are now
  `AIHUB_STARTUP_TENANT_ID` and `StartupTenantSettings`, clarifying that this tenant is treated as an ordinary tenant
  after initial seeding, losing its special "default" status.
- ⚡️ **Refined `AuthHandler` Tenant Resolution**: The logic for resolving active and requested tenants has been updated,
  with `KeycloakAdminService` now the authoritative source for tenant existence and membership checks, improving
  consistency and reliability.
- 👤 **User Profile Data Sourced from Keycloak**: User profile data (name, email) is now exclusively read from Keycloak
  (JWT claims for OAuth2, `KeycloakAdminService` for bearer tokens), eliminating the need for a local `UserEntity` in
  MongoDB.
- 📚 **Updated Documentation for Admin/Sysadmin UI**: User-facing documentation and UI layouts for admin functionality
  are now separated, with dedicated sections for tenant-scoped admin pages (`/[tenant]/service/`) and global sysadmin
  pages (`/sysadmin/`).
- 🔗 **Dynamic Endpoints Include Tenant ID**: Dynamic Agent and Process endpoints now explicitly include the tenant ID in
  their URL paths: `POST /api/v1/{tenant_id}/agents/{agent_class}/{agent_id}/{event_name}`.
- 📈 **`get_my_tenants` Returns Sysadmin Status**: The `/my-tenants` API endpoint now includes the user's `is_sys_admin`
  status in its response, providing a clearer overview of user privileges.
- 🛡️ **Bot API Authentication Hardened**: The Bot API's main entry point (`packages/bot/app/main.py`) now uses
  `KeycloakAuthHandler` as a fail-closed safety net, replacing the `DangerousDevelopmentOnlyAuthHandler` placeholder.
- 📊 **Stricter `MONGO_MAIN_DB_NAME` Validation**: Updated validation for `AIHubSettings().MONGO_MAIN_DB_NAME` to ensure
  stricter adherence to valid MongoDB database naming conventions.
- 🛠️ **Agent `RunContext`/`ThreadContext` Backing Changed**: `RunContext` and `ThreadContext` for agents are now backed
  by Valkey (Redis), providing ephemeral (RunContext) and persistent (ThreadContext) key-value storage.
- 🔗 **Keycloak Service Account Permissions Extended**: The `aihub-api-service` Keycloak client now requires `view-realm`
  and `view-clients` roles in `realm-management` to enable proper sysadmin status resolution.

### Fixed

- 🐛 **PostgreSQL FerretDB Catalog Backup Workaround**: Implemented a specific workaround for PostgreSQL FerretDB catalog
  tables to ensure their data is correctly backed up and restored, preventing empty catalogs after recovery.
- 🐛 **MongoDB Test Database Isolation**: Ensured robust isolation of MongoDB test databases by enforcing an early import
  in `conftest.py` that sets `AIHUB_MONGO_MAIN_DB_NAME` to `aihub_test`, preventing accidental data leakage to dev/prod
  databases.
- 🐛 **Token Verification Error Messages**: Improved error messages for bearer token verification to distinguish between
  malformed, unknown, and expired tokens, aiding in debugging and troubleshooting.

### Removed

- 🗑️ **`TenantEntity` Database Collection**: The `TenantEntity` MongoDB collection has been completely removed, with its
  metadata functionality replaced by `TenantMetadataEntity` and existence managed by Keycloak.
- ❌ **`DangerousDevelopmentOnlyAuthHandler`**: The insecure `DangerousDevelopmentOnlyAuthHandler` has been entirely
  removed, promoting more secure authentication practices even in development environments.
- 🚫 **`SuperuserAuthHandler`**: The dedicated `SuperuserAuthHandler` has been removed as the superuser is now an
  ordinary Keycloak user authenticated via the standard `TokenAuthHandler`.
- 🗑️ **System-Wide Roles**: The concept and implementation of system-wide roles (roles with `tenant_id=None`) have been
  removed; all roles are now strictly tenant-scoped.
- 🗑️ **`is_default` Flag on Tenants**: The `is_default` boolean flag has been removed from tenant metadata, simplifying
  the tenant model and delegating "startup tenant" identification to configuration.
- 🗑️ **Legacy `KEYCLOAK_DEV_USER_*` Environment Variables**: The `KEYCLOAK_DEV_USER_*` environment variables, previously
  used for a configurable development user, have been removed in favor of the more robust `SUPERUSER_*` configuration.

### Security

- 🔒 **Opaque API Bearer Token Format**: API bearer tokens now use an opaque `sk-<random>` format, enhancing security by
  removing sensitive database internal IDs and improving token opacity, requiring rotation of existing tokens.
- 🛡️ **Sysadmin Authorization Bypass Refinement**: Sysadmin access now grants `ACCESS_ADMIN` within any tenant the
  principal is a member of, bypassing normal rule evaluation, while explicitly NOT granting implicit membership,
  aligning with the principle of least privilege.
- 👮 **Stricter Tenant Request Validation**: New DTOs and validation rules for tenant administration API endpoints
  prevent malformed or invalid tenant IDs and names from reaching business logic or Keycloak, mitigating potential
  injection risks.
- 🚨 **Explicit Auth Handler Requirement**: `Controller.__init__(auth=...)` now explicitly raises a `TypeError` if no
  auth handler is provided, preventing silent activation of insecure bypass mechanisms.
- 🕵️ **Tenant Enumeration Protection**: Tenant resolution via URL path parameter now consistently returns a generic
  "Access denied" (403) for non-existent, non-member, or unconfigured tenants, preventing attackers from enumerating
  valid tenant IDs.
- 🛑 **Last Tenant Deletion Guard**: The tenant deletion service now explicitly prevents the removal of the last
  remaining tenant, ensuring continuous platform availability and integrity.

### Refactor

- 🧹 **Consolidated Superuser Configuration**: The configuration for the platform superuser is consolidated into a single
  `SUPERUSER_` block in `.env` files, simplifying setup and maintenance.
- 🧽 **Race-Safe Tenant Deletion Logic**: The tenant deletion process is refactored with robust race-safety mechanisms,
  including snapshotting and a post-deletion recount, to ensure the "at least one tenant must remain" invariant is never
  violated by concurrent operations.
- 🧹 **Centralized Keycloak Admin Service**: The `KeycloakAdminService` is significantly expanded with new static methods
  for comprehensive tenant group, user membership, and realm role management, centralizing Keycloak interactions and
  improving testability.
- 🧹 **Streamlined Auth Handler Composition**: The `TokenAndOauth2Handler` composition logic is streamlined, removing
  unused authentication paths and clarifying the overall authentication flow.
- 🧹 **Unified Test Identity Management**: Test identity constants (OID, name, email, roles) and a `fake_user()` helper
  are moved to `swiss_ai_hub.core.testing.auth_utils.test_identity.py`, explicitly separating test-only values from
  production settings.
- 🧹 **Updated `AccessChangeHook` for New Entities**: The `AccessChangeHook` now correctly tracks changes on
  `TenantMetadataEntity` instead of the removed `TenantEntity`, maintaining consistency for OpenWebUI synchronization.
- 🧹 **Standardized Agent Playground Triggers**: Agent playground trigger scripts now consistently use `fake_user()` from
  the new `core.testing.auth_utils` for mock user identities, promoting uniformity and ease of testing.
- 🧹 **Consolidated Role Card Deletion Logic**: Role card deletion in the UI now uses a unified confirmation dialog and
  delegates to a shared composable for improved user experience and maintainability.
- 🎨 **Standardized UI Loading Indicator**: Introduced a new `AppLoader` component for a consistent and visually
  appealing loading indicator across the UI.
- 🧹 **General Code Cleanup and Consistency**: Various minor code cleanups, including improved logging, removal of
  redundant code, and consistency adjustments across the codebase.

______________________________________________________________________

## [v0.277.2] - 2026-04-20 - Refined Event Protocol: Introducing `RAGStartEvent` and Clarifying Chat Contracts

### Added

- ✨ **Introduced `RAGStartEvent`**: A new, dedicated `StartEvent` for RAG agents. This event allows custom domain
  front-ends or other agents to initiate RAG workflows with pre-selected namespaces, maintaining a clean separation from
  the generic chat UI contract.
- 🧪 **Unit Tests for `RAGStartEvent`**: Comprehensive unit tests were added to validate the properties and behavior of
  the new `RAGStartEvent`, ensuring its reliability.
- 🖼️ **Web UI Display for `RAGStartEvent`**: A new Vue component and updated event mapping were implemented to enable
  proper rendering of `RAGStartEvent` in the web interface, showcasing selected namespaces and chat history.
- 🌐 **Internationalization for `RAGStartEvent`**: Added translations across supported languages for the `RAGStartEvent`
  and its associated "selected namespaces" property, enhancing multi-language support.

### Changed

- 📄 **Clarified `UserMessageEvent` as Chat UI Contract**: Updated documentation and internal guidance across `SKILL.md`,
  agent reports, and `CLAUDE.md` files. This change emphasizes that `UserMessageEvent` is exclusively for generic chat
  interfaces and advises subclassing `StartEvent` directly for agent- or domain-specific payloads.
- 🔄 **RAG Agent Event Acceptance**: Modified `ExpertRAGAgent` and `RAGAgent` to explicitly accept the new
  `RAGStartEvent` (alongside `UserMessageEvent`) for initiating RAG workflows, ensuring proper handling of
  namespace-aware queries from non-chat sources.

### Refactor

- 🧹 **Replaced `NamespaceAwareUserMessageEvent` with `RAGStartEvent`**: Refactored internal agent logic and
  configurations to transition from `NamespaceAwareUserMessageEvent` to the newly introduced `RAGStartEvent`,
  streamlining the event model for RAG delegation.
- ⚡️ **Optimized `UserMessageEvent.user_query` Property**: Performed a minor internal optimization to the `user_query`
  property within `UserMessageEvent` for enhanced readability and maintainability.

### Removed

- 🗑️ **Deprecated `NamespaceAwareUserMessageEvent`**: The `NamespaceAwareUserMessageEvent` class was removed, as its
  functionality has been superseded by the more appropriately designed `RAGStartEvent` which directly extends
  `StartEvent`.

______________________________________________________________________

## [v0.277.1] - 2026-04-17 - Enhanced Development Experience and Service Orchestration

### Added

- ✨ **New IntelliJ Run Configurations:** Introduced dedicated IntelliJ run configurations for `Bot Dev` and `Bot Prod`
  to streamline local development and testing of bot services using Makefiles.

### Changed

- 🚀 **Improved IntelliJ Docker Compose Configurations:** Enhanced existing Docker Compose run configurations in IntelliJ
  by explicitly defining environment file paths and ensuring services are rebuilt on each run.
- ⚙️ **Streamlined Open WebUI Dependencies:** Optimized Docker Compose configurations to remove the direct dependency of
  `open-webui` on the `api` service's health in non-development environments, improving startup times.
- ♻️ **Enhanced `openwebui-init` Resilience:** Updated the `openwebui-init` service in Docker Compose to automatically
  restart on failure, improving the stability and robustness of initialization tasks.
- ⏱️ **Ensured Sequential Service Startup:** Configured `openwebui-manager` to wait for `openwebui-init` to successfully
  complete its tasks before starting, preventing potential race conditions and ensuring correct setup.

### Removed

- 🗑️ **Deprecated Bot Run Configuration:** Removed the outdated IntelliJ Python run configuration for "Run Bots," now
  superseded by the new, more specific Makefile-based configurations.

### Refactor

- 🧹 **Centralized Keycloak Client Dependency:** Relocated the `python-keycloak` dependency from the `packages/api`
  module to `packages/core`, centralizing common authentication functionalities.

______________________________________________________________________

## [v0.277.0] - 2026-04-14 - Enhanced Data Resilience: Introducing a Centralized Backup and Restore Service

### Added

- 🚀 **New Centralized Backup and Restore Service:** Introduced a comprehensive, Dagster-powered backup service that
  ensures data integrity across all stateful services, including PostgreSQL (main and FerretDB), Milvus, Neo4j,
  ClickHouse, Valkey, and NATS.
- ⏰ **Automated Daily Backups:** Configured daily backup schedules at 1 AM (Europe/Zurich) with automatic retention
  cleanup policies, managed via the dedicated Dagster UI.
- ↩️ **Self-Service Restore Capabilities:** Enabled parameterized point-in-time recovery for the entire platform through
  the intuitive Dagster Launchpad in the Backup UI.
- 📄 **Extensive Backup Documentation:** Provided detailed documentation covering the backup architecture, configuration,
  operational procedures, and recovery steps for all data stores.
- 🧪 **End-to-End Backup Tests:** Implemented a robust end-to-end (E2E) test suite to validate the entire backup and
  restore lifecycle, ensuring reliability and data integrity in an integrated environment.
- 📦 **Dedicated Backup S3 Bucket:** Automatically provisioned a new `backups` bucket within the internal SeaweedFS S3
  storage for all backup artifacts.
- 🛠️ **Native Backup Tooling Integration:** Incorporated official `milvus-backup` and `nats` CLI tools directly into the
  backup service for precise and efficient data handling.
- ⚙️ **ClickHouse S3 Integration:** Configured ClickHouse to directly utilize the internal SeaweedFS S3 for its native
  `BACKUP TO Disk()` and `RESTORE FROM Disk()` operations.
- 📦 **New `packages/backup` Module:** Introduced a new top-level Python package to house all the logic for the
  centralized backup and restore service.

### Changed

- 🗃️ **Improved Backup Retention Logic:** Enhanced the backup retention policy to guarantee a minimum number of backups
  are always preserved, even if they exceed the defined age limit.
- 📈 **Milvus Collection Loading Reliability:** Updated Milvus vector store operations to explicitly ensure collections
  are loaded into memory before use, preventing potential issues after service restarts or restores.
- 🏗️ **Docker Compose Integration:** Updated core Docker Compose configurations across all stages to seamlessly
  integrate the new backup service, manage its dependencies, and define necessary environment variables.

### Fixed

- 🐛 **DocumentDB Catalog Backup Fix:** Resolved a critical issue where `pg_dump` would silently skip essential
  DocumentDB catalog tables in FerretDB's PostgreSQL backend. The backup service now explicitly backs up and restores
  these tables and sequences using the `COPY` protocol, ensuring consistent FerretDB restores.

### Removed

- 🗑️ **Deprecated Backup Stubs:** Removed placeholder (stub) implementations for backup handlers, replacing them with
  fully functional and robust service-specific backup logic.

______________________________________________________________________

## [v0.276.0] - 2026-04-14 - Streamlined Workflow Visualization and Enhanced Multi-Tenancy

### Refactor

- 🧹 **Agent Workflow Visualizer**: Completely re-engineered the backend workflow visualizer, eliminating the `networkx`
  dependency and streamlining the internal graph representation for improved efficiency.
- 🔄 **Frontend Workflow Visualization**: Overhauled the frontend workflow visualization to use a custom grid-based
  layout algorithm, providing a more intuitive and performant display of agent structures without relying on external
  graphing libraries.
- 🦾 **Simplified Workflow Graph Models**: Refactored the underlying data models (`WorkflowGraph`, `NodeData`,
  `EdgeData`) for agent workflows, removing verbose event details from the graph structure for a cleaner and more
  focused representation.
- 🏗️ **Standardized Workflow Node Components**: Restructured workflow node components (`StartNode`, `StepNode`,
  `StopNode`) to utilize a new `WorkflowNodeCard` for consistent styling and updated connection handle positions for
  better layout integration.
- ⚡️ **Improved `useTenantPath` hook usage**: Applied minor refactorings to ensure consistent and efficient usage of the
  `useTenantPath` hook across the application.

### Added

- 🖼️ **Agent Workflow Modal**: Introduced a new modal component for a dedicated, expanded view of agent workflow
  diagrams, improving user experience for understanding agent logic.
- ✨ **Generic Workflow Node Card**: Added a reusable `WorkflowNodeCard` component to standardize the appearance of nodes
  across the new workflow visualization, ensuring a consistent look and feel.
- 🚀 **View Workflow Button**: Implemented a "View workflow" button on the agent class list, allowing quick access to the
  visual representation of an agent's logic directly from the overview.
- 📄 **Localization for Workflow UI**: Added new localization strings to support the user interface elements of the
  enhanced workflow visualization in multiple languages.

### Changed

- 🔑 **Enforced Tenant ID in API Calls**: Updated numerous frontend API calls to explicitly include the `tenantId`,
  strengthening multi-tenancy enforcement and data isolation across various services.
- 📊 **Streamlined WorkflowGraph Data Model**: Simplified the `WorkflowGraph` data model by removing `directed`,
  `multigraph`, and generic `graph` attributes, focusing solely on `nodes` and `links` for a leaner representation.

### Removed

- 🗑️ **Dropped Graphing Library Dependencies**: Eliminated `networkx` from backend dependencies and `@dagrejs/dagre`
  from frontend dependencies, significantly reducing the package footprint and improving performance.
- 🚫 **Deprecated Detailed Event Models**: Removed Pydantic and MongoEngine models (`EventInfo`, `EventPayloadField`,
  `InputEventInfo`) that previously stored extensive event details within the graph, aligning with the simplified
  visualization approach.
- 🧹 **Legacy Workflow UI Components**: Removed old Vue components (`WorkflowEventEdge.vue`, `WorkflowEventSpecs.vue`)
  that are no longer needed due to the redesigned workflow visualization.

______________________________________________________________________

## [v0.275.0] - 2026-04-14 - Keycloak as Source of Truth: Centralized User Management and Active Tenant Handling

### Refactor

- 🔄 **Centralized User Management**: Rearchitected user management by migrating user profile data (name, email) and
  active tenant ID from the local MongoDB `UserEntity` collection to Keycloak. Keycloak now serves as the single source
  of truth for user identities, reducing data duplication.
- 🧹 **User Dashboard Persistence**: Refactored the storage of user dashboard configurations into a new, dedicated
  MongoDB collection, **`UserDashboardEntity`**, separating it from core user identity data.
- ⚡️ **Enhanced Keycloak Admin Permissions**: Updated the **`aihub-api-service` Keycloak client** with necessary
  `manage-users` and `query-users` roles, enabling the application to perform user and group management operations
  directly via the Keycloak Admin API.
- ⚙️ **Configurable Default Tenant ID**: Standardized the **default tenant ID (`AIHUB_DEFAULT_TENANT_ID`)** across
  environment variables and Keycloak realm configurations for improved consistency and flexibility.
- 📄 **Internal API and Bot Codebase**: Performed extensive updates across the API and bot services to align with the new
  user management architecture, removing all direct dependencies on the defunct `UserEntity` and migrating to
  asynchronous Keycloak Admin Service calls.

### Added

- 🔑 **Keycloak Admin Service**: Introduced a new, robust **`KeycloakAdminService`** with methods for user lookup,
  creation, and management, including reading and writing custom user attributes (like `active_tenant_id`) and managing
  tenant groups.
- 📊 **Dedicated User Dashboard Entity**: Implemented **`UserDashboardEntity`** to manage user dashboard configurations,
  replacing the dashboard functionality previously embedded in `UserEntity`.
- ✨ **Keycloak Data Models**: Introduced **`KeycloakUser`** and **`KeycloakGroup`** Pydantic models for structured
  representation of Keycloak entities, improving type safety and development experience.
- 🚀 **Automated Keycloak Tenant Group Provisioning**: Added logic to automatically create corresponding **Keycloak
  tenant groups** for default tenants and to backfill existing Keycloak users into these groups upon initial setup.

### Removed

- 🗑️ **Elimination of `UserEntity`**: Completely removed the **`UserEntity` MongoDB collection**, simplifying the
  persistence layer by centralizing user identity in Keycloak.
- ⛔️ **Removed User-Local Metadata**: Discontinued local storage of **`last_accessed`** timestamps and
  **`favorite_modules`** lists from user profiles, reflecting the shift to Keycloak as the primary user data store.
- 🚫 **Superuser Database Record**: The **superuser** no longer creates a persistent record in the local database,
  operating purely as a virtual identity for system administration.

______________________________________________________________________

## [v0.274.4] - 2026-04-14 - Introducing Fine-Grained OpenWebUI Agent Visibility & Workflow Enhancements

### Added

- 🛡️ **Implemented OpenWebUI Agent Visibility Provisioning:** AI-Hub now actively manages OpenWebUI's internal state,
  including groups, workspace models, and access grants. This ensures users only see agents they are authorized to use,
  enforcing granular access control based on AI-Hub's permission system.
- ✨ **New Webhook Controller:** Introduced a `WebhookController` in the API to receive and process external service
  notifications, currently used for OpenWebUI user signup events to trigger access synchronization.
- ⚙️ **Access Change Hook:** Added an `AccessChangeHook` to automatically trigger OpenWebUI access synchronization when
  AI-Hub roles, tenants, or user-role assignments are created, updated, or deleted, with built-in debouncing for
  performance.
- 📄 **OpenWebUI Access Control Documentation:** New architecture decision records and user documentation have been added
  to explain the new OpenWebUI model visibility and access control mechanisms.
- 🧪 **Comprehensive OpenWebUI Provisioner Tests:** Expanded unit and integration tests for OpenWebUI provisioning,
  covering group management, access grant computation, and distributed locking.
- 🛠️ **Utility Methods for Agent Discovery:** Introduced `AgentClassEntity.get_online_conversational()` and
  `AgentConfigEntityDocument.find_for_classes()` to efficiently retrieve online conversational agent data for
  provisioning.

### Changed

- 🚀 **Upgraded OpenWebUI Dependency:** Updated OpenWebUI Docker image to `v0.8.10`, enabling new features and security
  enhancements required for integrated access control.
- 🎯 **Refined PR Feedback Skill:** The `implement-feedback-from-pr` skill now intelligently fetches only unresolved,
  non-outdated review comments from GitHub, streamlining the feedback implementation process.
- 🎥 **PR Demo Video Workflow:** The `pr-demo-video` skill now posts demo video descriptions as comments directly on the
  linked GitHub issue, falling back to the PR if no issue is connected, improving PR management and clarity.
- 🔑 **OpenWebUI Configuration Parameters:** Added new environment variables (`OPENWEBUI_SCIM_TOKEN`,
  `OPENWEBUI_WEBHOOK_SECRET`) and updated Docker Compose configurations to enable OpenWebUI's SCIM and webhook
  capabilities, alongside disabling model access control bypass.
- 🔄 **API Lifetime Management:** Integrated the OpenWebUI provisioner into the API's lifecycle manager, ensuring access
  control is applied automatically on startup and updated when access entities change.
- ⚡️ **Optimized Agent Instance Hashing:** Improved the internal logic for computing agent instance hashes, enhancing
  the efficiency of change detection for provisioning services.
- 📧 **Keycloak Development User Email:** Updated the default Keycloak development user email domain for consistency.
- 👥 **User Active Tenant Sync Trigger:** Modified the `UserEntity.set_active_tenant` method to explicitly notify the
  `AccessChangeHook`, ensuring OpenWebUI permissions are re-evaluated when a user changes their active tenant.

### Refactor

- 🧹 **OpenWebUI Initialization Script Renaming:** Renamed `infra/configs/openwebui/init-functions.sh` to
  `init-openwebui.sh` for improved clarity and consistency with its expanded role in initializing OpenWebUI functions
  and service accounts.
- ⚙️ **Internal Provisioner Dependencies:** Refactored the `AgentEndpointsDiscoveryService` to internally instantiate
  `LangfuseProvisioner` and `OpenWebuiProvisioner`, simplifying its constructor and centralizing dependency management.

______________________________________________________________________

## [v0.274.3] - 2026-04-10 - Addressing Duplicate Agent-in-the-Loop Responses and Enhancing Event Control

### Fixed

- 🐛 **Agent-in-the-Loop response duplication:** Resolved a critical bug in the `AgentDispatcher` that previously led to
  duplicate Agent-in-the-Loop (AITL) responses and unintended repeated execution of orchestration steps. The dispatcher
  now accurately subscribes only to control events, preventing these issues.
- ⚡️ **Tracing accuracy for AITL events:** Improved the timing of span completion for Agent-in-the-Loop interactions,
  ensuring tracing data is precisely recorded before final responses are published.

### Added

- ✨ **Dedicated control event subscription:** Introduced `AgentNCSubscriber.for_thread_control_events`, a new method
  that allows agents to precisely subscribe only to control events within a thread, enhancing event handling efficiency
  and reliability.
- 📄 **Robust AITL response verification tests:** Added new comprehensive test scenarios to validate the uniqueness of
  Agent-in-the-Loop responses and orchestration results, significantly improving the stability and correctness of agent
  workflows.

______________________________________________________________________

## [v0.274.2] - 2026-04-10 - Web Platform Tenant Context Enforcement

### Changed

- 🔐 **Enforced Tenant Scoping for Agent Management:** Operations for creating new agent instances and fetching available
  agent classes or instances now correctly enforce tenant isolation, ensuring agent data is specific to the active
  tenant.
- 📚 **Improved Tenant Context for Knowledge Management:** Database selectors, document uploads, and detailed document
  views now properly utilize the tenant context, ensuring knowledge base operations are isolated to the specific tenant.
- 💡 **Applied Tenant Scoping to Model and File Access:** API calls for fetching LiteLLM models and resolving file URLs
  now consistently respect the active tenant, enhancing data security and isolation for these resources.
- 🚀 **Ensured Consistent Versioning Across Components:** All core packages, including `agent`, `api`, `backup`, `bot`,
  `core`, `pipeline`, `process`, and `web`, have been updated to version `v0.274.2` for release consistency.

______________________________________________________________________

## [v0.274.1] - 2026-04-10 - Streamlined Data Lake Integrations and Document Handling

### Added

- ✨ **Introduced automatic MongoDB Document Store configuration**: Rclone to Data Lake pipelines now automatically
  provision and configure a MongoDB document store based on the data lake container name, streamlining data ingestion
  and indexing.

### Changed

- 🔄 **Enhanced RawLoader file reading robustness**: Updated the `RawLoader` to use a more robust byte-based file reading
  approach with error replacement, improving handling of various file encodings and malformed characters.

### Removed

- 🗑️ **Deprecated `placeholder_refdocs_factory`**: The `placeholder_refdocs_factory` asset has been removed from
  SharePoint and local filesystem to Data Lake pipelines, simplifying asset definitions and reducing overhead.

______________________________________________________________________

## [v0.274.0] - 2026-04-08 - Enhanced Tenant Management and API Routing

### Added

- ✨ **Introduced `MyTenantController`**: A new API controller providing endpoints for users to view and manage their
  tenant memberships, including fetching all associated tenants and setting their active tenant.
- 📄 **New Client-Side Tenant Management Composables**: Added a suite of Vue composables (`useTenant`, `useTenantPath`,
  `useTenantMemberships`, `useActiveTenantQuery`, `useSetActiveTenant`, `useTenantPolling`, `useTenantReady`) to provide
  robust and reactive tenant context management across the frontend application.
- 🖼️ **Tenant Selection User Interface**: Introduced a dedicated `/select-tenant` page and a `TenantSwitcher` component,
  enabling users to easily view and switch between their available tenants.
- 🚀 **Tenant-Aware Root Landing Page**: The main landing page (`/`) now intelligently redirects users based on their
  tenant access: auto-selecting for single-tenant users, or presenting a tenant selection page for users with multiple
  tenants.
- 🛠️ **`get_tenant_ids_for_user` Utility**: Added a new utility method to retrieve all tenant IDs a specific user
  belongs to, supporting tenant management features.

### Changed

- 🔄 **API Base URL for Frontend**: The frontend's API base URL has been updated from a hardcoded tenant
  (`/api/v1/active`) to a generic `/api/v1`, aligning with the new flexible tenant-scoped routing.
- 🐛 **Improved Frontend Error Handling for Access Denied**: Enhanced the client-side API error handling to automatically
  redirect users to the tenant selection page upon receiving an "Access denied" (403) response, ensuring a smoother user
  experience.
- 🍪 **Login Redirect URL Preservation**: The authentication middleware now stores the intended redirect URL before
  login, allowing users to return to their specific page (including tenant context) after successful authentication.
- 🏛️ **Global Auth Provider Endpoints**: The Auth Provider API endpoints are now consistently non-tenant-scoped,
  accessible at `/api/v1/auth-providers`.

### Refactor

- 🧹 **Comprehensive API Routing Overhaul**: Redesigned API routing to explicitly distinguish between global and
  tenant-scoped controllers, with tenant-scoped endpoints automatically prefixed by `/{tenant_id}`.
- 🚀 **Dynamic OpenAPI Schema Generation**: Implemented a custom OpenAPI schema hook to dynamically inject the
  `{tenant_id}` path parameter into the OpenAPI specification for all tenant-scoped endpoints, ensuring accurate client
  SDK generation.
- ⚡️ **Consistent Tenant Context in API Calls**: Updated almost all frontend API calls and query keys to explicitly
  include the `tenantId`, ensuring proper tenant context and more efficient cache invalidation.
- 🌐 **Tenant-Aware Frontend Page Structure**: Major restructuring of the frontend's page directory, moving most
  service-related pages under a `/[tenant]/` dynamic route to natively embed tenant context into URL paths.
- ⚙️ **Modular Controller Architecture**: Introduced `TenantScopedController` as a base class for all tenant-specific
  API controllers, enforcing consistent tenant-aware routing and authentication practices. Many existing controllers
  (e.g., Agent, Model, User) now inherit from this new base class.
- 📖 **Updated API Documentation for Routing**: The API documentation (`CLAUDE.md`) has been updated to reflect the new
  tenant-scoped routing paradigm, clarifying how controllers are mounted and how `tenant_id` is handled.
- 🛠️ **Dynamic Endpoint Discovery Integration**: Updated the endpoint discovery services to leverage the new
  tenant-scoped routing, ensuring that dynamically generated endpoints (e.g., for agent and process instances) correctly
  incorporate the tenant context.
- 📍 **Unified Authentication Identity Building**: Refactored authentication handlers to use a single `build_identity`
  method, which correctly resolves user and tenant context based on the incoming request, improving consistency and
  maintainability.

______________________________________________________________________

## [v0.273.6] - 2026-04-07 - Empowering Recovery: New System Restore Workflow

### Added

- ✨ **Enabled Full System Restore Workflow:** Introduced a comprehensive Dagster-based workflow for performing full
  system restores, allowing recovery from a specified backup timestamp. This new capability orchestrates service
  shutdowns, validates backup integrity, manages individual service restorations, and restarts all services upon
  successful completion.
- ⚙️ **Granular Container Lifecycle Management:** Implemented a new `ContainerLifecycleManager` resource to provide
  precise control over starting, stopping, and health-checking specific groups of containers required by individual
  services during the restore process.
- 🧩 **Service Dependency Mapping:** Established a centralized mapping (`SERVICE_DEPS`) that defines the container
  dependencies for each backup service, ensuring correct sequencing and isolation during parallel backup and restore
  operations.
- 🛠️ **Modular Service Handler Architecture:** Introduced a new `BackupHandler` interface and a factory mechanism to
  standardize how backup and restore logic is implemented for each service, improving modularity and extensibility for
  future service integrations.
- ✅ **Backup Integrity Validation:** Added a critical pre-restore validation step that checks for the presence of all
  expected backup files in S3, preventing restore attempts on incomplete or corrupted backups.
- 🧪 **Comprehensive Restore Test Suite:** Included extensive new unit tests covering the container lifecycle management,
  handler factory, restore definitions, and backup validation to ensure the reliability and correctness of the new
  restore functionality.

### Fixed

- 🐛 **Improved Container Stop Logging:** Enhanced the accuracy of container stop logging, so that only successfully
  stopped containers are counted, providing a more reliable report of system state during backup preparations.

______________________________________________________________________

## [v0.273.5] - 2026-04-07 - Robust Backup System with S3 Integration and Automated Operations

### Added

- ✨ **Introduced a comprehensive backup system:** The previously placeholder backup service is now fully functional,
  providing robust data protection.
- 🚀 **Integrated S3 storage for backups:** Backups are now securely stored on S3-compatible object storage, configurable
  via environment variables.
- 🗓️ **Implemented automated daily backups:** A new Dagster schedule runs daily at 1 AM (Zurich time) to perform
  system-wide backups.
- 🧹 **Added intelligent backup retention policies:** Old backups are automatically pruned based on configurable
  retention days, while ensuring a minimum number of backups are always kept.
- 🗄️ **Enabled service-aware backup for core components:** Explicit support for backing up critical services including
  PostgreSQL, Milvus, Neo4j, ClickHouse, Valkey, and NATS.
- ⚙️ **Streamlined configuration management for backup:** Sensitive credentials and backup settings are now securely
  managed using `pydantic-settings` and exposed via Docker environment variables.
- 🔄 **Dynamic partitioning for easier restore selection:** Dagster now dynamically partitions backups by timestamp,
  simplifying the selection of a specific backup for restoration.
- 🌐 **Dedicated 'storage' network for backup service:** The backup service now connects to a specific `storage` network
  in Docker Compose, improving network isolation and access control.

### Changed

- 🛠️ **Enhanced backup session robustness:** The backup process now automatically purges any pre-existing, incomplete
  backup artifacts for the current timestamp on S3 before starting a new session.
- 📄 **Improved backup logging clarity:** Backup session logs now explicitly include the S3 bucket and prefix for easier
  monitoring and debugging.

### Fixed

- 🐛 **Prevented Traefik service interruption during backup:** The backup process now correctly excludes `traefik`
  containers from being stopped and restarted, ensuring continuous inbound traffic handling.

### Removed

- 🗑️ **Removed placeholder status from backup README:** The `README` for the backup package no longer states it's a
  skeleton, reflecting its new, fully operational status.

### Refactor

- 🚰 **Streamlined Dagster resource injection for backup:** Refactored backup-related resources into a unified factory
  for improved modularity and dependency management.
- 🧱 **Centralized service mapping for backup assets:** Defined a clear mapping between backup service names and their
  corresponding Dagster asset keys, enhancing code organization.
- 📦 **Updated backup package dependencies:** Added `boto3` for S3 interaction and `pydantic-settings` for robust
  configuration.

______________________________________________________________________

## [v0.273.4] - 2026-04-07 - Improved Authentication and Service Configuration

### Added

- ✨ **Keycloak Client Plugin**: Introduced a new client plugin dedicated to Keycloak API interactions, facilitating more
  robust authentication management flows.
- 💾 **LiteLLM Model Persistence**: Enabled the `STORE_MODEL_IN_DB` configuration for LiteLLM services, allowing models
  to be stored and managed within the database.

### Changed

- 🔐 **Enhanced Logout Security**: Improved the logout process to explicitly revoke the Keycloak session using the
  refresh token, ensuring a more complete and secure session termination.
- 🔄 **Forced Login Prompt**: Modified the authentication flow to include `prompt: 'login'`, which will now consistently
  prompt users for their credentials during login.
- ⚙️ **Flexible Keycloak Configuration**: Updated Keycloak realm and identity provider template variables to use
  `config_variant_suffix`, enhancing configuration flexibility across different deployment stages.
- 🌐 **Open WebUI CORS Delimiter**: Adjusted the `CORS_ALLOW_ORIGIN` configuration in Open WebUI services to use a
  semicolon (`;`) as a delimiter for multiple origins, improving compatibility.
- 📄 **Jupyter Lab Boolean Format**: Standardized the `JUPYTER_ENABLE_LAB` setting to use the boolean `true` format for
  consistency with Jupyter's configuration expectations.

### Removed

- 🗑️ **Development Configuration Cleanup**: Cleaned up obsolete blank lines and comments in development-specific
  `docker-compose` files, enhancing configuration readability.

______________________________________________________________________

## [v0.273.3] - 2026-04-07 - OpenWebUI Integration & Agent Provisioning Enhancements

### Added

- ✨ **OpenWebUI Agent Workspace Integration:** Introduced comprehensive integration with OpenWebUI, allowing dynamic
  provisioning and management of AI-Hub agent instances as workspace models. This enables a seamless experience for
  users interacting with AI-Hub agents directly within OpenWebUI.
- 🔑 **Keycloak Role-Based Access for OpenWebUI:** Configured Keycloak to include user roles in OpenID Connect tokens and
  defined specific admin roles for OpenWebUI, enhancing security and access management for the new integration.
- ⚙️ **Automated OpenWebUI Service Account Provisioning:** Implemented an automatic creation of a dedicated AI-Hub
  service account with administrator privileges in OpenWebUI's database, facilitating secure and programmatic model
  management via API.
- 🧪 **Improved Agent Provisioning with Redis Caching:** Enhanced agent discovery and synchronization to external
  platforms (Langfuse, OpenWebUI) by implementing a Redis-backed, hash-based caching mechanism, reducing redundant sync
  operations and improving efficiency.
- 🔐 **New JWT Library for OpenWebUI Security:** Added `pyjwt` as a new core dependency, providing essential
  cryptographic capabilities for secure token-based communication with OpenWebUI APIs.

### Changed

- 🔄 **Standardized Agent and Process Health Check Ports:** Unified the default health check port for all agent and
  process runners to `8090` (previously `8080`), preventing potential port conflicts and ensuring consistent monitoring.
- 🚀 **Refactored External Provisioning Orchestration:** Streamlined the agent instance synchronization logic within the
  API service, enabling a more robust and extensible system for provisioning agents to platforms like Langfuse and
  OpenWebUI.

______________________________________________________________________

## [v0.273.2] - 2026-04-07 - Establishing the Backup Service Framework

### Added

- ✨ **New Automated Backup Service:** Introduced a dedicated backup service built on Dagster, designed to orchestrate
  and manage system backups. This service runs as an independent set of Docker containers within the main project.
- 🦾 **Container Orchestration Capabilities:** Added core functionality to discover, stop, and restart Docker Compose
  containers using direct Docker daemon interaction, forming the basis for coordinated backup and restore operations.
- ⚡️ **Resilient Failure Recovery:** Implemented a critical safety mechanism that automatically restarts all managed
  containers if any part of the backup process fails, preventing prolonged service downtime.
- 📦 **Comprehensive Infrastructure for Backup Service:** Established all necessary Docker Compose configurations,
  Dagster definitions, and tooling for deploying and managing the new backup service across various environments (dev,
  build, local, latest, nightly).
- 📄 **Docker Interaction Utilities:** Provided a `DockerManager` for low-level Docker operations, enabling precise
  control over container lifecycle, file transfers, and command execution within the backup service.
- 🚦 **Dedicated Backup UI:** The backup Dagster instance now includes a dedicated webserver, accessible at
  `http://localhost:3004` in `dev` and `local` environments, for monitoring and manual triggering of backup processes.

### Changed

- 🔄 **Main Dagster Logging Configuration:** Updated the main Dagster instances to log `swiss_ai_hub` messages at `INFO`
  level, providing more consistent operational insights.
- 🧹 **Streamlined Backup Service Configuration:** Moved the backup service's `dagster.yaml` and `workspace.yaml`
  configurations into dynamically generated Docker Compose volume mounts, simplifying deployment and ensuring
  consistency.

### Removed

- 🗑️ **Deprecated Backup Development Workflow:** Removed the standalone `dagster dev` command from the backup package's
  Makefile, as development is now integrated with the Docker Compose setup.

______________________________________________________________________

## [v0.273.1] - 2026-04-01 - New Automated Backup Service & Improved Build Processes

### Added

- ✨ **Introduced `Backup Service`:** A new Dagster-based service has been added to provide automated database backup
  orchestration. This initial release establishes the foundational structure for future backup capabilities.
- 🔒 **Configured Backup Service Authentication:** Integrated Keycloak OAuth2 Proxy for the new `Backup Service`,
  ensuring secure access and management through a dedicated endpoint (e.g., `backup.<DOMAIN>`).
- 📦 **Added Docker Image Build Workflow for Backup:** A new GitHub Actions workflow has been established to automate the
  building and releasing of the `backup` service Docker image.
- ⚙️ **Integrated Backup Service into Build System:** The new `backup` package is now fully integrated into the
  project's `Makefile` for testing, linting, formatting, PR readiness checks, and consistent version bumping.
- 🚀 **Deployed Backup Service via Docker Compose:** The `backup` service, comprising Dagster code server, webserver, and
  daemon, along with its OAuth2 proxy, is now deployable across all environments via updated Docker Compose
  configurations.
- 📄 **Initial Backup Service Documentation:** A `README.md` file has been added to the `backup` package, outlining its
  purpose as a placeholder for backup and restore orchestration.

### Refactor

- 🧹 **Standardized Docker Build Contexts:** Refined the Dockerfile build contexts for numerous existing services (e.g.,
  `api`, `web`, `agents`, `pipelines`, `bot`) in the Docker Compose configurations to ensure consistent and correct
  local image building across the monorepo structure.

______________________________________________________________________

## [v0.273.0] - 2026-04-01 - Multi-Tenant API Routing & Active Tenant Experience

### Added

- 🦾 **PR Demo Video Skill**: Introduced a new skill that automates the generation of pull request demo video
  descriptions and updates test plan checklist items based on screen recordings, streamlining the PR review process.
- ✨ **Active Tenant Persistence**: The `UserEntity` now includes an `active_tenant_id` field, allowing the system to
  remember a user's last selected tenant for an improved multi-tenant user experience.
- 📄 **Tenant Path Parameter ADR**: A new Architecture Decision Record (`2026_03_30_tenant_path_parameter.md`) was added,
  detailing the strategic shift to tenant identification via a required URL path parameter.

### Changed

- 🔄 **Core API Tenant Routing**: All primary API endpoints now require a `{tenant_id}` path parameter (e.g.,
  `/api/v1/{tenant_id}/...`) for explicit tenant context. The `x-tenant-id` HTTP header is no longer supported, and
  there is no implicit fallback to a default tenant.
- 🚀 **"Active" Tenant Slug**: Introduced a special `"active"` slug (e.g., `/api/v1/active/...`) that resolves to the
  authenticated user's persisted active tenant, simplifying frontend interactions.
- 🔐 **Authentication Handlers**: Updated `AuthHandler` and its implementations (Keycloak, DangerousDevelopmentOnly,
  Token) to resolve tenant context from the URL path parameter and use the `active_tenant_id` for contexts without a
  request (e.g., WebSocket connections).
- 🤖 **Bot Framework Endpoints**: Azure Bot Service and other bot connection configurations were updated to utilize the
  new tenant-scoped API paths, primarily through the `/api/v1/active/...` slug.
- 🌐 **Frontend API Client**: The main frontend API client's `baseURL` was updated to use `/api/v1/active`, ensuring all
  frontend-initiated requests correctly leverage the active tenant context.
- ⚙️ **Deployment Configurations**: Numerous environment variables across `docker-compose` files (dev, build, latest,
  local, nightly variants) were updated to point to the new `/api/v1/active/...` API paths, ensuring consistent
  deployments.
- 📚 **Documentation & Skill Guides**: Extensive updates were made across all relevant documentation (ADRs, platform
  docs, skill definitions, `CLAUDE.md`, `README.md`) to reflect the new API routing, tenant identification, and active
  tenant behavior.
- 🩺 **Health Endpoints**: Health check endpoints are now specifically mounted outside the tenant scope at
  `/api/v1/health/`, allowing for unauthenticated status checks.

### Fixed

- 🐛 **Tenant Data Consistency on Deletion**: Enhanced the `delete_tenant_by_id` and `remove_user_from_tenant` operations
  to automatically clear the `active_tenant_id` for affected users, preventing stale tenant references when tenants or
  user-tenant associations are removed.

### Refactor

- 🧹 **API Routing Implementation**: The core `ApiRunner` logic was significantly refactored to implement the new
  tenant-scoped routing using Starlette `Mount` for path parameter capture, and to separate health endpoints.
- 🧪 **Test Suite Alignment**: Various API and authentication test cases, including mock request creation and tenant
  resolution scenarios, were updated to align with the new tenant path parameter and active tenant resolution logic.
- ⚡️ **OpenTelemetry Tracing**: Improved the OpenTelemetry span attributes in `Controller` to accurately record the
  *resolved* tenant ID for business context, filtering out the raw `{tenant_id}` path parameter.

______________________________________________________________________

## [v0.272.2] - 2026-03-31 - Enhanced Configuration Authorization for Secure Operations

### Added

- ✨ **Introduced Configuration Authorization Service:** A new service (`ConfigAuthorizationService`) has been
  implemented to automatically validate user permissions for resources referenced within agent and process
  configurations (e.g., knowledge databases, other agents) during their creation and update.
- 📄 **Authorization Violation Model:** A new data model (`ConfigAuthorizationViolation`) was added to standardize the
  reporting of configuration authorization issues, providing clear details on unauthorized resources.
- 🌐 **Localized Authorization Messages:** New translation keys for configuration authorization messages have been added
  across all supported languages (German, English, French, Italian), ensuring a consistent user experience.

### Changed

- 🔑 **Mandatory Configuration Authorization:** Agent and Process instance creation and update operations now include a
  mandatory step to enforce authorization checks on submitted configurations, preventing users from referencing
  resources they do not have access to.
- 🦾 **Agent Selector Authorization:** The **Agent Selector** form element now performs real-time authorization
  validation, ensuring users can only select and configure agents they are permitted to access.
- 📚 **Knowledge Database Selector Authorization:** The **Knowledge Database Selector** form element now performs
  authorization validation, ensuring users can only select knowledge databases they are permitted to access.
- 🔄 **Model Configuration Update:** The default Claude model has been updated to `opus[1m]`, and explicit support for
  this new model variant has been added to the list of available models.

### Refactor

- 🧹 **Form Module Exports:** Key form components, including `ConfigAuthorizationViolation`, `FormkitElement`, `Group`,
  `ModelSelect`, and `Repeater`, are now explicitly exported within the core form module for improved internal
  consistency and module organization.

______________________________________________________________________

## [v0.272.1] - 2026-03-30 - Robust Agent Context: Valkey AOF and True Thread Persistence

### Fixed

- ⚡️ **Enhanced Valkey Data Durability**: Addressed the previously identified "Valkey persistence gap" by enabling
  Append-Only File (AOF) persistence across all Valkey instances. This crucial update reduces potential data loss during
  crashes from 30 seconds to approximately 1 second, significantly improving the reliability of agent runtime state.

### Changed

- 💾 **Introduced Truly Persistent ThreadContext**: Modified the `ThreadContext` to be genuinely persistent by removing
  its 30-day Time-to-Live (TTL). This change ensures that conversation history, user preferences, and other long-lived
  agent-set data remain durable across multiple runs without automatic expiry.
- ⚙️ **Refined RunContext Lifecycle**: Clarified the behavior of `RunContext`, which is now explicitly cleaned up upon
  `StopEvent` completion. Its 30-day TTL now functions as a safety net for orphaned runs in case of unexpected crashes,
  ensuring data integrity while simplifying cleanup.
- 📄 **Updated Agent Context Documentation**: Improved documentation across `CLAUDE.md`, solution strategy, and SDK
  guides to accurately reflect the new persistence models and durability guarantees for `RunContext` and `ThreadContext`
  in Valkey.

### Refactor

- 🧹 **Improved IDE Configuration**: Streamlined the Node.js interpreter setup in `Web.xml` to use project-level
  settings, enhancing consistency for developers.
- 🧹 **Internal Code Cleanups**: Performed minor code reordering for imports and test configurations to improve
  maintainability and style.

______________________________________________________________________

## [v0.272.0] - 2026-03-25 - Empowering Agents with External Tooling: Introducing the MCP React Agent

### Added

- 🦾 **New MCP React Agent**: A sophisticated AI agent capable of dynamically discovering and interacting with tools and
  resources exposed by external Message Control Protocol (MCP) servers, leveraging ReAct reasoning.
- 🚀 **MCP Integration Framework**: Core components and utilities (`McpClientFactory`, `McpClientConfig`,
  `mcp_resource_schemas`, `mcp_tool_schemas`) for seamless and robust communication with MCP-compliant services.
- 📄 **Architectural Decision Record (ADR)**: A detailed document outlining the strategy for agents to consume MCP
  resources, utilizing system prompts for static data and a meta-tool for templated data.
- 🌐 **Internationalization for MCP Agent**: Added comprehensive localization support for the MCP React Agent's metadata,
  configuration parameters, and workflow steps in German, English, French, and Italian.
- ✨ **Tool Call ID to `ToolEvent`**: Introduced a `tool_call_id` field within `ToolEvent` to establish a clear link
  between a tool invocation and its corresponding result message.
- 🐳 **Docker Deployment for MCP Agent**: Provided a Dockerfile to facilitate the easy containerization and deployment of
  the new MCP React Agent.
- 🧪 **Playground Workflow for MCP React Agent**: A minimal example workflow, complete with a dummy MCP server, to
  demonstrate and test the capabilities of the MCP React Agent.
- 📦 **`fastmcp` Dependency**: Integrated `fastmcp` as a crucial dependency to enable direct client interaction with MCP
  servers.

### Changed

- 🔄 **Enhanced `Message` Tool Call Handling**: Improved the `Message` class to accurately normalize and preserve
  `tool_calls` data during conversion to and from `llama_index`'s `ChatMessage` format, ensuring data integrity across
  the LLM pipeline.
- 🔗 **OpenAI API Compatibility for `Message`**: Added methods `to_openai_dict` and `from_openai_response` to the
  `Message` class, enabling better interoperability with OpenAI API messages, especially for complex tool interactions.
- 🛡️ **Robust Content Extraction in `Message`**: Made the `content` property of the `Message` class more resilient by
  explicitly handling cases where message contents might be empty.

### Refactor

- 🧹 **Organized MCP Core Components**: Restructured the codebase by creating dedicated `packages/agent/mcp/` and
  `packages/core/mcp/` directories, centralizing all MCP-related infrastructure and agent-specific logic.
- ⚙️ **Standardized Line Endings**: Ensured consistent LF line endings for `.sh` files across the repository via
  `.gitattributes` for improved cross-platform compatibility.

______________________________________________________________________

## [v0.271.6] - 2026-03-25 - Document Processing Refinements

### Changed

- ⚡️ **Improved Document Intelligence Loader:** Enhanced file processing within the Document Intelligence Loader by
  switching to direct byte content reading, leading to more robust and compatible document analysis.

______________________________________________________________________

## [v0.271.5] - 2026-03-24 - Documentation Base Path Update and Link Alignment

### Changed

- 📄 **Updated Documentation Base Paths:** The base path for all project documentation has been consistently updated from
  `/swiss-ai-hub/` to `/aihub-core/` across the VitePress configuration, `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`,
  and the `install.sh` script. This ensures all documentation links and internal paths correctly point to the new
  `aihub-core` URL structure.

______________________________________________________________________

## [v0.271.4] - 2026-03-23 - Enhanced AI Workflow Automation and API Resilience

### Added

- 🦾 **Introduced a new `splice-issue` skill** for the AI assistant, enabling it to intelligently decompose large GitHub
  issues into smaller, independently mergeable sub-issues with appropriate dependency relationships, metadata
  inheritance, and project board priority propagation.

### Changed

- 📄 **Improved license report generation** by making the `generate-license.sh` script smart enough to preserve the
  existing "Generated on" date if the core content of the license report has not changed, reducing noise in version
  control.
- ⚙️ **Increased LiteLLM rate limit error retries** from 3 to 5 across all proxy configurations, enhancing the system's
  resilience and reliability against temporary API rate limits from model providers.

______________________________________________________________________

## [v0.271.3] - 2026-03-23 - Improved Agent Docker Image Documentation

### Changed

- 📄 **Enhanced Agent Docker Images**: The `README.md` file from the `packages/agent` module is now included in the
  Docker builds for all agent applications, ensuring better in-image documentation and context.

______________________________________________________________________

## [v0.271.2] - 2026-03-23 - Enhanced Test Suite Reliability

### Changed

- ⚡️ **Improved Test Suite Stability:** Marked several integration and memory-related tests as flaky, ensuring automatic
  retries on transient failures to enhance overall CI/CD reliability and reduce false-positive test failures.

______________________________________________________________________

## [v0.271.1] - 2026-03-23 - Configuration & CI/CD Refinements Post-Renaming

### Fixed

- 🐛 **Development Configuration File:** Corrected the JSON string formatting for `OTEL_CLOUD_HEADERS` within the
  `.env.dev` file to ensure proper parsing.

### Changed

- 📄 **Changelog Accuracy:** Updated the changelog entry for `v0.271.0` to fully detail the significant "Grand Renaming
  and Open-Source Restructure" that took place in that release.
- ⚙️ **Frontend Linting Process:** Modified the frontend linting GitHub Action to include an additional
  `nuxi prepare .app` step, ensuring comprehensive preparation for linting in the updated project structure.
- 🤖 **ChatBot Test Setup:** Enhanced `ChatBot` tests to provision a default tenant and assign administrative roles to
  the test user, improving the realism and robustness of multi-tenancy and authorization test environments.

### Refactor

- 🧹 **CI/CD Artifact Naming:** Standardized the naming convention for build artifacts (pytest, coverage reports) across
  GitHub Actions workflows by sanitizing working directory paths, increasing robustness and consistency in artifact
  management.
- 🔄 **CI/CD Workflow Paths:** Updated internal GitHub Actions workflow references from the older `swiss-ai-hub` path to
  `aihub-core` to align with the new repository and package naming conventions.
- 🏷️ **SonarCloud Project Identifiers:** Aligned SonarCloud project keys and names across all packages (`agent`, `api`,
  `bot`, `core`, `pipeline`, `process`, `web`) to reflect the new `aihub-core` branding and simplified naming.

______________________________________________________________________

## [v0.271.0] - 2026-03-19 - Grand Renaming and Open-Source Restructure

### Changed

- 🏗️ **Repository Layout**: Reorganized all source packages under `packages/` directory — `aihub_lib` → `packages/core`,
  `aihub_agent` → `packages/agent`, `aihub_api` → `packages/api`, `aihub_bot` → `packages/bot`, `aihub_pipeline` →
  `packages/pipeline`, `aihub_process` → `packages/process`, `swiss_ai_hub_web` → `packages/web`. Non-code directories
  moved to conventional locations: `aihub_doc` → `docs`, `aihub_action` → `.github/actions`, `deployment` →
  `infra/deployment`.
- 📦 **Python Namespace Packages**: All packages renamed to use `swiss_ai_hub` namespace via `uv_build` — import paths
  are now `swiss_ai_hub.core`, `swiss_ai_hub.agent`, etc. PyPI names follow as `swiss-ai-hub-core`,
  `swiss-ai-hub-agent`, etc.
- 🐍 **snake_case Everywhere**: Renamed all CamelCase Python source files and directories to `snake_case` (e.g.,
  `ExpertAskingAgent/ExpertAskingAgent.py` → `expert_asking_agent/expert_asking_agent.py`), resolving import ambiguity
  that previously prevented proper `__init__.py` usage.
- 📤 **Public Interface via `__init__.py`**: Added lazy `__init__.py` exports (using `TYPE_CHECKING` + `__getattr__`) to
  all top-level package folders, establishing clear public interfaces. Cross-package imports now go through
  `__init__.py`; intra-package imports use full module paths.
- 🔄 **Import Rewrite**: Updated all imports across the entire codebase to follow the new namespace structure and import
  conventions.
- 📝 **License Change**: Moved from `LicenseRef-Proprietary` to `Apache-2.0` across all packages.
- 📚 **Documentation Updates**: Updated all references from old naming conventions (`aihub_doc`, `aihub-core`, etc.) to
  new names across docs, READMEs, CLAUDE.md files, whitepapers, and configuration files.
- ⚙️ **Docker & CI Updates**: Updated all Docker Compose files, Dockerfiles, GitHub Actions workflows, and run
  configurations to reference the new directory structure and package names.

### Added

- 📄 **Architecture Decision Record**: Added ADR documenting the rename and restructure rationale
  (`docs/arc42/decisions/2026_03_13_rename_and_restructure_for_open_source_release.md`).
- 🏗️ **`docker-compose.build.yml`**: Added comprehensive build-stage Docker Compose for multi-stack orchestration.

### Removed

- 🗑️ **Old Directory Structure**: Removed all `aihub_*` top-level directories, replaced by `packages/` layout.
- 🗑️ **Deprecated Test Suites**: Removed outdated test suites for `AgentConfig` and `Form` classes.
- 🗑️ **Outdated READMEs**: Removed stale README files that were superseded by the restructure.

______________________________________________________________________

## [v0.270.4] - 2026-03-19 - Enhanced Configuration and Dev Environment Streamlining

### Changed

- ✨ **Updated `MinerU2.5-2509-1.2B` Model Identifier:** Corrected the internal model name from `openai/mineru` to
  `openai/MinerU2.5-2509-1.2B` across all LiteLLM configurations, ensuring accurate model referencing.
- ⚙️ **Simplified Development CORS Configuration:** Adjusted the `CORS_ALLOW_ORIGIN` setting for development
  environments to `http://localhost:8080`, streamlining local frontend development and testing.
- 🌐 **Improved Development Playwright Integration:** Updated the `PLAYWRIGHT_WS_URL` for development environments to
  `ws://localhost:3036`, making local Playwright service integration more straightforward.

______________________________________________________________________

## [v0.270.3] - 2026-03-11 - Repository Cleanup: Streamlining Project Configuration

### Removed

- 🗑️ **IDE Configuration Files:** Deleted all `.idea/` directories and their associated configuration files (e.g.,
  `misc.xml`, `modules.xml`, `inspectionProfiles/`) from the main project and various sub-projects (`aihub_agent`,
  `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) to clean up the repository and remove
  environment-specific configurations.

### Changed

- 🧹 **Updated Git Ignore Rules:** Modified the root `.gitignore` file to explicitly exclude `.idea/misc.xml` and all
  `aihub_*/.idea/` directories, preventing IDE-specific files from being committed in the future and maintaining a
  cleaner codebase.

______________________________________________________________________

## [v0.270.2] - 2026-03-09 - Deployment Script Readability Enhancements

### Refactor

- 🧹 **Enhanced Deployment Script Clarity:** Renamed internal variables for destination paths (`output_dir` to `dst_rel`)
  within the deployment generation scripts to improve code readability and maintainability.

______________________________________________________________________

## [v0.270.1] - 2026-03-05 - Enhanced Authentication Experience and Deployment Flexibility

### Added

- ✨ **Custom Keycloak Login Theme**: Introduced a new `aihub` custom login theme for Keycloak, providing a branded and
  dark-mode compatible authentication experience.
- 🔑 **Keycloak Account Audience Mapper**: Added an OIDC audience mapper for the `account` client within Keycloak realms,
  ensuring proper audience claims in tokens.

### Changed

- 🚀 **Flexible Keycloak Entrypoint**: Updated the Keycloak entrypoint script and its Docker Compose integration to
  support dynamic arguments for `kc.sh`, enhancing deployment flexibility across all stages.
- ⚙️ **Standardized Keycloak Realm Imports**: All Keycloak realm configurations are now consistently processed as
  templates by the entrypoint script before import, streamlining environment variable substitution.
- 🌐 **Updated Development Environment URLs**: Adjusted Keycloak client `rootUrl`, `redirectUris`, and
  `post.logout.redirect.uris` for the development environment to `http://localhost:3333`, aligning with current frontend
  settings.
- 🔐 **Refined OpenWebUI OIDC Configuration**: Modified the `OPENID_PROVIDER_URL` for OpenWebUI in development
  environments to `http://localhost:8180` for improved local setup consistency.
- 🛠️ **Enhanced Deployment Script for Static Assets**: The `generate_compose.py` script now supports copying static
  directories and files, enabling the seamless inclusion of custom themes and other assets in deployments.
- 📝 **Adjusted Logging Configuration**: Fine-tuned the list of modules for which logging is disabled in `aihub_lib` for
  improved log output.

### Fixed

- 🐛 **License Generation Locale Compatibility**: Added `LC_ALL=C` export to the `generate-license.sh` script to ensure
  consistent behavior across different locales.

______________________________________________________________________

## [v0.270.0] - 2026-03-04 - Keycloak Takes the Helm: Major Authentication Overhaul with Dynamic Identity & Enhanced Security

### Added

- 🔐 **Keycloak Identity and Access Management (IAM) System**: Fully integrated Keycloak as the central identity broker,
  enabling OIDC/OAuth2 authentication for all platform services. This provides multi-provider federation, improved local
  development experience, and enhanced control over identity.
- ✨ **Dynamic Identity Provider Discovery**: Introduced an API endpoint (`/auth-providers`) and a new frontend component
  to dynamically fetch and display available identity providers from Keycloak. This allows for flexible, IdP-specific
  login buttons with custom icons on the authentication page, eliminating static configuration.
- 📄 **New Architecture Decision Records (ADRs)**: Documented key architectural decisions regarding Keycloak integration,
  seamless OpenWebUI SSO in iframes, parent application ownership of authentication state, and multi-tenant assignment
  via Keycloak groups.
- 🧪 **Playwright E2E Testing Framework**: Implemented a new End-to-End (E2E) testing framework using Playwright for the
  web UI, including an automated authentication setup to ensure reliable testing of user flows.
- ⚙️ **Centralized Tenant Configuration**: Introduced a new `TenantSettings` class to centralize configuration for
  multi-tenant aspects, such as default tenant name, description, access rules, and initial user signup roles.
- ➕ **Dedicated Keycloak API Service Account**: Created a least-privilege Keycloak service account (`aihub-api-service`)
  for the API backend to securely query identity provider information.

### Changed

- 🔄 **Unified OIDC Client Configuration**: Updated the platform's OIDC client to directly integrate with Keycloak,
  ensuring consistent authentication against the new identity broker.
- 🛠️ **Service-Wide Authentication Rework**: Reworked the authentication configuration across all Docker Compose
  services (Admin UI, OpenWebUI, Dagster, SeaweedFS, Attu, Langfuse, API) to leverage Keycloak as the OIDC provider,
  ensuring a consistent and centralized authentication flow.
- 🚀 **Improved OpenWebUI SSO Experience**: Optimized the integration of OpenWebUI by directly initiating its OAuth login
  flow within the iframe, providing a seamless Single Sign-On experience for users.
- 🌎 **Dynamic Login Page UI**: The frontend login page now dynamically renders authentication buttons based on the
  discovered identity providers, enhancing flexibility and user choice.
- 📝 **Comprehensive Documentation Updates**: Updated platform documentation, including the authentication setup,
  prerequisites, multi-tenancy guides, and quick start instructions, to reflect the new Keycloak-based identity
  management system and associated roles.
- 📦 **PostgreSQL Database Expansion**: Configured the PostgreSQL service to manage a new dedicated database for
  Keycloak, ensuring proper data isolation and persistence for the IAM system.
- 🏗️ **Automated Compose File Generation**: Enhanced the `generate-compose` Makefile target to automatically include
  Keycloak-specific configurations and ensure proper YAML formatting.

### Security

- 🛡️ **Elevated Admin Tool Access Role**: Restricted access to critical infrastructure administration tools (Dagster,
  SeaweedFS, Attu) to users with the new `AIHubSysAdmin` realm role, enhancing security for these sensitive services.
- 🔒 **Hardened Keycloak Admin Console Access**: Documented and implemented IP allowlisting capabilities via Traefik
  middleware to restrict access to the Keycloak admin console and metrics endpoint in production deployments.
- 🔐 **Secure OpenWebUI CORS Policy**: Hardened the Cross-Origin Resource Sharing (CORS) policy for OpenWebUI, explicitly
  allowing access only from trusted domains to prevent unauthorized access.
- 👮 **Mandatory `AIHubAccess` Role Enforcement**: Configured Keycloak authentication flows to deny login to any user who
  does not possess the `AIHubAccess` realm role, acting as a crucial access gate.

### Fixed

- 🐛 **Graceful Iframe Logout Handling**: Resolved an issue where logging out from embedded services (e.g., OpenWebUI)
  could lead to a blank iframe. The parent application now detects this and redirects the user to the home page while
  preserving the main session.
- 🩹 **S3 Anonymous File Download Error Handling**: Corrected the error type from `IOError` to `OSError` in the S3
  anonymous file access service, improving the robustness and accuracy of error handling during file download
  operations.

### Removed

- 🗑️ **Direct Azure AD Configuration & Handlers**: Eliminated all environment variables and code paths related to direct
  Azure AD integration, including the `OAuth2AuthHandler` and its settings, in favor of the new Keycloak-centric
  architecture.
- 🗑️ **Obsolete Authentication Strategy Resolver**: Eliminated an outdated utility for resolving authentication
  strategies, simplifying the authentication codebase.

______________________________________________________________________

## [v0.269.4] - 2026-03-03 - Streamlined Setup and Enhanced Observability

### Added

- 🚀 **One-Command Installer:** Introduced a new `install.sh` script to simplify platform setup and upgrades, featuring
  auto-detection for GPU hardware and robust `.env` secret generation.
- 🖼️ **Platform Tour Demos:** Added new demo videos and images to the `README.md` and documentation, visually showcasing
  key platform features like document ingestion, agent interaction, and cost control.
- ✨ **Standardized Startup Banner:** All core services now display a consistent startup banner with version information,
  improving visibility and branding upon service launch.

### Changed

- 📄 **Revamped Main Documentation:** The `README.md` has been completely rewritten to provide a higher-level overview, a
  more intuitive quick start guide, and a comprehensive platform tour, making it easier for new users to understand and
  engage with the Swiss AI-Hub.
- ⚙️ **Unified Versioning Configuration:** Renamed the `AIHUB_API_VERSION` environment variable to `AIHUB_VERSION`
  across all `.env` files, Dockerfiles, and internal settings for greater consistency.
- 📦 **Centralized Version Management:** The platform's version is now automatically derived from package metadata,
  ensuring consistency across all components and deployment artifacts.
- 🇩🇪 **Improved German Documentation:** Enhanced clarity and detail in German documentation, particularly for sections
  on low-level traces (including AITL delegation details), quick start, and update/maintenance procedures.

### Refactor

- 🧹 **Consolidated Version Environment Variables:** Standardized the version environment variable name (e.g.,
  `AIHUB_AGENT_VERSION`, `AIHUB_PIPELINE_VERSION` merged into `AIHUB_VERSION`) across all Python services and Docker
  images for simplified configuration.

______________________________________________________________________

## [v0.269.3] - 2026-03-03 - Expanded Document Parsing and Flexible File Handling

### Added

- ✨ **New RawLoader for Plaintext Files:** Introduced a dedicated loader for various plaintext formats (e.g., `txt`,
  `md`, `csv`, `json`, `xml`, `yml`, `yaml`, `log`, `ini`, `cfg`, `toml`) to ensure accurate content parsing without
  conversion.
- ⚙️ **Configurable Passthrough Extensions:** Added a new setting, `ParsingSettings.PASSTHROUGH_EXTENSIONS`, allowing
  configuration of file types (like `zip` or `wav`) that bypass markdown conversion and return empty content, enabling
  agents to access the raw files directly from S3.
- 📦 **Direct S3 File Download:** Implemented `S3AnonymousFileAccessService.download_file` to enable raw byte downloads
  from S3, facilitating in-memory processing for various file types beyond standard document parsing.

### Changed

- 🔄 **Updated Document Parsing Service:** The `ParsingService` now intelligently routes documents to the new `RawLoader`
  for plaintext files and incorporates the configurable passthrough mechanism for agent-centric file types,
  significantly improving versatility and robustness.
- 📄 **Dynamic Extension Support in Parser:** The `DocumentParserResource` now dynamically includes all supported
  extensions from `RawLoader`, simplifying configuration and ensuring consistent parsing capabilities.
- 🚨 **Improved Unsupported File Type Messaging:** Enhanced the error message for unsupported file types in the parsing
  service to clearly list all currently recognized extensions, including those handled by the new `RawLoader`.

### Refactor

- 🧹 **Minor Import Clean-up:** Removed an unused import in the `TraceStore` module for improved code hygiene.

______________________________________________________________________

## [v0.269.2] - 2026-02-27 - Release Packaging Refinement

### Fixed

- 📦 **Improved Release Archive Structure:** Corrected the packaging process for `.tar.gz` release artifacts to ensure
  they now extract into a proper, versioned top-level directory, enhancing consistency and user experience upon
  extraction.

______________________________________________________________________

## [v0.269.1] - 2026-02-27 - Enhanced Distributed Tracing and Agent-in-the-Loop Observability

### Added

- 🚀 **Introduced `TraceStore`:** A new Redis-backed store designed to persist tracing metadata, which is crucial for
  enabling distributed tracing across agent runs and Agent-in-the-Loop (AITL) delegations.
- ✨ **Added OpenInference Trace Context Propagation:** Implemented a new context management system
  (`openinference_trace_context`) that propagates OpenInference trace state. This ensures that `CHAIN` span kinds are
  automatically applied to traced functions, maintaining consistent observability across workflows.
- 🦾 **Implemented AITL Wrapper Spans:** New tracing logic creates dedicated `AGENT` wrapper spans for Agent-in-the-Loop
  (AITL) delegations. These spans bridge the caller's trace to the delegated agent's steps, enabling clear nested
  visibility in observability tools like Langfuse.

### Changed

- 🔄 **Refactored Agent Tracing Architecture:** The `AgentRunTracer` was significantly refactored to utilize the new
  `TraceStore` for all run metadata, including user input, user ID, and LLM output. This change replaces previous
  in-memory caches and enables cross-service trace continuity.
- 📝 **Updated Tracing Documentation:** The platform's documentation on low-level traces has been thoroughly updated to
  reflect the new distributed tracing architecture, AITL delegation, and enhanced Langfuse integration details.
- ⚙️ **Improved OpenTelemetry Collector Configuration:** Modified OpenTelemetry collector configurations to include a
  `filter/noise` processor in the Langfuse trace pipeline. This helps reduce unwanted telemetry noise and improves the
  quality of ingested traces.
- ⚡️ **Enhanced Docker Compose Dependencies:** Adjusted `docker-compose` configurations to improve service startup
  reliability by ensuring that the `langfuse-server` service now explicitly waits for `langfuse-web` to be in a healthy
  state.

### Fixed

- 🐛 **Corrected Retriever Namespace Filtering:** Addressed an issue in `filter_retrievers_by_namespace` where retriever
  namespaces were being updated incorrectly. The fix ensures proper filtering based on the `vector_store`'s
  `index_namespaces`.
- 🛡️ **Improved Langfuse Model Provisioning Robustness:** Enhanced the `LangfuseProvisioner` to gracefully handle `400`
  errors containing "already exists" messages during model definition creation, treating them as conflicts similar to
  `409` status codes to prevent failures.

### Refactor

- 🧹 **Streamlined `AgentDispatcher` Cleanup:** Simplified the run completion cleanup logic within the `AgentDispatcher`.
  The explicit `clear_run` call for tracing metadata is now removed, as cleanup is automatically handled by the
  `TraceStore`.
- 🧪 **Overhauled Agent Tracing Test Suite:** The entire test suite for `AgentRunTracer` has been updated to align with
  the new Redis-backed `TraceStore` and the distributed tracing functionalities, removing outdated cache tests and
  adding comprehensive coverage for AITL scenarios.
- ⚙️ **Refined Python Auto-Formatting Hook:** Adjusted the `.claude/hooks/auto-format-python.sh` script to ignore the
  `F401` (unused import) ruff check during the `--fix` step, providing more flexibility for specific code patterns
  without causing formatting conflicts.

______________________________________________________________________

## [v0.269.0] - 2026-02-26 - Revamped AI Model Strategy: Embracing Swiss Sovereignty with Dual-Mode Inference & Standardized Models

### Added

- ✨ **Introduced Swiss LLM Cloud Integration**: Full support for Swiss LLM Cloud across various AI tasks (text
  generation, embedding, reranking, whisper, OCR) to ensure data sovereignty and provide a diverse range of models for
  non-GPU deployments.
- 🦾 **Integrated Local vLLM for GPU Deployments**: Replaced `llama.cpp` with `vLLM` for high-performance local GPU
  inference, supporting text generation, embeddings, and reranking on NVIDIA RTX 6000 Pro with explicit VRAM budgets.
- 📄 **New Architectural Decision Record (ADR)**: Added a comprehensive ADR outlining the rationale and details of the
  Swiss LLM Cloud and local vLLM dual-mode inference strategy.
- 💡 **New AI Toolkit Settings**: Added `.idea/ai_toolkit.xml` for improved AI-assisted development experience in IDEs.
- ⬆️ **New Environment Variables for Swiss LLM Cloud**: Added specific environment variables for different Swiss LLM
  Cloud API endpoints (embedding, reranking, whisper, OCR) for fine-grained configuration.

### Changed

- 🔄 **Centralized AI Model Strategy**: Migrated the platform's core AI model inference from Azure OpenAI and Cohere to a
  dual-mode strategy utilizing Swiss LLM Cloud for non-GPU deployments and local `vLLM` for GPU-enabled setups.
- ⚙️ **Standardized Model Naming Convention**: Replaced abstract model tier names (e.g., `text-generation/nano`,
  `embedding/large`) with canonical, descriptive model names (e.g., `text-generation/gpt-oss-120b`, `embedding/bge-m3`)
  across LiteLLM configurations, agent templates, and pipeline definitions for clarity and consistency.
- 📝 **Updated Documentation for Model Strategy**: Extensively updated architecture, quick start, deployment guide, and
  security documentation to reflect the new AI model inference strategy, including details on Swiss LLM Cloud and vLLM
  integration.
- 🚀 **Enhanced Document Parsing with MinerU**: Transitioned the primary document parsing service from Docling to MinerU,
  updating related configurations, resource definitions, and documentation in Dagster pipelines and API routes.
- ⚡️ **Improved Mem0 Compatibility**: Integrated patches for Mem0's OpenAI LLM and embedding components to ensure
  seamless compatibility with Swiss LLM Cloud's API behavior, particularly concerning `dimensions` and
  `response_format`.
- 🔢 **Adjusted Milvus Embedding Dimensions**: Updated the default Milvus embedding dimension from 3072 to 1024, aligning
  with the BGE-M3 embedding model used in the new model strategy.
- 🗣️ **Refined Expert Escalation Prompt**: Modified the `expert_answer_sufficient` prompt template to focus on the
  *latest* expert answer in the conversation history, improving the accuracy of agent-driven expert interaction
  assessments.
- 🛠️ **Updated GitHub Actions for CI**: Modified the `analyze-test-pr.yml` workflow to remove `llama.cpp` services,
  inject new Swiss LLM Cloud secrets, and no longer skip `azure`-marked tests, streamlining the CI pipeline.
- 🧹 **Updated IDE Test Configurations**: Removed the `-k "not azure"` flag from PyCharm/IntelliJ run configurations for
  API, Agent, Bot, Lib, and Process tests, enabling all tests to run without Azure-specific exclusions.

### Fixed

- 🐛 **Ensured Idempotent Logging Configuration**: Implemented a fix in `aihub_lib`'s logging setup and OpenTelemetry
  integration to prevent duplicate log handlers from being added when `enable_logging` is called multiple times.

### Removed

- 🗑️ **Deprecated `llama.cpp` Inference Services**: Eliminated `llama.cpp` containers for chat, embeddings, and
  reranking from Docker Compose files, in favor of `vLLM` for GPU deployments or Swiss LLM Cloud for non-GPU.
- 🗑️ **Removed Azure OpenAI and Cohere Integrations**: Azure OpenAI base URLs and keys, as well as Cohere API base and
  keys, were removed from environment configurations and LiteLLM settings, consolidating cloud inference to Swiss LLM
  Cloud.
- 🚫 **Dropped Image Generation and Text-to-Speech (TTS) Capabilities**: Removed DALL-E 3 and Kokoro/TTS model
  configurations due to the lack of Swiss-sovereign alternatives in the new model strategy.
- 🧹 **Eliminated Azure-Specific Test Markers**: The `@pytest.mark.azure` marker and related exclusions were removed from
  Python test files and `pyproject.toml` configurations, simplifying test management.
- ❌ **Removed AI Code Review GitHub Action**: The `review-pr.yml` workflow and its associated action definition were
  removed from the repository.

### Refactor

- 🧹 **Streamlined Agent Configuration**: Removed the redundant `agent_class` field from `AgentConfig` and its subclasses
  across various agent definitions in `aihub_agent` for cleaner configuration.
- 🔄 **Standardized License Generation Output**: Modified the `generate-license.sh` script to sort Python packages and
  Docker images alphabetically in the output, ensuring deterministic and consistent license reports.
- ⚙️ **Reordered `pr-ready` Makefile Targets**: Adjusted the execution order of `format-md` and `format-yaml` in the
  `pr-ready` Makefile target for logical consistency.

______________________________________________________________________

## [v0.268.0] - 2026-02-26 - Introducing Secure Agent File Uploads and Streamlined Integrations

### Added

- ✨ **New Secure File Upload API for Agents:** Introduced dedicated API endpoints to securely initiate and validate file
  uploads to agent instances, providing presigned URLs for direct bucket interaction.
- 🚀 **Dedicated Agent File Storage:** Implemented a new shared S3 bucket (`agent-files`) for all agent-related user
  uploads. This bucket is automatically created and configured with a 7-day lifecycle policy to expire files, ensuring
  efficient storage management.
- 🦾 **File ID Reference System:** Enhanced the `UserUploadedFile` NATS event model to include a unique `file_id`,
  enabling agents to reference uploaded files by identifier instead of directly embedding large file data.
- 🧪 **Comprehensive Test Coverage:** Added extensive unit and integration tests to ensure the reliability and security
  of the new file upload service and API endpoints.

### Changed

- 🔄 **OpenWebUI File Upload Workflow:** The OpenWebUI integration pipeline has been updated to utilize the new secure
  agent file upload API. Files are now fetched from OpenWebUI's S3, uploaded to the agent's dedicated bucket via
  presigned URLs, and validated, streamlining the data flow.
- 🔒 **Granular File Access Control:** Agent instance permissions are now tied to file upload capabilities, ensuring that
  only authorized users can upload files to specific agent instances.

### Removed

- 🗑️ **Deprecated `file_data` in NATS Event:** The `file_data` field (base64-encoded content) has been removed from the
  `UserUploadedFile` NATS event, shifting to a more scalable file reference mechanism.
- 🧹 **Internal S3 Storage Adapter from OpenWebUI Pipeline:** The internal `S3StorageAdapter` and `FileStorageAdapter`
  protocol have been removed from the OpenWebUI integration, as file interaction is now handled by the new AI-Hub API.

### Security

- 🔑 **Path Traversal Prevention:** Introduced stringent validation for filenames and path segments in file upload
  requests and the `UserUploadedFile` model to actively prevent path traversal attacks.
- 🛡️ **Presigned URL Security Model:** Leveraged presigned URLs for file uploads, significantly enhancing security by
  providing temporary, single-use access to S3 resources, eliminating the need for persistent credentials on the client
  side.

______________________________________________________________________

## [v0.267.4] - 2026-02-26 - Pipeline Robustness: Enhanced Partition Key Encoding

### Added

- ✨ **New Partition Key Encoding Utilities:** Introduced `encode_partition_key` and `decode_partition_key` functions to
  safely URL-encode and decode file paths, ensuring compatibility when used as Dagster partition keys.
- 🚀 **`encode_partition_keys` Configuration:** Added a new `encode_partition_keys` parameter to
  `observable_data_lake_factory`, `observable_local_file_system_factory`, and `observable_rclone_factory`, allowing
  pipelines to opt-in to URL-encoded partition keys.
- ⚙️ **IO Manager Encoding Support:** `LocalFileSystemIOManager`, `RcloneIOManager`, and `S3DataLakeIOManager` now
  include an `encode_partition_keys` configuration, enabling automatic decoding of partition keys for accurate file
  retrieval.
- 🛡️ **Robust Data Versioning:** Data versioning ops for data lake, local file system, and rclone sources
  (`data_version_by_partition_for_data_lake_files_no_op`, `data_version_by_partition_for_local_files`,
  `data_version_by_partition_for_rclone_files`) now support generating URL-encoded partition keys when
  `encode_partition_keys` is enabled.
- ✅ **Comprehensive Test Coverage:** Added extensive unit tests for partition key encoding/decoding utilities and their
  integration within IO managers and ops to ensure robustness and correct behavior.

### Changed

- 🔄 **Pipeline Definition Factories Updated:** `default_definitions`,
  `default_local_filesystem_to_datalake_definitions`, and `default_rclone_to_datalake_definitions` now accept an
  `encode_partition_keys` parameter, providing a centralized control point for this new functionality.
- ⚠️ **Deprecation Warning for `encode_partition_keys` Default:** When `encode_partition_keys` is not explicitly set in
  pipeline definition factories, a deprecation warning is now emitted, indicating that the default behavior will change
  from `False` to `True` in a future release.

______________________________________________________________________

## [v0.267.3] - 2026-02-26 - Enhanced User Experience with Dedicated Account Management

### Added

- 🚀 **Introduced 'My Account' API Endpoint:** A new dedicated API endpoint `/my-account` allows users to retrieve and
  manage their personal profile and dashboard settings, separate from administrative user management.
- ✨ **Created MyAccountController and Service:** Implemented new backend components (`MyAccountController` and
  `MyAccountService`) to handle personal user account data, including profile details and dashboard configurations.
- 📄 **Added 'My Account' Frontend Page:** A new `my-account.vue` page provides a centralized view for users to inspect
  their profile, roles, last access time, and granular access permissions across services, agents, and processes.
- 🌐 **Expanded Internationalization for Account Management:** Added new translations across all supported languages for
  "My Account," "Services," "Agents," and "Processes" to support the new user profile section.

### Changed

- 🔄 **Refocused UserController for Administrative Tasks:** The existing `UserController` has been narrowed in scope to
  exclusively manage administrative user operations within a tenant, such as listing all users or retrieving specific
  user details by OID.
- 🧹 **Updated UserService to Admin-Level Operations:** The `UserService` now focuses solely on backend logic for
  administrative user management, with personal account-related functions moved to the new `MyAccountService`.
- 🖼️ **Revised RoleController Icon:** The icon for the `RoleController` has been updated from `mage:users` to
  `mage:security-shield` to better reflect its function of managing security roles.
- ⚡️ **Adjusted Default Landing Page for Users:** Non-admin users are now automatically redirected to the
  `/service/openai` page upon login, improving the initial user experience by guiding them directly to functional areas.
- 📝 **Clarified User Management Titles:** Updated the "User" title in internationalization files to "Users" (English)
  and corresponding terms in other languages, to distinguish between individual user accounts and the administrative
  list of users.

### Refactor

- 🏗️ **Architectural Separation of User Account and User Management:** Significant architectural refactoring to cleanly
  separate endpoints and services for a user's *personal account settings* (now `/my-account`) from *administrative user
  management* (still `/users`), enhancing modularity and security.
- 🧹 **Migrated Personal Dashboard Endpoints:** Dashboard retrieval and update endpoints previously under
  `/users/me/dashboard` have been migrated to the new `/my-account/dashboard` route, aligning with the new account
  management structure.

______________________________________________________________________

## [v0.267.2] - 2026-02-26 - Streamlined Release Note Extraction

### Added

- ✨ **New `extract-release-notes` Makefile Target:** Introduced a dedicated `Makefile` target to standardize and
  centralize the process of extracting version-specific release notes from `CHANGELOG.md`, improving reusability and
  maintainability.

### Changed

- 🔄 **Updated Release Workflow:** The GitHub Actions release creation process now utilizes the new
  `extract-release-notes` Makefile target for generating changelog entries, simplifying the workflow configuration and
  reducing redundancy.

### Refactor

- 🧹 **Enhanced Release Note Extraction Logic:** Refactored the underlying logic for extracting release notes to include
  robust input validation for version tags and improved fallback handling when a specific changelog section is not
  found.

______________________________________________________________________

## [v0.267.1] - 2026-02-25 - Streamlined Deployment with Self-Contained Release Bundles

### Added

- ✨ **New GitHub Release Workflow**: A comprehensive GitHub Actions workflow (`create-release.yml`) was introduced to
  fully automate the creation and publishing of self-contained release bundles to GitHub. This includes generating,
  verifying, archiving, and uploading CPU and GPU deployment packages.
- 🔐 **Automated Environment Setup Script**: A new `setup-env.sh` script now automatically generates secure `.env` files
  for production deployments, filling in unique, cryptographically strong secrets for database passwords, API keys, and
  other sensitive values from a template.
- 📦 **`generate-release` Makefile Target**: A new `Makefile` target has been added to facilitate the creation of
  version-pinned Docker Compose and configuration bundles for official releases, integrating seamlessly with the
  automated release workflow.

### Changed

- 🚀 **Fundamental Deployment Strategy**: The recommended production deployment method has transitioned to downloading
  self-contained CPU and GPU release bundles directly from GitHub Releases, simplifying initial setup and updates
  significantly.
- 📄 **Deployment & Update Documentation**: The "One-Command Deployment Guide" and "Updates and Maintenance"
  documentation have been completely revised to reflect the new bundle-based deployment, automated environment
  configuration, and streamlined update processes.
- ⚙️ **Docker Compose Generation**: The underlying `generate_compose.py` script has been substantially upgraded to
  support a new "release mode" for creating deployable bundles with version-pinned image tags and simplified
  configuration filenames.
- 🛠️ **Local Development Setup**: Local setup instructions are now streamlined to encourage `git clone` of the
  repository and the use of a new `make local-cert` command for easier certificate generation.

### Refactor

- 🧹 **CI/CD Workflow Run Naming**: Standardized `run-name` configurations across all build and deploy GitHub Actions
  workflows for clearer identification and tracking of CI/CD pipeline executions.
- 🔄 **Docker Compose Template Flexibility**: Refactored Docker Compose templates to introduce a `config_file_suffix`
  variable, allowing for cleaner filenames without stage or hardware specific suffixes in generated release bundles.

______________________________________________________________________

## [v0.267.0] - 2026-02-25 - Secure Document Access and API Simplification

### Added

- ✨ **Introduced API for secure document source URLs:** A new endpoint
  (`GET /databases/{database}/namespaces/{namespace}/documents/{document_id}/url`) allows authenticated users to obtain
  a short-lived, secure URL for downloading a document's original source file, enhancing security and control over data
  access.
- 🦾 **Enhanced document lookup by namespace:** Added a new method (`RefDoc.by_id_and_namespace`) to efficiently retrieve
  document references using both document ID and namespace, improving data retrieval for knowledge base operations.

### Changed

- 🔄 **Updated document download mechanism in frontend:** The web application now utilizes the new backend API endpoint
  to fetch secure, presigned URLs for document downloads. This change centralizes file access through the backend,
  improving consistency and security.

### Removed

- 🗑️ **Removed direct file redirection for logged-in users:** The `/logged-in/redirect` endpoint and its associated
  backend logic for file redirection have been removed, streamlining the API and consolidating file access patterns.

______________________________________________________________________

## [v0.266.5] - 2026-02-25 - Milvus Compatibility Update

### Fixed

- 🐛 **Resolved Milvus Resource Initialization:** Addressed an issue where the **MilvusVectorStoreResource** could fail
  to initialize in synchronous environments (e.g., Dagster resource creation) when using `pymilvus 2.6+`. This was due
  to `pymilvus`'s internal reliance on an `asyncio` event loop during initialization, and the fix ensures a loop is
  present to allow for seamless and robust resource setup.

______________________________________________________________________

## [v0.266.4] - 2026-02-25 - Port Harmonization for Streamlined Local Development

### Changed

- ⚡️ **Standardized Local Development Ports:** Aligned the default development ports for key services to improve
  consistency and reduce potential conflicts during local development:
  - The **Admin UI (Frontend)** now runs on `http://localhost:3333` (previously `3000`).
  - The **Dagster Orchestrator** now runs on `http://localhost:3000` (previously `3002`).
- 🦾 **Improved Dagster Tool Integration:** Updated the `mcp-server-dagster` script to correctly utilize the `--url`
  argument for specifying the Dagster instance, simplifying its configuration and removing the need for an inline Python
  patch.
- 📄 **Updated Documentation and Configuration:** All relevant documentation, skill prerequisites, environment variables
  (`.env.dev`), and Docker Compose configurations have been updated to reflect the new port assignments for the Admin UI
  and Dagster.

______________________________________________________________________

## [v0.266.3] - 2026-02-25 - Enhanced Git Push Command Management

### Changed

- ✨ **Expanded `git push` Command Recognition:** The system now recognizes and handles a significantly broader range of
  `git push` commands, including those with advanced options such as `--force-with-lease`, `--delete`, `--mirror`,
  `--all`, and `--tags`. This enhances the system's ability to understand and process complex push operations more
  intelligently.
- 🚀 **Streamlined `git push` Interactions:** Generic and specific `git push` operations have been refined in their
  handling, potentially leading to more seamless execution and fewer prompts during typical `git push` workflows.

______________________________________________________________________

## [v0.266.2] - 2026-02-25 - Streamlined Workflow Configuration

### Changed

- 🔄 **Streamlined GitHub Actions YAML:** Updated the `additional_permissions` configuration in `claude.yml` to use a
  more concise single-line scalar format, improving the readability of workflow definitions.

### Refactor

- 🧹 **Cleaned Workflow Configurations:** Removed unnecessary blank lines and commented-out placeholders from both
  `claude-code-review.yml` and `claude.yml`, enhancing file clarity and reducing clutter within the workflow
  definitions.

______________________________________________________________________

## [v0.266.1] - 2026-02-24 - Changelog Precision Update

### Fixed

- 🐛 **Updated changelog entry date:** Corrected the placeholder date for the `v0.262.2` release from `YYYY-MM-DD` to
  `2026-02-17` to ensure historical accuracy.

______________________________________________________________________

## [v0.266.0] - 2026-02-24 - Major Overhaul: Multi-Tenant Access Control and Core System Refinements

### Added

- ✨ Introduced **Multi-Tenant Architecture**: Core entities such as `TenantEntity` and `UserTenantRoleEntity` enable
  robust organizational isolation and tenant-scoped user management.
- 🔑 New **Local Role Management**: Roles are now managed directly within the platform's database, supporting both
  system-wide and tenant-specific roles, which reduces external dependencies for role synchronization.
- 🚀 Enabled **Automatic Default Tenant Initialization**: A default tenant is now automatically created and configured
  during the initial startup, ensuring immediate multi-tenant functionality.
- 👥 Implemented **Configurable User Signup Roles**: Roles are now automatically assigned to the first administrator and
  subsequent regular users upon their initial login, streamlining user onboarding.
- 📄 New SDK documentation for the **Agent Execution Model** and a detailed **Event Reference** guide, providing deeper
  insights into workflow design and event-driven patterns.
- ⚙️ Added **Default Tenant Settings** and **User Signup Settings** for precise control over initial tenant setup and
  user role assignments.

### Changed

- 🔄 **Refactored Authentication Stack**: The `IdentityProvider` abstraction has been removed, simplifying `AuthHandler`
  implementations and consolidating identity resolution logic directly within the authentication handlers.
- 🛡️ **Enhanced Two-Stage Access Control**: The `AccessChecker` now implements a critical two-stage authorization
  process where a tenant's access rules act as a strict upper bound for all user permissions within that tenant.
- ⚡️ **Tenant-Aware API Endpoints and Services**: All relevant API routes (e.g., roles, threads, users) and core
  services (e.g., `ThreadService`, `UserService`, `UsageLimits`) have been updated to enforce multi-tenant awareness,
  ensuring data isolation and correct permission handling.
- 👤 **Decoupled User Roles from UserEntity**: `UserEntity` no longer directly stores user roles; instead, roles are
  dynamically fetched from `UserTenantRoleEntity` based on the user's active tenant context.
- 🤖 **Integrated Bot Authentication**: The AI-Hub Bot's authentication process now fully utilizes the new local user and
  tenant role management, ensuring secure and tenant-scoped bot interactions.
- 📚 **Updated Platform Documentation**: Extensive revisions across architectural documentation (`arc42`) and user guides
  to reflect the new multi-tenancy model, local role management, and updated authentication flows.
- 🎨 **Minor UI Layout Adjustment**: Adjusted spacing in the default layout of the web user interface for a more refined
  visual experience.

### Fixed

- 🐛 Resolved an issue where `UserEntity.profile_image` could store invalid data URLs; it now strictly enforces valid
  `http://` or `https://` URLs for improved data integrity.

### Removed

- 🗑️ Deprecated the **`IdentityProvider` Abstraction**: The `IdentityProvider` interface and all its implementations
  (e.g., `AzureIdentityProvider`, `TokenIdentityProvider`) have been removed to streamline the authentication
  architecture.
- 🗑️ Eliminated **`AUTH_IDENTITY_PROVIDER` and `SUPERUSER_ENABLED`** environment variables, as their functionality has
  been integrated into the new, more flexible authentication and tenant management system.
- 🗑️ Removed the **`generate_api_token.py`** utility script and its corresponding `Makefile` target, as API token
  generation is now managed through the refined API and aligned with the new authentication model.
- 🗑️ Deleted outdated **RBAC SDK documentation** (`aihub_doc/docs/3_sdk/5_advanced_topics/5_rbac`), which has been
  superseded by new, comprehensive multi-tenancy and access control guides.

### Refactor

- 🧹 **Upgraded Document Parsing Engine**: Replaced `Docling` with `MinerU` across the platform and its documentation,
  providing enhanced capabilities for document processing.
- 🧹 **Simplified Development Authentication**: Streamlined `DangerousDevelopmentOnlyAuthHandler` by removing its
  dependency on `IdentityProvider`, reflecting the consolidated authentication architecture.
- 🧹 **Consolidated User Onboarding Logic**: Centralized user creation and default tenant role assignment into
  `UserEntity.ensure_user_exists_for_auth` for a more consistent and robust user provisioning process.
- 🧹 **Standardized Test Fixtures**: Introduced new test fixtures (`mock_tenant_entity_autouse`,
  `mock_user_entity_autouse`) to standardize mocking multi-tenant authentication components in tests.

______________________________________________________________________

## [v0.265.3] - 2026-02-24 - Enhanced Service Health Monitoring for Docker Compose

### Added

- ✨ **Implemented standardized HTTP health check labels** for various core services, including **SeaweedFS Volume**,
  **Ferretdb**, **NATS Server**, **Presidio Analyzer**, **Presidio Anonymizer**, and **Langfuse Server**. These labels
  provide explicit metadata (protocol, port, path) for external monitoring and orchestration tools to determine service
  readiness and liveness.
- 🚀 **Configured native Docker health checks** for the **Jupyter Notebook** service, introducing robust internal
  validation of its operational status with defined intervals, timeouts, and retries.
- 🔄 **Explicitly set Docker's internal health check to `NONE`** for **Ferretdb** and **Langfuse Server** services. This
  clarifies the monitoring strategy, indicating that external systems should rely on the newly added health check labels
  for status checks rather than Docker's default internal mechanism.

______________________________________________________________________

## [v0.265.2] - 2026-02-24 - Comprehensive Architecture Documentation and AI-Powered Management

### Added

- ✨ **Arc42 Skill**: Introduced a new Claude skill designed to write, edit, and review architecture documentation
  chapters following the official `arc42` framework. This enhances the ability to generate structured, high-quality
  architectural documentation.
- 📖 **Complete Arc42 Documentation Set**: Added all 12 chapters of the `arc42` architecture documentation (Introduction,
  Constraints, Context, Solution Strategy, Building Blocks, Runtime, Deployment, Crosscutting Concepts, Architecture
  Decisions, Quality Requirements, Risks, and Glossary). This provides a foundational and detailed understanding of the
  platform's design, operational aspects, quality goals, risks, and deployment views.

### Refactor

- 📚 **Centralized Glossary**: Consolidated all project-specific terminology from individual component `README.md` files
  into a single, comprehensive `arc42` glossary (Chapter 12). This significantly improves documentation consistency and
  ease of reference across all stakeholders.

### Removed

- 🗑️ **Redundant Component Glossaries**: Eliminated duplicate glossary sections from component-specific `README.md`
  files (e.g., `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_pipeline`, `aihub_process`, `aihub_web`),
  streamlining documentation and reducing information fragmentation.

______________________________________________________________________

## [v0.265.1] - 2026-02-23 - Revolutionizing AI-Assisted Development with Comprehensive Claude Code Integration

### Added

- 🦾 **Extended Claude Code Integration**: Introduced a comprehensive suite of new capabilities for AI-assisted
  development, including 7 specialized **Custom Subagents** (e.g., `architect`, `codebase-expert`, `test-analyzer`), 8
  **Automated Hooks** for enforcing code quality, security, and environment setup, and 39 detailed **Skills** to
  streamline workflows from scaffolding to debugging across all project scopes.
- 🔗 **New MCP Server Integrations**: Integrated 11 additional **Model Context Protocol (MCP) servers**, providing
  enhanced, real-time access to documentation and runtime insights for key technologies such as **Langfuse**, **Context7
  (general library docs)**, **Playwright**, **PostgreSQL**, **PrimeVue**, **Nuxt**, **Milvus**, and **NATS**.
- 🛠️ **Developer Tooling**: Added new **pre-commit hooks** for automated Python (Ruff), YAML, and Markdown formatting,
  along with checks for common issues, ensuring code consistency before commits.
- 📄 **Critical Documentation**: Introduced new, in-depth documentation pages for **Agent Execution Model** and **Events
  Reference**, providing foundational knowledge for building robust AI agents.
- ✍️ **Claude Code Context Files**: Created dedicated `CLAUDE.md` context files for `aihub_action`, `aihub_api`,
  `aihub_bot`, `aihub_doc`, `aihub_lib`, `aihub_process`, `aihub_web`, and `deployment` scopes, offering AI assistants
  precise, scope-specific guidance.
- ✨ **Developer Convenience**: Added new `Makefile` targets in `aihub_web` for streamlined frontend development tasks
  like formatting, linting, and SDK generation.

### Changed

- ⚙️ **Claude Code Configuration Overhaul**: Rewrote the core `.claude/settings.json` to enable granular tool
  permissions, define available AI models, integrate automated hooks, and activate advanced Claude Code plugins,
  significantly enhancing AI assistant capabilities and security.
- 🚀 **Main `CLAUDE.md` and `README.md`**: Updated the primary project documentation to reflect the extensive new Claude
  Code features, revised architectural overview, and updated tooling ecosystem.
- 📝 **Agent Documentation Enhancements**: Expanded existing documentation for agent fundamentals, Human-in-the-Loop
  (HITL), and memory integration to cover new patterns like **Bot-in-the-Loop (BITL)**, dynamic HITL type selection, and
  config-driven memory management.
- 🔄 **Backend Linting Action**: Switched the `lint_backend` GitHub Action from using `black` to `ruff format` for Python
  code formatting, aligning CI with local development tooling.
- 🏗️ **Process Endpoint Configuration**: Modified the `ProcessEndpointsDiscoveryService` to now expect explicit `name`
  and `description` fields for process configurations, removing previous conditional defaults.

### Fixed

- 🐛 **Dagster UI Port Correction**: Updated the documented Dagster UI access port from `3000` to `3002` in
  `aihub_pipeline/README.md` for accuracy.

### Removed

- 🗑️ **Legacy Claude Code Commands**: Replaced the outdated `.claude/commands/` directory with the new, more powerful
  and structured **Claude Code Skills** system.
- 🧹 **Old Gemini CLI Integration**: Removed the `AGENTS.md` context file and `.gemini/settings.json`, standardizing AI
  assistant context management exclusively through the `.claude/` directory.
- 🌐 **Obsolete Frontend Testing Files**: Removed old placeholder frontend testing assets (`index.html`, `logo.png`,
  `script.js`) from the `aihub_api` playground.

### Refactor

- 🧹 **YAML File Consistency**: Standardized YAML file formatting across the repository by adding the `---` document
  start indicator to numerous configuration and i18n files.
- 🔧 **Docker Compose Restart Syntax**: Updated `restart: no` to `restart: "no"` in Docker Compose templates and
  generated files for improved YAML parser compatibility and consistency.
- 📄 **Makefile Formatting Tasks**: Streamlined code formatting workflows by integrating `format-md` and a new
  `format-yaml` target into the main `pr-ready` Makefile command.
- 🩹 **MCP Script Robustness**: Improved the `.claude/mcp/mcp-aihub-api.sh` and `mcp-mongodb.sh` scripts with more
  robust, conditional sourcing of environment variables.
- 📝 **Gitignore Updates**: Expanded `.gitignore` to include new Claude Code local override files, ensuring a cleaner and
  more focused repository.

______________________________________________________________________

## [v0.265.0] - 2026-02-23 - Major Infrastructure Upgrade: Embracing uv for Superior Python Dependency Management

### Added

- ✨ **Introduced uv Workspaces:** The project has fully migrated to `uv` workspaces, simplifying Python package
  management across the monorepo with a single virtual environment and lockfile.
- 📄 **New Architectural Decision Record:** Added a detailed Architectural Decision Record
  (`2026_02_18_migrate_from_poetry_to_uv.md`) outlining the strategic decision and benefits of migrating from Poetry to
  uv.
- ⚙️ **Standardized Python Version:** A new `.python-version` file is now included to explicitly declare Python `3.13`
  as the required version for the project, ensuring consistent environments.

### Changed

- 🔄 **Updated Core Development Stack:** All Python package management has transitioned from Poetry to `uv`, drastically
  improving dependency resolution and installation speed for developers.
- 🛠️ **Refined CI/CD Workflows:** GitHub Actions for tagging, testing, and linting have been updated to leverage `uv`
  and its caching mechanisms for faster, more reliable, and consistent execution.
- 🐳 **Optimized Docker Builds:** Dockerfiles for all microservices (agents, API, bots, pipelines) now utilize `uv` for
  lean, multi-stage builds, eliminating Poetry from runtime images and simplifying application entrypoints.
- 📝 **Comprehensive Documentation Updates:** All developer guides, `AGENTS.md` files, and quick start instructions
  across the monorepo have been extensively updated to reflect the new `uv`-based setup and workflows.
- 💡 **Improved Makefile Targets:** The root `Makefile` now includes `uv` commands for `setup`, `test`, `format-md`,
  `changelog`, `license-check`, `generate-compose`, `generate-api-token`, and `version-bump`, streamlining the developer
  experience.
- 🏷️ **Renamed License Report:** The project's license report is now generated as `LICENSE_REPORT.md` instead of
  `LICENSES.md` for clearer identification and consistency.
- 🎨 **IDE Configuration Alignment:** Updated PyCharm/IntelliJ IDEA project and run configurations to seamlessly
  recognize and utilize the `uv` virtual environment and workspace structure.
- 💻 **Enhanced Frontend Linting Script:** The `lint` script in `aihub_web/aihub_web/package.json` has been made more
  robust, ensuring `nuxi prepare` only runs when necessary.

### Fixed

- 🐛 **Robust Process Configuration Fetching:** Improved process configuration fetching logic in
  `ProcessEndpointsDiscoveryService` to ensure `name` and `description` fields correctly fall back to default values if
  not explicitly provided in the configuration.
- 🔒 **Explicit Azure Identity Provider in Tests:** Added an explicit environment variable (`AUTH_IDENTITY_PROVIDER`) in
  `OpenWebuiAuthHandler` tests to ensure the Azure Identity Provider is correctly mocked, preventing potential test
  flakiness.

### Refactor

- 🧹 **Consolidated Python Dependency Scanning:** The license generation script (`generate-license.sh`) has been
  refactored to scan all Python dependencies from a single shared `uv` workspace environment, improving efficiency and
  accuracy.
- ♻️ **Streamlined Internal Build Scripts:** Removed the custom `switch_dependencies.py` script, which previously
  managed local versus remote dependency paths, as `uv` workspaces natively handle this functionality.
- 🧹 **Unified Python Enum Usage:** Replaced `enum.Enum` with `enum.StrEnum` in `RcloneSourceConfig` for improved type
  safety and clarity, aligning with modern Python best practices.
- ⚙️ **Simplified Docker Entrypoints:** The entrypoints for `aihub_api` and `aihub_bot` Docker images now directly
  execute `gunicorn`, removing an intermediate `make run-prod` call for better efficiency.

### Removed

- 🗑️ **Deprecated PR Agent Configuration:** The `.pr_agent.toml` configuration file has been removed, streamlining
  project configuration.
- 🗑️ **Eliminated Redundant Module Entries:** Removed explicit module entries for sub-packages from the
  `.idea/modules.xml` file, as the IDE now infers them directly from the workspace.
- 🗑️ **Removed Local/Remote Core Switching Tooling:** Deleted the `switch_dependencies.py` script along with related
  Makefile targets (`use-local-core`, `use-remote-core`) and IDE run configurations, as `uv` provides native workspace
  dependency resolution.
- 🗑️ **Removed `aihub_lib` Module Dependency in Pipeline IDE Config:** The explicit module dependency for `aihub_lib`
  has been removed from `aihub_pipeline/.idea/aihub_pipeline.iml`, aligning with the new workspace structure.

______________________________________________________________________

## [v0.264.0] - 2026-02-19 - Templates for Agents & Processes: Quick Start and Enhanced Configuration Management

### Added

- ✨ **Agent and Process Profile Templates**: Introduced a new system to define and manage pre-configured templates for
  agent and process profiles, replacing the previous "default profile" mechanism and offering administrators multiple
  starting points for instance creation.
- 🦾 **New Pre-built Agent Templates**: Added a suite of practical templates for `FewShotAgent` (e.g., Structured Data
  Extractor, Support Ticket Classifier, Professional Tone Rewriter) and `LLMWrappingAgent` (e.g., Code Explainer, Email
  Drafter, Meeting Minutes Assistant) to accelerate common use cases.
- 🖼️ **Intuitive UI for Templates and Cloning**: Enhanced the web UI with a dedicated section to browse and select agent
  templates, and enabled cloning functionality for existing agent instances to pre-fill creation forms.
- ➕ **Flexible Form Input Elements**: Expanded the capabilities of `InputText` and `LocaleInput` form elements to
  support both `LocaleString` and plain `str` for `placeholder`, `prefix`, and `suffix` fields, offering more dynamic UI
  customization.
- 🗺️ **Agent Navigation in UI**: Introduced new navigation in the web UI to easily switch between "My Agents" and the
  new "Templates" view.

### Refactor

- 🧹 **Streamlined Agent and Process Configuration Models**: Removed the `agent_class` and `process_class` fields from
  the `AgentConfig` and `ProcessConfig` Pydantic models, respectively, as these are now derived from the runtime context
  rather than being user-configurable. This improves data model clarity and type safety.
- ⚙️ **Centralized Instance Configuration Management**: Consolidated configuration normalization, validation, and
  metadata extraction logic into a new `InstanceConfigHelper` utility within the API, reducing code duplication and
  ensuring consistent handling across agent and process instances.
- 🔄 **Generic UI Composable for Instance Creation**: Developed a reusable `useCreateInstanceForm` composable for the web
  UI, standardizing the logic for creating both agent and process instances, including handling of class selection,
  dynamic form rendering, and initial data application from templates or cloned instances.
- 💾 **Stricter Icon Requirements**: Agent and Process classes now explicitly require an icon to be defined, ensuring
  consistent visual representation across the platform.
- 💬 **Improved Agent Memory Initialization**: `AgentMemory` now explicitly receives the `agent_class` during
  initialization, providing a clearer and more direct way to establish agent-specific memory contexts.

### Removed

- 🗑️ **Deprecated "Default Process Configuration"**: The legacy `default_process_config` field and its associated
  auto-creation mechanism have been removed from the `ProcessClassDiscoveryResponseEvent` and related backend logic, in
  favor of the new, more flexible template system.

______________________________________________________________________

## [v0.263.1] - 2026-02-19 - Smarter AI Hub Streaming: Better Errors & Usage Warnings

### Added

- ✨ **Usage Warning Display:** Implemented functionality to detect and display usage warnings (e.g., nearing API limits)
  received from the AI Hub service via response headers directly in the chat interface.

### Changed

- 🌐 **Localized Error Support:** The `Accept-Language` header from the user's request is now forwarded to the AI Hub
  service, enabling localized error messages and responses from the backend where supported.
- 🚀 **Enhanced Streaming Error Handling:** Improved the robustness of streaming requests by allowing for early detection
  and more detailed handling of HTTP errors before processing the stream, providing clearer feedback to the user.
- 💡 **Smarter API Error Message Parsing:** The system now intelligently parses JSON error bodies from the AI Hub service
  to extract and display more specific and user-friendly error messages, improving diagnostic clarity.

### Refactor

- 🧹 **Code Readability Enhancements:** Applied minor formatting and whitespace adjustments across pipeline
  configurations to improve overall code readability and maintainability.

______________________________________________________________________

## [v0.263.0] - 2026-02-18 - Adopting MinerU for Superior Document Processing and Platform Architecture

### Added

- 🚀 **MinerU Integration**: Replaced Docling with MinerU as the primary document parsing engine. This provides improved
  performance and quality for PDF and image processing, with advanced OCR, table, and formula extraction capabilities.
- 📄 **MarkItDown Loader**: Introduced a dedicated loader for Office documents (DOCX, PPTX, XLSX, Outlook messages),
  ensuring comprehensive support for a wider range of file types alongside MinerU.
- ✨ **Flexible Image Handling**: Implemented new utilities for managing images within parsed documents. This supports
  both S3-based storage with signed URLs and base64 embedding in markdown, offering greater flexibility for client-side
  rendering.
- 🏗️ **Docker Network Isolation Documentation**: Added detailed documentation on the platform's Docker network
  segmentation, enhancing security and clarifying internal service communication for better architectural understanding.
- ⚙️ **Configurable Agent Forms**: Introduced a "Form Duality Pattern" for agent configurations, allowing administrators
  to create and customize agent profiles via the Admin UI without requiring code changes.
- 🔗 **S3 Filesystem Utility**: Added a new `create_s3_filesystem` helper for consistent and easy S3 access across
  various services, simplifying file operations.
- ⚡️ **New API Parsing Endpoint**: Introduced `/api/v1/parsing` as a generic, implementation-agnostic endpoint for
  document conversion, adhering to the OpenWebUI external loader specification.

### Changed

- 🔄 **Document Parsing Core Logic**: All internal `DoclingLoader` usage across the platform's document processing
  pipelines has been replaced with `MineruLoader` and `MarkItDownLoader`.
- 📝 **API Endpoint and Translation Naming**: The API controller group has been renamed from `docling` to `parsing` in
  translations to reflect the generalized document processing capabilities.
- 💡 **Pipeline Ingestion Strategy**: Updated the data ingestion pipeline to use a more flexible
  `default_rclone_to_datalake_definitions` factory, expanding support for various cloud storage providers via Rclone.
- ⚙️ **Environment Variables**: Migrated all `DOCLING_*` environment variables to `MINERU_*` for configuring the new
  document parsing services.
- 🌐 **LLM Proxy Configuration**: Updated LiteLLM configurations to route Visual Language Model (VLM) requests for OCR to
  the new MinerU VLM, leveraging either local GPU inference or partner-hosted cloud endpoints.
- 📚 **Documentation Updates**: Numerous documentation pages (e.g., solution overview, quick start, architecture) have
  been updated to reflect the transition from Docling to MinerU.
- 🛠️ **API Request Body Limit**: Implemented a `use_limited_body` dependency in the API to enforce a maximum file size
  for document uploads, preventing excessively large requests.
- ⚡️ **PR Ready Build Target**: Enhanced the `pr-ready` Makefile target to include `generate-compose` and
  `license-check` steps, ensuring configuration and compliance checks automatically.

### Refactor

- 🧹 **`aihub_lib` Dependency Management**: Refactored `aihub_lib` dependencies across `aihub_agent`, `aihub_api`,
  `aihub_bot`, `aihub_pipeline`, and `aihub_process` to use local path references, streamlining the local development
  workflow.
- 🗄️ **IDE Run Configurations**: Streamlined API development and production run configurations in `.idea` to use
  Makefile targets, simplifying IDE setup for developers.
- 🔄 **Image Path Sanitation**: Improved the `create_figures_folder_name` utility with more robust URI and filename
  validation and sanitization.

### Removed

- 🗑️ **Docling Components**: Completely removed the `DoclingController`, `DoclingService`, `DoclingLoader`,
  `DoclingSettings`, and all related DTOs and test files from the codebase.
- ❌ **Docling Docker Services**: Eliminated the `docling` and `vllm-docling` Docker services, along with their
  associated image tags and initialization containers.
- ⛔ **Old API Endpoint**: Deprecated and removed the `/api/v1/docling` API endpoint.

______________________________________________________________________

## [v0.262.4] - 2026-02-17 - Introducing Role-Based Usage Limits and Enhanced API Feedback

### Added

- ✨ **Introduced Role-Based Usage Limits**: A new powerful system enables administrators to define granular,
  pattern-based usage limits for agents within specific roles. These limits are enforced in real-time by the API using
  Redis for atomic counting.
- ⚡️ **Usage Limit Enforcement in API Endpoints**: Integrated real-time usage limit checks into both OpenAI-compatible
  chat completion endpoints and direct agent event endpoints, returning a `HTTP 429 Too Many Requests` status when
  limits are exceeded.
- 🛠️ **New Usage Limit Configuration UI**: Added a dedicated editor within the role management interface, allowing easy
  configuration and management of pattern-based usage limits for each role.
- 🌐 **Localized Usage Limit Messages**: Implemented comprehensive internationalization for usage limit warnings and
  exceeded messages, providing clear feedback to users in multiple languages (DE, EN, FR, IT).
- 📄 **Structured Error Responses for Rate Limits**: The API now provides detailed, structured error responses for
  exceeded usage limits, including localized messages and information about when the limit resets.
- ⚠️ **Usage Warning Headers for Streaming APIs**: Streaming API responses now include `X-Usage-Warning` headers and
  messages when a user's usage approaches a defined limit, enabling client applications to provide proactive
  notifications.
- ✍️ **Access Rule and Usage Pattern Help Texts**: Added informative help texts and examples directly within the Role
  editor UI to guide users in defining effective access rules and usage limit patterns.

### Changed

- 🔄 **Improved API Error Display in Web UI**: Enhanced the web application's global error handler to parse structured
  API error responses (such as usage limit exceeded messages) and display more user-friendly details instead of raw
  error messages.
- ⬆️ **Expanded Access Rule Pattern Characters**: Access rule patterns now support uppercase letters, offering greater
  flexibility in naming conventions for resources.
- ⚙️ **Updated OpenWebUI Pipeline for Usage Warnings**: The OpenWebUI integration pipeline now processes
  `X-Usage-Warning` headers from the API to display in-chat notifications when a user is nearing their agent usage
  limit.
- 📡 **Refined OpenWebUI API Error Handling**: The OpenWebUI integration pipeline's streaming service now proactively
  captures HTTP error responses before stream processing begins, parsing structured error bodies for more informative
  user messages.
- 📜 **Simplified HTTP 429 Error Message**: The generic `Too Many Requests` error message in the web UI has been made
  more concise.

### Refactor

- 🧹 **Modularized Role Editor Components**: The access rules editing functionality has been extracted into a dedicated
  `AccessRulesEditor` component, and a new `UsageLimitsEditor` component was created, significantly improving the
  maintainability and clarity of the role editor.
- 🎨 **Enhanced Role Creation UI**: The entry point for creating new roles in the web interface has been redesigned for a
  cleaner, more intuitive user experience.

______________________________________________________________________

## [v0.262.3] - 2026-02-17 - Enhanced Developer Tooling and IDE Configurations

### Added

- 🚀 **Introduced Service Run Configurations:** Added new PyCharm configurations to facilitate direct execution of core
  services, such as the **API**, from within the IDE for improved development workflow.
- 🛠️ **Expanded Makefile Target Configurations:** Integrated new PyCharm run configurations for critical development
  tasks, including **Generate Compose**, **License Check**, **Use Local Core**, and **Use Remote Core**, making common
  operations more accessible.

### Changed

- 🔄 **Renamed Test Configurations:** Clarified existing PyCharm test configurations by appending "Tests" to their names
  (e.g., **API Tests**, **Agent Tests**, **Bot Tests**, **Lib Tests**, **Process Tests**), enhancing consistency and
  discoverability for developers.

______________________________________________________________________

## [v0.262.2] - 2026-02-17 - Introducing the LLM-Powered Whitepaper Generation System

### Added

- ✨ **LLM-Powered Whitepaper Generation System**: A comprehensive, iterative system has been introduced to automatically
  transform technical documentation into business-focused whitepapers, ensuring consistency, professional output, and
  maintainability.
- 📄 **Automated Chapter Content and Structure**: Each whitepaper chapter is now generated via an LLM, organized in
  self-contained folders with dedicated prompts, source mappings, and generated outputs (`chapters/*/`).
- 🔍 **LLM-Based Source Discovery**: Implemented `generate-sources.py` to intelligently identify and map relevant
  technical documentation files for each chapter, dynamically keeping content synchronized with evolving technical
  documents.
- 🚀 **Python-Based Iterative Generation**: The `generate-whitepaper.py` script facilitates sequential chapter
  generation, leveraging Jinja2 templates and previous chapters as context to maintain narrative flow and style
  consistency.
- 💰 **Integrated Cost Tracking and Observability**: LLM calls within the generation process now include token usage and
  estimated cost summaries for better financial transparency and operational oversight.
- 📚 **Centralized Glossary and General Writing Guidelines**: New configuration files (`glossary.md`,
  `general_prompt.md`) are used to enforce consistent terminology and writing style across all generated whitepaper
  chapters.
- 📈 **Professional PDF Output with LaTeX**: The system now supports direct Markdown to LaTeX to PDF conversion using
  `pandoc` and a custom LaTeX template, ensuring high-quality, professional-looking whitepapers.
- 🧹 **Automated Markdown Formatting**: Generated `.md` files are automatically formatted using `mdformat` to ensure
  consistent readability and adherence to project styling.
- 📝 **Architectural Decision Record**: An `arc42` decision record
  (`2025_12_05_llm_based_whitepaper_generation_system.md`) outlines the context, drivers, decision, and consequences of
  adopting this new LLM-based whitepaper generation system.

______________________________________________________________________

## [v0.262.1] - 2026-02-17 - Expanded External Service Configuration

### Added

- ✨ **Milvus Vector Database Configuration**: Introduced new environment variables (`MILVUS_URL`, `MILVUS_DIMENSION`,
  `MILVUS_ROOT_PASSWORD`) across deployment files, enabling flexible configuration and integration with the Milvus
  vector database.
- 🔑 **Docling API Key Support**: Added the `DOCLING_API_KEY` environment variable to allow for secure authentication and
  access control for the Docling document processing service.

______________________________________________________________________

## [v0.262.0] - 2026-02-12 - Comprehensive Observability Upgrade: Migrating to Langfuse for LLM Tracing and Evaluation

### Added

- ✨ **Langfuse Observability Platform**: Integrated Langfuse as the new open-source LLM observability and evaluation
  platform, replacing Arize Phoenix. This provides enhanced tracing, cost tracking, dataset management, and UI-driven
  experiment workflows.
- 📦 **Langfuse Docker Services**: Introduced `clickhouse`, `langfuse-worker`, and `langfuse-web` services to the Docker
  Compose stack for robust self-hosted Langfuse deployment.
- ⚙️ **Automated Langfuse Provisioning**: Added a `LangfuseProvisioner` to automatically configure Langfuse on API
  startup, including registering AI-Hub agent models, LLM connections (e.g., LiteLLM), and default prompt templates.
- 🔑 **Comprehensive Langfuse Configuration**: New environment variables for Langfuse API keys, database settings, SSO
  (Azure AD) integration, and access control for production deployments.
- 📊 **Evaluation Dataset Management API**: Introduced new API endpoints under `/datasets` for creating, retrieving, and
  updating evaluation datasets in Langfuse, supporting structured testing of AI agents.
- 📈 **Langfuse Trace Attributes**: Enhanced agent tracing (`AgentRunTracer`) to enrich OpenTelemetry spans with
  Langfuse-specific trace-level attributes (name, session, user, input/output, usage details) for richer visualization
  and analytics.
- 🛡️ **Increased OpenTelemetry Span Limits**: Expanded the maximum number of attributes per span to 512 to prevent
  truncation of detailed telemetry data, especially for complex RAG traces.

### Changed

- 🔄 **Core Observability Switch**: Replaced all references to Arize Phoenix with Langfuse across the entire platform,
  including documentation, code comments, and configuration files, for a consistent observability experience.
- 🔬 **Streamlined LLM Evaluation Workflow**: Shifted from a custom, programmatic experiment evaluation framework to
  leveraging Langfuse's native UI for managing and running experiments against datasets, simplifying evaluation
  processes and reducing custom code.
- 📡 **Agent Instance Sync to Langfuse**: The `AgentEndpointsDiscoveryService` now automatically syncs online agent
  instances to Langfuse, ensuring they are visible and selectable for experiment evaluation within the Langfuse UI.
- 📄 **Updated Documentation**: All relevant documentation has been updated to reflect the transition to Langfuse,
  detailing its features and usage for tracing and evaluation.

### Refactor

- 🧹 **Simplified AgentRunTracer Logic**: Refactored the `AgentRunTracer` to directly leverage Langfuse's OpenTelemetry
  ingestion capabilities, removing Phoenix-specific logic for root spans and complex context storage.

### Removed

- 🗑️ **Arize Phoenix Components**: Eliminated all Docker services, configuration, API endpoints, and associated Python
  code (including `PhoenixExperimentEvaluator` and `JudgeOutput`) related to Arize Phoenix due to licensing
  incompatibility and technical advantages of Langfuse.
- 🚫 **Experiment Management Frontend**: Removed the custom frontend components for managing and running evaluation
  experiments, as these functionalities are now handled directly within the Langfuse UI.

______________________________________________________________________

## [v0.261.7] - 2026-02-11 - Enhanced Docling Configuration with API Key Support

### Added

- 🔑 **Docling API Key Support:** Introduced a new configuration option (`DOCLING_API_KEY`) to allow specifying an API
  key for the Docling service, improving secure access and authentication.

______________________________________________________________________

## [v0.261.6] - 2026-02-11 - Enhanced Deployment Flexibility and Routing Accuracy

### Added

- 🚀 **Introduced dynamic frontend configuration:** Environment variables (`AIHUB_API_VERSION`, `AIHUB_FRONTEND_ORIGIN`)
  are now passed to AI-Hub frontend services in Docker Compose setups, enabling more flexible and dynamic deployment
  settings.

### Changed

- ⚙️ **Optimized Nuxt.js prerendering:** Specific authentication routes (e.g., `/en/auth`) are now explicitly ignored
  during Nuxt.js prerendering, which enhances build efficiency and better accommodates dynamic authentication pages.

### Fixed

- 🐛 **Resolved authentication path matching issues:** The authentication middleware now correctly identifies public
  paths, regardless of trailing slashes, ensuring consistent access to non-authenticated routes.
- 🐞 **Corrected Nginx absolute redirect behavior:** Disabled absolute redirects in Nginx to prevent issues with
  incorrect schemes or ports when the application is deployed behind a reverse proxy.
- ⚡️ **Improved Nginx SPA routing:** Refined the Nginx configuration for single-page applications to ensure all non-file
  requests are reliably served by `index.html`.

______________________________________________________________________

## [v0.261.5] - 2026-02-10 - Streamlined Development and Dependency Management

### Refactor

- 🔄 **Monorepo Dependency Alignment:** Updated the `aihub_lib` dependency across `aihub_agent`, `aihub_api`,
  `aihub_bot`, `aihub_pipeline`, and `aihub_process` to use local path references with `develop = true`. This change
  streamlines local development workflows and better supports a monorepo project structure.

### Removed

- 🗑️ **`flatdict` Dependency:** The `flatdict` library has been removed from the `aihub_agent` package's dependencies
  and its documentation, simplifying the project's dependency footprint.

______________________________________________________________________

## [v0.261.4] - 2026-02-10 - Internal Dependency Streamlining

### Refactor

- 🧹 **Streamlined event attribute flattening:** Replaced the external `flatdict` library with a custom, in-house
  implementation. This change reduces external dependencies and improves control over how event attributes are processed
  and presented for display.

______________________________________________________________________

## [v0.261.3] - 2026-02-09 - Dependency Script Logging Enhancements

### Changed

- 📄 **Enhanced `poetry` Command Output:** The `switch_dependencies.py` script now prints the standard output (stdout)
  from `poetry lock` and `poetry install` commands, offering more transparency into dependency management processes.
- 🚨 **Clarified Dependency Installation Errors:** Error messages generated by `switch_dependencies.py` for failed
  `poetry lock` and `poetry install` operations have been improved to explicitly display the standard error (stderr)
  only when relevant, preventing empty or unhelpful error outputs.

______________________________________________________________________

## [v0.261.2] - 2026-02-09 - Streamlined CI/CD Builds with Dynamic Image Discovery

### Refactor

- 🔄 **Dynamic Agent Image Discovery:** Improved the `build-agents.yml` workflow to automatically determine which agent
  images to build by parsing `compose-config.yml`, enhancing build system flexibility and reducing manual configuration.
- 🔄 **Dynamic Pipeline Image Discovery:** Enhanced the `build-pipelines.yml` workflow to dynamically identify pipeline
  images for building directly from `compose-config.yml`, streamlining the CI/CD process and ensuring consistency.

______________________________________________________________________

## [v0.261.1] - 2026-02-09 - Comprehensive Changelog History Update

### Added

- 📄 **Comprehensive Changelog History**: Updated `CHANGELOG.md` to include detailed release notes for recent versions,
  specifically adding entries for `v0.261.0`, `v0.260.2`, `v0.254.6`, `v0.254.5`, `v0.243.3`, and `v0.243.2`, ensuring a
  complete and up-to-date historical record of changes.

______________________________________________________________________

## [v0.261.0] - 2026-02-06 - Dynamic Configuration and Enhanced Management for Agents & Processes

### Added

- ⚙️ **Dynamic Agent Configuration via Admin UI**: Introduced the **Form Duality Pattern** enabling developers to define
  agent configurations directly in code that are automatically rendered as editable forms in the Admin UI. This empowers
  administrators to customize agent behavior without code changes.
- ✨ **New Agent Profile Management API**: Implemented a comprehensive set of API endpoints for managing agent instances
  (profiles) including creation, retrieval, updates, and deletion. This replaces previous discovery-only mechanisms with
  robust CRUD operations.
- ✨ **New Process Instance Management API**: Similarly, introduced a complete API for managing process instances,
  offering full control over process deployment and configuration through the Admin UI.
- ⚙️ **NATS RPC for Dynamic Configuration Retrieval**: Added a new NATS RPC mechanism (`AgentConfigClient`,
  `ProcessConfigClient`, `AgentConfigResponder`, `ProcessConfigResponder`) enabling agents and processes to fetch their
  runtime configurations dynamically from the API, decoupling configuration from event payloads.
- ✨ **New FormKit UI Elements**: Developed custom FormKit components (`AgentSelector`, `IconSelector`,
  `KnowledgeDatabaseSelector`, `LocaleInput`, `ModelSelect`, `Repeater`, `VectorStoreInput`) to support rich, dynamic
  and multi-language configuration forms in the UI.
- 📝 **Comprehensive Configuration Documentation**: Added detailed documentation
  (`arc42/decisions/2026_01_07_enable_dynamic_agent_configuration_ui.md`,
  `docs/2_platform/5_agents/3_blueprints_and_profiles`, `docs/3_sdk/2_building_agents/8_configurable_agents`) explaining
  the new configuration paradigm, agent blueprints vs. profiles, and how to build configurable agents.
- ⚙️ **New Agent Implementations**: Moved and refactored `FewShotAgent`, `RetrievalAgent`, and `NamespaceSelectionAgent`
  from playground to production-ready `app` directories, making them configurable via the new UI.
- ⚙️ **LLM-Based Translation Service**: Introduced a new API route and service for performing LLM-based translations of
  `LocaleString` objects across all supported languages (de, en, fr, it).
- ✨ **Agent and Process Class Metadata**: Added class-level `name`, `description`, and `icon` properties to `Agent` and
  `AgenticProcess` base classes, enabling consistent display of agent/process types in the UI.
- ⚙️ **New Makefile Targets**: Added `run-dev`, `format-md`, and `pr-ready` targets for local development, markdown
  formatting, and pull request preparation.
- ✅ **Expanded Test Coverage**: Introduced new unit tests for `AgentConfig`, `Form` classes, and NATS RPC mechanisms,
  ensuring the robustness of new features.
- ⚙️ **Enhanced OpenWebUI Integration**: Added a new OpenWebUI function (`memory_action`) to allow viewing agent
  memories directly from the AI-Hub frontend.

### Changed

- 🔄 **API Restructuring for Agents and Processes**: Overhauled the `/agents` and `/processes` API endpoints to reflect
  the "class vs. instance" (blueprint vs. profile) distinction, providing more granular control and a clearer hierarchy
  for management.
- 🔄 **Centralized Configuration Fetching**: Refactored `AgentService` and `ProcessService` to adopt a **database-first
  approach** for configuration. Agent/Process dispatchers now fetch runtime configurations dynamically via NATS RPC from
  the API service, rather than relying on event payloads or local defaults.
- 🔄 **Updated `AgentRunner` and `ProcessRunner`**: Modified runners to use the new form-mode configuration instances and
  expose class-level metadata for discovery.
- 🔄 **Refined `StartEvent` Structure**: Removed the `agent_config` field from `StartEvent` and `UserMessageEvent`,
  streamlining event payloads as configuration is now fetched dynamically by the receiving agent/process.
- 🔄 **Dependency Updates**: Updated numerous dependencies in `aihub_web` to their latest versions, including
  `@pinia/colada`, `@vueuse`, `gridstack`, `oidc-client-ts`, and `socket.io-client`, improving performance and
  stability.
- 🔄 **Improved UI/UX Icons**: Updated various icons across the web frontend (e.g., chat, file, search, agent status) for
  a more consistent and modern look and feel.
- 🔄 **Console Logging Level Adjustment**: Changed the default logging level for several external libraries in
  `aihub_lib` to `ERROR` to reduce noise in console output.
- 🔄 **Unified Workflow Visualization**: Updated `WorkflowVisualizer` to use localized strings for start/end nodes,
  improving multi-language support.
- 🔄 **Configurable Milvus Vector Store**: Refactored `MilvusVectorStoreConfig` to expose `index_namespaces` for explicit
  configuration and now fetches connection details from `MilvusSettings` at runtime.
- 🔄 **Refined OpenWebUI Integration**: Updated existing OpenWebUI integration to align with the new API endpoint
  structure for agents and dynamic display of agent names.

### Fixed

- 🐛 **UI Console Log Duplication**: Fixed an issue where console logs were excessively verbose by adjusting default
  logging levels for common libraries.
- 🐛 **Process Page Title Display**: Corrected a typo in the process details page title.
- 🐛 **Agent `StartEvent` Test Data**: Updated test event data to correctly include agent ID, aligning with new event
  structures.

### Removed

- 🗑️ **Deprecated `WebuiAgent`**: Removed the `WebuiAgent` and all associated files, streamlining the agent portfolio.
- 🗑️ **Obsolete `open_webui` SDK**: Removed the internal OpenWebUI Python SDK as it is no longer actively maintained.
- 🗑️ **Legacy Agent and Process Discovery Caches**: Eliminated in-memory caches (e.g., `DISCOVER_AGENTS_CACHE`,
  `GET_AGENT_INSTANCE_CACHE`) as discovery and configuration now leverage a database-first approach and NATS RPC.
- 🗑️ **Redundant Agent and Process Entities**: Removed `AgentEntity` and `ProcessEntity` database models, replacing them
  with `AgentClassEntity` and `ProcessClassEntity` for class-level data, and `AgentConfigEntityDocument` for
  instance-specific configurations.
- 🗑️ **Outdated Playground Run Scripts**: Removed various `run.py` and `trigger.py` scripts from the `playground`
  directories, as agents have been migrated to the `app` directory and integrated with the new configuration system.
- 🗑️ **Unused Agent/Process Instance Discovery Events**: Removed `AgentInstanceDiscoveryRequestEvent`,
  `AgentInstanceDiscoveryResponseEvent`, `ProcessInstanceDiscoveryRequestEvent`, and
  `ProcessInstanceDiscoveryResponseEvent`, shifting to class-level discovery.

### Refactor

- 🧹 **Unified Configuration Logic (`Form` Class)**: Consolidated form generation, data validation, and configuration
  handling into a single `Form` base class in `aihub_lib`, enabling a consistent "duality pattern" for defining
  UI-editable configurations across agents and processes.
- 🧹 **Centralized Type Hinting**: Applied `Self` type hints across numerous methods in `aihub_lib`, `aihub_api`, and
  `aihub_bot` for improved type inference and code consistency.
- 🧹 **Cleaned Up Internal Comments**: Removed extraneous comments from various core files to improve code readability
  and maintainability.
- 🧹 **Streamlined `.idea/runConfigurations`**: Reorganized and renamed numerous IntelliJ IDEA run configurations for
  better clarity and ease of use.
- 🧹 **Modularized API Controllers**: Refactored API controllers by extracting `ApiLocaleString` for localized names and
  descriptions, enhancing modularity and i18n support.
- 🧹 **Normalized Form Data**: Introduced new utility functions (`normalize_empty_objects_to_none`,
  `normalize_empty_locale_strings`, `transform_formkit_arrays`) to standardize form data sent from the frontend to
  backend Pydantic models.

______________________________________________________________________

## [v0.260.2] - 2026-02-03 - Universal Data Ingestion with Rclone and Smarter Memory Retrieval

### Added

- 🚀 **Introduced Rclone Integration for Universal Data Ingestion:** A new, unified pipeline now supports syncing
  documents from over 70 cloud storage providers (including SharePoint, OneDrive, Google Drive, AWS S3, Azure Blob,
  SFTP, and local filesystems) to your S3 data lake. This replaces previous provider-specific implementations, offering
  a single, flexible solution.
- ⚙️ **New `Rclone` Docker Service:** A dedicated `rclone` service has been added to the Docker Compose setup, providing
  the Rclone Remote Control (RC) API for seamless integration with ingestion pipelines.
- 📄 **Comprehensive Source Templates:** Pre-configured templates and detailed setup guides have been added for common
  Rclone sources, simplifying configuration for Azure Blob, Google Drive, Local Filesystem, OneDrive, S3, SFTP, and
  SharePoint.
- ✨ **Enhanced Memory Retrieval Display:** New event handlers (`RetrieveUserMemoryEventHandler`,
  `RetrieveOrganizationMemoryEventHandler`) improve the display of retrieved user and organization memories, providing
  more detailed source information in the UI.
- 🔑 **Rclone RC API Environment Variables:** Added `RCLONE_URL`, `RCLONE_RC_USER`, and `RCLONE_RC_PASS` environment
  variables for configuring the Rclone RC API connection, including secure authentication for production.

### Changed

- 🔄 **Migrated Data Ingestion Documentation:** The data ingestion pipeline documentation has been comprehensively
  updated to reflect the new Rclone-based universal approach, deprecating the previous SharePoint-specific guide.
- 🛠️ **Updated Data Lake Definitions Utility:** The `default_sharepoint_to_datalake_definitions` factory has been
  replaced by `default_rclone_to_datalake_definitions`, streamlining the creation of data ingestion pipelines.

### Removed

- 🗑️ **Deprecated SharePoint-specific Data Lake Definition:** The `default_sharepoint_to_datalake_definitions` factory
  has been removed, superseded by the more versatile Rclone integration.

### Security

- 🔒 **Rclone RC API Authentication Enforced:** The Rclone service now requires authentication via `RCLONE_RC_USER` and
  `RCLONE_RC_PASS` in production environments, significantly improving security. Users are explicitly warned to change
  default credentials in production.

### Refactor

- 🧹 **Flexible Environment Settings Configuration:** The `create_settings_config` method in `EnvironmentSettings` now
  supports an `extra` argument, allowing for more flexible loading of dynamic, backend-specific Rclone options from
  environment variables.

______________________________________________________________________

## [v0.260.1] - 2026-02-03 - API Configuration Standardization for Docling Loader

### Refactor

- 🧹 **Standardized API Base URL Configuration:** Renamed the internal configuration variable for the Docling API base
  URL from `BASE_API_URL` to `API_BASE_URL` within the `DoclingLoader` for improved consistency and clarity in the
  codebase.

______________________________________________________________________

## [v0.260.0] - 2026-02-02 - Enhanced Memory Management and Agent Context

### Added

- 🧠 **Introduced Comprehensive User and Organization Memory**: A new, robust memory system has been implemented across
  `RAGAgent` and `ExpertRAGAgent`, allowing agents to retrieve personalized user memories and organization-wide
  knowledge.
- 🦾 **New Agent Workflow Steps for Memory Management**: Added dedicated agent steps for `ExpertRAGAgent` and `RAGAgent`
  to retrieve user memories, retrieve organization memories, inject them into chat history, and store new user memories
  from conversations.
- ⚙️ **Configurable Memory Options for RAG Agents**: `RAGAgentConfig` and `ExpertAskingAgentConfig` now include explicit
  configuration fields to enable/disable organization memory retrieval, user memory retrieval, and user memory storage,
  along with `tenant_id` and `tenant_namespace` for scoping.
- 🗄️ **Memory Management Pages in Web UI**: Dedicated UI pages are now available for managing user memories associated
  with specific agents and threads, providing a centralized view for collected knowledge.
- 📊 **OpenWebUI Integration for Agent Memories**: Introduced new UI components and an OpenWebUI function to display
  agent-specific user memories directly within the chat interface, with toggleable list and graph views.
- 🔍 **Advanced Memory Search Filters in API**: Added `agent_class` and `agent_id` parameters to the User and
  Organization Memory search API endpoints, enabling more precise filtering of stored memories.
- 💬 **Localized Memory Interface**: Extended translation files to support the new memory management sections and views
  across multiple languages.
- ⚡️ **Granular LLM Event Handling**: The `do_respond_with_llm` step function now supports returning an `LLMEvent` for
  intermediate steps, allowing for post-LLM processing (like memory storage) before a final `StopEvent` is emitted.

### Changed

- 🔄 **Expert Conversation Storage Refactored**: `ExpertAskingAgent` now stores expert conversations as general
  "organization memories" instead of the specialized "insights," aligning with the new unified memory system.
- 🧪 **RAG Agent Test Suite Updated**: The RAG Agent test suite has been updated to remove references to the deprecated
  insight system and now tests the new organization memory retrieval.
- 💻 **SDK Schema Generalization**: The `Usage` schema in the SDK has been generalized to represent duration, with
  specific token usage details moved to an image-response-specific schema.
- 🎨 **Enhanced Memory List UI**: Improved the visual presentation of the memory list component in the web UI with
  striped rows, better column styling, and severity-based tagging for relevance scores.

### Removed

- 🗑️ **Deprecated Insight System**: The entire "insight" persistence and retrieval system, including `InsightEntity`,
  `InsightRetriever`, related configurations, API endpoints, and UI logic, has been removed.
- 🧹 **Cleanup of Insight-Related Code**: All code paths, imports, and translation files associated with the old insight
  system have been meticulously removed from the codebase.

### Fixed

- 🐛 **Improved Mem0 Metadata Filtering**: Corrected Mem0 service logic to accurately filter out empty strings in
  addition to `None` values when processing metadata and filters, preventing unintended memory retrieval behavior.

______________________________________________________________________

## [v0.259.3] - 2024-07-29 - Automated Latest Tagging Workflow Enhancement

### Changed

- 🚀 **Automated Docker Image Discovery for 'latest' Tagging:** The GitHub Actions workflow responsible for promoting
  release tags to "latest" now dynamically identifies all custom application Docker images. It parses
  `deployment/compose-config.yml` to automatically detect images marked for local builds, removing the need for manual
  updates to the workflow when new services are added or removed.
- 📄 **Improved Workflow Documentation:** Comprehensive comments have been added to the `set-latest.yml` GitHub Actions
  workflow, clearly detailing its purpose, usage, and the logic used for image selection and promotion.

______________________________________________________________________

## [v0.259.2] - 2026-01-30 - Strengthened Security with Docker Network Isolation

### Security

- 🔑 Implemented a comprehensive **Docker network isolation strategy**, segmenting the platform into `proxy`, `backend`,
  `data`, `storage`, and `egress` networks to significantly enhance security posture. This limits lateral movement and
  reduces the blast radius in case of a breach.
- 🔒 Configured `internal: true` for core `backend`, `data`, and `storage` Docker networks (in non-development
  environments), preventing direct external access to sensitive internal services.
- 🚫 Explicitly disabled Inter-Container Communication (ICC) on the dedicated `egress` network, ensuring that services
  requiring outbound internet access cannot communicate with other containers on that network, further isolating them.

### Refactor

- 🔄 Systematically updated **Docker Compose deployment configurations** across all environments (`dev`, `build`,
  `local`, `latest`, `nightly`) to integrate the new multi-network architecture, assigning each service to its specific,
  isolated network zone.

### Added

- 📄 Introduced detailed **documentation for Docker Network Isolation**, providing a clear overview of the new network
  topology, service assignments, security benefits, and operational guidelines.
- 🩺 Implemented a new **health check for the Open WebUI** service to improve monitoring and ensure its availability.

### Changed

- 🛠️ Migrated the **Playwright service to a custom Dockerfile build process**, providing greater control over its
  runtime environment and dependencies.
- ⬇️ Pinned the **Playwright image version to `v1.49.0-jammy`** to ensure stability and compatibility within the new
  custom build setup.
- 🔗 Updated **service dependencies for `api` and `bot`**, ensuring they now explicitly await the healthy state of Milvus
  and Neo4j, respectively, for more robust startup sequences.
- 🧹 Refined **health check commands for `postgres-ferretdb` and `litellm`** for improved accuracy and reliability.

______________________________________________________________________

## [v0.259.1] - 2026-01-30 - Enhanced OAuth Security and Granular Access Control

### Security

- 🔑 **Improved OAuth Cookie Secret Management:** Replaced the single shared OAuth cookie secret with individual,
  service-specific secrets (`OAUTH_COOKIE_SECRET_DAGSTER`, `OAUTH_COOKIE_SECRET_SEAWEEDFS`, `OAUTH_COOKIE_SECRET_ATTU`).
  This significantly enhances security by isolating session cookies for different platform components (Dagster,
  SeaweedFS, Attu).

### Changed

- 🔄 **Refined OAuth Group Restrictions:** Renamed and segregated OAuth allowed group configurations to be
  service-specific (e.g., `DAGSTER_OAUTH_ALLOWED_GROUPS` is now `OAUTH_ALLOWED_GROUPS_DAGSTER`). This provides more
  granular control over user access for each component.
- 📄 **Updated Environment Variable Configuration:** Adjusted `.env` templates and all Docker Compose configurations to
  reflect the new, service-specific OAuth cookie secrets and allowed group variables, streamlining secure setup.
- 📚 **Revised Documentation for OAuth Setup:** Updated quick start guides and secret generation instructions to provide
  clear guidance on configuring the new, separate OAuth cookie secrets for each service.

### Removed

- 🗑️ **Deprecated Shared OAuth Cookie Secret:** The generic `OAUTH_COOKIE_SECRET` environment variable has been removed
  in favor of service-specific secrets, reducing potential security exposure.

______________________________________________________________________

## [v0.259.0] - 2026-01-28 - Empowering Agents with Long-Term Memory and Knowledge Graphs

### Added

- ✨ **Introduced Agent Memory System:** Agents can now learn from past conversations and organizational facts, providing
  long-term personalization and shared knowledge, powered by `mem0` and `Neo4j`.
- 🧠 **User Memory Capabilities:** Agents can automatically learn and store private user preferences, working styles, and
  individual context from conversations, enabling highly personalized interactions.
- 🏢 **Organization Memory for Shared Knowledge:** Agents can now leverage explicit, shared organizational facts
  (policies, tech stack, processes) accessible to all users within a tenant, fostering consistent and institutional
  knowledge.
- 📈 **New Memory Management API Endpoints:** Introduced comprehensive API endpoints for viewing, searching, updating,
  and deleting both user and organization memories via the platform's API.
- 📊 **Interactive Memory Knowledge Graphs:** The web interface now visualizes memory relationships as interactive
  knowledge graphs, helping users understand how concepts are connected within their memories.
- 📺 **Dedicated Memory Management UI:** New sections in the web interface provide dedicated pages for managing and
  exploring personal user memories and shared organization memories.
- ⚙️ **Integrated Neo4j Graph Database:** Incorporated Neo4j for powerful graph-based memory storage and retrieval,
  enabling rich relational understanding between concepts.
- 🧩 **Microsoft Teams Support for Expert Asking Agent:** The Expert Asking Agent can now escalate questions to human
  experts via Microsoft Teams, expanding its capabilities beyond Slack integration.
- ⏱️ **Run Duration and Cost Metrics in Event List:** The event list now displays the duration and total cost for each
  agent run, enhancing observability and cost transparency.
- 📄 **Comprehensive Agent Memory Documentation:** Added detailed guides on User Memory, Organization Memory, and how to
  build memory-enhanced agents using the SDK.
- ⚖️ **Automated Python Dependency License Scanning:** Python packages now have their licenses automatically scanned and
  reported in `LICENSES.md`, significantly improving license transparency and compliance.

### Changed

- 🛠️ **Refactored AI Utility Modules:** Reorganized general AI utility functions into more logical and specialized
  modules: `chat_history`, `rerank`, and `retrieval`, improving code structure and maintainability.
- 📦 **Updated LiteLLM Proxy Configuration:** Improved model parameter handling in LiteLLM by adding `drop_params` for
  better compatibility and efficiency across various models.
- 📏 **Adjusted Milvus Embedding Dimension:** Updated the default Milvus embedding dimension to 1024 in development
  environments, optimizing vector storage for newer embedding models.
- 📄 **Renumbered Platform Documentation Chapters:** Reorganized the platform documentation structure to logically
  integrate the new memory features and improve navigability.
- 📄 **Renumbered Agent SDK Documentation:** Restructured the Agent SDK documentation to seamlessly integrate new memory
  patterns and improve readability for developers.

### Fixed

- 🐛 **Corrected Redis Host in LiteLLM Configuration:** Ensured LiteLLM correctly references `valkey` (the
  Redis-compatible service) within the Docker network instead of `localhost`, resolving connectivity issues.

### Refactor

- 🧹 **Standardized Enum Usage:** Converted several `enum.Enum` implementations to `enum.StrEnum` across the codebase for
  improved type safety and consistency.

### Removed

- 🗑️ **Deprecated GDPR Documentation:** Removed previous GDPR documentation pages, as the content has been updated and
  integrated into the new compliance and memory management sections.

______________________________________________________________________

## [v0.258.4] - 2026-01-19 - Enhanced Service Health, API Stability, and Richer Chat Interactions

### Added

- ✨ **Comprehensive Service Health Checks:** Introduced new liveness and readiness endpoints for the API, Agents, and
  Processes, providing detailed dependency status for critical infrastructure like NATS, MongoDB, Redis, Milvus, and S3.
- ⚙️ **Centralized Health Check Server:** Implemented a generic HTTP health check server running in a background thread
  for Agents and Processes, ensuring consistent and robust monitoring across all services.
- 🚀 **New Model Management API Endpoints:** Added dedicated API endpoints to retrieve lists of all available models
  grouped by type, and to fetch detailed information for specific models.
- 💬 **Expanded Chat Message Blocks:** Introduced support for new message content types, including **VideoBlock**,
  **ThinkingBlock**, and **ToolCallBlock**, significantly enriching conversational capabilities and allowing for more
  complex multimodal interactions.
- 🗣️ **Chat-style Human-in-the-Loop (HITL):** Added a new `chat` type for Human-in-the-Loop requests, enabling users to
  provide input and respond to prompts directly within the regular chat interface, improving user experience.
- 🧩 **FastAPI Infrastructure Client Dependencies:** Introduced new FastAPI dependencies (`use_milvus`, `use_redis`,
  `use_s3`, `use_s3_public`, `use_s3_service`, `use_vector_store_factory`) to standardize access to shared Milvus,
  Redis, and S3 clients and vector store factories, promoting consistency and reusability.

### Changed

- ⬆️ **Agent and Process Runner Upgrades:** Integrated Agent and Process runners with the newly introduced health check
  server, now providing detailed readiness statuses for their respective dependencies (NATS, Redis, Milvus).
- ✅ **API Readiness Checks:** The API service now utilizes the `ApiHealthController` for comprehensive readiness checks,
  moving beyond a simple liveness probe to verify all critical service dependencies.
- 🔗 **Milvus Client Reusability:** Refactored Milvus vector store creation to reuse a shared `MilvusClient` instance
  across the application, improving connection pooling efficiency and enabling centralized health monitoring.
- 📍 **Bot Service Port Update:** Corrected the exposed port for the Bot service from 8000 to 8001 to align with standard
  deployment configurations.
- 🔒 **Milvus Authentication Variable:** Standardized Milvus client authentication across various services by updating
  the `MILVUS_TOKEN` environment variable to `MILVUS_ROOT_PASSWORD` for consistency and clarity.
- 🛡️ **Enhanced SDK Endpoint Security:** Applied security headers to all endpoints within the generated TypeScript SDK
  client, improving overall API security.

### Refactor

- 🧹 **S3 File Access Service Modernization:** Refactored the `S3AnonymousFileAccessService` to accept injected S3 client
  instances, significantly improving testability and streamlining resource management.
- ♻️ **Knowledge Controller Dependency Injection:** Migrated direct instantiation of `VectorStoreFactory` and
  `S3AnonymousFileAccessService` within the `KnowledgeController` to FastAPI's dependency injection system, enhancing
  modularity and maintainability.

______________________________________________________________________

## [v0.258.3] - 2026-01-19 - Hardened Docker Integration with Socket Proxy

### Security

- 🔑 **Implemented Docker Socket Proxy:** Introduced a new `docker-socket-proxy` service that acts as a secure
  intermediary between Traefik and the Docker daemon. This significantly enhances system security by limiting Traefik's
  access to only the essential Docker API endpoints (container and network discovery) needed for service routing,
  mitigating potential container escape vulnerabilities.

### Added

- ✨ **`docker-socket-proxy` Service:** A dedicated `tecnativa/docker-socket-proxy` service has been added to all Docker
  Compose configurations, providing fine-grained control over Docker API access.
- ⚙️ **Docker Socket Proxy Configuration:** Comprehensive configurations for the new proxy service are included,
  explicitly disabling dangerous Docker API permissions (e.g., build, commit, exec, images) and ensuring read-only
  access to the underlying Docker socket.

### Changed

- 🔄 **Traefik Docker Endpoint:** Traefik's Docker provider endpoint has been updated to connect to the new
  `docker-socket-proxy` over TCP (`tcp://docker-socket-proxy:2375`) instead of directly accessing the Unix Docker
  socket.
- 🧹 **Removed Direct Docker Socket Mount:** The direct volume mount of `/var/run/docker.sock` from the Traefik service
  has been removed across all deployment configurations, delegating Docker socket interaction to the new, more secure
  proxy service.

______________________________________________________________________

## [v0.258.2] - 2026-01-13 - Deepening Knowledge: Insights Now Integral to Document & Node Retrieval

### Added

- ✨ **Enhanced Knowledge Base with Insight Integration:** Introduced the capability to retrieve **Insights** directly as
  standard documents and nodes within the knowledge base, enabling their use in Retrieval-Augmented Generation (RAG)
  flows.
- 📚 **Direct Insight Retrieval by ID:** Added a new method (`InsightEntity.get_by_id`) to directly fetch insights using
  their unique identifier, streamlining access to structured knowledge.
- 🌍 **Localized Insight Representation:** Implemented support for localizing insight content when presented as nodes,
  ensuring that questions, answers, and conversation parts are displayed in the user's preferred language.

### Changed

- 🔄 **Unified Document and Node Retrieval:** Modified the `KnowledgeService` to transparently handle both regular
  documents and **Insights** when fetching documents by ID or retrieving specific nodes, providing a more consistent API
  experience.
- 🛠️ **Refined Insight-to-Document Conversion:** Updated `DocumentDTO` to include a dedicated method for converting an
  `InsightEntity` into a document data transfer object, standardizing how insights are represented.
- 🌐 **Improved Insight Source Handling in UI:** Adjusted the web interface to recognize insights as a distinct document
  source, ensuring the "View Original" action is correctly hidden for insight-based knowledge.
- 🗄️ **Virtual Bucket Assignment for Insights:** Updated the `extractBucket` utility in the UI to correctly assign a
  virtual 'insights' bucket for documents originating from MongoDB-stored insights.

### Refactor

- 🧹 **Encapsulated Insight Node Conversion Logic:** Moved the logic for transforming an `InsightEntity` into an
  `IngestedNode` directly into the `InsightEntity` class, improving modularity and reusability.
- 📄 **Minor Logging Message Formatting:** Adjusted a logging message in the `DoclingLoader` for improved clarity.

______________________________________________________________________

## [v0.258.1] - 2026-01-13 - Knowledge Base Evolution: Advanced Document Management and Visibility

### Added

- ✨ **Introduced Document Search and Sorting**: Users can now easily find documents by title or filename and sort them
  by creation date, update date, or title directly in the Knowledge Base UI.
- 🚀 **Real-time Document Ingestion Tracking**: Documents uploaded to the data lake are now immediately visible in the UI
  with a "pending" status, providing real-time feedback on ingestion progress.
- 📄 **Placeholder Document Support**: The backend now creates `RefDoc` placeholders for newly uploaded files, enabling
  immediate visibility and consistent tracking throughout the ingestion lifecycle.
- 🔗 **Deterministic Document IDs**: Implemented a new utility for generating deterministic IDs for `RefDoc` entries
  based on their source path, improving consistency and data management.
- 🧩 **Dagster Pipeline Assets for Placeholders**: Integrated new Dagster assets and operations to automate the creation
  of placeholder `RefDoc` entries for files entering the data lake via SharePoint and local filesystem pipelines.

### Changed

- 🔄 **Unified Document Retrieval Logic**: The Knowledge Base backend has been revamped to use a single, unified approach
  for fetching documents from the `RefDoc` store, simplifying the architecture and improving consistency.
- ⬆️ **Enhanced Document Upload Validation**: The document upload process now reliably creates a `RefDoc` placeholder
  for pending files and includes improved error handling for event publishing, making uploads more robust.
- 📝 **Clarified DocumentDTO fields**: The `DocumentDTO` fields `source` and `is_ingested` have clearer descriptions,
  better reflecting the document's state and origin.
- 🧹 **Refined Document List UI**: The document list now uses consistent field names (`document_title`, `created_at`,
  `updated_at`) aligning with backend changes and supports the new sorting capabilities.
- ⚡️ **Improved UI Loading States**: The document list now provides a clearer loading indicator, only showing a full
  loading state on initial data fetch for a smoother user experience.
- ⚠️ **Conditional Document Upload Button**: The document upload button is now only visible for knowledge bases that are
  not configured for automatic synchronization, preventing manual uploads to auto-synced sources.
- 🗑️ **Enhanced Data Lake File Deletion**: Deleting files from the data lake now automatically cleans up associated
  `RefDoc` entries from the document store, ensuring data consistency.
- ⚙️ **Human-in-the-Loop Event Structure**: `HumanInTheLoop` request and response events have been refined to include a
  `hitl_type` and support more flexible response data types, making them more adaptable to various human interaction
  patterns.

### Refactor

- 🧹 **Centralized MongoDB Connection Management**: MongoDB connection handling across `aihub_lib` and `aihub_pipeline`
  has been refactored to use `switch_db` context managers and dedicated helper functions, improving multi-database
  support and connection stability.

### Removed

- 🗑️ **Deprecated Document Caching Logic**: Custom caching mechanisms for distinguishing between processed and
  unprocessed documents in the Knowledge Service have been removed, replaced by the new unified `RefDoc` retrieval
  strategy.
- 📚 **Streamlined Models API**: Several deprecated model-related DTOs and API endpoints have been removed or
  consolidated, simplifying the API surface for model management.

______________________________________________________________________

## [v0.258.0] - 2026-01-12 - Fortified Core Services: Enhanced Security, Streamlined Configuration, and Improved Observability

### Security

- 🔑 **Introduced comprehensive token-based authentication** for key infrastructure components including Milvus, NATS,
  Redis/Valkey, Etcd, and SeaweedFS, significantly enhancing the platform's security posture.
- 🔑 **Enabled authentication for Docling API** access, allowing API key-based security for document processing services.
- 🔐 **Added `etcd-init` service** to automatically set up root password authentication for Etcd on startup, ensuring
  secure metadata storage from the outset.
- 🔑 **Centralized management of API keys** for local Large Language Models (LLMs) (llama.cpp and vLLM) under the
  `LOCAL_LLM_TOKEN` environment variable for easier and more secure configuration.

### Added

- 📦 **Enabled Docker secrets support for Pydantic settings**, allowing sensitive configuration data to be managed
  securely as Docker secrets, with environment variables taking precedence for development flexibility.
- ⚡️ **Integrated LiteLLM caching with Redis**, now supporting authentication to improve performance and secure cached
  responses.
- 📊 **Introduced debug exporters for OpenTelemetry** logs and metrics in development environments, providing immediate
  visibility into service telemetry.

### Changed

- 🔄 **Standardized NATS and Redis client initialization** by centralizing their creation within dedicated `NatsSettings`
  and `RedisSettings` classes, simplifying client setup across all services (agents, API, pipelines).
- 📈 **Activated OpenTelemetry by default** in development environments to provide immediate observability into service
  operations.
- 🏷️ **Implemented dynamic service versioning** for OpenTelemetry resources, automatically deriving service versions
  from Docker image tags for more accurate telemetry data.
- ⚙️ **Standardized Docling API configuration variables** (`DOCLING_BASE_API_URL` to `DOCLING_API_BASE_URL` and
  `DOCLING_HOSTED_VLM_API_ENDPOINT` to `DOCLING_HOSTED_VLM_API_BASE_URL`) for consistency.
- 🌐 **Renamed Swiss LLM Cloud API URL** to `SWISS_LLM_CLOUD_API_BASE_URL` for improved clarity and consistency in
  configuration.
- 🚫 **Disabled OpenTelemetry for local Dagster runs** by default in the `Makefile` to prevent potential conflicts and
  streamline local development workflows.
- 🔗 **Updated OpenWebUI connections** to Redis and Milvus to properly utilize the newly introduced authentication
  tokens.
- 👷 **Adjusted CI workflow to always rebuild Docker images** for backend tests instead of relying on cached images,
  ensuring tests run against the freshest code.

### Refactor

- 🧹 **Migrated SeaweedFS Filer configuration** entirely from static TOML files to environment variables, streamlining
  deployment and configuration management.
- ⚙️ **Simplified Agent and Process runners** by removing direct NATS server list and Redis URL parameters, now
  leveraging `NatsSettings` and `RedisSettings` for configuration.

______________________________________________________________________

## [v0.257.2] - 2026-01-11 - Core Pipeline Refinements and Human-in-the-Loop Context

### Changed

- 🦾 **Human-in-the-Loop (HITL) Context**: Enhanced the Human-in-the-Loop response mechanism to explicitly pass agent
  class and ID, providing more precise context for agent interactions.

### Refactor

- 🧹 **Code Readability**: Improved code readability and conciseness across various AI Hub pipeline components by
  optimizing variable assignments and method signatures.

______________________________________________________________________

## [v0.257.1] - 2026-01-09 - Enhanced Knowledge Retriever Namespace Flexibility

### Changed

- 🔄 **Improved `KnowledgeRetrieverConfig` for Namespaces:** Relaxed the constraint on `index_namespaces`, allowing it to
  be an empty list. An empty list now signifies the intention to retrieve information from *all* available namespaces,
  offering greater flexibility.
- 🦾 **Smarter Retriever Filtering:** Updated the `filter_retrievers_by_namespace` utility to correctly interpret an
  empty `index_namespaces` list, ensuring that retrievers are considered for all relevant namespaces when no specific
  namespace is provided.
- ⚡️ **Dynamic Node Retrieval:** The `retrieve_nodes` function now intelligently constructs metadata filters. If
  `index_namespaces` is empty, it will skip namespace-specific filtering, allowing retrieval of nodes across all
  namespaces based solely on node type.

______________________________________________________________________

## [v0.257.0] - 2026-01-08 - Empowering RAG with Dynamic Namespace Selection and Enhanced Retrieval

### Added

- ✨ **Namespace Selection Agent:** Introduced a new agent dedicated to interactively guiding users through the selection
  of relevant knowledge source namespaces for their queries. This agent uses an LLM to understand intent and
  incorporates human-in-the-loop (HITL) steps for clarification and approval, ensuring accurate context for RAG.
- 🦾 **Namespace-Aware User Message Event:** Implemented a new event type (`NamespaceAwareUserMessageEvent`) that extends
  the standard user message to include pre-selected knowledge source namespaces, enabling RAG agents to receive and
  process this crucial contextual information.
- 📄 **Core Namespace Utilities:** Developed foundational data structures (`BucketNamespacePair`) and utility functions
  (`filter_retrievers_by_namespace`) within `aihub_lib` to support dynamic filtering of RAG retrievers based on
  user-selected namespaces.
- ⚙️ **New Configuration Options:** Added `NamespaceSelectionAgentConfig` and `RAGDelegationConfig` to provide flexible
  configuration for the namespace selection workflow, including LLM settings, available buckets, and how it delegates to
  RAG agents.

### Changed

- 🔄 **RAG Agent Namespace Filtering:** Updated both the **RAG Agent** and **Expert RAG Agent** to leverage the new
  `NamespaceAwareUserMessageEvent`. These agents can now dynamically filter their knowledge retrievers based on the
  pre-selected namespaces, significantly improving the precision and relevance of information retrieval.

### Fixed

- 🐛 **OpenAI Service Header Injection:** Corrected an issue in the OpenAI service where additional headers were not
  consistently injected into SDK calls, ensuring proper instrumentation and metadata propagation for requests.

______________________________________________________________________

## [v0.256.14] - 2026-01-08 - Robust Timeout Management and Enhanced Dagster Run Monitoring

### Added

- ✨ **Introduced Comprehensive Document Loading Timeout:** Added an `OPERATION_TIMEOUT` setting for the DoclingLoader,
  allowing control over the overall duration of document loading operations to prevent indefinite hangs.
- 🚀 **Granular HTTP Timeouts for Docling API:** Implemented explicit connect, read, write, and pool timeouts for HTTPX
  clients used in Docling API interactions, providing more fine-grained control over network requests.
- 🦾 **Explicit Filesystem Timeouts:** Configured explicit connection and read timeouts for Azure Data Lake and S3
  filesystem resources, improving reliability for storage operations.
- ⚡️ **Enabled Dagster Run Monitoring:** Activated Dagster's run monitoring across all environments, with configurable
  settings for maximum runtime, start timeout, cancel timeout, and poll intervals to automatically manage and prevent
  stuck runs.

### Changed

- 🔄 **Clarified Docling API Timeout Scope:** The `API_TIMEOUT` setting for Docling API calls is now explicitly defined
  as the timeout for *individual* API calls, distinguishing it from the new overall operation timeout.

### Fixed

- 🐛 **Improved Docling Async Poll Error Handling:** Refined the error handling for asynchronous polling in the
  DoclingLoader to catch more specific HTTP, OS, and asyncio cancellation errors, leading to more robust operation.

### Refactor

- 🧹 **Streamlined DoclingLoader Asynchronous Logic:** Refactored the asynchronous document loading method in
  `DoclingLoader` by extracting core logic into an internal helper method, improving readability and maintainability.

______________________________________________________________________

## [v0.256.13] - 2026-01-08 - Enhanced Observability for Document Parsing

### Changed

- 📄 **Improved Document Parsing Logging:** Added comprehensive logging within the `parse_document_from_data_lake`
  operation to provide greater visibility and easier debugging for document loading, parsing, and metadata application
  steps.

______________________________________________________________________

## [v0.256.12] - 2026-01-07 - Improved Database Connectivity for Docker Environments

### Added

- 🔗 **Configured `MONGO_CONNECTION_STRING`:** Explicitly defined the MongoDB connection string across Docker Compose
  configurations, leveraging `ferretdb` and existing environment variables (`MONGO_USERNAME`, `MONGO_PASSWORD`) for a
  more robust and clearer database setup.

______________________________________________________________________

## [v0.256.11] - 2026-01-06 - Enhanced Document Processing and Interactive AI

### Added

- ✨ **Introduced Chat-style Human-in-the-Loop (HITL) interactions:** Agents can now prompt users with questions directly
  within the chat interface, appearing as regular messages rather than pop-up dialogs, for more seamless conversational
  workflows.
- 🧹 **Automatic Docling Result Cleanup:** Implemented client-side and server-side mechanisms to automatically clear old
  Docling conversion results after retrieval, improving storage management and preventing orphaned data.
- ⚙️ **Configurable Docling Result Removal Delay:** Added a new `CLEAR_RESULTS_DELAY` setting to control how long
  Docling results are retained before automatic cleanup.

### Changed

- 🛡️ **Improved Docling Conversion Resiliency:** Enhanced error handling for Docling document conversion to more
  robustly manage network issues, connection resets, timeouts, and server restarts, reducing transient failures.
- 📊 **Enhanced Docling Conversion Logging:** Significantly expanded debug and error logging within the Docling loader to
  provide greater visibility into the document conversion process, aiding in troubleshooting.
- 🚀 **Updated Docling Service Configurations:** Modified Docker Compose templates to enable `SINGLE_USE_RESULTS` and set
  a `RESULT_REMOVAL_DELAY` for the Docling service, complementing client-side cleanup efforts.

______________________________________________________________________

## [v0.256.10] - 2026-01-05 - Improved PDF Handling and Development Workflow

### Added

- 🦾 **Enhanced PDF Document Processing:** Introduced a new pre-processing step to automatically fix malformed PDF files,
  specifically those with missing or invalid page dimensions, using A4 as a standard fallback. This significantly
  improves the robustness of document conversion through the Docling service.
- 🧪 **Comprehensive PDF Pre-processing Tests:** Added a dedicated test suite for the new PDF pre-processing
  functionality, ensuring its reliability and correctness across various PDF formats.
- ⚡️ **Asynchronous Test Utility:** Implemented a new `run_with_event_loop` helper function to streamline the execution
  of synchronous methods within an asyncio event loop, particularly for Milvus-related testing, enhancing test
  reliability and developer experience.

### Changed

- 💬 **Improved Docling Task Error Reporting:** Updated error messages for failed or skipped Docling conversion tasks to
  provide the full API response, offering more detailed context for debugging and troubleshooting.

### Refactor

- 🔄 **Streamlined Dependency Management:** Standardized `aihub_lib` dependency across all projects to use local path
  references (`path = "../aihub_lib", develop = true`), simplifying local development and monorepo integration.
- 🧹 **Centralized Asynchronous Test Setup:** Refactored Milvus-related test fixtures and helper functions to leverage
  the new `run_with_event_loop` utility, centralizing and improving the management of asynchronous operations in tests.

______________________________________________________________________

## [v0.256.9] - 2026-01-05 - Introducing Chat-Style Human-in-the-Loop for Seamless Agent Collaboration

### Added

- ✨ **New Chat-Style Human-in-the-Loop (HITL) Interaction**: Agents can now ask questions that appear as regular chat
  messages, allowing users to respond by typing a normal chat message, enabling more fluid conversational workflows.
- 🦾 **`HitlDemoAgent`**: A new demo agent has been introduced to showcase all three Human-in-the-Loop types: input,
  confirmation, and the newly introduced chat-style interaction, providing clear examples for developers.
- 🚀 **API Endpoint for Open Chat HITL**: A new `/threads/{thread_id}/open-chat-hitl` API endpoint has been added,
  allowing client applications to efficiently query for active chat-style HITL requests within a thread.
- 📄 **Dedicated Chat HITL Event Types**: New event classes (`HumanInTheLoopChatRequestEvent`,
  `HumanInTheLoopChatResponseEvent`) and a helper class (`HumanInTheLoopChat`) have been implemented to specifically
  support and simplify the integration of chat-style Human-in-the-Loop interactions.
- 🌐 **Internationalization Support for Chat HITL**: Translations have been added for the new chat-style HITL request and
  response events across supported languages (DE, EN, FR, IT), ensuring a global user experience.
- ⚙️ **IntelliJ Run Configuration for `HitlDemoAgent`**: A new IntelliJ IDEA run configuration has been included to
  simplify the setup and execution of the `HitlDemoAgent` for local development and testing.

### Changed

- 🔄 **OpenWebUI Pipeline Intelligent HITL Handling**: The OpenWebUI pipeline now intelligently detects active chat-style
  HITL requests at the start of a user message and routes the user's input as a chat HITL response, streamlining
  conversational turns.
- ⚡️ **Enhanced Base HITL Events**: The core `HumanInTheLoopRequestEvent` and `HumanInTheLoopResponseEvent` have been
  updated to incorporate the new `chat` interaction type and now utilize type generics for improved type safety and
  clarity.
- 🔐 **Improved Thread API Access Control**: Thread-related API endpoints in the `ThreadController` now leverage
  extracted helper methods for more robust, consistent access checking and error handling across operations.
- 🔌 **Application and Playground Router Integration**: The new API endpoint for retrieving open chat HITL requests has
  been seamlessly integrated into the main application and playground router configurations.

### Refactor

- 🧹 **Reorganized Human-in-the-Loop Modules**: The `HumanInTheLoopInput` and `HumanInTheLoopConfirmation` helper
  classes, along with their respective request/response event classes, have been refactored and moved into dedicated,
  separate modules for better organization and maintainability.
- 🏗️ **Streamlined HITL Event Imports**: Imports for Human-in-the-Loop event types have been simplified and made
  consistent across the agent codebase and playground examples, reducing verbosity and improving code readability.

______________________________________________________________________

## [v0.256.8] - 2025-12-30 - Enhanced Document Upload Security and Validation

### Fixed

- 🔒 **Strengthened Filename Validation:** Implemented more robust and secure filename validation to prevent the upload
  of malformed or potentially malicious filenames, including those containing path traversal sequences or invalid
  control characters. This significantly enhances the security and integrity of uploaded documents.
- 🐛 **Improved File Extension Handling:** Revised the logic for parsing and validating file extensions, ensuring that
  all uploaded filenames consistently include a valid, single extension and preventing issues arising from improperly
  formatted document types.

______________________________________________________________________

## [v0.256.7] - 2025-12-23 - Enhanced Agent Context Evaluation and Retrieval

### Added

- ✨ **Improved Context Management Visibility:** The agent now provides clearer insights into its decision-making
  process, indicating when it has gathered sufficient information to answer a question or when it needs to perform
  additional retrieval steps to find more relevant data.

______________________________________________________________________

## [v0.256.6] - 2025-12-19 - Optimized Streaming for Real-time Interactions

### Changed

- 🚀 **Improved Streaming Robustness:** Enhanced server-sent event (SSE) and streaming responses across chat completions
  and agent event endpoints by adding critical HTTP headers. This prevents caching and buffering issues from
  intermediary proxies, ensuring more reliable, real-time data delivery and a smoother user experience.

______________________________________________________________________

## [v0.256.5] - 2025-12-19 - Enhanced Docling Reliability with Automatic Retries

### Added

- ✨ **Docling API Retry Mechanism:** Introduced an automatic retry mechanism for Docling API calls, significantly
  improving resilience against transient network errors and temporary service unresponsiveness during document
  processing.
- ⚙️ **`DOCLING_HTTP_RETRIES` Configuration:** Added a new configuration setting `DOCLING_HTTP_RETRIES` (defaulting to
  3\) to control the number of retries attempted for Docling API requests, providing more control over system behavior.

### Changed

- 🚀 **Improved Docling Request Resilience:** Docling document conversion processes (both synchronous and asynchronous)
  now incorporate retry logic with exponential backoff, automatically handling HTTP connection issues, timeouts, and
  specific transient API errors.
- 🛡️ **Refined Docling Error Handling:** Enhanced the classification of Docling API errors to differentiate between
  transient failures (which trigger retries) and permanent issues, leading to more robust document processing.

### Refactor

- 🧹 **Streamlined Docling API Execution:** The underlying HTTP request execution logic for Docling API interactions has
  been refactored into dedicated internal methods, improving code clarity and maintainability.

______________________________________________________________________

## [v0.256.4] - 2025-12-19 - Enhanced Document Processing: Configurable Figure Descriptions and Robustness

### Added

- ✨ **Configurable Figure Description Generation:** Introduced a new option to enable or disable the generation of
  figure descriptions using a vision LLM, providing more control over document processing, with the feature enabled by
  default.

### Fixed

- 🐛 **Improved Figure Description Robustness:** Added a safeguard to prevent errors when generating figure descriptions
  for documents that lack text content, ensuring smoother processing and logging a warning instead.

### Changed

- ⚙️ **Updated Quick Start Pipeline:** The `my_document_pipeline` example now explicitly enables both table refinement
  and figure description generation, showcasing recommended best practices and demonstrating the new feature.

______________________________________________________________________

## [v0.256.3] - 2025-12-17 - Enhanced Knowledge Management with Shared RAG Pipelines and Dynamic Buckets

### Added

- ✨ **Shared RAG Pipeline:** Introduced a new `shared_rag_pipeline` to process and manage shared knowledge, complete
  with its own Docker image, Dagster configuration, and deployment setup.
- 📦 **Dynamic Knowledge Bucket Configuration:** Added new environment variables (`AIHUB_CREATE_DEFAULT_BUCKETS`,
  `AIHUB_DEFAULT_BUCKET_NAME`, `AIHUB_SHARED_BUCKET_NAME`, `AIHUB_DEFAULT_NAMESPACE_NAME`,
  `AIHUB_SHARED_NAMESPACE_NAME`) to allow flexible naming and conditional creation of knowledge buckets and namespaces.
- 🌱 **Automated Knowledge Bucket Initialization:** Implemented API startup logic to automatically create default
  knowledge buckets and namespaces in MongoDB, ensuring consistent setup.
- 📄 **New Docker Compose Conventions:** Added a section to `AGENTS.md` outlining best practices for Docker Compose
  templates and environment variable usage.

### Changed

- ⚙️ **RAG Agent Knowledge Retrieval:** Updated `RAGAgent` and `ExpertRAGAgent` to simultaneously retrieve information
  from both default and shared knowledge buckets and namespaces, enhancing retrieval capabilities.
- 🔄 **Dynamic Pipeline Datalake Naming:** Configured existing RAG pipelines (`default_rag_pipeline`, playground
  pipeline) to use dynamically defined datalake container names from `AIHubSettings`, improving configurability.
- 💬 **Refined Condenser Prompt Instructions:** Improved the prompt instructions for the standalone question condenser
  across all supported languages, focusing on better context resolution and preventing the addition of new information.
  This leads to more accurate and self-contained queries.
- 🚀 **Conditional S3 Bucket Creation:** Modified the S3 initialization script (`init-buckets.sh`) to conditionally
  create default and shared knowledge buckets based on `AIHUB_CREATE_DEFAULT_BUCKETS` settings.
- 💡 **Unified RAG Pipelines Development Setup:** Replaced the specific "Default RAG Pipeline Dev" run configuration with
  a consolidated "RAG Pipelines Dev" setup to streamline development for all RAG pipelines.

______________________________________________________________________

## [v0.256.2] - 2025-12-17 - Platform-wide Observability Boost

### Added

- 📈 **Enhanced System Observability:** Integrated `AihubInstrumentor` across all core agent applications
  (`ExpertAskingAgent`, `ExpertRAGAgent`, `LLMWrappingAgent`, `RAGAgent`) and the main API. This crucial update enables
  comprehensive OpenTelemetry instrumentation, significantly improving distributed tracing and telemetry for better
  system monitoring and debugging capabilities.

______________________________________________________________________

## [v0.256.1] - 2025-12-16 - Empowering RAG with Human Expertise: Introducing Expert RAG and Asking Agents

### Added

- 🦾 **Introduced Expert RAG Agent**: A new agent specifically designed for Retrieval-Augmented Generation with
  integrated human expert escalation capabilities. This agent facilitates consulting human experts when the knowledge
  base is insufficient.
- 💬 **New Expert Asking Agent**: A dedicated agent to manage the end-to-end process of engaging human experts via
  communication platforms like Microsoft Teams or Slack, capturing their responses, and integrating them into the
  knowledge base.
- ⚙️ **Expert Escalation Configuration**: Added new environment variables (`EXPERT_ASKING_CHANNEL_TYPE`,
  `TEAMS_CHANNEL_ID`, `TEAMS_TENANT_ID`, `TEAMS_BOT_ID`, `SLACK_CHANNEL_ID`, `SLACK_SERVICE_URL`) to configure the
  Expert Asking Agent for communication with human experts.
- 🚀 **Deployment Support for Expert Agents**: Integrated `expert_rag_agent` and `expert_asking_agent` into the CI/CD
  pipeline and Docker Compose configurations, enabling seamless building and deployment of these new agents.
- 📄 **Expert Escalation Documentation**: Updated quick start and agent-specific documentation to guide users through
  configuring and utilizing the new Expert RAG and Expert Asking Agents.
- 🛠️ **Agent Test Runner Enhancement**: Added `ensure_dependent_agent_stream` method to the `AgentTestRunner` to better
  support testing of agent-in-the-loop delegation scenarios.
- 🔄 **Expert Conversation Formatting Utility**: Introduced a new utility function (`format_expert_conversation`) to
  consistently format expert chat messages for use as context within agents.

### Changed

- 🔄 **RAG Agent Redefined**: The original RAG Agent has been streamlined to focus solely on standard RAG functionality,
  removing its previous expert escalation logic and configuration. Expert escalation is now exclusively handled by the
  new Expert RAG Agent.
- 📝 **Docstring Guidelines Update**: Revised `AGENTS.md` to update docstring best practices, advising against `Args:` or
  `Returns:` sections for conciseness.
- 🧪 **Playground Test Restructuring**: Moved expert escalation-related playground examples and tests from the generic
  RAG Agent to the new, dedicated Expert RAG Agent's test suite for clearer separation of concerns.

### Refactor

- 🧹 **Centralized RAG Logic**: Extracted common RAG preconditioning and step functions into new shared modules
  (`aihub_agent/aihub_agent/rag/preconditions.py` and `aihub_agent/aihub_agent/rag/step_functions.py`) to promote code
  reuse and improve modularity across RAG-based agents.
- 🗂️ **Retriever Module Organization**: Refactored the `aihub_lib/aihub_lib/generative_ai/retrievers` module by moving
  `RetrieverConfig` and `create_retriever` into their own dedicated files for better clarity and maintainability.
- ⚡️ **Simplified Retrieval Event Display**: Streamlined the `retrieve_from_all_sources` utility by removing the direct
  `displayer` argument, centralizing thought message handling at the agent step level.

______________________________________________________________________

## [v0.256.0] - 2025-12-16 - Enhanced Dynamic Partition Naming for Clarity

### Refactor

- 🔄 **Improved Dynamic Partition Naming:** Dynamic partition definitions for various data sources (documents,
  SharePoint, and local filesystem) now automatically incorporate the `datalake_container_name` as a prefix. This
  ensures unique and contextually relevant partition names, enhancing system clarity and preventing potential naming
  collisions in complex environments.

______________________________________________________________________

## [v0.255.6] - 2025-12-12 - Smarter Data Lake Cleanup and Milvus Compatibility

### Added

- 🦾 **Introduced flexible document parser loader type:** The document parser can now be configured with different loader
  types (e.g., `DOCLING`) directly via pipeline definitions, enhancing parsing capabilities.
- 🗑️ **Automated figures folder cleanup:** When data lake files are deleted, their associated `__figures__` folders are
  now automatically removed, improving data hygiene and ensuring complete data removal.
- 📄 **Centralized Data Lake path building:** A new `build_path` utility method in `DataLakeResource` provides a
  consistent way to construct relative paths within the data lake, including any configured directory prefixes.

### Changed

- ⚡️ **Enhanced Milvus vector store deletion:** The `PartitionAwareMilvusVectorStore` delete operation now includes a
  backward compatibility check, ensuring correct fallback to the base class's delete method when manual partitions are
  not in use, improving reliability.
- 🔄 **Robust S3 directory operations:** The S3 Data Lake client now gracefully handles full S3 URIs (e.g.,
  `s3://bucket/`) for directory existence, listing, and deletion checks, and ensures complete removal of S3 directory
  marker objects.

### Fixed

- 🐛 **Corrected data lake file removal logic:** The process for identifying data lake files to remove now accurately
  considers the configured `directory_name` prefix, ensuring that URIs are consistently built to prevent incorrect
  deletion decisions.

### Refactor

- 🧹 **Streamlined figure folder naming:** The `create_figures_folder_name` utility has been refactored for cleaner and
  more direct URI parsing, reducing reliance on `os.path` functions.

______________________________________________________________________

## [v0.255.5] - 2025-12-12 - RAG Agent Rejection Message Customization

### Added

- ✨ **Configurable context insufficient prompt:** Introduced a new `context_insufficient_prompt` configuration option
  for the **RAGAgent**, allowing customization of the leading message when the agent cannot answer due to insufficient
  context.

### Changed

- 🔄 **Dynamic RAG Agent rejection messages:** The **RAGAgent** now dynamically constructs rejection messages based on
  the new `context_insufficient_prompt` configuration, providing more flexible and user-friendly responses for few-shot,
  context insufficient, or expert rejections.
- 📄 **Flexible internationalized guard rejection prompts:** Updated the `guard.reject` translations to support a dynamic
  `{prompt}` placeholder, enabling greater customization of rejection messages across all supported languages.

______________________________________________________________________

## [v0.255.4] - 2025-12-11 - Smarter Standalone Questions: Multimodal Support and Centralized Prompts

### Added

- 🧪 **Comprehensive Tests for Question Condensation**: Introduced new test cases for the `condense_standalone_question`
  utility, ensuring robust functionality for text-only and multimodal inputs, and proper handling of chat history.

### Changed

- 🖼️ **Enabled Multimodal Question Condensation**: The `condense_standalone_question` utility now supports multimodal
  input (e.g., text and images) by accepting a `ChatMessage` object directly, allowing agents to understand and rephrase
  questions that refer to visual content.
- ⚙️ **Standardized Standalone Question Prompt**: The prompt for generating standalone questions is now centralized and
  embedded within `aihub_lib`, removing the configurable `condense_question_prompt` option from `FewShotAgentConfig` and
  `RAGAgentConfig` to ensure consistent and optimized behavior across all agents.
- 🚀 **Upgraded LLM Interaction for Condensation**: The internal mechanism for condensing questions transitioned from
  simple `llm.predict` to `llm.chat`, utilizing system messages to provide more structured instructions to the LLM for
  improved accuracy and multimodal processing.
- 💬 **Enhanced User Message Handling**: Agents now leverage the `last_user_message` property to retrieve the complete
  user input, including any multimodal content, ensuring all relevant information is considered during question
  condensation.
- 📄 **Improved Standalone Question Prompt Logic**: Updated the default prompt translations (`lib/prompt.*.yml`) for
  standalone question condensation with explicit instructions, including directives for image analysis and replacing
  pronouns with precise textual descriptions of visible objects.

### Removed

- 🗑️ **Deprecated Configurable Condense Prompt**: The `condense_question_prompt` configuration field has been removed
  from `FewShotAgentConfig` and `RAGAgentConfig`, streamlining agent configuration by relying on the new centralized
  prompt definition.

______________________________________________________________________

## [v0.255.3] - 2025-12-11 - Enhanced Milvus Performance and Smarter Data Management

### Added

- ✨ **Introduced Partition-Aware Deletion for Milvus**: Implemented a new deletion mechanism in
  `PartitionAwareMilvusVectorStore` that enables more granular and efficient removal of vector nodes associated with a
  reference document within specific Milvus partitions.
- 🦾 **Enabled Upsert Mode for Milvus Vector Stores**: Configured the Milvus vector store factory to use
  `upsert_mode=True`, which automatically overwrites existing nodes when new data with matching IDs is added,
  streamlining data synchronization and preventing duplicates.

### Changed

- 🚀 **Optimized Milvus Configuration for Performance and Resource Management**: Significantly adjusted Milvus parameters
  across all configurations (including `rocksmq`, `queryNode`, and `quotaAndLimits`) to improve memory usage, enhance
  data eviction policies, and optimize query processing, leading to better stability and efficiency.
- 🧹 **Streamlined Milvus Node Addition Workflow**: Updated the `VectorStoreIOManager` to leverage Milvus's
  `upsert_mode`, removing the explicit pre-deletion of nodes before adding new ones. This simplifies the data ingestion
  pipeline and prevents potential memory leaks.
- 🎯 **Enhanced Reference Document Deletion Op**: The `delete_nodes_for_ref_doc` operation now utilizes partition-aware
  deletion, ensuring that nodes related to a reference document are targeted precisely within their respective Milvus
  partitions.
- ⚙️ **Upgraded Core Infrastructure Components**: Updated **Milvus** to `v2.6.7` and **Etcd** to `v3.5.25`,
  incorporating performance improvements, bug fixes, and new features from these latest versions.

______________________________________________________________________

## [v0.255.2] - 2025-12-11 - Unlocking Knowledge: Expert Insights and Advanced RAG for Smarter Agents

### Added

- ✨ **Expert Insight Persistence**: Expert responses and conversations from the `ExpertAskingAgent` are now stored as
  valuable 'insights' in MongoDB, enabling agents to learn from and leverage past expert interactions.
- 🚀 **Modular Multi-Source Retrieval System**: Introduced a new, flexible system allowing RAG agents to retrieve
  information from diverse sources, including traditional knowledge bases and newly persisted expert insights, in
  parallel.
- 💬 **Specialized Human-in-the-Loop (HITL) Events**: Enhanced human interaction capabilities with new event types
  (`HumanInTheLoopInput` and `HumanInTheLoopConfirmation`), providing more explicit and structured dialogues for
  free-form text input or yes/no confirmations.
- 🌐 **Bot-in-the-Loop Path Entity**: A new MongoDB path entity has been added to streamline bot-in-the-loop responses,
  improving the integration and handling of bot channel interactions.
- 🧪 **Comprehensive Agent Test Suites**: New test coverage has been added for the `ExpertAskingAgent` and expanded for
  the `RAGAgent`, specifically addressing expert escalation workflows and the new insight retrieval functionality.
- 🖥️ **Robust MongoDB Connection Management**: Implemented enhanced connection management for MongoDB within both agent
  and process runners, ensuring reliable data persistence and retrieval.

### Changed

- ⚙️ **RAG Agent Configuration**: The `RAGAgent`'s retrieval configuration has been modernized to utilize the new
  multi-source retrieval system, replacing the singular `retrieve_step_config` with a flexible list of `retrievers`.
- 🆔 **Detailed Expert Identification**: `ExpertAnswerSufficientEvent` and `ExpertAnswerInsufficientEvent` now include
  the `expert_user_id`, allowing for more granular tracking and identification of expert contributions.
- 🤝 **Mandatory Bot-in-the-Loop Responder Information**: The `responder` and `user_name` fields in
  `BotInTheLoopResponseEvent` are now required, ensuring complete traceability of human responses from bot channels.
- 🔄 **OpenWebUI Human-in-the-Loop Handler**: The OpenWebUI integration has been updated to fully support the new
  specialized `HumanInTheLoopConfirmation` dialogs, providing a richer and more intuitive user experience for agent
  confirmations.

### Refactor

- 🧹 **Centralized Retrieval Logic**: Core retrieval utilities and configurations, including `RetrieveSummariesConfig`
  and helper functions for node retrieval, have been moved to a shared library (`aihub_lib`), promoting better code
  organization and reusability across agents.
- ⚡️ **Streamlined Human-in-the-Loop Event Structure**: The internal architecture of Human-in-the-Loop events has been
  refined, abstracting common `Request` and `Response` patterns into base classes and introducing dedicated subclasses
  for specific interaction types.

______________________________________________________________________

## [v0.255.1] - 2025-12-11 - Enhanced Database Connection Management with PgBouncer

### Added

- 🚀 **PgBouncer Integration:** Introduced PgBouncer connection pooling for Dagster deployments (all stages except `dev`)
  to improve database connection management and prevent connection exhaustion.
- ✨ **PgBouncer Service:** Added a dedicated PgBouncer service with robust health checks and configurable pooling
  parameters to all non-development Docker Compose configurations.
- 📄 **PgBouncer License Information:** Included the ISC license details for PgBouncer in the project's license
  configuration.

### Changed

- 🔄 **Dagster Database Connectivity:** Updated Dagster's database configuration in `build`, `latest`, `local`, and
  `nightly` stages to connect through PgBouncer (hostname `pgbouncer`, port `6432`) instead of directly to PostgreSQL.
- ⚡️ **Service Dependencies:** Configured Dagster's `webserver` and `daemon` services in non-development environments to
  explicitly depend on the `pgbouncer` service, ensuring correct startup order.

### Refactor

- 🧹 **Dynamic Dagster Configuration:** Refactored the Dagster configuration template (`dagster-config.yml.j2`) to
  conditionally configure database connections: direct to PostgreSQL for `dev` stage, and via PgBouncer for all other
  stages.

______________________________________________________________________

## [v0.255.0] - 2025-12-10 - Enhanced Platform Experience and High-Availability Storage

### Added

- ✨ **Enhanced User Interface Descriptions**: A comprehensive update across all API routes, introducing multi-language
  support (German, French, Italian) and more descriptive names for key platform components, such as `AI Assistants`
  (formerly `Agents`), `Quality Testing` (formerly `Evaluation`), `Activity Log` (formerly `Events`), `Knowledge Base`
  (formerly `Knowledge`), `AI Models` (formerly `Models`), `Chat` (formerly `Open WebUI`), `Workflows` (formerly
  `Processes`), and `Platform Overview` (formerly `Suite`).
- 🔄 **New Document Conversion API**: Introduced a new `/docling/process` API endpoint and corresponding schemas
  (`DocumentConversionMetadata`, `DocumentConversionResponse`) to provide advanced document conversion capabilities,
  allowing direct processing of documents via the API.
- 🚀 **Integrated `etcd` with SeaweedFS Filer**: Added `etcd` as the metadata backend for `SeaweedFS Filer`, enabling
  high-availability deployments and robust metadata storage for the object storage service.
- 🎨 **Improved Image Display in Documentation**: Added CSS rules to invert image colors in light mode within the
  documentation, enhancing readability and visual consistency.
- 📦 **Globally Available `NavigationBoxes` Component**: Made the `NavigationBoxes` component available globally in the
  VitePress documentation theme.

### Changed

- ⚙️ **Refined OpenAI API Endpoints**: Updated OpenAI-compatible API routes to integrate `_with_assistants` versions for
  `get_model` and `chat_completion`, streamlining interactions with AI assistants.
- 📝 **Updated Image Generation Model Default**: Changed the default model for image generation from `dall-e-3` to a more
  generic `image-generation` string, allowing greater flexibility in model selection.
- 📚 **Comprehensive Documentation Overhaul**: Extensive updates to German and English documentation, including
  terminology clarifications, vision alignment, updated feature descriptions, and rewritten FAQs to reflect the
  platform's focus on open-source, data sovereignty, and the new SeaweedFS storage.
- 💾 **Alphabetical Sorting of Services in Platform Overview**: The platform overview now sorts services alphabetically
  by name, improving navigability and user experience.
- 💄 **Theme and UI Enhancements**: Minor visual adjustments to the documentation, including updating tip box colors from
  gray to green and refining gradients and font styles for navigation boxes.

### Fixed

- 🐛 **Docs Link Handling**: Set `ignoreDeadLinks: true` in VitePress configuration to prevent documentation build
  failures due to temporary or external dead links.

### Security

- 🔒 **Removed Anonymous S3 Read Access**: Hardened security for the SeaweedFS S3 policy by removing anonymous read
  actions, ensuring all S3 access requires proper authentication.

### Refactor

- 🧹 **Internal Development Configuration Cleanup**: Removed unused `<node-interpreter>` setting from
  `.idea/runConfigurations/Docs_Dev.xml`.
- 🔄 **Build System Configuration for SeaweedFS**: Updated `generate_compose.py` to include new
  `seaweed-filer-config.toml.j2` templates, ensuring proper generation of SeaweedFS configurations across different
  deployment stages and hardware types.
- 🧹 **User Mock Data Adjustment**: Updated the user mock data to reflect the new `My Account` localization for service
  names.

______________________________________________________________________

## [v0.254.19] - 2025-12-10 - Refined Contextual Chat History Management

### Changed

- 🔄 **Adjusted message ordering** within the `limit_chat_history_with_context` utility. Context messages are now placed
  after the limited chat history but before the final user prompt, optimizing the input structure for generative AI
  models to potentially enhance comprehension and response quality.

______________________________________________________________________

## [v0.254.18] - 2025-12-09 - Docling Loader Robustness and Development Workflow Enhancements

### Fixed

- 🐛 **Improved Docling Content Robustness:** Enhanced the Docling document loader to recursively handle and fix
  malformed `null` meta fields within document content, ensuring better compatibility and preventing errors when
  processing data from older Docling server deployments.

### Changed

- 🔄 **Expanded PR Branch Naming:** Updated CI/CD rules to allow feature branches prefixed with `claude/` to pass
  semantic pull request checks, streamlining specific development workflows.

______________________________________________________________________

## [v0.254.17] - 2025-12-09 - Enhanced RAG Agent with Expert Escalation and Streamlined Bot Communication

### Added

- ✨ **Expert Escalation to RAG Agent**: Introduced a new capability for the **RAG Agent** to escalate questions to human
  experts when the retrieved context is insufficient, improving answer reliability for complex queries.
- 🦾 **Unified Channel Configuration for Bot-in-the-Loop**: Centralized bot communication setup with a new
  `channel_config` for the **Bot-in-the-Loop** agent, enabling seamless integration with both Slack and Microsoft Teams.
- 💬 **Expert Conversation Context Event**: Added `ExpertAnswerContextEvent` to seamlessly integrate expert responses
  into the **RAG Agent**'s context for generating more informed answers.
- 🚫 **Expert Rejection Event**: Introduced `ExpertRejectEvent` to gracefully handle scenarios where users decline human
  expert assistance within the workflow.

### Changed

- 🔄 **RAG Agent Expert Escalation Flow**: The **RAG Agent** now includes new steps for user consent, invoking the
  `ExpertAskingAgent`, and incorporating expert answers, integrating functionality previously handled by the standalone
  `ExpertGroundedAgent`.
- 🤖 **Expert Asking Agent Role Refinement**: The **Expert Asking Agent**'s responsibilities have been refined to focus
  solely on posing questions to experts and validating their responses, removing the previous capability to generate and
  save knowledge snippets to an OpenWebUI knowledge base.
- 📝 **Improved Expert Answer Sufficiency Logic**: Refined the prompt and criteria used by the system to determine
  whether an expert's answer is sufficient, leading to more accurate routing decisions in multi-turn expert
  conversations.
- 📊 **Enhanced Bot Logging**: Added more detailed logging for the **Bot-in-the-Loop** service to provide better
  visibility into conversation handling and thread management across different channels.
- 🖼️ **Refined Image Handling in Pipelines**: Updated the image processing logic within the **AI Hub Pipeline**'s
  `MessageConverter` to directly pass data URLs, improving compatibility with LlamaIndex's image block handling.
- ⚙️ **RAG Agent Configuration Defaults**: Adjusted default settings for the **RAG Agent**, including enabling context
  sufficiency checks by default and increasing the maximum number of input tokens, leading to improved performance and
  robustness.

### Fixed

- 🐛 **Docker Compose Configuration**: Addressed Docker Compose settings by including `LOG_LEVEL` environment variables
  for agents and implementing Traefik labels and local port exposure (8001) for the **Bot** service, enhancing
  debuggability and accessibility in various deployment stages.

### Removed

- 🗑️ **Deprecated Expert Grounded Agent**: The `ExpertGroundedAgent` and all its associated files and events have been
  removed, as its core functionality has been refactored and integrated into the **RAG Agent**.
- 🧹 **OpenWebUI Knowledge Snippet Features**: Eliminated the `ExpertAskingAgent`'s capabilities related to generating
  and persisting knowledge snippets to OpenWebUI, streamlining its core function.
- 📦 **Unused `aihub_integration` Module**: Removed references to the `aihub_integration` module from IDE configuration
  files.
- ✂️ **Unused `stringcase` Dependency**: Cleaned up the `stringcase` dependency from `pyproject.toml` as it was no
  longer utilized.

______________________________________________________________________

## [v0.254.16] - 2025-12-05 - Enhanced Data Versioning for Active Partitions

### Changed

- 🔄 **Refined Dynamic Partition Versioning:** The data versioning operations for Data Lake, Local File System, and
  SharePoint files now intelligently filter to generate versions only for **actively managed dynamic partitions**. This
  improvement ensures that the system tracks versions exclusively for partitions recognized by Dagster, enhancing
  efficiency and preventing the generation of version keys for stale or non-existent partitions.

______________________________________________________________________

## [v0.254.15] - 2025-12-04 - Deeper OpenWebUI Integration, Smarter Document Processing, and Refined Model Management

### Added

- ✨ **Enhanced OpenWebUI Interactivity**: Introduced a suite of new OpenWebUI functions, enabling native streaming for
  AI-Hub agent responses, interactive displays for event traces and document sources, and direct OpenAI-compatible
  access to AI-Hub models directly within OpenWebUI.
- 🚀 **LLM-Powered Document Table Refinement**: Implemented a new pipeline resource and operation for intelligent table
  processing during document ingestion, which uses LLMs to automatically detect and split merged tables and identify
  complex multi-row headers, significantly improving data extraction accuracy.
- 📦 **Dedicated Production Configuration Template**: A new `.env.prod` template now provides a clear and comprehensive
  guide for configuring production deployments, enhancing setup reliability and security.
- ⚙️ **Streamlined Development Run Configurations**: Added new run configurations for simplified local web development
  and one-click execution of the default RAG pipeline.
- 🗃️ **Automatic Default Knowledge Base Bucket**: The S3 storage service now automatically provisions a
  `defaultknowledge` bucket, simplifying initial setup for RAG-enabled applications.

### Changed

- ⬆️ **Upgraded Core AI Models**: Updated LiteLLM configurations to integrate the latest Azure OpenAI models for chat,
  vision, and audio (e.g., GPT-4o mini, text-embedding-3-large) and Cohere for reranking, boosting overall model
  performance and broadening AI capabilities.
- 📈 **Optimized Agent Online Status Reporting**: The AI-Hub API now determines agent online status based on
  `last_discovered` timestamps stored in the database, reducing overhead and improving responsiveness compared to
  real-time NATS discovery for every request.
- 🔑 **Improved S3 Public File Access**: Enhanced S3 file access services to ensure presigned URLs for uploaded documents
  are consistently generated with public endpoints and `s3v4` signatures, facilitating reliable browser access.
- 📄 **Clarified VLM Prompting Guidelines**: Updated Vision Language Model (VLM) prompt instructions across all supported
  languages to strictly guide models to describe only observable visual content, preventing speculative responses based
  on text context.
- 🗄️ **Standardized MongoDB UUID Handling**: All MongoDB connections are now explicitly configured with
  `uuidRepresentation="standard"`, ensuring consistent and predictable UUID behavior across the platform.
- 🐳 **Improved Docker Compose Build Process**: The Docker Compose build run configuration now includes the `--build`
  flag by default, ensuring that service images are rebuilt when upstream changes occur.
- ⏱️ **Increased LiteLLM Startup Robustness**: Extended the health check `start_period` for the LiteLLM service to 120
  seconds, improving stability during initial deployment and preventing premature health check failures.
- 🛠️ **Refined RAG Agent and Pipeline Defaults**: Adjusted default RAG agent and pipeline configurations, including
  upgrading to `embedding/large` and adding `max_partitions` to improve data ingestion control and vector retrieval
  efficiency.
- 🖥️ **OpenWebUI Feature Cache Management**: Disabled the base model cache in OpenWebUI to ensure that dynamic pipeline
  models and agent configurations are always fetched fresh.
- 🐛 **Docling Document Loader Table Output**: Modified the Docling document loader to output tables in a standardized
  Markdown format instead of raw HTML, improving compatibility with subsequent document parsing steps.

### Refactor

- 🧹 **Centralized Logging Infrastructure**: The core logging system was refactored and moved to
  `aihub_lib.infrastructure.logging`, promoting a more modular and reusable architectural design.
- ⚙️ **Consolidated Internal Service Endpoints**: Internal Docker network endpoints for various services are now
  hardcoded directly within Docker Compose templates, simplifying environment variable management and improving
  deployment consistency.
- 🗑️ **Modernized OpenWebUI Integration Module**: The `aihub_integration` module has been removed, as its
  functionalities are now provided through the new, more flexible OpenWebUI function integration.

### Fixed

- 🐛 **Docling Metadata Handling**: Resolved an issue in the Docling document loader where null meta fields in JSON
  content could cause processing errors, enhancing document ingestion reliability.
- 🐞 **WebSocket Endpoint Correction**: Fixed an incorrect WebSocket endpoint path in the API service configuration,
  ensuring proper real-time event streaming for clients.

______________________________________________________________________

## [v0.254.14] - 2025-12-03 - LLM Input Processing and Multimodal Enhancements

### Added

- ✨ **Enhanced `UserMessageEvent`**: Introduced the `last_user_message` property to `UserMessageEvent`, providing direct
  access to the complete last user message, including all multimodal blocks (like images), for richer LLM interactions.

### Changed

- 🔄 **Improved LLM Message Handling in RAG Agent**: The RAG Agent now explicitly merges consecutive chat messages
  (including multimodal content blocks) with the same role right before sending them to the LLM. This ensures better
  compatibility with various LLM providers (e.g., LiteLLM) and more robust multimodal support.
- 🦾 **Refined Multimodal Message Merging**: The internal `merge_consecutive_messages` utility has been updated to
  correctly handle and combine multimodal `ChatMessage` blocks, ensuring proper formatting when multiple parts of a
  message are from the same role.
- 🖼️ **Simplified Image URL Processing**: The Open WebUI integration now streamlines the handling of image URLs,
  including `data:image` URLs, by directly passing them to LlamaIndex's `ImageBlock`. This improves consistency and
  reliability for multimodal inputs.

### Refactor

- 🧹 **Streamlined LLM Configuration**: The custom `PreprocessingOpenAILike` wrapper has been removed, and `LLMConfig`
  now directly utilizes `OpenAILike`. This change centralizes message preprocessing logic within the agent's flow rather
  than the LLM wrapper, simplifying the overall architecture.

______________________________________________________________________

## [v0.254.13] - 2025-12-03 - Robust Evaluation and Phoenix Client Modernization

### Refactor

- 🔄 **Upgraded Phoenix Client Integration**: Modernized the backend to utilize the new asynchronous Phoenix client,
  streamlining experiment and dataset interactions with updated imports, client initialization, and method calls.
- 🦾 **Optimized LLM Structured Output**: Improved the judge LLM's ability to generate structured evaluations by
  transitioning from direct JSON output instructions to leveraging LlamaIndex's advanced tool-calling capabilities,
  enhancing reliability.

### Changed

- ⚡️ **Stricter Evaluation Summary Generation**: Evaluation summaries are now only created when valid scores are
  available, ensuring data integrity and preventing empty summary entries in the evaluation results.
- 📄 **Updated Evaluation Summary Data Model**: The `avg_score` field in evaluation summaries is now explicitly a
  required float, aligning with the refined backend logic that guarantees a valid score when a summary exists.

### Fixed

- 🐛 **Improved UI Robustness for Missing Scores**: Frontend evaluation result displays now gracefully handle cases where
  scores might be absent for certain evaluators, preventing UI errors and defaulting to zero when data is unavailable.
- 🛠️ **Corrected Phoenix Experiment ID Access**: Addressed an issue where `RanExperiment` data was accessed incorrectly,
  ensuring reliable retrieval of experiment IDs after an experiment run.

______________________________________________________________________

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

______________________________________________________________________

## [v0.254.11] - 2025-12-02 - Enhanced Document Intelligence Figure Extraction

### Changed

- 🖼️ **Document Intelligence Figure Handling:** Reworked the figure extraction and replacement mechanism within the
  `DocumentIntelligenceLoader` to leverage precise span offsets provided by the API, ensuring more accurate and robust
  figure integration into the document text.
- ⚡️ **Improved Figure Processing Robustness:** Implemented a new strategy for figure replacement that processes figures
  in reverse order of their appearance, mitigating issues related to text shifts and ensuring correct figure placement.
- 🐛 **Strengthened Figure Data Validation:** Introduced validation checks for figure span information to gracefully
  handle cases where span data is missing or out of bounds, preventing errors during document processing.

______________________________________________________________________

## [v0.254.10] - 2025-12-02 - AI-Powered Code Review and On-Demand Assistance with Claude

### Added

- ✨ **Automated AI Code Reviews:** Introduced a new GitHub Actions workflow to automatically run Claude AI code reviews
  on pull requests, providing comprehensive feedback on code quality, potential bugs, performance, security, and test
  coverage.
- 🤖 **On-Demand AI Assistant:** Added a new GitHub Actions workflow enabling direct interaction with Claude AI within
  issues, pull request comments, and reviews by tagging `@claude`. This facilitates on-demand code assistance,
  explanations, and insights.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.254.6] - 2025-11-24 - Documentation Experience Refresh and Strategic Messaging Update

### Added

- 🖼️ **Enhanced Image Viewing:** Integrated a new lightbox plugin and `medium-zoom` functionality into the
  documentation, providing an improved and interactive experience when viewing images.
- ⚡️ **Custom Documentation Layout:** Introduced a dedicated `Layout.vue` component to streamline and centralize
  documentation theme customizations, including a `GradientBackground` component.

### Changed

- 📄 **Updated Homepage Features:** The homepage (`index.en.md`) feature descriptions have been entirely rewritten to
  better articulate the platform's value proposition, emphasizing open-source, ownership, rapid deployment, strategic
  independence, transparency, and collaborative strength.
- 📐 **Refreshed Architecture Diagrams:** Updated various high-level and low-level architecture diagrams to reflect the
  latest system design and clarity.

### Refactor

- 🧹 **Documentation Theme Structure:** Refactored the documentation theme's `index.js` to leverage a dedicated
  `Layout.vue` component, simplifying the theme configuration and improving maintainability.
- 🔄 **Dependency Import Path:** Adjusted the import path for `CopyOrDownloadAsMarkdownButtons` in the documentation
  theme for consistency and clarity.

______________________________________________________________________

## [v0.254.5] - 2025-11-24 - Platform Configuration Update and Docling Refinements

### Changed

- 📄 **Updated DNS Prerequisites:** Replaced the `datalake-api` subdomain requirement with `litellm.aihub.example.com`
  for the `litellm` proxy, streamlining API access configurations for the platform.

### Removed

- 🗑️ **Removed Docling Model Initialization Script:** The dedicated `init-models.sh` script, previously responsible for
  checking and downloading Docling models, has been removed, indicating an updated or integrated approach to model
  management.

______________________________________________________________________

## [v0.254.4] - 2025-11-21 - Internal Consistency Improvements

### Refactor

- 🧹 **Standardized `build_uri` parameter:** Updated the `data_lake_client.build_uri` method call within the data lake
  file removal process to use `file_path` instead of `path`, enhancing parameter naming consistency across the API.

______________________________________________________________________

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

______________________________________________________________________

## [v0.254.2] - 2025-11-18 - New Service Integrations and Deployment Enhancements

### Added

- 🚀 **Gunicorn Dependency**: Incorporated Gunicorn, a robust WSGI HTTP server, into the project dependencies to bolster
  production deployment capabilities.
- 📄 **Docling Configuration**: Integrated new environment variables for **Docling** and **Hosted VLM** API endpoints,
  timeouts, and model specifics across all Docker Compose configurations, preparing the ground for advanced document
  processing and visual language model integrations.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.253.2] - 2025-11-14 - Comprehensive Bot Setup Documentation

### Added

- 📄 **New Bot Creation Manual Setup Guide**: Introduced a comprehensive, step-by-step guide for manually creating and
  configuring bots with Microsoft Teams and Slack. This detailed resource covers everything from Azure Bot Framework and
  Teams Developer Portal setup to MongoDB configuration and Slack OAuth integration, complete with app manifest
  examples, key terminology, and troubleshooting tips.

### Changed

- 🔗 **Updated Chat Interface Documentation Link**: Corrected and updated an internal documentation link pointing to the
  chat interface feature overview, ensuring users are directed to the most current information.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.249.3] - 2025-11-05 - Streamlined LiteLLM API Parameter Handling

### Changed

- 🔄 **Improved LiteLLM Model Parameter Handling:** Configured various LiteLLM models (e.g., `text-generation/mini`,
  `text-generation/small`, `text-generation/large`) across all environments (`dev`, `latest`, `local`, `nightly`) to
  automatically **drop extraneous parameters** from API requests, enhancing compatibility and robustness with underlying
  services.

______________________________________________________________________

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

______________________________________________________________________

## [v0.249.1] - 2025-11-04 - Enhanced Authentication Service Robustness

### Fixed

- 🐛 **Resolved intermittent connectivity issues** with external authentication and identity services (JWKS and Azure
  Graph API) by extending connection timeouts to better accommodate IPv6 fallback mechanisms.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.247.7] - 2025-11-03 - Enhanced RAG with Hybrid Search and Model Updates

### Added

- 🚀 **Introduced Hybrid Search Capability:** Enabled **Milvus vector stores** to perform hybrid search queries by
  integrating sparse embeddings and BM25 functionality, improving retrieval relevance.

### Changed

- 🔄 **Default Query Mode to Hybrid:** Updated the default query mode for **RAG and Retrieval agents** to `HYBRID`,
  leveraging the newly added hybrid search capabilities in Milvus for more comprehensive retrieval.
- ⬆️ **Updated Default LLM Model:** Switched the default Large Language Model in **RAG pipelines** from
  `gemma-3-multimodal-small` to `qwen-2.5-multimodal-small`, enhancing model performance and capabilities.

______________________________________________________________________

## [v0.247.6] - 2025-10-31 - Empowering Contributors with New Guidelines

### Added

- ✨ **Added a comprehensive `CONTRIBUTING.md` guide:** This new document provides clear instructions and best practices
  for anyone looking to contribute to the Swiss AI-Hub project, covering everything from code contributions to
  documentation, community engagement, and advocacy, fostering a more collaborative environment.

______________________________________________________________________

## [v0.247.5] - 2025-10-31 - Enhanced Security Measures

### Security

- 🔑 **Established comprehensive security policy:** Introduced a new `SECURITY.md` file, providing clear guidelines on
  how to report security vulnerabilities, outlining supported versions, and detailing the coordinated disclosure
  process.

______________________________________________________________________

## [v0.247.4] - 2025-10-31 - Community Guidelines Established

### Added

- 📄 **Introduced Code of Conduct**: Adopted the Contributor Covenant 3.0 to foster a welcoming, safe, and equitable
  community by outlining expected behaviors, restricted actions, and a clear process for reporting and addressing
  issues.

______________________________________________________________________

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

______________________________________________________________________

## [v0.247.2] - 2025-10-31 - Optimized CI Documentation Builds

### Changed

- 🚀 **Streamlined CI documentation deployment:** Updated the GitHub Actions workflow for documentation deployment to
  utilize a new, optimized build script, enhancing efficiency and reducing build times in continuous integration
  environments.
- ⚙️ **Introduced dedicated `docs:build:ci` script:** Added a specialized `docs:build:ci` command to `package.json`,
  which supports the faster documentation building process for CI by omitting the translation step.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.246.9] - 2025-10-22 - Streamlined DoclingLoader File Handling

### Refactor

- ⚡️ **Optimized `DoclingLoader` file content retrieval:** Improved the internal efficiency of `DoclingLoader` by
  switching to `fs.cat_file` for more direct and potentially faster reading of file contents.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.246.5] - 2025-10-14 - Refined S3 URI Handling in Data Lake Components

### Refactor

- 🧹 **Standardized S3 URI Parsing:** Replaced manual string slicing with the more robust `str.removeprefix()` method for
  parsing S3 URIs across `S3DataLakeIOManager` and `S3DataLakeClient`, enhancing reliability and code clarity.
- ⚡️ **Improved S3 Path Normalization:** Added `lstrip("/")` during S3 URI processing to ensure more consistent and
  robust path handling within the `S3DataLakeIOManager`.
- 📄 **Enhanced S3 Write Logging:** Updated the logging message for successful S3 writes to display the fully
  reconstructed S3 URI, improving clarity and debuggability.

______________________________________________________________________

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

______________________________________________________________________

## [v0.246.3] - 2025-10-13 - Enhanced S3 URI Robustness

### Changed

- 🚀 **Improved S3 URI Parsing:** The `S3DataLakeClient` now intelligently handles S3 URIs, automatically prepending the
  "s3://" prefix when a URI starts directly with the configured container name, reducing errors and making input more
  flexible.

______________________________________________________________________

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

______________________________________________________________________

## [v0.246.1] - 2025-10-09 - Retrieval Agent Context Customization

### Added

- ✨ **Configurable Context Prompt for Retrieval Agent:** Introduced a new `context_prompt` configuration option for the
  `RetrievalAgent`, allowing users to define a custom prompt that dictates how combined and ordered retrieved nodes are
  formatted.

______________________________________________________________________

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

______________________________________________________________________

## [v0.245.9] - 2025-10-07 - Enhanced User Data Handling in Authentication

### Changed

- ⚡️ **Improved User Header Encoding**: Switched from Base64 to URL encoding for usernames in authentication headers and
  signatures, enhancing compatibility and robustness when handling special characters.

______________________________________________________________________

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

______________________________________________________________________

## [v0.245.7] - 2025-10-02 - Agent Guard Message Consistency

### Fixed

- 🐛 **Corrected RAGAgent guard rejection messaging:** Ensured the **RAGAgent** accurately formats system messages for
  guard rejections by using the correct reason property (`event.reason`), improving clarity and consistency in agent
  responses.

______________________________________________________________________

## [v0.245.6] - 2025-10-01 - Containerization of Aihub Bot for Enhanced Deployment

### Added

- ✨ **Introduced Dockerfile for Aihub Bot:** Added a comprehensive Docker configuration to containerize the Aihub Bot,
  enabling consistent and portable deployments across various environments.
- 🚀 **Streamlined Build and Runtime Environments:** Implemented a multi-stage Docker build process to optimize image
  size and efficiency, ensuring a lean runtime environment.
- 🔒 **Enhanced Operational Security and Dependency Management:** Configured a non-root user for improved security and
  integrated Poetry for robust Python dependency management within the container.

______________________________________________________________________

## [v0.245.5] - 2025-09-30 - Infrastructure and Developer Experience Enhancements

### Added

- ⚙️ **Introduced `set-latest` GitHub Action:** A new automated workflow for managing container image tags, ensuring the
  `latest` tag is correctly applied to published images, improving deployment consistency.

### Refactor

- 🧹 **Refined Model Data Fetching:** Updated the web application's SDK to use clearer `getModels` API calls and
  `ModelTypeGroupDtoReadable` types, enhancing code readability and maintainability.
- ⚡️ **Optimized ESLint Configuration:** Streamlined the ESLint setup by expanding global ignore rules to skip
  unnecessary files and simplifying plugin imports, leading to faster linting and a cleaner development environment.

______________________________________________________________________

## [v0.245.4] - 2025-09-30 - Internal Codebase Refinements

### Refactor

- 🧹 **Standardized Event Types:** Aligned internal naming conventions by updating the `ChunkEventReadable` type to
  `ChunkEvent` within the event component resolution logic, enhancing code consistency.

______________________________________________________________________

## [v0.245.3] - 2025-09-25 - LLM Event Metadata Refinement and Developer Experience Improvements

### Changed

- 🔄 **Updated LLM Event Logging:** Adjusted the **`LLMEvent`** to correctly capture the chat model name using the
  `model_name` property from the agent configuration, ensuring more accurate and consistent event metadata.

### Refactor

- 🧹 **Improved `.gitignore`:** Added a rule to ignore **GitHub Copilot** related files, streamlining the development
  environment setup and reducing repository clutter.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.244.1] - 2025-09-16 - Persistence Layer Refinement

### Refactor

- 🧹 **Namespace Entity field renamed:** Renamed the `last_updated` field to `updated_at` in the `NamespaceEntity` for
  improved consistency and clarity in data lake persistence.

______________________________________________________________________

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

______________________________________________________________________

## [v0.243.10] - 2025-09-13 - Quick Start Documentation Refinement

### Removed

- 🗑️ Removed the extensive **SDK Architecture documentation** from the Quick Start section, which previously detailed
  the `aihub_lib`, `aihub_agent`, `aihub_pipeline`, `aihub_process`, `aihub_api`, and `aihub_bot` packages, as well as
  cross-package integration patterns. This content, previously marked as Work In Progress (WIP), has been temporarily
  cleared.
- 🗑️ Removed the in-depth **"Why our SDK" documentation** from the Quick Start guides, which provided a comprehensive
  comparison with other AI frameworks and platforms. This content, previously marked as Work In Progress (WIP), has been
  temporarily cleared.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.243.7] - 2025-09-11 - Streamlined Release Tagging Workflow

### Refactor

- 🔄 **Refactored Release Tagging Workflow:** Improved the internal GitHub Actions workflow responsible for creating and
  pushing release tags. This update ensures that any last-minute changes are incorporated into the main release commit
  via an atomic amend operation, and utilizes a safer `force-with-lease` push strategy. Additionally, redundant tag
  verification steps have been removed to streamline the overall release process.

______________________________________________________________________

## [v0.243.6] - 2025-09-10 - Robust Release Tagging Workflow

### Fixed

- 🐛 **Corrected Tagging Reference:** Ensured that release tags consistently point to the correct merge commit or the
  latest `main` branch tip in GitHub Actions, particularly for squash and rebase merges, preventing tags from being
  created against incorrect SHAs.

### Changed

- 🚀 **Improved Tag Verification Process:** Enhanced the reliability and feedback of the post-push tag verification in
  GitHub Actions by directly fetching remote tags and performing a local check, providing clearer success and failure
  indications during the release tagging workflow.

______________________________________________________________________

## [v0.243.5] - 2025-09-09 - Enhanced CI/CD Tag Verification Reliability

### Changed

- ⚡️ **Improved Tag Verification Reliability:** The GitHub Actions workflow for adding release tags now includes
  multiple retry attempts with a brief delay, making the remote tag verification process more robust and resilient to
  transient network issues or eventual consistency delays.

______________________________________________________________________

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

______________________________________________________________________

## [v0.243.3] - 2025-09-09 - Next-Gen AI Development: Comprehensive Docs, Core Platform & SDK Refinements

### Added

- ✨ **New Documentation Structure & Content:** Introduced a completely reorganized documentation site, moving from a
  previous three-part structure to a comprehensive five-part journey: `Vision & Positioning`, `Platform Journey`,
  `SDK Journey`, `Ecosystem Journey`, and `Reference & Resources`. This includes entirely new sections on the problem
  solved, our solution, the Swiss approach, and detailed architecture.
- 🎨 **Interactive Documentation UI:** Enhanced the documentation site with new Vue components for interactive navigation
  boxes and dynamic gradient backgrounds, significantly improving user experience and visual appeal.
- 🚀 **Refined Core Platform Deployment:** Introduced `docker-compose-core.dev.yml`, a comprehensive Docker Compose
  configuration that integrates all core infrastructure services for robust local development and streamlined production
  deployments.
- 📦 **SDK Quickstart Examples:** Added new Python files (`my_document_pipeline.py`, `simple_pipeline.py`) to the
  `aihub_pipeline/playground/quick_start/` directory, providing runnable examples for building data ingestion pipelines.
- ⚡ **Pipeline Quickstart Tooling:** Added a `quickstart` target to the `aihub_pipeline` Makefile for easily running
  quickstart pipeline examples.
- 🌐 **Frontend Development Variables:** Added `WEBUI_URL` and `WS_ENDPOINT` to `.env.dev` to streamline local frontend
  development.
- 🧹 **Temporary File Exclusion:** Added `.tmp*` to `.gitignore` in `aihub_pipeline` to ignore temporary build files.

### Changed

- ⚙️ **Deep OpenWebUI Integration & Configuration:** Expanded the `open-webui` service configuration with extensive
  environment variables, enabling granular control over authentication, storage, model access, PII handling, web search,
  image generation, code interpretation, audio features, and user permissions.
- 📖 **Documentation Navigation & Styling:** Updated documentation front matter indices and integrated new custom CSS for
  enhanced theming, fonts, scrollbars, and improved Mermaid diagram rendering across the site.
- 🔗 **Documentation Internal Linking:** Updated internal links within `aihub_bot/README.md`, `aihub_lib/README.md`,
  `aihub_agent/README.md`, `aihub_api/README.md`, and `aihub_process/README.md` to align with the new documentation
  structure.
- 📄 **Unified Root README Location:** Modified the `sync-docs.sh` script to correctly place the root `README.md` within
  the new documentation structure at `docs/6_code_deep_dive/1_introduction/index.md`.
- 🚀 **Docling UI Enabled by Default:** Enabled the Docling service UI in `docker-compose.dev.yml` for improved
  visibility during development.
- 🦶 **Updated Footer Copyright:** Changed the footer message in the documentation site.

### Removed

- 🗑️ **Obsolete Documentation Content:** Deleted outdated documentation sections related to `1_business`,
  `2_developers`, and `3_features`, which have been superseded by the new, comprehensive documentation structure.
- 🖼️ **Deprecated Architecture Diagrams:** Removed old architecture diagrams (`tier1.png`, `tier2.png`, etc.) as they
  have been replaced by new, detailed diagrams reflecting the updated platform vision.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.243.0] - 2025-09-02 - Refined Image Tagging for Build Action

### Changed

- ⚡️ **Improved Image Tagging:** The `build_image` GitHub Action has been updated to use comma-separated values for
  secondary image tags, ensuring more robust and widely compatible tag assignment for published images.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.240.6] - 2025-08-26 - S3 Security Hardening and Configuration Alignment

### Security

- 🔑 **Enhanced Secret Key Handling:** Updated S3 resource configurations to securely access secret keys using
  `.get_secret_value()`, reinforcing protection for sensitive credentials across S3 file access services and data lake
  clients.

### Changed

- 🔄 **Standardized S3 Endpoint Configuration:** Renamed the S3 configuration parameter `ENDPOINT_URL` to `ENDPOINT` for
  consistency across all related S3 services and resources, simplifying configuration management.

______________________________________________________________________

## [v0.240.5] - 2025-08-22 - Core Infrastructure Updates and Build System Refinements

### Changed

- 🚀 **Upgraded `aihub_pipeline` Docker images to Python 3.13** from 3.11, leveraging the latest language features and
  performance improvements for pipeline execution.
- ⚙️ **Enhanced CI/CD workflows to support private GitHub dependencies** by configuring SSH, facilitating more robust
  and secure access to internal repositories during automated builds.
- 📦 **Streamlined Docker build processes** by temporarily including the `mdformat-vuepress` module in several service
  images (`aihub_agent`, `aihub_api`, `aihub_pipeline`) to ensure internal tool compatibility.

______________________________________________________________________

## [v0.240.4] - 2025-08-15 - Enhanced CI/CD Actions with Python Version Flexibility

### Changed

- ⚡️ **Configurable Python Version for Backend Actions**: The `lint_backend` and `test_backend` GitHub Actions now
  support a new `python_version` input. This allows users to specify the Python version used for linting and testing
  within their workflows, providing greater flexibility while maintaining `3.13` as the default.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.238.0] - 2025-08-06 - Internal Version Alignment

### Changed

- ⬆️ **Internal Version Alignment:** Updated the version numbers across all core microservices (`aihub_agent`,
  `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`) and synchronized internal
  dependency tags to `v0.238.0`, ensuring consistent versioning for the new release.

______________________________________________________________________

## [v0.237.0] - 2025-08-06 - GitHub Action Streamlining

### Removed

- 🗑️ **Removed GitHub Release creation:** The automated step within the build image action that previously created a
  GitHub Release for the built Docker image has been removed.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.233.0] - 2025-07-30 - Internal Dependency Enhancements

### Changed

- ⚡️ **Internal Dependency Updates:** Upgraded core libraries to enhance stability and prepare for future improvements.

______________________________________________________________________

## [v0.232.0] - 2025-07-29 - Enhanced Dashboard Trend Clarity

### Changed

- 💡 **Adjusted Trend Indicator Logic:** The trending up/down visual indicators for **Exception Events** on dashboards
  now correctly reflect their severity, displaying green for trending down (good) and red for trending up (bad) to
  provide more intuitive visual feedback.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.228.0] - 2025-07-25 - Azure Document Intelligence Key Access Alignment

### Refactor

- 🔄 **Updated Azure Document Intelligence Key Access:** Aligned the method for retrieving primary keys from Azure
  Document Intelligence services with recent API changes, ensuring robust and consistent authentication.

______________________________________________________________________

## [v0.227.0] - 2025-07-23 - Improved Azure Identity Service Robustness

### Fixed

- 🖼️ **Azure User Profile Image Fetching**: Enhanced the retrieval of user profile images from the Azure Graph API to be
  more resilient to various API errors. The service now gracefully handles non-404 errors by logging warnings and
  consistently returns `None` when an image cannot be fetched, preventing unexpected exceptions and improving stability.

### Refactor

- 🧹 **Import Statement Placement**: Relocated the `asyncio` import to the top-level of the `AzureGraphService` module,
  aligning with best practices for improved code readability and organization.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.221.0] - 2025-07-14 - Prompt Refinements and Image Handling Improvements for RAG

### Changed

- 🔄 **Updated RAG Context Prompt Role:** The chat role for the RAG context prompt has been adjusted from `system` to
  `user` across all supported languages (German, English, French, and Italian) to better align with prompt engineering
  best practices and enhance model interpretation of contextual information.

### Fixed

- 🖼️ **Corrected Image URL Handling in RAG Prompts:** Resolved an issue in the English RAG context prompt where image
  URLs were not consistently processed, ensuring that images are now correctly referenced and displayed by explicitly
  converting their URL object to a string representation.

______________________________________________________________________

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

______________________________________________________________________

## [v0.219.0] - 2025-07-11 - Internal Workflow Automation Adjustment

### Removed

- 🗑️ **Automatic Draft PR Workflow:** The GitHub Actions workflow that previously created automatic draft pull requests
  for new branches has been removed.

______________________________________________________________________

## [v0.218.0] - 2025-07-11 - Enhanced API Configuration and Extensibility

### Added

- ✨ **Enabled custom environment variable configuration for API services:** This new capability allows users to define
  and inject additional environment variables, including secret references, directly into API deployments, significantly
  increasing configuration flexibility and integration possibilities.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.209.0] - 2025-07-03 - Automated PR Readiness Checks with Claude Integration

### Added

- 🦾 **Automated Subproject PR Readiness:** Introduced a new intelligent script that automatically identifies the root of
  a subproject based on edited files and executes `make pr-ready`, standardizing pre-PR checks and ensuring code
  quality.
- ⚡️ **Claude Post-Edit Automation:** Configured Claude to automatically trigger the new PR readiness script immediately
  after any file modifications (Write, Edit, MultiEdit), providing instant feedback on code quality and readiness within
  the development workflow.

______________________________________________________________________

## [v0.208.0] - 2025-07-03 - Refined Context Metadata for Generative AI

### Changed

- 📄 **Streamlined RAG Context Metadata**: The **`document_title`** is now explicitly included in the metadata when
  combining nodes for Retrieval Augmented Generation (RAG) contexts, providing more direct document identification
  within prompts.
- 🗑️ **Consolidated Node Metadata Fields**: To simplify and optimize the context provided to generative AI models, the
  `namespace`, `type`, and `content_type` fields are no longer emitted as part of the combined node metadata.

______________________________________________________________________

## [v0.207.0] - 2025-07-01 - Streamlined Release Tagging

### Removed

- 🗑️ **Streamlined Release Tagging**: Removed the redundant step of deleting existing Git tags in the CI/CD workflow,
  simplifying the release automation process.

### Changed

- 🔄 **Platform Version Alignment**: All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`,
  `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their internal `aihub_lib` dependencies have been updated to
  `v0.207.0`, ensuring a unified and consistent release across the entire platform.

______________________________________________________________________

## [v0.206.0] - 2025-07-01 - Core System Modernization: Enhanced Model Definitions

### Refactor

- 🧹 **Updated Pydantic Model Definitions**: Migrated numerous internal data models across all core services
  (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`, `aihub_process`,
  `webui_pipelines`) to leverage Pydantic v2's `Annotated` type hint and explicit default value assignments. This
  enhances code clarity, type safety, and aligns the codebase with modern Python best practices.

______________________________________________________________________

## [v0.205.0] - 2025-07-01 - Core Module Version Synchronization

### Changed

- 🔄 **Core Module Version Alignment**: All internal microservices (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`,
  `aihub_lib`, `aihub_pipeline`, `aihub_process`) and their `aihub_lib` dependencies have been updated to `v0.205.0`,
  ensuring consistent versioning across the platform.
- ⚙️ **Build Tag Update**: The default build tag in the `Makefile` has been updated to `v0.205.0` to reflect the latest
  release version.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.198.0] - 2025-06-24 - Pipeline Embedding Enhancements

### Changed

- 🦾 Improved **node embedding content** within pipelines by transitioning from `get_text()` to
  `get_content(metadata_mode=MetadataMode.EMBED)` for extracting text. This ensures that relevant metadata is also
  considered, leading to potentially richer and more accurate vector embeddings.

______________________________________________________________________

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

______________________________________________________________________

## [v0.196.0] - 2025-06-20 - Automation Enhancements and Version Synchronization

### Added

- ✨ **Enhanced Automated Pull Request Creation:** Improved the CI/CD workflow for generating automatic draft pull
  requests by incorporating full Git history fetching and enabling automatic population of PR descriptions from commit
  messages, streamlining development processes.

### Changed

- 🔄 **Project Version Synchronization:** Aligned all microservices and core libraries, including `aihub_agent`,
  `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, and `aihub_pipeline`, to version `v0.196.0` for consistent
  dependency management and release coordination.

______________________________________________________________________

## [v0.195.0] - 2025-06-20 - Enhanced Pipeline Efficiency

### Changed

- ⚡️ **Optimized Dynamic Partition Management**: The `replace_partition_keys` utility in the pipeline core has been
  significantly improved to efficiently add and delete only the necessary dynamic partitions, thereby reducing
  unnecessary operations and enhancing overall performance for data pipeline execution.

______________________________________________________________________

## [v0.194.0] - 2025-06-19 - Core System Alignment and Pipeline Operation Streamlining

### Changed

- 🔄 **Core Service Version Alignment:** Updated internal dependency versions across all `aihub_` services (agent, api,
  bot, iac, lib, pipeline) and the Makefile to `v0.194.0` for consistent build and deployment.

### Refactor

- 🧹 **Simplified Data Lake File Fetching:** Refactored `fetch_all_files_in_data_lake` operations within the pipeline
  module to remove direct `OpExecutionContext` dependency and internal logging, promoting cleaner, more focused data
  retrieval logic.

______________________________________________________________________

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

______________________________________________________________________

## [v0.192.0] - 2025-06-18 - Streamlined Branch Naming and Project Alignment

### Changed

- 🔄 **Relaxed Branch Naming Conventions:** Updated the semantic PR GitHub workflow to allow more flexible and generic
  branch names (e.g., `feature/my-feature`, `bugfix/issue-123`) by replacing specific initiative branch patterns with a
  broader regular expression. This simplifies development workflows and enhances consistency.
- ⬆️ **Project Version Alignment:** Aligned all internal project and library dependencies across microservices
  (`aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_iac`, `aihub_lib`, `aihub_pipeline`) to the new `v0.192.0` release
  tag, ensuring consistent versioning throughout the codebase.

______________________________________________________________________

## [v0.191.0] - 2025-06-18 - LLM Event Reporting Enhancements

### Added

- ✨ **Improved LLM Event Reporting**: Introduced a new `from_chat_response` method to `LLMEvent` for easier creation of
  LLM events directly from LlamaIndex chat responses, automatically capturing token usage for enhanced observability.

______________________________________________________________________

## [v0.190.0] - 2025-06-16 - Core Updates and Path Robustness

### Fixed

- 🐛 **Enhanced Data Lake Path Generation:** Improved the utility for creating data lake figure folder names by
  transitioning to a more robust file name parsing method (`os.path.splitext`), ensuring accurate and reliable folder
  structures regardless of complex file naming conventions.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.187.0] - 2025-06-12 - Core Refinements and Stability Updates

### Fixed

- 🐛 **Document Parsing Robustness:** Enhanced the Markdown structural node parser to gracefully handle empty content,
  preventing potential processing errors during document ingestion.
- 🛡️ **Table Reformatting Stability:** Improved the document table reformatting process within the pipeline to prevent
  errors when encountering documents with missing or empty text content.

### Changed

- ⚙️ **Pipeline Function Clarity:** Updated function calls within the `documents_factory` in the pipeline to
  consistently use keyword arguments, improving code readability and maintainability.

______________________________________________________________________

## [v0.186.0] - 2025-06-12 - Enhanced Data Flexibility and Azure AI Integration

### Changed

- 🔄 **Improved Document Metadata Handling:** The `IngestedBase` and `IngestedNode` document types now dynamically
  capture and retain all additional, non-standardized metadata fields present in source documents, significantly
  enriching the information available for RAG pipelines.
- 🔑 **Enhanced Azure OpenAI Embedding Authentication:** Explicitly enabled Azure Active Directory (AAD) authentication
  for Azure OpenAI embedding models, providing more secure and robust integration with Azure environments.

______________________________________________________________________

## [v0.185.0] - 2025-06-11 - Internal Updates and CI/CD Streamlining

### Refactor

- 🧹 **Optimized Build Process:** Removed the explicit code checkout step within the `build_image` GitHub Action,
  streamlining the image building process and potentially reducing redundant operations.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.182.0] - 2025-06-11 - Enhanced Bot Responsiveness

### Fixed

- 🐛 **Resolved Bot Typing Behavior:** Corrected the timing of the bot's "typing" indicator to ensure it only appears
  when the bot is actively processing a response, preventing misleading indicators for interactions the bot is
  configured not to respond to (e.g., expired conversations).

______________________________________________________________________

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

______________________________________________________________________

## [v0.180.0] - 2025-06-10 - Enhanced Bot Robustness and Core Version Alignment

### Fixed

- 🐛 **Improved Chat Bot Locale Handling:** Addressed an issue in the `BaseChatBot` to gracefully handle scenarios where
  user locale information might be missing, ensuring robust locale resolution by falling back to a default.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.174.0] - 2025-05-30 - Infrastructure Constant Refinement

### Refactor

- 🧹 **Centralized Document Store Suffix:** Extracted the `DEFAULT_DOCSTORE_SUFFIX` constant from the `StoresConfig`
  module into a new, dedicated constants file, enhancing code organization and maintainability within the infrastructure
  components.

______________________________________________________________________

## [v0.173.0] - 2025-05-30 - Infrastructure Enhancements: Cosmos DB Document Store Support

### Added

- ✨ **Cosmos DB Document Store Integration:** Introduced full support for provisioning and managing Cosmos DB as a
  document store within the Azure Infrastructure as Code (IaC) layer.
- 🚀 **Standardized Cosmos DB Naming:** Implemented a new utility to ensure consistent and predictable naming conventions
  for Cosmos DB document store instances.
- 🔑 **Automated Identity Permissions for Cosmos DB:** Enhanced user-assigned identity management to automatically assign
  the necessary roles for secure interaction with Cosmos DB document stores.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.170.0] - 2025-05-26 - Infrastructure Tooling Enhancements

### Added

- 🚀 **New `mirror-image` Makefile Target:** Introduced a utility in `aihub_iac` to easily pull, retag, and push Docker
  images between registries, streamlining image management and distribution for internal consumption.

______________________________________________________________________

## [v0.169.0] - 2025-05-26 - Enhanced DataLakeFile Handling

### Fixed

- 🐛 **Improved DataLakeFile Owner Detection**: Enhanced the logic for determining the owner of a `DataLakeFile` to be
  more robust across different environments. The system now checks the `USER` environment variable (Unix), `USERNAME`
  environment variable (Windows), and falls back to a default `pipeline-user` if no specific user is found, ensuring
  proper ownership assignment in varied execution contexts.

______________________________________________________________________

## [v0.168.0] - 2025-05-24 - Infrastructure Refinements for Enhanced Stability

### Changed

- 🔄 **NATS Container IP Address**: Assigned a fixed private IP address to the NATS container instance in Azure
  deployments. This enhancement improves network stability and predictability for NATS within the infrastructure.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.164.0] - 2025-05-15 - Dependency and Infrastructure Alignment

### Refactor

- 🔄 **Refined Infrastructure Type Definitions:** Updated environment variable argument types in the Azure Container
  Instance module for improved consistency and clarity in infrastructure-as-code deployments.

______________________________________________________________________

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

______________________________________________________________________

## [v0.162.0] - 2025-05-14 - Enhanced Azure Bot Setup for Improved Integration

### Added

- ⚙️ **Azure Bot Setup**: The `setup_azure_bot.py` script now automatically creates a service principal for Azure AD app
  registrations, streamlining the setup process and ensuring smoother integration with Azure resources.

______________________________________________________________________

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

______________________________________________________________________

## [v0.160.0] - 2025-05-13 - Refined Embedding Model Configuration

### Changed

- 🔄 **Enhanced Azure OpenAI Embedding Parameter Handling:** The `dimensions` parameter for Azure OpenAI embeddings now
  robustly supports the `NotGiven` type, enabling more precise control over API requests and aligning better with the
  underlying OpenAI library's parameter conventions.

### Refactor

- 🧹 **Streamlined Embedding Model Configuration:** The `dimensions` parameter has been moved from the generic embedding
  model configuration to specific provider configurations, improving modularity and ensuring parameters are only present
  where relevant.

______________________________________________________________________

## [v0.159.0] - 2025-05-13 - Enhanced LLM Embeddings and Event Query Performance

### Added

- ✨ **Enhanced Embedding LLM Configuration:** Introduced support for specifying the `dimensions` parameter in embedding
  LLM configurations, allowing for more control over the output vector size, particularly for models like
  `text-embedding-3` and later.
- ⚡️ **Improved Event Persistence Querying:** Added a new index on `event_data.created_at` for `PersistedEventEntity`,
  significantly enhancing the performance of time-based queries on persisted event data.

______________________________________________________________________

## [v0.158.0] - 2025-05-12 - Core API Simplifications

### Refactor

- 🧹 **Streamlined Pydantic Model Creation**: Removed redundant `__base__=BaseModel` arguments from `create_model` calls
  in the API event model generation, simplifying the code while maintaining full functionality.

______________________________________________________________________

## [v0.157.0] - 2025-05-08 - Infrastructure Enhancements for WebUI Deployment

### Refactor

- 🧹 **Refined WebUI API Key Configuration**: Explicitly set optional API key fields to `None` by default in
  `OpenWebUIConfig` for improved clarity in infrastructure deployments.
- ⚙️ **Standardized WebUI Container Naming**: Renamed an internal method to `container_app_name` within `WebUIConfig`
  for consistent resource naming conventions.
- 🔗 **Integrated Registry Settings for WebUI**: Added `RegistrySettings` to `WebUIConfig`, allowing for more robust and
  configurable container registry management for WebUI deployments.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.154.0] - 2025-05-08 - Streamlined Versioning and IAC Integration

### Changed

- 🔄 **Automated Versioning Scope**: The `aihub_iac` project has been fully integrated into the automated version tagging
  workflow, ensuring consistent release management and version alignment across all core components.

______________________________________________________________________

## [v0.153.0] - 2025-05-08 - Internal Tooling and CI/CD Scope Expansion

### Changed

- ⚙️ **Expanded Semantic PR Scopes:** Added `iac` (Infrastructure as Code) and `ci-cd` as recognized scopes for semantic
  pull requests, enhancing consistency and automation for relevant contributions.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.148.0] - 2025-04-24 - Enhanced RAG Agent Context Sufficiency

### Changed

- 🦾 Refined **RAG Agent's context handling**: The RAG Agent now provides more precise information to its context
  sufficiency guard regarding the availability of further retrieval attempts (hops), allowing for more informed
  decision-making.
- ⚙️ Improved **Context Sufficiency Guard**: The guard's response structure and internal logic now adapt dynamically
  based on whether more retrieval hops are available. This leads to more accurate reasoning and a tailored output,
  providing clearer indications when the maximum retrieval attempts have been reached or when further queries are still
  possible.

______________________________________________________________________

## [v0.147.0] - 2025-04-24 - Enhanced Azure AI Search Vector Store Configuration

### Added

- ✨ **Configurable Azure AI Search Embedding Dimensions:** Introduced a new `dimensions` parameter for Azure AI Search
  vector stores, allowing users to specify the embedding dimensionality (defaulting to 3072). This feature ensures
  better compatibility and performance by enabling the vector store to precisely match the output dimensions of
  different embedding models used for RAG operations. This enhancement is available through `aihub_lib` and integrated
  into `aihub_pipeline` resources and definitions for seamless configuration.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.138.0] - 2025-04-07 - Core Infrastructure and Testing Improvements

### Changed

- 🚀 **Upgraded Milvus Vector Store Integration:** Updated the `llama-index-vector-stores-milvus` dependency from `0.3.0`
  to `0.6.0`, bringing the latest enhancements and fixes for vector store operations.
- 🧪 **Enhanced Asynchronous Test Stability:** Introduced session-scoped asyncio event loops within test fixtures to
  ensure more reliable and consistent execution of asynchronous tests.
- ⚙️ **Streamlined Local Development Setup:** Refined the NATS service configuration in `docker-compose.yml` by removing
  the health check, which helps optimize the local development environment startup.

______________________________________________________________________

## [v0.137.0] - 2025-04-07 - Core Event System Enhancements

### Changed

- 🔄 **Improved Human-in-the-Loop (HITL) Event Handling:** Enhanced the serialization and deserialization of
  `HumanInTheLoopResponseEvent` within the chat service to ensure proper type information is consistently included,
  leading to more robust and reliable event processing.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.134.0] - 2025-04-01 - Core Component Synchronization

### Changed

- 🔄 **Synchronized Component Versions:** All core microservices (`aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_pipeline`) and the shared `aihub_lib` have been updated to `v0.134.0`, ensuring consistent internal dependency
  alignment across the platform.
- ⚙️ **Makefile Tag Update:** The `Makefile`'s default `TAG` for remote core operations has been updated to `v0.134.0`
  to reflect the new coordinated release version.

______________________________________________________________________

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

______________________________________________________________________

## [v0.132.0] - 2025-04-01 - Improved Chatbot Reliability and User Feedback

### Changed

- 🔄 **Enhanced Chatbot Error Handling:** Standardized and centralized the handling of unexpected errors across all
  chatbot types (Agent and OpenAI, streaming and non-streaming) to provide more consistent user feedback and better
  internal logging.
- ⚡️ **Introduced Response Timeout for Chatbots:** Chatbots now detect and notify users if a response takes an unusually
  long time, preventing indefinite waiting and indicating potential issues.
- 🔗 **Improved Internal Exception Propagation:** Enhanced the system's ability to propagate specific `ExceptionEvent`
  types from core services, allowing for more precise and robust error management within the chatbot framework.

______________________________________________________________________

## [v0.131.0] - 2025-04-01 - Enhanced Markdown Parsing Accuracy

### Fixed

- 🐛 **Markdown Parsing:** Improved the accuracy of Markdown document parsing by automatically unescaping HTML entities,
  ensuring that content extracted from Markdown files is correctly represented without escaped characters.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.128.0] - 2025-03-27 - Improved Embedding Reliability

### Fixed

- 🐛 **Enhanced Embedding Robustness**: Implemented a recursive batch splitting strategy within the embedding process to
  gracefully handle validation errors that might occur during batch embedding generation, improving the reliability of
  vector generation for large inputs.

______________________________________________________________________

## [v0.127.0] - 2025-03-25 - Enhanced Bot Chat Interactions

### Changed

- ⚡️ **Enhanced Typing Indicators**: Implemented continuous and stoppable typing indicators for agent and OpenAI chat
  bots, providing a more responsive and fluid user experience during bot message processing.

______________________________________________________________________

## [v0.126.0] - 2025-03-24 - Enhanced LLM Call Reliability

### Added

- ✨ **Configurable LLM Request Timeout:** Introduced a new `timeout` parameter in `ChatLLMConfig`, enabling users to
  specify a maximum duration for chat-based Large Language Model requests, with a default of 30 seconds.
- ⚙️ **Applied Timeout to Chat LLM Implementations:** The newly added timeout configuration is now actively utilized by
  both **Azure OpenAI** and **Self-Hosted LLM** integrations, providing greater control and improved reliability for API
  call durations.

______________________________________________________________________

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

______________________________________________________________________

## [v0.124.0] - 2025-03-21 - Core Service Refinements and Enhanced Agent Interactions

### Changed

- 🚀 **Streamlined Agent Event Processing:** Relaxed the validation for external agent events, allowing for more flexible
  event distribution to agents without requiring explicit listing within a thread's agent list, enhancing dynamic agent
  interactions.

### Refactor

- 🧹 **Unified Bot Database Structure:** Standardized MongoDB collection names to `bot_conversations` and `bot_paths` and
  unified the database name to `aihub` for the bot service. This improves database organization and consistency across
  services.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.120.0] - 2025-03-20 - Introducing Language Detection for Enhanced Processing

### Added

- ✨ **Introduced Language Detection**: A new utility has been added to automatically detect the language (German,
  English, French, Italian, or other) of user queries using an LLM, enabling more language-aware processing
  capabilities.

### Refactor

- 🧹 **Streamlined IDE Module Configuration**: Optimized internal `.idea` project files to improve module referencing and
  overall development environment setup.

______________________________________________________________________

## [v0.119.0] - 2025-03-19 - API Routing Improvements

### Changed

- 🔄 **Enhanced dynamic route naming for agent event controllers** to incorporate a route postfix, which improves the
  uniqueness and clarity of dynamically generated API endpoints.

______________________________________________________________________

## [v0.118.0] - 2025-03-19 - Improved Event Handling and Core Updates

### Added

- ✨ **Enhanced Event Serialization:** Introduced a new `model_dump_json` method within `BaseEvent` to provide robust
  serialization of event data to JSON strings, ensuring all data, including previously unknown fields, is fully
  preserved.

### Changed

- 🧹 **Refined Event Method Overrides:** Added the `@override` decorator to the `model_dump` method in `BaseEvent` for
  improved code clarity and maintainability.

______________________________________________________________________

## [v0.117.0] - 2025-03-19 - Empowering Custom Workflow Control

### Added

- ✨ **Custom Start and Stop Event Support**: Introduced the ability to define and utilize custom `StartEvent` and
  `StopEvent` types, enabling more tailored and application-specific workflow initiation and termination for agents.
- 🚀 **New Playground Example for Custom Events**: Added a comprehensive playground example (`CustomStartStopEventAgent`)
  that demonstrates how to implement and integrate custom start and stop events into agent workflows, providing a
  practical guide for developers.
- 🧪 **Dedicated Tests for Custom Workflows**: Included new BDD tests to validate the functionality of custom start and
  stop events, ensuring reliability and providing a robust example for extending agent capabilities.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.111.0] - 2025-03-17 - Optimized NATS Message Routing for Display Events

### Changed

- ⚡️ **WebSocketReceiver** now leverages both NATS core and JetStream publishers, routing display events through NATS
  core for enhanced real-time performance and reduced latency.
- 🔄 Updated **API** and **Bot** services to align with the new **WebSocketReceiver** architecture, passing the NATS
  client instance during initialization.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.108.0] - 2025-03-13 - Asynchronous Preconditions for Flexible Workflow Control

### Changed

- ⚡️ **Enhanced Workflow Preconditions**: Step precondition functions (`precondition` argument in `@step` decorator) can
  now be asynchronous (`async def`). This allows for more dynamic and non-blocking checks before a workflow step
  executes, such as waiting for external events or performing asynchronous data lookups.
- 🔄 **Updated Dispatcher Logic**: The internal dispatcher has been updated to correctly handle and await asynchronous
  precondition functions, ensuring seamless integration and execution of the new capability.

______________________________________________________________________

## [v0.107.0] - 2025-03-13 - API Enhancements and Internal Utilities

### Added

- ✨ **Introduced `clear_cache` method for `AgentService`:** A new static method has been added to allow clearing
  in-memory caches used for agent discovery, primarily beneficial for testing purposes to ensure fresh discovery
  requests.

______________________________________________________________________

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

______________________________________________________________________

## [v0.105.0] - 2025-03-11 - Core Component Version Alignment and Documentation Refinement

### Changed

- 🔄 **Component Version Synchronization**: All core components, including **aihub_agent**, **aihub_api**, **aihub_bot**,
  **aihub_lib**, and **aihub_pipeline**, have been updated and synchronized to version `v0.105.0`.
- 📄 **Documentation Formatting**: Minor cosmetic adjustments were made to the Mermaid flowchart syntax within the
  introduction documentation for improved clarity.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.102.0] - 2025-03-07 - Enhanced Document Metadata Handling

### Fixed

- 🐛 **RefDocDocument**: Improved robustness of metadata property access (e.g., `namespace`, `hash`, `uri`, `updated`) by
  transitioning from direct dictionary access to using `.get()` methods with default fallback values, preventing
  potential `KeyError` exceptions for missing metadata.

### Changed

- ⚡️ **RefDocDocument**: Enhanced the **metadata enrichment process** from `DataLakeFile` objects to intelligently
  prioritize existing metadata fields and gracefully fall back to default attributes when populating document properties
  like `namespace`, `hash`, `updated`, `source`, and `document title`.

______________________________________________________________________

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

______________________________________________________________________

## [v0.100.0] - 2025-03-07 - Enhanced Bot Setup and Structural Refinements

### Added

- ✨ **System Message Configuration for Azure Bots:** Introduced the capability to define and store a default
  `system_message` during Azure bot setup, enabling better initial bot personality or instructional guidance. This
  message is now saved to the connected MongoDB or Cosmos DB instance.

### Refactor

- 🧹 **Relocated Azure Bot Setup Script:** The `setup_azure_bot.py` script has been moved into its own dedicated
  subdirectory (`aihub_bot/aihub_bot/`), improving the overall organization and clarity of the bot module.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.97.0] - 2025-03-06 - LLM Configuration Enhancements

### Added

- ✨ **Enhanced LLM System Prompt Control:** The `cost_reporting_llm` context manager in `ChatLLMConfig` now supports an
  optional `system_prompt` parameter, allowing for direct configuration of system messages for Large Language Models
  within cost-tracked sessions.

______________________________________________________________________

## [v0.96.0] - 2025-03-06 - Enhanced Bot Message Handling

### Fixed

- 🐛 **Improved Bot Message Sending:** The bot service now gracefully handles empty message buffers, preventing
  unnecessary activity updates and enhancing the reliability of message delivery.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.93.0] - 2025-03-05 - Core Component Version Alignment

### Changed

- 🔄 **Component Version Synchronization**: Updated the project version and internal `aihub_lib` dependency tags across
  all `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_lib`, and `aihub_pipeline` components to `v0.93.0` to ensure full
  system compatibility and release alignment.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.89.0] - 2025-03-03 - Enhanced Agent Dispatching with Idempotency

### Added

- ✨ **Introduced Idempotent Agent Step Execution:** Agent steps now include a robust mechanism to prevent duplicate
  executions within the same run when called with identical input events. This significantly enhances the reliability
  and efficiency of agent dispatching by avoiding redundant processing.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.86.0] - 2025-03-03 - Streamlined Bot Services

### Refactor

- 🧹 **Refined Bot System Message Retrieval:** Removed redundant calls to `get_system_message` from `StreamAgentChatBot`,
  `OpenaiChatBot`, and `StreamOpenaiChatBot` to centralize and simplify how system messages are handled within bot
  services.

______________________________________________________________________

## [v0.85.0] - 2025-02-28 - Core Component Alignment and API Refinements

### Changed

- 🔄 **Updated Core Component Versions**: Synchronized the versions of `aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_lib`, and `aihub_pipeline` to `v0.85.0` for consistent deployment and development.
- 📄 **Enhanced Document Intelligence Loader**: Adapted the **Document Intelligence Loader** to align with the latest API
  specifications by updating the parameter name from `analyze_request` to `body` for improved compatibility.

______________________________________________________________________

## [v0.84.0] - 2025-02-28 - Minor Refinements and Event Stream Optimization

### Removed

- 🗑️ **Removed `LimitChatHistoryWithContextEvent`:** The event previously used for explicitly limiting chat messages and
  context within the `FewShotAgent` has been removed.

______________________________________________________________________

## [v0.83.0] - 2025-02-27 - Core Performance and Stability Improvements

### Changed

- ⚡️ **Optimized NATS JetStream Storage:** Switched the default storage type for all NATS JetStream Key-Value stores
  (including run and thread contexts) and general streams from file-based (`FILE`) to in-memory (`MEMORY`). This change
  significantly enhances performance and responsiveness of context and stream operations.
- ⚙️ **Enhanced KV Store Creation Robustness:** Improved the error handling for Key-Value store creation, ensuring that
  the system more gracefully attempts to retrieve an existing store if creation fails, leading to increased stability.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.80.0] - 2025-02-27 - Enhanced Localization Capabilities

### Changed

- 🌍 **Improved Internationalization (i18n)**: The `LocaleHandler` now supports passing additional arguments for dynamic
  content interpolation within translated strings, enabling more flexible and context-aware localized messages.

______________________________________________________________________

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

______________________________________________________________________

## [v0.78.0] - 2025-02-27 - Streamlined Azure AI Search Configuration

### Changed

- ⚡️ **Simplified Azure AI Search Vector Store Creation:** The `create_azure_ai_search_vector_store` function now
  utilizes a default value for `semantic_configuration_name`, which streamlines the configuration process and simplifies
  the internal logic for setting up Azure AI Search vector stores.

______________________________________________________________________

## [v0.77.0] - 2025-02-26 - Enhanced Message Processing Reliability

### Refactor

- ⚡️ **Improved NATS JetStream Message Acknowledgment:** Refactored the `JSSubscriber` to acknowledge messages
  immediately upon receipt, preventing re-delivery of messages if subsequent processing tasks encounter issues. This
  enhances the reliability and predictability of message consumption.

______________________________________________________________________

## [v0.76.0] - 2025-02-26 - NATS Message Processing Refinement

### Changed

- 🔄 **Adjusted NATS JetStream Acknowledgment Logic:** The order of message acknowledgment has been updated in the
  `JSSubscriber` to occur *before* the message handler is executed. This change optimizes message flow and prevents
  potential re-delivery of messages in scenarios where the handler might encounter an error after initial processing has
  begun.

______________________________________________________________________

## [v0.75.0] - 2025-02-26 - Enhanced Asynchronous NATS Message Processing

### Changed

- ⚡️ **Improved NATS JetStream Message Processing:** The `JSSubscriber` now handles incoming messages asynchronously by
  creating a separate task for each message. This prevents the main message loop from being blocked by slow handlers,
  significantly enhancing concurrency and system resilience.
- 🚀 **Optimized NATS Core Message Handling:** The `NCSubscriber` has been updated to process incoming messages in a
  non-blocking fashion. This change ensures that message handling is more robust and efficient, improving overall system
  responsiveness.

______________________________________________________________________

## [v0.74.0] - 2025-02-26 - Enhanced Document Metadata Handling

### Fixed

- 🐛 **Corrected Document Title Extraction:** Ensured that the document title is accurately extracted from the
  **DataLakeFile** URI when enriching **RefDocDocument** metadata, preventing incorrect title assignments.

______________________________________________________________________

## [v0.73.0] - 2025-02-26 - Core Stability Enhancements and Version Alignment

### Fixed

- 🐛 **WebSocket Message Handling:** Enhanced robustness of the `WebSocketReceiver` to gracefully handle cases where a
  start event might not contain a `messages` attribute, preventing potential runtime errors.

### Changed

- 🔄 **Project-wide Version Bump:** Aligned all core microservices and internal dependencies to version `v0.73.0` for
  consistent build and deployment.

______________________________________________________________________

## [v0.72.0] - 2025-02-26 - Enhanced Document Metadata for RAG

### Added

- ✨ **Enriched `RefDocDocument` Metadata**: Improved document processing in the pipeline by automatically extracting and
  adding the **document title** and **source URI** to `RefDocDocument` instances. This enhancement provides richer, more
  granular context for Retrieval-Augmented Generation (RAG) applications.

______________________________________________________________________

## [v0.71.0] - 2025-02-26 - Improved Self-Hosted LLM Compatibility

### Changed

- ⚙️ **Enhanced Self-Hosted LLM Tokenizer Compatibility:** Updated the self-hosted LLM configuration to correctly infer
  base model names by stripping additional suffixes (`-bnb` and `-4bit`), improving compatibility with various quantized
  model formats for tokenization.

______________________________________________________________________

## [v0.70.0] - 2025-02-26 - Expanded Azure OpenAI Authentication Options

### Changed

- 🔑 **Enhanced Azure OpenAI LLM Authentication:** Enabled direct API key authentication for **Azure OpenAI Large
  Language Models**, providing a flexible alternative to Azure AD for resource access.

______________________________________________________________________

## [v0.69.0] - 2025-02-25 - Enhanced Build Stability and CI Efficiency

### Changed

- ⚡️ **Optimized CI Workflow:** Reordered Python and Poetry setup steps and introduced Poetry caching in the
  `add-tag.yml` GitHub Actions workflow to significantly improve build times and efficiency.
- 🦾 **Strengthened Dependency Management in CI:** Added explicit `poetry lock` and `poetry install` steps to GitHub
  Actions workflows, ensuring consistent and reliable dependency resolution and installation across all CI runs.
- 🧹 **Streamlined Build Dependencies:** Removed direct `pip install` commands for global tools like `tomlkit` in CI, now
  relying entirely on Poetry for comprehensive dependency management.

______________________________________________________________________

## [v0.68.0] - 2025-02-25 - Enhanced Self-Hosted LLM Configuration

### Changed

- ⚡️ **Improved Self-Hosted LLM Tokenizer Loading:** Enhanced the `tokenizer` property within `SelfHostedLLMConfig` to
  correctly load tokenizers for various self-hosted models by stripping common suffixes (like `-GGUF` and `-AWQ`) from
  model names and ensuring the proper encoding function is returned.

______________________________________________________________________

## [v0.67.0] - 2025-02-25 - Build System Enhancements and Poetry Integration

### Refactor

- 🧹 **Renamed Dependency Management Script:** The script for switching between local and remote cores has been renamed
  from `switch_dependency.py` to `switch_dependencies.py` for improved clarity.
- ⚡️ **Poetry Integration for Development Scripts:** Updated Makefile commands to utilize `poetry run` for executing
  core dependency switching scripts, streamlining the development workflow and aligning with Poetry's project management
  practices.

______________________________________________________________________

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

______________________________________________________________________

## [v0.65.0] - 2025-02-25 - Core Agent LLM Flexibility

### Changed

- 🔄 **Enhanced LLMWrappingAgent Configuration:** The `LLMWrappingAgentConfig` has been updated to use the more generic
  `ChatLLMConfig` instead of the provider-specific `AzureOpenAILLMConfig`. This modification provides greater
  flexibility, enabling the LLM Wrapping Agent to integrate seamlessly with a broader range of chat LLM providers.

______________________________________________________________________

## [v0.64.0] - 2025-02-24 - Improved Core Robustness and System Alignment

### Fixed

- 🐛 **Enhanced Locale Handling:** Ensured that the system's locale context reliably defaults to a predefined value when
  no specific locale is provided, improving overall stability and preventing potential issues.

______________________________________________________________________

## [v0.63.0] - 2025-02-21 - Refined Guards and Enhanced Testability

### Changed

- 🔄 **Improved Few-Shot Guard Prompting:** The `Few-Shot Guard` has been updated with a refined internal prompt that
  strictly enforces JSON-formatted output for guard responses, enhancing their reliability and programmatic parsing.
- ⚡️ **Enhanced `AgentTestRunner`:** The `get_events` and `get_events_of_type` methods in `AgentTestRunner` now support
  an `event_filter` parameter, allowing for more granular observation and testing of events based on their specific
  event type.

______________________________________________________________________

## [v0.62.0] - 2025-02-20 - Streamlined Development and Enhanced CI/CD

### Changed

- 🚀 **Improved CI/CD Stability**: The Docker service health check in the backend test action has been reordered to occur
  after Python dependency installation, enhancing the reliability of automated tests.
- ✨ **Simplified NoAuth Configuration**: The `NoAuthHandler` now provides default values for user `NAME`, `EMAIL`, and
  `ROLES`, reducing the need for explicit configuration in local development environments.

______________________________________________________________________

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

______________________________________________________________________

## [v0.60.0] - 2025-02-20 - Build Action Configuration Update

### Changed

- 🔄 **Adjusted `build_image` GitHub Action:** The `file` input for the `build_image` action no longer has a default
  value. This change requires users to explicitly specify the Dockerfile path, promoting clearer and more explicit build
  configurations.

______________________________________________________________________

## [v0.59.0] - 2025-02-20 - Minor Infrastructure Enhancements

### Changed

- 🛠️ **Improved Backend Testing Visibility:** Added `docker compose ps` command to the backend test action, providing
  better insights into service health during automated testing workflows.
- 🔄 **Updated LLM Inference Server:** Upgraded the `llama.cpp` Docker image to the latest `server` tag, ensuring access
  to the most recent optimizations and features from the underlying LLM inference backend.

______________________________________________________________________

## [v0.58.0] - 2025-02-20 - Enhanced Image Building Flexibility

### Added

- ✨ **Improved `build_image` GitHub Action:** The `build_image` action now supports specifying a custom `Dockerfile`
  path via a new `file` input, providing greater flexibility for projects with non-standard Dockerfile locations.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.52.0] - 2025-02-19 - Bot Reliability and Code Clarity Improvements

### Fixed

- 🐛 **Improved Conversation Message Retrieval:** Enhanced the conversation message retrieval mechanism to consistently
  return a list, ensuring more robust handling of conversation history within the bot service.

### Refactor

- 🧹 **Refined Conversation Entity Type Hinting:** Updated internal type hints for conversation message access, providing
  a more accurate representation of the data structure and improving code clarity.

______________________________________________________________________

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

______________________________________________________________________

## [v0.50.0] - 2025-02-19 - Smarter Slack Bot Responses in Channels

### Changed

- 🤖 **Improved Slack Channel Interaction**: Bots, including both Agent and OpenAI variants, now intelligently respond in
  Slack channels only when explicitly mentioned. This change significantly enhances bot etiquette by preventing
  unnecessary responses in shared conversations.

### Added

- ✨ **Introduced Slack Interaction Utilities**: New helper functions, `is_slack_channel_message` and `is_bot_mentioned`,
  have been added to accurately detect Slack channel messages and identify when the bot is mentioned. These utilities
  are crucial for enabling the new, more selective response behavior in Slack.

______________________________________________________________________

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

______________________________________________________________________

## [v0.48.0] - 2025-02-19 - Enhanced Test Stability and Build System Updates

### Changed

- 🚀 Updated the **SonarCloud scan GitHub Action** to v5, improving the CI/CD pipeline's analysis capabilities and
  ensuring compatibility with the latest SonarCloud features.

### Fixed

- 🐛 Improved **chatbot test stability** by significantly extending timeouts for asynchronous operations, which helps
  prevent flaky test failures related to health checks and streaming response validations.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.45.0] - 2025-02-17 - Internal Workflow Enhancements

### Changed

- 🔄 **Updated CI/CD Dependency Locking:** The GitHub Actions workflow now utilizes `poetry lock` instead of
  `poetry lock --no-update` for dependency management, ensuring more current dependency resolution during build
  processes.

______________________________________________________________________

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

______________________________________________________________________

## [v0.43.0] - 2025-02-17 - Core Tooling and Build System Enhancements

### Changed

- 🚀 **Updated Poetry Version:** Upgraded the Poetry dependency management tool in GitHub Actions workflows from v1.8.3
  to v2.1.1, ensuring compatibility with the latest features and improved build processes.
- ⚙️ **Refined Poetry Core Requirements:** Standardized and updated the `poetry-core` build system requirements across
  all `pyproject.toml` files to `>=2.0.0,<3.0.0`, enhancing build stability and future compatibility.

______________________________________________________________________

## [v0.42.0] - 2025-02-17 - Internal API Refinement

### Refactor

- 🧹 **Updated Node Post-processing**: Renamed the `process` method to `postprocess_nodes` within
  `ScoreScalerPostProcessor` for better clarity and consistency in node manipulation utilities.

______________________________________________________________________

## [v0.41.0] - 2025-02-17 - Enhanced Azure AI Search Capabilities

### Added

- ✨ **Expanded Azure AI Search Configuration:** Introduced the ability to specify a `semantic_configuration_name` when
  creating Azure AI Search vector stores, providing more control over semantic search behavior and relevance tuning.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.38.0] - 2025-02-13 - Bot Stability and OpenAI Integration Enhancements

### Fixed

- 🐛 **Improved Robustness for Chat Roles**: Ensured that chat message roles default to "user" if not explicitly
  provided, preventing potential issues with `None` values in bot interactions.
- ⚡️ **Enhanced OpenAI Streaming Reliability**: Added robust error handling for OpenAI chat completions, ensuring the
  stream continues smoothly even if content chunks are empty or null.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.31.0] - 2025-02-07 - Enhanced Tracing Authentication

### Added

- ✨ **Introduced Phoenix Tracing Authentication**: Added support for configuring and using a `PHOENIX_AUTH_TOKEN` to
  authenticate tracing data sent to the Phoenix endpoint, enhancing the security and control over your observability
  data.

______________________________________________________________________

## [v0.30.0] - 2025-02-07 - Improved Chat Event Handling

### Changed

- 🔄 **Streamlined User Message Event Creation:** Simplified the construction of `UserMessageEvent` within the
  `ChatService` by directly providing the full list of messages, enhancing consistency and streamlining how user message
  events are handled.

______________________________________________________________________

## [v0.29.0] - 2025-02-07 - Enhanced Bot Connectivity and Development Workflow

### Changed

- ⚡️ **Improved NATS Connectivity for Bots:** The `aihub_bot` now dynamically retrieves its NATS endpoint from
  `NatsConfig`, enhancing deployment flexibility and making the connection environment-agnostic.
- 📄 **Updated Semantic PR Workflow:** Added `bots` as a recognized type in the semantic PR workflow, standardizing and
  streamlining the development process for bot-related contributions.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.24.0] - 2025-02-06 - Core Module Synchronization and CI/CD Enhancements

### Changed

- ✨ **Synchronized Core Module Versions**: All `aihub` core modules (`aihub_agent`, `aihub_api`, `aihub_bot`,
  `aihub_lib`, `aihub_pipeline`) and their internal `aihub_lib` dependencies have been consistently updated to
  `v0.24.0`, ensuring full compatibility and alignment across the ecosystem.

### Refactor

- 🧹 **Streamlined CI/CD Test Workflow**: The GitHub Actions test workflow now references the `test_backend` action
  locally within the repository, improving build reliability and simplifying the continuous integration setup.

______________________________________________________________________

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

______________________________________________________________________

## [v0.22.0] - 2025-02-04 - Internal System Alignment and Workflow Stabilization

### Changed

- 🔄 **Updated Core Dependency Versions:** Synchronized all core modules (aihub_agent, aihub_api, aihub_pipeline) to
  utilize the latest `v0.22.0` release of `aihub_lib`, ensuring consistent functionality and compatibility across the
  system.
- ⚙️ **Refined CI/CD Workflow References:** Updated GitHub Actions workflows (analyze, lint, review) to reference the
  stable `main` branch of AIHub Core actions, enhancing the reliability and consistency of automated checks.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.19.0] - 2025-01-31 - Core Component Release Synchronization

### Changed

- 🔄 **Component Version Alignment:** All core components, including `aihub_agent`, `aihub_api`, `aihub_lib`, and
  `aihub_pipeline`, have been synchronized and updated to version `v0.19.0`. This ensures all projects utilize the
  latest features and improvements from `aihub_lib`.

______________________________________________________________________

## [v0.18.0] - 2025-01-31 - Refined Release Workflow

### Refactor

- 🧹 **Improved Release Tagging Workflow:** Reordered the SSH key cleanup step in the GitHub Actions workflow to ensure
  it executes consistently after all tagging operations, enhancing the robustness of the release process.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.15.0] - 2025-01-21 - Workflow Refinements

### Changed

- ⚙️ **CI/CD Workflow Stability:** Enhanced the Pytest coverage comment job within pull requests to ensure it
  exclusively triggers on pull request events, improving workflow reliability.

______________________________________________________________________

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

______________________________________________________________________

## [v0.13.0] - 2025-01-17 - Enhanced Workflow Observability and Type System Robustness

### Added

- ✨ **Enhanced Step Debugging Capabilities**: Introduced comprehensive debug logging for workflow steps, providing more
  detailed insights into their configuration and event mappings for easier troubleshooting.
- ⚡️ **Enabled Logging in Playground Example**: Activated logging within a minimal workflow example to assist with
  debugging and understanding runtime behavior.

### Refactor

- 🧹 **Improved Type Extraction for Fixed-Size Lists**: Refactored the internal mechanism for extracting item types from
  `FixedList` annotations, leading to more robust and explicit type handling within the workflow system.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.10.0] - 2025-01-16 - Introducing Robust Branch Protection Policies

### Added

- 🛡️ **Implemented Comprehensive Branch Protection Policies:** New documentation has been added to the README, detailing
  robust branch protection rules for `main` and `initiative` branches. These rules enforce restricted direct pushes,
  prevent deletions and force pushes, require a linear commit history, and mandate pull requests with specific approval
  processes (including squashed merges), significantly enhancing codebase stability and integrity.

______________________________________________________________________

## [v0.9.0] - 2025-01-16 - Enhanced Windows Setup Documentation

### Added

- 📄 **Improved Windows Setup Guide**: Added specific instructions for installing and verifying `make` on Windows,
  streamlining the prerequisite setup for Windows users.

______________________________________________________________________

## [v0.8.0] - 2025-01-15 - Documentation Enhancements and Version Update

### Changed

- 📄 **Improved Docker Setup Guide:** Added troubleshooting information and a helpful resource link in the `README.md` to
  assist users with common Docker Desktop WSL update issues during setup.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## [v0.2.0] - 2025-01-07 - Enhanced Context Understanding and Pipeline Alignment

### Changed

- 📄 **Documentation Clarity**: Clarified the behavior of **RunContext** during Human-in-the-Loop (HITL) pauses,
  emphasizing that it remains open to preserve agent state.
- 🔄 **Context Utilization**: Updated documentation to reflect that both **RunContext** and **ThreadContext** can be
  leveraged for maintaining agent state during HITL steps.

### Refactor

- 🧹 **Dependency Management**: Transitioned **aihub_pipeline**'s dependency on **aihub_lib** from a local path to a
  direct Git repository reference, streamlining module integration and future releases.

______________________________________________________________________
