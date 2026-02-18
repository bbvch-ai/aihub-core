---
title: AI-Hub Bot Integration
index: 6
---

# 🤖 AI-Hub Bot Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_bot-core&metric=alert_status&token=03193dc08631f5b20dd72de1b2bf28cdb48a9ed1)](https://sonarcloud.io/summary/new_code?id=aihub-core_bot-core)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_bot-core&metric=security_rating&token=03193dc08631f5b20dd72de1b2bf28cdb48a9ed1)](https://sonarcloud.io/summary/new_code?id=aihub-core_bot-core)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_bot-core&metric=vulnerabilities&token=03193dc08631f5b20dd72de1b2bf28cdb48a9ed1)](https://sonarcloud.io/summary/new_code?id=aihub-core_bot-core)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_bot-core&metric=sqale_rating&token=03193dc08631f5b20dd72de1b2bf28cdb48a9ed1)](https://sonarcloud.io/summary/new_code?id=aihub-core_bot-core)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_bot-core&metric=ncloc&token=03193dc08631f5b20dd72de1b2bf28cdb48a9ed1)](https://sonarcloud.io/summary/new_code?id=aihub-core_bot-core)

## 1. 🎯 Foundational Knowledge of Bot Development

This section covers the foundational architecture, patterns, and terminology you need to know before building a bot.

::: info
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_bot`

You are contributing to the **aihub_bot** scope, which provides the core logic for building and integrating chatbots with platforms like Microsoft Teams and Slack within the AI-Hub platform. This scope implements conversational interfaces that connect users to AI-Hub services through familiar collaboration tools, enabling seamless AI interactions without context switching.

### 📁 Project Structure

The `aihub_bot` scope is organized as follows:

```
aihub_bot/
├── aihub_bot/                  # Main package source
│   ├── bots/                   # Core bot implementations
│   │   ├── bot_in_the_loop/   # Bot-in-the-loop pattern implementation
│   │   └── chat/               # Chat bot base classes and handlers
│   │       ├── agent/          # Agent-based chat implementations
│   │       └── openai/         # OpenAI-based chat implementations
│   ├── persistence/            # Conversation and state management
│   │   └── entities/           # Database entities
│   ├── routes/                 # Bot controllers and API endpoints
│   │   ├── agent/              # Agent chat endpoints
│   │   ├── bot_in_the_loop/   # Bot-in-the-loop endpoints
│   │   └── openai/             # OpenAI chat endpoints
│   └── runners/                # Bot server runners and test infrastructure
│       └── lifetime/           # Lifecycle management
└── playground/                 # Examples and testing - START HERE
    ├── development/            # Development utilities
    └── testing/                # Test bot server with frontend
```

### 🏗️ The Bot Architecture

Bots in AI-Hub follow a layered architecture designed for flexibility and reusability:

```python
# Layer 1: Base Bot - Common functionality for all bots
class BaseChatBot(ActivityHandler):
    """Handles conversation lifecycle, message routing, and error handling."""

# Layer 2: Specialized Bots - Different completion strategies
class AgentChatBot(BaseChatBot):
    """Connects to AI-Hub agents via NATS."""

class OpenaiChatBot(BaseChatBot):
    """Direct OpenAI model integration."""

# Layer 3: Streaming Variants - Real-time response streaming
class StreamAgentChatBot(AgentChatBot):
    """Streams agent responses incrementally."""
