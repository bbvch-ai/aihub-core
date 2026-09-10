---
title: User and Role Management
description: Define and assign the app roles that grant access to the Swiss AI Hub
---

# User and Role Management

Access to the Swiss AI Hub is granted through **app roles** on the Azure app registration. When a user logs in, Entra ID
includes their assigned app roles in the `roles` claim; Keycloak maps each one to a realm role of the same name.

Two roles take effect in the platform — define both on the app registration and assign them to users.

## Define the app roles

In the app registration, add these app roles (App roles blade, or the manifest). The **value** must match exactly — it
is what Keycloak maps:

| Display name    | Value           | Grants                                                             |
| --------------- | --------------- | ------------------------------------------------------------------ |
| AI-Hub Access   | `AIHubAccess`   | Permission to log in. **Required** — without it, login is denied.  |
| AI-Hub Sysadmin | `AIHubSysAdmin` | Platform administrator + access to admin tools (Dagster, Attu, …). |

Equivalent `appRoles` manifest entries:

```json
"appRoles": [
  {
    "displayName": "AI-Hub Access",
    "value": "AIHubAccess",
    "description": "Allows login to the Swiss AI Hub",
    "allowedMemberTypes": ["User"],
    "isEnabled": true
  },
  {
    "displayName": "AI-Hub Sysadmin",
    "value": "AIHubSysAdmin",
    "description": "Platform administrator and admin tool access",
    "allowedMemberTypes": ["User"],
    "isEnabled": true
  }
]
```

::: warning
`AIHubAccess` is mandatory. Keycloak's login flow denies any user who does not have it, regardless of other roles. Every
user who should reach the platform must be assigned `AIHubAccess`.
:::

## Assign roles to users

Assign the app roles to users or groups on the backing **Enterprise Application** — see Microsoft's
[Assign users and groups to an application](https://learn.microsoft.com/entra/identity/enterprise-apps/assign-user-or-group-access-portal).
Assigned app roles appear automatically in the token's `roles` claim; no optional-claims configuration is needed.

A typical assignment:

- **All platform users** → `AIHubAccess`
- **Platform administrators** → `AIHubAccess` **and** `AIHubSysAdmin`

::: tip
Assigning a role to a **group** (rather than individual users) requires a Microsoft Entra ID P1 or P2 license and
`"Group"` in the role's `allowedMemberTypes`. Per-user assignment works on any tier.
:::
