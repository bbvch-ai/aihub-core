---
title: Agent fundamentals
index: 1
---

# Agent fundamentals

An agent is a self-contained, event-driven workflow. It processes an input through a series of operations to produce a final output. Each agent should do one thing well.

## Agent design contexts

Consider how your agent might be used:

- **Assistant** - Responds directly to user input in conversations
- **Process worker** - Automated component in larger, non-interactive workflows
- **Sub-agent** - Specialized tool called by other agents

Design flexibly so your agent can work across different contexts.

## Core architecture

The framework uses three components: configuration, steps, and events. A workflow engine orchestrates their interaction.

::: details Architecture components
- **Agent** - Top-level class that encapsulates the workflow
- **Configuration** - Static, injectable settings for the agent and steps
- **Steps** - Individual methods that perform units of work
- **Events** - Data objects that trigger steps and pass information between them
:::

The engine routes events from one step to the next step designed to consume them.

## Configuration

Configuration controls agent behavior without changing code, letting you reuse the same logic for different purposes.

### AgentConfig: global configuration

`AgentConfig` holds settings that apply to the entire agent:

```python
class MyAgentConfig(AgentConfig):
    system_prompt: Annotated[str, Field(description="The system prompt for the LLM")] = "You are a helpful assistant."
    temperature: Annotated[float, Field(description="The LLM temperature")] = 0.7
```

Any step can access the configuration via dependency injection:

```python
@step()
async def process_text(self, event: InputEvent, config: MyAgentConfig):
    # Use config.system_prompt, config.temperature, etc.
    pass
```

### StepConfig: step-specific configuration

For complex agents, configure steps individually using `StepConfig`:

::: code-group

```python [Step config definition]
class SummarizeStepConfig(StepConfig):
    max_length: int = 500
    model: str = "gpt-4-turbo"
```

```python [Embed in agent config]
class MyReportAgentConfig(AgentConfig):
    name: LocaleString = LocaleString(en="Report Agent")
    summarize_text: SummarizeStepConfig = SummarizeStepConfig(max_length=250)
```

```python [Use in step]
class MyReportAgent(Agent):
    @step()
    async def summarize_text(self, event: TextEvent, config: SummarizeStepConfig):
        # Engine injects only the SummarizeStepConfig
        print(f"Max length: {config.max_length}")
        pass
```

:::

The engine automatically injects just the specific configuration each step needs.

## Steps: units of work

A step is an `async` method representing a single operation. The `@step` decorator identifies and manages it.

### @step decorator

The decorator enables dependency injection and attaches metadata:

```python
@step(
    name=LocaleString(en="Process Input"),
    stop_on_error=True,
    max_executions_per_run=1
)
async def process_step(self, event: InputEvent) -> OutputEvent:
    # Step logic here
    return OutputEvent(result="processed")
```

> [!TIP]
> Steps must consume one `ControlEvent` to be triggered.

### Connecting steps

Steps chain together through events. When a step returns a `ControlEvent`, the engine finds the next step that consumes that event type. The workflow continues until a `StopEvent` is returned.

```python
class SimpleAgent(Agent):
    @step()
    async def first_step(self, event: UserMessageEvent) -> ProcessingEvent:
        return ProcessingEvent(data=event.content)

    @step()
    async def second_step(self, event: ProcessingEvent) -> StopEvent:
        return StopEvent(final_message=f"Processed: {event.data}")
```

## Events: data and control flow

Events either control the workflow or display information. They inherit from `BaseEvent` for standardization and automatic registration.

### Event types

Two primary event branches:

- **ControlEvent** - Directs workflow execution path (returned from steps)
- **DisplayEvent** - Provides user interface information (emitted within steps)

::: details Event hierarchy
```
BaseEvent
├── ControlEvent
│   ├── StartEvent (initiates agent run)
│   └── StopEvent (terminates workflow, also DisplayEvent)
└── DisplayEvent (UI information only)
```
:::

### Key distinction

- Steps **return** `ControlEvent`s to advance the workflow
- Steps **emit** `DisplayEvent`s to communicate with users

```python
@step()
async def example_step(self, event: InputEvent, displayer: EventDisplayer) -> OutputEvent:
    # Emit display event (doesn't affect workflow)
    await displayer.display_thought("Processing data...")

    # Return control event (advances workflow)
    return OutputEvent(result="done")
```

> [!IMPORTANT]
> Display events never affect control flow. UI failures won't break your agent's logic.