---
title: Agent-Grundlagen
source_sha: 0656fcfb1f8fccaa63407af4a27307317bbeb4ed1925776c9e9a88626e938894
---

# Agent-Grundlagen

Ein Agent ist ein eigenständiger, ereignisgesteuerter Workflow. Er verarbeitet eine Eingabe durch eine Reihe von
Operationen, um eine endgültige Ausgabe zu erzeugen. Die besten Agents sind fokussiert und erledigen eine Sache gut.

Diese Seite behandelt die wesentlichen Bausteine und die Kernmechanismen, die jeden Agent antreiben.

## So funktioniert's: Der Agent-Dispatcher

Hinter den Kulissen orchestriert eine Komponente namens **Agent Dispatcher** Ihren Workflow. Das Verständnis seiner drei
Hauptaufgaben erleichtert das Erstellen von Agents erheblich:

1. **Introspektion**: Wenn ein Agent startet, inspiziert der Dispatcher alle Methoden, die mit dem `@step`-Decorator
   markiert sind. Er analysiert deren Parameter und Rückgabetypen, um eine Karte Ihres Workflows zu erstellen, bevor
   dieser ausgeführt wird.
2. **Ereignis-Routing**: Der Dispatcher fungiert als zentraler Router. Wenn ein Schritt ein Ereignis **zurückgibt**,
   fängt der Dispatcher es ab und leitet es an den *nächsten* Schritt weiter, der darauf ausgelegt ist, diesen
   Ereignistyp zu **akzeptieren**. So werden Ihre Schritte automatisch miteinander verkettet.
3. **Dependency Injection**: Der Dispatcher stellt – oder "injiziert" – automatisch notwendige Objekte wie Konfiguration
   und Kontext direkt in Ihre Schrittmethoden basierend auf deren Typ-Hints bereit. Sie erstellen diese Objekte nicht;
   Sie fordern sie einfach an.

Da der Dispatcher das **Wie** übernimmt, können Sie sich auf das **Was** konzentrieren: die Definition der Logik Ihres
Agents.

## Ereignisse: Der Daten- und Kontrollfluss

Ereignisse sind das Herzstück eines Agents. Es sind einfache Pydantic-Modelle, die Daten tragen und den Workflow
steuern.

### Kontroll- vs. Anzeige-Ereignisse

Es gibt zwei primäre Kategorien von Ereignissen:

- **`ControlEvent`**: Diese steuern den Ausführungspfad des Workflows. Schritte **geben** `ControlEvent`s **zurück**, um
  den nächsten Teil des Prozesses auszulösen. Der Workflow beginnt mit einem `StartEvent` und endet, wenn ein Schritt
  ein `StopEvent` zurückgibt.
- **`DisplayEvent`**: Diese liefern Informationen an eine Benutzeroberfläche, z. B. indem sie die "Gedanken" des Agents
  anzeigen oder eine Antwort streamen. Sie werden innerhalb eines Schritts **ausgegeben** und beeinflussen niemals die
  Logik des Agents.

Diese Trennung stellt sicher, dass UI-Belange Ihren Kern-Workflow nicht beeinträchtigen können.

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # 1. Ein DisplayEvent an die UI ausgeben (beeinflusst den Workflow nicht)
    await displayer.display_thought("Processing the user's request...")

    # 2. Ein ControlEvent zurückgeben, um den Workflow voranzutreiben
    return OutputEvent(result="done")
```

### Benutzerdefinierte Ereignisse definieren

Sie erstellen benutzerdefinierte `ControlEvent`s, um Daten zwischen Ihren Schritten zu übergeben. Erben Sie einfach von
`ControlEvent` und fügen Sie Ihre Pydantic-Felder hinzu. Das häufigste Start-Ereignis für einen konversationellen Agent
ist das integrierte `UserMessageEvent`.

```python
from aihub_agent.events.ControlEvent import ControlEvent

