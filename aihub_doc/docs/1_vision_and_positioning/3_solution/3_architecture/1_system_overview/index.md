---
title: System Overview
index: 1
---

# System Overview

The Swiss AI-Hub is an enterprise platform that enables organizations to deploy AI assistants and autonomous agents
securely within their own infrastructure. It provides the complete technology stack needed to integrate generative AI
into business processes while maintaining full control over data and compliance.

## Platform and Model: A Strategic Separation

The Swiss AI-Hub is architected with a clear separation between the **platform** that provides access to generative AI,
orchestrates AI workflows, and enables management, monitoring, and governance of AI usage—and the **large language
models (LLMs)** themselves that generate responses.

The reason for this separation is simple: The platform is your strategic asset, the models are a commodity. Models will
evolve rapidly over the coming years. New, more capable models will be released frequently. New providers will enter the
market. Existing providers will change pricing, terms of service, or discontinue models. The platform must remain stable
and unchanged regardless of the models you choose to use. This eliminates vendor lock-in and ensures you can always
adopt the best available AI technology. In addition, LLMs need extensive hardware resources to run. Hosting them
yourself is expensive and complex. However, many providers offer LLMs as a service, allowing you to pay only for what
you use. Since LLMs operate statelessly—they process prompts and return responses without storing data—you can safely
use third-party models without exposing your data.

The platform is designed to be deployed entirely within infrastructure you control—on-premise, in a Swiss private cloud,
or a hybrid combination. Your documents, data, and conversation history remain entirely under your jurisdiction.

---

## System Architecture

![System Overview](../../../../../media/architecture/system_overview/system-overview.png)

The Swiss AI Hub provides a complete, self-contained system that runs in your infrastructure without mandatory
dependencies on external services. This gives you control over where your data resides and how AI is integrated into
your operations.

The architecture prioritizes **modularity** as a key design principle. Each component can be adapted, replaced, or
upgraded independently as your needs evolve or new technologies emerge. This future-proofing approach ensures the
platform remains relevant even as the AI landscape changes rapidly.

### What is part of the platform?

The platform consists of the following main components:

#### API Gateway

The API Gateway serves as the single entry point for all interactions with the platform, handling security, access
control, and routing to internal services. It enables various ways to access and integrate AI capabilities:

External applications—such as custom portals, mobile apps, or business systems—can programmatically manage agents,
processes, users, and configurations, embedding AI functionality into existing workflows. Real-time chat interactions
are supported for conversational AI experiences in web or custom applications. The platform also integrates directly
with collaboration tools like Microsoft Teams or Slack, bringing AI assistance into the messaging platforms employees
already use daily.

The centralized gateway ensures consistent security policies across all access methods, handles rate limiting and
request validation, and simplifies integration for development teams.

#### User Interface

There are multiple ways how the platform lets users interact with the generative AI capabilities. The core UI component
is the Suite UI, a modern web application that provides access to all platform capabilities through an intuitive user
interface. On this UI, administrators can manage users, roles, permissions, monitor usage and costs, and configure the
platform. End users can participate in agentic processes and contribute to them to reach a successful conclusion. They
get notifications when their actions are needed and can analyze their past actions. Employees responsible for AI agents
can set up and run experiments to evaluate the quality of produced answers. Normal chat-based interactions are provided
through a dedicated Chat UI that is integrated into the Suite UI but can also be used standalone.

#### Agent Service

The Agent Service is the core component of the platform. It provides the capability to create, manage, and run AI agents
that can perform complex tasks autonomously. Agents are configured through structured workflows that define the steps an
agent takes to achieve a goal. The Agent Service executes these workflows, orchestrating calls to LLMs, retrieval of
information from knowledge bases, and interaction with users. It also manages the state of each agent, ensuring that it
can resume tasks after interruptions and maintain context over long-running processes.

#### Process Service

The Process Service orchestrates high-level business processes that involve collaboration between multiple agents, human
actors, and external programs. While individual agents handle specific tasks, the Process Service coordinates complex,
multi-step workflows where different parties contribute to achieving a larger business goal. It manages the lifecycle of
these processes, tracks their state, routes tasks to the appropriate participants, and ensures that all necessary steps
are completed in the correct sequence.

#### Data Pipelines

Agents need access to your organization's data to provide relevant answers and perform meaningful tasks. The Data
Pipelines component ingests, processes, and stores data from various sources—such as document repositories, databases,
or file shares. It automatically synchronizes these data sources and updates specialized search indexes that enable
agents to quickly find relevant information. This ensures that agents always work with current information when
answering questions or making decisions.

#### LLM Proxy

The LLM Proxy acts as an intermediary between the platform and the LLM. This is especially useful when the LLM is
provided as a service by a third party. With the use of this proxy, it is easy to switch between different LLM providers
or models without changing the platform or agents. Additionally, the proxy provides mechanisms for rate limiting to
optimize usage and control costs, as well as caching to improve performance and safeguarding your information to prevent
data leakage towards untrusted LLM providers.

#### Event System

At the core is a messaging system that allows all components to communicate with each other in a decoupled manner. This
is the cornerstone for scalability and reliability of the platform, as well as for the observability and transparency of
all operations.

### What is not part of the platform and needs to be provided?

#### LLM

As already mentioned, the platform is model agnostic. It does not come with a built-in LLM but needs to be connected to
one or multiple LLMs. This can be a third-party LLM provider like OpenAI, Anthropic, or Google connected through an API,
but also a self-hosted LLM that you run in your own infrastructure or your own LLM infrastructure in a Swiss cloud.

#### Identity Provider

Security is a top priority for the platform. Only authenticated and authorized users should be able to access the
platform. Therefore, the platform needs to be connected to an identity provider that manages users and their
authentication. This can be an open-source on-premise solution like Keycloak or, in most cases for enterprises, a
cloud-based identity provider like Azure Entra ID, Amazon Cognito, or Google Identity.
