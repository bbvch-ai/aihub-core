---
name: bot-framework
description: "Comprehensive reference for the bot integration framework (aihub_bot): handler architecture, CompletionHandler pattern, multi-channel handling (Teams, Slack, WebChat), BITL flow, conversation state, NATS integration, streaming, and testing. Use when user says 'how does the bot work', 'CompletionHandler pattern', 'bot architecture', 'Slack thread handling', 'BITL flow', 'bot streaming', 'conversation state management', 'bot testing', 'how do bot channels work', 'BaseChatBot', 'bot framework', 'bot handler', 'bot completion', or 'bot routes'. Do NOT use for bot setup/provisioning (use setup-bot-connection), bot debugging (use debug-bot), or scaffolding new handlers (use scaffold-bot-handler). Covers all bot components, request flow, and testing patterns."
allowed-tools: Read, Grep, Glob
---

# Bot Integration Framework Reference

Look up bot framework architecture, patterns, and implementation details. Topic or question via `$ARGUMENTS` (e.g.,
"CompletionHandler", "Slack threads", "BITL flow", "streaming", "testing", "conversation state", "handler pattern",
"routes").

---

## Architecture Overview

The **aihub_bot** scope provides chatbot logic for MS Teams, Slack, and Web Chat, connecting users to AI-Hub agents via
conversational interfaces.

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

**WebChat fallback**: Streaming variants (`StreamAgentChatBot`, `StreamOpenaiChatBot`) detect WebChat channel and fall
back to non-streaming (`super().on_message_activity()`). Note: `StreamAgentChatBot` uses `Channels.webchat` (enum) while
`StreamOpenaiChatBot` uses the string literal `"webchat"`.

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
   ├─ ConversationTracker.should_show_expiration_message()  # TTL check
   ├─ ConversationTracker.track_conversation()
   ├─ CompletionHandler.add_user_message_to_conversation()  # Persists BEFORE filtering
   ├─ handle_slack_message() / handle_teams_message()  # Returns None → early return if ignored
   ├─ typing_task = send_typing_activity()  # Background, every 2s
   └─ response = await _respond()
       └─ CompletionHandler.get_completion() → NATS → Agent → response
5. CompletionHandler.add_bot_message_to_conversation()
6. Return to Azure Bot Service → Channel → User
```

---

## CompletionHandler Pattern (Strategy)

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py`

The CompletionHandler is the **core abstraction** for generating responses. All methods are `@staticmethod`. Subclasses
override `get_completion` and `get_stream_completion` with typed parameters resolved via `handler_kwargs` in
`BaseChatBot`.

### Interface

```python
class CompletionHandler:
    @staticmethod
    async def get_completion(**kwargs) -> str:
        """Non-streaming: returns full response as string."""

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

| Handler                   | File                                          | Purpose                             |
| ------------------------- | --------------------------------------------- | ----------------------------------- |
| `AgentCompletionHandler`  | `bots/chat/agent/AgentCompletionHandler.py`   | NATS → Agent via ChatService        |
| `OpenaiCompletionHandler` | `bots/chat/openai/OpenaiCompletionHandler.py` | Direct LLM calls via LiteLLMService |

`OpenaiCompletionHandler` also overrides `handle_exception` to extract LiteLLM-specific error messages from
`APIStatusError`.

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
4. # JSON mode: await resources.stop_signal.wait() → subscriber.stop() → build response
5. # Stream mode: yield chunks from resources.chunk_queue (30s timeout per chunk)
```

---

## Multi-Channel Handling

All channel-specific logic is static methods on `CompletionHandler` — there are no separate `TeamsHandler` or
`SlackHandler` classes, and no channel-specific message formatters.

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
# Detects: members_added contains bot recipient + not a team channel (channel_data.get("team") is None)
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
- `_mark_conversation_as_mentioned()` persists mention state in `ConversationEntity.is_mentioned`

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

## Bot-in-the-Loop (BITL)

**Purpose**: AI agents pause execution → request human input via Slack/Teams → resume with response.

