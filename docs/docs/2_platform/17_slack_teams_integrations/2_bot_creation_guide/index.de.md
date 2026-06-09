---
title: Manuelle Anleitung zur Bot-Erstellung
source_sha: 739cc666e50837c64fb814d34e4fc7dbcf2706c3bdf21b25d1e1cdc63d686421
---

# Manuelle Anleitung zur Bot-Erstellung :robot: :wrench:

::: info **TL;DR – Worum geht es in diesem Leitfaden?**
Dieses umfassende Handbuch bietet **Schritt-für-Schritt-Anleitungen zur manuellen Erstellung und Konfiguration von
Bots** mit Microsoft Teams- und Slack-Integration. Nutzen Sie diesen Leitfaden, wenn Sie neue Bots von Grund auf
erstellen, Azure Bot Framework-Kanäle konfigurieren oder bestehende Bot-Deployments beheben müssen. Er deckt alles ab,
von der Einrichtung des Teams Developer Portals über die MongoDB-Konfiguration bis hin zur Slack OAuth-Integration.
:::

::: tip Automatisierte Einrichtung verfügbar
Bevor Sie mit der manuellen Einrichtung fortfahren, sollten Sie das **automatisierte Einrichtungs-Skript** verwenden,
das die meisten dieser Schritte für Sie erledigt:

```bash
python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "my-ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/messages" \
    --mongo-connection-string "mongodb://localhost:27017"
```

**Wann sollte das automatisierte Skript verwendet werden:**

- Erstellung neuer Bots für das Produktions-Deployment
- Standard-Einzelbot- oder Multibot-Konfigurationen
- Schnelle Einrichtung ohne Anpassung

**Wann sollte dieser manuelle Leitfaden verwendet werden:**

- Fehlerbehebung bei automatisierten Einrichtungsfehlern
- Detailliertes Verständnis der Bot-Konfiguration
- Erstellung benutzerdefinierter oder nicht standardisierter Konfigurationen
- Verständnis der Bot-Integration

Für Details zur automatisierten Einrichtung, siehe das [Azure Bot Service Integrationshandbuch](../1_setup/).
:::

## Verwandte Dokumentation :books:

- **[Übersicht über Slack- & Teams-Integrationen](../)** – Hochrangige Konzepte und Geschäftswert
- **[Azure Bot Service Integration](../1_setup/)** – Automatisierte Einrichtungsanleitung
- **[Swiss AI Hub Bot Entwicklerhandbuch](../../../6_code_deep_dive/packages/bot/)** – Technische
  Implementierungsdetails
