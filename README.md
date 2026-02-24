---
title: Introduction
index: 1
---

# AI-Hub Developer Guide

## 1. :rocket: Introduction

### What is the Swiss AI-Hub?

::: info
The Swiss AI-Hub is a comprehensive, enterprise-grade platform designed to integrate artificial intelligence into the
core of your business. It addresses a critical need in the Swiss market for a sovereign, trustworthy, and collaborative
AI platform.
:::

Most available AI tools are frameworks or libraries, which are excellent for proofs-of-concept but leave the user with
the immense challenge of building a secure, scalable, and maintainable enterprise-ready system. The Swiss AI-Hub fills
this gap by providing a complete, production-grade ecosystem for Swiss companies to succeed with AI, not just another
agentic framework. It is a foundational software framework that serves as a bridge between people, enterprise knowledge,
and digital processes. A core principle of the Hub is to bring specialized intelligence directly into familiar work
environments, rather than forcing employees to switch between special applications for AI support.

### Our Goal: An Enterprise-Grade Platform, Not Just a Library

The distinction between a library and a platform is central to our vision. While a library helps you solve a specific
problem, a platform provides the entire environment to solve problems at scale, reliably, and over the long term.

::: tip :battery: Batteries Included!
The Swiss AI-Hub is a "batteries-included" platform for developers. It provides a full-fledged enterprise architecture,
including:

- A database layer
- A REST API and WebSocket gateway
- A user interface
- Scalable data ingestion pipelines
- Pre-configured Docker containers for deployment
:::

This allows developers to focus on creating business value by designing an agent's logic, while the platform handles
security, scalability, and infrastructure.

### Core Philosophy: The "Swiss Way"

Our architecture is built on a set of non-negotiable principles that reflect the values of the companies we serve.

::: warning :shield: Non-Negotiable Principles
- **Privacy and Sovereignty by Design**: The platform is designed to be fully self-hostable, allowing the entire
  technology stack to run on-premises or in a Swiss cloud. This guarantees complete data sovereignty, ensuring sensitive
  company data remains in Switzerland and is subject to Swiss regulations.
- **Security as a Prerequisite**: Security is built into every layer of the architecture, from a secure development
  lifecycle to granular access control and support for enterprise authentication like OAuth and LDAP. It is a principle
  that informs every architectural decision, not an add-on.
- **Radical Transparency and Auditability**: We believe trust is earned through transparency. Our "AI Agents as
  Workflows" philosophy ensures that agent behavior is not a "black box". Agents and assistants are built as structured,
  step-by-step workflows, making them inherently transparent and testable. Every step can be visually monitored and
  audited using tools like Langfuse Tracing, which is crucial for gaining the trust of employees, managers, and
  regulators.
:::

### The Vision: From Assistants to Autonomous Agents

The AI-Hub is designed to grow with an organization, supporting an evolutionary journey from simple assistance to
autonomous process automation. It enables the creation of a rich ecosystem of specialized AI solutions that collaborate
with your team.

::: details :robot: AI Assistants: Your AI-Powered Co-Worker    
For employees, the AI-Hub provides secure access to specialized AI Assistants tailored to your team's needs. Unlike
generic chatbots, these assistants are valuable because they are integrated with relevant business data and tools. They
are reactive, context-aware partners designed to enhance your daily work by answering complex questions, analyzing data,
and saving you time and effort.
:::

::: details :gear: AI Agents: Autonomous Process Partners    
As an organization advances, the platform enables collaboration with AI Agents—autonomous partners that proactively
participate in business processes. Instead of simply reacting to prompts, these agents are designed to analyze
workflows, autonomously determine the next steps, and execute tasks with minimal human intervention. This reimagines
workflows as a deep collaboration between humans and AI, allowing employees to focus on the most critical and creative
aspects of their jobs while maintaining oversight for key decisions.
:::

______________________________________________________________________

## 2. :file_folder: Project Structure & Repositories

The Swiss AI-Hub is designed as a powerful, cohesive ecosystem. Its structure is not just a technical choice; it is a
reflection of our vision to provide a platform that is both ready-to-use and infinitely extensible.

### Repository Types: Core vs. Customer

The ecosystem is organized into two fundamental types of repositories to ensure a clean separation of concerns and
foster collaboration without risking data leakage.

::: danger :warning: Critical Separation
- **Core Repository (`aihub-core`)**: This is the heart of the platform. It contains all the shared, reusable
  functionality and code that powers the AI-Hub. Under no circumstances should it contain any customer-specific
  information. This strict separation is critical, as `aihub-core` is referenced as a dependency by all
  customer-specific projects.
- **Customer Repositories (`aihub-<CUSTOMER>`)**: These repositories are where you bring the Hub to life for a specific
  context. They build on the powerful foundation of `aihub-core`, allowing you to add or override components—like
  agents, pipelines, or processes—for a specific customer's needs.
:::

### An Architecture for Speed and Extensibility

To a developer, the AI-Hub is an entire "batteries-included" platform, not just a library. The monorepo contains
multiple, distinct Python packages called "scopes," which are organized into logical layers. This architecture is
designed to let you focus on creating business value, while we handle the heavy lifting of infrastructure, security, and
scalability.

::: details :building_construction: The Foundational & Logic Layers
At the lowest level is **`aihub_lib`**, the foundational shared library for code used by more than one service. Building
on this, we provide a base layer for the core AI components:

- **`aihub_pipeline`**: Contains definitions for data ingestion and processing pipelines, often using Dagster.
- **`aihub_agents`**: Contains all agent-specific logic and workflow definitions.
- **`aihub_process`**: Orchestrates high-level business processes that involve collaboration between agents, humans, and
  external programs.
:::

::: details :electric_plug: The Integration & Interaction Layer
This layer provides a full-stack experience for interacting with the core logic.

- **`aihub_api`**: The main user-facing REST API and WebSocket gateway, built with FastAPI.
- **`aihub_web`**: The complete frontend application, built with Nuxt.js, providing the user interface.
- **`aihub_bot`**: The core logic for integrating with collaboration platforms like MS Teams.
:::

::: details :toolbox: The Operational & Best Practices Layer
We provide tools to ensure your solutions are robust, maintainable, and easy to deploy.

