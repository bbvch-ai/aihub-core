---
title: API Tokens
description: Generate, review and revoke personal API tokens to authenticate REST API requests.
---

# API Tokens

Calling the REST API from a script, integration, or command line requires a bearer token. Rather than reusing the
short-lived JWT from your browser session, you create a long-lived personal token (prefixed `sk-`) that authenticates as
your own user, with your own permissions. A token works in every tenant you belong to, until it expires or you revoke
it.

## Manage tokens in the admin interface

Open **API Tokens** from the service menu of the admin interface. The page lists your tokens, newest first, including
expired ones:

| Column    | Meaning                                                                                       |
| --------- | --------------------------------------------------------------------------------------------- |
| Name      | The name you gave the token when you generated it.                                            |
| Created   | When the token was generated.                                                                 |
| Expires   | The expiry date, tagged Active, Expires soon (within seven days), or Expired.                 |
| Last used | When the token last authenticated a request, accurate to about five minutes, or "Never used". |

### Generate a token

1. Click **Generate token**.
2. Enter a name that tells you later what uses the token, for example the script or integration.
3. Choose how long the token stays valid: 30 days, 90 days, 6 months, 1 year, or a custom date.
4. Click **Generate**.

::: danger Copy the token immediately
The token value is shown only once, in the dialog that opens after generating it, and no page or endpoint returns it
again. Copy it before you close the dialog. If you lose it, revoke it and generate a new one.
:::

### Revoke a token

Click the trash icon in the token's row and confirm. Revoking deletes the token permanently and immediately invalidates
any client still using it. Revoke a token as soon as you suspect it has leaked, and revoke tokens you no longer use.

## Use the token

Send the `sk-` token as a bearer credential on every API request:

```bash
curl https://<your-deployment>/api/v1/active/agents/ \
  -H "Authorization: Bearer sk-..."
```

`active` in the path resolves to your active tenant. To act in another tenant you belong to, put its id there instead.

## Manage tokens through the API

The page above is a client of the same endpoints, which scripts can call directly. Creating a token through the API
needs a credential to begin with, so the first one is easiest to generate in the admin interface.

| Operation | Endpoint                                       |
| --------- | ---------------------------------------------- |
| Create    | `POST /api/v1/{tenant_id}/tokens/`             |
| List      | `GET /api/v1/{tenant_id}/tokens/`              |
| Revoke    | `DELETE /api/v1/{tenant_id}/tokens/{token_id}` |

The create endpoint takes a name of 1 to 100 characters and an expiry date that must be a future ISO-8601 datetime:

```json
{
  "name": "my-api-token",
  "expiry_date": "2027-12-31T23:59:59Z"
}
```

A `201` response contains the token value, the only response that ever does:

```json
{
  "id": "...",
  "name": "my-api-token",
  "expiry_date": "2027-12-31T23:59:59Z",
  "token": "sk-..."
}
```

The list endpoint returns each token's `id`, `name`, `created_at`, `expiry_date` and `last_used_at`, but never the token
value. Revoking a token that does not exist or belongs to someone else answers `404`.

::: details Create a token from the Swagger UI without the admin interface
The Swagger UI at `https://<your-deployment>/api/v1/docs` accepts the access token your browser holds after you log in.

1. Open the browser developer tools, switch to the Network tab, and click any request to the API.
2. Under the request headers, find `Authorization: Bearer eyJ...` and copy the value after `Bearer `.
3. In the Swagger UI, click Authorize, paste the value into the HTTPBearer field without a `Bearer ` prefix, and click
   Authorize, then Close.
4. Find `POST /api/v1/{tenant_id}/tokens/` (Create API Token), click Try it out, set `tenant_id` to `active`, provide
   the request body above, and click Execute.

Copy the access token, not the id token. The API validates the `account` audience, which only the access token carries;
an id token (for example from the `oidc.user:...` entry in local storage) fails with `401 ... Invalid token`.
:::
