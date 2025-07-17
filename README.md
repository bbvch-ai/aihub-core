---
title: "Dev Documentation"
index: 2
---

# AI-Hub Developer Guide

## Introduction

### What is AI-Hub?

The AI-Hub is a foundational software framework designed to be a central platform that serves as a bridge between people, enterprise knowledge, and digital processes. Instead of forcing employees to switch to special applications for AI support, the AI-Hub's core principle is to bring focused, specialized intelligence directly into familiar work environments like Microsoft Teams or Slack. It enables the creation of a rich ecosystem of specialized AI assistants, each with deep expertise in a specific domain.

To meet increasingly sophisticated business needs, the AI-Hub is delivered in a series of evolving tiers:

1.  **Basic Tier:** This tier provides company-wide access to advanced large language models (LLMs) like GPT through a modern web interface. It allows users to manage chats and leverage features such as voice input/output and image generation in a secure, experimental environment.
2.  **Basic+ Tier:** Extends the platform's reach by offering API integrations with collaboration tools such as Microsoft Teams, Slack, and email, embedding AI interactions directly into daily workflows.
3.  **Assistant Package:** In this tier, custom AI assistants are developed to provide reactive, chat-based support tailored to an organization’s unique processes. These assistants are context-aware and include a transparency module so users can trace how answers were generated and which data sources were used.
4.  **Agentic Process Automation:** This is the most advanced tier, focusing on building autonomous AI agents that proactively participate in business processes. It reimagines workflows as a deep collaboration between humans, specialized AI agents, and external programs to get things done. Agents are designed to analyze workflows, autonomously determine process steps, and execute tasks with minimal human intervention, while human oversight is maintained for critical decisions.

Across all tiers, the AI-Hub provides a unified user interface, ensuring a consistent experience whether a user is interacting with a base LLM, a custom assistant, or an autonomous agent.

> **Note on Terminology:**
> * **AI Assistants** are custom-developed, reactive solutions that provide context-aware support when prompted by a user.
> * **AI Agents** are built for autonomous process automation. They proactively monitor and execute tasks within a collaborative process, often with minimal human intervention required for their steps.

### 1.2. Core Concepts & Philosophy

The AI-Hub is built on two fundamental philosophies: first, that agents should be structured as controllable workflows, and second, that AI adoption is an evolutionary journey from simple assistance to autonomous process automation.

**AI Agents as Structured Workflows**
Rather than building agents as monolithic, open-ended entities, the AI-Hub implements them as step-by-step workflows. This approach combines the determinism of traditional algorithms with the reasoning power of AI, providing several key benefits:
* **Testability:** Each step in the workflow can be tested and validated independently.
* **Traceability:** The entire process is visible and auditable, making it clear why an agent took a certain action.
* **Controlled Autonomy:** It ensures the agent follows business rules and moves from one well-understood step to the next, preventing unpredictable behavior. This allows organizations to harness AI benefits without relinquishing oversight.

**The Two Evolutionary Stages**
The AI-Hub is designed to grow with an organization's needs, following a two-stage evolution.

* **Stage 1: Reactive AI Assistants – Specialized Support**
    In the first stage, the focus is on integrating specialized, purpose-built AI assistants into daily work. Instead of generic "do-everything" bots, this stage promotes an ecosystem of experts, such as a finance assistant for financial data or an HR assistant for policy questions. These assistants are reactive, providing context-aware support when prompted by a user within their existing tools. They do more than just retrieve information; they can interact with business applications, trigger authorized workflows, and coordinate with other assistants, all while operating within strictly defined permission boundaries.

* **Stage 2: Agentic Process Automation – Rethinking Enterprise Processes**
    The second stage goes beyond reactive assistance to fundamentally rethink business processes as a dynamic interplay between humans, purpose-built AI agents, and traditional automation tools. This stage is not about simply digitizing old processes but redesigning them as hybrid workflows where each step is assigned to the most suitable actor—be it a human for critical decisions, an automation tool for deterministic tasks, or a specialized AI agent for steps requiring intelligent analysis. This creates a true collaboration where agents proactively execute tasks and move processes forward, while humans remain in control for approvals and creative or strategic work.

-----

## 2. Project Structure & Repositories

### 2.1. Repository Types: Core vs. Customer