- **`aihub_action`**: Contains reusable GitHub Actions to standardize CI/CD pipelines and avoid duplication.
- **`aihub_doc`**: Holds all project documentation, including arc42 and Architectural Decision Records (ADRs).
:::

### Use It Out-of-the-Box or Make It Your Own

::: tip :package: Instant Start
This architecture gives you incredible flexibility. You can use the Hub as-is by simply running the`docker-compose.yaml`
to get a fully working, locally running AI-Hub complete with pre-built standard agents, pipelines, and processes ready
to go.
:::

::: info :sparkles: The Magic of Extension
Or, you can extend it. This is where the magic happens. When you build your own components, you build on the same
battle-tested base that we do. Create a new agent, a new pipeline, or a new process, package it as a Docker image, and
add it to the `docker-compose.yaml`. Instantly, your creation becomes a first-class citizen in the ecosystem. You will
see all our platform-level features work for your component automatically, out-of-the-box:

- **Automatic Observability**: Your new agent will immediately appear in the **`aihub_web`** UI, where it can be managed
  and observed.
- **Built-in Traceability**: Every run of your agent is automatically traced and can be audited visually in Langfuse
  without any extra work.
- **Seamless Interaction**: Your agent can be invoked from the chat interface and can use our built-in protocols to
  interact with other agents in the Hub.
- **Process Integration**: You can immediately employ your new agent as a step within a larger, more complex agentic
  process using **`aihub_process`**.

Want to build a new pipeline in **`aihub_pipeline`** that ingests and feeds data into an existing, perfected RAG-Agent
we already provide? You can. The Hub is designed for this kind of powerful, modular composition. You focus on the unique
logic, and the platform handles the rest.
:::

______________________________________________________________________

## 3.:computer: Getting Started: Local Development Setup

This chapter outlines the technologies used in the AI-Hub and the necessary steps to set up the development environment
from the command line. It is up to the developer to install the required tools according to their operating system and
preferences.

### Required Technologies

::: details :wrench: Complete Technology Stack    
The AI-Hub project utilizes the following technologies. Ensure they are installed and accessible from your command line
environment.

- **Git**: For version control.
- **Python**: The project is built on Python, specifically version 3.13.
- **uv**: For dependency management and managing virtual environments across the monorepo workspace.
- **make**: Used for running common tasks and commands defined in Makefiles.
- **Docker & Docker Compose**: For containerizing and running the project's infrastructure stack.
- **Node.js**: The LTS version is used for frontend development, managed via a version manager like NVM.
- **pnpm**: Fast package manager for node.js.
- **Other Tools**: For specific tasks, developers may also need tools like **Postman** for API testing, **MongoDB
  Compass** for database management, and the **Bot Framework Emulator** for testing chatbots.
:::

#### :robot: AI & LLM Orchestration

Our AI capabilities are primarily powered by the LlamaIndex ecosystem and integrations with leading AI providers.

- **LlamaIndex**: The central framework for building context-aware RAG (Retrieval-Augmented Generation) applications.
  This includes `llama-index-core`, along with various integrations for vector stores, embeddings, and LLMs.
- **LLM & Embedding Providers**:
  - **OpenAI & Azure OpenAI**: Integrated via the `openai`, `llama-index-llms-openai-like`, and
    `llama-index-embeddings-azure-openai` libraries.
  - **Google GenAI**: Support for Google's models through `google-genai` and `llama-index-llms-google-genai`.
  - **Hugging Face**: Using `transformers` and `llama-index-embeddings-text-embeddings-inference` for local or
    self-hosted models.
- **Azure AI Services**: We make extensive use of Azure's managed AI services, including:
  - **Azure Cognitive Search**: For powerful search and retrieval capabilities.
  - **Azure Document Intelligence**: For document analysis and information extraction.
  - **Azure Speech Services**: For speech-to-text and other speech-related features.

#### :floppy_disk: Data & Storage

- **Databases**:
  - **FerretDB**: Used as our primary MongoDB-compatible NoSQL database, accessed via **MongoEngine** and integrated
    into LlamaIndex for document storage (`llama-index-storage-docstore-mongodb`). Provides MongoDB compatibility while
    using PostgreSQL as the backend.
  - **Valkey**: For in-memory caching and fast data retrieval. A Redis-compatible fork providing high-performance
    key-value storage.
- **Vector Stores**:
  - **Azure AI Search**: The primary vector store for our production environment (
    `llama-index-vector-stores-azureaisearch`).
  - **Milvus**: An alternative or additional vector database option (`llama-index-vector-stores-milvus`).
- **File Storage**:
  - **SeaweedFS**: S3-compatible distributed file system for local and cloud storage, providing scalable object storage.
  - **Azure Data Lake Storage (ADLS)**: Managed through `azure-storage-file-datalake` and `adlfs` for large-scale data
    storage and access.

#### :satellite: Observability & Communication

- **Monitoring**: We use a combination of tools for comprehensive application monitoring:
  - **OpenTelemetry**: The foundational toolkit for generating and exporting telemetry data (traces, metrics, logs).
  - **OpenInference**: A specialized instrumentation library for monitoring LLM applications built with LlamaIndex.
  - **Langfuse**: For LLM observability, tracing, and model performance evaluation.
- **Asynchronous Messaging**:
  - **NATS**: Used for high-performance, asynchronous communication between services.

#### :sparkles: Code Quality & Tooling

We enforce strict standards to ensure our code is clean, consistent, and bug-free.

- **Linting & Formatting**:
  - **Ruff**: Our primary linter for speed and comprehensive checks.
  - **Black**: For uncompromising and consistent code formatting.
- **Type Checking**:
  - **MyPy**: Used in `strict` mode to enforce static type safety across the entire codebase.
- **Testing**:
  - **Pytest**: The core framework for writing and running our tests, along with `pytest-asyncio` for asynchronous code
    and `pytest-mock` for mocking.
  - **Pytest BDD**: For writing behavior-driven tests.

### :gear: Codebase & Dependency Setup

#### Clone Repositories

::: info
First, clone the necessary repositories into your local workspace.

- **aihub-core** (this repo): `git clone https://github.com/bbvch-ai/aihub-core`
:::

#### Install Project Dependencies

