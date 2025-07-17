---
title: High Level
index: 2
---

# What IS the Hub - For Techies

From a business perspective, the Swiss AI-Hub is a strategic platform for integrating AI into the enterprise. From a technical standpoint, it is a comprehensive, foundational software framework designed for security, scalability, and extensibility. It is not a single, monolithic application, but a complete ecosystem of specialized services and well-defined components that work in concert.

### The High-Level Architecture: A Modular, Hub-and-Spoke Ecosystem

The AI-Hub is built on a "hub-and-spoke" model with a strong emphasis on **separation of concerns**. This is reflected in our project structure, which is a monorepo containing multiple, distinct Python packages we call "scopes". This modularity allows for independent development, testing, and deployment of each component, ensuring the system remains maintainable and adaptable.

At the center is a shared library and a core API, with specialized scopes handling specific domains like agentic logic, data pipelines, and frontend interfaces. This design is mirrored in our repository strategy, which distinguishes between a reusable `aihub-core` repository and customer-specific `aihub-<CUSTOMER>` repositories that extend the core functionality for bespoke solutions.

### The Core Components: The Scopes of the AI-Hub

The AI-Hub is composed of several key scopes, each with a dedicated responsibility. Understanding these scopes is key to understanding what we build:

* **`aihub_lib`**: This is the foundational library. Any code that needs to be shared by more than one other service lives here. It's the bedrock of the entire platform.
* **`aihub_api`**: This is the central nervous system of the Hub. Built with FastAPI, it provides the main user-facing REST API and the WebSocket gateway for real-time communication. All frontend interactions flow through this component.
* **`aihub_web`**: This is the face of the Hub—the frontend application that users interact with directly. It provides the chat interface, process dashboards, and administrative panels.
* **`aihub_agents` & `aihub_process`**: These are the "brains" of the operation. `aihub_agents` contains the logic for individual, workflow-based AI agents. `aihub_process` takes it a step further, orchestrating high-level business processes that coordinate between agents, humans, and external programs.
* **`aihub_pipeline`**: This is the data factory. Using orchestrators like Dagster, this scope handles all data ingestion and processing, transforming raw enterprise data into knowledge that agents can use.
* **`aihub_bot`**: This is the integration layer for conversational platforms. It contains the logic for connecting the Hub's capabilities to external services like Microsoft Teams or Slack.

These components work together seamlessly. For example, a user on the **`aihub_web`** interface might initiate a chat. The request goes to the **`aihub_api`**, which could trigger an **`aihub_process`**. That process might delegate a task to an **`aihub_agent`**, which in turn uses knowledge processed by an **`aihub_pipeline`**.

### The Technology Stack: What It Runs On

The AI-Hub is powered by a modern, containerized infrastructure stack, managed via Docker Compose. This ensures a consistent and reproducible environment, whether on-premises or in the cloud.

* **Databases & Caching:**
    * **Postgres (with pgvector):** Serves as our primary relational database and, with the pgvector extension, provides efficient vector storage for Retrieval-Augmented Generation (RAG).
    * **MongoDB:** Used as a NoSQL database for its flexibility in storing semi-structured data like agent and process definitions.
    * **Redis:** A high-performance in-memory data store used for caching, pub/sub messaging, and managing WebSocket connections to support stateless, scalable deployments.
* **AI & Embedding Services:**
    * **On-Premises LLMs (llama.cpp):** We use llama.cpp server for highly efficient, on-premises inference of large language models, with support for both CPU and GPU environments.
    * **Text Embeddings Inference (TEI):** A dedicated Hugging Face service optimized for generating text embeddings at scale, crucial for our RAG capabilities.
* **Messaging & Observability:**
    * **NATS:** A lightweight, high-performance messaging system that enables asynchronous, event-driven communication between our microservices, particularly for agentic processes.
    * **OpenTelemetry & Phoenix:** We embrace modern observability standards. The entire platform is instrumented with OpenTelemetry to capture distributed traces, which can be visualized and debugged in Arize Phoenix. This provides deep insight into agent behavior.
* **Web Interface:**
    * **Open WebUI:** Our user-facing chat interface is built upon the feature-rich Open WebUI, which we configure and extend for the enterprise context.

### Development and Governance: How We Build It

The AI-Hub is developed with professional software engineering discipline to ensure quality, maintainability, and security.

* **Dependency Management:** We use Poetry for managing Python dependencies within each scope, ensuring isolated and reproducible environments.
* **Standardized Tooling:** `make` is used to provide a consistent command-line interface for common development tasks like testing and formatting across all scopes.
* **Enforced Code Quality:** Our CI/CD pipelines, built on GitHub Actions, strictly enforce code standards. We use **Black** for formatting, **Ruff** for linting, and **MyPy** for strict static type checking. Code cannot be merged unless it meets these standards.
* **Testing Philosophy:** We employ a pragmatic testing strategy using `pytest`. For complex agent and process workflows, we leverage Behavior-Driven Development (BDD) with `pytest-bdd` to ensure our tests are readable and align with business requirements.

In conclusion, the Swiss AI-Hub is more than just a collection of AI models. It is a robust, well-architected framework that combines a modular software design, a scalable infrastructure stack, and a rigorous development process. This comprehensive approach is what makes it a true enterprise-grade platform, capable of delivering secure, powerful, and customizable AI solutions.