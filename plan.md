# MCP Tool Invocation — Implementation Plan

## Goal

Enable Swiss AI Hub agents to act as full MCP clients, connecting to external MCP servers (via MetaMCP gateway or
directly) to invoke tools, handle sampling requests, process elicitation, and access resources.

## Architecture

```
Agent Workflow Step
  │  declares: mcp_client: Client (from fastmcp)
  ▼
AgentDispatcher (DI)
  │  _get_parameter_value() detects Client type annotation
  │  _get_or_create_mcp_client() lazily creates + connects per run
  │  AsyncExitStack manages Client lifecycle (async with)
  │  cleanup on StopEvent / ExceptionEvent
  ▼
fastmcp.Client (direct FastMCP usage — no wrapper)
  │  Client(url) — auto-infers transport
  │  Client(url, auth=BearerAuth(...)) — with API key
  │  Client(StreamableHttpTransport(url, headers)) — custom headers
  │  list_tools(), call_tool(), list_resources(), read_resource(), etc.
  ▼
MCP Server(s)
  ├── MetaMCP Gateway (aggregates multiple servers behind one URL)
  ├── Direct MCP server (any StreamableHTTP-compatible server)
  └── ...
```

## Current Implementation (Phase 1: Tool Invocation)

### `aihub_lib/aihub_lib/mcp/McpClientConfig.py` — Connection Configuration

`McpClientConfig(StepConfig)` — injected via dispatcher StepConfig DI:

- `name` — logical name for this connection
- `url` — MCP server URL (FastMCP auto-infers transport)
- `api_key` — optional `SecretStr` for `BearerAuth`
- `headers` — optional HTTP headers (triggers explicit `StreamableHttpTransport`)
- `timeout` — client timeout in seconds (default 30s)

### `aihub_agent/aihub_agent/dispatchers/AgentDispatcher.py` — DI Wiring

Direct `fastmcp.Client` injection with per-run lifecycle:

1. **Registry**: `_mcp_clients: dict[str, McpClient]` — per-run instances keyed by `execution_context_id`
2. **Lazy DI**: When a step declares `mcp_client: Client`, the dispatcher:
   - Fetches `McpClientConfig` from `agent_config.get_step_configs()`
   - Creates `Client(url)` or `Client(transport)` depending on headers/auth
   - Enters via `AsyncExitStack.enter_async_context(client)` (proper `async with` lifecycle)
3. **Auth**: Uses `BearerAuth` from `fastmcp.client.auth` when `api_key` is set
4. **Lifecycle cleanup**: On `StopEvent` or `ExceptionEvent`, `aclose()` the exit stack

### `aihub_lib/aihub_lib/mcp/react.py` — Reusable MCP Step Functions

Shared functions in `aihub_lib` (usable by agents, processes, bots — any package):

- `to_openai_tool_schemas(tools)` — converts `list[mcp.types.Tool]` to OpenAI function-calling format
- `extract_result_text(result)` — extracts text from `CallToolResult.content` blocks
- `react_loop(mcp_client, messages, llm, displayer, model_name, max_iterations)` — full ReAct loop

### `playground/minimal_workflow/mcp_react_workflow/` — ReAct Agent Example

| File                          | Purpose                                                                |
| ----------------------------- | ---------------------------------------------------------------------- |
| `McpReactAgent.py`            | Minimal agent — delegates to `McpReactService.react_loop()`            |
| `McpReactAgentConfig.py`      | Config with `mcp: McpClientConfig`, `llm: LLMConfig`, `max_iterations` |
| `trigger.py`                  | Manual test runner                                                     |
| `tests/test_McpReactAgent.py` | BDD test with mocked MCP server and LLM                                |

### How to Add MCP to Any Agent

1. Add `McpClientConfig` to your agent config:

   ```python
   class MyAgentConfig(AgentConfig):
       mcp: Annotated[McpClientConfig, Field(description="MCP connection.")]
   ```

2. Declare `Client` (from fastmcp) in step parameters — dispatcher injects it:

   ```python
   from fastmcp import Client
   from aihub_lib.mcp.react import react_loop

   @step()
   async def my_step(self, event: UserMessageEvent, mcp_client: Client,
                     config: MyAgentConfig, displayer: EventDisplayer) -> StopEvent:
       async with config.llm.cost_reporting_llm(displayer) as llm:
           await react_loop(
               mcp_client, list(event.messages), llm, displayer,
               config.llm.model_name, config.max_iterations,
           )
       return StopEvent()
   ```

   Or use `Client` directly for custom tool logic:

   ```python
   @step()
   async def my_step(self, event: UserMessageEvent, mcp_client: Client) -> StopEvent:
       tools = await mcp_client.list_tools()
       result = await mcp_client.call_tool("search", {"query": "hello"})
       return StopEvent()
   ```

3. Configure in agent config:

   ```python
   McpClientConfig(name="my-server", url="http://metamcp:8080/mcp")
   ```

## FastMCP Alignment

The implementation uses FastMCP exactly as documented:

| FastMCP Feature          | How We Use It                                           |
| ------------------------ | ------------------------------------------------------- |
| `Client(url)` auto-infer | Default path when no custom headers                     |
| `Client(transport)`      | Only when `headers` or `api_key` are configured         |
| `async with` lifecycle   | Via `AsyncExitStack.enter_async_context(client)`        |
| `name=` param            | Passed from `McpClientConfig.name`                      |
| `timeout=` param         | Passed from `McpClientConfig.timeout`                   |
| `auth=BearerAuth(...)`   | When `api_key` is set                                   |
| `client.list_tools()`    | Returns `list[mcp.types.Tool]`                          |
| `client.call_tool()`     | Returns `fastmcp.client.client.CallToolResult`          |
| `raise_on_error=True`    | Default — errors propagate as exceptions (fail-fast)    |
| `result.content`         | Content blocks (`TextContent`, `ImageContent`, etc.)    |
| `result.data`            | Parsed structured output (when output schema available) |

