```markdown
---
title: Ausführungsmodell
source_sha: "5c8cc4d3e6cf7155bd881b5c50564b1bfcfdb928f0504e5938e73d9edcf3b2e2"
---

# Ausführungsmodell

Das Verständnis des Ausführungsmodells ist essenziell für die Entwicklung korrekter Agents. Die meisten Fehler in der Agentenentwicklung resultieren aus einem Missverständnis, wie der Dispatcher Schritte plant. Diese Seite erklärt die Mechanismen detailliert.

## Das DAG-Mentalmodell

Ein Agent ist keine Abfolge von Funktionsaufrufen. Er ist ein **Directed Acyclic Graph (DAG)**, bei dem die Knoten **Schritte** und die Kanten **Ereignisse** sind. Die Workflow-Topologie ist implizit und leitet sich vollständig von den Typ-Hints Ihrer `@step`-Methoden ab.

**Schritte deklarieren Datenanforderungen, nicht die Ausführungsreihenfolge.**

Ein Schritt wird ausgeführt, wenn die Workflow-Engine alle seine benötigten Parameter bereitstellen kann – nicht wenn ein vorheriger Schritt ihn "aufruft". Dies hat drei entscheidende Implikationen:

1. Jeder Schritt kann von jedem Ereignis abhängen, einschliesslich des ursprünglichen `StartEvent`, unabhängig davon, wie viele Schritte seitdem ausgeführt wurden.
2. Parallele Ausführung ist automatisch: Schritte mit unabhängigen Abhängigkeiten werden gleichzeitig ausgeführt.
3. Der Workflow ist ein Abhängigkeitsgraph, keine Sequenz.

### Der dreiphasige Zyklus des Dispatchers

Der `AgentDispatcher` arbeitet als reaktiver Zustandsautomat:

1. **Ingestion**: Abonniert das NATS JetStream Subject des Agents und empfängt Ereignisse.
2. **Evaluation**: Beim Empfang von Ereignis *e* werden alle Schritte *S* identifiziert, bei denen *e* einem Eingabetyp von *S* entspricht.
3. **Trigger**: Ruft Schritt *S* auf, wenn und nur wenn alle erforderlichen Eingaben im Ereignisspeicher vorhanden sind.

Die Ausführungsreihenfolge ist emergent, nicht vorschreibend.

## Denken in Datenabhängigkeiten

### Zwei Perspektiven

#### Top-Down: „Was habe ich, was mache ich als Nächstes?“

Beginnen Sie mit der Eingabe, gehen Sie zur Ausgabe über. Natürlich für sequentielle Pipelines, fördert aber lineare Ketten und unnötige Datenweitergabe.

#### Bottom-Up: „Was brauche ich, was stellt es bereit?“

Beginnen Sie mit der gewünschten Ausgabe, arbeiten Sie rückwärts. Identifiziert natürlich alle Datenabhängigkeiten und macht direkte Abhängigkeiten vom `StartEvent` offensichtlich.

### Der entscheidende Unterschied

**Top-Down erzeugt dies (problematisch):**

```python
@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieveEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieveEvent(nodes=nodes, user_query=event.user_query)  # Passing query forward

@step()
async def respond(self, event: RetrieveEvent) -> StopEvent:
    return await generate(event.user_query, event.nodes)  # Accessing passed-through data
```

Das `user_query`-Feld in `RetrieveEvent` ist eine **Pass-Through-Verschmutzung** – das Ereignis trägt Daten, die es semantisch nicht repräsentiert, nur um sie weiterzuleiten.

**Bottom-Up erzeugt dies (korrekt):**

```python
@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieveEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieveEvent(nodes=nodes)  # Only retrieval-specific data

@step()
async def respond(
    self,
    retrieve_event: RetrieveEvent,
    user_event: UserMessageEvent,  # Direct dependency on original event
) -> StopEvent:
    return await generate(user_event.user_query, retrieve_event.nodes)
