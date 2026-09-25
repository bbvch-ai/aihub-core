# IMAP Mailbox Login via OAuth 2.0 App-Only Tokens (Client Credentials)

## Context

The mailbox agents (`EmailClassificationAgent`, `ImapAgent`) logged in with a username and password only. Microsoft 365
tenants increasingly disable basic authentication, and once they do, no password — not even an app password — logs in
over IMAP. Request [aihub-requests#8](https://github.com/bbvch-ai/aihub-requests/issues/8) asks for OAuth 2.0 support so
these agents keep working against such tenants.

Both blueprints authenticate through a single point, `ImapClientFactory.create`, and every mailbox step opens its
connection there. The connection config is the shared `ImapClientConfig` in `packages/core/imap/` (see
[2026_07_05_agent_imap_read_capability](2026_07_05_agent_imap_read_capability.md)). The agents run headless, triggered
by a schedule or another workflow — no user is present to sign in.

Microsoft offers three ways to reach a mailbox without a password:

1. **IMAP with an app-only token** (client credentials flow, application permission `IMAP.AccessAsApp`), logged in with
   SASL `XOAUTH2`.
2. **IMAP with a delegated token** (authorization code or device flow, `IMAP.AccessAsUser.All`), kept alive with refresh
   tokens.
3. **Microsoft Graph** instead of IMAP.

## Decision Drivers

- **Headless operation**\
  A scheduled agent cannot complete an interactive sign-in, and must not stop working when a user's session or refresh
  token is revoked.
- **Change only the authentication**\
  Listing, filing and drafting are built on IMAP semantics (UIDs, folder names, `APPEND` of drafts, the `$AiHubDrafted`
  keyword). A new login method should leave them untouched, and keep working for Gmail, Dovecot and the GreenMail-backed
  integration tests.
- **No new secret infrastructure**\
  Credentials follow the existing `Password`-field-in-agent-config pattern, as the mailbox password already does.
- **A config error must not take the profile down**\
  Per
  [2026_08_07_agent_config_failures_surface_as_exception_events](2026_08_07_agent_config_failures_surface_as_exception_events.md),
  an agent config is validated on every dispatched event.

## Decision

**Option 1: IMAP with an app-only token from Microsoft Entra ID, alongside the existing password login.**

- `ImapClientConfig` gains `auth_method` (`"password"` | `"oauth2_client_credentials"`, default `"password"`, so saved
  profiles are unchanged) and `tenant_id`, `client_id`, `client_secret`. The form shows only the fields of the selected
  method. `client_secret` is a `Password` element, so it is handled exactly like the mailbox password.
- `oauth_authority` and `oauth_scope` are deployment-fixed plain fields (defaults `login.microsoftonline.com` and
  `https://outlook.office365.com/.default`); they differ only for sovereign clouds.
- `ImapClientFactory` branches on `auth_method`. For OAuth, `EntraTokenProvider` acquires a token with
  `azure.identity.ClientSecretCredential`, and the factory logs in with `IMAPClient.oauth2_login(username, token)` — the
  username names the mailbox.
- Required OAuth fields are checked where they are used, in `EntraTokenProvider.from_config`, not in a config validator:
  an empty field fails the step that logs in, with a message naming only the fields, never their values.
- **New dependency for `packages/agent`**: `azure-identity`, already used by `packages/api` and `packages/bot`. The
  synchronous credential is used and off-loaded with `asyncio.to_thread`, like every imapclient call; the async variant
  would add aiohttp as a direct dependency.
- A token is acquired per connection, with no cache. A run opens only a handful of connections.

Option 2 was rejected because it needs a one-time interactive consent plus an encrypted token store and revocation
handling, and still breaks when the consenting user leaves. Option 3 was rejected for this change because it is a second
mailbox backend rather than an authentication method: immutable ids instead of UIDs, folder ids instead of names,
`createReply` instead of `APPEND`, and no custom keywords. It remains Microsoft's strategic direction and would need its
own decision if a tenant disables IMAP altogether.

## Consequences

- Microsoft 365 mailboxes with basic authentication disabled work, and the password path is unchanged for every other
  server.
- **The access boundary lives in the tenant, not in the platform.** An app with `IMAP.AccessAsApp` can open exactly the
  mailboxes an Exchange administrator granted its service principal with `Add-MailboxPermission`. The agent cannot
  enforce this; the setup is documented on the Email Agent page, and anyone who can edit a profile's username can point
  it at any granted mailbox.
- The client secret is stored in the agent config like the mailbox password, and carries the same risk: whoever holds it
  can read every granted mailbox. Moving mailbox secrets behind an indirection is a separate, pre-existing concern for
  both.
- Client secrets expire (at most two years). An expired secret fails every run until it is renewed on the profile.
- Exchange answers `NO AUTHENTICATE failed` for a missing service principal, a missing mailbox permission and IMAP being
  disabled on the mailbox alike, so misconfiguration is diagnosed from the documentation, not from the error.
- XOAUTH2 against Exchange is not covered by the automated integration tests — GreenMail does not implement it — and is
  verified manually against a Microsoft 365 tenant.
- Certificate credentials (`CertificateCredential`) are a natural follow-up if a tenant's policy forbids client secrets;
  `EntraTokenProvider` is the only place that would change.