- **[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** –
  Human-AI-Kollaborations-Workflows

## Schlüsselbegriffe :book:

Das Verständnis dieser Begriffe ist entscheidend für eine erfolgreiche Bot-Konfiguration:

| Begriff                              | Definition                                                                                                                                                                                                                                           |
| :----------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bot Framework Messaging-Endpunkt** | Die einzelne öffentliche URL, an die der Azure Bot Service ALLE Bot-Nachrichten sendet. Immer `/api/v1/messages`. Konfiguriert im Teams Developer Portal (Schritt 3).                                                                                |
| **MongoDB `path`-Feld**              | Interner Routing-Pfad, der bestimmt, welche Bot-Implementierung eine Konversation verarbeitet. Beispiele: `/api/v1/agent/chat/completions/...` oder `/api/v1/openai/chat/completions`. Konfiguriert in der MongoDB `bot_paths`-Sammlung (Schritt 7). |
| **App-ID / Client-ID**               | Azure AD Anwendungs-ID (UUID-Format). Derselbe Wert wird als Bot-ID und in `credentials.APP_ID` in MongoDB verwendet.                                                                                                                                |
| **Client Secret / App-Passwort**     | Azure AD Anwendungs-Secret. In MongoDB als `credentials.APP_PASSWORD` gespeichert. Läuft ab und muss erneuert werden.                                                                                                                                |
| **Tenant-ID**                        | Microsoft 365 Tenant-ID. Erforderlich für SingleTenant-Bots, gespeichert als `credentials.APP_TENANTID`.                                                                                                                                             |
| **Bot-in-the-Loop**                  | Muster, bei dem KI-Agents während der Workflow-Ausführung über Slack-Kanäle menschliche Eingaben anfordern.                                                                                                                                          |
| **Slack Bot OAuth-Token**            | Token für die Slack-Integration (Format: `xoxb-...`). In MongoDB als `slack_token` gespeichert.                                                                                                                                                      |

::: warning Wichtiger Unterschied
**Bot Framework Messaging-Endpunkt** (`/api/v1/messages`) ≠ **MongoDB `path`-Feld** (z.B.
`/api/v1/agent/chat/completions/...`)

Dies sind zwei unterschiedliche Konzepte, die verschiedenen Zwecken dienen. Der Messaging-Endpunkt ist der Ort, an den
der Azure Bot Service Nachrichten sendet. Das `path`-Feld bestimmt, wie diese Nachrichten intern verarbeitet werden.
:::

## Voraussetzungen :clipboard:

Bevor Sie beginnen, stellen Sie sicher, dass Sie Zugang haben zu:

- **Microsoft Teams Developer Portal** – Zum Erstellen von Teams-Apps und Bots
- **MongoDB-Datenbank** mit `bot_paths`-Sammlung – Zum Speichern der Bot-Konfiguration
- **Azure Bot Framework** – Für Multi-Channel-Bot-Management
- **Slack Workspace** mit Admin-Berechtigungen – Für die Slack-Integration

______________________________________________________________________

## Teil 1: Einrichtung des Teams Developer Portals :microsoft:

### Schritt 1: App mit grundlegenden Informationen erstellen

1. Navigieren Sie zum [Teams Developer Portal](https://dev.teams.microsoft.com/)
2. Klicken Sie auf **„Apps“** → **„Neue App“**
3. Füllen Sie die grundlegenden Informationen aus:
   - App-Name
   - Kurze Beschreibung
   - Vollständige Beschreibung
   - Entwicklerinformationen
   - App-URLs
   - Anwendungs- (Client-)ID (bei Bedarf generieren)

### Schritt 2: Berechtigungen konfigurieren

1. Gehen Sie zu **„App-Funktionen“** → **„Bot“**
2. Legen Sie die erforderlichen Berechtigungen fest:
   - **Nachricht lesen** in Chat/Team
   - **Nachricht senden** in Chat/Team
3. Berechtigungsänderungen speichern

### Schritt 3: Neuen Bot erstellen

1. Navigieren Sie in der App zum Abschnitt **„Bot“**
2. Klicken Sie auf **„Einrichten“** oder **„Neuen Bot erstellen“**
3. Geben Sie die **Bot Framework Messaging-Endpunkt-URL** ein:
   - Format: `https://your-domain.com/api/v1/messages`
   - Dies ist der Standard-Endpunkt des Azure Bot Service
   - Muss öffentlich über das Internet zugänglich sein
   - Für die lokale Entwicklung verwenden Sie Azure DevTunnel oder ngrok
4. **Notieren Sie die Bot-ID** für die spätere Verwendung

::: warning Bot Framework-Endpunkt vs. MongoDB-Pfad
**WICHTIGER UNTERSCHIED:**

- **Bot Framework Messaging-Endpunkt** (`/api/v1/messages`): Der einzige Einstiegspunkt, an den der Azure Bot Service
  ALLE Bot-Nachrichten sendet. Dies wird hier im Teams Developer Portal konfiguriert.

- **MongoDB `path`-Feld** (z.B. `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`): Interner
  Routing-Pfad, der bestimmt, welche Bot-Implementierung die Konversation verarbeitet. Dies wird in MongoDB (Schritt 7)
  konfiguriert und ermöglicht die Koexistenz mehrerer Bots.

**So funktioniert es:**

1. Azure Bot Service sendet Nachrichten an `/api/v1/messages`
2. Swiss AI Hub sucht den `path` der Konversation in der MongoDB `bot_paths`-Sammlung
3. Die Anfrage wird an die spezifische Bot-Implementierung weitergeleitet

**Beispiel:**

- Teams Developer Portal-Endpunkt: `https://my-domain.com/api/v1/messages`
- MongoDB-Pfad für Agent Bot: `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
- MongoDB-Pfad für OpenAI Bot: `/api/v1/openai/chat/completions`

Diese müssen NICHT übereinstimmen! Der Messaging-Endpunkt ist immer `/api/v1/messages`.
:::

::: tip Lokale Entwicklung
Für die lokale Entwicklung exponieren Sie Ihren Bot-Server mit Azure DevTunnel:

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Use the https URL (e.g., https://abc123-8000.devtunnels.ms/api/v1/messages)
```

Für eine detaillierte lokale Entwicklungseinrichtung siehe das
[Entwicklerhandbuch](../../../6_code_deep_dive/packages/bot/).
:::

### Schritt 4: Client Secret erstellen

1. Suchen Sie in der Bot-Konfiguration nach **„Client Secrets“**
2. Klicken Sie auf **„Client Secret hinzufügen“**
3. **WICHTIG**: Kopieren und speichern Sie das Client Secret sofort sicher
   - Secret-Format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Sie können es danach nicht mehr einsehen
4. Notieren Sie das Ablaufdatum des Secrets

::: danger Sicherheitswarnung
Client Secrets werden nur einmal zum Zeitpunkt der Erstellung angezeigt. Speichern Sie sie sofort sicher in einem
Passwort-Manager oder Secrets-Vault. Bei Verlust müssen Sie ein neues Secret generieren und Ihre MongoDB-Konfiguration
aktualisieren.
:::

### Schritt 5: Bot zur App hinzufügen

1. Navigieren Sie zurück zur App-Übersicht
2. Bestätigen Sie, dass der Bot unter **„App-Funktionen“** aufgeführt ist
3. Überprüfen Sie, ob die Bot-ID mit der in Schritt 3 erstellten übereinstimmt

### Schritt 6: App in der Organisation veröffentlichen

1. Gehen Sie zu **„Veröffentlichen“** → **„In Organisation veröffentlichen“**
2. Überprüfen Sie alle Konfigurationen
3. Klicken Sie auf **„Veröffentlichen“**
4. Warten Sie auf die Administratorgenehmigung (falls erforderlich)
5. Nach Genehmigung notieren Sie die **App-/Client-ID** und **Tenant-ID**

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
  - **Dies ist NICHT der Bot Framework Messaging-Endpunkt** (der immer `/api/v1/messages` ist)
  - Dies bestimmt, welcher Bot-Handler Konversationen verarbeitet
  - Beispiele:
    - `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json` – Agent-basierter Bot
    - `/api/v1/openai/chat/completions` – Direkter OpenAI-Bot
    - `/api/v1/bitl/chat/completions` – Bot-in-the-Loop Bot
- `credentials`: Objekt, das die Azure Bot-Authentifizierung enthält
  - `APP_TYPE`: Authentifizierungstyp (`"SingleTenant"` oder `"MultiTenant"`)
  - `APP_ID`: Teams App-Client-ID aus Schritt 6
  - `APP_PASSWORD`: Client Secret aus Schritt 4
  - `APP_TENANTID`: Microsoft 365 Tenant-ID aus Schritt 6 (erforderlich für SingleTenant)
- `system_message`: Standard-Systemnachricht/Anweisungen für den Bot
- `slack_token`: Anfangs leerer String (wird in Schritt 14 für die Slack-Integration befüllt)

::: tip Multi-Bot-Konfiguration
Sie können **mehrere Bot-Implementierungen** mit unterschiedlichen `path`-Werten haben, die alle denselben Bot Framework
Messaging-Endpunkt (`/api/v1/messages`) teilen:

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
4. Geben Sie Ihrer App einen Namen (z.B. „Mein Bot-Name“)
5. Wählen Sie den Workspace aus, in dem Sie die App entwickeln möchten
6. Klicken Sie auf **„App erstellen“**

### Schritt 8.5: App Home-Einstellungen konfigurieren

1. Gehen Sie zu den App Home-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/app-home`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/app-home`
2. Im Abschnitt **„Tabs anzeigen“**:
   - Schalten Sie **„Meinen Bot immer als online anzeigen“** auf **EIN**
   - Schalten Sie **„Home-Tab“** auf **EIN**
3. Im Abschnitt **„Nachrichten-Tab“**:
   - **Lassen Sie den „Nachrichten-Tab“ deaktiviert** – der Bot interagiert stattdessen über Kanäle und
     Direktnachrichten
   - Deaktivieren Sie „Benutzern erlauben, Slash-Befehle und Nachrichten über den Nachrichten-Tab zu senden“ (falls
     sichtbar)
4. Klicken Sie auf **„Änderungen speichern“**, wenn Sie dazu aufgefordert werden

::: info Nachrichten-Tab-Konfiguration
Der Nachrichten-Tab ist in der Regel deaktiviert, wenn das Bot Framework verwendet wird, da der Bot über Kanäle,
Gruppenchats und Direktnachrichten kommuniziert und nicht über den Nachrichten-Tab der App.
:::

### Schritt 9: Bot Framework Slack-Kanal konfigurieren

1. Navigieren Sie zum [Bot Framework Portal](https://dev.botframework.com/)
2. Gehen Sie zur Kanalseite Ihres Bots:
   - URL-Format: `https://dev.botframework.com/bots/channels?id={APP_ID}&channelId=slack`
   - Ersetzen Sie `{APP_ID}` durch Ihre Teams App-ID (aus Schritt 6)
   - Beispiel: `https://dev.botframework.com/bots/channels?id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&channelId=slack`
3. Klicken Sie auf den Kanal **„Slack“** oder auf **„Konfigurieren“**, falls bereits hinzugefügt
4. Kopieren Sie die App-Anmeldeinformationen aus Ihrer Slack-App (aus Schritt 8):
   - **Client-ID** (aus Slack App-Anmeldeinformationen)
   - **Client Secret** (aus Slack App-Anmeldeinformationen)
5. Fügen Sie diese in die Bot Framework Slack-Kanal-Konfiguration ein
6. Kopieren Sie die folgenden URLs zur späteren Verwendung:
   - **Redirect-URL** (benötigt für Schritt 10)
   - **Event Subscription-URL** (benötigt für Schritt 11)
7. Klicken Sie auf **„Speichern“**
8. **WICHTIG:** Nach dem Speichern werden Sie automatisch zu Slack weitergeleitet, um die Anwendung zu installieren/neu
   zu installieren
   - Dies schließt den OAuth-Fluss ab
   - Folgen Sie den Anweisungen zur Autorisierung der App
   - Dies kann die Anforderungen für Event Subscriptions automatisch erfüllen

::: tip Automatische Konfiguration
Das Bot Framework konfiguriert viele Slack-Einstellungen oft automatisch während des OAuth-Flows. Überprüfen Sie nach
Abschluss von Schritt 9 die Schritte 10-12, um die Einstellungen zu bestätigen, anstatt alles manuell zu konfigurieren.
:::

### Schritt 10: Slack OAuth konfigurieren

1. Gehen Sie zu den OAuth-Einstellungen Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/oauth`
2. Scrollen Sie zum Abschnitt **„Scopes“**
3. Klicken Sie unter **„Bot Token Scopes“** auf **„Einen OAuth Scope hinzufügen“**
4. Fügen Sie die folgenden Scopes hinzu:
   - `chat:write` – Ermöglicht dem Bot, Nachrichten zu senden
   - `assistant:write` – Ermöglicht dem Bot, mit App-Agents/Assistenten zu interagieren
5. Klicken Sie unter **„Redirect URLs“** auf **„Neue Redirect-URL hinzufügen“**
6. Fügen Sie die **Redirect-URL** vom Bot Framework (Schritt 9) ein
7. Klicken Sie auf **„URLs speichern“**

::: info Automatische Scopes
Andere erforderliche Scopes (channels:history, groups:history, im:history, mpim:history) können automatisch hinzugefügt
werden, wenn Sie Bot-Ereignisse in Schritt 12 abonnieren oder wenn Sie den Bot Framework OAuth-Fluss abschließen.
:::

### Schritt 11: Slack Event-Subscriptions konfigurieren

1. Gehen Sie zu den Event Subscriptions Ihrer Slack-App:
   - URL-Format: `https://api.slack.com/apps/{SLACK_APP_ID}/event-subscriptions`
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/event-subscriptions`
2. Schalten Sie **„Ereignisse aktivieren“** auf EIN
3. Fügen Sie in **„Request URL“** die **Event Subscription-URL** vom Bot Framework (Schritt 9) ein
4. Warten Sie auf die URL-Verifizierung (sollte „Verifiziert ✓“ anzeigen)

::: tip Bereits konfiguriert?
Wenn Sie während Schritt 9 zu Slack weitergeleitet wurden und die Installation abgeschlossen haben, können die
Event-Subscriptions bereits automatisch vom Bot Framework konfiguriert worden sein. Überprüfen Sie diese Seite zur
Bestätigung.
:::

### Schritt 12: Bot-Ereignisse abonnieren (falls erforderlich)

::: warning Optionaler Schritt
Diese Event-Subscriptions sind möglicherweise nicht erforderlich, wenn der Bot Framework Slack-Kanal sie automatisch
handhabt. Prüfen Sie, ob die Events bereits konfiguriert sind, bevor Sie sie manuell hinzufügen.
:::

Wenn Events nicht automatisch konfiguriert sind, scrollen Sie auf der Event Subscriptions-Seite zu **„Bot-Ereignisse
abonnieren“** und fügen Sie Folgendes hinzu:

| Ereignisname                       | Beschreibung                                                               | Erforderlicher Scope |
| :--------------------------------- | :------------------------------------------------------------------------- | :------------------- |
| `message.channels`                 | Eine Nachricht wurde in einem Kanal gepostet                               | `channels:history`   |
| `message.groups`                   | Eine Nachricht wurde in einem privaten Kanal gepostet                      | `groups:history`     |
| `message.im`                       | Eine Nachricht wurde in einem Direktnachrichtenkanal gepostet              | `im:history`         |
| `message.mpim`                     | Eine Nachricht wurde in einem Mehrparteien-Direktnachrichtenkanal gepostet | `mpim:history`       |
| `assistant_thread_started`         | Ein App Agent-Thread wurde gestartet                                       | keine                |
| `assistant_thread_context_changed` | Der Kontext änderte sich, während ein App Agent-Thread sichtbar war        | keine                |

::: info Automatische Scope-Hinzufügung
Wenn Sie diese Events hinzufügen, fügt Slack automatisch die notwendigen OAuth Scopes zu Ihrer App-Konfiguration hinzu.
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
   - Ersetzen Sie `{SLACK_APP_ID}` durch Ihre Slack App-ID
   - Beispiel: `https://api.slack.com/apps/A09QARZNF45/install-on-team`
2. Klicken Sie auf **„Im Workspace installieren“** (oder **„Im Workspace neu installieren“**, falls Sie aktualisieren)
3. Überprüfen Sie die angeforderten Berechtigungen
4. Klicken Sie auf **„Zulassen“**
5. **WICHTIG:** Kopieren Sie das angezeigte **Bot User OAuth-Token**
   - Format: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`
   - Dies ist das Token, das Sie im nächsten Schritt zu MongoDB hinzufügen werden

**Alternative:** Wenn bereits installiert, rufen Sie Ihr Token ab von:

- **OAuth & Berechtigungen**-Seite: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
- Suchen Sie unter „OAuth Tokens for Your Workspace“ nach **„Bot User OAuth-Token“**

::: danger Token-Sicherheit
Das Slack Bot OAuth-Token bietet vollen Zugriff auf die Funktionen Ihres Bots. Speichern Sie es sicher und committen Sie
es niemals in die Versionskontrolle. Behandeln Sie es mit derselben Sicherheit wie Passwörter und API-Schlüssel.
:::

### Schritt 14: Slack OAuth Token zu MongoDB hinzufügen

Aktualisieren Sie das Bot-Pfad-Dokument in MongoDB, um das Slack OAuth-Token aus Schritt 13 einzufügen:

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

**Details zum Slack OAuth-Token:**

- Format: `xoxb-` gefolgt von Zahlen und Bindestrichen
- Erhalten aus Schritt 13 während der Slack App-Installation
- Ersetzen Sie den leeren String `""` durch das tatsächliche Token
- Halten Sie dieses Token sicher und committen Sie es niemals in die Versionskontrolle

**Um ein bestehendes Dokument zu aktualisieren:**

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

- **app_home**: Konfiguration für die Home- und Nachrichten-Tabs der App
  - **home_tab_enabled**: Auf `true` setzen, um den Home-Tab zu aktivieren
  - **messages_tab_enabled**: Auf `false` setzen (Interaktion erfolgt über Kanäle/DMs, nicht über den Nachrichten-Tab)
  - **messages_tab_read_only_enabled**: Auf `false` setzen
- **always_online**: Auf `true` setzen, um den Bot immer als online anzuzeigen
- **redirect_urls**: Immer `https://slack.botframework.com` für die Bot Framework-Integration
- **request_url**: Das Format ist `https://slack.botframework.com/api/Events/{APP_ID}`, wobei `{APP_ID}` Ihre Teams
  App-Client-ID ist
- **bot scopes**: Alle 6 Scopes sind für die volle Funktionalität erforderlich (einschließlich `chat:write` und
  `assistant:write`)
- **bot_events**: Alle 6 Events ermöglichen dem Bot, Nachrichten über alle Konversationstypen hinweg zu empfangen

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

- **id** und **webApplicationInfo.id**: Ihre Teams App-Client-ID (APP_ID)
- **botId**: Identisch mit Ihrer App-Client-ID
- **scopes**: Bot in persönlichen Chats, Teams und Gruppenchats aktivieren
- **supportsFiles**: Auf `true` setzen, um Datei-Uploads zu erlauben
- **Ressourcenspezifische Berechtigungen:**
  - `ChannelMessage.Read.Group` – Nachrichten in Kanälen lesen
  - `ChannelMessage.Send.Group` – Nachrichten in Kanälen senden
  - `ChatMessage.Read.Chat` – Nachrichten in Chats lesen
  - `ChatMessage.Send.Chat` – Nachrichten in Chats senden

### Manifeste zur App-Erstellung verwenden

**Slack:**

1. Gehen Sie zu [Slack API Apps](https://api.slack.com/apps)
2. Klicken Sie auf **„Neue App erstellen“** → **„Aus einem App-Manifest“**
3. Wählen Sie Ihren Workspace aus
4. Fügen Sie das Slack Manifest JSON ein
5. Überprüfen und erstellen

**Teams:**

1. Laden Sie das Manifest als `manifest.json` herunter
2. Fügen Sie Icon-Dateien (`outline.png` und `color.png`) in dasselbe Verzeichnis ein
3. Zippen Sie alle drei Dateien zusammen
4. Klicken Sie im Teams Developer Portal auf **„App importieren“**
5. Laden Sie die ZIP-Datei hoch

______________________________________________________________________

## Verifizierungs-Checkliste :white_check_mark:

Nach Abschluss aller Schritte überprüfen Sie:

**Teams-Konfiguration:**

- [ ] Teams-App ist veröffentlicht und genehmigt
- [ ] Bot Framework Messaging-Endpunkt ist auf `/api/v1/messages` eingestellt
- [ ] Bot Framework Messaging-Endpunkt-URL ist öffentlich zugänglich
- [ ] Bot antwortet auf Nachrichten in Teams
- [ ] Bot-Berechtigungen sind korrekt eingestellt (Nachricht lesen/senden in Chat/Team)

**MongoDB-Konfiguration:**

- [ ] `bot_paths`-Eintrag existiert mit allen erforderlichen Feldern
- [ ] `credentials`-Objekt enthält APP_TYPE, APP_ID, APP_PASSWORD und APP_TENANTID (für SingleTenant)
- [ ] `path`-Feld enthält internen Routing-Pfad (z.B. `/api/v1/agent/chat/completions/...`)
- [ ] `path`-Feld ist ANDERS als der Bot Framework Messaging-Endpunkt (`/api/v1/messages`)
- [ ] `system_message` ist entsprechend dem Bot-Zweck konfiguriert
- [ ] Client Secret (APP_PASSWORD) ist sicher gespeichert und nicht abgelaufen

**Slack-Konfiguration:**

- [ ] Slack-App ist mit korrektem Namen erstellt
- [ ] App Home konfiguriert: „Meinen Bot immer als online anzeigen“ auf EIN
- [ ] App Home konfiguriert: „Home-Tab“ auf EIN
- [ ] App Home konfiguriert: „Nachrichten-Tab“ ist deaktiviert (Bot interagiert über Kanäle/DMs)
- [ ] Bot-Token-Scopes `chat:write` und `assistant:write` sind in den Slack OAuth-Einstellungen hinzugefügt
- [ ] Bot Framework Slack-Kanal ist mit Client-ID und Client Secret konfiguriert
- [ ] Bot Framework-Konfiguration gespeichert und OAuth-Weiterleitung zu Slack abgeschlossen
- [ ] Redirect-URL ist zu den Slack OAuth-Einstellungen hinzugefügt
- [ ] Event Subscription-URL ist verifiziert (kann automatisch erfolgen)
- [ ] Bot-Ereignisse sind abonniert (kann automatisch über Bot Framework erfolgen)
- [ ] Slack-App ist im Workspace installiert (kann während der Weiterleitung in Schritt 9 erfolgt sein)
- [ ] `slack_token` wurde von der Slack OAuth & Berechtigungen-Seite abgerufen
- [ ] `slack_token` ist zu MongoDB hinzugefügt
- [ ] Bot antwortet auf Nachrichten in Slack-Kanälen
- [ ] Bot antwortet auf Direktnachrichten in Slack

______________________________________________________________________

## Fehlerbehebung :wrench:

### Bot antwortet nicht in Teams

- **Probleme mit dem Messaging-Endpunkt:**
  - Überprüfen Sie, ob der Bot Framework Messaging-Endpunkt im Teams Developer Portal auf `/api/v1/messages` eingestellt
    ist
  - Stellen Sie sicher, dass die Endpunkt-URL öffentlich zugänglich ist (mit curl oder Browser testen)
  - Bestätigen Sie für die lokale Entwicklung, dass Azure DevTunnel oder ngrok läuft
- **Authentifizierungsprobleme:**
  - Überprüfen Sie, ob `APP_PASSWORD` (Client Secret) korrekt ist und nicht abgelaufen ist
  - Bestätigen Sie, dass `APP_TENANTID` und `APP_ID` mit den Werten aus Schritt 6 übereinstimmen
  - Überprüfen Sie, ob `APP_TYPE` korrekt eingestellt ist (`SingleTenant` oder `MultiTenant`)
- **Konfigurationsprobleme:**
  - Überprüfen Sie die App-Berechtigungen im Teams Developer Portal (Nachricht lesen/senden in Chat/Team)
  - Überprüfen Sie, ob der MongoDB `bot_paths`-Eintrag mit den korrekten Anmeldeinformationen existiert
  - Überprüfen Sie, ob das `path`-Feld in MongoDB einen gültigen internen Routing-Pfad enthält
  - Stellen Sie sicher, dass die Konversation mit dem korrekten `path`-Wert erstellt wurde

### Probleme bei der Slack-Integration

- Überprüfen Sie, ob `slack_token` gültig ist (beginnt mit `xoxb-`)
- Überprüfen Sie, ob die Slack-App die notwendigen Bot-Token-Scopes hat:
  - `chat:write` (erforderlich zum Senden von Nachrichten)
  - `assistant:write` (erforderlich für App Agent-Interaktionen)
  - `channels:history`, `groups:history`, `im:history`, `mpim:history` (für Nachrichten-Events)
- Überprüfen Sie, ob die App Home-Einstellungen konfiguriert sind:
  - „Meinen Bot immer als online anzeigen“ sollte auf EIN stehen
  - „Home-Tab“ sollte auf EIN stehen
  - „Benutzern erlauben, Slash-Befehle und Nachrichten über den Nachrichten-Tab zu senden“ sollte aktiviert sein
- Bestätigen Sie, dass der Bot den gewünschten Slack-Kanälen hinzugefügt wurde (Bot mit @botname einladen)
- Stellen Sie sicher, dass alle 6 Bot-Events in Event Subscriptions abonniert sind
- Überprüfen Sie, ob die Event Subscription-URL „Verifiziert ✓“ anzeigt
- Überprüfen Sie, ob die Redirect-URL in den Slack OAuth-Einstellungen korrekt hinzugefügt wurde
- Stellen Sie sicher, dass das `slack_token`-Feld in MongoDB kein leerer String ist
- Überprüfen Sie die Bot Framework Slack-Kanal-Konfiguration
- Installieren Sie die Slack-App neu, wenn Scopes nach der Erstinstallation geändert wurden (erforderlich, damit
  Scope-Änderungen wirksam werden)

### MongoDB-Verbindungsprobleme

- Überprüfen Sie, ob der Sammlungsname `bot_paths` ist
- Überprüfen Sie, ob die Dokumentstruktur den obigen Beispielen entspricht
- Stellen Sie sicher, dass alle erforderlichen Felder im `credentials`-Objekt vorhanden sind
- Überprüfen Sie, ob `APP_ID` und `APP_TENANTID` im korrekten UUID-Format vorliegen
- Bestätigen Sie, dass das `path`-Feld mit `/api/` beginnt

______________________________________________________________________

## Best Practices für die Sicherheit :shield:

1. **Niemals Secrets in die Versionskontrolle committen**
2. **Client Secrets vor Ablauf rotieren**
3. **Umgebungsvariablen für sensible Daten verwenden**
4. **MongoDB-Zugriff mit geeigneter Authentifizierung einschränken**
5. **OAuth Token-Nutzung auf Anomalien überwachen**
6. **Audit-Logs von Bot-Pfad-Änderungen führen**
7. **HTTPS für alle Messaging-Endpunkte verwenden**

______________________________________________________________________

## Support :sos:

Für Probleme oder Fragen:

- **Teams Developer Portal**:
  [Microsoft Teams Dokumentation](https://learn.microsoft.com/en-us/microsoftteams/platform/)
- **Bot Framework**: [Azure Bot Service Dokumentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- **Slack API**: [Slack API Dokumentation](https://api.slack.com/)

______________________________________________________________________

## Nächste Schritte :rocket:

Nach Abschluss der manuellen Bot-Einrichtung:

1. **Testen Sie Ihren Bot**: Senden Sie eine Nachricht in Teams oder Slack, um zu überprüfen, ob der Bot korrekt
   antwortet
2. **Logs überprüfen**: Überprüfen Sie die Anwendungs-Logs auf Fehler oder Warnungen während der Bot-Interaktionen
3. **Zusätzliche Funktionen konfigurieren**: Erkunden Sie
   [Bot-in-the-Loop](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für die Zusammenarbeit zwischen Mensch und KI
4. **Benutzerdefinierte Logik implementieren**: Siehe das [Entwicklerhandbuch](../../../6_code_deep_dive/packages/bot/)
   für benutzerdefinierte Bot-Implementierungen
5. **Performance überwachen**: Richten Sie Observability und Monitoring für Produktions-Deployments ein

______________________________________________________________________

*Zuletzt aktualisiert: 14. November 2025*
