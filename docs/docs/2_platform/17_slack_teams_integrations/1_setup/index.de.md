---
title: Azure Bot Service-Integration
source_sha: cb50b2ca16e162c5a1e986c5f8587464ea8ceb1b21bd714f6f47933bb6b1b2e3
---

# Azure Bot Service-Integration :speech_balloon: :100:

::: info **TL;DR - Was ist die Azure Bot Service-Integration?**
Die Azure Bot Service-Integration verwandelt den Swiss AI Hub in eine **Omnichannel-Konversationsplattform**, die
Benutzer über vertraute Kollaborationstools wie Microsoft Teams und Slack mit KI-Agents verbindet. Diese Integration
bietet Bot-Konnektivität auf Unternehmensebene mit Streaming-Antworten, Konversationspersistenz und nahtlosen
Human-in-the-Loop-Workflows, wodurch Benutzer nicht mehr zwischen Anwendungen wechseln müssen, um auf KI-Unterstützung
zuzugreifen.
:::

## Was ist die Azure Bot Service-Integration und wie funktioniert sie? :brain:

Die Azure Bot Service-Integration nutzt das **Microsoft Bot Framework**, um einheitliche Konversationserlebnisse über
mehrere Kanäle hinweg zu ermöglichen und die Funktionen des Swiss AI Hub dort zugänglich zu machen, wo Benutzer
natürlich arbeiten und zusammenarbeiten.

Die **Omnichannel-Bot-Architektur** ermöglicht konsistente KI-Interaktionen über folgende Kanäle hinweg:

- **Microsoft Teams** - Native Integration mit Unternehmens-Kollaborations-Workflows
- **Slack** - Direkte Kanalnachrichten für Expertenkonsultationen und Bot-Antworten
- **Web-Chat** - Browserbasierte Oberfläche für Tests und Entwicklung
- **Erweiterbarer Kanal-Support** - Jede vom Bot Framework unterstützte Plattform

