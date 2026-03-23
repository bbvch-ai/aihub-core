---
name: scaffold-bot-handler
description: Scaffold a new bot conversation handler in packages/bot following the BaseChatBot + CompletionHandler strategy pattern. Generates ChatBot subclass, streaming variant, CompletionHandler, Controller with fluent builder, and registers in app/main.py. Use when user says "create a bot handler", "scaffold bot handler", "new chat bot", "add bot type", "generate bot integration", "build a chatbot for X", or "add bot handler". Do NOT use for bot connection setup and Azure registration (use setup-bot-connection), bot architecture questions (use bot-framework), or agent debugging (use debug-agent).
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Scaffold a New Bot Handler

Generate a new bot handler following the strategy pattern. The bot purpose should be provided via `$ARGUMENTS`.

## Step 1: Read Reference Materials

1. Read the bot scope guide: `packages/bot/CLAUDE.md`
2. Study the agent bot variant (the primary reference implementation):
   - Bot: `packages/bot/swiss_ai_hub/bot/bots/chat/agent/AgentChatBot.py`
   - Stream: `packages/bot/swiss_ai_hub/bot/bots/chat/agent/StreamAgentChatBot.py`
   - Handler: `packages/bot/swiss_ai_hub/bot/bots/chat/agent/AgentCompletionHandler.py`
   - Controller: `packages/bot/swiss_ai_hub/bot/routes/agent/AgentChatController.py`
3. Also study the OpenAI variant for a simpler example (no NATS):
   - Bot: `packages/bot/swiss_ai_hub/bot/bots/chat/openai/OpenaiChatBot.py`
   - Handler: `packages/bot/swiss_ai_hub/bot/bots/chat/openai/OpenaiCompletionHandler.py`
   - Controller: `packages/bot/swiss_ai_hub/bot/routes/openai/OpenaiChatController.py`
4. Read base classes:
   - `packages/bot/swiss_ai_hub/bot/bots/chat/BaseChatBot.py`
   - `packages/bot/swiss_ai_hub/bot/bots/chat/CompletionHandler.py`
5. Extract the bot name from `$ARGUMENTS` and derive `CamelCase` for class names

## Architecture: Strategy Pattern

```
Controller (HTTP layer, fluent builder)
    |
    v
ChatBot (BaseChatBot subclass — constructor-only wiring)
    |
    v
CompletionHandler (strategy — implements get_completion / get_stream_completion)
    |
    v
External service (NATS agent, LiteLLM, custom API, etc.)
```

- **BaseChatBot** handles the full message lifecycle (typing, persistence, channel-specific filtering)
- **CompletionHandler** is the strategy object — subclasses implement the actual response generation
- **Controller** creates bot instances per request and delegates to `CloudAdapter.process()`
- **No config files** — per-endpoint credentials come from `PathEntity` in MongoDB (`bot_paths` collection)
- **No formatter files** — channel handling is built into `BaseChatBot` and `CompletionHandler` utilities

## Step 2: Create Directory Structure

```
packages/bot/swiss_ai_hub/bot/bots/chat/<bot_name>/
├── __init__.py
├── <Name>ChatBot.py              # BaseChatBot subclass (constructor-only)
├── Stream<Name>ChatBot.py        # Streaming variant (one-method override)
└── <Name>CompletionHandler.py    # CompletionHandler strategy

packages/bot/swiss_ai_hub/bot/routes/<bot_name>/
├── __init__.py
└── <Name>ChatController.py       # Controller with fluent builder
```

## Step 3: Create CompletionHandler

File: `packages/bot/swiss_ai_hub/bot/bots/chat/<bot_name>/<Name>CompletionHandler.py`

This is where the actual response generation logic lives. All methods are `@staticmethod`.

```python
from collections.abc import AsyncGenerator

from swiss_ai_hub.bot.bots.chat.CompletionHandler import CompletionHandler


class <Name>CompletionHandler(CompletionHandler):
    """Completion strategy for <name> bot."""

    @staticmethod
    async def get_completion(
        turn_context,
        path: str,
        # ... your custom kwargs (passed via handler_kwargs)
        **kwargs,
    ) -> str:
        """Non-streaming response. Return the full response string."""
        # 1. Get conversation history (inherited utility):
        #    messages = CompletionHandler.get_messages_by_conversation_id(conversation_id, bot_id)
        # 2. Get system message (inherited utility):
        #    system_msg = CompletionHandler.get_system_message(turn_context, path)
        # 3. Call your external service and return the response text
        raise NotImplementedError

    @staticmethod
    async def get_stream_completion(
        turn_context,
        path: str,
        # ... your custom kwargs
        **kwargs,
    ) -> AsyncGenerator[str]:
        """Streaming response. Yield response chunks as strings."""
        raise NotImplementedError
```

