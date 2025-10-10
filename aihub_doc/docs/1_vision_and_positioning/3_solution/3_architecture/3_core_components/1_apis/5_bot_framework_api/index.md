---
title: Bot Framework API
index: 5
---

# Bot Framework API (Independent Component)

## Overview

The Bot Framework API is a **separate, independently deployable service** that integrates AI-Hub agents with Microsoft
Azure Bot Service, enabling users to interact with AI agents through familiar collaboration platforms like Microsoft
Teams and Slack. Unlike the main API service that exposes HTTP and WebSocket endpoints, the Bot API translates bot
platform messages (Activities) into AI-Hub events and streams agent responses back to users in their preferred
communication channels.

## Design Rationale

### Meeting Users Where They Work

A core principle of the Swiss AI-Hub is to bring specialized intelligence directly into familiar work environments
rather than forcing employees to switch to specialized AI applications. The Bot Framework API fulfills this principle
by:

- **Embedding AI in Collaboration Tools**: Users interact with AI agents through the same Teams or Slack interfaces they
  already use for daily communication
- **Eliminating Context Switching**: No need to open separate applications or remember additional credentials
- **Leveraging Existing Workflows**: Conversations with AI agents integrate seamlessly with team channels, group chats,
  and direct messages
- **Reducing Adoption Friction**: Users can start benefiting from AI without learning new tools or interfaces

### Azure Bot Service as Multi-Channel Gateway

Microsoft's Azure Bot Service provides a standardized abstraction over multiple messaging platforms. By integrating with
Bot Service, the Swiss AI-Hub gains:

- **Multi-Channel Support**: Single integration provides access to Teams, Slack, Web Chat, and future channels
- **Standardized Messaging**: Uniform "Activity" format eliminates platform-specific code
- **Enterprise Authentication**: Integration with Microsoft Entra ID for Teams, OAuth for Slack
- **Rich Messaging**: Support for Cards, adaptive forms, buttons, and interactive elements
- **Multimodal Inputs**: Text, speech, images, and file uploads work consistently across channels

### Independent Deployment Model

The Bot API is packaged as a **separate Docker container** and deployed independently from the main API service for
several architectural reasons:

**Separation of Concerns**:

- Bot API handles only bot-specific logic (Activity translation, conversation tracking)
- Main API focuses on HTTP/REST and WebSocket concerns
- Changes to bot integration don't impact core API stability

**Independent Scaling**:

- Bot API instances scale based on conversation volume
- Main API instances scale based on HTTP request patterns
- Different scaling characteristics don't interfere with each other

**Deployment Flexibility**:

- Organizations can deploy bot integration only if needed
- Bot API can be deployed in different regions or availability zones
- Updates to bot functionality don't require main API redeployment

**Security Isolation**:

- Bot credentials and channel configurations isolated from main API
- Reduced blast radius if bot-specific vulnerabilities discovered
- Separate audit trails for bot interactions

## Core Capabilities

### 1. Multi-Channel Conversation Management

**Supported Channels**:

- **Microsoft Teams**: Private chats, group chats, team channels
- **Slack**: Direct messages, private channels, public channels (via Bot-in-the-Loop)
- **Web Chat**: Embeddable web chat widget for custom applications
- **Future Channels**: Extensible to other Bot Framework-supported platforms

**Conversation State Management**:

The Bot API maintains persistent conversation state across user interactions:

**ConversationEntity**: Each conversation is tracked in MongoDB with:

- `conversation_id`: Unique identifier from the bot platform
- `channel`: Platform identifier (msteams, slack, webchat)
- `locale`: User's language preference for localized responses
- `messages`: Complete message history for context reconstruction
- `ttl`: Time-to-live for automatic conversation cleanup (default 30 days)
- `metadata`: Channel-specific context (team ID, thread ID, etc.)

**TTL and Cleanup**: Conversations are automatically deleted after the configured TTL expires, preventing indefinite
data retention and ensuring compliance with data retention policies.

### 2. Agent Integration and Routing

**Agent Selection**:

The Bot API supports multiple agent routing strategies:

**Direct Agent Binding**: Specific bot endpoints route to predetermined agents:

- `/agent/chat/completions/research_agent/default/stream` - Routes to research_agent:default

**Dynamic Agent Selection**: Users can specify agents in conversation:

- "@research_agent analyze this market data"
- Agent discovery and routing based on user permissions

