---
title: Ausführungsmodell
source_sha: "05b412645a06ad90027efd39ceb57f169eab963aa2629b389f70172fcf5e4587"
---

# Ausführungsmodell

Das Verständnis des Ausführungsmodells ist für die Entwicklung korrekter Agents unerlässlich. Die meisten Fehler in der Agent-Entwicklung resultieren aus einem Missverständnis, wie der Dispatcher Schritte plant. Diese Seite erklärt die Mechanik im Detail.

## Das DAG-Mentalmodell

Ein Agent ist keine Abfolge von Funktionsaufrufen. Es ist ein **Gerichteter Azyklischer Graph (DAG)**, bei dem Knoten **Schritte** und Kanten **Ereignisse** sind. Die Workflow-Topologie ist implizit und leitet sich vollständig von den Typ-Hinweisen Ihrer `@step`-Methoden ab.

**Schritte deklarieren Datenanforderungen, nicht die Ausführungsreihenfolge.**

Ein Schritt wird ausgeführt, wenn die Workflow-Engine alle seine erforderlichen Parameter bereitstellen kann – nicht, wenn ein vorheriger Schritt ihn "aufruft". Dies hat drei entscheidende Implikationen:

1. Jeder Schritt kann von jedem Ereignis abhängen, einschließlich des ursprünglichen `StartEvent`, unabhängig davon, wie viele Schritte seitdem ausgeführt wurden
2. Parallele Ausführung ist automatisch: Schritte mit unabhängigen Abhängigkeiten werden gleichzeitig ausgeführt
3. Der Workflow ist ein Abhängigkeitsgraph, keine Sequenz

### Der Drei-Phasen-Zyklus des Dispatchers

Der `AgentDispatcher` agiert als reaktiver Zustandsautomat:

1. **Ingestion**: Abonniert das NATS JetStream Subject des Agents und empfängt Ereignisse
2. **Evaluation**: Beim Empfang von Ereignis *e* werden alle Schritte *S* identifiziert, bei denen *e* einem Eingabetyp von *S* entspricht
3. **Trigger**: Ruft Schritt *S* nur dann auf, wenn alle erforderlichen Eingaben im Event Store vorhanden sind

Die Ausführungsreihenfolge ist emergent, nicht präskriptiv.

## Denken in Datenabhängigkeiten

### Zwei Perspektiven

#### Top-down: "Was habe ich, was mache ich als Nächstes?"

Beginnen Sie mit der Eingabe, fahren Sie mit der Ausgabe fort. Natürlich für sequentielle Pipelines, fördert aber lineare Ketten und unnötige Datenübergabe.

#### Bottom-up: "Was brauche ich, was liefert es?"

Beginnen Sie mit der gewünschten Ausgabe, arbeiten Sie rückwärts. Identifiziert auf natürliche Weise alle Datenabhängigkeiten und macht direkte Abhängigkeiten vom `StartEvent` offensichtlich.

### Der entscheidende Unterschied

**Top-down erzeugt dies (problematisch):**

```python
@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieveEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieveEvent(nodes=nodes, user_query=event.user_query)  # Passing query forward

@step()
async def respond(self, event: RetrieveEvent) -> StopEvent:
    return await generate(event.user_query, event.nodes)  # Accessing passed-through data
```

Das Feld `user_query` auf `RetrieveEvent` ist eine **Pass-Through-Verschmutzung** — das Ereignis transportiert Daten, die es semantisch nicht repräsentiert, nur um sie weiterzuleiten.

**Bottom-up erzeugt dies (korrekt):**

```python
@step()
async def respond(
    self,
    retrieve_event: RetrieveEvent,
    user_event: UserMessageEvent,  # Direct dependency on original event
) -> StopEvent:
    return await generate(user_event.user_query, retrieve_event.nodes)
```

Jedes Ereignis enthält nur die Daten, die es semantisch repräsentiert. Der `respond`-Schritt deklariert genau, was er benötigt: die abgerufenen Knoten *und* die ursprüngliche Benutzernachricht.

### Der vereinheitlichte Ansatz

1. **Skizzieren Sie top-down**, um den logischen Fluss zu verstehen
2. **Verfeinern Sie bottom-up**, um wahre Abhängigkeiten zu identifizieren
3. **Validieren Sie** beide Richtungen

