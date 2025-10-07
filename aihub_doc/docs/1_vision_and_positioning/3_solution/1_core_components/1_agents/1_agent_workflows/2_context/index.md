---
title: Context Management
index: 2
---

# TODO: @mhoegger verify


# Context Management in Agent Workflows

The Swiss AI-Hub implements a sophisticated context management system that enables agents to maintain state across conversations while ensuring optimal performance and resource utilization. This system uses a multi-layered storage architecture designed to balance immediate responsiveness with long-term data retention.

## Hierarchical Context Scoping

The platform organizes all agent interactions through a three-level hierarchical context structure. This hierarchy provides granular control over state management, security, and observability while enabling flexible workflow composition.

### The Three-Level Context Hierarchy

Every agent interaction operates within three nested scopes, each serving distinct purposes:

**Thread Context** represents the highest-level scope, grouping multiple interactions and workflow runs that belong to a single overarching goal or conversation. A chat conversation constitutes a thread. An autonomous agent processing business documents for an entire month might operate within a single thread for that month's work. Thread context maintains long-term history and state across extended periods, enabling conversational continuity and process consistency.

**Display Context** provides an intermediate scope designed for grouping multiple workflow runs together for presentation in user interfaces. This scope can span activities from multiple agents, controlling what end-users or observers see. When an agent delegates work to another agent, it can choose to pass on its display context, making both agents' activities appear as a single seamless interaction in the user interface. Alternatively, creating a new display context for delegated work effectively hides that work from specific UI views, enabling background processing invisible to the user.

**Run Context** represents the most granular scope, defining a single traceable execution of a workflow between a start event and corresponding stop or exception event. This scope provides unique identification for individual agent operations, essential for tracing and debugging as it isolates events of one specific task.

This hierarchical structure directly influences how the platform manages security, routes events, and stores state across different persistence layers.

### Security Through Hierarchical Scoping

The hierarchical context structure forms the foundation of the platform's security model. Access control operates at the thread level: users can only observe events from threads of which they are members. This ensures conversations and workflows remain private to authorized participants.

Agents can also operate in threads without human members. In such cases, only administrators with sufficient permissions for the participating agents can observe events within that thread. This capability ensures autonomous backend processes remain secure and isolated from unauthorized access.

The scoping hierarchy encoded into every event topic enables the messaging infrastructure to enforce these security boundaries automatically, without requiring event-by-event permission checks.

## Context Architecture Overview

The platform distinguishes between different types of context based on their scope and lifecycle, storing each type in the most appropriate backend system to optimize for both performance and persistence. The hierarchical scoping structure described above maps onto multiple storage systems, each optimized for specific use cases.

### Threads and Runs: Foundational Organization

The context system is built around two fundamental concepts that organize agent interactions within the hierarchical scoping structure:

**Threads** represent ongoing conversations or workflows between users and agents. A thread maintains its identity across multiple interactions, enabling contextual continuity. Each thread has a unique identifier that persists throughout its lifecycle and is associated with specific users and agents. Threads form the highest level of the security boundary.

**Runs** represent individual executions or attempts within a thread. When a user sends a message to an agent, the agent processes it in a distinct run. A single thread may contain many runs as the conversation progresses, with each run having its own unique identifier and execution context. Runs provide the granular scope necessary for precise debugging and tracing.

## Context Types and Storage

The platform provides two distinct context types, each optimized for different use cases and stored in different backend systems:

### Run Context

Run Context provides short-lived storage for data specific to a single agent execution. This context is isolated between different runs and automatically expires after a defined period.

**Purpose and Use Cases:**
Run Context serves as temporary working memory for intermediate calculations, step-by-step state tracking, and temporary caching within a single agent execution. For example, in a multi-step analysis workflow, the agent might store preliminary findings from early steps in Run Context to be used by later steps in the same run.

**Storage Implementation:**
Run Context data is stored in Redis, a high-performance in-memory data store. Each piece of data is stored with a key pattern combining the thread identifier, run identifier, and a descriptive key. The platform automatically manages the lifecycle of this data through Redis's native time-to-live mechanism, with each entry expiring after 30 days.

The platform stores agent configuration as a special entry within Run Context at workflow initiation. This ensures every workflow run operates with a consistent, immutable configuration throughout its execution, even if the agent's default configuration changes during processing. This configuration snapshot enables precise replay of historical runs with their original parameters.

