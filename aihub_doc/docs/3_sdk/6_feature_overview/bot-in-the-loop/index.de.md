---
title: Bot-in-the-Loop
index: 4
source_sha: "82cdc362bcee9dbd22ed8b74869963fd1e280150f7a7e927390d38c417e40392"
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **TL;DR – Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agenten, **Arbeitsabläufe nahtlos zu unterbrechen und über Slack-Kanäle menschliche Eingaben anzufordern**, um anschließend die Ausführung mit der menschlichen Antwort automatisch fortzusetzen. Dieses Muster überbrückt die Lücke zwischen autonomer KI-Verarbeitung und menschlicher Expertise und ermöglicht es Agenten, komplexe Entscheidungen zu treffen und dabei die vollständige Automatisierung der menschlichen Beteiligung aufrechtzuerhalten.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop stellt ein ausgeklügeltes **Mensch-KI-Kollaborationsmuster** dar, das es KI-Agenten ermöglicht, ihre automatisierten Arbeitsabläufe an kritischen Entscheidungspunkten zu unterbrechen und menschliche Expertise nahtlos durch strukturierte Slack-Interaktionen zu integrieren.

Die **Workflow-Integrationsarchitektur** ermöglicht es KI-Agenten, Bot-in-the-Loop an jedem Punkt ihrer Ausführung aufzurufen. Wenn ein Agent auf eine Entscheidung stößt, die menschliche Eingaben, Genehmigungen oder Fachkenntnisse erfordert, sendet er ein `BotInTheLoopRequestEvent` aus, das automatisch:

- Eine formatierte Frage an einen bestimmten Slack-Kanal sendet
- Den vollständigen Workflow-Kontext und die Konversations-Threads beibehält
- Auf menschliche Antworten wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agentenausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** stellt die menschliche Schnittstelle über vertraute Kollaborationstools bereit. Experten antworten direkt in Slack-Threads, wo:

- Fragen als strukturierte, Thread-basierte Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antworten verfolgt, wer Eingaben gemacht hat
- Der Konversationsverlauf für Audit und Lernen beibehalten wird

Die **Ereignisgesteuerte Orchestrierung** steuert die gesamte Interaktion über das Ereignissystem des AI-Hub:

- `BotInTheLoopRequestEvent` unterbricht Workflows und postet an Slack
- `BotInTheLoopResponseEvent` erfasst Antworten und setzt Workflows fort
- Die vollständige Kontexterhaltung gewährleistet eine nahtlose Fortsetzung
- Die Fehlerbehandlung verwaltet Timeouts und fehlgeschlagene Antworten

Die **Agenten-Workflow-Integration** verwendet den einfachen `BotInTheLoop.invoke()`-Helfer, der die Integration für Agentenentwickler trivial macht:

```python
# Pause workflow for human input
return BotInTheLoop.invoke(
    user=current_user,
    question="Should I proceed with this high-risk operation?",
    slack_channel_id="C08MCK6LEBY"
)
```

**Schlüsseltechnologien:**

- **NATS Event System** – Asynchrone Nachrichtenweiterleitung und Workflow-Orchestrierung
- **Slack Bot Framework** – Kanalintegration mit Threading und Zuordnung
- **Azure Bot Service** – Multi-Kanal-Bot-Konnektivität und Nachrichtenverarbeitung
- **Event Store** – Persistenter Kontext und Konversationsverfolgung
- **Agent Workflow Engine** – Nahtlose Integration mit den Ausführungsabläufen von KI-Agenten

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop verändert die Art und Weise, wie Organisationen die KI-Automatisierung angehen, indem es die kritische Herausforderung der Mensch-KI-Kollaboration im großen Maßstab löst:

**🤝 Nahtlose Mensch-KI-Kollaboration**: KI-Agenten können menschliche Experten nun auf natürliche Weise einbeziehen, ohne automatisierte Workflows zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen über vertraute Slack-Interaktionen, während die KI den vollständigen Kontext beibehält und die Verarbeitung mit menschlicher Eingabe automatisch fortsetzt.

