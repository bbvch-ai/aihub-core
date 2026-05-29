---
title: API Tokens
description: Generate a personal API token to authenticate REST API requests.
---

# API Tokens

Calling the REST API from a script, integration, or command line requires a bearer token. Rather than reusing the
short-lived JWT from your browser session, you create a long-lived personal token (prefixed `sk-`) that authenticates as
your own user. This page walks through generating one entirely from the browser using the built-in Swagger UI.

There is no dedicated screen for this in the admin interface yet, so the Swagger UI at `/api/v1/docs` is the supported
way to create a token interactively.

## Get a session token

The token endpoints are themselves protected, so you first need to authenticate the request that creates your `sk-`
token. The simplest credential is the access token your browser already holds after you log in.

1. Log in to the platform in your browser.
2. Open the browser developer tools, switch to the Network tab, and click any request to the API.
3. Under the request headers, find `Authorization: Bearer eyJ...` and copy the value after `Bearer `.

::: warning Copy the access token, not the id token
The API validates the `account` audience, which only the access token carries. If you copy the id token (for example
from the `oidc.user:...` entry in local storage) the request fails with `401 ... Invalid token`. The Network tab always
shows the access token, so it is the most reliable source.

To check a token, decode its payload and confirm `"typ": "Bearer"` and an `"aud"` that includes `"account"`.
:::

## Create the token in Swagger

Open the Swagger UI for the deployment:

```
https://<your-deployment>/api/v1/docs
```

1. Click Authorize (top right).
2. Paste the access token into the HTTPBearer field. Enter the token only, without a `Bearer ` prefix.
3. Click Authorize, then Close.
4. Find `POST /api/v1/{tenant_id}/tokens/` (Create API Token) and click Try it out.
5. Set `tenant_id` to `active`, which resolves to your active tenant.
6. Provide a request body. The name is 1 to 100 characters and the expiry date must be a future ISO-8601 datetime:

   ```json
   {
     "name": "my-api-token",
     "expiry_date": "2026-12-31T23:59:59Z"
   }
   ```

7. Click Execute.

A `201` response contains the token:

```json
{
  "id": "...",
  "name": "my-api-token",
  "expiry_date": "2026-12-31T23:59:59Z",
  "token": "sk-..."
}
```

::: danger Copy the token immediately
The `token` value is returned only once, at creation. It is never shown again. If you lose it, revoke the token and
create a new one.
:::

## Use the token

Send the `sk-` token as a bearer credential on every API request:

```bash
curl https://<your-deployment>/api/v1/active/agents/ \
  -H "Authorization: Bearer sk-..."
```

Unlike the browser session token, the `sk-` token stays valid until its expiry date, so it suits scripts and long-lived
integrations.

## List and revoke tokens

The same controller exposes the rest of the token lifecycle, also callable from the Swagger UI:

| Operation | Endpoint                                |
| --------- | --------------------------------------- |
| Create    | `POST /api/v1/{tenant_id}/tokens/`      |
| List      | `GET /api/v1/{tenant_id}/tokens/`       |
| Revoke    | `DELETE /api/v1/{tenant_id}/tokens/{token_id}` |

The list endpoint returns each token's id, name, and expiry date, but never the token value. Revoking a token deletes it
permanently and immediately invalidates any client still using it.
