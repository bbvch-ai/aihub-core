---
title: Azure App-Registrierung
description: Konfigurieren Sie eine Entra ID App-Registrierung, damit Keycloak sie als Identitätsanbieter akzeptiert
source_sha: 7658b23b473fe0f88018be7d4e2a72d7ecf3b677670bcc4d081a0b73ae9e9240
---

# Azure App-Registrierung

Keycloaks `aihub`-Realm wird mit einem bereits definierten Microsoft Entra ID-Anbieter (Alias `azure-ad`) ausgeliefert.
Um ihn zu aktivieren, erstellen Sie eine **App-Registrierung** in Ihrem Entra-Mandanten, die wie unten beschrieben
konfiguriert ist, und übergeben Sie dann drei Werte an die Plattform.

::: info Voraussetzungen
Ein Entra ID-Mandant und die Berechtigung, App-Registrierungen zu erstellen und Unternehmensanwendungsrollen zuzuweisen.
Das Erstellen einer App-Registrierung selbst ist eine Standard-Entra-Administration – siehe
[Microsofts Dokumentation](https://learn.microsoft.com/entra/identity-platform/quickstart-register-app). Diese Seite
dokumentiert nur die AI-Hub-spezifische Konfiguration.
:::

## Was die Plattform von Azure benötigt

Nach der Konfiguration der App-Registrierung legen Sie diese drei Variablen in Ihrer `.env`-Datei fest. Keycloak liest
sie beim Start und injiziert sie in den `azure-ad`-Anbieter:

| Variable                       | Quelle in Azure                                |
| :----------------------------- | :--------------------------------------------- |
| `KEYCLOAK_AZURE_CLIENT_ID`     | Anwendungs-(Client-)ID der App-Registrierung   |
| `KEYCLOAK_AZURE_TENANT_ID`     | Verzeichnis-(Mandanten-)ID                     |
| `KEYCLOAK_AZURE_CLIENT_SECRET` | Wert eines von Ihnen erstellten Client-Secrets |

## Erforderliche Konfiguration

### Umleitungs-URI

Registrieren Sie diese exakte **Web**-Umleitungs-URI (es ist Keycloaks Broker-Endpunkt für den `azure-ad`-Alias im
`aihub`-Realm):

```text
https://auth.<DOMAIN>/realms/aihub/broker/azure-ad/endpoint
```

Ersetzen Sie `<DOMAIN>` durch Ihre Deployment-Domain. Für die lokale Entwicklung fügen Sie zusätzlich hinzu:

```text
http://localhost:8180/realms/aihub/broker/azure-ad/endpoint
```

### API-Berechtigungen

Keycloak fordert die Standard-OpenID Connect-Scopes an – keine Microsoft Graph-Berechtigungen sind erforderlich:

```text
openid email profile
```

Diese liefern die Claims, die Keycloak dem Benutzer zuordnet: `email`, `given_name`, `family_name` und
`preferred_username`.

### Client-Secret

Erstellen Sie ein Client-Secret und kopieren Sie dessen **Wert** (nicht die Secret-ID) in
`KEYCLOAK_AZURE_CLIENT_SECRET`. Keycloak authentifiziert sich gegenüber Azure mit diesem Secret (`client_secret_post`)
und fügt zusätzlich PKCE (`S256`) hinzu.

::: warning
Client-Secrets verfallen. Erstellen Sie eine Kalendererinnerung vor dem Ablaufdatum und rotieren Sie das Secret, indem
Sie `KEYCLOAK_AZURE_CLIENT_SECRET` aktualisieren – ein abgelaufenes Secret unterbricht alle Anmeldungen über diesen
Anbieter.
:::

## Nächster Schritt

Die App-Registrierung ist erst nutzbar, wenn Sie deren **App-Rollen** definieren und zuweisen – siehe
[Benutzer- und Rollenverwaltung](../2_user_and_role_management/). Mindestens benötigen Benutzer die Rolle `AIHubAccess`,
um sich anzumelden.

::: tip Betreiber bearbeiten den Anbieter nicht
Der `azure-ad`-Anbieter und seine Claim-Mapper sind in
`infra/deployment/templates/configs/keycloak-identity-providers.json.j2` definiert. Normalerweise setzen Sie nur die
drei `.env`-Variablen – es ist keine Keycloak-Konfiguration erforderlich.
:::

::: tip Multi-Tenant-Deployments
Ein einzelnes Deployment kann mehrere Organisationen föderieren, jede mit ihrer eigenen App-Registrierung, die einer
separaten Mandantengruppe in Keycloak zugeordnet ist. Dies ist eine erweiterte, nicht standardmäßige Einrichtung; siehe
die Kommentare in `keycloak-identity-providers.json.j2` für das hardcoded-group-Mapper-Muster.
:::