**Inherited utilities from `CompletionHandler`** (use freely — no need to reimplement):

- `get_system_message(turn_context, path)` — resolves system message from PathEntity, substitutes `{username}` /
  `{assistant_name}`
- `handle_teams_message(turn_context)` — filters channel messages where bot wasn't mentioned
- `handle_slack_message(turn_context)` — Slack threading and mention handling
- `add_user_message_to_conversation(path, turn_context)` — persists user turn to MongoDB
- `add_bot_message_to_conversation(path, turn_context, message)` — persists bot reply
- `get_messages_by_conversation_id(conversation_id, bot_id)` — retrieves conversation history
- `send_response_stream(turn_context, response_generator)` — streams chunks via Activity updates
- `handle_exception(turn_context, exception, ...)` — error handling (override if needed)

## Step 4: Create ChatBot

File: `packages/bot/swiss_ai_hub/bot/bots/chat/<bot_name>/<Name>ChatBot.py`

Bot classes are constructor-only — they wire the CompletionHandler and forward custom kwargs. `BaseChatBot` handles the
full message lifecycle.

```python
from swiss_ai_hub.bot.bots.chat.BaseChatBot import BaseChatBot
from swiss_ai_hub.bot.bots.chat.<bot_name>.<Name>CompletionHandler import <Name>CompletionHandler


class <Name>ChatBot(BaseChatBot):
    """<Name> chat bot — non-streaming variant."""

    def __init__(
        self,
        path: str,
        # ... your custom dependencies (NATS client, service instance, etc.)
        typing_timeout_seconds: int = 60,
    ):
        super().__init__(
            path=path,
            completion_handler=<Name>CompletionHandler(),
            handler_kwargs={
                # These kwargs are forwarded to get_completion() / get_stream_completion()
                # Example: "nc": nc, "model_name": model_name
            },
            typing_timeout_seconds=typing_timeout_seconds,
        )
```

See `AgentChatBot.py` (29 lines) and `OpenaiChatBot.py` for real examples — they are just constructor wiring.

## Step 5: Create Streaming Variant

File: `packages/bot/swiss_ai_hub/bot/bots/chat/<bot_name>/Stream<Name>ChatBot.py`

The streaming variant overrides one method. Webchat doesn't support Activity updates, so it falls back to non-streaming.

```python
from microsoft_agents.connector.models import Channels
from typing import override

from swiss_ai_hub.bot.bots.chat.<bot_name>.<Name>ChatBot import <Name>ChatBot


class Stream<Name>ChatBot(<Name>ChatBot):
    """<Name> chat bot — streaming variant."""

    @override
    async def on_message_activity(self, turn_context):
        if turn_context.activity.channel_id == Channels.webchat:
            await super().on_message_activity(turn_context)
        else:
            await self._process_message(turn_context, is_streaming=True)
```

This is typically ~15 lines. See `StreamAgentChatBot.py` and `StreamOpenaiChatBot.py`.

## Step 6: Create Controller

File: `packages/bot/swiss_ai_hub/bot/routes/<bot_name>/<Name>ChatController.py`

Controllers use the fluent builder pattern — each method registers a route and returns `Self`.

```python
from typing import Self

from swiss_ai_hub.core.auth.dependencies.AuthHandler import AuthHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.routes.Controller import Controller
from fastapi import Request, Response

from swiss_ai_hub.bot.bots.chat.<bot_name>.<Name>ChatBot import <Name>ChatBot
from swiss_ai_hub.bot.bots.chat.<bot_name>.Stream<Name>ChatBot import Stream<Name>ChatBot
from swiss_ai_hub.bot.routes.RoutesService import RoutesService


class <Name>ChatController(Controller):
    """Controller for <name> chat endpoints."""

    name = LocaleString(en="<Name> Chat")
    description = LocaleString(en="Chat with <name>")
    icon = "mage:chat"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/<bot_name>/chat",
        additionally_required_permission: str | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def completions_json(self, route: str = "/completions/json") -> Self:
        @self.router.post(route, tags=self.tags)
        async def completions_json(request: Request) -> Response:
            """Non-streaming <name> chat completion."""
            return await self._process_request(request, bot_class=<Name>ChatBot)
        return self

    def completions_stream(self, route: str = "/completions/stream") -> Self:
        @self.router.post(route, tags=self.tags)
        async def completions_stream(request: Request) -> Response:
            """Streaming <name> chat completion."""
            return await self._process_request(request, bot_class=Stream<Name>ChatBot)
        return self

    @staticmethod
    async def _process_request(request: Request, bot_class: type) -> Response:
        path = RoutesService.get_path(request)
        chat_bot = bot_class(path=path)  # Add your custom dependencies here
        adapter = RoutesService.get_adapter(path)
        return await adapter.process(request, chat_bot)
```

