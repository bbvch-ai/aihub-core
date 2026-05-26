---
title: Building Agents
---

# Building Agents with the Swiss AI Hub SDK

An agent in the Swiss AI Hub is a workflow defined by a series of steps that process events. Agents can interact with
users, call external services, and coordinate with other agents to perform complex tasks.

This documentation guides you through the architecture, patterns, and best practices for building robust and scalable
agents.

::: warning
Before you begin, please complete the [Development Environment Setup](../1_quick_start/1_dev_environment_setup/) and
build [Your First Agent](../1_quick_start/3_your_first_agent/).
:::

## What's Covered

This guide is structured to build your knowledge progressively:

01. [**Agent Fundamentals**](./1_agent_fundamentals/) - The core architecture, including events, steps, and
    configuration.
02. [**Core Patterns**](./2_core_patterns/) - Essential workflow patterns like conditional logic, loops, and state
    management.
03. [**Human in the Loop**](./3_human_in_the_loop/) - Building interactive workflows that require human approval or
    input.
04. [**Multi-Agent Systems**](./4_multi_agent_systems/) - Coordinating multiple agents to solve complex problems.
05. [**Memory**](./5_memory/) - Adding persistent memory to your agents for user preferences and organizational
    knowledge.
06. [**Testing and Debugging**](./6_testing_and_debugging/) - Best practices for ensuring your agent is reliable and
    correct.
07. [**Production Deployment**](./7_production_deployment/) - Guidelines for packaging and deploying your agent.
08. [**Agent Observation**](./8_agent_observation/) - Monitoring your agent's behavior and performance with integrated
    tracing.
09. [**Configurable Agent Forms**](./8_configurable_agents/) - Making agent configuration editable through the Admin UI
    using the Form Duality Pattern.
10. [**Execution Model**](./9_execution_model/) - How the dispatcher executes steps, synchronization primitives,
    anti-patterns, and troubleshooting.
11. [**Events Reference**](./10_events_reference/) - Complete event hierarchy, choosing the right base event, and
    available events catalog.
12. [**Using MCP Tools**](./11_using_mcp_tools/) - Connecting agents to external MCP servers to call their tools.

## Key Principles of the SDK

The SDK is designed around a few core principles to make development intuitive and scalable:

- **Event-Driven by Nature**: Agents react to a stream of events. This asynchronous, message-based architecture makes
  workflows dynamic and resilient.
- **Declarative Workflows**: You define *what* each step does using the `@step` decorator. The SDK automatically handles
  the *how* of routing events and wiring your steps together.
- **Managed State**: Handle conversation memory and run-time data effortlessly with injectable `RunContext` and
  `ThreadContext` objects, backed by a distributed store.
- **Built for Production**: With strongly-typed configuration, a dedicated testing framework, and built-in
  observability.

## The Development Workflow

Building a high-quality agent typically follows these four stages:

::: tip 
A core design principle is that each agent should do one thing well. Complex problems are best solved by coordinating
multiple specialized agents.
:::

1. **Design Your Workflow**: Outline your agent's purpose, the events it will handle, and the sequence of steps it will
   take to achieve its goal.
2. **Implement the Core Logic**: Write your `Agent` class, define its strongly-typed `AgentConfig`, and implement the
   `@step` methods that transform events.
3. **Test and Debug**: Use the `AgentTestRunner` for unit testing and a tracing tool like Langfuse to visually debug the
   flow of events through your agent.
4. **Deploy and Monitor**: Package your agent and deploy it to the Swiss AI Hub, where its performance and behavior can
   be monitored in real-time.

## Next Steps

Start with [agent fundamentals](./1_agent_fundamentals/) to understand the core architecture, then explore the specific
patterns and techniques in the following sections.
