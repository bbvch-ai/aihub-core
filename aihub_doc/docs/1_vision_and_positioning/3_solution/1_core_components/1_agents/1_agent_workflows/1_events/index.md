---
title: Event-Driven Communication
index: 1
---

# TODO: @mhoegger verify


# Event-Driven Communication in Agent Workflows

The Swiss AI-Hub implements agent workflows through a sophisticated event-driven architecture that enables transparent, scalable, and resilient autonomous operations. This communication model represents a fundamental departure from traditional request-response architectures, providing the foundation for long-running, observable, and composable agent behaviors.

## Communication Philosophy

The platform's communication architecture addresses the unique challenges of autonomous AI systems that operate independently over extended periods. Unlike chatbots limited to synchronous request-response interactions, the platform's agents function as persistent, autonomous entities capable of executing workflows that span minutes, hours, or even months without direct user intervention.

This persistent autonomy necessitates a communication model that supports:

- **Asynchronous Operations**: Agents process tasks without blocking other system components
- **State Independence**: Agent logic remains stateless while state is externalized to infrastructure
- **Deep Observability**: Every action, thought, and state transition generates traceable events
- **Loose Coupling**: Components communicate without direct dependencies on each other's implementation

## The Event as Fundamental Communication Unit

Events serve as immutable records of facts that have occurred within the system. Each event is a structured, typed data object representing a specific occurrence or state change. The platform distinguishes events into distinct categories based on their purpose within the architecture.

### Control Events: Workflow Instructions

Control Events drive workflow execution and cause state changes within the system. The protocol mandates that only Control Events can trigger the execution of agent workflow steps. These events represent commands, completed tasks, or responses that require agents to proceed to the next logical operation.

Control Events influence system flow by:

- Initiating new workflow runs when user messages arrive
- Advancing internal agent processing through multi-step operations
- Delegating tasks to other agents or system components
- Signaling workflow completion or exceptional conditions

Examples include user message events that start agent processing, internal step completion events that drive multi-stage workflows, and agent delegation events that coordinate between autonomous components.

### Display Events: Observability Information

Display Events provide purely informational content intended for observation by users or monitoring systems. The protocol mandates that Display Events must never influence the logical flow of agent workflows. Their purpose is providing real-time narrative of agent internal states, reasoning processes, and partial results.

This strict separation ensures that failures in UI components or logging systems cannot disrupt agent core logic. Display Events enable:

- Real-time streaming of agent-generated content to user interfaces
- Transparency into agent reasoning and decision-making processes
- Progress indicators and status updates for long-running operations
- Detailed telemetry for monitoring, debugging, and compliance

Examples include text chunks streamed token-by-token to user interfaces, thought events revealing agent reasoning steps, and cost tracking events for operational monitoring.

### Dual-Purpose Events

Certain events serve both control and display functions simultaneously. These events adhere to the rules of both categories, influencing workflow execution while simultaneously providing information to observers.

Workflow lifecycle events exemplify this dual nature: a stop event terminates workflow execution (control function) while informing user interfaces that processing has completed (display function). This design ensures both system components and human observers maintain consistent understanding of workflow states.

## Event Structure and Metadata

Every event carries standardized metadata enabling routing, tracing, and observability across the distributed system:

- **Event Identity**: Unique identifier distinguishing this specific event instance
- **Timestamp**: Nanosecond-precision creation time enabling precise sequencing
- **Type Hierarchy**: Full inheritance chain supporting flexible event routing and filtering
- **Display Information**: Multi-language names and descriptions for user-facing presentation

This metadata enables sophisticated event processing patterns including hierarchical filtering, multilingual user interfaces, and precise temporal reconstruction of workflow execution.

### Automatic Event Registration and Discovery

The platform implements automatic event type registration, enabling dynamic system evolution without manual configuration. When new event types are defined in the codebase, they automatically register themselves in a central event registry during application initialization. This registry enables:

**Dynamic Deserialization**: The system can deserialize incoming events into appropriate type instances based solely on event metadata, without requiring explicit type mappings. This capability is essential for distributed systems where different components may process events of types unknown at compile time.

**Graceful Degradation**: When the system encounters events of unrecognized types, it automatically falls back to the closest known parent type in the inheritance hierarchy. This fallback mechanism ensures system operation continues even when components receive events from newer versions of other components.

**Extensibility Without Modification**: Organizations can introduce domain-specific event types without modifying platform code. Custom events integrate seamlessly with existing routing, storage, and monitoring infrastructure through the automatic registration mechanism.

**Nested Event Structures**: Events can contain other events as nested data structures, enabling complex information hierarchies. The deserialization system recursively processes nested events, preserving type information throughout the structure.

## Core Event Categories

The platform defines standardized event types for common operations in agentic systems:

### Lifecycle Events

Lifecycle events manage the states of workflow runs:

- **Start Events**: Signal the beginning of new workflow runs and carry initial context
- **Stop Events**: Indicate successful workflow completion with no further processing
- **Exception Events**: Signal unrecoverable errors causing workflow termination

### User Interaction Events

User interaction events handle direct input from human users:

- **User Message Events**: Specialized start events triggered by user messages, containing message history and user identity

