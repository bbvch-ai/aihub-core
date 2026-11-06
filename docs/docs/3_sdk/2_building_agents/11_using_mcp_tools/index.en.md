---
title: Using MCP Tools
description: Connect agents to external MCP servers and let them call the tools those servers expose.
---

# Using MCP Tools

Agents are not limited to the steps you write and the knowledge you index — they can also call tools hosted on
**external MCP servers**. The [Model Context Protocol](https://modelcontextprotocol.io) is an open standard for exposing
tools and data to AI applications. An agent connects to any MCP server and lets its LLM call the tools it offers: create
a ticket, query a database, send a message.

## The connection config

`McpClientConfig` describes a single MCP server connection. It is a `StepConfig`, so the dispatcher injects it into any
step that declares it as a parameter — add it to your agent config and it becomes available in your workflow.

| Field       | Purpose                                                                                        |
| ----------- | ---------------------------------------------------------------------------------------------- |
| `name`      | A logical name for the connection.                                                             |
| `url`       | The MCP server's HTTP(S) endpoint; a URL ending in `/sse` uses SSE, any other Streamable HTTP. |
| `auth_mode` | How to authenticate: `none`, `api_key`, or `user_token`.                                       |
| `api_key`   | The static key, used only when `auth_mode` is `api_key`.                                       |
| `timeout`   | Client timeout in seconds.                                                                     |

## Which servers an agent may reach

Whoever edits an agent profile sets the URL, and agents run next to the platform's own services. `McpClientFactory`
therefore connects only to public hosts: a Docker service name, `localhost`, a private address, or a name that resolves
to one is refused before the connection opens, and redirects are not followed. To reach an MCP server on an internal
network, such as the platform's own API at `http://api:8000/mcp`, list its host name in `MCP_ALLOWED_PRIVATE_HOSTS`
(comma-separated) in the agent's environment.

## Authentication modes

| Mode         | Behavior                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------- |
| `none`       | No credentials are sent.                                                                     |
| `api_key`    | A static key configured on the connection is sent as the bearer token.                       |
| `user_token` | The requesting user's token is forwarded, so the external action is attributed to that user. |

`user_token` mode only works for user-initiated chat runs that carry the user's token. Scheduled, process-initiated,
bot-channel, and agent-to-agent runs forward no user token and fail in this mode — use `api_key` or `none` for those.

## Calling MCP tools from a step

Add an `McpClientConfig` field to your agent config, then open a client inside a step with `McpClientFactory`.
`McpAuthResolver` reads the forwarded user token out of the run context, so a connection set to `user_token` mode acts
on behalf of the requesting user.

```python
from swiss_ai_hub.core.mcp import McpClientConfig
from swiss_ai_hub.agent.mcp import McpAuthResolver, McpClientFactory


class ResearchAgentConfig(AgentConfig):
    mcp: McpClientConfig


class ResearchAgent(Agent):
    @step()
    async def call_tools(
        self,
        event: UserMessageEvent,
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> StopEvent:
        user_token = await McpAuthResolver.resolve_user_token(run_context)
        async with McpClientFactory.create(mcp_config, user_token=user_token) as mcp_client:
            tools = await mcp_client.list_tools()
            result = await mcp_client.call_tool("create_ticket", {"title": "..."})
        ...
```

::: warning
`McpClientFactory` raises if `auth_mode` is `api_key` or `user_token` but the credential is missing. A misconfigured
connection fails loudly instead of silently calling the server unauthenticated or with the wrong identity.
:::

## The ready-made McpReactAgent

If you just need an agent that reasons over an MCP server's tools, the SDK ships **`McpReactAgent`** — a complete
ReAct-style agent that discovers an MCP server's tools and resources, lets the LLM pick and call them in a loop, and
streams the result. Point its `McpClientConfig` at your server, choose an `auth_mode`, and run it. It is also the
reference implementation for the pattern above.
