````markdown
---
title: Testen und Debugging
source_sha: "d583f292aec5702df734201c1bd60423773a2eb7b7b41924fede766a44cdf093"
---

# Testen und Debugging

Das Testen und Debuggen von Agents erfordert aufgrund ihrer ereignisgesteuerten, asynchronen Natur einen anderen Ansatz als bei herkömmlichen Anwendungen.

## Unit-Tests: Direkte Schritt-Aufrufe

Der einfachste Weg, einzelne Schritte zu testen, ist, den Agent zu instanziieren und die Schritt-Methoden direkt mit gemockten Abhängigkeiten aufzurufen:

```python
from unittest.mock import AsyncMock, Mock

async def test_retrieve_step():
    agent = MyAgent()
    event = UserMessageEvent(messages=[...], user=fake_user(), locale="en")
    memory = Mock(spec=AgentMemory)
    memory.search_user_memory = AsyncMock(return_value=MemorySearchResult(...))

    result = await agent.retrieve_step(event, memory)

    assert isinstance(result, RetrieveUserMemoryEvent)
    memory.search_user_memory.assert_called_once()
````

Dieser Ansatz testet die Schrittlogik isoliert ohne Dispatcher, NATS oder sonstige Infrastruktur. Mocken Sie injizierte
Abhängigkeiten (`AgentMemory`, `EventDisplayer`, `RunContext`) und prüfen Sie das zurückgegebene Ereignis.

## Integrationstests: pytest-bdd + AgentTestRunner

Nutzen Sie Behavior-Driven Development (BDD) mit `pytest-bdd` zum Testen vollständiger Agent-Workflows.

### Grundlegende Teststruktur

1. **Feature-Datei** – Beschreiben Sie das Verhalten in natürlicher Sprache

```gherkin
# tests/features/iterative_agent.feature
Feature: Iterative Processing Agent
  An agent that performs iterative processing with configurable limits

  Scenario: Agent processes data with iteration limit
    Given an iterative processing agent with maximum 2 iterations
    When I ask the agent to process some data
    Then the agent should complete all iterations
    And the agent should stop after reaching the limit
    And the processing should be successful
```

2. **Testimplementierung** – Verbinden Sie Gherkin mit Code

::: code-group
```python [Test setup]
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/iterative_agent.feature")

@given(parsers.parse('an iterative processing agent with maximum {max_iterations:d} iterations'))
def _(max_iterations: int):
    return AgentTestRunner(
        agent_type=BoundedLoopAgent,
        agent_config=BoundedLoopAgentConfig(
            agent_id="iterative_agent",
            loop_max=max_iterations
        )
    )
```

```python [Test execution]
@when("I ask the agent to process some data")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Process this data", role=MessageRole.USER)],
                user=fake_user()
            )
        )

@then("the agent should complete all iterations")
def _(agent_runner: AgentTestRunner):
    iteration_events = agent_runner.get_events_of_class(BeginEvent)
    assert len(iteration_events) == 3, f"Expected 3 iterations, got {len(iteration_events)}"
```
:::

## AgentTestRunner: Kern-Testwerkzeug

`AgentTestRunner` bietet eine Sandbox-Umgebung für das Testen von Agents.

### Grundlegende Nutzung

```python
async def test_simple_agent():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig(agent_id="test_agent")
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(...)
        )

    # Assertions
    assert runner.has_stop_event
    stop_event = runner.get_stop_event()
    assert "expected content" in stop_event.final_message
```

### Methoden zur Ereignisinspektion

::: details Verfügbare Methoden
```python
# Check for specific events
assert runner.has_start_event
assert runner.has_stop_event

# Get specific events
stop_event = runner.get_stop_event()
start_event = runner.get_start_event()

# Get events by type
all_events = runner.get_events_of_class(MyCustomEvent)
single_event = runner.get_event_of_class(MyCustomEvent)