**⚡ Ununterbrochene Automatisierung**: Im Gegensatz zu traditionellen Systemen, die manuelle Eingriffspunkte erfordern, gewährleistet Bot-in-the-Loop eine kontinuierliche Automatisierung um die menschliche Beteiligung herum. Agenten pausieren nur bei Bedarf, fordern spezifische Eingaben an und nehmen die Verarbeitung sofort wieder auf, wodurch sowohl die Effizienz als auch die Nutzung menschlicher Expertise maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können mehrere KI-Workflows gleichzeitig effizient durch strukturierte Slack-Interaktionen unterstützen. Eine Expertenkonsultation kann mehrere Agenten informieren, und ihr Wissen wird für das organisationale Lernen und zukünftige Verbesserungen der Automatisierung erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern – wie die Einhaltung gesetzlicher Vorschriften, hochriskante Genehmigungen oder komplexe Interpretationen – können nahtlos in ansonsten automatisierte Prozesse integriert werden. Dies gewährleistet sowohl Geschwindigkeit als auch Sicherheit in KI-gesteuerten Workflows.

**📚 Erfassung von Organisationswissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst, wodurch ein ständig wachsendes Repository von Expertenentscheidungen und -wissen entsteht. Dies ermöglicht die kontinuierliche Verbesserung von KI-Systemen und baut institutionelles Wissen auf, das Personalwechsel überdauert.

::: details **Einrichtung und Verwendung von Bot-in-the-Loop**
## Konfigurationsanforderungen

### Slack Bot-Einrichtung

1.  **Azure Bot Service Konfiguration**: Stellen Sie sicher, dass Ihr AI-Hub über eine Azure Bot Service Integration verfügt

    ```bash
    python aihub_bot/setup_azure_bot.py \
      --resource-group "your-resource-group" \
      --bot-name "your-ai-hub-bot" \
      --token-url "https://your-aihub-domain.com" \
      --slack-token "xoxb-your-slack-oauth-token"
    ```

2.  **Slack App Konfiguration**: Erstellen Sie eine Slack App mit den erforderlichen Berechtigungen

    -   **Bot-Token-Bereiche**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
    -   **Ereignisabonnements**: Abonnieren Sie `message.channels`-Ereignisse
    -   **OAuth-Installation**: Installieren Sie die App in Ihrem Workspace

3.  **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt wurde, in denen Sie Fragen posten möchten

    ```
    /invite @YourAIHubBot
    ```

### Agenten-Integrations-Setup

1.  **Bot-in-the-Loop Helper importieren**: Fügen Sie dies Ihren Agenten-Imports hinzu

    ```python
    from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
    ```

2.  **Slack Kanal-IDs konfigurieren**: Ermitteln Sie Ihre Slack Kanal-IDs (Format: `C08MCK6LEBY`)

    ```python
    # Rechtsklick auf den Kanal → Kanal-Details anzeigen → Kanal-ID kopieren
    EXPERT_CHANNEL_ID = "C08MCK6LEBY"
    ```

3.  **NATS Ereignisverteilung**: Stellen Sie sicher, dass Ihre AI-Hub-Bereitstellung für das Event-Routing mit NATS Messaging konfiguriert ist

## Anwendungsbeispiele

### Grundlegende Agentenintegration

**Einfacher Entscheidungspunkt:**

```python
class ApprovalAgent(Agent):
    @step()
    async def approval_step(
        self,
        event: RequestEvent,
        run_context: RunContext
    ) -> BotInTheLoop.request:
        user = await run_context.get("user")
        return BotInTheLoop.invoke(
            user=user,
            question=f"Approve budget request for ${event.amount}?",
            slack_channel_id="C08MCK6LEBY"
        )

    @step()
    async def process_approval(
        self,
        response: BotInTheLoop.response
    ) -> ApprovedEvent | RejectedEvent:
        if response.response.lower() in ["yes", "approved", "approve"]:
            return ApprovedEvent(approver=response.responder.user_name)
        return RejectedEvent(reason=response.response)
```

### Expertenkonsultations-Workflow

**Muster zur Wissenssuche:**

```python
class ExpertConsultationAgent(Agent):
    @step()
    async def consult_expert(
        self,
        event: ComplexQuestionEvent,
        agent_config: ConsultationConfig
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=event.user,
            question=f"Expert input needed: {event.question}",
            slack_channel_id=agent_config.expert_channel_id
        )

    @step()
    async def process_expert_response(
        self,
        response: BotInTheLoop.response,
        agent_config: ConsultationConfig
    ) -> ExpertAnswerEvent:
        # Optional in Wissensdatenbank speichern
        if agent_config.save_to_knowledge_base:
            await self.save_expert_knowledge(
                question=response.request_event.question,
                answer=response.response,
                expert=response.responder.user_name
            )

        return ExpertAnswerEvent(
            answer=response.response,
            expert_name=response.responder.user_name,
            confidence_score=self.assess_response_quality(response.response)
        )
```

### Mehrstufiger Genehmigungsprozess

