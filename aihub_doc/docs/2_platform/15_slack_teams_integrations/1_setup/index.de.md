---
title: Azure Bot Service Integration
index: 3
source_sha: "fa7c883fb72890cc1f965c7ad61707f516bbf6f459922b53abd698b6e9e43e4f"
---

# Azure Bot Service Integration :speech_balloon: :100:

::: info **Kurz gesagt – Was ist die Integration des Azure Bot Service?**
Die Azure Bot Service Integration verwandelt den AI-Hub in eine **Multi-Channel-Konversationsplattform**, die Benutzer
über vertraute Kollaborationstools wie Microsoft Teams und Slack mit KI-Agenten verbindet. Diese Integration bietet
Bot-Konnektivität der Enterprise-Klasse mit Streaming-Antworten, Konversationspersistenz und nahtlosen Human-in-the-Loop-Workflows,
wodurch Benutzer nicht mehr zwischen Anwendungen wechseln müssen, um auf KI-Unterstützung zuzugreifen.
:::

## Was ist die Integration des Azure Bot Service und wie funktioniert sie? :brain:

Die Azure Bot Service Integration nutzt das **Microsoft Bot Framework**, um einheitliche Konversationserlebnisse über
mehrere Kanäle hinweg bereitzustellen und die Funktionen des AI-Hub dort zugänglich zu machen, wo Benutzer natürlich
arbeiten und zusammenarbeiten.

Die **Multi-Channel Bot-Architektur** ermöglicht konsistente KI-Interaktionen über:

-   **Microsoft Teams** – Native Integration in Unternehmens-Kollaborationsworkflows
-   **Slack** – Direkte Kanalnachrichten für Expertenberatung und Bot-Antworten
-   **Web Chat** – Browserbasierte Oberfläche für Tests und Entwicklung
-   **Erweiterbare Kanalunterstützung** – Jede vom Bot Framework unterstützte Plattform

