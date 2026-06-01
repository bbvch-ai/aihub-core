---
title: Bot-in-the-Loop
source_sha: d3279c4d643b5e2e9a58c611463b78783d2538041d99a9b64d0e6572441ef9a4
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **TL;DR – Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agents, **Workflows nahtlos zu pausieren und menschliche Eingaben über Slack-Kanäle
anzufordern**, um dann die Ausführung mit der menschlichen Antwort automatisch fortzusetzen. Dieses Muster überbrückt
die Lücke zwischen autonomer KI-Verarbeitung und menschlichem Fachwissen, wodurch Agents komplexe Entscheidungen treffen
können, während die vollständige Automatisierung rund um die menschliche Beteiligung erhalten bleibt.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop repräsentiert ein ausgeklügeltes **Mensch-KI-Kollaborationsmuster**, das es KI-Agents ermöglicht, ihre
automatisierten Workflows an kritischen Entscheidungspunkten zu pausieren und menschliches Fachwissen nahtlos durch
strukturierte Slack-Interaktionen zu integrieren.

Die **Workflow-Integrationsarchitektur** ermöglicht es KI-Agents, Bot-in-the-Loop an jedem Punkt ihrer Ausführung
aufzurufen. Wenn ein Agent auf eine Entscheidung trifft, die menschliche Eingabe, Genehmigung oder Fachwissen erfordert,
sendet er ein `BotInTheLoopRequestEvent` aus, das automatisch:

- Eine formatierte Frage in einem zugewiesenen Slack-Kanal postet
- Den vollständigen Workflow-Kontext und das Konversations-Threading beibehält
- Auf menschliche Antwort wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agent-Ausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** bietet die menschliche Schnittstelle über vertraute Kollaborationstools. Experten
antworten direkt in Slack-Threads, wo:

- Fragen als strukturierte, gethreadete Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antwort nachverfolgt, wer die Eingabe gemacht hat
- Der Konversationsverlauf für Audit und Lernen beibehalten wird

Die **Ereignisgesteuerte Orchestrierung** treibt die gesamte Interaktion über das Ereignissystem des Swiss AI Hub an:

- `BotInTheLoopRequestEvent` Workflows pausiert und in Slack postet
- `BotInTheLoopResponseEvent` Antworten erfasst und Workflows fortsetzt
- Die vollständige Kontextbewahrung sorgt für eine nahtlose Fortsetzung
- Die Fehlerbehandlung verwaltet Timeouts und fehlgeschlagene Antworten

Die **Agent-Workflow-Integration** nutzt den einfachen `BotInTheLoop.invoke()`-Helfer, der die Integration für
Agent-Entwickler trivial macht:

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
- **Agent Workflow Engine** – Nahtlose Integration mit den Ausführungsabläufen von KI-Agents

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop verändert, wie Organisationen KI-Automatisierung angehen, indem es die kritische Herausforderung der
Mensch-KI-Kollaboration im großen Maßstab löst:

**🤝 Nahtlose Mensch-KI-Kollaboration**: KI-Agents können jetzt menschliche Experten auf natürliche Weise einbeziehen,
ohne automatisierte Workflows zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen
über vertraute Slack-Interaktionen, während die KI den vollständigen Kontext beibehält und die Verarbeitung mit
menschlicher Eingabe automatisch fortsetzt.

**⚡ Unterbrechungsfreie Automatisierung**: Im Gegensatz zu traditionellen Systemen, die manuelle Eingriffspunkte
erfordern, sorgt Bot-in-the-Loop für eine kontinuierliche Automatisierung rund um die menschliche Beteiligung. Agents
pausieren nur bei Bedarf, fordern spezifische Eingaben an und setzen die Verarbeitung sofort fort, wodurch sowohl die
Effizienz als auch die Nutzung menschlichen Fachwissens maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können effizient mehrere KI-Workflows gleichzeitig über
strukturierte Slack-Interaktionen unterstützen. Eine Expertenkonsultation kann mehrere Agents informieren, und ihr
Wissen wird für das organisationale Lernen und zukünftige Automatisierungsverbesserungen erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern –
regulatorische Compliance, hochriskante Genehmigungen oder komplexe Interpretationen – können nahtlos in ansonsten
automatisierte Prozesse integriert werden. Dies gewährleistet sowohl Geschwindigkeit als auch Sicherheit in
KI-gestützten Workflows.

**📚 Erfassung von Organisationswissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst und schafft so
ein ständig wachsendes Repository an Expertenentscheidungen und Wissen. Dies ermöglicht eine kontinuierliche
Verbesserung von KI-Systemen und baut institutionelles Wissen auf, das Personalwechsel überdauert.

::: details **Einrichtung und Nutzung von Bot-in-the-Loop**
## Konfigurationsanforderungen

### Slack Bot-Einrichtung

