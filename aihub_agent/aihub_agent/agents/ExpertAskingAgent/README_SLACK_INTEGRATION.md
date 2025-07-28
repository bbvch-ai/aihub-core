# Slack Direct API Integration for Expert Agents

This document describes the direct Slack Web API integration for the Expert Asking Agent and Expert Grounded Agent, replacing the previous Bot Framework dependency.

## Overview

The Expert Asking Agent now uses the official Slack Web API directly via HTTPS calls, eliminating the dependency on Microsoft Bot Framework. This provides:

- **Direct API Access**: Uses `https://slack.com/api/` endpoints directly
- **Simplified Authentication**: OAuth 2.0 bearer tokens only
- **Thread Support**: Maintains conversation threading for follow-up questions
- **Response Polling**: Polls for expert responses with configurable timeouts
- **Error Handling**: Comprehensive error handling for API failures

## Architecture Changes

### New Components

1. **SlackDirectClient** - Direct Slack Web API client
2. **SlackResponsePoller** - Polls for responses in threads
3. **SlackMessagePostedEvent** - Event for successful message posting
4. **SlackResponseReceivedEvent** - Event for received responses

### Modified Components

1. **ExpertAskingAgent** - Updated workflow steps for direct API calls
2. **ExpertAskingAgentConfig** - Added `slack_token` field
3. **Translation files** - Added new thought messages

## Configuration

### Expert Asking Agent Config

```python
class ExpertAskingAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig | GeminiLLMConfig | OpenaiLikeLLMConfig
    slack_channel_id: str  # Channel ID (e.g., "C1234567890")
    slack_token: str       # Bot token (e.g., "xoxb-...")
    loop_max: int = 3
    open_webui_knowledge_id: str
    open_webui_api_key: str  
    open_webui_api_url: str
```

### Required Slack Scopes

The Slack bot token must have these OAuth scopes:

- `chat:write` - Post messages to channels
- `chat:write.public` - Post to public channels  
- `conversations:history` - Read channel history
- `conversations:read` - Access channel info
- `users:read` - Get user information

## Workflow Changes

### Previous Flow (Bot Framework)
1. Post question via BotInTheLoop.request
2. Wait for BotInTheLoop.response  
3. Process expert response

### New Flow (Direct API)
1. Post question via SlackDirectClient.post_message
2. Poll for responses via SlackResponsePoller.wait_for_response
3. Process expert response from SlackResponseReceivedEvent

## New Agent Steps

### 1. Post to Slack Step
- **Purpose**: Posts question directly to Slack channel
- **Input**: AskExpertStartEvent | AskExpertEvent
- **Output**: SlackMessagePostedEvent
- **Features**: Thread support for follow-up questions

### 2. Wait for Slack Response Step  
- **Purpose**: Polls for expert responses
- **Input**: SlackMessagePostedEvent
- **Output**: SlackResponseReceivedEvent
- **Features**: 5-minute timeout, multi-response handling

### 3. Expert Response Step (Modified)
- **Purpose**: Processes expert responses  
- **Input**: SlackResponseReceivedEvent
- **Output**: RouterEvent (sufficient/insufficient)
- **Features**: Same LLM evaluation logic

## API Integration Details

### Message Posting
```python
# Post message to channel
response = await slack_client.post_message(
    channel="C1234567890",
    text="What is the best approach for...",
    thread_ts="1234567890.123456"  # Optional for threading
)
```

### Response Polling
```python
# Poll for responses in thread
poller = SlackResponsePoller(slack_client)
responses = await poller.wait_for_response(
    channel="C1234567890", 
    message_ts="1234567890.123456",
    timeout=300  # 5 minutes
)
```

## Error Handling

### Network Errors
- HTTP connection failures
- Slack API rate limiting
- Invalid channel/token errors

### Response Handling
- No response timeout (5 minutes)
- Empty responses
- Bot message filtering

### Fallback Behavior
- Timeout returns empty response → triggers insufficient answer flow
- API errors bubble up as exceptions
- Retry mechanisms for transient failures

## Thread Management

### Initial Questions
- Creates new thread with message timestamp
- Stores `thread_ts` in RunContext for follow-ups

### Follow-up Questions  
- Uses stored `thread_ts` for threading
- Maintains conversation context
- Supports unlimited follow-ups (within loop_max)

## Testing

### Unit Tests
Run the integration test:
```bash
cd aihub_agent/agents/ExpertAskingAgent/
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_TEST_CHANNEL="C1234567890" 
python test_slack_integration.py
```

### Integration Tests
1. Configure agent with valid Slack credentials
2. Deploy agent with test configuration
3. Send test question through agent workflow
4. Verify Slack message posting and response handling

## Migration Guide

### From Bot Framework to Direct API

1. **Update Configuration**:
   ```python
   # Add slack_token field
   slack_token: str = "xoxb-your-bot-token"
   ```

2. **Update Scopes**:
   - Ensure bot has required OAuth scopes
   - Test API access with new token

3. **Deploy Changes**:
   - Deploy updated agent code
   - Update agent configurations  
   - Test with real Slack channels

### Backward Compatibility
- No breaking changes to agent interfaces
- Same input/output event types for consumers
- Expert Grounded Agent works unchanged

## Security Considerations

- **Token Storage**: Store Slack tokens securely (environment vars, secrets management)
- **Channel Access**: Bot only accesses configured channels
- **User Privacy**: Respects Slack workspace privacy settings
- **Rate Limiting**: Implements proper API rate limiting

## Monitoring & Observability

### Metrics to Track
- Message posting success/failure rates
- Response polling timeouts
- API error rates by type
- Average response times from experts

### Logging
- Slack API calls and responses
- Polling iterations and timeouts
- Expert response processing
- Error conditions and retries

## Limitations

1. **Polling Based**: Uses polling instead of real-time webhooks
2. **Single Response**: Takes first response only (could be enhanced)
3. **No Rich Formatting**: Plain text messages only
4. **Timeout Fixed**: 5-minute response timeout (configurable in code)

## Future Enhancements

1. **Webhook Support**: Replace polling with Slack Events API
2. **Rich Messages**: Support Block Kit formatting
3. **Multi-Response**: Handle multiple expert responses
4. **Reaction Support**: Use emoji reactions for response validation
5. **File Attachments**: Support file uploads and downloads