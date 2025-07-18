---
title: "High-Level Architecture"
index: 2
---

# :building_construction: Swiss AI-Hub Architecture

::: tip Architecture Overview
The Swiss AI-Hub is built as a comprehensive, event-driven platform that seamlessly integrates AI agents, business processes, and enterprise infrastructure. This architecture enables the creation of transparent, auditable, and sovereign AI solutions that scale from simple assistants to complex autonomous systems.
:::

## :mountain: Platform vs. Library Approach

The Swiss AI-Hub follows a **platform-first architecture** rather than a library-based approach:

- **Libraries** help you solve specific problems but leave you to build the infrastructure
- **Platforms** provide the complete environment to solve problems at scale, reliably, and sustainably

Our architecture embodies this philosophy by providing a complete, production-ready ecosystem where developers can focus on creating business value while the platform handles security, scalability, and infrastructure.

## :building_construction: Component Architecture Overview

The Swiss AI-Hub is architected as a symphony of interconnected components, each playing a vital role in creating intelligent, collaborative workflows. Rather than a monolithic system, we've designed a modular ecosystem where each layer serves a specific purpose while harmoniously working together.


::: tip Architecture Philosophy
Our architecture follows the principle of **separation of concerns** with **clear interfaces** between components. This design enables independent development, testing, and scaling of each layer while maintaining system cohesion.
:::

## :globe_with_meridians: The User Experience Layer

These components form the interface through which users interact with the AI-Hub, whether through web applications, APIs, or collaboration platforms.

::: details AI-Hub API Layer - The Gateway to Intelligence
**Your Bridge to AI Capabilities**

The API layer serves as the primary interface for web and bot clients, translating HTTP requests into NATS events and streaming responses back to users in real-time.

**What makes it special:**
- **Protocol Translation**: Seamlessly converts REST and WebSocket requests into NATS events that agents and processes understand
- **Real-time Streaming**: WebSocket connections stream agent workflow steps back to users as they happen
- **Discovery Orchestration**: Sends discovery events to find available agents and processes, enabling dynamic system composition
- **Enterprise-Grade Security**: Hierarchical permissions ensure the right users access the right resources at the right time
- **Developer-Friendly**: Auto-generated OpenAPI schemas and comprehensive documentation make integration seamless

**Behind the scenes:**
The API doesn't orchestrate the system—it translates between protocols. When you ask a question, the API sends a NATS event to the appropriate agent, then subscribes to the response stream, forwarding each step back to your browser via WebSocket. This creates a responsive, real-time experience while keeping the API layer lightweight and focused.
:::

::: details AI-Hub Web Interface - The Command Center
**Where Intelligence Meets Intuition**

The web interface provides multiple interaction modes: chat interfaces for direct agent communication and process dashboards for monitoring and participating in complex workflows.

**What makes it special:**
- **Dual Interface Modes**: Chat mode for direct agent interaction, Process mode for workflow participation and monitoring
- **Real-time Everything**: Live updates show agent workflow steps, process progress, and system health as they happen
- **Dynamic Process UIs**: Automatically generates forms and interfaces based on what each process step needs from humans
- **Complete Observability**: Inspect every step an agent took, what data it used, and how it reached its conclusions
- **Multi-Cultural**: Native support for German, French, Italian, and English ensures global accessibility

**Behind the scenes:**
Built on Nuxt 3 and Vue 3, the interface receives real-time updates via WebSocket connections to the API. When agents work or processes execute, each step streams to the browser immediately. The system auto-generates TypeScript clients from API schemas, while Pinia-Colada manages state and caching seamlessly.
:::

::: details AI-Hub Bot Integration - The Conversational Bridge
**AI in Your Workspace**

The bot layer brings AI capabilities directly into the collaboration tools your team already uses, eliminating context switching and friction.

**What makes it special:**
- **Native Integration**: Works seamlessly within Teams, Slack, and other platforms as if it were built specifically for each
- **Context Awareness**: Maintains conversation history and understands threading, making interactions feel natural
- **Streaming Responses**: See AI thinking in real-time with progressive response building
- **Human-AI Collaboration**: Enables sophisticated workflows where AI agents can request human input when needed

**Behind the scenes:**
The bot system uses Microsoft Bot Framework for multi-channel support, with specialized adapters for each platform. Conversation state is persisted with configurable TTL, and the system handles the complexity of different messaging formats automatically.
:::

## :brain: The Intelligence Layer

