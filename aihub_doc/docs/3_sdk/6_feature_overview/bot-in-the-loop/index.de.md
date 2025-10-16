---
title: Bot-in-the-Loop
index: 4
source_sha: "72215edac05b9bd75ed5999a8027a1a0386b56b73db2b33808b943c7d411de9a"
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **TL;DR - Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agenten, **Arbeitsabläufe nahtlos zu pausieren und menschliche Eingaben über Slack-Kanäle anzufordern**, und die Ausführung dann
automatisch mit der menschlichen Antwort fortzusetzen. Dieses Muster überbrückt die Lücke zwischen autonomer KI-Verarbeitung
und menschlichem Fachwissen und ermöglicht es Agenten, komplexe Entscheidungen zu treffen, während die vollständige Automatisierung rund um die menschliche
Beteiligung aufrechterhalten wird.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop stellt ein ausgeklügeltes **Mensch-KI-Kollaborationsmuster** dar, das es KI-Agenten ermöglicht, ihre
automatisierten Arbeitsabläufe an kritischen Entscheidungspunkten zu pausieren und menschliches Fachwissen nahtlos über strukturierte Slack-Interaktionen zu integrieren.

Die **Architektur für die Workflow-Integration** ermöglicht es KI-Agenten, Bot-in-the-Loop an jedem Punkt ihrer Ausführung aufzurufen. Wenn
ein Agent auf eine Entscheidung stößt, die menschliche Eingabe, Genehmigung oder Fachwissen erfordert, sendet er ein `BotInTheLoopRequestEvent` aus, das
automatisch:

- Eine formatierte Frage an einen bestimmten Slack-Kanal sendet
- Den vollständigen Workflow-Kontext und die Konversations-Threads beibehält
- Auf menschliche Antwort wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agenten-Ausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** stellt die menschliche Schnittstelle über vertraute Kollaborationstools bereit. Experten antworten
direkt in Slack-Threads, wo:

- Fragen als strukturierte, geordnete Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antworten verfolgt, wer die Eingabe gemacht hat
- Der Konversationsverlauf für Audit und Lernen beibehalten wird

Die **Ereignisgesteuerte Orchestrierung** treibt die gesamte Interaktion über das Ereignissystem des AI-Hubs an:

- `BotInTheLoopRequestEvent` pausiert Workflows und postet an Slack
- `BotInTheLoopResponseEvent` erfasst Antworten und setzt Workflows fort
- Volle Kontextbewahrung gewährleistet nahtlose Fortsetzung
- Fehlerbehandlung verwaltet Timeouts und fehlgeschlagene Antworten

Die **Agenten-Workflow-Integration** nutzt den einfachen `BotInTheLoop.invoke()` Helfer, der die Integration für Agentenentwickler trivial macht:

```python
# Workflow für menschliche Eingabe pausieren
return BotInTheLoop.invoke(
    user=current_user,
    question="Should I proceed with this high-risk operation?",
    slack_channel_id="C08MCK6LEBY"
)
```

**Schlüsseltechnologien:**

- **NATS Event System** – Asynchrones Nachrichten-Routing und Workflow-Orchestrierung
- **Slack Bot Framework** – Kanalintegration mit Threading und Zuordnung
- **Azure Bot Service** – Multi-Kanal-Bot-Konnektivität und Nachrichtenverarbeitung
- **Event Store** – Persistenter Kontext und Konversationsverfolgung
- **Agent Workflow Engine** – Nahtlose Integration in die Ausführungsabläufe von KI-Agenten

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop transformiert die Art und Weise, wie Organisationen die KI-Automatisierung angehen, indem es die kritische Herausforderung der Mensch-KI-Kollaboration
in großem Maßstab löst:

**🤝 Nahtlose Mensch-KI-Kollaboration**: KI-Agenten können nun menschliche Experten auf natürliche Weise einbeziehen, ohne automatisierte
Arbeitsabläufe zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen über vertraute Slack-Interaktionen, während die
KI den vollständigen Kontext beibehält und die Verarbeitung mit menschlicher Eingabe automatisch fortsetzt.

**⚡ Unterbrechungsfreie Automatisierung**: Im Gegensatz zu herkömmlichen Systemen, die manuelle Eingriffspunkte erfordern,
gewährleistet Bot-in-the-Loop eine kontinuierliche Automatisierung um die menschliche Beteiligung herum. Agenten pausieren nur bei Bedarf, fordern spezifische Eingaben an und
setzen die Verarbeitung sofort fort, wodurch sowohl Effizienz als auch die Nutzung menschlichen Fachwissens maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können effizient mehrere KI-Workflows gleichzeitig über strukturierte Slack-Interaktionen unterstützen.
Eine Expertenkonsultation kann mehrere Agenten informieren, und ihr Wissen wird für organisationales Lernen und zukünftige Verbesserungen der Automatisierung erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern – wie die Einhaltung gesetzlicher Vorschriften, hochrangige Genehmigungen
oder komplexe Interpretationen – können nahtlos in ansonsten automatisierte Prozesse integriert werden. Dies gewährleistet sowohl
Geschwindigkeit als auch Sicherheit in KI-gestützten Arbeitsabläufen.

**📚 Erfassung von Unternehmenswissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst, wodurch ein stetig wachsendes
Repository von Expertenentscheidungen und -wissen entsteht. Dies ermöglicht die kontinuierliche Verbesserung von KI-Systemen
und baut institutionelles Wissen auf, das Personalwechsel überdauert.

::: details **Einrichtung und Nutzung von Bot-in-the-Loop**
## Konfigurationsanforderungen

