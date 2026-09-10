---
title: Microsoft Entra ID
description: Federate the Swiss AI Hub to Microsoft Entra ID (Azure AD) via Keycloak
---

# Microsoft Entra ID

Keycloak's `aihub` realm ships with a Microsoft Entra ID provider (alias `azure-ad`) already defined. To activate it,
create an **App Registration** in your Entra tenant configured as the realm expects, define its app roles, and assign
users.

Entra ID is integrated as an
[OpenID Connect v1.0 identity provider](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker_oidc).
Keycloak validates the ID token against Entra's JWKS endpoint and authenticates with a client secret plus PKCE (`S256`)
— there is nothing to choose here, the realm is preconfigured for OIDC.

## Pages

- **[Azure App Registration](./1_azure_app_registration/)** — create the app registration and configure it exactly as
  Keycloak expects (redirect URI, scopes, client secret).
- **[User and Role Management](./2_user_and_role_management/)** — define the AI-Hub app roles and assign them to users
  so they can log in and gain the right access.
