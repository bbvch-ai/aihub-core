---
title: Agent Interaction REST API
---

# Agent Interaction REST API

## Concept and Purpose

The Agent Interaction REST API, built on FastAPI, serves as the platform-native HTTP interface for accessing the full
capabilities of the Swiss AI Hub. While the OpenAI-Compatible API provides standardized LLM access for migration
scenarios, this API exposes the complete agent orchestration, process automation, and platform management functionality
unique to the Swiss AI Hub.

This API is designed for organizations building native applications that leverage the platform's advanced capabilities:
multi-agent collaboration, long-running business processes, comprehensive observability, and sophisticated knowledge
management. It provides programmatic control over the entire platform lifecycle, from agent discovery and configuration
through process execution and quality evaluation.

## Core Design Principles

### Platform-Native Capabilities

The API provides direct access to capabilities that distinguish the Swiss AI Hub from simple LLM proxies: stateful
conversations involving multiple specialized agents, orchestrated business processes that coordinate AI with human
decision points, comprehensive event history for audit and debugging, and centralized knowledge management for
retrieval-augmented generation. These capabilities enable organizations to build sophisticated AI-powered workflows
rather than simple question-answer interactions.

Applications can discover available agents dynamically, configure multi-agent teams for specific tasks, initiate complex
business processes, and monitor execution through detailed event streams. This flexibility supports both interactive
applications requiring immediate responses and batch processes running autonomously over extended periods.

### Event-Driven Integration

The API serves as an HTTP gateway to the platform's event-driven core, translating synchronous HTTP requests into
asynchronous platform events. This architecture provides several advantages: requests return immediately while agents
process tasks in the background, distributed agent services scale independently without API changes, comprehensive event
streams enable real-time monitoring and historical analysis, and operations remain observable and debuggable through
structured event logs.

This design bridges traditional request-response expectations from web and mobile applications with the asynchronous,
distributed nature of autonomous agent operations. Applications receive immediate acknowledgment of requests while the
platform orchestrates complex, potentially long-running agent workflows. .

## Business Value

### Comprehensive Platform Control

Unlike simple LLM APIs that provide basic model access, this interface exposes the full platform for organizations
building sophisticated AI solutions. Development teams gain programmatic control over agent configuration, process
orchestration, and knowledge management without requiring direct infrastructure access. This enables application-level
automation while maintaining security boundaries and audit trails.

### Operational Visibility and Compliance

The extensive observability capabilities address critical enterprise requirements for transparency and compliance.
Organizations can demonstrate to auditors exactly how AI systems reached specific decisions, reconstruct conversations
for dispute resolution, identify performance degradation before it impacts users, and monitor costs by tracking agent
execution and resource utilization across teams and projects.

### Scalable Multi-Agent Architectures

The API's support for multi-agent collaboration enables organizations to build scalable AI solutions by composing
specialized agents. Rather than training single, monolithic models for diverse tasks, organizations can develop focused
agents for specific domains and orchestrate them through this interface. This modular approach reduces individual agent
complexity, enables independent agent improvement cycles, and supports reuse of agents across different business
processes.

## Implementation Approach

Built on FastAPI, the API operates as part of the main platform service with stateless design enabling horizontal
scaling. Authentication integrates with organizational identity providers via OAuth2, and hierarchical permissions
control resource access at runtime. Request handling translates HTTP operations into NATS events that flow through the
platform's event system, maintaining clean separation between the synchronous HTTP interface and asynchronous agent
execution. All operations are instrumented via OpenTelemetry for distributed tracing, and structured logging captures
contextual information for comprehensive observability across HTTP and event boundaries.
