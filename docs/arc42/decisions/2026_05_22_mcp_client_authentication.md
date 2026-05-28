# MCP Client Authentication: Three Modes with User-Token Passthrough

## Context

The `McpReactAgent` connects out to external MCP servers to call their tools. When a tool performs an action against an
external system — creating a Jira ticket, sending a message, updating a record — that action needs to be attributed to
the actual user who triggered the agent, not to a shared agent service account. Otherwise the external system's audit
trail loses the real actor and its per-user authorization cannot be enforced.

The platform already forwards `X-AIHub-*` request headers along the agent pipeline (API → NATS → dispatcher →
RunContext). The requesting user's token can ride along as an `X-AIHub-User-Token` header. We needed to decide how an
MCP connection chooses what credential to present.

The previous model mixed an `auth_mode` toggle with a separate optional `api_key` field. Because `api_key` was nullable,
the form rendered it with an "Enable API key" checkbox stacked on top of the toggle — a confusing nested control with no
single source of truth.

## Decision Drivers

- **Attribution**\
  External actions must be recorded against the real user, not a generic service account.
- **Not every connection is the same**\
  Some MCP servers need no credentials, some need a shared static key, some need per-user identity.
- **Fail loud, never mask the actor**\
  A misconfigured connection must fail, not silently fall back to a shared key — a silent fallback would attribute the
  user's action to the service account.

## Decision

`McpClientConfig.auth_mode` is a single three-way choice, and it is the only auth control on the connection:

- **none** — no credentials are sent.
- **api_key** — a static bearer token configured on the connection. The `api_key` field is shown only in this mode.
- **user_token** — the requesting user's bearer token, forwarded as the MCP call's bearer.

`McpAuthResolver` reads the user token from the `X-AIHub-User-Token` header that `AgentDispatcher` stashes in
RunContext. `McpClientFactory` resolves the bearer per mode and raises if `api_key` or `user_token` mode is selected
without the corresponding credential — it never falls back to another mode.

`user_token` mode only works for user-initiated chat-completion runs that carry the header. Scheduled,
process-initiated, bot-channel, and agent-to-agent runs forward no user token and fail loudly in this mode.

## Consequences

### Positive

- External actions are attributed to the actual user, so the external system's audit trail and per-user authorization
  stay correct.
- One explicit control instead of a toggle plus an optional key — the configuration has a single source of truth.
- Misconfiguration fails loudly and never masks the actor behind a shared key.

### Trade-offs

- `user_token` mode depends on the client sending an `X-AIHub-User-Token` header; nothing forwards it automatically yet,
  so it currently requires a client that sets it explicitly.
- The forwarded header is untrusted client input — the MCP server must validate the token itself before acting on it.
- An MCP connection that needs per-user auth cannot be driven by non-interactive runs (scheduled, process, bot).
