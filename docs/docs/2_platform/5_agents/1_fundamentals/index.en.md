---
title: Agent fundamentals
---

# Agent fundamentals

Agents use an event-driven architecture. Users can interact through chat interfaces or agents can run autonomously.
Workflows, context management, and event handling operate in the background.

## Structured workflows

Each agent follows a predefined workflow that defines its exact sequence of operations. Instead of giving an agent tools
and letting it decide how to use them, workflows specify each step the agent takes.

Workflows provide:

- Transparency: Developers and compliance officers can read the workflow definition and understand what the agent does
- Testability: Each step can be developed and tested independently
- Control: The agent cannot access unauthorized data or perform actions outside its workflow

Steps can use language models when needed for reasoning and natural language tasks, but many steps perform deterministic
operations like data validation, formatting, or conditional routing without any LLM involvement. The workflow controls
the overall execution path.

## Context management

Agents use three levels of context to manage state:

**Thread context** stores persistent state across multiple agent runs within the same thread. A thread represents a
continuous interaction session - for chat agents, this is a conversation; for autonomous agents, it's a series of
related executions. When you return to a conversation started yesterday, thread context lets the agent remember previous
exchanges. This context has a 30-day expiration. Access control operates at this level.

**Display context** manages what appears in the user interface. It groups actions to present them as a single
interaction. When agents collaborate, the primary agent controls whether sub-agent work appears to the user or stays
hidden.

**Run context** holds temporary data for a single agent run. It contains intermediate calculations and cached data for
that specific execution. This context expires after 30 days but is isolated between different runs.

## Event-driven architecture

Agents operate within an ecosystem of components that communicate through asynchronous messages on a message bus (NATS).

Four participants:

**Agent**: Executes business logic defined in its workflow. Receives instructions and produces results and telemetry.

**API Gateway**: Authenticates users, translates HTTP requests into internal events, and streams agent responses back to
the user interface.

**Frontend**: Receives agent output and renders it in real-time as streaming text and UI elements.

**Process Orchestrator**: Manages multi-agent workflows by monitoring when one agent completes and triggering the next
participant.

This decoupled architecture prevents issues in one component from affecting others. A slowdown in the frontend cannot
crash an agent's workflow.

## Collaboration patterns

### Human-in-the-loop

Agent workflows can pause to request human input. The workflow creates a task in the user's interface with context and
choices. The workflow stays paused (minutes, hours, or days) until the user responds, then resumes execution.

Key characteristics:

- Context preservation: The workflow resumes from the exact point it paused with full memory of intermediate results
- Audit trail: Every interaction (question, responder, decision, timestamp) gets logged
- Use cases: Regulatory approvals, quality assurance checks, ambiguous situations requiring clarification, consent
  workflows

### Agent-to-agent delegation

A primary agent can delegate tasks to specialized agents. For example, a Document Inquiry Agent receiving a complex
legal question can delegate to a Legal Compliance Agent.

Benefits:

- Reusability: Build focused agents for specific tasks (entity extraction, PII detection, compliance checking) and
  orchestrate them for larger problems
- Isolation: The delegated agent runs in its own workflow and cannot access the primary agent's internal state
- Visibility control: The primary agent controls the display context and can show or hide the delegation from the user
- Scalability: High-demand specialized agents can scale independently
