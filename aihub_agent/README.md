---
title: AI-Hub Agents
index: 3
---

# 🤖 AI-Hub Agent Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_agents-core&metric=alert_status&token=d536ea3509f1ddb1ca2b071681be1ee5bac7d212)](https://sonarcloud.io/summary/new_code?id=aihub-core_agents-core)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_agents-core&metric=security_rating&token=d536ea3509f1ddb1ca2b071681be1ee5bac7d212)](https://sonarcloud.io/summary/new_code?id=aihub-core_agents-core)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_agents-core&metric=vulnerabilities&token=d536ea3509f1ddb1ca2b071681be1ee5bac7d212)](https://sonarcloud.io/summary/new_code?id=aihub-core_agents-core)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_agents-core&metric=sqale_rating&token=d536ea3509f1ddb1ca2b071681be1ee5bac7d212)](https://sonarcloud.io/summary/new_code?id=aihub-core_agents-core)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_agents-core&metric=ncloc&token=d536ea3509f1ddb1ca2b071681be1ee5bac7d212)](https://sonarcloud.io/summary/new_code?id=aihub-core_agents-core)

## 1. 🎯 Foundational Knowledge of Agent Development

This section covers the foundational architecture, patterns, and terminology you need to know before building an agent.

::: info
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you
have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_agent`

You are contributing to the **aihub_agent** scope, which contains all agent logic and workflow definitions within the
AI-Hub platform. This scope implements autonomous AI agents designed for proactive process automation—components that
work alongside humans to execute tasks as part of redesigned business processes.

### 📁 Project Structure

The `aihub_agent` scope is organized as follows:

```
aihub_agent/
├── aihub_agent/                # Main package source
│   ├── agents/                 # Core agent implementations (e.g., RagAgent, LLMWrappingAgent)
│   ├── context/                # RunContext and ThreadContext implementation
│   ├── runners/                # AgentRunner and AgentTestRunner
│   ├── workflow/               # Core engine, including the @step decorator
│   └── ...                     # Other core components (tracing, i18n, etc.)
└── playground/                 # Examples, demos, and testing code - START HERE
    ├── agent/                  # Examples of production agents
    └── minimal_workflow/       # Self-contained examples of every core pattern - ESSENTIAL
```

### 🤖 The Agent: A Dispatchable Workflow

::: info Core Concept
An agent is a **dispatchable workflow** that performs structured operations on input data to achieve a pre-defined goal.
Agents follow a step-based approach where complex tasks are broken down into discrete, testable operations.
:::

```python
class Agent(DispatchableWorkflow):
    """
    An agent defines a series of operations performed on input data to achieve a
    pre-defined goal - the agent's output. Each step brings the agent's input
    (StartEvent) one step closer to the desired output (StopEvent).
    """
```

::: tip Key Principles
- **Single Responsibility**: Each agent should do one thing and do it well.
- **Transparency**: All operations are explicit steps that can be traced and debugged.
- **Flexibility**: Agents can function as assistants, process components, or services for other agents.
:::

### 📶 The Event-Driven Architecture

::: info Event Communication
Agents communicate through **events**—structured data objects that represent specific occurrences or states.
:::

- **Control Events**: Manage the workflow lifecycle (`StartEvent`, `StopEvent`, `ExceptionEvent`).
- **Semantic Events**: Carry business logic and data specific to a domain.
- **Display Events**: Used for presenting results to users in a frontend.

### 🏷️ The `@step` Decorator: Building Blocks of Workflows

::: tip Step Decorator
Steps are the fundamental building blocks of agent workflows, defined using the `@step()` decorator. This decorator
orchestrates the flow of events between functions.
:::

```python
@step(
    max_executions_per_run=3,
    stop_on_error=True,
    name=LocaleString(en="Classification Step"),
    description=LocaleString(en="Classifies incoming requests")
)
async def classify_request(self, event: UserMessageEvent) -> ClassificationEvent:
    # Step implementation
    return ClassificationEvent(classification="question")