The project is a monorepo containing multiple packages ("scopes"), such as `aihub_agent` or `aihub_api`, managed as a uv
workspace with a single lockfile at the root.

::: warning :warning: Important
To install all dependencies across the workspace:

1. From the repository root, run: `uv sync --all-packages`
2. This creates a single `.venv` at the root with all packages installed.
3. Run scope-specific commands from within each scope directory using `make` targets (which use `uv run` internally).
:::

For frontend services (`aihub_web`), follow the setup instructions in that directory's `README.md` file.

#### Manage Dependencies with uv

::: tip :package: uv Commands
Use the following commands to manage dependencies. The workspace uses a single `uv.lock` at the root.

- `uv sync --all-packages`: Installs all dependencies from the lockfile.
- `uv add <package>`: Adds a new package as a dependency (run from the scope directory).
- `uv remove <package>`: Removes a package (run from the scope directory).
- `uv lock --upgrade`: Updates all dependencies to their latest allowed versions.
:::

### :whale: Starting the Infrastructure Stack (Docker)

To run the full AI-Hub stack locally, use Docker Compose to start the required services. Several configuration files are
provided for different environments. Run the appropriate command from the root of the `aihub-core` repository:

::: tip :whale: Choose Your Environment
**For a CPU Environment**:

```bash
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

**For a GPU Environment**:

```bash
docker compose -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml -f docker-compose-gpu.yml up -d
```
:::

::: warning :clock3: Wait for Health Check
Wait for all services to become healthy (you can check with `docker ps`) before proceeding.
:::

### :house: Running the AI-Hub Locally

::: warning :warning: Important
Only use self-signed SSL certificates for local development. Never use them in production or public environments.
:::

For local development with SSL support and custom domain routing, we provide two deployment options:

#### Option 1: Using Pre-built Images (Recommended for Testing)

Use `docker-compose.local.yml` to run with pre-built images from the registry:

**Prerequisites:**

1. **mkcert**: Install mkcert for generating local SSL certificates

   - **Linux (Ubuntu/Debian)**:
     ```bash
     sudo apt install libnss3-tools
     wget -O mkcert https://dl.filippo.io/mkcert/latest?for=linux/amd64
     chmod +x mkcert
     sudo mv mkcert /usr/local/bin/
     ```
   - **Windows**:
     ```powershell
     # Using Chocolatey
     choco install mkcert

     # Using Scoop
     scoop bucket add extras
     scoop install mkcert
     ```
   - **macOS**:
     ```bash
     brew install mkcert
     ```

2. **Generate SSL Certificates**:

   ```bash
   make local-cert
   ```

3. **Environment Configuration**:

   - Copy `.env.dev` to `.env` and configure with your settings
   - The default domain `127.0.0.1.nip.io` provides wildcard DNS resolution to localhost

**Start the Stack:**

```bash
# Start all services with pre-built images
docker compose -f docker-compose.local.yml up -d

# Check service health
docker compose -f docker-compose.local.yml ps
```

#### Option 2: Building from Source (For Development)

Use `docker-compose.build.yml` to build images from source code:

**Prerequisites:**

Same as Option 1, plus ensure you have cloned the repository and have the required build tools.

**Start the Stack:**

```bash
# Build and start all services from source
docker compose -f docker-compose.build.yml up -d --build

