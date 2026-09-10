---
title: Microsoft Entra ID
description: Föderieren Sie den Swiss AI Hub über Keycloak mit Microsoft Entra ID (Azure AD)
source_sha: fd65cc5495094842db53461762023478e1cf5f11600a8652f18042b683c8bbe4
---

# Microsoft Entra ID

Das `aihub`-Realm von Keycloak wird mit einem bereits definierten Microsoft Entra ID-Provider (Alias `azure-ad`)
ausgeliefert. Um ihn zu aktivieren, erstellen Sie eine **App-Registrierung** in Ihrem Entra-Tenant, konfiguriert, wie
das Realm es erwartet, definieren Sie dessen App-Rollen und weisen Sie Benutzern diese zu.

Entra ID ist als ein
[OpenID Connect v1.0 Identitätsprovider](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker_oidc)
integriert. Keycloak validiert das ID-Token anhand des JWKS-Endpoints von Entra und authentifiziert sich mit einem
Client-Geheimnis plus PKCE (`S256`) — hier gibt es nichts zu wählen, das Realm ist für OIDC vorkonfiguriert.

## Seiten

- **[Azure App-Registrierung](./1_azure_app_registration/)** — erstellen Sie die App-Registrierung und konfigurieren Sie
  diese genau so, wie Keycloak es erwartet (Redirect-URI, Scopes, Client-Geheimnis).
- **[Benutzer- und Rollenverwaltung](./2_user_and_role_management/)** — definieren Sie die AI-Hub App-Rollen und weisen
  Sie diese Benutzern zu, damit diese sich anmelden und den richtigen Zugang erhalten können.
