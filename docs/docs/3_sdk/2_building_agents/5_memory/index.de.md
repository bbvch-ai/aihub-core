---
title: Agentenspeicher
source_sha: 7b36ac47b5673ef0fec9ce838baebc5f4a215e65a54cb46103bc10c73d5a044c
---

# Agentenspeicher

Agentenspeicher ermöglicht langfristige Personalisierung und den Austausch von Organisationswissen, der über die
Chat-Historie einer einzelnen Sitzung hinausgeht. Das SDK bietet zwei unterschiedliche Speicherbereiche:
Benutzerspeicher für private, benutzerspezifische Präferenzen und Organisationsspeicher für gemeinsame, mandantenweite
Fakten.

Der Speicher wird über Dependency Injection und dedizierte Events automatisch in Agenten-Workflows integriert.

## Zwei Speicherbereiche

Der Benutzerspeicher ist privat für einzelne Benutzer und wird automatisch von der LLM aus Konversationsnachrichten
extrahiert. Er speichert persönliche Präferenzen, Arbeitsstile und individuellen Kontext – Dinge wie "Benutzer bevorzugt
prägnante Codebeispiele in Python." Sowohl Vektor- (semantische Suche) als auch Graph-Speicher (Beziehungen) ermöglichen
den Abruf.

Der Organisationsspeicher wird von allen Benutzern in einem Mandanten oder Namespace geteilt. Im Gegensatz zum
Benutzerspeicher erfordert er eine explizite Dokumentation anstelle einer automatischen Inferenz. Er speichert
Unternehmensrichtlinien, Projektdetails und Teamkonventionen – Dinge wie "Wir deployen freitags in die Produktion."
Derselbe Vektor- und Graph-Speicher unterstützt den semantischen und relationalen Abruf.

## Speicher-Workflow-Muster

Beide Speichertypen folgen einem gemeinsamen vierstufigen Workflow:

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

Das Muster ruft relevante Speicher ab, injiziert sie als Systemnachricht in die Chat-Historie, generiert eine
speicherbewusste Antwort und speichert neue Erkenntnisse dauerhaft.

## Benutzerspeicher-Muster

Der Benutzerspeicher lernt persönliche Präferenzen automatisch aus Konversationen. Der Agent extrahiert Fakten über den
Arbeitsstil des Benutzers, ohne explizite Dokumentation zu erfordern. Verwenden Sie dieses Muster für
Konversations-Agents, die sich im Laufe der Zeit an individuelle Benutzerpräferenzen anpassen sollen – Code-Assistenten,
persönliche Produktivitäts-Agents, benutzerdefinierte Assistenten.

Referenzimplementierung: `playground/minimal_workflow/user_memory_workflow/`

::: warning Die Beendigungskonstante
Wenn die Speicherdauerhaftigkeit von der LLM-Ausgabe abhängt, darf der LLM-Schritt **kein** `StopEvent` zurückgeben.
Wenn `as_stop_step=True` gesetzt ist, terminiert der Workflow sofort mit einem `LLMStopEvent` — der Speicherschritt wird
nie ausgeführt.

```python
# INCORRECT: LLMStopEvent terminates before storage
@step()
async def respond(self, ..., displayer: EventDisplayer) -> LLMStopEvent:
    return await displayer.display_llm_stream(..., as_stop_step=True)  # Workflow ends here

@step()
async def store(self, llm: LLMStopEvent, ...) -> StoreMemoryEvent:
    ...  # Never executes — StopEvent already terminated the run

# CORRECT: LLMEvent allows downstream steps
@step()
async def respond(self, ..., displayer: EventDisplayer) -> LLMEvent:
    return await displayer.display_llm_stream(..., as_stop_step=False)

@step()
async def store(self, llm: LLMEvent, memory: AgentMemory) -> StoreUserMemoryEvent:
    await memory.add_user_memory(messages=llm.chat_messages, ...)
    return StoreUserMemoryEvent(...)

@step()
async def stop_step(self, _: StoreUserMemoryEvent) -> StopEvent:
    return StopEvent()
```

