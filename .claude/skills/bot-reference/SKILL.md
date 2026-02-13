---
name: bot-reference
description: >-
  Comprehensive reference for the bot integration platform: handler architecture,
  CompletionHandler pattern, multi-channel handling, HITL flow, conversation state,
  NATS integration, streaming, and testing. Use when user says 'how does the bot work',
  'CompletionHandler pattern', 'bot architecture', 'Slack thread handling', 'HITL flow',
  'bot streaming', 'conversation state management', 'bot testing', 'how do bot channels work',
  or 'BaseChatBot'. Covers all bot components, request flow, and testing patterns.
arguments:
  - name: topic
    description: Topic or question (e.g., "CompletionHandler", "Slack threads", "HITL flow", "streaming", "testing", "conversation state")
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
---

# Bot Integration Platform Reference

Look up bot architecture information. Topic or question via `$ARGUMENTS`.

---

## Architecture Overview

The **aihub_bot** scope provides chatbot logic for MS Teams, Slack, and Web Chat, connecting users to AI-Hub agents via conversational interfaces.

### Three-Layer Architecture

```
Layer 1: BaseChatBot (ActivityHandler)
    ├─ Common conversation lifecycle
    ├─ Message routing & channel detection
    ├─ Typing indicators & error handling
    └─ Message persistence

Layer 2: Specialized Bots
    ├─ AgentChatBot (NATS → agents)
    └─ OpenaiChatBot (direct LLM)

Layer 3: Streaming Variants
    ├─ StreamAgentChatBot
    └─ StreamOpenaiChatBot
```

### Request Flow

```
1. Azure Bot Service → POST /api/v1/agent/chat/completions/{class}/{id}/json
2. AgentChatController._process_agent_chat_request()
   ├─ RoutesService.get_path(request) → extract URL path
   ├─ bot = AgentChatBot(nc, distributor, agent_class, agent_id, path)
   └─ adapter = RoutesService.get_adapter(path)  # Cached CloudAdapter
3. adapter.process(request, bot)
   └─ bot.on_message_activity(turn_context)
4. BaseChatBot._process_message(turn_context)
   ├─ ConversationTracker.track_conversation()
   ├─ CompletionHandler.add_user_message_to_conversation()
   ├─ handle_slack_message() / handle_teams_message()  # Channel-specific
   ├─ typing_task = send_typing_activity()  # Background typing indicator
   └─ response = await _respond()
       └─ CompletionHandler.get_completion() → NATS → Agent → response
5. CompletionHandler.add_bot_message_to_conversation()
6. Return to Azure Bot Service → Channel → User
```

---

## CompletionHandler Pattern (Strategy)

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py`

The CompletionHandler is the **core abstraction** for generating responses. All bot variants delegate to a handler.

### Interface

```python
class CompletionHandler:
    @staticmethod
    async def get_completion(**kwargs) -> str:
        """Synchronous: returns full response as string."""

    @staticmethod
    async def get_stream_completion(**kwargs) -> AsyncGenerator[str]:
        """Streaming: yields response chunks."""

    # Shared utilities (implemented in base):
    @staticmethod
    def get_system_message(turn_context, path) -> Message | None
    @staticmethod
    def handle_teams_message(turn_context) -> TurnContext | None
    @staticmethod
    def handle_slack_message(turn_context) -> TurnContext | None
    @staticmethod
    def add_user_message_to_conversation(path, turn_context) -> ConversationEntity
    @staticmethod
    def add_bot_message_to_conversation(path, turn_context, message) -> ConversationEntity
    @staticmethod
    async def send_response_stream(turn_context, response_generator) -> str
    @staticmethod
    async def send_typing_activity(turn_context, signal, t, timeout_seconds=60)
    @staticmethod
    async def handle_exception(turn_context, exception, typing_task, typing_stop_signal, t) -> str