### Streaming and Reasoning Events

Streaming events provide real-time updates about agent internal processing:

- **Chunk Events**: Enable token-by-token text streaming to user interfaces
- **Thought Events**: Expose agent internal reasoning and current actions for transparency

### Observability Events

Observability events provide detailed telemetry for monitoring and cost management:

- **LLM Events**: Record language model invocations including prompts, responses, and parameters
- **Retriever Events**: Document knowledge base retrieval operations and retrieved content
- **Cost Events**: Track calculated costs of AI interactions including token consumption

### Asynchronous Interaction Events

Interaction events manage complex multi-step workflows requiring pauses and resumptions:

- **Human-in-the-Loop Events**: Pause workflows to request human input or approval, then resume upon response
- **Agent-in-the-Loop Events**: Delegate tasks to other agents, pausing until delegated work completes

These request-response patterns enable sophisticated approval workflows, expert consultation processes, and hierarchical agent collaboration.

## Event-Driven Workflow Execution

Agent workflows execute through event consumption and production:

1. **Event Reception**: Agents subscribe to specific event types relevant to their function
2. **Step Execution**: Workflow steps consume Control Events as inputs, executing defined logic
3. **Event Production**: Steps produce new events (both Control and Display) as outputs
4. **Event Routing**: The messaging infrastructure delivers events to appropriate consumers

This model enables:

- **Workflow Decomposition**: Complex tasks broken into discrete, testable steps
- **Parallel Processing**: Independent workflow branches executing concurrently
- **Conditional Logic**: Different event types routing to appropriate processing steps
- **Error Isolation**: Failures contained to specific workflow branches without cascading

## Event Storage and Replay

The platform implements sophisticated event storage enabling both real-time processing and historical analysis:

**Persistent Event Streams**: All Control Events are stored in persistent event streams with guaranteed ordering and delivery. Each event receives a unique sequence number enabling precise replay of workflow execution from any historical point.

**Replay Capabilities**: The system can reconstruct complete workflow state by replaying historical events. This capability proves essential for debugging production issues, analyzing agent behavior patterns, and recovering from system failures. Replay operates at multiple granularities—individual workflow runs, complete threads, or arbitrary time windows.

**Event Stream Segmentation**: Events are organized into streams based on their hierarchical context (thread, display, run), enabling efficient retrieval and replay of related events without processing unrelated data. This segmentation optimizes both storage efficiency and replay performance.

**Immutable Event Log**: Once stored, events cannot be modified or deleted (within retention windows), ensuring audit trail integrity. This immutability provides strong guarantees for compliance, security investigations, and forensic analysis of system behavior.

## Observability Through Events

The event-driven model provides comprehensive observability into agent operations:

- **Complete Audit Trails**: Every workflow step produces events creating permanent execution records with sequence numbers enabling precise chronological reconstruction
- **Real-Time Monitoring**: Display events stream to monitoring dashboards as workflows execute, providing immediate visibility into agent operations
- **Debugging Support**: Event sequences reconstructed from persistent storage enable time-travel debugging of past workflow executions with complete state information
- **Compliance Documentation**: Event logs provide evidence of processing steps, decision points, and data transformations suitable for regulatory submission

This granular event stream supports regulatory compliance, quality assurance, continuous improvement of agent behaviors, and forensic investigation of incidents.

## Scalability and Resilience

The event-driven architecture enables horizontal scalability and system resilience:

- **Stateless Agent Code**: Agent logic contains no mutable state, enabling any instance to process any event
- **Load Distribution**: Events distributed across multiple agent instances for parallel processing
- **Failure Recovery**: Failed operations retried without state loss through event replay
- **System Evolution**: New event types introduced without modifying existing components

Organizations can scale agent capacity by deploying additional instances without architectural changes, and system upgrades deploy incrementally without service interruption.

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

1. **Event Persistence Duration**: How long are events retained in the message bus? Is there a difference between persistence for Control Events versus Display Events? Are there capacity limits that could trigger earlier deletion?

2. **Event Ordering Guarantees**: What ordering guarantees does the system provide for events within a single workflow run? Across multiple concurrent runs? Are there scenarios where event ordering might not be preserved?

3. **Event Schema Evolution**: How does the system handle schema changes when events are upgraded with new fields or structures? Is there a versioning strategy? How are older event types handled when consumed by newer code?

4. **Event Replay Capabilities**: Under what circumstances can events be replayed? Are there limitations on replay scope (single run, entire thread, time window)? What are the security implications of event replay?

5. **Display Event Delivery Guarantees**: Since Display Events don't affect control flow, what delivery guarantees are provided? Can Display Events be dropped under high load? How does the system handle slow consumers of Display Events?

6. **Custom Event Creation Guidelines**: What are the organizational policies for creating domain-specific custom events? When should teams create new event types versus using existing ones? Are there approval processes or architectural reviews required?

7. **Event Size Limits**: Are there maximum size constraints for event payloads? How should large data be handled (e.g., documents, images)? Should references to external storage be used instead of embedding large payloads?

8. **Multi-Language Event Support**: The documentation mentions internationalization support. Are event names and descriptions required to support all four platform languages (de, en, fr, it)? How is this enforced during development?