**Multi-Model Support**: A single bot conversation can interact with multiple agents:

- Switch between agents based on conversation context
- Specialized agents for different types of questions

**Agent Communication Flow**:

1. **User Message Received**: Bot API receives Activity from Azure Bot Service
2. **Authentication and Authorization**: User identity validated, permissions checked
3. **Message Translation**: Activity converted to `ExternalAgentEvent` with:
   - Thread ID for conversation context
   - User message content and attachments
   - Channel-specific metadata
4. **Event Publishing**: Event published to NATS topic for target agent
5. **Response Streaming**: Agent events streamed back from NATS and translated to bot Activities
6. **Activity Delivery**: Bot API sends response Activities to Azure Bot Service, which delivers to user

### 3. Streaming and Non-Streaming Response Modes

**Non-Streaming (JSON) Mode**:

- Bot waits for complete agent response
- Single Activity sent to user with full response
- Simpler implementation, suitable for quick responses
- Used by `AgentChatBot` implementation

**Streaming Mode**:

- Initial empty Activity created immediately
- Activity updated incrementally as agent generates response chunks
- Provides real-time feedback with typing indicators
- Updates throttled to 0.5 second intervals to respect platform rate limits
- Used by `StreamAgentChatBot` implementation

**Typing Indicators**:

- Displayed while agent processes request
- Automatically timeout after configurable period (default 60 seconds)
- Provide user feedback even if agent response delayed

### 4. Bot-in-the-Loop Pattern

A specialized capability enabling **AI agents to request human input mid-workflow** via Slack channels:

**How It Works**:

1. **Agent Requests Human Input**: During execution, an agent sends `BotInTheLoop.request` event with:
   - Slack channel ID where to post the question
   - Message text asking for human decision or input
   - Context about why human input is needed
2. **Bot Posts to Slack**: Bot API posts formatted message to specified Slack channel
3. **Human Responds**: Team member replies in Slack thread
4. **Response Captured**: Bot API captures thread reply and sends `BotInTheLoop.response` event back to agent
5. **Agent Continues**: Agent receives human input and continues workflow execution

**Use Cases**:

- Approval workflows (e.g., "Approve this expense?")
- Expert consultation (e.g., "Which pricing model should we use?")
- Disambiguation (e.g., "Did you mean customer A or customer B?")
- Quality checks (e.g., "Does this summary look correct?")

**Slack Integration Requirements**:

- Slack OAuth token configured in bot credentials
- Bot must be invited to target Slack channels
- Thread detection to capture responses correctly

## Implementation Architecture

The Bot API integrates with Azure Bot Service through platform-specific handlers that address channel differences.
Microsoft Teams handlers manage conversation ID reuse and rich message formatting (Adaptive Cards). Slack handlers
support thread detection and platform-specific markdown translation.

### Deployment Model

The component is packaged as an independent Docker container (`aihub-bot:latest`), enabling separate deployment and
scaling from the main API service. The stateless design with MongoDB-persisted state supports horizontal scaling based
on conversation volume. Integration with the platform's NATS event system enables bidirectional communication: bot
activities translate to NATS events for agent processing, with responses streamed back through NATS subscriptions.

## Authentication and Access Control

Azure AD app registration provides bot authentication with support for single-tenant and multi-tenant configurations.
Bot credentials are stored separately from main API credentials in MongoDB, indexed by endpoint path. Azure Bot Service
validates all incoming activities with signed JWT tokens. User identity flows from collaboration platforms (Microsoft
Entra ID for Teams, OAuth for Slack) to AI-Hub accounts, enabling consistent permission enforcement through the
platform's hierarchical access control system.

## Observability and Performance

Comprehensive instrumentation captures conversation metrics (count, duration, volume), response latency, error rates,
and TTL-based cleanup statistics. Distributed tracing follows bot interactions end-to-end from Azure Bot Service through
NATS to agent processing. Typical performance characteristics include 50-100ms activity processing latency, 1-3 second
end-to-end user response time, and support for thousands of concurrent conversations per instance with linear horizontal
scaling.

## Security and Compliance

Input validation and sanitization protect against injection attacks and enforce message length limits. Output filtering
applies content safety checks and PII redaction based on organizational policies. Credential separation reduces blast
radius, with support for zero-downtime secret rotation. Configurable conversation TTL (default 30 days) ensures data
retention policy compliance, with complete conversation logging for audit requirements. Communication uses TLS 1.2+
encryption across all channels.