The AI-Hub ecosystem uses two types of repositories:

* **Core Repository**: Named **`aihub-core`**, this repository contains all shared functionality and code used across multiple projects. Under no circumstances should it contain any customer-specific information. This separation is critical to prevent information leakage, as `aihub-core` is referenced by customer-specific repositories.
* **Customer Repositories**: Named using the format **`aihub-<CUSTOMER>`**, these repositories build on the functionality provided by `aihub-core` while adding or overriding components for a specific customer's context.

### 2.2. Monorepo Scopes (Project Structure)

The project is a monorepo containing multiple Python packages, referred to as "scopes". Placing code in the correct scope is critical for maintaining the architecture. Whether in the core or a customer repository, you will find the same top-level folders. In the `aihub-core` repository, each scope is prefixed with `aihub_` (e.g., `aihub_agents`, `aihub_api`).

The primary scopes and their purposes are:

* **`aihub_action`**: Contains reusable code for GitHub Actions used in the CI/CD pipelines of customer repositories. Managing these actions in the core repository helps to avoid duplication and reduces maintenance overhead.
* **`aihub_agents`**: Contains all agent-specific logic and workflow definitions.
* **`aihub_api`**: Contains the main user-facing REST API, built with FastAPI, and the WebSocket gateway.
* **`aihub_bot`**: Provides the core logic for building and integrating chatbots with platforms like MS Teams.
* **`aihub_doc`**: Holds all project documentation, including arc42 documentation and Architectural Decision Records (ADRs).
* **`aihub_iac`**: (Infrastructure-as-Code) Defines and manages reusable cloud infrastructure resources that can be used by customer repositories.
* **`aihub_lib`**: The foundational shared library. If code is used by more than one other service, it belongs here.
* **`aihub_pipeline`**: Contains definitions for data ingestion and processing pipelines, typically using Dagster.
* **`aihub_process`**: Orchestrates high-level business processes that involve a collaboration between agents, humans, and programs.
* **`aihub_web`**: Contains the frontend application code, built with Nuxt.js.

-----

## 3. Getting Started: Local Development Setup

This chapter outlines the technologies used in the AI-Hub and the necessary steps to set up the development environment from the command line. It is up to the developer to install the required tools according to their operating system and preferences.

### 3.1. Required Technologies

The AI-Hub project utilizes the following technologies. Ensure they are installed and accessible from your command line environment.

  * **Git**: For version control.
  * **Python**: The project is built on Python, specifically version 3.11.
  * **Poetry**: For dependency management and managing virtual environments for each Python package.
  * **make**: Used for running common tasks and commands defined in Makefiles.
  * **Docker & Docker Compose**: For containerizing and running the project's infrastructure stack.
  * **Node.js**: The LTS version is used for frontend development, managed via a version manager like NVM.
  * **Azure CLI**: For interacting with Microsoft Azure resources.
  * **Other Tools**: For specific tasks, developers may also need tools like **Postman** for API testing, **MongoDB Compass** for database management, and the **Bot Framework Emulator** for testing chatbots.

### 3.2. Codebase & Dependency Setup

#### 3.2.1. Clone Repositories

First, clone the necessary repositories into your local workspace.

  * **aihub-core**: `git clone https://github.com/bbvch-ai/aihub-core`
  * **aihub-bbv**: `git clone https://github.com/bbvch-ai/aihub-bbv`

#### 3.2.2. Install Project Dependencies

The project is a monorepo containing multiple packages ("scopes"), such as `aihub_agent` or `aihub_api`. Each scope has its own isolated Poetry environment and dependencies.

To work on a specific scope, you must first activate its environment:

1.  Navigate into the scope's directory (e.g., `cd aihub_agent`).
2.  Activate the environment using the command: `poetry shell`.
3.  Once the shell is activated, install the dependencies with: `poetry install`.

You must run commands from within the correct scope's activated environment. This process needs to be repeated for each scope you intend to work on.

For frontend services (`aihub_web`), follow the setup instructions in that directory's `README.md` file.

#### 3.2.3. Manage Dependencies with Poetry

Use the following commands to manage dependencies within an activated scope environment. Do not edit the `pyproject.toml` or `poetry.lock` files manually.

  * `poetry install`: Installs all dependencies defined in `poetry.lock`.
  * `poetry add <package>`: Adds a new package as a dependency.
  * `poetry remove <package>`: Removes a package.
  * `poetry update`: Updates all dependencies to their latest allowed versions.

