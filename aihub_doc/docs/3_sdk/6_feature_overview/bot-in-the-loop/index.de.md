---
title: Bot-in-the-Loop
source_sha: 1335ce35efc84caecfd66496a26ed0ae893d0e408e02ecbb521a01c4b88b3772
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **TL;DR – Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agenten, **Workflows nahtlos zu pausieren und menschliche Eingaben über Slack-Kanäle
anzufordern**, um dann die Ausführung mit der menschlichen Antwort automatisch fortzusetzen. Dieses Muster überbrückt
die Lücke zwischen autonomer KI-Verarbeitung und menschlicher Expertise, wodurch Agenten komplexe Entscheidungen treffen
können, während die volle Automatisierung rund um die menschliche Beteiligung erhalten bleibt.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop stellt ein hochentwickeltes **Muster der Mensch-KI-Zusammenarbeit** dar, das es KI-Agenten ermöglicht,
ihre automatisierten Workflows an kritischen Entscheidungspunkten zu unterbrechen und menschliche Expertise nahtlos
durch strukturierte Slack-Interaktionen zu integrieren.

Die **Architektur der Workflow-Integration** erlaubt KI-Agenten, Bot-in-the-Loop an jedem Punkt ihrer Ausführung
aufzurufen. Wenn ein Agent auf eine Entscheidung stößt, die menschliche Eingabe, Genehmigung oder Expertise erfordert,
sendet er ein \`BotInTheLoopRequestEvent aus, das automatisch:

- Eine formatierte Frage in einem bestimmten Slack-Kanal postet
- Den vollständigen Workflow-Kontext und die Konversationsverlauf beibehält
- Auf menschliche Antwort wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agentenausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** stellt die menschliche Schnittstelle über vertraute Kollaborationstools bereit. Experten
antworten direkt in Slack-Threads, wo:

- Fragen als strukturierte, Thread-basierte Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antwort verfolgt, wer die Eingabe bereitgestellt hat
- Der Konversationsverlauf für Audits und Lernzwecke beibehalten wird

Die **ereignisgesteuerte Orchestrierung** treibt die gesamte Interaktion über das Ereignissystem des AI-Hubs an:

- `BotInTheLoopRequestEvent` unterbricht Workflows und postet an Slack
- `BotInTheLoopResponseEvent` erfasst Antworten und setzt Workflows fort
- Die vollständige Kontexterhaltung gewährleistet eine nahtlose Fortsetzung
- Die Fehlerbehandlung verwaltet Timeouts und fehlgeschlagene Antworten

Die **Agenten-Workflow-Integration** verwendet den einfachen `BotInTheLoop.invoke()`-Helfer, der die Integration für
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
- **Slack Bot Framework** – Kanal-Integration mit Threading und Zuordnung
- **Azure Bot Service** – Multi-Kanal-Bot-Konnektivität und Nachrichtenverarbeitung
- **Event Store** – Persistenter Kontext und Konversationsverfolgung
- **Agent Workflow Engine** – Nahtlose Integration mit den Ausführungsabläufen von KI-Agenten

## Warum dies ein Wegbereiter für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop verändert, wie Organisationen KI-Automatisierung angehen, indem es die kritische Herausforderung der
Mensch-KI-Zusammenarbeit im großen Maßstab löst:

**🤝 Nahtlose Mensch-KI-Zusammenarbeit**: KI-Agenten können jetzt menschliche Experten auf natürliche Weise einbeziehen,
ohne automatisierte Workflows zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen
über vertraute Slack-Interaktionen, während die KI den vollständigen Kontext beibehält und die Verarbeitung mit
menschlicher Eingabe automatisch fortsetzt.

**⚡ Ununterbrochene Automatisierung**: Im Gegensatz zu traditionellen Systemen, die manuelle Eingriffspunkte erfordern,
gewährleistet Bot-in-the-Loop eine kontinuierliche Automatisierung rund um die menschliche Beteiligung. Agenten
pausieren nur bei Bedarf, fordern spezifische Eingaben an und nehmen die Verarbeitung sofort wieder auf, wodurch sowohl
die Effizienz als auch die Nutzung menschlicher Expertise maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können effizient mehrere KI-Workflows gleichzeitig durch
strukturierte Slack-Interaktionen unterstützen. Eine Expertenkonsultation kann mehrere Agenten informieren, und ihr
Wissen wird für organisationales Lernen und zukünftige Automatisierungsverbesserungen erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern –
behördliche Compliance, risikoreiche Genehmigungen oder komplexe Interpretationen – können nahtlos in ansonsten
automatisierte Prozesse integriert werden. Dies gewährleistet sowohl Geschwindigkeit als auch Sicherheit in
KI-gesteuerten Workflows.

**📚 Erfassung von organisationalem Wissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst und schafft
so ein stetig wachsendes Repository an Expertenentscheidungen und -wissen. Dies ermöglicht die kontinuierliche
Verbesserung von KI-Systemen und baut institutionelles Wissen auf, das Personalwechsel überdauert.

::: details **Einrichtung und Verwendung von Bot-in-the-Loop**
## Konfigurationsanforderungen

### Slack Bot Einrichtung

1. **Azure Bot Service Konfiguration**: Stellen Sie sicher, dass Ihr AI-Hub eine Azure Bot Service-Integration
   konfiguriert hat

   ```bash
   python aihub_bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-ai-hub-bot" \
     --token-url "https://your-aihub-domain.com" \
     --slack-token "xoxb-your-slack-oauth-token"
   ```

2. **Slack App Konfiguration**: Erstellen Sie eine Slack-App mit den erforderlichen Berechtigungen

   - **Bot Token Scopes**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
   - **Event Subscriptions**: Abonnieren Sie `message.channels`-Ereignisse
   - **OAuth Installation**: Installieren Sie die App in Ihrem Workspace

3. **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt wurde, in denen Sie Fragen
   stellen möchten

   ```
   /invite @YourAIHubBot
   ```

### Agenten-Integrations-Setup

1. **Bot-in-the-Loop Helfer importieren**: Fügen Sie dies Ihren Agenten-Imports hinzu

   ```python
   from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
   ```

2. **Slack-Kanal-IDs konfigurieren**: Identifizieren Sie Ihre Slack-Kanal-IDs (Format: `C08MCK6LEBY`)

   ```python
   # Right-click channel → View channel details → Copy channel ID
   EXPERT_CHANNEL_ID = "C08MCK6LEBY"
   ```

3. **NATS Ereignisverteilung**: Stellen Sie sicher, dass Ihre AI-Hub-Bereitstellung für das Ereignis-Routing
   NATS-Messaging konfiguriert hat

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

### Workflow für Expertenkonsultation

**Wissensbeschaffungs-Muster:**

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

**Sequenzielle menschliche Prüfpunkte:**

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
- **Kontexterhaltung**: Vollständiger Workflow-Zustand wird über menschliche Interaktionen hinweg beibehalten
- **Antwortverarbeitung**: Strukturierte Antwortverarbeitung mit Benutzerzuordnung
- **Fehlerbehandlung**: Timeout-Verwaltung und elegante Fehlerbehandlung

**Slack-Kanal-Funktionen:**

- **Thread-basierte Konversationen**: Antworten werden in organisierten Threads erfasst
- **Unterstützung mehrerer Experten**: Mehrere Experten können an Antworten zusammenarbeiten
- **Benutzerzuordnung**: Verfolgen Sie, wer jede Antwort für die Rechenschaftspflicht bereitgestellt hat
- **Umfangreiche Formatierung**: Unterstützung für Slack-Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

- **Asynchrone Verarbeitung**: Nicht-blockierende menschliche Interaktionen mit paralleler Workflow-Unterstützung
- **Ereignispersistenz**: Vollständiger Konversationsverlauf für Audit und Replay gespeichert
- **Agentenübergreifende Kommunikation**: Antworten können zwischen verschiedenen Agenten-Workflows geteilt werden
- **Monitoring-Integration**: Langfuse-Tracing und Observability für menschliche Interaktionsmuster

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Kanalzugriffskontrolle**: Beschränken Sie den Bot-Zugriff nur auf zugewiesene Expertenkanäle
- **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und den Antworten zugeordnet
- **Audit-Trails**: Vollständiger Konversationsverlauf für Compliance-Anforderungen beibehalten
- **Umgang mit sensiblen Daten**: Fragen sollten vermeiden, vertrauliche Informationen in Kanalnachrichten preiszugeben

**Best Practices:**

- **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten von Expertenkonsultationen (technisch,
  rechtlich, geschäftlich)
- **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anforderungen, um qualitativ
  hochwertige Antworten zu erhalten
- **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Workflows
  fortgesetzt werden
- **Timeout-Verwaltung**: Legen Sie angemessene Erwartungen an die Antwortzeiten fest und behandeln Sie Timeouts elegant
- **Wissenserfassung**: Erwägen Sie, wertvolle Expertenantworten automatisch in Wissensdatenbanken zu speichern

**Leistungsoptimierung:**

- **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu
  vermeiden
- **Batching**: Für ähnliche Fragen sollten Sie in Erwägung ziehen, Anfragen zu bündeln, um Expertenunterbrechungen zu
  reduzieren
- **Caching**: Speichern Sie häufige Expertenantworten im Cache, um redundante Fragen zu reduzieren
- **Eskalationspfade**: Implementieren Sie eine Eskalation, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrer AI-Hub-Bereitstellung zu implementieren:

1. **Slack-Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie
   sicher, dass Ihr Bot Zugriff auf zugewiesene Expertenkanäle hat
2. **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten für die
   Beantwortung von Agentenfragen zur Verfügung stehen
3. **In Agenten-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()`-Muster an
   Entscheidungspunkten, an denen menschliche Eingaben einen Mehrwert für automatisierte Prozesse bieten

Für detaillierte Agenten-Integrationsmuster lesen Sie die
[Dokumentation für Experten-Agenten](../../../2_platform/5_agents/3_expert_asking_agent/) für Beispiele aus der Praxis
und den AI-Hub Agent Developer's Guide für umfassende Anweisungen zur Workflow-Integration.