```

Jedes Ereignis enthält nur die Daten, die es semantisch repräsentiert. Der `respond`-Schritt deklariert genau, was er benötigt: die abgerufenen Knoten *und* die ursprüngliche Benutzernachricht.

### Der einheitliche Ansatz

1. **Top-Down skizzieren**, um den logischen Fluss zu verstehen.
2. **Bottom-Up verfeinern**, um echte Abhängigkeiten zu identifizieren.
3. **Validieren** Sie beide Richtungen.

Fragen Sie bei jedem Schritt:

- *Top-Down:* Welche Transformation führt dieser Schritt durch?
- *Bottom-Up:* Welches ist der minimale Satz von Daten, den dieser Schritt benötigt?

## Isolation der Schrittausführung

::: warning
Für **jede** Schrittausführung wird eine neue `Agent`-Instanz erstellt. Speichern Sie keinen Zustand in `self` – er geht zwischen den Schritten verloren. Mehrere Schritte für denselben Run können parallel auf verschiedenen Instanzen ausgeführt werden.
:::

Verwenden Sie Ereignisse, um Daten zwischen Schritten zu übergeben, `RunContext` für Schleifenzähler und `ThreadContext` für den Status über Runs hinweg.

## Ausführungsregeln

### Die Regel des minimalen brauchbaren Inputs

Ein Schritt wird in dem Moment ausgeführt, in dem seine minimal erforderlichen Inputs erfüllt sind.

Gegeben sei ein Schritt *S* mit:

- **R(S)** = Menge der erforderlichen Parameter (kein Standardwert)
- **O(S)** = Menge der optionalen Parameter (typisiert als `T | None = None`)
- **E** = Menge der verfügbaren Ereignisse

**Triggerbedingung:** Die Ausführung erfolgt, wenn **R(S) ⊆ E** – alle erforderlichen Parametertypen im Ereignisspeicher verfügbar sind.

- Erforderliche Parameter: aus passenden Ereignissen injiziert
- Optionale Parameter: injiziert, falls vorhanden, sonst `None`

### Das Race Condition Problem

Betrachten Sie einen Schritt mit sowohl erforderlichen als auch optionalen Ereignisparametern:

```python
@step()
async def merge(self, primary: EventA, secondary: EventB | None = None) -> OutputEvent:
    ...
```

**Ausführungssequenz:**

| Zeit | Ereignis trifft ein | R(S) erfüllt | O(S) erfüllt | Ergebnis                                            |
| ---- | ------------------- | ------------ | ------------ | --------------------------------------------------- |
| t1   | EventA              | Ja           | Nein         | Schritt wird mit `(EventA, None)` ausgeführt        |
| t2   | EventB              | Ja           | Ja           | Schritt wird **erneut** mit `(EventA, EventB)` ausgeführt |

Der Schritt wurde zweimal ausgeführt. Dies ist kein Bug – es ist das definierte Verhalten. Die Regel des minimalen brauchbaren Inputs löst die Ausführung aus, sobald die erforderlichen Parameter erfüllt sind, und erneut, wenn optionale Parameter eintreffen.

::: warning
Verwenden Sie keine optionalen Ereignisparameter, um auf Daten zu "warten", die möglicherweise später eintreffen. Verwenden Sie stattdessen `@precondition`.
:::

### Die sechs Ausführungsregeln

| Regel   | Aussage                                                        | Folge der Verletzung                                        |
| ------- | -------------------------------------------------------------- | ----------------------------------------------------------- |
| **R1**  | Schritte werden ausgeführt, wenn R(S) ⊆ E                     | Race Conditions mit optionalen Parametern                   |
| **R2**  | Schritte können mehrmals pro Run ausgeführt                    | Doppelte Verarbeitung, verschwendete Ressourcen             |
| **R3**  | `list[Event]` Parameter lösen bei jedem neuen Ereignis aus     | Unerwartete erneute Ausführung ohne Precondition oder `FixedList` |
| **R4**  | Nach `StopEvent` dürfen keine Ereignisse veröffentlicht werden | Illegaler Workflow-Zustand                                  |
| **R5**  | Preconditions steuern die Ausführung                           | Deadlock, wenn Precondition nie erfüllt wird               |
| **R6**  | Alle Ereignisse bleiben bis zum Abschluss des Runs bestehen   | Späte Schritte können auf frühe Ereignisse zugreifen        |

## Synchronisationsprimitive

### Der `@precondition`-Decorator

Eine Precondition ist eine Gatekeeper-Funktion, die vor der Schrittlogik ausgeführt wird.

**Mechanismen:**

- Der Dispatcher ruft die Precondition mit der gleichen Dependency Injection wie bei Schritten auf.
- Wenn sie `False` zurückgibt, wird der Schritt nicht geplant.
- Die Precondition wird bei jeder neuen Ereignisankunft neu bewertet.

**Kritische Einschränkung:** Precondition-Parameter müssen eine **Untermenge** der injizierbaren Typen des Schritts sein. Parameternamen sind irrelevant; die Dependency Injection löst nach Typ auf.

```python
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition

