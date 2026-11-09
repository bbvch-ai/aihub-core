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

## Decision

- **Microsoft 365 with OAuth client credentials (SMTP XOAUTH2).** Every stage sends through `smtp.office365.com:587`
  with Keycloak's token authentication (`authType: token`, available in Keycloak 26.8.1). An Entra app with the
  application permission `SMTP.SendAsApp` and access to the mailbox fetches the token. Settings live in
  `compose-config.yml` under `keycloak.smtp_server`. Without the `KEYCLOAK_SMTP_*` values (the dev default), Keycloak
  sends nothing and logs the failure.
- **The client secret is read from Keycloak's file vault.** The realm stores `${vault.smtp-client-secret}`; the
  entrypoint writes `KEYCLOAK_SMTP_CLIENT_SECRET` to a tmpfs at `/opt/keycloak/vault` and starts Keycloak with
  `--vault=file`. Keycloak 26.8.1's `TokenAuthEmailAuthenticator` resolves `authTokenClientSecret` through the vault.
  This is the one deliberate `${...}` placeholder in the realm.
- **Converge by default migration.** The entrypoint's existing kcadm block also writes `smtpServer` once
  `KEYCLOAK_SMTP_TENANT_ID` and `KEYCLOAK_SMTP_CLIENT_ID` are set, only while the realm has no mail server or still has
  the platform's server without a client id (tenant and client id are substituted once, so a realm first started without
  them would otherwise keep the empty values).
- **Invitations use Keycloak's admin-triggered mail.** Administrators create the user, add the tenant group and
  `AIHubAccess`, and send *Credential Reset* with *Update Password* and *Verify Email* from the admin console. The
  platform adds no invitation API or UI; the steps are documented in the operator guide.

Keeping the secret in an environment variable substituted into the realm JSON, as the client secrets are, was rejected
because the secret must never be part of the realm. Managing `smtpServer` with keycloak-config-cli was rejected because
"file wins" there would overwrite a mail server an operator changed. A platform invitation API and UI (the first plan
for #435) was dropped in favour of Keycloak's built-in mail.

## Consequences

- One Entra client secret serves every instance that sends from the shared mailbox. It expires (at most 24 months) and
  must be rotated on every instance; the operator guide covers this.
- Keycloak needs outbound access to `login.microsoftonline.com:443` and `smtp.office365.com:587`.
- Deployments not using the platform's Compose files (Kubernetes at customers) must provide the three `KEYCLOAK_SMTP_*`
  values and a writable `/opt/keycloak/vault`.
- Inviting takes several steps in the Keycloak admin console, and only Keycloak administrators can do it; tenant admins
  without Keycloak access cannot invite. Mails use Keycloak's default language and the realm has no password policy.
  Both can be revisited if inviting becomes frequent.
