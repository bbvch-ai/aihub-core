---
title: Ereignisreferenz
source_sha: "fbe6d78b3308786c31067874b660004f3f0a01fb5b29549fddd2a1ae7b058f81"
---

# Ereignisreferenz

Diese Seite bietet eine vollständige Referenz zur Ereignishierarchie, zur Auswahl des richtigen Basisereignisses und einen Katalog aller verfügbaren Ereignisse.

## Steuer-, Anzeige- und kombinierte Ereignisse

Das Framework unterscheidet zwischen Ereigniskategorien basierend auf deren Auswirkung auf den Workflow:

| Kategorie               | Basisklasse              | Löst Dispatcher aus | Anwendungsfall                                          |
| :---------------------- | :----------------------- | :------------------ | :------------------------------------------------------ |
| **Steuerung**           | `ControlEvent`           | Ja                  | Workflow-Statusübergänge, Schrittabhängigkeiten         |
| **Anzeige**             | `DisplayEvent`           | Nein                | UI-Updates, Streaming-Ausgabe, Observability            |
| **Steuerung und Anzeige** | `ControlAndDisplayEvent` | Ja                  | Beides: treibt Workflow voran UND wird in der UI angezeigt |

**Steuerereignisse** (Control events) beeinflussen den Kontrollfluss des Workflows. Wenn ein `ControlEvent` veröffentlicht wird, evaluiert der Dispatcher alle Schritte, um festzustellen, ob neue Schritte ausgeführt werden sollen. Nur `ControlEvent`-Typen (oder Unterklassen) können Schritt-Eingabeanforderungen erfüllen.

**Anzeigeereignisse** (Display events) lösen den Dispatcher nicht aus. Verwenden Sie diese für hochfrequente Updates, die in der UI erscheinen sollen, aber keine erneute Schrittauswertung verursachen dürfen. Eine gestreamte LLM-Antwort kann Hunderte von `ChunkEvent`-Instanzen pro Minute emittieren; würde man diese zu Steuerereignissen machen, würde dies zu unnötigem Dispatcher-Overhead führen.

**Kombinierte Ereignisse** (Combined events) benötigen beide Verhaltensweisen – sie beeinflussen den Workflow UND erscheinen in der UI. Die meisten semantischen Ereignisse (`LLMEvent`, `RetrieverEvent` usw.) erben von `ControlAndDisplayEvent`.

```python
from swiss_ai_hub.core.events.control.control_event import ControlEvent
from swiss_ai_hub.core.events.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.control_and_display_event import ControlAndDisplayEvent

# Control event: triggers dispatcher, can satisfy step dependencies
class AnalysisCompleteEvent(ControlEvent):
    summary: str

# Display event: does NOT trigger dispatcher, UI-only
class ProgressUpdateEvent(DisplayEvent):
    percent_complete: float
    status_message: str

# Combined: triggers dispatcher AND displays in UI
class RetrieveEvent(ControlAndDisplayEvent):
    nodes: list[IngestedNode]
```

## Ereignisse als Fluss-Carrier

Ereignisse dienen zwei unterschiedlichen Zwecken:

1.  **Datenträger:** Transportieren von Werten zwischen Schritten
2.  **Flussträger:** Steuern der Ausführungsreihenfolge unabhängig von Daten

Ein Schritt kann von einem Ereignis abhängen, um ausschliesslich die Ausführungsreihenfolge sicherzustellen, ohne Daten von diesem zu benötigen:

```python
class PathA(ControlEvent):
    pass  # No fields — pure flow control

class PathB(ControlEvent):
    pass

@step()
async def decide(self, event: StartEvent) -> PathA | PathB:
    if condition():
        return PathA()
    return PathB()

@step()
async def handle_path_a(self, _: PathA) -> StopEvent:
    # Underscore signals: "I need this event for flow control, not data"
    return StopEvent()
```

