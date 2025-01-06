# AI Hub

# AI-Hub Developer Introduction

Welcome to the AI-Hub project! This document provides an overview of the AI-Hub platform, its key features, and technical aspects for developers.

## What is AI-Hub?

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

## Repositories

There are two types of repositories in the AI-Hub ecosystem:

1. **Core repository**  
   The core repository, named **`aihub-core`**, contains all shared functionality and code used across multiple projects. Under no circumstances should it contain any customer-specific information. This separation is critical to prevent information leakage because this repo is referenced by customer-specific repositories.

2. **Customer repositories**  
   Customer repositories are named **`aihub-<CUSTOMER>`**. These repositories build on the functionality provided by `aihub-core` while adding or overriding components for the specific customer context.

### Repository Structure

Regardless of whether you are working in the core repository or a customer repository, you will find the following top-level folders (or *scopes*). The main difference is that, in `aihub-core`, each folder is prefixed with `aihub_` (e.g., `aihub_agents`, `aihub_api`, etc.):

- **`agents`**: Contains agent-specific code, such as workflow steps.

- **`api`**: Contains API endpoint definitions.

- **`doc`**: Contains documentation (for example, arc42 documentation).

- **`lib`**: Provides shared functionality that can be reused across multiple scopes within the repository.

- **`pipeline`**: Contains definitions for Dagster pipelines.

- **`web`**: Contains frontend code.

Within a customer repository (`aihub-<CUSTOMER>`), the corresponding scopes will typically import core functionalities from `aihub-core` as needed. The `lib` folder in each repo may also be consumed by other scopes within the same repo.

#### Additional Scopes (Core Repository Only)

In addition to the folders listed above, the core repository (`aihub-core`) includes the following additional scopes:

- **`aihub_action`**  
  Contains reusable code for GitHub Actions used in the CI/CD pipelines of customer repositories. Managing these actions in the core repo helps to avoid duplication and reduces maintenance overhead.

  > ☝ **Note:** This is **not** the same as the `.github` folder.  
  > The `.github` folder contains the actual GitHub Actions and workflows executed in the CI/CD flow for `aihub-core` itself.

- **`aihub_iac`**  
  Contains Infrastructure-as-Code (IaC) resources that can be reused by customer repositories.


## Project and Work Management

The **AI-Hub** ecosystem uses two main GitHub Projects to manage development and roadmap planning:

1. **`aihub-roadmap`**  
   Focuses on high-level planning, covering both customer projects and larger initiatives for the AI-Hub core.

2. **`aihub`**  
   Focuses on day-to-day development tasks that contribute to the overall initiatives and customer projects.

### Types of Projects

We distinguish between two primary types of projects:

1. **Customer Projects**  
   These are engagements specific to a customer. They are often tied to a particular `aihub-<CUSTOMER>` repository but may also require changes or enhancements in `aihub-core`.

2. **Initiatives**  
   These can be viewed as large features or focus areas targeted for improvement or creation within the AI-Hub core. They are broader in scope than most customer projects and generally aim to advance the platform as a whole.

### Roadmap Overview ([aihub-roadmap](https://github.com/orgs/bbvch-ai/projects/7))

