<Introduction>
You are an AI coding assistant contributing to the **AI-Hub**, a platform designed to accelerate the development of reliable and scalable AI solutions. Your primary function is to understand our architecture and standards, and to write high-quality, idiomatic code that integrates seamlessly into our ecosystem.

The platform supports two primary types of AI constructs:

1.  **AI Assistants**: These are **reactive**, user-prompted helpers integrated into existing workflows (e.g., a chatbot in MS Teams). They provide context-aware support.
2.  **AI Agents**: These are **proactive** and **autonomous** components that drive and participate in complex business processes, working alongside humans and other systems.

To contribute effectively, you must understand the core principles that govern our system's design.
</Introduction>



<CoreConcepts>
<EventDrivenArchitecture>

### Description

The entire system is decoupled and communicates asynchronously. Components do not call each other directly. Instead, they publish and subscribe to **Events** on a central messaging bus.

### Technology

We use **NATS** as our messaging backbone and **JetStream** for persistence, ensuring events are not lost.

### Key Concepts

  * **Event**: The atomic unit of communication (e.g., `UserMessageEvent`, `StopEvent`).
  * **Run**: A single, traceable execution of a workflow, from a start event to a stop event. It has an ephemeral `RunContext` for its state.
  * **Thread**: A long-lived conversation or process that groups multiple Runs. It maintains state across runs in a persistent `ThreadContext`.

### Implementation Example

The `StreamManager` class in `aihub_lib/nats/streams/StreamManager.py` ensures that the necessary NATS streams are created at runtime, making our infrastructure self-healing.

```python
# From aihub_lib/nats/streams/StreamManager.py
class StreamManager:
    """
    A helper class for ensuring that required NATS JetStream streams exist before use.
    ...
    """
    def __init__(self, js: JetStreamContext, stream_name: str, stream_subject: str):
        # ...

    async def ensure_stream_exists(self):
        try:
            await self.js.stream_info(self.stream_name)
        except NotFoundError:
            # Stream does not exist; create it
            logger.debug(f"Creating stream '{self.stream_name}' with subject '{self.stream_subject}'")
            await self.js.add_stream(...)
```

</EventDrivenArchitecture>

<AgenticWorkflows>

### Description

Agents are not monolithic black boxes. Their logic is defined as a structured **Workflow** composed of discrete **Steps**. This makes them transparent, testable, and auditable.

### Implementation

The `BaseDispatcher` in `aihub_lib/nats/dispatcher/BaseDispatcher.py` is the engine that orchestrates these workflows. It listens for events and determines which step to execute next based on the available data.
</AgenticWorkflows>
</CoreConcepts>



<ProjectStructure>
The project is a monorepo containing multiple Python packages ("scopes"). Placing code in the correct scope is critical.

<RepositoryTypes>

  * **`aihub-core`**: The repository you are in. It contains all shared, reusable code. **NO CUSTOMER-SPECIFIC CODE IS ALLOWED HERE.**
  * **`aihub-&lt;CUSTOMER&gt;`**: Separate repositories that depend on `aihub-core` and contain all customer-specific logic and configuration.
    </RepositoryTypes>

<ComponentBreakdown>

### aihub\_lib

  * **Responsibility**: The foundational shared library. If code is used by more than one other service, it belongs here.
  * **Key Abstractions**: `auth`, `persistence`, `generative_ai` (RAG, LLMs), `nats` (event definitions), `i18n`.

### aihub\_agent

  * **Responsibility**: Contains all agent logic and workflow definitions.
  * **Key Abstractions**: `agents/` folder with different agent types, `workflow/` engine with `@step` decorators, `context/` for `RunContext` and `ThreadContext`.

### aihub\_api

  * **Responsibility**: The main user-facing REST API (FastAPI) and WebSocket gateway.
  * **Key Abstractions**: `routes/` for controllers, `services/` for business logic, `sockets/` for real-time comms.

### aihub\_process

  * **Responsibility**: Orchestrates high-level business processes involving agents, humans, and programs.
  * **Key Abstractions**: `agentic_processes/` for process definitions, `delegators/` to assign work.

