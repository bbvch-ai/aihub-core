---
title: Azure Bot Service Integration
---

# Azure Bot Service Integration :speech_balloon: :100:

::: info **TL;DR - What is Azure Bot Service Integration?**
Azure Bot Service Integration transforms the Swiss AI Hub into a **multi-channel conversational platform** that connects
users to AI agents through familiar collaboration tools like Microsoft Teams and Slack. This integration provides
enterprise-grade bot connectivity with streaming responses, conversation persistence, and seamless human-in-the-loop
workflows, eliminating the need for users to switch between applications to access AI assistance.
:::

## What is Azure Bot Service Integration and How Does It Work? :brain:

Azure Bot Service Integration leverages **Microsoft Bot Framework** to provide unified conversational experiences across
multiple channels, making Swiss AI Hub's capabilities accessible wherever users naturally work and collaborate.

**Multi-Channel Bot Architecture** enables consistent AI interactions across:

- **Microsoft Teams** - Native integration with enterprise collaboration workflows
- **Slack** - Direct channel messaging for expert consultation and bot responses
- **Web Chat** - Browser-based interface for testing and development
- **Extensible Channel Support** - Any Bot Framework-supported platform

**[Bot-in-the-Loop Infrastructure](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** powers sophisticated human-AI
collaboration by enabling AI agents to pause their workflows and seamlessly request human input through Slack channels.
When agents need expert knowledge or approval, they automatically post structured questions to designated channels,
capture responses, and continue processing with human-provided context.

**Intelligent Chat Bot Implementations** provide multiple completion strategies:

- **Agent Chat Bots** connect directly to Swiss AI Hub agents via NATS messaging for complex workflows
- **OpenAI Chat Bots** provide direct LLM integration for faster, simpler interactions
- **Streaming Support** delivers real-time response updates with typing indicators across all channels

**Enterprise-Grade Infrastructure** includes automated Azure AD app registration, secure credential management,
conversation persistence with configurable TTL, and comprehensive audit trails for compliance requirements.

**Key Technologies:**

- **Azure Bot Framework** - Multi-channel connectivity and message routing
- **Azure AD Integration** - Enterprise authentication and authorization
- **NATS Messaging** - Agent orchestration and event-driven workflows
- **MongoDB/Cosmos DB** - Conversation persistence and configuration storage
- **Infrastructure as Code** - Pulumi-based Azure resource deployment

## Why This is a Game-Changer for Your AI Strategy :trophy:

Azure Bot Service Integration eliminates the friction between AI capabilities and user adoption by meeting users where
they already work:

**🔄 Zero Context Switching**: Users access AI assistance directly within Microsoft Teams, Slack, and other familiar
collaboration platforms. No need to learn new interfaces or interrupt established workflows - AI becomes a natural part
of daily collaboration.

**🌐 Enterprise-Scale Multi-Channel Support**: Single Swiss AI Hub deployment serves users across multiple communication
platforms simultaneously. Whether teams use Teams, Slack, or other Bot Framework-supported channels, everyone gets
consistent AI assistance tailored to their preferred collaboration environment.

**⚡ Real-Time Streaming Responses**: Advanced streaming implementation provides immediate feedback with typing
indicators, partial responses, and incremental updates. Users see AI thinking and responding in real-time, creating
natural conversation flows that feel responsive and engaging.

**🛡️ Enterprise Security and Compliance**: Built on Azure AD authentication with comprehensive conversation audit
trails, configurable retention policies, and secure credential management. All bot interactions are logged and
traceable, meeting enterprise security and compliance requirements.

**🤝 Seamless Human-AI Collaboration**:
[Bot-in-the-Loop infrastructure](../../../3_sdk/6_feature_overview/bot-in-the-loop/) enables AI agents to naturally
escalate to human experts through structured Slack workflows. Complex decisions, approvals, and knowledge gaps are
handled smoothly without breaking user experience or losing conversation context.

::: details **Setting Up and Using Azure Bot Service Integration**
## Configuration Requirements

### Azure Infrastructure Setup

1. **Azure Bot Resource Creation**: Use the automated setup script

   ```bash
   python packages/bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-swiss-ai-hub-bot" \
     --token-url "https://your-swiss-ai-hub-domain.com" \
     --token-path "/api/v1/messages" \
     --mongo-connection-string "mongodb://localhost:27017"
   ```

2. **Azure AD App Registration**: Automatically handled by setup script

   - Creates Azure AD application with Bot Framework permissions
   - Generates secure app credentials (App ID and password)
   - Configures single-tenant or multi-tenant authentication

3. **Channel Configuration**: Manually configure in Azure Portal after setup

   - **Microsoft Teams**: Add Teams channel in Azure Bot Service
   - **Slack**: Create Slack App and link to Azure Bot Service
   - **Web Chat**: Automatically configured for testing

### Local Development Setup

1. **Development Tunnel**: Expose local Swiss AI Hub for Azure Bot Service

   ```bash
   # Install and configure Azure DevTunnel
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   # Use tunnel URL in bot configuration
   ```

2. **Database Configuration**: Credentials stored in MongoDB

   ```json
   {
     "path": "/api/v1/messages",
     "credentials": {
       "APP_TYPE": "MultiTenant",
       "APP_ID": "your-app-id",
       "APP_PASSWORD": "your-app-password"
     },
     "system_message": "Custom bot instructions",
     "slack_token": "slack-oauth-token"
   }
   ```

## Usage Examples

### Microsoft Teams Integration

**Basic Chat Interaction:**

1. **Add Bot to Teams**: Install Swiss AI Hub bot in your Teams workspace
2. **Start Conversation**: Message the bot directly or mention in channels
3. **Streaming Responses**: See real-time typing indicators and incremental responses
4. **Conversation Persistence**: Context maintained across multiple interactions

**Advanced Features:**

- **Rich Responses**: Support for cards, buttons, and interactive elements
- **File Uploads**: Process documents and images directly in Teams
- **Thread Support**: Maintain conversation context in threaded discussions

### Slack Bot-in-the-Loop Workflows

For detailed information on Bot-in-the-Loop workflows, including expert consultation processes, channel configuration,
and agent integration patterns, see the dedicated
[Bot-in-the-Loop documentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot Deployment

**Agent-Based Bots**: Connect to specific Swiss AI Hub agents

```python
# Configure bot to use specific agent
AgentChatBot(
    agent_class="ExpertGroundedAgent",
    agent_id="expert_agent_v1",
    streaming=True
)
```

**OpenAI-Based Bots**: Direct LLM integration for simpler use cases

```python
# Configure bot with direct OpenAI access
OpenaiChatBot(
    llm_config=OpenAIConfig(...),
    system_message="You are a helpful assistant",
    streaming=True
)
```

## Available Capabilities

**Bot Framework Integration:**

- **Multi-Channel Deployment**: Single codebase serves Teams, Slack, Web Chat, and other channels
- **Activity Processing**: Handle messages, typing events, conversation updates, and file uploads
- **Rich Message Support**: Cards, buttons, attachments, and interactive elements
- **Conversation Management**: Persistent state with configurable TTL (default 30 days)

**[Bot-in-the-Loop Infrastructure](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

- **Slack Channel Integration**: Direct posting to expert channels with thread support
- **Response Capture**: Automatic detection and processing of human responses
- **Conversation Threading**: Maintain context across multi-turn expert consultations
- **Knowledge Persistence**: Expert responses stored for organizational learning

**Chat Bot Implementations:**

- **Streaming Responses**: Real-time message updates with typing indicators
- **Agent Integration**: Direct connection to Swiss AI Hub agent workflows via NATS
- **OpenAI Integration**: Standalone LLM interactions for simple use cases
- **Error Handling**: Graceful degradation with user-friendly error messages

## Security and Best Practices

**Security Considerations:**

- **Azure AD Authentication**: Enterprise-grade authentication with role-based access
- **Secure Credential Storage**: Bot credentials encrypted and stored in MongoDB/Cosmos DB
- **Audit Trails**: Complete conversation history with user attribution and timestamps
- **Network Security**: Support for private endpoints and VNet integration

**Best Practices:**

- **Channel Organization**: Dedicate specific Slack channels for different expert domains
- **Conversation TTL**: Configure appropriate retention policies for compliance requirements
- **Bot Naming**: Use clear, descriptive names for multiple bot deployments
- **Monitoring**: Implement comprehensive logging and alerting for bot health
- **Capacity Planning**: Monitor conversation volume and response times

**Performance Optimization:**

- **Streaming Configuration**: Tune update frequency for optimal user experience
- **Conversation Cleanup**: Implement automated cleanup of expired conversations
- **Database Indexing**: Optimize MongoDB queries for conversation retrieval
- **Caching Strategy**: Cache frequently accessed configuration and credentials
:::

## Getting Started

To implement Azure Bot Service Integration in your Swiss AI Hub deployment:

1. **Run Azure Setup Script**: Use the provided automation to create Azure Bot resources and configure authentication
   with your preferred database backend
2. **Configure Channels**: Set up Microsoft Teams and/or Slack integrations through Azure Portal channel configuration
3. **Deploy Bot Implementations**: Choose between agent-based bots for complex workflows or OpenAI-based bots for
   simpler interactions, with streaming support for enhanced user experience

For detailed setup instructions, troubleshooting guidance, and advanced configuration options, refer to the
[Bot-in-the-Loop documentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) for human-AI collaboration
workflows, the [Expert Agents documentation](../../5_agents/9_expert_coordinator_agent/) for knowledge consultation
patterns, and the Swiss AI Hub Bot Developer's Guide for implementation details.