Fragen Sie für jeden Schritt:

- *Top-down:* Welche Transformation führt dieser Schritt durch?
- *Bottom-up:* Was ist die minimale Menge an Daten, die dieser Schritt benötigt?

## Schritt-Ausführungsisolation

::: warning
Für **jede** Schrittausführung wird eine neue `Agent`-Instanz erstellt. Speichern Sie keinen Zustand auf `self` – er geht zwischen den Schritten verloren. Mehrere Schritte für denselben Run können parallel auf verschiedenen Instanzen ausgeführt werden.
:::

Verwenden Sie Ereignisse, um Daten zwischen Schritten zu übergeben, `RunContext` für Schleifenzähler und `ThreadContext` für den Zustandsübergreifenden Run.

## Ausführungsregeln

### Die Regel der minimal realisierbaren Eingabe

Ein Schritt wird in dem Moment ausgeführt, in dem seine minimal erforderlichen Eingaben erfüllt sind.

Gegeben sei ein Schritt *S* mit:

- **R(S)** = Menge der erforderlichen Parameter (ohne Standardwert)
- **O(S)** = Menge der optionalen Parameter (getypt als `T | None = None`)
- **E** = Menge der verfügbaren Ereignisse

**Auslösebedingung:** Die Ausführung erfolgt, wenn **R(S) ⊆ E** — alle erforderlichen Parametertypen im Event Store verfügbar sind.

- Erforderliche Parameter: aus passenden Ereignissen injiziert
- Optionale Parameter: injiziert, falls vorhanden, sonst `None`

### Das Race-Condition-Problem

Betrachten Sie einen Schritt mit sowohl erforderlichen als auch optionalen Ereignisparametern:

```python
@step()
async def merge(self, primary: EventA, secondary: EventB | None = None) -> OutputEvent:
    ...
```

**Ausführungssequenz:**

| Zeit | Ereignis trifft ein | R(S) erfüllt | O(S) erfüllt | Ergebnis                                          |
| ---- | ------------------- | ------------ | ------------ | ------------------------------------------------- |
| t1   | EventA              | Ja           | Nein         | Schritt wird mit `(EventA, None)` ausgeführt      |
| t2   | EventB              | Ja           | Ja           | Schritt wird **erneut** mit `(EventA, EventB)` ausgeführt |

Der Schritt wurde zweimal ausgeführt. Dies ist kein Bug – es ist das definierte Verhalten. Die Regel der minimal realisierbaren Eingabe löst die Ausführung aus, sobald die erforderlichen Parameter erfüllt sind, und erneut, wenn optionale Parameter eintreffen.

::: warning
Verwenden Sie keine optionalen Ereignisparameter, um auf Daten zu "warten", die möglicherweise später eintreffen. Verwenden Sie stattdessen `@precondition`.
:::

### Die sechs Ausführungsregeln

| Regel   | Aussage                                                     | Folge der Verletzung                                        |
| ------ | ----------------------------------------------------------- | ----------------------------------------------------------- |
| **R1** | Schritte werden ausgeführt, wenn R(S) ⊆ E                    | Race Conditions mit optionalen Parametern                   |
| **R2** | Schritte können pro Run mehrfach ausgeführt werden          | Doppelte Verarbeitung, verschwendete Ressourcen             |
| **R3** | `list[Event]` Parameter lösen bei jedem neuen Ereignis aus  | Unerwartete erneute Ausführung ohne Precondition oder `FixedList` |
| **R4** | Nach `StopEvent` dürfen keine Ereignisse veröffentlicht werden | Illegaler Workflow-Zustand                                  |
| **R5** | Preconditions steuern die Ausführung                        | Deadlock, wenn Precondition nie erfüllt wird               |
| **R6** | Alle Ereignisse bleiben bis zum Abschluss des Runs bestehen | Späte Schritte können auf frühe Ereignisse zugreifen        |

## Synchronisations-Primitive

### Der `@precondition`-Decorator

Eine Precondition ist eine Gatekeeper-Funktion, die vor der Schrittlogik ausgeführt wird.

**Mechanik:**

- Der Dispatcher ruft die Precondition mit der gleichen Dependency Injection auf wie die Schritte
- Wenn sie `False` zurückgibt, wird der Schritt nicht geplant
- Die Precondition wird bei jedem neuen Ereignis erneut evaluiert

