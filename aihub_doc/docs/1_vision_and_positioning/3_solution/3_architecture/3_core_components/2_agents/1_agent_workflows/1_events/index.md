---
title: Event-Driven Communication
index: 1
---

# Event-Driven Communication in Agent Workflows

The Swiss AI-Hub implements agent workflows through a sophisticated event-driven architecture that enables transparent,
scalable, and resilient autonomous operations. This communication model represents a fundamental departure from
traditional request-response architectures, providing the foundation for long-running, observable, and composable agent
behaviors.

## Communication Philosophy

The platform's communication architecture addresses the unique challenges of autonomous AI systems that operate
independently over extended periods. Unlike chatbots limited to synchronous request-response interactions, the
platform's agents function as persistent, autonomous entities capable of executing workflows that span minutes, hours,
or even months without direct user intervention.

This persistent autonomy necessitates a communication model that supports:

- **Asynchronous Operations**: Agents process tasks without blocking other system components
- **State Independence**: Agent logic remains stateless while state is externalized to infrastructure
- **Deep Observability**: Every action, thought, and state transition generates traceable events
- **Loose Coupling**: Components communicate without direct dependencies on each other's implementation

## Event-Driven Architecture

The platform implements all agent communication through immutable events—structured records of facts that have occurred
within the system. This event-driven approach replaces traditional synchronous method calls with asynchronous message
passing, enabling loose coupling, comprehensive audit trails, and horizontal scalability.

**Automatic Type Management and Extensibility**: Event types register automatically without manual configuration,
enabling graceful system evolution and rapid integration of new capabilities. Organizations can introduce
domain-specific event types that seamlessly integrate with existing infrastructure, allowing teams to extend workflows
without modifying core components. When components encounter unknown event types, the system degrades gracefully to
known parent types, ensuring continuous operation across version boundaries and supporting forward and backward
compatibility. This approach enables innovation, reduces maintenance overhead, and accelerates the adoption of new
features across the platform.

**Self-Coordinating Workflows**: Agent workflows execute through continuous event processing without centralized
control. Steps automatically execute when required events arrive, producing new events that trigger subsequent
processing. This model enables automatic parallelization, conditional branching, failure isolation, and independent
testability of workflow components. Decoupling agent logic from infrastructure allows agent instances to be deployed
multiple times, supporting high throughput and enabling automatic load balancing across instances for scalable
operations.


## Data Retention Strategy

The platform implements a carefully designed retention strategy that balances operational efficiency with compliance
obligations:

**Ephemeral Data (30-Day Automatic Deletion):** High-performance working memory stored in Redis expires automatically.
Execution-specific data provides a fixed 30-day window for debugging, while conversational memory employs a sliding
30-day expiration that resets with each access. Organizations must capture critical debugging information within this
window, as no mechanisms exist to selectively preserve ephemeral data beyond the 30-day period.

**Workflow Events (Dual Constraints):** NATS JetStream manages workflow events with both time-based (30 days) and
capacity-based (10 million messages) limits. In high-throughput deployments, events may be deleted well before the
30-day limit when capacity is reached. Organizations should monitor event generation rates to estimate actual retention
windows for their specific usage patterns.

**Permanent Storage (Manual Lifecycle Management):** MongoDB retains conversation history indefinitely without automatic
expiration. Organizations must implement explicit data lifecycle policies aligned with regulatory requirements (GDPR,
data minimization principles) and business needs. This includes processes for handling user data deletion requests and
periodic purging of aged conversations.

**Operational Implications:** The tiered retention strategy creates specific operational responsibilities:

- Organizations have a 30-day window for forensic analysis of workflow execution details
- After 30 days of inactivity, working memory is lost even though event history remains in permanent storage
- Critical execution information should be persisted to permanent storage before the 30-day threshold for long-term
  retention
- Compliance investigations requiring workflow reconstruction are limited to the available retention window

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

1. **Event Ordering Guarantees**: What ordering guarantees does the system provide for events within a single workflow
   run? Across multiple concurrent runs? Are there scenarios where event ordering might not be preserved?

2. **Event Schema Evolution**: How does the system handle schema changes when events are upgraded with new fields or
   structures? Is there a versioning strategy? How are older event types handled when consumed by newer code?

3. **Event Replay Capabilities**: Under what circumstances can events be replayed? Are there limitations on replay scope
   (single run, entire thread, time window)? What are the security implications of event replay?

4. **Display Event Delivery Guarantees**: Since Display Events don't affect control flow, what delivery guarantees are
   provided? Can Display Events be dropped under high load? How does the system handle slow consumers of Display Events?

5. **Custom Event Creation Guidelines**: What are the organizational policies for creating domain-specific custom
   events? When should teams create new event types versus using existing ones? Are there approval processes or
   architectural reviews required?

6. **Event Size Limits**: Are there maximum size constraints for event payloads? How should large data be handled (e.g.,
   documents, images)? Should references to external storage be used instead of embedding large payloads?

7. **Multi-Language Event Support**: The documentation mentions internationalization support. Are event names and
   descriptions required to support all four platform languages (de, en, fr, it)? How is this enforced during
   development?
