---
title: Azure Bot Service-Integration
source_sha: 8c03583a489361246fdf3d3feac70258a41ab3bd0c97f65e58777786f2f88ecc
---

# Azure Bot Service-Integration :speech_balloon: :100:

::: info **Kurz gesagt – Was ist die Azure Bot Service-Integration?**
Die Azure Bot Service-Integration verwandelt den Swiss AI Hub in eine **mehrkanalige Konversationsplattform**, die
Benutzer über bekannte Kollaborationstools wie Microsoft Teams und Slack mit KI-Agents verbindet. Diese Integration
bietet Bot-Konnektivität auf Unternehmensniveau mit Streaming-Antworten, Konversationspersistenz und nahtlosen
Human-in-the-Loop-Workflows, wodurch die Notwendigkeit entfällt, zwischen Anwendungen zu wechseln, um auf
KI-Unterstützung zuzugreifen.
:::

## Was ist die Azure Bot Service-Integration und wie funktioniert sie? :brain:

Die Azure Bot Service-Integration nutzt das **Microsoft Bot Framework**, um einheitliche Konversationserlebnisse über
mehrere Kanäle hinweg bereitzustellen, wodurch die Funktionen des Swiss AI Hub überall dort zugänglich werden, wo
Benutzer auf natürliche Weise arbeiten und zusammenarbeiten.

Die **Multi-Kanal-Bot-Architektur** ermöglicht konsistente KI-Interaktionen über folgende Kanäle hinweg:

- **Microsoft Teams** – Native Integration in Kollaborations-Workflows auf Unternehmensebene
- **Slack** – Direkte Kanalnachrichten für Expertenberatung und Bot-Antworten
- **Web Chat** – Browserbasierte Oberfläche für Tests und Entwicklung
- **Erweiterbarer Kanal-Support** – Jede vom Bot Framework unterstützte Plattform