These components form the cognitive core of the AI-Hub, providing the reasoning, automation, and data processing capabilities that make the system truly intelligent.

::: details AI-Hub Agent System - The AI Workforce
**Intelligent Agents That Actually Work**

The agent system creates autonomous entities that can reason, plan, and execute complex tasks with human-level understanding and reliability.

**What makes it special:**
- **Transparent Intelligence**: Every agent decision is traceable and auditable, building trust through transparency
- **Multi-Provider Flexibility**: Seamlessly works with OpenAI, Azure, Google, and other LLM providers, with automatic fallback strategies
- **Knowledge Integration**: Agents can access and reason over your organization's specific knowledge through advanced RAG capabilities
- **Tool Integration**: Agents can interact with external systems, databases, and APIs to accomplish real tasks

**Behind the scenes:**
Agents are built using workflow-based execution that makes every step visible and debuggable. The system provides comprehensive observability through Phoenix tracing, making it easy to understand how agents reach their conclusions.
:::

::: details AI-Hub Process Orchestration - The Collaboration Engine
**Where Human and AI Intelligence Converge**

The process layer orchestrates complex workflows that involve multiple agents, human participants, and external systems working together toward common goals.

**What makes it special:**
- **Delegation-Based Design**: Processes don't execute work themselves—they intelligently delegate to the most appropriate entity
- **Human-AI Collaboration**: Seamlessly integrates human decision-making with AI automation
- **Visual Workflows**: Complex processes are represented as clear, understandable flowcharts
- **Flexible Patterns**: Supports everything from simple approval workflows to complex multi-stage business processes

**Behind the scenes:**
The process engine uses event-driven architecture with NATS messaging to coordinate between entities. The system provides rich testing frameworks with BDD support, making complex workflows easy to validate and debug.
:::

::: details AI-Hub Data Pipelines - The Knowledge Foundation
**Turning Information into Intelligence**

The pipeline layer operates independently, watching the data lake for changes and automatically transforming documents into AI-ready knowledge that agents can access.

**What makes it special:**
- **Fully Autonomous**: Watches data lake changes and processes documents without any external coordination
- **Smart Document Understanding**: Handles PDFs, Word documents, PowerPoint presentations, and more with intelligent parsing
- **Vector Intelligence**: Converts text into high-dimensional embeddings that agents use for semantic search and reasoning
- **Zero-Coordination Architecture**: Operates independently—agents and API access the results, but pipelines run on their own schedule

**Behind the scenes:**
Built on Dagster with observable assets that react to data lake changes. When the API uploads a file or external systems add documents, pipelines automatically detect and process them. The results flow into vector stores and document databases where agents can access them. No coordination needed—pure reactive processing.
:::

## :electric_plug: The Event-Driven Nervous System

The true power of the AI-Hub lies not in how components connect, but in how they **don't** connect. This is an event-driven, discovery-based architecture where NATS serves as the nervous system, carrying signals between loosely coupled components.

::: tip The Discovery Revolution
Agents and processes don't need to know about each other or the API. They simply announce their presence through NATS events, creating a self-organizing system that scales automatically.
:::

### :zap: NATS - The Nervous System

NATS is the electrical impulse system that makes everything work:


**🔍 Discovery Events**: When the API needs to find agents, it sends a discovery event into NATS. Available agents respond, creating a dynamic registry.

**🎯 Work Delegation**: The API translates user requests into NATS events that the right agents receive automatically.

**📡 Workflow Streaming**: Every agent workflow step publishes to NATS, creating a real-time stream of intelligence.

**🔄 Process Orchestration**: Processes use NATS to coordinate between agents, humans, and external programs.

**⚖️ Automatic Load Balancing**: Deploy multiple instances of the same agent, and NATS automatically distributes work between them.

## :arrows_counterclockwise: Intelligence in Action: Two Core Patterns

The AI-Hub supports two fundamental interaction patterns that showcase the power of the event-driven architecture.

### 💬 Pattern 1: Direct User-Agent Communication