**Sequentielle menschliche Prüfpunkte:**

```python
class MultiStageApprovalAgent(Agent):
    @step()
    async def technical_review(
        self,
        event: SubmissionEvent
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=event.user,
            question=f"Technical review: {event.proposal_summary}",
            slack_channel_id="C08TECH123"  # Kanal des technischen Teams
        )

    @step()
    async def business_approval(
        self,
        technical_response: BotInTheLoop.response
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=technical_response.request_event.user,
            question=f"Business approval needed. Technical review: {technical_response.response}",
            slack_channel_id="C08BIZ456"  # Kanal des Business-Teams
        )

    @step()
    async def final_decision(
        self,
        business_response: BotInTheLoop.response
    ) -> FinalDecisionEvent:
        return FinalDecisionEvent(
            approved=self.parse_approval(business_response.response),
            technical_reviewer=business_response.request_event.request_event.responder.user_name,
            business_approver=business_response.responder.user_name
        )
```

## Verfügbare Funktionen

**Agenten-Workflow-Integration:**

-   **Einfacher Aufruf**: Einzeilige Integration mit `BotInTheLoop.invoke()`
-   **Kontexterhaltung**: Vollständiger Workflow-Status über menschliche Interaktionen hinweg beibehalten
-   **Antwortverarbeitung**: Strukturierte Antwortverarbeitung mit Benutzerzuordnung
-   **Fehlerbehandlung**: Timeout-Verwaltung und fehlerfreie Fehlerbehandlung

**Slack-Kanal-Funktionen:**

-   **Thread-basierte Konversationen**: Antworten werden in organisierten Threads erfasst
-   **Multi-Experten-Unterstützung**: Mehrere Experten können an Antworten zusammenarbeiten
-   **Benutzerzuordnung**: Verfolgen, wer jede Antwort für die Verantwortlichkeit gegeben hat
-   **Umfassende Formatierung**: Unterstützung für Slack Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

-   **Asynchrone Verarbeitung**: Nicht-blockierende menschliche Interaktionen mit paralleler Workflow-Unterstützung
-   **Ereignispersistenz**: Vollständiger Konversationsverlauf für Audit und Replay gespeichert
-   **Agentenübergreifende Kommunikation**: Antworten können zwischen verschiedenen Agenten-Workflows geteilt werden
-   **Monitoring-Integration**: Phoenix-Tracing und Observability für menschliche Interaktionsmuster

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

-   **Kanalzugriffskontrolle**: Beschränken Sie den Bot-Zugriff nur auf bestimmte Expertenkanäle
-   **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und den Antworten zugeordnet
-   **Audit-Trails**: Vollständiger Konversationsverlauf für Compliance-Anforderungen beibehalten
-   **Umgang mit sensiblen Daten**: Fragen sollten vermeiden, vertrauliche Informationen in Kanalnachrichten preiszugeben

**Best Practices:**

-   **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten der Expertenkonsultation (technisch, rechtlich, geschäftlich)
-   **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anforderungen, um qualitativ hochwertige Antworten zu erhalten
-   **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Workflows fortgesetzt werden
-   **Timeout-Management**: Legen Sie angemessene Erwartungen an Antwortzeiten fest und behandeln Sie Timeouts elegant
-   **Wissenserfassung**: Erwägen Sie die automatische Speicherung wertvoller Expertenantworten in Wissensdatenbanken

**Leistungsoptimierung:**

-   **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu vermeiden
-   **Batch-Verarbeitung**: Für ähnliche Fragen erwägen Sie die Batch-Verarbeitung von Anfragen, um Expertenunterbrechungen zu reduzieren
-   **Caching**: Häufige Expertenantworten zwischenspeichern, um redundante Fragen zu reduzieren
-   **Eskalationspfade**: Implementieren Sie Eskalationen, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrer AI-Hub-Bereitstellung zu implementieren:

1.  **Slack-Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie sicher, dass Ihr Bot Zugriff auf die dafür vorgesehenen Expertenkanäle hat
2.  **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten zur Beantwortung von Agentenfragen zur Verfügung stehen
3.  **In Agenten-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()`-Muster an Entscheidungspunkten, an denen menschliche Eingaben einen Mehrwert für automatisierte Prozesse schaffen

Für detaillierte Agenten-Integrationsmuster lesen Sie die [Dokumentation zu Experten-Agenten](../../../2_platform/5_agents/3_expert_asking_agent/) für Beispiele aus der Praxis und den AI-Hub Agent Developer's Guide für umfassende Anweisungen zur Workflow-Integration.