# Ein benutzerdefiniertes Ereignis zum Übertragen von Daten von einem Schritt zum anderen
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
    name=LocaleString(de="Dokument verarbeiten"),
    description=LocaleString(de="Extrahiert Text und erstellt eine Zusammenfassung."),
    max_executions_per_run=1, # Verhindert versehentliche Schleifen
    stop_on_error=True       # Stoppt den Workflow, wenn dieser Schritt fehlschlägt
)
async def process_document(self, event: DocumentUploadEvent) -> DocumentProcessedEvent:
    # Hier die Schrittlogik...
    return DocumentProcessedEvent(...)
```

## Konfiguration: Agents wiederverwendbar machen

Um die Logik Ihres Agents von seinen Einstellungen zu trennen, verwendet das SDK ein stark typisiertes
Konfigurationssystem. Dies ermöglicht es Ihnen, das Verhalten eines Agents (z.B. den Wechsel von LLM-Modellen) zu
ändern, ohne dessen Code zu modifizieren.

::: tip Über die UI bearbeitbare Konfiguration
Um die Konfiguration Ihres Agents über die Admin-UI bearbeitbar zu machen, siehe
[Konfigurierbare Agent-Formulare](../8_configurable_agents/). Das Form Duality Pattern ermöglicht Administratoren,
Agent-Profile ohne Codeänderungen zu erstellen und anzupassen.
:::

### `AgentConfig`: Globale Konfiguration

Definieren Sie eine Klasse, die von `AgentConfig` erbt, für Einstellungen, die für den gesamten Agent gelten. Dieses
Objekt kann in jeden Schritt injiziert werden.

```python
from aihub_lib.agents.AgentConfig import AgentConfig
from pydantic import Field
from typing import Annotated

class MyAgentConfig(AgentConfig):
    model_name: Annotated[str, Field(description="LLM-Modellname")] = "gpt-4o-mini"
    temperature: Annotated[float, Field(description="Die LLM-Temperatur")] = 0.7
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

```python [In Agent-Konfiguration einbetten]
class MyAgentConfig(AgentConfig):
    summarize_step_settings: SummarizeStepConfig = SummarizeStepConfig()
```

```python [Im Schritt verwenden]
@step()
async def summarize_text(self, event: TextEvent, config: SummarizeStepConfig):
    # Der Dispatcher injiziert nur das SummarizeStepConfig-Objekt
    print(f"Maximale Zusammenfassungslänge: {config.max_length}")
    pass
```
:::

## Dependency Injection: Automatische Parameter

Wie Sie gesehen haben, müssen Sie Objekte wie Konfigurationen oder Kontexte nicht manuell an Ihre Schritte übergeben.
Der **Agent Dispatcher** stellt sie automatisch basierend auf dem Typ-Hint des Parameters bereit.

Hier sind die Schlüsselobjekte, die Sie injizieren lassen können:

- **`AgentConfig`**: Das Hauptkonfigurationsobjekt Ihres Agents.
- **`StepConfig`**: Eine spezifische Konfigurationsklasse für einen einzelnen Schritt.
- **`RunContext`**: Ein temporärer Key-Value-Store für eine *einzelne* Agent-Ausführung.
- **`ThreadContext`**: Ein persistenter Key-Value-Store für einen Konversations-*Thread*.
- **`EventDisplayer`**: Ein Helfer zum Ausgeben von `DisplayEvent`s an die UI.

Diese leistungsstarke Funktion hält Ihren Code sauber und auf die Geschäftslogik fokussiert.

```python
@step()
async def complex_step(
    self,
    event: InputEvent,
    config: MyAgentConfig,         # Injiziert
    run_context: RunContext,       # Injiziert
    displayer: EventDisplayer      # Injiziert
) -> StopEvent:
    # Die injizierten Objekte zur Ausführung verwenden
    await displayer.display_thought(f"Using model: {config.model_name}")
    await run_context.set("processed_items", 1)
    return StopEvent(final_message="Done.")
```

## Nächste Schritte

Nachdem Sie die Grundlagen verstanden haben, erkunden Sie die **[Core Patterns](../2_core_patterns/)**, um zu sehen, wie
diese Konzepte zum Aufbau von Agent-Workflows verwendet werden.