```

**Key Parameters:**

- `max_executions_per_run`: Limits how many times a step can run within a single execution.
- `stop_on_error`: Controls whether the workflow halts on an exception in this step.
- `name` / `description`: Localized metadata for UI and logging.
- `icon`: An identifier for a UI icon.
- `precondition`: A function that must return `True` for the step to execute.

### 💾 State Management: `RunContext` and `ThreadContext`

::: info Context Types
Agents use two types of context for state management:
:::

- **RunContext**: Short-lived storage for ephemeral data **within a single run**. It's isolated between different runs
  and is ideal for intermediate calculations or temporary caching. It expires after 30 days.
- **ThreadContext**: Persistent storage for state **across multiple runs** within the same conversation thread. It
  maintains conversational history and user preferences, enabling contextual follow-up interactions. It also has a
  30-day TTL.

______________________________________________________________________

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging an agent.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

### 🛠️ Step 1: Create the Agent, Configuration, and Events

::: info
Follow this three-part process to define a new agent. Each part builds on the previous one to create a complete agent
implementation.
:::

1. **Create the Agent Class**: Define the agent's workflow by creating a class that inherits from `Agent` and uses the
   `@step` decorator.
   ```python
   # my_agent/MyAgent.py
   from aihub_agent.agents.Agent import Agent
   from aihub_agent.workflow.decorators.step import step
   # ... other imports

   class MyAgent(Agent):
       @step()
       async def start_step(self, event: UserMessageEvent) -> MyCustomEvent:
           # ...
       @step()
       async def process_step(self, event: MyCustomEvent) -> StopEvent:
           # ...
   ```
2. **Define the Agent Configuration**: Create a Pydantic model inheriting from `AgentConfig` using the **form duality
   pattern**. This allows the same model to define both the UI form (for the Admin UI) and the runtime configuration
   data.
   ```python
   # my_agent/MyAgentConfig.py
   from typing import Annotated
   from aihub_lib.agents.AgentConfig import AgentConfig
   from aihub_lib.i18n.LocaleString import LocaleString
   from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
   from aihub_lib.nats.events.form.constraints import Ge, Le
   from pydantic import Field

   class MyAgentConfig(AgentConfig):
       # Form duality: float for data mode, InputNumber for form mode
       temperature: Annotated[float | InputNumber, Field(description="LLM temperature"), Ge(0.0), Le(1.0)] = 0.7
       confidence_threshold: Annotated[float | InputNumber, Field(description="Minimum confidence"), Ge(0.0), Le(1.0)] = 0.5

       @classmethod
       def as_form(cls) -> "MyAgentConfig":
           """Create form-mode config with FormKit elements for UI rendering."""
           base = AgentConfig.as_form()
           return cls(
               agent_id=base.agent_id,
               name=base.name,
               description=base.description,
               icon=base.icon,
               temperature=InputNumber(label=LocaleString(en="Temperature", de="Temperatur"), min=0.0, max=1.0, step=0.1),
               confidence_threshold=InputNumber(label=LocaleString(en="Confidence Threshold"), min=0.0, max=1.0, step=0.1),
           )
   ```

   ::: tip Form Duality Pattern
The `as_form()` method returns the config with FormKit elements instead of values. When registering with `AgentRunner`,
use form mode. At runtime, the dispatcher injects the actual values from the database.
   :::

3. **Define Custom Events**: If your workflow requires custom data structures to be passed between steps, define them as
   Pydantic models inheriting from `Event`.
   ```python
   # my_agent/events/MyCustomEvent.py
   from aihub_lib.nats.events import Event

   class MyCustomEvent(Event):
       data: Annotated[str, Field(description="Some data")]
       confidence: Annotated[float, Field(description="Certainty level between 0 and 1")]
   ```

### 🧪 Step 2: Write and Run Tests

::: tip Testing with BDD
We use Behavior-Driven Development (BDD) with `pytest-bdd` as the primary method for testing agent workflows.
:::

1. **Write a Feature File**: Describe the agent's behavior in Gherkin syntax.
   ```gherkin
   # tests/features/my_agent.feature
   Feature: My Agent
     Scenario: Test basic functionality
       Given a MyAgent configuration
       When the user sends a message with content: "Hello"
       Then the agent run should complete
   ```
2. **Implement the Test Steps**: Write Python code to implement the Gherkin steps using the `AgentTestRunner`. The test
   runner provides a sandboxed environment to execute the agent and inspect the resulting events.
   ```python
   # tests/test_MyAgent.py
   from aihub_lib.i18n.LocaleString import LocaleString
   from aihub_lib.nats.events import UserMessageEvent
   from aihub_lib.testing.asyncio_utils.bdd import async_test
   from aihub_lib.testing.auth_utils.fake_user import fake_user
   from llama_index.core.base.llms.types import ChatMessage, MessageRole
   from pytest_bdd import given, parsers, scenarios, then, when
   from aihub_agent.runners.AgentTestRunner import AgentTestRunner

   scenarios("./features/my_agent.feature")

   @given("a MyAgent configuration", target_fixture="agent_runner")
   def _():
       return AgentTestRunner(
           agent_type=MyAgent,
           agent_config=MyAgentConfig(
               agent_id="my_agent",
               name=LocaleString(en="My Agent"),
               description=LocaleString(en="Test agent"),
               system_prompt=LocaleString(en="You are a helpful agent"),
               temperature=0.7,
               confidence_threshold=0.5
           ),
       )

   @when(parsers.parse('the user sends a message with content: "{payload}"'))
   @async_test
   async def _(agent_runner: AgentTestRunner, payload: str):
       async with agent_runner.test_run() as topic:
           await agent_runner.send_event_from_topic(
               start_event=UserMessageEvent(
                   messages=[ChatMessage(content=payload, role=MessageRole.USER)], 
                   user=fake_user()
               ),
               topic=topic,
           )

   @then("the agent run should complete")
   def _(agent_runner: AgentTestRunner):
       assert agent_runner.has_stop_event, "Agent did not receive stop event"
   ```
3. **Run the Tests**: Execute tests from the scope directory.
   ```bash
   # Run all tests (excluding cloud dependencies)
   uv run pytest -k "not azure"

   # Run a specific test file
   uv run pytest tests/test_MyAgent.py
   ```

### 🔍 Step 3: Debug and Observe Your Agent

::: warning Debugging Approach
Due to the asynchronous, event-driven nature of agents, traditional debugging with breakpoints is often ineffective.
Instead, adopt a trace-driven debugging methodology.
:::

#### 🔍 The Debugging Mindset: Tracing and Logging over Breakpoints

::: tip Debugging Tools
Your primary tools are **Langfuse Tracing** for visual flow analysis and **structured logging** for detailed event
inspection. Use `print` statements within steps for quick checks.
:::

#### 📝 Essential Debugging Tool: The `trigger.py` Script

::: tip Trigger Script
For any non-trivial agent, create a `trigger.py` script. This script programmatically starts your agent and sends it a
specific `StartEvent`, allowing you to test a precise scenario in isolation without needing a frontend.
:::

```python
# my_agent/trigger.py - Essential for debugging
import asyncio
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

