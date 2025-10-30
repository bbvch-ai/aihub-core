---
title: Azure Bot Service Integration
source_sha: 01d72a7d10ab49c0c4a59f8ba13b445243187870aa957a5ed632f70b94fe9e08
---

# Azure Bot Service Integration :speech_balloon: :100:

::: info **TL;DR – Was ist die Azure Bot Service Integration?**
Die Azure Bot Service Integration verwandelt den AI-Hub in eine **Omnichannel-Konversationsplattform**, die Benutzer
über bekannte Kollaborationstools wie Microsoft Teams und Slack mit KI-Agenten verbindet. Diese Integration bietet
Bot-Konnektivität auf Enterprise-Niveau mit Streaming-Antworten, Konversationspersistenz und nahtlosen
Human-in-the-Loop-Workflows, wodurch Benutzer nicht mehr zwischen Anwendungen wechseln müssen, um auf KI-Unterstützung
zuzugreifen.
:::

## Was ist die Azure Bot Service Integration und wie funktioniert sie? :brain:

Die Azure Bot Service Integration nutzt das **Microsoft Bot Framework**, um einheitliche Konversationserlebnisse über
mehrere Kanäle hinweg bereitzustellen und die Funktionen des AI-Hub dort zugänglich zu machen, wo Benutzer natürlich
arbeiten und kollaborieren.

Die **Architektur für Multi-Kanal-Bots** ermöglicht konsistente KI-Interaktionen über:

- **Microsoft Teams** – Native Integration in Enterprise-Kollaborationsworkflows
- **Slack** – Direkte Kanalnachrichten für Expertenkonsultation und Bot-Antworten
- **Web Chat** – Browserbasierte Oberfläche für Tests und Entwicklung
- **Erweiterbare Kanalunterstützung** – Jede vom Bot Framework unterstützte Plattform

