---
title: Grundlagen von Agents
source_sha: 60fc6ad6b418615c46fd499f02da74da9110e70af2ddc5ca05e978c6e271f17e
---

# Grundlagen von Agents

Ein Agent ist ein eigenständiger, ereignisgesteuerter Workflow. Er verarbeitet eine Eingabe durch eine Reihe von
Operationen, um eine finale Ausgabe zu erzeugen. Die besten Agents sind fokussiert und erledigen eine Aufgabe gut.

Diese Seite behandelt die wesentlichen Bausteine und die Kernmechanismen, die jeden Agent antreiben.

## Funktionsweise: Der Agent Dispatcher

Hinter den Kulissen orchestriert eine Komponente namens **Agent Dispatcher** Ihren Workflow. Das Verständnis seiner drei
Hauptaufgaben erleichtert die Erstellung von Agents erheblich:

1. **Introspektion**: Wenn ein Agent startet, inspiziert der Dispatcher alle mit dem `@step`-Decorator markierten
   Methoden. Er analysiert deren Parameter und Rückgabetypen, um vor der Ausführung eine Map Ihres Workflows zu
   erstellen.
2. **Ereignis-Routing**: Der Dispatcher fungiert als zentraler Router. Wenn ein Schritt ein Event **zurückgibt**, fängt
   der Dispatcher es ab und leitet es an den *nächsten* Schritt weiter, der dafür ausgelegt ist, diesen Event-Typ zu
   **akzeptieren**. So werden Ihre Schritte automatisch miteinander verkettet.
3. **Dependency Injection**: Der Dispatcher stellt – oder „injiziert“ – erforderliche Objekte wie Konfiguration und
   Kontext basierend auf deren Typ-Hints automatisch direkt in Ihre Schrittmethoden bereit. Sie erstellen diese Objekte
   nicht; Sie fordern sie einfach an.

Da der Dispatcher das **Wie** übernimmt, können Sie sich auf das **Was** konzentrieren: die Definition der Logik Ihres
Agents.

## Events: Der Daten- und Kontrollfluss

Events sind das Herzstück eines Agents. Es handelt sich um einfache Pydantic-Modelle, die Daten tragen und den Workflow
steuern.

### ControlEvents vs. DisplayEvents

Es gibt zwei primäre Kategorien von Events:

- **`ControlEvent`**: Diese steuern den Ausführungspfad des Workflows. Schritte **geben** `ControlEvent`s **zurück**, um
  den nächsten Teil des Prozesses auszulösen. Der Workflow beginnt mit einem `StartEvent` und endet, wenn ein Schritt
  ein `StopEvent` zurückgibt.
- **`DisplayEvent`**: Diese liefern Informationen an eine Benutzeroberfläche, z. B. indem sie die „Gedanken“ des Agents
  anzeigen oder eine Antwort zurückstreamen. Sie werden innerhalb eines Schritts **emittiert** und beeinflussen niemals
  die Logik des Agents.

Diese Trennung stellt sicher, dass UI-Belange Ihren Kern-Workflow nicht unterbrechen können.

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # 1. Emit a DisplayEvent to the UI (does not affect workflow)
    await displayer.display_thought("Processing the user's request...")

    # 2. Return a ControlEvent to advance the workflow
    return OutputEvent(result="done")
```

### Definieren von benutzerdefinierten Events

Sie werden benutzerdefinierte `ControlEvent`s erstellen, um Daten zwischen Ihren Schritten zu übergeben. Erben Sie
einfach von `ControlEvent` und fügen Sie Ihre Pydantic-Felder hinzu. Das gebräuchlichste Start-Event für einen
konversationellen Agent ist das integrierte `UserMessageEvent`.

```python
from swiss_ai_hub.core.events.control_event import ControlEvent

# A custom event to carry data from one step to another
class DocumentProcessedEvent(ControlEvent):
    document_id: str
    summary: str
    confidence_score: float
```

## Schritte: Die Arbeitseinheiten

Ein Schritt ist eine `async`-Methode, die eine einzelne, logische Operation ausführt. Der `@step`-Decorator registriert
sie beim Dispatcher und konfiguriert ihr Verhalten.

```python
from swiss_ai_hub.agent.workflow.decorators.step import step
from swiss_ai_hub.core.i18n.locale_string import LocaleString

@step(
    name=LocaleString(en="Process Document"),
    description=LocaleString(en="Extracts text and generates a summary."),
    max_executions_per_run=1, # Prevents accidental loops
    stop_on_error=True       # Halts the workflow if this step fails
)
async def process_document(self, event: DocumentUploadEvent) -> DocumentProcessedEvent:
    # Step logic here...
    return DocumentProcessedEvent(...)
```

::: warning Step execution isolation
Für **jede** Schrittausführung wird eine neue `Agent`-Instanz erstellt. Speichern Sie keinen Zustand auf `self` – dieser
geht verloren. Mehrere Schritte für denselben Run können parallel auf verschiedenen Instanzen ausgeführt werden.
Verwenden Sie Events, um Daten zwischen Schritten zu übergeben.
:::

### Rückgabetypen von Schritten

| Rückgabetyp        | Verhalten                               |
| ------------------ | --------------------------------------- |
| `EventA`           | Einzelnes Event veröffentlicht          |
| `EventA \| EventB` | Ein Event veröffentlicht (Verzweigung)  |
| `list[EventA]`     | Mehrere Events veröffentlicht (Fan-Out) |
| `None`             | Nur Nebenwirkung, kein Event            |

### Internationalisierte Schrittnamen

Verwenden Sie `LocaleString` für Schrittnamen und Beschreibungen, die in der Benutzeroberfläche erscheinen:

```python
from swiss_ai_hub.core.i18n.locale_string import LocaleString

