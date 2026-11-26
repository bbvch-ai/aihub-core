# Realm Mail via Microsoft 365 OAuth, Invitations via Keycloak

## Context

The Keycloak realm had no mail server (`"smtpServer": {}`), so Keycloak sent no mail at all: "Forgot password" did
nothing, and people without an Entra account could not be invited by email (bbvch-ai/aihub-core-private#435). Keycloak
already offers an admin-triggered mail that lets a new user verify the address and set a password ("Credential Reset"
with the actions *Update Password* and *Verify Email*); it only lacked a way to send it.

Two constraints shaped the solution. The sending mailbox, `noreply.ai-hub@bbv.ch`, is in Microsoft 365, where basic SMTP
authentication with a mailbox password is being retired in favour of OAuth. And realm settings are bootstrap-only per
[`2026_06_12_declarative_keycloak_realm_reconciliation`](./2026_06_12_declarative_keycloak_realm_reconciliation.md): the
realm import runs only on first start, while existing deployments must get mail too, without overwriting a mail server
an operator set in the admin console.

## Decision Drivers

- *No secret in the realm*\
  The realm file is committed and exported; the mail credential must come from the deployment's secret store.
- *Existing deployments converge*\
  Realms created before this change must get the mail server.
- *Operator overrides survive*\
  Same rule as the session lifespans in
  [`2026_06_11_keycloak_sso_session_lifespans`](./2026_06_11_keycloak_sso_session_lifespans.md).
- *No new product surface*\
  Inviting is rare and done by administrators who already use the Keycloak admin console.
- *Mail must not weaken federated sign-in*\
  With mail, "Forgot password" works for every account, including users who sign in through Entra ID and have no
  password. A password set that way would skip Entra's MFA and conditional access and outlive the Entra account.

## Decision

- **Microsoft 365 with OAuth client credentials (SMTP XOAUTH2).** Every stage sends through `smtp.office365.com:587`
  with Keycloak's token authentication (`authType: token`, available in Keycloak 26.8.1). An Entra app with the
  application permission `SMTP.SendAsApp` and access to the mailbox fetches the token. Settings live in
  `compose-config.yml` under `keycloak.smtp_server`; the mailbox, used as sender and SMTP user, is
  `KEYCLOAK_SMTP_MAILBOX` (default `noreply.ai-hub@bbv.ch`). Without the `KEYCLOAK_SMTP_*` values (the dev default),
  Keycloak has no mail server and sends nothing.
- **The client secret is read from Keycloak's file vault.** The realm stores `${vault.smtp-client-secret}`; the
  entrypoint writes `KEYCLOAK_SMTP_CLIENT_SECRET` to a tmpfs at `/opt/keycloak/vault` and starts Keycloak with
  `--vault=file`. Keycloak 26.8.1's `TokenAuthEmailAuthenticator` resolves `authTokenClientSecret` through the vault.
  This is the one deliberate `${...}` placeholder in the realm.
- **The entrypoint writes the mail server; the platform's mailbox is platform-managed.** The realm import leaves
  `smtpServer` empty, because Keycloak validates the sender on import and a sender from an unset variable would fail the
  whole first start. Once `KEYCLOAK_SMTP_TENANT_ID`, `KEYCLOAK_SMTP_CLIENT_ID` and `KEYCLOAK_SMTP_MAILBOX` are set, the
  entrypoint's existing kcadm block writes `smtpServer` to any realm that has none, new or existing. It rewrites the
  platform's mail server (on `smtp.office365.com`, signing in as `KEYCLOAK_SMTP_MAILBOX`) whenever its client id or
  tenant differ from the variables, so replacing the Entra app needs only the variables. Every other mail server is the
  operator's and is kept as a whole, including an organisation's own Microsoft 365 mailbox on the same host; telling the
  two apart by host alone overwrote such a mailbox, sender and credentials included.
- **Users who sign in through an identity provider never use a password.** A *Hardcoded Role* mapper on every identity
  provider grants the realm role `AIHubFederatedUser` on each sign-in (sync mode `FORCE`). The managed flows deny that
  role the password form (in `browser-aihub-forms`) and password reset (a custom `reset-credentials-aihub`, bound as the
  realm's reset flow). The reset flow denies after its mail step, so the address form answers the same for every address
  and reveals nothing about who signs in through Entra. Identity providers are bootstrap-only, so the entrypoint adds
  the mapper to each one that lacks it, also to ones added in the admin console, and grants the role to users linked
  before it existed.
- **Invitations use Keycloak's admin-triggered mail.** Administrators create the user, add the tenant group and
  `AIHubAccess`, and send *Credential Reset* with *Update Password* and *Verify Email* from the admin console. The
  platform adds no invitation API or UI; the steps are documented in the operator guide.

Keeping the secret in an environment variable substituted into the realm JSON, as the client secrets are, was rejected
because the secret must never be part of the realm. Marking federated users with a user attribute (*Hardcoded Attribute*
mapper and *Condition - user attribute*) was rejected because users must not be able to remove the mark: an unmanaged
attribute is protected only while the realm's user profile keeps unmanaged attributes admin-only, while a realm role
cannot be changed by the user at all. Turning password reset off on instances with Entra was rejected because invited
users without an Entra account need it there. Managing `smtpServer` with keycloak-config-cli was rejected because "file
wins" there would overwrite a mail server an operator changed. A platform invitation API and UI (the first plan for
#435) was dropped in favour of Keycloak's built-in mail.

## Consequences

- One Entra client secret serves every instance that sends from the shared mailbox. It expires (at most 24 months) and
  must be rotated on every instance; the operator guide covers this.
- Keycloak needs outbound access to `login.microsoftonline.com:443` and `smtp.office365.com:587`.
- Users of an identity provider added in the admin console get `AIHubFederatedUser` only from the next Keycloak start,
  unless an administrator adds the mapper. The role stays when an identity provider link is removed; an administrator
  removes it by hand to let that person use a password.
- Changing `KEYCLOAK_SMTP_MAILBOX` on a deployment that already sends mail needs the new mailbox set once in the admin
  console, because the realm's old mailbox otherwise counts as the operator's.
- `reset-credentials-aihub` replicates Keycloak's built-in reset flow, like `browser-aihub` does the browser flow, and
  must be reviewed on Keycloak major upgrades.
- Deployments not using the platform's Compose files (Kubernetes at customers) must provide the four `KEYCLOAK_SMTP_*`
  values and a writable `/opt/keycloak/vault`.
- Inviting takes several steps in the Keycloak admin console, and only Keycloak administrators can do it; tenant admins
  without Keycloak access cannot invite. Mails use Keycloak's default language and the realm has no password policy.
  Both can be revisited if inviting becomes frequent.
