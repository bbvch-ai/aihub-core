---
title: Microsoft 365 setup (customer)
description: What the customer's Microsoft 365 administrators set up so Keycloak can send invitation and password-reset mail from the customer's own mailbox with OAuth (SMTP XOAUTH2), how to verify it, and which values to hand to the operator.
---

# Microsoft 365 setup (customer)

Keycloak sends invitation and password-reset mail through Exchange Online and signs in with an OAuth 2.0 token instead
of a mailbox password. The mailbox and the Entra app that sends as it live in **the customer's own Microsoft 365
tenant**, so the customer's administrators set them up. The platform operator never needs admin rights in that tenant.

This page is for the customer's Entra and Exchange administrators. It takes about 30 minutes, plus up to an hour for
Microsoft to apply the permissions.

## Who does what

| Customer (Microsoft 365 tenant)                                                             | Operator (Swiss AI-Hub deployment)                                                               |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Creates the sending mailbox                                                                 | Receives the values from [step 8](#step-8-send-the-values-to-the-operator)                       |
| Registers the Entra app and grants it `SMTP.SendAsApp` with admin consent                   | Stores the client secret in the deployment's secret store                                        |
| Registers the app in Exchange Online, gives it the mailbox, allows SMTP AUTH on the mailbox | Sets the `KEYCLOAK_SMTP_*` variables and restarts Keycloak                                       |
| Creates the client secret and renews it before it expires                                   | Updates the secret when the customer sends a new one                                             |
| Allows the sender address in its own mail filters, if needed                                | Allows outbound traffic to Microsoft (see [Network requirements](../../7_network_requirements/)) |

The examples below use `noreply.ai-hub@contoso.com` as the sending mailbox. Replace it with the customer's address.

## Before you start

| You need                                                                                 | For                                      |
| ---------------------------------------------------------------------------------------- | ---------------------------------------- |
| **Application Administrator** (or Cloud Application Administrator) in Microsoft Entra ID | Registering the app and its secret       |
| **Privileged Role Administrator** or **Global Administrator**                            | Granting admin consent to the permission |
| **Exchange Administrator**                                                               | The mailbox and the PowerShell steps     |
| PowerShell 7 with the `ExchangeOnlineManagement` module                                  | Steps 5 and 6                            |

Install the module once:

```powershell
Install-Module ExchangeOnlineManagement -Scope CurrentUser
```

## Step 1: Create the mailbox

A **shared mailbox** is enough: it needs no license and nobody signs in to it.

1. Open the **Exchange admin center** (`https://admin.exchange.microsoft.com`) → **Recipients** → **Mailboxes**.
2. Choose **Add a shared mailbox**.
3. Display name, for example `Swiss AI-Hub`, and the email address, for example `noreply.ai-hub@contoso.com`, then
   **Create**.

If a suitable mailbox already exists, skip this step.

## Step 2: Register the app

1. Open the **Microsoft Entra admin center** (`https://entra.microsoft.com`) → **Identity** → **Applications** → **App
   registrations** → **New registration**.
2. Name: `Swiss AI-Hub Keycloak SMTP`.
3. Supported account types: **Accounts in this organizational directory only**.
4. Redirect URI: leave empty. Choose **Register**.
5. On the app's **Overview**, note:
   - **Application (client) ID**
   - **Directory (tenant) ID**

## Step 3: Add the SMTP permission

The app needs exactly one permission. It lets the app send mail over SMTP, and only as mailboxes it is given access to
in step 6.

1. In the app, open **API permissions** → **Add a permission** → **APIs my organization uses**.
2. Search for **Office 365 Exchange Online** and select it.
3. Choose **Application permissions**, tick **`SMTP.SendAsApp`**, then **Add permissions**.
4. Choose **Grant admin consent for** *(your organization)* and confirm. The status column turns to a green check.

You can remove the default delegated `User.Read` permission. Keycloak does not use it.

## Step 4: Create the client secret

1. In the app, open **Certificates & secrets** → **Client secrets** → **New client secret**.
2. Description `keycloak-smtp`, expiry **24 months** (the maximum), then **Add**.
3. Copy the **Value** right away. It is shown only once. The *Secret ID* is not the secret.

Note the expiry date: when the secret expires, Keycloak stops sending mail. Create a new secret and send it to the
operator before that date.

## Step 5: Register the app in Exchange Online

Exchange keeps its own record of the app. It needs the object ID of the app's **enterprise application** (service
principal), which differs from the app registration's IDs:

1. In the Entra admin center, open **Identity** → **Applications** → **Enterprise applications**.
2. Remove the default filter if needed, search for `Swiss AI-Hub Keycloak SMTP` and open it.
3. On its **Overview**, note the **Object ID**.

Then, in PowerShell:

```powershell
Connect-ExchangeOnline -UserPrincipalName <your-admin-account>

New-ServicePrincipal `
  -AppId <application-client-id> `
  -ObjectId <enterprise-application-object-id> `
  -DisplayName "Swiss AI-Hub Keycloak SMTP"