# Check service health
docker compose -f docker-compose.build.yml ps
```

::: tip :bulb: When to Use Which Option
- **Pre-built images** (`docker-compose.local.yml`): Fast startup, testing platform features, no code changes needed
- **Build from source** (`docker-compose.build.yml`): Active development, testing code changes, debugging
:::

#### Access Points

Once running, access the AI-Hub services at:

- **Main Web Interface**: https://127.0.0.1.nip.io
- **OpenWebUI**: https://openwebui.127.0.0.1.nip.io
- **Keycloak Admin**: http://localhost:8180 (admin / admin)
- **LiteLLM**: https://litellm.127.0.0.1.nip.io
- **Dagster**: https://dagster.127.0.0.1.nip.io
- **SeaweedFS Console**: https://datalake.127.0.0.1.nip.io
- **Attu (Milvus UI)**: https://attu.127.0.0.1.nip.io
- **Traefik Dashboard**: https://traefik.localhost (admin credentials required)

::: tip :key: Default Development Credentials
The dev environment includes a pre-configured Keycloak user for development and testing:
- **Username**: `admin`
- **Password**: `admin`
- **Role**: `AIHubAdmin`

These credentials can be customized via environment variables (`KEYCLOAK_DEV_USER_*`).
:::

::: tip :bulb: Local Development Tips
- The `.nip.io` domain automatically resolves to your localhost, providing a production-like domain experience
- SSL certificates are valid for both `*.127.0.0.1.nip.io` and `*.localhost` domains
- All services use Traefik for SSL termination and routing
- Volume data is stored in `${VOLUME_ROOT:-./.docker-volumes}/` (defaults to `.docker-volumes/`)
- All OAuth2/OIDC authentication goes through Keycloak, which can broker to Azure AD in production
:::

### :key: Configure Environment Variables

::: warning
The project requires environment variables for configuration. You will need to request the `.env` files from the team
and place them in the root directories of the relevant backend and frontend projects.
:::

### :robot: AI Coding Assistant Integration (MCP)

The AI-Hub provides enhanced integration with AI coding assistants through the Model Context Protocol (MCP). This
integration allows AI tools like Claude Code, Gemini CLI, and other assistants to interact directly with your
development environment.

::: info MCP Benefits
MCP integration provides AI coding assistants with:

- **Real-time observation** of running services and their state
- **Direct access** to development databases for debugging
- **API interaction** capabilities for testing and validation
- **Observability integration** with Langfuse tracing and monitoring
:::

#### :gear: MCP Configuration

The MCP integration is configured through the `.mcp.json` file in the project root. It defines 12 MCP servers (11
enabled by default), each with a wrapper script in `.claude/mcp/`:

**Platform Servers** (require running Docker dev stack):

1. **Langfuse MCP**: LLM observability — prompt management, tracing, cost tracking, evaluations
2. **MongoDB MCP**: Read-only database access to the FerretDB/MongoDB data layer
3. **AI-Hub API MCP**: Test API endpoints directly through MCP
4. **PostgreSQL MCP**: Read-only access to infrastructure databases (Langfuse, Dagster, LiteLLM, OpenWebUI)
5. **Milvus MCP**: Vector database operations — manage collections, run similarity searches, inspect indexes
6. **NATS MCP**: Messaging system integration — inspect subjects, view messages, monitor JetStream streams
7. **Dagster MCP**: Pipeline orchestration — explore pipelines, monitor runs, manage data assets

**Development Servers** (work independently):

08. **Context7 MCP**: Up-to-date library documentation for LlamaIndex, FastAPI, Pydantic, and other dependencies
09. **PrimeVue MCP**: Official component library — props, events, slots, theming, Pass Through, design tokens
10. **Nuxt MCP**: Official framework docs, API references, and deployment guides (remote at nuxt.com/mcp)
11. **Playwright MCP**: Browser automation and UI debugging — visual inspection, screenshots, DOM/CSS analysis
12. **GitHub MCP**: Issues, PRs, code search, CI status — disabled by default, requires `GITHUB_PERSONAL_ACCESS_TOKEN`
    in `.env` (create at https://github.com/settings/tokens with `repo, read:org, read:project` scopes)

#### :rocket: Using MCP Integration

Once your development environment is running, AI coding assistants that support MCP can automatically discover and use
these integrations:

- **Query agent execution traces** through Langfuse UI at http://localhost:6006
- **Inspect database state** through MongoDB MCP (read-only)
- **Test API endpoints** through AI-Hub API MCP
- **Debug complex issues** with full development context

::: tip AI Assistant Setup
Ensure your AI coding assistant (Claude Code, Gemini CLI, etc.) is configured to use the `.mcp.json` file. Most modern
AI assistants will automatically detect and use this configuration when present in the project root.
:::

### :hammer_and_wrench: Claude Code Integration

The AI-Hub includes comprehensive Claude Code enablement with skills, custom subagents, automated hooks, and MCP
servers. Full details are in `.claude/README.md`.

#### Skills (43 total — invoke via `/skill-name`)

**Workflow**:

- **`/review-diff`**: Pre-PR code review — analyze diff as a senior developer
- **`/create-pr`**: Pre-PR validation, formatting, linting, type checking, and tests across affected scopes
- **`/implement-feedback-from-pr`**: Fetch PR comments and implement reviewer feedback
- **`/plan-issue`**: Fetch GitHub issue and create detailed implementation plan
- **`/reflect`**: Session retrospective — identify mistakes, improve CLAUDE.md and skills
- **`/release-prep`**: Comprehensive pre-release validation across all scopes
- **`/test-scope`**: Smart scoped test runner — detects affected scopes from git diff

**Documentation**:

- **`/update-doc`**: Sync docs, CLAUDE.md, and skills with code changes
- **`/explain`**: Analyze and explain code structure, identify gaps
- **`/document-decision`**: Create Architecture Decision Records (ADRs)
- **`/document-feature`**: Create user-facing VitePress feature documentation
- **`/document-solution`**: Edit solution concept docs for procurement evaluators

**Scaffolding**:

- **`/scaffold-agent`**: Generate AI agent boilerplate (class, events, config, tests)
- **`/scaffold-pipeline`**: Generate Dagster pipeline boilerplate (asset factory, I/O manager, resources)
- **`/scaffold-process`**: Generate process orchestration boilerplate (entity delegation, work events)
- **`/scaffold-api-endpoint`**: Generate REST API controller (endpoints, DTOs, registration)
- **`/scaffold-api-service`**: Generate API service layer (business logic, validation)
- **`/scaffold-api-repository`**: Generate MongoEngine entity (schema, indexes, methods)
- **`/scaffold-frontend-page`**: Generate Nuxt page boilerplate (composables, pages, components)
- **`/scaffold-bot-handler`**: Generate bot conversation handler boilerplate (ChatBot subclass)

**Developer Experience**:

- **`/docker-dev`**: Manage Docker dev environment (up, down, health, logs, restart, ports, status)
- **`/check-i18n`**: Validate all 4 locale files have matching keys, report missing translations
- **`/generate-sdk`**: Regenerate frontend API SDK from OpenAPI specification
- **`/dependency-audit`**: Audit dependencies for outdated packages, vulnerabilities, version drift
- **`/validate-events`**: Validate event hierarchy, registration, and subscriber matching
- **`/debug-agent`**: Debug agent event flow, NATS subscriptions, and Langfuse traces
- **`/debug-pipeline`**: Debug Dagster pipeline failures, sensor issues, resource config

**Frontend**:

- **`/scaffold-composable`**: Generate Pinia-Colada composable (query + mutation)
- **`/scaffold-event-display`**: Generate event timeline component
- **`/scaffold-dashboard-widget`**: Generate dashboard widget (ApexCharts, GridStack)
- **`/scaffold-frontend-subpage`**: Generate detail page with tab subpages
- **`/scaffold-frontend-component`**: Generate Vue component (card, modal, list, form)
- **`/debug-frontend`**: Visual UI debugging with Playwright
- **`/audit-frontend`**: Frontend code audit (SDK, i18n, accessibility, patterns)
- **`/primevue-lookup`**: PrimeVue component docs lookup
- **`/design-system`**: Design system reference guide

**API & Pipeline**:

- **`/api-auth-guide`**: Auth, identity, permissions reference
- **`/nats-events`**: NATS, JetStream, events, pub/sub, RPC reference
- **`/dagster-pipelines`**: Dagster assets, resources, IO managers, partitions reference
- **`/rclone-guide`**: Rclone cloud storage integration reference

**Bot**:

- **`/setup-bot-connection`**: Bot connection setup (Azure, Teams, Slack)
- **`/debug-bot`**: Bot troubleshooting and debugging
- **`/bot-reference`**: Bot architecture and patterns reference

#### Custom Subagents (7 — used automatically for specialized tasks)

- **`codebase-expert`**: Deep monorepo knowledge, cross-scope tracing, architectural questions (with memory)
- **`code-reviewer`**: Quality, security, and standards review against CLAUDE.md conventions
- **`event-flow-analyzer`**: Traces Swiss AI Agent Protocol event flows end-to-end (with memory)
- **`docker-ops`**: Docker infrastructure expert for 30+ services, networks, and health checks
- **`test-analyzer`**: Test coverage analysis, gap identification, pytest-bdd and custom test runners
- **`frontend-analyzer`**: Nuxt 3 composables, Pinia-Colada queries, PrimeVue, SDK generation pipeline
- **`documentation-keeper`**: Documentation freshness tracking against code changes (with memory)

#### Automated Hooks (6 — run automatically, no invocation needed)

- **`auto-format-python.sh`** (PostToolUse): Ruff format + check on Python file edits
- **`auto-format-frontend.sh`** (PostToolUse): ESLint fix on TypeScript/Vue file edits
- **`protect-sensitive-files.sh`** (PreToolUse): Blocks access to .env, .pem, .key, credentials, certs, tokens
- **`scope-boundary-check.sh`** (PreToolUse): Warns about cross-scope import violations
- **`stop-hook-git-check.sh`** (Stop): Checks uncommitted changes at session end
- **`session-start.sh`** (SessionStart): Installs dependencies, checks environment, warns about main branch

#### Plugins (5 — community plugins from `claude-plugins-official`)

These plugins extend Claude Code with additional slash commands and automated behaviors. They are configured in
`.claude/settings.json` under `plugins`.

**`code-review`** — Automated PR review with multi-agent architecture

- **`/code-review [--comment]`**: Launches four independent review agents in parallel, each focusing on a different
  aspect: two check CLAUDE.md compliance, one detects bugs, one analyzes git history context. Every issue is scored
  0–100 for confidence; only issues scoring 80+ are surfaced. Trivial, draft, and already-reviewed PRs are automatically
  skipped. Use `--comment` to post the review directly as a PR comment on GitHub.

**`ralph-loop`** — Iterative self-correcting development loop

- **`/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"`**: Runs Claude Code in a loop,
  re-injecting the same prompt after each iteration until the completion promise string is output or the iteration limit
  is reached. Useful for TDD workflows (write failing test, implement, validate, repeat) and well-defined problems with
  automatically verifiable success criteria. Not suited for subjective design tasks or ambiguous goals.