Let's trace a real user interaction from start to finish:

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant A as API
    participant N as NATS
    participant Ag as Agent
    participant V as Vector Store
    participant P as Pipeline
    participant D as Data Lake
    
    Note over P,D: 1. Knowledge Preparation
    P-->>D: Watch for changes
    D->>P: New document detected
    P->>V: Process & store embeddings
    
    Note over U,A: 2-4. User Interaction
    U->>W: Ask question
    W->>A: WebSocket request
    A->>N: Discovery event
    N->>Ag: Who can handle this?
    Ag->>N: I can handle it
    A->>N: Delegate work
    N->>Ag: User question
    
    Note over Ag,V: 5-6. Agent Processing
    Ag->>V: Query knowledge
    V-->>Ag: Relevant data
    Ag->>N: Workflow step 1
    N->>A: Workflow step 1
    A->>W: Stream step 1
    Ag->>N: Workflow step 2
    N->>A: Workflow step 2
    A->>W: Stream step 2
    Ag->>N: Final response
    N->>A: Final response
    A->>W: Stream final response
    W->>U: Real-time updates
```

**📁 Step 1: Knowledge Preparation**
An admin uploads a document to the data lake. The Data Pipeline automatically detects this change, processes the document with AI, and ingests it into the vector store. No coordination needed—pure reactive processing.

**💬 Step 2: User Question**
A user types a question in the web interface. The browser sends this to the API via WebSocket.

**🎯 Step 3: Agent Discovery**
The API sends a discovery event into NATS: "Who can handle this type of question?" Available agents respond with their capabilities.

**📨 Step 4: Work Delegation**
The API selects the best agent and sends a NATS event with the user's question. The agent receives and begins processing.

**🔍 Step 5: Knowledge Retrieval**
The agent queries the vector store for relevant information, finding the document that was processed earlier.

**⚡ Step 6: Real-time Streaming**
As the agent works through its workflow—reasoning, retrieving, generating—each step is published to NATS. The API subscribes to these events and streams them to the user's browser via WebSocket.

**🎉 Step 7: Live Observability**
The user sees the agent's thinking process in real-time. Later, they can navigate to the observability interface to inspect every step, every piece of data used, and how the agent reached its conclusion.

### 🔄 Pattern 2: Agentic Process Orchestration

Now let's see how the AI-Hub orchestrates complex workflows involving multiple entities. Here's a CV reviewing process triggered by incoming emails:

```mermaid
sequenceDiagram
    participant E as Email Program
    participant API as API
    participant N as NATS
    participant P as Agentic Process
    participant A as CV Agent
    participant W as Web UI
    participant H as HR Person
    
    Note over E,API: Process Trigger
    E->>API: POST /process/cv-review (webhook)
    API->>N: Email received event
    N->>P: New email at talent@company.ch
    P->>N: Process started event
    N->>API: Process started
    API->>W: Live process update
    
    Note over P,A: Step 1: Agent Analysis
    P->>N: CV review request
    N->>A: Analyze CV from email
    A->>N: Analysis step 1
    N->>API: Stream agent work
    API->>W: Live agent progress
    A->>N: Analysis step 2
    N->>API: Stream agent work
    API->>W: Live agent progress
    A->>N: CV assessment complete
    N->>P: CV assessment result
    P->>N: Agent step completed
    N->>API: Process step update
    API->>W: Step 1 completed
    
    Note over P,H: Step 2: Human Decision
    P->>N: HR review request
    N->>API: Human work needed
    API->>W: Generate dynamic form
    W->>H: Notification: Action required
    H->>W: Navigate to process
    W->>H: Show: Email + Agent assessment + Decision form
    H->>W: Submit decision (Accept/Reject)
    W->>API: Form submission
    API->>N: Human decision
    N->>P: Human work completed
    P->>N: Process completed
    N->>API: Final process update
    API->>W: Process finished
