# Slack Message ID Issue with Microsoft Agents SDK

## Issue Summary

After migrating from `botbuilder-integration-aiohttp 4.16.2` to `microsoft-agents-hosting-core 0.5.0`, the `ResourceResponse.id` returned from `TurnContext.send_activity()` is `None` for Slack messages sent via proactive messaging (Bot-in-the-Loop pattern).

This prevents capturing the Slack message timestamp (`ts`), which is required for threading responses back to the correct message.

**Status**: Open issue with microsoft-agents SDK
**Date Discovered**: 2025-10-31
**Affected Code**: `aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py:196-202`

## Background

The Bot-in-the-Loop handler uses proactive messaging to send questions from AI agents to Slack channels. When a message is sent, we need to capture the Slack message timestamp (`ts`) to use as a thread identifier. This allows subsequent user responses to be matched back to the original question.

### Working Code (Pre-Migration)

```python
async def callback(turn_context: TurnContext):
    response = await turn_context.send_activity(question)
    if response and hasattr(response, "id") and thread.thread_identifier is None:
        thread.thread_identifier = response.id
```

This code worked with the old `botbuilder-integration-aiohttp` SDK but now returns `response.id = None` with the new `microsoft-agents` SDK.

## Root Cause Analysis

### The Response Chain

1. **`TurnContext.send_activity()`** → calls `send_activities()`
   - Location: `microsoft_agents/hosting/core/turn_context.py:210`

2. **`TurnContext.send_activities()`** → calls `adapter.send_activities()`
   - Location: `microsoft_agents/hosting/core/turn_context.py:258`

3. **`ChannelServiceAdapter.send_activities()`** → calls Azure Bot Service API
   - Location: `microsoft_agents/hosting/core/channel_service_adapter.py:103-114`
   ```python
   response = await connector_client.conversations.send_to_conversation(
       activity.conversation.id,
       activity,
   )
   ```

4. **Critical Fallback** (line 115):
   ```python
   response = response or ResourceResponse(id=activity.id or "")
   ```

### The Problem

The Azure Bot Service API endpoint (`v3/conversations/{conversation_id}/activities`) is returning a response where:
- The `id` field is either missing, `null`, or empty
- This occurs specifically for Slack proactive messages sent via `continue_conversation`

### Evidence

1. **Slack API Behavior**: Slack's `chat.postMessage` API always returns a `ts` (timestamp) field that serves as the message ID. This is essential for threading.

2. **Old SDK Documentation**: The `botbuilder-integration-aiohttp 4.16.2` documentation explicitly states: *"The SlackAdapter returns an array of ResourceResponse objects containing the IDs that Slack assigned to the sent messages."*

3. **Historical Working Code**: The original Bot-in-the-Loop implementation (commit `3c3d2161`, 2024) used identical logic to capture `response.id`, indicating the old SDK received proper IDs from Azure Bot Service.

4. **ResourceResponse Structure**: Inspection of the new SDK shows:
   ```python
   ResourceResponse.model_fields = {
       'id': FieldInfo(annotation=str, required=False, default=None, ...)
   }
   ```
   The field exists but is not being populated.

## Possible Causes

1. **Azure Bot Service API Change**: Azure Bot Service may have changed how it returns response data for Slack proactive messages (messages sent via `continue_conversation` rather than in response to user input).

2. **SDK Request Format Change**: The new `microsoft-agents` SDK might be formatting the API request differently, causing Azure Bot Service to not return the Slack message ID.

3. **Proactive Message Limitation**: Azure Bot Service may not return message IDs for proactive messages to Slack channels (only for direct user responses).

4. **SDK Regression**: The new SDK may have a bug where it's not properly parsing the response from Azure Bot Service.

## Recommended Solutions

### Option 1: Call Slack API Directly (Most Reliable)

Bypass the Azure Bot Service response and call Slack API directly to get the message timestamp:

```python
async def _bot_in_the_loop_callback(question: str, thread: BotInTheLoopThread) -> Callable:
    async def callback(turn_context: TurnContext):
        # Send through Bot Framework first
        response = await turn_context.send_activity(question)

        # If no ID returned, call Slack API directly to get the ts
        if (not response or not response.id) and thread.thread_identifier is None:
            slack_token = PathEntity.get_slack_token_by_path(self.path)
            # Parse conversation ID to get channel
            parts = turn_context.activity.conversation.id.split(":")
            channel_id = parts[2] if len(parts) > 2 else None

            if slack_token and channel_id:
                import httpx
                async with httpx.AsyncClient() as client:
                    slack_response = await client.post(
                        "https://slack.com/api/chat.postMessage",
                        headers={
                            "Authorization": f"Bearer {slack_token}",
                            "Content-Type": "application/json"
                        },
                        json={"channel": channel_id, "text": question}
                    )
                    data = slack_response.json()
                    if data.get("ok"):
                        thread.thread_identifier = data.get("ts")
                        logger.info(f"Captured Slack ts from direct API: {thread.thread_identifier}")
        elif response and hasattr(response, "id") and response.id and thread.thread_identifier is None:
            thread.thread_identifier = response.id
            logger.info(f"Captured thread identifier from Bot Framework: {thread.thread_identifier}")

    return callback
```

