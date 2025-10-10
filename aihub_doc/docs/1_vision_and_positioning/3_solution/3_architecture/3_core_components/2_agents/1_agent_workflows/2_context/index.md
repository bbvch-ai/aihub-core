---
title: Context Management
index: 2
---

# Context Management in Agent Workflows

The Swiss AI-Hub implements a sophisticated context management system that enables agents to maintain state across
conversations while ensuring optimal performance and resource utilization. This system uses a multi-layered storage
architecture designed to balance immediate responsiveness with long-term data retention.

## Hierarchical Context Scoping

The platform organizes all agent interactions through a three-level hierarchical context structure that provides
granular control over state management, security, and observability:

**Thread Context** represents the highest-level scope, grouping multiple interactions and workflow runs that belong to a
single overarching goal or conversation. A chat conversation constitutes a thread, while an autonomous agent processing
business documents for an entire month might operate within a single thread for that period's work. Threads maintain
long-term history and state across extended periods, enabling conversational continuity and process consistency.
Thread-level access control ensures conversations and workflows remain private to authorized participants.

**Display Context** provides an intermediate scope designed for grouping multiple workflow runs together for
presentation in user interfaces. When an agent delegates work to another agent, it can choose to pass on its display
context, making both agents' activities appear as a single seamless interaction. Alternatively, creating a new display
context for delegated work effectively hides that work from specific UI views, enabling background processing invisible
to the user.

**Run Context** represents the most granular scope, defining a single traceable execution of a workflow between a start
event and corresponding stop or exception event. This scope provides unique identification for individual agent
operations, essential for tracing and debugging as it isolates events of one specific task.

This hierarchical structure directly influences how the platform manages security, routes events, and stores state
across different persistence layers.

## Context Storage

The platform stores context data across multiple persistence layers optimized for different access patterns and
lifecycle requirements:

**Run Context** provides short-lived storage for data specific to a single agent execution, serving as temporary working
memory for intermediate calculations and step-by-step state tracking. The platform stores agent configuration as a
special entry within Run Context at workflow initiation, ensuring every workflow run operates with a consistent,
immutable configuration throughout its execution.

**Thread Context** provides persistent storage for data that must be maintained across multiple runs within the same
conversation thread, serving as the agent's long-term memory. This includes user preferences, session metadata, and
accumulated knowledge from previous runs.

Both context types use high-performance in-memory storage (Redis) for sub-millisecond access times, ensuring optimal
agent performance during execution. For detailed information about retention policies, storage durations, capacity
limits, and lifecycle management, see the Event-Driven Communication documentation.

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

1. **Display Context Guidelines**: What are the organizational policies for when agents should create new display
   contexts versus inheriting parent display contexts? Can users control display context visibility?

2. **Thread Membership Management**: How are thread members added or removed? Can agents dynamically modify thread
   membership? What happens to access rights when a user leaves an organization?

3. **Context Size Limits**: Are there maximum size limits for data stored in Run Context or Thread Context? How should
   large contextual state be handled?

4. **Cross-Thread Context Sharing**: Can context be shared between threads? Are there mechanisms for agents to access
   context from related threads?

5. **Context Encryption**: Is context data encrypted at rest in Redis and MongoDB? Are there compliance certifications
   for data protection?

6. **Backup and Disaster Recovery**: What backup mechanisms exist for the different context types? Can thread context be
   restored after expiration if backups exist?

7. **Multi-Region Deployment**: How does context management work in multi-region deployments? Is context replicated
   across regions?

8. **Compliance and Data Residency**: Can organizations specify data residency requirements for context storage? Are
   there mechanisms to ensure context data remains within specific geographic regions?
