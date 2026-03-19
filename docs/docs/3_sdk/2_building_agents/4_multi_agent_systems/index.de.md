---
title: Multi-Agent-Systeme
source_sha: "be9dc0d866f7059a8bfdaf8fe413829491598acad71ff91b78f6d2d261ebfd17"
---

# Multi-Agent-Systeme

Komplexe Probleme lassen sich oft am besten lösen, indem man sie in kleinere, überschaubare Teile zerlegt. Das **Agent in the Loop (AITL)**-Muster ermöglicht es Ihnen, Multi-Agent-Systeme zu erstellen, bei dem ein primärer **Orchestrator**-Agent spezifische Aufgaben an einen oder mehrere spezialisierte **Worker**-Agents delegieren kann.

**Wann einsetzen**:

- Um modulare, wiederverwendbare Komponenten zu erstellen (z.B. einen Agenten, der nur Dokumente zusammenfasst).
- Um Zuständigkeiten zu trennen (z.B. einen Agenten für die Datenbeschaffung, einen anderen für die Analyse).
- Um komplexe Ketten oder parallele Workflows aufzubauen, die die Stärken mehrerer Agents kombinieren.

## Funktionsweise

Das AITL-Muster wird durch ein Trio von Events verwaltet, die die Delegation, Ausführung und Antwort zwischen Agents orchestrieren.

1.  **Orchestrator sendet eine Anfrage**: Der Orchestrator-Agent gibt ein `AgentInTheLoop.request`-Event zurück. Dieses Event fungiert als Paket, das das `start_event` für den Worker und die Routing-Informationen für die Antwort enthält. Dies pausiert den Workflow des Orchestrators.
2.  **Worker führt seine Aufgabe aus**: Der Dispatcher liefert das `start_event` an den angegebenen Worker-Agent. Der Worker führt seinen eigenen, selbstständigen Workflow aus, ohne zu wissen, dass er von einem anderen Agenten aufgerufen wurde.
3.  **Worker schliesst ab und antwortet**: Wenn der Worker seine Aufgabe beendet, gibt er ein `StopEvent` zurück (oder ein `ExceptionEvent`, falls er fehlschlägt). Das System verpackt dieses abschliessende Event automatisch entweder in ein `AgentInTheLoop.response`- oder ein `AgentInTheLoop.exception`-Event.
4.  **Orchestrator setzt fort**: Der Dispatcher leitet das Antwort- oder Exception-Event zurück an den Orchestrator, der seinen Workflow in einem separaten Schritt fortsetzt, der dazu dient, das Ergebnis zu verarbeiten.

Die `AgentInTheLoop`-Helferklasse vereinfacht diesen Prozess, indem sie eine praktische `invoke`-Methode zur Erstellung des Request-Events bereitstellt.

______________________________________________________________________

## Kernmuster: Orchestrator und Worker

Dieses Beispiel zeigt einen `OrchestratorAgent`, der einen `WorkerAgent` bittet, eine einfache Berechnung durchzuführen. Beachten Sie, dass der `WorkerAgent` lediglich ein standardmässiger, selbstständiger Agent ist.

**Referenz**: `playground/minimal_workflow/agent_in_the_loop_workflow/`

::: code-group
```python [OrchestratorAgent.py]
from swiss_ai_hub.core.events.agent.aitl.agent_in_the_loop import AgentInTheLoop

class OrchestratorAgent(Agent):
    @step()
    async def delegate_task(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        # 1. Delegate the task to the WorkerAgent
        return AgentInTheLoop.invoke(
            agent_id="worker_agent",
            agent_class="WorkerAgent",
            start_event=event  # Pass the original event to the worker
        )

    @step()
    async def handle_result(self, response: AgentInTheLoop.response) -> StopEvent:
        # 3a. This step runs if the worker succeeds
        result = response.stop_event.result
        return StopEvent(final_message=f"Worker succeeded with result: {result}")

    @step()
    async def handle_error(self, response: AgentInTheLoop.exception) -> StopEvent:
        # 3b. This step runs if the worker fails
        error_message = response.exception_event.message
        return StopEvent(final_message=f"Worker failed: {error_message}")
```