### 3.3. Starting the Infrastructure Stack (Docker)

To run the full AI-Hub stack locally, use Docker Compose to start the required services. Several configuration files are provided for different environments. Run the appropriate command from the root of the `aihub-core` repository:

  * **For a CPU Environment**:

    ```bash
    docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
    ```

  * **For a GPU Environment**:

    ```bash
    docker compose -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml -f docker-compose-gpu.yml up -d
    ```

Wait for all services to become healthy (you can check with `docker ps`) before proceeding.

### 3.4. Configure Environment Variables

The project requires environment variables for configuration. You will need to request the `.env` files from the team and place them in the root directories of the relevant backend and frontend projects.


## 4. Project Governance & Work Management

This chapter outlines the rules and processes that govern contributions, technical decision-making, and how development work is managed across the project.

### 4.1. Work Management (Roadmap & Kanban)

The AI-Hub ecosystem uses two main GitHub Projects to manage development and high-level planning. All interactions can be performed via the GitHub CLI (`gh`).

#### 4.1.1. High-Level Planning: `aihub-roadmap`

The `aihub-roadmap` project focuses on high-level planning, covering both customer projects and larger initiatives for the AI-Hub core. Here you will find general project information, goals, and ongoing documentation related to major initiatives.

  * **URL**: `https://github.com/orgs/bbvch-ai/projects/7`
  * **View the roadmap via CLI**:
    ```bash
    # View high-level details of the roadmap project
    gh project view 7 --owner bbvch-ai

    # List all items in the roadmap
    gh project item-list 7 --owner bbvch-ai
    ```

#### 4.1.2. Daily Work: `aihub` Kanban Board

While high-level context lives in the roadmap, actual development tasks are tracked in the `aihub` Kanban Board. Tasks on this board are always linked back to a corresponding item in the `aihub-roadmap` to ensure traceability.

The board uses three primary status columns: **To Do**, **In Progress**, and **Done**. When you begin work on a task, assign it to yourself and move it from "To Do" to "In Progress". Once complete, move it to "Done".

  * **URL**: `https://github.com/orgs/bbvch-ai/projects/2`
  * **Interact with the board via CLI**:
    ```bash
    # List all open issues on the Kanban board that are assigned to you
    gh issue list -R "bbvch-ai/aihub-core" -a "@me" -S "project:bbvch-ai/2"

    # View the details and comments of a specific issue
    gh issue view <issue_number> -c -R "bbvch-ai/aihub-core"
    ```

### 4.2. Architectural Decision Records (ADRs)

To ensure our architecture evolves consistently, all significant technical decisions are documented using an Architectural Decision Record (ADR) process.

#### 4.2.1. Consultation Protocol

Before you make any "significant change," you **must** consult the existing ADRs located in `aihub_doc/arc42/decisions/` to ensure your change does not conflict with a past decision. A significant change includes adding major dependencies, introducing new tools, or altering fundamental architectural patterns.

#### 4.2.2. Documentation Protocol

If your task requires a new significant decision, you **must** document it by creating a new ADR file in the same directory.

  * **Naming Convention**: `YYYY_MM_DD_short-decision-summary.md`
  * **Template**: Use the following markdown template for the new ADR file.
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

-----

## 5. Git & GitHub Workflow

This chapter outlines the rules and processes for source code management, including branching, commit conventions, and pull request procedures.

### 5.1. Branching Strategy

To maintain a clean and manageable repository, we follow a simple branching strategy.

  * **`main` branch**: This is the single long-lived branch, which represents the stable, main line of development.

  * **Feature branches**: All new work, including features, fixes, and chores, must be done on short-lived branches. These branches are created from `main` and merged back into `main` via a pull request. Branch names **must** follow this pattern:

      * `type/short-description`

    Where `type` must be one of `feat`, `fix`, or `chore`.

      * Example feature branch: `feat/new-agent-workflow`
      * Example fix branch: `fix/login-bug-incorrect-redirect`

### 5.2. Conventional Commits & Pull Request (PR) Titles

Both commit messages and Pull Request (PR) titles **must** follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This ensures a clear and descriptive history that can be easily parsed.

