---
title: Bot-in-the-Loop
source_sha: c7605d2a66454e9e89d273e81908be389878529a23ec3de6fad705a2aab8596b
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **Kurz gesagt – Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agenten, **Workflows nahtlos zu pausieren und menschliche Eingaben über Slack-Kanäle
anzufordern**, um dann die Ausführung automatisch mit der menschlichen Antwort fortzusetzen. Dieses Muster schließt die
Lücke zwischen autonomer KI-Verarbeitung und menschlichem Fachwissen, wodurch Agenten komplexe Entscheidungen treffen
können, während die vollständige Automatisierung der menschlichen Beteiligung erhalten bleibt.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop repräsentiert ein ausgeklügeltes **Mensch-KI-Kollaborationsmuster**, das es KI-Agenten ermöglicht, ihre
automatisierten Workflows an kritischen Entscheidungspunkten zu pausieren und menschliches Fachwissen nahtlos durch
strukturierte Slack-Interaktionen zu integrieren.

Die **Workflow-Integrationsarchitektur** erlaubt es KI-Agenten, Bot-in-the-Loop zu jedem Zeitpunkt ihrer Ausführung
aufzurufen. Wenn ein Agent auf eine Entscheidung stößt, die menschliche Eingaben, Genehmigungen oder Fachwissen
erfordert, emittiert er ein `BotInTheLoopRequestEvent`, das automatisch:

- Eine formatierte Frage in einem bestimmten Slack-Kanal postet
- Den vollständigen Workflow-Kontext und die Konversations-Threads beibehält
- Auf menschliche Antworten wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agentenausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** stellt die menschliche Schnittstelle über vertraute Kollaborationstools bereit. Experten
antworten direkt in Slack-Threads, wo:

- Fragen als strukturierte, gethreadete Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antwort verfolgt, wer die Eingabe bereitgestellt hat
- Der Konversationsverlauf für Audit und Lernen beibehalten wird

Die **ereignisgesteuerte Orchestrierung** treibt die gesamte Interaktion über das Ereignissystem des Swiss AI Hub an:

- `BotInTheLoopRequestEvent` pausiert Workflows und postet in Slack
- `BotInTheLoopResponseEvent` erfasst Antworten und setzt Workflows fort
- Vollständige Kontexterhaltung gewährleistet eine nahtlose Fortsetzung
- Die Fehlerbehandlung verwaltet Timeouts und fehlgeschlagene Antworten

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

- **NATS Event System** – Asynchrone Nachrichtenweiterleitung und Workflow-Orchestrierung
- **Slack Bot Framework** – Kanalintegration mit Threading und Attribution
- **Azure Bot Service** – Multi-Kanal-Bot-Konnektivität und Nachrichtenverarbeitung
- **Event Store** – Persistenter Kontext und Konversationsverfolgung
- **Agent Workflow Engine** – Nahtlose Integration in die Ausführungsabläufe von KI-Agenten

## Warum dies ein Game-Changer für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop transformiert die Art und Weise, wie Organisationen die KI-Automatisierung angehen, indem es die
kritische Herausforderung der Mensch-KI-Kollaboration im großen Maßstab löst:

**🤝 Nahtlose Mensch-KI-Kollaboration**: KI-Agenten können jetzt menschliche Experten auf natürliche Weise einbeziehen,
ohne automatisierte Workflows zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen
über vertraute Slack-Interaktionen, während die KI den vollständigen Kontext beibehält und die Verarbeitung mit
menschlicher Eingabe automatisch fortsetzt.

**⚡ Unterbrechungsfreie Automatisierung**: Im Gegensatz zu traditionellen Systemen, die manuelle Eingriffspunkte
erfordern, gewährleistet Bot-in-the-Loop eine kontinuierliche Automatisierung rund um die menschliche Beteiligung.
Agenten pausieren nur bei Bedarf, fordern spezifische Eingaben an und setzen die Verarbeitung sofort fort, wodurch
sowohl die Effizienz als auch die Nutzung menschlichen Fachwissens maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können mehrere KI-Workflows gleichzeitig effizient über
strukturierte Slack-Interaktionen unterstützen. Eine Expertenkonsultation kann mehrere Agenten informieren, und ihr
Wissen wird für das organisatorische Lernen und zukünftige Automatisierungsverbesserungen erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern –
Einhaltung von Vorschriften, hochrangige Genehmigungen oder komplexe Interpretationen – können nahtlos in ansonsten
automatisierte Prozesse integriert werden. Dies gewährleistet sowohl Geschwindigkeit als auch Sicherheit in
KI-gestützten Workflows.

**📚 Erfassung von Organisationswissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst, wodurch ein
ständig wachsendes Repository von Expertenentscheidungen und -wissen entsteht. Dies ermöglicht die kontinuierliche
Verbesserung von KI-Systemen und den Aufbau von institutionellem Wissen, das Personalwechsel überdauert.

::: details **Bot-in-the-Loop einrichten und verwenden**
## Konfigurationsanforderungen

### Slack Bot-Setup

