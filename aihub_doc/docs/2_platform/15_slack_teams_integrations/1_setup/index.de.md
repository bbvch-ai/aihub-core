---
title: Integration des Azure Bot Service
index: 3
source_sha: "ce7063f1b3093bcd1106388b15f9185b1e51e89c73c2ab5b4ffcb1352af24c95"
---

# Integration des Azure Bot Service :speech_balloon: :100:

::: info **TL;DR – Was ist die Integration des Azure Bot Service?**
Die Integration des Azure Bot Service verwandelt den AI-Hub in eine **Multi-Channel-Konversationsplattform**, die Benutzer
über bekannte Kollaborationstools wie Microsoft Teams und Slack mit KI-Agenten verbindet. Diese Integration bietet
Bot-Konnektivität auf Unternehmensniveau mit Streaming-Antworten, Konversationspersistenz und nahtlosen Human-in-the-Loop-Workflows,
wodurch die Notwendigkeit entfällt, dass Benutzer zwischen Anwendungen wechseln müssen, um auf KI-Unterstützung zuzugreifen.
:::

## Was ist die Integration des Azure Bot Service und wie funktioniert sie? :brain:

Die Integration des Azure Bot Service nutzt das **Microsoft Bot Framework**, um einheitliche Konversationserlebnisse über
mehrere Kanäle hinweg zu bieten und die Funktionen des AI-Hubs überall dort zugänglich zu machen, wo Benutzer auf natürliche
Weise arbeiten und zusammenarbeiten.

Die **Multi-Channel-Bot-Architektur** ermöglicht konsistente KI-Interaktionen über:

-   **Microsoft Teams** – Native Integration in Unternehmens-Kollaborations-Workflows
-   **Slack** – Direkte Kanalnachrichten für Expertenkonsultationen und Bot-Antworten
-   **Web Chat** – Browserbasierte Schnittstelle für Tests und Entwicklung
-   **Erweiterbare Kanalunterstützung** – Jede vom Bot Framework unterstützte Plattform

