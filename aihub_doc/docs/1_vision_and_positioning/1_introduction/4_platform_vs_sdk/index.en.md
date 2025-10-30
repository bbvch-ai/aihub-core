---
title: Platform vs SDK
---

# Platform vs SDK: Understanding the dual architecture

The Swiss AI Hub separates platform from SDK deliberately. This separation isn't architectural complexity; it's
strategic design that gives you maximum flexibility in how you adopt, deploy, and extend the system.

## The platform: Your AI infrastructure

The platform is everything that runs when you execute `docker compose up`. It's the databases, message queues, LLM
gateway, vector stores, authentication system, user interfaces, and monitoring tools. Apache 2.0 licensed, it's yours to
deploy, modify, and operate however you need.

Think of the platform as your AI operating system. It handles:

- Where data is stored and how it's accessed
- Which models are available and how they're called
- Who can access what and how they're authenticated
- How components communicate and coordinate
- What users see and how they interact

The platform works immediately. Deploy it and you have a functional AI system with pre-built agents, chat interfaces,
and integrations. You can use it as-is without writing any code.

## The SDK: Your development framework

The SDK is how you build new capabilities that run on the platform. It provides base classes, decorators, patterns, and
tools that make your custom agents, pipelines, and processes automatically compatible with the platform infrastructure.

When you build with the SDK, you're writing business logic while the SDK handles platform integration:

```python
class MyAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your business logic here
        return AnalysisEvent(results=analysis)
```

This agent automatically:

- Streams updates through the platform's WebSocket connections
- Appears in the chat interface
- Gets traced in Phoenix
- Respects platform authentication
- Stores state in platform databases
- Handles errors according to platform patterns

## Why the separation matters

**Deployment flexibility**\
You can deploy the platform without any custom development code. Teams can start using AI immediately with pre-built
capabilities while developers work on custom agents. The platform provides value from day one.

**Development independence**\
SDK development happens outside the platform runtime. Developers work in their IDE with familiar tools, testing locally
before deploying. No need to understand the platform's internal architecture to build agents.

**Update isolation**\
Platform updates (new versions of Phoenix, LiteLLM, or the web UI) don't break your custom agents. SDK updates (new
decorators or patterns) don't require platform changes. Each layer evolves independently.

**Clear ownership boundaries**\
The platform is Apache 2.0, so you own your deployment completely. The SDK has different licensing (EUPL 1.2 for
community version), creating clear boundaries between infrastructure you own and development tools you license.

## How they work together

The magic happens through well-defined interfaces:

**Event contracts**\
The SDK defines event types that the platform understands. When your agent emits a `UserMessageEvent`, the platform
knows how to route it, store it, and display it. The contract is the event schema, not the implementation.

**Discovery protocols**\
Agents built with the SDK announce themselves to the platform through NATS messages. The platform discovers available
agents dynamically, no configuration required.

**Resource injection**\
The SDK knows about platform resources (databases, LLM clients, storage). When your agent needs them, the platform
injects configured instances automatically.

**Standardized patterns**\
The SDK enforces patterns the platform expects. Workflow steps, context management, error handling all follow
conventions the platform can monitor and manage.

## A practical comparison

Consider building a document analysis agent:

**Without the SDK:**

- Write custom API endpoints
- Implement WebSocket streaming
- Add authentication checks
- Configure database connections
- Instrument tracing manually
- Build a user interface
- Handle error states
- Manage deployment

**With the SDK:**

```python
class DocumentAnalyzer(Agent):
    @step()
    async def analyze(self, doc: Document) -> Analysis:
        return analyze_document(doc)
```

The SDK isn't hiding complexity, it's eliminating redundancy. The platform already knows how to stream, authenticate,
store, trace, display, and deploy. The SDK provides the patterns to tap into these capabilities.

## Licensing and business model

The architectural split enables a sustainable business model:

**Platform (Apache 2.0)**: Take it, deploy it, modify it, own it. No fees, no restrictions. This removes adoption
barriers and vendor lock-in concerns.

**SDK (Dual licensed)**:

- **Community edition (EUPL 1.2)**: Free to use but modifications must be shared back
- **Commercial edition**: Proprietary development without sharing requirements

This model means:

- Organizations can adopt the platform risk-free
- Basic customization using platform features remains free
- Advanced SDK development contributes back to the community or requires commercial licensing
- Everyone benefits from platform improvements

## When you need each part

**Platform only:** You want secure AI access with pre-built capabilities. Perfect for organizations starting their AI
journey or teams that need standard agents.

**Platform + SDK:** You need custom agents, specialized pipelines, or complex process automation. The SDK becomes
essential when pre-built capabilities aren't enough.

**SDK for migration:** You have existing agents built with other frameworks. The SDK provides migration paths to make
them platform-native while preserving your investment in business logic.

The platform runs your AI infrastructure. The SDK builds your competitive advantage. Together, they provide a complete
ecosystem where infrastructure is solved and development is streamlined, letting you focus on what makes your AI
applications unique.