Siehe [Die Verletzung des "Dangling Stop"](../9_execution_model/#the-dangling-stop-violation) für die allgemeine Regel.
:::

### Vollständiges Beispiel

::: code-group
```python [UserMemoryAgent.py]
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_user_memory import (
    extend_chat_history_with_user_memory,
)
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import LLMEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.memory.retrieve.retrieve_user_memory_event import RetrieveUserMemoryEvent
from swiss_ai_hub.core.events.agent.memory.history.add_user_memory_to_chat_history_event import AddUserMemoryToChatHistoryEvent
from swiss_ai_hub.core.events.agent.memory.store.store_user_memory_event import StoreUserMemoryEvent
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

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
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

class UserMemoryAgentConfig(AgentConfig):
    llm: LLMConfig
```
:::

### Schlüsselkomponenten

#### AgentMemory-Injektion

Das `AgentMemory`-Objekt wird über Dependency Injection automatisch in Schritte injiziert:

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

#### Speicherabruf

`search_user_memory()` führt eine semantische Suche im privaten Benutzerspeicher durch. Sie nimmt die Suchanfrage
(typischerweise die aktuelle Nachricht des Benutzers), die Benutzer-ID und ein optionales Limit (Standard: 100)
entgegen. Sie gibt ein `MemorySearchResult` zurück, das Speicher und Beziehungen enthält.

#### Erweiterung der Chat-Historie

Der Helfer `extend_chat_history_with_user_memory()` fügt Erinnerungen als Systemnachricht ein:

```python
extended_chat_history = extend_chat_history_with_user_memory(
    chat_history=user_message_event.messages,
    memories=memory_event.memories,
    relations=memory_event.relations,
    user=user_message_event.user,
    t=t,  # LocaleHandler for i18n
)
```

LLMs behandeln Systemnachrichten als maßgebliche Hintergrundinformationen, daher werden Erinnerungen als optionaler
Kontext präsentiert, den die LLM je nach Relevanz verwenden kann oder nicht. Die Erinnerungen werden nach bestehenden
Systemnachrichten (Agenten-Persönlichkeit/Verhalten), aber vor Benutzernachrichten eingefügt.

#### Speicherpersistenz

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

Die LLM analysiert die Konversation und extrahiert Fakten wie "Benutzer bevorzugt Python gegenüber JavaScript", ohne die
gesamte Konversation zu speichern.

## Organisationsspeicher-Muster

Der Organisationsspeicher speichert explizites, gemeinsames Organisationswissen. Im Gegensatz zum Benutzerspeicher (der
abgeleitet wird) erfordert der Organisationsspeicher, dass Benutzer Fakten absichtlich dokumentieren. Verwenden Sie
dieses Muster für Agents, die gemeinsam genutzten organisatorischen Kontext verwalten – Teamkonventionen,
Projektdokumentation, Unternehmensrichtlinien oder technische Fakten, die alle Benutzer kennen sollten.

Referenzimplementierung: `playground/minimal_workflow/organization_memory_workflow/`

### Vollständiges Beispiel

::: code-group
```python [OrganizationMemoryAgent.py]
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory
from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event import LLMStopEvent
from swiss_ai_hub.core.events.agent.memory.store.store_organization_memory_event import StoreOrganizationMemoryEvent
from swiss_ai_hub.core.events.agent.memory.retrieve.retrieve_organization_memory_event import RetrieveOrganizationMemoryEvent
from swiss_ai_hub.core.events.agent.memory.history.add_organization_memory_to_chat_history_event import AddOrganizationMemoryToChatHistoryEvent
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic
from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

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
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

class OrganizationMemoryAgentConfig(AgentConfig):
    """Configuration for OrganizationMemoryAgent.

    Defines the LLM and the tenant context (ID and namespace) for memory scoping.
    """
    llm: LLMConfig
    tenant_id: str
    tenant_namespace: str
```
:::

### Wesentliche Unterschiede zum Benutzerspeicher

#### Explizite Speicherung (keine Inferenz)

Der Organisationsspeicher wird direkt so gespeichert, wie er vom Benutzer bereitgestellt wird:

```python
memory_added = await memory.add_organization_memory(
    memory=event.user_query,  # Direct - no LLM extraction
    # ... context fields ...
)
```

Organisationserinnerungen betreffen alle Benutzer, daher gewährleistet eine explizite Dokumentation Genauigkeit und
Intentionalität. Dies verhindert die unbeabsichtigte Erstellung von Richtlinien aus informellen Gesprächen.

#### Mandanten-Bereichsabgrenzung

Der Organisationsspeicher unterstützt Multi-Mandanten- und Abteilungs-Isolation:

```python
memory_search_result = await memory.search_organization_memory(
    query=event.user_query,
    tenant_id=agent_config.tenant_id,           # Organization boundary
    tenant_namespace=agent_config.tenant_namespace,  # Department boundary
    user_id=event.user.id,
)
```

Der Namespace-Parameter grenzt Speicher auf Abteilungen ab. "Engineering" könnte technische Dokumentation und
Deployment-Verfahren enthalten, "Sales" könnte Produktpreise und Kundensegmente enthalten, und `None` zeigt globales
Mandantenwissen an.

#### Gemeinsame Sichtbarkeit

Abgerufene Speicher sind für alle Benutzer im Mandanten/Namespace sichtbar, nicht nur für den Benutzer, der sie erstellt
hat.

## Speicher-Events

Das Speichersystem bietet sechs spezialisierte Events für die Workflow-Steuerung:

| Event-Typ                                 | Zweck                                                       |
| :---------------------------------------- | :---------------------------------------------------------- |
| `RetrieveUserMemoryEvent`                 | Enthält abgerufene Benutzerspeicher                         |
| `RetrieveOrganizationMemoryEvent`         | Enthält abgerufene Organisationsspeicher                    |
| `AddUserMemoryToChatHistoryEvent`         | Enthält Chat-Historie mit injiziertem Benutzerspeicher      |
| `AddOrganizationMemoryToChatHistoryEvent` | Enthält Chat-Historie mit injiziertem Organisationsspeicher |
| `StoreUserMemoryEvent`                    | Bestätigt Benutzerspeicher-Persistenz                       |
| `StoreOrganizationMemoryEvent`            | Bestätigt Organisationsspeicher-Persistenz                  |

Speicherabruf und -speicherung senden automatisch Display-Events für die Observability. Diese erscheinen im Swiss AI
Agent Protocol Trace und erfordern keine spezielle Behandlung.

## Kombination von Benutzer- und Organisationsspeicher

Für Agents, die beide Speichertypen benötigen, kombinieren Sie die Workflows:

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

Die Reihenfolge ist wichtig: Benutzerspeicher werden zuerst hinzugefügt (allgemeinerer Kontext), dann
Organisationsspeicher (spezifische Fakten).

## Erweiterte Nutzung

### Filterung des Speicherabrufs

Engen Sie Speichersuchen nach Agent oder Thread ein:

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

Thread-spezifische Filterung unterstützt Anwendungsfälle wie "Erinnerung an das, was wir in dieser Konversation
besprochen haben". Agenten-spezifische Filterung verhindert, dass ein Code-Assistent Erinnerungen sieht, die von einem
RAG-Agenten erstellt wurden.

### Benutzerdefinierte Speicher-Extraktion

Die Klasse `AgentMemory` passt die Extraktion basierend auf der Agentenklasse automatisch an:

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
basierend auf dem Agenten-Typ.

### Konfigurationsgesteuerter Speicher

Produktions-Agents machen Speicherfunktionen oft über Konfigurations-Flags optional. Verwenden Sie Vorbedingungen, um
Speicherschritte basierend auf der Konfiguration zu steuern und Race Conditions mit optionalen Events zu verhindern:

```python
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition

@precondition()
def check_memory_ready(
    user_event: UserMessageEvent,
    user_memory: RetrieveUserMemoryEvent | None,
    org_memory: RetrieveOrganizationMemoryEvent | None,
    config: AgentConfig,
) -> bool:
    if config.enable_user_memory and user_memory is None:
        return False
    if config.enable_org_memory and org_memory is None:
        return False
    return config.enable_user_memory or config.enable_org_memory

@precondition()
def check_storage_complete(
    llm: LLMEvent,
    stored: StoreUserMemoryEvent | None,
    config: AgentConfig,
) -> bool:
    if config.enable_memory_storage and stored is None:
        return False
    return True
```

Die Vorbedingung `check_memory_ready` blockiert den Schritt zur Historien-Erweiterung, bis alle aktivierten
Speichertypen abgerufen wurden. Die Vorbedingung `check_storage_complete` blockiert den letzten Stop-Schritt, bis die
Speicherung abgeschlossen ist (falls aktiviert). Dies verhindert die
[optionale Parameterfalle](../9_execution_model/#the-optional-parameter-trap), bei der Schritte vorzeitig mit
`None`-Werten ausgeführt werden.

## Observability

Alle Speicheroperationen werden automatisch im Observability Dashboard nachverfolgt. Abruf-Traces zeigen die Anfrage,
zurückgegebene Speicher und Relevanzbewertungen. Speicher-Traces zeigen extrahierte Speicher, Beziehungen und Metadaten.
Die Erweiterung der Chat-Historie zeigt die Systemnachricht mit dem Speicherinhalt an.

Alle Speicher speichern den vollständigen Swiss AI Agent Protocol-Kontext: `agent_id` (welcher Agent den Speicher
erstellt hat), `thread_id` (welcher Konversations-Thread), `display_id` (UI-Anzeigekontext), `run_id`
(Workflow-Ausführungs-ID) und `user_id` (wem der Speicher gehört oder wer ihn dokumentiert hat). Dies ermöglicht eine
vollständige Auditierbarkeit – Sie können nachvollziehen, welche Konversation dem Agenten eine bestimmte Präferenz
beigebracht hat.

## Bewährte Praktiken

Verwenden Sie Benutzerspeicher für Präferenzen ("Benutzer bevorzugt knappe Antworten") und Organisationsspeicher für
Fakten ("Wir deployen freitags"). Lassen Sie den Benutzerspeicher aus der Konversation ableiten, während der
Organisationsspeicher explizit dokumentiert wird. Rufen Sie Erinnerungen immer zu Beginn des Workflows ab, damit der
Speicherkontext die gesamte Antwort leitet, und speichern Sie neue Erkenntnisse am Ende des Workflows, nachdem die
LLM-Antwort enthalten ist.

Der Speicherabruf fügt ungefähr 100ms Latenz hinzu. Verwenden Sie den `limit`-Parameter, um überwältigenden Kontext zu
vermeiden, und filtern Sie bei Bedarf nach Agent oder Thread, um irrelevante Speicher zu reduzieren.

Der Benutzerspeicher ist DSGVO-konform – Benutzer können alle ihre Speicher einsehen, bearbeiten und löschen. Der
Organisationsspeicher erfordert eine Zugriffskontrolle, da Änderungen alle Benutzer betreffen. Jeder Speicher verfolgt,
wer ihn wann erstellt hat, zur Auditierbarkeit, und alle Speicherdaten verbleiben auf Schweizer Infrastruktur.

::: tip Nächste Schritte
Erkunden Sie die vollständigen Beispiele in `playground/minimal_workflow/user_memory_workflow/` und
`playground/minimal_workflow/organization_memory_workflow/`. Überprüfen Sie Speicher-Events in Langfuse, nachdem Sie
einen speichergestützten Agenten ausgeführt haben. Versuchen Sie, einen Hybrid-Agenten zu erstellen, der beide
Speichertypen kombiniert, oder experimentieren Sie mit Namespace-Scoping für die abteilungsbezogene Isolation.
:::