# ... other imports

# ALWAYS enable logging for debugging
enable_logging()

async def main():
    runner = AgentTestRunner(agent_type=MyAgent, agent_config=MyAgentConfig(...))
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=UserMessageEvent(...))

if __name__ == "__main__":
    asyncio.run(main())
```

#### 👁️ Primary Observability Tool: Langfuse Tracing (Port 6006)

::: warning Langfuse Tracing
**Langfuse** is your most important debugging tool. It provides a web UI to visualize the step-by-step execution of your
agent, showing the flow of events, timings, and errors.
:::

- **Access**: `http://localhost:6006` (available when the Docker stack is running).
- **Usage**: Run your agent via its `trigger.py` script, then open the Langfuse UI to find the execution trace. Click on
  steps to inspect inputs, outputs, and metadata.

#### 🔗 Langfuse Integration

::: info Langfuse
Langfuse is running alongside the development environment and provides programmatic access to trace data for debugging
and monitoring agent executions. This integration allows you to query trace information directly from your development
tools.
:::

**Key Concepts:**

- **Projects**: Each agent is its own project in Langfuse
- **Traces**: Each agent run is its own trace
- **Spans**: Each step within an agent run is its own span

**Usage in Development:**

- Use the Langfuse API to programmatically check if an agent run was successful
- Query trace data to analyze agent performance and behavior patterns
- Access span annotations and metadata for detailed debugging
- Retrieve experiment results and dataset information for evaluation

**Common MCP Commands:**

- List all projects to see available agents
- Get spans from a specific project to analyze agent steps
- Retrieve span annotations to understand step outcomes
- Access experiment data for agent evaluation workflows

This integration is particularly useful for automated testing, performance analysis, and building monitoring dashboards
around agent behavior.

#### 📝 Analyzing Event Flow with Logging

