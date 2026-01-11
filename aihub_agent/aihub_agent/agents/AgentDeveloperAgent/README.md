# AgentDeveloperAgent

**Meta-agent that enables developers to build AI agents through chat interface by proxying requests to OpenCode servers.**

---

## Overview

The AgentDeveloperAgent acts as a bridge between users in OpenWebUI and OpenCode servers running in agent development containers. Instead of manually connecting to OpenCode via CLI or VS Code, developers can simply chat with this agent to build new AI agents.

### Architecture

```
User (OpenWebUI) → AgentDeveloperAgent → OpenCode Server → Creates Agent Files
                                            ↓
                                    /workspace/agent/ (Container)
                                            ↓
                                    ./agents/<name>/ (Host)
```

---

## Features

✅ **Chat-based agent development** - Build agents through natural language
✅ **Session persistence** - Multi-turn conversations within same thread
✅ **Real-time updates** - See file creation and tool execution progress
✅ **Error handling** - Graceful error messages with troubleshooting tips
✅ **Multiple OpenCode servers** - Route to different dev containers
✅ **Configurable** - Control verbosity, timeouts, models

---

## Configuration

### Required Fields

```python
from aihub_agent.agents.AgentDeveloperAgent import AgentDeveloperAgentConfig

config = AgentDeveloperAgentConfig(
    agent_class="AgentDeveloperAgent",
    agent_id="agent-builder-1",

    # REQUIRED: OpenCode server URL
    opencode_server_url="http://agent-1-dev:8080",
)
```

### Optional Fields

```python
config = AgentDeveloperAgentConfig(
    agent_class="AgentDeveloperAgent",
    agent_id="agent-builder-1",
    opencode_server_url="http://agent-1-dev:8080",

    # Timeouts
    opencode_timeout=300,  # 5 minutes (default)

    # Model configuration
    model_id="claude-3-5-sonnet-20241022",  # Default: Claude Sonnet
    provider_id="anthropic",  # Default: Anthropic

    # Initialization
    initialization_prompt="Custom system prompt...",  # Default: Swiss AI-Hub conventions

    # Response formatting
    show_file_changes=True,  # Show ✅ Created: file.py (default: True)
    show_tool_calls=True,     # Show ✅ Completed: pytest (default: True)
    verbose_output=False,     # Show detailed info (default: False)
)
```

---

## Usage

### 1. Start OpenCode Dev Container

```bash
# Start agent dev environment
docker-compose -f docker-compose.agent-dev.yml up -d agent-1-dev

# Verify OpenCode server is running
docker exec -it agent-1-dev ps aux | grep opencode
```

### 2. Register Agent in OpenWebUI

**Via Admin UI:**

Navigate to **Admin Settings → Agents → Add Agent**

**Configuration JSON:**
```json
{
  "agent_class": "AgentDeveloperAgent",
  "agent_id": "agent-builder-1",
  "opencode_server_url": "http://agent-1-dev:8080",
  "opencode_timeout": 300,
  "model_id": "claude-3-5-sonnet-20241022",
  "provider_id": "anthropic",
  "show_file_changes": true,
  "show_tool_calls": true,
  "verbose_output": false
}
```

### 3. Chat with Agent

**Open OpenWebUI** and select "Agent Builder" from the agent dropdown.

**Example conversation:**

**You:**
```
Build a legal RAG agent with the following requirements:
- Retrieve from Milvus 'legal_docs' index
- Track citations with document IDs
- Add confidence scoring
- Create comprehensive tests
```

**Agent:**
```
🤖 Forwarding to OpenCode server...

Your request: Build a legal RAG agent with...

✅ Created: `LegalRAGAgent/LegalRAGAgent.py`
✅ Created: `LegalRAGAgent/configs/LegalRAGAgentConfig.py`
✅ Created: `LegalRAGAgent/events/CitationEvent.py`
✅ Created: `tests/test_legal_rag.py`
✅ Created: `tests/features/legal_rag.feature`
✅ Completed: `poetry install`
✅ Completed: `make pr-ready`
✅ Completed: `make test`

Your agent is ready at /workspace/agent/LegalRAGAgent/
All tests passing! ✓
```

### 4. Multi-Turn Conversation

The agent maintains session state across messages:

**You:**
```
Add reranking to improve relevance
```

**Agent:**
```
✅ Modified: `LegalRAGAgent/LegalRAGAgent.py`
✅ Created: `LegalRAGAgent/configs/RerankingConfig.py`
✅ Completed: `make test`

Reranking added successfully!
```

---

## How It Works

### Session Management

1. **First message:** Creates new OpenCode session, stores ID in ThreadContext
2. **Subsequent messages:** Reuses same session ID from ThreadContext
3. **Session initialization:** Sends system prompt with Swiss AI-Hub conventions
4. **Persistence:** Session survives across multiple messages

### Event Flow

```python
UserMessageEvent (from chat)
    ↓
AgentDeveloperAgent.proxy_to_opencode_step()
    ↓
OpenCode SDK: client.session.chat(message)
    ↓
OpenCode Server (processes request)
    ↓
AssistantMessage (parts: text, files, tools)
    ↓
_convert_response_to_events()
    ↓
list[ChunkEvent, StopEvent]
    ↓
Swiss AI-Hub Dispatcher
    ↓
OpenWebUI (user sees updates)
```

### Response Part Conversion

| OpenCode Part | ChunkEvent Output |
|--------------|------------------|
| `TextPart` | AI's textual response |
| `FilePart` | `✅ Created: file.py` |
| `ToolPart` (completed) | `✅ Completed: pytest` |
| `ToolPart` (error) | `❌ Failed: pytest` |
| `SnapshotPart` | (hidden unless verbose) |

