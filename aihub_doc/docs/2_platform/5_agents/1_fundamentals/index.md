---
title: Agent Fundamentals
index: 1
---

# Agent Fundamentals

While the user interacts with agents through a simple chat interface, a sophisticated, event-driven architecture works behind the scenes to make them reliable, auditable, and intelligent. This section explores the fundamental concepts that govern how agents in the Swiss AI Hub operate, manage information, and collaborate.

Understanding these principles is key to appreciating how the platform transforms AI from an unpredictable "black box" into a transparent and trustworthy enterprise tool.

## The Agent's Blueprint: Structured Workflows

Every agent's behavior is defined by a **workflow**—an explicit, step-by-step process. This is the most critical design principle of the platform. Instead of giving an agent a set of tools and letting it autonomously decide how to use them, we define the exact sequence of operations it must follow.

This structured approach provides the predictability and control that enterprises require:

-   **Transparency**: Anyone, from a developer to a compliance officer, can look at the workflow definition and understand the agent's logic. This makes AI behavior explainable.
-   **Reliability & Testability**: Each step in a workflow can be developed and tested independently. This reduces deployment risk and ensures that complex processes are built from reliable components.
-   **Control**: The agent is constrained by its workflow. It cannot decide to access data it shouldn't or perform actions outside its predefined sequence, eliminating a significant class of risks associated with autonomous AI.

Within each step, the agent can use the full power of AI to reason, analyze data, and make intelligent decisions, but its overall path is governed by the workflow you define.

## The Agent's Memory: Hierarchical Context Management

For an agent to be effective, especially in a long conversation, it needs a memory. The platform provides a sophisticated, multi-layered context management system that acts as the agent's memory, ensuring it never loses track of the conversation while optimizing for performance.

This memory is organized into a three-level hierarchy:

-   **Thread Context**: This is the agent's **long-term memory** for an entire conversation or a long-running business process. It stores user preferences, the complete conversation history, and knowledge accumulated across multiple interactions. When you return to a conversation you started yesterday, the Thread Context is what allows the agent to remember everything you discussed. It is the foundation for security, as access is controlled at the thread level.

-   **Display Context**: This scope manages what is shown to the user in the interface. It groups together a set of actions to present them as a single, seamless interaction. This is particularly important when agents collaborate behind the scenes, as it allows a primary agent to control whether the "work" of a sub-agent is visible or hidden from the user.

-   **Run Context**: This is the agent's **short-term, working memory** for a single, traceable task (e.g., from your question to its answer). It holds the intermediate calculations, temporary data, and immutable configuration for that specific execution. This memory is ephemeral and optimized for high-speed access during the agent's operation.

## The Agent's Ecosystem: Event-Driven Participants

An agent doesn't work in isolation. It's part of an ecosystem of components that collaborate to deliver a seamless and secure experience. This interaction is entirely **event-driven**, meaning components communicate through asynchronous messages on a central message bus. This design makes the system highly scalable, resilient, and perfectly auditable.

There are four key participants in this ecosystem:

1.  **The Agent**: The autonomous worker that executes the business logic defined in its workflow. It consumes instructions (Control Events) and produces a rich stream of results and telemetry (Display Events).
2.  **The API Gateway**: The secure front door to the platform. It is the only component that can create initial events from external requests. It authenticates users, translates their HTTP requests into secure internal events, and streams the agent's responses back to the user interface.
3.  **The Frontend**: The user interface you interact with. It's primarily a listener, subscribing to a stream of "Display Events" from the agent and rendering them in real-time as streaming text, thought processes, or other UI elements.
4.  **The Process Orchestrator**: A specialized type of agent that manages high-level business processes. It acts like a conductor, consuming the completion events from one agent to trigger the next participant in a complex, multi-step workflow.

This decoupled architecture ensures the platform is robust. A slowdown in the user interface, for example, cannot crash the underlying agent's workflow.

## Advanced Capabilities: Collaboration Patterns

The platform's architecture enables sophisticated collaboration patterns that allow agents to work effectively with each other and with human users.

### Human-in-the-Loop: Integrating Human Judgment

Not every decision can or should be fully automated. The platform is built with "human-in-the-loop" capabilities as a core feature, allowing workflows to seamlessly integrate human oversight.

::: details How It Works
An agent's workflow can be designed to pause at any critical step and publish a `HumanInTheLoopRequestEvent`. This event creates a task in the user's interface, presenting them with the necessary context and choices. The workflow remains paused—for minutes, hours, or even days—until the user responds. Upon response, an `HumanInTheLoopResponseEvent` is generated, and the agent's workflow resumes.
:::

This pattern is far more powerful than simple user prompts.

-   **True Context Preservation**: The workflow does not restart after human input. It resumes from the **exact point it paused**, with full memory of all intermediate results and prior steps. This is critical for complex, multi-step processes.
-   **Full Audit Trail**: Every human interaction—the question asked, who responded, what they decided, and when—is immutably logged as an event, ensuring full accountability for compliance and auditing.
-   **Use Case Flexibility**: This enables critical enterprise scenarios, from regulatory approvals and quality assurance checks to handling ambiguous situations where an agent needs clarification. It also allows for user consent workflows, where an agent presents a disclaimer that a user must accept before the process can continue.

### Agent-to-Agent Delegation: A Team of Specialists

Complex problems are often best solved by a team of specialists. The platform enables this by allowing a primary agent to **delegate** tasks to other, more specialized agents using an `AgentInTheLoop` event pattern.

For example, a general "Document Inquiry Agent" might receive a complex legal question. Instead of trying to answer it itself, it can delegate the task to a specialized "Legal Compliance Agent."

This pattern allows you to build a powerful, composable system of AI capabilities:
-   **Reusability**: Build focused, reusable agents for specific tasks (e.g., entity extraction, PII detection, compliance checking) and orchestrate them to solve larger business problems.
-   **Isolation and Security**: The delegated agent runs in its own isolated workflow. It cannot access the primary agent's internal state, ensuring security and preventing unintended side effects.
-   **Control Over Visibility**: The primary agent controls the `Display Context`, deciding what the user sees. It can make the collaboration transparent, showing the user that it's consulting another expert, or it can happen entirely in the background, with the user only ever seeing the final, consolidated answer.
-   **Scalability**: Specialized, high-demand agents can be scaled independently, ensuring that bottlenecks in one capability do not slow down the entire system.