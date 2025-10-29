---
title: Agenten-Grundlagen
source_sha: "996e2901c22a47dabe475bfa2179e82ff8168f4686f119ae7c7b4f70202815ef"
---

# Agenten-Grundlagen

Ein Agent ist ein eigenständiger, ereignisgesteuerter Workflow. Er verarbeitet eine Eingabe durch eine Reihe von Operationen, um eine endgültige Ausgabe zu erzeugen. Die besten Agenten sind fokussiert und erledigen eine Aufgabe gut.

Diese Seite behandelt die wesentlichen Bausteine und die Kernmechanismen, die jeden Agenten antreiben.

## Funktionsweise: Der Agent Dispatcher

Hinter den Kulissen orchestriert eine Komponente namens **Agent Dispatcher** Ihren Workflow. Das Verständnis seiner drei Hauptaufgaben vereinfacht das Erstellen von Agenten erheblich:

1.  **Introspektion**: Wenn ein Agent startet, überprüft der Dispatcher alle mit dem `@step`-Decorator markierten Methoden. Er analysiert deren Parameter und Rückgabetypen, um einen Plan Ihres Workflows zu erstellen, bevor dieser ausgeführt wird.
2.  **Ereignis-Routing**: Der Dispatcher fungiert als zentraler Router. Wenn ein Schritt ein Ereignis **zurückgibt**, fängt der Dispatcher es ab und leitet es an den *nächsten* Schritt weiter, der darauf ausgelegt ist, diesen Ereignistyp zu **akzeptieren**. So werden Ihre Schritte automatisch miteinander verkettet.
3.  **Dependency Injection**: Der Dispatcher stellt – oder „injiziert“ – notwendige Objekte wie Konfiguration und Kontext basierend auf deren Typ-Hints automatisch direkt in Ihre Schrittmethoden bereit. Sie erstellen diese Objekte nicht; Sie fordern sie lediglich an.

Da der Dispatcher das **Wie** handhabt, können Sie sich auf das **Was** konzentrieren: die Definition der Logik Ihres Agenten.

## Ereignisse: Der Daten- und Kontrollfluss

Ereignisse sind das Herzstück eines Agenten. Es sind einfache Pydantic-Modelle, die Daten transportieren und den Workflow steuern.

### Kontroll- vs. Anzeigeereignisse

Es gibt zwei primäre Kategorien von Ereignissen:

  * **`ControlEvent`**: Diese steuern den Ausführungspfad des Workflows. Schritte **geben** `ControlEvent`s **zurück**, um den nächsten Teil des Prozesses auszulösen. Der Workflow beginnt mit einem `StartEvent` und endet, wenn ein Schritt ein `StopEvent` zurückgibt.
  * **`DisplayEvent`**: Diese liefern Informationen an eine Benutzeroberfläche, wie z.B. die „Gedanken“ des Agenten anzuzeigen oder eine Antwort zurückzustreamen. Sie werden innerhalb eines Schritts **ausgegeben** und beeinflussen niemals die Logik des Agenten.

Diese Trennung stellt sicher, dass UI-Belange Ihren Kern-Workflow nicht beeinträchtigen können.

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # 1. Emit a DisplayEvent to the UI (does not affect workflow)
    await displayer.display_thought("Processing the user's request...")

    # 2. Return a ControlEvent to advance the workflow
    return OutputEvent(result="done")
```

### Definieren benutzerdefinierter Ereignisse

Sie erstellen benutzerdefinierte `ControlEvent`s, um Daten zwischen Ihren Schritten zu übergeben. Erben Sie einfach von `ControlEvent` und fügen Sie Ihre Pydantic-Felder hinzu. Das häufigste Start-Ereignis für einen Konversationsagenten ist das eingebaute `UserMessageEvent`.

```python
from aihub_agent.events.ControlEvent import ControlEvent

# A custom event to carry data from one step to another
class DocumentProcessedEvent(ControlEvent):
    document_id: str
    summary: str
    confidence_score: float
```

## Schritte: Die Arbeitseinheiten

Ein Schritt ist eine `async`-Methode, die eine einzelne, logische Operation ausführt. Der `@step`-Decorator registriert sie beim Dispatcher und konfiguriert ihr Verhalten.

```python
from aihub_agent.workflow.decorators.step import step
from aihub_lib.i18n.LocaleString import LocaleString

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

## Konfiguration: Agenten wiederverwendbar machen

Um die Logik Ihres Agenten von seinen Einstellungen zu trennen, verwendet das SDK ein stark typisiertes Konfigurationssystem. Dadurch können Sie das Verhalten eines Agenten ändern (z.B. LLM-Modelle wechseln, ohne seinen Code zu ändern).

### `AgentConfig`: Globale Konfiguration

Definieren Sie eine Klasse, die von `AgentConfig` erbt, für Einstellungen, die für den gesamten Agenten gelten. Dieses Objekt kann in jeden Schritt injiziert werden.

```python
from aihub_lib.agents.AgentConfig import AgentConfig
from pydantic import Field
from typing import Annotated

class MyAgentConfig(AgentConfig):
    model_name: Annotated[str, Field(description="LLM model name")] = "gpt-4o-mini"
    temperature: Annotated[float, Field(description="The LLM temperature")] = 0.7
```

### `StepConfig`: Schrittspezifische Konfiguration

Für komplexe, wiederverwendbare Schritte können Sie spezielle `StepConfig`-Klassen erstellen. Verschachteln Sie sie in Ihrer Haupt-`AgentConfig`, und der Dispatcher injiziert automatisch nur die relevante Konfiguration in den Schritt, der sie benötigt.

::: code-group

```python [Schrittkonfigurationsdefinition]
class SummarizeStepConfig(StepConfig):
    max_length: int = 500
```

```python [In Agentenkonfiguration einbetten]
class MyAgentConfig(AgentConfig):
    summarize_step_settings: SummarizeStepConfig = SummarizeStepConfig()
```

```python [Im Schritt verwenden]
@step()
async def summarize_text(self, event: TextEvent, config: SummarizeStepConfig):
    # The dispatcher injects only the SummarizeStepConfig object
    print(f"Max summary length: {config.max_length}")
    pass
```

:::

## Dependency Injection: Automatische Parameter

Wie Sie gesehen haben, müssen Sie Objekte wie Konfigurationen oder Kontexte nicht manuell an Ihre Schritte übergeben. Der **Agent Dispatcher** stellt sie automatisch basierend auf dem Typ-Hint des Parameters bereit.

Hier sind die wichtigsten Objekte, die Sie injizieren lassen können:

  * **`AgentConfig`**: Das Hauptkonfigurationsobjekt Ihres Agenten.
  * **`StepConfig`**: Eine spezifische Konfigurationsklasse für einen einzelnen Schritt.
  * **`RunContext`**: Ein temporärer Schlüssel-Wert-Speicher für einen *einzelnen* Agentenlauf.
  * **`ThreadContext`**: Ein persistenter Schlüssel-Wert-Speicher für einen Konversations-*Thread*.
  * **`EventDisplayer`**: Eine Hilfsklasse zum Ausgeben von `DisplayEvent`s an die Benutzeroberfläche.

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

Nachdem Sie nun die Grundlagen verstanden haben, erkunden Sie die **[Kernmuster](../2_core_patterns/)**, um zu sehen, wie diese Konzepte zum Aufbau von Agenten-Workflows verwendet werden.