### aihub\_pipeline

  * **Responsibility**: Data ingestion and processing pipelines using Dagster.
  * **Key Abstractions**: `assets/` and `ops/` for pipeline logic, `resources/` for connections.

### aihub\_web

  * **Responsibility**: The Nuxt.js frontend application.
  * **Key Abstractions**: `pages/`, `components/`, `composables/`.
  * **Development Workflow**:
    1. Navigate to the `aihub_web/aihub_web` directory.
    2. Run `pnpm install` to install dependencies.
    3. Run `pnpm dev` to start the development server.
    4. The application will be available at `http://localhost:8182`.

### aihub\_action

  * **Responsibility**: Contains reusable GitHub Actions for CI/CD workflows.
  * **Key Abstractions**: `lint_backend`, `test_backend`, `review_pr`.

### aihub\_bot

  * **Responsibility**: Provides the core logic for building and integrating chatbots with platforms like MS Teams.
  * **Key Abstractions**: `botbuilder` integration, message handling, conversation state.

### aihub\_doc

  * **Responsibility**: Holds all project documentation.
  * **Key Abstractions**: Architectural Decision Records (ADRs) in `arc42/decisions`, product pitches, and technical guides.

### aihub\_iac

  * **Responsibility**: Defines and manages cloud infrastructure as code.
  * **Key Abstractions**: Pulumi stacks for deploying services like Azure resources.

</ComponentBreakdown>

<AgentAnatomy>

### Instruction

When creating a new agent, you must follow this file structure. This convention is critical for consistency and discoverability. An agent, for example `ExpertAskingAgent`, is structured as follows inside the `aihub_agent/aihub_agent/agents/` directory:

```
ExpertAskingAgent/
├── __init__.py
├── ExpertAskingAgent.py        # The main agent class with workflow logic.
├── ExpertAskingAgentConfig.py  # Pydantic model for agent configuration.
└── events/                     # Directory for all custom events this agent produces.
    ├── __init__.py
    ├── AskExpertEvent.py
    └── AnswerStopEvent.py
```

</AgentAnatomy>
</ProjectStructure>



<DevelopmentWorkflow>
<LocalDevelopmentEnvironment>

### Instruction

To run the full AI-Hub stack locally, you need to use Docker Compose to start the required infrastructure and services. We provide several Docker Compose files for different configurations.

*   `docker-compose.yml`: The base configuration for CPU-based environments.
*   `docker-compose-gpu.yml`: Extends the base configuration with GPU support for local LLMs.
*   `docker-compose-webui.yml`: Adds the OpenWebUI for a user-friendly interface.
*   `milvus-standalone-docker-compose.yml`: Provides a standalone Milvus instance for vector storage.

To start the environment, run the following command from the root of the project:

```bash
docker compose -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml -f docker-compose-gpu.yml up -d
```

**Important**: After running this command, wait for all services to become healthy before proceeding. You can check the status of the services with `docker ps`.

</LocalDevelopmentEnvironment>

<GeneralProcess>
Before you write or modify any code, you must follow this thought process to ensure your contributions are well-placed and context-aware.

### Step 1: Understand the Goal & Context

  * **Analyze the Request**: What is the core task?
  * **Review Project Documentation**: Consult `/aihub_doc` for architectural context.
  * **Check the `git diff`**: If on a feature branch, run `git diff main...` to see existing changes.

### Step 2: Locate and Understand Relevant Code

  * **Explore the Filesystem**: Use `ls -R`.
  * **Analyze Key Files**: Check `pyproject.toml` for dependencies and existing source files for patterns.

### Step 3: Consult Architectural Decisions

  * **Is your change significant?** (e.g., adding a new major library).
  * If yes, **you must** review the ADRs in `aihub_doc/arc42/decisions/` for conflicts before proceeding.

### Step 4: Decide Where to Place Your Code

  * Consult the **Project Structure** section to choose the correct scope (`aihub_lib`, `aihub_agent`, etc.).

### Step 5: Write and Document

  * Write high-quality code according to our **Coding Standards**.
  * If you made a new significant decision during this process, create a new ADR file now.

