---
title: Agent-Memory
source_sha: 42a6ba0a911d4ab01328984b5a9ad0a7f3b845576d77853427fdebbd0bd8dc2e
---

# Agent-Memory

Agent-Memory ermöglicht langfristige Personalisierung und den organisationsweiten Wissensaustausch über die
Chat-Historie einer einzelnen Session hinaus. Das SDK bietet zwei unterschiedliche Memory-Scopes: User-Memory für
private, benutzerspezifische Präferenzen und Organization-Memory für geteilte, mandantenweite Fakten.

Memory wird automatisch durch Dependency Injection und dedizierte Events in Agent-Workflows integriert.

## Zwei Memory-Scopes

User-Memory ist privat für einzelne Benutzer und wird automatisch von der LLM aus Konversationsnachrichten extrahiert.
Es speichert persönliche Präferenzen, Arbeitsstile und individuellen Kontext – Dinge wie „Benutzer bevorzugt prägnante
Code-Beispiele in Python.“ Sowohl Vektor- (semantische Suche) als auch Graph-Speicher (Beziehungen) ermöglichen den
Abruf.

Organization-Memory wird über alle Benutzer in einem Mandanten oder Namespace hinweg geteilt. Im Gegensatz zu
User-Memory erfordert es eine explizite Dokumentation anstatt einer automatischen Inferenz. Es speichert
Unternehmensrichtlinien, Projektdetails und Teamkonventionen – Dinge wie „Wir deployen freitags in die Produktion.“
Derselbe Vektor- und Graph-Speicher unterstützt semantischen und relationalen Abruf.

## Memory-Workflow-Muster

Beide Memory-Typen folgen einem gemeinsamen vierstufigen Workflow:

```mermaid
graph LR
    A[UserMessageEvent] --> B(1. Retrieve Memory)
    B --> C[RetrieveMemoryEvent]
    C --> D(2. Extend Chat History)
    D --> E[AddMemoryToChatHistoryEvent]
    E --> F(3. Generate Response)
    F --> G[LLMEvent]
    G --> H(4. Store Memory)
    H --> I[StoreMemoryEvent]
    I --> J[StopEvent]
```

Das Muster ruft relevante Memories ab, injiziert sie als System-Message in die Chat-Historie, generiert eine
Memory-bewusste Antwort und persistiert neue Erkenntnisse.

## User-Memory-Muster

User-Memory lernt persönliche Präferenzen automatisch aus Konversationen. Der Agent extrahiert Fakten über den
Arbeitsstil des Benutzers, ohne dass eine explizite Dokumentation erforderlich ist. Verwenden Sie dieses Muster für
konversationelle Agents, die sich im Laufe der Zeit an individuelle Benutzerpräferenzen anpassen sollen –
Code-Assistenten, persönliche Produktivitäts-Agents, benutzerdefinierte Assistenten.

Referenzimplementierung: `playground/minimal_workflow/user_memory_workflow/`

### Vollständiges Beispiel