::: tip Event Flow Analysis
Enable logging in your `trigger.py` script to see a detailed, real-time feed of events being produced and consumed by
each step. This is invaluable for understanding why a workflow might be stalled or taking an unexpected path.
:::

```python
# Add this to the top of your trigger.py or run.py
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```

### ✅ Step 4: Ensure Code Quality

::: warning
Before committing your changes, use the provided Makefile commands to format, lint, and type-check your code.
:::

```bash
# Run this before creating a pull request
make pr-ready

# Or run commands individually
make format
make lint
```

::: danger
All agent code must use strict Python type annotations. This is enforced by CI/CD.
:::

______________________________________________________________________

## 3. 🎨 A Library of Agent Design Patterns

This section provides a library of established patterns for building robust and sophisticated agents. Each pattern
includes a conceptual explanation, use cases, and a reference to a working example in the playground.

### 📎 Basic Patterns

#### ➡️ Simple Linear Workflow

- **Concept**: A basic, sequential workflow where one step follows another in a straight line.
- **Reference**: `/playground/minimal_workflow/simple_workflow/`
  ```python
  class SimpleAgent(Agent):
      @step()
      async def start_step(self, event: UserMessageEvent) -> SimpleEventA: ...
      @step()
      async def end_step(self, event: SimpleEventA) -> StopEvent: ...
  ```

#### 🔀 Conditional Workflow

- **Concept**: A workflow that takes different paths based on data or logic. A step returns one of several possible
  event types, and the workflow engine routes it to the appropriate downstream step.
- **Reference**: `/playground/minimal_workflow/conditional_workflow/`
  ```python
  class ConditionalAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent) -> AboveThresholdEvent | BelowThresholdEvent: ...
      @step()
      async def end_step(self, event: AboveThresholdEvent | BelowThresholdEvent) -> StopEvent: ...
  ```

### 🔄 Interaction Patterns

#### 👥 Human-in-the-Loop

- **Concept**: Pauses the workflow to request input from a human user. The agent emits a request event and waits for a
  corresponding response event before continuing.
- **Reference**: `/playground/minimal_workflow/human_in_the_loop_workflow/`
  ```python
  class HumanInTheLoopAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent) -> HumanInTheLoop.request:
          return HumanInTheLoop.invoke(question="Shall I continue?")
      @step()
      async def end_step(self, event: HumanInTheLoop.response) -> StopEvent: ...
  ```

#### 🤖 Agent-in-the-Loop (Orchestration)

- **Concept**: An agent (the orchestrator) invokes another agent (the worker) and waits for its result. This allows for
  creating complex workflows by composing smaller, specialized agents.
- **Reference**: `/playground/minimal_workflow/agent_in_the_loop_workflow/`
  ```python
  class OrchestratorAgent(Agent):
      @step()
      async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
          return AgentInTheLoop.invoke(agent_id="worker_agent", agent_class="WorkerAgent", start_event=event)
      @step()
      async def end_step(self, response: AgentInTheLoop.response) -> OrchestrationResultEvent: ...
  ```

#### 🔄 Multistep Human-in-the-Loop

- **Concept**: A workflow with multiple, distinct points of human interaction, often used for multi-stage approval
  processes.
- **Reference**: `/playground/minimal_workflow/multistep_human_in_the_loop_workflow/`
  ```python
  class MultistepHumanInTheLoopAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
          return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")
      @step()
      async def second_hitl(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
          return SecondStepHumanInTheLoop.invoke(question="Are you sure?")
      @step()
      async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent: ...
  ```

### 🔀 Flow Control Patterns

#### 🔁 Bounded Loop

- **Concept**: An iterative workflow that repeats a cycle of steps until a condition is met or a maximum number of
  iterations is reached. State (like a loop counter) is managed using `RunContext`.
- **Reference**: `/playground/minimal_workflow/bounded_loop/`
  ```python
  class BoundedLoopAgent(Agent):
      @step()
      async def start_step(self, event: UserMessageEvent, run_context: RunContext) -> BeginEvent:
          await run_context.set("loop_count", 0)
          return BeginEvent(count=0)
      @step()
      async def decision_step(self, event: BoundedLoopAEvent, agent_config: BoundedLoopAgentConfig, run_context: RunContext) -> DecisionEvent | BeginEvent:
          loop_count = await run_context.get("loop_count")
          if loop_count < agent_config.loop_max:
              await run_context.set("loop_count", loop_count + 1)
              return BeginEvent(count=loop_count + 1)  # Continue loop
          return DecisionEvent()  # Exit loop
      @step()
      async def end_step(self, event: DecisionEvent) -> StopEvent: ...
  ```

