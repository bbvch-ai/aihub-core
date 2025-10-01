---
title: Agent Fundamentals
index: 1
---

# Agent Fundamentals

An **`Agent`** is a self-contained, event-driven workflow. 
Its purpose is to perform a specific task by processing an input (`StartEvent`) through a series of operations (`Steps`) to produce a final output (`StopEvent`). 
A well-designed agent should **do one thing and do it well**.

## Design Contexts

When building an agent, consider its potential roles:

  * **As an Assistant:** A conversational agent responding directly to user input.
  * **As a Process Worker:** An automated component in a larger, non-interactive workflow.
  * **As a Sub-Agent:** A specialized tool called by another agent to perform a task.

Designing with flexibility in mind—for example, by not limiting inputs to only user messages—allows your agent to be reused across these different contexts.


## Core Architecture

The framework's architecture is event-driven and modular, built upon three primary components: **Configuration**, **Steps**, and **Events**. A central **workflow engine** orchestrates their interaction to execute complex tasks.

  * **The Agent** is the top-level class that encapsulates the entire workflow.
  * **Configuration** provides static, injectable settings for the agent and its steps.
  * **Steps** are individual methods that perform a single unit of work.
  * **Events** are data objects that trigger steps and pass information between them.

The engine's primary role is to route events produced by one step to the next step that is designed to consume them, injecting the necessary configuration and utilities along the way.


## Configuration

Configuration provides a powerful way to control an agent's runtime behavior without changing its code. This allows the same agent logic to be reused for different purposes.

### `AgentConfig`: Global Configuration

The `AgentConfig` class holds settings that apply to the entire agent, such as its name, description, and any shared parameters like model names or system prompts. You will typically create a custom subclass of `AgentConfig` for your agent.

Any step in your workflow can access the entire configuration object via dependency injection:

```python
@step()
async def some_step(self, event: InputEvent, config: MyAgentConfig):
    # Access global settings like config.system_prompt
    pass
```

### `StepConfig`: Step-Specific Configuration

For more complex agents, you may want to configure steps individually. The `StepConfig` class enables this. You can create a specific configuration model for a single step, defining only the parameters it needs.

To use it, you define your `StepConfig` subclass and then embed it as an attribute within your main `AgentConfig`. The workflow engine is smart enough to inject **just the specific `StepConfig`** into the step that requests it. This keeps your steps decoupled and focused only on the configuration they care about.

#### Example of Step-Specific Configuration

```python
# 1. Define a config for a specific step
class SummarizeStepConfig(StepConfig):
    max_length: int = 500
    model: str = "gpt-4-turbo"

# 2. Embed it in the main agent config
class MyReportAgentConfig(AgentConfig):
    name: LocaleString = LocaleString(en="Report Agent")
    # Embed the step-specific config
    summarize_text: SummarizeStepConfig = SummarizeStepConfig(max_length=250)

# 3. The step requests ONLY the config it needs
class MyReportAgent(Agent):
    @step()
    async def summarize_text(self, event: TextEvent, config: SummarizeStepConfig):
        # The engine injects the SummarizeStepConfig instance automatically
        print(f"Summarizing to a max length of {config.max_length}...")
        # 'config' here is the SummarizeStepConfig object, not the whole MyReportAgentConfig
        pass
```


## Steps: The Units of Work

A **step** is an `async` method that represents a single, logical operation. It's identified and managed by the `@step` decorator.

### The `@step` Decorator

This decorator does more than just identify a method as a step. It also:

1.  **Enables Dependency Injection:** The engine inspects the method's type hints (`event: MyEvent`, `config: MyConfig`) and automatically provides the required objects. A step must consume one `ControlEvent` to be triggered.
2.  **Attaches Metadata:** You can configure a step's behavior with parameters like a human-readable `name`, error handling rules (`stop_on_error`), or execution limits (`max_executions_per_run`).


```python
@step(name="Process Input", stop_on_error=True, max_executions_per_run=1)
async def process_step(self, event: InputEvent) -> OutputEvent:
    # Step logic here...
    pass
```

### Connecting Steps

Steps are chained together implicitly through events. When one step **returns** a `ControlEvent`, the engine finds the next step that consumes that event type. The workflow continues until a `StopEvent` is returned.

## Events: The Data and Control Flow

Events either control the workflow or display information. They all inherit from a common `BaseEvent`, which provides standardization and enables the engine to automatically register and deserialize different event types.

### Event Hierarchy & Purpose

The two primary branches of events are `ControlEvent` and `DisplayEvent`.

  * `BaseEvent`
      * **`ControlEvent`**: An event that directs the workflow's execution path. These are the events **returned** from steps to trigger subsequent steps.
          * `StartEvent`: A `ControlEvent` that initiates a new agent run. You can create different `StartEvent` subclasses to trigger different starting points in your agent's logic, adding flexibility.
          * `StopEvent` (\*, also a `DisplayEvent`): This special event has a dual role. As a `ControlEvent`, it **terminates the workflow**. As a `DisplayEvent`, it provides the final, user-visible output. This is why it inherits from both.
      * **`DisplayEvent`**: A purely informational event for the user interface (e.g., streaming text, showing thoughts). These events are **emitted from within** a step using the `EventDisplayer` and **never** affect the control flow. This separation ensures that UI-related failures don't break the agent's core logic.

The key distinction is that **steps return `ControlEvent`s to advance the workflow** but **emit `DisplayEvent`s to communicate with the user**.