- **`/cancel-ralph`**: Terminates an active Ralph loop.

**`commit-commands`** — Git commit, push, and PR automation

- **`/commit`**: Analyzes staged and unstaged changes, matches the repository's existing commit style, generates a
  conventional commit message, and creates the commit. Skips sensitive files (`.env`, credentials). Attributed to Claude
  Code.
- **`/commit-push-pr`**: Full workflow — creates a feature branch if needed, commits changes, pushes to origin, and
  opens a PR via `gh` with summary and test plan sections.
- **`/clean_gone`**: Removes local branches marked as `[gone]` (remote-deleted) including their associated worktrees.

**`hookify`** — Custom behavioral rules via markdown files

- **`/hookify [description]`**: Creates behavioral rules from explicit instructions or by analyzing the current
  conversation for unwanted patterns. Rules are stored as markdown files with YAML frontmatter.
- **`/hookify:list`**: Lists all configured rules and their enabled/disabled state.
- **`/hookify:configure`**: Interactive enable/disable management for existing rules.
- **`/hookify:help`**: Documentation and usage guidance.
- **Rule anatomy**: Each rule specifies an `event` (bash, file, stop, prompt, or all), an `action` (warn or block), and
  a `pattern` (Python regex). Conditions support operators like `regex_match`, `contains`, `not_contains`, `equals`,
  `starts_with`, and `ends_with`. Rules take effect immediately without restart.

**`security-guidance`** — Automatic security pattern scanner (no slash commands — hook only)

- **Trigger**: PreToolUse hook on every `Edit`, `Write`, and `MultiEdit` operation. Runs automatically before file
  changes are applied.
- **What it detects**: Scans file paths and content for known vulnerability patterns:
  - **Command injection**: `child_process.exec()`, `execSync()`, `os.system()`, GitHub Actions workflow injection via
    untrusted inputs (`issue.title`, `pull_request.body` in `.github/workflows/`)
  - **Code injection**: `eval()`, `new Function()`, `pickle` deserialization
  - **XSS**: `dangerouslySetInnerHTML`, `document.write`, `.innerHTML =`
- **Behavior**: When a pattern is matched, the hook prints a detailed warning explaining the vulnerability and
  suggesting safer alternatives, then blocks the edit (exit code 2). Warnings are deduplicated per session — the same
  file/rule combination is only flagged once. Session state is stored in `~/.claude/` and auto-cleaned after 30 days.
- **Disable**: Set `ENABLE_SECURITY_REMINDER=0` in your environment to turn off.

::: info AI Assistant Context Files
Each scope contains `CLAUDE.md` files with scope-specific architecture, patterns, and examples. These provide AI
assistants with proper context about each component's purpose and architecture. Local overrides (gitignored):
`CLAUDE.local.md`, `.claude/settings.local.json`, `.claude/mcp.local.json`.
:::

## 4. :clipboard: Project Governance & Work Management

This chapter outlines the rules and processes that govern contributions, technical decision-making, and how development
work is managed across the project.

### :chart_with_upwards_trend: Work Management (Roadmap & Kanban)

The AI-Hub ecosystem uses two main GitHub Projects to manage development and high-level planning. All interactions can
be performed via the GitHub CLI (`gh`).

#### High-Level Planning: `aihub-roadmap`

The `aihub-roadmap` project focuses on high-level planning, covering both customer projects and larger initiatives for
the AI-Hub core. Here you will find general project information, goals, and ongoing documentation related to major
initiatives.

::: details :chart_with_upwards_trend: Roadmap Access
**URL**: `https://github.com/orgs/bbvch-ai/projects/7`

**View the roadmap via CLI**:

```bash
# View high-level details of the roadmap project
gh project view 7 --owner bbvch-ai

# List all items in the roadmap
gh project item-list 7 --owner bbvch-ai
```
:::

#### Daily Work: `aihub` Kanban Board

While high-level context lives in the roadmap, actual development tasks are tracked in the `aihub` Kanban Board. Tasks
on this board are always linked back to a corresponding item in the `aihub-roadmap` to ensure traceability.