::: code-group
```python [UserMemoryAgent.py]
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.generative_ai.chat_history.extend_chat_history_with_user_memory import (
    extend_chat_history_with_user_memory,
)
from aihub_lib.nats.events import (
    UserMessageEvent,
    LLMEvent,
    StopEvent,
)
from aihub_lib.nats.events.memory.retrieve.RetrieveUserMemoryEvent import RetrieveUserMemoryEvent
from aihub_lib.nats.events.memory.history.AddUserMemoryToChatHistoryEvent import AddUserMemoryToChatHistoryEvent
from aihub_lib.nats.events.memory.store.StoreUserMemoryEvent import StoreUserMemoryEvent
from aihub_lib.nats.topics import AgentInstanceTopic
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler

class UserMemoryAgent(Agent):
    """
    Memory-enhanced conversational agent that retrieves and persists user memories.

    Use this agent for personalized conversations requiring long-term context
    beyond single session chat history.
    """

    @step()
    async def retrieve_memory_step(
        self,
        event: UserMessageEvent,
        memory: AgentMemory,
    ) -> RetrieveUserMemoryEvent:
        """Searches user memories to provide personalized context."""
        memory_search_result = await memory.search_user_memory(
            query=event.user_query,
            user_id=event.user.id
        )
        return RetrieveUserMemoryEvent.from_memory_search_result(
            memory_search_result=memory_search_result
        )

    @step()
    async def add_memory_to_chat_history_step(
        self,
        user_message_event: UserMessageEvent,
        memory_event: RetrieveUserMemoryEvent,
        t: LocaleHandler
    ) -> AddUserMemoryToChatHistoryEvent:
        """Prepends memories as system message to guide LLM responses."""
        extended_chat_history = extend_chat_history_with_user_memory(
            chat_history=user_message_event.messages,
            memories=memory_event.memories,
            relations=memory_event.relations,
            user=user_message_event.user,
            t=t,
        )
        return AddUserMemoryToChatHistoryEvent(extended_history=extended_chat_history)

    @step()
    async def respond_with_memory_step(
        self,
        event: AddUserMemoryToChatHistoryEvent,
        agent_config: UserMemoryAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        """Generates response using memory-enhanced chat history."""
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(
                agent_config.llm,
                llm,
                event.extended_history,
                as_stop_step=False
            )

    @step()
    async def update_memory_step(
        self,
        user_message_event: UserMessageEvent,
        llm_event: LLMEvent,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
    ) -> StoreUserMemoryEvent:
        """Persists conversation learnings to long-term memory."""
        memory_added = await memory.add_user_memory(
            messages=llm_event.chat_messages,
            user_id=user_message_event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        return StoreUserMemoryEvent.from_memory_added_object(
            memory_added=memory_added
        )

    @step()
    async def stop_step(self, _: StoreUserMemoryEvent) -> StopEvent:
        """Marks workflow completion."""
        return StopEvent()
```

```python [UserMemoryAgentConfig.py]
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

class UserMemoryAgentConfig(AgentConfig):
    llm: LLMConfig
```
:::

### Schlüsselkomponenten

#### AgentMemory-Injektion

Das `AgentMemory`-Objekt wird automatisch über Dependency Injection in Schritte injiziert:

```python
@step()
async def retrieve_memory_step(
    self,
    event: UserMessageEvent,
    memory: AgentMemory,  # Injected automatically
) -> RetrieveUserMemoryEvent:
    memory_search_result = await memory.search_user_memory(
        query=event.user_query,
        user_id=event.user.id
    )
    return RetrieveUserMemoryEvent.from_memory_search_result(
        memory_search_result=memory_search_result
    )
```

#### Memory-Abruf

`search_user_memory()` führt eine semantische Suche im privaten Memory-Speicher des Benutzers durch. Es benötigt die
Suchanfrage (typischerweise die aktuelle Nachricht des Benutzers), die Benutzer-ID und ein optionales Limit (Standard:
100). Es gibt ein `MemorySearchResult` zurück, das Memories und Beziehungen enthält.

#### Chat-Historie-Erweiterung

Der Helfer `extend_chat_history_with_user_memory()` fügt Memories als System-Message ein:

```python
extended_chat_history = extend_chat_history_with_user_memory(
    chat_history=user_message_event.messages,
    memories=memory_event.memories,
    relations=memory_event.relations,
    user=user_message_event.user,
    t=t,  # LocaleHandler for i18n
)
```

LLMs behandeln System-Messages als maßgebliche Hintergrundinformationen, daher werden Memories als optionaler Kontext
präsentiert, den die LLM je nach Relevanz nutzen kann oder nicht. Die Memories werden nach bestehenden System-Messages
(Agenten-Persönlichkeit/Verhalten) aber vor Benutzer-Messages eingefügt.

#### Memory-Persistenz

`add_user_memory()` verwendet eine LLM, um Erkenntnisse aus der Konversation zu extrahieren:

```python
memory_added = await memory.add_user_memory(
    messages=llm_event.chat_messages,  # Full conversation including LLM response
    user_id=user_message_event.user.id,
    thread_id=topic.thread_id,      # Swiss AI Agent Protocol context
    display_id=topic.display_id,    # Swiss AI Agent Protocol context
    run_id=topic.run_id,            # Swiss AI Agent Protocol context
)
```

Die LLM analysiert die Konversation und extrahiert Fakten wie „Benutzer bevorzugt Python gegenüber JavaScript“, ohne die
gesamte Konversation zu speichern.

## Organization-Memory-Muster