@step(
    name=LocaleString(
        en="Search Knowledge Base",
        de="Wissensdatenbank durchsuchen",
        fr="Rechercher dans la base de connaissances",
        it="Cerca nella base di conoscenza",
    ),
    description=LocaleString(en="Retrieves relevant documents", ...),
)
async def search(self, event: UserMessageEvent, t: LocaleHandler) -> SearchEvent:
    await displayer.display_thought(t("agent.thought.searching"))
    ...
```

Übersetzungsdateien befinden sich in `aihub_agent/i18n/translations/agent/<agent_name>/` mit einer YAML-Datei pro Locale
(`en.yml`, `de.yml` usw.). Suchreihenfolge: Lokale Agent-Übersetzungen, Agent-Scope, Bibliothek, englischer Fallback.

## Konfiguration: Agents wiederverwendbar machen

Um die Logik Ihres Agents von seinen Einstellungen zu trennen, verwendet das SDK ein stark typisiertes
Konfigurationssystem. Dies ermöglicht es Ihnen, das Verhalten eines Agents zu ändern (z. B. LLM-Modelle zu wechseln),
ohne seinen Code zu ändern.

::: tip UI-Editable Configuration
Um die Konfiguration Ihres Agents über die Admin-Benutzeroberfläche editierbar zu machen, siehe
[Konfigurierbare Agent-Formulare](/de/docs/8_configurable_agents/). Das Form-Dualitäts-Muster ermöglicht es
Administratoren, Agent-Profile ohne Codeänderungen zu erstellen und anzupassen.
:::

### `AgentConfig`: Globale Konfiguration

Definieren Sie eine Klasse, die von `AgentConfig` erbt, für Einstellungen, die für den gesamten Agent gelten. Dieses
Objekt kann in jeden Schritt injiziert werden.

```python
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from pydantic import Field
from typing import Annotated

class MyAgentConfig(AgentConfig):
    model_name: Annotated[str, Field(description="LLM model name")] = "gpt-4o-mini"
    temperature: Annotated[float, Field(description="The LLM temperature")] = 0.7
```

### `StepConfig`: Schrittspezifische Konfiguration

Für komplexe, wiederverwendbare Schritte können Sie dedizierte `StepConfig`-Klassen erstellen. Verschachteln Sie diese
in Ihrer Haupt-`AgentConfig`, und der Dispatcher injiziert automatisch nur die relevante Konfiguration in den Schritt,
der sie benötigt.

::: code-group
```python [Step config definition]
class SummarizeStepConfig(StepConfig):
    max_length: int = 500
```

```python [Embed in agent config]
class MyAgentConfig(AgentConfig):
    summarize_step_settings: SummarizeStepConfig = SummarizeStepConfig()
```

```python [Use in step]
@step()
async def summarize_text(self, event: TextEvent, config: SummarizeStepConfig):
    # The dispatcher injects only the SummarizeStepConfig object
    print(f"Max summary length: {config.max_length}")
    pass
```
:::

## Dependency Injection: Automatische Parameter

Wie Sie gesehen haben, müssen Sie Objekte wie Konfigurationen oder Kontexte nicht manuell an Ihre Schritte übergeben.
Der **Agent Dispatcher** stellt sie automatisch basierend auf dem Typ-Hint des Parameters bereit.

Hier sind die Objekte, die Sie injizieren lassen können:

| Typ                  | Gültigkeitsbereich | Beschreibung                                                                  |
| -------------------- | ------------------ | ----------------------------------------------------------------------------- |
| `AgentConfig`        | Run                | Das Hauptkonfigurationsobjekt Ihres Agents (unveränderlich pro Run)           |
| `StepConfig`         | Step               | Eine spezifische Konfigurationsklasse für einen einzelnen Schritt             |
| `RunContext`         | Run                | Redis-gestützter KV-Speicher, ephemer (wird bei Abschluss des Runs gelöscht)  |
| `ThreadContext`      | Thread             | Redis-gestützter KV-Speicher, persistent über Runs hinweg                     |
| `EventDisplayer`     | Step               | Hilfsklasse zum Emittieren von `DisplayEvent`s an die UI                      |
| `AgentMemory`        | Step               | Langzeitgedächtnis-Operationen (abrufen, speichern)                           |
| `LocaleHandler`      | Run                | Internationalisierung — rufen Sie `t("key")` für übersetzte Zeichenketten auf |
| `AgentInstanceTopic` | Step               | Metadaten: `agent_id`, `thread_id`, `run_id`, `display_id`                    |

Diese leistungsstarke Funktion hält Ihren Code sauber und auf die Geschäftslogik konzentriert.

```python
@step()
async def complex_step(
    self,
    event: InputEvent,
    config: MyAgentConfig,         # Injected
    run_context: RunContext,       # Injected
    displayer: EventDisplayer      # Injected
) -> StopEvent:
    # Use the injected objects to perform work
    await displayer.display_thought(f"Using model: {config.model_name}")
    await run_context.set("processed_items", 1)
    return StopEvent(final_message="Done.")
```

## Nächste Schritte

Nachdem Sie die Grundlagen verstanden haben, erkunden Sie die **[Core Patterns](/de/docs/2_core_patterns/)**, um zu
sehen, wie diese Konzepte zum Aufbau von Agent-Workflows verwendet werden.