Die **[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht anspruchsvolle
Mensch-KI-Kollaboration, indem sie KI-Agents befähigt, ihre Workflows zu pausieren und nahtlos menschliche Eingaben über
Slack-Kanäle anzufordern. Wenn Agents Expertenwissen oder Genehmigungen benötigen, posten sie automatisch strukturierte
Fragen in designierte Kanäle, erfassen die Antworten und setzen die Verarbeitung mit dem vom Menschen bereitgestellten
Kontext fort.

**Intelligente Chatbot-Implementierungen** bieten mehrere Abschlussstrategien:

- **Agent Chatbots** verbinden sich direkt mit Swiss AI Hub-Agents über NATS Messaging für komplexe Workflows
- **OpenAI Chatbots** bieten direkte LLM-Integration für schnellere, einfachere Interaktionen
- **Streaming-Support** liefert Echtzeit-Antwort-Updates mit Tippindikatoren über alle Kanäle hinweg

Die **Infrastruktur auf Unternehmensniveau** umfasst die automatisierte Azure AD App-Registrierung, sichere
Anmeldeinformationsverwaltung, Konversationspersistenz mit konfigurierbarer TTL und umfassende Audit-Trails für
Compliance-Anforderungen.

**Schlüsseltechnologien:**

- **Azure Bot Framework** – Mehrkanal-Konnektivität und Nachrichten-Routing
- **Azure AD Integration** – Authentifizierung und Autorisierung auf Unternehmensebene
- **NATS Messaging** – Agenten-Orchestrierung und ereignisgesteuerte Workflows
- **MongoDB/Cosmos DB** – Konversationspersistenz und Konfigurationsspeicherung
- **Infrastructure as Code** – Pulumi-basiertes Azure-Ressourcen-Deployment

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Die Azure Bot Service-Integration beseitigt die Reibung zwischen KI-Funktionen und Benutzerakzeptanz, indem sie Nutzer
dort erreicht, wo sie bereits arbeiten:

**🔄 Kein Kontextwechsel**: Benutzer greifen direkt in Microsoft Teams, Slack und anderen bekannten
Kollaborationsplattformen auf KI-Unterstützung zu. Es ist nicht nötig, neue Oberflächen zu lernen oder etablierte
Workflows zu unterbrechen – KI wird zu einem natürlichen Bestandteil der täglichen Zusammenarbeit.

**🌐 Mehrkanal-Support auf Unternehmensebene**: Ein einziges Swiss AI Hub-Deployment bedient Benutzer über mehrere
Kommunikationsplattformen hinweg gleichzeitig. Ob Teams Teams, Slack oder andere vom Bot Framework unterstützte Kanäle
nutzen, jeder erhält konsistente KI-Unterstützung, die auf seine bevorzugte Kollaborationsumgebung zugeschnitten ist.

**⚡ Echtzeit-Streaming-Antworten**: Eine fortschrittliche Streaming-Implementierung bietet sofortiges Feedback mit
Tippindikatoren, Teilantworten und inkrementellen Updates. Benutzer sehen, wie die KI in Echtzeit denkt und antwortet,
wodurch natürliche Konversationsabläufe entstehen, die sich reaktionsschnell und ansprechend anfühlen.

**🛡️ Sicherheit und Compliance auf Unternehmensebene**: Aufbauend auf Azure AD-Authentifizierung mit umfassenden
Konversations-Audit-Trails, konfigurierbaren Aufbewahrungsrichtlinien und sicherer Anmeldeinformationsverwaltung. Alle
Bot-Interaktionen werden protokolliert und sind nachvollziehbar, wodurch die Sicherheits- und Compliance-Anforderungen
von Unternehmen erfüllt werden.

**🤝 Nahtlose Mensch-KI-Kollaboration**: Die
[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/) ermöglicht es KI-Agents, auf
natürliche Weise an menschliche Experten über strukturierte Slack-Workflows zu eskalieren. Komplexe Entscheidungen,
Genehmigungen und Wissenslücken werden reibungslos gehandhabt, ohne die Benutzererfahrung zu unterbrechen oder den
Konversationskontext zu verlieren.

::: details **Einrichtung und Nutzung der Azure Bot Service-Integration**
## Konfigurationsanforderungen

### Azure-Infrastruktur-Setup

1. **Erstellung von Azure Bot-Ressourcen**: Verwenden Sie das automatisierte Setup-Skript

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

3. **Kanal-Konfiguration**: Nach der Einrichtung manuell im Azure-Portal konfigurieren

   - **Microsoft Teams**: Teams-Kanal im Azure Bot Service hinzufügen
   - **Slack**: Slack-App erstellen und mit Azure Bot Service verknüpfen
   - **Web Chat**: Automatisch für Tests konfiguriert

### Lokales Entwicklungs-Setup

1. **Entwicklungstunnel**: Lokalen Swiss AI Hub für Azure Bot Service freigeben

   ```bash
   # Install and configure Azure DevTunnel
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   # Use tunnel URL in bot configuration
   ```

2. **Datenbank-Konfiguration**: Anmeldeinformationen in MongoDB gespeichert

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

1. **Bot zu Teams hinzufügen**: Swiss AI Hub-Bot in Ihrem Teams-Workspace installieren
2. **Konversation starten**: Dem Bot direkt eine Nachricht senden oder ihn in Kanälen erwähnen
3. **Streaming-Antworten**: Echtzeit-Tippindikatoren und inkrementelle Antworten sehen
4. **Konversationspersistenz**: Kontext wird über mehrere Interaktionen hinweg beibehalten

**Erweiterte Funktionen:**

- **Umfassende Antworten**: Unterstützung für Karten, Schaltflächen und interaktive Elemente
- **Datei-Uploads**: Dokumente und Bilder direkt in Teams verarbeiten
- **Thread-Unterstützung**: Konversationskontext in Thread-Diskussionen beibehalten

### Slack Bot-in-the-Loop-Workflows

Für detaillierte Informationen zu Bot-in-the-Loop-Workflows, einschliesslich Expertenkonsultationsprozessen,
Kanal-Konfiguration und Agent-Integrationsmustern, siehe die dedizierte
[Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot-Deployment

**Agenten-basierte Bots**: Verbindung zu spezifischen Swiss AI Hub-Agents

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

- **Mehrkanal-Deployment**: Eine einzige Codebasis bedient Teams, Slack, Web Chat und andere Kanäle
- **Aktivitätsverarbeitung**: Nachrichten, Tipp-Ereignisse, Konversations-Updates und Datei-Uploads verarbeiten
- **Umfassender Nachrichten-Support**: Karten, Schaltflächen, Anhänge und interaktive Elemente
- **Konversationsmanagement**: Persistenter Zustand mit konfigurierbarer TTL (Standard 30 Tage)

**[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

- **Slack-Kanal-Integration**: Direktes Posten in Expertenkanäle mit Thread-Unterstützung
- **Antwort-Erfassung**: Automatische Erkennung und Verarbeitung menschlicher Antworten
- **Konversations-Threading**: Kontext über mehrstufige Expertenkonsultationen hinweg beibehalten
- **Wissenspersistenz**: Expertenantworten für organisationales Lernen gespeichert

**Chatbot-Implementierungen:**

- **Streaming-Antworten**: Echtzeit-Nachrichten-Updates mit Tippindikatoren
- **Agenten-Integration**: Direkte Verbindung zu Swiss AI Hub-Agenten-Workflows über NATS
- **OpenAI-Integration**: Standalone LLM-Interaktionen für einfache Anwendungsfälle
- **Fehlerbehandlung**: Anmutige Degradierung mit benutzerfreundlichen Fehlermeldungen

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Azure AD-Authentifizierung**: Authentifizierung auf Unternehmensniveau mit rollenbasierter Zugriffskontrolle
- **Sichere Speicherung von Anmeldeinformationen**: Bot-Anmeldeinformationen verschlüsselt in MongoDB/Cosmos DB
  gespeichert
- **Audit-Trails**: Vollständige Konversationshistorie mit Benutzerzuordnung und Zeitstempeln
- **Netzwerksicherheit**: Unterstützung für private Endpunkte und VNet-Integration

**Best Practices:**

- **Kanal-Organisation**: Dedizierte Slack-Kanäle für verschiedene Expertendomänen zuweisen
- **Konversations-TTL**: Angemessene Aufbewahrungsrichtlinien für Compliance-Anforderungen konfigurieren
- **Bot-Benennung**: Klare, beschreibende Namen für mehrere Bot-Deployments verwenden
- **Monitoring**: Umfassende Protokollierung und Alarmierung für die Bot-Integrität implementieren
- **Kapazitätsplanung**: Konversationsvolumen und Antwortzeiten überwachen

**Leistungsoptimierung:**

- **Streaming-Konfiguration**: Update-Frequenz für optimale Benutzererfahrung anpassen
- **Konversationsbereinigung**: Automatisierte Bereinigung abgelaufener Konversationen implementieren
- **Datenbank-Indizierung**: MongoDB-Abfragen für die Konversationsabfrage optimieren
- **Caching-Strategie**: Häufig aufgerufene Konfiguration und Anmeldeinformationen cachen
:::

## Erste Schritte

Um die Azure Bot Service-Integration in Ihrem Swiss AI Hub-Deployment zu implementieren:

1. **Azure Setup-Skript ausführen**: Nutzen Sie die bereitgestellte Automatisierung, um Azure Bot-Ressourcen zu
   erstellen und die Authentifizierung mit Ihrem bevorzugten Datenbank-Backend zu konfigurieren
2. **Kanäle konfigurieren**: Richten Sie Microsoft Teams- und/oder Slack-Integrationen über die Kanal-Konfiguration im
   Azure-Portal ein
3. **Bot-Implementierungen deployen**: Wählen Sie zwischen agenten-basierten Bots für komplexe Workflows oder
   OpenAI-basierten Bots für einfachere Interaktionen, mit Streaming-Support für eine verbesserte Benutzererfahrung

Für detaillierte Einrichtungsanweisungen, Fehlerbehebung und erweiterte Konfigurationsoptionen verweisen wir auf die
[Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für
Mensch-KI-Kollaborations-Workflows, die [Expert Agents-Dokumentation](../../5_agents/9_expert_coordinator_agent/) für
Wissenskonsultationsmuster und den Swiss AI Hub Bot Developer's Guide für Implementierungsdetails.
