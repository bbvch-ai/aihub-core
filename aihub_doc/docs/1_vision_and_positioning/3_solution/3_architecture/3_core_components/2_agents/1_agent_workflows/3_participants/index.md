---
title: System Participants
index: 3
---

# System Participants in Agent Workflows

The Swiss AI-Hub's event-driven architecture defines communication rules for multiple system participants, each with
distinct roles and responsibilities. Understanding these participants and their interactions provides insight into how
the platform orchestrates complex autonomous operations while maintaining security and observability.

## Participant Roles

The platform distinguishes four primary participant types, each interacting with the event stream in specific ways:

### The Agent

Agents serve as the autonomous workers of the ecosystem, executing business logic and complex reasoning. Their role
encompasses:

**Event Consumption**: Agents consume Control Events to initiate or continue their work. Start events trigger new
workflow runs, while intermediate Control Events drive multi-step internal processes.

**Workflow Execution**: Upon receiving Control Events, agents execute their defined workflow steps, which may involve
language model interactions, knowledge base retrievals, data transformations, or business rule evaluations.

**Multiple Execution Modes**: The platform supports different agent execution contexts to accommodate various deployment
scenarios. Agents can operate in production mode for handling real user workloads, in testing mode for validation and
quality assurance, or in specialized modes for performance analysis and load testing. The architecture ensures agents
behave identically across these modes while enabling mode-specific instrumentation and monitoring.

### The API Gateway

The API Gateway functions as the secure entry point for all external clients, translating between external communication
protocols and the internal event-driven architecture. Its responsibilities include:

**Protocol Translation**: The gateway converts HTTP requests from frontend applications into internal Control Events,
and streams internal Display Events back to clients as Server-Sent Events or other appropriate formats.

**Authentication and Authorization**: Before publishing any event to the message bus, the gateway validates user
identity and verifies permissions. This ensures all events entering the system carry authenticated user context.

**Context Management**: The gateway creates and manages hierarchical context identifiers (Thread, Display, Run) for
incoming requests, enabling proper event scoping and security enforcement throughout the system.

**Event Initiation**: The gateway serves as the exclusive producer of initial Control Events originating from outside
the system, maintaining a clear security boundary between external requests and internal operations.

### The Frontend

User interfaces provide real-time visibility into agent operations, serving primarily as event consumers. Their role
encompasses:

**Display Event Consumption**: Frontends subscribe to Display Event streams for specific display contexts, receiving
real-time updates as agents execute workflows.

**UI Rendering**: Based on consumed events, frontends render streaming text, reasoning visualizations, progress
indicators, and other interactive elements that expose agent activity to users.

**Indirect Event Production**: Frontends do not produce events directly. Instead, they initiate actions by sending HTTP
requests to the API Gateway, which validates these requests and produces corresponding Control Events.

This separation ensures user interface failures or slowdowns cannot directly disrupt agent workflow execution.

### The Process Orchestrator

Process orchestrators manage high-level business processes involving multiple agents, human tasks, and external systems.
They function as specialized agents with particular orchestration responsibilities:

**Process Coordination**: Orchestrators consume Control Events (often Stop Events from worker agents) and use these to
determine which participant should act next in a multi-step business process.

**Participant Invocation**: Based on process definitions, orchestrators produce Control Events that trigger the next
participant—whether another agent, a human task request, or an external program invocation.

**Process State Management**: Through context management and event sequencing, orchestrators maintain the state of
long-running business processes that may span days or weeks.

**Compliance and Audit**: As central coordinators, orchestrators produce events that document process progression,
decision points, and participant handoffs for compliance and audit purposes.

## Interaction Patterns

System participants collaborate through well-defined interaction patterns. The platform supports three fundamental
collaboration models:

**Direct User Interaction**: Users interact with agents through the frontend and API Gateway. Synchronous HTTP requests
translate into asynchronous event-driven workflows with streaming responses, enabling real-time feedback while
maintaining the benefits of event-driven architecture.

**Agent Collaboration**: Agents delegate specialized tasks to other agents through structured request-response patterns.
This enables hierarchical decomposition of complex objectives, allowing specialized agents to contribute domain
expertise to broader workflows. For detailed information, see the Agent Collaboration and Delegation documentation.