```

**Key Principles:**

- **Channel Agnostic**: Core logic works across Teams, Slack, and other channels
- **Stateful Conversations**: Persistent conversation tracking with configurable TTL
- **Flexible Completion**: Support for both agent-based and direct LLM completions
- **Real-time Streaming**: Progressive response display with typing indicators

### 🔗 Bot Framework Integration

The AI-Hub uses Microsoft Bot Framework for channel connectivity, leveraging Azure Bot Service for multi-channel support and standardized message processing.

**Azure Bot Service Architecture:**

- **Unified Platform**: Humans and AI agents share the same conversational interface
- **Multi-Channel Support**: Consistent experience across Teams, Slack, web chat, and other channels
- **Standardized Messaging**: Uniform message format enables predictable interactions
- **Multimodal Input**: Support for text, speech, images, and file uploads
- **Structured Output**: Rich responses with Cards, buttons, and interactive elements

**Channel Support:**

- Microsoft Teams (primary)
- Slack (via Bot-in-the-Loop)
- Web Chat (for testing)
- Extensible to other Bot Framework channels

**Activity Processing:**

- Message activities trigger chat completions
- Conversation updates handle bot lifecycle
- Typing activities provide user feedback
- Event activities enable custom integrations

**Event-Driven Integration:**
Once the Bot API receives messages from Azure Bot Service, it transforms them into events that integrate with the AI-Hub's event-driven architecture:

- **Agent Workflow Integration**: Messages route to appropriate AI agent workflows
- **Context Preservation**: Thread and run contexts maintain multi-turn dialogue state
- **Human Collaboration**: Seamless escalation from AI agents to human operators when needed

---

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging a bot.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

::: warning
All subsequent commands must be run from within an activated Poetry shell. This is critical for proper environment isolation.
:::

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

```bash
cd aihub_bot
poetry shell
```

#### ☁️ Azure Bot Framework Setup

::: tip
For production deployment or integration with Microsoft Teams/Slack, you'll need to configure Azure Bot Service. The AI-Hub provides a Python setup script that automates this process:
:::

```bash
# Example Azure Bot setup
python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "my-ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/messages" \
    --mongo-connection-string "mongodb://localhost:27017" \
    --system-message "You are a helpful AI assistant"
