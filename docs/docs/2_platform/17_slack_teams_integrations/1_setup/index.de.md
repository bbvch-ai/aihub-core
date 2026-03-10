---
title: Integration des Azure Bot Service
source_sha: b9d1911becf64d1171045b4136cb9a08947a7c2fb7d6bf1b7af38c05e268cf92
---

# Integration des Azure Bot Service :speech_balloon: :100:

::: info **TL;DR - Was ist die Azure Bot Service Integration?**
Die Azure Bot Service Integration verwandelt den Swiss AI Hub in eine **Multichannel-Konversationsplattform**, die
Benutzer über vertraute Kollaborationstools wie Microsoft Teams und Slack mit KI-Agenten verbindet. Diese Integration
bietet Bot-Konnektivität auf Unternehmensniveau mit Streaming-Antworten, Konversationspersistenz und nahtlosen
Human-in-the-Loop-Workflows, wodurch Benutzer nicht mehr zwischen Anwendungen wechseln müssen, um auf KI-Unterstützung
zuzugreifen.
:::

## Was ist die Azure Bot Service Integration und wie funktioniert sie? :brain:

Die Azure Bot Service Integration nutzt das **Microsoft Bot Framework**, um vereinheitlichte Konversationserlebnisse
über mehrere Kanäle hinweg zu bieten und die Funktionen des Swiss AI Hubs überall dort zugänglich zu machen, wo Benutzer
natürlich arbeiten und zusammenarbeiten.

Die **Multichannel-Bot-Architektur** ermöglicht konsistente KI-Interaktionen über folgende Kanäle hinweg:

- **Microsoft Teams** – Native Integration in Unternehmens-Kollaborations-Workflows
- **Slack** – Direktes Channel-Messaging für Expertenkonsultationen und Bot-Antworten
- **Web Chat** – Browserbasierte Oberfläche für Tests und Entwicklung
- **Erweiterbarer Kanal-Support** – Jede vom Bot Framework unterstützte Plattform

