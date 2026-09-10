---
title: Azure App-Registrierung
description: Konfigurieren Sie eine Entra ID-App-Registrierung, damit Keycloak sie als Identitätsprovider akzeptiert.
source_sha: 1c636c6918594e760dd319d0b3c9f004ba1666c5f0e4236c9d22b7277df59960
---

# Azure App-Registrierung

Der `aihub`-Realm von Keycloak wird mit einem bereits definierten Microsoft Entra ID-Provider (Alias `azure-ad`)
ausgeliefert. Um ihn zu aktivieren, erstellen Sie eine **App-Registrierung** in Ihrem Entra-Tenant, wie unten
beschrieben konfiguriert, und übergeben Sie dann drei Werte an die Plattform.

::: info Voraussetzungen
Ein Entra ID-Tenant und die Berechtigung, App-Registrierungen zu erstellen und Unternehmensanwendungsrollen zuzuweisen.
Das Erstellen einer App-Registrierung ist eine Standard-Entra-Administration — siehe
[die Dokumentation von Microsoft](https://learn.microsoft.com/entra/identity-platform/quickstart-register-app). Diese
Seite dokumentiert nur die AI-Hub-spezifische Konfiguration.
:::

## Was die Plattform von Azure benötigt

Nach der Konfiguration der App-Registrierung legen Sie diese drei Variablen in Ihrer `.env`-Datei fest. Keycloak liest
sie beim Start und injiziert sie in den `azure-ad`-Provider:

| Variable                       | Quelle in Azure                                |
| ------------------------------ | ---------------------------------------------- |
| `KEYCLOAK_AZURE_CLIENT_ID`     | Anwendungs-(Client-)ID der App-Registrierung   |
| `KEYCLOAK_AZURE_TENANT_ID`     | Verzeichnis-(Tenant-)ID                        |
| `KEYCLOAK_AZURE_CLIENT_SECRET` | Wert eines von Ihnen erstellten Client-Secrets |

## Erforderliche Konfiguration

### Redirect-URI

Registrieren Sie diese exakte **Web**-Redirect-URI (es ist Keycloaks Broker-Endpunkt für den `azure-ad`-Alias im
`aihub`-Realm):

```text
https://auth.<DOMAIN>/realms/aihub/broker/azure-ad/endpoint
```

Ersetzen Sie `<DOMAIN>` durch Ihre Deployment-Domain. Für die lokale Entwicklung fügen Sie auch hinzu:

```text
http://localhost:8180/realms/aihub/broker/azure-ad/endpoint
```

### API-Berechtigungen

Keycloak fordert die Standard-OpenID Connect Scopes an — keine Microsoft Graph-Berechtigungen sind erforderlich:

```text
openid email profile
```

Diese stellen die Claims bereit, die Keycloak dem Benutzer zuordnet: `email`, `given_name`, `family_name` und
`preferred_username`.

### Client-Secret

Erstellen Sie ein Client-Secret und kopieren Sie dessen **Wert** (nicht die Secret-ID) in
`KEYCLOAK_AZURE_CLIENT_SECRET`. Keycloak authentifiziert sich mit diesem Secret (`client_secret_post`) bei Azure und
fügt zusätzlich PKCE (`S256`) hinzu.

::: warning
Client-Secrets laufen ab. Setzen Sie eine Kalendererinnerung vor dem Ablaufdatum und rotieren Sie das Secret, indem Sie
`KEYCLOAK_AZURE_CLIENT_SECRET` aktualisieren — ein abgelaufenes Secret unterbricht alle Anmeldungen über diesen
Provider.
:::

## Nächster Schritt

Die App-Registrierung ist erst nutzbar, wenn Sie ihre **App-Rollen** definieren und zuweisen — siehe
[Benutzer- und Rollenmanagement](../2_user_and_role_management/). Mindestens benötigen Benutzer die `AIHubAccess`-Rolle,
um sich anzumelden.

::: tip Operatoren bearbeiten den Provider nicht
Der `azure-ad`-Provider und seine Claim-Mapper sind in
`infra/deployment/templates/configs/keycloak/bootstrap/identity-providers.json.j2` definiert. Sie setzen normalerweise
nur die drei `.env`-Variablen — es ist keine Keycloak-Konfiguration erforderlich. Dies ist Bootstrap-Konfiguration: Sie
wird vom Realm-Import **nur beim ersten Start** angewendet, sodass manuelle Admin-Konsolen-Bearbeitungen am Provider
Neustarts überstehen und Änderungen an der Datei ein bereits initialisiertes Deployment nur über die Admin Console (oder
eine frische Realm-Datenbank) erreichen.
:::

::: tip Multi-Tenant-Deployments
Ein einzelnes Deployment kann mehrere Organisationen föderieren, jede mit ihrer eigenen App-Registrierung, die einer
separaten Tenant-Gruppe in Keycloak zugeordnet ist. Dies ist ein erweitertes, nicht standardmäßiges Setup; siehe die
Kommentare in `bootstrap/identity-providers.json.j2` für das Hardcoded-Group-Mapper-Muster.
:::
