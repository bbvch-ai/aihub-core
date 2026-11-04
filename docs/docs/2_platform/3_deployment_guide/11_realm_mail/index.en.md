---
title: Realm mail and invitations
description: How Keycloak sends invitation and password-reset mail from the platform mailbox through Microsoft 365, how operators set it up, and how administrators invite users by email.
---

# Realm mail and invitations

Keycloak sends every mail the platform needs: password resets ("Forgot password") and invitations for people who cannot
sign in through Entra ID. It sends them from the Microsoft 365 mailbox `noreply.ai-hub@bbv.ch`, with an OAuth 2.0
client-credentials token (SMTP XOAUTH2) instead of a mailbox password.

This page covers what the platform configures, what you set up in Microsoft 365, how to invite a user, and how to check
that mail arrives.

## What the platform configures

The mail server is set in `infra/deployment/compose-config.yml` under `keycloak.smtp_server` and rendered into the realm
on the first start:

| Setting        | Value                                                                                           |
| -------------- | ----------------------------------------------------------------------------------------------- |
| Mail server    | `smtp.office365.com:587`, STARTTLS                                                              |
| Sender         | `noreply.ai-hub@bbv.ch` (display name "Swiss AI-Hub")                                           |
| Authentication | OAuth 2.0 token from `login.microsoftonline.com`, scope `https://outlook.office365.com/.default` |

Existing deployments get the mail server on the next Keycloak start, as long as the realm has none yet. A mail server an
administrator already configured in the Keycloak admin console is kept.

The client secret never appears in the realm. Keycloak reads it at send time from its file vault: the entrypoint writes
`KEYCLOAK_SMTP_CLIENT_SECRET` to `/opt/keycloak/vault/aihub_smtp-client-secret`, a memory-only mount, and the realm
refers to it as `${vault.smtp-client-secret}`.

## Microsoft 365 setup

These steps need an Entra administrator and an Exchange Online administrator of the tenant that owns the mailbox.

1. **Register an app** in Microsoft Entra ID (App registrations → New registration). No redirect URI is needed.
2. **Add the permission** *Office 365 Exchange Online* → *Application permissions* → `SMTP.SendAsApp`, and grant admin
   consent.
3. **Create a client secret** (Certificates & secrets) and note its value and expiry date.
4. **Register the app with Exchange Online** and give it access to the mailbox, in Exchange Online PowerShell:

   ```powershell
   Connect-ExchangeOnline
   New-ServicePrincipal -AppId <application-client-id> -ObjectId <enterprise-application-object-id>
   Add-MailboxPermission -Identity "noreply.ai-hub@bbv.ch" -User <enterprise-application-object-id> -AccessRights FullAccess
   ```

   The object id is the one of the **enterprise application** (service principal), not of the app registration.

5. **Allow SMTP AUTH** on the mailbox:

   ```powershell
   Set-CASMailbox -Identity "noreply.ai-hub@bbv.ch" -SmtpClientAuthenticationDisabled $false
   ```

## Deployment configuration

Set these variables in the deployment's `.env` (see [Environment variables](../9_environment_variables/)):

| Variable                      | Value                                         |
| ----------------------------- | --------------------------------------------- |
| `KEYCLOAK_SMTP_TENANT_ID`     | Directory (tenant) id of the mailbox's tenant |
| `KEYCLOAK_SMTP_CLIENT_ID`     | Application (client) id of the app            |
| `KEYCLOAK_SMTP_CLIENT_SECRET` | The client secret                             |

Then restart Keycloak (`docker compose up -d keycloak`).

Deployments that do not run the platform's Docker Compose files, for example on Kubernetes, need the same three values
in the Keycloak container's environment and a writable directory at `/opt/keycloak/vault`, ideally memory-backed. The
platform's entrypoint script (`infra/configs/keycloak/keycloak-entrypoint.sh`) does the rest; if you replace it, start
Keycloak with `--vault=file --vault-dir=/opt/keycloak/vault` and write the secret to the file
`aihub_smtp-client-secret` in that directory.

Keycloak connects to `login.microsoftonline.com:443` and `smtp.office365.com:587`, so outbound traffic to both must be
allowed (see [Network requirements](../7_network_requirements/)).

## Invite a user by email

Invitations use Keycloak's own admin-triggered mail. A Keycloak administrator does this in the admin console
(`https://auth.<domain>/admin`, realm **aihub**):

1. **Users** → **Add user**. Enter the email address (and optionally first and last name), leave *Email verified* off,
   and choose **Create**.
2. On the new user's **Groups** tab, choose **Join Group** and select the tenant under `tenants`.
3. On the **Role mapping** tab, choose **Assign role** → *Filter by realm roles* and assign `AIHubAccess`. Without it,
   sign-in is denied.
4. On the **Credentials** tab, choose **Credential Reset**, select the actions **Update Password** and **Verify Email**,
   pick a link lifetime, and choose **Send Email**.

The person receives a mail from `noreply.ai-hub@bbv.ch` with a link. Opening it verifies the address and lets them set a
password; afterwards they sign in with email and password, also on instances whose tenants otherwise log in through
Entra. To resend an invitation, repeat step 4. A tenant role (for example `AIHubUser`) is assigned in the platform's
admin UI under the tenant's users, as for every other user.

## Check that mail arrives

1. Open the sign-in page and choose **Forgot password?**.
2. Enter the address of an existing account. A reset mail from `noreply.ai-hub@bbv.ch` should arrive within a minute.
3. If nothing arrives, check the Keycloak log: `docker compose logs keycloak | grep -i -E "mail|smtp"`. Common causes:
   - `AADSTS7000215` (invalid client secret): the secret is wrong or has expired.
   - `535 5.7.3 Authentication unsuccessful`: SMTP AUTH is disabled on the mailbox, or the service principal has no
     mailbox permission.

In the Keycloak admin console, *Realm settings* → *Email* → *Test connection* sends a test mail to the address of the
administrator who is signed in.

## Secret rotation

Entra client secrets expire (at most 24 months). Before the expiry date, create a new secret on the app, update
`KEYCLOAK_SMTP_CLIENT_SECRET` and restart Keycloak. Keycloak caches the access token per secret, so the new secret takes
effect with the next mail.