Adapt the route methods based on your bot's URL pattern. See `AgentChatController.py` (path params for
agent_class/agent_id) vs `OpenaiChatController.py` (query param for model_name).

## Step 7: Register in app/main.py

Edit `packages/bot/app/main.py` — add your controller to `runner.mount()`:

```python
from swiss_ai_hub.bot.routes.<bot_name>.<Name>ChatController import <Name>ChatController

runner.mount(
    # ... existing controllers ...
    <Name>ChatController(auth=auth).completions_json().completions_stream(),
)
```

## Step 8: Seed PathEntity

Create a PathEntity for your endpoint via `packages/bot/swiss_ai_hub/bot/add_path_entity.py`, or use
`setup_azure_bot.py` for full Azure registration. See the `setup-bot-connection` skill for details.

## Step 9: Create Tests

File: `packages/bot/playground/testing/tests/test_<Name>Bot.py`

Follow the patterns in `playground/testing/tests/test_ChatBot.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from swiss_ai_hub.bot.persistence.entities.PathEntity import PathEntity
from swiss_ai_hub.bot.runners.BotTestRunner import BotTestRunner
# Or SimulatedAgentBotTestRunner for NATS-based bots


@pytest.fixture(scope="module")
def setup_test_credentials():
    """Seed PathEntity for test endpoints."""
    # Create PathEntity with test credentials
    # Clean up after tests
    ...


@pytest.mark.asyncio
async def test_<name>_json_completion(setup_test_credentials, captured_responses):
    runner = BotTestRunner()
    runner.mount(<Name>ChatController(auth=auth).completions_json())
    app = runner.create_app()

    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        response = await client.post(
            "/api/v1/<bot_name>/chat/completions/json",
            json={...},  # Bot Framework Activity JSON
        )
    assert response.status_code == 200
```

Key test fixtures from `conftest.py`:

- `mock_msal_auth` (autouse) — prevents Azure AD HTTP calls
- `captured_responses` — captures outbound bot messages
- `mock_aiohttp_requests` (autouse) — patches aiohttp to capture sent Activities

## Step 10: Verify

1. Confirm imports work:
   ```bash
   cd packages/bot && uv run python -c "from swiss_ai_hub.bot.bots.chat.<bot_name>.<Name>ChatBot import <Name>ChatBot"
   cd packages/bot && uv run python -c "from swiss_ai_hub.bot.routes.<bot_name>.<Name>ChatController import <Name>ChatController"
   ```
2. Confirm controller is mounted in `packages/bot/app/main.py`
3. Run tests: `cd packages/bot && make test`

## Examples

**Input**: `$ARGUMENTS = "faq"` — A bot that answers FAQ questions via a custom knowledge API

**Expected output files**:

- `packages/bot/swiss_ai_hub/bot/bots/chat/faq/FaqChatBot.py` — `FaqChatBot(BaseChatBot)`, constructor-only
- `packages/bot/swiss_ai_hub/bot/bots/chat/faq/StreamFaqChatBot.py` — `StreamFaqChatBot(FaqChatBot)`, one-method
  override
- `packages/bot/swiss_ai_hub/bot/bots/chat/faq/FaqCompletionHandler.py` — `FaqCompletionHandler(CompletionHandler)`,
  implements `get_completion` / `get_stream_completion`
- `packages/bot/swiss_ai_hub/bot/routes/faq/FaqChatController.py` — `FaqChatController(Controller)`, fluent builder
- Registration in `packages/bot/app/main.py`: `FaqChatController(auth=auth).completions_json().completions_stream()`
- `packages/bot/playground/testing/tests/test_FaqBot.py`

## Troubleshooting

| Symptom                          | Likely Cause                                             | Fix                                                          |
| -------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------ |
| "No credentials found for path"  | PathEntity missing in MongoDB                            | Seed via `add_path_entity.py` or `setup_azure_bot.py`        |
| Bot doesn't respond              | Controller not mounted in `app/main.py`                  | Add to `runner.mount()` with fluent methods chained          |
| `NotImplementedError` at runtime | `get_completion`/`get_stream_completion` not implemented | Implement both methods in your CompletionHandler             |
| Webchat streaming broken         | Missing webchat fallback in Stream variant               | Override `on_message_activity` with `Channels.webchat` check |
| Conversation not persisted       | Not calling inherited `add_*_message_to_conversation`    | BaseChatBot handles this — don't override `_process_message` |
