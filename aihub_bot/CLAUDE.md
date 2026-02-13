# aihub_bot - Bot Integration Platform

**Purpose**: Chatbot logic for MS Teams, Slack, web chat. Connects users to AI-Hub agents via conversational interfaces.

Tech Stack & Paradigms: Azure Bot Framework (botbuilder-integration-aiohttp) for MS Teams/Slack. FastAPI + uvicorn + gunicorn for webhooks. Azure Identity + Azure mgmt SDKs (Cosmos, resources). MongoEngine with 30-day TTL for ConversationEntity. NATS pub-sub for agent communication. httpx HTTP client. cryptography + PyJWT for auth. cachetools for caching. Bot-in-the-loop pattern for human input. Streaming responses with incremental updates. BaseChatBot with AgentChatBot and OpenaiChatBot specializations. CompletionHandler abstraction. Channel-specific formatting (Markdown for Teams, Slack syntax). Azure DevTunnel for local development. BotRunner and BotTestRunner. pytest-bdd + asgi-lifespan for testing.

## Scope Responsibility

Bot Framework integration, conversation management, streaming responses, channel-specific handling. NOT agent logic (delegate to agents via NATS).

## Folder Structure

```
aihub_bot/
├── bots/                      # Bot implementations
│   ├── bot_in_the_loop/       # Bot-in-the-loop pattern (Slack integration)
│   └── chat/                  # Chat bot base + variants
│       ├── agent/             # Agent-based chat (AgentChatBot, StreamAgentChatBot)
│       └── openai/            # Direct LLM chat (OpenaiChatBot, StreamOpenaiChatBot)
├── persistence/entities/      # ConversationEntity (MongoDB, 30-day TTL)
├── routes/                    # Bot controllers (FastAPI endpoints)
└── playground/testing/        # Test server with Bot Framework Emulator support
```

## Key Architecture

**Bot Layers**:

1. **BaseChatBot**: Common conversation lifecycle, routing, error handling
2. **Specialized Bots**: `AgentChatBot` (NATS to agents), `OpenaiChatBot` (direct LLM)
3. **Streaming Variants**: `StreamAgentChatBot`, `StreamOpenaiChatBot` (real-time responses)

**Completion Handler Pattern**: Abstract interface for generating responses. Implementations for agents vs direct LLM.

## Channel-Specific Patterns

**MS Teams**:

- **Conversation Reuse**: Teams reuses conversation IDs. Detect fresh conversation via `on_conversation_update_activity` (bot re-added).
- **Critical**: Delete `ConversationEntity` when bot added to reset history.

**Slack** (Bot-in-the-Loop):

- **Thread Detection**: Check `conversation.conversation_type == "channel"` + `thread_ts` in conversation ID.
- **Formatting**: Convert markdown (`**text**` → `*text*`, `[text](url)` → `<url|text>`).

## Conversation Management

**ConversationEntity**:

- Stored in MongoDB with 30-day TTL (configurable)
- Tracks: messages, channel, locale, metadata
- Auto-refreshed on interaction, auto-deleted on expiry

**Configuration**: `BotRunner(conversation_ttl_days=60)`

## Streaming Responses

**How it works**:

1. Send empty message to establish activity
2. Update incrementally as chunks arrive (throttled every 0.5s)
3. Final message shows complete response

**Built-in**: `StreamAgentChatBot`, `StreamOpenaiChatBot`

## Bot-in-the-Loop Pattern

**Purpose**: AI agents pause → request human input via Slack → resume with response.

**Components**:

- **Handler** (outbound): Sends agent questions to Slack channels
- **Bot** (inbound): Captures human responses, returns to agents

**Separation**: Handler builds channel refs, Bot parses them. Inverse operations, clear boundaries.

## Azure Bot Service Setup

**Script**: `/home/user/aihub-core/aihub_bot/setup_azure_bot.py`

**Creates**:

- Azure AD app registration
- Azure Bot resource
- Credentials stored in MongoDB (`bot_paths` collection)

**Channels**: Manually configure in Azure Portal (Teams, Slack, Web Chat).

**Local Dev**: Use Azure DevTunnel to expose local bot → Azure Bot Service.

## Testing

**BotTestRunner**: Simulated agents for testing without real agent services.

**Bot Framework Emulator**:

- Desktop app for testing conversations
- Connect to: `http://localhost:8000/api/v1/messages`
- Leave App ID/Password empty for local testing

**Test Activities**: Use JSON files (e.g., `tests/user_message.json`) to simulate channel-specific messages.

## Playground

**Location**: `/home/user/aihub-core/aihub_bot/playground/testing/`
**Start**: `cd playground/testing && python main.py`
**Access**: http://localhost:8000 (web UI), http://localhost:8000/api/v1/messages (bot endpoint)

## Pre-Commit

```bash
make pr-ready  # Format + lint
make test      # Run tests
```

## Essential Files

- Base bot: `/home/user/aihub-core/aihub_bot/aihub_bot/bots/chat/BaseChatBot.py`
- Agent chat bot: `/home/user/aihub-core/aihub_bot/aihub_bot/bots/chat/agent/AgentChatBot.py`
- Conversation entity: `/home/user/aihub-core/aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py`
- Bot-in-the-loop: `/home/user/aihub-core/aihub_bot/aihub_bot/bots/bot_in_the_loop/`
- Playground: `/home/user/aihub-core/aihub_bot/playground/testing/main.py`

## Quick Reference

**Create custom bot**:

```python
class MyBot(BaseChatBot):
    def __init__(self, path: str, completion_handler: CompletionHandler, **kwargs):
        super().__init__(path, completion_handler, kwargs)

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        # Custom logic or delegate to base
        await super().on_message_activity(turn_context)
```

**Create completion handler**:

```python
class MyCompletionHandler(CompletionHandler):
    async def complete(self, messages: list[ChatMessage], conversation_entity: ConversationEntity, t: LocaleHandler) -> ChatMessage:
        # Generate response
        return ChatMessage(content="response", role=MessageRole.ASSISTANT)
```

**Enable logging**:

```python
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```