Organization-Memory speichert explizites, geteiltes Organisationswissen. Im Gegensatz zu User-Memory (das abgeleitet
wird) erfordert Organization-Memory, dass Benutzer Fakten bewusst dokumentieren. Verwenden Sie dieses Muster für Agents,
die geteilten organisatorischen Kontext verwalten – Teamkonventionen, Projektdokumentation, Unternehmensrichtlinien oder
technische Fakten, die alle Benutzer kennen sollten.

Referenzimplementierung: `playground/minimal_workflow/organization_memory_workflow/`

### Vollständiges Beispiel

::: code-group
```python [OrganizationMemoryAgent.py]
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from aihub_lib.nats.events import (
    UserMessageEvent,
    LLMStopEvent,
    StoreOrganizationMemoryEvent,
    RetrieveOrganizationMemoryEvent,
    AddOrganizationMemoryToChatHistoryEvent,
)
from aihub_lib.nats.topics import AgentInstanceTopic
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler

class OrganizationMemoryAgent(Agent):
    """
    Organization memory management agent that stores and retrieves
    explicit organizational facts.

    Key Differences from UserMemoryAgent:
    - Input: Explicit facts (user provides clean memory text) vs. inferred from chat
    - Scope: Organization-wide (shared) vs. user-private
    - Namespace: Supports department-level scoping via tenant_namespace
    """

    @step()
    async def store_organization_memory_step(
        self,
        event: UserMessageEvent,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
        agent_config: OrganizationMemoryAgentConfig,
    ) -> StoreOrganizationMemoryEvent:
        """Stores the user's query as an explicit organizational fact."""
        memory_added = await memory.add_organization_memory(
            memory=event.user_query,  # Direct storage - user query is the fact itself
            user_id=event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            tenant_id=agent_config.tenant_id,
            tenant_namespace=agent_config.tenant_namespace,
        )
        return StoreOrganizationMemoryEvent.from_memory_added_object(
            memory_added=memory_added
        )

    @step()
    async def retrieve_organization_memory_step(
        self,
        event: UserMessageEvent,
        memory: AgentMemory,
        agent_config: OrganizationMemoryAgentConfig,
    ) -> RetrieveOrganizationMemoryEvent:
        """Searches organization memories to provide shared org context."""
        memory_search_result = await memory.search_organization_memory(
            query=event.user_query,
            tenant_id=agent_config.tenant_id,
            tenant_namespace=agent_config.tenant_namespace,
            user_id=event.user.id,
        )
        return RetrieveOrganizationMemoryEvent.from_memory_search_result(
            memory_search_result=memory_search_result
        )

    @step()
    async def add_memory_to_chat_history_step(
        self,
        user_message_event: UserMessageEvent,
        memory_event: RetrieveOrganizationMemoryEvent,
        t: LocaleHandler
    ) -> AddOrganizationMemoryToChatHistoryEvent:
        """Prepends organization memories as system message."""
        extended_chat_history = extend_chat_history_with_organization_memory(
            chat_history=user_message_event.messages,
            memories=memory_event.memories,
            relations=memory_event.relations,
            t=t,
        )
        return AddOrganizationMemoryToChatHistoryEvent(extended_history=extended_chat_history)

    @step()
    async def respond_with_memory_step(
        self,
        event: AddOrganizationMemoryToChatHistoryEvent,
        agent_config: OrganizationMemoryAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMStopEvent:
        """Generates response using memory-enhanced chat history."""
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(
                agent_config.llm,
                llm,
                event.extended_history,
                as_stop_step=True
            )
```

```python [OrganizationMemoryAgentConfig.py]
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

class OrganizationMemoryAgentConfig(AgentConfig):
    """Configuration for OrganizationMemoryAgent.

    Defines the LLM and the tenant context (ID and namespace) for memory scoping.
    """
    llm: LLMConfig
    tenant_id: str
    tenant_namespace: str
```
:::

### Wesentliche Unterschiede zum User-Memory

#### Explizite Speicherung (keine Inferenz)

Organization-Memory wird direkt so gespeichert, wie es vom Benutzer bereitgestellt wird:

```python
memory_added = await memory.add_organization_memory(
    memory=event.user_query,  # Direct - no LLM extraction
    # ... context fields ...
)
```

Organization-Memories betreffen alle Benutzer, daher gewährleistet eine explizite Dokumentation Genauigkeit und
Intentionalität. Dies verhindert die unbeabsichtigte Erstellung von Richtlinien aus beiläufigen Konversationen.