```python [WorkerAgent.py]
class WorkerAgent(Agent):
    @step()
    async def process_number(self, event: UserMessageEvent) -> ExtractNumberEvent:
        # 2. The worker agent performs its logic...
        number = int(event.messages[-1].content)
        return ExtractNumberEvent(number=number)

    @step()
    async def calculate_result(self, event: ExtractNumberEvent) -> WorkerStopEvent:
        # ...and returns its own custom StopEvent with a result.
        return WorkerStopEvent(result=event.number * 2)
```
:::

## Kontextfreigabe

Sie können steuern, welche Kontexte vom Orchestrator an den Worker weitergegeben werden. Dies ist nützlich, um eine konsistente Konversation oder Benutzeroberflächen-Erlebnis zu gewährleisten.

- `share_thread_id=True` (Standard): Der Worker teilt sich den gleichen Konversationsspeicher (`ThreadContext`) wie der Orchestrator.
- `share_display_id=True` (Standard): Die `DisplayEvent`s des Workers erscheinen im gleichen UI-Stream wie die des Orchestrators.
- `share_run_id=False` (Standard): Der Worker führt in seinem eigenen, unabhängigen Run aus.

```python
AgentInTheLoop.invoke(
    agent_id="specialized_agent",
    agent_class="SpecializedAgent",
    start_event=event,
    share_thread_id=True,      # Konversationsspeicher teilen
    share_display_id=True,     # UI-Kontext teilen
    share_run_id=False         # Empfohlen: Runs getrennt halten
)
```

::: warning
Das Teilen der `run_id` ist eine fortgeschrittene Funktion und kann zu unerwartetem Verhalten führen, da beide Agents in denselben ephemeren `RunContext` schreiben würden. Es ist fast immer besser, es auf `False` zu belassen.
:::

## Gängige Multi-Agent-Muster

### Spezialisierte Verarbeitung (Router)

Ein Orchestrator fungiert als Router, der Aufgaben basierend auf der Eingabe an verschiedene Worker-Agents delegiert.

```python
class DocumentRouterAgent(Agent):
    @step()
    async def route_document(self, event: DocumentEvent) -> AgentInTheLoop.request:
        if event.document_type == "financial":
            # An den Finanzanalyse-Agenten delegieren
            return AgentInTheLoop.invoke(agent_id="financial_analyzer", ...)
        elif event.document_type == "legal":
            # An den Rechtsanalyse-Agenten delegieren
            return AgentInTheLoop.invoke(agent_id="legal_analyzer", ...)
```

### Sequenzielle Agentenkette

Ein Workflow, bei dem die Ausgabe eines Worker-Agenten zur Eingabe für den nächsten wird und so eine Verarbeitungspipeline entsteht.

```python
class ProcessingChainAgent(Agent):
    @step()
    async def extract_data(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        # Erster Agent in der Kette
        return AgentInTheLoop.invoke(agent_id="data_extractor", ...)

    @step()
    async def validate_data(self, response: AgentInTheLoop.response) -> AgentInTheLoop.request:
        # Das Ergebnis des ersten Agenten wird verwendet, um den zweiten zu starten
        extracted_data = response.stop_event.result
        validation_event = ProcessingEvent(data=extracted_data)
        return AgentInTheLoop.invoke(agent_id="data_validator", start_event=validation_event)
```

### Parallele Agentenausführung (Fan-Out)

Ein Orchestrator delegiert dieselbe Aufgabe gleichzeitig an mehrere Agents und aggregiert dann deren Antworten.

```python
class ParallelProcessorAgent(Agent):
    @step()
    async def fan_out(self, event: UserMessageEvent) -> list[AgentInTheLoop.request]:
        # Eine Liste von Anfragen zurückgeben, um die parallele Ausführung auszulösen
        return [
            AgentInTheLoop.invoke(agent_id="processor_a", ...),
            AgentInTheLoop.invoke(agent_id="processor_b", ...)
        ]

    @step()
    async def combine_results(self, responses: list[AgentInTheLoop.response]) -> StopEvent:
        # Dieser Schritt wartet auf alle Antworten, bevor er ausgeführt wird
        results = [r.stop_event.result for r in responses]
        return StopEvent(final_message=f"Kombinierte Ergebnisse: {results}")
```