@precondition()
async def check_ready(
    evt: EventB | None,  # Name differs from step parameter — that's fine
    cfg: AgentConfig,    # Resolved by type, not name
) -> bool:
    if cfg.enable_feature and evt is None:
        return False  # Wait for optional event
    return True

@step(precondition=check_ready)
async def process(
    self,
    required: EventA,
    optional: EventB | None = None,  # Type matches precondition's 'evt'
    config: AgentConfig,             # Type matches precondition's 'cfg'
) -> OutputEvent:
    # Guaranteed: if config.enable_feature, optional is not None
    ...
```

### Listenparameter

Wenn ein Schrittparameter als `list[EventType]` typisiert ist, wird der Schritt bei **jeder neuen Ereignisankunft** ausgeführt:

```python
@step()
async def aggregate(self, results: list[ResultEvent]) -> StopEvent:
    # Executes every time a ResultEvent arrives
    ...
```

**Ausführungssequenz für 3 produzierte Ereignisse:**

| Ereignisankunft  | Listeninhalt                                     | Schritt wird ausgeführt |
| ---------------- | ------------------------------------------------ | ----------------------- |
| ResultEvent #1   | [ResultEvent #1]                                 | Ja                      |
| ResultEvent #2   | [ResultEvent #1, ResultEvent #2]                 | Ja                      |
| ResultEvent #3   | [ResultEvent #1, ResultEvent #2, ResultEvent #3] | Ja                      |

Der Schritt wird 3 Mal ausgeführt. Dies ergibt sich aus der Regel des minimalen brauchbaren Inputs: Eine Liste der Länge 1 erfüllt `list[T]`. Ereignisse in der Liste sind nach Ankunftszeit geordnet.

### FixedList für zur Compile-Zeit bekannte Anzahlen

Wenn Sie die genaue Anzahl der Ereignisse zum Definitionszeitpunkt kennen, verwenden Sie `FixedList`, um zu blockieren, bis alle Ereignisse verfügbar sind:

```python
from swiss_ai_hub.core.workflow.annotations.custom_types.list_of_size import FixedList

N = 5

@step()
async def aggregate(self, results: FixedList(ResultEvent, N)) -> StopEvent:
    # Executes once when exactly N ResultEvents are available
    ...
```

`FixedList` erfordert, dass *N* zum Definitionszeitpunkt bekannt ist.

### Precondition mit erwarteter Anzahl

Wenn die Anzahl zur Laufzeit bestimmt wird (z. B. aus der Konfiguration), verwenden Sie eine Precondition:

```python
@precondition()
async def check_all_arrived(results: list[ResultEvent], config: AgentConfig) -> bool:
    return len(results) >= config.expected_count

@step(precondition=check_all_arrived)
async def aggregate(self, results: list[ResultEvent], config: AgentConfig) -> StopEvent:
    # Executes once when expected count reached
    ...
```

### Strategie zur Ereignisauflösung

Beim Binden von Ereignissen an Schrittparameter:

1. **Feste Sammlung:** `FixedList(Event, N)` blockiert, bis genau *N* Ereignisse verfügbar sind, und gibt dann alle *N* zurück.
2. **Unbegrenzte Liste:** `list[Event]` gibt alle Ereignisse dieses Typs zurück, die aktuell verfügbar sind; der Schritt wird bei jeder neuen Ankunft erneut ausgeführt.
3. **Einzelne Instanz:** Wenn das auslösende Ereignis dem Parametertyp entspricht, wird diese Instanz verwendet. Andernfalls wird das zuletzt erstellte Ereignis dieses Typs verwendet.

## Technische Einschränkungen (Anti-Patterns)

### Die "Dangling Stop"-Verletzung

**Einschränkung:** Kein Schritt darf von `StopEvent` oder einer Unterklasse als Eingabeparameter abhängen.

Wenn ein `StopEvent` ausgegeben wird, wird der Run beendet. Nachfolgende Schritte werden nicht geplant.

```python
# VIOLATION: depending on stop event
@step()
async def cleanup(self, stop: LLMStopEvent) -> CleanupEvent:
    ...  # Never executes

