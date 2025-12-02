---
title: Testen und Debuggen
source_sha: 0d7ba1c5f7571d1f0b851e3e2f59201efd1222f5ead6df1aeb29d37510b81afd
---

# Testen und Debuggen

Das Testen und Debuggen von Agents erfordert aufgrund ihrer ereignisgesteuerten, asynchronen Natur einen anderen Ansatz
als bei traditionellen Anwendungen.

## Test-Framework: pytest-bdd + AgentTestRunner

Nutzen Sie Behavior-Driven Development (BDD) mit `pytest-bdd` zum Testen von Agent-Workflows.

### Grundlegende Teststruktur

1. **Feature-Datei** - Beschreiben Sie das Verhalten in natürlicher Sprache

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

2. **Test-Implementierung** - Verbinden Sie Gherkin mit Code

::: code-group
```python [Test-Setup]
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/iterative_agent.feature")

@given(parsers.parse('an iterative processing agent with maximum {max_iterations:d} iterations'))
def _(max_iterations: int):
    return AgentTestRunner(
        agent_type=BoundedLoopAgent,
        default_agent_config=BoundedLoopAgentConfig(
            agent_id="iterative_agent",
            loop_max=max_iterations
        )
    )
```

```python [Test-Ausführung]
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

## AgentTestRunner: zentrales Testwerkzeug

`AgentTestRunner` bietet eine Sandbox-Umgebung zum Testen von Agents.

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

Traditionelles Debugging mit Breakpoints funktioniert bei ereignisgesteuerten Agents nicht gut. Verwenden Sie
stattdessen Trace-gesteuertes Debugging.

> [!TIPP] Ihr Debugging-Toolkit: Phoenix Tracing (primär), umfassendes Logging, Trigger-Skripte,
> Ereignisfluss-Inspektion.

### Essenzielles Werkzeug: trigger.py Skripte

Erstellen Sie `trigger.py` Skripte, um bestimmte Szenarien zu testen:

```python
# my_agent/trigger.py
import asyncio
from aihub_lib.testing.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

# ALWAYS enable logging for debugging
enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        default_agent_config=MyAgentConfig(
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
from aihub_lib.testing.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        default_agent_config=MyAgentConfig(agent_id="interactive_agent")
    )

    # Keeps agent running for interactive testing
    await runner.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Phoenix Tracing: visuelles Debugging

Phoenix bietet eine Schritt-für-Schritt-Visualisierung der Agent-Ausführung unter `http://localhost:6006`.

**Hauptmerkmale:**

- **Trace-Ansicht** - Sehen Sie die vollständige Workflow-Ausführung
- **Schrittdetails** - Klicken Sie auf Schritte, um Ein-/Ausgaben zu inspizieren
- **Timing-Analyse** - Identifizieren Sie Leistungsengpässe
- **Fehlerverfolgung** - Lokalisieren Sie, wo Fehler auftreten

**Debugging-Workflow:**

1. Führen Sie Ihr `trigger.py` Skript aus
2. Öffnen Sie die Phoenix UI unter `localhost:6006`
3. Finden Sie den Ausführungs-Trace Ihres Agents
4. Klicken Sie sich durch die Schritte, um den Ereignisfluss zu inspizieren
5. Identifizieren Sie, wo etwas schiefgeht

## Tests ausführen

```bash
# Run all tests (excluding cloud dependencies)
poetry run pytest -k "not azure"

# Run specific test file
poetry run pytest tests/test_my_agent.py

# Run with verbose output
poetry run pytest -v tests/

# Run with coverage
poetry run pytest --cov=aihub_agent tests/
```