#### 🔀 Fan-Out (Parallel Processing)

- **Concept**: A single step returns a `list` of events, which are then processed in parallel by downstream steps. This
  is useful for batch processing or concurrent operations.
- **Reference**: `/playground/minimal_workflow/fan_out_workflow/`
  ```python
  class FanOutAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent) -> list[FanOutA]:
          return [FanOutA(payload=str(i)) for i in range(5)]
      @step()
      async def process_a(self, event: FanOutA) -> FanOutB:
          return FanOutB(payload=event.payload)
      @step()
      async def stop_step(self, events: list[FanOutB]) -> StopEvent: ...
  ```

#### ✅ Precondition-Based Control

- **Concept**: A step is decorated with a `@precondition` function that must return `True` for the step to execute. This
  is useful for synchronizing parallel branches of a workflow.
- **Reference**: `/playground/minimal_workflow/precondition_workflow/`
  ```python
  @precondition()
  async def ensure_enough_events(parallel_events: list[ParallelEvent], config: PreconditionAgentConfig) -> bool:
      return len(parallel_events) == config.number_of_events

  class PreconditionAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent, config: PreconditionAgentConfig) -> list[ParallelEvent]:
          return [ParallelEvent(payload=str(i)) for i in range(config.number_of_events)]
      @step(precondition=ensure_enough_events)
      async def stop_step(self, events: list[ParallelEvent]) -> StopEvent: ...
  ```

### 💾 State and Configuration Patterns

#### 💾 Context Management

- **Concept**: Using `RunContext` and `ThreadContext` to manage state within and across agent runs.
- **Reference**: `/playground/minimal_workflow/context_workflow/`
  ```python
  class ContextAgent(Agent):
      @step()
      async def start_step(self, event: CustomStartEvent, thread_context: ThreadContext, run_context: RunContext) -> ContextEvent:
          thread_count = await thread_context.get("count", 0)
          run_count = await run_context.get("count", 0)
          await thread_context.set("count", thread_count + 1)
          await run_context.set("count", run_count + 1)
          return ContextEvent(thread_count=thread_count + 1, run_count=run_count + 1)
      @step()
      async def end_step(self, event: ContextEvent, thread_context: ThreadContext, run_context: RunContext) -> StopEvent: ...
  ```

#### ⚙️ Complex, Validated Configuration

- **Concept**: Using nested Pydantic models with detailed `Annotated` fields to create sophisticated, self-validating
  configurations for production-grade agents.
- **Reference**: `/aihub_agent/agents/RagAgent/configs/RAGAgentConfig.py`
  ```python
  class RAGAgentConfig(AgentConfig):
      llm: Annotated[ChatLLMConfig, Field(description="The LLM configuration for the agent.")]
      number_of_input_tokens: Annotated[int, Field(description="Maximum tokens allowed in input.")]
      context_prompt: Annotated[LocaleString | None, Field(description="Prompt template for context.")] = None
      max_hops: Annotated[int, Field(description="Maximum number of retrieval hops.", ge=1)] = 1
  ```

#### 📶 Configuration-Driven Behavior

- **Concept**: The agent's internal logic branches based on values from its configuration object, allowing its behavior
  to be changed without altering code.
- **Reference**: Many agents, such as `BoundedLoopAgent`, use this.
  ```python
  class ConfigurableAgent(Agent):
      @step()
      async def process_input(self, event: InputEvent, config: ConfigurableAgentConfig) -> ProcessedEvent | HumanReviewEvent:
          if config.processing_mode == "thorough":
              result = await thorough_processing(event.data)
          elif config.processing_mode == "fast":
              result = await fast_processing(event.data)
          else:
              result = await standard_processing(event.data)
          
          if config.enable_human_review and result.confidence < config.confidence_threshold:
              return HumanReviewEvent(data=result.data, confidence=result.confidence)
          return ProcessedEvent(data=result.data)
  ```

### 🚀 Advanced & Utility Patterns

#### 🌍 Multi-Locale Support (i18n)

- **Concept**: Building agents that support multiple languages by using the `LocaleHandler` to fetch translated strings
  from YAML files.
