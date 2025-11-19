---
title: Multi-tenancy
---

# Multi-tenancy

Multi-tenancy lets you create organizational boundaries within a single platform instance. Each tenant represents a
workspace with its own users, roles, and access to agents and services.

The platform's multi-tenant model gives you flexibility to structure access in ways that match your organization's
needs, from simple departmental separation to complex hierarchical configurations.

## Three resource types

The platform provides three types of resources:

**Services** are platform capabilities like user management, knowledge base management, agent evaluation, and system
configuration. Most users don't need direct service access.

**Agents** are AI assistants that perform specific tasks. Users interact with agents through chat or agents execute
tasks autonomously. Agents access data and perform actions based on how they're configured.

**Processes** orchestrate workflows involving multiple agents, human approvals, and external systems. Processes
coordinate complex business operations.

## The agent independence principle

::: info The Most Important Concept
**Agents operate independently of user and tenant permissions.**

When a user chats with an agent, the agent doesn't inherit that user's access restrictions. The agent accesses data
based on its own configuration. This has profound implications for how you structure tenants and control data access.
:::

Why design it this way? Agents often need to:

- Access data from multiple sources that individual users can't see
- Run autonomously without any user interaction
- Participate in group conversations with users who have different permissions
- Execute scheduled tasks regardless of who's online

You control data access by controlling which users can interact with which agents. The agent's configuration determines
what data it can access. Your tenant design determines who can use that agent.

## Common patterns

Most organizations use a three-tier structure:

**System administrator tier**: A tenant for platform administrators who develop agents, deploy pipelines, and maintain
the infrastructure. These users see everything and can modify system-level configurations.

**Management tier**: A tenant for people who administer the platform for business users. They create tenants, assign
users to tenants, configure agent instances, and monitor usage. They can't deploy new agent code or modify
infrastructure.

**Department tiers**: One tenant per department, business unit, or customer. Users work with agents relevant to their
department. They can't see agents for other departments or access administrative functions.

This structure separates technical operations, business administration, and day-to-day use.

## Flexibility and responsibility

The system is intentionally flexible. You can create permissive configurations where agents access all data, or
restrictive setups where agents have narrowly scoped access to specific information.

This flexibility means you're responsible for:

- Designing a tenant structure that matches your security requirements
- Configuring agents with appropriate data access
- Assigning users to the right tenants with appropriate roles
- Regularly reviewing who can access which agents

The platform enforces the boundaries you define. It won't stop you from creating an agent that accesses everything and
giving that agent to everyone. That's a valid configuration if it matches your needs - but you must understand the
implications.