**Kritische Einschränkung:** Precondition-Parameter müssen eine **Untermenge** der injizierbaren Typen des Schritts sein. Parameternamen sind irrelevant; Dependency Injection löst nach Typ auf.

```python
from aihub_agent.workflow.decorators.precondition import precondition

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

Wenn ein Schrittparameter als `list[EventType]` getypt ist, wird der Schritt bei **jedem neuen Ereigniseingang** ausgeführt:

```python
@step()
async def aggregate(self, results: list[ResultEvent]) -> StopEvent:
    # Executes every time a ResultEvent arrives
    ...
```

**Ausführungssequenz für 3 erzeugte Ereignisse:**

| Ereigniseingang    | Listeninhalte                                    | Schritt wird ausgeführt |
| ------------------ | ------------------------------------------------ | ----------------------- |
| ResultEvent #1     | [ResultEvent #1]                                 | Ja                      |
| ResultEvent #2     | [ResultEvent #1, ResultEvent #2]                 | Ja                      |
| ResultEvent #3     | [ResultEvent #1, ResultEvent #2, ResultEvent #3] | Ja                      |

Der Schritt wird 3 Mal ausgeführt. Dies folgt aus der Regel der minimal realisierbaren Eingabe: Eine Liste der Länge 1 erfüllt `list[T]`. Ereignisse in der Liste sind nach Ankunftszeit geordnet.

### FixedList für zur Kompilierzeit bekannte Anzahlen

Wenn Sie die genaue Anzahl der Ereignisse zum Zeitpunkt der Definition kennen, verwenden Sie `FixedList`, um zu blockieren, bis alle Ereignisse verfügbar sind:

```python
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import FixedList

N = 5

@step()
async def aggregate(self, results: FixedList(ResultEvent, N)) -> StopEvent:
    # Executes once when exactly N ResultEvents are available
    ...
```

`FixedList` erfordert, dass *N* zum Zeitpunkt der Definition bekannt ist.

### Precondition mit erwarteter Anzahl

Wenn die Anzahl zur Laufzeit bestimmt wird (z.B. aus der Konfiguration), verwenden Sie eine Precondition:

```python
@precondition()
async def check_all_arrived(results: list[ResultEvent], config: AgentConfig) -> bool:
    return len(results) >= config.expected_count

@step(precondition=check_all_arrived)
async def aggregate(self, results: list[ResultEvent], config: AgentConfig) -> StopEvent:
    # Executes once when expected count reached
    ...