Die Konvention `_: EventType` weist auf eine Abhängigkeit von der Existenz eines Ereignisses und nicht von dessen Inhalt hin. Dieses Muster ist wesentlich für:

-   **Bedingte Verzweigung:** Unterschiedliche Schritte werden basierend auf dem emittierten Ereignistyp ausgeführt.
-   **Sequenzierung:** Sicherstellen, dass Schritt B auf Schritt A wartet, ohne die Ausgabedaten von A zu benötigen.
-   **Synchronisationsbarrieren:** Warten auf ein Signal, dass die Arbeit abgeschlossen ist.

## Ereignishierarchie

```
BaseEvent
├── ControlEvent                    # Triggers dispatcher
│   ├── StartEvent                  # Workflow entry points
│   │   └── UserMessageEvent        # User-initiated workflow
│   ├── StopEvent                   # Workflow termination
│   └── ExceptionEvent              # Error signaling
│
├── DisplayEvent                    # UI-only, no dispatcher trigger
│   ├── ChunkEvent                  # Streaming text chunks
│   ├── ThoughtEvent                # Agent reasoning display
│   └── CostEvent                   # Cost tracking display
│       └── LLMCostEvent            # LLM-specific costs
│
├── ControlAndDisplayEvent          # Both behaviors
│   ├── SemanticEvent               # OpenInference-compatible (OTEL/Phoenix/Langfuse)
│   │   ├── LLMEvent                # LLM invocation
│   │   │   └── LLMStopEvent        # Terminal LLM response
│   │   ├── RetrieverEvent          # Document retrieval
│   │   ├── RerankerEvent           # Result reranking
│   │   ├── EmbeddingEvent          # Embedding generation
│   │   ├── ToolEvent               # Tool invocation
│   │   ├── GuardEvent              # Guardrail evaluation
│   │   ├── ChainEvent              # Chain execution
│   │   └── AgentEvent              # Agent invocation
│   │
│   ├── HumanInTheLoopRequestEvent  # HITL requests
│   ├── HumanInTheLoopResponseEvent # HITL responses
│   ├── AgentInTheLoopRequestEvent  # AITL delegation
│   ├── AgentInTheLoopResponseEvent # AITL results
│   ├── BotInTheLoopRequestEvent    # BITL Teams/Slack requests
│   ├── BotInTheLoopResponseEvent   # BITL responses
│   │
│   ├── BaseRetrieveMemoryEvent     # Memory retrieval
│   │   ├── RetrieveUserMemoryEvent
│   │   └── RetrieveOrganizationMemoryEvent
│   ├── BaseStoreMemoryEvent        # Memory persistence
│   │   ├── StoreUserMemoryEvent
│   │   └── StoreOrganizationMemoryEvent
│   │
│   └── RouterEvent                 # LLM routing decisions
```

## Auswahl des richtigen Basisereignisses

Wenn Sie ein benutzerdefiniertes Ereignis erstellen, erben Sie von der spezifischsten anwendbaren Basisklasse:

| Wenn Ihr Ereignis darstellt...      | Erben Sie von                                                 | Vorteile                                        |
| :-------------------------------- | :------------------------------------------------------------ | :---------------------------------------------- |
| Workflow-Startbedingung           | `StartEvent`                                                  | Als Einstiegspunkt erkannt                      |
| Benutzernachricht, die Workflow initiiert | `UserMessageEvent`                                            | Chat-Verlauf, Locale, Benutzeridentität         |
| Workflow-Beendigung               | `StopEvent`                                                   | Signalisiert Abschluss                          |
| Fehler/Fehlschlag                 | `ExceptionEvent`                                              | Fehlerbehandlungsmuster                         |
| LLM-Aufrufergebnis                | `LLMEvent`                                                    | Token-Zähler, Nachrichten, OpenInference-Spans  |
| Terminale LLM-Antwort             | `LLMStopEvent`                                                | Kombiniert LLM-Daten mit Workflow-Beendigung    |
| Dokumentenabruf                   | `RetrieverEvent`                                              | Abgerufene Nodes, OpenInference-Spans           |
| Reranking-Operation               | `RerankerEvent`                                               | Eingabe-/Ausgabe-Nodes, OpenInference-Spans     |
| Embedding-Generierung             | `EmbeddingEvent`                                              | Vektoren, Modellinformationen, OpenInference-Spans |
| Tool-/Funktionsaufruf             | `ToolEvent`                                                   | Tool-Name, Parameter, OpenInference-Spans       |
| Guardrail-Prüfung                 | `GuardEvent`                                                  | Guard-Ergebnis, OpenInference-Spans             |
| Menschliche Genehmigung benötigt  | `HumanInTheLoopRequestEvent`                                  | Workflow-Aussetzung, UI-Eingabeaufforderung     |
| Agenten-Delegation                | `AgentInTheLoopRequestEvent`                                  | Cross-Agent-Kommunikation                       |
| Speicherabruf                     | `RetrieveUserMemoryEvent` / `RetrieveOrganizationMemoryEvent` | Speicher-Suchergebnisse                         |
| Speicherspeicherung               | `StoreUserMemoryEvent` / `StoreOrganizationMemoryEvent`       | Speicherbestätigung                             |
| Streaming-Text-Chunk              | `ChunkEvent`                                                  | Echtzeit-UI-Updates (nur Anzeige)               |
| Agenten-Gedanke/Argumentation     | `ThoughtEvent`                                                | Transparenzanzeige (nur Anzeige)                |
| Kosteninformationen               | `LLMCostEvent`                                                | Token-Nutzung, Preisgestaltung (nur Anzeige)    |
| Generischer Workflow-Status       | `ControlAndDisplayEvent`                                      | Löst Dispatcher + UI-Anzeige aus                |
| Generisches UI-Update             | `DisplayEvent`                                                | Nur UI, kein Dispatcher-Overhead                |

## Semantische Ereignisse und OpenInference