Die **[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht eine
hochentwickelte Mensch-KI-Kollaboration, indem sie KI-Agenten befähigt, ihre Workflows zu pausieren und nahtlos
menschliche Eingaben über Slack-Kanäle anzufordern. Wenn Agenten Expertenwissen oder Genehmigungen benötigen,
veröffentlichen sie automatisch strukturierte Fragen in designierten Kanälen, erfassen Antworten und setzen die
Verarbeitung mit dem vom Menschen bereitgestellten Kontext fort.

**Intelligente Chatbot-Implementierungen** bieten mehrere Vervollständigungsstrategien:

- **Agenten-Chatbots** verbinden sich direkt mit AI-Hub Agenten über NATS Messaging für komplexe Workflows
- **OpenAI-Chatbots** bieten direkte LLM-Integration für schnellere, einfachere Interaktionen
- **Streaming-Unterstützung** liefert Echtzeit-Antwortaktualisierungen mit Tippindikatoren über alle Kanäle hinweg

Die **Enterprise-Grade Infrastruktur** umfasst die automatisierte Azure AD App-Registrierung, sicheres
Credential-Management, Konversationspersistenz mit konfigurierbarer TTL und umfassende Audit-Trails für
Compliance-Anforderungen.

**Schlüsseltechnologien:**

- **Azure Bot Framework** – Multi-Kanal-Konnektivität und Nachrichten-Routing
- **Azure AD Integration** – Enterprise-Authentifizierung und -Autorisierung
- **NATS Messaging** – Agenten-Orchestrierung und ereignisgesteuerte Workflows
- **MongoDB/Cosmos DB** – Konversationspersistenz und Konfigurationsspeicherung
- **Infrastructure as Code** – Pulumi-basierte Azure Ressourcen-Bereitstellung

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Die Azure Bot Service Integration eliminiert die Reibung zwischen KI-Funktionen und Benutzerakzeptanz, indem sie
Benutzer dort abholt, wo sie bereits arbeiten:

**🔄 Kein Kontextwechsel**: Benutzer greifen direkt in Microsoft Teams, Slack und anderen vertrauten
Kollaborationsplattformen auf KI-Unterstützung zu. Es ist nicht nötig, neue Oberflächen zu erlernen oder etablierte
Workflows zu unterbrechen – KI wird zu einem natürlichen Bestandteil der täglichen Zusammenarbeit.

**🌐 Multi-Kanal-Unterstützung im Enterprise-Maßstab**: Eine einzige AI-Hub-Bereitstellung bedient Benutzer gleichzeitig
über mehrere Kommunikationsplattformen. Unabhängig davon, ob Teams Teams, Slack oder andere Bot Framework-unterstützte
Kanäle nutzen, erhält jeder konsistente KI-Unterstützung, die auf seine bevorzugte Kollaborationsumgebung zugeschnitten
ist.

**⚡ Echtzeit-Streaming-Antworten**: Die fortschrittliche Streaming-Implementierung bietet sofortiges Feedback mit
Tippindikatoren, teilweisen Antworten und inkrementellen Updates. Benutzer sehen, wie die KI in Echtzeit denkt und
antwortet, was natürliche Konversationsabläufe schafft, die reaktionsschnell und ansprechend wirken.

**🛡️ Enterprise-Sicherheit und Compliance**: Basiert auf Azure AD-Authentifizierung mit umfassenden
Konversations-Audit-Trails, konfigurierbaren Aufbewahrungsrichtlinien und sicherem Credential-Management. Alle
Bot-Interaktionen werden protokolliert und sind nachvollziehbar, wodurch die Sicherheits- und Compliance-Anforderungen
des Unternehmens erfüllt werden.

**🤝 Nahtlose Mensch-KI-Kollaboration**: Die
[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/) ermöglicht es KI-Agenten, auf
natürliche Weise über strukturierte Slack-Workflows an menschliche Experten zu eskalieren. Komplexe Entscheidungen,
Genehmigungen und Wissenslücken werden reibungslos behandelt, ohne die Benutzererfahrung zu unterbrechen oder den
Konversationskontext zu verlieren.

::: details **Einrichtung und Nutzung der Azure Bot Service Integration**
## Konfigurationsanforderungen

### Einrichtung der Azure Infrastruktur

1. **Erstellung der Azure Bot Ressource**: Verwenden Sie das automatisierte Setup-Skript

   ```bash
   python aihub_bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-ai-hub-bot" \
     --token-url "https://your-aihub-domain.com" \
     --token-path "/api/v1/messages" \
     --mongo-connection-string "mongodb://localhost:27017"
   ```

2. **Azure AD App-Registrierung**: Automatisch durch das Setup-Skript gehandhabt

   - Erstellt eine Azure AD-Anwendung mit Bot Framework-Berechtigungen
   - Generiert sichere App-Zugangsdaten (App ID und Passwort)
   - Konfiguriert Single-Tenant- oder Multi-Tenant-Authentifizierung

3. **Kanal-Konfiguration**: Manuell im Azure Portal nach dem Setup konfigurieren

   - **Microsoft Teams**: Teams-Kanal im Azure Bot Service hinzufügen
   - **Slack**: Slack-App erstellen und mit dem Azure Bot Service verknüpfen
   - **Web Chat**: Automatisch für Tests konfiguriert

### Lokales Entwicklungs-Setup

1. **Entwicklungstunnel**: Lokalen AI-Hub für Azure Bot Service freilegen

   ```bash
   # Install and configure Azure DevTunnel
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   # Use tunnel URL in bot configuration
   ```

2. **Datenbankkonfiguration**: Zugangsdaten in MongoDB gespeichert

   ```json
   {
     "path": "/api/v1/messages",
     "credentials": {
       "APP_TYPE": "MultiTenant",
       "APP_ID": "your-app-id",
       "APP_PASSWORD": "your-app-password"
     },
     "system_message": "Custom bot instructions",
     "slack_token": "slack-oauth-token"
   }
   ```

## Anwendungsbeispiele

### Microsoft Teams Integration

**Grundlegende Chat-Interaktion:**

1. **Bot zu Teams hinzufügen**: AI-Hub Bot in Ihrem Teams-Workspace installieren
2. **Konversation starten**: Senden Sie dem Bot direkt eine Nachricht oder erwähnen Sie ihn in Kanälen
3. **Streaming-Antworten**: Sehen Sie Echtzeit-Tippindikatoren und inkrementelle Antworten
4. **Konversationspersistenz**: Kontext wird über mehrere Interaktionen hinweg beibehalten

**Erweiterte Funktionen:**

- **Rich Responses**: Unterstützung für Karten, Schaltflächen und interaktive Elemente
- **Dateiuploads**: Dokumente und Bilder direkt in Teams verarbeiten
- **Thread-Unterstützung**: Konversationskontext in Thread-Diskussionen beibehalten

### Slack Bot-in-the-Loop Workflows

Für detaillierte Informationen zu Bot-in-the-Loop Workflows, einschließlich Expertenkonsultationsprozessen,
Kanal-Konfiguration und Agenten-Integrationsmustern, siehe die dedizierte
[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot Bereitstellung

**Agenten-basierte Bots**: Verbindung zu spezifischen AI-Hub Agenten

```python
# Configure bot to use specific agent
AgentChatBot(
    agent_class="ExpertGroundedAgent",
    agent_id="expert_agent_v1",
    streaming=True
)
```

**OpenAI-basierte Bots**: Direkte LLM-Integration für einfachere Anwendungsfälle

```python
# Configure bot with direct OpenAI access
OpenaiChatBot(
    llm_config=OpenAIConfig(...),
    system_message="You are a helpful assistant",
    streaming=True
)
```

## Verfügbare Funktionen

**Bot Framework Integration:**

- **Multi-Kanal-Bereitstellung**: Eine einzige Codebasis bedient Teams, Slack, Web Chat und andere Kanäle
- **Aktivitätsverarbeitung**: Verarbeitet Nachrichten, Tippereignisse, Konversationsaktualisierungen und Dateiuploads
- **Unterstützung für Rich Messages**: Karten, Schaltflächen, Anhänge und interaktive Elemente
- **Konversationsmanagement**: Persistenter Zustand mit konfigurierbarer TTL (Standard 30 Tage)

**[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

- **Slack-Kanalintegration**: Direktes Posten in Expertenkanälen mit Thread-Unterstützung
- **Antwortenerfassung**: Automatische Erkennung und Verarbeitung menschlicher Antworten
- **Konversations-Threading**: Kontext über mehrstufige Expertenkonsultationen hinweg beibehalten
- **Wissenspersistenz**: Expertenantworten werden für organisationales Lernen gespeichert

**Chatbot-Implementierungen:**

- **Streaming-Antworten**: Echtzeit-Nachrichtenaktualisierungen mit Tippindikatoren
- **Agenten-Integration**: Direkte Verbindung zu AI-Hub Agenten-Workflows über NATS
- **OpenAI-Integration**: Standalone LLM-Interaktionen für einfache Anwendungsfälle
- **Fehlerbehandlung**: Anmutiger Abbau mit benutzerfreundlichen Fehlermeldungen

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Azure AD-Authentifizierung**: Enterprise-Grade-Authentifizierung mit rollenbasiertem Zugriff
- **Sichere Speicherung von Zugangsdaten**: Bot-Zugangsdaten verschlüsselt und in MongoDB/Cosmos DB gespeichert
- **Audit-Trails**: Kompletter Konversationsverlauf mit Benutzerzuordnung und Zeitstempeln
- **Netzwerksicherheit**: Unterstützung für private Endpunkte und VNet-Integration

**Best Practices:**

- **Kanalorganisation**: Spezifische Slack-Kanäle für verschiedene Expertendomänen dedizieren
- **Konversations-TTL**: Geeignete Aufbewahrungsrichtlinien für Compliance-Anforderungen konfigurieren
- **Bot-Benennung**: Klare, beschreibende Namen für mehrere Bot-Bereitstellungen verwenden
- **Monitoring**: Umfassendes Logging und Alerting für die Bot-Gesundheit implementieren
- **Kapazitätsplanung**: Konversationsvolumen und Antwortzeiten überwachen

**Performance-Optimierung:**

- **Streaming-Konfiguration**: Aktualisierungsfrequenz für optimale Benutzererfahrung anpassen
- **Konversationsbereinigung**: Automatische Bereinigung abgelaufener Konversationen implementieren
- **Datenbankindizierung**: MongoDB-Abfragen für den Konversationsabruf optimieren
- **Caching-Strategie**: Häufig aufgerufene Konfigurationen und Zugangsdaten cachen
:::

## Erste Schritte

Um die Azure Bot Service Integration in Ihrer AI-Hub-Bereitstellung zu implementieren:

1. **Azure Setup-Skript ausführen**: Verwenden Sie die bereitgestellte Automatisierung, um Azure Bot-Ressourcen zu
   erstellen und die Authentifizierung mit Ihrem bevorzugten Datenbank-Backend zu konfigurieren
2. **Kanäle konfigurieren**: Richten Sie Microsoft Teams- und/oder Slack-Integrationen über die Azure Portal
   Kanal-Konfiguration ein
3. **Bot-Implementierungen bereitstellen**: Wählen Sie zwischen agenten-basierten Bots für komplexe Workflows oder
   OpenAI-basierten Bots für einfachere Interaktionen, mit Streaming-Unterstützung für eine verbesserte
   Benutzererfahrung

Für detaillierte Setup-Anweisungen, Fehlerbehebungsleitfäden und erweiterte Konfigurationsoptionen verweisen wir auf die
[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für
Mensch-KI-Kollaborations-Workflows, die [Expert Agents Dokumentation](../../5_agents/3_expert_asking_agent/) für Muster
der Wissenskonsultation und den AI-Hub Bot Developer's Guide für Implementierungsdetails.
