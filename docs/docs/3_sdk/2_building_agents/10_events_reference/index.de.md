```yaml
---
title: Ereignisreferenz
source_sha: "9e9f8a61a88a2c9fe05503c6b0c1d949b4103ad22da1feb9a5936f7a432116f7"
---
```

# Ereignisreferenz

Diese Seite bietet eine vollständige Referenz zur Ereignishierarchie, zur Auswahl des richtigen Basisereignisses und
einen Katalog aller verfügbaren Ereignisse.

## Steuerungs-, Anzeige- und kombinierte Ereignisse

Das Framework unterscheidet Ereigniskategorien basierend auf ihrer Auswirkung auf den Workflow:

| Kategorie                 | Basisklasse              | Löst Dispatcher aus | Anwendungsfall                                           |
| :------------------------ | :----------------------- | :------------------ | :------------------------------------------------------- |
| **Steuerung**             | `ControlEvent`           | Ja                  | Workflow-Zustandsübergänge, Schritt-Abhängigkeiten       |
| **Anzeige**               | `DisplayEvent`           | Nein                | UI-Updates, Streaming-Ausgabe, Observability             |
| **Steuerung und Anzeige** | `ControlAndDisplayEvent` | Ja                  | Beides: Workflow wird vorangetrieben UND in UI angezeigt |

**Control-Events** beeinflussen den Kontrollfluss des Workflows. Wenn ein `ControlEvent` veröffentlicht wird, evaluiert
der Dispatcher alle Schritte, um festzustellen, ob neue Schritte ausgeführt werden sollen. Nur `ControlEvent`-Typen
(oder Unterklassen) können Schritt-Input-Anforderungen erfüllen.

**Display-Events** lösen den Dispatcher nicht aus. Verwenden Sie diese für hochfrequente Updates, die in der UI
erscheinen sollen, aber keine erneute Schritt-Evaluierung verursachen dürfen. Eine gestreamte LLM-Antwort kann Hunderte
von `ChunkEvent`-Instanzen pro Minute emittieren; würde man diese zu Control-Events machen, würde dies unnötigen
Dispatcher-Overhead verursachen.

**Kombinierte Events** benötigen beide Verhaltensweisen – sie beeinflussen den Workflow UND erscheinen in der UI. Die
meisten semantischen Events (`LLMEvent`, `RetrieverEvent` usw.) erben von `ControlAndDisplayEvent`.

```python
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent

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

## Events als Fluss-Träger

Events dienen zwei unterschiedlichen Zwecken:

1. **Datenträger:** Transportieren von Werten zwischen Schritten
2. **Fluss-Träger:** Steuern die Ausführungsreihenfolge unabhängig von Daten

Ein Schritt kann von einem Event abhängen, um lediglich die Ausführungsreihenfolge sicherzustellen, ohne Daten von
diesem zu benötigen:

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
    # Unterstrich signalisiert: "Ich benötige dieses Event für die Ablaufsteuerung, nicht für Daten"
    return StopEvent()
```

Die Konvention `_: EventType` weist auf eine Abhängigkeit von der Existenz eines Events und nicht von dessen Inhalt hin.
Dieses Muster ist essenziell für:

- **Bedingte Verzweigung:** Unterschiedliche Schritte werden basierend auf dem emittierten Event-Typ ausgeführt
- **Sequenzierung:** Sicherstellen, dass Schritt B auf Schritt A wartet, ohne die Ausgabedaten von A zu benötigen
- **Synchronisationsbarrieren:** Warten auf ein Signal, dass die Arbeit abgeschlossen ist

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

Wenn Sie ein benutzerdefiniertes Event erstellen, erben Sie von der spezifischsten anwendbaren Basisklasse:

| Wenn Ihr Event Folgendes darstellt...       | Erben Sie von                                                 | Vorteile                                       |
| :------------------------------------------ | :------------------------------------------------------------ | :--------------------------------------------- |
| Workflow-Startbedingung                     | `StartEvent`                                                  | Als Einstiegspunkt erkannt                     |
| Benutzernachricht, die den Workflow startet | `UserMessageEvent`                                            | Chatverlauf, Locale, Benutzeridentität         |
| Workflow-Beendigung                         | `StopEvent`                                                   | Signalisierung der Fertigstellung              |
| Fehler/Fehlfunktion                         | `ExceptionEvent`                                              | Fehlerbehandlungsmuster                        |
| LLM-Aufruf-Ergebnis                         | `LLMEvent`                                                    | Token-Zähler, Nachrichten, OpenInference-Spans |
| Terminale LLM-Antwort                       | `LLMStopEvent`                                                | Kombiniert LLM-Daten mit Workflow-Beendigung   |
| Dokumentenabruf                             | `RetrieverEvent`                                              | Abgerufene Nodes, OpenInference-Spans          |
| Reranking-Operation                         | `RerankerEvent`                                               | Input/Output-Nodes, OpenInference-Spans        |
| Embedding-Generierung                       | `EmbeddingEvent`                                              | Vektoren, Modellinfo, OpenInference-Spans      |
| Tool-/Funktionsaufruf                       | `ToolEvent`                                                   | Tool-Name, Parameter, OpenInference-Spans      |
| Guardrail-Überprüfung                       | `GuardEvent`                                                  | Guard-Ergebnis, OpenInference-Spans            |
| Menschliche Genehmigung erforderlich        | `HumanInTheLoopRequestEvent`                                  | Workflow-Aussetzung, UI-Prompt                 |
| Agenten-Delegierung                         | `AgentInTheLoopRequestEvent`                                  | Cross-Agent-Kommunikation                      |
| Speicherabruf                               | `RetrieveUserMemoryEvent` / `RetrieveOrganizationMemoryEvent` | Speicher-Suchergebnisse                        |
| Speicher-Speicherung                        | `StoreUserMemoryEvent` / `StoreOrganizationMemoryEvent`       | Speicher-Persistenz-Bestätigung                |
| Streaming-Text-Chunk                        | `ChunkEvent`                                                  | Echtzeit-UI-Updates (nur Anzeige)              |
| Agenten-Gedanke/Argumentation               | `ThoughtEvent`                                                | Transparenzanzeige (nur Anzeige)               |
| Kosteninformationen                         | `LLMCostEvent`                                                | Token-Nutzung, Preisgestaltung (nur Anzeige)   |
| Generischer Workflow-Zustand                | `ControlAndDisplayEvent`                                      | Löst Dispatcher aus + UI-Anzeige               |
| Generisches UI-Update                       | `DisplayEvent`                                                | Nur UI, kein Dispatcher-Overhead               |

## Semantische Events und OpenInference