The format is: `<type>(<scope>): <subject>`

  * **`type`**: Must be one of: `fix`, `feat`, `test`, `doc`, `chore`.
  * **`scope`**: Describes what part of the codebase is affected, such as a package name, customer, or initiative (e.g., `aihub`, `api`, `fmh`).
  * **`subject`**: A short, imperative-tense description of the change.

**Examples**:

  * `fix(aihub): Fix bug where old messages can't be edited anymore`
  * `feat(fmh): Add new tariff validation rule for medical billing`

### 5.3. GitHub CLI Integration

All GitHub-related operations should be performed using the GitHub CLI (`gh`) tool rather than the web interface. This ensures consistency and enables automation.

  * **Create a Pull Request**:

    ```bash
    # Create a new PR with a title and body
    gh pr create --title "feat(api): Add new endpoint for user profiles" --body "This PR introduces..."
    ```

  * **View Pull Requests**:

    ```bash
    # See the current status of all PRs in the repository
    gh pr status

    # List all PRs that you have authored
    gh pr list --author "@me"
    ```

  * **Review a Pull Request**:

    ```bash
    # Check out a PR locally to test it
    gh pr checkout <pr_number>

    # View the details and changes of a PR in the terminal
    gh pr view <pr_number> --web

    # Approve a PR
    gh pr review <pr_number> --approve --body "LGTM!"
    ```

  * **Merge a Pull Request**:

    ```bash
    # Merge a PR after it has been approved and all checks have passed
    gh pr merge <pr_number> --squash
    ```

### 5.4. Branch Protection Rules

To ensure the stability and integrity of our codebase, the `main` branch is protected by the following rules.

  * **Require a Pull Request Before Merging**: All changes must be made through a pull request. Direct pushes to `main` are blocked.
      * **Required Approvals**: At least **one** approving review is required before merging.
      * **Dismiss Stale Approvals**: When new commits are pushed to the branch, previous approvals are dismissed and a new review is required.
      * **Require Conversation Resolution**: All comments and discussions on the PR must be resolved before merging.
  * **Require Linear History**: This rule disallows merge commits, keeping the repository history clean and easy to follow.
  * **Allowed Merge Method**: Only **Squash Merging** is enabled. This means all commits from a feature branch are squashed into a single commit when merged into `main`. This keeps the history of the `main` branch concise and linear.
  * **Block Force Pushes and Deletions**: Force pushing to `main` is denied to preserve commit history. Deleting the `main` branch is also restricted.


-----

## 6. Testing In-Depth

This chapter describes the testing frameworks and philosophies used in the AI-Hub project. While comprehensive testing is a core part of our development cycle, we do **not** follow a strict Test-Driven Development (TDD) methodology.


### 6.1. Pytest & Markers

**`pytest`** is the standard testing framework for the AI-Hub project. Tests are located in a `tests` directory at the same level as the code being tested. All test files must be prefixed with `test_`, such as `test_<unit_being_tested>.py`.

To better categorize tests, we use `pytest` markers. This allows us to selectively run or exclude certain types of tests. Common markers include:

* `azure`
* `self_hosted`
* `slow`
* `integration`


### 6.2. Behavior-Driven Development (BDD) with pytest-bdd

For testing agent and process workflows, we try to use **Behavior-Driven Development (BDD)** with the `pytest-bdd` plugin. BDD provides a structured way to write tests that are easily understandable by both technical and non-technical team members.

However, `pytest-bdd` does not fully support `async` testing, which can be clumsy. Therefore, for truly asynchronous tests, we often fall back to using **`pytest` directly**.

#### How It Works

The BDD process involves two main components:

1.  **Feature Files**: Written in Gherkin syntax (`.feature`), these files describe a feature and its scenarios in plain English. They are located in the `tests/features/` directory.
2.  **Step Definitions**: These are Python functions that implement the steps defined in the feature files. They use decorators like `@given`, `@when`, and `@then` to link the code to the Gherkin steps.

Tests are structured into three parts: `Given` (setup), `When` (execute), and `Then` (assert).

#### Why We Use BDD

When possible, we favor BDD for several key reasons:

* **Readable Tests**: Scenarios written in plain language allow non-technical stakeholders to validate requirements.
* **Reusability**: Step definitions can be shared across multiple scenarios, which reduces code duplication.
* **Faster Iterations**: New test cases can often be added by writing new Gherkin scenarios without needing new Python code.
* **Closer Collaboration**: The process encourages collaboration between business, QA, and development teams.


-----

## 7. Code Conventions

Adherence to a consistent coding standard is critical for maintaining the quality, readability, and long-term maintainability of the AI-Hub codebase. The following conventions are not optional; they are strictly enforced by our CI/CD pipelines.

### 7.1 Formatting, Linting, and Type Checking

We use a specific set of tools to automate code formatting, enforce style rules, and perform static analysis.

  * **Code Formatter: Black**

      * **Rule**: All Python code is formatted using the `black` code formatter.
      * **Configuration**: The line length is set to **120 characters**. No other configuration is changed from the default.

  * **Linter: Ruff**

      * **Rule**: We use `ruff` for high-performance linting and import sorting.
      * **Configuration**: We enforce a specific set of rules: `select = ["E", "F", "UP", "I"]`.
          * `E`/`F`: Catches errors and warnings from Pyflakes (e.g., unused imports, undefined names).
          * `UP`: Includes rules from `pyupgrade` to enforce modern Python syntax.
          * `I`: Enforces import sorting, handled automatically by Ruff.

  * **Static Type Checker: MyPy**

      * **Rule**: We use `mypy` for static type checking to catch type-related errors before runtime.
      * **Configuration**: Type checking is run in `strict = true` mode, which enforces the highest level of type safety.

### 7.2 Enforcement via Makefile

While these checks run automatically in our CI pipeline, you **must** run them locally before committing your code. Each scope (and the root directory) contains a `Makefile` with the necessary commands. Always run these from within an activated Poetry shell.

  * `make format`: Formats all code in the current scope using **Black**.
  * `make lint`: Lints all code using **Ruff** and runs **MyPy** for type checking.
  * `make pr-ready`: This is the **most important command**. It runs both `make format` and `make lint` with auto-fixing capabilities (`ruff check --fix`). Run this command to ensure your code is 100% compliant before creating a pull request.

### 7.3 Naming Conventions

  * **Files and Directories**: All Python files and directory names must use `snake_case`.
      * Example file: `agent_workflow_manager.py`
      * Example directory: `workflow_steps`
  * **Test Files**: All test files must be prefixed with `test_` and follow the `snake_case` convention.
      * Example: `test_agent_workflow_manager.py`

### 7.4 Docstrings and Comments

  * **Docstrings**: All public modules, classes, methods, and functions **must** have a multi-line docstring that clearly explains their purpose, context, and usage. This is crucial for maintainability and for others to understand your code.

    ```python
    class AgenticProcess:
        """
        Manages the lifecycle of an agentic process from instantiation to completion.

        This class orchestrates the flow of events between different actors (agents, humans, programs)
        and ensures that the process adheres to its predefined workflow definition.
        """
    ```

  * **Comments**: Comments should explain the **why**, not the **what**. Write your code to be as self-documenting as possible, and use comments only to clarify complex logic, business rules, or the reasoning behind a specific implementation choice.

    ```python
    # Incorrect: "what" the code does
    # Increment the counter
    i += 1

    # Correct: "why" the code does it
    # We must wait for the event to propagate before proceeding to avoid a race condition.
    await asyncio.sleep(0.1)
    ```

### 7.5 Type Annotations

Strict and specific type hints are mandatory.

  * **Rule**: All variables, function arguments, and return values must have type annotations.

  * **Style**: Use modern standard library types where possible (e.g., `list[int]` instead of `typing.List[int]`, and `int | None` instead of `typing.Optional[int]`).

  * **Advanced Types**: For more complex scenarios, use the advanced types available in the `typing` module, such as `Annotated`, `TypeVar`, and `Generic`.

    ```python
    from typing import Annotated
    from fastapi import Depends

    # Good example demonstrating modern type hints and advanced usage
    async def get_user_data(
        user_id: int | None,
        token: Annotated[str, Depends(oauth2_scheme)]
    ) -> dict[str, str | int]:
        """Fetches user data based on an ID and an authentication token."""
        if user_id is None:
            return {}
        # ... logic to fetch data
        return {"user_id": user_id, "name": "Example User"}
    ```

