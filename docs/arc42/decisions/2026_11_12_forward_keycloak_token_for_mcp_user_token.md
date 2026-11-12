# Forward the User's Keycloak Token for MCP `user_token` Connections Until Runs Have Their Own Token

## Context

An MCP connection with `auth_mode: user_token` sends the requesting user's token to the MCP server as its bearer
(`2026_05_22_mcp_client_authentication`). The agent reads that token from the `X-AIHub-User-Token` header the API
forwards. No first-party client sent it, so every chat with such a connection failed with "no user token was provided"
(#2451).

This blocks one integration in particular. A connection that sends the acting tenant's external id
(`forward_tenant_id_header`, for example `X-LCDM-Tenant`) requires `user_token`, because the MCP server can only trust
the tenant header when it can bind the request to a user of that tenant. The LCDM Hub verifies a Keycloak token against
the realm's JWKS for this.

The lasting answer is a short-lived token the platform mints for each run, bound to one audience (#2121). That needs key
management, verification in every receiving service and a change on the MCP server side, so it will take a while.

Two further gaps were found on the way:

- The OpenWebUI pipe calls the dynamic agent endpoints (`/agents/classes/{class}/instances/{id}/{event}/stream`), which
  dropped every `X-AIHub-*` header. Only the OpenAI-style completions endpoint forwarded them.
- The API forwarded the header without checking it. A client authenticated as one user could send another user's token.

## Decision Drivers

- **Unblock the chat clients people use**\
  OpenWebUI and the Admin UI chat should work with `user_token` connections now.
- **The token must be the requesting user's**\
  The API must not forward a token that belongs to someone else or that Keycloak would reject.
- **Keep the replacement small**\
  When #2121 lands, only the source of the token should change.

## Decision

Until #2121, clients forward the user's own Keycloak access token, and the API verifies it:

- **OpenWebUI pipe**: declares `__oauth_token__` and sends its `access_token` as `X-AIHub-User-Token`. OpenWebUI
  refreshes the token before handing it over. Accounts that did not log in through Keycloak have no token and send none.
- **Admin UI chat**: sends the user's access token as `X-AIHub-User-Token` on the chat-completion call only, not on
  every API request.
- **API**: `ForwardedUserTokenVerifier` checks the token's signature, issuer and expiry
  (`KeycloakAuthHandler.decode_token`) and that its `sub` is the requesting user's id. Otherwise the request fails with
  401 before anything is stored or published. Both the OpenAI-style completions endpoint and the dynamic agent
  endpoints, JSON and streaming, verify and forward the headers.
- **No audience check on the forwarded token.** OpenWebUI's tokens carry no `aud` claim (`azp: openwebui`), so the
  `account` audience the API requires for its own logins would refuse every OpenWebUI user. The API never acts on the
  forwarded token; it only confirms that it is a valid realm token of the requesting user. The Admin UI's tokens come
  from `aihub-frontend` with audience `account`. An MCP server must accept both.
- **Debug logs**: `NATSTraceContextPropagator` logs only the trace context fields of NATS headers, no longer all of
  them, since the same headers now carry the user's token.
- **Bots and non-interactive runs** stay without a user token and keep failing clearly in `user_token` mode.

## Consequences

### Positive

- MCP connections with `user_token`, and with them the tenant-header integration, work from OpenWebUI and the Admin UI.
- A client can no longer slip another user's token into a run.
- Answers to a run's questions (tool approvals, chat questions) carry the token again, so the stored token is refreshed.

### Trade-offs (accepted until #2121)

- **The token is valid beyond the MCP server.** The Admin UI's token carries audience `account`, which the AI Hub API
  accepts, and every realm token lives up to an hour (`accessTokenLifespan` 3600 s). The MCP server, or anyone who takes
  such a token from it, can call the AI Hub API as that user until it expires. Only connect `user_token` to servers
  trusted like the platform.
- **The token is stored.** It travels in the JetStream message headers of the run's control events (stream retention 30
  days) and in the run's context in Valkey. It is useless after it expires, but it is readable by anyone with access to
  those stores until then.
- **Traces carry a prefix.** `trace_fn` records the forwarded headers truncated to 50 characters, the JWT's header part.
  It identifies the signing key, not the user, and cannot be replayed.
- **Bots are not covered.** Teams and Slack users have no Keycloak token.
- **The token can expire mid-run.** A run longer than the token's remaining life fails on its next MCP call.

#2121 replaces the client-supplied header with a per-run token. The agent side then reads that token instead, and the
client changes from this decision are removed.
