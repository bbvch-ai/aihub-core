# MCP Host Integration – Implementation Plan

## Executive Summary

Enable Swiss AI Hub agents to act as **MCP Hosts**, connecting through a centralized **MetaMCP gateway** (and optionally directly) to interact with external MCP servers. This gives agents access to the growing MCP ecosystem (databases, APIs, file systems, specialized tools) without building each integration ourselves.

**MCP Protocol Alignment**: The MCP specification defines three roles: **Host** (the AI application orchestrating everything), **Client** (1:1 connection to a Server), and **Server** (provides tools/resources/prompts). Our agent acts as the **Host** — it manages one or more Client instances, each connecting to a single Server (or MetaMCP endpoint). This distinction drives the entire architecture.

---

## Architecture

### MCP Protocol Roles Mapped to AI Hub

```
┌─────────────────────────────────────────────────────────────┐
│  Agent = MCP Host                                            │
│  (orchestrates LLM + manages MCP Clients)                    │
│                                                              │
│  ┌─────────────────┐       ┌──────────────────────────────┐ │
│  │ MCP Client A    │──────→│ MetaMCP Gateway (MCP Server)  │ │
│  │ (StreamableHTTP) │       │  ├── External MCP Server A     │ │
│  │                  │       │  ├── GitHub MCP Server        │ │
│  │                  │       │  └── [weitere Server]         │ │
│  └─────────────────┘       └──────────────────────────────┘ │
│                                                              │
│  ┌─────────────────┐       ┌──────────────────────────────┐ │
│  │ MCP Client B    │──────→│ Direct MCP Server             │ │
│  │ (StreamableHTTP/ │       │ (for sampling-capable servers │ │
│  │  SSE / stdio)    │       │  or special transports)       │ │
│  └─────────────────┘       └──────────────────────────────┘ │
│                                                              │
│  LLM (via LiteLLM)                                           │
│  ├── Used for tool selection (function calling)              │
│  └── Used to fulfill sampling requests from MCP servers      │
│                                                              │
│  RAG Agent (via AgentInTheLoop)                               │
│  └── Delegated to when LLM calls "search_knowledge_base"    │
└─────────────────────────────────────────────────────────────┘
```

**Key protocol constraints**:
- Each `Client` has a **1:1 relationship** with a Server (MCP spec requirement)
- MetaMCP aggregates multiple backend servers into **one** MCP Server endpoint — so one Client suffices for the gateway
- For servers needing **sampling** or **elicitation** support, direct Client connections may be needed (MetaMCP may not pass these through)
- The Host is responsible for **capability negotiation**, **access control**, and **user consent** for sampling

### What already exists

| Component | Status | Location |
|-----------|--------|----------|
| OpenAI-compatible endpoint | Exists | OpenWebUI → LiteLLM → Agent pipeline |
| MCP Server (read-only API) | Exists | `aihub_api/runners/ApiRunner.py` (FastMCP `^2.11.2`) |
| AgentInTheLoop delegation | Exists | `aihub_lib/nats/events/agent_in_the_loop.py` |
| HumanInTheLoop pattern | Exists | `aihub_lib/nats/events/human_in_the_loop.py` |
| LLM calls via LiteLLM | Exists | `aihub_lib/generative_ai/resources/models/llm/` |
| Docker Compose templating | Exists | `deployment/templates/docker-compose.yml.j2` |
| Step dependency injection | Exists | `AgentDispatcher._get_parameter_value()` |

### What needs to be built

| Component | Scope | Package |
|-----------|-------|---------|
| MetaMCP docker service | Infrastructure | `deployment/` |
| McpHostManager (Host abstraction) | Shared library | `aihub_lib` |
| McpHostConfig (multi-connection config) | Shared library | `aihub_lib` |
| McpHostManager injection into steps | Agent framework | `aihub_agent` |
| Sampling handler (→ LiteLLM, with audit) | Shared library | `aihub_lib` |
| Orchestration Agent | Agent | `aihub_agent` |
| OTEL tracing for MCP calls | Observability | `aihub_lib` |

---

## Design Decisions

### D1: Agent = MCP Host, not Client

The MCP spec is clear: the **Host** is the AI application that orchestrates LLM access and manages Client instances. Our agent is the Host. It:
- Creates one `fastmcp.Client` per MCP Server connection (1:1 as per spec)
- Aggregates tools from all connected Clients
- Routes sampling requests through LiteLLM
- Enforces access control and audit logging

We name our abstraction **`McpHostManager`** (not `McpClientManager`) to be precise about the protocol role.

### D2: MCP tool calling = within-step operation (not event delegation)

MCP tool calls are **synchronous from the agent's perspective** (call tool → get result), like LLM calls. They don't need the event-driven AgentInTheLoop pattern. The McpHostManager gets **injected into steps** like `EventDisplayer` or `RunContext`.

**Rationale**: AgentInTheLoop is for inter-agent delegation across NATS. MCP tool calls are direct HTTP calls, analogous to how `llm.stream_chat()` calls LiteLLM.

### D3: LLM function calling drives tool selection

The orchestration agent doesn't need hand-coded routing logic. Instead:
1. Discover available MCP tools at startup (tool schemas from all connected Clients)
2. Present them to the LLM as function/tool definitions
3. LLM decides which tools to call (standard function calling)
4. Agent executes the tool calls and feeds results back to LLM
5. LLM iterates until it has a final answer

This is the standard **ReAct / tool-use loop** pattern. No custom routing logic needed.

### D4: RAG as a "tool" alongside MCP tools

**Recommendation**: Keep RAG as AgentInTheLoop delegation (preserves existing RAG pipeline quality), but expose it as a callable tool to the LLM. The LLM sees: "You have access to `search_knowledge_base` AND these MCP tools. Decide what to use."

When the LLM calls `search_knowledge_base`, the orchestrator delegates to the RAG agent via AgentInTheLoop and returns the result as a tool response.

### D5: Sampling with audit trail (not silent auto-approve)

The MCP spec states that sampling (`sampling/createMessage`) **should** include a human-in-the-loop checkpoint where the user can approve/edit/reject the request. In an automated agent context, full human approval per request is impractical. Instead:

- **`log_only` (default)**: Auto-approve but log every sampling request with full details (OTEL span + DisplayEvent). This maintains **radical transparency** (core platform philosophy).
- **`auto`**: Silent auto-approve (for trusted, high-throughput scenarios).
- **`require_approval`**: Translate to HumanInTheLoop request (future, complex).

Configurable per-agent via `McpHostConfig.sampling_policy`.

### D6: Support both MetaMCP and direct connections

MetaMCP is an MCP Server itself (not a transparent proxy). It aggregates tools/resources/prompts from backend servers. However:
- **Sampling pass-through is unconfirmed** — MetaMCP may not forward `sampling/createMessage` from backend servers to our Client
- **Elicitation pass-through is unconfirmed** — same concern
- Some servers may need **specific transports** (stdio, custom auth)