# CORRECT: use non-stop event, then explicit stop
@step()
async def respond(self, event: InputEvent, displayer: EventDisplayer) -> LLMEvent:
    return await displayer.display_llm_stream(..., as_stop_step=False)

@step()
async def cleanup(self, llm: LLMEvent) -> CleanupEvent:
    ...

@step(precondition=cleanup_complete)
async def finalize(self, cleanup: CleanupEvent) -> StopEvent:
    return StopEvent()
```

### Die "Context Smuggle"-Verletzung

**Einschränkung:** Daten müssen zwischen Schritten über Ereignisse fliessen, nicht über `RunContext`.

Kontextbasierte Datenübergabe erzeugt unsichtbare Abhängigkeiten, durchbricht den DAG und verursacht Race Conditions.

```python
# VIOLATION: using context as data bus
@step()
async def step_a(self, event: InputEvent, run_context: RunContext) -> EventA:
    await run_context.set("query", event.query)  # Wrong
    return EventA()

@step()
async def step_b(self, event: EventA, run_context: RunContext) -> OutputEvent:
    query = await run_context.get("query")  # Wrong — invisible dependency
    ...

# CORRECT: direct event dependency
@step()
async def step_b(self, event_a: EventA, original: InputEvent) -> OutputEvent:
    query = original.query  # Explicit, visible dependency
    ...
```

**Ausnahme:** `RunContext` ist nur für den Kontrollfluss-Status gültig (Schleifenzähler, Rekursionstiefe, Wiederholungsverfolgung).

### Die "Config Lie"-Verletzung

**Einschränkung:** Überprüfen Sie `AgentConfig` nicht innerhalb eines Schritts, um zu bestimmen, ob Sie auf ein Ereignis hätten warten sollen.

Zum Zeitpunkt der Ausführung hat der Dispatcher die Planungsentscheidung bereits getroffen. Die Race Condition ist bereits aufgetreten.

```python
# VIOLATION: config check inside step
@step()
async def process(self, required: EventA, optional: EventB | None = None, config: AgentConfig) -> OutputEvent:
    if config.enable_feature and optional is None:
        return None  # Too late — step already executed with None

# CORRECT: precondition prevents premature scheduling
@step(precondition=check_ready)
async def process(self, required: EventA, optional: EventB | None = None, config: AgentConfig) -> OutputEvent:
    # If config.enable_feature, precondition guarantees optional is not None
    ...
```

### Die "Double-Dip"-Verletzung

**Einschränkung:** Verwenden Sie nicht denselben Ereignistyp für mehrere unterschiedliche logische Phasen.

Der Dispatcher fragt nach Typ ab. Nachfolgende Schritte können unvorhersehbar ausgelöst werden oder die falsche Instanz verarbeiten.

```python
# VIOLATION: same event type for different stages
@step()
async def validate(self, event: InputEvent) -> ProcessedEvent:
    return ProcessedEvent(data="validated")

@step()
async def enrich(self, event: ProcessedEvent) -> ProcessedEvent:  # Same type!
    return ProcessedEvent(data="enriched")

# CORRECT: distinct types for each logical state
@step()
async def validate(self, event: InputEvent) -> ValidatedEvent:
    return ValidatedEvent(data="validated")

@step()
async def enrich(self, event: ValidatedEvent) -> EnrichedEvent:
    return EnrichedEvent(data="enriched")
```

### Die Falle der optionalen Parameter

**Einschränkung:** Optionale Parameter ohne Preconditions führen zu erneuter Ausführung.

```python
# Executes twice: once with b=None, again with b=EventB
@step()
async def process(self, a: EventA, b: EventB | None = None) -> OutputEvent:
    ...

# Executes once when precondition satisfied
@step(precondition=check_b_ready)
async def process(self, a: EventA, b: EventB | None = None, config: AgentConfig) -> OutputEvent:
    ...