**Human-in-the-Loop**: Workflows seamlessly pause awaiting human input for approvals, decisions, or data provision.
These pause points integrate naturally into workflow definitions, maintaining full context when humans respond hours or
days later. For detailed information, see the Human-in-the-Loop Integration documentation.

## Participant Collaboration Principles

The participant model embodies several key architectural principles with significant operational consequences:

**Decoupling Through Events**: Participants communicate exclusively through events, eliminating direct dependencies. The
API Gateway doesn't invoke agents directly; it publishes events. Agents don't call other agents; they publish delegation
events. This decoupling enables independent development, testing, and deployment of participants. Organizations can
update individual agents without coordinating changes across the system, accelerating development cycles and reducing
deployment risk.

**Single Security Boundary**: The API Gateway enforces authentication and authorization once at the system boundary.
Internal participants trust event authenticity, simplifying security logic throughout the system. This centralized
security model reduces implementation complexity, minimizes potential vulnerabilities, and enables consistent security
policy enforcement. Security audits and compliance verification focus on a single, well-defined boundary rather than
distributed security logic.

**Observable Interactions**: Every participant interaction generates events preserved in the event store. This provides
complete audit trails of system behavior without requiring separate logging infrastructure. Organizations gain
comprehensive visibility into system operations for debugging, compliance reporting, performance analysis, and security
investigations. The built-in observability eliminates the need for custom logging frameworks and ensures consistent
audit trail quality across all participants.

**Scalable Distribution**: Multiple instances of any participant type can operate concurrently. The messaging
infrastructure distributes events across available instances, enabling horizontal scalability without architectural
changes. Organizations can scale capacity by deploying additional instances in response to demand, without code
modifications or architectural redesign. This elasticity enables cost-effective resource utilization and supports
variable workload patterns.

**Flexible Composition**: New participant types can be introduced without modifying existing participants. Process
orchestrators, monitoring dashboards, and analytics services subscribe to relevant events without disrupting agent
operations. This extensibility enables organizations to evolve their AI capabilities incrementally, adding new
functionality without risking disruption to production systems. Innovation occurs at the edge—new participants integrate
with existing event streams—rather than requiring changes to core components.

This participant model enables the platform to evolve from simple chatbot interactions to complex multi-agent business
process automation while maintaining consistent communication patterns and security guarantees. Organizations can start
with basic use cases and progressively expand capabilities as requirements and confidence grow.

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

01. **Participant Discovery**: How do participants discover each other? Is there a service registry? How do agents
    locate the API Gateway? How does the gateway discover available agents for routing?

02. **Participant Lifecycle**: What happens when a participant (agent, orchestrator) starts or stops? Are there health
    check mechanisms? How does the system handle graceful shutdowns during active workflows?

03. **Load Balancing Strategy**: When multiple instances of the same agent exist, how are events distributed? Is it
    round-robin, least-loaded, or consistent hashing? Can specific instances be targeted?

04. **Participant Authentication**: How do participants authenticate to the messaging infrastructure? Do agents use
    service principals or shared secrets? How are credentials managed and rotated?

05. **Event Subscription Management**: How do participants subscribe to relevant events? Are subscriptions dynamic or
    configuration-driven? Can participants adjust subscriptions at runtime?

06. **Participant Monitoring**: What monitoring capabilities exist for participant health and performance? Are there
    dashboards showing participant activity, event processing rates, and error rates?

07. **Error Handling Between Participants**: What happens when a participant fails to process an event? Are there retry
    mechanisms? Dead letter queues? How are persistent failures escalated?

08. **Gateway Scalability**: Can multiple API Gateway instances run concurrently? How is state managed across gateway
    instances? What are the performance implications of gateway horizontal scaling?

09. **Custom Participant Types**: Can organizations introduce custom participant types beyond agents, gateways,
    frontends, and orchestrators? What extension points exist? Are there SDK requirements?

10. **Inter-Participant Security**: Beyond the gateway security boundary, do participants authenticate each other? Are
    there mechanisms to prevent rogue participants from injecting malicious events?