# Count events
event_count = len(runner.get_events_of_class(ProcessingEvent))
```
:::

## Debugging-Strategie: Trace-gesteuerte Entwicklung

Herkömmliches Debugging mit Breakpoints funktioniert bei ereignisgesteuerten Agents nicht gut. Verwenden Sie stattdessen
Trace-gesteuertes Debugging.

> [!TIP] Ihr Debugging-Toolkit: Langfuse Tracing (primär), umfassendes Logging, Trigger-Skripte,
> Ereignisfluss-Inspektion.

### Essentielles Werkzeug: trigger.py Skripte

Erstellen Sie `trigger.py`-Skripte, um spezifische Szenarien zu testen:

```python
# my_agent/trigger.py
import asyncio
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

# Aktivieren Sie IMMER das Logging für das Debugging
enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig(
            agent_id="debug_agent"
        )
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="test input", role=MessageRole.USER)],
                user=fake_user()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Interaktives Testen: run.py Skripte

Für Agents, die kontinuierlich laufen müssen:

```python
# my_agent/run.py
import asyncio
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig(agent_id="interactive_agent")
    )

    # Hält den Agent für interaktives Testen am Laufen
    await runner.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Langfuse Tracing: Visuelles Debugging

Langfuse bietet eine Schritt-für-Schritt-Visualisierung der Agent-Ausführung unter `http://localhost:6006`.

**Hauptfunktionen:**

- **Trace-Ansicht** – Sehen Sie die vollständige Workflow-Ausführung
- **Schrittdetails** – Klicken Sie auf Schritte, um Ein-/Ausgaben zu überprüfen
- **Timing-Analyse** – Identifizieren Sie Leistungsengpässe
- **Fehlerverfolgung** – Lokalisieren Sie, wo Fehler auftreten

**Debugging-Workflow:**

1. Führen Sie Ihr `trigger.py`-Skript aus
2. Öffnen Sie die Langfuse UI unter `localhost:6006`
3. Finden Sie den Ausführungs-Trace Ihres Agents
4. Klicken Sie durch die Schritte, um den Ereignisfluss zu überprüfen
5. Identifizieren Sie, wo Dinge schiefgehen

## Tests ausführen

```bash
# Alle Tests ausführen
uv run pytest

# Spezifische Testdatei ausführen
uv run pytest tests/test_my_agent.py

# Mit ausführlicher Ausgabe ausführen
uv run pytest -v tests/

# Mit Coverage ausführen
uv run pytest --cov=aihub_agent tests/
```

## Implementierungs-Checkliste

Verwenden Sie diese Checkliste beim Erstellen oder Überprüfen von Agents:

### Vor der Implementierung

- [ ] Verstehen Sie das [Ausführungsmodell](../9_execution_model/) – Schritte sind ein Abhängigkeitsgraph, keine Sequenz
- [ ] Überprüfen Sie den [Speicher-Lebenszyklus](../5_memory/), wenn Ihr Agent Speicher verwendet
- [ ] Studieren Sie Produktions-Agents: `aihub_agent/agents/RagAgent/`, `ExpertRagAgent/`

### Für jeden Schritt

- [ ] Optionale Parameter (`T | None = None`) haben Vorbedingungen, die sowohl die Konfiguration ALS AUCH die
  Ereignispräsenz prüfen
- [ ] Vorbedingungsparametertypen sind eine Untermenge der injizierbaren Typen des Schritts
- [ ] Der Rückgabetyp zeigt korrekt terminal (`StopEvent`) vs. nicht-terminal an
- [ ] Keine Abhängigkeit von `StopEvent` oder seinen Unterklassen als Eingabeparameter

### Für die Speicherintegration

- [ ] LLM-Schritt verwendet `as_stop_step=False` (gibt `LLMEvent` zurück, nicht `LLMStopEvent`)
- [ ] Speicherschritt hängt von `LLMEvent` ab
- [ ] Der letzte Schritt hat eine Vorbedingung, die auf den Abschluss der Speicherung wartet

### Nach der Implementierung

- [ ] Langfuse/Phoenix Trace zeigt die erwartete Ausführungsreihenfolge
- [ ] Keine doppelten Schrittausführungen (prüfen Sie die
  [optionale Parameterfalle](../9_execution_model/#the-optional-parameter-trap))
- [ ] Keine Ereignisse nach `StopEvent`
- [ ] Tests decken alle Konfigurationsflag-Kombinationen ab

```
```
