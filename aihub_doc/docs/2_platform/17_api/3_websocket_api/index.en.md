---
title: WebSocket API
---

# WebSocket API

## Concept and Purpose

The WebSocket API, built on FastAPI, provides bidirectional, real-time communication channels for applications requiring
immediate feedback during AI operations. Unlike traditional request-response HTTP patterns where clients must repeatedly
poll for updates, WebSocket connections enable the platform to push events to clients instantly as they occur,
supporting modern interactive user experiences.

This capability addresses a fundamental challenge in AI applications: users need to observe what autonomous agents are
doing in real-time to build trust and maintain engagement. Without real-time visibility, long-running agent operations
appear as black boxes, creating uncertainty and reducing user confidence in AI-powered systems.

## Core Design Principles

### Real-Time Transparency and Trust

Modern AI applications require responsive interfaces that provide continuous feedback during agent execution. Users
expect to observe agent reasoning steps as they occur, receive progressive streaming of response content, monitor
real-time status changes, and receive immediate notification of issues or completion. This transparency transforms
opaque AI operations into observable, understandable processes.

The business impact of real-time visibility extends beyond user experience: it builds trust in AI systems by
demonstrating how agents reach conclusions, enables users to interrupt or redirect long-running operations before
wasting time, reduces perceived latency through progressive disclosure of results, and provides immediate feedback when
issues occur rather than silent failures.

### Event-Driven Architecture Bridge

The WebSocket API serves as a bridge between the platform's internal event-driven architecture and external client
applications. All platform operations—agent execution, process orchestration, message handling—generate structured
events that flow through the NATS messaging backbone. The WebSocket layer translates these internal events into
client-consumable messages, maintaining a consistent view of platform state across all connected applications.

This architecture ensures that multiple clients observing the same operations receive identical event streams,
supporting collaborative scenarios where teams work together with shared AI assistants. The event-sourced foundation
also enables reliable delivery: even if connections temporarily fail, clients can recover lost events through the event
history APIs.

### Security and Access Control

Despite providing real-time access to platform operations, the WebSocket API maintains strict security boundaries.
Connections are read-only from the client perspective—applications receive events but cannot publish through the
WebSocket channel. This design ensures that all actions requiring authorization validation flow through REST APIs where
proper security checks occur.

Event filtering based on user permissions ensures clients only receive events for resources they can access:
conversations they participate in, agents they can use, and processes they own or contribute to. This fine-grained
access control supports multi-tenant deployments where different users share platform infrastructure while maintaining
complete data isolation.

## Supported Capabilities

The API delivers real-time visibility across three primary operation types:

**Agent Execution Monitoring**: Applications receive continuous updates as agents execute tasks—reasoning steps, tool
invocations, response generation, and completion status. Streaming response chunks enable progressive display of agent
output, similar to typing indicators in messaging applications. This visibility helps users understand agent
capabilities and limitations, building appropriate trust levels for different task types.

**Conversation Updates**: Real-time notification of conversation state changes ensures users stay synchronized with
collaborative discussions. Applications learn immediately when new messages arrive, participants join or leave
conversations, or conversation metadata changes. This supports both human-human and human-AI collaboration patterns
where multiple parties contribute to problem-solving.

**Process State Tracking**: Complex multi-step business processes generate events as they progress through workflow
stages. Applications can display process status, highlight current steps, indicate completion progress, and notify users
when their input is required. This visibility enables proactive engagement rather than reactive notification—users see
processes advancing and can prepare responses before being explicitly prompted.

## Business Value

### Enhanced User Experience and Engagement

Real-time feedback transforms how users interact with AI systems. Rather than submitting requests and waiting with no
indication of progress, users observe continuous activity that maintains engagement and builds confidence. This
transparency is particularly valuable for complex agent operations that may take minutes or hours—users can monitor
progress, understand what the agent is currently doing, and make informed decisions about whether to wait or pursue
alternative approaches. Progressive response streaming in chat interfaces feels more natural and engaging than long
pauses followed by complete responses, and process status visibility helps users understand where they are in multi-step
workflows.

### Operational Efficiency and Cost Management

Real-time monitoring enables users to identify and abort unproductive operations early, avoiding wasted compute
resources and API costs. When agents pursue incorrect reasoning paths or encounter issues, immediate visibility allows
intervention before significant resources are consumed. This capability becomes increasingly important as organizations
scale AI deployments across multiple teams and use cases.

Administrators benefit from real-time platform monitoring—observing agent utilization patterns, identifying performance
bottlenecks, and receiving immediate notification of system issues. This operational visibility supports proactive
management rather than reactive troubleshooting.

### Collaborative AI Workflows

The WebSocket API's multi-client support enables team collaboration scenarios where multiple users work together with
shared AI assistants. All participants receive identical event streams, ensuring everyone observes the same agent
behaviors and conversation developments. This capability supports use cases like group decision-making with AI
assistance, training scenarios where experts guide AI interactions, and quality review processes where supervisors
monitor agent performance.

## Implementation Approach

Built on FastAPI's WebSocket capabilities, the API integrates directly with the platform's NATS JetStream event
backbone. Persistent connections handle thousands of concurrent clients per instance with minimal resource overhead.
Authentication occurs via bearer tokens validated against organizational identity providers, with automatic connection
termination for authentication failures. Event filtering applies hierarchical permission checks before delivery,
ensuring users receive only events for authorized resources. The architecture scales horizontally across API instances
using NATS-based event broadcasting, maintaining consistent event delivery regardless of which instance serves a
particular client connection. Typical event delivery latency remains below 50 milliseconds, supporting truly real-time
user experiences.
