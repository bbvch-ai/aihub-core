---
title: Anleitung zur manuellen Bot-Erstellung
source_sha: 7b39f80c3fbe73d16375e50b8cc961cfe977727197fa25ea0a357b5892cdda4a
---

# Anleitung zur manuellen Bot-Erstellung :robot: :wrench:

::: info **TL;DR – Was ist diese Anleitung?**
Dieses umfassende Handbuch bietet **Schritt-für-Schritt-Anleitungen zur manuellen Erstellung und Konfiguration von
Bots** mit Microsoft Teams und Slack-Integration. Verwenden Sie diese Anleitung, wenn Sie neue Bots von Grund auf
erstellen, Azure Bot Framework-Kanäle konfigurieren oder bestehende Bot-Deployments beheben müssen. Es deckt alles ab,
von der Einrichtung des Teams Developer Portal bis zur MongoDB-Konfiguration und Slack OAuth-Integration.
:::

::: tip Automatisierte Einrichtung verfügbar
Bevor Sie mit der manuellen Einrichtung fortfahren, sollten Sie das **automatisierte Setup-Skript** in Betracht ziehen,
das die meisten dieser Schritte für Sie erledigt:

```bash
python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "my-ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/messages" \
    --mongo-connection-string "mongodb://localhost:27017"
```

**Wann Sie das automatisierte Skript verwenden sollten:**

- Erstellung neuer Bots für die Produktionsbereitstellung
- Standardmäßige Single-Bot- oder Multi-Bot-Konfigurationen
- Schnelle Einrichtung ohne Anpassung

**Wann Sie diese manuelle Anleitung verwenden sollten:**

- Behebung von Fehlern bei der automatisierten Einrichtung
- Detailliertes Verständnis der Bot-Konfiguration
- Erstellung benutzerdefinierter oder nicht-standardmäßiger Konfigurationen
- Erlernen der Funktionsweise der Bot-Integration

Details zur automatisierten Einrichtung finden Sie in der [Azure Bot Service Integrationsanleitung](../1_setup/).
:::

## Verwandte Dokumentation :books:

- **[Übersicht über Slack- & Teams-Integrationen](../)** – Hochrangige Konzepte und Geschäftswert
- **[Azure Bot Service Integration](../1_setup/)** – Anleitung zur automatisierten Einrichtung
- **[AI-Hub Bot Developer's Guide](../../../6_code_deep_dive/aihub_bot/)** – Technische Implementierungsdetails
- **[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** – Workflows für die
  Mensch-KI-Zusammenarbeit

## Schlüsselterminologie :book:

Das Verständnis dieser Begriffe ist entscheidend für eine erfolgreiche Bot-Konfiguration:

| Begriff                              | Definition                                                                                                                                                                                                                                             |
| :----------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bot Framework Messaging Endpoint** | Die einzige öffentliche URL, an die Azure Bot Service ALLE Bot-Nachrichten sendet. Immer `/api/v1/messages`. Im Teams Developer Portal konfiguriert (Schritt 3).                                                                                       |
| **MongoDB `path` Feld**              | Interner Routing-Pfad, der bestimmt, welche Bot-Implementierung eine Konversation verarbeitet. Beispiele: `/api/v1/agent/chat/completions/...` oder `/api/v1/openai/chat/completions`. Konfiguriert in der MongoDB `bot_paths` Collection (Schritt 7). |
| **App ID / Client ID**               | Azure AD Anwendungsbezeichner (UUID-Format). Derselbe Wert wird als Bot ID und in der MongoDB `credentials.APP_ID` verwendet.                                                                                                                          |
| **Client Secret / App Password**     | Azure AD Anwendungsgeheimnis. Wird in MongoDB als `credentials.APP_PASSWORD` gespeichert. Läuft ab und muss rotiert werden.                                                                                                                            |
| **Tenant ID**                        | Microsoft 365 Tenant-Bezeichner. Erforderlich für SingleTenant-Bots, gespeichert als `credentials.APP_TENANTID`.                                                                                                                                       |
| **Bot-in-the-Loop**                  | Muster, bei dem KI-Agents während der Workflow-Ausführung menschliche Eingaben über Slack-Kanäle anfordern.                                                                                                                                            |
| **Slack Bot OAuth Token**            | Token für die Slack-Integration (Format: `xoxb-...`). Wird in MongoDB als `slack_token` gespeichert.                                                                                                                                                   |

::: warning Kritischer Unterschied
**Bot Framework Messaging Endpoint** (`/api/v1/messages`) ≠ **MongoDB `path` Feld** (z. B.
`/api/v1/agent/chat/completions/...`)

Dies sind zwei unterschiedliche Konzepte, die verschiedenen Zwecken dienen. Der Messaging Endpoint ist der Ort, an den
der Azure Bot Service Nachrichten sendet. Das `path`-Feld bestimmt, wie diese Nachrichten intern verarbeitet werden.
:::

## Voraussetzungen :clipboard:

Bevor Sie beginnen, stellen Sie sicher, dass Sie Zugriff haben auf:

- **Microsoft Teams Developer Portal** – Zum Erstellen von Teams-Apps und Bots
- **MongoDB database** mit `bot_paths` Collection – Zum Speichern der Bot-Konfiguration
- **Azure Bot Framework** – Für Multi-Channel Bot-Management
- **Slack Workspace** mit Administratorrechten – Für die Slack-Integration

______________________________________________________________________

## Teil 1: Teams Developer Portal Einrichtung :microsoft:

### Schritt 1: App mit grundlegenden Informationen erstellen

1. Navigieren Sie zum [Teams Developer Portal](https://dev.teams.microsoft.com/)
2. Klicken Sie auf **"Apps"** → **"New app"**
3. Geben Sie die grundlegenden Informationen ein:
   - App-Name
   - Kurzbeschreibung
   - Vollständige Beschreibung
   - Entwicklerinformationen
   - App-URLs
   - Application (client) ID (bei Bedarf generieren)

### Schritt 2: Berechtigungen konfigurieren

1. Gehen Sie zu **"App features"** → **"Bot"**
2. Legen Sie die erforderlichen Berechtigungen fest:
   - **Message Read** in Chat/Team
   - **Message Send** in Chat/Team
3. Speichern Sie die Berechtigungsänderungen

### Schritt 3: Neuen Bot erstellen

1. Navigieren Sie in der App zum Bereich **"Bot"**
2. Klicken Sie auf **"Set up"** oder **"Create new bot"**
3. Geben Sie die **Bot Framework Messaging Endpoint URL** ein:
   - Format: `https://your-domain.com/api/v1/messages`
   - Dies ist der standardmäßige Azure Bot Service Endpoint
   - Muss öffentlich über das Internet zugänglich sein
   - Für die lokale Entwicklung verwenden Sie Azure DevTunnel oder ngrok
4. **Notieren Sie die Bot ID** zur späteren Verwendung

::: warning Bot Framework Endpoint vs. MongoDB Path
**WICHTIGER UNTERSCHIED:**

- **Bot Framework Messaging Endpoint** (`/api/v1/messages`): Der einzige Einstiegspunkt, an den der Azure Bot Service
  ALLE Bot-Nachrichten sendet. Dies wird hier im Teams Developer Portal konfiguriert.

- **MongoDB `path` Feld** (z. B. `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`): Interner Routing-
  Pfad, der bestimmt, welche Bot-Implementierung die Konversation verarbeitet. Dies wird in MongoDB (Schritt 7)
  konfiguriert und ermöglicht es, dass mehrere Bots koexistieren.

**So funktioniert es:**

1. Azure Bot Service sendet die Nachricht an `/api/v1/messages`
2. AI-Hub sucht den `path` der Konversation in der MongoDB `bot_paths` Collection
3. Die Anfrage wird an die spezifische Bot-Implementierung weitergeleitet

**Beispiel:**

- Teams Developer Portal Endpoint: `https://my-domain.com/api/v1/messages`
- MongoDB `path` für Agent Bot: `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
- MongoDB `path` für OpenAI Bot: `/api/v1/openai/chat/completions`

Diese müssen NICHT übereinstimmen! Der Messaging Endpoint ist immer `/api/v1/messages`.
:::

::: tip Lokale Entwicklung
Für die lokale Entwicklung stellen Sie Ihren Bot-Server mit Azure DevTunnel bereit:

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Use the https URL (e.g., https://abc123-8000.devtunnels.ms/api/v1/messages)
```

Detaillierte Anweisungen zur lokalen Entwicklung finden Sie im
[Developer's Guide](../../../6_code_deep_dive/aihub_bot/).
:::

### Schritt 4: Client Secret erstellen

1. Suchen Sie in der Bot-Konfiguration **"Client secrets"**
2. Klicken Sie auf **"Add a client secret"**
3. **WICHTIG**: Kopieren und speichern Sie das Client Secret sofort sicher
   - Secret-Format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Sie können es später nicht mehr anzeigen
4. Notieren Sie das Ablaufdatum des Secrets

::: danger Sicherheitshinweis
Client Secrets werden nur einmal bei der Erstellung angezeigt. Speichern Sie sie sofort sicher in einem Password Manager
oder Secrets Vault. Wenn sie verloren gehen, müssen Sie ein neues Secret generieren und Ihre MongoDB-Konfiguration
aktualisieren.
:::

### Schritt 5: Bot zur App hinzufügen

1. Navigieren Sie zurück zur App-Übersicht
2. Bestätigen Sie, dass der Bot unter **"App features"** aufgeführt ist
3. Überprüfen Sie, ob die Bot ID mit der in Schritt 3 erstellten übereinstimmt

### Schritt 6: App in der Organisation veröffentlichen

1. Gehen Sie zu **"Publish"** → **"Publish to org"**
2. Überprüfen Sie alle Konfigurationen
3. Klicken Sie auf **"Publish"**
4. Warten Sie auf die Administratorgenehmigung (falls erforderlich)
5. Notieren Sie nach der Genehmigung die **App/Client ID** und **Tenant ID**

______________________________________________________________________

## Teil 2: MongoDB Konfiguration :floppy_disk:

### Schritt 7: Bot-Pfad-Eintrag hinzufügen

Fügen Sie der `bot_paths` Collection ein neues Dokument mit der folgenden Struktur hinzu:

```json
{
  "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json",
  "credentials": {
    "APP_TYPE": "SingleTenant",
    "APP_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "APP_PASSWORD": "xxx8Q~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "APP_TENANTID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "system_message": "You are a helpful AI assistant powered by Azure OpenAI.",
  "slack_token": ""
}
```

**Erforderliche Felder:**

- `path`: Der **interne Routing-Pfad** für diese spezifische Bot-Implementierung
  - **Dies ist NICHT der Bot Framework Messaging Endpoint** (der immer `/api/v1/messages` ist)
  - Dies bestimmt, welcher Bot-Handler Konversationen verarbeitet
  - Beispiele:
    - `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json` – Agentenbasierter Bot
    - `/api/v1/openai/chat/completions` – Direkter OpenAI Bot
    - `/api/v1/bitl/chat/completions` – Bot-in-the-Loop Bot
- `credentials`: Objekt, das die Azure Bot-Authentifizierung enthält
  - `APP_TYPE`: Authentifizierungstyp (`"SingleTenant"` oder `"MultiTenant"`)
  - `APP_ID`: Teams App Client ID aus Schritt 6
  - `APP_PASSWORD`: Client Secret aus Schritt 4
  - `APP_TENANTID`: Microsoft 365 Tenant ID aus Schritt 6 (erforderlich für SingleTenant)
- `system_message`: Standard-Systemnachricht/Anweisungen für den Bot
- `slack_token`: Anfangs leerer String (wird in Schritt 14 für die Slack-Integration gefüllt)

::: tip Multi-Bot-Konfiguration
Sie können **mehrere Bot-Implementierungen** mit unterschiedlichen `path`-Werten haben, die alle denselben Bot Framework
Messaging Endpoint (`/api/v1/messages`) teilen:

**Agentenbasierter Bot für den Kundensupport:**

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
Verwenden Sie beschreibende Pfadnamen, die den Agenten oder die Funktionalität angeben, um die Verwaltung mehrerer Bots
zu erleichtern. Zum Beispiel identifiziert `/api/v1/agent/chat/completions/CustomerSupportAgent/production/json` den
Zweck des Bots eindeutig.
:::

______________________________________________________________________

## Teil 3: Bot Framework & Slack-Integration :slack:

### Schritt 8: Slack-App erstellen

1. Navigieren Sie zu [Slack API Apps](https://api.slack.com/apps)
2. Klicken Sie auf **"Create New App"**
3. Wählen Sie **"From scratch"**
4. Geben Sie Ihrer App einen Namen (z. B. "Mein Bot-Name")
5. Wählen Sie den Workspace aus, in dem Sie die App entwickeln möchten
6. Klicken Sie auf **"Create App"**

### Schritt 8.5: App Home Einstellungen konfigurieren

1. Gehen Sie zu den App Home-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/app-home`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/app-home`
2. Im Abschnitt **"Show Tabs"**:
   - Schalten Sie **"Always show my bot as online"** auf **ON**
   - Schalten Sie **"Home Tab"** auf **ON**
3. Im Abschnitt **"Messages Tab"**:
   - **Lassen Sie "Messages Tab" deaktiviert** – Der Bot interagiert stattdessen über Kanäle und Direktnachrichten
   - Deaktivieren Sie "Allow users to send Slash commands and messages from the messages tab" (falls sichtbar)
4. Klicken Sie auf **"Save Changes"**, wenn Sie dazu aufgefordert werden

::: info Messages Tab Konfiguration
Der Messages Tab ist typischerweise deaktiviert, wenn das Bot Framework verwendet wird, da der Bot über Kanäle,
Gruppenchats und Direktnachrichten kommuniziert, anstatt über den Messages Tab der App.
:::

### Schritt 9: Bot Framework Slack-Kanal konfigurieren

1. Navigieren Sie zum [Bot Framework Portal](https://dev.botframework.com/)
2. Gehen Sie zur Kanalseite Ihres Bots:
   - URL-Format: `https://dev.botframework.com/bots/channels?id={APP_ID}&channelId=slack`
   - Ersetzen Sie `{APP_ID}` durch Ihre Teams App ID (aus Schritt 6)
   - Beispiel: `https://dev.botframework.com/bots/channels?id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&channelId=slack`
3. Klicken Sie auf den Kanal **"Slack"** oder **"Configure"**, falls bereits hinzugefügt
4. Kopieren Sie die App-Anmeldeinformationen aus Ihrer Slack-App (aus Schritt 8):
   - **Client ID** (aus den Slack App Credentials)
   - **Client Secret** (aus den Slack App Credentials)
5. Fügen Sie diese in die Bot Framework Slack-Kanal-Konfiguration ein
6. Kopieren Sie die folgenden URLs zur späteren Verwendung:
   - **Redirect URL** (für Schritt 10 benötigt)
   - **Event Subscription URL** (für Schritt 11 benötigt)
7. Klicken Sie auf **"Save"**
8. **WICHTIG:** Nach dem Speichern werden Sie automatisch zu Slack weitergeleitet, um die Anwendung zu installieren/neu
   zu installieren
   - Dies schließt den OAuth-Flow ab
   - Folgen Sie den Anweisungen, um die App zu autorisieren
   - Dies kann die Anforderungen für die Ereignis-Abonnement automatisch erfüllen

::: tip Automatische Konfiguration
Das Bot Framework konfiguriert oft viele Slack-Einstellungen automatisch während des OAuth-Flows. Überprüfen Sie nach
Abschluss von Schritt 9, ob die Schritte 10-12 die Einstellungen bestätigen, anstatt alles manuell zu konfigurieren.
:::

### Schritt 10: Slack OAuth konfigurieren

1. Gehen Sie zu den OAuth-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/oauth`
2. Scrollen Sie zum Abschnitt **"Scopes"**
3. Unter **"Bot Token Scopes"** klicken Sie auf **"Add an OAuth Scope"**
4. Fügen Sie die folgenden Scopes hinzu:
   - `chat:write` – Ermöglicht dem Bot, Nachrichten zu senden
   - `assistant:write` – Ermöglicht dem Bot, mit App Agents/Assistants zu interagieren
5. Unter **"Redirect URLs"** klicken Sie auf **"Add New Redirect URL"**
6. Fügen Sie die **Redirect URL** aus dem Bot Framework ein (Schritt 9)
7. Klicken Sie auf **"Save URLs"**

::: info Automatische Scopes
Andere erforderliche Scopes (channels:history, groups:history, im:history, mpim:history) können automatisch hinzugefügt
werden, wenn Sie in Schritt 12 Bot-Events abonnieren oder wenn Sie den Bot Framework OAuth-Flow abschließen.
:::

### Schritt 11: Slack Event Subscriptions konfigurieren

1. Gehen Sie zu den Event Subscriptions Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/event-subscriptions`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/event-subscriptions`
2. Schalten Sie **"Enable Events"** auf ON
3. In **"Request URL"** fügen Sie die **Event Subscription URL** aus dem Bot Framework ein (Schritt 9)
4. Warten Sie auf die URL-Verifizierung (sollte "Verified ✓" anzeigen)

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

Wenn Events nicht automatisch konfiguriert sind, scrollen Sie auf der Event Subscriptions-Seite nach unten zu
**"Subscribe to bot events"** und fügen Sie die folgenden hinzu:

| Event-Name                         | Beschreibung                                                             | Erforderlicher Scope |
| :--------------------------------- | :----------------------------------------------------------------------- | :------------------- |
| `message.channels`                 | Eine Nachricht wurde in einem Kanal gepostet                             | `channels:history`   |
| `message.groups`                   | Eine Nachricht wurde in einem privaten Kanal gepostet                    | `groups:history`     |
| `message.im`                       | Eine Nachricht wurde in einem Direktnachrichtenkanal gepostet            | `im:history`         |
| `message.mpim`                     | Eine Nachricht wurde in einem Multiparty-Direktnachrichtenkanal gepostet | `mpim:history`       |
| `assistant_thread_started`         | Ein App Agent Thread wurde gestartet                                     | keiner               |
| `assistant_thread_context_changed` | Der Kontext änderte sich, während ein App Agent Thread sichtbar war      | keiner               |

::: info Automatische Scope-Hinzufügung
Wenn Sie diese Events hinzufügen, fügt Slack automatisch die notwendigen OAuth-Scopes zu Ihrer App-Konfiguration hinzu.
:::

Klicken Sie auf **"Save Changes"**

### Schritt 13: Slack-App im Workspace installieren

::: tip Kann bereits abgeschlossen sein
Wenn Sie während Schritt 9 zu Slack weitergeleitet wurden und die Installation abgeschlossen haben, kann dieser Schritt
bereits abgeschlossen sein. Sie können dies überprüfen, indem Sie prüfen, ob der Bot bereits in Ihrem Slack-Workspace
erscheint.
:::

Falls noch nicht installiert:

1. Gehen Sie zur Installationsseite Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/install-on-team`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/install-on-team`
2. Klicken Sie auf **"Install to Workspace"** (oder **"Reinstall to Workspace"**, falls Sie aktualisieren)
3. Überprüfen Sie die angeforderten Berechtigungen
4. Klicken Sie auf **"Allow"**
5. **WICHTIG:** Kopieren Sie den **Bot User OAuth Token**, der erscheint
   - Format: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`
   - Dies ist das Token, das Sie im nächsten Schritt zu MongoDB hinzufügen werden

**Alternative:** Falls bereits installiert, rufen Sie Ihr Token ab unter:

- **OAuth & Permissions** Seite: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
- Suchen Sie nach **"Bot User OAuth Token"** unter "OAuth Tokens for Your Workspace"

::: danger Token-Sicherheit
Der Slack Bot OAuth Token bietet vollen Zugriff auf die Funktionen Ihres Bots. Speichern Sie ihn sicher und committen
Sie ihn niemals in die Versionskontrolle. Behandeln Sie ihn mit derselben Sicherheit wie Passwörter und API-Schlüssel.
:::

### Schritt 14: Slack OAuth Token zu MongoDB hinzufügen

Aktualisieren Sie das Bot-Pfad-Dokument in MongoDB, um das Slack OAuth Token aus Schritt 13 einzuschließen:

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
  "system_message": "You are a helpful AI assistant powered by Azure OpenAI.",
  "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Slack OAuth Token Details:**

- Format: `xoxb-` gefolgt von Zahlen und Bindestrichen
- Erhalten aus Schritt 13 während der Slack App-Installation
- Ersetzen Sie den leeren String `""` durch das tatsächliche Token
- Bewahren Sie dieses Token sicher auf und committen Sie es niemals in die Versionskontrolle

**Um ein bestehendes Dokument zu aktualisieren:**

```javascript
db.bot_paths.updateOne(
  { "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json" },
  { $set: { "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx" } }
)
```

**Alternative: Aktualisierung nach \_id:**

```javascript
db.bot_paths.updateOne(
  { "_id": ObjectId("xxxxxxxxxxxxxxxxxxxxxxxx") },
  { $set: { "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx" } }
)
```

______________________________________________________________________

## App Manifest Beispiele :page_facing_up:

Diese Manifeste zeigen die vollständige Konfiguration für sowohl Slack- als auch Teams-Apps. Sie können diese als
Referenz verwenden oder um Apps programmatisch zu erstellen.

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
  - **messages_tab_enabled**: Auf `false` setzen (Interaktion erfolgt über Kanäle/DMs, nicht den Nachrichten-Tab)
  - **messages_tab_read_only_enabled**: Auf `false` setzen
- **always_online**: Auf `true` setzen, um den Bot immer als online anzuzeigen
- **redirect_urls**: Immer `https://slack.botframework.com` für die Bot Framework-Integration
- **request_url**: Das Format ist `https://slack.botframework.com/api/Events/{APP_ID}`, wobei `{APP_ID}` Ihre Teams App
  Client ID ist
- **bot scopes**: Alle 6 Scopes sind für die volle Funktionalität erforderlich (einschließlich `chat:write` und
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
- **botId**: Gleiche wie Ihre App Client ID
- **scopes**: Aktivieren Sie den Bot in persönlichen Chats, Teams und Gruppenchats
- **supportsFiles**: Auf `true` setzen, um Dateiuploads zu erlauben
- **Ressourcenspezifische Berechtigungen**:
  - `ChannelMessage.Read.Group` – Nachrichten in Kanälen lesen
  - `ChannelMessage.Send.Group` – Nachrichten in Kanälen senden
  - `ChatMessage.Read.Chat` – Nachrichten in Chats lesen
  - `ChatMessage.Send.Chat` – Nachrichten in Chats senden

### Verwenden von Manifesten zur App-Erstellung

**Slack:**

1. Gehen Sie zu [Slack API Apps](https://api.slack.com/apps)
2. Klicken Sie auf **"Create New App"** → **"From an app manifest"**
3. Wählen Sie Ihren Workspace aus
4. Fügen Sie das Slack Manifest JSON ein
5. Überprüfen und erstellen

**Teams:**

1. Laden Sie das Manifest als `manifest.json` herunter
2. Fügen Sie Icon-Dateien (`outline.png` und `color.png`) in dasselbe Verzeichnis hinzu
3. Zippen Sie alle drei Dateien zusammen
4. Im Teams Developer Portal klicken Sie auf **"Import app"**
5. Laden Sie die Zip-Datei hoch

______________________________________________________________________

## Verifizierungs-Checkliste :white_check_mark:

Überprüfen Sie nach Abschluss aller Schritte Folgendes:

**Teams Konfiguration:**

- [ ] Teams App ist veröffentlicht und genehmigt
- [ ] Bot Framework Messaging Endpoint ist auf `/api/v1/messages` eingestellt
- [ ] Bot Framework Messaging Endpoint URL ist öffentlich zugänglich
- [ ] Bot antwortet auf Nachrichten in Teams
- [ ] Bot-Berechtigungen sind korrekt gesetzt (Message Read/Send in Chat/Team)

**MongoDB Konfiguration:**

- [ ] `bot_paths`-Eintrag existiert mit allen erforderlichen Feldern
- [ ] `credentials`-Objekt enthält APP_TYPE, APP_ID, APP_PASSWORD und APP_TENANTID (für SingleTenant)
- [ ] `path`-Feld enthält den internen Routing-Pfad (z. B. `/api/v1/agent/chat/completions/...`)
- [ ] `path`-Feld ist UNTERSCHIEDLICH vom Bot Framework Messaging Endpoint (`/api/v1/messages`)
- [ ] `system_message` ist für den Zweck des Bots angemessen konfiguriert
- [ ] Client Secret (APP_PASSWORD) ist sicher gespeichert und nicht abgelaufen

**Slack Konfiguration:**

- [ ] Slack App wurde mit korrektem Namen erstellt
- [ ] App Home konfiguriert: "Always show my bot as online" ist auf ON geschaltet
- [ ] App Home konfiguriert: "Home Tab" ist auf ON geschaltet
- [ ] App Home konfiguriert: "Messages Tab" ist deaktiviert (Bot interagiert über Kanäle/DMs)
- [ ] Bot Token Scopes `chat:write` und `assistant:write` sind in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Bot Framework Slack-Kanal ist mit Client ID und Client Secret konfiguriert
- [ ] Bot Framework Konfiguration gespeichert und OAuth-Redirect zu Slack abgeschlossen
- [ ] Redirect URL ist in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Event Subscription URL ist verifiziert (kann automatisch erfolgen)
- [ ] Bot-Events sind abonniert (kann automatisch über Bot Framework erfolgen)
- [ ] Slack App ist im Workspace installiert (kann während des Schritt 9 Redirects passiert sein)
- [ ] `slack_token` wurde von der Slack OAuth & Permissions Seite abgerufen
- [ ] `slack_token` wurde zu MongoDB hinzugefügt
- [ ] Bot antwortet auf Nachrichten in Slack-Kanälen
- [ ] Bot antwortet auf Direktnachrichten in Slack

______________________________________________________________________

## Fehlerbehebung :wrench:

### Bot antwortet nicht in Teams

- **Messaging Endpoint Probleme:**
  - Überprüfen Sie, ob der Bot Framework Messaging Endpoint im Teams Developer Portal auf `/api/v1/messages` eingestellt
    ist
  - Stellen Sie sicher, dass die Endpoint-URL öffentlich zugänglich ist (Test mit curl oder Browser)
  - Für die lokale Entwicklung bestätigen Sie, dass Azure DevTunnel oder ngrok läuft
- **Authentifizierungsprobleme:**
  - Überprüfen Sie, ob `APP_PASSWORD` (Client Secret) korrekt ist und nicht abgelaufen ist
  - Bestätigen Sie, dass `APP_TENANTID` und `APP_ID` mit den Werten aus Schritt 6 übereinstimmen
  - Überprüfen Sie, ob `APP_TYPE` korrekt eingestellt ist (`SingleTenant` oder `MultiTenant`)
- **Konfigurationsprobleme:**
  - Überprüfen Sie die App-Berechtigungen im Teams Developer Portal (Message Read/Send in Chat/Team)
  - Verifizieren Sie, dass der MongoDB `bot_paths`-Eintrag mit den korrekten Anmeldeinformationen existiert
  - Überprüfen Sie, dass das `path`-Feld in MongoDB einen gültigen internen Routing-Pfad enthält
  - Stellen Sie sicher, dass die Konversation mit dem korrekten `path`-Wert erstellt wurde

### Slack-Integrationsprobleme

- Verifizieren Sie, dass `slack_token` gültig ist (beginnt mit `xoxb-`)
- Überprüfen Sie, ob die Slack App die notwendigen Bot Token Scopes hat:
  - `chat:write` (erforderlich zum Senden von Nachrichten)
  - `assistant:write` (erforderlich für App Agent Interaktionen)
  - `channels:history`, `groups:history`, `im:history`, `mpim:history` (für Nachrichten-Events)
- Überprüfen Sie, ob die App Home-Einstellungen konfiguriert sind:
  - "Always show my bot as online" sollte auf ON stehen
  - "Home Tab" sollte auf ON stehen
  - "Allow users to send Slash commands and messages from the messages tab" sollte aktiviert sein
- Bestätigen Sie, dass der Bot zu den gewünschten Slack-Kanälen hinzugefügt wurde (laden Sie den Bot mit @botname ein)
- Stellen Sie sicher, dass alle 6 Bot-Events in den Event Subscriptions abonniert sind
- Verifizieren Sie, dass die Event Subscription URL "Verified ✓" anzeigt
- Überprüfen Sie, ob die Redirect URL in den Slack OAuth-Einstellungen korrekt hinzugefügt wurde
- Stellen Sie sicher, dass das `slack_token`-Feld in MongoDB kein leerer String ist
- Überprüfen Sie die Bot Framework Slack-Kanal-Konfiguration
- Installieren Sie die Slack App neu, wenn Scopes nach der ersten Installation geändert wurden (erforderlich, damit
  Scope-Änderungen wirksam werden)

### MongoDB Verbindungsprobleme

- Überprüfen Sie, ob der Collections-Name `bot_paths` ist
- Überprüfen Sie, ob die Dokumentstruktur den obigen Beispielen entspricht
- Stellen Sie sicher, dass alle erforderlichen Felder im `credentials`-Objekt vorhanden sind
- Validieren Sie, dass `APP_ID` und `APP_TENANTID` im korrekten UUID-Format vorliegen
- Bestätigen Sie, dass das `path`-Feld mit `/api/` beginnt

______________________________________________________________________

## Best Practices für die Sicherheit :shield:

1. **Committen Sie niemals Secrets in die Versionskontrolle**
2. **Rotieren Sie Client Secrets vor Ablauf**
3. **Verwenden Sie Umgebungsvariablen für sensible Daten**
4. **Beschränken Sie den MongoDB-Zugriff mit der richtigen Authentifizierung**
5. **Überwachen Sie die Nutzung von OAuth-Tokens auf Anomalien**
6. **Führen Sie Audit-Logs für Bot-Pfad-Modifikationen**
7. **Verwenden Sie HTTPS für alle Messaging-Endpoints**

______________________________________________________________________

## Support :sos:

Bei Problemen oder Fragen:

- **Teams Developer Portal**:
  [Microsoft Teams Dokumentation](https://learn.microsoft.com/en-us/microsoftteams/platform/)
- **Bot Framework**: [Azure Bot Service Dokumentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- **Slack API**: [Slack API Dokumentation](https://api.slack.com/)

______________________________________________________________________

## Nächste Schritte :rocket:

Nach Abschluss der manuellen Bot-Einrichtung:

1. **Testen Sie Ihren Bot**: Senden Sie eine Nachricht in Teams oder Slack, um zu überprüfen, ob der Bot korrekt
   antwortet
2. **Überprüfen Sie Logs**: Suchen Sie in den Anwendungs-Logs nach Fehlern oder Warnungen während der Bot-Interaktionen
3. **Zusätzliche Funktionen konfigurieren**: Entdecken Sie
   [Bot-in-the-Loop](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für die Mensch-KI-Zusammenarbeit
4. **Benutzerdefinierte Logik implementieren**: Siehe den [Developer's Guide](../../../6_code_deep_dive/aihub_bot/) für
   benutzerdefinierte Bot-Implementierungen
5. **Performance überwachen**: Richten Sie Observability und Monitoring für Produktions-Deployments ein

______________________________________________________________________

*Zuletzt aktualisiert: 14. November 2025*
