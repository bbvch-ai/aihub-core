---
title: Service Catalog
index: 4
---

# Service Catalog

The Swiss AI Hub suite integrates multiple specialized services that address the complete lifecycle of AI-powered work.
This catalog describes each integrated service, its purpose, key capabilities, and how it contributes to the unified
suite experience.

## Agent Management Service

The Agent Management Service provides centralized visibility into all available AI agents, their configurations,
capabilities, and operational status.

**Purpose**: Enables users to discover, interact with, and monitor AI agents deployed in the organization. Rather than
requiring users to know which agents exist and how to access them, the service presents a browsable catalog of
authorized agents with descriptions, capability summaries, and access points.

**Key Capabilities**:

- **Agent Discovery**: Browse all agents the user is authorized to access, with visual cards showing agent names,
  descriptions, icons, and status indicators
- **Agent Inspection**: View detailed agent configurations including available tools, knowledge sources, model
  selections, and workflow definitions
- **Workflow Visualization**: Examine agent workflows as interactive diagrams showing decision logic, tool invocations,
  and integration points
- **Direct Interaction**: For conversational agents, initiate chat sessions directly from the agent management interface
- **Thread Overview**: View all conversation threads associated with a specific agent, monitoring its usage and
  reviewing interactions
- **Status Monitoring**: Real-time status indicators show whether agents are running, stopped, or experiencing errors

**Business Value**: The agent management service eliminates the "where do I find the right AI assistant" problem common
in AI deployments. Users can discover agents relevant to their tasks through browsing or search, understand agent
capabilities before engaging, and monitor agent performance without requiring technical expertise.

## Thread Management Service

The Thread Management Service provides comprehensive management of conversations between users and AI agents or
processes.

**Purpose**: Maintains conversation history, enables resumption of interrupted interactions, and provides visibility
into agent reasoning and decision-making across multi-turn dialogues.

**Key Capabilities**:

- **Thread Catalog**: View all conversation threads the user has participated in, with recent activity summaries and
  status indicators
- **Thread Continuation**: Resume conversations from where they left off, maintaining full context across sessions
- **Participant Management**: View which users and agents have participated in a thread, supporting collaborative AI
  interactions
- **Message History**: Complete conversation history with message timestamps, participant identification, and role
  indicators
- **Display Events**: Rich visualization of agent outputs, including thought processes, tool invocations, retrieval
  operations, and intermediate results
- **Thread Organization**: Search, filter, and organize threads by date, agent, participants, or custom labels

**Business Value**: The thread service ensures users never lose conversation context or have to re-explain requirements
to AI agents. Conversation histories support quality assurance, training, and compliance requirements by providing
complete audit trails of AI interactions.

## Knowledge Management Service

The Knowledge Management Service enables users to organize, upload, and maintain the knowledge bases that power
AI-driven retrieval and reasoning.

**Purpose**: Provides a transparent, controllable interface for managing enterprise knowledge that AI agents reference
during interactions, ensuring users understand what information agents can access and how it's represented.

**Key Capabilities**:

- **Knowledge Database Organization**: Hierarchical organization through databases (buckets) and namespaces (folders)
  that mirror organizational information structures
- **Document Upload**: Manual document upload with preview and validation before processing
- **Processing Transparency**: Complete visibility into how documents are parsed, chunked, and embedded for AI retrieval
- **Document Reconstruction**: View exactly how agents will see documents, enabling quality assurance and
  troubleshooting
- **Node Inspection**: Examine individual document chunks (nodes) to understand segmentation and metadata extraction
- **Processing Status**: Clear indicators distinguish uploaded-but-unprocessed documents from processed, AI-ready
  content
- **Multi-Language Support**: Interface elements and organizational labels available in German, English, French, and
  Italian

**Business Value**: The knowledge service eliminates the "black box" problem common in RAG (Retrieval-Augmented
Generation) systems. Users can verify that documents are correctly represented, understand what knowledge agents can
access, and troubleshoot retrieval issues without requiring technical AI expertise.

## Process Management Service

The Process Management Service visualizes and manages agentic processes—complex workflows involving multiple agents,
human decision points, and external system integrations.

**Purpose**: Provides operational visibility into automated business processes powered by AI agents, enabling
monitoring, intervention, and optimization of multi-step workflows.

**Key Capabilities**:

- **Process Catalog**: Browse all process definitions the user is authorized to view or execute
- **Process Visualization**: Interactive workflow diagrams showing process steps, decision logic, and integration points
- **Execution Monitoring**: Real-time monitoring of running processes with current step indication and progress tracking
- **Human Intervention**: For processes requiring human decisions, provide intervention points where users can review
  information and guide process execution
- **Execution History**: Complete audit trails of process executions with step-by-step logs and outcomes
- **Performance Analytics**: Aggregated process performance metrics showing completion rates, timing, and bottlenecks

**Business Value**: The process service enables organizations to implement sophisticated AI-powered automation while
maintaining visibility, control, and intervention capability. Rather than black-box automation, users understand and can
influence complex workflows even when AI agents perform most operations autonomously.

## Evaluation Service

The Evaluation Service supports systematic agent testing and quality assurance through dataset management, experiment
configuration, and results analysis.

**Purpose**: Enables data scientists, AI engineers, and quality assurance teams to validate agent performance, compare
configurations, and ensure quality standards before deployment.