Therefore, `McpHostConfig` supports a **list of connections**: MetaMCP endpoints AND direct server connections. Each connection creates one `fastmcp.Client` instance (1:1 per spec).

### D7: Elicitation deferred

MCP elicitation (`elicitation/create`) allows servers to request structured user input. This maps naturally to HumanInTheLoop, but the implementation is complex:
- The MCP Client is waiting synchronously for the tool result
- HumanInTheLoop is event-driven and async
- Bridging requires coroutine suspension + event subscription

Deferred to a later phase. The Host abstraction is designed to accommodate it later.

### D8: MetaMCP over raw FastMCP multi-server config

While FastMCP's transports can connect to multiple servers directly, MetaMCP adds:
- Web UI for server management (no code changes to add/remove servers)
- Namespace-based grouping and access control
- Tool enable/disable and middleware (filtering, overrides)
- Rate limiting per endpoint
- Bootstrap configuration for reproducible deployments

This is worth the additional infrastructure component.

### D9: Authentication Strategy (MetaMCP vs. Direct Connections)

**Problem**: External MCP servers may require per-user JWT authentication.
The end-to-end flow is: External Frontend → External Backend → Our OpenAI Endpoint → Our Agent → External MCP Server.

**MetaMCP auth capabilities (verified from docs)**:
- Clients → MetaMCP: API-Key or OAuth per MCP Spec 2025-06-18 ✅
- MetaMCP → Upstream: Static bearer tokens, static custom headers, OAuth sessions (server-level) ✅
- MetaMCP → Upstream: Per-user JWT forwarding ❌ (connection pool is server-scoped, not user-scoped)

**FastMCP Client auth capabilities (verified from docs)**:
- Static bearer token: `Client(url, auth="my-token")` ✅
- OAuth 2.1 (browser-based Authorization Code + PKCE): `Client(url, auth="oauth")` ✅ (interactive only)
- Custom `httpx.Auth`: `Client(url, auth=custom_auth)` ✅ — `async_auth_flow()` called per HTTP request
- Proxy mode header forwarding: `get_http_headers()` auto-forwards incoming `Authorization` header ✅

**Decision**: Two-tier auth strategy:
1. **MetaMCP** for servers that need only service-level auth (static API-Key/Bearer token) — default path
2. **Direct connection with custom `httpx.Auth`** for servers that need per-user JWT — the `httpx.Auth` subclass
   resolves the token dynamically from `RunContext` per request

**Per-User JWT Flow** (for direct connections):
1. External backend sends user JWT to our OpenAI endpoint (e.g., `X-User-Token` header)
2. Our API stores it in `RunContext`
3. McpHostManager creates a `DynamicBearerAuth(httpx.Auth)` that reads from `RunContext`
4. FastMCP Client calls `async_auth_flow()` on every HTTP request → token injected dynamically

```python
class DynamicBearerAuth(httpx.Auth):
    """Resolves per-user JWT from RunContext for each MCP request."""

    def __init__(self, run_context: RunContext, token_key: str = "user_jwt"):
        self._run_context = run_context
        self._token_key = token_key

    async def async_auth_flow(self, request: httpx.Request):
        token = await self._run_context.get(self._token_key)
        if token:
            request.headers["Authorization"] = f"Bearer {token}"
        yield request
```

**Open question per integration**: Does the external MCP server require a real per-user JWT, or would a service
account with user_id as tool argument suffice? This determines MetaMCP (Option A) vs. direct connection (Option B).

---

## FastMCP & MetaMCP Documentation Reference

Key findings from the official documentation, relevant for our implementation.

### FastMCP Client (fastmcp ^2.x)

**Source**: https://github.com/jlowin/fastmcp/tree/main/docs

#### Transports
- **`StreamableHttpTransport`** (recommended for remote): Production HTTP transport for remote servers.
- **`SSETransport`**: Legacy Server-Sent Events transport, maintained for backward compatibility.
- **In-memory**: Direct connection to `FastMCP` server instance (testing).
- **STDIO**: Subprocess communication (Claude Desktop pattern).

#### Authentication
- **`auth` parameter** on `Client(transport, auth=...)`: Accepts `str` (bearer token), `"oauth"` (interactive OAuth 2.1), or any `httpx.Auth` subclass.
- **`BearerAuth(token="...")`**: Built-in, wraps token in `SecretStr`, injects `Authorization: Bearer <token>` header.
- **Plain string**: `Client(url, auth="my-token")` → auto-wrapped in `BearerAuth`.
- **OAuth 2.1**: Built-in browser-based Authorization Code + PKCE flow. NOT suitable for server-to-server.
- **Custom `httpx.Auth`**: `async_auth_flow()` is called **per HTTP request** — ideal for dynamic per-user tokens.
- **Static headers**: `StreamableHttpTransport(url, headers={"X-Custom": "value"})` — static dict, not per-request.

**Important**: Use `auth` parameter instead of manually setting `Authorization` in `headers`. This is the
intended API and enables dynamic token resolution.

#### Tool Calling
- `client.call_tool("name", args)` returns a **`ToolResult`** object, not raw data.
- `result.data`: Deserialized Python objects (datetime, UUID, etc.)
- `result.content[0].text`: Raw MCP TextContent
- `result.is_error`: Boolean error flag
- `result.structured_content`: Raw JSON from server
- Supports `timeout` parameter: `client.call_tool("name", args, timeout=30.0)`
- Supports `raise_on_error=False` for graceful error handling.

#### Multi-Server Config (v2.4.0+)
- `MCPConfig` / `mcpServers` dict format natively supported.
- Tool names auto-prefixed with server name (e.g., `weather_get_forecast`).

#### Proxy Pattern
- `ProxyProvider` wraps a remote MCP server, exposing its tools as local server components.
- **Header forwarding**: `get_http_headers()` automatically captures incoming request's `Authorization` header
  and forwards to upstream in proxy mode.
- **Middleware**: Can intercept requests, extract auth tokens, and store in context.

### MetaMCP Gateway

**Source**: https://github.com/metatool-ai/metamcp/tree/main/docs

#### Architecture
- MCP aggregator/gateway: Combines multiple upstream MCP servers into one unified MCP server endpoint.
- Clients connect to MetaMCP's SSE or Streamable HTTP endpoint.
- MetaMCP connects to upstream servers using configured credentials.

#### Authentication — Clients → MetaMCP
- **API-Key**: In header (`Authorization: Bearer <key>`) or query parameter.
- **OAuth per MCP Spec 2025-06-18**: Standard MCP authorization flow.
- **SSO/OIDC**: OpenID Connect Authorization Code + PKCE for user login to MetaMCP UI.

#### Authentication — MetaMCP → Upstream Servers
- **Static Bearer Token**: Per server configuration (`bearerToken` field).
- **Static Custom Headers**: Per server configuration (`headers` field).
- **OAuth Sessions**: MetaMCP authenticates as a service to upstream OAuth-protected servers.
- **Per-user JWT forwarding**: ❌ NOT SUPPORTED
  - Connection pool is **server-scoped** (all users share the same connection)
  - No per-request header injection in the aggregated endpoint path
  - `x-custom-auth-header` exists only for the direct server proxy path (Inspector), not production

