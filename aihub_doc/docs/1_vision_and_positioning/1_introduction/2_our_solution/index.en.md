---
title: Our solution
---

# Our solution: Enterprise AI infrastructure as a product

The Swiss AI Hub is a complete, open-source AI platform that you deploy, own, and control. It's not a service you
subscribe to or a framework you build upon—it's production-ready infrastructure that becomes yours.

## Platform + SDK: The complete package

The Swiss AI Hub consists of two complementary parts:

**The platform** is your AI infrastructure. Apache 2.0 licensed, it includes everything needed to run AI in production:
LLM gateway, vector databases, data pipelines, authentication, monitoring, and user interfaces. Deploy it with
`docker compose up` and you have a working AI system.

**The SDK** is how you extend the platform. It provides the patterns, tools, and frameworks for building agents,
pipelines, and processes that automatically integrate with the platform. When you build with our SDK, your components
inherit all platform capabilities—they don't need custom deployment, monitoring, or user access because the platform
handles it.

## What you get out of the box

When you deploy the Swiss AI Hub, you immediately have:

::: details Infrastructure layer
- **Unified LLM gateway** through LiteLLM, connecting to any model provider
- **Vector databases** (Milvus) for semantic search and RAG
- **Document processing** with MinerU for PDFs, Office files, and more
- **Data pipelines** using Dagster for ingestion and processing
- **Message queuing** with NATS for event-driven architecture
- **Object storage** via SeaweedFS S3-compatible layer
- **Multiple databases** (PostgreSQL, FerretDB, ValKey) pre-configured
:::

::: details AI capabilities
- **Multi-provider LLM access** with automatic failover and cost tracking
- **Built-in RAG** with document parsing, chunking, and retrieval
- **Agent orchestration** for complex multi-step workflows
- **Process automation** coordinating between humans, AI, and systems
- **PII detection and anonymization** through Presidio
- **Embeddings and semantic search** with configurable models
:::

::: details Enterprise features  
- **SSO/OAuth integration** with your identity provider
- **Role-based access control** with granular permissions
- **Full audit trails** for compliance and debugging
- **Cost tracking and limits** per user, team, or model
- **API tokens** for programmatic access
- **Langfuse tracing** for complete observability
:::

::: details User interfaces
- **Modern chat interface** with voice, images, and documents
- **Process cockpit** for workflow monitoring and participation
- **Admin dashboard** for system management
- **Microsoft Teams and Slack bots** for where users already work
- **OpenAI-compatible API** for existing tool integration
:::

## How it solves the infrastructure problem

Remember those hard questions from before? Here's how the platform answers them:

::: tip "How do we deploy this?"
Everything runs in containers. One command starts the entire stack. Scale by adjusting container counts.
:::

::: tip "Where does our data stay?"
Wherever you deploy it. Run on-premise, in a Swiss data center, or your preferred cloud. Your infrastructure, your
control.
:::

::: tip "Can we track what the AI is doing?"
Every agent action is traced through Langfuse. Every API call is logged. Every decision is auditable.
:::

::: tip "How do we control costs?"
LiteLLM provides unified cost tracking across all models. Set limits by user, team, or globally.
:::

::: tip "What happens when it fails?"
Built-in error handling, automatic failover between models, and graceful degradation to human review.
:::

::: tip "How do users actually access it?"
Through the web UI, Teams, Slack, or API. Authentication handled by your existing identity provider.
:::

::: tip "Can we integrate it with our existing tools?"
OpenAI-compatible API for tool compatibility. Event-driven architecture for custom integrations. Webhook endpoints for
external systems.
:::

## Why open source changes everything

The Apache 2.0 license means you're not adopting a platform—you're acquiring one:

- **No vendor lock-in**: The code is yours. Run it anywhere, modify it as needed
- **No licensing fees**: Pay only for the infrastructure you run it on
- **Transparent operations**: Every component is inspectable and auditable
- **Community-driven**: Improvements from other organizations benefit everyone
- **Future-proof**: If we disappeared tomorrow, you'd still have a working platform

## The SDK advantage

While the platform solves infrastructure, the SDK solves development complexity. Building with our SDK means your agents
automatically:

- Stream real-time updates to users through WebSocket connections
- Appear in the chat interface without custom UI development
- Get traced without instrumentation code
- Handle authentication and authorization without security logic
- Store state in provided databases without connection management
- Process documents through existing pipelines without custom parsing

You write business logic. The platform handles everything else.

## A practical example

Here's what deploying your first AI capability looks like:

1. **Clone the repository** and configure environment variables
2. **Run `docker compose up`** to start the platform
3. **Access the web UI** and authenticate with your SSO
4. **Chat with pre-built agents** that work immediately
5. **Connect your data sources** through the admin interface
6. **Build custom agents** using SDK patterns when needed

No infrastructure setup. No service provisioning. No complex configurations. The platform is ready for production from
day one.

This is infrastructure as a product: complete, functional, and yours to build upon.
