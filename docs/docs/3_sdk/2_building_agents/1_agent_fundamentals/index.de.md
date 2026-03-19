---
title: Grundlagen von Agents
source_sha: "70f315c36182303889884446221631a1f7e2e193f390e7c532c3bb0cfe371d8a"
---

# Grundlagen von Agents

Ein Agent ist ein eigenständiger, ereignisgesteuerter Workflow. Er verarbeitet eine Eingabe durch eine Reihe von Operationen, um eine finale Ausgabe zu erzeugen. Die besten Agents sind fokussiert und erledigen eine Aufgabe gut.

Diese Seite behandelt die wesentlichen Bausteine und die Kernmechanismen, die jeden Agent antreiben.

## So funktioniert's: Der Agent Dispatcher

Hinter den Kulissen orchestriert eine Komponente namens **Agent Dispatcher** Ihren Workflow. Das Verständnis seiner drei Hauptaufgaben erleichtert das Erstellen von Agents erheblich:

1.  **Introspektion**: Wenn ein Agent startet, inspiziert der Dispatcher alle Methoden, die mit dem `@step`-Decorator gekennzeichnet sind. Er analysiert deren Parameter und Rückgabetypen, um eine Karte Ihres Workflows zu erstellen, bevor dieser ausgeführt wird.
2.  **Ereignis-Routing**: Der Dispatcher fungiert als zentraler Router. Wenn ein Schritt ein Ereignis **zurückgibt**, fängt der Dispatcher es ab und liefert es an den *nächsten* Schritt, der für die **Annahme** dieses Ereignistyps konzipiert ist. So werden Ihre Schritte automatisch miteinander verkettet.
3.  **Dependency Injection**: Der Dispatcher stellt – oder „injiziert“ – automatisch notwendige Objekte wie Konfiguration und Kontext direkt in Ihre Schrittmethoden bereit, basierend auf deren Typ-Hints. Sie erstellen diese Objekte nicht; Sie fordern sie einfach an.

Da der Dispatcher das **Wie** übernimmt, können Sie sich auf das **Was** konzentrieren: die Definition der Logik Ihres Agents.

## Ereignisse: Der Daten- und Kontrollfluss

Ereignisse sind das Herzstück eines Agents. Es sind einfache Pydantic-Modelle, die Daten tragen und den Workflow steuern.

### Kontroll- vs. Display-Ereignisse

Es gibt zwei Hauptkategorien von Ereignissen:

-   **`ControlEvent`**: Diese steuern den Ausführungspfad des Workflows. Schritte **geben** `ControlEvent`s **zurück**, um den nächsten Teil des Prozesses auszulösen. Der Workflow beginnt mit einem `StartEvent` und endet, wenn ein Schritt ein `StopEvent` zurückgibt.
-   **`DisplayEvent`**: Diese stellen Informationen für eine Benutzeroberfläche bereit, z. B. indem sie die „Gedanken“ des Agents anzeigen oder eine Antwort zurückstreamen. Sie werden innerhalb eines Schritts **ausgegeben** und beeinflussen niemals die Logik des Agents.

Diese Trennung stellt sicher, dass UI-Belange Ihren Kern-Workflow nicht beeinträchtigen können.

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # 1. Emit a DisplayEvent to the UI (does not affect workflow)
    await displayer.display_thought("Processing the user's request...")

    # 2. Return a ControlEvent to advance the workflow
    return OutputEvent(result="done")
```

### Benutzerdefinierte Ereignisse definieren

Sie erstellen benutzerdefinierte `ControlEvent`s, um Daten zwischen Ihren Schritten zu übergeben. Erben Sie einfach von `ControlEvent` und fügen Sie Ihre Pydantic-Felder hinzu. Das häufigste Start-Ereignis für einen konversationellen Agent ist das integrierte `UserMessageEvent`.

```python
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent

# A custom event to carry data from one step to another
class DocumentProcessedEvent(ControlEvent):
    document_id: str
    summary: str
    confidence_score: float
