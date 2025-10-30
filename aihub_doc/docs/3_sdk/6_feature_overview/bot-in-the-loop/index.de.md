---
title: Bot-in-the-Loop
source_sha: 67401d06ffdd763bd13969231ae3d1e0ffb5381b315753d32809ff1fcc5409d3
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **Kurz gesagt – Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agenten, **Workflows nahtlos zu pausieren und menschliche Eingaben über Slack-Kanäle
anzufordern**, um die Ausführung dann automatisch mit der menschlichen Antwort fortzusetzen. Dieses Muster überbrückt
die Lücke zwischen autonomer KI-Verarbeitung und menschlichem Fachwissen, wodurch Agenten komplexe Entscheidungen
treffen können, während die vollständige Automatisierung der menschlichen Beteiligung erhalten bleibt.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop stellt ein ausgeklügeltes **Muster für die Zusammenarbeit zwischen Mensch und KI** dar, das es
KI-Agenten ermöglicht, ihre automatisierten Workflows an kritischen Entscheidungspunkten zu unterbrechen und
menschliches Fachwissen nahtlos durch strukturierte Slack-Interaktionen zu integrieren.

Die **Workflow-Integrationsarchitektur** ermöglicht es KI-Agenten, Bot-in-the-Loop zu jedem Zeitpunkt ihrer Ausführung
aufzurufen. Wenn ein Agent auf eine Entscheidung stößt, die menschliche Eingaben, Genehmigungen oder Fachkenntnisse
erfordert, sendet er ein `BotInTheLoopRequestEvent` aus, das automatisch:

- Eine formatierte Frage in einem bestimmten Slack-Kanal postet
- Den vollständigen Workflow-Kontext und die Konversations-Threads beibehält
- Auf eine menschliche Antwort wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agentenausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** bietet die menschliche Schnittstelle durch vertraute Kollaborationstools. Experten
antworten direkt in Slack-Threads, wo:

- Fragen als strukturierte, gethreadete Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antwort verfolgt, wer die Eingabe gemacht hat
- Der Konversationsverlauf für Audit und Lernen erhalten bleibt

Die **ereignisgesteuerte Orchestrierung** steuert die gesamte Interaktion über das Ereignissystem des AI-Hub:

- `BotInTheLoopRequestEvent` Workflows pausiert und in Slack postet
- `BotInTheLoopResponseEvent` Antworten erfasst und Workflows fortsetzt
- Die vollständige Kontexterhaltung eine nahtlose Fortsetzung gewährleistet
- Die Fehlerbehandlung Timeouts und fehlgeschlagene Antworten verwaltet

Die **Agenten-Workflow-Integration** verwendet den einfachen `BotInTheLoop.invoke()` Helfer, der die Integration für
Agentenentwickler trivial macht:

```python
# Pause workflow for human input
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
- **Agent Workflow Engine** – Nahtlose Integration mit den Ausführungsabläufen von KI-Agenten

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop verändert die Art und Weise, wie Unternehmen KI-Automatisierung angehen, indem es die kritische
Herausforderung der Mensch-KI-Zusammenarbeit in großem Maßstab löst:

**🤝 Nahtlose Mensch-KI-Zusammenarbeit**: KI-Agenten können jetzt menschliche Experten auf natürliche Weise einbeziehen,
ohne automatisierte Workflows zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen
über vertraute Slack-Interaktionen, während die KI den vollständigen Kontext beibehält und die Verarbeitung mit
menschlicher Eingabe automatisch fortsetzt.

**⚡ Ununterbrochene Automatisierung**: Im Gegensatz zu traditionellen Systemen, die manuelle Eingriffspunkte erfordern,
gewährleistet Bot-in-the-Loop eine kontinuierliche Automatisierung rund um die menschliche Beteiligung. Agenten
pausieren nur bei Bedarf, fordern spezifische Eingaben an und nehmen die Verarbeitung sofort wieder auf, wodurch sowohl
die Effizienz als auch die Nutzung menschlichen Fachwissens maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können mehrere KI-Workflows gleichzeitig effizient durch
strukturierte Slack-Interaktionen unterstützen. Eine Expertenkonsultation kann mehrere Agenten informieren, und ihr
Wissen wird für das organisationale Lernen und zukünftige Automatisierungsverbesserungen erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern –
Einhaltung gesetzlicher Vorschriften, risikoreiche Genehmigungen oder komplexe Interpretationen – können nahtlos in
ansonsten automatisierte Prozesse integriert werden. Dies gewährleistet sowohl Geschwindigkeit als auch Sicherheit in
KI-gestützten Workflows.

**📚 Erfassung von Organisationswissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst, wodurch ein
ständig wachsendes Repository von Expertenentscheidungen und Wissen entsteht. Dies ermöglicht die kontinuierliche
Verbesserung von KI-Systemen und den Aufbau von institutionellem Wissen, das Personalwechsel überdauert.

::: details **Einrichtung und Nutzung von Bot-in-the-Loop**
## Konfigurationsanforderungen

### Slack Bot-Einrichtung

1. **Azure Bot Service Konfiguration**: Stellen Sie sicher, dass Ihr AI-Hub über eine Azure Bot Service Integration
   verfügt.

   ```bash
   python aihub_bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-ai-hub-bot" \
     --token-url "https://your-aihub-domain.com" \
     --slack-token "xoxb-your-slack-oauth-token"
   ```

2. **Slack App Konfiguration**: Erstellen Sie eine Slack App mit den erforderlichen Berechtigungen.

   - **Bot Token Scopes**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
   - **Ereignis-Abonnements**: Abonnieren Sie `message.channels` Ereignisse
   - **OAuth Installation**: Installieren Sie die App in Ihrem Workspace

3. **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt ist, in denen Sie Fragen posten
   möchten.

   ```
   /invite @YourAIHubBot
   ```

### Agenten-Integrations-Setup

1. **Bot-in-the-Loop Helfer importieren**: Fügen Sie dies zu Ihren Agenten-Imports hinzu.

   ```python
   from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
   ```

2. **Slack Kanal-IDs konfigurieren**: Identifizieren Sie Ihre Slack-Kanal-IDs (Format: `C08MCK6LEBY`).

   ```python
   # Right-click channel → View channel details → Copy channel ID
   EXPERT_CHANNEL_ID = "C08MCK6LEBY"
   ```

3. **NATS Ereignisverteilung**: Stellen Sie sicher, dass Ihre AI-Hub-Bereitstellung für das Ereignis-Routing mit
   NATS-Messaging konfiguriert ist.

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
        # Optionally save to knowledge base
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
            slack_channel_id="C08TECH123"  # Technical team channel
        )
    
    @step()
    async def business_approval(
        self, 
        technical_response: BotInTheLoop.response
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=technical_response.request_event.user,
            question=f"Business approval needed. Technical review: {technical_response.response}",
            slack_channel_id="C08BIZ456"  # Business team channel
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

- **Einfacher Aufruf**: Einzeilige Integration mit `BotInTheLoop.invoke()`
- **Kontexterhaltung**: Vollständiger Workflow-Status wird über menschliche Interaktionen hinweg beibehalten
- **Antwortverarbeitung**: Strukturierte Antwortverarbeitung mit Benutzerzuordnung
- **Fehlerbehandlung**: Timeout-Verwaltung und fehlerverzeihende Fehlerbehandlung

**Slack Kanal-Funktionen:**

- **Gethreadete Konversationen**: Antworten werden in organisierten Threads erfasst
- **Multi-Experten-Unterstützung**: Mehrere Experten können an Antworten zusammenarbeiten
- **Benutzerzuordnung**: Verfolgen Sie, wer jede Antwort für die Rechenschaftspflicht bereitgestellt hat
- **Reichhaltige Formatierung**: Unterstützung für Slack Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

- **Asynchrone Verarbeitung**: Nicht-blockierende menschliche Interaktionen mit paralleler Workflow-Unterstützung
- **Ereignispersistenz**: Vollständiger Konversationsverlauf zur Prüfung und Wiedergabe gespeichert
- **Agentenübergreifende Kommunikation**: Antworten können zwischen verschiedenen Agenten-Workflows geteilt werden
- **Monitoring-Integration**: Phoenix Tracing und Beobachtbarkeit für menschliche Interaktionsmuster

## Sicherheit und Best Practices

**Sicherheitsüberlegungen:**

- **Kanalzugriffskontrolle**: Beschränken Sie den Bot-Zugriff nur auf dafür vorgesehene Expertenkanäle
- **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und den Antworten zugeordnet
- **Audit-Trails**: Vollständiger Konversationsverlauf für Compliance-Anforderungen beibehalten
- **Umgang mit sensiblen Daten**: Fragen sollten vermeiden, vertrauliche Informationen in Kanalnachrichten preiszugeben

**Best Practices:**

- **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten der Expertenkonsultation (technisch,
  rechtlich, geschäftlich)
- **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anfragen, um qualitativ hochwertige
  Antworten zu erhalten
- **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Sie Workflows
  fortsetzen
- **Timeout-Management**: Legen Sie angemessene Erwartungen an die Antwortzeiten fest und behandeln Sie Timeouts elegant
- **Wissenserfassung**: Erwägen Sie, wertvolle Expertenantworten automatisch in Wissensdatenbanken zu speichern

**Leistungsoptimierung:**

- **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu
  vermeiden
- **Batching**: Erwägen Sie bei ähnlichen Fragen, Anfragen zu bündeln, um Expertenunterbrechungen zu reduzieren
- **Caching**: Speichern Sie häufige Expertenantworten zwischen, um redundante Fragen zu reduzieren
- **Eskalationspfade**: Implementieren Sie eine Eskalation, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrer AI-Hub-Bereitstellung zu implementieren:

1. **Slack Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie
   sicher, dass Ihr Bot Zugriff auf die dafür vorgesehenen Expertenkanäle hat
2. **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten zur
   Beantwortung von Agentenfragen zur Verfügung stehen
3. **In Agenten-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()` Muster an
   Entscheidungspunkten, an denen menschliche Eingaben einen Mehrwert für automatisierte Prozesse schaffen

Für detaillierte Agenten-Integrationsmuster lesen Sie die
[Dokumentation für Experten-Agenten](../../../2_platform/5_agents/3_expert_asking_agent/) für praxisnahe
Implementierungsbeispiele und das AI-Hub Agent Developer's Guide für umfassende Anweisungen zur Workflow-Integration.
