# aihub_bot - Bot Integration Platform

**Purpose**: Connects users to AI-Hub agents via MS Teams, Slack, and web chat. Three parts: the SDK framework
(`aihub_bot/`), production entry point (`app/`), and playground (`playground/`). Agent logic lives in `aihub_agent` —
bots only handle conversation management, channel-specific formatting, and streaming. Built on the `microsoft-agents-*`
SDK (v0.5.0).

## Folder Structure

```
aihub_bot/                              # SDK framework
├── bots/
│   ├── chat/
│   │   ├── BaseChatBot.py              # Core base: conversation lifecycle, routing, error handling
│   │   ├── CompletionHandler.py        # Strategy base + shared static utilities (channel handling, streaming, CRUD)
│   │   ├── ContentExtractor.py         # Multi-channel file/text extraction (Slack, Teams, generic)
│   │   ├── agent/
│   │   │   ├── AgentChatBot.py         # NATS-based agent chat (non-streaming)
│   │   │   ├── AgentCompletionHandler.py  # Agent completion via ChatService + NATS events
│   │   │   └── StreamAgentChatBot.py   # Streaming variant (disabled for webchat)
│   │   └── openai/
│   │       ├── OpenaiChatBot.py        # Direct LLM chat via LiteLLM (non-streaming)
│   │       ├── OpenaiCompletionHandler.py  # OpenAI completion via LiteLLMService
│   │       └── StreamOpenaiChatBot.py  # Streaming variant (disabled for webchat)
│   └── bot_in_the_loop/
│       └── BotInTheLoopBot.py          # Inbound handler: human replies from Slack/Teams threads
├── persistence/entities/
│   ├── ConversationEntity.py           # MongoDB: conversation history + TTL + ConversationTracker
│   └── PathEntity.py                   # MongoDB: per-endpoint credentials + system message + Slack token
├── routes/
│   ├── RoutesService.py                # CloudAdapter factory (cached), path resolution, credential lookup
│   ├── agent/AgentChatController.py    # POST /completions/{class}/{id}/{json|stream}
│   ├── openai/OpenaiChatController.py  # POST /completions/{json|stream}?model_name=
│   └── bot_in_the_loop/
│       ├── BotInTheLoopController.py   # POST /bot_in_the_loop/response
│       ├── BotInTheLoopHandler.py      # Outbound: sends agent questions to Slack/Teams channels
│       └── SlackUtils.py              # Slack auth.test API wrapper (cached 30d)
├── runners/
│   ├── BotRunner.py                    # Production ASGI runner (Gunicorn/uvicorn)
│   ├── BotTestRunner.py               # Test runner with /service catch-all for response capture
│   ├── SimulatedAgentBotTestRunner.py  # Test runner with fake NATS agent (discovery + events)
│   └── lifetime/lifetime_manager.py    # FastAPI lifespan: MongoDB + NATS + BITL subscription
├── add_path_entity.py                  # CLI script to seed PathEntity to MongoDB
└── setup_azure_bot.py                  # Azure AD app registration + Bot resource creation

app/main.py                             # Production entry point (Gunicorn: app.main:app)

playground/
├── development/main.py                 # Full dev server (BotTestRunner, real NATS, 60-day TTL)
└── testing/
    ├── main.py                         # Simulated agent test server + static web UI
    ├── frontend/                       # Bot Framework Emulator web UI
    └── tests/                          # pytest tests (test_ChatBot, test_ConversationTTL)
```

## Architecture

Three-layer design:

1. **Routes**: FastAPI controllers receive Bot Framework webhook calls. `RoutesService.get_adapter(path)` creates a
   cached `CloudAdapter` per endpoint using `PathEntity` credentials. Controllers use fluent API:
   `AgentChatController(auth=auth).completions_json().completions_stream()`

