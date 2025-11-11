---
title: User Interface
---

# The Platform interface

The Swiss AI Hub interface is designed as an integrated suite, not a collection of separate tools. This approach mirrors
familiar productivity software like Microsoft Office or Google Workspace, where different applications for different
tasks coexist within a single, unified environment.

Users authenticate once to access a cohesive suite of AI services. A shared navigation framework and a consistent design
language across all capabilities reduce the learning curve and eliminate the workflow disruption common in fragmented
platforms. This design allows users to focus on their work, not on learning how to navigate different tools.

## The service catalog

The interface provides a set of specialized services that cover the entire lifecycle of enterprise AI, from knowledge
management and agent development to process automation and evaluation.

### Agent management

This is the central hub for discovering, interacting with, and monitoring all AI agents deployed in your organization.
It provides a browsable catalog of available agents, allowing users to understand their capabilities before engaging
with them.

::: details Key capabilities
- **Agent discovery**: Browse a visual catalog of all agents you are authorized to access, with descriptions and status
  indicators.
- **Workflow visualization**: Examine agent workflows as interactive diagrams showing their decision logic and tool
  integrations.
- **Direct interaction**: Initiate chat sessions directly from the agent's profile.
- **Thread overview**: View all conversation threads associated with a specific agent to review its interaction history.
- **Status monitoring**: See real-time indicators showing whether agents are running, stopped, or experiencing errors.
:::

### Thread management

This service provides a complete history of all conversations between users and AI agents. It allows you to resume past
interactions, review an agent's reasoning, and maintain a full audit trail of AI-powered dialogues.

::: details Key capabilities
- **Thread catalog**: View, search, and filter all your past conversation threads.
- **Conversation history**: Access the complete message history for any thread, with timestamps and participant details.
- **Resume conversations**: Continue any past interaction from where you left off, with full context preserved.
- **Display events**: See a rich visualization of an agent's internal operations during a conversation, including its
  thought process, tool use, and data retrieval steps.
:::

### Knowledge management

This service gives you transparent control over the knowledge bases that your AI agents use for Retrieval-Augmented
Generation (RAG). You can manage the documents and data that provide context for your agents' responses.

::: details Key capabilities
- **Organize knowledge**: Structure information in databases and namespaces that mirror your organization's data
  structures.
- **Document upload**: Manually upload documents with previews and validation.
- **Processing transparency**: See exactly how documents are parsed, chunked, and prepared for AI retrieval.
- **Document reconstruction**: View the final, processed version of a document to understand how an agent sees it.
:::

### Process management

This service is for visualizing and managing complex, multi-step workflows that involve AI agents, human decision
points, and integrations with external systems. It provides operational visibility into sophisticated AI-powered
automation.

::: details Key capabilities
- **Process visualization**: View interactive diagrams of your automated business processes.
- **Execution monitoring**: Track the real-time progress of running processes, seeing which step is currently active.
- **Human intervention**: Participate in workflows that require human approval or review at designated steps.
- **Execution history**: Review a complete audit trail of every process run, with step-by-step logs and outcomes.
:::

### Evaluation service

This service brings systematic testing and quality assurance to your AI agents. It allows you to validate agent
performance against predefined datasets to ensure quality and accuracy before and after deployment.

::: details Key capabilities
- **Dataset management**: Upload and manage test datasets with question-answer pairs or other evaluation criteria.
- **Experiment configuration**: Define and run automated experiments that test agents against your datasets.
- **Results analysis**: View comprehensive results showing success rates, performance metrics, and failure analysis.
- **Comparative analysis**: Compare the results of different experiments to measure the impact of configuration changes.
:::

### Administrative services

A set of services enables administrators to manage users, roles, and permissions through an intuitive interface. This
centralizes platform governance for security, compliance, and operational teams.

::: details Key capabilities
- **User management**: Provision, modify, and deactivate user accounts.
- **Role management**: Define roles with specific permission sets (e.g., "Agent Developer," "Knowledge Manager").
- **Permission assignment**: Assign users to roles to grant them access to specific services and capabilities.
- **Audit trails**: Review user activity logs and access patterns across the entire platform.
:::

## A unified experience

These services are not isolated applications. The suite is designed to create a seamless workflow where context flows
between them.

- **Persistent navigation**: A permanent sidebar provides one-click access to any authorized service from anywhere in
  the application. You never need to return to a "home" screen to switch tasks.
- **Consistent design**: All services share the same visual design and interaction patterns. Forms, tables, and buttons
  behave predictably everywhere, so learning one service helps you understand them all.
- **Cross-service context**: The interface understands the relationships between objects. When viewing an agent, you can
  navigate directly to its knowledge sources or its conversation threads. When reviewing a thread, you can see which
  agent participated.
- **Intelligent interface**: The interface uses modern web patterns to feel fast and responsive. Skeleton screens show
  you what content is loading, and real-time updates are pushed via WebSockets for live agent execution and process
  monitoring.

This integrated approach ensures that the platform is not just a collection of powerful features, but a productive and
coherent environment for all users.
