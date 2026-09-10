---
title: Identity Provider Setup
description: Connect an external identity provider to the Swiss AI Hub through Keycloak
---

# Identity Provider Setup

The Swiss AI Hub does not manage user credentials itself. It uses **Keycloak as an identity broker** that federates to
your organization's identity provider (IdP). Users sign in with their existing corporate account; Keycloak validates the
login and issues the platform a token.

Keycloak can broker providers over three protocols, plus a range of built-in social providers — see the
[Keycloak identity brokering documentation](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker)
for the full list:

- [OpenID Connect v1.0](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker_oidc)
- [OAuth v2](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker_oauth)
- [SAML v2.0](https://www.keycloak.org/docs/latest/server_admin/index.html#saml-v2-0-identity-providers)

The platform places no restriction on the protocol — any enabled, visible provider configured in the `aihub` realm
appears on the login page. The one practical requirement for **role-based access** is that the provider emits the AI-Hub
role values in a claim that Keycloak maps to realm roles (see
[User and Role Management](./1_azure_entra_id/2_user_and_role_management/)).

The pages below walk through the IdPs we configure and support out of the box. Each one explains how to set up the
provider so it matches what the Keycloak `aihub` realm expects.

## Supported providers

- **[Microsoft Entra ID (Azure AD)](./1_azure_entra_id/)** — create the app registration and manage its users and roles.

::: tip
This section is operational. For the conceptual model — how Keycloak validates tokens, maps claims, and enforces roles —
see [Authentication and Authorization](../../20_security/1_authentication/).
:::