`SemanticEvent`-Unterklassen implementieren die Methode `to_semantic_convention()`, die Attribute erzeugt, die mit der
[OpenInference-Spezifikation](https://github.com/Arize-ai/openinference) kompatibel sind. Dies ermöglicht die
Integration mit:

- **Arize Phoenix:** Trace-Visualisierung und -Debugging
- **Langfuse:** LLM-Observability und -Analysen
- **Jedem OpenTelemetry-kompatiblen System:** Standard-Span-Attribute

```python
from aihub_lib.nats.events.semantic import RetrieverEvent

# RetrieverEvent exportiert automatisch OpenInference-Attribute:
# - openinference.span.kind: "RETRIEVER"
# - retrieval.documents.{i}.document.id
# - retrieval.documents.{i}.document.content
# - retrieval.documents.{i}.document.score

event = RetrieverEvent.from_nodes(retrieved_nodes)
otel_attributes = event.to_semantic_convention()
```

Beim Erstellen von Agents, die Observability benötigen, bevorzugen Sie semantische Events gegenüber generischen
`ControlAndDisplayEvent`:

```python
# Bevorzugt: semantisches Event für Observability
from aihub_lib.nats.events.semantic import RetrieverEvent

@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieverEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieverEvent.from_nodes(nodes)  # OpenInference-kompatibel

# Nicht empfohlen: generisches Event verliert Observability-Vorteile
class MyRetrieveEvent(ControlAndDisplayEvent):
    nodes: list[NodeWithScore]  # Keine OpenInference-Integration
```

## Referenz der verfügbaren Events

### Control-Events (lösen Dispatcher aus)

| Event            | Modul                              | Zweck                               |
| :--------------- | :--------------------------------- | :---------------------------------- |
| `ControlEvent`   | `control.ControlEvent`             | Basisklasse für alle Control-Events |
| `StartEvent`     | `control.start.StartEvent`         | Workflow-Einstiegspunkt             |
| `StopEvent`      | `control.stop.StopEvent`           | Workflow-Beendigung                 |
| `ExceptionEvent` | `control.exception.ExceptionEvent` | Fehler-Signalisierung               |

### Display-Events (nur UI)

| Event          | Modul                  | Zweck                                 |
| :------------- | :--------------------- | :------------------------------------ |
| `DisplayEvent` | `display.DisplayEvent` | Basisklasse für Display-Events        |
| `ChunkEvent`   | `display.ChunkEvent`   | Streaming-Textausgabe                 |
| `ThoughtEvent` | `display.ThoughtEvent` | Transparenz der Agenten-Argumentation |
| `CostEvent`    | `cost.CostEvent`       | Basis für Kostenverfolgung            |
| `LLMCostEvent` | `cost.LLMCostEvent`    | LLM-Token-/Kostenberichterstattung    |

### Semantische Events (OpenInference-kompatibel)

| Event            | Modul                               | OpenInference Span-Typ |
| :--------------- | :---------------------------------- | :--------------------- |
| `SemanticEvent`  | `semantic.SemanticEvent`            | Basisklasse (abstrakt) |
| `LLMEvent`       | `semantic.llm.LLMEvent`             | `LLM`                  |
| `LLMStopEvent`   | `semantic.llm.LLMStopEvent`         | `LLM` (terminal)       |
| `RetrieverEvent` | `semantic.retriever.RetrieverEvent` | `RETRIEVER`            |
| `RerankerEvent`  | `semantic.reranker.RerankerEvent`   | `RERANKER`             |
| `EmbeddingEvent` | `semantic.embedding.EmbeddingEvent` | `EMBEDDING`            |
| `ToolEvent`      | `semantic.tool.ToolEvent`           | `TOOL`                 |
| `GuardEvent`     | `semantic.guard.GuardEvent`         | `GUARDRAIL`            |
| `ChainEvent`     | `semantic.chain.ChainEvent`         | `CHAIN`                |
| `AgentEvent`     | `semantic.agent.AgentEvent`         | `AGENT`                |

### Interaktions-Events

| Event                                    | Modul                         | Zweck                                  |
| :--------------------------------------- | :---------------------------- | :------------------------------------- |
| `UserMessageEvent`                       | `user.UserMessageEvent`       | Benutzerinitiierter Workflow-Start     |
| `HumanInTheLoopRequestEvent`             | `human_in_the_loop.request`   | Basisklasse für HITL-Anfragen          |
| `HumanInTheLoopInputRequestEvent`        | `human_in_the_loop.request`   | Popup mit Texteingabefeld              |
| `HumanInTheLoopConfirmationRequestEvent` | `human_in_the_loop.request`   | Ja-/Nein-Schaltflächenauswahl          |
| `HumanInTheLoopChatRequestEvent`         | `human_in_the_loop.request`   | Chat-Nachricht (Fallback)              |
| `HumanInTheLoopResponseEvent`            | `human_in_the_loop.response`  | Basisklasse für HITL-Antworten         |
| `AgentInTheLoopRequestEvent`             | `agent_in_the_loop.request`   | Delegieren an einen anderen Agent      |
| `AgentInTheLoopResponseEvent`            | `agent_in_the_loop.response`  | Ergebnis des delegierten Agenten       |
| `AgentInTheLoopExceptionEvent`           | `agent_in_the_loop.exception` | Fehler des delegierten Agenten         |
| `BotInTheLoopRequestEvent`               | `bot_in_the_loop.request`     | Nachricht an Teams-/Slack-Kanal senden |
| `BotInTheLoopResponseEvent`              | `bot_in_the_loop.response`    | Antwort von Teams-/Slack-Benutzer      |

**HITL-Helferklassen** (keine Events, aber Workflow-Utilities):

| Helfer                       | UI-Verhalten                                              |
| :--------------------------- | :-------------------------------------------------------- |
| `HumanInTheLoopInput`        | Popup-Dialog für Freitext-Eingabe                         |
| `HumanInTheLoopConfirmation` | Ja-/Nein-Schaltflächenauswahl                             |
| `HumanInTheLoopChat`         | Nachricht im Chat-Stream (Fallback für einfache UIs/APIs) |

### Speicher-Events

| Event                             | Modul             | Zweck                                     |
| :-------------------------------- | :---------------- | :---------------------------------------- |
| `BaseRetrieveMemoryEvent`         | `memory.retrieve` | Basis für Speicherabruf                   |
| `RetrieveUserMemoryEvent`         | `memory.retrieve` | Benutzerbezogener Speicherabruf           |
| `RetrieveOrganizationMemoryEvent` | `memory.retrieve` | Organisationsbezogener Speicherabruf      |
| `BaseStoreMemoryEvent`            | `memory.store`    | Basis für Speicherspeicherung             |
| `StoreUserMemoryEvent`            | `memory.store`    | Benutzerbezogene Speicherspeicherung      |
| `StoreOrganizationMemoryEvent`    | `memory.store`    | Organisationsbezogene Speicherspeicherung |
| `AddMemoryToChatHistoryEvent`     | `memory.history`  | Erweiterter Chat-Verlauf                  |

### Guard-Events

| Event                            | Modul                       | Zweck                                 |
| :------------------------------- | :-------------------------- | :------------------------------------ |
| `GuardAcceptEvent`               | `guard.GuardAcceptEvent`    | Guard akzeptiert                      |
| `GuardRejectionEvent`            | `guard.GuardRejectionEvent` | Guard abgelehnt                       |
| `AgentSuitabilityAcceptEvent`    | `guard`                     | Agent kann Anfrage bearbeiten         |
| `AgentSuitabilityRejectEvent`    | `guard`                     | Agent kann Anfrage nicht bearbeiten   |
| `ContextSufficientAcceptEvent`   | `guard`                     | Ausreichender Kontext verfügbar       |
| `ContextInsufficientRejectEvent` | `guard`                     | Unzureichender Kontext                |
| `SensitiveInfoAcceptEvent`       | `guard`                     | Keine sensiblen Informationen erkannt |
| `SensitiveInfoRejectEvent`       | `guard`                     | Sensible Informationen erkannt        |

### Utility-Events

| Event                              | Modul                          | Zweck                    |
| :--------------------------------- | :----------------------------- | :----------------------- |
| `RouterEvent`                      | `router.RouterEvent`           | LLM-Routing-Entscheidung |
| `LanguageEvent`                    | `common.LanguageEvent`         | Spracherkennung          |
| `LimitChatHistoryEvent`            | `common.LimitChatHistoryEvent` | Gekürzter Chat-Verlauf   |
| `StandaloneQuestionCondenserEvent` | `common`                       | Umformulierung der Frage |

## Benutzerdefinierte Events

Benutzerdefinierte Events sind Pydantic-Modelle. Alle Felder erfordern Typ-Annotationen:

```python
from aihub_lib.nats.events.control.ControlEvent import ControlEvent

class AnalysisCompleteEvent(ControlEvent):
    summary: str
    confidence: float
    findings: list[str]
    metadata: dict | None = None
```

::: warning Die Stop-Event-Einschränkung
Kein Schritt darf von `StopEvent` oder einer Unterklasse als Eingabeparameter abhängen. Wenn ein `StopEvent` emittiert
wird, wird die Ausführung beendet und nachfolgende Schritte werden nicht geplant. Details und das korrekte Muster finden
Sie im [Ausführungsmodell](../9_execution_model/#the-dangling-stop-violation).
:::