**Key Capabilities**:

- **Dataset Management**: Upload and manage test datasets containing question-answer pairs or interaction scenarios
- **Experiment Configuration**: Define experiments testing agents against datasets with various configurations
- **Automated Execution**: Run experiments automatically, testing agents against complete datasets
- **Results Visualization**: Comprehensive result displays showing success rates, performance metrics, and failure
  analysis
- **Comparative Analysis**: Compare experiment results to understand how configuration changes affect performance
- **Quality Metrics**: Standard evaluation metrics appropriate for different agent types and use cases

**Business Value**: The evaluation service brings rigor and empirical validation to AI deployment. Rather than relying
on anecdotal assessments of agent performance, organizations can validate agents systematically, compare alternatives
objectively, and demonstrate quality standards to stakeholders.

## Role and User Management Services

The administrative services provide user provisioning, role assignment, permission configuration, and system monitoring
capabilities.

**Purpose**: Enables administrators to manage the AI platform, control access, and monitor system health without
requiring direct database access or configuration file editing.

**User Management Capabilities**:

- **User Provisioning**: Create, modify, and deactivate user accounts
- **Profile Management**: Manage user profiles including names, email addresses, and authentication credentials
- **Activity Monitoring**: View user activity logs and usage patterns
- **Access Auditing**: Review which resources users have accessed and when

**Role Management Capabilities**:

- **Role Definition**: Create and modify roles defining standard permission sets
- **Permission Assignment**: Assign fine-grained permissions to roles using the hierarchical permission system
- **User-Role Mapping**: Assign users to roles, automatically granting associated permissions
- **Role Analytics**: Understand which roles grant access to which capabilities

**Business Value**: Administrative services centralize platform governance, enabling security teams to manage access
control, compliance teams to generate audit reports, and operations teams to monitor platform health—all through
intuitive interfaces rather than technical configuration systems.

## Model Management Service

The Model Management Service provides visibility into available AI models, their configurations, and usage patterns.

**Purpose**: Enables administrators and users to understand which AI models power various capabilities, monitor model
usage, track costs, and optimize model selections for different use cases.

**Key Capabilities**:

- **Model Catalog**: Browse available AI models with capability descriptions and specifications
- **Usage Monitoring**: Track model usage across agents and services
- **Cost Tracking**: Monitor AI model costs with detailed breakdowns by model, agent, and time period
- **Performance Metrics**: View model performance characteristics including response times and error rates
- **Configuration Management**: Administrative control over model selections and configurations

**Business Value**: The model service enables organizations to optimize AI costs, ensure appropriate model selections
for different use cases, and maintain visibility into the AI technologies powering their platform deployment.

## OpenAI-Compatible API Service

While primarily accessible programmatically, the suite provides monitoring and management interfaces for the
OpenAI-compatible API service.

**Purpose**: Enables organizations to provide standardized, OpenAI-compatible API access to their AI Hub capabilities,
supporting integration with tools and applications that consume OpenAI APIs.

**Key Capabilities**:

- **API Token Management**: Generate and revoke API tokens for programmatic access
- **Usage Monitoring**: Track API usage by token, endpoint, and time period
- **Source Attribution**: For RAG-powered API responses, view source documents and retrieval contexts
- **Trace Inspection**: Examine execution traces for API-driven agent invocations

**Business Value**: The OpenAI-compatible API enables organizations to leverage AI Hub capabilities from custom
applications, integrate with existing tools expecting OpenAI APIs, and provide programmatic access while maintaining
visibility and control.

## Service Integration Philosophy

These services are not isolated applications but integrated components of a unified platform. Users moving between
services experience:

**Consistent Interaction Patterns**: Similar operations (creating resources, viewing lists, editing configurations)
behave similarly across services, reducing learning requirements.

**Cross-Service Navigation**: The suite recognizes relationships between services. Viewing an agent enables direct
navigation to its conversation threads or knowledge sources. Examining a thread shows which agent powered the
interaction. Inspecting a knowledge document reveals which agents can access it.

**Shared Infrastructure**: All services share authentication, authorization, internationalization, and observability
infrastructure. Users authenticate once, select their language once, and receive consistent error handling and feedback
mechanisms across all services.

**Unified Audit Trail**: Activities across all services contribute to a unified audit trail, enabling comprehensive
compliance reporting and security analysis without correlating logs from disparate systems.

## Deployment Flexibility

Organizations can deploy the complete service catalog or selective subsets based on their needs:

**Full Suite Deployment**: Comprehensive organizations deploy all services, providing employees with the complete range
of AI capabilities from agent interaction through evaluation and administration.

**Focused Deployments**: Organizations might deploy only agent and thread services for an employee-facing AI assistant
deployment, omitting evaluation and administrative services until operational needs expand.

**Phased Rollouts**: Initial deployments might provide core services (agents, threads, knowledge) with additional
services (processes, evaluation) introduced as organizational AI maturity increases.

The suite's dynamic service discovery ensures the interface automatically adapts to available services, requiring no
manual configuration as deployment scope evolves.

This comprehensive service catalog ensures that the Swiss AI Hub suite addresses the complete lifecycle of AI work, from
knowledge preparation and agent development through deployment, operation, monitoring, and continuous improvement.