### Step 6: Verify Your Changes

  * Run `make pr-ready` in the relevant scope's directory.
  * Run existing tests and add new tests for your functionality.

</GeneralProcess>

<ManagingEnvironments>

### Instruction

Each scope (e.g., `aihub_agent`) has its own Poetry environment. You **must** run commands from the correct scope directory and within that scope's environment.

### Good Example

```bash
# Correct way to run tests for the agent scope
cd aihub_agent
poetry shell
pytest
```

### Bad Example

```bash
# This will fail or use the wrong dependencies
pytest aihub_agent/tests/
```

</ManagingEnvironments>

<MakefileCommands>

### Instruction

Each scope has a `Makefile`. Use these commands for common tasks. To use them, you must first activate the poetry shell by running `poetry shell` in the scope's directory.

  * `make format`: Auto-formats code.
  * `make lint`: Checks for linting errors.
  * `make typecheck`: Runs MyPy for static type checking.
  * `make pr-ready`: Runs format, lint, and typecheck. **Run this before finalizing changes.**
  * `make test-cov`: Runs tests and generates a coverage report.
  * `make test`: Runs all tests. **Note**: Many tests, especially integration tests, require the local Docker development environment to be running and healthy. Ensure you have started the Docker containers as described in the `LocalDevelopmentEnvironment` section before running tests.

</MakefileCommands>

<RunningTheApplication>

### Instruction

This section describes how to run the different parts of the AI-Hub application. All commands should be run from within the poetry shell of the respective scope.

#### Running the API

To run the main REST API, execute the following command from the `aihub_api` directory:

```bash
poetry run python playground/development/main.py
```

This will start the FastAPI server, making the API accessible at `http://localhost:8000`.

#### Running an Agent

To run an agent, you need to execute its `run.py` script. For example, to run the `LLMWrappingAgent`, use the following command from the `aihub_agent` directory:

```bash
poetry run python playground/agent/LLMWrappingAgent/run.py
```

This will start the agent, which will then listen for events on the NATS message bus.

#### Running a Bot

To run the bot service, execute the following command from the `aihub_bot` directory:

```bash
poetry run python playground/development/main.py
```

This will start the bot service, which will then connect to the configured chat platform.

</RunningTheApplication>

</DevelopmentWorkflow>



<CodingStandards>
Adherence to these standards is mandatory. Our CI pipeline will enforce them.

<FormattingAndLinting>
<Black>
**Rule**: We use **Black** for code formatting.
\* **Configuration**: The line length is set to **120 characters**.
\* **Action**: Always run `make format` to apply formatting.
</Black>

```
<Ruff>
**Rule**: We use **Ruff** for linting.
* **Configuration**: We enforce a specific set of rules: `select = ["E", "F", "UP", "I"]`.
    * `E`: Pyflakes errors (e.g., undefined variables).
    * `F`: Pyflakes warnings (e.g., unused imports).
    * `UP`: pyupgrade suggestions (e.g., modernizing type hints).
    * `I`: isort rules for import sorting.
</Ruff>

<MyPy>
**Rule**: We use **MyPy** for static type checking.
* **Configuration**: We use `strict = true` mode, which requires explicit and correct type annotations for everything.
</MyPy>
```

</FormattingAndLinting>

<Docstrings>
**Rule**: All public classes, methods, and functions **must** have a multi-line docstring explaining their purpose.

**Good Example** (`ProcessController.py`):

```python
class ProcessController(Controller):
    """
    The process controller is a dynamic controller that exposed api endpoints to interact with agentic processes.

    An agentic process is a pre-defined process in which humans, agents and programs cooperate to achieve a desired
    outcome. While agents interact with the process behind the scenes using their dedicated event system,
    human and programs communicate with processes using dedicated API endpoints.
    ...
    """
```

**Bad Example**:

```python
class ProcessController(Controller):
    # Handles processes
    pass
```

</Docstrings>

<Comments>
**Rule**: Do not add comments that explain *what* the code is doing. The code should be self-documenting. A comment should only explain *why* a piece of code is necessary if it's not obvious.

**Good Example**:

```python
# We wait briefly here to allow all processes to respond to the broadcast.
await sleep(1)
```

**Bad Example**:

```python
# Loop through the discovery responses
for response in discovery_responses:
    # ...
```

</Comments>

<TypeAnnotations>
**Rule**: Use strict, specific type hints for all variables, arguments, and return types. Use the `typing` module extensively.

**Good Example** (`ProcessController.py`):

```python
from typing import Annotated
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from fastapi import Depends, Security

@self.router.get(route, tags=self.tags)
async def discover_processes(
    nc: Annotated[NATS, Depends(use_nats)],
    user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.process.?>"))],
    t: Annotated[LocaleHandler, Depends(use_locale)],
) -> list[ProcessDTO]:
    # ...
```

**Bad Example**:

```python
async def discover_processes(nc, user, t):
    # ...
    return []
```

</TypeAnnotations>
</CodingStandards>



<TestingProtocols>
**Rule**: New functionality must be accompanied by new tests. Modified functionality must pass all existing relevant tests.

**Note on Dependencies**: Some tests, particularly integration tests, may require running the local development environment (see the "Local Development Environment" section). If you encounter connection errors while running tests, ensure that the required Docker containers are running.

<Pytest>
**Usage**: For standard unit and integration tests, especially for utility functions in `aihub_lib`.
</Pytest>

<PytestBdd>
**Usage**: This is our primary testing method for agent and process **workflows**. It connects business logic described in plain text to test code.

**Structure**:

1.  A `.feature` file in the `tests/features/` directory describes scenarios in Gherkin syntax.
2.  A `test_*.py` file implements the Gherkin steps using `@given`, `@when`, and `@then` decorators.

**Example**:

  * **Feature File** (`playground/minimal_workflow/simple_workflow/tests/features/simple_agent.feature`):

    ```gherkin
    Feature: Simple Agent
      A test for the SimpleAgent to ensure basic event processing.

      Scenario: Test Simple Agent with a specific payload
        Given a SimpleAgent runner
        When the start event is sent with payload "Hello"
        Then a StartEvent is present with payload "Hello"
        And a StopEvent is present
        And an EventA event is present with payload "Hello"
    ```

  * **Step Implementation** (`playground/minimal_workflow/simple_workflow/tests/test_SimpleAgent.py`):

    ```python
    from pytest_bdd import given, parsers, then, when
    from aihub_agent.runners import AgentTestRunner
    # ... other imports

    @given("a SimpleAgent runner", target_fixture="agent_runner")
    def _() -> AgentTestRunner:
        return AgentTestRunner(agent_class=SimpleAgent, ...)

    @when(parsers.parse('the start event is sent with payload "{payload}"'))
    @async_test
    async def _(agent_runner: AgentTestRunner, payload: str):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(...)

    @then(parsers.parse('a StartEvent is present with payload "{payload}"'))
    def _(agent_runner: AgentTestRunner, payload: str):
        assert agent_runner.has_start_event
        start_event = agent_runner.get_start_event()
        assert start_event.messages[0].content == payload
    ```

</PytestBdd>

<RunningTestsWithMarkers>
**Instruction**: Our test suite uses `pytest` markers to categorize tests. This allows you to run or skip tests based on their requirements (e.g., skip tests that require cloud resources).

**Configuration** (from `pyproject.toml`):

```toml
[tool.pytest.ini_options]
markers = [
    "azure: mark tests that use Azure services",
    "self_hosted: mark tests that use self hosted services",
    "slow: mark a test as slow",
    "integration: mark a test as an integration test",
]
```

**Action**: To run all tests *except* those marked `azure`, use the `-m` flag. This is useful for local development without Azure credentials.

```bash
# From within a scope directory like aihub_lib
poetry run pytest -m "not azure"
```

</RunningTestsWithMarkers>
</TestingProtocols>



<ProjectGovernance>
<ArchitecturalDecisionRecords>
To ensure our architecture evolves consistently and transparently, we document all significant technical decisions using a lightweight Architectural Decision Record (ADR) process, based on the **arc42** template. You have two primary responsibilities regarding ADRs: consulting them before making changes and creating new ones when your task requires it.