Die **[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht eine hochentwickelte
Mensch-KI-Kollaboration, indem KI-Agenten ihre Workflows unterbrechen und nahtlos menschliche Eingaben über Slack-Kanäle
anfordern können. Wenn Agenten Expertenwissen oder Genehmigung benötigen, posten sie automatisch strukturierte Fragen in
designierte Kanäle, erfassen die Antworten und setzen die Verarbeitung mit dem vom Menschen bereitgestellten Kontext fort.

**Intelligente Chatbot-Implementierungen** bieten mehrere Abschlussstrategien:

-   **Agenten-Chatbots** verbinden sich direkt mit AI-Hub-Agenten über NATS-Messaging für komplexe Workflows
-   **OpenAI-Chatbots** bieten direkte LLM-Integration für schnellere, einfachere Interaktionen
-   **Streaming-Unterstützung** liefert Echtzeit-Antwort-Updates mit Tippindikatoren über alle Kanäle hinweg

Die **Infrastruktur auf Unternehmensniveau** umfasst die automatisierte Azure AD App-Registrierung, sichere
Anmeldeinformationsverwaltung, Konversationspersistenz mit konfigurierbarer TTL und umfassende Audit-Trails für
Compliance-Anforderungen.

**Schlüsseltechnologien:**

-   **Azure Bot Framework** – Multi-Channel-Konnektivität und Nachrichten-Routing
-   **Azure AD-Integration** – Authentifizierung und Autorisierung auf Unternehmensebene
-   **NATS Messaging** – Agenten-Orchestrierung und ereignisgesteuerte Workflows
-   **MongoDB/Cosmos DB** – Konversationspersistenz und Konfigurationsspeicherung
-   **Infrastructure as Code** – Pulumi-basierte Azure-Ressourcenbereitstellung

## Warum dies Ihre KI-Strategie grundlegend verändert :trophy:

Die Integration des Azure Bot Service beseitigt die Reibung zwischen KI-Funktionen und Benutzerakzeptanz, indem sie Benutzer
dort abholt, wo sie bereits arbeiten:

**🔄 Kein Kontextwechsel**: Benutzer greifen direkt in Microsoft Teams, Slack und anderen bekannten Kollaborationsplattformen
auf KI-Unterstützung zu. Es ist nicht erforderlich, neue Schnittstellen zu erlernen oder etablierte Workflows zu
unterbrechen – KI wird zu einem natürlichen Bestandteil der täglichen Zusammenarbeit.

**🌐 Skalierbare Multi-Channel-Unterstützung für Unternehmen**: Eine einzige AI-Hub-Bereitstellung bedient Benutzer
gleichzeitig über mehrere Kommunikationsplattformen hinweg. Unabhängig davon, ob Teams Teams, Slack oder andere vom Bot
Framework unterstützte Kanäle nutzen, erhält jeder konsistente KI-Unterstützung, die auf seine bevorzugte
Kollaborationsumgebung zugeschnitten ist.

**⚡ Echtzeit-Streaming-Antworten**: Die fortschrittliche Streaming-Implementierung bietet sofortiges Feedback mit
Tippindikatoren, teilweisen Antworten und inkrementellen Updates. Benutzer sehen, wie die KI in Echtzeit denkt und
antwortet, wodurch natürliche Konversationsabläufe entstehen, die sich reaktionsschnell und ansprechend anfühlen.

**🛡️ Unternehmenssicherheit und Compliance**: Basiert auf Azure AD-Authentifizierung mit umfassenden
Konversations-Audit-Trails, konfigurierbaren Aufbewahrungsrichtlinien und sicherer Anmeldeinformationsverwaltung. Alle
Bot-Interaktionen werden protokolliert und sind nachvollziehbar, wodurch die Sicherheits- und Compliance-Anforderungen
von Unternehmen erfüllt werden.

**🤝 Nahtlose Mensch-KI-Kollaboration**: Die
**[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** ermöglicht es KI-Agenten, auf
natürliche Weise menschliche Experten über strukturierte Slack-Workflows einzubeziehen. Komplexe Entscheidungen,
Genehmigungen und Wissenslücken werden reibungslos bearbeitet, ohne das Benutzererlebnis zu beeinträchtigen oder den
Konversationskontext zu verlieren.

::: details **Einrichtung und Nutzung der Azure Bot Service Integration**
## Konfigurationsanforderungen

### Azure Infrastruktur-Setup

1.  **Erstellung von Azure Bot-Ressourcen**: Verwenden Sie das automatisierte Setup-Skript

    ```bash
    python aihub_bot/setup_azure_bot.py \
      --resource-group "your-resource-group" \
      --bot-name "your-ai-hub-bot" \
      --token-url "https://your-aihub-domain.com" \
      --token-path "/api/v1/messages" \
      --mongo-connection-string "mongodb://localhost:27017"
    ```

2.  **Azure AD App-Registrierung**: Automatisch durch das Setup-Skript gehandhabt

    -   Erstellt eine Azure AD-Anwendung mit Bot Framework-Berechtigungen
    -   Generiert sichere App-Anmeldeinformationen (App ID und Passwort)
    -   Konfiguriert Single-Tenant- oder Multi-Tenant-Authentifizierung

3.  **Kanal-Konfiguration**: Manuell im Azure Portal nach dem Setup konfigurieren

    -   **Microsoft Teams**: Teams-Kanal im Azure Bot Service hinzufügen
    -   **Slack**: Slack-App erstellen und mit Azure Bot Service verknüpfen
    -   **Web Chat**: Automatisch für Tests konfiguriert

### Lokales Entwicklungs-Setup

1.  **Entwicklungstunnel**: Lokalen AI-Hub für Azure Bot Service freigeben

    ```bash
    # Installieren und konfigurieren Sie Azure DevTunnel
    devtunnel create --allow-anonymous
    devtunnel port create -p 8000
    devtunnel host
    # Verwenden Sie die Tunnel-URL in der Bot-Konfiguration
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

## Anwendungsbeispiele

### Microsoft Teams-Integration

**Grundlegende Chat-Interaktion:**

1.  **Bot zu Teams hinzufügen**: AI-Hub-Bot in Ihrem Teams-Arbeitsbereich installieren
2.  **Konversation starten**: Dem Bot direkt eine Nachricht senden oder ihn in Kanälen erwähnen
3.  **Streaming-Antworten**: Echtzeit-Tippindikatoren und inkrementelle Antworten sehen
4.  **Konversationspersistenz**: Kontext bleibt über mehrere Interaktionen hinweg erhalten

**Erweiterte Funktionen:**

-   **Rich Responses**: Unterstützung für Karten, Schaltflächen und interaktive Elemente
-   **Dateiuploads**: Dokumente und Bilder direkt in Teams verarbeiten
-   **Thread-Unterstützung**: Konversationskontext in Thread-Diskussionen beibehalten

### Slack Bot-in-the-Loop-Workflows

Für detaillierte Informationen zu Bot-in-the-Loop-Workflows, einschließlich Expertenkonsultationsprozessen,
Kanal-Konfiguration und Agenten-Integrationsmustern, siehe die dedizierte
[Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/).

### Multi-Bot-Bereitstellung

**Agentenbasierte Bots**: Verbindung zu spezifischen AI-Hub-Agenten herstellen

```python
# Konfigurieren Sie den Bot zur Verwendung eines bestimmten Agenten
AgentChatBot(
    agent_class="ExpertGroundedAgent",
    agent_id="expert_agent_v1",
    streaming=True
)
```

**OpenAI-basierte Bots**: Direkte LLM-Integration für einfachere Anwendungsfälle

```python
# Konfigurieren Sie den Bot mit direktem OpenAI-Zugriff
OpenaiChatBot(
    llm_config=OpenAIConfig(...),
    system_message="You are a helpful assistant",
    streaming=True
)
```

## Verfügbare Funktionen

**Bot Framework-Integration:**

-   **Multi-Channel-Bereitstellung**: Eine einzige Codebasis bedient Teams, Slack, Web Chat und andere Kanäle
-   **Aktivitätsverarbeitung**: Nachrichten, Tippereignisse, Konversations-Updates und Dateiuploads verarbeiten
-   **Unterstützung für Rich Messages**: Karten, Schaltflächen, Anhänge und interaktive Elemente
-   **Konversationsverwaltung**: Persistenter Zustand mit konfigurierbarer TTL (Standard 30 Tage)

**[Bot-in-the-Loop-Infrastruktur](../../../3_sdk/6_feature_overview/bot-in-the-loop/):**

-   **Slack-Kanal-Integration**: Direktes Posten in Expertenkanäle mit Thread-Unterstützung
-   **Antwort-Erfassung**: Automatische Erkennung und Verarbeitung menschlicher Antworten
-   **Konversations-Threading**: Kontext über Expertengespräche mit mehreren Runden hinweg beibehalten
-   **Wissenspersistenz**: Expertenantworten für organisatorisches Lernen gespeichert

**Chatbot-Implementierungen:**

-   **Streaming-Antworten**: Echtzeit-Nachrichten-Updates mit Tippindikatoren
-   **Agenten-Integration**: Direkte Verbindung zu AI-Hub-Agenten-Workflows über NATS
-   **OpenAI-Integration**: Standalone LLM-Interaktionen für einfache Anwendungsfälle
-   **Fehlerbehandlung**: Graceful Degradation mit benutzerfreundlichen Fehlermeldungen

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

-   **Azure AD-Authentifizierung**: Authentifizierung auf Unternehmensebene mit rollenbasiertem Zugriff
-   **Sichere Speicherung von Anmeldeinformationen**: Bot-Anmeldeinformationen verschlüsselt und in MongoDB/Cosmos DB gespeichert
-   **Audit-Trails**: Vollständiger Konversationsverlauf mit Benutzerzuordnung und Zeitstempeln
-   **Netzwerksicherheit**: Unterstützung für private Endpunkte und VNet-Integration

**Best Practices:**

-   **Kanalorganisation**: Dedizierte Slack-Kanäle für verschiedene Expertenbereiche
-   **Konversations-TTL**: Geeignete Aufbewahrungsrichtlinien für Compliance-Anforderungen konfigurieren
-   **Bot-Benennung**: Klare, beschreibende Namen für mehrere Bot-Bereitstellungen verwenden
-   **Überwachung**: Umfassendes Logging und Alerting für die Bot-Gesundheit implementieren
-   **Kapazitätsplanung**: Konversationsvolumen und Antwortzeiten überwachen

**Leistungsoptimierung:**

-   **Streaming-Konfiguration**: Update-Frequenz für optimale Benutzererfahrung abstimmen
-   **Konversationsbereinigung**: Automatisierte Bereinigung abgelaufener Konversationen implementieren
-   **Datenbankindexierung**: MongoDB-Abfragen für den Abruf von Konversationen optimieren
-   **Caching-Strategie**: Häufig aufgerufene Konfiguration und Anmeldeinformationen cachen
:::

## Erste Schritte

Um die Integration des Azure Bot Service in Ihrer AI-Hub-Bereitstellung zu implementieren:

1.  **Azure Setup-Skript ausführen**: Verwenden Sie die bereitgestellte Automatisierung, um Azure Bot-Ressourcen zu erstellen
    und die Authentifizierung mit Ihrem bevorzugten Datenbank-Backend zu konfigurieren
2.  **Kanäle konfigurieren**: Richten Sie Microsoft Teams- und/oder Slack-Integrationen über die Kanal-Konfiguration im
    Azure Portal ein
3.  **Bot-Implementierungen bereitstellen**: Wählen Sie zwischen agentenbasierten Bots für komplexe Workflows oder
    OpenAI-basierten Bots für einfachere Interaktionen, mit Streaming-Unterstützung für ein verbessertes Benutzererlebnis

Für detaillierte Einrichtungsanweisungen, Fehlerbehebung und erweiterte Konfigurationsoptionen lesen Sie die
[Bot-in-the-Loop-Dokumentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/) für Mensch-KI-Kollaborations-Workflows,
die [Expert Agents-Dokumentation](../expert-agents/) für Wissenskonsultationsmuster und den AI-Hub Bot Developer's
Guide für Implementierungsdetails.
