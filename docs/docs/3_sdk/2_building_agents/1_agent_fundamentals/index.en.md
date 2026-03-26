---
title: Agent Fundamentals
---

# Agent Fundamentals

An agent is a self-contained, event-driven workflow. It processes an input through a series of operations to produce a
final output. The best agents are focused, doing one thing well.

This page covers the essential building blocks and the core mechanics that power every agent.

## How It Works: The Agent Dispatcher

Behind the scenes, a component called the **Agent Dispatcher** orchestrates your workflow. Understanding its three main
jobs makes building agents much easier:

1. **Introspection**: When an agent starts, the dispatcher inspects all methods marked with the `@step` decorator. It
   analyzes their parameters and return types to build a map of your workflow before it runs.
2. **Event Routing**: The dispatcher acts as a central router. When one step **returns** an event, the dispatcher
   catches it and delivers it to the *next* step that is designed to **accept** that event type. This is how your steps
   are automatically chained together.
3. **Dependency Injection**: The dispatcher automatically provides - or "injects" - necessary objects like configuration
   and context directly into your step methods based on their type hints. You don't create these objects; you just ask
   for them.

With the dispatcher handling the **how** you can focus on the **what**: defining your agent's logic.

## Events: The Data and Control Flow

Events are the lifeblood of an agent. They are simple Pydantic models that carry data and direct the workflow.

### Control vs. Display Events

There are two primary categories of events:

- **`ControlEvent`**: These direct the workflow's execution path. Steps **return** `ControlEvent`s to trigger the next
  part of the process. The workflow begins with a `StartEvent` and ends when a step returns a `StopEvent`.
- **`DisplayEvent`**: These provide information to a user interface, like showing the agent's "thoughts" or streaming
  back a response. They are **emitted** within a step and never affect the agent's logic.

This separation ensures that UI concerns cannot break your core workflow.

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # 1. Emit a DisplayEvent to the UI (does not affect workflow)
    await displayer.display_thought("Processing the user's request...")

    # 2. Return a ControlEvent to advance the workflow
    return OutputEvent(result="done")
```

### Defining Custom Events

You'll create custom `ControlEvent`s to pass data between your steps. Simply inherit from `ControlEvent` and add your
Pydantic fields. The most common starting event for a conversational agent is the built-in `UserMessageEvent`.

```python
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent

# A custom event to carry data from one step to another
class DocumentProcessedEvent(ControlEvent):
    document_id: str
    summary: str
    confidence_score: float
```

## Steps: The Units of Work

A step is an `async` method that performs a single, logical operation. The `@step` decorator registers it with the
dispatcher and configures its behavior.

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
A fresh `Agent` instance is created for **every** step execution. Do not store state on `self` — it will be lost.
Multiple steps for the same run may execute in parallel on different instances. Use events to pass data between steps.
:::

### Step return types

| Return type        | Behavior                            |
| ------------------ | ----------------------------------- |
| `EventA`           | Single event published              |
| `EventA \| EventB` | One event published (branching)     |
| `list[EventA]`     | Multiple events published (fan-out) |
| `None`             | Side-effect only, no event          |

### Internationalized step names

Use `LocaleString` for step names and descriptions that appear in the UI:

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

Translation files live in `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/<agent_name>/` with one YAML file
per locale (`en.yml`, `de.yml`, etc.). Lookup order: Local agent translations, agent scope, library, English fallback.

## Configuration: Making Agents Reusable

To keep your agent's logic separate from its settings, the SDK uses a strongly-typed configuration system. This allows
you to change an agent's behavior (e.g., switching LLM models) without changing its code.

::: tip UI-Editable Configuration
To make your agent's configuration editable through the Admin UI, see
[Configurable Agent Forms](../8_configurable_agents/). The Form Duality Pattern allows administrators to create and
customize agent profiles without code changes.
:::

### `AgentConfig`: Global Configuration

Define a class that inherits from `AgentConfig` for settings that apply to the entire agent. This object can be injected
into any step.

```python
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from pydantic import Field
from typing import Annotated

class MyAgentConfig(AgentConfig):
    model_name: Annotated[str, Field(description="LLM model name")] = "gpt-4o-mini"
    temperature: Annotated[float, Field(description="The LLM temperature")] = 0.7
```

### `StepConfig`: Step-Specific Configuration

For complex, reusable steps, you can create dedicated `StepConfig` classes. Nest them inside your main `AgentConfig`,
and the dispatcher will automatically inject only the relevant config into the step that needs it.

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

## Dependency Injection: Automatic Parameters

As you've seen, you don't need to manually pass objects like configs or contexts to your steps. The **Agent Dispatcher**
provides them automatically based on the parameter's type hint.

Here are the objects you can have injected:

| Type                 | Scope  | Description                                                               |
| -------------------- | ------ | ------------------------------------------------------------------------- |
| `AgentConfig`        | Run    | Your agent's main configuration object (immutable per run)                |
| `StepConfig`         | Step   | A specific configuration class for a single step                          |
| `RunContext`         | Run    | Valkey-backed KV store, cleared on run completion (30-day TTL safety net) |
| `ThreadContext`      | Thread | Valkey-backed KV store, persistent across runs (no TTL)                   |
| `EventDisplayer`     | Step   | Helper for emitting `DisplayEvent`s to the UI                             |
| `AgentMemory`        | Step   | Long-term memory operations (retrieve, store)                             |
| `LocaleHandler`      | Run    | Internationalization — call `t("key")` for translated strings             |
| `AgentInstanceTopic` | Step   | Metadata: `agent_id`, `thread_id`, `run_id`, `display_id`                 |

This powerful feature keeps your code clean and focused on business logic.

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

## Next Steps

Now that you understand the fundamentals, explore the **[Core Patterns](../2_core_patterns/)** to see how these concepts
are used to build agent workflows.
