---
title: Realm mail and invitations
description: How Keycloak sends invitation and password-reset mail from the platform mailbox through Microsoft 365, how operators set it up, and how administrators invite users by email.
---

# Realm mail and invitations

Keycloak sends every mail the platform needs: password resets ("Forgot password") and invitations for people who cannot
sign in through Entra ID. It sends them from a Microsoft 365 mailbox (`KEYCLOAK_SMTP_MAILBOX`, by default
`noreply.ai-hub@bbv.ch`), with an OAuth 2.0 client-credentials token (SMTP XOAUTH2) instead of a mailbox password.

This page covers what the platform configures, what you set up in Microsoft 365, how to invite a user, and how to check
that mail arrives.

## What the platform configures

The mail server is set in `infra/deployment/compose-config.yml` under `keycloak.smtp_server`:

| Setting        | Value                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------ |
| Mail server    | `smtp.office365.com:587`, STARTTLS                                                               |
| Sender         | `KEYCLOAK_SMTP_MAILBOX` (display name "Swiss AI-Hub"), also the SMTP user                        |
| Authentication | OAuth 2.0 token from `login.microsoftonline.com`, scope `https://outlook.office365.com/.default` |

Keycloak's entrypoint writes the mail server on the first start after `KEYCLOAK_SMTP_TENANT_ID`,
`KEYCLOAK_SMTP_CLIENT_ID` and `KEYCLOAK_SMTP_MAILBOX` are set, on new and existing deployments alike. The platform's
mail server is the one on `smtp.office365.com` that signs in as `KEYCLOAK_SMTP_MAILBOX`: on every start, its tenant and
client id are set to the values of the variables, so edit the variables, not the admin console, to change them.

Any other mail server an administrator configures in the admin console is kept, including the organisation's own
Microsoft 365 mailbox on `smtp.office365.com`. To hand mail back to the platform, set the mail server's username in the
admin console to `KEYCLOAK_SMTP_MAILBOX` and restart Keycloak. Do the same after changing `KEYCLOAK_SMTP_MAILBOX` on a
deployment that already sends mail, because the realm still holds the old mailbox and would otherwise count as the
operator's.

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
| `KEYCLOAK_SMTP_MAILBOX`       | The sending mailbox (`noreply.ai-hub@bbv.ch`) |

In the Microsoft 365 setup above, use this mailbox wherever `noreply.ai-hub@bbv.ch` appears.

Then restart Keycloak (`docker compose up -d keycloak`).

Deployments that do not run the platform's Docker Compose files, for example on Kubernetes, need the same four values in
the Keycloak container's environment and a writable directory at `/opt/keycloak/vault`, ideally memory-backed. The
platform's entrypoint script (`infra/configs/keycloak/keycloak-entrypoint.sh`) does the rest; if you replace it, start
Keycloak with `--vault=file --vault-dir=/opt/keycloak/vault` and write the secret to the file `aihub_smtp-client-secret`
in that directory.

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

The person receives a mail from the sending mailbox with a link. Opening it verifies the address and lets them set a
password; afterwards they sign in with email and password, also on instances whose tenants otherwise log in through
Entra. To resend an invitation, repeat step 4. A tenant role (for example `AIHubUser`) is assigned in the platform's
admin UI under the tenant's users, as for every other user.

## Users who sign in through Entra ID never use a password

A user who has signed in through an identity provider such as Entra ID cannot sign in with a password or reset one.
Otherwise anyone could choose **Forgot password?**, set a password and from then on skip Entra's MFA and conditional
access, and keep access after IT disables them in Entra. Keycloak shows them a message to use the identity provider's
sign-in button instead. The reset mail is still sent, so the reset form does not reveal which addresses belong to Entra
users; its link leads to the same message.

The platform marks these users with the realm role `AIHubFederatedUser`, which a *Hardcoded Role* mapper named
`aihub-federated-user-role` grants on every sign-in through an identity provider. On every start, Keycloak's entrypoint
adds this mapper to each identity provider that lacks it and gives the role to users linked before it existed. After
adding an identity provider in the admin console, restart Keycloak (or add the mapper yourself) before its users sign
in.

The role stays when a user's identity provider link is removed. To let such a person use a password again, remove
`AIHubFederatedUser` on the user's **Role mapping** tab and send a *Credential Reset* as for an invitation. An invited
user who later signs in through Entra gets the role and from then on signs in through Entra only.

## Check that mail arrives

1. Open the sign-in page and choose **Forgot password?**.
2. Enter the address of an existing account that does not sign in through Entra. A reset mail from the sending mailbox
   should arrive within a minute.
3. If nothing arrives, check the Keycloak log: `docker compose logs keycloak | grep -i -E "mail|smtp"`. Common causes:
   - `AADSTS7000215` (invalid client secret): the secret is wrong or has expired.
   - `535 5.7.3 Authentication unsuccessful`: SMTP AUTH is disabled on the mailbox, or the service principal has no
     mailbox permission.

The admin console's *Realm settings* → *Email* → *Test connection* button is not a reliable check: it stays disabled for
administrators who sign in to the `master` realm, such as the bootstrap `admin`. Use "Forgot password" or an invitation
instead.

## Secret rotation and a new app

Entra client secrets expire (at most 24 months). Before the expiry date, create a new secret on the app, update
`KEYCLOAK_SMTP_CLIENT_SECRET` and restart Keycloak. Keycloak caches the access token per secret, so the new secret takes
effect with the next mail.

To switch to another Entra app or tenant, update `KEYCLOAK_SMTP_CLIENT_ID`, `KEYCLOAK_SMTP_TENANT_ID` and
`KEYCLOAK_SMTP_CLIENT_SECRET` the same way and restart Keycloak; the realm picks up the new ids on start. A new mailbox
also needs the admin-console step described under [What the platform configures](#what-the-platform-configures).
