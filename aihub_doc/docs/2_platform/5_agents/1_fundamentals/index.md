---
title: Agent Fundamentals
index: 1
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

Both context types use high-performance in-memory storage for sub-millisecond access times, ensuring optimal
agent performance during execution.

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
expertise to broader workflows. For detailed information, see the Agent Collaboration and Delegation (agent in the loop)

**Human-in-the-Loop**: Workflows seamlessly pause awaiting human input for approvals, decisions, or data provision.
These pause points integrate naturally into workflow definitions, maintaining full context when humans respond hours or
days later. For detailed information, see the Human-in-the-Loop Integration.

## Collaboration Principles

The participant model embodies key architectural principles with significant operational advantages:

**Decoupling Through Events**: Participants communicate exclusively through events, eliminating direct dependencies.
This enables independent development, testing, and deployment. Organizations can update individual agents without
coordinating system-wide changes, accelerating development and reducing deployment risk.

**Single Security Boundary**: The API Gateway enforces authentication and authorization once at the system boundary.
Internal participants trust event authenticity, simplifying security logic and enabling consistent policy enforcement.

**Observable Interactions**: Every participant interaction generates events preserved in the event store, providing
complete audit trails without separate logging infrastructure. Organizations gain comprehensive visibility for
debugging, compliance, performance analysis, and security investigations.

**Scalable Distribution**: Multiple instances of any participant type can operate concurrently. The messaging
infrastructure distributes events across instances, enabling horizontal scalability without architectural changes or
code modifications.

**Flexible Composition**: New participant types can be introduced without modifying existing participants. Process
orchestrators, monitoring dashboards, and analytics services subscribe to relevant events without disrupting operations,
enabling incremental capability evolution.

This participant model enables platform evolution from simple chatbot interactions to complex multi-agent business
process automation while maintaining consistent communication patterns and security guarantees.


# Human-in-the-Loop Integration

The Swiss AI-Hub enables seamless integration of human judgment into autonomous agent workflows. This capability
addresses a fundamental requirement for enterprise AI: the ability to pause automated processes at critical decision
points, gather human input, and continue execution with full context preservation.

## Integration Philosophy

Not all decisions can or should be fully automated. Regulatory requirements, strategic importance, ethical
considerations, or simple prudence often mandate human oversight at specific workflow junctures. Traditional automation
systems handle such requirements poorly, forcing awkward transitions between automated and manual processes that lose
context and create operational friction.

The platform addresses this challenge by treating human involvement as a first-class workflow pattern. Agents can
request human input at any point, workflows pause naturally while awaiting responses, and execution resumes seamlessly
when humans provide decisions—whether minutes, hours, or days later. **Critically, the workflow continues from exactly
where it paused**, rather than restarting the agent's entire reasoning process.

## Human Approval Pattern

The platform implements human-in-the-loop through a standardized event-driven pattern:

1. An agent reaches a decision point requiring human approval
2. The agent publishes a Human-in-the-Loop Request Event containing the approval question and context
3. The API Gateway routes this event to appropriate human participants based on thread membership
4. The frontend displays the approval request to the human user
5. Upon user response, the frontend sends the approval decision to the API Gateway
6. The gateway publishes a Human-in-the-Loop Response Event containing the human decision
7. The agent consumes this response and continues workflow execution based on the approval outcome

This pattern demonstrates how autonomous workflows pause for human judgment while maintaining audit trails and security
context.

## Workflow Integration

Human-in-the-loop integrates naturally into agent workflow definitions:

**Declarative Requests**: Agents specify approval requirements as part of their workflow logic, defining what
information must be presented to humans and what response options are available. This declarative approach makes human
involvement explicit and reviewable during workflow design.

**Context Preservation**: All workflow state and conversational context remain available when humans respond. Whether a
human approves a decision immediately or returns days later, the agent continues execution **from exactly where it
paused** with complete knowledge of the original request and workflow state. This is a crucial advantage over systems
where human interaction triggers a complete restart of the agent's internal workflow—in the Swiss AI-Hub, especially in
complex multi-step workflows, the agent seamlessly resumes at the exact point where human input was needed, preserving
all intermediate results, context, and progress.

**Audit Trail Generation**: Every human-in-the-loop interaction generates detailed audit events documenting the question
posed, who responded, what decision was made, and when. This comprehensive audit trail satisfies compliance requirements
and enables forensic analysis of workflow execution.

## Use Cases

Human-in-the-loop integration enables critical enterprise scenarios:

**Regulatory Approvals**: Workflows requiring legal, compliance, or financial approval can pause automatically at
designated checkpoints, present relevant information to authorized approvers, and continue only upon explicit approval.

**Quality Assurance**: Automated analysis or content generation workflows can request human review before finalizing
outputs, ensuring quality standards while maintaining automation efficiency for routine cases.

**Exception Handling**: When agents encounter ambiguous situations or low-confidence decisions, they can request human
clarification rather than proceeding with potentially incorrect actions or simply failing.

**Progressive Automation**: Organizations can begin with heavy human oversight and gradually reduce intervention as
confidence in agent behavior grows, all without modifying core workflow logic.

**Agent-Specific Disclaimers**: Agents can present customized disclaimers, terms of use, or data processing notices
before execution begins. Users must explicitly acknowledge these disclaimers, with their responses stored in the thread
context for audit purposes. This enables compliance with legal requirements, informed consent workflows, or
agent-specific usage policies while maintaining a complete record of user acknowledgments within the conversational
context.

## Operational Implications

The human-in-the-loop capability provides significant organizational benefits:

**Compliance Assurance**: Many regulatory frameworks require human oversight of automated decisions. The platform's
audit trail and explicit approval points satisfy these requirements without disrupting automation benefits.

