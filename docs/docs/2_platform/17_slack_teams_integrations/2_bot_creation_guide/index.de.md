---
title: Manuelle Einrichtungsanleitung für Bot-Erstellung
source_sha: ed66a86634148988baa8f04af9227d9dcb72d28689d3ba36b15416c08373b830
---

# Manuelle Einrichtungsanleitung für Bot-Erstellung :robot: :wrench:

::: info **Kurz gesagt – Wozu dient diese Anleitung?**
Dieses umfassende Handbuch bietet **Schritt-für-Schritt-Anleitungen zur manuellen Erstellung und Konfiguration von
Bots** mit Microsoft Teams- und Slack-Integration. Nutzen Sie diese Anleitung, wenn Sie neue Bots von Grund auf
erstellen, Azure Bot Framework-Kanäle konfigurieren oder bestehende Bot-Deployments beheben müssen. Sie deckt alles ab,
von der Einrichtung des Teams Developer Portal über die MongoDB-Konfiguration bis hin zur Slack OAuth-Integration.
:::

::: tip Automatisierte Einrichtung verfügbar
Bevor Sie mit der manuellen Einrichtung fortfahren, ziehen Sie das **automatisierte Setup-Skript** in Betracht, das die
meisten dieser Schritte für Sie erledigt:

```bash
python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "my-ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/messages" \
    --mongo-connection-string "mongodb://localhost:27017"
```

**Wann das automatisierte Skript verwendet werden sollte:**

- Erstellung neuer Bots für das Production-Deployment
- Standard-Einzel-Bot- oder Multi-Bot-Konfigurationen
- Schnelleinrichtung ohne Anpassung

**Wann diese manuelle Anleitung verwendet werden sollte:**

- Behebung von Fehlern bei der automatisierten Einrichtung
- Detailliertes Verständnis der Bot-Konfiguration
- Erstellung benutzerdefinierter oder nicht standardmäßiger Konfigurationen
- Verständnis der Bot-Integration

Details zur automatisierten Einrichtung finden Sie in der [Anleitung zur Azure Bot Service-Integration](../1_setup/).
:::

## Zugehörige Dokumentation :books:

- **[Übersicht über Slack- und Teams-Integrationen](../)** – High-Level-Konzepte und geschäftlicher Nutzen
- **[Azure Bot Service-Integration](../1_setup/)** – Anleitung zur automatisierten Einrichtung
- **[Entwicklerhandbuch für Swiss AI Hub Bot](../../../6_code_deep_dive/aihub_bot/)** – Technische
  Implementierungsdetails
