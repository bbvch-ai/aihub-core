---
title: Event System
index: 0
---

# Event System

![System Overview - Event System](../../../../../../media/architecture/system_overview/system-overview-highlight-nats.png)

The Swiss AI-Hub's event-driven architecture provides the communication backbone for all platform operations. This
fundamental infrastructure enables asynchronous, observable, and scalable interactions between agents, services, and
users while maintaining comprehensive audit trails essential for enterprise AI deployment.

## Purpose and Strategic Value

The event system addresses unique challenges of autonomous AI operations that must function reliably over extended
periods without direct supervision. Unlike traditional request-response architectures designed for synchronous
interactions, the event-driven model supports workflows spanning minutes, hours, or even days while maintaining complete
operational transparency.

**Asynchronous Operations**: Components communicate without blocking, enabling agents to process long-running tasks
while the system remains responsive to other requests.

**Loose Coupling**: Services interact through well-defined events rather than direct dependencies, allowing independent
evolution and deployment of platform components.

**Comprehensive Observability**: Every system action generates traceable events, creating permanent audit trails that
satisfy regulatory requirements and enable forensic investigation.

**Horizontal Scalability**: Stateless event processing enables automatic load distribution across multiple instances,
supporting high-throughput operations and resilient deployments.

## Event-Driven Architecture

The platform implements all communication through immutable events - structured records of facts that have occurred
within the system. This approach replaces synchronous method calls with asynchronous message passing, providing the
foundation for autonomous agent operations.

**Event Types and Extensibility**: Event types register automatically without manual configuration, enabling graceful
system evolution. Organizations can introduce domain-specific events that seamlessly integrate with existing
infrastructure. When components encounter unknown event types, the system degrades gracefully to known parent types,
ensuring continuous operation across version boundaries and supporting forward and backward compatibility.

**Self-Coordinating Workflows**: Agent workflows execute through continuous event processing without centralized
control. Steps automatically execute when required events arrive, producing new events that trigger subsequent
processing. This model enables automatic parallelization, conditional branching, failure isolation, and independent
testability of workflow components.

**Distributed Execution**: Event-driven coordination allows agent instances to be deployed multiple times, supporting
automatic load balancing across instances for high-throughput scenarios. The stateless nature of event processing
ensures any instance can handle any event, maximizing resource utilization.

## Communication Infrastructure

**NATS with JetStream**: The platform uses NATS as its message bus, providing reliable event delivery with persistence
through JetStream. This infrastructure ensures events survive system restarts and enables event replay for debugging and
recovery scenarios.

**Event Persistence**: Events are stored with both time-based (30 days) and capacity-based (10 million messages)
retention limits. Organizations should monitor event generation rates to estimate actual retention windows for their
specific usage patterns.

**Real-Time Streaming**: Display events stream to monitoring dashboards and user interfaces as workflows execute,
providing immediate visibility into agent operations without affecting control flow or workflow execution.

## Data Retention Strategy

The platform implements a tiered retention strategy balancing operational efficiency with compliance obligations:

**Ephemeral Data (30-Day Automatic Deletion)**: High-performance working memory stored in Redis expires automatically.
Execution-specific data provides a fixed 30-day window for debugging, while conversational memory employs a sliding
30-day expiration that resets with each access.

**Workflow Events (Dual Constraints)**: NATS JetStream manages workflow events with both time-based (30 days) and
capacity-based (10 million messages) limits. In high-throughput deployments, events may be deleted well before the
30-day limit when capacity is reached.

**Permanent Storage (Manual Lifecycle Management)**: MongoDB retains conversation history indefinitely without automatic
expiration. Organizations must implement explicit data lifecycle policies aligned with regulatory requirements and
business needs.

**Operational Implications**: Organizations have a 30-day window for forensic analysis of workflow execution details.
Critical execution information should be persisted to permanent storage before the 30-day threshold for long-term
retention. Compliance investigations requiring workflow reconstruction are limited to the available retention window.

## Integration with Platform Components

**Agent Workflows**: All agent communication occurs through events, enabling transparent, observable autonomous
operations. Workflow steps produce events that trigger subsequent processing, creating self-coordinating execution
patterns.

**API Gateway**: External requests translate to internal events, bridging synchronous client expectations with
asynchronous backend processing. The API maintains session context while coordinating event-driven workflows.

**User Interfaces**: Display events stream to frontends, providing real-time updates as workflows execute. This
separation between control flow (workflow events) and presentation (display events) ensures UI responsiveness without
impacting agent execution.

**Process Orchestration**: Complex multi-agent processes coordinate through event streams, enabling hierarchical
workflows where specialized agents contribute to larger business operations.

## Organizational Benefits

The event-driven architecture provides strategic advantages for enterprise AI deployment:

- Complete audit trails support regulatory compliance and security investigations
- Asynchronous processing enables long-running autonomous operations
- Loose coupling allows independent service evolution and deployment
- Automatic scalability through stateless event processing
- Comprehensive observability through structured event streams
- Graceful degradation and forward compatibility through flexible event typing

## Implementation Approach

Event-driven communication is transparent to developers. Agents automatically participate in the event system through
platform abstractions. The infrastructure handles event persistence, delivery guarantees, and routing, allowing
development teams to focus on business logic rather than messaging infrastructure.

For detailed information on how specific platform components leverage the event system, see the subsections covering
agent workflows, context management, and system participants.