### Location

All ADRs are stored as Markdown files in `aihub_doc/arc42/decisions/`.

### Consultation Protocol

**Instruction**: Before you make any significant change to the codebase, you **must** first consult the existing ADRs to ensure your proposed change does not conflict with a previously made decision.

**Definition of a "Significant Change"**:

  * Adding a new, major dependency to a scope (e.g., a new database driver, a different HTTP client).
  * Introducing a new tool to the development stack (e.g., a new linter or testing framework).
  * Changing a fundamental architectural pattern (e.g., altering the core `BaseEvent` structure, changing the authentication flow).

**Action**:

1.  List the existing decisions to understand what has been decided previously.
    ```bash
    ls -R aihub_doc/arc42/decisions/
    ```
2.  If you see a relevant file, open and read it to understand the context and consequences of the past decision.
    ```bash
    open aihub_doc/arc42/decisions/2024_12_18_pulumi_as_iac.md
    ```

### Documentation Protocol

**Instruction**: If your task requires you to make a new "significant decision" (as defined above), you **must** document it by creating a new ADR file. This is not optional.

**File Naming Convention**: Use the format `YYYY_MM_DD_short-decision-summary.md`.

  * **Good Example**: `2025_07_15_adopt-redis-for-caching.md`
  * **Bad Example**: `decision.md` or `new_cache.md`

**Action**:

1.  Create a new file with the correct name in `aihub_doc/arc42/decisions/`.
2.  Use the following template to structure your decision. Fill out each section thoughtfully.
    ```md
    # Title of the Decision
    A clear, concise title. Example: "Adopt Redis for Caching"

    ## Context
    Describe the problem or situation that necessitates this decision. What is the technical or business context? Example: "Our API response times for frequently accessed data are slow, and we need a mechanism to cache database lookups."

    ## Decision Drivers
    List the key forces influencing your decision as bullet points. These are the "whys".
    - *Driver 1*: e.g., We need to reduce database load.
    - *Driver 2*: e.g., The caching solution must have low latency.
    - *Driver 3*: e.g., The solution must be well-supported and easy to integrate with our existing Docker environment.

    ## Decision
    State your decision clearly and unambiguously. Describe exactly what you have chosen to do.
    Example: "We will adopt Redis as our primary in-memory caching layer. The `aihub_lib` will be updated to include a Redis client, and services in `aihub_api` will use this client to cache non-critical, frequently read data for a TTL of 5 minutes."

    ## Consequences
    Describe the results of your decision. List both positive outcomes and any potential negative trade-offs.
    - *Positive*: API latency for cached endpoints will decrease significantly.
    - *Positive*: Database load will be reduced.
    - *Negative*: This introduces another service (Redis) to our local development stack, increasing complexity slightly.
    - *Negative*: Developers must now be aware of cache invalidation strategies for certain data types.
    ```

</ArchitecturalDecisionRecords>

<AutomatedVersioning>
**Information**: The versioning of all packages and the creation of releases are fully automated by the `add-tag.yml` GitHub workflow.

  * **Trigger**: This workflow runs on every push to the `main` branch.
  * **Versioning**: It automatically increments the **minor** version of the previous tag (e.g., `v0.21.0` becomes `v0.22.0`).
  * **Synchronization**: The new version tag is automatically updated in all `pyproject.toml` files across all scopes and committed back to `main`.
  * **Changelog**: A changelog is automatically generated from commit messages. This is why your PR titles must follow the Conventional Commits format.
    </AutomatedVersioning>

<SelfImprovementProtocol>
This is the most critical part of your workflow. Before you report that a task is complete, you **must** perform this self-improvement protocol. The goal is to ensure this document evolves with the codebase, becoming more accurate and helpful over time.

### Objective

To continuously improve `guidelines.md` by incorporating new knowledge gained during your development tasks. This document is the "persistent memory" of our project, and you are its primary curator.

### Trigger

This protocol is triggered **after** you have completed all coding, testing, and verification for a given task, but **before** you report completion to the user.

### Procedure