```

Check it with `Get-ServicePrincipal | Where-Object DisplayName -eq "Swiss AI-Hub Keycloak SMTP"`.

## Step 6: Give the app the mailbox and allow SMTP AUTH

Still in the same PowerShell session:

```powershell
Add-MailboxPermission `
  -Identity "noreply.ai-hub@contoso.com" `
  -User <enterprise-application-object-id> `
  -AccessRights FullAccess

Set-CASMailbox -Identity "noreply.ai-hub@contoso.com" -SmtpClientAuthenticationDisabled $false
```

The first command limits the app to this one mailbox. The second allows SMTP sign-in for this mailbox even when the
organization turns SMTP AUTH off globally. Check both:

```powershell
Get-MailboxPermission -Identity "noreply.ai-hub@contoso.com" | Where-Object AccessRights -like "*FullAccess*"
Get-CASMailbox -Identity "noreply.ai-hub@contoso.com" | Format-List SmtpClientAuthenticationDisabled
```

`SmtpClientAuthenticationDisabled` must read `False`.

Microsoft can take **up to an hour** to apply permission changes. Until then, the checks below fail with
`535 5.7.3 Authentication unsuccessful`.

## Step 7: Verify the setup

These two checks prove the setup before the platform is involved. Run them from any machine with outbound access to
`login.microsoftonline.com:443` and `smtp.office365.com:587`.

**Get a token.** Replace the three placeholders:

```bash
curl -s -X POST "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token" \
  -d client_id=<application-client-id> \
  --data-urlencode client_secret='<client-secret>' \
  -d scope=https://outlook.office365.com/.default \
  -d grant_type=client_credentials
```

The answer contains an `access_token`. Paste it into a JWT decoder you trust (it is a credential, so not a public
website for production tokens) and check that its `roles` claim contains `SMTP.SendAsApp`. An error code here points to
the app, see [Troubleshooting](#troubleshooting).

**Send a test mail** with the token, using Python's standard library:

```python
import base64, json, smtplib, urllib.parse, urllib.request
from email.message import EmailMessage

TENANT_ID = "<tenant-id>"
CLIENT_ID = "<application-client-id>"
CLIENT_SECRET = "<client-secret>"
SENDER = "noreply.ai-hub@contoso.com"
RECIPIENT = "<your-own-address>"

body = urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "https://outlook.office365.com/.default",
    "grant_type": "client_credentials",
}).encode()
token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
token = json.load(urllib.request.urlopen(token_url, body))["access_token"]

message = EmailMessage()
message["From"], message["To"], message["Subject"] = SENDER, RECIPIENT, "Swiss AI-Hub SMTP test"
message.set_content("If you can read this, the Entra app can send as the mailbox.")

xoauth2 = base64.b64encode(f"user={SENDER}\x01auth=Bearer {token}\x01\x01".encode()).decode()
with smtplib.SMTP("smtp.office365.com", 587) as smtp:
    smtp.starttls()
    smtp.ehlo()
    code, reply = smtp.docmd("AUTH", "XOAUTH2 " + xoauth2)
    if code != 235:
        raise SystemExit(f"Sign-in refused: {code} {reply.decode()}")
    smtp.send_message(message)
print("Sent")
```

Run it with `python3 smtp_test.py`. "Sent" and a mail in your inbox mean the Microsoft side is done. Delete the file
afterwards: it contains the secret.

## Step 8: Send the values to the operator

| Value                   | From   | Becomes                       |
| ----------------------- | ------ | ----------------------------- |
| Directory (tenant) ID   | Step 2 | `KEYCLOAK_SMTP_TENANT_ID`     |
| Application (client) ID | Step 2 | `KEYCLOAK_SMTP_CLIENT_ID`     |
| Client secret value     | Step 4 | `KEYCLOAK_SMTP_CLIENT_SECRET` |
| Sending mailbox address | Step 1 | `KEYCLOAK_SMTP_MAILBOX`       |
| Secret expiry date      | Step 4 | Reminder to renew the secret  |

The tenant ID, client ID and mailbox are not secret. Send the **client secret** only through a password manager share or
another encrypted channel agreed with the operator, never by plain email, chat or ticket.

The operator then follows [Deployment configuration](../#deployment-configuration) and
[Check that mail arrives](../#check-that-mail-arrives).

## Troubleshooting

| Message                                                    | Cause                                                                                              | Fix                                                                                        |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `AADSTS7000215: Invalid client secret`                     | Wrong value (the Secret ID was copied) or expired secret                                           | Create a new secret (step 4) and send it to the operator                                   |
| `AADSTS700016: Application ... was not found in directory` | Wrong tenant ID, or the app lives in another tenant                                                | Use the Directory (tenant) ID of the app's own tenant                                      |
| Token has no `roles` claim                                 | Admin consent missing                                                                              | Grant admin consent (step 3)                                                               |
| `535 5.7.3 Authentication unsuccessful`                    | Service principal not registered, no mailbox permission, SMTP AUTH off, or changes not applied yet | Re-check steps 5 and 6, then wait up to an hour                                            |
| `554 5.2.252 SendAsDenied`                                 | The sender address differs from the mailbox the app has access to                                  | Send the operator the exact mailbox address from step 6                                    |
| Connection timeout on port 587                             | Outbound SMTP blocked by a firewall                                                                | Allow `smtp.office365.com:587` (see [Network requirements](../../7_network_requirements/)) |