**Risk Mitigation**: Organizations can deploy agents with confidence, knowing critical decisions require human
authorization. This reduces deployment risk while enabling automation of routine tasks.

**Gradual Adoption**: Teams can introduce automation incrementally, starting with full human oversight and progressively
reducing intervention as trust develops. The architecture supports this evolution without workflow redesign.

**Accountability**: Clear documentation of who approved what decisions, when, and based on what information ensures
organizational accountability even in highly automated processes.


# Agent Collaboration and Delegation

The Swiss AI-Hub enables sophisticated agent collaboration through a structured delegation pattern. This architectural
approach allows agents to invoke specialized capabilities from other agents, enabling hierarchical decomposition of
complex objectives while maintaining workflow independence and reusability.

## Collaboration Philosophy

Complex enterprise objectives often require diverse capabilities—natural language understanding, document analysis, data
retrieval, regulatory compliance checking, and domain-specific reasoning. Rather than building monolithic agents
attempting to master all capabilities, the platform enables composition of specialized agents, each excelling in its
specific domain.

This specialization approach mirrors successful software engineering practices: building focused, reusable components
that collaborate to achieve complex goals. The event-driven architecture ensures agents remain loosely coupled, enabling
independent development, testing, and evolution of specialized capabilities.

## Agent Delegation Pattern

The platform implements agent collaboration through a standardized delegation pattern:

1. A primary agent reaches a workflow step requiring specialized processing
2. The agent publishes an Agent-in-the-Loop Request Event (Control Event) specifying the target agent and required input
3. The messaging infrastructure routes this event to the appropriate agent instance
4. The delegated agent executes its workflow, potentially publishing Display Events to its own display context (visible
   or hidden based on configuration)
5. Upon completion, the delegated agent publishes a Stop Event
6. The messaging infrastructure wraps this Stop Event in an Agent-in-the-Loop Response Event
7. The primary agent consumes this response and continues its workflow

This pattern enables sophisticated agent compositions while maintaining workflow independence and reusability.

## Delegation Capabilities

The agent delegation architecture provides several key capabilities:

**Specialized Expertise**: Organizations can develop highly specialized agents for specific tasks—document
classification, entity extraction, compliance checking, data validation—and compose them into complex workflows. Each
agent maintains focus on its core competency while contributing to broader objectives.

**Display Context Control**: Primary agents can choose whether delegated agent activities appear to users. Passing the
display context makes delegation transparent—users see the collaborative process. Creating a new display context hides
delegation details—users see only the primary agent's output. This flexibility enables both transparent collaboration
and abstraction of implementation details.

**Workflow Isolation**: Delegated agents execute in complete isolation, unable to access the primary agent's internal
state. This isolation ensures reusability—the same specialized agent serves multiple primary agents without
cross-contamination. It also enables independent testing and validation of agent capabilities.

**Scalability**: Multiple instances of specialized agents can operate concurrently, with the messaging infrastructure
automatically distributing delegation requests. Organizations scale specific capabilities independently based on demand
patterns without modifying primary agent logic.

## Use Cases

Agent collaboration enables powerful enterprise scenarios:

**Multi-Stage Analysis**: A document processing agent delegates specialized tasks to document classification agents,
entity extraction agents, sentiment analysis agents, and compliance checking agents, orchestrating their contributions
into comprehensive document intelligence.

**Domain Decomposition**: Complex business processes decompose into specialized agents handling specific
domains—customer verification agents, credit check agents, fraud detection agents—coordinated by orchestration agents
implementing overall business logic.

**Capability Extension**: Organizations extend existing agent capabilities by developing specialized agents for new
domains. Existing orchestration logic automatically benefits from new capabilities without modification.

**A/B Testing**: Multiple implementations of specialized agents can coexist, with primary agents routing requests to
specific versions based on testing requirements or user cohorts. This enables controlled evaluation of new approaches
without disrupting production workflows.

## Architectural Implications

The delegation pattern provides significant architectural advantages:

**Reusability**: Specialized agents serve multiple primary agents and business processes. Investment in specialized
capabilities compounds across use cases rather than requiring reimplementation.

**Independent Evolution**: Specialized agents evolve independently as long as they maintain compatible input/output
event contracts. Organizations can improve specific capabilities without coordinating changes across all dependent
workflows.

**Clear Accountability**: Each agent maintains its own audit trail. When issues arise, organizations can trace problems
to specific agents and workflow steps, simplifying debugging and accountability.

**Composable Intelligence**: Complex AI capabilities emerge from composition of simple, validated components. This
composability enables rapid development of sophisticated workflows while maintaining quality and reliability.

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

1. **Agent Discovery**: How do primary agents discover available specialized agents? Is there a registry of
   capabilities? How are new agents made discoverable to existing workflows?

2. **Error Handling**: How are failures in delegated agents communicated back to primary agents? Can primary agents
   specify fallback strategies for delegation failures?

3. **Timeout Management**: What happens if a delegated agent fails to respond within expected timeframes? Can primary
   agents specify timeout policies?

4. **Nested Delegation**: Can delegated agents themselves delegate to other agents? Are there limits on delegation
   depth? How is the complete delegation chain tracked for audit purposes?

5. **Agent Selection**: When multiple implementations of specialized capabilities exist, how do primary agents select
   which to use? Can selection be dynamic based on runtime conditions?

6. **Performance Isolation**: How is resource contention handled when heavily-used specialized agents create
   bottlenecks? Are there prioritization mechanisms?

7. **Version Compatibility**: How does the system handle version mismatches when primary agents request capabilities
   from specialized agents with incompatible event contracts?