```

### Ereignisauflösungsstrategie

Beim Binden von Ereignissen an Schrittparameter:

1. **Feste Sammlung:** `FixedList(Event, N)` blockiert, bis genau *N* Ereignisse verfügbar sind, und gibt dann alle *N* zurück
2. **Unbegrenzte Liste:** `list[Event]` gibt alle Ereignisse dieses Typs zurück, die derzeit verfügbar sind; der Schritt wird bei jedem neuen Ereignis erneut ausgeführt
3. **Einzelinstanz:** Wenn das auslösende Ereignis dem Parametertyp entspricht, wird diese Instanz verwendet. Andernfalls wird das zuletzt erstellte Ereignis dieses Typs verwendet.

## Technische Einschränkungen (Anti-Pattern)

### Die "Dangling Stop"-Verletzung

**Einschränkung:** Kein Schritt darf von `StopEvent` oder einer Unterklasse als Eingabeparameter abhängen.

Wenn ein `StopEvent` emittiert wird, endet der Run. Nachfolgende Schritte werden nicht geplant.

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

**Einschränkung:** Daten müssen zwischen Schritten über Ereignisse fließen, nicht über `RunContext`.

Kontextbasierte Datenübergabe erzeugt unsichtbare Abhängigkeiten, bricht den DAG und verursacht Race Conditions.

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

**Ausnahme:** `RunContext` ist nur für den Kontrollflusszustand gültig (Schleifenzähler, Rekursionstiefe, Wiederholungsversuche).

### Die "Config Lie"-Verletzung

**Einschränkung:** Prüfen Sie `AgentConfig` nicht innerhalb eines Schritts, um zu bestimmen, ob Sie auf ein Ereignis hätten warten sollen.

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

Der Dispatcher fragt nach Typ. Nachfolgende Schritte können unvorhersehbar ausgelöst werden oder die falsche Instanz verarbeiten.

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

### Schritt wird mehrfach ausgeführt

**Symptom:** Phoenix/Langfuse Trace zeigt doppelte Schrittausführungen.

**Grundursache:** Optionale Parameter ohne Precondition. Der Schritt löst aus, wenn R(S) ⊆ E, und dann erneut, wenn optionale Ereignisse eintreffen.

**Diagnose:**

1. Überprüfen Sie die Schrittsignatur auf `param: T | None = None`
2. Verifizieren Sie, dass `@step(precondition=...)` vorhanden ist
3. Verifizieren Sie, dass die Precondition sowohl die Konfiguration ALS AUCH das Vorhandensein des Ereignisses überprüft

**Lösung:** Fügen Sie eine Precondition hinzu, die `False` zurückgibt, bis alle erwarteten Ereignisse eingetroffen sind.

### Schritt wird nie ausgeführt

**Symptom:** Schritt fehlt im Trace.

**Grundursache:** Precondition gibt nie `True` zurück, oder das erforderliche Ereignis wird nie von einem vorgeschalteten Schritt emittiert.

**Diagnose:**

1. Fügen Sie der Precondition Logging hinzu
2. Verifizieren Sie, dass vorgeschaltete Schritte die erwarteten Ereignisse emittieren
3. Überprüfen Sie Konfigurationsflags – eine deaktivierte Funktion kann die Ereignisemission verhindern

**Lösung:** Stellen Sie sicher, dass die Precondition deaktivierte Funktionen berücksichtigt: `if not config.enable_feature: return True`

### Ereignisse nach StopEvent

**Symptom:** Trace zeigt Ereignisse, die nach `StopEvent` datiert sind.

**Grundursache:** Ein Schritt hängt von `StopEvent` oder einer Unterklasse (wie `LLMStopEvent`) ab, oder ein asynchroner Schritt wird nach der Beendigung abgeschlossen.

**Lösung:** Verwenden Sie `LLMEvent` (nicht `LLMStopEvent`) mit `as_stop_step=False`, und fügen Sie dann einen expliziten letzten Schritt mit einer Precondition hinzu.

### Precondition-Parameter-Fehlübereinstimmung

**Symptom:** Laufzeitfehler aufgrund unauflösbarer Parameter.

**Grundursache:** Precondition fordert einen Typ an, der im Kontext des Schritts nicht injizierbar ist.

**Lösung:** Stellen Sie sicher, dass die Parametertypen der Precondition eine Untermenge der injizierbaren Typen des Schritts sind. Parameternamen sind irrelevant; nur die Typen müssen übereinstimmen.

## Checkliste zur Implementierung

### Vor der Implementierung

- [ ] Ausführungssemantik verstehen (diese Seite)
- [ ] Überprüfen Sie den [Speicherlebenszyklus](../5_memory/), falls Sie Speicher verwenden
- [ ] Studieren Sie Produktions-Agents in `aihub_agent/agents/RagAgent/` und `ExpertRagAgent/`

### Für jeden Schritt

- [ ] Optionale Parameter haben Preconditions, die die Konfiguration UND das Vorhandensein von Ereignissen überprüfen
- [ ] Precondition-Parametertypen sind eine Untermenge der injizierbaren Typen des Schritts
- [ ] Der Rückgabetyp zeigt korrekt terminal (`StopEvent`) vs. nicht-terminal an
- [ ] Keine Abhängigkeit von `StopEvent` oder seinen Unterklassen

### Für die Speicherintegration

- [ ] LLM-Schritt verwendet `as_stop_step=False` (gibt `LLMEvent`, nicht `LLMStopEvent` zurück)
- [ ] Speicherschritt hängt von `LLMEvent` ab
- [ ] Letzter Schritt hat Precondition, die auf den Abschluss der Speicherung wartet

### Nach der Implementierung

- [ ] Trace zeigt die erwartete Ausführungsreihenfolge (Langfuse oder Phoenix)
- [ ] Keine doppelten Schrittausführungen
- [ ] Keine Ereignisse nach `StopEvent`
- [ ] Tests decken alle Kombinationen von Konfigurationsflags ab