## Phase 2: Sampling (MCP Server → LLM)

When an MCP server calls `sampling/createMessage`, it asks the client to generate an LLM completion. FastMCP handles
this via a `sampling_handler` callback on the Client:

```python
async def sampling_handler(
    messages: list[SamplingMessage],
    params: SamplingParams,
    context: RequestContext,
) -> str:
```

**Integration with AI-Hub**: Route through LiteLLM via `LLMConfig`:

```python
async def aihub_sampling_handler(messages, params, context) -> str:
    llm_config = LLMConfig(model_name=params.modelPreferences or "gpt-4o")
    llm, _ = llm_config.to_llama_index()
    chat_messages = [ChatMessage(role=m.role, content=m.content.text) for m in messages]
    response = await llm.achat(chat_messages)
    return str(response.message.content)
```

Pass to Client: `Client(url, sampling_handler=aihub_sampling_handler)`

**SAAP mapping**: MCP sampling ≈ inline LLM call within agent step. No event flow change needed — the handler runs
synchronously within the tool call.

## Phase 3: Elicitation (MCP Server → User)

When an MCP server sends `elicitation/create`, it asks for user input. FastMCP handles this via an
`elicitation_handler`:

```python
async def elicitation_handler(
    message: str,
    response_type: type | None,
    params: ElicitRequestParams,
    context: RequestContext,
) -> ElicitResult | object:
```

**Integration with AI-Hub**: Translate to `HumanInTheLoopRequestEvent`:

1. Elicitation handler receives request from MCP server
2. Emit `HumanInTheLoopRequestEvent` with the message/schema
3. Await `HumanInTheLoopResponseEvent` (async bridge needed — `asyncio.Event` or similar)
4. Return `ElicitResult(action="accept", content=response_type(value=user_response))`

**Challenge**: The elicitation handler is a sync callback within a tool call, but HITL is async over NATS. Need an async
bridge (e.g. `asyncio.Future`) that the handler awaits while the HITL flow runs.

**SAAP mapping**: MCP elicitation ≈ `HumanInTheLoop.request` → `HumanInTheLoop.response`.

## Phase 4: Resources, Prompts, Roots

Lower priority — extend as needed:

| MCP Feature | FastMCP API                   | AI-Hub Integration                            |
| ----------- | ----------------------------- | --------------------------------------------- |
| Resources   | `client.list_resources()`     | Feed resource content into RAG context        |
| Resources   | `client.read_resource(uri)`   | Read data from MCP servers                    |
| Prompts     | `client.list_prompts()`       | Discover available prompts                    |
| Prompts     | `client.get_prompt(name)`     | Use server-provided prompt templates          |
| Roots       | \`Client(url, roots=[...])    | Provide filesystem paths to servers           |
| Roots       | `Client(url, roots=callback)` | Dynamic root computation based on agent state |

## Definition of Done

- [x] Tool invocation working with external MCP servers
- [ ] Sampling requests from servers fulfilled via LiteLLM
- [ ] Elicitation requests translated to `HumanInTheLoop` events
- [x] MCP client injectable into agent steps via dispatcher
- [x] `McpClientConfig` added as `StepConfig` for declarative server access
- [x] MetaMCP gateway supported (any URL works — FastMCP auto-infers transport)
- [ ] OTEL tracing spans for MCP client calls
- [x] Example agent using external MCP tools in `playground/`
- [ ] Documentation with examples for common MCP server integrations

## Key Design Decisions

1. **Direct `fastmcp.Client` injection** — no wrapper layer. Steps get the real FastMCP Client, with full access to
   `list_tools()`, `call_tool()`, `list_resources()`, `read_resource()`, `list_prompts()`, `get_prompt()`. Future-proof
   — when we add sampling/elicitation handlers, the same Client is extended with callbacks.
2. **Lazy connect** — only connects when a step actually requests `Client`, not on every run start
3. **Per-run lifecycle** — matches `RunContext` lifecycle; cleanup on stop/exception
4. **`AsyncExitStack`** — proper `async with` lifecycle management as required by FastMCP
5. **No transport config** — FastMCP auto-infers; only explicit transport for custom headers
6. **`BearerAuth`** — FastMCP's built-in auth helper for API keys

## Files on This Branch

| File                                                          | Change                                          |
| ------------------------------------------------------------- | ----------------------------------------------- |
| `aihub_lib/aihub_lib/mcp/McpClientConfig.py`                  | New — MCP connection config as StepConfig       |
| `aihub_lib/aihub_lib/mcp/__init__.py`                         | New — public export                             |
| `aihub_agent/aihub_agent/dispatchers/AgentDispatcher.py`      | Modified — Client DI + AsyncExitStack lifecycle |
| `aihub_lib/aihub_lib/mcp/react.py`                            | New — reusable ReAct loop + MCP tool helpers    |
| `aihub_agent/pyproject.toml`                                  | Modified — added `fastmcp>=2.11.2`              |
| `aihub_agent/playground/minimal_workflow/mcp_react_workflow/` | New — ReAct agent example + BDD test            |
