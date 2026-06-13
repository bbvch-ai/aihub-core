---
title: Azure App Registration
description: Configure an Entra ID app registration so Keycloak accepts it as an identity provider
---

# Azure App Registration

Keycloak's `aihub` realm ships with a Microsoft Entra ID provider (alias `azure-ad`) already defined. To activate it,
create an **App Registration** in your Entra tenant configured as described below, then hand three values to the
platform.

::: info Prerequisites
An Entra ID tenant and permission to create app registrations and assign enterprise application roles. Creating an app
registration itself is standard Entra administration — see
[Microsoft's documentation](https://learn.microsoft.com/entra/identity-platform/quickstart-register-app). This page
documents only the AI-Hub-specific configuration.
:::

## What the platform needs from Azure

After configuring the app registration, set these three variables in your `.env` file. Keycloak reads them at startup
and injects them into the `azure-ad` provider:

| Variable                       | Source in Azure                         |
| ------------------------------ | --------------------------------------- |
| `KEYCLOAK_AZURE_CLIENT_ID`     | Application (client) ID of the app reg. |
| `KEYCLOAK_AZURE_TENANT_ID`     | Directory (tenant) ID                   |
| `KEYCLOAK_AZURE_CLIENT_SECRET` | Value of a client secret you create     |

## Required configuration

### Redirect URI

Register this exact **Web** redirect URI (it is Keycloak's broker endpoint for the `azure-ad` alias on the `aihub`
realm):

```text
https://auth.<DOMAIN>/realms/aihub/broker/azure-ad/endpoint
```

Replace `<DOMAIN>` with your deployment domain. For local development, also add:

```text
http://localhost:8180/realms/aihub/broker/azure-ad/endpoint
```

### API permissions

Keycloak requests the standard OpenID Connect scopes — no Microsoft Graph permissions are required:

```text
openid email profile
```

These provide the claims Keycloak maps to the user: `email`, `given_name`, `family_name`, and `preferred_username`.

### Client secret

Create a client secret and copy its **value** (not the secret ID) into `KEYCLOAK_AZURE_CLIENT_SECRET`. Keycloak
authenticates to Azure with this secret (`client_secret_post`) and adds PKCE (`S256`) on top.

::: warning
Client secrets expire. Set a calendar reminder before the expiry date and rotate the secret by updating
`KEYCLOAK_AZURE_CLIENT_SECRET` — an expired secret breaks all logins through this provider.
:::

## Next step

The app registration is not usable until you define and assign its **app roles** — see
[User and Role Management](../2_user_and_role_management/). At minimum, users need the `AIHubAccess` role to log in.

::: tip Operators don't edit the provider
The `azure-ad` provider and its claim mappers are defined in
`infra/deployment/templates/configs/keycloak/managed/50-identity-providers.json.j2`. You normally only set the three
`.env` variables — no Keycloak configuration is needed. This file is reconciled on every stack start: changes reach
running deployments automatically, and manual admin-console edits to the provider are overwritten.
:::

::: tip Multi-tenant deployments
A single deployment can federate multiple organizations, each with its own app registration mapped to a separate tenant
group in Keycloak. This is an advanced, non-default setup; see the comments in `50-identity-providers.json.j2` for the
hardcoded-group mapper pattern.
:::