```

### Implementations

| Handler | File | Purpose |
|---------|------|---------|
| `AgentCompletionHandler` | `bots/chat/agent/AgentCompletionHandler.py` | NATS → Agent via ChatService |
| `OpenaiCompletionHandler` | `bots/chat/openai/OpenaiCompletionHandler.py` | Direct LLM calls |

### Agent Completion Flow

```python
# AgentCompletionHandler.chat_completion()
1. persisted_messages = get_messages_by_conversation_id(conversation_id, bot_id)
2. chat_messages = [_message_to_chat_message(msg) for msg in persisted_messages]
3. resources = await ChatService.start_stream_chat_interaction(
       user=user, agent_class=agent_class, agent_id=agent_id,
       messages=chat_messages, nc=nc,
       external_agent_event_distributor=distributor,
       thread_id=thread_id, display_id=display_id
   )
4. # JSON mode: await resources.stop_signal.wait() → return content
5. # Stream mode: yield chunks from resources.chunk_queue
```

---

## Multi-Channel Handling

### Channel Detection

```python
from microsoft_agents.activity import Channels

if turn_context.activity.channel_id == Channels.ms_teams:
    # Teams-specific
elif turn_context.activity.channel_id == Channels.slack:
    # Slack-specific
elif turn_context.activity.channel_id == Channels.webchat:
    # Web Chat
```

### Teams Specifics

**Conversation reuse**: Teams reuses conversation IDs — when user deletes and re-adds bot, same ID is recycled.

```python
# BaseChatBot.on_conversation_update_activity()
# Detects: members_added contains bot recipient + not a team channel
# Action: mark as explicitly deleted, wipe conversation history
```

**Direct message detection**:
```python
# CompletionHandler._is_teams_direct_message()
channel_data = turn_context.activity.channel_data
is_dm = channel_data is None or channel_data.get("channel") is None
```

### Slack Specifics

**Conversation ID formats**:
```
Channel message:  B[bot_id]:T[team_id]:C[channel_id]
Thread message:   B[bot_id]:T[team_id]:C[channel_id]:[timestamp]
Direct message:   B[bot_id]:T[team_id]:D[dm_id]:[timestamp]
```

**Thread handling** (`CompletionHandler._update_slack_turn_context()`):
1. Detect channel message via regex: `^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+$`
2. Extract thread timestamp from `channel_data["SlackMessage"]["event"]["ts"]`
3. Append `:{ts}` to conversation ID → unique thread identifier
4. Fetch parent channel messages for context

**Mention handling**:
- Bot only responds in channels if **@mentioned** or in an existing bot thread
- `_is_bot_mentioned()` checks `activity.get_mentions()` against `activity.recipient.id`
- `_mark_conversation_as_mentioned()` persists mention state in ConversationEntity

### System Message Templates

**File**: `aihub_bot/aihub_bot/persistence/entities/PathEntity.py`

```python
# Stored in PathEntity.system_message with placeholders:
"You are {assistant_name}. The user's name is {username}."
# Resolved at runtime from TurnContext:
#   {username} → turn_context.activity.from_property.name
#   {assistant_name} → turn_context.activity.recipient.name
```

---

## Bot-in-the-Loop (HITL)

**Purpose**: AI agents pause execution → request human input via Slack/Teams → resume with response.

### Flow

```
1. Agent emits BotInTheLoopRequestEvent (control event)
2. BotInTheLoopHandler (subscriber) receives event
   ├─ Extracts channel_config (channel_id, service_url)
   ├─ Looks up Slack bot/team IDs via Slack API
   ├─ Builds ConversationReference for the target channel
   └─ Sends question message to Slack/Teams channel
3. Human replies in channel/thread
4. BotInTheLoopBot (ActivityHandler) receives reply
   ├─ Parses conversation_id → base_conversation_id + thread_identifier
   ├─ Matches to active BotInTheLoopHandler.threads entry
   └─ Distributes BotInTheLoop.response() via ExternalAgentEventDistributor