### Slack Bot-Einrichtung

1.  **Azure Bot Service-Konfiguration**: Stellen Sie sicher, dass Ihr AI-Hub über eine konfigurierte Azure Bot Service-Integration verfügt

    ```bash
    python aihub_bot/setup_azure_bot.py \
      --resource-group "your-resource-group" \
      --bot-name "your-ai-hub-bot" \
      --token-url "https://your-aihub-domain.com" \
      --slack-token "xoxb-your-slack-oauth-token"
    ```

2.  **Slack App-Konfiguration**: Erstellen Sie eine Slack App mit erforderlichen Berechtigungen

    - **Bot-Token-Berechtigungen**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
    - **Ereignis-Abonnements**: Abonnieren Sie `message.channels`-Ereignisse
    - **OAuth-Installation**: Installieren Sie die App in Ihrem Workspace

3.  **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt ist, in denen Sie Fragen posten möchten

    ```
    /invite @YourAIHubBot
    ```

### Agenten-Integrationseinrichtung

1.  **Bot-in-the-Loop Helper importieren**: Fügen Sie es zu Ihren Agenten-Importen hinzu

    ```python
    from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
    ```

2.  **Slack-Kanal-IDs konfigurieren**: Identifizieren Sie Ihre Slack-Kanal-IDs (Format: `C08MCK6LEBY`)

    ```python
    # Rechtsklick auf Kanal → Kanaldetails anzeigen → Kanal-ID kopieren
    EXPERT_CHANNEL_ID = "C08MCK6LEBY"
    ```

3.  **NATS-Ereignisverteilung**: Stellen Sie sicher, dass Ihr AI-Hub-Deployment für das Ereignis-Routing über NATS Messaging konfiguriert ist

## Anwendungsbeispiele

### Grundlegende Agenten-Integration

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

**Wissenssuchendes Muster:**

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
            slack_channel_id="C08TECH123"  # Technisches Team-Kanal
        )
    
    @step()
    async def business_approval(
        self, 
        technical_response: BotInTheLoop.response
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=technical_response.request_event.user,
            question=f"Business approval needed. Technical review: {technical_response.response}",
            slack_channel_id="C08BIZ456"  # Business Team-Kanal
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
-   **Kontextbewahrung**: Vollständiger Workflow-Status wird über menschliche Interaktionen hinweg beibehalten
-   **Antwortverarbeitung**: Strukturierte Antwortverarbeitung mit Benutzerzuordnung
-   **Fehlerbehandlung**: Timeout-Verwaltung und elegante Fehlerbehandlung

**Slack-Kanal-Funktionen:**

-   **Geordnete Konversationen**: Antworten werden in organisierten Threads erfasst
-   **Multi-Experten-Unterstützung**: Mehrere Experten können an Antworten zusammenarbeiten
-   **Benutzerzuordnung**: Verfolgen Sie, wer jede Antwort für die Rechenschaftspflicht bereitgestellt hat
-   **Umfangreiche Formatierung**: Unterstützung für Slack Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

-   **Asynchrone Verarbeitung**: Nicht-blockierende menschliche Interaktionen mit paralleler Workflow-Unterstützung
-   **Ereignispersistenz**: Vollständiger Konversationsverlauf für Audit und Replay gespeichert
-   **Agentenübergreifende Kommunikation**: Antworten können zwischen verschiedenen Agenten-Workflows geteilt werden
-   **Monitoring-Integration**: Phoenix Tracing und Observability für menschliche Interaktionsmuster

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

-   **Kanalzugriffskontrolle**: Beschränken Sie den Bot-Zugriff nur auf ausgewiesene Expertenkanäle
-   **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und den Antworten zugeordnet
-   **Audit-Trails**: Vollständiger Konversationsverlauf für Compliance-Anforderungen beibehalten
-   **Umgang mit sensiblen Daten**: Fragen sollten vermeiden, vertrauliche Informationen in Kanalnachrichten preiszugeben

**Best Practices:**

-   **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten von Expertenkonsultationen (technisch, rechtlich, geschäftlich)
-   **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anfragen, um qualitativ hochwertige Antworten zu erhalten
-   **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Workflows fortgesetzt werden
-   **Timeout-Management**: Setzen Sie angemessene Erwartungen an die Antwortzeiten und behandeln Sie Timeouts elegant
-   **Wissenserfassung**: Erwägen Sie, wertvolle Expertenantworten automatisch in Wissensdatenbanken zu speichern

**Leistungsoptimierung:**

-   **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu vermeiden
-   **Batch-Verarbeitung**: Erwägen Sie bei ähnlichen Fragen die Batch-Verarbeitung von Anfragen, um Expertenunterbrechungen zu reduzieren
-   **Caching**: Cachen Sie gängige Expertenantworten, um redundante Fragen zu reduzieren
-   **Eskalationspfade**: Implementieren Sie eine Eskalation, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrer AI-Hub-Bereitstellung zu implementieren:

1.  **Slack-Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie sicher, dass Ihr Bot Zugriff auf die dafür vorgesehenen Expertenkanäle hat
2.  **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten für die Beantwortung von Agentenfragen zur Verfügung stehen
3.  **In Agenten-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()`-Muster an Entscheidungspunkten, wo menschliche Eingaben automatisierten Prozessen einen Mehrwert verleihen

Detaillierte Agenten-Integrationsmuster finden Sie in der [Expert Agents Dokumentation](../expert-agents/) für praktische Implementierungsbeispiele,
sowie im AI-Hub Agent Developer's Guide für umfassende Anweisungen zur Workflow-Integration.