The board uses three primary status columns: **To Do**, **In Progress**, and **Done**. When you begin work on a task,
assign it to yourself and move it from "To Do" to "In Progress". Once complete, move it to "Done".

::: details :clipboard: Kanban Board Access
**URL**: `https://github.com/orgs/bbvch-ai/projects/2`

**Interact with the board via CLI**:

```bash
# List all open issues on the Kanban board that are assigned to you
gh issue list -R "bbvch-ai/aihub-core" -a "@me" -S "project:bbvch-ai/2"

# View the details and comments of a specific issue
gh issue view <issue_number> -c -R "bbvch-ai/aihub-core"
```
:::

### :memo: Architectural Decision Records (ADRs)

To ensure our architecture evolves consistently, all significant technical decisions are documented using an
Architectural Decision Record (ADR) process.

#### Consultation Protocol

::: danger :stop_sign: Required Reading
Before you make any "significant change," you **must** consult the existing ADRs located in `aihub_doc/arc42/decisions/`
to ensure your change does not conflict with a past decision. A significant change includes adding major dependencies,
introducing new tools, or altering fundamental architectural patterns.
:::

#### Documentation Protocol

If your task requires a new significant decision, you **must** document it by creating a new ADR file in the same
directory.

::: details :memo: ADR Template
**Naming Convention**: `YYYY_MM_DD_short-decision-summary.md`

**Template**: Use the following markdown template for the new ADR file.

```markdown
# Title of the Decision

A clear, concise title. Example: "Adopt Redis for Caching"

## Context

Describe the problem or situation that necessitates this decision. What is the technical or business context?

## Decision Drivers

List the key forces influencing your decision as bullet points. These are the "whys".

## Decision

State your decision clearly and unambiguously. Describe exactly what you have chosen to do.

## Consequences

Describe the results of your decision. List both positive outcomes and any potential negative trade-offs.
```
:::

______________________________________________________________________

## 5. :evergreen_tree: Git & GitHub Workflow

This chapter outlines the rules and processes for source code management, including branching, commit conventions, and
pull request procedures.

### :herb: Branching Strategy

To maintain a clean and manageable repository, we follow a simple branching strategy.

::: info :herb: Branch Structure
- **`main` branch**: This is the single long-lived branch, which represents the stable, main line of development.

- **Feature branches**: All new work, including features, fixes, and chores, must be done on short-lived branches. These
  branches are created from `main` and merged back into `main` via a pull request. Branch names **must** follow this
  pattern:

  - `type/short-description`

  Where `type` must be one of `feat`, `fix`, `chore`, `test` or `doc`.

  - Example feature branch: `feat/new-agent-workflow`
  - Example fix branch: `fix/login-bug-incorrect-redirect`
:::

### :label: Conventional Commits & Pull Request (PR) Titles

Both commit messages and Pull Request (PR) titles **must** follow the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This ensures a clear and
descriptive history that can be easily parsed.

The format is: `<type>(<scope>): <subject>`

::: details :label: Format Specification
- **`type`**: Must be one of: `fix`, `feat`, `test`, `doc`, `chore`.
- **`scope`**: Describes what part of the codebase is affected, such as a package name, customer, or initiative (e.g.,
  `aihub`, `api`, `bbv`).
- **`subject`**: A short, imperative-tense description of the change.
:::

::: tip :memo: Examples
- `fix(aihub): Fix bug where old messages can't be edited anymore`
- `feat(ci-cd): Add new feature to ci-cd pipeline`
:::

### :computer: GitHub CLI Integration

All GitHub-related operations should be performed using the GitHub CLI (`gh`) tool rather than the web interface. This
ensures consistency and enables automation.

::: details :computer: Common GitHub CLI Commands
**Create a Pull Request**:

```bash
# Create a new PR with a title and body
gh pr create --title "feat(api): Add new endpoint for user profiles" --body "This PR introduces..."
```

**View Pull Requests**:

```bash
# See the current status of all PRs in the repository
gh pr status

# List all PRs that you have authored
gh pr list --author "@me"
```

**Review a Pull Request**:

```bash
# Check out a PR locally to test it
gh pr checkout <pr_number>

# View the details and changes of a PR in the terminal
gh pr view <pr_number> --web

# Approve a PR
gh pr review <pr_number> --approve --body "LGTM!"
```

**Merge a Pull Request**:

```bash
# Merge a PR after it has been approved and all checks have passed
gh pr merge <pr_number> --squash
```
:::

### :lock: Branch Protection Rules

::: warning :shield: Protected Branch
To ensure the stability and integrity of our codebase, the `main` branch is protected by the following rules.
:::

::: details :shield: Protection Rules
- **Require a Pull Request Before Merging**: All changes must be made through a pull request. Direct pushes to `main`are
  blocked.
  - **Required Approvals**: At least **one** approving review is required before merging.
  - **Dismiss Stale Approvals**: When new commits are pushed to the branch, previous approvals are dismissed and a new
    review is required.
  - **Require Conversation Resolution**: All comments and discussions on the PR must be resolved before merging.
- **Require Linear History**: This rule disallows merge commits, keeping the repository history clean and easy to
  follow.
- **Allowed Merge Method**: Only **Squash Merging** is enabled. This means all commits from a feature branch are
  squashed into a single commit when merged into `main`. This keeps the history of the `main` branch concise and linear.
- **Block Force Pushes and Deletions**: Force pushing to `main` is denied to preserve commit history. Deleting the`main`
  branch is also restricted.
:::

______________________________________________________________________

## 6. :test_tube: Testing In-Depth

This chapter describes the testing frameworks and philosophies used in the AI-Hub project. While comprehensive testing
is a core part of our development cycle, we do **not** follow a strict Test-Driven Development (TDD) methodology.

### :checkered_flag: Pytest & Markers

::: info :test_tube: Test Structure
**`pytest`** is the standard testing framework for the AI-Hub project. Tests are located in a `tests` directory at the
same level as the code being tested. All test files must be prefixed with `test_`, such as`test_<unit_being_tested>.py`.
:::

::: info :label: Test Markers
To better categorize tests, we use `pytest` markers. This allows us to selectively run or exclude certain types of
tests. Common markers include:

- `azure`
- `self_hosted`
- `slow`
- `integration`
:::

### :cucumber: Behavior-Driven Development (BDD) with pytest-bdd

