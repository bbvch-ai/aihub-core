# MCP Resources as System Prompt Context with Tool-Based Fallback

## Context

The `McpReactAgent` connects to MCP servers at runtime. MCP servers expose two primitives: **tools** (actions the LLM
can call) and **resources** (read-only data identified by URI). Tools work out of the box — the LLM calls them via
OpenAI function-calling. Resources do not: the LLM has no native mechanism to request a resource read.

The MCP spec is explicit about this. Resources are **application-controlled** — the spec states: *"If you want the model
to be able to request data dynamically, consider using Tools instead."* In interactive clients (Claude Desktop, Cursor),
a human picks which resources to attach via a UI. Our agents are autonomous — there is no human to pick.

We needed to decide how an autonomous agent consumes MCP resources.

## Decision Drivers

- **No LLM-native resource access**\
  OpenAI function-calling only supports tool calls. The LLM cannot request a resource read.
- **Two types of resources with different characteristics**\
  Static resources have fixed URIs known at connection time. Templated resources have parameterized URIs (e.g.
  `users://{id}/profile`) whose values depend on the conversation.
- **Token efficiency**\
  Resources that can be resolved upfront should not waste a tool slot.

## Decision

MCP resources are **context** (like a system prompt), not actions. We handle them based on when their content can be
resolved:

**Static resources** — URI is known, content is fixed. Fetched once at agent init, injected into the system prompt. Zero
tool calls, zero overhead.

**Templated resources** — URI contains parameters unknown at init (can't fetch `users://42/profile` before knowing the
user asks about user 42). Exposed as a single meta-tool `read_mcp_resource` so the LLM can fetch them on-demand when it
knows the parameters. This is late-bound context retrieval, not an action.

## Consequences

### Positive

- Static resources cost nothing — they're just prompt context
- All templated resources share one tool slot regardless of count
- Follows the MCP spec's own recommendation for autonomous agents

### Trade-offs

- Developers who know MCP from interactive clients may find the tool conversion surprising
- The LLM must correctly construct URIs from template patterns, which may fail for complex templates
- A server with many resource templates produces a long tool description