In the [aihub-roadmap](https://github.com/orgs/bbvch-ai/projects/7) GitHub Project, we manage both **customer projects** and **initiatives**. Here, you will find:

- **General Project Information**: Owner, Project Manager, Development Lead, etc.  
- **Project Goal & Initial Setup**: Defined in the main issue describing the project or initiative.  
- **Ongoing Documentation**: All major events, decisions, and outcomes are recorded in the issues.  
- **Project Health States**:  
  - **In Schedule**: Work is proceeding as planned.  
  - **Tight Schedule**: There is a risk of falling behind schedule.  
  - **Behind Schedule**: The project or initiative has already fallen behind planned milestones.  
  - **Schedule Impossible**: The current timeline can no longer be met without major changes.

At the end of a project or initiative, the main issue can also serve as a record of **learnings**, providing valuable insights for future work.

### Daily Work Management ([aihub](https://github.com/orgs/bbvch-ai/projects/2))

While the high-level status and context of projects or initiatives live in `aihub-roadmap`, the actual development tasks are tracked in the [aihub](https://github.com/orgs/bbvch-ai/projects/2) GitHub Project. Tasks in `aihub` may span multiple projects or initiatives but are always linked back to the corresponding item in `aihub-roadmap`. This ensures:

- **Traceability**: Developers can see which larger project or initiative their tasks belong to.  
- **Alignment**: Project Managers and Dev Leads can monitor progress on overarching goals by reviewing associated tasks.  

In each task’s GitHub issue, you should see a reference or link to the main issue in `aihub-roadmap` that tracks the project or initiative. This linkage helps keep the broader context visible and maintains clarity on priorities.

For day-to-day tasks managed in the `aihub` board, we use three primary status columns:

- **To Do**  
- **In Progress**  
- **Done**

#### Guidelines

1. **Assigning Tasks**  
   - If you start working on a task and it is unassigned, assign yourself to it.  
   - Always keep the assignee field up to date to ensure transparency.

2. **Moving Tasks**  
   - When you begin work, move the task from **To Do** to **In Progress**.  
   - Once you complete the task (and all necessary reviews and merges), move it to **Done**.

This straightforward workflow helps maintain a clear overview of who is working on what, and the current status of 
each task. Keeping the board updated is crucial for effective collaboration and progress tracking.


---


## Key Features

1. **Specialized AI Agents**: Unlike generic AI tools, AI-Hub focuses on providing targeted, controlled, and high-quality AI-assisted support in specific areas through specialized agents.

2. **Collaborative AI**: AI-Hub enables collaboration between different AI agents, supporting cross-disciplinary approaches and creating swarm intelligence.

3. **Context-Aware Agents**: AI-Hub agents are equipped with extensive contextual knowledge, minimizing the need for detailed prompts from users.

4. **Flexible Integration**: The platform can work with multiple Large Language Models (LLMs) such as Azure Open AI, OpenAI ChatGPT, Gemini, and LLama.

5. **Enhanced Privacy and Security**: AI-Hub can be configured to run entirely within a company's IT infrastructure or in a secure Swiss cloud environment.

6. **Customizable and Scalable**: The platform allows for deep integration into existing business processes and systems, with the ability to scale as needed.

## Technical Aspects

### Architecture

- AI-Hub is built on a flexible architecture that can integrate with various LLMs and vector databases.
- It uses a custom Business Logic Application to extract information from and perform actions in various systems.
- The frontend is designed for seamless dialogue between employees and AI agents.

### Key Components

1. **Vector Databases**: Support for Azure Cognitive Search, Weaviate, Pinecode, and Milvus.
2. **LLM Integration**: Flexible integration with multiple LLMs, allowing for optimal model selection based on specific use cases.
3. **Retrieval-Augmented Generation (RAG)**: Enables cataloging and provision of company-internal knowledge.
4. **Agent Capabilities**: Internet research, speech processing, speech response generation, and integration with company-specific interfaces.

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
| usage_limits      | usage limits are visible int he frontend                               | Always                                                               |
| chat_export_import | chat can be exported and imported                                      | Always                                                               |


## Tech-Stack

### Base Technologies

| Category                       | Technology Used                             | Description                                                                                                                                                                                                                                                         | Alternatives |
|----------------------------------|---------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| ----------------------- |
| Python AI Framework             | [Llama-Index](https://www.llamaindex.ai/)   | A rapidly evolving framework for using AI capabilities. It is very close to the research and quickly adapts new approaches. Downside: Because it develops so quickly, there are regular major changes and sometimes bugs.                                         | [Langchain](https://www.langchain.com/) |
| Tracing                         | OpenTelemetry                               | OpenTelemetry is an observability framework for cloud-native software, providing APIs, libraries, agents, and other integration components to capture distributed traces and metrics.                                                                                    | ... |
| Tracing Explorer                | [Arize Phoenix](https://phoenix.arize.com/) | A tool for exploring and visualizing distributed traces captured by OpenTelemetry.                                                                                                                                                                                     | ... |
| Ingestion Pipeline Orchestrator | [Dagster](https://dagster.io/)              | A workflow management system for building and managing complex data processing pipelines.                                                                                                                                                                             | ... |
| Version Control System          | GitHub                                      | A web-based platform for version control and collaboration, providing a centralized place for developers to store, track, and manage their code.                                                                                                                      | ... |
| IDE                             | PyCharm, WebStorm                           | Integrated Development Environments (IDEs) for writing and testing code, offering features like code editing, debugging, and project management.                                                                                                                     | ... |
| Container Orchestration         | Docker, Docker-Compose                      | Tools for building, deploying, and managing containerized applications, enabling consistent and scalable deployments across different environments.                                                                                                                    | ... |
| CI/CD                           | GitHub Actions                              | A cloud-based automation platform that allows you to build, test, and deploy your code directly from GitHub.                                                                                                                                                          | ... |
| Code Quality                    | [SonarCloud](https://sonarcloud.io/)                              | A cloud-based code quality and security tool that analyzes your code, identifies issues, and provides insights to improve code quality.                                                                                                                              | ... |
| Testing                         | PyTest                                      | A popular Python testing framework that makes it easy to write and run tests for your Python code.                                                                                                                                                                     | ... |
| Testing (Frontend)              | Playwright                                  | A framework for end-to-end (E2E) testing of web applications, supporting multiple browsers and providing a reliable and fast testing experience.                                                                                                                        | Cypress, Selenium |
| Identity Management             | MSAL / Entra ID                             | Libraries and services for managing user authentication and authorization, ensuring secure access to your applications.                                                                                                                                               | ... |

### Cloud Technologies

| Category         | Technology Used                         | Description                                                                                                                                                                                                                                                        | Alternatives |
|------------------|-------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| Vector Database  | Azure Cognitive Search                    | Azure Cognitive Search is a cloud-based search service that provides full-text, numerical, and faceted search capabilities over structured and unstructured data. It is used to store and index vector representations of data, enabling efficient similarity-based searches.                                                                                                                                 | ...         |
| LLM              | GPT Models, Open Source LLaMA, Mistral     | Azure provides access to various large language models (LLMs), including GPT models, the open-source LLaMA models, and the Mistral model. These LLMs are used for natural language processing tasks such as text generation, question answering, and language understanding.                                                                                                                                 | ...         |
| Database         | Cosmos MongoDB (Azure)                    | The agent definitions are stored in an Azure Cosmos DB MongoDB database, which is a fully managed, globally distributed, and highly available NoSQL database service.                                                                                                                                                                                  | ...         |
| Backend Server   | Azure App Service                         | The backend server is deployed on Azure App Service, a fully managed platform for building, deploying, and scaling web applications and APIs.                                                                                                                                                                                                 | ...         |
| Frontend Host    | Azure Static Web App                      | The frontend of the application is hosted on Azure Static Web Apps, a fully managed service that automatically builds and deploys full-stack web apps from a GitHub repository.                                                                                                                                                                                                 | ...         |
| Voice Input      | Azure Speech Service                      | The Azure Speech Service is used to enable voice input functionality, allowing users to interact with the application using speech recognition.                                                                                                                                                                                                 | ...         |
| Voice Output     | Azure Speech Service                      | The Azure Speech Service is also used to generate speech output, enabling the application to provide audio responses to users.                                                                                                                                                                                                 | ...         |

### OnPrem Technologies

| Category                        | Technology Used                          | Description                                                                                                                                                                                                                                                           | Alternatives |
|---------------------------------|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| ----------------------- |
| Vector Database (On-Premises)   | Milvus                                   | Milvus is an open-source, highly reliable, and scalable vector database used for efficient storage and retrieval of high-dimensional vector data. It is well-suited for applications that require fast similarity searches, like recommendation systems, image/text search, and natural language processing.                                                                                                                                  | ... |
| LLM (On-Premises)               | LLaMA, Mistral, Phi                      | LLaMA, Mistral, and Phi are large language models (LLMs) that can be deployed on-premises, enabling organizations to leverage the power of advanced natural language processing capabilities within their own infrastructure. These models can be used for a variety of tasks, such as text generation, question answering, and language understanding.                                                                                                          | ... |
| LLM Server                      | llama.cpp, vllm                          | llama.cpp and vllm are open-source projects that provide server-based deployment of large language models, allowing organizations to integrate these models into their applications and services without the need to manage the underlying infrastructure.                                                                                                                                                      | ... |
| Database (On-Premises)          | MongoDB                                  | MongoDB is a popular NoSQL database used for storing the definitions of the agents, which are the autonomous entities that interact with users or other systems within the application.                                                                                                                                                                        | ... |
| Voice Input (On-Premises)       | Whisper.cpp                              | Whisper.cpp is an open-source speech recognition model developed by OpenAI, which can be deployed on-premises to enable voice input capabilities within the application. This allows users to interact with the system using voice commands or dictation.                                                                                                                                                       | ... |

# Getting Started

## Branching Strategy & PR Conventions

Our branching strategy is designed to streamline development by organizing code changes based on customer
projects and internal initiatives. This approach enhances collaboration, simplifies code management,
and ensures that updates are efficiently merged and deployed.

### Long-Lived Branches

We maintain long-lived branches that correspond to specific customer projects and internal initiatives.
These branches serve as stable bases for ongoing development related to their respective areas.

**Customer Branches:**

- customer/bbv
- customer/fmh
- customer/bs
- ...

**Initiative Branches:**

- initiative/agent-custom
- initiative/agent-xp
- initiative/avatar
- ...

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

### Pull Request Titles

Pull request (PR) titles follow a specific format to indicate:

Why the code was changed (PR-Type):

- fix
- feat
- test
- doc
- chore

For whom the code was changed (PR-Scope):

- aihub *(internal product owner without initiative)*
- workflows *(initiative)*
- fmh *(customer)*
- customer-xyz

#### PR Title Format

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

### Benefits of This Strategy

- **Clarity**: Clear branch names and PR titles make it easy to understand the purpose and target of code changes.
- **Efficiency**: By indicating the customer or initiative, we can prioritize merges that are critical for specific
  stakeholders.
- **Flexibility**: Allows for parallel development across different projects and initiatives without conflicts.
- **Traceability**: Enhances the ability to track changes back to their origin, facilitating better project management.