For testing agent and process workflows, we try to use **Behavior-Driven Development (BDD)** with the `pytest-bdd`
plugin. BDD provides a structured way to write tests that are easily understandable by both technical and non-technical
team members.

::: warning :warning: Async Testing Limitation
However, `pytest-bdd` does not fully support `async` testing, which can be clumsy. Therefore, for truly asynchronous
tests, we often fall back to using **`pytest` directly**.
:::

::: details :gear: How It Works
The BDD process involves two main components:

1. **Feature Files**: Written in Gherkin syntax (`.feature`), these files describe a feature and its scenarios in plain
   English. They are located in the `tests/features/` directory.
2. **Step Definitions**: These are Python functions that implement the steps defined in the feature files. They use
   decorators like `@given`, `@when`, and `@then` to link the code to the Gherkin steps.

Tests are structured into three parts: `Given` (setup), `When` (execute), and `Then` (assert).
:::

::: tip :bulb: Why We Use BDD
When possible, we favor BDD for several key reasons:

- **Readable Tests**: Scenarios written in plain language allow non-technical stakeholders to validate requirements.
- **Reusability**: Step definitions can be shared across multiple scenarios, which reduces code duplication.
- **Faster Iterations**: New test cases can often be added by writing new Gherkin scenarios without needing new Python
  code.
- **Closer Collaboration**: The process encourages collaboration between business, QA, and development teams.
:::

______________________________________________________________________

## 7. :pencil2: Code Conventions

Adherence to a consistent coding standard is critical for maintaining the quality, readability, and long-term
maintainability of the AI-Hub codebase. The following conventions are not optional; they are strictly enforced by our
CI/CD pipelines.

### :art: Formatting, Linting, and Type Checking

We use a specific set of tools to automate code formatting, enforce style rules, and perform static analysis.

::: details :black_circle: Code Formatter: Black
**Rule**: All Python code is formatted using the `black` code formatter. **Configuration**: The line length is set to
**120 characters**. No other configuration is changed from the default.
:::

::: details :zap: Linter: Ruff
**Rule**: We use `ruff` for high-performance linting and import sorting. **Configuration**: We enforce a specific set of
rules: `select = ["E", "F", "UP", "I"]`.

- `E`/`F`: Catches errors and warnings from Pyflakes (e.g., unused imports, undefined names).
- `UP`: Includes rules from `pyupgrade` to enforce modern Python syntax.
- `I`: Enforces import sorting, handled automatically by Ruff.
:::

::: details :mag: Static Type Checker: MyPy
**Rule**: We use `mypy` for static type checking to catch type-related errors before runtime. **Configuration**: Type
checking is run in `strict = true` mode, which enforces the highest level of type safety.
:::

### :hammer: Enforcement via Makefile

::: danger :rotating_light: Critical Commands
While these checks run automatically in our CI pipeline, you **must** run them locally before committing your code. Each
scope (and the root directory) contains a `Makefile` with the necessary commands. Run these from within each scope
directory (Makefile targets use `uv run` internally).

- `make format`: Formats all code in the current scope using **Black**.
- `make lint`: Lints all code using **Ruff** and runs **MyPy** for type checking.
- `make pr-ready`: This is the **most important command**. It runs both `make format` and `make lint` with auto-fixing
  capabilities (`ruff check --fix`). Run this command to ensure your code is 100% compliant before creating a pull
  request.
:::

### :abc: Naming Conventions

::: info :snake: Snake Case Rules
- **Files and Directories**: All Python files and directory names must use `snake_case`.
  - Example file: `agent_workflow_manager.py`
  - Example directory: `workflow_steps`
- **Test Files**: All test files must be prefixed with `test_` and follow the `snake_case` convention.
  - Example: `test_agent_workflow_manager.py`
:::

::: info :camel: Camel Case Rules
- **Classes**: All class names must use `CamelCase`.
  - Example: `AgentWorkflowManager.py`, `ProcessExecutor.py`, `UserIdentity.py`
:::

### :speech_balloon: Docstrings and Comments

::: tip :speech_balloon: Documentation Best Practices
**Docstrings**: All public modules, classes, methods, and functions **must** have a multi-line docstring that clearly
explains their purpose, context, and usage. This is crucial for maintainability and for others to understand your code.

```python
class AgenticProcess:
    """
    Manages the lifecycle of an agentic process from instantiation to completion.

    This class orchestrates the flow of events between different actors (agents, humans, programs)
    and ensures that the process adheres to its predefined workflow definition.
    """
```

**Comments**: Comments should explain the **why**, not the **what**. Write your code to be as self-documenting as
possible, and use comments only to clarify complex logic, business rules, or the reasoning behind a specific
implementation choice.

```python
# Incorrect: "what" the code does
# Increment the counter
i += 1

# Correct: "why" the code does it
# We must wait for the event to propagate before proceeding to avoid a race condition.
await asyncio.sleep(0.1)
```
:::

### :label: Type Annotations

Strict and specific type hints are mandatory.

::: tip :label: Type Annotation Guidelines
**Rule**: All variables, function arguments, and return values must have type annotations.

**Style**: Use modern standard library types where possible (e.g., `list[int]` instead of `typing.List[int]`, and
`int | None` instead of `typing.Optional[int]`).

**Advanced Types**: For more complex scenarios, use the advanced types available in the `typing` module, such as
`Annotated`, `TypeVar`, and `Generic`.

```python
from typing import Annotated
from fastapi import Depends


# Good example demonstrating modern type hints and advanced usage
async def get_user_data(
        user_id: int | None,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> UserDto:
    """Fetches user data based on an ID and an authentication token."""
    if user_id is None:
        raise ValueError(...)
    # ... logic to fetch data
    return UserDto(user_id=user_id, name="Example User")
```

**Complex types**: Avoid dicts or complex types like `tuple[str, int, list[float]]` at all costs. Always create pydantic
objects or dataclasses to hold complex data structures.

**Let things fail**: Do not catch errors and return none. Instead, if a function or method can't generate its output, it
shall fail.
:::

______________________________________________________________________

## 8. :repeat: The Core Development Cycle

This chapter outlines the standard, step-by-step process for every development task. Following this cycle ensures that
all work is done consistently, contextually aware, and meets our quality standards.