```

## Schritte: Die Arbeitseinheiten

Ein Schritt ist eine `async`-Methode, die eine einzelne, logische Operation ausführt. Der `@step`-Decorator registriert sie beim Dispatcher und konfiguriert ihr Verhalten.

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

::: warning Isolation der Schrittausführung
Für **jede** Schrittausführung wird eine neue `Agent`-Instanz erstellt. Speichern Sie keinen Zustand auf `self` — er geht verloren. Mehrere Schritte für denselben Durchlauf können parallel auf verschiedenen Instanzen ausgeführt werden. Verwenden Sie Ereignisse, um Daten zwischen Schritten zu übergeben.
:::

### Rückgabetypen von Schritten

| Rückgabetyp        | Verhalten                           |
| :----------------- | :---------------------------------- |
| `EventA`           | Einzelnes Ereignis veröffentlicht    |
| `EventA \| EventB` | Ein Ereignis veröffentlicht (Verzweigung) |
| `list[EventA]`     | Mehrere Ereignisse veröffentlicht (Fan-Out) |
| `None`             | Nur Nebeneffekt, kein Ereignis      |

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

Übersetzungsdateien befinden sich in `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/<agent_name>/` mit einer YAML-Datei pro Locale (`en.yml`, `de.yml` usw.). Suchreihenfolge: Lokale Agent-Übersetzungen, Agent-Scope, Bibliothek, englischer Fallback.

## Konfiguration: Agents wiederverwendbar machen

Um die Logik Ihres Agents von seinen Einstellungen zu trennen, verwendet das SDK ein stark typisiertes Konfigurationssystem. Dies ermöglicht es Ihnen, das Verhalten eines Agents zu ändern (z. B. LLM-Modelle zu wechseln), ohne seinen Code anzupassen.

::: tip Über die Benutzeroberfläche editierbare Konfiguration
Um die Konfiguration Ihres Agents über die Admin-UI editierbar zu machen, siehe [Konfigurierbare Agent-Formulare](../8_configurable_agents/). Das Form Duality Pattern ermöglicht Administratoren, Agent-Profile ohne Codeänderungen zu erstellen und anzupassen.
:::

### ``AgentConfig`: Globale Konfiguration`

Definieren Sie eine Klasse, die von `AgentConfig` erbt, für Einstellungen, die für den gesamten Agent gelten. Dieses Objekt kann in jeden Schritt injiziert werden.

```python
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from pydantic import Field
from typing import Annotated

class MyAgentConfig(AgentConfig):
    model_name: Annotated[str, Field(description="LLM model name")] = "gpt-4o-mini"
    temperature: Annotated[float, Field(description="The LLM temperature")] = 0.7
```

### ``StepConfig`: Schrittspezifische Konfiguration`

Für komplexe, wiederverwendbare Schritte können Sie dedizierte `StepConfig`-Klassen erstellen. Verschachteln Sie diese in Ihrer Haupt-`AgentConfig`, und der Dispatcher injiziert automatisch nur die relevante Konfiguration in den Schritt, der sie benötigt.

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

Wie Sie gesehen haben, müssen Sie Objekte wie Konfigurationen oder Kontexte nicht manuell an Ihre Schritte übergeben. Der **Agent Dispatcher** stellt sie automatisch basierend auf dem Typ-Hint des Parameters bereit.

Hier sind die Objekte, die Sie injizieren lassen können:

| Typ                 | Scope  | Beschreibung                                                    |
| :------------------ | :----- | :-------------------------------------------------------------- |
| `AgentConfig`       | Run    | Das Hauptkonfigurationsobjekt Ihres Agents (unveränderlich pro Lauf) |
| `StepConfig`        | Step   | Eine spezifische Konfigurationsklasse für einen einzelnen Schritt |
| `RunContext`        | Run    | Redis-gestützter KV-Store, ephemer (wird bei Laufabschluss gelöscht) |
| `ThreadContext`     | Thread | Redis-gestützter KV-Store, persistent über Läufe hinweg         |
| `EventDisplayer`    | Step   | Helfer zum Ausgeben von `DisplayEvent`s an die Benutzeroberfläche |
| `AgentMemory`       | Step   | Operationen für Langzeitspeicher (abrufen, speichern)           |
| `LocaleHandler`     | Run    | Internationalisierung – rufen Sie `t("key")` für übersetzte Zeichenketten auf |
| `AgentInstanceTopic`| Step   | Metadaten: `agent_id`, `thread_id`, `run_id`, `display_id`      |

Diese leistungsstarke Funktion hält Ihren Code sauber und auf die Geschäftslogik fokussiert.

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

Nachdem Sie die Grundlagen verstanden haben, erkunden Sie die **[Kernmuster](../2_core_patterns/)**, um zu sehen, wie diese Konzepte zum Aufbau von Agent-Workflows verwendet werden.