#### Mandanten-Scoping

Organization-Memory unterstützt Multi-Mandanten- und Abteilungs-Isolation:

```python
memory_search_result = await memory.search_organization_memory(
    query=event.user_query,
    tenant_id=agent_config.tenant_id,           # Organization boundary
    tenant_namespace=agent_config.tenant_namespace,  # Department boundary
    user_id=event.user.id,
)
```

Der Namespace-Parameter begrenzt Memories auf Abteilungen. „Engineering“ könnte technische Dokumentation und
Deployment-Prozeduren enthalten, „Sales“ könnte Produktpreise und Kundensegmente enthalten, und `None` deutet auf
globales Mandantenwissen hin.

#### Geteilte Sichtbarkeit

Abgerufene Memories sind für alle Benutzer im Mandanten/Namespace sichtbar, nicht nur für den Benutzer, der sie erstellt
hat.

## Memory-Events

Das Memory-System bietet sechs spezialisierte Events zur Workflow-Steuerung:

| Event type                                | Purpose                                           |
| ----------------------------------------- | ------------------------------------------------- |
| `RetrieveUserMemoryEvent`                 | Enthält abgerufene User-Memories                  |
| `RetrieveOrganizationMemoryEvent`         | Enthält abgerufene Organization-Memories          |
| `AddUserMemoryToChatHistoryEvent`         | Enthält Chat-Historie mit injiziertem User-Memory |
| `AddOrganizationMemoryToChatHistoryEvent` | Enthält Chat-Historie mit injiziertem Org-Memory  |
| `StoreUserMemoryEvent`                    | Bestätigt die Persistenz von User-Memory          |
| `StoreOrganizationMemoryEvent`            | Bestätigt die Persistenz von Organization-Memory  |

Memory-Abruf und -Speicherung emittieren automatisch Display-Events für die Observability. Diese erscheinen im Swiss AI
Agent Protocol Trace und erfordern keine spezielle Behandlung.

## Kombination von User- und Organization-Memory

Für Agents, die beide Memory-Typen benötigen, kombinieren Sie die Workflows:

```python
class HybridMemoryAgent(Agent):
    @step()
    async def retrieve_user_memory_step(
        self, event: UserMessageEvent, memory: AgentMemory
    ) -> RetrieveUserMemoryEvent:
        # Retrieve personal preferences
        result = await memory.search_user_memory(query=event.user_query, user_id=event.user.id)
        return RetrieveUserMemoryEvent.from_memory_search_result(result)

    @step()
    async def retrieve_org_memory_step(
        self, event: UserMessageEvent, memory: AgentMemory, config: AgentConfig
    ) -> RetrieveOrganizationMemoryEvent:
        # Retrieve organizational facts
        result = await memory.search_organization_memory(
            query=event.user_query,
            tenant_id=config.tenant_id,
            tenant_namespace=config.tenant_namespace,
            user_id=event.user.id
        )
        return RetrieveOrganizationMemoryEvent.from_memory_search_result(result)

    @step()
    async def combine_memories_step(
        self,
        event: UserMessageEvent,
        user_mem: RetrieveUserMemoryEvent,
        org_mem: RetrieveOrganizationMemoryEvent,
        t: LocaleHandler
    ) -> CombinedMemoryEvent:
        # Extend with both memory types
        chat_history = extend_chat_history_with_user_memory(
            chat_history=event.messages,
            memories=user_mem.memories,
            relations=user_mem.relations,
            user=event.user,
            t=t
        )
        chat_history = extend_chat_history_with_organization_memory(
            chat_history=chat_history,  # Already has user memory
            memories=org_mem.memories,
            relations=org_mem.relations,
            t=t
        )
        return CombinedMemoryEvent(extended_history=chat_history)
```

Die Reihenfolge ist wichtig: User-Memories werden zuerst hinzugefügt (allgemeinerer Kontext), dann Organization-Memories
(spezifische Fakten).

## Erweiterte Nutzung

### Filtern des Memory-Abrufs

Engen Sie Memory-Suchen nach Agent oder Thread ein:

```python
@step()
async def retrieve_memory_step(
    self, event: UserMessageEvent, memory: AgentMemory, topic: AgentInstanceTopic
) -> RetrieveUserMemoryEvent:
    result = await memory.search_user_memory(
        query=event.user_query,
        user_id=event.user.id,
        agent_id=topic.agent_id,      # Only memories from this agent
        thread_id=topic.thread_id,    # Only memories from this conversation
    )
    return RetrieveUserMemoryEvent.from_memory_search_result(result)
```

Thread-spezifisches Filtern unterstützt Anwendungsfälle wie „sich erinnern, was wir in dieser Konversation besprochen
haben“. Agent-spezifisches Filtern verhindert, dass ein Code-Assistent Memories sieht, die von einem RAG-Agent erstellt
wurden.

### Benutzerdefinierte Memory-Extraktion

Die Klasse `AgentMemory` passt die Extraktion basierend auf der Agent-Klasse automatisch an:

```python
class SpecializedMemoryAgent(Agent):
    @step()
    async def update_memory_step(
        self, user_message_event: UserMessageEvent, llm_event: LLMEvent, memory: AgentMemory, topic: AgentInstanceTopic
    ) -> StoreUserMemoryEvent:
        # AgentMemory automatically customizes extraction based on agent class
        memory_added = await memory.add_user_memory(
            messages=llm_event.chat_messages,
            user_id=user_message_event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        # AgentMemory includes agent context automatically via self.agent_id
        return StoreUserMemoryEvent.from_memory_added_object(memory_added)
```

Code-Assistenten extrahieren technische Präferenzen, RAG-Agents extrahieren Domäneninteressen – alles automatisch
basierend auf dem Agent-Typ.

## Observability

Alle Memory-Operationen werden automatisch in Phoenix (http://localhost:6006) getraced. Abruf-Traces zeigen die Abfrage,
zurückgegebene Memories und Relevanz-Scores. Speicher-Traces zeigen extrahierte Memories, Beziehungen und Metadaten. Die
Chat-Historie-Erweiterung zeigt die System-Message mit Memory-Inhalt an.

Alle Memories speichern den vollständigen Swiss AI Agent Protocol Kontext: `agent_id` (welcher Agent die Memory erstellt
hat), `thread_id` (welcher Konversations-Thread), `display_id` (UI-Display-Kontext), `run_id` (Workflow-Ausführungs-ID)
und `user_id` (wem die Memory gehört oder wer sie dokumentiert hat). Dies ermöglicht eine vollständige Auditierbarkeit –
Sie können zurückverfolgen, welche Konversation dem Agent eine bestimmte Präferenz beigebracht hat.

## Best Practices

Verwenden Sie User-Memory für Präferenzen („Benutzer bevorzugt kurze Antworten“) und Organization-Memory für Fakten
(„Wir deployen freitags“). Lassen Sie User-Memory aus Konversationen ableiten, während Organization-Memory explizit
dokumentiert wird. Rufen Sie Memories immer zu Beginn des Workflows ab, damit der Memory-Kontext die gesamte Antwort
leitet, und speichern Sie neue Erkenntnisse am Ende des Workflows, nachdem die LLM-Antwort eingeschlossen wurde.

Der Memory-Abruf fügt etwa 100 ms Latenz hinzu. Verwenden Sie den `limit`-Parameter, um eine Überladung des Kontexts zu
vermeiden, und filtern Sie bei Bedarf nach Agent oder Thread, um irrelevante Memories zu reduzieren.

User-Memory ist DSGVO-konform – Benutzer können all ihre Memories einsehen, bearbeiten und löschen. Organization-Memory
erfordert Zugriffskontrolle, da Änderungen alle Benutzer betreffen. Jede Memory verfolgt, wer sie wann erstellt hat, zur
Auditierbarkeit, und alle Memory-Daten verbleiben auf Schweizer Infrastruktur.

::: tip Nächste Schritte
Erkunden Sie die vollständigen Beispiele in `playground/minimal_workflow/user_memory_workflow/` und
`playground/minimal_workflow/organization_memory_workflow/`. Überprüfen Sie Memory-Events in Phoenix, nachdem Sie einen
Memory-erweiterten Agent ausgeführt haben. Versuchen Sie, einen Hybrid-Agent zu erstellen, der beide Memory-Typen
kombiniert, oder experimentieren Sie mit Namespace-Scoping für die Abteilungs-Isolation.
:::