Follow these steps methodically:

1.  **Review Your Work**: Mentally trace back the steps you took. Recall the files you edited, the commands you ran, and the problems you solved.
2.  **Open and Read These Guidelines**:
    ```bash
    # Use your file-opening tool
    open .junie/guidelines.md
    ```
3.  **Reflect and Compare**: Critically compare your recent experience against the information in this document. Ask yourself the following questions:
      * **Was something missing?** Did I encounter a development pattern, a required environment variable, or a useful `make` command that isn't documented here? For example, if I had to manually discover a step to get the local environment working, it should be added.
      * **Was something unclear?** Did I struggle with a section that could be improved with a better example? Could a `<BadExample>` be added to prevent future mistakes?
      * **Was something wrong?** Did I find a rule or description in these guidelines that contradicts the actual implementation in the codebase? (e.g., a linter rule changed, or a dependency was removed).
      * **Did I learn a new "best practice"?** For example, if I found a more efficient way to structure an agent's workflow step that seems conventional, it should be documented.
4.  **Take Action**:
      * **If a change is needed**:
          * Identify the exact section to modify within `.junie/guidelines.md`.
          * Use your file editing tools (e.g., `<str_replace>`, `<insert>`) to add or correct the information.
          * Your changes should match the tone and XML-based structure of this document.
          * In your final message to the user, you can briefly mention that you have also updated the project guidelines.
      * **If no change is needed**:
          * It is perfectly acceptable to conclude that the guidelines are up-to-date. Do not force an edit if none is necessary.
          * Simply proceed to report your task as complete.

This final reflection is what makes you a valuable long-term partner for our team. By ensuring the documentation keeps pace with the code, you help us all build better software, faster.
</SelfImprovementProtocol>
</ProjectGovernance>

<GitWorkflow>

### Branching

All branches must follow this pattern: `type/short-description`. For example, `feat/new-agent` or `fix/login-bug`.

### Commits

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Your commit messages must follow this format:

```
<type>(<scope>): <subject>
```

* **type**: Must be one of: `fix`, `feat`, `doc`, `test`, `chore`.
* **scope**: Must be one of the scopes defined in `semantic-pr.yml`.
* **subject**: A short, imperative-tense description of the change, starting with a capital letter.

</GitWorkflow>



<Glossary>
This glossary defines terms, concepts, and technologies that have a specific meaning within the AI-Hub ecosystem. Understanding this language is critical.

| Term                         | Definition                                                                                                                                                                                                                                   |
| :-- | : |
| **AI Assistant** | A reactive, chat-based AI designed for context-aware support. Assistants are purpose-built for specific domains (e.g., Finance, HR) and integrate with enterprise data to answer questions or draft documents, always with human oversight. Represents "Stage 1" of the AI-Hub. |
| **AI Agent** | An autonomous AI designed for proactive process automation. Agents are components in redesigned business processes, working alongside humans to execute tasks. They are "Stage 2" of the AI-Hub's evolution, moving from reactive support to collaborative automation. |
| **Agents Transparency Frontend**| A specialized interface for monitoring and auditing the activities of AI agents. This transparency layer allows stakeholders to inspect agent decisions and review detailed logs, building trust and ensuring compliance. |
| **Event** | The atomic unit of communication within our event-driven architecture. It is a Pydantic model representing a specific occurrence, such as `UserMessageEvent` or `ThoughtEvent`. |
| **Run** | A single, traceable execution of an agent's workflow, beginning with a `StartEvent` and ending with a `StopEvent`. It has an ephemeral `RunContext` for its state. |
| **Scopes** | The top-level folders within the `aihub-core` repository that represent a specific component or microservice (e.g., `aihub_agent`, `aihub_api`). Each scope is a self-contained Python package. |
| **Thread** | A logical grouping of multiple **Runs** that form a continuous conversation. It maintains state across runs via the persistent `ThreadContext`, allowing for contextual follow-up interactions. |
| **Workflow** | The fundamental design pattern for all AI Agents. A task is broken down into a series of structured, explicit `@step`-decorated methods. This ensures testability and transparency. |
</Glossary>