**Data Lifecycle:**
Data written to Run Context during an agent execution remains available throughout that execution and persists for 30 days afterward. This retention period allows for debugging and analysis of past executions while ensuring automatic cleanup of temporary data. Once a run completes, its context data becomes read-only and is primarily used for troubleshooting or audit purposes. The stored agent configuration enables developers to understand exactly what parameters drove agent behavior during historical executions.

### Thread Context

Thread Context provides persistent storage for data that must be maintained across multiple runs within the same conversation thread. This enables agents to maintain conversational continuity and remember information from previous interactions.

**Purpose and Use Cases:**
Thread Context serves as the agent's long-term memory for a conversation, storing user preferences, session metadata, conversation summaries, and accumulated knowledge from previous runs. For example, if a user indicates their preferred language or provides context about their use case, this information can be stored in Thread Context and used across all subsequent runs in that thread.

**Storage Implementation:**
Like Run Context, Thread Context uses Redis for storage, ensuring fast access to conversational state. The data is organized by thread identifier, with all runs within that thread sharing access to the same context data. Each entry maintains a 30-day time-to-live period that refreshes with each access, ensuring actively used threads retain their context while inactive threads are cleaned up automatically.

**Data Lifecycle:**
Thread Context data remains available across all runs within a thread for 30 days from the last access. As conversations continue, the time-to-live period is extended with each interaction. This approach ensures active conversations maintain their full context while inactive threads are automatically archived.

### Conversation History and Events

Beyond the ephemeral context systems, the platform maintains permanent records of all interactions and events through MongoDB, providing comprehensive audit trails and conversation history.

**Message Persistence:**
All user messages, agent responses, and interaction events are permanently stored in MongoDB as structured event documents. Each event includes the thread identifier, run identifier, event type, timestamp, and complete event data. This comprehensive event log enables the platform to reconstruct full conversation histories and analyze agent behavior across all interactions.

**Thread Metadata:**
Thread information, including participating users and agents, creation timestamps, and thread relationships, is stored in MongoDB with no expiration. This permanent record enables the platform to provide users with access to their complete conversation history and supports long-term analytics and compliance requirements.

**Message History Retrieval:**
When an agent needs access to conversation history, the platform queries MongoDB to retrieve relevant events from the thread. The system filters these events to extract user messages and agent responses, reconstructing the conversation flow. This separation between working context (Redis) and permanent history (MongoDB) allows the platform to optimize for both immediate performance and long-term data retention.

## Workflow Event Management

The platform uses NATS JetStream to manage workflow events that control agent execution, providing reliable event streaming with automatic persistence and replay capabilities.

**Event Storage:**
Control events that drive agent workflow execution are stored in NATS JetStream with file-based persistence. The platform configures these streams with a 30-day retention policy and a maximum capacity of 10 million messages. When the stream reaches capacity, the oldest messages are automatically discarded while maintaining the most recent workflow states.

**In-Memory Caching:**
To optimize performance, frequently accessed execution contexts are cached in memory with a 30-day time-to-live period. This dual-layer approach (persistent JetStream storage plus in-memory cache) ensures both reliability and responsiveness, allowing agents to quickly access recent execution states while maintaining the ability to replay historical workflows.

**Replay Capability:**
The platform can replay the complete event history for a thread from JetStream storage, enabling sophisticated debugging, analysis, and recovery scenarios. This capability proves valuable when investigating agent behavior, recovering from failures, or analyzing execution patterns across multiple runs.

## Data Retention Strategy and Implications

The platform implements a carefully designed retention strategy that balances operational efficiency, system performance, data protection requirements, and compliance obligations. Understanding the implications of this strategy is crucial for organizations deploying the platform.

### Ephemeral Storage: Redis (30-Day Automatic Deletion)

Ephemeral data stored in Redis is subject to automatic, irreversible deletion after 30 days from creation or last access. This automated deletion has several important implications:

**Run Context (30 Days, No Refresh):**
Data written to Run Context expires exactly 30 days after creation, regardless of subsequent access. This means:
- Organizations have a fixed 30-day window for debugging and analyzing completed agent executions
- After 30 days, all intermediate calculation results, temporary state, and step-by-step execution details are permanently deleted
- No manual intervention can extend this retention period for specific runs
- The automatic deletion ensures predictable storage costs and prevents accumulation of obsolete debugging data