Not to be confused with HITL (Human-in-the-Loop) which refers to process tasks for humans in the process engine.

### Flow

```
1. Agent emits BotInTheLoopRequestEvent (control event)
2. BotInTheLoopHandler (subscriber) receives event
   ├─ Extracts channel_config (channel_id, service_url)
   ├─ Looks up Slack bot/team IDs via Slack API (cached 30 days on handler instance)
   ├─ Builds ConversationReference for the target channel
   └─ Sends question message to Slack/Teams channel via adapter.continue_conversation()
3. Human replies in channel/thread
4. BotInTheLoopBot (ActivityHandler, NOT BaseChatBot) receives reply
   ├─ Parses conversation_id → base_conversation_id + thread_identifier
   ├─ Matches to active BotInTheLoopHandler.threads entry
   └─ Distributes BotInTheLoopResponseEvent via ExternalAgentEventDistributor (JetStream)
5. Agent receives response → continues workflow
```

### Key Components

| Component                  | File                                               | Direction                                    |
| -------------------------- | -------------------------------------------------- | -------------------------------------------- |
| **BotInTheLoopHandler**    | `routes/bot_in_the_loop/BotInTheLoopHandler.py`    | Outbound: agent → channel                    |
| **BotInTheLoopBot**        | `bots/bot_in_the_loop/BotInTheLoopBot.py`          | Inbound: channel → agent                     |
| **BotInTheLoopController** | `routes/bot_in_the_loop/BotInTheLoopController.py` | HTTP endpoint                                |
| **SlackUtils**             | `routes/bot_in_the_loop/SlackUtils.py`             | Slack API helpers (`auth.test` → `SlackIds`) |

### Thread Tracking

```python
# BotInTheLoopHandler stores active threads — IN-MEMORY, process-local:
threads: dict[str, BotInTheLoopThread] = {}
# Key: thread_id (from agent event)
# Value: BotInTheLoopThread(thread_id, conversation_id, thread_identifier, last_request_event)
#
# WARNING: If the bot process restarts, all pending BITL threads are lost.
# Slack thread_identifier = Slack ts; Teams thread_identifier = messageid=...
```

---

## Conversation State Management

Both `ConversationEntity` and `ConversationTracker` are defined in the same file:
`aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py`

### ConversationEntity (MongoDB)

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

Distinguishes between TTL expiration vs explicit deletion (Teams conversation reset).

```python
class ConversationTracker(Document):
    conversation_id: str
    bot_id: str
    explicitly_deleted: bool = False  # True when user deleted in Teams

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
# 2. Slack file attachments → Bearer download via PathEntity.slack_token → Content(type="image_url")
# 3. Bot Framework attachments → Content based on content_type
```

**Supported types**: Text → `Content(type="text")`, Images → `Content(type="image_url")` with base64 data URL, Text
files → `Content(type="text")` with `<file name='...'>content</file>` wrapper.

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

# 3. Start BITL subscriber (listens to ALL agent events via NATS Core, ephemeral)
bot_in_the_loop_subscriber = AgentNCSubscriber.for_all_agent_events(
    nc=nc, topic_manager=AgentTopicManager(),
    handler=bot_in_the_loop_handler.handle_event
)
await bot_in_the_loop_subscriber.start()

# 4. Create ExternalAgentEventDistributor (NCPublisher + JSPublisher for publishing)
external_agent_event_distributor = ExternalAgentEventDistributor(nc=nc, js=js)

# 5. Store in app.state for FastAPI dependency injection
app.state.nc = nc
app.state.external_agent_event_distributor = external_agent_event_distributor
```

### Event Flow: Bot → Agent → Bot

```
Bot sends user message:
  ChatService.start_stream_chat_interaction()
    → Creates AgentNCSubscriber for display events BEFORE publishing (avoids race)
    → Publishes UserMessageEvent (StartEvent) via JSPublisher (JetStream, durable)
    → Subject: agent.{class}.{id}.{thread_id}.{display_id}.{run_id}.control.{event_name}.{event_id}