#### Bootstrap Configuration
- Pre-configure admin users, API keys, namespaces, and endpoints via environment variables (JSON arrays).
- `BOOTSTRAP_ENABLE=true` + `BOOTSTRAP_USER_EMAIL`, `BOOTSTRAP_API_KEYS`, etc.
- Reproducible deployments without manual UI setup.

#### Key Limitation for Our Use Case
MetaMCP is ideal for aggregating MCP servers that need only service-level authentication (static tokens).
For servers requiring per-user authentication (dynamic JWTs), direct connections are required.

---

## Implementation Review (Current Code vs. FastMCP Docs)

Review of the existing MVP implementation against FastMCP documentation best practices.

| Aspect | Current Implementation | FastMCP Best Practice | Priority |
|--------|----------------------|----------------------|----------|
| **`auth` parameter** | Not used. Auth set via static `headers` dict in transport | Use `Client(transport, auth=...)` — accepts string, OAuth, or `httpx.Auth` | **High** (needed for per-user JWT) |
| **SSE transport** | `McpConnectionConfig.transport` allows `"sse"` but `_create_transport()` always creates `StreamableHttpTransport` | Create `SSETransport` when `transport == "sse"` | Medium |
| **Context manager** | `client.__aenter__()` / `client.__aexit__()` called directly | `async with Client(...) as client:` — idiomatic context manager | Low (works, but not idiomatic) |
| **ToolResult handling** | `call_tool()` returns `Any`, no error checking | Returns `ToolResult` with `.data`, `.content`, `.is_error`, `.structured_content` | Medium |
| **Timeout on tool calls** | No timeout set | `client.call_tool("name", args, timeout=30.0)` supported | Medium |
| **Tool schema conversion** | ✅ Correct — `mcp_tool_to_openai_function()` | Matches expected format | — |
| **Lifecycle management** | ✅ Correct — lazy init per run, cleanup on Stop/Exception | Matches recommended pattern | — |
| **DI injection** | ✅ Correct — `param.annotation == McpHostManager` in dispatcher | Clean pattern | — |

### Action Items for Implementation
1. **Use `auth` parameter** on `Client()` instead of manual `Authorization` header in transport
2. **Implement SSE transport** fallback when `conn.transport == "sse"`
3. **Add `DynamicBearerAuth(httpx.Auth)`** for per-user JWT from RunContext (see D9)
4. **Handle `ToolResult.is_error`** in `call_tool()` — log warning, include in OTEL span
5. **Add `timeout`** parameter to `call_tool()` (default 60s)
6. **Pass `run_context`** to McpHostManager for dynamic auth support

---

## Implementation Phases

### Phase 1: MetaMCP Infrastructure

**Goal**: MetaMCP running in docker-compose, accessible by agents.

#### 1.1 Add MetaMCP to docker-compose template

**File**: `deployment/templates/docker-compose.yml.j2`

```yaml
metamcp:
  container_name: metamcp
  image: ghcr.io/metatool-ai/metamcp:latest
  restart: always
  environment:
    - NODE_ENV=production
    - POSTGRES_HOST=postgres
    - POSTGRES_PORT=5432
    - POSTGRES_USER=${METAMCP_POSTGRES_USER}
    - POSTGRES_PASSWORD=${METAMCP_POSTGRES_PASSWORD}
    - POSTGRES_DB=metamcp
    - APP_URL=${METAMCP_APP_URL}
    - NEXT_PUBLIC_APP_URL=${METAMCP_APP_URL}
    - BETTER_AUTH_SECRET=${METAMCP_AUTH_SECRET}
    - BOOTSTRAP_ENABLE=true
    - BOOTSTRAP_USER_EMAIL=${METAMCP_ADMIN_EMAIL}
    - BOOTSTRAP_USER_PASSWORD=${METAMCP_ADMIN_PASSWORD}
    - BOOTSTRAP_API_KEYS=${METAMCP_BOOTSTRAP_API_KEYS}
    - BOOTSTRAP_NAMESPACES=${METAMCP_BOOTSTRAP_NAMESPACES}
    - BOOTSTRAP_ENDPOINTS=${METAMCP_BOOTSTRAP_ENDPOINTS}
    - BOOTSTRAP_DISABLE_REGISTRATION_UI=true
    - BOOTSTRAP_DISABLE_REGISTRATION_SSO=true
    - TRANSFORM_LOCALHOST_TO_DOCKER_INTERNAL=true
    - LOG_LEVEL=info
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - backend
    - data
  # Dev: expose port directly
  # Prod: Traefik routing
```

**Key decisions**:
- **Share existing PostgreSQL**: Add `metamcp` to `POSTGRES_MULTIPLE_DATABASES` (same pattern as openwebui, phoenix, dagster, litellm). Separate user for schema isolation.
- **Networks**: `backend` (agent access) + `data` (PostgreSQL access)
- **Dev port**: `12008` (MetaMCP default)
- **Bootstrap**: Pre-configure admin user, API key, and initial namespace via environment variables (JSON arrays)

#### 1.2 Environment variables

**File**: `.env.dev`

```bash
# MetaMCP
METAMCP_POSTGRES_USER=metamcp
METAMCP_POSTGRES_PASSWORD=metamcp_dev
METAMCP_APP_URL=http://localhost:12008
METAMCP_AUTH_SECRET=metamcp-dev-secret-change-in-prod
METAMCP_ADMIN_EMAIL=admin@aihub.local
METAMCP_ADMIN_PASSWORD=changeme
METAMCP_API_KEY=sk_mt_dev_key_for_local_development
METAMCP_BOOTSTRAP_API_KEYS=[{"name":"agent-access","key":"sk_mt_dev_key_for_local_development"}]
METAMCP_BOOTSTRAP_NAMESPACES=[{"name":"default","description":"Default namespace for AI Hub agents"}]
METAMCP_BOOTSTRAP_ENDPOINTS=[{"name":"default","namespaceName":"default"}]
```

**File**: `.env.prod`

```bash
METAMCP_POSTGRES_USER=metamcp
METAMCP_POSTGRES_PASSWORD=REPLACE_WITH_SECURE_PASSWORD
METAMCP_APP_URL=https://metamcp.${DOMAIN}
METAMCP_AUTH_SECRET=REPLACE_WITH_SECURE_SECRET
METAMCP_ADMIN_EMAIL=REPLACE_WITH_ADMIN_EMAIL
METAMCP_ADMIN_PASSWORD=REPLACE_WITH_SECURE_PASSWORD
METAMCP_API_KEY=REPLACE_WITH_SECURE_API_KEY
```

#### 1.3 PostgreSQL database provisioning

Add `metamcp` to the multi-database init script pattern already used by the platform. The existing `configs/postgres/init-multiple-dbs.sh` creates databases from `POSTGRES_MULTIPLE_DATABASES`.