5. Agent receives response → continues workflow
```

### Key Components

| Component | File | Direction |
|-----------|------|-----------|
| **BotInTheLoopHandler** | `routes/bot_in_the_loop/BotInTheLoopHandler.py` | Outbound: agent → channel |
| **BotInTheLoopBot** | `bots/bot_in_the_loop/BotInTheLoopBot.py` | Inbound: channel → agent |
| **BotInTheLoopController** | `routes/bot_in_the_loop/BotInTheLoopController.py` | HTTP endpoint |
| **SlackUtils** | `routes/bot_in_the_loop/SlackUtils.py` | Slack API helpers |

### Thread Tracking

```python
# BotInTheLoopHandler stores active threads:
threads: dict[str, BotInTheLoopThread] = {}
# Key: thread_id (from agent event)
# Value: BotInTheLoopThread(base_conversation_id, thread_identifier, last_request_event)
```

---

## Conversation State Management

### ConversationEntity (MongoDB)

**File**: `aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py`

```python
class ConversationEntity(Document):
    meta = {
        "collection": "bot_conversations",
        "indexes": [
            {"fields": ["conversation_id", "bot_id"], "unique": True},
            {"fields": [("last_activity", 1)], "expireAfterSeconds": TTL_SECONDS}
        ]
    }

    is_mentioned = BooleanField(default=False)     # Channel mention tracking
    conversation_id = StringField(required=True)   # From Activity.conversation.id
    bot_id = StringField(required=True)            # From Activity.recipient.id
    messages = ListField(EmbeddedDocumentField(Message))
    last_activity = DateTimeField()                # Auto-refreshed, drives TTL
```

### TTL (Time-to-Live)

- **Default**: 30 days
- **Configurable**: `BotRunner(conversation_ttl_days=60)`
- **MongoDB TTL index** on `last_activity` field — auto-deletes expired conversations
- **Updated** on each interaction via `ConversationEntity.update_ttl_index()`

### ConversationTracker

**Purpose**: Distinguish between TTL expiration vs explicit deletion.

```python
class ConversationTracker(Document):
    conversation_id: str
    bot_id: str
    explicitly_deleted: bool = False  # True when user deleted in Teams

# Usage:
ConversationTracker.should_show_expiration_message(conversation_id, bot_id)
# Returns True only if: tracker exists AND not explicitly deleted AND ConversationEntity is gone
```

### Message Model

```python
class Message(EmbeddedDocument):
    user_id = StringField(required=True)
    content = ListField(EmbeddedDocumentField(Content))
    role = StringField(required=True)     # "user", "bot", "system"
    name = StringField(required=True)

class Content(EmbeddedDocument):
    text = StringField(required=True)     # Plain text or data URL
    type = StringField(required=True)     # "text" or "image_url"
```

---

## Content Extraction

**File**: `aihub_bot/aihub_bot/bots/chat/ContentExtractor.py`

Extracts content from Azure Bot Framework Activity objects:

```python
ContentExtractor.extract_content_from_activity(path, activity) -> list[Content]
# Sources:
# 1. activity.text → Content(text=text, type="text")
# 2. Slack file attachments → download via SlackUtils → Content(text=data_url, type="image_url")
# 3. Bot Framework attachments → Content based on content_type
```

**Supported types**:
- Text → `Content(type="text")`
- Images → `Content(type="image_url")` with base64 data URL
- Text files → `Content(type="text")` with `<file name='...'>content</file>` wrapper

---

## NATS Integration

### Startup (Lifetime Manager)

**File**: `aihub_bot/aihub_bot/runners/lifetime/lifetime_manager.py`

```python
# 1. Connect to MongoDB
connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING)

# 2. Connect to NATS + JetStream
nc = await NatsSettings.create_client()
js = nc.jetstream()

# 3. Start Bot-in-the-Loop subscriber (listens to ALL agent events)
bot_in_the_loop_subscriber = AgentNCSubscriber.for_all_agent_events(
    nc=nc, topic_manager=AgentTopicManager(),
    handler=bot_in_the_loop_handler.handle_event
)
await bot_in_the_loop_subscriber.start()

# 4. Create ExternalAgentEventDistributor (for publishing events to agents)
external_agent_event_distributor = ExternalAgentEventDistributor(nc=nc, js=js)