```

**What the setup script does:**

- Creates Azure AD app registration with appropriate permissions
- Generates app credentials (App ID and password)
- Creates Azure Bot resource pointing to your API endpoint
- Stores credentials in MongoDB/Cosmos DB for runtime access
- Configures single-tenant or multi-tenant authentication

**Required parameters:**

- `--resource-group`: Azure resource group name
- `--bot-name`: Name for your bot (display name and resource name)
- `--token-url`: Public URL where your bot API is hosted (use Azure DevTunnel for local development)
- `--token-path`: API endpoint path (typically `/api/v1/messages`)
- Database connection (either `--mongo-connection-string` or `--cosmos-name` + `--subscription-id`)

**Optional parameters:**

- `--tenant-id`: For single-tenant configuration (defaults to multi-tenant)
- `--location`: Azure region (default: `westeurope`)
- `--sku`: Bot service pricing tier (default: `F0` for free tier)
- `--system-message`: Custom system message for the bot
- `--slack-token`: Slack OAuth token for Slack integration

**Channel Configuration:**
After running the setup script, you must manually configure channels in the Azure Portal:

- **Microsoft Teams**: Add Teams channel in Azure Bot Service
- **Slack**: Create Slack App at [api.slack.com](https://api.slack.com/apps) and link to Azure Bot
- **Web Chat**: Automatically configured with Azure Bot Service

**Local Development with Azure DevTunnel:**

```bash
# Install Azure DevTunnel and expose your local bot server
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Use the DevTunnel URL in your bot setup (e.g., https://abc123-8000.devtunnels.ms)
```

### 🛠️ Step 1: Create Bot, Controller, and Configuration

::: info
Follow this three-part process to implement a new bot integration. Each part builds on the previous one to create a complete bot implementation.
:::

1. **Create the Bot Class**: Define the bot's behavior by extending appropriate base classes.

   ```python
   # my_bot/MyCustomBot.py
   from aihub_bot.bots.chat.BaseChatBot import BaseChatBot
   from aihub_bot.bots.chat.CompletionHandler import CompletionHandler
   from microsoft_agents.hosting.core import TurnContext
   from typing_extensions import override

   class MyCustomBot(BaseChatBot):
       def __init__(
           self,
           path: str,
           completion_handler: CompletionHandler,
           handler_kwargs: dict[str, Any],
           custom_setting: str,
       ):
           super().__init__(path, completion_handler, handler_kwargs)
           self.custom_setting = custom_setting
       
       @override
       async def on_message_activity(self, turn_context: TurnContext):
           # Custom preprocessing before base handling
           if self.should_handle_specially(turn_context):
               await self.special_handling(turn_context)
           else:
               await super().on_message_activity(turn_context)
   ```

2. **Create the Completion Handler**: Implement the logic for generating responses.

   ```python
   # my_bot/MyCompletionHandler.py
   from aihub_bot.bots.chat.CompletionHandler import CompletionHandler
   from aihub_lib.generative_ai.LLMs import LLMs
   from typing import AsyncGenerator

   class MyCompletionHandler(CompletionHandler):
       def __init__(self, llm_config: ChatLLMConfig):
           self.llm = LLMs.from_config(llm_config)
       
       async def complete(
           self,
           messages: list[ChatMessage],
           conversation_entity: ConversationEntity,
           t: LocaleHandler,
       ) -> ChatMessage:
           # Non-streaming completion
           response = await self.llm.achat(messages)
           return response.message
       
       async def stream_complete(
           self,
           messages: list[ChatMessage],
           conversation_entity: ConversationEntity,
           t: LocaleHandler,
       ) -> AsyncGenerator[str | None, None]:
           # Streaming completion
           async for chunk in await self.llm.astream_chat(messages):
               if chunk.delta:
                   yield chunk.delta
   ```

3. **Create the Controller**: Define HTTP endpoints for bot integration.

   ```python
   # my_bot/MyBotController.py
   from aihub_lib.routes.Controller import Controller
   from aihub_bot.routes.RoutesService import RoutesService
   from typing import Annotated
   from fastapi import Depends

   class MyBotController(Controller):
       name = LocaleString(en="My Custom Bot")
       description = LocaleString(en="Custom bot implementation")
       icon = "robot"
       
       def __init__(self, *, auth: AuthHandler, custom_config: dict, route: str = "/my-bot"):
           super().__init__(auth=auth, route=route)
           self.custom_config = custom_config
       
       def chat_completion(self, route: str = "/chat", **kwargs) -> "MyBotController":
           @self.router.post(route, tags=self.tags)
           async def chat_completion(
               activity: dict,
               service_url: Annotated[str, Header()],
               routes_service: Annotated[RoutesService, Depends(use_routes_service)],
               user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.bot.chat"))],
               t: Annotated[LocaleHandler, Depends(use_locale)]
           ) -> dict:
               bot = MyCustomBot(
                   path=f"{self.route}{route}",
                   completion_handler=MyCompletionHandler(self.custom_config["llm"]),
                   handler_kwargs={"user": user},
                   **kwargs
               )
               return await routes_service.process_activity(activity, service_url, bot)
           return self
   ```

### 🧪 Step 2: Write and Run Tests

::: tip
Bot testing uses pytest with the `BotTestRunner` for integration testing. This provides a complete testing environment without requiring external services.
:::

1. **Create Test Files**: Write comprehensive tests for your bot.

   ```python
   # playground/testing/tests/test_my_bot.py
   import pytest
   from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler
   from fastapi.testclient import TestClient
   from aihub_bot.runners.BotTestRunner import BotTestRunner
   from aihub_bot.routes.my_bot.MyBotController import MyBotController

   @pytest.fixture
   def bot_client():
       """Fixture to create a test client for the bot."""
       auth = DangerousDevelopmentOnlyAuthHandler()
       runner = BotTestRunner()
       runner.mount(MyBotController(auth=auth, custom_config=test_config).chat_completion())
       return TestClient(runner.create_app())

   def test_bot_message_handling(bot_client):
       """Test bot handles messages correctly."""
       # Load test activity from JSON
       with open("tests/user_message.json") as f:
           activity = json.load(f)
       
       response = bot_client.post(
           "/api/v1/my-bot/chat",
           json=activity,
           headers={"Service-Url": "https://test.bot.framework.com"}
       )
       assert response.status_code == 200
       
   @pytest.mark.asyncio
   async def test_bot_conversation_tracking():
       """Test conversation persistence works correctly."""
       # Test conversation entity creation and TTL
       entity = await ConversationEntity.create_or_update(
           conversation_id="test-conv-123",
           channel="msteams",
           locale="en-US"
       )
       assert entity.conversation_id == "test-conv-123"
       assert entity.ttl > 0
   ```

2. **Run Tests**: Execute tests from your activated Poetry shell.

   ```bash
   # Run all tests
   poetry run pytest

   # Run specific test file
   poetry run pytest playground/testing/tests/test_my_bot.py

   # Run with coverage
   make test-cov
   ```

### 🎮 Step 3: Test with Playground

::: info
The playground provides a full bot server with web interface for interactive testing. This is the recommended way to test your bot implementation interactively.
:::

1. **Update Playground Configuration**: Add your bot to the test server.

   ```python
   # playground/testing/main.py
   from aihub_bot.routes.my_bot.MyBotController import MyBotController

   async def main():
       runner = BotTestRunner()
       auth = DangerousDevelopmentOnlyAuthHandler()
       
       runner.mount(
           # ... existing controllers ...
           MyBotController(
               auth=auth,
               custom_config={
                   "llm": test_llm_config,
                   "special_mode": True
               }
           ).chat_completion(),
       )
       
       # Mount the test frontend
       runner.mount_frontend(join(dirname(abspath(__file__)), "frontend"))
       
       await runner.run()
   ```

2. **Start the Test Server**: Run the playground server.

   ```bash
   cd playground/testing
   python main.py
   ```

3. **Access the Bot**:

   - **Web Interface**: `http://localhost:8000` (interactive chat UI)
   - **API Docs**: `http://localhost:8000/api/v1/docs` (Swagger UI)
   - **Direct Bot Endpoint**: `http://localhost:8000/api/v1/my-bot/chat`
   - **Bot Framework Emulator**: Connect to `http://localhost:8000/api/v1/messages`

### 🔍 Step 4: Debug and Observe Your Bot

::: tip Enable Logging
Add logging to your bot development for better debugging visibility.
:::

```python
# Add to your main.py or test files
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```

**Key Debugging Tools:**

- **Bot Framework Emulator**: Desktop app for testing bot conversations
- **Activity Inspection**: Log full activity JSON to understand channel-specific data
- **Conversation Tracking**: Monitor `ConversationEntity` updates in MongoDB
- **Network Monitoring**: Use browser dev tools to inspect bot API calls

**Common Debugging Patterns:**

- Check activity type and channel ID for proper routing
- Verify conversation reference for reply activities
- Test typing indicator timeouts with slow completions
- Monitor NATS messages for agent-based bots

### ✅ Step 5: Ensure Code Quality

::: warning
Before committing your changes, use the provided Makefile commands to ensure code quality.
:::

```bash
# Run this before creating a pull request
make pr-ready

# Or run commands individually
make format      # Ruff formatting
make lint        # Ruff linting
```

::: danger
All bot code must use strict Python type annotations and follow the established patterns. This is enforced by CI/CD.
:::

---

## 3. 🎨 Bot Design Patterns and Best Practices

This section covers common patterns and best practices for building robust bot implementations.

### 📱 Channel-Specific Patterns

::: info
Different channels require different handling approaches due to their unique features and limitations. Understanding these patterns is crucial for robust bot development.
:::

#### 🟣 Microsoft Teams Pattern

::: warning Microsoft Teams Conversation Management
Microsoft Teams has unique conversation management behavior that requires special handling. Unlike other channels, Teams reuses conversation IDs when users delete and restart conversations. The only way to detect a fresh conversation is by monitoring when the bot is re-added to the conversation.

This pattern is crucial for maintaining proper conversation state - without it, users would see old conversation history even after deleting a conversation in Teams.
:::

```python
class TeamsBot(BaseChatBot):
    @override
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """Handle Teams-specific conversation lifecycle."""
        if turn_context.activity.channel_id == Channels.ms_teams:
            # Teams reuses conversation IDs - check if bot was re-added
            members_added = turn_context.activity.members_added or []
            bot_id = turn_context.activity.recipient.id
            
            if any(member.id == bot_id for member in members_added):
                # Bot was added - treat as new conversation
                await ConversationEntity.delete_by_conversation_id(
                    turn_context.activity.conversation.id
                )
                await turn_context.send_activity("Starting fresh conversation!")
```

#### 💬 Slack Integration Pattern

::: tip Slack Integration Considerations
Slack integration requires special handling for threading and message formatting. The Bot-in-the-Loop pattern specifically uses Slack channels with threading support, where the bot posts messages to specific channels and monitors thread responses for human input.
:::

Key considerations for Slack integration:

- **Thread Detection**: Messages must be identified as coming from Slack channel threads
- **Message Formatting**: Slack uses different markdown syntax than other channels
- **Response Handling**: Bot responses need to be formatted appropriately for Slack's display requirements

```python
class SlackBot(BaseChatBot):
    def is_slack_channel_thread_message(self, turn_context: TurnContext) -> bool:
        """Check if message is from a Slack thread."""
        conversation = turn_context.activity.conversation
        return (
            conversation 
            and hasattr(conversation, "conversation_type") 
            and conversation.conversation_type == "channel"
            and "thread_ts" in turn_context.activity.conversation.id
        )
    
    async def format_slack_response(self, text: str) -> str:
        """Convert markdown to Slack formatting."""
        # Bold: **text** -> *text*
        text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
        # Links: [text](url) -> <url|text>
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<\2|\1>', text)
        return text
```

### 🎯 Completion Strategies

::: info
AI-Hub bots support multiple completion strategies through the `CompletionHandler` interface:
:::

**Agent-Based Completion:**

- Routes messages to AI-Hub agents via NATS messaging
- Supports both streaming and non-streaming responses
- Maintains conversation context across agent interactions
- Used by `AgentChatBot` and `StreamAgentChatBot`

**Direct LLM Completion:**

- Directly calls OpenAI-compatible models
- Faster response times without agent overhead
- Used by `OpenaiChatBot` and `StreamOpenaiChatBot`

**Multi-Model Support:**

- Single bot can support multiple LLM configurations
- Configurable selection strategies (round-robin, least-cost, etc.)
- Useful for fallback scenarios or cost optimization

### 💬 Conversation Management

::: info
AI-Hub bots maintain conversation state across user interactions and bot restarts through the `ConversationEntity` system:
:::

**Key Features:**

- **Persistent Storage**: Conversations are stored in MongoDB with configurable TTL (default 30 days)
- **Message History**: Full conversation history is maintained and can be reconstructed
- **Channel Context**: Each conversation tracks its channel, locale, and metadata
- **Automatic Cleanup**: TTL is refreshed on each interaction and expired conversations are automatically removed

**Configuration:**

```python
runner = BotRunner(conversation_ttl_days=60)  # Custom TTL
```

### 🌊 Streaming Responses

::: tip
AI-Hub bots support real-time response streaming, allowing users to see responses as they're generated:
:::

**How it works:**

1. Bot sends an empty message to establish the activity
2. As response chunks are generated, the message is updated incrementally
3. Updates are throttled (every 0.5 seconds) to avoid rate limits
4. Final message shows the complete response

**Built-in streaming support:**

- `StreamAgentChatBot`: Streams responses from AI agents
- `StreamOpenaiChatBot`: Streams responses from OpenAI models
- Automatic error handling with partial response preservation

### 🔄 Bot-in-the-Loop Pattern

::: info Bot-in-the-Loop Pattern
The Bot-in-the-Loop pattern enables AI agents to pause their execution and request human input via Slack channels. This is particularly useful for approval workflows, complex decision-making, or when human expertise is required.
:::

**How it works:**

1. An AI agent encounters a decision point requiring human input
2. The agent sends a `BotInTheLoop.request` event to the bot system
3. The bot posts a formatted message to the specified Slack channel
4. A human responds in the Slack thread
5. The bot captures the response and sends it back to the waiting agent
6. The agent continues execution with the human input

This pattern enables seamless human-AI collaboration within automated workflows.

#### 🔄 Handler vs Bot: Separation of Concerns

::: info Architectural Pattern
The Bot-in-the-Loop implementation demonstrates a clear separation of concerns between two complementary components: the **Handler** (outbound message delivery) and the **Bot** (inbound message processing). Understanding this separation is crucial when working with or extending the bot-in-the-loop functionality.
:::

**Handler - Outbound Message Delivery:**

The Handler is responsible for **sending** bot-in-the-loop requests from AI agents to human users via communication channels:

- **Purpose**: Delivers questions from AI agents to Slack/Teams channels
- **Trigger**: AI agent requests human input during workflow execution
- **Responsibilities**:
  - Manages thread state and conversation tracking
  - Builds channel-specific conversation references
  - Formats and sends outbound messages
  - Stores thread identifiers for matching future responses

**Bot - Inbound Message Processing:**

The Bot is responsible for **receiving** human responses from Slack/Teams and routing them back to waiting AI agents:

- **Purpose**: Captures human responses and returns them to AI agents
- **Trigger**: Human replies in Slack/Teams thread
- **Responsibilities**:
  - Parses incoming messages to identify the thread
  - Matches responses to original request threads
  - Extracts responder information (user identity, metadata)
  - Publishes response events back to waiting agents

**Why This Separation Matters:**

1. **Distinct Data Flow**: Handler manages agent→human flow; Bot manages human→agent flow
2. **Different Event Sources**: Handler consumes internal agent events; Bot consumes external channel activities
3. **Inverse Operations**: Handler **builds** channel-specific references; Bot **parses** them back
4. **Clear Boundaries**: Each component has a single, well-defined responsibility
5. **Independent Evolution**: Changes to outbound logic don't affect inbound processing and vice versa

**Shared Concepts:**

While the components are separate, they share domain concepts:

- Both reference the same thread tracking data
- Both use channel-specific identifiers (Slack thread timestamps, Teams message IDs)
- Both operate on the same conversation lifecycle
- They communicate through a shared thread registry

This architectural pattern ensures maintainability and makes it easy to extend bot-in-the-loop functionality to new channels by implementing channel-specific logic in each component independently.

### 🛡️ Error Handling and Testing

::: tip
For robust bot development, implement comprehensive error handling and use the provided testing infrastructure:
:::

**Error Handling Best Practices:**

- Show typing indicators during processing to provide user feedback
- Handle timeouts gracefully with user-friendly messages
- Log errors for debugging while showing generic error messages to users
- Implement retry logic for transient failures

**Testing with Simulated Agents:**
The `SimulatedAgentBotTestRunner` allows you to test bot functionality without requiring actual agents:

```python
# Create test runner with mock agent responses
runner = SimulatedAgentBotTestRunner(agent_class="test_agent", agent_id="test_123")
runner.with_simple_chunk_events()  # Simulates streaming responses
```

**Channel-Specific Testing:**
Test your bot with different Bot Framework activity types to ensure compatibility across Teams, Slack, and other channels.

---

## 4. 📚 Reference Material

This section serves as an appendix for locating key files and running specific tasks.

### 🎮 Running Bots Interactively

::: info
The playground provides different configurations for various testing scenarios.
:::

#### 🚀 Development Mode

```bash
# Full bot with all features enabled
cd playground/development
python main.py
```

This starts a bot server with:

- OpenAI chat endpoints
- Agent chat endpoints
- Bot-in-the-loop functionality
- Extended conversation TTL (60 days)

#### 🧪 Testing Mode

```bash
# Bot with simulated agents and web UI
cd playground/testing
python main.py
```

This provides:

- Simulated agent responses (no real agents needed)
- Web-based chat interface
- All bot endpoints for testing
- Frontend at `http://localhost:8000`

### 🖥️ Bot Framework Emulator Setup

1. Download Bot Framework Emulator from Microsoft
2. Configure endpoint URL: `http://localhost:8000/api/v1/messages`
3. Leave App ID and Password empty for local testing
4. Test different activity types and channels

### ☁️ Azure Bot Deployment

#### 🏭 Production Deployment Process

1. **Run the Setup Script**: Use the provided `setup_azure_bot.py` script to automate Azure resource creation
2. **Configure Public Endpoint**: Ensure your bot API is publicly accessible (use ngrok for development)
3. **Set Up Channels**: Manually configure channels in Azure Portal after resource creation
4. **Monitor and Debug**: Use Azure Portal monitoring and Bot Framework Emulator for testing

#### 🔐 Credential Management

::: danger Credential Security
The setup script stores bot credentials in your database for runtime access. Ensure your database is properly secured in production environments.
:::

```python
# Credentials stored in MongoDB collection "bot_paths"
{
    "path": "/api/v1/messages",
    "credentials": {
        "APP_TYPE": "MultiTenant",  # or "SingleTenant"
        "APP_ID": "your-app-id",
        "APP_PASSWORD": "your-app-password", 
        "APP_TENANTID": "your-tenant-id"     # Only for single-tenant
    },
    "system_message": "Custom system message",
    "slack_token": "slack-oauth-token"       # Optional for Slack
}
```

#### 🔧 Local Development with Azure Bot

::: tip Local Development
For local development that integrates with Azure Bot Service:
:::

1. **Start your bot server locally**:

   ```bash
   cd playground/development
   python main.py
   ```

2. **Expose via Azure DevTunnel**:

   ```bash
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   # Copy the https URL (e.g., https://abc123-8000.devtunnels.ms)
   ```

3. **Update Azure Bot endpoint**:

   ```bash
   az bot update --name "my-bot" --resource-group "my-rg" \
       --endpoint "https://abc123-8000.devtunnels.ms/api/v1/messages"
   ```

4. **Test in Teams/Slack**: Your local bot now receives messages from Azure Bot Service

### 📖 Glossary of Bot-Specific Terms

This glossary defines terms, concepts, and technologies that have specific meaning within the `aihub_bot` scope, building upon the core AI-Hub terminology.

| Term                                | Definition                                                                                                                     |
| :---------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **Activity**                        | Bot Framework concept representing any communication between bot and user (messages, typing indicators, conversation updates). |
| **Activity Handler**                | Base class from Bot Framework that processes different types of activities. All bots extend this class.                        |
| **Agent Chat Bot**                  | Bot implementation that connects to AI-Hub agents, forwarding user messages to agents and streaming responses back.            |
| **Bot Framework**                   | Microsoft's framework for building conversational AI applications, supporting multiple channels like Teams, Slack, etc.        |
| **Bot-in-the-Loop**                 | Pattern where a bot pauses an agent workflow to request human input via Slack, then resumes with the response.                 |
| **Channel**                         | Communication platform where the bot operates (e.g., Microsoft Teams, Slack, Web Chat).                                        |
| **Chat Completion**                 | Process of generating AI responses to user messages, supporting both streaming and non-streaming modes.                        |
| **Completion Handler**              | Abstract interface for processing chat completions, implemented differently for agents and OpenAI models.                      |
| **Content Extractor**               | Utility for extracting text and attachments from bot activities across different channels.                                     |
| **Conversation Entity**             | Database model tracking conversation state, messages, and metadata with configurable TTL.                                      |
| **Conversation Tracker**            | Service for persisting and managing conversation history across bot restarts.                                                  |
| **OpenAI Chat Bot**                 | Bot implementation that directly uses OpenAI-compatible models without agent orchestration.                                    |
| **Path Entity**                     | Database model storing conversation paths and routing information for multi-bot scenarios.                                     |
| **Routes Service**                  | Centralized service managing bot endpoint registration and channel configuration.                                              |
| **Simulated Agent Bot Test Runner** | Testing infrastructure that mocks agent responses for development without real agents.                                         |
| **Slack Utils**                     | Utilities for handling Slack-specific formatting, threading, and user mentions.                                                |
| **Stream Chat Bot**                 | Base class for bots that stream responses incrementally, providing real-time typing indicators.                                |
| **Turn Context**                    | Bot Framework object containing all information about the current conversation turn.                                           |
| **Typing Indicator**                | Visual feedback showing the bot is processing, with configurable timeout protection.                                           |
