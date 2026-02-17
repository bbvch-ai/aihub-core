---
name: scaffold-bot-handler
description: Scaffold a new bot conversation handler for MS Teams or Slack. Generates
  ChatBot subclass, completion handler, message formatter, config, and tests. Use when
  user says "create a bot", "scaffold bot handler", "new Teams bot", "add Slack bot",
  "generate bot integration", "build a chatbot for X", or "add bot handler".
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Bot Handler

Generate boilerplate for a new bot conversation handler. The bot type/purpose should be provided via `$ARGUMENTS`.

## Step 1: Read Reference Materials

1. Read the bot scope guide: `/home/user/aihub-core/aihub_bot/CLAUDE.md`
2. Study existing bot handlers in `aihub_bot/aihub_bot/bots/` for reference patterns
3. Extract the bot name and target platform (Teams/Slack) from `$ARGUMENTS`

## Step 2: Create Bot Directory Structure

Create in `aihub_bot/aihub_bot/bots/<bot_name>/`:

```
<bot_name>/
├── __init__.py
├── bot.py            # ChatBot subclass
├── handler.py        # CompletionHandler for response generation
├── formatter.py      # Channel-specific message formatting
└── config.py         # Bot configuration
```

## Step 3: Create ChatBot Class (`bot.py`)

- Extend `BaseChatBot`
- Handle incoming messages from the bot platform
- Manage conversation context
- Route to appropriate completion handler

## Step 4: Create Completion Handler (`handler.py`)

- Process user messages
- Interact with agents via NATS events
- Stream responses back to the user
- Handle errors gracefully

## Step 5: Create Message Formatter (`formatter.py`)

- Format responses for the target platform (Teams Adaptive Cards, Slack Blocks, etc.)
- Handle rich content (images, tables, code blocks)
- Manage message length limits per platform

## Step 6: Create Configuration (`config.py`)

- Bot authentication settings
- Channel-specific configuration
- Conversation TTL settings
- Agent routing configuration

## Step 7: Register Webhook Route

Register a webhook endpoint in the API for receiving bot platform callbacks.

## Step 8: Create Tests

Create in `aihub_bot/tests/bots/<bot_name>/`:
- `test_<bot_name>.py` -- Unit tests using BotTestRunner
- Test message handling, formatting, and error cases

## Key Patterns

- **BaseChatBot**: All bots extend the base class
- **CompletionHandler**: Separated from bot routing logic
- **ConversationEntity**: TTL-managed conversation state
- **Platform-agnostic core**: Business logic separate from platform formatting
- **MSAL auth**: Azure AD authentication for Teams bots

## Examples

**Input**: `$ARGUMENTS = "teams_support_bot - A Teams bot that routes support questions to the FAQ agent"`
**Expected output files**:
- `aihub_bot/aihub_bot/bots/teams_support_bot/bot.py` with class `TeamsSupportBot(BaseChatBot)`
- `aihub_bot/aihub_bot/bots/teams_support_bot/handler.py` with `TeamsSupportCompletionHandler`
- `aihub_bot/aihub_bot/bots/teams_support_bot/formatter.py` with Teams Adaptive Card formatting
- `aihub_bot/aihub_bot/bots/teams_support_bot/config.py` with auth and routing config
- `aihub_bot/tests/bots/teams_support_bot/test_teams_support_bot.py`

## Troubleshooting

- **Bot not receiving messages**: Verify the webhook endpoint is registered and the bot platform's messaging endpoint URL is correct
- **MSAL auth failures**: Ensure Azure AD app registration credentials are configured in `.env` and match the bot channel registration
- **Conversation state lost**: Check ConversationEntity TTL settings -- conversations expire after the configured timeout
- **NATS connection issues**: Verify NATS is running and the bot can publish/subscribe to agent event topics
- **Message formatting errors**: Test formatting separately -- Teams Adaptive Cards and Slack Blocks have different structure requirements