# 5. Store in app.state for FastAPI dependency injection
app.state.nc = nc
app.state.external_agent_event_distributor = external_agent_event_distributor
```

### Event Flow: Bot → Agent → Bot

```
Bot sends user message:
  ChatService.start_stream_chat_interaction()
    → Publishes StartInteractionEvent to JetStream
    → Subject: agent.{class}.{id}.thread.{tid}.control

Agent processes and responds:
  Agent emits ChunkEvent (display) + StopEvent (control+display)
    → Subject: agent.{class}.{id}.thread.{tid}.display.{did}

Bot receives response:
  ExternalAgentEventDistributor creates temporary subscriber
    → Listens on: agent.{class}.{id}.thread.{tid}.display.{did}
    → Queues ChunkEvents → response_generator yields to bot
    → StopEvent triggers stop_signal
```

---

## Streaming Responses

**File**: `CompletionHandler.send_response_stream()`

### How It Works

1. **First chunk** → `turn_context.send_activity(text)` — creates initial message
2. **Subsequent chunks** → `turn_context.update_activity(activity)` — updates in-place
3. **Message too long** → catches `msg_too_long` error → starts new message
4. **Throttling** → updates sent as fast as the previous `update_activity` completes (asyncio task)

### Typing Indicator

```python
# Runs in background while waiting for response
async def send_typing_activity(turn_context, signal, t, timeout_seconds=60):
    for _ in range(timeout_seconds // 2):
        if signal.is_set(): break
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))
        await asyncio.sleep(2)  # Send every 2 seconds
    if not signal.is_set():
        # Timeout! Send error message
        await turn_context.send_activity(t("bot.error.response_timeout"))
```

---

## CloudAdapter Caching

**File**: `aihub_bot/aihub_bot/routes/RoutesService.py`

```python
class RoutesService(ChatService):
    _adapter_cache: dict[str, CloudAdapter] = {}

    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        if path in cache: return cache[path]
        credentials = PathEntity.get_credentials_by_path(path)
        connection_manager = MsalConnectionManager({"SERVICE_CONNECTION": {
            "auth_type": AuthTypes.client_secret,
            "client_id": credentials.APP_ID,
            "client_secret": credentials.APP_PASSWORD,
            "scopes": ["https://api.botframework.com/.default"],
            "tenant_id": credentials.APP_TENANTID,  # if single-tenant
        }})
        adapter = CloudAdapter(connection_manager=connection_manager)
        cache[path] = adapter
        return adapter
```

---

## Bot Endpoint Routes

| Controller | Route | Bot Class |
|-----------|-------|-----------|
| `AgentChatController` | `/agent/chat/completions/{class}/{id}/json` | `AgentChatBot` |
| `AgentChatController` | `/agent/chat/completions/{class}/{id}/stream` | `StreamAgentChatBot` |
| `OpenaiChatController` | `/openai/chat/completions/json` | `OpenaiChatBot` |
| `OpenaiChatController` | `/openai/chat/completions/stream` | `StreamOpenaiChatBot` |
| `BotInTheLoopController` | `/bot_in_the_loop/response` | `BotInTheLoopBot` |

---

## Testing

### Test Runners

| Runner | File | Purpose |
|--------|------|---------|
| `BotRunner` | `runners/BotRunner.py` | Production server |
| `BotTestRunner` | `runners/BotTestRunner.py` | Test server (no NATS) |
| `SimulatedAgentBotTestRunner` | `runners/SimulatedAgentBotTestRunner.py` | Mocked agent responses |

### SimulatedAgentBotTestRunner

```python
runner = SimulatedAgentBotTestRunner(agent_class="test_agent", agent_id="test_id")
runner.with_simple_chunk_events()  # Mock: agent responds with predefined chunks
runner.responses  # Captured bot responses for assertions
```

### Test Pattern

```python
@pytest.mark.asyncio
async def test_send_message(test_runner, client, patch_requests_adapter, setup_test_credentials):
    with open("user_message.json") as f:
        payload = json.load(f)
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["recipient"]["id"] = BOT_ID

    response = await client.post(JSON_ENDPOINT, json=payload)

    assert response.status_code == 200
    assert test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."