Die **[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht eine
ausgeklügelte Mensch-KI-Kollaboration, indem KI-Agenten ihre Workflows pausieren und nahtlos menschliche Eingaben über
Slack-Kanäle anfordern können. Wenn Agenten Expertenwissen oder Genehmigungen benötigen, posten sie automatisch
strukturierte Fragen in designierten Kanälen, erfassen Antworten und setzen die Verarbeitung mit dem vom Menschen
bereitgestellten Kontext fort.

**Intelligente Chatbot-Implementierungen** bieten mehrere Vervollständigungsstrategien:

- **Agenten-Chatbots** verbinden sich direkt mit Swiss AI Hub-Agenten über NATS-Messaging für komplexe Workflows
- **OpenAI-Chatbots** bieten direkte LLM-Integration für schnellere, einfachere Interaktionen
- **Streaming-Support** liefert Echtzeit-Antwort-Updates mit Tipp-Indikatoren über alle Kanäle hinweg

Die **Enterprise-Grade Infrastruktur** umfasst die automatisierte Azure AD App-Registrierung, sicheres Credential
Management, Konversationspersistenz mit konfigurierbarer TTL und umfassende Audit-Trails für Compliance-Anforderungen.

**Schlüsseltechnologien:**

- **Azure Bot Framework** – Multichannel-Konnektivität und Nachrichten-Routing
- **Azure AD Integration** – Enterprise-Authentifizierung und -Autorisierung
- **NATS Messaging** – Agent-Orchestrierung und ereignisgesteuerte Workflows
- **MongoDB/Cosmos DB** – Konversationspersistenz und Konfigurationsspeicherung
- **Infrastructure as Code** – Pulumi-basierte Azure-Ressourcenbereitstellung

## Warum dies Ihre KI-Strategie grundlegend verändert :trophy:

Die Azure Bot Service Integration eliminiert die Reibung zwischen KI-Funktionalitäten und Benutzerakzeptanz, indem sie
Benutzer dort abholt, wo sie bereits arbeiten:

**🔄 Kein Kontextwechsel**: Benutzer greifen direkt in Microsoft Teams, Slack und anderen vertrauten
Kollaborationsplattformen auf KI-Unterstützung zu. Es ist nicht nötig, neue Oberflächen zu lernen oder etablierte
Workflows zu unterbrechen – KI wird zu einem natürlichen Bestandteil der täglichen Zusammenarbeit.

**🌐 Multichannel-Support auf Unternehmensniveau**: Eine einzige Swiss AI Hub-Bereitstellung bedient Benutzer
gleichzeitig über mehrere Kommunikationsplattformen hinweg. Ob Teams Teams, Slack oder andere vom Bot Framework
unterstützte Kanäle verwenden, jeder erhält konsistente KI-Unterstützung, die auf seine bevorzugte
Kollaborationsumgebung zugeschnitten ist.

**⚡ Echtzeit-Streaming-Antworten**: Die fortschrittliche Streaming-Implementierung bietet sofortiges Feedback mit
Tipp-Indikatoren, partiellen Antworten und inkrementellen Updates. Benutzer sehen, wie die KI in Echtzeit denkt und
antwortet, wodurch natürliche Konversationsflüsse entstehen, die reaktionsschnell und ansprechend wirken.

**🛡️ Unternehmenssicherheit und Compliance**: Basiert auf Azure AD Authentifizierung mit umfassenden
Konversations-Audit-Trails, konfigurierbaren Aufbewahrungsrichtlinien und sicherem Credential Management. Alle
Bot-Interaktionen werden protokolliert und sind nachverfolgbar, wodurch Unternehmenssicherheits- und
Compliance-Anforderungen erfüllt werden.

**🤝 Nahtlose Mensch-KI-Kollaboration**: Die
[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/) ermöglicht es KI-Agenten, auf
natürliche Weise über strukturierte Slack-Workflows an menschliche Experten zu eskalieren. Komplexe Entscheidungen,
Genehmigungen und Wissenslücken werden reibungslos behandelt, ohne die Benutzererfahrung zu beeinträchtigen oder den
Konversationskontext zu verlieren.

::: details **Einrichtung und Nutzung der Azure Bot Service Integration**
## Konfigurationsanforderungen

### Azure Infrastruktur-Setup

1. **Erstellung von Azure Bot Ressourcen**: Verwenden Sie das automatisierte Setup-Skript

   ```bash
   python packages/bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-swiss-ai-hub-bot" \
     --token-url "https://your-swiss-ai-hub-domain.com" \
     --token-path "/api/v1/messages" \
     --mongo-connection-string "mongodb://localhost:27017"
   ```

2. **Azure AD App-Registrierung**: Automatisch durch Setup-Skript gehandhabt

   - Erstellt Azure AD Anwendung mit Bot Framework Berechtigungen
   - Generiert sichere App-Zugangsdaten (App ID und Passwort)
   - Konfiguriert Single-Tenant- oder Multi-Tenant-Authentifizierung

3. **Kanal-Konfiguration**: Manuelle Konfiguration im Azure Portal nach dem Setup

   - **Microsoft Teams**: Teams-Kanal im Azure Bot Service hinzufügen
   - **Slack**: Slack-App erstellen und mit Azure Bot Service verknüpfen
   - **Web Chat**: Automatisch für Tests konfiguriert

### Lokales Entwicklungs-Setup

1. **Entwicklungstunnel**: Lokalen Swiss AI Hub für Azure Bot Service freilegen

   ```bash
   # Install and configure Azure DevTunnel
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   # Use tunnel URL in bot configuration
   ```

2. **Datenbank-Konfiguration**: Zugangsdaten in MongoDB gespeichert

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

1. **Bot zu Teams hinzufügen**: Swiss AI Hub Bot in Ihrem Teams-Workspace installieren
2. **Unterhaltung starten**: Den Bot direkt anschreiben oder in Kanälen erwähnen
3. **Streaming-Antworten**: Echtzeit-Tipp-Indikatoren und inkrementelle Antworten sehen
4. **Konversationspersistenz**: Kontext über mehrere Interaktionen hinweg erhalten

**Erweiterte Funktionen:**

- **Rich Responses**: Unterstützung für Karten, Schaltflächen und interaktive Elemente
- **Datei-Uploads**: Dokumente und Bilder direkt in Teams verarbeiten
- **Thread-Unterstützung**: Konversationskontext in Thread-Diskussionen beibehalten

### Slack Bot-in-the-Loop Workflows

Für detaillierte Informationen zu Bot-in-the-Loop Workflows, einschließlich Expertenkonsultationsprozessen,
Kanal-Konfiguration und Agenten-Integrationsmustern, siehe die dedizierte
[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot-Bereitstellung

**Agentenbasierte Bots**: Verbindung zu spezifischen Swiss AI Hub-Agenten

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

- **Multichannel-Bereitstellung**: Eine einzige Codebasis bedient Teams, Slack, Web Chat und andere Kanäle
- **Aktivitätsverarbeitung**: Nachrichten, Tippereignisse, Konversations-Updates und Datei-Uploads verarbeiten
- **Rich Message Support**: Karten, Schaltflächen, Anhänge und interaktive Elemente
- **Konversationsmanagement**: Persistenter Zustand mit konfigurierbarer TTL (standardmäßig 30 Tage)

**[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

- **Slack Kanalintegration**: Direktes Posten in Expertenkanäle mit Thread-Unterstützung
- **Antwort-Erfassung**: Automatische Erkennung und Verarbeitung menschlicher Antworten
- **Konversations-Threading**: Kontext über mehrstufige Expertenkonsultationen hinweg beibehalten
- **Wissenspersistenz**: Expertenantworten für organisatorisches Lernen gespeichert

**Chatbot-Implementierungen:**

- **Streaming-Antworten**: Echtzeit-Nachrichten-Updates mit Tipp-Indikatoren
- **Agenten-Integration**: Direkte Verbindung zu Swiss AI Hub Agenten-Workflows über NATS
- **OpenAI-Integration**: Standalone LLM-Interaktionen für einfache Anwendungsfälle
- **Fehlerbehandlung**: Graceful Degradation mit benutzerfreundlichen Fehlermeldungen

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Azure AD Authentifizierung**: Enterprise-Grade Authentifizierung mit rollenbasiertem Zugriff
- **Sichere Speicherung von Zugangsdaten**: Bot-Zugangsdaten verschlüsselt und in MongoDB/Cosmos DB gespeichert
- **Audit Trails**: Vollständige Konversationshistorie mit Benutzerzuordnung und Zeitstempeln
- **Netzwerksicherheit**: Unterstützung für private Endpunkte und VNet-Integration

**Best Practices:**

- **Kanalorganisation**: Dedizierte Slack-Kanäle für verschiedene Expertenbereiche
- **Konversations-TTL**: Geeignete Aufbewahrungsrichtlinien für Compliance-Anforderungen konfigurieren
- **Bot-Benennung**: Klare, beschreibende Namen für mehrere Bot-Bereitstellungen verwenden
- **Monitoring**: Umfassendes Logging und Alerting für Bot-Gesundheit implementieren
- **Kapazitätsplanung**: Konversationsvolumen und Antwortzeiten überwachen

**Performance-Optimierung:**

- **Streaming-Konfiguration**: Update-Frequenz für optimale Benutzererfahrung optimieren
- **Konversationsbereinigung**: Automatisierte Bereinigung abgelaufener Konversationen implementieren
- **Datenbank-Indizierung**: MongoDB-Abfragen für Konversationsabruf optimieren
- **Caching-Strategie**: Häufig aufgerufene Konfiguration und Zugangsdaten cachen
:::

## Erste Schritte

Um die Azure Bot Service Integration in Ihrer Swiss AI Hub-Bereitstellung zu implementieren:

1. **Azure Setup-Skript ausführen**: Verwenden Sie die bereitgestellte Automatisierung, um Azure Bot Ressourcen zu
   erstellen und die Authentifizierung mit Ihrem bevorzugten Datenbank-Backend zu konfigurieren
2. **Kanäle konfigurieren**: Richten Sie Microsoft Teams und/oder Slack-Integrationen über die Azure Portal
   Kanal-Konfiguration ein
3. **Bot-Implementierungen bereitstellen**: Wählen Sie zwischen agentenbasierten Bots für komplexe Workflows oder
   OpenAI-basierten Bots für einfachere Interaktionen, mit Streaming-Unterstützung für eine verbesserte
   Benutzererfahrung

Für detaillierte Setup-Anweisungen, Fehlerbehebungsleitfäden und erweiterte Konfigurationsoptionen verweisen wir auf die
[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für
Mensch-KI-Kollaborations-Workflows, die [Expert Agents Dokumentation](../../5_agents/3_expert_asking_agent/) für
Wissenskonsultationsmuster und den Swiss AI Hub Bot Developer's Guide für Implementierungsdetails.