- **[Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** –
  Mensch-KI-Kollaborations-Workflows

## Wichtige Terminologie :book:

Das Verständnis dieser Begriffe ist entscheidend für eine erfolgreiche Bot-Konfiguration:

| Begriff                              | Definition                                                                                                                                                                                                                                           |
| :----------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bot Framework Messaging Endpoint** | Die einzelne öffentliche URL, an die der Azure Bot Service ALLE Bot-Nachrichten sendet. Immer `/api/v1/messages`. Konfiguriert im Teams Developer Portal (Schritt 3).                                                                                |
| **MongoDB `path`-Feld**              | Interner Routing-Pfad, der bestimmt, welche Bot-Implementierung eine Konversation verarbeitet. Beispiele: `/api/v1/agent/chat/completions/...` oder `/api/v1/openai/chat/completions`. Konfiguriert in der MongoDB-Sammlung `bot_paths` (Schritt 7). |
| **App ID / Client ID**               | Azure AD Anwendungsbezeichner (UUID-Format). Derselbe Wert wird als Bot ID und in MongoDB `credentials.APP_ID` verwendet.                                                                                                                            |
| **Client Secret / App Password**     | Azure AD Anwendungsgeheimnis. In MongoDB als `credentials.APP_PASSWORD` gespeichert. Läuft ab und muss rotiert werden.                                                                                                                               |
| **Tenant ID**                        | Microsoft 365 Tenant-Bezeichner. Erforderlich für SingleTenant-Bots, gespeichert als `credentials.APP_TENANTID`.                                                                                                                                     |
| **Bot-in-the-Loop**                  | Muster, bei dem KI-Agents während der Workflow-Ausführung menschliche Eingaben über Slack-Kanäle anfordern.                                                                                                                                          |
| **Slack Bot OAuth Token**            | Token für die Slack-Integration (Format: `xoxb-...`). In MongoDB als `slack_token` gespeichert.                                                                                                                                                      |

::: warning Wichtiger Unterschied
**Bot Framework Messaging Endpoint** (`/api/v1/messages`) ≠ **MongoDB `path`-Feld** (z. B.
`/api/v1/agent/chat/completions/...`)

Dies sind zwei verschiedene Konzepte, die unterschiedlichen Zwecken dienen. Der Messaging Endpoint ist der Ort, an den
der Azure Bot Service Nachrichten sendet. Das `path`-Feld bestimmt, wie diese Nachrichten intern verarbeitet werden.
:::

## Voraussetzungen :clipboard:

Bevor Sie beginnen, stellen Sie sicher, dass Sie Zugang zu folgendem haben:

- **Microsoft Teams Developer Portal** – Für die Erstellung von Teams-Apps und Bots
- **MongoDB-Datenbank** mit `bot_paths`-Sammlung – Zum Speichern der Bot-Konfiguration
- **Azure Bot Framework** – Für die Multi-Channel-Bot-Verwaltung
- **Slack Workspace** mit Admin-Berechtigungen – Für die Slack-Integration

______________________________________________________________________

## Teil 1: Einrichtung des Teams Developer Portal :microsoft:

### Schritt 1: App mit grundlegenden Informationen erstellen

1. Navigieren Sie zum [Teams Developer Portal](https://dev.teams.microsoft.com/)
2. Klicken Sie auf **„Apps“** → **„Neue App“**
3. Füllen Sie die grundlegenden Informationen aus:
   - App-Name
   - Kurzbeschreibung
   - Vollständige Beschreibung
   - Entwicklerinformationen
   - App-URLs
   - Anwendungs- (Client-) ID (falls erforderlich generieren)

### Schritt 2: Berechtigungen konfigurieren

1. Gehen Sie zu **„App-Features“** → **„Bot“**
2. Legen Sie die erforderlichen Berechtigungen fest:
   - **Nachricht lesen** in Chat/Team
   - **Nachricht senden** in Chat/Team
3. Berechtigungsänderungen speichern

### Schritt 3: Neuen Bot erstellen

1. Navigieren Sie in der App zum Abschnitt **„Bot“**
2. Klicken Sie auf **„Einrichten“** oder **„Neuen Bot erstellen“**
3. Geben Sie die **Bot Framework Messaging Endpoint URL** ein:
   - Format: `https://your-domain.com/api/v1/messages`
   - Dies ist der Standard-Endpunkt des Azure Bot Service
   - Muss öffentlich über das Internet zugänglich sein
   - Für die lokale Entwicklung verwenden Sie Azure DevTunnel oder ngrok
4. **Notieren Sie die Bot ID** für die spätere Verwendung

::: warning Bot Framework Endpoint vs. MongoDB-Pfad
**WICHTIGER UNTERSCHIED:**

- **Bot Framework Messaging Endpoint** (`/api/v1/messages`): Der einzige Einstiegspunkt, an den der Azure Bot Service
  ALLE Bot-Nachrichten sendet. Dies wird hier im Teams Developer Portal konfiguriert.

- **MongoDB `path`-Feld** (z. B. `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`): Interner
  Routing-Pfad, der bestimmt, welche Bot-Implementierung die Konversation verarbeitet. Dies wird in MongoDB (Schritt 7)
  konfiguriert und ermöglicht die Koexistenz mehrerer Bots.

**So funktioniert es:**

1. Der Azure Bot Service sendet Nachrichten an `/api/v1/messages`
2. Der Swiss AI Hub sucht den `path` der Konversation in der MongoDB-Sammlung `bot_paths`
3. Die Anfrage wird an die spezifische Bot-Implementierung weitergeleitet

**Beispiel:**

- Teams Developer Portal Endpoint: `https://my-domain.com/api/v1/messages`
- MongoDB-Pfad für Agent Bot: `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
- MongoDB-Pfad für OpenAI Bot: `/api/v1/openai/chat/completions`

Diese müssen NICHT übereinstimmen! Der Messaging Endpoint ist immer `/api/v1/messages`.
:::

::: tip Lokale Entwicklung
Für die lokale Entwicklung stellen Sie Ihren Bot-Server über Azure DevTunnel bereit:

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Use the https URL (e.g., https://abc123-8000.devtunnels.ms/api/v1/messages)
```

Ein detailliertes Setup für die lokale Entwicklung finden Sie im
[Entwicklerhandbuch](../../../6_code_deep_dive/aihub_bot/).
:::

### Schritt 4: Client Secret erstellen

1. Suchen Sie in der Bot-Konfiguration nach **„Client Secrets“**
2. Klicken Sie auf **„Client Secret hinzufügen“**
3. **WICHTIG**: Kopieren und speichern Sie das Client Secret sofort sicher
   - Secret-Format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Sie werden es danach nicht wieder anzeigen können
4. Notieren Sie das Ablaufdatum des Secrets

::: danger Sicherheitswarnung
Client Secrets werden nur einmal zum Zeitpunkt der Erstellung angezeigt. Speichern Sie sie sofort sicher in einem
Passwort-Manager oder einem Secrets Vault. Gehen sie verloren, müssen Sie ein neues Secret generieren und Ihre
MongoDB-Konfiguration aktualisieren.
:::

### Schritt 5: Bot zur App hinzufügen

1. Navigieren Sie zurück zur App-Übersicht
2. Bestätigen Sie, dass der Bot unter **„App-Features“** aufgeführt ist
3. Überprüfen Sie, ob die Bot-ID mit der in Schritt 3 erstellten übereinstimmt

### Schritt 6: App in der Organisation veröffentlichen

1. Gehen Sie zu **„Veröffentlichen“** → **„In Organisation veröffentlichen“**
2. Überprüfen Sie alle Konfigurationen
3. Klicken Sie auf **„Veröffentlichen“**
4. Warten Sie auf die Admin-Genehmigung (falls erforderlich)
5. Sobald genehmigt, notieren Sie die **App-/Client-ID** und die **Tenant ID**

______________________________________________________________________

## Teil 2: MongoDB-Konfiguration :floppy_disk:

### Schritt 7: Bot-Pfad-Eintrag hinzufügen

Fügen Sie der `bot_paths`-Sammlung ein neues Dokument mit der folgenden Struktur hinzu:

```json
{
  "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json",
  "credentials": {
    "APP_TYPE": "SingleTenant",
    "APP_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "APP_PASSWORD": "xxx8Q~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "APP_TENANTID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "system_message": "You are a helpful AI assistant.",
  "slack_token": ""
}
```

**Erforderliche Felder:**

- `path`: Der **interne Routing-Pfad** für diese spezifische Bot-Implementierung
  - **Dies ist NICHT der Bot Framework Messaging Endpoint** (der immer `/api/v1/messages` ist)
  - Dies bestimmt, welcher Bot-Handler Konversationen verarbeitet
  - Beispiele:
    - `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json` – Agent-basierter Bot
    - `/api/v1/openai/chat/completions` – Direkter OpenAI-Bot
    - `/api/v1/bitl/chat/completions` – Bot-in-the-Loop-Bot
- `credentials`: Objekt mit Azure Bot-Authentifizierung
  - `APP_TYPE`: Authentifizierungstyp (`„SingleTenant“` oder `„MultiTenant“`)
  - `APP_ID`: Teams App Client-ID aus Schritt 6
  - `APP_PASSWORD`: Client Secret aus Schritt 4
  - `APP_TENANTID`: Microsoft 365 Tenant ID aus Schritt 6 (erforderlich für SingleTenant)
- `system_message`: Standard-Systemnachricht/Anweisungen für den Bot
- `slack_token`: Zunächst leerer String (wird in Schritt 14 für die Slack-Integration befüllt)

::: tip Multi-Bot-Konfiguration
Sie können **mehrere Bot-Implementierungen** mit unterschiedlichen `path`-Werten haben, die alle denselben Bot Framework
Messaging Endpoint (`/api/v1/messages`) nutzen:

**Agent-basierter Bot für den Kundensupport:**

```json
{
  "path": "/api/v1/agent/chat/completions/CustomerSupportAgent/prod/json",
  "credentials": { "APP_ID": "xxx", "APP_PASSWORD": "xxx", "APP_TENANTID": "xxx", "APP_TYPE": "SingleTenant" },
  "system_message": "You are a customer support assistant."
}
```

**OpenAI-basierter Bot für allgemeine Anfragen:**

```json
{
  "path": "/api/v1/openai/chat/completions",
  "credentials": { "APP_ID": "xxx", "APP_PASSWORD": "xxx", "APP_TENANTID": "xxx", "APP_TYPE": "SingleTenant" },
  "system_message": "You are a helpful AI assistant."
}
```

Jede Konversation ist einem `path` zugeordnet, der ihre Bot-Implementierung und ihr Verhalten bestimmt.
:::

::: tip Konfigurationstipp
Verwenden Sie beschreibende Pfadnamen, die den Agent oder die Funktionalität angeben, um die Verwaltung mehrerer Bots zu
erleichtern. Zum Beispiel identifiziert `/api/v1/agent/chat/completions/CustomerSupportAgent/production/json` den Zweck
des Bots eindeutig.
:::

______________________________________________________________________

## Teil 3: Bot Framework & Slack-Integration :slack:

### Schritt 8: Slack-App erstellen

1. Navigieren Sie zu [Slack API Apps](https://api.slack.com/apps)
2. Klicken Sie auf **„Neue App erstellen“**
3. Wählen Sie **„Von Grund auf neu“**
4. Geben Sie Ihrer App einen Namen (z. B. „Mein Bot-Name“)
5. Wählen Sie den Workspace aus, in dem Sie die App entwickeln möchten
6. Klicken Sie auf **„App erstellen“**

### Schritt 8.5: App Home-Einstellungen konfigurieren

1. Gehen Sie zu den App Home-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/app-home`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/app-home`
2. Im Abschnitt **„Tabs anzeigen“**:
   - Schalten Sie **„Meinen Bot immer als online anzeigen“** auf **EIN**
   - Schalten Sie **„Home Tab“** auf **EIN**
3. Im Abschnitt **„Nachrichten-Tab“**:
   - **Lassen Sie den „Nachrichten-Tab“ deaktiviert** – Der Bot interagiert stattdessen über Kanäle und
     Direktnachrichten
   - Deaktivieren Sie „Benutzern erlauben, Slash-Befehle und Nachrichten vom Nachrichten-Tab zu senden“ (falls sichtbar)
4. Klicken Sie auf **„Änderungen speichern“**, falls dazu aufgefordert

::: info Nachrichten-Tab-Konfiguration
Der Nachrichten-Tab ist in der Regel deaktiviert, wenn das Bot Framework verwendet wird, da der Bot über Kanäle,
Gruppenchats und Direktnachrichten kommuniziert und nicht über den Nachrichten-Tab der App.
:::

### Schritt 9: Bot Framework Slack-Kanal konfigurieren

1. Navigieren Sie zum [Bot Framework Portal](https://dev.botframework.com/)
2. Gehen Sie zur Kanalseite Ihres Bots:
   - URL-Format: `https://dev.botframework.com/bots/channels?id={APP_ID}&channelId=slack`
   - Ersetzen Sie `{APP_ID}` durch Ihre Teams App ID (aus Schritt 6)
   - Beispiel: `https://dev.botframework.com/bots/channels?id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&channelId=slack`
3. Klicken Sie auf den **„Slack“**-Kanal oder auf **„Konfigurieren“**, falls bereits hinzugefügt
4. Kopieren Sie die App-Anmeldeinformationen aus Ihrer Slack-App (aus Schritt 8):
   - **Client-ID** (aus Slack App Credentials)
   - **Client Secret** (aus Slack App Credentials)
5. Fügen Sie diese in die Konfiguration des Bot Framework Slack-Kanals ein
6. Kopieren Sie die folgenden URLs zur späteren Verwendung:
   - **Redirect URL** (für Schritt 10 erforderlich)
   - **Event Subscription URL** (für Schritt 11 erforderlich)
7. Klicken Sie auf **„Speichern“**
8. **WICHTIG:** Nach dem Speichern werden Sie automatisch zu Slack weitergeleitet, um die Anwendung zu installieren/neu
   zu installieren
   - Dies schliesst den OAuth-Flow ab
   - Befolgen Sie die Anweisungen zur Autorisierung der App
   - Dies kann die Anforderungen an Event Subscriptions automatisch erfüllen

::: tip Automatische Konfiguration
Das Bot Framework konfiguriert viele Slack-Einstellungen oft automatisch während des OAuth-Flows. Überprüfen Sie nach
Abschluss von Schritt 9 die Schritte 10-12, um die Einstellungen zu bestätigen, anstatt alles manuell zu konfigurieren.
:::

### Schritt 10: Slack OAuth konfigurieren

1. Gehen Sie zu den OAuth-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/oauth`
2. Scrollen Sie zum Abschnitt **„Scopes“**
3. Klicken Sie unter **„Bot Token Scopes“** auf **„OAuth Scope hinzufügen“**
4. Fügen Sie die folgenden Scopes hinzu:
   - `chat:write` – Ermöglicht dem Bot, Nachrichten zu senden
   - `assistant:write` – Ermöglicht dem Bot, mit App Agents/Assistants zu interagieren
5. Klicken Sie unter **„Redirect URLs“** auf **„Neue Redirect URL hinzufügen“**
6. Fügen Sie die **Redirect URL** vom Bot Framework (Schritt 9) ein
7. Klicken Sie auf **„URLs speichern“**

::: info Automatische Scopes
Andere erforderliche Scopes (channels:history, groups:history, im:history, mpim:history) können automatisch hinzugefügt
werden, wenn Sie in Schritt 12 Bot-Events abonnieren oder wenn Sie den Bot Framework OAuth-Flow abschliessen.
:::

### Schritt 11: Slack Event Subscriptions konfigurieren

1. Gehen Sie zu den Event Subscriptions Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/event-subscriptions`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/event-subscriptions`
2. Schalten Sie **„Events aktivieren“** auf EIN
3. Fügen Sie in **„Request URL“** die **Event Subscription URL** vom Bot Framework (Schritt 9) ein
4. Warten Sie auf die URL-Verifizierung (es sollte „Verified ✓“ angezeigt werden)

::: tip Bereits konfiguriert?
Wenn Sie während Schritt 9 zu Slack weitergeleitet wurden und die Installation abgeschlossen haben, sind die Event
Subscriptions möglicherweise bereits automatisch vom Bot Framework konfiguriert worden. Überprüfen Sie diese Seite zur
Bestätigung.
:::

### Schritt 12: Bot-Events abonnieren (falls erforderlich)

::: warning Optionaler Schritt
Diese Event Subscriptions sind möglicherweise nicht erforderlich, wenn der Bot Framework Slack-Kanal sie automatisch
verarbeitet. Überprüfen Sie, ob Events bereits konfiguriert sind, bevor Sie sie manuell hinzufügen.
:::

Wenn Events nicht automatisch konfiguriert sind, scrollen Sie auf der Seite Event Subscriptions nach unten zu
**„Bot-Events abonnieren“** und fügen Sie Folgendes hinzu:

| Event-Name                         | Beschreibung                                                             | Erforderlicher Scope |
| :--------------------------------- | :----------------------------------------------------------------------- | :------------------- |
| `message.channels`                 | Eine Nachricht wurde an einen Kanal gesendet                             | `channels:history`   |
| `message.groups`                   | Eine Nachricht wurde an einen privaten Kanal gesendet                    | `groups:history`     |
| `message.im`                       | Eine Nachricht wurde in einem Direktnachrichtenkanal gesendet            | `im:history`         |
| `message.mpim`                     | Eine Nachricht wurde in einem Multiparty-Direktnachrichtenkanal gesendet | `mpim:history`       |
| `assistant_thread_started`         | Ein App Agent-Thread wurde gestartet                                     | keine                |
| `assistant_thread_context_changed` | Der Kontext hat sich geändert, während ein App Agent-Thread sichtbar war | keine                |

::: info Automatische Scope-Ergänzung
Wenn Sie diese Events hinzufügen, fügt Slack die notwendigen OAuth-Scopes automatisch Ihrer App-Konfiguration hinzu.
:::

Klicken Sie auf **„Änderungen speichern“**

### Schritt 13: Slack-App im Workspace installieren

::: tip Möglicherweise bereits abgeschlossen
Wenn Sie während Schritt 9 zu Slack weitergeleitet wurden und die Installation abgeschlossen haben, ist dieser Schritt
möglicherweise bereits abgeschlossen. Sie können dies überprüfen, indem Sie prüfen, ob der Bot bereits in Ihrem Slack
Workspace erscheint.
:::

Falls noch nicht installiert:

1. Gehen Sie zur Installationsseite Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/install-on-team`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/install-on-team`
2. Klicken Sie auf **„Im Workspace installieren“** (oder **„Im Workspace neu installieren“**, falls Sie aktualisieren)
3. Überprüfen Sie die angeforderten Berechtigungen
4. Klicken Sie auf **„Zulassen“**
5. **WICHTIG:** Kopieren Sie das angezeigte **Bot User OAuth Token**
   - Format: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`
   - Dies ist das Token, das Sie im nächsten Schritt zu MongoDB hinzufügen werden

**Alternative:** Falls bereits installiert, rufen Sie Ihr Token ab von:

- **OAuth & Berechtigungen**-Seite: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
- Suchen Sie nach **„Bot User OAuth Token“** unter „OAuth Tokens for Your Workspace“

::: danger Token-Sicherheit
Das Slack Bot OAuth Token bietet vollen Zugriff auf die Funktionen Ihres Bots. Speichern Sie es sicher und committen Sie
es niemals in die Versionskontrolle. Behandeln Sie es mit der gleichen Sicherheit wie Passwörter und API-Schlüssel.
:::

### Schritt 14: Slack OAuth Token zu MongoDB hinzufügen

Aktualisieren Sie das Bot-Pfad-Dokument in MongoDB, um das Slack OAuth Token aus Schritt 13 einzufügen:

```json
{
  "_id": {
    "$oid": "xxxxxxxxxxxxxxxxxxxxxxxx"
  },
  "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json",
  "credentials": {
    "APP_TYPE": "SingleTenant",
    "APP_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "APP_PASSWORD": "xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "APP_TENANTID": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
  },
  "system_message": "You are a helpful AI assistant.",
  "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Slack OAuth Token Details:**

- Format: `xoxb-` gefolgt von Zahlen und Bindestrichen
- Aus Schritt 13 während der Slack App-Installation erhalten
- Ersetzen Sie den leeren String `""` durch das tatsächliche Token
- Halten Sie dieses Token sicher und committen Sie es niemals in die Versionskontrolle

**So aktualisieren Sie ein bestehendes Dokument:**

```javascript
db.bot_paths.updateOne(
  { "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json" },
  { $set: { "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx" } }
)
```

**Alternative: Update per \_id:**

```javascript
db.bot_paths.updateOne(
  { "_id": ObjectId("xxxxxxxxxxxxxxxxxxxxxxxx") },
  { $set: { "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx" } }
)
```

______________________________________________________________________

## App-Manifest-Beispiele :page_facing_up:

Diese Manifeste zeigen die vollständige Konfiguration für Slack- und Teams-Apps. Sie können diese als Referenz verwenden
oder Apps programmatisch erstellen.

### Slack App Manifest

```json
{
    "display_information": {
        "name": "LLM Wrapping Agent"
    },
    "features": {
        "app_home": {
            "home_tab_enabled": true,
            "messages_tab_enabled": false,
            "messages_tab_read_only_enabled": false
        },
        "bot_user": {
            "display_name": "LLM Wrapping Agent",
            "always_online": true
        }
    },
    "oauth_config": {
        "redirect_urls": [
            "https://slack.botframework.com"
        ],
        "scopes": {
            "bot": [
                "channels:history",
                "groups:history",
                "im:history",
                "mpim:history",
                "chat:write",
                "assistant:write"
            ]
        }
    },
    "settings": {
        "event_subscriptions": {
            "request_url": "https://slack.botframework.com/api/Events/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "bot_events": [
                "assistant_thread_context_changed",
                "assistant_thread_started",
                "message.channels",
                "message.groups",
                "message.im",
                "message.mpim"
            ]
        },
        "org_deploy_enabled": false,
        "socket_mode_enabled": false,
        "token_rotation_enabled": false
    }
}
```

**Wichtige Konfigurationspunkte:**

- **app_home**: Konfiguration für die Home- und Nachrichten-Tabs der App
  - **home_tab_enabled**: Auf `true` setzen, um den Home Tab zu aktivieren
  - **messages_tab_enabled**: Auf `false` setzen (Interaktion erfolgt über Kanäle/DMs, nicht über den Nachrichten-Tab)
  - **messages_tab_read_only_enabled**: Auf `false` setzen
- **always_online**: Auf `true` setzen, um den Bot immer als online anzuzeigen
- **redirect_urls**: Immer `https://slack.botframework.com` für die Bot Framework-Integration
- **request_url**: Das Format ist `https://slack.botframework.com/api/Events/{APP_ID}`, wobei `{APP_ID}` Ihre Teams App
  Client ID ist
- **Bot-Scopes**: Alle 6 Scopes sind für die volle Funktionalität erforderlich (einschliesslich `chat:write` und
  `assistant:write`)
- **bot_events**: Alle 6 Events ermöglichen es dem Bot, Nachrichten über alle Konversationstypen hinweg zu empfangen

### Teams App Manifest

```json
{
    "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.23/MicrosoftTeams.schema.json",
    "version": "1.0.0",
    "manifestVersion": "1.23",
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "name": {
        "short": "LLM Agent",
        "full": "LLM Wrapping Agent"
    },
    "developer": {
        "name": "Your Organization Name",
        "websiteUrl": "https://your-domain.com",
        "privacyUrl": "https://your-domain.com/privacy",
        "termsOfUseUrl": "https://your-domain.com/terms"
    },
    "description": {
        "short": "LLMWrappingAgent",
        "full": "LLMWrappingAgent"
    },
    "icons": {
        "outline": "outline.png",
        "color": "color.png"
    },
    "accentColor": "#ffffff",
    "bots": [
        {
            "botId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "scopes": [
                "personal",
                "team",
                "groupChat"
            ],
            "isNotificationOnly": false,
            "supportsCalling": false,
            "supportsVideo": false,
            "supportsFiles": true
        }
    ],
    "validDomains": [],
    "webApplicationInfo": {
        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "authorization": {
        "permissions": {
            "resourceSpecific": [
                {
                    "name": "ChannelMessage.Read.Group",
                    "type": "Application"
                },
                {
                    "name": "ChannelMessage.Send.Group",
                    "type": "Application"
                },
                {
                    "name": "ChatMessage.Read.Chat",
                    "type": "Application"
                },
                {
                    "name": "ChatMessage.Send.Chat",
                    "type": "Application"
                }
            ]
        }
    }
}
```

**Wichtige Konfigurationspunkte:**

- **id** und **webApplicationInfo.id**: Ihre Teams App Client ID (APP_ID)
- **botId**: Identisch mit Ihrer App Client ID
- **scopes**: Bot in persönlichen Chats, Teams und Gruppenchats aktivieren
- **supportsFiles**: Auf `true` setzen, um Datei-Uploads zu erlauben
- **Ressourcenspezifische Berechtigungen**:
  - `ChannelMessage.Read.Group` – Nachrichten in Kanälen lesen
  - `ChannelMessage.Send.Group` – Nachrichten in Kanälen senden
  - `ChatMessage.Read.Chat` – Nachrichten in Chats lesen
  - `ChatMessage.Send.Chat` – Nachrichten in Chats senden

### Verwendung von Manifesten für die App-Erstellung

**Slack:**

1. Gehen Sie zu [Slack API Apps](https://api.slack.com/apps)
2. Klicken Sie auf **„Neue App erstellen“** → **„Aus einem App-Manifest“**
3. Wählen Sie Ihren Workspace aus
4. Fügen Sie das Slack Manifest JSON ein
5. Überprüfen und erstellen

**Teams:**

1. Laden Sie das Manifest als `manifest.json` herunter
2. Fügen Sie Icon-Dateien (`outline.png` und `color.png`) zum selben Verzeichnis hinzu
3. Zippen Sie alle drei Dateien zusammen
4. Klicken Sie im Teams Developer Portal auf **„App importieren“**
5. Laden Sie die Zip-Datei hoch

______________________________________________________________________

## Verifizierungs-Checkliste :white_check_mark:

Nach Abschluss aller Schritte überprüfen Sie:

**Teams-Konfiguration:**

- [ ] Teams-App ist veröffentlicht und genehmigt
- [ ] Bot Framework Messaging Endpoint ist auf `/api/v1/messages` gesetzt
- [ ] Bot Framework Messaging Endpoint URL ist öffentlich zugänglich
- [ ] Bot antwortet auf Nachrichten in Teams
- [ ] Bot-Berechtigungen sind korrekt gesetzt (Nachricht lesen/senden in Chat/Team)

**MongoDB-Konfiguration:**

- [ ] `bot_paths`-Eintrag mit allen erforderlichen Feldern existiert
- [ ] `credentials`-Objekt enthält APP_TYPE, APP_ID, APP_PASSWORD und APP_TENANTID (für SingleTenant)
- [ ] `path`-Feld enthält internen Routing-Pfad (z. B. `/api/v1/agent/chat/completions/...`)
- [ ] `path`-Feld unterscheidet sich vom Bot Framework Messaging Endpoint (`/api/v1/messages`)
- [ ] `system_message` ist dem Zweck des Bots entsprechend konfiguriert
- [ ] Client Secret (APP_PASSWORD) ist sicher gespeichert und nicht abgelaufen

**Slack-Konfiguration:**

- [ ] Slack-App ist mit korrektem Namen erstellt
- [ ] App Home konfiguriert: „Meinen Bot immer als online anzeigen“ auf EIN
- [ ] App Home konfiguriert: „Home Tab“ auf EIN
- [ ] App Home konfiguriert: „Nachrichten-Tab“ ist deaktiviert (Bot interagiert über Kanäle/DMs)
- [ ] Bot Token Scopes `chat:write` und `assistant:write` sind in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Bot Framework-Konfiguration gespeichert und OAuth-Weiterleitung zu Slack abgeschlossen
- [ ] Redirect URL ist in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Event Subscription URL ist verifiziert (kann automatisch erfolgen)
- [ ] Bot-Events sind abonniert (kann automatisch über Bot Framework erfolgen)
- [ ] Slack-App ist im Workspace installiert (kann während der Weiterleitung in Schritt 9 erfolgt sein)
- [ ] `slack_token` wird von der Slack OAuth & Berechtigungen-Seite abgerufen
- [ ] `slack_token` ist zu MongoDB hinzugefügt
- [ ] Bot antwortet auf Nachrichten in Slack-Kanälen
- [ ] Bot antwortet auf Direktnachrichten in Slack

______________________________________________________________________

## Fehlerbehebung :wrench:

### Bot antwortet nicht in Teams

- **Probleme mit dem Messaging Endpoint:**
  - Überprüfen Sie, ob der Bot Framework Messaging Endpoint im Teams Developer Portal auf `/api/v1/messages` gesetzt ist
  - Stellen Sie sicher, dass die Endpoint-URL öffentlich zugänglich ist (mit curl oder Browser testen)
  - Für die lokale Entwicklung bestätigen Sie, dass Azure DevTunnel oder ngrok läuft
- **Authentifizierungsprobleme:**
  - Überprüfen Sie, ob `APP_PASSWORD` (Client Secret) korrekt ist und nicht abgelaufen ist
  - Bestätigen Sie, dass `APP_TENANTID` und `APP_ID` mit den Werten aus Schritt 6 übereinstimmen
  - Überprüfen Sie, ob `APP_TYPE` korrekt gesetzt ist (`SingleTenant` oder `MultiTenant`)
- **Konfigurationsprobleme:**
  - Überprüfen Sie die App-Berechtigungen im Teams Developer Portal (Nachricht lesen/senden in Chat/Team)
  - Überprüfen Sie, ob der MongoDB `bot_paths`-Eintrag mit den korrekten Anmeldeinformationen existiert
  - Überprüfen Sie, ob das `path`-Feld in MongoDB einen gültigen internen Routing-Pfad enthält
  - Stellen Sie sicher, dass die Konversation mit dem korrekten `path`-Wert erstellt wurde

### Probleme mit der Slack-Integration

- Überprüfen Sie, ob `slack_token` gültig ist (beginnt mit `xoxb-`)
- Überprüfen Sie, ob die Slack-App die notwendigen Bot-Token Scopes hat:
  - `chat:write` (erforderlich zum Senden von Nachrichten)
  - `assistant:write` (erforderlich für App Agent-Interaktionen)
  - `channels:history`, `groups:history`, `im:history`, `mpim:history` (für Nachrichten-Events)
- Überprüfen Sie, ob die App Home-Einstellungen konfiguriert sind:
  - „Meinen Bot immer als online anzeigen“ sollte auf EIN stehen
  - „Home Tab“ sollte auf EIN stehen
  - „Benutzern erlauben, Slash-Befehle und Nachrichten vom Nachrichten-Tab zu senden“ sollte aktiviert sein
- Bestätigen Sie, dass der Bot zu den gewünschten Slack-Kanälen hinzugefügt wurde (Bot mit @botname einladen)
- Stellen Sie sicher, dass alle 6 Bot-Events in den Event Subscriptions abonniert sind
- Überprüfen Sie, ob die Event Subscription URL „Verified ✓“ anzeigt
- Überprüfen Sie, ob die Redirect URL in den Slack OAuth-Einstellungen korrekt hinzugefügt wurde
- Stellen Sie sicher, dass das `slack_token`-Feld in MongoDB kein leerer String ist
- Überprüfen Sie die Bot Framework Slack-Kanal-Konfiguration
- Installieren Sie die Slack-App neu, wenn Scopes nach der Erstinstallation geändert wurden (erforderlich, damit
  Scope-Änderungen wirksam werden)

### Probleme mit der MongoDB-Verbindung

- Überprüfen Sie, ob der Sammlungsname `bot_paths` ist
- Überprüfen Sie, ob die Dokumentstruktur den obigen Beispielen entspricht
- Stellen Sie sicher, dass alle erforderlichen Felder im `credentials`-Objekt vorhanden sind
- Überprüfen Sie, ob `APP_ID` und `APP_TENANTID` im korrekten UUID-Format vorliegen
- Bestätigen Sie, dass das `path`-Feld mit `/api/` beginnt

______________________________________________________________________

## Best Practices für Sicherheit :shield:

1. **Niemals Secrets in die Versionskontrolle committen**
2. **Client Secrets vor Ablauf rotieren**
3. **Umgebungsvariablen für sensible Daten verwenden**
4. **MongoDB-Zugriff mit geeigneter Authentifizierung einschränken**
5. **OAuth-Token-Nutzung auf Anomalien überwachen**
6. **Audit-Logs von Bot-Pfad-Modifikationen führen**
7. **HTTPS für alle Messaging Endpoints verwenden**

______________________________________________________________________

## Support :sos:

Bei Problemen oder Fragen:

- **Teams Developer Portal**:
  [Microsoft Teams-Dokumentation](https://learn.microsoft.com/en-us/microsoftteams/platform/)
- **Bot Framework**: [Azure Bot Service-Dokumentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- **Slack API**: [Slack API-Dokumentation](https://api.slack.com/)

______________________________________________________________________

## Nächste Schritte :rocket:

Nach Abschluss der manuellen Bot-Einrichtung:

1. **Testen Sie Ihren Bot**: Senden Sie eine Nachricht in Teams oder Slack, um zu überprüfen, ob der Bot korrekt
   antwortet
2. **Logs überprüfen**: Überprüfen Sie die Anwendungsprotokolle auf Fehler oder Warnungen während der Bot-Interaktionen
3. **Zusätzliche Funktionen konfigurieren**: Erkunden Sie
   [Bot-in-the-Loop](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für die Zusammenarbeit zwischen Mensch und KI
4. **Benutzerdefinierte Logik implementieren**: Im [Entwicklerhandbuch](../../../6_code_deep_dive/aihub_bot/) finden Sie
   Informationen zu benutzerdefinierten Bot-Implementierungen
5. **Leistung überwachen**: Richten Sie Observability und Monitoring für Production-Deployments ein

______________________________________________________________________

*Zuletzt aktualisiert: 14. November 2025*
