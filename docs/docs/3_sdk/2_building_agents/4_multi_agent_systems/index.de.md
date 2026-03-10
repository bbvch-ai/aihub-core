---
title: Multi-Agenten-Systeme
source_sha: 587629f6979d56af49624027a5fd53761b232109704e5748afd72ba7e7b1780c
---

# Multi-Agenten-Systeme

Komplexe Probleme lassen sich oft am besten lösen, indem man sie in kleinere, überschaubare Teile zerlegt. Das **Agent
in the Loop (AITL)**-Muster ermöglicht es Ihnen, Multi-Agenten-Systeme zu erstellen, bei denen ein primärer
**Orchestrator**-Agent spezifische Aufgaben an einen oder mehrere spezialisierte **Worker**-Agents delegieren kann.

**Wann es zu verwenden ist**:

- Um modulare, wiederverwendbare Komponenten zu erstellen (z.B. einen Agent, der nur Dokumente zusammenfasst).
- Um Belange zu trennen (z.B. ein Agent für die Datenbeschaffung, ein anderer für die Analyse).
- Um komplexe Ketten oder parallele Workflows zu erstellen, die die Stärken mehrerer Agents kombinieren.

## Funktionsweise

Das AITL-Muster wird durch ein Trio von Events verwaltet, die die Delegation, Ausführung und Antwort zwischen Agents
orchestrieren.

1. **Orchestrator sendet eine Anfrage**: Der Orchestrator-Agent gibt ein `AgentInTheLoop.request`-Event zurück. Dieses
   Event fungiert als Paket, das das `start_event` für den Worker und die Routing-Informationen für die Antwort enthält.
   Dies pausiert den Workflow des Orchestrators.
2. **Worker führt seine Aufgabe aus**: Der Dispatcher liefert das `start_event` an den angegebenen Worker-Agent. Der
   Worker führt seinen eigenen, in sich geschlossenen Workflow aus, völlig ohne zu wissen, dass er von einem anderen
   Agent aufgerufen wurde.
3. **Worker schließt ab und antwortet**: Wenn der Worker fertig ist, gibt er ein `StopEvent` (oder ein `ExceptionEvent`,
   falls er fehlschlägt) zurück. Das System verpackt dieses abschließende Event automatisch entweder in ein
   `AgentInTheLoop.response` oder `AgentInTheLoop.exception`-Event.
4. **Orchestrator nimmt die Arbeit wieder auf**: Der Dispatcher leitet das Antwort- oder Ausnahme-Event zurück an den
   Orchestrator, der seinen Workflow in einem separaten Schritt fortsetzt, der zur Behandlung des Ergebnisses konzipiert
   ist.

Die `AgentInTheLoop`-Helferklasse vereinfacht diesen Prozess, indem sie eine praktische `invoke`-Methode zur Erstellung
des Request-Events bereitstellt.

______________________________________________________________________

## Kernmuster: Orchestrator und Worker

Dieses Beispiel zeigt einen `OrchestratorAgent`, der einen `WorkerAgent` bittet, eine einfache Berechnung durchzuführen.
Beachten Sie, dass der `WorkerAgent` lediglich ein standardmäßiger, in sich geschlossener Agent ist.

**Referenz**: `playground/minimal_workflow/agent_in_the_loop_workflow/`

::: code-group
```python [OrchestratorAgent.py]
from aihub_lib.nats.events.agent_in_the_loop.AgentInTheLoop import AgentInTheLoop

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

## Kontext-Sharing

Sie können steuern, welche Kontexte vom Orchestrator an den Worker weitergegeben werden. Dies ist nützlich, um eine
konsistente Konversation oder UI-Erfahrung aufrechtzuerhalten.

- `share_thread_id=True` (Standard): Der Worker teilt sich denselben Konversationsspeicher (`ThreadContext`) wie der
  Orchestrator.
- `share_display_id=True` (Standard): Die `DisplayEvent`s des Workers erscheinen im selben UI-Stream wie die des
  Orchestrators.
- `share_run_id=False` (Standard): Der Worker wird in einem eigenen, unabhängigen Run ausgeführt.

```python
AgentInTheLoop.invoke(
    agent_id="specialized_agent",
    agent_class="SpecializedAgent",
    start_event=event,
    share_thread_id=True,      # Share conversation memory
    share_display_id=True,     # Share UI context
    share_run_id=False         # Recommended: Keep runs separate
)
```

::: warning
Das Teilen der `run_id` ist eine fortgeschrittene Funktion und kann zu unerwartetem Verhalten führen, da beide Agents in
denselben ephemeren `RunContext` schreiben würden. Es ist fast immer besser, sie auf `False` zu belassen.
:::

## Gängige Multi-Agenten-Muster

### Spezialisierte Verarbeitung (Router)

Ein Orchestrator fungiert als Router, der Aufgaben basierend auf der Eingabe an verschiedene Worker-Agents delegiert.

```python
class DocumentRouterAgent(Agent):
    @step()
    async def route_document(self, event: DocumentEvent) -> AgentInTheLoop.request:
        if event.document_type == "financial":
            # Delegate to the financial analysis agent
            return AgentInTheLoop.invoke(agent_id="financial_analyzer", ...)
        elif event.document_type == "legal":
            # Delegate to the legal analysis agent
            return AgentInTheLoop.invoke(agent_id="legal_analyzer", ...)
```

### Sequentielle Agent-Kette

Ein Workflow, bei dem die Ausgabe eines Worker-Agents zur Eingabe für den nächsten wird und so eine
Verarbeitungspipeline entsteht.

```python
class ProcessingChainAgent(Agent):
    @step()
    async def extract_data(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        # First agent in the chain
        return AgentInTheLoop.invoke(agent_id="data_extractor", ...)

    @step()
    async def validate_data(self, response: AgentInTheLoop.response) -> AgentInTheLoop.request:
        # The result from the first agent is used to start the second
        extracted_data = response.stop_event.result
        validation_event = ProcessingEvent(data=extracted_data)
        return AgentInTheLoop.invoke(agent_id="data_validator", start_event=validation_event)
```

### Parallele Agenten-Ausführung (Fan-Out)

Ein Orchestrator delegiert dieselbe Aufgabe gleichzeitig an mehrere Agents und aggregiert anschließend deren Antworten.

```python
class ParallelProcessorAgent(Agent):
    @step()
    async def fan_out(self, event: UserMessageEvent) -> list[AgentInTheLoop.request]:
        # Return a list of requests to trigger parallel execution
        return [
            AgentInTheLoop.invoke(agent_id="processor_a", ...),
            AgentInTheLoop.invoke(agent_id="processor_b", ...)
        ]

    @step()
    async def combine_results(self, responses: list[AgentInTheLoop.response]) -> StopEvent:
        # This step waits for all responses before running
        results = [r.stop_event.result for r in responses]
        return StopEvent(final_message=f"Combined results: {results}")
```