#### 1.4 Traefik routing (production only)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=proxy"
  - "traefik.http.routers.metamcp.rule=Host(`metamcp.${DOMAIN}`)"
  - "traefik.http.routers.metamcp.entrypoints=websecure"
  - "traefik.http.routers.metamcp.tls.certresolver=letsencrypt"
  - "traefik.http.services.metamcp.loadbalancer.server.port=12008"
```

#### 1.5 Image tag configuration

**File**: `deployment/compose-config.yml`

```yaml
image_tags:
  metamcp: ghcr.io/metatool-ai/metamcp:latest
```

#### 1.6 Regenerate and verify

```bash
make generate-compose
docker compose -f docker-compose.dev.yml up -d metamcp
# Verify: http://localhost:12008 accessible
# Verify: API key works via curl
```

---

### Phase 2: MCP Host Foundation (aihub_lib)

**Goal**: Reusable MCP Host abstraction that manages multiple Client connections, with sampling support and OTEL tracing.

#### 2.1 McpHostConfig model

**File**: `aihub_lib/aihub_lib/mcp/McpHostConfig.py` (exists, needs update)

```python
class McpConnectionConfig(BaseModel):
    """Configuration for a single MCP Client ↔ Server connection (1:1 per MCP spec)."""

    name: str                                                  # Logical name for this connection
    url: str                                                   # MetaMCP endpoint or direct server URL
    transport: Literal["streamable_http", "sse"] = "streamable_http"
    api_key: SecretStr | None = None                           # Static bearer token (FastMCP auth parameter)
    sampling_enabled: bool = False                             # Whether this server may request sampling
    headers: dict[str, str] | None = None                      # Additional static HTTP headers
    dynamic_auth: bool = False                                 # If True, use per-user JWT from RunContext


class McpHostConfig(StepConfig):
    """MCP Host configuration for agents.

    The agent acts as an MCP Host, managing one Client per connection.
    Each connection is a 1:1 Client-Server pair as per MCP spec.
    """

    connections: Annotated[list[McpConnectionConfig], Field(min_length=1)]
    sampling_policy: Annotated[
        Literal["auto", "log_only", "require_approval"],
        Field(default="log_only"),
    ]
    max_tool_iterations: Annotated[int, Field(default=10, ge=1, le=50)]
```

**Why a list of connections**: The MCP spec mandates 1:1 Client-Server. MetaMCP aggregates many servers behind one endpoint (one connection). But for servers needing sampling, direct transport, or per-user JWT, additional direct connections are needed.

#### 2.2 McpHostManager

**File**: `aihub_lib/aihub_lib/mcp/McpHostManager.py` (new)

```python
class McpHostManager:
    """MCP Host abstraction — manages multiple Client instances.

    Per MCP spec, the Host:
    - Creates and manages Client instances (1:1 with Servers)
    - Aggregates tools/resources from all connected Servers
    - Handles sampling requests (routes to LLM, with audit)
    - Enforces access control and capability negotiation
    """

    def __init__(
        self,
        config: McpHostConfig,
        llm_config: LLMConfig | None = None,
        displayer: EventDisplayer | None = None,
        run_context: RunContext | None = None,
    ):
        self._config = config
        self._llm_config = llm_config
        self._displayer = displayer
        self._run_context = run_context
        self._clients: dict[str, Client] = {}        # connection_name → Client
        self._tools_cache: dict[str, list[Tool]] = {}  # connection_name → tools

    async def connect_all(self) -> None:
        """Establish all Client connections (one per configured server)."""
        for conn in self._config.connections:
            transport, auth = self._create_transport_and_auth(conn, self._run_context)
            sampling_handler = (
                self._create_sampling_handler(conn)
                if conn.sampling_enabled and self._llm_config
                else None
            )
            # Use FastMCP's auth parameter (not manual headers) per docs
            client = Client(transport, auth=auth, sampling_handler=sampling_handler)
            await client.__aenter__()
            self._clients[conn.name] = client

    async def disconnect_all(self) -> None:
        """Close all Client connections."""
        for name, client in self._clients.items():
            await client.__aexit__(None, None, None)
        self._clients.clear()
        self._tools_cache.clear()

    async def list_all_tools(self, refresh: bool = False) -> list[Tool]:
        """Aggregate tools from all connected Servers."""
        all_tools = []
        for name, client in self._clients.items():
            if refresh or name not in self._tools_cache:
                self._tools_cache[name] = await client.list_tools()
            all_tools.extend(self._tools_cache[name])
        return all_tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Route tool call to the correct Client and trace with OTEL.

        Returns a FastMCP ToolResult with:
        - result.data: Deserialized Python objects
        - result.content[0].text: Raw text content
        - result.is_error: Boolean error flag
        - result.structured_content: Raw JSON from server
        """
        conn_name = self._find_connection_for_tool(name)
        client = self._clients[conn_name]
        tracer = trace.get_tracer("aihub.mcp")
        with tracer.start_as_current_span(
            f"mcp.tool.{name}",
            attributes={
                "mcp.tool.name": name,
                "mcp.connection": conn_name,
            },
        ):
            result = await client.call_tool(name, arguments, timeout=60.0)
            if result.is_error:
                logger.warning("MCP tool '%s' returned error: %s", name, result.content)
            return result

    def _create_transport_and_auth(
        self,
        conn: McpConnectionConfig,
        run_context: RunContext | None = None,
    ) -> tuple[Transport, httpx.Auth | str | None]:
        """Create transport and auth for a connection.

        Uses FastMCP's `auth` parameter instead of manual Authorization headers.
        This is the intended API per FastMCP docs and enables dynamic token resolution.
        """
        headers = dict(conn.headers or {})

        # Determine auth strategy
        auth: httpx.Auth | str | None = None
        if conn.dynamic_auth and run_context:
            # Per-user JWT from RunContext (see D9: Authentication Strategy)
            auth = DynamicBearerAuth(run_context)
        elif conn.api_key:
            # Static bearer token — use FastMCP's auth parameter (not headers)
            auth = conn.api_key.get_secret_value()

        if conn.transport == "streamable_http":
            transport = StreamableHttpTransport(url=conn.url, headers=headers)
        else:  # sse
            transport = SSETransport(url=conn.url, headers=headers)

        return transport, auth

    def _create_sampling_handler(self, conn: McpConnectionConfig):
        """Create a sampling handler with audit logging for a connection."""
        async def handler(
            messages: list[SamplingMessage],
            params: SamplingParams,
            context: RequestContext,
        ) -> CreateMessageResult:
            # 1. Audit log (always, regardless of policy)
            tracer = trace.get_tracer("aihub.mcp")
            with tracer.start_as_current_span(
                "mcp.sampling.request",
                attributes={
                    "mcp.sampling.connection": conn.name,
                    "mcp.sampling.message_count": len(messages),
                    "mcp.sampling.policy": self._config.sampling_policy,
                },
            ):
                # 2. Emit DisplayEvent for transparency
                if self._displayer:
                    await self._displayer.display_thought(
                        f"MCP server '{conn.name}' requested LLM sampling "
                        f"({len(messages)} messages). Policy: {self._config.sampling_policy}"
                    )

                # 3. Apply policy
                if self._config.sampling_policy == "require_approval":
                    raise NotImplementedError(
                        "require_approval sampling policy not yet implemented. "
                        "Requires HumanInTheLoop bridge."
                    )

                # 4. Route to LiteLLM
                llm, _ = self._llm_config.to_llama_index()
                chat_messages = [_convert_sampling_message(m) for m in messages]
                if params.systemPrompt:
                    chat_messages.insert(
                        0, ChatMessage(role=MessageRole.SYSTEM, content=params.systemPrompt)
                    )
                response = await llm.achat(chat_messages)

                return CreateMessageResult(
                    role="assistant",
                    content=TextContent(type="text", text=response.message.content),
                    model=self._llm_config.model_name,
                )
        return handler

    def _find_client_for_tool(self, tool_name: str) -> Client:
        """Find which Client owns a tool (by searching the cache)."""
        for conn_name, tools in self._tools_cache.items():
            if any(t.name == tool_name for t in tools):
                return self._clients[conn_name]
        raise ValueError(f"Tool '{tool_name}' not found in any connected MCP server")
```

#### 2.3 Tool schema conversion

**File**: `aihub_lib/aihub_lib/mcp/tool_conversion.py` (new)

Convert MCP tool schemas to OpenAI function calling format for LLM integration:

```python
def mcp_tool_to_openai_function(tool: mcp.types.Tool) -> dict:
    """Convert MCP tool to OpenAI function calling schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }
```

#### 2.4 OTEL tracing

**File**: `aihub_lib/aihub_lib/mcp/tracing.py` (new)

Span conventions for MCP operations:
- `mcp.host.connect` — Host connecting all Clients
- `mcp.tool.{name}` — Individual tool call
- `mcp.tool.discovery` — Tool listing from all Clients
- `mcp.sampling.request` — Sampling request received (with full audit attributes)

#### 2.5 Package dependency

Add `fastmcp` to `aihub_lib/pyproject.toml` (currently only in `aihub_api`). The Host/Client functionality is needed at the lib level.

---

### Phase 3: Agent MCP Integration (aihub_agent)

**Goal**: Agents can use MCP tools within their workflow steps via injected `McpHostManager`.

#### 3.1 Extend AgentDispatcher for McpHostManager injection

**File**: `aihub_agent/aihub_agent/dispatchers/AgentDispatcher.py`

Add `McpHostManager` to the parameter resolution in `_get_parameter_value()`:

```python
# In _get_parameter_value(), add case:
if issubclass(parameter_type, McpHostManager):
    mcp_config = agent_config.get_step_configs_by_type(McpHostConfig)
    if mcp_config:
        return await self._get_or_create_mcp_host(run_id, mcp_config[0], agent_config)
    return None  # No MCP config = no MCP host
```

#### 3.2 Host lifecycle management in dispatcher

```python
class AgentDispatcher(BaseDispatcher):
    _mcp_hosts: dict[str, McpHostManager]  # run_id → host

    async def _get_or_create_mcp_host(
        self, run_id: str, config: McpHostConfig, agent_config: AgentConfig
    ) -> McpHostManager:
        """Create or retrieve McpHostManager for a run."""
        if run_id not in self._mcp_hosts:
            llm_config = getattr(agent_config, "llm", None)
            host = McpHostManager(config, llm_config)
            await host.connect_all()
            self._mcp_hosts[run_id] = host
        return self._mcp_hosts[run_id]

    async def _cleanup_run(self, run_id: str) -> None:
        """Disconnect all MCP Clients when run completes."""
        if run_id in self._mcp_hosts:
            await self._mcp_hosts[run_id].disconnect_all()
            del self._mcp_hosts[run_id]
        # ... existing cleanup