```

### Bot Framework Emulator

1. Download: https://github.com/microsoft/BotFramework-Emulator
2. Start test server: `cd playground/testing && poetry run python main.py`
3. Connect to: `http://localhost:8000/api/v1/messages`
4. Leave App ID/Password empty for local testing

### Test Files

```
playground/testing/tests/
├── test_ChatBot.py          # Bot message handling tests
├── test_ConversationTTL.py  # TTL expiration tests
├── user_message.json        # Sample Activity payload
└── conversation_update.json # Sample ConversationUpdate payload
```

---

## PathEntity Configuration

**File**: `aihub_bot/aihub_bot/persistence/entities/PathEntity.py`

```python
class PathEntity(Document):
    meta = {"collection": "bot_paths", "indexes": [{"fields": ["path"], "unique": True}]}

    path = StringField(required=True)                     # API endpoint path
    credentials = EmbeddedDocumentField(Credentials)      # Azure AD creds
    system_message = StringField(required=False)          # LLM instructions
    slack_token = StringField(required=False)             # Slack OAuth token

class Credentials(EmbeddedDocument):
    APP_TYPE = StringField()      # "SingleTenant" or "MultiTenant"
    APP_ID = StringField()        # Azure AD App ID
    APP_PASSWORD = StringField()  # Azure AD Client Secret
    APP_TENANTID = StringField()  # Tenant ID (None for multi-tenant)
```

---

## Key Files Reference

### Bot Implementations
| File | Purpose |
|------|---------|
| `aihub_bot/aihub_bot/bots/chat/BaseChatBot.py` | Base bot class |
| `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py` | Handler interface + utilities |
| `aihub_bot/aihub_bot/bots/chat/ContentExtractor.py` | Extract text/files from Activity |
| `aihub_bot/aihub_bot/bots/chat/agent/AgentChatBot.py` | Agent-based chat bot |
| `aihub_bot/aihub_bot/bots/chat/agent/AgentCompletionHandler.py` | Agent completion via NATS |
| `aihub_bot/aihub_bot/bots/chat/agent/StreamAgentChatBot.py` | Streaming agent chat bot |
| `aihub_bot/aihub_bot/bots/chat/openai/OpenaiChatBot.py` | Direct LLM chat bot |
| `aihub_bot/aihub_bot/bots/chat/openai/OpenaiCompletionHandler.py` | Direct LLM completion |

### HITL
| File | Purpose |
|------|---------|
| `aihub_bot/aihub_bot/bots/bot_in_the_loop/BotInTheLoopBot.py` | Inbound: human → agent |
| `aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py` | Outbound: agent → channel |
| `aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopController.py` | HTTP endpoint |
| `aihub_bot/aihub_bot/routes/bot_in_the_loop/SlackUtils.py` | Slack API utilities |

### Persistence
| File | Purpose |
|------|---------|
| `aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py` | Conversation state + TTL |
| `aihub_bot/aihub_bot/persistence/entities/PathEntity.py` | Bot credentials + config |

### Infrastructure
| File | Purpose |
|------|---------|
| `aihub_bot/aihub_bot/routes/RoutesService.py` | CloudAdapter caching |
| `aihub_bot/aihub_bot/routes/agent/AgentChatController.py` | Agent chat endpoints |
| `aihub_bot/aihub_bot/routes/openai/OpenaiChatController.py` | OpenAI chat endpoints |
| `aihub_bot/aihub_bot/runners/lifetime/lifetime_manager.py` | NATS + MongoDB startup |
| `aihub_bot/aihub_bot/runners/BotRunner.py` | Production runner |
| `aihub_bot/aihub_bot/setup_azure_bot.py` | Azure Bot provisioning |
| `aihub_bot/aihub_bot/add_path_entity.py` | PathEntity CLI |

### Testing
| File | Purpose |
|------|---------|
| `aihub_bot/aihub_bot/runners/BotTestRunner.py` | Test runner |
| `aihub_bot/aihub_bot/runners/SimulatedAgentBotTestRunner.py` | Mocked agent runner |
| `aihub_bot/playground/testing/main.py` | Local test server |
| `aihub_bot/playground/testing/tests/test_ChatBot.py` | Bot message tests |
