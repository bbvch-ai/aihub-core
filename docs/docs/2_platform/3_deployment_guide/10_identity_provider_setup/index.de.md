---
title: Einrichtung des Identitätsanbieters
description: Verbindung eines externen Identitätsanbieters mit dem Swiss AI Hub über Keycloak
source_sha: d02098df6b97875deee207127cc2631e44b7bff868c429899a2b3be7cb2af3bc
---

# Einrichtung des Identitätsanbieters

Der Swiss AI Hub verwaltet Benutzeranmeldeinformationen nicht selbst. Er verwendet **Keycloak als Identitätsbroker**,
der an den Identitätsanbieter (IdP) Ihrer Organisation föderiert. Benutzer melden sich mit ihrem bestehenden
Unternehmenskonto an; Keycloak validiert die Anmeldung und stellt der Plattform einen Token aus.

Keycloak kann Anbieter über drei Protokolle sowie eine Reihe von integrierten sozialen Anbietern vermitteln – eine
vollständige Liste finden Sie in der
[Keycloak-Dokumentation zum Identitätsbrokering](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker):

- [OpenID Connect v1.0](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker_oidc)
- [OAuth v2](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker_oauth)
- [SAML v2.0](https://www.keycloak.org/docs/latest/server_admin/index.html#saml-v2-0-identity-providers)

Die Plattform schränkt das Protokoll nicht ein – jeder aktivierte, sichtbare Anbieter, der im `aihub`-Realm konfiguriert
ist, erscheint auf der Anmeldeseite. Die einzige praktische Anforderung für den **rollenbasierten Zugriff** ist, dass
der Anbieter die AI-Hub-Rollenwerte in einem Claim ausgibt, den Keycloak Realm-Rollen zuordnet (siehe
[Benutzer- und Rollenverwaltung](./1_azure_entra_id/2_user_and_role_management/)).

Die folgenden Seiten führen Sie durch die IdPs, die wir vorkonfigurieren und unterstützen. Jede Seite erklärt, wie Sie
den Anbieter so einrichten, dass er den Erwartungen des Keycloak `aihub`-Realms entspricht.

## Unterstützte Anbieter

- **[Microsoft Entra ID (Azure AD)](./1_azure_entra_id/)** – Erstellung der App-Registrierung und Verwaltung ihrer
  Benutzer und Rollen.

::: tip
Dieser Abschnitt ist operativ. Für das konzeptionelle Modell – wie Keycloak Tokens validiert, Claims zuordnet und Rollen
durchsetzt – siehe [Authentifizierung und Autorisierung](../../20_security/1_authentication/).
:::
