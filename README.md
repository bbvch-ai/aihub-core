# AI Hub

Table of Content:

- [AI-Hub Developer Introduction](#1-ai-hub-developer-introduction)
- [Getting Started](#2-getting-started)
- [Testing](#3-testing)
- [Additional Infos](#4-additional-infos)

# 1 AI-Hub Developer Introduction

Welcome to the AI-Hub project! This document provides an overview of the AI-Hub platform, its key features, and
technical aspects for developers.

## 1.1 What is AI-Hub?

The AI-Hub is more than just a code repository; it is a carefully crafted and evolving platform that encapsulates
best practices, standardizes common functionalities, and allows bbv to deliver AI solutions with greater agility and
reliability. As you progress through the subsequent sections—for instance, understanding the deeper reasoning behind
AI agents in Section 1.2 or the foundational principles of how the AI-Hub approaches workflows and autonomy in Section
2—you will see how the core ideas introduced here form the bedrock of the entire AI-Hub ecosystem.

For further information, please refer to the AI-Hub Documentation:

1. [Introduction](aihub_doc/1_introduction.md)
2. [Core Concepts and Philosophy](aihub_doc/2_core_concepts_and_philosophy.md)
3. [Project Phases and Client Engagement](aihub_doc/3_project_phases_and_client_engagement.md)
4. [Architectural Overview](aihub_doc/4_architectural_overview.md)
5. [Agents in Detail](aihub_doc/5_agents_in_detail.md)
6. [Pipelines](aihub_doc/6_pipelines.md)
7. [Frontend](aihub_doc/7_frontend.md)
8. [Backend / API](aihub_doc/8_backend_api.md)
9. [Tooling, Testing, and CI/CD](aihub_doc/9_tooling_testing_ci_cd.md)
10. [Extensibility and Licensing](aihub_doc/10_extensibility_and_licensing.md)
11. [Best Practices and Guidelines](aihub_doc/11_best_practices_and_guidelines.md)
12. [Roadmap and Initiatives](aihub_doc/12_roadmap_and_initiatives.md)

---

## 1.2 Repositories

There are two types of repositories in the AI-Hub ecosystem:

1. **Core repository**  
   The core repository, named **`aihub-core`**, contains all shared functionality and code used across multiple
   projects. Under no circumstances should it contain any customer-specific information. This separation is critical to
   prevent information leakage because this repo is referenced by customer-specific repositories.

2. **Customer repositories**  
   Customer repositories are named **`aihub-<CUSTOMER>`**. These repositories build on the functionality provided by
   `aihub-core` while adding or overriding components for the specific customer context.

### 1.2.1 Repository Structure

Regardless of whether you are working in the core repository or a customer repository, you will find the following
top-level folders (or *scopes*). The main difference is that, in `aihub-core`, each folder is prefixed with `aihub_` (
e.g., `aihub_agents`, `aihub_api`, etc.):

- **`agents`**: Contains agent-specific code, such as workflow steps.

- **`api`**: Contains API endpoint definitions.

- **`doc`**: Contains documentation (for example, arc42 documentation).

- **`lib`**: Provides shared functionality that can be reused across multiple scopes within the repository.

- **`pipeline`**: Contains definitions for Dagster pipelines.

- **`web`**: Contains frontend code.

Within a customer repository (`aihub-<CUSTOMER>`), the corresponding scopes will typically import core functionalities
from `aihub-core` as needed. The `lib` folder in each repo may also be consumed by other scopes within the same repo.

#### 1.2.1.1 Additional Scopes (Core Repository Only)

In addition to the folders listed above, the core repository (`aihub-core`) includes the following additional scopes:

- **`aihub_action`**  
  Contains reusable code for GitHub Actions used in the CI/CD pipelines of customer repositories. Managing these actions
  in the core repo helps to avoid duplication and reduces maintenance overhead.

  > ☝ **Note:** This is **not** the same as the `.github` folder.  
  > The `.github` folder contains the actual GitHub Actions and workflows executed in the CI/CD flow for `aihub-core`
  itself.

- **`aihub_iac`**  
  Contains Infrastructure-as-Code (IaC) resources that can be reused by customer repositories.

---

## 1.3 Project and Work Management

The **AI-Hub** ecosystem uses two main GitHub Projects to manage development and roadmap planning:

1. **`aihub-roadmap`**  
   Focuses on high-level planning, covering both customer projects and larger initiatives for the AI-Hub core.

2. **`aihub`**  
   Focuses on day-to-day development tasks that contribute to the overall initiatives and customer projects.

### 1.3.1 Types of Projects

We distinguish between two primary types of projects:

1. **Customer Projects**  
   These are engagements specific to a customer. They are often tied to a particular `aihub-<CUSTOMER>` repository but
   may also require changes or enhancements in `aihub-core`.

2. **Initiatives**  
   These can be viewed as large features or focus areas targeted for improvement or creation within the AI-Hub core.
   They are broader in scope than most customer projects and generally aim to advance the platform as a whole.

### 1.3.2 Roadmap Overview ([aihub-roadmap](https://github.com/orgs/bbvch-ai/projects/7))

In the [aihub-roadmap](https://github.com/orgs/bbvch-ai/projects/7) GitHub Project, we manage both **customer projects**
and **initiatives**. Here, you will find:

- **General Project Information**: Owner, Project Manager, Development Lead, etc.
- **Project Goal & Initial Setup**: Defined in the main issue describing the project or initiative.
- **Ongoing Documentation**: All major events, decisions, and outcomes are recorded in the issues.
- **Project Health States**:
    - **In Schedule**: Work is proceeding as planned.
    - **Tight Schedule**: There is a risk of falling behind schedule.
    - **Behind Schedule**: The project or initiative has already fallen behind planned milestones.
    - **Schedule Impossible**: The current timeline can no longer be met without major changes.

At the end of a project or initiative, the main issue can also serve as a record of **learnings**, providing valuable
insights for future work.

### 1.3.3 Daily Work Management ([aihub](https://github.com/orgs/bbvch-ai/projects/2))

While the high-level status and context of projects or initiatives live in `aihub-roadmap`, the actual development tasks
are tracked in the [aihub](https://github.com/orgs/bbvch-ai/projects/2) GitHub Project. Tasks in `aihub` may span
multiple projects or initiatives but are always linked back to the corresponding item in `aihub-roadmap`. This ensures:

- **Traceability**: Developers can see which larger project or initiative their tasks belong to.
- **Alignment**: Project Managers and Dev Leads can monitor progress on overarching goals by reviewing associated tasks.

In each task’s GitHub issue, you should see a reference or link to the main issue in `aihub-roadmap` that tracks the
project or initiative. This linkage helps keep the broader context visible and maintains clarity on priorities.

For day-to-day tasks managed in the `aihub` board, we use three primary status columns:

- **To Do**
- **In Progress**
- **Done**

#### 1.3.3.1 Guidelines

1. **Assigning Tasks**
    - If you start working on a task and it is unassigned, assign yourself to it.
    - Always keep the assignee field up to date to ensure transparency.

2. **Moving Tasks**
    - When you begin work, move the task from **To Do** to **In Progress**.
    - Once you complete the task (and all necessary reviews and merges), move it to **Done**.

This straightforward workflow helps maintain a clear overview of who is working on what, and the current status of
each task. Keeping the board updated is crucial for effective collaboration and progress tracking.

---

## 1.4 Branching Strategy & PR Conventions

Our branching strategy is designed to streamline development by organizing code changes based on customer
projects and internal initiatives. This approach enhances collaboration, simplifies code management,
and ensures that updates are efficiently merged and deployed.

### 1.4.1 Long-Lived Branches

We maintain long-lived branches that correspond to specific customer projects and internal initiatives.
These branches serve as stable bases for ongoing development related to their respective areas.

**Customer Branches:**

- `customer/bbv`, `customer/fmh`, `customer/bs`, ...

**Initiative Branches:**

- `initiative/agent-custom`, `initiative/agent-xp`, `initiative/avatar`, ...

**Short-Lived Branches:**

Short-lived branches are created for specific tasks or fixes and are intended to be merged back into their
originating branch promptly. The naming convention indicates both their origin and intended merge target
using hierarchical names. Due to naming constraints. e.g., not being able to have both a branch and a scope (part before
`/`), we use:

- `quickfix` for target `dev`-branch
- `hotfix` for target `main`-branch

Example 1: `quickfix/fix-message-editing`

*Originates from the development branch.
Intended to be merged back into development.*

Example 2: `hotfix/fix-message-editing`

*Originates from the main branch.
Intended to be merged back into main.*

Example 3: `workflows/hitl`

*Originates from the initiative/workflows branch.
Intended to be merged back into initiative/workflows.*

### 1.4.2 Pull Request Titles

Pull request (PR) titles follow a specific format to indicate:

Why the code was changed (PR-Type):

- `fix`
- `feat`
- `test`
- `doc`
- `chore`

For whom the code was changed (PR-Scope):

- `aihub` *(internal product owner without initiative)*
- `workflows` *(initiative)*
- `fmh` *(customer)*

#### 1.4.2.1 PR Title Format

```txt
type(scope): Description of the change
```

Examples:

- `fix(aihub): Fix bug where old messages can't be edited anymore`
    - Origin: Could be from `chat-xp/message-editing`.
    - Merge Target: `initiative/chat-xp`.
    - > Note: Indicates a fix primarily benefiting our internal product (aihub).

- `fix(siemens): Fix environment variable for D-ID that broke avatars in online setting`
    - Origin: Could be from `quickfix/fix-did` if it's a quick fix.
    - Merge Target: `dev`.
    - > Note: Although originating from `dev`, the PR-scope (`siemens`) indicates it's a fix for Siemens, helping
      prioritize the merge.

### 1.4.3 Benefits of This Strategy

- **Clarity**: Clear branch names and PR titles make it easy to understand the purpose and target of code changes.
- **Efficiency**: By indicating the customer or initiative, we can prioritize merges that are critical for specific
  stakeholders.
- **Flexibility**: Allows for parallel development across different projects and initiatives without conflicts.
- **Traceability**: Enhances the ability to track changes back to their origin, facilitating better project management.

## 1.5 Branch Protection

To ensure the stability and integrity of our codebase, we have implemented branch protection rules for our branches.

### 1.5.1 Main Branch

For the main branch, the following rules apply:

- **Restrict Updates**
    - **Description:** Only users with bypass can push directly.
    - **Reason:** This rule ensures that most contributors can’t directly push to certain critical branches.
      They have to go through a pull request, which requires reviews or checks to pass before merging.
      By limiting who can push directly, we reduce the chance of accidental or unreviewed changes.

- **Restrict Deletions**
    - **Description:** Only users with bypass can delete `main`.
    - **Reason:** Preserves the integrity of the primary branch.

- **Block Force Pushes**
    - **Description:** Denies force-pushes to `main`.
    - **Reason:** Preserves commit history from destructive rewrites. By limiting who can push directly,
      we reduce the chance of accidental or unreviewed changes.

- **Require Linear History**
    - **Description:** Disallows merge commits, enforcing a linear commit history.
    - **Reason:** Keeps the repository history clean and traceable. A linear history is easier to read and navigate,
      since you don’t have merge commits branching off in different directions.

- **Require a Pull Request Before Merging**
    - **Description:** All changes must be introduced via pull requests.
    - **Reason:** Encourages peer review and prevents unauthorized merges.
    - **Approvals**:
        - **Required Approvals**
            - **Config:** At least 1 approving review is needed.
        - **Dismiss Stale Pull Request Approvals**
            - **Config:** New commits dismiss previous approvals which means after new commits are pushed to the branch,
              the
              previous approvals are removed.
        - **Require Conversation Resolution Before Merging**
            - **Config:** All review discussions must be resolved this includes also comments by bots.
        - **Allowed Merge Methods**
            - **Config:** Only `Squash` is enabled. This means that into the main branch only squash commits are
              allowed.
              This means that each pull request is merged as a single commit to the main branch. As a result,
              the commit history remains linear—avoiding merge commits—and each merge is captured as one
              commit representing all changes in that pull request.
              Like this we will later not bloat the main branches' history. There might be the case where we have
              long-running initiative which only should be merged to the main once all features of the initiative are
              done.
              In that case we use the initiative branch and then merge it into main. Since this is considered an
              exception we have to temporarily change the rule for this.

### 1.5.1 Initiative Branch

For the `initiative/*` branches, the same rules apply as for the main branch.

**Important**: Initiative branches should only be used if the features of an initiative can only be merged
once all features are done.

---

# 2 Getting Started

## 2.1 Install Required & Recommended Tools

- **JetBrains Toolbox**: Download the [JetBrains Toolbox](https://www.jetbrains.com/toolbox-app/). Install and manage
  IDEs like PyCharm (backend) and WebStorm (frontend).
    - bbv employees: Request a JetBrains license via [YouTrack](https://youtrack.bbv.ch/newIssue?project=issues) .
- **Git**: You may install it in your IDE under Version Control and link your account (alternatively: download
  it [directly](https://git-scm.com/))).
  JetBrain IDEs have built-in support for Git. You can use the Git integration to commit, push, and pull changes
  directly from the IDE.
- **Python (3.11)** via Miniconda: Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
  Miniconda is a package manager for Python. It is a lightweight version of Anaconda, which is a distribution of Python
  for scientific computing.

  Make sure to add Miniconda to the PATH during installation.
  Test the installation by opening a command prompt and typing `conda --version`. If the installation was successful,
  you should see the version of Miniconda.

  > ☝ **Note: Miniconda for Virtual Environment Only**  
  > We use Miniconda to create virtual environments and install the initial Python version in it. For the package
  management inside the virtual environment, we use poetry. (see below)

- **make (Windows only)**
  You can download `make`
  from [GnuWin32](http://gnuwin32.sourceforge.net/packages/make.htm). Make sure to add the `bin` directory of the `make`
  installation to the PATH.
    - Verify: `make --version`

- **Poetry**: Dependency management tool for Python ([Download Poetry](https://python-poetry.org/docs/)).
    - Verify: `poetry --version`
- **Docker**: Containerization tool ([Download Docker](https://www.docker.com/products/docker-desktop/)). If problems
  occur when trying to run Docker Desktop:
  it says **wsl --update** but running this command doesn't resolve the issue. Refer
  to [WSL Update Failed](https://stackoverflow.com/questions/78879806/docker-desktop-wsl-update-failed)
    - Verify: `docker --version`
- **Node.js (LTS)** through **NVM**: Download and install Node Version Manager (NVM)
  for [Windows](https://github.com/coreybutler/nvm-windows/releases)
  or [Linux](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating). NVM is a version manager for
  Node.js that allows you to install multiple versions of Node.js and switch between them easily.

  After installing NVM, open a new command prompt and type `nvm --version`. If the installation was successful, you
  should see the version of NVM.

  Install the latest LTS version of Node.js by typing `nvm install --lts` in the command prompt. When successful, it
  will finish with a statement like

  ```
  Installation complete. If you want to use this version, type
  
  nvm use 20.16.0
  ```
  Run the `nvm use` command with the version you get indicated. Alternatively, use `nvm list` to see, which versions you
  have installed.

  Test the installation by typing `node --version` and `npm --version`. If the installation was successful, you should
  see the versions of Node.js and npm. If not, type `nvm user --lts` and try again.

- **MongoDB Compass**: GUI for managing MongoDB ([Download MongoDB Compass](https://www.mongodb.com/products/compass)).
- **Azure CLI**: Manage Azure
  resources ([Download Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)).
    - Verify: `az --version`
- **Postman**: For API testing ([Download Postman](https://www.postman.com/)).

### 2.1.1 Optional JetBrains Tools

Useful PyCharm Plugins & Settings

Install the following plugins in PyCharm to make development easier:

- [Github Copilot](https://plugins.jetbrains.com/plugin/17718-github-copilot) - AI coding assistant
- [Database Tools and SQL](https://www.jetbrains.com/help/pycharm/database-tool-window.html) - Interact with MongoDB
  directly within PyCharm. This should be activated by default. To access the database from PyCharm, create a new
  MongoDB connection and paste the connection string from Microsoft Azure. Learn more about the
  setup [here](https://www.jetbrains.com/help/pycharm/mongodb.html).
- [Docker](https://www.jetbrains.com/help/pycharm/docker-containers.html) - Interact with Docker containers within
  PyCharm. This should be activated by default if you have a docker development setup.
- [SonarLint](https://www.sonarsource.com/products/sonarlint/features/jetbrains/) - Extension for checking code quality
  before commiting.

Enable the following settings for optimal developer experience:

- [Black](https://www.jetbrains.com/help/pycharm/2023.2/reformat-and-rearrange-code.html#format-python-code-with-black) -
  Code formatter for Python
- [Code With Me](https://www.jetbrains.com/code-with-me/) - Collaborative development tool, use this to pair-code with
  other AI-Hub developers.

Install the following software for convenience:

- [Microsoft Azure Command Line Interface (CLI)](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli) -
  Run `az` commands from the command-line or Power Shell without using the dedicated Azure Cloud Shell.

### 2.1.2 (Optional) Useful WebStorm Plugins & Settings

Install the following plugins to make development easier:

- [Github Copilot](https://plugins.jetbrains.com/plugin/17718-github-copilot) - AI coding assistant
- [Docker](https://www.jetbrains.com/help/pycharm/docker-containers.html) - Interact with Docker containers within
  WebStorm (only needed if you have a docker development setup).
- [SonarLint](https://www.sonarsource.com/products/sonarlint/features/jetbrains/) extension for checking code quality
  before commiting.

Enable the following settings for optimal developer experience:

- [EsLint](https://www.jetbrains.com/help/webstorm/eslint.html#ws_eslint_configure_run_eslint_on_save) - Code linter for
  JavaScript / TypeScript

### 2.1.3 Setup Auto-Reformat and Lint

#### 2.1.3.1 On Save (PyCharm)

We can set up Pycharm so that whenever a file is saved (Ctrl + S), it is automatically reformatted and linted.

1. Go to **File > Settings > Tools > Actions on Save**.
2. Check the boxes for `Reformat code` and `Run Black`.
3. Click `OK`.

#### 2.1.3.2 Before Commit (PyCharm)

We can set up Pycharm so that before committing changes, the code is automatically reformatted and linted.

1. In the Commit dialog, click on the gear icon next to the Commit button.
2. In the section **Commit Checks**, check the boxes for `Reformat code` and `Perform SonarQube for IDE analysis`.

---

## 2.2 Set Up the Codebase

### **2.2.1 Clone Repositories**

Clone the following repositories:

- **aihub-core**: Core services for the AI-Hub.
    ```bash 
    git clone https://github.com/bbvch-ai/aihub-core
    ```
- **aihub-bbv**: bbv customer repo (for bbv employees only)
    ```bash
    git clone https://github.com/bbvch-ai/aihub-bbv
    ```
- **ai-hub**: Legacy repository
    ```bash
    git clone https://github.com/bbvch-ai/ai-hub
    ```

### **2.2.2 Install Dependencies**

#### 2.2.2.1 Backend Services

Each folder in the `aihub-core` repository represents a **microservice**, which is an independent, self-contained module
designed to handle a specific functionality within the broader system. This modular approach enhances scalability and
maintainability.

1. **Open the `aihub-core` Project (or a Parent Directory)**:

    - Open PyCharm.
    - Navigate to the `aihub-core` directory or any parent directory containing `aihub-core` and open it as the main
      project. Opening a parent directory can help manage additional related projects, such as customer projects, in the
      same workspace.

2. **Attach Microservices as Additional Projects**:

    - For each folder in `aihub-core` containing a `pyproject.toml` file (e.g., `aihub_api`, `aihub_lib`, `aihub_agent`,
      `aihub_pipeline`):
        - Go to **File > Open...**.
        - Select the microservice folder.
        - In the popup, select the **Attach** option to keep all microservices accessible within the same PyCharm
          workspace.

3. **Set Up Poetry Environments for Each Microservice**:

    - For each attached project:
        - Go to **File > Settings > Project:\*\*\*\* > Python Interpreter**.
        - Select the microservice in the left column (e.g., `aihub_agent`).
        - Click on **Add Interpreter > Add Local Interpreter**.
            - **Type**: Poetry
            - **Base interpreter**: Use the Miniconda Python executable (usually found under
              `AppData/Local/miniconda3`).
            - **Poetry executable**: Locate and select the `poetry.exe` file.
        - Apply the settings.
    - Navigate to the microservice directory and run:
      ```bash
      poetry install
      ```
    - *Alternatively*, you can just open any Python file in the microservice, and PyCharm should prompt you to configure
      the Poetry environment based on the project's `pyproject.toml` file.

4. **Repeat for Each Microservice**:

    - Ensure every microservice folder is configured with its own Poetry environment to avoid dependency conflicts. For
      example, if one microservice uses a specific version of a library, it won't interfere with others.

5. **Add `aihub_lib` dependency to other services**:

    - Go to **File > Settings > Project:\*\*\*\* > Project Dependencies**.
    - Add `aihub_lib` as a dependency to each microservice project (`aihub_api`, `aihub_agent`, `aihub_pipeline`).

##### 2.2.2.1.1 Poetry Commands

- `poetry install` to install the dependencies
- `poetry add <package> --group dev` to install the dev-dependencies
- `poetry add <package>` to add a new package
- `poetry remove <package>` to remove a package
- `poetry update` to update the dependencies

> ☝ **Note: Don't Edit Configuration Files**  
> Poetry uses two configuration files: "pyproject.toml" and "poetry.lock".
> Don't edit these files manually but use the `poetry` command instead.

> Modify the "pyproject.toml" dependency configuration file with `poetry add` and `poetry remove`.
> The poetry.lock file is maintained by the `poetry update` command.

#### 2.2.2.2 Frontend Services

Navigate to the `aihub_web` folder

- Follow the instructions in the `README.md` file to set up the frontend.

### **2.2.3 Configure Environment Variables**

- Request `.env` files from the team.
- Place them in the root directories of backend and frontend projects.

---

## 2.3 Read Documentation

- Read the whole documentation in the [aihub_doc](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_doc) folder in
  the `aihub-core` repository.
- Feel free to read up on any other resource used in the project e.g. AI Agents, LlamaIndex, FastAPI, Nuxt.js, etc.

---

## 2.4 First Steps

### 2.4.1 Explore the Codebase + Playground

- **Codebase**: Explore the codebase to understand the structure and the services provided.
- **Playground**: Use the `playground` directories in the services to test and experiment with the code.
  Quickstart:
    - Start Docker.
        - Navigate to the `aihub_agent` directory.
        - Run the following command:
          ```bash
          docker compose up
          ```
          or simply click the green play button in PyCharm. This will start phoenix on localhost:6006, nats, and mongo
          DB.
            - *Start Docker including the local milvus vector DB by running:*
              ```bash
              docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml up
              ```

---

# 3 Testing

## 3.1 pytest

We are using `pytest` as the testing framework for the AI-Hub project. The tests are located in the `tests` directory
at the location of the code that is being tested. The testfile itself should be prefixed with `test_` resulting in
a filename like `test_<unit_beeing_tested>.py`.

## 3.2 Behaviour-Driven Development (bdd) based testing

This repository uses **Behavior-Driven Development (BDD)** with the [
pytest-bdd plugin](https://pytest-bdd.readthedocs.io/). BDD provides a structured approach for writing tests that
capture business requirements in a format understandable to both technical and non-technical team members.

### 3.2.1 How It Works

1. **Feature Files**: Written in Gherkin syntax (`.feature` files) that describe the feature, the scenarios, and the
   expected behavior.
2. **Step Definitions**: Python functions decorated with `pytest-bdd` decorators (e.g. `@given`, `@when`, `@then`) that
   implement the steps defined in the feature files.
3. **Test Execution**: `pytest` discovers the feature files and maps each Gherkin step to the matching Python step
   definition.

### 3.2.2 Project Structure

The BDD tests are organized in the following structure:

```plaintext
.
├── SystemUnderTest.py
└── tests
    ├── features
    │   ├── system_under_test.feature
    │   └── ...
    └── test_SystemUnderTest.py
```

*As a general rule there is always one .feature file per system-under-test. There can be exceptions if
the same class hase multiple purposes but this should be prevented*

### 3.2.3 Gherkin Syntax

The .feature files are located in the `tests/features` directory and contain the Gherkin scenarios and look like this:

```gherkin
Feature: Simple Agent
  test for SimpleAgent

  Scenario: Test Simple Agent
    Given a SimpleAgent runner

    When a the start event is sent with payload "Hello"
    Then a StartEvent is present with payload "Hello"
    And a StopEvent is present
    And an EventA event is present with payload "Hello"
```

These scenarios can be written in a configurable way where input can be passed as variables to the test or the same test
is executed with different values.
For extensive list of possibilities see the [pytest-bdd documentation](https://pytest-bdd.readthedocs.io/en/stable/)

Each line the scenario maps to a method in the `test_SystemUnderTest.py` file which might look like this:

```python
@given("a SimpleAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )


@when(parsers.parse('a the start event is sent with payload "{payload}"'))
@async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content=payload, role=MessageRole.USER)]),
            topic=topic,
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive start event"
```

We see that all tests are structured into three parts:

- `given`: setup the test environment
- `when`: execute behaviour that is tested
- `then`: check if the behaviour was executed correctly

  > ☝ **Note: Test can have multiple steps of the same type! **  
  > It can occur or even is encouraged to have multiple steps of the same type (`given`, `when`, `then`) in the
  > same scenario. This allows to have the steps as atomic as possible which makes it easier for the steps to be
  > reused in different scenarios.

### 3.2.4 Why we use bdd testing

- **Readable Tests**: Scenarios in plain English let non-technical stakeholders validate requirements.
- **Reusability**: Step definitions can be shared across multiple scenarios, reducing duplicate test code.
- **Faster Iterations**: New test cases often require no new Python code—just add new scenarios in the feature file.
- **Closer Collaboration**: Encourages collaboration between business, QA, and development.

# 4 Package Management

## 4.1 Package structure

The AI hub consists of multiple packages:

- `aihub_agents`: Contains common code for agent development
- `aihub_api`: Contains common code for API implementation
- `aihub_pipeline`: Contains common code pipeline development
- `aihub_lib`: Contains code relevant for multiple packages of above

This means that the `aihub_lib` package is used by all other packages.

All our packages have versions which are increased in sync with the tags in the repository.
This means that the version is increased with every merge into the main branch.

### 4.2 Referencing

By default, the referencing is done by referencing to the `aihub_lib` package by the git url in the `pyproject.toml`
file.
This is done to allow to tag git commits as versions of the package using tags.
As we expect that changes in the `aihub_lib` package are done in sync with the other packages we are aware
that for local development one might want to reference the local package instead of the git repository.
This can be done by using `make use-local-core` which switches the reference to the local package.

#### 4.2.1 Deployment

For deployment (of customer projects) the referencing is adjusted to reference the package from the github repo
and specifying the version by the tag.

# 5 Additional Infos

## Key Features

1. **Specialized AI Agents**: Unlike generic AI tools, AI-Hub focuses on providing targeted, controlled, and
   high-quality AI-assisted support in specific areas through specialized agents.

2. **Collaborative AI**: AI-Hub enables collaboration between different AI agents, supporting cross-disciplinary
   approaches and creating swarm intelligence.

3. **Context-Aware Agents**: AI-Hub agents are equipped with extensive contextual knowledge, minimizing the need for
   detailed prompts from users.

4. **Flexible Integration**: The platform can work with multiple Large Language Models (LLMs) such as Azure Open AI,
   OpenAI ChatGPT, Gemini, and LLama.

5. **Enhanced Privacy and Security**: AI-Hub can be configured to run entirely within a company's IT infrastructure or
   in a secure Swiss cloud environment.

6. **Customizable and Scalable**: The platform allows for deep integration into existing business processes and systems,
   with the ability to scale as needed.

## Technical Aspects

### Architecture

- AI-Hub is built on a flexible architecture that can integrate with various LLMs and vector databases.
- It uses a custom Business Logic Application to extract information from and perform actions in various systems.
- The frontend is designed for seamless dialogue between employees and AI agents.

### Key Components

1. **Vector Databases**: Support for Azure Cognitive Search, Weaviate, Pinecode, and Milvus.
2. **LLM Integration**: Flexible integration with multiple LLMs, allowing for optimal model selection based on specific
   use cases.
3. **Retrieval-Augmented Generation (RAG)**: Enables cataloging and provision of company-internal knowledge.
4. **Agent Capabilities**: Internet research, speech processing, speech response generation, and integration with
   company-specific interfaces.

### Security and Data Protection

- Role-Based Access Control (RBAC) for securing data in vector databases and agents.
- Integration with Azure Active Directory for additional security layers.
- Option for data anonymization to protect user privacy while enabling full data analysis and processing.

### Optimization Strategies

- Specialized system prompts and agent-level optimization.
- Few-Shot Learning techniques for context-specific responses.
- Optimized data ingestion into vector databases, including structured information and additional context.

## Features

| Feature            | Description                                                            | Availability                                                         |
|--------------------|------------------------------------------------------------------------|----------------------------------------------------------------------|
| prompt_enhance     | User can improve the prompt by clicking the magic-Wand                 | Switzerland North, Dependent on LLM-Model (currently GPT3 (13.8.24)) |
| prompt_library     | Use can access a list of pre-written prompts that are globally defined | Always                                                               |
| voice_input        | user can input prompt by voice                                         | US East, Whisper (13.8.24)                                           |
| voice_output       | User can let the app read the messages as voice                        | Switzerland North, Speech Service (13.8.24)                          |
| tracing            | The Interactions and agent behaviour is traces and reported to phoenix | Always                                                               |
| usage_limits       | usage limits are visible int he frontend                               | Always                                                               |
| chat_export_import | chat can be exported and imported                                      | Always                                                               |

## Tech-Stack

### Base Technologies

| Category                        | Technology Used                             | Description                                                                                                                                                                                                               | Alternatives                            |
|---------------------------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| Python AI Framework             | [Llama-Index](https://www.llamaindex.ai/)   | A rapidly evolving framework for using AI capabilities. It is very close to the research and quickly adapts new approaches. Downside: Because it develops so quickly, there are regular major changes and sometimes bugs. | [Langchain](https://www.langchain.com/) |
| Tracing                         | OpenTelemetry                               | OpenTelemetry is an observability framework for cloud-native software, providing APIs, libraries, agents, and other integration components to capture distributed traces and metrics.                                     | ...                                     |
| Tracing Explorer                | [Arize Phoenix](https://phoenix.arize.com/) | A tool for exploring and visualizing distributed traces captured by OpenTelemetry.                                                                                                                                        | ...                                     |
| Ingestion Pipeline Orchestrator | [Dagster](https://dagster.io/)              | A workflow management system for building and managing complex data processing pipelines.                                                                                                                                 | ...                                     |
| Version Control System          | GitHub                                      | A web-based platform for version control and collaboration, providing a centralized place for developers to store, track, and manage their code.                                                                          | ...                                     |
| IDE                             | PyCharm, WebStorm                           | Integrated Development Environments (IDEs) for writing and testing code, offering features like code editing, debugging, and project management.                                                                          | ...                                     |
| Container Orchestration         | Docker, Docker-Compose                      | Tools for building, deploying, and managing containerized applications, enabling consistent and scalable deployments across different environments.                                                                       | ...                                     |
| CI/CD                           | GitHub Actions                              | A cloud-based automation platform that allows you to build, test, and deploy your code directly from GitHub.                                                                                                              | ...                                     |
| Code Quality                    | [SonarCloud](https://sonarcloud.io/)        | A cloud-based code quality and security tool that analyzes your code, identifies issues, and provides insights to improve code quality.                                                                                   | ...                                     |
| Testing                         | PyTest                                      | A popular Python testing framework that makes it easy to write and run tests for your Python code.                                                                                                                        | ...                                     |
| Testing (Frontend)              | Playwright                                  | A framework for end-to-end (E2E) testing of web applications, supporting multiple browsers and providing a reliable and fast testing experience.                                                                          | Cypress, Selenium                       |
| Identity Management             | MSAL / Entra ID                             | Libraries and services for managing user authentication and authorization, ensuring secure access to your applications.                                                                                                   | ...                                     |

### Cloud Technologies

| Category        | Technology Used                        | Description                                                                                                                                                                                                                                                                   | Alternatives |
|-----------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| Vector Database | Azure Cognitive Search                 | Azure Cognitive Search is a cloud-based search service that provides full-text, numerical, and faceted search capabilities over structured and unstructured data. It is used to store and index vector representations of data, enabling efficient similarity-based searches. | ...          |
| LLM             | GPT Models, Open Source LLaMA, Mistral | Azure provides access to various large language models (LLMs), including GPT models, the open-source LLaMA models, and the Mistral model. These LLMs are used for natural language processing tasks such as text generation, question answering, and language understanding.  | ...          |
| Database        | Cosmos MongoDB (Azure)                 | The agent definitions are stored in an Azure Cosmos DB MongoDB database, which is a fully managed, globally distributed, and highly available NoSQL database service.                                                                                                         | ...          |
| Backend Server  | Azure App Service                      | The backend server is deployed on Azure App Service, a fully managed platform for building, deploying, and scaling web applications and APIs.                                                                                                                                 | ...          |
| Frontend Host   | Azure Static Web App                   | The frontend of the application is hosted on Azure Static Web Apps, a fully managed service that automatically builds and deploys full-stack web apps from a GitHub repository.                                                                                               | ...          |
| Voice Input     | Azure Speech Service                   | The Azure Speech Service is used to enable voice input functionality, allowing users to interact with the application using speech recognition.                                                                                                                               | ...          |
| Voice Output    | Azure Speech Service                   | The Azure Speech Service is also used to generate speech output, enabling the application to provide audio responses to users.                                                                                                                                                | ...          |

### OnPrem Technologies

| Category                      | Technology Used     | Description                                                                                                                                                                                                                                                                                                                                             | Alternatives |
|-------------------------------|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| Vector Database (On-Premises) | Milvus              | Milvus is an open-source, highly reliable, and scalable vector database used for efficient storage and retrieval of high-dimensional vector data. It is well-suited for applications that require fast similarity searches, like recommendation systems, image/text search, and natural language processing.                                            | ...          |
| LLM (On-Premises)             | LLaMA, Mistral, Phi | LLaMA, Mistral, and Phi are large language models (LLMs) that can be deployed on-premises, enabling organizations to leverage the power of advanced natural language processing capabilities within their own infrastructure. These models can be used for a variety of tasks, such as text generation, question answering, and language understanding. | ...          |
| LLM Server                    | llama.cpp, vllm     | llama.cpp and vllm are open-source projects that provide server-based deployment of large language models, allowing organizations to integrate these models into their applications and services without the need to manage the underlying infrastructure.                                                                                              | ...          |
| Database (On-Premises)        | MongoDB             | MongoDB is a popular NoSQL database used for storing the definitions of the agents, which are the autonomous entities that interact with users or other systems within the application.                                                                                                                                                                 | ...          |
| Voice Input (On-Premises)     | Whisper.cpp         | Whisper.cpp is an open-source speech recognition model developed by OpenAI, which can be deployed on-premises to enable voice input capabilities within the application. This allows users to interact with the system using voice commands or dictation.                                                                                               | ...          |