**Practical Implications for Run Context:**
For incident investigation and compliance requirements, organizations must capture and export any critical debugging information within the 30-day window. The platform does not provide mechanisms to selectively preserve Run Context beyond this period, as this data is explicitly designed as ephemeral working memory.

**Thread Context (30 Days, Refreshed on Access):**
Thread Context employs a sliding expiration window that resets with each read or write operation. This creates a dynamic retention behavior:
- Active conversations continuously extend their context retention as long as interactions occur
- Conversations inactive for 30 days have their context automatically and permanently deleted
- There is no warning or notification before automatic deletion occurs
- Once deleted, user preferences, session metadata, and accumulated conversation state are irrecoverably lost

**Practical Implications for Thread Context:**
Organizations must understand that conversation context automatically disappears after 30 days of inactivity. For use cases requiring long-term memory across extended idle periods, applications must implement explicit context preservation by:
- Periodically accessing Thread Context to refresh its TTL (artificial "keep-alive" mechanism)
- Persisting critical context information to MongoDB explicitly before the 30-day threshold
- Designing agent workflows that gracefully handle missing context when users return after extended absences

**Redis Deletion Mechanism:**
Redis deletion is passive and automatic. When a key's TTL expires, Redis removes it during its background eviction cycle. This means:
- No application code is executed during deletion
- No callbacks or notifications inform the application that data has expired
- The deletion is permanent with no recovery mechanism
- Organizations cannot configure different retention periods for different threads or runs without modifying platform code

### Workflow Event Storage: NATS JetStream (30 Days + Capacity Limits)

NATS JetStream manages workflow control events with dual retention constraints that interact in complex ways:

**Dual Retention Boundaries:**
Events are subject to both time-based (30 days) and capacity-based (10 million messages) limits. Deletion occurs when either threshold is reached:
- Time-based deletion: Events older than 30 days are automatically removed regardless of stream capacity
- Capacity-based deletion: When the stream exceeds 10 million messages, the oldest events are deleted to maintain the capacity limit, even if they are less than 30 days old

**Implications of Capacity-Based Deletion:**
In high-throughput deployments, workflow events may be deleted well before the 30-day time limit:
- Organizations with heavy agent usage may see workflow history limited to days or weeks rather than a full month
- The actual retention period becomes unpredictable and dependent on system load
- Critical workflow traces for recent runs may be deleted prematurely in busy environments
- Capacity planning requires monitoring event generation rates to estimate actual retention windows

**Stream Configuration Rigidity:**
The 10-million message limit and 30-day retention are configured at the platform level. Organizations cannot:
- Adjust these limits per thread or agent type
- Prioritize retention of certain event types over others
- Prevent deletion of events for specific high-priority workflows
- Receive warnings when approaching capacity limits

**Workflow Replay Limitations:**
The ability to replay workflow execution depends entirely on event availability in JetStream. Once events are deleted:
- Historical workflow states become unrecoverable
- Debugging of issues that manifested more than 30 days ago (or earlier with high throughput) becomes impossible
- Compliance investigations requiring workflow reconstruction are limited to the available retention window
- Organizations cannot extend retention for specific incidents under investigation

### Persistent Storage: MongoDB (Indefinite, Manual Deletion Required)

MongoDB stores thread metadata and complete message history without automatic expiration, creating different operational implications:

**Indefinite Retention Benefits:**
The absence of automatic deletion provides:
- Complete conversation history available for all historical interactions
- Reliable audit trails for compliance and regulatory requirements
- Long-term analysis capabilities for usage patterns and agent performance
- User access to complete conversation archives regardless of age

**Indefinite Retention Challenges:**
Without automatic cleanup, organizations face different data management challenges:
- MongoDB storage continuously grows as conversation volume increases
- Organizations must implement explicit data lifecycle policies for aged conversations
- Data protection regulations (GDPR, data minimization principles) may require periodic purging
- No built-in mechanisms for automated deletion based on data age or relevance

**Manual Deletion Requirements:**
Organizations must implement custom processes for MongoDB data lifecycle management:
- Identify conversations subject to retention policy limits or user deletion requests
- Execute database operations to remove thread metadata and associated events
- Ensure referential integrity when deleting threads referenced by other system components
- Maintain audit logs of data deletion activities for compliance verification

**Data Protection Implications:**
The permanent retention default creates specific obligations:
- Organizations must actively manage personal data retention to comply with data protection regulations
- User right-to-deletion requests require explicit database operations
- Data minimization principles may require periodic review and purging of aged conversations
- Privacy impact assessments must account for indefinite message retention