`SemanticEvent`-Unterklassen implementieren die Methode `to_semantic_convention()`, die Attribute erzeugt, die mit der [OpenInference-Spezifikation](https://github.com/Arize-ai/openinference) kompatibel sind. Dies ermöglicht die Integration mit:

-   **Arize Phoenix:** Trace-Visualisierung und Debugging
-   **Langfuse:** LLM-Observability und -Analysen
-   **Jedem OpenTelemetry-kompatiblen System:** Standard-Span-Attribute

```python
from swiss_ai_hub.core.events.semantic import RetrieverEvent

# RetrieverEvent automatically exports OpenInference attributes:
# - openinference.span.kind: "RETRIEVER"
# - retrieval.documents.{i}.document.id
# - retrieval.documents.{i}.document.content
# - retrieval.documents.{i}.document.score

event = RetrieverEvent.from_nodes(retrieved_nodes)
otel_attributes = event.to_semantic_convention()
```

Beim Erstellen von Agents, die Observability benötigen, bevorzugen Sie semantische Ereignisse gegenüber generischen `ControlAndDisplayEvent`:

```python
# Preferred: semantic event for observability
from swiss_ai_hub.core.events.semantic import RetrieverEvent

@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieverEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieverEvent.from_nodes(nodes)  # OpenInference-compatible

# Discouraged: generic event loses observability benefits
class MyRetrieveEvent(ControlAndDisplayEvent):
    nodes: list[NodeWithScore]  # No OpenInference integration
```

## Referenz der verfügbaren Ereignisse

### Steuerereignisse (lösen Dispatcher aus)

| Ereignis         | Modul                              | Zweck                                  |
| :--------------- | :--------------------------------- | :------------------------------------- |
| `ControlEvent`   | `control.ControlEvent`             | Basisklasse für alle Steuerereignisse  |
| `StartEvent`     | `control.start.StartEvent`         | Workflow-Einstiegspunkt                |
| `StopEvent`      | `control.stop.StopEvent`           | Workflow-Beendigung                    |
| `ExceptionEvent` | `control.exception.ExceptionEvent` | Fehler-Signalisierung                  |

### Anzeigeereignisse (nur UI)

| Ereignis       | Modul                  | Zweck                                |
| :------------- | :--------------------- | :----------------------------------- |
| `DisplayEvent` | `display.DisplayEvent` | Basisklasse für Anzeigeereignisse    |
| `ChunkEvent`   | `display.ChunkEvent`   | Streaming-Textausgabe                |
| `ThoughtEvent` | `display.ThoughtEvent` | Transparenz der Agenten-Argumentation |
| `CostEvent`    | `cost.CostEvent`       | Kostenverfolgung Basis               |
| `LLMCostEvent` | `cost.LLMCostEvent`    | LLM-Token-/Kostenberichterstattung   |

### Semantische Ereignisse (OpenInference-kompatibel)

| Ereignis         | Modul                               | OpenInference Span-Typ  |
| :--------------- | :---------------------------------- | :---------------------- |
| `SemanticEvent`  | `semantic.SemanticEvent`            | Basisklasse (abstrakt)  |
| `LLMEvent`       | `semantic.llm.LLMEvent`             | `LLM`                   |
| `LLMStopEvent`   | `semantic.llm.LLMStopEvent`         | `LLM` (terminal)        |
| `RetrieverEvent` | `semantic.retriever.RetrieverEvent` | `RETRIEVER`             |
| `RerankerEvent`  | `semantic.reranker.RerankerEvent`   | `RERANKER`              |
| `EmbeddingEvent` | `semantic.embedding.EmbeddingEvent` | `EMBEDDING`             |
| `ToolEvent`      | `semantic.tool.ToolEvent`           | `TOOL`                  |
| `GuardEvent`     | `semantic.guard.GuardEvent`         | `GUARDRAIL`             |
| `ChainEvent`     | `semantic.chain.ChainEvent`         | `CHAIN`                 |
| `AgentEvent`     | `semantic.agent.AgentEvent`         | `AGENT`                 |

### Interaktionsereignisse

| Ereignis                                 | Modul                         | Zweck                                   |
| :--------------------------------------- | :---------------------------- | :-------------------------------------- |
| `UserMessageEvent`                       | `user.UserMessageEvent`       | Benutzerinitiierter Workflow-Start      |
| `HumanInTheLoopRequestEvent`             | `human_in_the_loop.request`   | Basisklasse für HITL-Anfragen           |
| `HumanInTheLoopInputRequestEvent`        | `human_in_the_loop.request`   | Popup mit Texteingabefeld               |
| `HumanInTheLoopConfirmationRequestEvent` | `human_in_the_loop.request`   | Ja/Nein-Schaltflächenauswahl            |
| `HumanInTheLoopChatRequestEvent`         | `human_in_the_loop.request`   | Chat-Nachricht (Fallback)               |
| `HumanInTheLoopResponseEvent`            | `human_in_the_loop.response`  | Basisklasse für HITL-Antworten          |
| `AgentInTheLoopRequestEvent`             | `agent_in_the_loop.request`   | An einen anderen Agenten delegieren     |
| `AgentInTheLoopResponseEvent`            | `agent_in_the_loop.response`  | Ergebnis des delegierten Agenten        |
| `AgentInTheLoopExceptionEvent`           | `agent_in_the_loop.exception` | Fehler des delegierten Agenten          |
| `BotInTheLoopRequestEvent`               | `bot_in_the_loop.request`     | Nachricht an Teams/Slack-Kanal senden   |
| `BotInTheLoopResponseEvent`              | `bot_in_the_loop.response`    | Antwort von Teams/Slack-Benutzer        |

**HITL-Hilfsklassen** (keine Ereignisse, sondern Workflow-Dienstprogramme):

| Helfer                       | UI-Verhalten                                              |
| :--------------------------- | :-------------------------------------------------------- |
| `HumanInTheLoopInput`        | Popup-Dialog für die freie Texteingabe                    |
| `HumanInTheLoopConfirmation` | Ja/Nein-Schaltflächenauswahl                              |
| `HumanInTheLoopChat`         | Nachricht im Chat-Stream (Fallback für einfache UIs/APIs) |

### Speicherereignisse

| Ereignis                          | Modul             | Zweck                               |
| :-------------------------------- | :---------------- | :---------------------------------- |
| `BaseRetrieveMemoryEvent`         | `memory.retrieve` | Basis für Speicherabruf             |
| `RetrieveUserMemoryEvent`         | `memory.retrieve` | Benutzerbezogener Speicherabruf     |
| `RetrieveOrganizationMemoryEvent` | `memory.retrieve` | Organisationsbezogener Speicherabruf |
| `BaseStoreMemoryEvent`            | `memory.store`    | Basis für Speicherspeicherung       |
| `StoreUserMemoryEvent`            | `memory.store`    | Benutzerbezogene Speicherspeicherung |
| `StoreOrganizationMemoryEvent`    | `memory.store`    | Organisationsbezogene Speicherspeicherung |
| `AddMemoryToChatHistoryEvent`     | `memory.history`  | Erweiterter Chatverlauf             |

### Guard-Ereignisse

| Ereignis                         | Modul                       | Zweck                               |
| :------------------------------- | :-------------------------- | :---------------------------------- |
| `GuardAcceptEvent`               | `guard.GuardAcceptEvent`    | Guard akzeptiert                    |
| `GuardRejectionEvent`            | `guard.GuardRejectionEvent` | Guard abgelehnt                     |
| `AgentSuitabilityAcceptEvent`    | `guard`                     | Agent kann Anfrage bearbeiten      |
| `AgentSuitabilityRejectEvent`    | `guard`                     | Agent kann Anfrage nicht bearbeiten |
| `ContextSufficientAcceptEvent`   | `guard`                     | Ausreichender Kontext verfügbar     |
| `ContextInsufficientRejectEvent` | `guard`                     | Unzureichender Kontext              |
| `SensitiveInfoAcceptEvent`       | `guard`                     | Keine sensiblen Informationen erkannt |
| `SensitiveInfoRejectEvent`       | `guard`                     | Sensible Informationen erkannt      |

### Dienstprogramme-Ereignisse

| Ereignis                           | Modul                          | Zweck                       |
| :--------------------------------- | :----------------------------- | :-------------------------- |
| `RouterEvent`                      | `router.RouterEvent`           | LLM-Routingentscheidung     |
| `LanguageEvent`                    | `common.LanguageEvent`         | Spracherkennung             |
| `LimitChatHistoryEvent`            | `common.LimitChatHistoryEvent` | Gekürzter Verlauf           |
| `StandaloneQuestionCondenserEvent` | `common`                       | Frage-Neuformulierung       |

## Benutzerdefinierte Ereignisse

Benutzerdefinierte Ereignisse sind Pydantic-Modelle. Alle Felder erfordern Typannotationen:

```python
from swiss_ai_hub.core.events.control.control_event import ControlEvent

class AnalysisCompleteEvent(ControlEvent):
    summary: str
    confidence: float
    findings: list[str]
    metadata: dict | None = None
```

::: warning Die Stop-Ereignis-Einschränkung
Kein Schritt darf von `StopEvent` oder einer seiner Unterklassen als Eingabeparameter abhängen. Wenn ein `StopEvent` emittiert wird, wird die Ausführung beendet und nachfolgende Schritte werden nicht geplant. Einzelheiten und das korrekte Muster finden Sie im
[Ausführungsmodell](../9_execution_model/#the-dangling-stop-violation).
:::
