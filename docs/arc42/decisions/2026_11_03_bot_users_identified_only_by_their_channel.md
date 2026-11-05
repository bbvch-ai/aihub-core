# Bot Users Are Identified Only by Their Channel, Within the Bot's Own Tenant or Workspace

## Context

`packages/bot` receives Bot Framework activities from Azure Bot Service and answers them by running an agent or an LLM
chat as the platform user behind the message. That user is the Keycloak account found by email
(ADR `2026_06_08_no_bot_first_keycloak_provisioning`). Each endpoint is configured by a `PathEntity` holding the Azure
bot's credentials (`APP_ID`, `APP_PASSWORD`, `APP_TENANTID`) and, for Slack, a bot token.

Three things were missing (aihub-core-private#378):

- **No inbound authentication.** Nothing validated the activity's JWT. The SDK's `CloudAdapter` runs a turn with
  anonymous claims when no middleware has stored verified ones, and the `KeycloakAuthHandler` passed to the controllers
  was never a dependency of any route. The statement in ADR `2026_06_08` that the bot authenticates inbound activities
  with Azure Bot Service credentials did not hold.
- **Identity from a field the sender controls.** On every channel except Teams, the email was taken from the activity's
  `from.name`.
- **No access check.** The bot never asked whether the resolved user may use the agent or model behind the endpoint.

Fixing the first is not enough on its own. The SDK's `JwtTokenValidator` checks only the signature and the audience, so
the issuer, the caller and the service URL need checks of their own. And an email that a channel lookup returns is only
as trustworthy as the tenant or workspace that issued it, while the platform maps a bot user to an account by email
alone.

## Decision Drivers

- **The sender must not choose the identity.** Only what Azure Bot Service and the channel vouch for may decide who a
  message comes from.
- **Fail closed.** When the bot cannot verify the sender, it refuses with a clear reply instead of guessing.
- **Use the mapping the platform already has.** Accounts are found by email (ADR `2026_06_08`); no new provisioning or
  identity linking.
- **No new configuration.** Only the existing `PathEntity` fields; no environment keys, no schema change.
- **Teams and Slack keep working end to end.**

## Decision

### Every activity is authenticated

All activity routes (agent, OpenAI, bot-in-the-loop) go through `RoutesService.process_activity()`, which runs
`BotActivityAuthenticator` against the path's credentials before the adapter sees the activity:

- signature from Microsoft's published keys, audience equal to the path's `APP_ID`;
- issuer among the Bot Framework issuer and the path's tenant issuers;
- no agent-to-agent tokens, which other applications can obtain;
- the token's `serviceurl` claim equal to the activity's `serviceUrl`, so a reply, and every lookup the bot makes
  through that URL, goes back to the channel that sent the message.

The verified claims are stored where the `CloudAdapter` reads them. A missing or invalid token gets `401`, a path with
no bot configured gets `404`. The `KeycloakAuthHandler` remains only because the `Controller` constructor requires one.

### The identity comes from the channel

- **Teams:** the email comes from the member roster (`get_conversation_member`), called through the token-bound service
  URL.
- **Slack:** the email comes from `users.info` for the user id in `from.id`, called with the path's bot token (scopes
  `users:read` and `users:read.email`).
- **Every other channel** (Web Chat, Direct Line, Emulator) has no such lookup and is not supported on the production
  bot. Its users get the localized reply `bot.error.unverified_user` ("cannot verify who you are"). The Emulator works
  only through `playground/testing/main.py`, which skips the token check and stubs the email.

`from.name` is never used.

### Only the bot's own tenant or workspace

- **Teams:** the member's `tenant_id`, as the roster returns it, must equal the path's `APP_TENANTID`. The member's
  tenant is used, not the conversation's: in a shared channel the conversation belongs to the host tenant while external
  members keep their home tenant. A path without `APP_TENANTID` refuses Teams users.
- **Slack:** the user's `team_id` must equal the workspace the path's token belongs to (`auth.test`, cached per token in
  `SlackUtils`).

Refusals use the same `unverified_user` reply and log the reason (foreign tenant, foreign workspace, missing scope, no
tenant configured) for operators.

### Access is enforced

`AgentCompletionHandler` checks `has_access_to_agent` and `OpenaiCompletionHandler` checks `has_access_to_model` for the
resolved user. A refusal gets the localized reply `bot.error.access_denied`.

## Considered Alternatives

### Rejected: match Teams users by their Azure AD object id

The roster gives the object id, but Keycloak's `azure-ad` provider links accounts by the OIDC `sub`, which Entra ID
issues per application. Matching the object id would mean changing the provider mapping and re-linking every user. Email
within the bot's own tenant identifies the same person.

### Deferred: a separate `PathEntity` field for the tenant a path serves

It would let a MultiTenant registration, which has no `APP_TENANTID`, serve Teams users. No deployment is known to need
it. If one does, the field can be added on top, falling back to `APP_TENANTID`.

### Rejected: pin the tenant only when `APP_TENANTID` is set

It would leave the check off on MultiTenant registrations, the paths that any tenant can reach.

### Rejected: keep Web Chat and Direct Line

Their users are identified only by what the client sends, so no platform account can be verified for them.

## Consequences

### Positive

- A message reaches an agent only when Azure Bot Service sent it for that bot. It runs as the user the channel vouches
  for, inside the bot's own tenant or workspace, and only on an agent or model that user may use.
- No new configuration or environment keys.
- Rejected users get a localized, actionable reply; the log tells an operator what to fix.

### Trade-offs

- Web Chat and Direct Line no longer work on the production bot.
- A MultiTenant Teams registration cannot serve Teams users. Filling in `APP_TENANTID` is not a field edit: it also
  changes the bot's outbound sign-in and the issuers it accepts, so the bot has to be registered as SingleTenant.
- External users (shared channels, federated chat, Slack Connect) are refused. Guests in the bot's own tenant keep
  working.
- Slack Enterprise Grid users from a sibling workspace have a different `team_id` and are refused.
- Slack apps need the `users:read` and `users:read.email` scopes and a reinstall before the change is deployed.
- A `PathEntity` with wrong or empty credentials stops working.
- Users need access to the endpoint's agent or model. Under the default `AIHubUser` role (`aihub.user.>`) everyone has
  it; deployments with scoped roles must grant it.
- Each Slack message costs one `users.info` call; `auth.test` is cached per token for 30 days.

### Related Decisions

- `2026_06_08_no_bot_first_keycloak_provisioning`: the bot maps users to Keycloak accounts by email and does not create
  them. This ADR makes its statement about authenticated inbound activities true and restricts which emails count.
- `2025_12_28_keycloak_as_identity_broker`: Keycloak brokers the Azure AD identities the bot's emails are matched
  against.