---

## Advanced Usage

### Multiple OpenCode Servers

Run multiple agent instances, each connected to different dev containers:

**Agent 1: Legal agent development**
```json
{
  "agent_class": "AgentDeveloperAgent",
  "agent_id": "legal-builder",
  "opencode_server_url": "http://agent-2-dev:8080"
}
```

**Agent 2: Product agent development**
```json
{
  "agent_class": "AgentDeveloperAgent",
  "agent_id": "product-builder",
  "opencode_server_url": "http://agent-3-dev:8080"
}
```

This allows parallel agent development across teams!

### Custom System Prompt

Override the default initialization prompt:

```python
config = AgentDeveloperAgentConfig(
    # ...
    initialization_prompt="""You are an AI agent builder for custom domain.

Follow these patterns:
- Pattern 1
- Pattern 2

Read documentation at /workspace/CUSTOM_GUIDE.md"""
)
```

### Verbose Output

See detailed OpenCode events:

```python
config = AgentDeveloperAgentConfig(
    # ...
    verbose_output=True  # Shows file previews, tool outputs
)
```

**Output with verbose=True:**
```
✅ Created: `MyAgent.py`
```python
from aihub_agent.agents.Agent import Agent

class MyAgent(Agent):
    @step()
    async def my_step(self, ...
```

✅ Completed: `pytest`
```
===== test session starts =====
collected 5 items
tests/test_my_agent.py .....
===== 5 passed in 2.31s =====
```
```

---

## Troubleshooting

### "Cannot connect to OpenCode server"

**Problem:** Agent can't reach OpenCode server

**Solutions:**

1. **Check if container is running:**
   ```bash
   docker ps | grep agent-dev
   ```

2. **Check if OpenCode server is running:**
   ```bash
   docker exec -it agent-1-dev ps aux | grep opencode
   ```

3. **Verify URL:**
   - ✅ Correct: `http://agent-1-dev:8080` (container name)
   - ✅ Correct: `http://localhost:8080` (if on same host)
   - ❌ Wrong: `http://localhost:8443` (that's VS Code port)

4. **Check container logs:**
   ```bash
   docker logs agent-1-dev
   ```

5. **Restart container:**
   ```bash
   docker-compose -f docker-compose.agent-dev.yml restart agent-1-dev
   ```

### "Rate limit exceeded"

**Problem:** Too many requests to OpenCode server

**Solution:** Wait a moment and try again. OpenCode uses underlying model providers (Anthropic, OpenAI) which have rate limits.

### "Session not found"

**Problem:** OpenCode session expired or was deleted

**Solution:** Start a new conversation in OpenWebUI. This creates a fresh OpenCode session.

### Files not appearing on host

**Problem:** Agent says files created, but you don't see them

**Solutions:**

1. **Check volume mount:**
   ```bash
   docker inspect agent-1-dev | grep -A 5 Mounts
   # Should show: ./agents/agent-1 → /workspace/agent
   ```

2. **Check inside container:**
   ```bash
   docker exec -it agent-1-dev ls -la /workspace/agent/
   ```

3. **Verify file path:**
   Files are at `./agents/agent-1/` on host (relative to docker-compose.yml)

---

## Testing

### Unit Tests

```bash
cd /home/user/aihub-core/aihub_agent
poetry shell

# Run all tests
pytest tests/test_agent_developer_agent.py -v

# Run specific test
pytest tests/test_agent_developer_agent.py::test_agent_developer_agent_basic -v
```

### Manual Testing

1. **Start OpenCode dev container:**
   ```bash
   docker-compose -f docker-compose.agent-dev.yml up -d agent-1-dev
   ```

2. **Use trigger script:**
   ```bash
   cd /home/user/aihub-core/aihub_agent/aihub_agent/agents/AgentDeveloperAgent
   python trigger.py
   ```

3. **Test via OpenWebUI:**
   - Register agent (see Usage section)
   - Open chat
   - Send test message

---

## Implementation Details

### Dependencies

- **`opencode-ai`**: Python SDK for OpenCode server
- **`aiohttp`**: Async HTTP client (better concurrency)

### Key Methods

| Method | Purpose |
|--------|---------|
| `proxy_to_opencode_step()` | Main step that proxies messages |
| `_get_or_create_session()` | Manages OpenCode session lifecycle |
| `_convert_response_to_events()` | Converts OpenCode parts to ChunkEvents |
| `_format_file_change()` | Formats file creation/modification |
| `_format_tool_call()` | Formats tool execution |

### ThreadContext Keys

| Key | Type | Purpose |
|-----|------|---------|
| `opencode_session_id` | `str` | OpenCode session ID for this conversation |

---

## Future Enhancements

1. **True Streaming (SSE)** - Use `client.event.list()` for real-time updates
2. **File Preview** - Show code snippets with syntax highlighting
3. **Interactive Refinement** - Multi-turn iterative development
4. **Agent Templates** - Pre-built patterns for common agent types
5. **Multi-Agent Orchestration** - Route to different servers based on intent

---

## Related Documentation

- **OpenCode Python SDK**: https://pypi.org/project/opencode-ai/
- **OpenCode Server**: https://opencode.ai/docs/server/
- **Agent Development Guide**: `/home/user/aihub-core/AI_AGENT_BUILD_AND_DEPLOY_GUIDE.md`
- **Agent Dev Environment**: `/home/user/aihub-core/AGENT_DEV_SETUP.md`

---

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review OpenCode server logs: `docker logs agent-1-dev`
3. Report issues: https://github.com/bbvch-ai/aihub-core/issues