```

**Lifecycle**:
- `McpHostManager` created on first step that requests it (lazy init)
- All Clients stay connected for the duration of the run
- All Clients disconnected on `StopEvent` or `ExceptionEvent`
- Tools are cached per connection for the run duration

#### 3.3 MCP-enabled step pattern

```python
@step()
async def process_with_tools(
    self,
    event: UserMessageEvent,
    config: OrchestratorConfig,
    mcp_host: McpHostManager,  # Injected by dispatcher (MCP Host role)
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> StopEvent:
    # 1. Discover tools from all connected MCP Servers
    tools = await mcp_host.list_all_tools()
    tool_schemas = [mcp_tool_to_openai_function(t) for t in tools]

    # 2. Call LLM with tool definitions (function calling)
    messages = build_messages(event, config)
    async with config.llm.cost_reporting_llm(displayer) as llm:
        response = await llm.achat(messages, tools=tool_schemas)

    # 3. ReAct tool-use loop
    iterations = 0
    while response.additional_kwargs.get("tool_calls") and iterations < config.mcp_host_config.max_tool_iterations:
        for tool_call in response.additional_kwargs["tool_calls"]:
            # Validate tool exists (prevent LLM hallucination)
            tool_name = tool_call["function"]["name"]
            if not any(t.name == tool_name for t in tools):
                messages.append(tool_error_message(tool_call, f"Unknown tool: {tool_name}"))
                continue
            result = await mcp_host.call_tool(
                tool_name,
                json.loads(tool_call["function"]["arguments"]),
            )
            messages.append(tool_result_message(tool_call, result))

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(messages, tools=tool_schemas)
        iterations += 1

    # 4. Return final answer
    return StopEvent(result=response.message.content)
```

---

### Phase 4: Orchestration Agent (Pure Event-Driven)

**Goal**: A concrete agent that combines MCP tools with RAG knowledge base access using a **pure event-driven
ReAct loop** — the workflow graph IS the loop. No while loops inside steps.

**Key Principle**: Each step does ONE thing then emits an event. The loop is created by the event flow graph,
following the same pattern as `bounded_loop` playground example. State lives in `RunContext`, events are
lightweight triggers.

#### 4.1 Workflow Graph

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                                                          │
                    ▼                                                          │
UserMessageEvent → init_step → PlanEvent → plan_step ──→ McpToolCallEvent ──→ │
                                  ▲          │       │                         │
                                  │          │       └→ AgentInTheLoop.request │
                                  │          │              │                  │
                                  │          │              ▼                  │
                                  │          │         [RAG Agent]             │
                                  │          │              │                  │
                                  │          │    AgentInTheLoop.response      │
                                  │          │              │                  │
                                  │          │              ▼                  │
                                  │          │     handle_rag_response ────────┘
                                  │          │
                                  │     execute_mcp_tools ────────────────────┘
                                  │          │
                                  │          └→ StopEvent (final answer)
                                  │
                                  └── PlanEvent (from tool result steps)
```

**Loop mechanism**: `execute_mcp_tools` and `handle_rag_response` both emit `PlanEvent`, which triggers
`plan_step` again. This is the same pattern as `bounded_loop` where `decision_step` emits `BeginEvent`
to loop back to `process_a_step`.

#### 4.2 Events

```python
class PlanEvent(ControlEvent):
    """Triggers the plan step to call the LLM and decide the next action.

    Lightweight trigger — all conversation state lives in RunContext.
    Emitted by init_step (first iteration) and tool result steps (subsequent iterations).
    """
    pass


class ToolCallRequest(BaseModel):
    """A single tool call requested by the LLM."""
    id: str                     # Tool call ID from LLM response (for result matching)
    name: str                   # Tool name
    arguments: dict[str, Any]   # Tool arguments


class McpToolCallEvent(ControlEvent):
    """Carries one or more MCP tool calls to the execution step.

    If the LLM also requested a RAG call in the same turn, it is stored in
    pending_rag_query so execute_mcp_tools can chain into AgentInTheLoop after
    processing the MCP calls.
    """
    tool_calls: list[ToolCallRequest]
    pending_rag_query: str | None = None
```

**Reused events**: `UserMessageEvent`, `StopEvent`, `AgentInTheLoop.request/response/exception` —
all from `aihub_lib`.

#### 4.3 Steps

**Step 1: init_step** — Bootstrap the loop

```python
@step()
async def init_step(
    self,
    event: UserMessageEvent,
    mcp_host: McpHostManager,
    config: McpOrchestratorConfig,
    run_context: RunContext,
    event_displayer: EventDisplayer,
) -> PlanEvent:
    """Initialize the ReAct loop: discover tools, store initial state in RunContext."""
    # 1. Discover MCP tools from all connected servers
    mcp_tools = await mcp_host.list_all_tools()
    tool_schemas = [mcp_tool_to_openai_function(t) for t in mcp_tools]

    # 2. Add RAG tool schema if RAG agent is configured
    if config.rag_agent_id:
        tool_schemas.append(RAG_TOOL_SCHEMA)

    # 3. Build initial messages
    messages = [
        {"role": "system", "content": config.system_prompt},
        {"role": "user", "content": event.messages[-1].content},
    ]

    # 4. Store everything in RunContext
    await run_context.set("messages", messages)
    await run_context.set("tool_schemas", tool_schemas)
    await run_context.set("iteration", 0)

    await event_displayer.display_thought(
        f"Discovered {len(mcp_tools)} MCP tools. Starting reasoning loop."
    )

    return PlanEvent()
```

**Step 2: plan_step** — The brain (LLM decides what to do)

```python
@step()
async def plan_step(
    self,
    event: PlanEvent,
    config: McpOrchestratorConfig,
    run_context: RunContext,
    event_displayer: EventDisplayer,
) -> McpToolCallEvent | AgentInTheLoop.request | StopEvent:
    """Call LLM with conversation + tool schemas. Decide: use tool, delegate to RAG, or answer."""
    # 1. Load state from RunContext
    messages = await run_context.get("messages")
    tool_schemas = await run_context.get("tool_schemas")
    iteration = await run_context.get("iteration")

    # 2. Check iteration limit
    if iteration >= config.mcp.max_tool_iterations:
        return StopEvent(result="Maximum tool iterations reached. Here is what I found so far: ...")

    # 3. Call LLM with function calling
    response = await llm_chat_with_tools(config.llm, messages, tool_schemas, event_displayer)

    # 4. Check if LLM wants to call tools
    tool_calls = extract_tool_calls(response)

    if not tool_calls:
        # LLM produced a final answer
        return StopEvent(result=response.content)

    # 5. Separate MCP tool calls from RAG calls
    mcp_calls = [tc for tc in tool_calls if tc.name != "search_knowledge_base"]
    rag_calls = [tc for tc in tool_calls if tc.name == "search_knowledge_base"]

    # 6. Store assistant message (with tool_calls) in RunContext
    messages.append({"role": "assistant", "tool_calls": tool_calls, "content": response.content})
    await run_context.set("messages", messages)
    await run_context.set("iteration", iteration + 1)

    # 7. Route based on what tools the LLM requested
    if mcp_calls:
        # Execute MCP tools (optionally chain to RAG after)
        return McpToolCallEvent(
            tool_calls=[ToolCallRequest(id=tc.id, name=tc.name, arguments=tc.arguments) for tc in mcp_calls],
            pending_rag_query=rag_calls[0].arguments.get("query") if rag_calls else None,
        )
    else:
        # Only RAG call — delegate directly
        return AgentInTheLoop.invoke(
            agent_id=config.rag_agent_id,
            agent_class=config.rag_agent_class,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=rag_calls[0].arguments["query"], role=MessageRole.USER)]
            ),
        )
```

**Step 3: execute_mcp_tools** — Execute MCP tool calls (synchronous HTTP, no loop)

```python
@step()
async def execute_mcp_tools(
    self,
    event: McpToolCallEvent,
    mcp_host: McpHostManager,
    config: McpOrchestratorConfig,
    run_context: RunContext,
    event_displayer: EventDisplayer,
) -> PlanEvent | AgentInTheLoop.request:
    """Execute all MCP tool calls and append results to conversation."""
    messages = await run_context.get("messages")

    # Execute each MCP tool call (direct HTTP, no loop needed)
    for tc in event.tool_calls:
        await event_displayer.display_thought(f"Calling MCP tool: {tc.name}")
        result = await mcp_host.call_tool(tc.name, tc.arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "name": tc.name,
            "content": str(result),
        })

    await run_context.set("messages", messages)

    # If there's a pending RAG query, chain into AgentInTheLoop
    if event.pending_rag_query:
        return AgentInTheLoop.invoke(
            agent_id=config.rag_agent_id,
            agent_class=config.rag_agent_class,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=event.pending_rag_query, role=MessageRole.USER)]
            ),
        )

    # Otherwise, loop back to plan_step
    return PlanEvent()
```

**Step 4: handle_rag_response** — Convert RAG result back into the loop

```python
@step()
async def handle_rag_response(
    self,
    response: AgentInTheLoop.response,
    run_context: RunContext,
) -> PlanEvent:
    """Append RAG result to conversation and re-enter the plan loop."""
    messages = await run_context.get("messages")
    messages.append({
        "role": "tool",
        "tool_call_id": "rag_call",  # Match with the RAG tool call ID from messages
        "name": "search_knowledge_base",
        "content": str(response.stop_event.result),
    })
    await run_context.set("messages", messages)
    return PlanEvent()
```

**Step 5: handle_rag_exception** — Handle RAG failures gracefully

```python
@step()
async def handle_rag_exception(
    self,
    response: AgentInTheLoop.exception,
    run_context: RunContext,
) -> PlanEvent:
    """Append RAG error to conversation and let the LLM handle the failure."""
    messages = await run_context.get("messages")
    messages.append({
        "role": "tool",
        "tool_call_id": "rag_call",
        "name": "search_knowledge_base",
        "content": f"Error: Knowledge base search failed. {response.exception_event}",
    })
    await run_context.set("messages", messages)
    return PlanEvent()
```

#### 4.4 State Management (RunContext)

All conversation state lives in RunContext, keeping events lightweight:

| Key | Type | Purpose |
|-----|------|---------|
| `messages` | `list[dict]` | Full conversation history (OpenAI function calling format) |
| `tool_schemas` | `list[dict]` | Discovered tool schemas (MCP + optional RAG) |
| `iteration` | `int` | Loop counter (bounded by `max_tool_iterations`) |

**Why RunContext, not events?**
- Conversation history grows unbounded — events should be small
- Multiple steps need to read/write the same state
- Follows the `bounded_loop` pattern where `RunContext` stores the loop counter
- Events are signals ("execute this"), state is context ("here's the conversation so far")

#### 4.5 Configuration

```python
class McpOrchestratorConfig(AgentConfig):
    """Configuration for the MCP Orchestrator Agent."""

    llm: Annotated[LLMConfig, Field(description="LLM for orchestration decisions.")]
    mcp: Annotated[McpHostConfig, Field(description="MCP Host configuration.")]
    rag_agent_id: Annotated[str | None, Field(default=None, description="RAG agent ID for knowledge base.")]
    rag_agent_class: Annotated[str | None, Field(default=None, description="RAG agent class name.")]
    system_prompt: Annotated[
        LocaleString,
        Field(default=LocaleString(en="You are a helpful assistant with access to tools...")),
    ]
```

#### 4.6 RAG Tool Schema (Hardcoded)

The RAG tool is presented to the LLM as a regular tool alongside MCP tools:

```python
RAG_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": "Search the organization's knowledge base for information. "
                       "Use this for questions about internal processes, documentation, "
                       "or organizational knowledge.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    },
}
```

The LLM doesn't know (or care) that `search_knowledge_base` is handled differently from MCP tools.
It sees a uniform list of callable tools and picks the best one.

#### 4.7 Handling Mixed Tool Calls (MCP + RAG in one turn)

When the LLM requests both MCP tools AND `search_knowledge_base` in a single response:

```
plan_step → McpToolCallEvent(tool_calls=[mcp_calls], pending_rag_query="...")
         → execute_mcp_tools (processes MCP calls, appends results to RunContext)
         → AgentInTheLoop.request (chains to RAG because pending_rag_query was set)
         → [RAG agent processes]
         → AgentInTheLoop.response
         → handle_rag_response (appends RAG result to RunContext)
         → PlanEvent
         → plan_step (LLM now has ALL tool results, continues reasoning)
```

MCP tools execute first (fast HTTP), then RAG delegates (async event-driven). All results are
collected in RunContext before the next `plan_step` call. The LLM sees all results in the next turn.

#### 4.8 Architecture Comparison: Why This Fits

| Concern | bounded_loop pattern | MCP Orchestrator |
|---------|---------------------|------------------|
| Loop mechanism | `decision_step` emits `BeginEvent` | `execute_mcp_tools` / `handle_rag_response` emit `PlanEvent` |
| State storage | `RunContext.set("loop_count", ...)` | `RunContext.set("messages", ...)`, `RunContext.set("iteration", ...)` |
| Exit condition | `loop_count >= loop_max` | `iteration >= max_tool_iterations` OR LLM returns final answer |
| No while loops | Correct — event graph is the loop | Correct — event graph is the loop |
| Step responsibility | Each step does one thing | `plan_step` = LLM call, `execute_mcp_tools` = tool execution |

| Concern | agent_in_the_loop pattern | MCP Orchestrator |
|---------|--------------------------|------------------|
| Delegation | `AgentInTheLoop.invoke()` | Same — for RAG delegation |
| Response handling | `end_step(response)` → result | `handle_rag_response(response)` → PlanEvent (back to loop) |
| Exception handling | `exception_step(exception)` → result | `handle_rag_exception(exception)` → PlanEvent (back to loop) |

The orchestrator **combines both patterns**: bounded loop (for the ReAct cycle) + AgentInTheLoop
(for RAG delegation). Each pattern is used exactly as designed — no fighting the architecture.

---

### Phase 5: Playground Example & Testing

#### 5.1 Playground example

**File**: `aihub_agent/playground/minimal_workflow/mcp_tool_workflow/` (new)

Minimal agent that:
1. Connects to MetaMCP as MCP Host
2. Discovers available tools
3. Uses LLM function calling to invoke tools
4. Returns combined result

Includes `trigger.py` for one-shot testing and `run.py` for interactive testing.

#### 5.2 Integration tests

- Test McpHostManager connection lifecycle (connect/disconnect)
- Test multi-Client management (multiple connections)
- Test tool discovery and aggregation across Clients
- Test tool routing (correct Client receives the call)
- Test tool calling and result processing
- Test sampling handler with audit logging
- Test sampling policy enforcement (log_only, auto)
- Test tool name validation (reject hallucinated tools)
- Test max_tool_iterations safety limit
- Test orchestrator agent end-to-end

#### 5.3 BDD features

```gherkin
Feature: MCP Host Integration
  Scenario: Agent discovers and calls MCP tools
    Given an agent configured as MCP Host with a MetaMCP connection
    And MetaMCP has a registered tool "get_weather"
    When a user asks "What is the weather in Zurich?"
    Then the agent discovers the "get_weather" tool
    And the LLM decides to call "get_weather"
    And the agent calls the tool via the correct MCP Client
    And returns a response containing weather information

  Scenario: Agent handles sampling request from MCP server
    Given an agent configured with sampling_policy "log_only"
    And a direct MCP server connection with sampling_enabled
    When the MCP server sends a sampling/createMessage request
    Then the agent logs the sampling request (OTEL span)
    And routes the request through LiteLLM
    And returns the LLM response to the MCP server
```

---

### Phase 6: Documentation & ADR

#### 6.1 ADR

**File**: `aihub_doc/arc42/decisions/2026_02_11_mcp-host-integration.md`

Document:
- Agent as MCP Host (not just Client) — protocol alignment
- MetaMCP as central gateway with direct connection fallback
- McpHostManager injection into steps (vs. event-based delegation)
- LLM function calling for tool routing (vs. hand-coded logic)
- Sampling policy with audit trail (transparency principle)
- Elicitation deferred (complexity, async/sync bridge)

#### 6.2 Documentation updates

- Update `aihub_agent/AGENTS.md` with MCP Host integration patterns
- Update `aihub_lib/AGENTS.md` with McpHostManager usage
- Add MCP section to root `README.md`
- Document MetaMCP setup in deployment docs

---

## MCP Protocol Compliance Matrix

| MCP Feature | Support | Implementation |
|-------------|---------|----------------|
| **Tool invocation** | Phase 2-3 | `McpHostManager.call_tool()` via `fastmcp.Client` |
| **Tool discovery** | Phase 2-3 | `McpHostManager.list_all_tools()` with caching |
| **Resource access** | Deferred | Can be added to McpHostManager later |
| **Prompt usage** | Deferred | Can be added to McpHostManager later |
| **Sampling (Server → Host)** | Phase 2 | `sampling_handler` → LiteLLM, with configurable audit policy |
| **Elicitation (Server → Host)** | Deferred | Complex async/sync bridge to HumanInTheLoop |
| **Roots provision** | Deferred | Not needed for current use cases |
| **Capability negotiation** | Phase 2 | FastMCP Client handles during `initialize` handshake |
| **1:1 Client-Server** | Phase 2 | One `fastmcp.Client` per `McpConnectionConfig` |
| **Host manages Clients** | Phase 2 | `McpHostManager` creates/destroys Client instances |

---

## Scope Analysis of Original Epics

| Original Epic | Assessment | Mapping |
|---------------|------------|---------|
| **Epic 1: Orchestrierungs-Agent** | Needed, but OpenAI endpoint already exists | Phase 4 (OrchestratorAgent), no new endpoint needed |
| **Task 1.2: OpenAI Endpoint** | **Already exists** via OpenWebUI + LiteLLM pipeline | No work needed |
| **Epic 2: RAG-Agent Anbindung** | Existing AgentInTheLoop pattern | Phase 4.3 (RAG as tool + AITL delegation) |
| **Epic 3: MetaMCP Gateway** | Fully needed | Phase 1 (Docker + config) |
| **Epic 4: FastMCP Client** | Fully needed, corrected to MCP Host | Phase 2 (aihub_lib) + Phase 3 (aihub_agent) |
| **Epic 5: Routing-Logik** | Simplified by LLM function calling | Phase 4 (LLM decides, no hand-coded routing) |

### Removed / Simplified

- **Task 1.2 (OpenAI Endpoint)**: Not needed. OpenWebUI already provides this.
- **Task 5.1 (Entscheidungslogik)**: No hand-coded routing. LLM function calling handles it.

### Deferred

- **Elicitation handling** (MCP server → HumanInTheLoop): Complex async/sync bridge.
- **Resource access** (reading MCP resources): Lower priority than tool calling.
- **Prompt usage** (MCP server prompts): Nice-to-have, not critical for MVP.

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| MetaMCP stability (external dependency) | Pin image version, monitor upstream, can fall back to direct FastMCP connections |
| MetaMCP doesn't pass sampling through | Support direct connections alongside MetaMCP for sampling-capable servers |
| Tool name collisions across Clients | MetaMCP prefixes tools with `ServerName__`; for direct connections, add connection prefix |
| MCP Client connection stability | FastMCP Client supports reconnection; add health checks in McpHostManager |
| LLM hallucinating tool calls | Validate tool names against discovered tools before calling |
| Runaway tool-call loops | `max_tool_iterations` config limit (default 10) |
| MetaMCP PostgreSQL conflicts | Separate database within shared instance (existing pattern) |
| Sampling latency (LLM call within tool call) | Acceptable tradeoff; add timeout. Audit via OTEL traces. |
| Sampling security (MCP server triggers LLM) | Audit logging + configurable policy (log_only default) |
| Per-user JWT expiry during agent run | JWT may expire while agent is running multi-step workflow. Mitigate with short-lived runs and token refresh support in `DynamicBearerAuth` |
| MetaMCP cannot forward per-user JWT | Use direct connections for servers requiring per-user auth (see D9). MetaMCP only for service-level auth |
| External MCP server auth requirements unclear | Clarify per integration: service-account + user_id param, or real per-user JWT? This determines MetaMCP vs. direct connection |

---

## File Change Summary

### New files

| File | Package | Purpose |
|------|---------|---------|
| `aihub_lib/aihub_lib/mcp/__init__.py` | aihub_lib | MCP module (exists) |
| `aihub_lib/aihub_lib/mcp/McpHostConfig.py` | aihub_lib | MCP Host + connection config models (exists, needs `dynamic_auth` field) |
| `aihub_lib/aihub_lib/mcp/McpHostManager.py` | aihub_lib | MCP Host lifecycle, multi-Client management (exists, needs `auth` param + ToolResult + timeout) |
| `aihub_lib/aihub_lib/mcp/auth.py` | aihub_lib | `DynamicBearerAuth(httpx.Auth)` for per-user JWT from RunContext |
| `aihub_lib/aihub_lib/mcp/sampling.py` | aihub_lib | Sampling handler (→ LiteLLM, with audit) |
| `aihub_lib/aihub_lib/mcp/tracing.py` | aihub_lib | OTEL span conventions for MCP |
| `aihub_lib/aihub_lib/mcp/tool_conversion.py` | aihub_lib | MCP tool → OpenAI function schema (exists) |
| `aihub_agent/aihub_agent/agents/orchestrator/McpOrchestratorAgent.py` | aihub_agent | Orchestrator agent (pure event-driven ReAct loop) |
| `aihub_agent/aihub_agent/agents/orchestrator/McpOrchestratorConfig.py` | aihub_agent | Orchestrator config (LLM, MCP, RAG, system prompt) |
| `aihub_agent/aihub_agent/agents/orchestrator/events/PlanEvent.py` | aihub_agent | Lightweight trigger for plan_step |
| `aihub_agent/aihub_agent/agents/orchestrator/events/McpToolCallEvent.py` | aihub_agent | Carries MCP tool calls to execute_mcp_tools step |
| `aihub_agent/playground/minimal_workflow/mcp_tool_workflow/` | aihub_agent | Playground example |
| `aihub_doc/arc42/decisions/2026_02_11_mcp-host-integration.md` | aihub_doc | ADR |

### Modified files

| File | Change |
|------|--------|
| `deployment/templates/docker-compose.yml.j2` | Add MetaMCP service |
| `deployment/compose-config.yml` | Add MetaMCP image tag |
| `.env.dev` | Add MetaMCP environment variables |
| `.env.prod` | Add MetaMCP environment variables |
| `configs/postgres/init-multiple-dbs.sh` | Add `metamcp` database |
| `aihub_lib/pyproject.toml` | Add `fastmcp` dependency |
| `aihub_agent/aihub_agent/dispatchers/AgentDispatcher.py` | Add McpHostManager injection + lifecycle |
| `aihub_agent/AGENTS.md` | Document MCP Host integration |
| `aihub_lib/AGENTS.md` | Document McpHostManager |

---

## Implementation Order

```
Phase 1 (MetaMCP Infra)  ─┐
                           ├──→  Phase 3 (Dispatcher Integration)  →  Phase 4 (Orchestrator)
Phase 2 (Host Library)   ─┘                                                     ↓
                                                                    Phase 5 (Testing/Playground)
                                                                                 ↓
                                                                    Phase 6 (Docs/ADR)
```

Phases 1 and 2 can run in parallel.
Phase 3 depends on Phase 2.
Phase 4 depends on Phase 3.
Phases 5 and 6 can overlap with Phase 4.