Die **[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht eine
ausgeklügelte Mensch-KI-Kollaboration, indem sie KI-Agents befähigt, ihre Workflows zu pausieren und nahtlos menschliche
Eingaben über Slack-Kanäle anzufordern. Wenn Agents Fachwissen oder Genehmigungen benötigen, posten sie automatisch
strukturierte Fragen in bestimmte Kanäle, erfassen Antworten und setzen die Verarbeitung mit dem vom Menschen
bereitgestellten Kontext fort.

**Intelligente Chat Bot-Implementierungen** bieten mehrere Vervollständigungsstrategien:

- **Agent Chat Bots** verbinden sich direkt mit Swiss AI Hub-Agents über NATS-Messaging für komplexe Workflows
- **OpenAI Chat Bots** bieten direkte LLM-Integration für schnellere, einfachere Interaktionen
- **Streaming-Support** liefert Echtzeit-Antwortupdates mit Tippindikatoren über alle Kanäle hinweg

Die **Enterprise-Grade-Infrastruktur** umfasst die automatisierte Azure AD App-Registrierung, sichere
Anmeldeinformationsverwaltung, Konversationspersistenz mit konfigurierbarer TTL und umfassende Audit-Trails für
Compliance-Anforderungen.

**Schlüsseltechnologien:**

- **Azure Bot Framework** - Omnichannel-Konnektivität und Nachrichten-Routing
- **Azure AD-Integration** - Authentifizierung und Autorisierung auf Unternehmensebene
- **NATS Messaging** - Agent-Orchestrierung und ereignisgesteuerte Workflows
- **MongoDB/Cosmos DB** - Konversationspersistenz und Konfigurationsspeicherung
- **Infrastructure as Code** - Pulumi-basiertes Azure-Ressourcen-Deployment

## Warum dies ein Game-Changer für Ihre KI-Strategie ist :trophy:

Die Azure Bot Service-Integration beseitigt die Reibung zwischen KI-Funktionen und Benutzerakzeptanz, indem sie Benutzer
dort abholt, wo sie bereits arbeiten:

**🔄 Kein Kontextwechsel**: Benutzer greifen direkt in Microsoft Teams, Slack und anderen vertrauten
Kollaborationsplattformen auf KI-Unterstützung zu. Es ist nicht nötig, neue Oberflächen zu lernen oder etablierte
Workflows zu unterbrechen – KI wird zu einem natürlichen Bestandteil der täglichen Zusammenarbeit.

**🌐 Omnichannel-Support auf Unternehmensebene**: Ein einziges Swiss AI Hub-Deployment bedient Benutzer gleichzeitig über
mehrere Kommunikationsplattformen hinweg. Ob Teams Teams, Slack oder andere vom Bot Framework unterstützte Kanäle
nutzen, jeder erhält konsistente KI-Unterstützung, die auf seine bevorzugte Kollaborationsumgebung zugeschnitten ist.

**⚡ Echtzeit-Streaming-Antworten**: Die fortschrittliche Streaming-Implementierung bietet sofortiges Feedback mit
Tippindikatoren, Teilantworten und inkrementellen Updates. Benutzer sehen, wie die KI in Echtzeit denkt und antwortet,
was natürliche Konversationsabläufe schafft, die reaktionsschnell und ansprechend wirken.

**🛡️ Unternehmenssicherheit und Compliance**: Aufgebaut auf Azure AD-Authentifizierung mit umfassenden
Konversations-Audit-Trails, konfigurierbaren Aufbewahrungsrichtlinien und sicherer Anmeldeinformationsverwaltung. Alle
Bot-Interaktionen werden protokolliert und sind nachvollziehbar, wodurch die Sicherheits- und Compliance-Anforderungen
von Unternehmen erfüllt werden.

**🤝 Nahtlose Mensch-KI-Kollaboration**: Die
[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/) ermöglicht es KI-Agents, über
strukturierte Slack-Workflows natürlich an menschliche Experten zu eskalieren. Komplexe Entscheidungen, Genehmigungen
und Wissenslücken werden reibungslos gehandhabt, ohne die Benutzererfahrung zu beeinträchtigen oder den
Konversationskontext zu verlieren.

::: details **Einrichten und Verwenden der Azure Bot Service-Integration**
## Konfigurationsanforderungen

### Azure Infrastruktur-Einrichtung

1. **Erstellung der Azure Bot-Ressource**: Verwenden Sie das automatisierte Setup-Skript

   ```bash
   python packages/bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-swiss-ai-hub-bot" \
     --token-url "https://your-swiss-ai-hub-domain.com" \
     --token-path "/api/v1/messages" \
     --mongo-connection-string "mongodb://localhost:27017"
   ```

2. **Azure AD App-Registrierung**: Automatisch durch das Setup-Skript gehandhabt

   - Erstellt eine Azure AD-Anwendung mit Bot Framework-Berechtigungen
   - Generiert sichere App-Anmeldeinformationen (App ID und Passwort)
   - Konfiguriert Single-Tenant- oder Multi-Tenant-Authentifizierung

3. **Kanal-Konfiguration**: Manuell im Azure-Portal nach der Einrichtung konfigurieren

   - **Microsoft Teams**: Teams-Kanal im Azure Bot Service hinzufügen
   - **Slack**: Slack-App erstellen und mit dem Azure Bot Service verknüpfen
   - **Web-Chat**: Automatisch für Tests konfiguriert

### Lokale Entwicklungsumgebung einrichten

1. **Entwicklungstunnel**: Lokalen Swiss AI Hub für Azure Bot Service freigeben

   ```bash
   # Install and configure Azure DevTunnel
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   # Use tunnel URL in bot configuration
   ```

2. **Datenbankkonfiguration**: Anmeldeinformationen in MongoDB gespeichert

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

### Microsoft Teams-Integration

**Grundlegende Chat-Interaktion:**

1. **Bot zu Teams hinzufügen**: Installieren Sie den Swiss AI Hub Bot in Ihrem Teams-Workspace
2. **Konversation starten**: Senden Sie dem Bot direkt eine Nachricht oder erwähnen Sie ihn in Kanälen
3. **Streaming-Antworten**: Sehen Sie Echtzeit-Tippindikatoren und inkrementelle Antworten
4. **Konversationspersistenz**: Kontext wird über mehrere Interaktionen hinweg beibehalten

**Erweiterte Funktionen:**

- **Umfassende Antworten**: Unterstützung für Karten, Schaltflächen und interaktive Elemente
- **Dateiuploads**: Verarbeiten Sie Dokumente und Bilder direkt in Teams
- **Thread-Support**: Konversationskontext in Thread-Diskussionen beibehalten

### Slack Bot-in-the-Loop Workflows

Für detaillierte Informationen zu Bot-in-the-Loop-Workflows, einschliesslich Expertenkonsultationsprozessen,
Kanalkonfiguration und Agent-Integrationsmustern, siehe die dedizierte
[Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot-Deployment

**Agenten-basierte Bots**: Verbindung zu spezifischen Swiss AI Hub Agents

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

**Bot Framework-Integration:**

- **Omnichannel-Deployment**: Eine einzige Codebasis bedient Teams, Slack, Web-Chat und andere Kanäle
- **Aktivitätsverarbeitung**: Bearbeitung von Nachrichten, Tippereignissen, Konversationsupdates und Dateiuploads
- **Umfassende Nachrichtenunterstützung**: Karten, Schaltflächen, Anhänge und interaktive Elemente
- **Konversationsmanagement**: Persistenter Zustand mit konfigurierbarer TTL (Standard 30 Tage)

**[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

- **Slack-Kanalintegration**: Direktes Posten in Expertenkanäle mit Thread-Unterstützung
- **Antwort-Erfassung**: Automatische Erkennung und Verarbeitung menschlicher Antworten
- **Konversations-Threading**: Kontext über mehrstufige Expertenkonsultationen hinweg beibehalten
- **Wissenspersistenz**: Expertenantworten werden für organisationales Lernen gespeichert

**Chat Bot-Implementierungen:**

- **Streaming-Antworten**: Echtzeit-Nachrichtenupdates mit Tippindikatoren
- **Agent-Integration**: Direkte Verbindung zu Swiss AI Hub Agent-Workflows über NATS
- **OpenAI-Integration**: Standalone LLM-Interaktionen für einfache Anwendungsfälle
- **Fehlerbehandlung**: Sanfte Fehlerbehandlung mit benutzerfreundlichen Fehlermeldungen

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Azure AD-Authentifizierung**: Authentifizierung auf Unternehmensebene mit rollenbasiertem Zugriff
- **Sichere Speicherung von Anmeldeinformationen**: Bot-Anmeldeinformationen verschlüsselt und in MongoDB/Cosmos DB
  gespeichert
- **Audit-Trails**: Vollständige Konversationshistorie mit Benutzerzuordnung und Zeitstempeln
- **Netzwerksicherheit**: Unterstützung für private Endpunkte und VNet-Integration

**Best Practices:**

- **Kanalorganisation**: Widmen Sie spezifische Slack-Kanäle für verschiedene Expertenbereiche
- **Konversations-TTL**: Konfigurieren Sie geeignete Aufbewahrungsrichtlinien für Compliance-Anforderungen
- **Bot-Benennung**: Verwenden Sie klare, beschreibende Namen für mehrere Bot-Deployments
- **Monitoring**: Implementieren Sie umfassende Protokollierung und Warnmeldungen für die Bot-Integrität
- **Kapazitätsplanung**: Überwachen Sie das Konversationsvolumen und die Antwortzeiten

**Performance-Optimierung:**

- **Streaming-Konfiguration**: Passen Sie die Update-Frequenz für ein optimales Benutzererlebnis an
- **Konversationsbereinigung**: Implementieren Sie eine automatisierte Bereinigung abgelaufener Konversationen
- **Datenbankindizierung**: Optimieren Sie MongoDB-Abfragen für den Abruf von Konversationen
- **Caching-Strategie**: Häufig aufgerufene Konfigurationen und Anmeldeinformationen zwischenspeichern
:::

## Erste Schritte

Um die Azure Bot Service-Integration in Ihrem Swiss AI Hub-Deployment zu implementieren:

1. **Azure Setup-Skript ausführen**: Verwenden Sie die bereitgestellte Automatisierung, um Azure Bot-Ressourcen zu
   erstellen und die Authentifizierung mit Ihrem bevorzugten Datenbank-Backend zu konfigurieren
2. **Kanäle konfigurieren**: Richten Sie Microsoft Teams- und/oder Slack-Integrationen über die
   Azure-Portal-Kanal-Konfiguration ein
3. **Bot-Implementierungen deployen**: Wählen Sie zwischen Agenten-basierten Bots für komplexe Workflows oder
   OpenAI-basierten Bots für einfachere Interaktionen, mit Streaming-Support für eine verbesserte Benutzererfahrung

Für detaillierte Einrichtungsanweisungen, Fehlerbehebungsleitfäden und erweiterte Konfigurationsoptionen konsultieren
Sie die [Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für
Mensch-KI-Kollaborations-Workflows, die [Expert Agents-Dokumentation](../../../5_agents/9_expert_coordinator_agent/) für
Wissenskonsultationsmuster und den Swiss AI Hub Bot Developer's Guide für Implementierungsdetails.