### :mag: Step 1: Understand the Goal and Context

::: tip :dart: Start with Context
Every development task begins with a clear goal, typically provided as a GitHub issue number. You must first understand
the task's requirements and its place within the broader project roadmap.
:::

::: info :link: Task Linking
Your task's issue title will often contain a prefix in brackets (e.g., `[process]`) that links it to a larger initiative
on the `aihub-roadmap`. You can view the roadmap using the `gh` CLI:
:::

::: tip :mag: View High-Level Initiatives
```bash
gh project item-list 7 --owner bbvch-ai --limit 100
```

This command will show the high-level initiatives:

```
> Issue  🗺️ Infrastructure [infra]                             375      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgbcrk4
> Issue  🗺️ Spike Container Deployment [container]             422      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgcQbYQ
> Issue  🗺️ Agentic Process Automation [process]               442      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgcTfWw
```

By fetching the main initiative issue (e.g., #442), you can gain more insight into the overall goal and see how your
specific task fits in with related issues.

```bash
gh issue view 442 -c -R "bbvch-ai/aihub-core"
```

This gives you the context and a checklist of related tasks, helping you to understand the full picture before you
begin.
:::

### :broom: Step 2: Prepare Your Workspace

Before writing any code, check your local environment.

::: info :gear: Workspace Preparation
1. **Check your current branch**. If you are on `main`, create a new branch that follows the naming convention outlined
   in Chapter Git & GitHub Workflow (e.g., `feat/new-process-feature`).
2. **Review existing work**. If you are already on a feature branch, run `git diff main...` to see what changes have
   already been made on that branch.
:::

### :bulb: Step 3: Plan and Implement Your Solution

::: tip :bulb: Implementation Steps
1. **Plan your implementation**. Think through the changes you need to make before writing code.
2. **Choose the correct scope**. It is critical that you place your code in the correct package (`aihub_lib`,
   `aihub_agent`, `aihub_api`, etc.). If code is used by more than one service, it belongs in `aihub_lib`.
3. **Write the code**. As you implement your solution, rigorously follow all rules defined in the Chapter **Code
   Conventions**.
:::

### :white_check_mark: Step 4: Verify Code Quality

Once you have a working implementation, you must run our automated formatting and linting tools to ensure your code is
100% compliant with our standards.

::: tip :white_check_mark: Quality Check
From within the scope directory you worked on, run:

```bash
make pr-ready
```

This command will automatically format your code and report any linting or type errors that need to be fixed.
:::

### :test_tube: Step 5: Write and Run Tests

Our approach to testing is pragmatic.

::: tip :test_tube: Pragmatic Testing Approach
- **Writing new tests**: You are not required to write tests for every change, as we do not aim for 100% test coverage.
  However, if it is easy and straightforward to write a test for your new code, you should do so. Only write complex
  tests if you are specifically instructed to.
- **Running all tests**: Whether you have written a new test or not, you **must** run the entire local test suite to
  ensure your changes have not broken any existing functionality. Tests must always pass before you consider your work
  complete.
:::

::: tip :test_tube: Run Tests
To run the local test suite, use the command:

```bash
make test
```
:::

______________________________________________________________________

## 9. :books: Documentation and Self-Improvement

A key principle of the AI-Hub project is that documentation must evolve with the code. This chapter outlines our
documentation philosophy and the process every developer must follow to ensure our documentation remains accurate,
helpful, and up-to-date.

### :thought_balloon: Documentation Philosophy

We follow a **README.md-only** documentation principle. All project documentation resides in one of two places:

::: info :two: Two Documentation Types
1. **Code Docstrings**: For documentation that is specific to a single class, method, or function, we use detailed
   docstrings directly in the implementation file. This is the most common form of documentation.
2. **README.md Files**: For documentation that holds true for a larger part of the codebase (a specific folder, a scope,
   or the entire project), we use `README.md` files.
:::

::: tip :file_folder: Hierarchical Structure
These README files are hierarchical. A `README.md` can exist at the project root, within each scope (e.g.,
`aihub_agent/README.md`), or even in nested sub-folders. This allows us to provide context at the most appropriate
level.

It is critical that these files are kept up-to-date and are well-written, as we use them to automatically generate a
developer documentation site with VuePress.
:::

### :arrows_clockwise: The Self-Improvement Protocol

::: danger :warning: Mandatory Step
This is the final, critical step of the development cycle. Before you consider a task complete, you **must** reflect on
your work and its impact on the documentation. This is not optional; it is essential for the long-term health of the
project.
:::

::: details :question: Self-Reflection Questions
After implementing your changes, ask yourself the following questions:

- **Does my change make existing documentation inaccurate?** If your code change implies that a section in a `README.md`
  is now out of date or incorrect, you must adapt that section of the README to align with your changes.

- **Is there missing information that would have helped me?** If you had to discover important information on your own
  that was not documented, you must add it. Either extend an existing `README.md` or create a new one at the appropriate
  level (folder, scope) to share this knowledge.

- **Did the documentation conflict with the code?** If you found information in a `README.md` that was wrong, you must
  correct or remove it. In this project, the **code is always the ground truth.**
:::

______________________________________________________________________

## 10. :book: Technical Reference

This chapter provides a reference for the project's package management strategy and the technologies used in the stack.

### :package: Package Management & Versioning

::: details :package: Package Structure
The AI Hub consists of multiple packages that handle specific functionalities:

- `aihub_agent`: Contains common code for agent development.
- `aihub_api`: Contains common code for API implementation.
- `aihub_bot`: Contains common code for bot development.
- `aihub_pipeline`: Contains common code for pipeline development.
- `aihub_process`: Contains common code for process development.
- `aihub_lib`: A foundational library containing code that is relevant for multiple other packages. The `aihub_lib`
  package is used by all other packages.
:::

::: tip :label: Versioning and Referencing
All packages have versions that are increased in sync with the tags in the repository. This means a package's version is
updated with every merge into the main branch.

The monorepo uses uv workspaces to manage inter-package dependencies. During local development, workspace members are
automatically resolved from their local directories. When published to PyPI, consumers install packages normally from
the registry. A single `uv.lock` at the root ensures consistent dependency resolution across all packages.
:::