```

## Fehlerbehebung

### Schritt wird mehrmals ausgeführt

**Symptom:** Phoenix/Langfuse Trace zeigt doppelte Schrittausführungen.

**Grundursache:** Optionale Parameter ohne Precondition. Der Schritt wird ausgelöst, wenn R(S) ⊆ E, dann erneut, wenn optionale Ereignisse eintreffen.

**Diagnose:**

1. Überprüfen Sie die Schrittsignatur auf `param: T | None = None`.
2. Verifizieren Sie, dass `@step(precondition=...)` vorhanden ist.
3. Verifizieren Sie, dass die Precondition sowohl die Konfiguration ALS AUCH das Vorhandensein des Ereignisses überprüft.

**Lösung:** Fügen Sie eine Precondition hinzu, die `False` zurückgibt, bis alle erwarteten Ereignisse eingetroffen sind.

### Schritt wird nie ausgeführt

**Symptom:** Schritt fehlt im Trace.

**Grundursache:** Precondition gibt nie `True` zurück, oder das erforderliche Ereignis wird von einem vorgelagerten Schritt nie emittiert.

**Diagnose:**

1. Fügen Sie Logging zur Precondition hinzu.
2. Verifizieren Sie, dass vorgelagerte Schritte die erwarteten Ereignisse emittieren.
3. Überprüfen Sie Konfigurationsflags – eine deaktivierte Funktion kann die Ereignisemittierung verhindern.

**Lösung:** Stellen Sie sicher, dass die Precondition deaktivierte Funktionen berücksichtigt: `if not config.enable_feature: return True`.

### Ereignisse nach StopEvent

**Symptom:** Trace zeigt Ereignisse mit Zeitstempel nach `StopEvent`.

**Grundursache:** Ein Schritt hängt von `StopEvent` oder einer Unterklasse (wie `LLMStopEvent`) ab, oder ein asynchroner Schritt wird nach der Beendigung abgeschlossen.

**Lösung:** Verwenden Sie `LLMEvent` (nicht `LLMStopEvent`) mit `as_stop_step=False` und fügen Sie dann einen expliziten letzten Schritt mit einer Precondition hinzu.

### Precondition-Parameter-Fehler

**Symptom:** Laufzeitfehler bezüglich nicht auflösbarer Parameter.

**Grundursache:** Precondition fordert einen Typ an, der im Kontext des Schritts nicht injizierbar ist.

**Lösung:** Stellen Sie sicher, dass die Precondition-Parametertypen eine Untermenge der injizierbaren Typen des Schritts sind. Parameternamen sind irrelevant; nur die Typen müssen übereinstimmen.

## Implementierungs-Checkliste

### Vor der Implementierung

- [ ] Ausführungssemantik verstehen (diese Seite)
- [ ] Den [Speicher-Lebenszyklus](../5_memory/) überprüfen, falls Speicher verwendet wird
- [ ] Produktions-Agents in `packages/agent/swiss_ai_hub/agent/agents/rag_agent/` und `expert_rag_agent/` studieren

### Für jeden Schritt

- [ ] Optionale Parameter haben Preconditions, die die Konfiguration UND das Vorhandensein von Ereignissen überprüfen.
- [ ] Precondition-Parametertypen sind eine Untermenge der injizierbaren Typen des Schritts.
- [ ] Der Rückgabetyp zeigt korrekt terminal (`StopEvent`) vs. nicht-terminal an.
- [ ] Keine Abhängigkeit von `StopEvent` oder seinen Unterklassen.

### Für die Speicherintegration

- [ ] LLM-Schritt verwendet `as_stop_step=False` (gibt `LLMEvent` zurück, nicht `LLMStopEvent`).
- [ ] Speicher-Schritt hängt von `LLMEvent` ab.
- [ ] Der finale Schritt hat eine Precondition, die auf den Abschluss der Speicherung wartet.

### Nach der Implementierung

- [ ] Trace zeigt die erwartete Ausführungsreihenfolge (Langfuse oder Phoenix).
- [ ] Keine doppelten Schrittausführungen.
- [ ] Keine Ereignisse nach `StopEvent`.
- [ ] Tests decken alle Konfigurationsflag-Kombinationen ab.
```