1. **Azure Bot Service-Konfiguration**: Stellen Sie sicher, dass Ihr Swiss AI Hub über eine konfigurierte Azure Bot
   Service-Integration verfügt

   ```bash
   python packages/bot/setup_azure_bot.py \
     --resource-group "your-resource-group" \
     --bot-name "your-swiss-ai-hub-bot" \
     --token-url "https://your-swiss-ai-hub-domain.com" \
     --slack-token "xoxb-your-slack-oauth-token"
   ```

2. **Slack App-Konfiguration**: Erstellen Sie eine Slack App mit den erforderlichen Berechtigungen

   - **Bot Token Scopes**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
   - **Event Subscriptions**: Abonnieren Sie `message.channels`-Ereignisse
   - **OAuth Installation**: Installieren Sie die App in Ihrem Workspace

3. **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt wird, in denen Sie Fragen posten
   möchten

   ```
   /invite @YourAIHubBot
   ```

### Agent-Integrations-Setup

1. **Importieren des Bot-in-the-Loop Helfers**: Fügen Sie es Ihren Agent-Imports hinzu

   ```python
   from swiss_ai_hub.core.events.agent.bitl import BotInTheLoop
   ```

2. **Slack-Kanal-IDs konfigurieren**: Identifizieren Sie Ihre Slack-Kanal-IDs (Format: `C08MCK6LEBY`)

   ```python
   # Rechtsklick auf Kanal → Kanaldetails anzeigen → Kanal-ID kopieren
   EXPERT_CHANNEL_ID = "C08MCK6LEBY"
   ```

3. **NATS-Ereignisverteilung**: Stellen Sie sicher, dass Ihr Swiss AI Hub Deployment NATS-Messaging für das
   Ereignis-Routing konfiguriert hat

## Anwendungsbeispiele

### Grundlegende Agent-Integration

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

**Agent-Workflow-Integration:**

- **Einfacher Aufruf**: Einzeilige Integration mit `BotInTheLoop.invoke()`
- **Kontextbewahrung**: Voller Workflow-Status wird über menschliche Interaktionen hinweg beibehalten
- **Antwortverarbeitung**: Strukturierte Antwortverarbeitung mit Benutzerzuordnung
- **Fehlerbehandlung**: Timeout-Management und graceful Failure Handling

**Slack-Kanal-Funktionen:**

- **Gethreadete Konversationen**: Antworten werden in organisierten Threads erfasst
- **Multi-Experten-Unterstützung**: Mehrere Experten können an Antworten zusammenarbeiten
- **Benutzerzuordnung**: Verfolgen Sie, wer welche Antwort zur Rechenschaftspflicht gegeben hat
- **Umfangreiche Formatierung**: Unterstützung für Slack Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

- **Asynchrone Verarbeitung**: Nicht blockierende menschliche Interaktionen mit paralleler Workflow-Unterstützung
- **Ereignispersistenz**: Vollständiger Konversationsverlauf für Audit und Replay gespeichert
- **Agent-übergreifende Kommunikation**: Antworten können zwischen verschiedenen Agent-Workflows geteilt werden
- **Monitoring-Integration**: Langfuse Tracing und Observability für menschliche Interaktionsmuster

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Kanalzugriffskontrolle**: Beschränken Sie den Bot-Zugriff nur auf zugewiesene Expertenkanäle
- **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und Antworten zugeordnet
- **Audit-Trails**: Vollständiger Konversationsverlauf für Compliance-Anforderungen beibehalten
- **Umgang mit sensiblen Daten**: Fragen sollten vermeiden, vertrauliche Informationen in Kanalnachrichten preiszugeben

**Best Practices:**

- **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten von Expertenkonsultationen (technisch,
  rechtlich, geschäftlich)
- **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anforderungen, um qualitativ
  hochwertige Antworten zu erhalten
- **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Workflows
  fortgesetzt werden
- **Timeout-Management**: Legen Sie angemessene Erwartungen an Antwortzeiten fest und behandeln Sie Timeouts elegant
- **Wissenserfassung**: Erwägen Sie das automatische Speichern wertvoller Expertenantworten in Wissensdatenbanken

**Leistungsoptimierung:**

- **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu
  vermeiden
- **Batching**: Erwägen Sie bei ähnlichen Fragen das Batching von Anfragen, um die Unterbrechung von Experten zu
  reduzieren
- **Caching**: Häufige Expertenantworten zwischenspeichern, um redundante Fragen zu reduzieren
- **Eskalationspfade**: Implementieren Sie eine Eskalation, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrem Swiss AI Hub Deployment zu implementieren:

1. **Slack-Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie
   sicher, dass Ihr Bot Zugriff auf die vorgesehenen Expertenkanäle hat
2. **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten verfügbar
   sind, um auf Agent-Fragen zu antworten
3. **In Agent-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()`-Muster an
   Entscheidungspunkten, an denen menschliche Eingaben einen Mehrwert für automatisierte Prozesse darstellen

Für detaillierte Agent-Integrationsmuster lesen Sie die
[Expert Agents-Dokumentation](../../../2_platform/5_agents/9_expert_coordinator_agent/) für praxisnahe
Implementierungsbeispiele und das Swiss AI Hub Agent Developer's Guide für umfassende Anweisungen zur
Workflow-Integration.