2. **Bots**: `BaseChatBot(ActivityHandler)` handles the full message lifecycle. Specialized bots add channel/agent
   integration: `AgentChatBot` (NATS), `OpenaiChatBot` (direct LLM). Streaming variants (`StreamAgentChatBot`,
   `StreamOpenaiChatBot`) override `on_message_activity` to enable streaming. `BotInTheLoopBot` handles inbound BITL
   replies (extends `ActivityHandler` directly, not `BaseChatBot`).

3. **Completions**: `CompletionHandler` strategy pattern. `AgentCompletionHandler` delegates to `ChatService` (NATS
   pub/sub) while `OpenaiCompletionHandler` calls LiteLLM directly. Both implement `get_completion(**kwargs)` and
   `get_stream_completion(**kwargs)`.

## PathEntity (Per-Endpoint Configuration)

Every bot endpoint is keyed by its URL path in MongoDB `bot_paths` collection. This is the central config mechanism.

- `path` (unique index) — the API path (e.g., `/api/v1/agent/chat/completions/RAGAgent/rag-hr/json`)
- `credentials` — `APP_TYPE`, `APP_ID`, `APP_PASSWORD`, `APP_TENANTID` (Azure Bot Service auth)
- `system_message` — optional text prepended to every conversation (supports `{username}`, `{assistant_name}` placeholders)
- `slack_token` — OAuth token for Slack API calls (file downloads, `auth.test`)

`RoutesService.get_adapter(path)` reads credentials → creates `MsalConnectionManager` → caches `CloudAdapter` by path.

Created via `setup_azure_bot.py` (full Azure AD registration) or `add_path_entity.py` (manual seed for dev).

## BaseChatBot Message Pipeline

`on_message_activity()` → `_process_message(is_streaming)`:

1. Check conversation expiry (`ConversationTracker.should_show_expiration_message()`)
2. Extract content via `ContentExtractor.extract_content_from_activity()` (handles Slack files with Bearer auth, Teams
   attachments via downloadUrl, text/HTML)
3. Channel-specific handling: `CompletionHandler.handle_slack_message()` (thread detection, mention tracking) or
   `handle_teams_message()` (channel vs DM filtering)
4. Persist user message to `ConversationEntity`
5. Start typing indicator task (parallel `asyncio.Task`, sends `ActivityTypes.typing` every 2s)
6. `_respond()` → streaming or non-streaming path
7. Stop typing indicator, persist bot reply

## Channel-Specific Behavior

**MS Teams**:

- Conversation reuse: Teams reuses conversation IDs. On `on_conversation_update_activity` (bot re-added), delete
  `ConversationEntity` + mark `ConversationTracker` as explicitly deleted.
- User identity: `aad_object_id` as user ID, email/role via `TeamsConnectorClient.get_conversation_member`

**Slack**:

- Conversation ID format: `BotID:TeamID:ChannelID[:timestamp]`. The `BotID:TeamID:` prefix is stripped before MongoDB
  storage (`_clean_conversation_id()`).
- Thread detection: `conversation.conversation_type == "channel"` + `thread_ts` in conversation ID
- Mention tracking: `is_mentioned` flag on `ConversationEntity`
- Markdown conversion: `**text**` → `*text*`, `[text](url)` → `<url|text>`

**Web Chat**:

- No streaming support. `StreamAgentChatBot`/`StreamOpenaiChatBot` fall back to non-streaming when
  `channel_id == "webchat"` (webchat doesn't support Activity updates).

## Streaming Responses

`CompletionHandler.send_response_stream(turn_context, response_generator)`:

1. `get_stream_completion()` returns `AsyncGenerator[str]` (from NATS chunk queue or OpenAI stream)
2. First chunk: `send_activity(buffer)` creates initial message, captures `activity.id`
3. Subsequent chunks: accumulate in buffer, `update_activity(activity)` updates message in-place
4. On `msg_too_long` error: splits response, sends overflow as new Activity
5. Typing indicator: parallel task with configurable `typing_timeout_seconds` (default 60)

## Bot-in-the-Loop (BITL)

Human expert escalation flow — an agent pauses, asks a human via Slack/Teams, then resumes:

1. Agent publishes `BotInTheLoopRequestEvent` (carries `SlackConfig` or `TeamsConfig` with channel details)
2. `BotInTheLoopHandler` (subscribed at startup via `AgentNCSubscriber.for_all_agent_events`) receives request
3. Handler sends question proactively to Slack/Teams channel using `adapter.continue_conversation()`
4. Handler stores `BotInTheLoopThread` in `threads` dict (maps `thread_id` → `{base_conversation_id, thread_identifier}`)
5. Human replies in Slack thread or Teams thread reply
6. `BotInTheLoopBot` (via `POST /bot_in_the_loop/response`) receives reply, matches to thread in registry
7. Bot publishes `BotInTheLoopResponseEvent` via `ExternalAgentEventDistributor` → agent workflow resumes

Slack IDs cached via `TTLCache(maxsize=100, ttl=30d)` from `SlackUtils.get_slack_ids()` (`auth.test` API).

## Conversation Management

**ConversationEntity** (MongoDB `bot_conversations`, unique on `(conversation_id, bot_id)`):

- Fields: `conversation_id`, `bot_id`, `messages` (list of `Message(user_id, content, role, name)`), `last_activity`,
  `is_mentioned`
- TTL index on `last_activity` — set at startup via `ConversationEntity.update_ttl_index(days)`, configurable via
  `BotRunner(conversation_ttl_days=30)`

**ConversationTracker** (MongoDB `bot_conversation_trackers`):

- Distinguishes TTL-expired conversations from explicitly deleted (Teams re-add)
- `should_show_expiration_message()`: True only when TTL expired (not explicitly deleted)

## Lifetime Manager (Startup Sequence)

`runners/lifetime/lifetime_manager.py` — FastAPI `asynccontextmanager` lifespan:

1. MongoDB connect (`MongoSettings`)
2. TTL index on `ConversationEntity`
3. NATS connect + JetStream
4. Create `BotInTheLoopHandler` + subscribe via `AgentNCSubscriber.for_all_agent_events`
5. Create `ExternalAgentEventDistributor`
6. Store all in `app.state` (`nc`, `js`, `bot_in_the_loop_handler`, `external_agent_event_distributor`)
7. Shutdown: stop subscriber, disconnect MongoDB, close NATS

## Testing

Tests live in `playground/testing/tests/` (NOT a top-level `tests/` dir). Plain pytest — no BDD features.

**Runners**:

- `BotTestRunner`: Extends `BotRunner` with `/service{full_path:path}` catch-all that captures Bot Framework outbound
  calls into `self.responses: list[BotServiceResponse]`
- `SimulatedAgentBotTestRunner`: Extends `BotTestRunner`. Connects to real NATS, subscribes to discovery + control
  events, publishes simulated `ChunkEvent`/`LLMCostEvent`/`StopEvent` on `StartEvent`.
  `with_simple_chunk_events()` builder method populates default simulated events.

**Test fixtures** (`conftest.py`):

- `mock_msal_auth`: Patches `MsalAuth.get_access_token` → prevents Azure AD calls
- `mock_aiohttp_requests`: Patches `aiohttp.ClientSession.{post,get,put}` → captures outbound bot messages
- `ASGIAdapter` from `aihub_lib.testing` routes Bot Framework HTTP callbacks to test app

**Test markers**: `flaky` (streaming tests with polling), `azure` (requires Azure credentials)

## Playground

- `playground/development/` — Full dev server with `BotTestRunner` + all controllers (real NATS, 60-day TTL).
  Run: `cd playground/development && python main.py`
- `playground/testing/` — Simulated agent test server with `SimulatedAgentBotTestRunner` + static web UI.
  Run: `cd playground/testing && python main.py`
- Bot Framework Emulator: Connect to `http://localhost:8001/api/v1/messages`, leave App ID/Password empty

## i18n

No `BotLocaleString` — all locale resolution via `aihub_lib.i18n.LocaleHandler`. Bot reads
`turn_context.activity.locale`. Translation keys (`bot.error.*`) live in `aihub_lib`.

## Deployment

- Bot runs **locally outside Docker** (not in `docker-compose.dev.yml`)
- Production: `make run-prod` → Gunicorn on port 8001 (`app.main:app`)
- Azure DevTunnel exposes local bot → Azure Bot Service for real channel testing
- Azure setup: `setup_azure_bot.py` creates AD app registration + Bot resource + stores credentials in MongoDB

## New Bot Checklist

1. Create bot class extending `BaseChatBot` (or `AgentChatBot` / `OpenaiChatBot`)
2. Create `CompletionHandler` subclass implementing `get_completion()` / `get_stream_completion()`
3. Create controller with fluent route registration
4. Register controller in `app/main.py` via `runner.mount()`
5. Create `PathEntity` for the endpoint credentials (`add_path_entity.py`)
6. Write tests using `BotTestRunner` or `SimulatedAgentBotTestRunner`
7. Run `make test`

## Essential Files

**Bot layer**:

- Base bot: `aihub_bot/bots/chat/BaseChatBot.py`
- Completion handler: `aihub_bot/bots/chat/CompletionHandler.py`
- Content extractor: `aihub_bot/bots/chat/ContentExtractor.py`
- Agent bot: `aihub_bot/bots/chat/agent/AgentChatBot.py`
- Agent completion: `aihub_bot/bots/chat/agent/AgentCompletionHandler.py`
- Stream agent bot: `aihub_bot/bots/chat/agent/StreamAgentChatBot.py`
- OpenAI bot: `aihub_bot/bots/chat/openai/OpenaiChatBot.py`
- OpenAI completion: `aihub_bot/bots/chat/openai/OpenaiCompletionHandler.py`
- Stream OpenAI bot: `aihub_bot/bots/chat/openai/StreamOpenaiChatBot.py`
- BITL bot: `aihub_bot/bots/bot_in_the_loop/BotInTheLoopBot.py`

**Routes**:

- Routes service: `aihub_bot/routes/RoutesService.py`
- Agent controller: `aihub_bot/routes/agent/AgentChatController.py`
- OpenAI controller: `aihub_bot/routes/openai/OpenaiChatController.py`
- BITL controller: `aihub_bot/routes/bot_in_the_loop/BotInTheLoopController.py`
- BITL handler: `aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py`
- Slack utils: `aihub_bot/routes/bot_in_the_loop/SlackUtils.py`

**Persistence**:

- Conversation entity: `aihub_bot/persistence/entities/ConversationEntity.py`
- Path entity: `aihub_bot/persistence/entities/PathEntity.py`

**Runners**:

- Bot runner: `aihub_bot/runners/BotRunner.py`
- Test runner: `aihub_bot/runners/BotTestRunner.py`
- Simulated agent runner: `aihub_bot/runners/SimulatedAgentBotTestRunner.py`
- Lifetime manager: `aihub_bot/runners/lifetime/lifetime_manager.py`

**Entry points**:

- Production: `app/main.py`
- Development: `playground/development/main.py`
- Testing: `playground/testing/main.py`

**From aihub_lib**:

- Event distributor: `aihub_lib/nats/distributor/ExternalAgentEventDistributor.py`
- Chat service: `aihub_lib/routes/chat/ChatService.py`
- BITL request event: `aihub_lib/nats/events/bot_in_the_loop/request/BotInTheLoopRequestEvent.py`
- BITL response event: `aihub_lib/nats/events/bot_in_the_loop/response/BotInTheLoopResponseEvent.py`
- Agent NC subscriber: `aihub_lib/nats/subscribers/agent/AgentNCSubscriber.py`
