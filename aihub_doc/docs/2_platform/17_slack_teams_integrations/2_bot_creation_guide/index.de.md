---
title: Manuelle Einrichtungsanleitung für die Bot-Erstellung
source_sha: 270e9cda82355a78e869e8e87a05d33df7f9d34fc685ef5f4ceebc0a7af263a4
---

# Manuelle Einrichtungsanleitung für die Bot-Erstellung :robot: :wrench:

::: info **Kurz gesagt – Worum geht es in dieser Anleitung?**
Dieses umfassende Handbuch bietet **Schritt-für-Schritt-Anweisungen zur manuellen Erstellung und Konfiguration von
Bots** mit Microsoft Teams- und Slack-Integration. Verwenden Sie diese Anleitung, wenn Sie neue Bots von Grund auf neu
erstellen, Azure Bot Framework-Kanäle konfigurieren oder bestehende Bot-Deployments beheben müssen. Es deckt alles ab,
von der Einrichtung des Teams Developer Portal bis zur MongoDB-Konfiguration und Slack OAuth-Integration.
:::

::: tip Automatisierte Einrichtung verfügbar
Bevor Sie mit der manuellen Einrichtung fortfahren, ziehen Sie die Verwendung des **automatisierten
Einrichtungs-Skripts** in Betracht, das die meisten dieser Schritte für Sie erledigt:

```bash
python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "my-ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/messages" \
    --mongo-connection-string "mongodb://localhost:27017"
```

**Wann der automatisierte Script zu verwenden ist:**

- Erstellung neuer Bots für das Produktions-Deployment
- Standard-Single-Bot- oder Multi-Bot-Konfigurationen
- Schnelle Einrichtung ohne Anpassung

**Wann diese manuelle Anleitung zu verwenden ist:**

- Behebung von Fehlern bei der automatisierten Einrichtung
- Detailliertes Verständnis der Bot-Konfiguration
- Erstellung benutzerdefinierter oder nicht-standardmäßiger Konfigurationen
- Erlernen der Funktionsweise der Bot-Integration

Für Details zur automatisierten Einrichtung siehe die [Azure Bot Service Integration Anleitung](../1_setup/).
:::

## Zugehörige Dokumentation :books:

- **[Übersicht über Slack- und Teams-Integrationen](../)** - Konzepte und Geschäftsnutzen auf hoher Ebene
- **[Azure Bot Service Integration](../1_setup/)** - Anleitung zur automatisierten Einrichtung
- **[AI-Hub Bot Entwicklerhandbuch](../../../6_code_deep_dive/aihub_bot/)** - Technische Implementierungsdetails
- **[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** -
  Mensch-KI-Kollaborations-Workflows

## Wichtige Terminologie :book:

Das Verständnis dieser Begriffe ist entscheidend für eine erfolgreiche Bot-Konfiguration:

| Begriff                                | Definition                                                                                                                                                                                                                                           |
| :------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bot Framework Nachrichten-Endpunkt** | Die einzige öffentliche URL, an die der Azure Bot Service ALLE Bot-Nachrichten sendet. Immer `/api/v1/messages`. Im Teams Developer Portal konfiguriert (Schritt 3).                                                                                 |
| **MongoDB "path"-Feld**                | Interner Routing-Pfad, der bestimmt, welche Bot-Implementierung eine Konversation verarbeitet. Beispiele: `/api/v1/agent/chat/completions/...` oder `/api/v1/openai/chat/completions`. Konfiguriert in der MongoDB-Sammlung `bot_paths` (Schritt 7). |
| **App-ID / Client-ID**                 | Azure AD Anwendungs-ID (UUID-Format). Gleicher Wert wird als Bot-ID und in MongoDB `credentials.APP_ID` verwendet.                                                                                                                                   |
| **Client Secret / App-Passwort**       | Azure AD Anwendungsschlüssel. In MongoDB als `credentials.APP_PASSWORD` gespeichert. Läuft ab und muss rotiert werden.                                                                                                                               |
| **Tenant-ID**                          | Microsoft 365 Tenant-ID. Erforderlich für SingleTenant-Bots, gespeichert als `credentials.APP_TENANTID`.                                                                                                                                             |
| **Bot-in-the-Loop**                    | Muster, bei dem AI Agents über Slack-Kanäle menschliche Eingaben während der Workflow-Ausführung anfordern.                                                                                                                                          |
| **Slack Bot OAuth Token**              | Token für die Slack-Integration (Format: `xoxb-...`). In MongoDB als `slack_token` gespeichert.                                                                                                                                                      |

::: warning Wichtiger Unterschied
**Bot Framework Nachrichten-Endpunkt** (`/api/v1/messages`) ≠ **MongoDB "path"-Feld** (z.B.
`/api/v1/agent/chat/completions/...`)

Dies sind zwei unterschiedliche Konzepte, die verschiedenen Zwecken dienen. Der Nachrichten-Endpunkt ist der Ort, an den
der Azure Bot Service Nachrichten sendet. Das `path`-Feld bestimmt, wie diese Nachrichten intern verarbeitet werden.
:::

## Voraussetzungen :clipboard:

Stellen Sie vor dem Start sicher, dass Sie Zugang haben zu:

- **Microsoft Teams Entwicklerportal** - Zum Erstellen von Teams-Apps und Bots
- **MongoDB-Datenbank** mit `bot_paths` Sammlung - Zum Speichern der Bot-Konfiguration
- **Azure Bot Framework** - Für das Multi-Channel-Bot-Management
- **Slack Workspace** mit Administratorberechtigungen - Für die Slack-Integration

______________________________________________________________________

## Teil 1: Teams Developer Portal Einrichtung :microsoft:

### Schritt 1: App mit grundlegenden Informationen erstellen

1. Navigieren Sie zum [Teams Developer Portal](https://dev.teams.microsoft.com/)
2. Klicken Sie auf **"Apps"** → **"Neue App"**
3. Füllen Sie die grundlegenden Informationen aus:
   - App-Name
   - Kurze Beschreibung
   - Vollständige Beschreibung
   - Entwicklerinformationen
   - App-URLs
   - Anwendungs-(Client-)ID (bei Bedarf generieren)

### Schritt 2: Berechtigungen konfigurieren

1. Gehen Sie zu **"App features"** → **"Bot"**
2. Legen Sie die erforderlichen Berechtigungen fest:
   - **Nachrichten lesen** in Chat/Team
   - **Nachrichten senden** in Chat/Team
3. Speichern Sie die Berechtigungsänderungen

### Schritt 3: Neuen Bot erstellen

1. Navigieren Sie in der App zum Abschnitt **"Bot"**
2. Klicken Sie auf **"Einrichten"** oder **"Neuen Bot erstellen"**
3. Geben Sie die **Bot Framework Nachrichten-Endpunkt-URL** ein:
   - Format: `https://your-domain.com/api/v1/messages`
   - Dies ist der Standard-Endpunkt des Azure Bot Service
   - Muss öffentlich über das Internet zugänglich sein
   - Für die lokale Entwicklung verwenden Sie Azure DevTunnel oder ngrok
4. **Notieren Sie die Bot-ID** zur späteren Verwendung

::: warning Bot Framework Endpunkt vs. MongoDB-Pfad
**WICHTIGER UNTERSCHIED:**

- **Bot Framework Nachrichten-Endpunkt** (`/api/v1/messages`): Der einzige Einstiegspunkt, an den der Azure Bot Service
  ALLE Bot-Nachrichten sendet. Dies wird hier im Teams Developer Portal konfiguriert.

- **MongoDB "path"-Feld** (z.B. `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`): Interner Routing-
  Pfad, der bestimmt, welche Bot-Implementierung die Konversation verarbeitet. Dies wird in MongoDB konfiguriert
  (Schritt 7) und ermöglicht es, dass mehrere Bots koexistieren.

**Funktionsweise:**

1. Azure Bot Service sendet Nachricht an `/api/v1/messages`
2. AI-Hub sucht den `path` der Konversation in der MongoDB-Sammlung `bot_paths`
3. Die Anfrage wird an die spezifische Bot-Implementierung weitergeleitet

**Beispiel:**

- Teams Developer Portal Endpunkt: `https://my-domain.com/api/v1/messages`
- MongoDB-Pfad für Agent Bot: `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
- MongoDB-Pfad für OpenAI Bot: `/api/v1/openai/chat/completions`

Diese müssen NICHT übereinstimmen! Der Nachrichten-Endpunkt ist immer `/api/v1/messages`.
:::

::: tip Lokale Entwicklung
Für die lokale Entwicklung legen Sie Ihren Bot-Server mit Azure DevTunnel offen:

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Verwenden Sie die https-URL (z.B. https://abc123-8000.devtunnels.ms/api/v1/messages)
```

Siehe das [Entwicklerhandbuch](../../../6_code_deep_dive/aihub_bot/) für eine detaillierte lokale
Entwicklungseinrichtung.
:::

### Schritt 4: Client Secret erstellen

1. Finden Sie in der Bot-Konfiguration **"Client secrets"**
2. Klicken Sie auf **"Add a client secret"**
3. **WICHTIG**: Kopieren und speichern Sie das Client Secret sofort sicher ab
   - Secret-Format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Sie werden es später nicht mehr anzeigen können
4. Notieren Sie das Ablaufdatum des Secrets

::: danger Sicherheitswarnung
Client Secrets werden nur einmal zum Zeitpunkt der Erstellung angezeigt. Speichern Sie sie sofort sicher in einem
Passwort-Manager oder Secrets Vault. Bei Verlust müssen Sie ein neues Secret generieren und Ihre MongoDB-Konfiguration
aktualisieren.
:::

### Schritt 5: Bot zur App hinzufügen

1. Navigieren Sie zurück zur App-Übersicht
2. Bestätigen Sie, dass der Bot unter **"App features"** aufgeführt ist
3. Überprüfen Sie, ob die Bot-ID mit der in Schritt 3 erstellten übereinstimmt

### Schritt 6: App in der Organisation veröffentlichen

1. Gehen Sie zu **"Publish"** → **"Publish to org"**
2. Überprüfen Sie alle Konfigurationen
3. Klicken Sie auf **"Publish"**
4. Warten Sie auf die Administratorgenehmigung (falls erforderlich)
5. Nach der Genehmigung notieren Sie die **App-/Client-ID** und die **Tenant-ID**

______________________________________________________________________

## Teil 2: MongoDB-Konfiguration :floppy_disk:

### Schritt 7: Bot-Pfad-Eintrag hinzufügen

Fügen Sie ein neues Dokument zur `bot_paths`-Sammlung mit folgender Struktur hinzu:

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
  - **Dies ist NICHT der Bot Framework Nachrichten-Endpunkt** (der immer `/api/v1/messages` ist)
  - Dies bestimmt, welcher Bot-Handler Konversationen verarbeitet
  - Beispiele:
    - `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json` - Agent-basierter Bot
    - `/api/v1/openai/chat/completions` - Direkter OpenAI-Bot
    - `/api/v1/bitl/chat/completions` - Bot-in-the-Loop Bot
- `credentials`: Objekt mit Azure Bot-Authentifizierung
  - `APP_TYPE`: Authentifizierungstyp (`"SingleTenant"` oder `"MultiTenant"`)
  - `APP_ID`: Teams App Client-ID aus Schritt 6
  - `APP_PASSWORD`: Client Secret aus Schritt 4
  - `APP_TENANTID`: Microsoft 365 Tenant-ID aus Schritt 6 (erforderlich für SingleTenant)
- `system_message`: Standard-Systemnachricht/Anweisungen für den Bot
- `slack_token`: Anfangs ein leerer String (wird in Schritt 14 für die Slack-Integration ausgefüllt)

::: tip Multi-Bot-Konfiguration
Sie können **mehrere Bot-Implementierungen** mit unterschiedlichen `path`-Werten haben, die alle denselben Bot Framework
Nachrichten-Endpunkt (`/api/v1/messages`) teilen:

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

Jede Konversation ist mit einem `path` verknüpft, der ihre Bot-Implementierung und ihr Verhalten bestimmt.
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
4. Geben Sie Ihrer App einen Namen (z.B. "Mein Bot Name")
5. Wählen Sie den Workspace aus, in dem Sie die App entwickeln möchten
6. Klicken Sie auf **"Create App"**

### Schritt 8.5: App Home-Einstellungen konfigurieren

1. Gehen Sie zu den App Home-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/app-home`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/app-home`
2. Im Abschnitt **"Show Tabs"**:
   - Schalten Sie **"Always show my bot as online"** auf **ON**
   - Schalten Sie **"Home Tab"** auf **ON**
3. Im Abschnitt **"Messages Tab"**:
   - **Lassen Sie "Messages Tab" deaktiviert** - Der Bot interagiert stattdessen über Kanäle und Direktnachrichten
   - Deaktivieren Sie "Allow users to send Slash commands and messages from the messages tab" (falls sichtbar)
4. Klicken Sie auf **"Save Changes"**, falls dazu aufgefordert

::: info Konfiguration des Nachrichten-Tabs
Der Nachrichten-Tab ist typischerweise deaktiviert, wenn das Bot Framework verwendet wird, da der Bot über Kanäle,
Gruppenchats und Direktnachrichten kommuniziert, anstatt über den Nachrichten-Tab der App.
:::

### Schritt 9: Slack-Kanal des Bot Frameworks konfigurieren

1. Navigieren Sie zum [Bot Framework Portal](https://dev.botframework.com/)
2. Gehen Sie zur Kanalseite Ihres Bots:
   - URL-Format: `https://dev.botframework.com/bots/channels?id={APP_ID}&channelId=slack`
   - Ersetzen Sie `{APP_ID}` durch Ihre Teams App-ID (aus Schritt 6)
   - Beispiel: `https://dev.botframework.com/bots/channels?id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&channelId=slack`
3. Klicken Sie auf den Kanal **"Slack"** oder **"Configure"**, falls bereits hinzugefügt
4. Kopieren Sie die App-Anmeldeinformationen aus Ihrer Slack-App (aus Schritt 8):
   - **Client-ID** (aus Slack App Credentials)
   - **Client Secret** (aus Slack App Credentials)
5. Fügen Sie diese in die Slack-Kanal-Konfiguration des Bot Frameworks ein
6. Kopieren Sie die folgenden URLs zur späteren Verwendung:
   - **Redirect URL** (für Schritt 10 benötigt)
   - **Event Subscription URL** (für Schritt 11 benötigt)
7. Klicken Sie auf **"Save"**
8. **WICHTIG:** Nach dem Speichern werden Sie automatisch zu Slack weitergeleitet, um die Anwendung zu installieren/neu
   zu installieren
   - Dies schließt den OAuth-Flow ab
   - Folgen Sie den Anweisungen, um die App zu autorisieren
   - Dies kann die Anforderungen für die Ereignisabonnements automatisch erfüllen

::: tip Automatische Konfiguration
Das Bot Framework konfiguriert während des OAuth-Flows oft viele Slack-Einstellungen automatisch. Überprüfen Sie nach
Abschluss von Schritt 9 die Schritte 10-12, um die Einstellungen zu bestätigen, anstatt alles manuell zu konfigurieren.
:::

### Schritt 10: Slack OAuth konfigurieren

1. Gehen Sie zu den OAuth-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/oauth`
2. Scrollen Sie nach unten zum Abschnitt **"Scopes"**
3. Unter **"Bot Token Scopes"** klicken Sie auf **"Add an OAuth Scope"**
4. Fügen Sie die folgenden Scopes hinzu:
   - `chat:write` - Erlaubt dem Bot, Nachrichten zu senden
   - `assistant:write` - Erlaubt dem Bot, mit App Agents/Assistants zu interagieren
5. Unter **"Redirect URLs"** klicken Sie auf **"Add New Redirect URL"**
6. Fügen Sie die **Redirect URL** vom Bot Framework ein (Schritt 9)
7. Klicken Sie auf **"Save URLs"**

::: info Automatische Scopes
Andere erforderliche Scopes (channels:history, groups:history, im:history, mpim:history) können automatisch hinzugefügt
werden, wenn Sie in Schritt 12 Bot-Events abonnieren oder wenn Sie den Bot Framework OAuth-Flow abschließen.
:::

### Schritt 11: Slack-Ereignisabonnements konfigurieren

1. Gehen Sie zu den Event Subscriptions Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/event-subscriptions`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/event-subscriptions`
2. Schalten Sie **"Enable Events"** auf ON
3. In **"Request URL"** fügen Sie die **Event Subscription URL** vom Bot Framework ein (Schritt 9)
4. Warten Sie auf die URL-Verifizierung (sollte "Verified ✓" anzeigen)

::: tip Bereits konfiguriert?
Wenn Sie während Schritt 9 zu Slack weitergeleitet wurden und die Installation abgeschlossen haben, sind die
Ereignisabonnements möglicherweise bereits automatisch vom Bot Framework konfiguriert worden. Überprüfen Sie diese Seite
zur Bestätigung.
:::

### Schritt 12: Bot-Ereignisse abonnieren (falls erforderlich)

::: warning Optionaler Schritt
Diese Ereignisabonnements sind möglicherweise nicht erforderlich, wenn der Bot Framework Slack-Kanal sie automatisch
verarbeitet. Prüfen Sie, ob Ereignisse bereits konfiguriert sind, bevor Sie sie manuell hinzufügen.
:::

Wenn Ereignisse nicht automatisch konfiguriert sind, scrollen Sie auf der Event Subscriptions-Seite nach unten zu
**"Subscribe to bot events"** und fügen Sie Folgendes hinzu:

| Ereignisname                       | Beschreibung                                                               | Erforderlicher Scope |
| :--------------------------------- | :------------------------------------------------------------------------- | :------------------- |
| `message.channels`                 | Eine Nachricht wurde in einem Kanal gepostet                               | `channels:history`   |
| `message.groups`                   | Eine Nachricht wurde in einem privaten Kanal gepostet                      | `groups:history`     |
| `message.im`                       | Eine Nachricht wurde in einem Direktnachrichtenkanal gepostet              | `im:history`         |
| `message.mpim`                     | Eine Nachricht wurde in einem Mehrparteien-Direktnachrichtenkanal gepostet | `mpim:history`       |
| `assistant_thread_started`         | Ein App Agent-Thread wurde gestartet                                       | keine                |
| `assistant_thread_context_changed` | Der Kontext hat sich geändert, während ein App Agent-Thread sichtbar war   | keine                |

::: info Automatische Scope-Hinzufügung
Wenn Sie diese Ereignisse hinzufügen, fügt Slack automatisch die notwendigen OAuth-Scopes zu Ihrer App-Konfiguration
hinzu.
:::

Klicken Sie auf **"Save Changes"**

### Schritt 13: Slack-App im Workspace installieren

::: tip Möglicherweise bereits abgeschlossen
Wenn Sie während Schritt 9 zu Slack weitergeleitet wurden und die Installation abgeschlossen haben, ist dieser Schritt
möglicherweise bereits abgeschlossen. Sie können dies überprüfen, indem Sie prüfen, ob der Bot bereits in Ihrem
Slack-Workspace erscheint.
:::

Falls noch nicht installiert:

1. Gehen Sie zur Installationsseite Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/install-on-team`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack-App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/install-on-team`
2. Klicken Sie auf **"Install to Workspace"** (oder **"Reinstall to Workspace"**, wenn Sie aktualisieren)
3. Überprüfen Sie die angeforderten Berechtigungen
4. Klicken Sie auf **"Allow"**
5. **WICHTIG:** Kopieren Sie den angezeigten **Bot User OAuth Token**
   - Format: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`
   - Dies ist das Token, das Sie im nächsten Schritt zu MongoDB hinzufügen werden

**Alternative:** Falls bereits installiert, rufen Sie Ihr Token ab unter:

- Seite **OAuth & Permissions**: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
- Suchen Sie nach **"Bot User OAuth Token"** unter "OAuth Tokens for Your Workspace"

::: danger Token-Sicherheit
Das Slack Bot OAuth Token bietet vollen Zugriff auf die Funktionen Ihres Bots. Speichern Sie es sicher und übertragen
Sie es niemals in die Versionskontrolle. Behandeln Sie es mit der gleichen Sicherheit wie Passwörter und API-Schlüssel.
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

**Details zum Slack OAuth Token:**

- Format: `xoxb-` gefolgt von Zahlen und Bindestrichen
- Erhalten in Schritt 13 während der Installation der Slack-App
- Ersetzen Sie den leeren String `""` durch das tatsächliche Token
- Bewahren Sie dieses Token sicher auf und committen Sie es niemals in die Versionskontrolle

**Dokument aktualisieren:**

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

## App-Manifest-Beispiele :page_facing_up:

Diese Manifeste zeigen die vollständige Konfiguration für Slack- und Teams-Apps. Sie können diese als Referenz verwenden
oder Apps programmatisch erstellen.

### Slack App-Manifest

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

- **app_home**: Konfiguration für die Start- und Nachrichten-Tabs der App
  - **home_tab_enabled**: Auf `true` gesetzt, um den Home-Tab zu aktivieren
  - **messages_tab_enabled**: Auf `false` gesetzt (Interaktion erfolgt über Kanäle/DMs, nicht über den Nachrichten-Tab)
  - **messages_tab_read_only_enabled**: Auf `false` gesetzt
- **always_online**: Auf `true` gesetzt, um den Bot immer als online anzuzeigen
- **redirect_urls**: Immer `https://slack.botframework.com` für die Bot Framework-Integration
- **request_url**: Das Format ist `https://slack.botframework.com/api/Events/{APP_ID}`, wobei `{APP_ID}` Ihre Teams App
  Client-ID ist
- **bot scopes**: Alle 6 Scopes sind für die volle Funktionalität erforderlich (einschließlich `chat:write` und
  `assistant:write`)
- **bot_events**: Alle 6 Ereignisse ermöglichen es dem Bot, Nachrichten über alle Konversationstypen hinweg zu empfangen

### Teams App-Manifest

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

- **id** und **webApplicationInfo.id**: Ihre Teams App Client-ID (APP_ID)
- **botId**: Entspricht Ihrer App Client-ID
- **scopes**: Aktivieren Sie den Bot in persönlichen Chats, Teams und Gruppenchats
- **supportsFiles**: Auf `true` gesetzt, um Dateiuploads zu ermöglichen
- **Ressourcenspezifische Berechtigungen**:
  - `ChannelMessage.Read.Group` - Nachrichten in Kanälen lesen
  - `ChannelMessage.Send.Group` - Nachrichten in Kanälen senden
  - `ChatMessage.Read.Chat` - Nachrichten in Chats lesen
  - `ChatMessage.Send.Chat` - Nachrichten in Chats senden

### Verwendung von Manifesten für die App-Erstellung

**Slack:**

1. Gehen Sie zu [Slack API Apps](https://api.slack.com/apps)
2. Klicken Sie auf **"Create New App"** → **"From an app manifest"**
3. Wählen Sie Ihren Workspace aus
4. Fügen Sie das Slack-Manifest-JSON ein
5. Überprüfen und erstellen Sie die App

**Teams:**

1. Laden Sie das Manifest als `manifest.json` herunter
2. Fügen Sie die Icon-Dateien (`outline.png` und `color.png`) in dasselbe Verzeichnis ein
3. Zippen Sie alle drei Dateien zusammen
4. Im Teams Developer Portal klicken Sie auf **"Import app"**
5. Laden Sie die Zip-Datei hoch

______________________________________________________________________

## Verifizierungs-Checkliste :white_check_mark:

Nachdem Sie alle Schritte abgeschlossen haben, überprüfen Sie:

**Teams-Konfiguration:**

- [ ] Teams App ist veröffentlicht und genehmigt
- [ ] Bot Framework Nachrichten-Endpunkt ist auf `/api/v1/messages` gesetzt
- [ ] Bot Framework Nachrichten-Endpunkt-URL ist öffentlich zugänglich
- [ ] Bot antwortet auf Nachrichten in Teams
- [ ] Bot-Berechtigungen sind korrekt gesetzt (Nachrichten lesen/senden in Chat/Team)

**MongoDB-Konfiguration:**

- [ ] `bot_paths`-Eintrag existiert mit allen erforderlichen Feldern
- [ ] `credentials`-Objekt enthält APP_TYPE, APP_ID, APP_PASSWORD und APP_TENANTID (für SingleTenant)
- [ ] `path`-Feld enthält den internen Routing-Pfad (z.B. `/api/v1/agent/chat/completions/...`)
- [ ] `path`-Feld ist UNTERSCHIEDLICH vom Bot Framework Nachrichten-Endpunkt (`/api/v1/messages`)
- [ ] `system_message` ist für den Zweck des Bots angemessen konfiguriert
- [ ] Client Secret (APP_PASSWORD) ist sicher gespeichert und nicht abgelaufen

**Slack-Konfiguration:**

- [ ] Slack App ist mit korrektem Namen erstellt
- [ ] App Home konfiguriert: "Always show my bot as online" Umschalter AN
- [ ] App Home konfiguriert: "Home Tab" Umschalter AN
- [ ] App Home konfiguriert: "Messages Tab" ist deaktiviert (Bot interagiert über Kanäle/DMs)
- [ ] Bot Token Scopes `chat:write` und `assistant:write` sind in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Bot Framework Slack-Kanal ist mit Client-ID und Client Secret konfiguriert
- [ ] Bot Framework-Konfiguration gespeichert und OAuth-Weiterleitung zu Slack abgeschlossen
- [ ] Redirect URL ist in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Event Subscription URL ist verifiziert (kann automatisch erfolgen)
- [ ] Bot-Ereignisse sind abonniert (kann automatisch über Bot Framework erfolgen)
- [ ] Slack App ist im Workspace installiert (kann während der Weiterleitung in Schritt 9 erfolgt sein)
- [ ] `slack_token` ist von der Slack OAuth & Permissions-Seite erhalten
- [ ] `slack_token` ist zu MongoDB hinzugefügt
- [ ] Bot antwortet auf Nachrichten in Slack-Kanälen
- [ ] Bot antwortet auf Direktnachrichten in Slack

______________________________________________________________________

## Fehlerbehebung :wrench:

### Bot reagiert nicht in Teams

- **Probleme mit dem Nachrichten-Endpunkt:**
  - Überprüfen Sie, ob der Bot Framework Nachrichten-Endpunkt im Teams Developer Portal auf `/api/v1/messages` gesetzt
    ist
  - Stellen Sie sicher, dass die Endpunkt-URL öffentlich zugänglich ist (mit curl oder Browser testen)
  - Bestätigen Sie für die lokale Entwicklung, dass Azure DevTunnel oder ngrok läuft
- **Authentifizierungsprobleme:**
  - Prüfen Sie, ob `APP_PASSWORD` (Client Secret) korrekt und nicht abgelaufen ist
  - Bestätigen Sie, dass `APP_TENANTID` und `APP_ID` mit den Werten aus Schritt 6 übereinstimmen
  - Überprüfen Sie, ob `APP_TYPE` korrekt gesetzt ist (`SingleTenant` oder `MultiTenant`)
- **Konfigurationsprobleme:**
  - Überprüfen Sie die App-Berechtigungen im Teams Developer Portal (Nachrichten lesen/senden in Chat/Team)
  - Verifizieren Sie, dass der MongoDB `bot_paths`-Eintrag mit den korrekten Anmeldeinformationen existiert
  - Prüfen Sie, ob das `path`-Feld in MongoDB einen gültigen internen Routing-Pfad enthält
  - Stellen Sie sicher, dass die Konversation mit dem korrekten `path`-Wert erstellt wurde

### Probleme mit der Slack-Integration

- Verifizieren Sie, dass `slack_token` gültig ist (beginnt mit `xoxb-`)
- Überprüfen Sie, ob die Slack-App die notwendigen Bot-Token-Scopes hat:
  - `chat:write` (zum Senden von Nachrichten erforderlich)
  - `assistant:write` (für App Agent-Interaktionen erforderlich)
  - `channels:history`, `groups:history`, `im:history`, `mpim:history` (für Nachrichtenereignisse)
- Überprüfen Sie, ob die App Home-Einstellungen konfiguriert sind:
  - "Always show my bot as online" sollte AN sein
  - "Home Tab" sollte AN sein
  - "Allow users to send Slash commands and messages from the messages tab" sollte aktiviert sein
- Bestätigen Sie, dass der Bot zu den gewünschten Slack-Kanälen hinzugefügt ist (Bot mit @botname einladen)
- Stellen Sie sicher, dass alle 6 Bot-Ereignisse in den Event Subscriptions abonniert sind
- Verifizieren Sie, dass die Event Subscription URL "Verified ✓" anzeigt
- Prüfen Sie, ob die Redirect URL in den Slack OAuth-Einstellungen korrekt hinzugefügt ist
- Stellen Sie sicher, dass das Feld `slack_token` in MongoDB kein leerer String ist
- Überprüfen Sie die Konfiguration des Bot Framework Slack-Kanals
- Installieren Sie die Slack-App neu, wenn Scopes nach der Erstinstallation geändert wurden (erforderlich, damit
  Scope-Änderungen wirksam werden)

### Probleme mit der MongoDB-Verbindung

- Überprüfen Sie, ob der Sammlungsname `bot_paths` ist
- Prüfen Sie, ob die Dokumentstruktur den obigen Beispielen entspricht
- Stellen Sie sicher, dass alle erforderlichen Felder im `credentials`-Objekt vorhanden sind
- Validieren Sie, dass `APP_ID` und `APP_TENANTID` im korrekten UUID-Format sind
- Bestätigen Sie, dass das `path`-Feld mit `/api/` beginnt

______________________________________________________________________

## Best Practices für Sicherheit :shield:

1. **Secrets niemals im Versionskontrollsystem speichern**
2. **Client Secrets vor Ablauf rotieren**
3. **Umgebungsvariablen für sensible Daten verwenden**
4. **MongoDB-Zugriff mit geeigneter Authentifizierung einschränken**
5. **Nutzung von OAuth-Token auf Anomalien überwachen**
6. **Audit-Logs von Bot-Pfad-Änderungen führen**
7. **HTTPS für alle Nachrichten-Endpunkte verwenden**

______________________________________________________________________

## Support :sos:

Für Probleme oder Fragen:

- **Teams Developer Portal**:
  [Microsoft Teams Dokumentation](https://learn.microsoft.com/en-us/microsoftteams/platform/)
- **Bot Framework**: [Azure Bot Service Dokumentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- **Slack API**: [Slack API Dokumentation](https://api.slack.com/)

______________________________________________________________________

## Nächste Schritte :rocket:

Nachdem Sie die manuelle Bot-Einrichtung abgeschlossen haben:

1. **Testen Sie Ihren Bot**: Senden Sie eine Nachricht in Teams oder Slack, um zu überprüfen, ob der Bot korrekt
   antwortet
2. **Logs überprüfen**: Prüfen Sie die Anwendungsprotokolle auf Fehler oder Warnungen während der Bot-Interaktionen
3. **Zusätzliche Funktionen konfigurieren**: Erkunden Sie
   [Bot-in-the-Loop](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für Mensch-KI-Kollaboration
4. **Benutzerdefinierte Logik implementieren**: Siehe das [Entwicklerhandbuch](../../../6_code_deep_dive/aihub_bot/) für
   benutzerdefinierte Bot-Implementierungen
5. **Performance überwachen**: Richten Sie Observability und Monitoring für Produktions-Deployments ein

______________________________________________________________________

*Zuletzt aktualisiert: 14. November 2025*