Agent processes and responds:
  Agent emits ChunkEvent (display) + StopEvent (control+display)
    → Subject: agent.{class}.{id}.{thread_id}.{display_id}.{run_id}.display.{event_name}.{event_id}

Bot receives response:
  AgentNCSubscriber (NATS Core, ephemeral) receives display events
    → response_aggregator pushes ChunkEvents into asyncio.Queue
    → StopEvent/ExceptionEvent sets stop_signal
    → Stream mode: generator yields from queue (30s timeout per chunk)
    → JSON mode: stop_signal.wait() then build response from collected chunks
```

---

## Streaming Responses

**File**: `CompletionHandler.send_response_stream()`

### How It Works

1. **First chunk** → `turn_context.send_activity(text)` — creates initial message
2. **Subsequent chunks** → `turn_context.update_activity(activity)` — updates in-place
3. **Message too long** → catches `msg_too_long` error → starts new message (overflow)
4. **Throttling** → updates sent as fast as the previous `update_activity` completes (asyncio task chaining)

Both Teams and Slack use the same update-in-place mechanism — the Bot Framework SDK handles the platform differences
transparently.

### Typing Indicator Lifecycle

The typing indicator runs **only while waiting for the agent to respond** — not during streaming.

1. Started as background `asyncio.Task` before `_respond()` is called
2. Sends `ActivityTypes.typing` every 2 seconds, up to `timeout_seconds // 2` iterations
3. **Stopped** (`typing_stop_signal.set()`) as soon as `get_stream_completion` returns the generator
4. During `send_response_stream`, no typing indicator is running — the user sees the message being built

If the signal is never set (agent timeout), sends `bot.error.response_timeout` localized message.

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
            "tenant_id": credentials.APP_TENANTID,
        }})
        adapter = CloudAdapter(connection_manager=connection_manager)
        cache[path] = adapter
        return adapter
```

---

## Bot Endpoint Routes

| Controller               | Route                                         | Bot Class             |
| ------------------------ | --------------------------------------------- | --------------------- |
| `AgentChatController`    | `/agent/chat/completions/{class}/{id}/json`   | `AgentChatBot`        |
| `AgentChatController`    | `/agent/chat/completions/{class}/{id}/stream` | `StreamAgentChatBot`  |
| `OpenaiChatController`   | `/openai/chat/completions/json`               | `OpenaiChatBot`       |
| `OpenaiChatController`   | `/openai/chat/completions/stream`             | `StreamOpenaiChatBot` |
| `BotInTheLoopController` | `/bot_in_the_loop/response`                   | `BotInTheLoopBot`     |

---

## PathEntity Configuration

**File**: `aihub_bot/aihub_bot/persistence/entities/PathEntity.py`

```python
class PathEntity(Document):
    meta = {"collection": "bot_paths", "indexes": [{"fields": ["path"], "unique": True}]}
    path = StringField(required=True)                     # Full URL path incl. query string
    credentials = EmbeddedDocumentField(Credentials)      # Azure AD creds
    system_message = StringField(required=False)          # LLM instructions with {placeholders}
    slack_token = StringField(required=False)             # Slack OAuth token (for file downloads)

class Credentials(EmbeddedDocument):
    APP_TYPE = StringField()      # "SingleTenant" or "MultiTenant"
    APP_ID = StringField()        # Azure AD App ID
    APP_PASSWORD = StringField()  # Azure AD Client Secret
    APP_TENANTID = StringField()  # Tenant ID (None for multi-tenant)