- **Reference**: `/playground/minimal_workflow/multi_locale_workflow/`
  ```python
  class MultiLocaleAgent(Agent):
      @step()
      async def start_step(self, event: UserMessageEvent, t: LocaleHandler, agent_config: MultiLocaleAgentConfig) -> MultiLocaleEvent:
          greeting = t('myagent.myscope.greeting')
          config_message = t(agent_config.locale_path)
          return MultiLocaleEvent(payload=config_message)
      @step()
      async def end_step(self, event: MultiLocaleEvent) -> StopEvent: ...
  ```

#### 🛡️ Error Handling and Resilience

- **Concept**: Building robust workflows by setting `stop_on_error=False` on steps that might fail, allowing the agent
  to catch `ExceptionEvent` and proceed along a failure path.
- **Reference**: The `@step` decorator parameters.
  ```python
  class ResilientAgent(Agent):
      @step(stop_on_error=False, max_executions_per_run=3)
      async def resilient_step(self, event: MyEvent) -> MyResponse | ExceptionEvent:
          try:
              result = await risky_operation()
              return MyResponse(result=result)
          except Exception as e:
              return ExceptionEvent(error=str(e))
      @step()
      async def handle_success(self, event: MyResponse) -> StopEvent: ...
      @step()
      async def handle_failure(self, event: ExceptionEvent) -> StopEvent: ...
  ```

#### 📱 Agent Step Metadata for UI

- **Concept**: Providing `name`, `description`, and `icon` metadata in the `@step` decorator to automatically populate
  monitoring and user-facing UIs.
- **Reference**: The `@step` decorator parameters.
  ```python
  class DocumentProcessingAgent(Agent):
      @step(
          name=LocaleString(en="Document Analysis", de="Dokumentenanalyse"),
          description=LocaleString(en="Analyzes uploaded documents", de="Analysiert hochgeladene Dokumente"),
          icon="document-text"
      )
      async def analyze_document(self, event: DocumentUploadEvent) -> DocumentAnalysisEvent: ...
      @step(
          name=LocaleString(en="Generate Report", de="Bericht erstellen"),
          icon="document-report"
      )
      async def generate_report(self, event: DocumentAnalysisEvent) -> StopEvent: ...
  ```

#### 🚀 Performance Testing & Optimization

- **Concept**: Using a dedicated agent and framework to measure performance, identify bottlenecks, and test workflows
  under load.
- **Reference**: `/playground/performance/PerformanceTestingAgent/`
  ```python
  class PerformanceTestingAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent, config: PerformanceTestingAgentConfig) -> list[ParallelEvent]:
          start_time = time.time()
          events = [ParallelEvent(payload=str(i), timestamp=start_time) for i in range(config.number_of_parallel_events)]
          return events
      @step()
      async def parallel_processing_step(self, events: list[ParallelEvent]) -> StopEvent:
          await asyncio.gather(*[self._process_single_event(event) for event in events])
          return StopEvent()
  ```

______________________________________________________________________

## 4. 📚 Reference Material

This section serves as an appendix for locating key files and running specific tasks.

### 🎮 Running Agents Interactively (`run.py`)

::: tip Interactive Testing
While `trigger.py` is for debugging specific, one-shot scenarios, `run.py` is used for interactive testing. A script
named `run.py` starts an agent and keeps it running, allowing it to be triggered multiple times from a frontend
application. This is useful for testing conversational flows and stateful behavior.
:::

```bash
# Example for starting an agent to interact with from the frontend
cd playground/agent/ExpertAskingAgent
python run.py
```

### 📝 Key Takeaways and Essential Files

::: tip Key Takeaways
- **Start in the Playground**: The best way to learn is to study the examples in `/playground/minimal_workflow/`. Each
  directory demonstrates a specific pattern.
- **Debug with Langfuse**: Always have `http://localhost:6006` open during development.
- **Test with BDD**: Follow the `pytest-bdd` and `AgentTestRunner` patterns for all new agents.
- **Compose Patterns**: Advanced agents are built by combining the simple patterns outlined in this guide.
:::

::: warning Essential Files to Read
- `/aihub_agent/agents/Agent.py`: The base class for all agents.
- `/aihub_agent/workflow/decorators/step.py`: The implementation of the core `@step` decorator.
- `/aihub_agent/runners/AgentTestRunner.py`: The foundation for all agent testing.
- `/aihub_agent/context/`: The context management system.
:::