### Data Synchronization and Consistency Challenges

The separation of ephemeral and persistent storage creates potential data consistency scenarios:

**Context Loss After 30 Days:**
After Thread Context expires in Redis while the conversation history remains in MongoDB:
- Agents can access complete message history but lose stored preferences and session state
- Resuming old conversations may result in degraded experience as agents lack contextual memory
- Users may need to re-establish preferences and context that was previously stored
- The platform cannot automatically reconstruct expired Thread Context from message history

**Debugging Limitations After Expiration:**
When investigating historical issues:
- MongoDB provides the "what" (what messages were exchanged)
- After 30 days, Redis no longer provides the "how" (how the agent processed those messages internally)
- NATS JetStream may no longer provide the "why" (why the agent made specific workflow decisions)
- Complete forensic analysis is only possible within the ephemeral retention window

**Storage Cost Trade-offs:**
The tiered retention strategy creates predictable cost patterns:
- Redis costs remain bounded due to automatic expiration of ephemeral data
- MongoDB costs grow continuously without active data lifecycle management
- Organizations cannot trade increased costs for extended ephemeral retention without platform modifications
- Storage cost optimization requires active MongoDB data management strategies

### Recommendations for Organizations

Organizations deploying the platform should:
- Implement monitoring for NATS JetStream event rates to predict actual workflow retention periods
- Establish explicit MongoDB data lifecycle policies aligned with regulatory requirements and business needs
- Design critical workflows to persist essential context to MongoDB before 30-day Thread Context expiration
- Create processes for capturing critical debugging information within the 30-day ephemeral retention window
- Develop procedures for handling user data deletion requests across all storage systems
- Consider the 30-day ephemeral retention limit when defining incident response and investigation timelines

## Storage Architecture Integration

The context management system integrates with the platform's infrastructure components to provide a cohesive data storage solution:

**Redis Integration:**
Redis serves as the primary backend for ephemeral context storage, providing sub-millisecond access times for Run Context and Thread Context data. The platform leverages Redis's native TTL mechanisms for automatic data expiration and its atomic operations for thread-safe context updates.

**MongoDB Integration:**
MongoDB provides durable storage for thread metadata and complete event histories. The platform uses MongoDB's flexible document model to store complex event structures and its indexing capabilities to enable efficient queries across large conversation histories.

**NATS JetStream Integration:**
NATS JetStream manages workflow event streams with configurable retention policies and replay capabilities. The platform uses JetStream's persistent storage for reliable event delivery and its streaming architecture for efficient event processing across distributed agent instances.

This multi-backend architecture ensures the platform delivers optimal performance for real-time agent interactions while maintaining comprehensive historical records for long-term analysis and compliance requirements.

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

1. **Display Context Creation and Management**: What are the rules for when agents should create new display contexts versus inheriting parent display contexts? Are there organizational guidelines for display context scoping? Can users control display context visibility?

2. **Thread Membership Management**: How are thread members added or removed? Can agents dynamically modify thread membership? What happens to access rights when a user leaves an organization but threads containing their data remain?

3. **Context Size Limits**: Are there maximum size limits for data stored in Run Context or Thread Context? How should large contextual state be handled? Are there best practices for context size optimization?

4. **Cross-Thread Context Sharing**: Can context be shared between threads? Are there mechanisms for agents to access context from related threads (e.g., forked conversations, related business processes)?

5. **Context Encryption**: Is context data encrypted at rest in Redis and MongoDB? Is thread context encrypted differently based on sensitivity? Are there compliance certifications for data protection?

6. **Backup and Disaster Recovery**: What backup mechanisms exist for the different context types? Can thread context be restored after expiration if backups exist? What is the recovery point objective (RPO) for persistent MongoDB data?

7. **Context Migration**: How is context handled when agents are upgraded or replaced? Can context be migrated between different agent versions? What happens to context when an agent is deprecated?

8. **Multi-Region Deployment**: How does context management work in multi-region deployments? Is context replicated across regions? What are the latency implications for cross-region context access?

9. **Context Access Patterns**: What are the performance characteristics of context access? Are there caching strategies beyond Redis? What are the recommended patterns for minimizing context access latency?

10. **Compliance and Data Residency**: Can organizations specify data residency requirements for context storage? Are there mechanisms to ensure context data remains within specific geographic regions? How does this interact with the distributed architecture?