```

Bot credentials are stored per-path in MongoDB — not in environment variables. Routing is determined by the URL path
structure: each endpoint maps to exactly one agent via path parameters `{agent_class}/{agent_id}`.

---

## Testing

**Test location**: `aihub_bot/playground/testing/tests/` (not a top-level `tests/` directory).

### Test Runners

| Runner                        | File                                     | Purpose                                   |
| ----------------------------- | ---------------------------------------- | ----------------------------------------- |
| `BotRunner`                   | `runners/BotRunner.py`                   | Production (Gunicorn on port 8001)        |
| `BotTestRunner`               | `runners/BotTestRunner.py`               | Test server (no NATS, captures responses) |
| `SimulatedAgentBotTestRunner` | `runners/SimulatedAgentBotTestRunner.py` | Mocked agent via fake NATS                |

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

Test fixtures: `conftest.py` patches `MsalAuth.get_access_token` and `aiohttp.ClientSession` methods. Uses `ASGIAdapter`
from `aihub_lib.testing.route_adapter` to route Bot Framework outbound callbacks to the test app. Markers: `flaky`
(timing-dependent streaming), `azure` (real credentials).

### Bot Framework Emulator

1. Download: https://github.com/microsoft/BotFramework-Emulator
2. Start test server: `cd playground/testing && uv run python main.py`
3. Connect to: `http://localhost:8000/api/v1/messages`
4. Leave App ID/Password empty for local testing

---

## Key Files Reference

| File                                                                   | Purpose                                                       |
| ---------------------------------------------------------------------- | ------------------------------------------------------------- |
| `aihub_bot/aihub_bot/bots/chat/BaseChatBot.py`                         | Base bot: lifecycle, routing, error handling                  |
| `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py`                   | Strategy base: channel handling, streaming, conversation CRUD |
| `aihub_bot/aihub_bot/bots/chat/ContentExtractor.py`                    | Multi-channel file/text extraction                            |
| `aihub_bot/aihub_bot/bots/chat/agent/AgentChatBot.py`                  | Agent-based chat (non-streaming)                              |
| `aihub_bot/aihub_bot/bots/chat/agent/AgentCompletionHandler.py`        | Agent completion via NATS                                     |
| `aihub_bot/aihub_bot/bots/chat/agent/StreamAgentChatBot.py`            | Streaming agent chat                                          |
| `aihub_bot/aihub_bot/bots/chat/openai/OpenaiChatBot.py`                | Direct LLM chat (non-streaming)                               |
| `aihub_bot/aihub_bot/bots/chat/openai/OpenaiCompletionHandler.py`      | Direct LLM completion                                         |
| `aihub_bot/aihub_bot/bots/chat/openai/StreamOpenaiChatBot.py`          | Streaming direct LLM                                          |
| `aihub_bot/aihub_bot/bots/bot_in_the_loop/BotInTheLoopBot.py`          | BITL inbound: human → agent                                   |
| `aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py`    | BITL outbound: agent → channel                                |
| `aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopController.py` | BITL HTTP endpoint                                            |
| `aihub_bot/aihub_bot/routes/bot_in_the_loop/SlackUtils.py`             | Slack API helpers                                             |
| `aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py`       | ConversationEntity + ConversationTracker                      |
| `aihub_bot/aihub_bot/persistence/entities/PathEntity.py`               | Bot credentials + config                                      |
| `aihub_bot/aihub_bot/routes/RoutesService.py`                          | CloudAdapter caching                                          |
| `aihub_bot/aihub_bot/routes/agent/AgentChatController.py`              | Agent chat endpoints                                          |
| `aihub_bot/aihub_bot/routes/openai/OpenaiChatController.py`            | OpenAI chat endpoints                                         |
| `aihub_bot/aihub_bot/runners/lifetime/lifetime_manager.py`             | NATS + MongoDB startup                                        |
| `aihub_bot/aihub_bot/runners/BotRunner.py`                             | Production runner                                             |
| `aihub_bot/aihub_bot/runners/BotTestRunner.py`                         | Test runner                                                   |
| `aihub_bot/aihub_bot/runners/SimulatedAgentBotTestRunner.py`           | Mocked agent runner                                           |
| `aihub_bot/aihub_bot/setup_azure_bot.py`                               | Azure Bot provisioning                                        |
| `aihub_bot/aihub_bot/add_path_entity.py`                               | PathEntity CLI                                                |
