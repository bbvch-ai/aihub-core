# AI-Hub Developer's Guide

## 1. Foundational Knowledge

This section provides the high-level context needed to understand the project's architecture and terminology.

### Introduction

You are an AI coding assistant contributing to the **AI-Hub**, a platform designed to accelerate the development of reliable and scalable AI solutions. Your primary function is to understand our architecture and standards and to write high-quality, idiomatic code that integrates seamlessly into our ecosystem.

### Project Structure

The project is a monorepo containing multiple Python packages ("scopes"). Placing code in the correct scope is critical.

- `aihub\_lib`: The foundational shared library. If code is used by more than one other service, it belongs here.
- `aihub\_agent`: Contains all agent logic and workflow definitions.
- `aihub\_api`: The main user-facing REST API (FastAPI) and WebSocket gateway.
- `aihub\_process`: Orchestrates high-level business processes involving agents, humans, and programs.
- `aihub\_pipeline`: Data ingestion and processing pipelines using Dagster.
- `aihub\_web`: The Nuxt.js frontend application.
- `aihub\_action`: Contains reusable GitHub Actions for CI/CD workflows.
- `aihub\_bot`: Provides the core logic for building and integrating chatbots with platforms like MS Teams.
- `aihub\_doc`: Holds all project documentation.
- `aihub\_iac`: Defines and manages cloud infrastructure as code.

-----

## 2. Project Governance & Git Workflow

This section outlines the rules and processes that govern contributions, decision-making, and repository management.

### Architectural Decision Records (ADRs)

To ensure our architecture evolves consistently, we document all significant technical decisions using an Architectural Decision Record (ADR) process.

#### Consultation Protocol

Before you make any significant change, you **must** consult the existing ADRs in `aihub_doc/arc42/decisions/` to ensure your change does not conflict with a past decision. A "significant change" includes adding major dependencies, introducing new tools, or altering fundamental architectural patterns.

#### Documentation Protocol

If your task requires a new "significant decision," you **must** document it by creating a new ADR file in `aihub_doc/arc42/decisions/`.

- **Naming Convention**: `YYYY_MM_DD_short-decision-summary.md`
- **Template**:
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

### Git Workflow (Branching & Conventional Commits)

#### Branching

All branches must follow this pattern: `type/short-description`. For example, `feat/new-agent` or `fix/login-bug`.

#### Commits

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Your commit messages must follow this format: `<type>(<scope>): <subject>`

-  **type**: Must be one of: `fix`, `feat`, `doc`, `test`, `chore`.
-  **scope**: Must be one of the scopes defined in `semantic-pr.yml`.
-  **subject**: A short, imperative-tense description of the change, starting with a capital letter.

-----

## 3. Local Development Setup

Follow these steps to prepare your local machine for development.

### 3.1 Start the Infrastructure Stack (Docker)

To run the full AI-Hub stack locally, use Docker Compose to start the required services. We provide several files for different configurations:

-  `docker-compose.yml`: The base configuration for CPU-based environments.
-  `docker-compose-gpu.yml`: Adds GPU support.
-  `docker-compose-webui.yml`: Adds the OpenWebUI interface.
-  `milvus-standalone-docker-compose.yml`: Provides a standalone Milvus instance.

Choose the command based on your hardware:

**CPU Environment**:

```bash
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

**GPU Environment**:

```bash
docker compose -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml -f docker-compose-gpu.yml up -d
```

**Important**: Wait for all services to become healthy (`docker ps`) before proceeding.

### 3.2 Activate a Scope's Environment (Poetry)

Each scope (e.g., `aihub_agent`) has its own isolated Poetry environment. You **must** run commands from within the correct scope's activated environment.

**Critical: Poetry Shell Activation**
Before running any commands in a scope, activate its Poetry shell:

```bash
cd aihub_agent
poetry shell
# Now you can run: make format, pytest, etc.
```

-----

## 4. The Core Development Cycle

This section walks through the step-by-step process for making and verifying code changes. This is the central loop of your day-to-day work.

### Step A: Understand the Goal & Context

Before writing any code, internalize the task and its place in the project.

-  **Analyze the Request**: What is the core task?
-  **Review Project Documentation**: Consult `/aihub_doc` for architectural context and existing ADRs.
-  **Check the `git diff`**: If on a feature branch, run `git diff main...` to see existing changes.
-  **Explore the Filesystem**: Use `ls -R` and analyze key files like `pyproject.toml` to understand dependencies and patterns.

### Step B: Write & Document Code (Coding Standards)

Adherence to these standards is mandatory and enforced by CI.

#### Formatting and Linting

-  **Black**: Used for code formatting with a line length of **120 characters**.
-  **Ruff**: Used for linting. We enforce the rules: `select = ["E", "F", "UP", "I"]` (Pyflakes errors/warnings, pyupgrade, isort).
-  **MyPy**: Used for static type checking in `strict = true` mode.

#### Docstrings

All public classes, methods, and functions **must** have a multi-line docstring explaining their purpose, context, and usage.

**Good Example**:

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

#### Comments

Comments should explain the *why*, not the *what*. Code should be self-documenting.

**Good Example**:

```python
# We wait briefly here to allow all processes to respond to the broadcast.
await sleep(1)
```

#### Type Annotations

Use strict, specific type hints for all variables, arguments, and return types, leveraging the `typing` module extensively for `Annotated` or `Generic` but
using `list[int]` instead of `typing.List[int]` or `int | None` instead of `typing.Optional[int]` or `typing.Union[int, None]`.

**Good Example**:

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

### Step C: Test Your Implementation (Testing Protocols)

New functionality should be accompanied by new tests. Modified functionality must pass all existing relevant tests. Ensure the local Docker environment is running for integration tests.

#### Pytest & Markers

Standard unit and integration tests are written with `pytest`. We use markers to categorize tests.

-  **Markers**: `azure`, `self_hosted`, `slow`, `integration`.
-  **Running Local Tests**: To run tests locally without cloud dependencies, exclude the `azure` marker.
    ```bash
    # From within an activated poetry shell (e.g., in aihub_lib)
    poetry run pytest -k "not azure"
    ```

#### Behavior-Driven Development with Pytest-BDD

This is our primary testing method for agent and process **workflows**. However, the underlying `python-bdd` library does not really support async testing. 
It can be patched to some degree using `pytest-asyncio` but it remains clumsy. Hence, for truly async tests, we use `pytest` directly.

- **Structure**: A `.feature` file in `tests/features/` describes scenarios in Gherkin syntax. A corresponding `test_*.py` file implements the steps using `@given`, `@when`, and `@then` decorators.
- **Example Feature**:
  ```gherkin
  Feature: Simple Agent
    Scenario: Test Simple Agent with a specific payload
      Given a SimpleAgent runner
      When the start event is sent with payload "Hello"
      Then a StartEvent is present with payload "Hello"
  ```

### Step D: Finalize with Makefile Commands

Each scope, and the root directory, has a `Makefile` for common tasks. Run these from an activated Poetry shell.

- **`make pr-ready`**: **Run this before finalizing changes.** It runs formatting and linting (`ruff format` and `ruff check --fix`) to ensure code quality.
-  `make format`: Formats code.
-  `make lint`: Lints code.
-  `make test`: Runs local tests (`-k "not azure"`).
-  `make test-cov`: Runs tests and generates a coverage report.

The root-level `Makefile` can run these tasks across all scopes simultaneously.

### Step E: Keep This Guide Updated (Self-Improvement Protocol)

This is the final, critical step. Before reporting a task complete, you **must** reflect on your work and update this document.

1.  **Review Your Work**: Recall the steps you took, problems you solved, and commands you ran.
2.  **Read This Guide**: Re-read the relevant sections of this document.
3.  **Compare & Reflect**: Ask yourself:
    -  Was any information **missing** that I had to discover on my own?
    -  Was any instruction **unclear** or could be improved with a better example?
    -  Was any information **wrong** or outdated compared to the codebase?
4.  **Take Action**: If you identified a gap or error, edit this document to correct it. If the guide is accurate, no change is needed. This ensures our documentation evolves with our code.
