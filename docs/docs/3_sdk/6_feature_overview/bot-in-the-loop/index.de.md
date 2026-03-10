---
title: Bot-in-the-Loop
source_sha: a89b2c0a56e104e4832ee4fa6c7c014f708911c43bdccd770ece22e28514d01d
---

# Bot-in-the-Loop :left_right_arrow: :100:

::: info **TL;DR - Was ist Bot-in-the-Loop?**
Bot-in-the-Loop ermöglicht es KI-Agents, **Workflows nahtlos zu pausieren und menschliche Eingaben über Slack-Kanäle
anzufordern**, um anschließend die Ausführung mit der menschlichen Antwort automatisch fortzusetzen. Dieses Muster
überbrückt die Lücke zwischen autonomer KI-Verarbeitung und menschlicher Expertise und ermöglicht es Agents, komplexe
Entscheidungen zu treffen, während die vollständige Automatisierung im Umfeld menschlicher Beteiligung erhalten bleibt.
:::

## Was ist Bot-in-the-Loop und wie funktioniert es? :brain:

Bot-in-the-Loop stellt ein hochentwickeltes **Mensch-KI-Kollaborationsmuster** dar, das es KI-Agents ermöglicht, ihre
automatisierten Workflows an kritischen Entscheidungspunkten zu pausieren und menschliche Expertise nahtlos durch
strukturierte Slack-Interaktionen zu integrieren.

Die **Workflow-Integrationsarchitektur** erlaubt KI-Agents, Bot-in-the-Loop zu jedem Zeitpunkt ihrer Ausführung
aufzurufen. Wenn ein Agent auf eine Entscheidung stößt, die menschliche Eingabe, Genehmigung oder Expertise erfordert,
sendet er ein `BotInTheLoopRequestEvent`, das automatisch:

- Eine formatierte Frage an einen bestimmten Slack-Kanal postet
- Den vollständigen Workflow-Kontext und die Konversationsverknüpfung beibehält
- Auf menschliche Antwort wartet, ohne andere Systemoperationen zu blockieren
- Die Antwort erfasst und die Agenten-Ausführung automatisch fortsetzt

Die **Slack-Kanal-Integration** bietet die menschliche Schnittstelle über vertraute Kollaborationstools. Experten
antworten direkt in Slack-Threads, wo:

- Fragen als strukturierte, verknüpfte Nachrichten erscheinen
- Mehrere Experten an Antworten zusammenarbeiten können
- Die Zuordnung der Antwort verfolgt, wer die Eingabe bereitgestellt hat
- Der Konversationsverlauf für Audit und Lernen beibehalten wird

Die **Ereignisgesteuerte Orchestrierung** treibt die gesamte Interaktion durch das Ereignissystem des Swiss AI Hubs an:

- `BotInTheLoopRequestEvent` pausiert Workflows und postet an Slack
- `BotInTheLoopResponseEvent` erfasst Antworten und setzt Workflows fort
- Die vollständige Kontextbewahrung gewährleistet eine nahtlose Fortsetzung
- Fehlerbehandlung verwaltet Timeouts und fehlgeschlagene Antworten

Die **Agenten-Workflow-Integration** verwendet den einfachen `BotInTheLoop.invoke()`-Helfer, der die Integration für
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
- **Slack Bot Framework** – Kanalintegration mit Threading und Zuordnung
- **Azure Bot Service** – Multi-Kanal-Bot-Konnektivität und Nachrichtenverarbeitung
- **Event Store** – Persistenter Kontext und Konversationsverfolgung
- **Agent Workflow Engine** – Nahtlose Integration in die Ausführungsabläufe von KI-Agents

## Warum dies ein Game Changer für Ihre KI-Strategie ist :trophy:

Bot-in-the-Loop transformiert die Herangehensweise von Organisationen an die KI-Automatisierung, indem es die kritische
Herausforderung der Mensch-KI-Kollaboration im großen Maßstab löst:

**🤝 Nahtlose Mensch-KI-Kollaboration**: KI-Agents können nun auf natürliche Weise menschliche Experten einbeziehen, ohne
automatisierte Workflows zu unterbrechen. Komplexe Entscheidungen, Genehmigungen und Wissensvalidierungen erfolgen über
vertraute Slack-Interaktionen, während die KI den vollständigen Kontext beibehält und die Verarbeitung mit menschlicher
Eingabe automatisch fortsetzt.

**⚡ Ununterbrochene Automatisierung**: Im Gegensatz zu traditionellen Systemen, die manuelle Eingriffspunkte erfordern,
gewährleistet Bot-in-the-Loop eine kontinuierliche Automatisierung im Umfeld menschlicher Beteiligung. Agents pausieren
nur bei Bedarf, fordern spezifische Eingaben an und nehmen die Verarbeitung sofort wieder auf, wodurch sowohl die
Effizienz als auch die Nutzung menschlicher Expertise maximiert werden.

**🧠 Skalierbare Integration von Expertenwissen**: Fachexperten können effizient mehrere KI-Workflows gleichzeitig durch
strukturierte Slack-Interaktionen unterstützen. Eine Expertenkonsultation kann mehrere Agents informieren, und ihr
Wissen wird für organisatorisches Lernen und zukünftige Automatisierungsverbesserungen erfasst.

**🛡️ Risikobewusste Entscheidungsfindung**: Kritische Entscheidungen, die menschliches Urteilsvermögen erfordern –
behördliche Compliance, hochrangige Genehmigungen oder komplexe Interpretationen – können nahtlos in ansonsten
automatisierte Prozesse integriert werden. Dies gewährleistet sowohl Geschwindigkeit als auch Sicherheit in
KI-gestützten Workflows.

**📚 Erfassung von Organisationswissen**: Jede menschliche Antwort wird mit vollständigem Kontext erfasst und schafft so
ein stetig wachsendes Repository an Expertenentscheidungen und Wissen. Dies ermöglicht eine kontinuierliche Verbesserung
von KI-Systemen und baut institutionelles Wissen auf, das Personalwechsel überdauert.

::: details **Einrichtung und Verwendung von Bot-in-the-Loop**
## Konfigurationsanforderungen

### Slack Bot-Einrichtung

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

   - **Bot-Token-Scopes**: `channels:read`, `chat:write`, `chat:write.public`, `users:read`
   - **Ereignisabonnements**: Abonnieren Sie `message.channels`-Ereignisse
   - **OAuth-Installation**: Installieren Sie die App in Ihrem Workspace

3. **Kanalzugriff**: Stellen Sie sicher, dass Ihr Bot zu den Slack-Kanälen hinzugefügt wird, in denen Sie Fragen posten
   möchten

   ```
   /invite @YourAIHubBot
   ```

### Agenten-Integrations-Setup

1. **Import des Bot-in-the-Loop Helfers**: Fügen Sie es Ihren Agenten-Imports hinzu

   ```python
   from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
   ```

2. **Konfigurieren Sie Slack-Kanal-IDs**: Identifizieren Sie Ihre Slack-Kanal-IDs (Format: `C08MCK6LEBY`)

   ```python
   # Rechtsklick auf den Kanal → Kanaldetails anzeigen → Kanal-ID kopieren
   EXPERT_CHANNEL_ID = "C08MCK6LEBY"
   ```

3. **NATS Ereignisverteilung**: Stellen Sie sicher, dass Ihr Swiss AI Hub-Deployment für das Nachrichten-Routing über
   NATS Messaging konfiguriert ist

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
- **Kontextbewahrung**: Der vollständige Workflow-Zustand wird über menschliche Interaktionen hinweg beibehalten
- **Antwortverarbeitung**: Strukturierte Antwortbearbeitung mit Benutzerzuordnung
- **Fehlerbehandlung**: Timeout-Verwaltung und elegante Fehlerbehandlung

**Slack-Kanal-Funktionen:**