```

**📧 Step 1: Email Trigger**
An email arrives at talent@company.ch. The email program sends a POST request to the API's dynamically generated webhook endpoint `/process/cv-review`. The API translates this HTTP request into a NATS event that triggers the agentic process.

**🤖 Step 2: Agent Analysis**
The process transforms the email into a CV review request and delegates it to the CV Agent via NATS. The agent analyzes the CV, with each workflow step streaming live through NATS to the API, then to the Web UI.

**📊 Step 3: Process Transformation**
The process receives the agent's assessment via NATS and transforms it into a human-readable format with a decision form.

**👥 Step 4: Human Review**
The HR person receives a notification in the AI-Hub interface. They navigate to the process view and see:
- **Step 1**: The original email from the candidate
- **Step 2**: The agent's technical assessment with reasoning  
- **Step 3**: A dynamic form asking for Accept/Reject decision

**✅ Step 5: Decision & Completion**
The HR person submits their decision through the Web UI. The API receives this form submission and translates it into a NATS event for the process orchestrator. The process marks the workflow as complete, and all participants can see the final result.

**👁️ Live Observability Throughout**
At every moment, the Web UI shows live updates:
- Process progress and current step
- Agent workflow steps as they happen
- Human participants and their required actions
- Complete audit trail of all decisions and reasoning

::: details Process-Driven Workflows - The Next Level
**Taking Humans Out of the Loop**

For complex workflows, Agentic Processes orchestrate everything:

**🎯 Process Definition**: Define who does what—humans provide approvals, agents do analysis, external programs handle integrations.

**⚡ Automatic Triggers**: Processes can be triggered by time, events, or other processes. No human intervention needed.

**🔄 Dynamic Coordination**: The process sends NATS events to coordinate between all participants—agents, humans, and external programs.

**📊 Live Monitoring**: The web interface transforms into a process dashboard, showing live progress and generating dynamic forms for human participants.

**🎭 Complete Flexibility**: Processes are just another type of NATS participant—they can be discovered, scaled, and coordinated just like agents.
:::

::: details The Discovery-Based Architecture
**Why This Changes Everything**

This architecture provides unprecedented flexibility:

**🔄 Hot Deployment**: Deploy new agents without system downtime. They announce themselves and immediately start receiving work.

**⚖️ Automatic Scaling**: Deploy multiple instances of popular agents. NATS automatically load balances between them.

**🔧 Zero Configuration**: No service registries, no hard-coded connections. Components find each other dynamically.

**🎯 Loose Coupling**: Agents and processes know nothing about the API or web interface. They just respond to NATS events.

**📈 Infinite Scalability**: Want more capacity? Deploy more instances. Want new capabilities? Deploy new agent types. The system adapts automatically.
:::

::: details Communication Patterns - The Signal Types
**How Different Components Communicate**

**🌐 Web ↔ API**: REST and WebSocket for user interactions and real-time streaming

**📡 API ↔ NATS**: Discovery events, work delegation, and response streaming

**🤖 Agent ↔ NATS**: Discovery responses, workflow step publishing, and inter-agent communication

**🔄 Process ↔ NATS**: Process orchestration, step coordination, and status updates

**📊 Pipeline ↔ Data Lake**: File watching and reactive processing (no NATS needed)

**🎯 Agent ↔ Vector Store**: Direct access for knowledge retrieval

**💾 API ↔ Data Lake**: File uploads that trigger pipeline processing
:::

::: details Security Architecture - Trust Through Transparency
**Enterprise-Grade Security That Scales**

Security isn't an afterthought in the AI-Hub—it's woven into every layer of the architecture:

**🔐 Authentication**: Seamless integration with enterprise identity providers through OAuth2/OIDC, supporting single sign-on and multi-factor authentication.

**🛡️ Authorization**: Hierarchical permission system with wildcard support allows fine-grained access control that scales with organizational complexity.

**🏠 Data Sovereignty**: Complete on-premises deployment capability ensures sensitive data never leaves your control, meeting the strictest regulatory requirements.

**📊 Audit Trails**: Comprehensive logging and traceability across all components provides the transparency needed for compliance and debugging.
:::

## :trophy: Why This Architecture Works

This architecture isn't just technically sound—it's designed to solve real business problems and grow with your organization.

::: details Modularity
**Independent Evolution**

Each component can be developed, tested, and deployed independently. Your API team can ship improvements without waiting for the web team, and your data scientists can enhance agents without affecting user interfaces.
:::

::: details Scalability
**Growth That Doesn't Hurt**

Components can be scaled horizontally based on demand. Need more API capacity? Scale the API layer. Processing more documents? Scale the pipeline layer. The architecture adapts to your needs.
:::

::: details Maintainability
**Code That Stays Clean**

Clear separation of concerns makes the system easier to understand and modify. New team members can quickly understand their area of responsibility without needing to grasp the entire system.
:::

::: details Extensibility
**Future-Proof Design**

New components can be added without disrupting existing functionality. Want to add mobile apps? The API layer is ready. Need new AI capabilities? The agent system is designed for expansion.
:::

::: details Testability
**Confidence in Every Change**

Each component can be tested in isolation with comprehensive test suites. Integration tests ensure components work together correctly, while unit tests catch issues early.
:::

::: details Observability
**Visibility Into Everything**

Built-in monitoring and tracing across all components means you always know what's happening in your system. Performance issues, bottlenecks, and errors are visible and actionable.
:::

The Swiss AI-Hub's architecture is more than just a technical design—it's a foundation for building intelligent, collaborative systems that users love and administrators trust.