**Pros**:
- Most reliable, doesn't depend on Azure Bot Service
- Direct control over Slack API
- Guaranteed to get the message timestamp

**Cons**:
- Sends message twice (once through Bot Framework, once directly)
- Requires additional API call
- Need to handle Slack API errors

### Option 2: Enhanced Logging and Investigation

Add comprehensive logging to understand what's being returned:

```python
async def callback(turn_context: TurnContext):
    import logging
    logger = logging.getLogger(__name__)

    response = await turn_context.send_activity(question)

    # Log everything we can about the response
    logger.info(f"Response object: {response}")
    logger.info(f"Response type: {type(response)}")
    if response:
        logger.info(f"Response.id: {response.id}")
        logger.info(f"Response dict: {response.model_dump()}")

    # Log activity details
    logger.info(f"Activity conversation ID: {turn_context.activity.conversation.id}")
    logger.info(f"Activity channel: {turn_context.activity.channel_id}")

    # Check turn context state
    logger.info(f"Turn state keys: {turn_context.turn_state.keys()}")

    if response and hasattr(response, "id") and thread.thread_identifier is None:
        thread.thread_identifier = response.id
```

Then test with both Slack and Teams to determine if this is channel-specific.

### Option 3: Report to Microsoft

This appears to be a regression in the microsoft-agents SDK or Azure Bot Service. File an issue with:

- **Repository**: https://github.com/microsoft/botframework-sdk
- **Title**: "ResourceResponse.id is None for Slack proactive messages in microsoft-agents SDK 0.5.0"
- **Details**: Include this analysis and comparison to botbuilder-integration-aiohttp 4.16.2 behavior

## Temporary Workaround

Currently implemented in `BotInTheLoopHandler.py:199-200`:

```python
if response and hasattr(response, "id") and thread.thread_identifier is None:
    thread.thread_identifier = response.id
```

This code is safe but non-functional. The `thread.thread_identifier` will remain `None`, which means:
- First message creates a new channel conversation
- Subsequent messages in the same logical thread may create new conversations instead of threading properly
- User responses may not be matched to the correct waiting agent

## Investigation Checklist

- [ ] Test with Microsoft Teams to determine if issue is Slack-specific
- [ ] Add enhanced logging to capture actual API responses
- [ ] Check Azure Bot Service logs/telemetry for the API call
- [ ] Test with direct user reply (non-proactive) to see if IDs are returned then
- [ ] Compare network traffic between old SDK and new SDK
- [ ] File issue with Microsoft if confirmed as SDK regression
- [ ] Implement Option 1 (direct Slack API) as permanent workaround if needed

## Migration History

- **Original Implementation**: Commit `3c3d2161` (2024) - Slack Bot-in-the-Loop feature added
- **SDK Migration**: Commit `75fc6bfd` (2025-10-31) - Migrated to Microsoft 365 Agents SDK
  - Old: `botbuilder-integration-aiohttp 4.16.2`
  - New: `microsoft-agents-hosting-core 0.5.0`
- **Issue Discovered**: 2025-10-31 - Response ID no longer populated

## Related Files

- `aihub_bot/aihub_bot/routes/bot_in_the_loop/BotInTheLoopHandler.py:196-202`
- `aihub_bot/aihub_bot/bots/bot_in_the_loop/BotInTheLoopBot.py:57-68`
- SDK: `microsoft_agents/hosting/core/channel_service_adapter.py:56-119`
- SDK: `microsoft_agents/hosting/core/turn_context.py:190-211`

## References

- [Slack API - chat.postMessage](https://api.slack.com/methods/chat.postMessage)
- [Slack Threading Documentation](https://medium.com/slack-developer-blog/bringing-your-bot-into-threaded-messages-cd272a42924f)
- [Microsoft Agents SDK Migration Guide](https://www.voitanos.io/blog/microsoft-teams-sdk-evolution-2025/)
- [Bot Framework SDK Deprecation Notice](https://github.com/microsoft/botframework-sdk)