- **Verknüpfte Konversationen**: Antworten werden in organisierten Threads erfasst
- **Unterstützung mehrerer Experten**: Mehrere Experten können an Antworten zusammenarbeiten
- **Benutzerzuordnung**: Verfolgen Sie, wer jede Antwort für die Verantwortlichkeit bereitgestellt hat
- **Umfassende Formatierung**: Unterstützung für Slack-Markdown und strukturierte Nachrichten

**Ereignissystem-Integration:**

- **Asynchrone Verarbeitung**: Nicht blockierende menschliche Interaktionen mit Unterstützung für parallele Workflows
- **Ereignispersistenz**: Der vollständige Konversationsverlauf wird für Audit und Wiedergabe gespeichert
- **Agentenübergreifende Kommunikation**: Antworten können zwischen verschiedenen Agenten-Workflows geteilt werden
- **Monitoring-Integration**: Langfuse-Tracing und Observability für menschliche Interaktionsmuster

## Sicherheit und Best Practices

**Sicherheitsaspekte:**

- **Kanalzugriffskontrolle**: Beschränken Sie den Bot-Zugriff nur auf bestimmte Expertenkanäle
- **Benutzerauthentifizierung**: Die Slack-Benutzeridentität wird erfasst und Antworten zugeordnet
- **Audit-Trails**: Vollständiger Konversationsverlauf wird für Compliance-Anforderungen beibehalten
- **Handhabung sensibler Daten**: Fragen sollten die Offenlegung vertraulicher Informationen in Kanalnachrichten
  vermeiden

**Best Practices:**

- **Kanalorganisation**: Erstellen Sie dedizierte Kanäle für verschiedene Arten von Expertenkonsultationen (technisch,
  rechtlich, geschäftlich)
- **Fragenformatierung**: Strukturieren Sie Fragen klar mit Kontext und spezifischen Anforderungen, um qualitativ
  hochwertige Antworten zu erhalten
- **Antwortvalidierung**: Implementieren Sie eine grundlegende Validierung menschlicher Antworten, bevor Sie Workflows
  fortsetzen
- **Timeout-Verwaltung**: Legen Sie angemessene Erwartungen für Antwortzeiten fest und behandeln Sie Timeouts elegant
- **Wissenserfassung**: Erwägen Sie die automatische Speicherung wertvoller Expertenantworten in Wissensdatenbanken

**Leistungsoptimierung:**

- **Kanalverteilung**: Verteilen Sie verschiedene Fragetypen auf mehrere Kanäle, um eine Überlastung der Experten zu
  vermeiden
- **Batch-Verarbeitung**: Für ähnliche Fragen sollten Anfragen gebündelt werden, um Unterbrechungen der Experten zu
  reduzieren
- **Caching**: Häufige Expertenantworten zwischenspeichern, um redundante Fragen zu reduzieren
- **Eskalationspfade**: Implementieren Sie eine Eskalation, wenn primäre Experten nicht verfügbar sind
:::

## Erste Schritte

Um Bot-in-the-Loop in Ihrem Swiss AI Hub-Deployment zu implementieren:

1. **Slack-Integration konfigurieren**: Richten Sie den Azure Bot Service mit Slack-Konnektivität ein und stellen Sie
   sicher, dass Ihr Bot Zugriff auf die dafür vorgesehenen Expertenkanäle hat
2. **Expertenkanäle identifizieren**: Erstellen oder identifizieren Sie Slack-Kanäle, in denen Fachexperten verfügbar
   sind, um auf Agentenfragen zu antworten
3. **In Agenten-Workflows integrieren**: Verwenden Sie das einfache `BotInTheLoop.invoke()`-Muster an
   Entscheidungspunkten, wo menschliche Eingaben automatisierten Prozessen Mehrwert verleihen

Für detaillierte Agenten-Integrationsmuster lesen Sie die
[Dokumentation der Experten-Agents](../../../2_platform/5_agents/3_expert_asking_agent/) für Beispiele aus der Praxis
sowie das Swiss AI Hub Agenten-Entwicklerhandbuch für umfassende Anweisungen zur Workflow-Integration.
