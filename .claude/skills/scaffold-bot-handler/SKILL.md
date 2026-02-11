---
name: scaffold-bot-handler
description: Scaffold a new bot conversation handler for MS Teams or Slack.
  Generates ChatBot subclass with completion handler and conversation management.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Bot Handler

Generate boilerplate for a new bot conversation handler. The bot type/purpose should be provided via `$ARGUMENTS`.

## Before You Start

Read the bot scope guide: `/home/user/aihub-core/aihub_bot/AGENTS.md`

Study existing bot handlers for reference patterns.

## What to Generate

### 1. File Structure

Create in `aihub_bot/aihub_bot/bots/<bot_name>/`:

```
<bot_name>/
├── __init__.py
├── bot.py            # ChatBot subclass
├── handler.py        # CompletionHandler for response generation
├── formatter.py      # Channel-specific message formatting
└── config.py         # Bot configuration
```

### 2. ChatBot Class (`bot.py`)

- Extend `BaseChatBot`
- Handle incoming messages from the bot platform
- Manage conversation context
- Route to appropriate completion handler

### 3. Completion Handler (`handler.py`)

- Process user messages
- Interact with agents via NATS events
- Stream responses back to the user
- Handle errors gracefully

### 4. Message Formatter (`formatter.py`)

- Format responses for the target platform (Teams Adaptive Cards, Slack Blocks, etc.)
- Handle rich content (images, tables, code blocks)
- Manage message length limits

### 5. Configuration (`config.py`)

- Bot authentication settings
- Channel-specific configuration
- Conversation TTL settings
- Agent routing configuration

### 6. Webhook Route

Register webhook endpoint in the API for receiving bot platform callbacks.

### 7. Tests

Create in `aihub_bot/tests/bots/<bot_name>/`:
- `test_<bot_name>.py` — Unit tests using BotTestRunner
- Test message handling, formatting, and error cases

## Key Patterns

- **BaseChatBot**: All bots extend the base class
- **CompletionHandler**: Separated from bot routing logic
- **ConversationEntity**: TTL-managed conversation state
- **Platform-agnostic core**: Business logic separate from platform formatting
- **MSAL auth**: Azure AD authentication for Teams bots
