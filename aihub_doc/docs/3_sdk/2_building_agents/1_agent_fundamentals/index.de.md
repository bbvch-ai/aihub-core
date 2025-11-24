---
title: Agenten-Grundlagen
source_sha: 7a29777932d6ca0235ff1c62636934b6abfa6a8a032f07a1e7bd9b8abc0daa2b
---

# Agenten-Grundlagen

Ein Agent ist ein eigenständiger, ereignisgesteuerter Workflow. Er verarbeitet eine Eingabe durch eine Reihe von
Operationen, um eine endgültige Ausgabe zu erzeugen. Die besten Agenten sind fokussiert und erledigen eine Sache gut.

Diese Seite behandelt die wesentlichen Bausteine und die Kernmechanismen, die jeden Agenten antreiben.

## Funktionsweise: Der Agent Dispatcher

Hinter den Kulissen orchestriert eine Komponente namens **Agent Dispatcher** Ihren Workflow. Das Verständnis seiner drei
Hauptaufgaben erleichtert das Erstellen von Agenten erheblich:

1. **Introspektion**: Wenn ein Agent startet, inspiziert der Dispatcher alle Methoden, die mit dem `@step`-Decorator
   markiert sind. Er analysiert deren Parameter und Rückgabetypen, um vor der Ausführung eine Karte Ihres Workflows zu
   erstellen.
2. **Event-Routing**: Der Dispatcher fungiert als zentraler Router. Wenn ein Schritt ein Ereignis **zurückgibt**, fängt
   der Dispatcher es ab und liefert es an den *nächsten* Schritt, der für die **Annahme** dieses Ereignistyps konzipiert
   ist. So werden Ihre Schritte automatisch miteinander verkettet.
3. **Dependency Injection**: Der Dispatcher stellt - oder „injiziert“ - automatisch notwendige Objekte wie Konfiguration
   und Kontext direkt in Ihre Schrittmethoden bereit, basierend auf deren Typ-Hints. Sie erstellen diese Objekte nicht;
   Sie fordern sie einfach an.

Da der Dispatcher das **Wie** übernimmt, können Sie sich auf das **Was** konzentrieren: die Definition der Logik Ihres
Agenten.

## Events: Der Daten- und Kontrollfluss

Events sind das Lebenselixier eines Agenten. Es sind einfache Pydantic-Modelle, die Daten tragen und den Workflow
steuern.

### Control- vs. Display-Events

Es gibt zwei primäre Kategorien von Events:

- **`ControlEvent`**: Diese steuern den Ausführungspfad des Workflows. Schritte **geben** `ControlEvent`s **zurück**, um
  den nächsten Teil des Prozesses auszulösen. Der Workflow beginnt mit einem `StartEvent` und endet, wenn ein Schritt
  ein `StopEvent` zurückgibt.
- **`DisplayEvent`**: Diese liefern Informationen an eine Benutzeroberfläche, z. B. indem sie die „Gedanken“ des Agenten
  anzeigen oder eine Antwort streamen. Sie werden innerhalb eines Schritts **emittiert** und beeinflussen niemals die
  Logik des Agenten.

Diese Trennung stellt sicher, dass UI-Belange Ihren Kern-Workflow nicht stören können.

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # 1. Emit a DisplayEvent to the UI (does not affect workflow)
    await displayer.display_thought("Processing the user's request...")

    # 2. Return a ControlEvent to advance the workflow
    return OutputEvent(result="done")
```

### Benutzerdefinierte Events definieren

Sie werden benutzerdefinierte `ControlEvent`s erstellen, um Daten zwischen Ihren Schritten zu übergeben. Erben Sie
einfach von `ControlEvent` und fügen Sie Ihre Pydantic-Felder hinzu. Das häufigste Start-Event für einen
konversationellen Agenten ist das integrierte `UserMessageEvent`.

```python
from aihub_agent.events.ControlEvent import ControlEvent

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

Um die Logik Ihres Agenten von seinen Einstellungen zu trennen, verwendet das SDK ein streng typisiertes
Konfigurationssystem. Dies ermöglicht es Ihnen, das Verhalten eines Agenten (z. B. den Wechsel von LLM-Modellen) zu
ändern, ohne dessen Code zu modifizieren.

### `AgentConfig`: Globale Konfiguration

Definieren Sie eine Klasse, die von `AgentConfig` erbt, für Einstellungen, die für den gesamten Agenten gelten. Dieses
Objekt kann in jeden Schritt injiziert werden.

```python
from aihub_lib.agents.AgentConfig import AgentConfig
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
```python [Definition der Schrittkonfiguration]
class SummarizeStepConfig(StepConfig):
    max_length: int = 500
```

```python [Einbetten in die Agentenkonfiguration]
class MyAgentConfig(AgentConfig):
    summarize_step_settings: SummarizeStepConfig = SummarizeStepConfig()
```

```python [Verwendung im Schritt]
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

Hier sind die Schlüsselobjekte, die Sie injizieren lassen können:

- **`AgentConfig`**: Das Hauptkonfigurationsobjekt Ihres Agenten.
- **`StepConfig`**: Eine spezifische Konfigurationsklasse für einen einzelnen Schritt.
- **`RunContext`**: Ein temporärer Key-Value-Store für einen *einzelnen* Agentenlauf.
- **`ThreadContext`**: Ein persistenter Key-Value-Store für einen Konversations-*Thread*.
- **`EventDisplayer`**: Ein Helfer zum Emittieren von `DisplayEvent`s an die Benutzeroberfläche.

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

Nachdem Sie die Grundlagen verstanden haben, erkunden Sie die **[Kernmuster](../2_core_patterns/)**, um zu sehen, wie
diese Konzepte zum Aufbau von Agenten-Workflows verwendet werden.
