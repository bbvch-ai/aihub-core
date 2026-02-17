---
name: debug-bot
description: >-
  Troubleshoot bot integration issues with Teams, Slack, and Web Chat. Use when user says 'bot not
  responding', 'Teams bot broken', 'Slack bot error', '401 from bot', 'HITL not working', 'bot
  timeout', 'conversation expired', 'streaming stuck', 'bot can't reach agent', or 'Slack thread
  lost'. Covers auth, NATS connectivity, channel-specific issues, and conversation state.
arguments:
  - name: issue
    description: Description of the bot issue (e.g., "bot not responding in Teams", "Slack thread not working", "HITL timeout", "auth 401 error")
allowed-tools: Read, Grep, Glob, Bash
---

# Bot Debugging Assistant

Investigate the bot issue described via `$ARGUMENTS`.

## Step 0: Read Scope Documentation

Read `/home/user/aihub-core/aihub_bot/CLAUDE.md` to understand bot architecture and patterns.

---

## Step 1: Identify the Symptom Category

Match the reported issue to one of these categories and jump to the relevant section:

| Symptom                             | Section                                          |
| ----------------------------------- | ------------------------------------------------ |
| Bot doesn't respond at all          | [Connection & Auth](#connection--auth-issues)    |
| Bot responds with error message     | [Error Messages](#error-messages)                |
| Bot responds but agent doesn't work | [NATS & Agent Issues](#nats--agent-issues)       |
| Slack-specific problems             | [Slack Issues](#slack-issues)                    |
| Teams-specific problems             | [Teams Issues](#teams-issues)                    |
| Bot-in-the-loop not working         | [HITL Issues](#hitl-issues)                      |
| Streaming not updating              | [Streaming Issues](#streaming-issues)            |
| Conversation history lost/expired   | [Conversation State](#conversation-state-issues) |

---

## Connection & Auth Issues

### "No credentials found for path"

**Cause**: PathEntity missing or path mismatch.

**Diagnose**:

```python
# Check MongoDB for PathEntity
# File: aihub_bot/aihub_bot/persistence/entities/PathEntity.py
PathEntity.get_credentials_by_path(path)  # Returns None if missing
```

**Fix**:

1. Check the exact URL path the request is hitting (logged in AgentChatController)
2. Verify PathEntity exists in `bot_paths` collection with matching `path` field
3. The path must match **exactly** including query params (e.g., `?model_name=...`)
4. Use `aihub_bot/aihub_bot/add_path_entity.py` to add it

### 401 Unauthorized from Azure Bot Service

**Cause**: Invalid or expired Azure AD credentials.

**Diagnose**:

1. Check CloudAdapter creation in `RoutesService.get_adapter()`:
   - File: `aihub_bot/aihub_bot/routes/RoutesService.py`
2. Check credentials stored in PathEntity match Azure AD App Registration

**Fix**:

```bash
# Regenerate credentials
az ad app credential reset --id <APP_ID>
# Update APP_PASSWORD in MongoDB bot_paths collection
```

### CloudAdapter cached with stale credentials

**Cause**: `RoutesService._adapter_cache` holds old CloudAdapter after credential rotation.

**Fix**: Restart the bot service (adapters are cached in memory, not persisted).

### Bot service unreachable

**Diagnose**:

```bash
# Check if bot service is running
docker compose -f docker-compose.dev.yml ps | grep bot

# Check bot logs
docker compose -f docker-compose.dev.yml logs aihub_bot --tail=100

# Check if endpoint is reachable
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/agent/chat/completions/test/test/json
```

**Fix**:

- Verify port 8001 is exposed and not blocked
- Check gunicorn/uvicorn startup in logs
- For DevTunnel: verify tunnel is active and port matches (8001)

---

## Error Messages

### "bot.error.response_timeout" (typing timeout)

**Cause**: Agent didn't respond within `typing_timeout_seconds` (default 60s).

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py` (line ~310)

**Diagnose**:

1. Check if the agent is running and processing events
2. Check NATS connectivity between bot and agent
3. Check agent logs for errors or slow LLM calls

**Fix**:

- Increase `typing_timeout_seconds` in controller: `completions_json(typing_timeout_seconds=120)`
- Check agent is subscribed to correct NATS subjects
- Check LLM endpoint is responsive

### "bot.error.generic_error"

**Cause**: Unhandled exception in CompletionHandler.

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py` (line ~327)

**Diagnose**: Check bot logs for the full exception traceback — the error is logged with `logger.exception()`.

### "No response from the agent."

**Cause**: Stream response generator yielded nothing.

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py` (line ~271)

**Diagnose**: Agent started but produced no ChunkEvents before StopEvent.

---

## NATS & Agent Issues

### Agent not receiving messages

**Diagnose**:

```
File: aihub_bot/aihub_bot/runners/lifetime/lifetime_manager.py

1. Check NATS connection: nc = await NatsSettings.create_client()
2. Check ExternalAgentEventDistributor is initialized
3. Verify agent is subscribed to: agent.{agent_class}.{agent_id}.thread.*.display.*
```

**Common causes**:

- NATS server not running: `docker compose -f docker-compose.dev.yml ps nats`
- Agent service not running (aihub_agent container)
- Wrong agent_class or agent_id in endpoint URL
- JetStream stream not created for agent class

### Agent responds but bot doesn't forward

**Cause**: `ExternalAgentEventDistributor` subscriber not receiving display events.

**Diagnose**:

1. Check the display_id and thread_id are correctly derived from conversation_id:
   - `thread_id = str_to_object_id(conversation_id)` (BaseChatBot line ~152)
   - `display_id = str_to_object_id(activity.id)` (BaseChatBot line ~153)
2. Check if ChunkEvents are being published on the expected subject
3. Check if StopEvent / ExceptionEvent is received

### ExceptionEvent from agent

**Cause**: Agent threw an error during processing.

**Diagnose**: Check `resources.stop_event` in AgentCompletionHandler — if it's an `ExceptionEvent`, the error message is
propagated as a `RuntimeError`.

---

## Slack Issues

### Bot not responding in Slack channels

**Cause**: Bot mention detection failed.

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py`

**How it works**: In channels, the bot only responds if:

1. Bot is **@mentioned** in the message, OR
2. The conversation is already **marked as mentioned** (ongoing thread)

**Diagnose**:

- Check `_is_bot_mentioned()` — compares `mention.mentioned.id` with `activity.recipient.id`
- Check `_is_mentioned_in_conversation()` — looks up `ConversationEntity.is_mentioned`
- For DMs: check `_is_slack_direct_message()` regex: `^B[0-9A-Z]+:T[0-9A-Z]+:D[0-9A-Z]+:\d+[.]\d+$`

### Slack thread context lost

**Cause**: Thread identifier not parsed correctly from conversation ID.

**Format**: `B[bot_id]:T[team_id]:C[channel_id]:[timestamp]`

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py` — `_update_slack_turn_context()`

**Diagnose**:

- Channel message regex: `^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+$`
- Thread messages get `:ts` appended to create thread-specific conversation ID
- Check `channel_data["SlackMessage"]["event"]["ts"]` exists in Activity

### Slack file uploads not working

**Cause**: Slack file download requires OAuth token.

**File**: `aihub_bot/aihub_bot/bots/chat/ContentExtractor.py`

**Diagnose**: Check `PathEntity.slack_token` is set for the bot's path — file downloads use this token via
`SlackUtils.download_file()`.

### Slack formatting broken

**Expected conversions** (Markdown → Slack):

- `**text**` → `*text*`
- `[text](url)` → `<url|text>`

Check the formatting logic in the CompletionHandler response chain.

---

## Teams Issues

### Teams conversation history reset unexpectedly

**Cause**: Teams reuses conversation IDs. When a user deletes and re-adds the bot, the conversation ID stays the same.

**File**: `aihub_bot/aihub_bot/bots/chat/BaseChatBot.py` — `on_conversation_update_activity()`

**How it works**:

1. `on_conversation_update_activity` detects bot re-added (`members_added` contains bot)
2. `ConversationTracker.mark_explicitly_deleted()` records this
3. `completion_handler.delete_conversation_if_exists()` wipes conversation

**Diagnose**: Check `ConversationTracker` in MongoDB for `explicitly_deleted=True`.

### "This conversation has expired after 1 month of inactivity"

**Cause**: Normal TTL expiration (30 days default).

**File**: `aihub_bot/aihub_bot/bots/chat/BaseChatBot.py` — `_process_message()`

**How it works**:

1. `ConversationTracker.should_show_expiration_message()` checks if conversation existed before but is now gone
2. If tracker exists AND not explicitly deleted AND ConversationEntity is gone → TTL expired

**Fix**: Adjust TTL via `BotRunner(conversation_ttl_days=60)`.

### Teams channel messages not getting replies

**Cause**: Same as Slack — bot only responds in channels if @mentioned or in an existing bot thread.

**File**: `CompletionHandler._is_teams_direct_message()` — checks `channel_data.get("channel") is None`

---

## HITL Issues

### Bot-in-the-loop questions not reaching Slack/Teams

**Diagnose**:

```
File: aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py

1. Check BotInTheLoopHandler subscriber is started (lifetime_manager.py)
2. Check the agent emits BotInTheLoopRequestEvent
3. Check event.channel_config has correct channel_id and service_url
4. Check PathEntity has slack_token (for Slack channels)
```

### Human response not reaching agent

**File**: `aihub_bot/aihub_bot/bots/bot_in_the_loop/BotInTheLoopBot.py`

**Diagnose**:

1. Check thread matching: `_find_matching_thread(base_conversation_id, thread_identifier)`
2. Check `BotInTheLoopHandler.threads` dict has an active entry for the thread_id
3. Check `ExternalAgentEventDistributor.distribute_event()` is called with correct thread_id

### HITL thread identifier parsing

**Slack format**:

- Base: `B[bot_id]:T[team_id]:C[channel_id]`
- With thread: `B[bot_id]:T[team_id]:C[channel_id]:[timestamp]`

**Teams format**:

- Base: `19:abc...@thread.tacv2`
- With message: `19:abc...@thread.tacv2;messageid=123`

---

## Streaming Issues

### Stream response stuck / not updating

**File**: `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py` — `send_response_stream()`

**How streaming works**:

1. First chunk → `send_activity()` (creates initial message)
2. Subsequent chunks → `update_activity()` (updates in-place)
3. Throttled by asyncio task completion (not time-based)

**Diagnose**:

- Check if first chunk arrives (if not, agent issue)
- Check if `update_activity` throws (message too long → auto-splits)
- Check `msg_too_long` error handling — creates new message when update exceeds limit

### 30-second chunk timeout

**File**: AgentCompletionHandler — `asyncio.wait_for(chunk_queue.get(), timeout=30)`

**Cause**: Agent produced no chunks for 30 seconds.

**Fix**: Check agent LLM call latency, increase timeout if needed.

---

## Conversation State Issues

### Conversation history empty

**Diagnose**:

1. Check MongoDB `bot_conversations` collection for the conversation_id + bot_id pair
2. Check TTL index: `db.bot_conversations.getIndexes()` — look for `expireAfterSeconds`
3. Check `ConversationEntity.add_messages_to_conversation()` is being called

### Messages not persisting

**File**: `aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py`

**Diagnose**:

- Check MongoDB connection: `MongoSettings.CONNECTION_STRING`
- Check `AIHubSettings.MONGO_MAIN_DB_NAME` (database name)
- Check the `bot_conversations` collection exists

---

## Diagnostic Commands

```bash
# Check all bot-related Docker services
docker compose -f docker-compose.dev.yml ps | grep -E "bot|nats|ferret"

# Check bot logs
docker compose -f docker-compose.dev.yml logs aihub_bot --tail=100

# Check NATS connectivity
docker compose -f docker-compose.dev.yml logs nats --tail=50

# Check MongoDB for PathEntity
docker compose -f docker-compose.dev.yml exec ferretdb mongosh --eval 'db.bot_paths.find().pretty()'

# Check MongoDB for conversations
docker compose -f docker-compose.dev.yml exec ferretdb mongosh --eval 'db.bot_conversations.find().pretty()'
```

---

## Key Files for Debugging

| Category               | File                                                                |
| ---------------------- | ------------------------------------------------------------------- |
| **Base bot**           | `aihub_bot/aihub_bot/bots/chat/BaseChatBot.py`                      |
| **Completion handler** | `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py`                |
| **Agent handler**      | `aihub_bot/aihub_bot/bots/chat/agent/AgentCompletionHandler.py`     |
| **Content extraction** | `aihub_bot/aihub_bot/bots/chat/ContentExtractor.py`                 |
| **HITL handler**       | `aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py` |
| **HITL bot**           | `aihub_bot/aihub_bot/bots/bot_in_the_loop/BotInTheLoopBot.py`       |
| **Routes service**     | `aihub_bot/aihub_bot/routes/RoutesService.py`                       |
| **PathEntity**         | `aihub_bot/aihub_bot/persistence/entities/PathEntity.py`            |
| **ConversationEntity** | `aihub_bot/aihub_bot/persistence/entities/ConversationEntity.py`    |
| **Lifetime manager**   | `aihub_bot/aihub_bot/runners/lifetime/lifetime_manager.py`          |
| **Agent controller**   | `aihub_bot/aihub_bot/routes/agent/AgentChatController.py`           |

---

## Summary

After investigating, provide a structured report with:

- **Symptom category**: Which section from Step 1 matched
- **Root cause**: Specific file and line responsible
- **Affected files**: All files involved in the issue
- **Recommended fix**: Specific code or configuration change

## Examples

- `/debug-bot bot not responding in Teams` -- Check PathEntity, Azure credentials, endpoint URL, NATS connectivity
- `/debug-bot Slack thread context lost` -- Check conversation ID parsing, thread timestamp extraction
- `/debug-bot HITL not working` -- Verify BotInTheLoopHandler subscriber, channel_config, Slack token
- `/debug-bot conversation expired unexpectedly` -- Check TTL settings, ConversationTracker, MongoDB TTL index