1. **Azure Bot Service Konfiguration**: Stellen Sie sicher, dass Ihr Swiss AI Hub über eine konfigurierte Azure Bot
   Service-Integration verfügt

   ```bash
   python packages/bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-swiss-ai-hub-bot" \
     --token-url "https://your-swiss-ai-hub-domain.com" \
     --slack-token "xoxb-your-slack-oauth-token"
   ```

2. **Slack App-Konfiguration**: Erstellen Sie eine Slack-App mit den erforderlichen Berechtigungen

   - **Bot Token Scopes**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
   - **Event Subscriptions**: Abonnieren Sie `message.channels`-Events
   - **OAuth Installation**: Installieren Sie die App in Ihrem Workspace

3. **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt wird, in denen Sie Fragen stellen
   möchten

   ```
   /invite @YourAIHubBot
   ```

### Agenten-Integrations-Setup

1. **Bot-in-the-Loop-Helfer importieren**: Fügen Sie dies Ihren Agenten-Importen hinzu

   ```python
   from swiss_ai_hub.core.events.agent.bitl import BotInTheLoop
   ```

2. **Slack-Kanal-IDs konfigurieren**: Identifizieren Sie Ihre Slack-Kanal-IDs (Format: `C08MCK6LEBY`)

   ```python
   # Right-click channel → View channel details → Copy channel ID
   EXPERT_CHANNEL_ID = "C08MCK6LEBY"
   ```

3. **NATS Ereignisverteilung**: Stellen Sie sicher, dass Ihr Swiss AI Hub Deployment NATS-Messaging für das
   Event-Routing konfiguriert hat

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

**Sequenzielle menschliche Checkpoints:**

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
- **Kontexterhaltung**: Voller Workflow-Status über menschliche Interaktionen hinweg beibehalten
- **Antwortverarbeitung**: Strukturierte Antwortbearbeitung mit Benutzerzuordnung
- **Fehlerbehandlung**: Timeout-Management und graceful Failure Handling

**Slack-Kanal-Funktionen:**

- **Gethreadete Konversationen**: Antworten werden in organisierten Threads erfasst
- **Multi-Experten-Unterstützung**: Mehrere Experten können an Antworten zusammenarbeiten
- **Benutzerzuordnung**: Verfolgt, wer jede Antwort für die Rechenschaftspflicht bereitgestellt hat
- **Umfassende Formatierung**: Unterstützung für Slack-Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

- **Asynchrone Verarbeitung**: Nicht-blockierende menschliche Interaktionen mit paralleler Workflow-Unterstützung
- **Ereignispersistenz**: Vollständiger Konversationsverlauf für Audit und Wiedergabe gespeichert
- **Agentenübergreifende Kommunikation**: Antworten können zwischen verschiedenen Agenten-Workflows geteilt werden
- **Monitoring-Integration**: Langfuse-Tracing und -Observability für Interaktionsmuster mit Menschen

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Kanalzugriffssteuerung**: Bot-Zugriff nur auf bestimmte Expertenkanäle beschränken
- **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und Antworten zugeordnet
- **Audit-Trails**: Vollständiger Konversationsverlauf für Compliance-Anforderungen beibehalten
- **Umgang mit sensiblen Daten**: Fragen sollten die Offenlegung vertraulicher Informationen in Kanalnachrichten
  vermeiden

**Best Practices:**

- **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten von Expertenkonsultationen (technisch,
  rechtlich, geschäftlich)
- **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anforderungen, um qualitativ
  hochwertige Antworten zu erhalten
- **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Sie Workflows
  fortsetzen
- **Timeout-Management**: Legen Sie angemessene Erwartungen an Antwortzeiten fest und behandeln Sie Timeouts graceful
- **Wissenserfassung**: Erwägen Sie die automatische Speicherung wertvoller Expertenantworten in Wissensdatenbanken

**Leistungsoptimierung:**

- **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu
  vermeiden
- **Batching**: Erwägen Sie bei ähnlichen Fragen das Batching von Anfragen, um die Unterbrechung von Experten zu
  reduzieren
- **Caching**: Häufige Expertenantworten zwischenspeichern, um redundante Fragen zu reduzieren
- **Eskalationspfade**: Implementieren Sie Eskalationen, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrem Swiss AI Hub Deployment zu implementieren:

1. **Slack-Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie
   sicher, dass Ihr Bot Zugriff auf die vorgesehenen Expertenkanäle hat
2. **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten für die
   Beantwortung von Agentenfragen zur Verfügung stehen
3. **In Agenten-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()` Muster an
   Entscheidungspunkten, an denen menschliche Eingaben einen Mehrwert für automatisierte Prozesse schaffen

Für detaillierte Agenten-Integrationsmuster lesen Sie die
[Dokumentation zu Experten-Agenten](../../../2_platform/5_agents/9_expert_coordinator_agent/) für Beispiele aus der
Praxis und das Swiss AI Hub Agenten-Entwicklerhandbuch für umfassende Anweisungen zur Workflow-Integration.