-----

## 8. The Core Development Cycle

This chapter outlines the standard, step-by-step process for every development task. Following this cycle ensures that all work is done consistently, contextually aware, and meets our quality standards.

### Step 1: Understand the Goal and Context

Every development task begins with a clear goal, typically provided as a GitHub issue number. You must first understand the task's requirements and its place within the broader project roadmap.

Your task's issue title will often contain a prefix in brackets (e.g., `[process]`) that links it to a larger initiative on the `aihub-roadmap`. You can view the roadmap using the `gh` CLI:

```bash
gh project item-list 7 --owner bbvch-ai --limit 100
```

This command will show the high-level initiatives:

```
> Issue  🗺️ Infrastructure [infra]                           375      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgbcrk4
> Issue  🗺️ Spike Container Deployment [container]             422      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgcQbYQ
> Issue  🗺️ Agentic Process Automation [process]               442      bbvch-ai/aihub-core  PVTI_lADOCmtSJM4ArqDTzgcTfWw
```

By fetching the main initiative issue (e.g., \#442), you can gain more insight into the overall goal and see how your specific task fits in with related issues.

```bash
gh issue view 442 -c -R "bbvch-ai/aihub-core"
```

This gives you the context and a checklist of related tasks, helping you to understand the full picture before you begin.

### Step 2: Prepare Your Workspace

Before writing any code, check your local environment.

1.  **Check your current branch**. If you are on `main`, create a new branch that follows the naming convention outlined in Chapter 6 (e.g., `feat/new-process-feature`).
2.  **Review existing work**. If you are already on a feature branch, run `git diff main...` to see what changes have already been made on that branch.

### Step 3: Plan and Implement Your Solution

1.  **Plan your implementation**. Think through the changes you need to make before writing code.
2.  **Choose the correct scope**. It is critical that you place your code in the correct package (`aihub_lib`, `aihub_agent`, `aihub_api`, etc.). If code is used by more than one service, it belongs in `aihub_lib`.
3.  **Write the code**. As you implement your solution, rigorously follow all rules defined in **Chapter 9: Code Conventions**.

### Step 4: Verify Code Quality

Once you have a working implementation, you must run our automated formatting and linting tools to ensure your code is 100% compliant with our standards.

From within the activated Poetry shell of the scope you worked on, run:

```bash
make pr-ready
```

This command will automatically format your code and report any linting or type errors that need to be fixed.

### Step 5: Write and Run Tests

Our approach to testing is pragmatic.

  * **Writing new tests**: You are not required to write tests for every change, as we do not aim for 100% test coverage. However, if it is easy and straightforward to write a test for your new code, you should do so. Only write complex tests if you are specifically instructed to.
  * **Running all tests**: Whether you have written a new test or not, you **must** run the entire local test suite to ensure your changes have not broken any existing functionality. Tests must always pass before you consider your work complete.

To run the local test suite, use the command:

```bash
make test
```

-----

## 9. Documentation and Self-Improvement

A key principle of the AI-Hub project is that documentation must evolve with the code. This chapter outlines our documentation philosophy and the process every developer must follow to ensure our documentation remains accurate, helpful, and up-to-date.

### 9.1. Documentation Philosophy

We follow a **README.md-only** documentation principle. All project documentation resides in one of two places:

1.  **Code Docstrings**: For documentation that is specific to a single class, method, or function, we use detailed docstrings directly in the implementation file. This is the most common form of documentation.
2.  **README.md Files**: For documentation that holds true for a larger part of the codebase (a specific folder, a scope, or the entire project), we use `README.md` files.

These README files are hierarchical. A `README.md` can exist at the project root, within each scope (e.g., `aihub_agent/README.md`), or even in nested sub-folders. This allows us to provide context at the most appropriate level.

It is critical that these files are kept up-to-date and are well-written, as we use them to automatically generate a developer documentation site with VuePress.

### 9.2. The Self-Improvement Protocol

This is the final, critical step of the development cycle. Before you consider a task complete, you **must** reflect on your work and its impact on the documentation. This is not optional; it is essential for the long-term health of the project.

After implementing your changes, ask yourself the following questions:

* **Does my change make existing documentation inaccurate?**
    If your code change implies that a section in a `README.md` is now out of date or incorrect, you must adapt that README to align with your changes.

* **Is there missing information that would have helped me?**
    If you had to discover important information on your own that was not documented, you must add it. Either extend an existing `README.md` or create a new one at the appropriate level (folder, scope) to share this knowledge.

* **Did the documentation conflict with the code?**
    If you found information in a `README.md` that was wrong, you must correct or remove it. In this project, the **code is always the ground truth.**

-----


## 10. Technical Reference

This chapter provides a reference for the project's package management strategy and the technologies used in the stack.

### 10.1. Package Management & Versioning

#### 10.1.1. Package Structure

The AI Hub consists of multiple packages that handle specific functionalities:
* `aihub_agents`: Contains common code for agent development.
* `aihub_api`: Contains common code for API implementation.
* `aihub_bot`: Contains common code for bot development.
* `aihub_pipeline`: Contains common code for pipeline development.
* `aihub_lib`: A foundational library containing code that is relevant for multiple other packages. The `aihub_lib` package is used by all other packages.

#### 10.1.2. Versioning and Referencing

All packages have versions that are increased in sync with the tags in the repository. This means a package's version is updated with every merge into the main branch.

By default, packages reference `aihub_lib` via its Git URL in the `pyproject.toml` file, which allows versioning to be handled by Git tags. For local development, it is possible to switch to a local version of the core library by running the command `make use-local-core`. For deployment, the reference is switched back to the GitHub repository, specifying the version by its tag.

### 10.2. Technology Stack

The AI-Hub is built on a flexible architecture that can integrate with various LLMs and databases.

#### 10.2.1. Base Technologies

| Category | Technology Used | Description | Alternatives |
| :--- | :--- | :--- | :--- |
| **Python AI Framework** | [Llama-Index](https://www.llamaindex.ai/) | A rapidly evolving framework for using AI capabilities that is close to research and quickly adapts new approaches. A downside is that its rapid development can lead to regular major changes and occasional bugs. | [Langchain](https://www.langchain.com/) |
| **Tracing** | OpenTelemetry | An observability framework for cloud-native software that provides components to capture distributed traces and metrics. | ... |
| **Tracing Explorer** | [Arize Phoenix](https://phoenix.arize.com/) | A tool for exploring and visualizing distributed traces captured by OpenTelemetry. | ... |
| **Ingestion Pipeline Orchestrator**| [Dagster](https://dagster.io/) | A workflow management system for building and managing complex data processing pipelines. | ... |
| **Version Control System**| GitHub | A web-based platform for version control and collaboration. | ... |
| **IDE** | PyCharm, WebStorm | Integrated Development Environments for writing and testing code. | ... |
| **Container Orchestration**| Docker, Docker-Compose| Tools for building, deploying, and managing containerized applications. | ... |
| **CI/CD** | GitHub Actions | A cloud-based automation platform to build, test, and deploy code directly from GitHub. | ... |
| **Code Quality** | [SonarCloud](https://sonarcloud.io/) | A cloud-based code quality and security tool that analyzes code and provides insights for improvement. | ... |
| **Testing** | PyTest, pytest-bdd | PyTest is a popular Python testing framework. pytest-bdd is a plugin for PyTest that enables Behavior-Driven Development (BDD). | ... |
| **Testing (Frontend)**| Playwright | A framework for end-to-end (E2E) testing of web applications. | Cypress, Selenium |
| **Identity Management**| MSAL / Entra ID | Libraries and services for managing user authentication and authorization. | ... |

#### 10.2.2. On-Premises Technologies

| Category | Technology Used | Description |
| :--- | :--- | :--- |
| **Vector Database** | Milvus, PG-vector | Milvus is an open-source vector database. PG-vector is a plugin for Postgres databases that converts them into vector databases. |
| **LLM** | LLaMA, Mistral, Phi | Large language models that can be deployed on-premises. |
| **LLM Server** | llama.cpp, vllm | Open-source projects providing server-based deployment of large language models. |
| **Database (NOSQL)** | MongoDB | A NoSQL database used for storing agent definitions. |
| **Database (SQL)** | Postgres | An open-source SQL database that can run in Docker containers. |
| **Voice Input** | Whisper.cpp | An open-source speech recognition model that can be deployed on-premises. |
| **App-Environment** | Docker | Used for creating reproducible application environments. |