Die **[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht eine ausgefeilte
Mensch-KI-Zusammenarbeit, indem sie KI-Agenten erlaubt, ihre Workflows zu unterbrechen und nahtlos menschliche
Eingaben über Slack-Kanäle anzufordern. Wenn Agenten Expertenwissen oder Genehmigung benötigen, posten sie
automatisch strukturierte Fragen in designierte Kanäle, erfassen Antworten und fahren mit der Verarbeitung mit dem vom
Menschen bereitgestellten Kontext fort.

**Intelligente Chatbot-Implementierungen** bieten mehrere Vervollständigungsstrategien:

-   **Agent-Chatbots** verbinden sich direkt mit AI-Hub-Agenten über NATS Messaging für komplexe Workflows
-   **OpenAI-Chatbots** bieten direkte LLM-Integration für schnellere, einfachere Interaktionen
-   **Streaming-Unterstützung** liefert Echtzeit-Antwortaktualisierungen mit Tippindikatoren über alle Kanäle hinweg

Die **Infrastruktur der Enterprise-Klasse** umfasst die automatisierte Azure AD App-Registrierung, sichere
Anmeldeinformationsverwaltung, Konversationspersistenz mit konfigurierbarer TTL und umfassende Audit-Trails für
Compliance-Anforderungen.

**Schlüsseltechnologien:**

-   **Azure Bot Framework** – Multi-Channel-Konnektivität und Nachrichten-Routing
-   **Azure AD Integration** – Unternehmensauthentifizierung und -autorisierung
-   **NATS Messaging** – Agenten-Orchestrierung und ereignisgesteuerte Workflows
-   **MongoDB/Cosmos DB** – Konversationspersistenz und Konfigurationsspeicherung
-   **Infrastructure as Code** – Pulumi-basierte Azure-Ressourcenbereitstellung

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Die Azure Bot Service Integration eliminiert die Reibung zwischen KI-Funktionen und Benutzerakzeptanz, indem sie
Benutzer dort abholt, wo sie bereits arbeiten:

**🔄 Kein Kontextwechsel**: Benutzer greifen direkt innerhalb von Microsoft Teams, Slack und anderen vertrauten
Kollaborationsplattformen auf KI-Unterstützung zu. Es ist nicht nötig, neue Schnittstellen zu lernen oder etablierte
Workflows zu unterbrechen – KI wird zu einem natürlichen Bestandteil der täglichen Zusammenarbeit.

**🌐 Unternehmensweite Multi-Channel-Unterstützung**: Eine einzige AI-Hub-Bereitstellung bedient Benutzer
gleichzeitig über mehrere Kommunikationsplattformen. Egal, ob Teams Teams, Slack oder andere vom Bot Framework
unterstützte Kanäle nutzen, jeder erhält konsistente KI-Unterstützung, die auf seine bevorzugte
Kollaborationsumgebung zugeschnitten ist.

**⚡ Echtzeit-Streaming-Antworten**: Eine fortschrittliche Streaming-Implementierung bietet sofortiges Feedback mit
Tippindikatoren, Teilantworten und inkrementellen Updates. Benutzer sehen, wie die KI in Echtzeit denkt und antwortet,
wodurch natürliche Konversationsabläufe entstehen, die sich reaktionsschnell und ansprechend anfühlen.

**🛡️ Unternehmenssicherheit und Compliance**: Basierend auf Azure AD-Authentifizierung mit umfassenden
Konversations-Audit-Trails, konfigurierbaren Aufbewahrungsrichtlinien und sicherer Anmeldeinformationsverwaltung.
Alle Bot-Interaktionen werden protokolliert und sind nachvollziehbar, wodurch die Sicherheits- und Compliance-Anforderungen
von Unternehmen erfüllt werden.

**🤝 Nahtlose Mensch-KI-Zusammenarbeit**: Die
[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/) ermöglicht es KI-Agenten, auf
natürliche Weise über strukturierte Slack-Workflows an menschliche Experten zu eskalieren. Komplexe Entscheidungen,
Genehmigungen und Wissenslücken werden reibungslos gehandhabt, ohne die Benutzererfahrung zu unterbrechen oder den
Konversationskontext zu verlieren.

::: details **Einrichtung und Nutzung der Azure Bot Service Integration**
## Konfigurationsanforderungen

### Azure Infrastruktur-Setup

1.  **Azure Bot-Ressourcenerstellung**: Verwenden Sie das automatisierte Setup-Skript

    ```bash
    python aihub_bot/setup_azure_bot.py \
      --resource-group "your-resource-group" \
      --bot-name "your-ai-hub-bot" \
      --token-url "https://your-aihub-domain.com" \
      --token-path "/api/v1/messages" \
      --mongo-connection-string "mongodb://localhost:27017"
    ```

2.  **Azure AD App-Registrierung**: Automatisch durch das Setup-Skript behandelt

    -   Erstellt Azure AD-Anwendung mit Bot Framework-Berechtigungen
    -   Generiert sichere App-Anmeldeinformationen (App ID und Passwort)
    -   Konfiguriert Single-Tenant- oder Multi-Tenant-Authentifizierung

3.  **Kanal-Konfiguration**: Manuell im Azure Portal nach dem Setup konfigurieren

    -   **Microsoft Teams**: Teams-Kanal im Azure Bot Service hinzufügen
    -   **Slack**: Slack App erstellen und mit Azure Bot Service verknüpfen
    -   **Web Chat**: Automatisch für Tests konfiguriert

### Lokales Entwicklungs-Setup

1.  **Entwicklungstunnel**: Lokalen AI-Hub für Azure Bot Service freilegen

    ```bash
    # Install and configure Azure DevTunnel
    devtunnel create --allow-anonymous
    devtunnel port create -p 8000
    devtunnel host
    # Use tunnel URL in bot configuration
    ```

2.  **Datenbankkonfiguration**: Anmeldeinformationen in MongoDB gespeichert

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

## Nutzungsbeispiele

### Microsoft Teams Integration

**Grundlegende Chat-Interaktion:**

1.  **Bot zu Teams hinzufügen**: AI-Hub-Bot in Ihrem Teams-Workspace installieren
2.  **Konversation starten**: Dem Bot direkt eine Nachricht senden oder in Kanälen erwähnen
3.  **Streaming-Antworten**: Echtzeit-Tippindikatoren und inkrementelle Antworten sehen
4.  **Konversationspersistenz**: Kontext über mehrere Interaktionen hinweg beibehalten

**Erweiterte Funktionen:**

-   **Rich Responses**: Unterstützung für Karten, Schaltflächen und interaktive Elemente
-   **Dateiuploads**: Dokumente und Bilder direkt in Teams verarbeiten
-   **Thread-Unterstützung**: Konversationskontext in Thread-Diskussionen beibehalten

### Slack Bot-in-the-Loop Workflows

Für detaillierte Informationen zu Bot-in-the-Loop Workflows, einschließlich Expertenkonsultationsprozessen,
Kanalkonfiguration und Agentenintegrationsmustern, siehe die dedizierte
[Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot-Bereitstellung

**Agenten-basierte Bots**: Verbindung zu spezifischen AI-Hub-Agenten

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

-   **Multi-Channel-Bereitstellung**: Eine einzige Codebasis bedient Teams, Slack, Web Chat und andere Kanäle
-   **Aktivitätsverarbeitung**: Nachrichten, Tippereignisse, Konversationsaktualisierungen und Dateiuploads verarbeiten
-   **Rich Message Unterstützung**: Karten, Schaltflächen, Anhänge und interaktive Elemente
-   **Konversationsmanagement**: Persistenter Zustand mit konfigurierbarer TTL (Standard 30 Tage)

**[Bot-in-the-Loop Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

-   **Slack Kanal-Integration**: Direktes Posten in Expertenkanäle mit Thread-Unterstützung
-   **Antwort-Erfassung**: Automatische Erkennung und Verarbeitung menschlicher Antworten
-   **Konversations-Threading**: Kontext über mehrstufige Expertenkonsultationen hinweg beibehalten
-   **Wissenspersistenz**: Expertenantworten für organisatorisches Lernen gespeichert

**Chatbot-Implementierungen:**

-   **Streaming-Antworten**: Echtzeit-Nachrichtenaktualisierungen mit Tippindikatoren
-   **Agenten-Integration**: Direkte Verbindung zu AI-Hub-Agenten-Workflows über NATS
-   **OpenAI-Integration**: Standalone LLM-Interaktionen für einfache Anwendungsfälle
-   **Fehlerbehandlung**: Anmutige Degradation mit benutzerfreundlichen Fehlermeldungen

## Sicherheit und Best Practices

**Sicherheitsüberlegungen:**

-   **Azure AD Authentifizierung**: Authentifizierung der Enterprise-Klasse mit rollenbasiertem Zugriff
-   **Sichere Speicherung von Anmeldeinformationen**: Bot-Anmeldeinformationen verschlüsselt und in MongoDB/Cosmos DB gespeichert
-   **Audit-Trails**: Vollständige Konversationshistorie mit Benutzerzuordnung und Zeitstempeln
-   **Netzwerksicherheit**: Unterstützung für private Endpunkte und VNet-Integration

**Best Practices:**

-   **Kanalorganisation**: Spezifische Slack-Kanäle für verschiedene Expertenbereiche dedizieren
-   **Konversations-TTL**: Geeignete Aufbewahrungsrichtlinien für Compliance-Anforderungen konfigurieren
-   **Bot-Benennung**: Klare, beschreibende Namen für mehrere Bot-Bereitstellungen verwenden
-   **Monitoring**: Umfassendes Logging und Alerting für die Bot-Gesundheit implementieren
-   **Kapazitätsplanung**: Konversationsvolumen und Antwortzeiten überwachen

**Leistungsoptimierung:**

-   **Streaming-Konfiguration**: Aktualisierungsfrequenz für optimale Benutzererfahrung anpassen
-   **Konversationsbereinigung**: Automatisierte Bereinigung abgelaufener Konversationen implementieren
-   **Datenbank-Indizierung**: MongoDB-Abfragen für den Konversationsabruf optimieren
-   **Caching-Strategie**: Häufig aufgerufene Konfigurationen und Anmeldeinformationen cachen
:::

## Erste Schritte

Um die Azure Bot Service Integration in Ihrer AI-Hub-Bereitstellung zu implementieren:

1.  **Azure Setup-Skript ausführen**: Verwenden Sie die bereitgestellte Automatisierung, um Azure Bot-Ressourcen zu
    erstellen und die Authentifizierung mit Ihrem bevorzugten Datenbank-Backend zu konfigurieren
2.  **Kanäle konfigurieren**: Richten Sie Microsoft Teams und/oder Slack-Integrationen über die Kanal-Konfiguration
    des Azure Portals ein
3.  **Bot-Implementierungen bereitstellen**: Wählen Sie zwischen agentenbasierten Bots für komplexe Workflows oder
    OpenAI-basierten Bots für einfachere Interaktionen, mit Streaming-Unterstützung für eine verbesserte Benutzererfahrung

Für detaillierte Einrichtungsanweisungen, Fehlerbehebungsleitfäden und erweiterte Konfigurationsoptionen konsultieren
Sie die [Bot-in-the-Loop Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für
Mensch-KI-Kollaborations-Workflows, die [Expert Agents Dokumentation](../../5_agents/3_expert_asking_agent/) für
Wissenskonsultationsmuster und den AI-Hub Bot Developer's Guide für Implementierungsdetails.
