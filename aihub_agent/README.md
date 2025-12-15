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
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_agent`

You are contributing to the **aihub_agent** scope, which contains all agent logic and workflow definitions within the AI-Hub platform. This scope implements autonomous AI agents designed for proactive process automation—components that work alongside humans to execute tasks as part of redesigned business processes.

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
An agent is a **dispatchable workflow** that performs structured operations on input data to achieve a pre-defined goal. Agents follow a step-based approach where complex tasks are broken down into discrete, testable operations.
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
Steps are the fundamental building blocks of agent workflows, defined using the `@step()` decorator. This decorator orchestrates the flow of events between functions.
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

- **RunContext**: Short-lived storage for ephemeral data **within a single run**. It's isolated between different runs and is ideal for intermediate calculations or temporary caching. It expires after 30 days.
- **ThreadContext**: Persistent storage for state **across multiple runs** within the same conversation thread. It maintains conversational history and user preferences, enabling contextual follow-up interactions. It also has a 30-day TTL.

---

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging an agent.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

::: warning
Always activate the Poetry environment before working. All subsequent commands must be run from within this activated shell.
:::

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

```bash
cd aihub_agent
poetry shell
```

### 🛠️ Step 1: Create the Agent, Configuration, and Events

::: info
Follow this three-part process to define a new agent. Each part builds on the previous one to create a complete agent implementation.
:::

1. **Create the Agent Class**: Define the agent's workflow by creating a class that inherits from `Agent` and uses the `@step` decorator.
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
2. **Define the Agent Configuration**: Create a Pydantic model inheriting from `AgentConfig` to hold the agent's settings. Use `Annotated` and `Field` for validation and documentation.
   ```python
   # my_agent/MyAgentConfig.py
   from typing import Annotated
   from aihub_lib.agents.AgentConfig import AgentConfig
   from pydantic import Field

   class MyAgentConfig(AgentConfig):
       temperature: Annotated[float, Field(0.7, description="LLM temperature", ge=0.0, le=1.0)]
       confidence_threshold: Annotated[float, Field(0.5, description="Minimum confidence threshold")]
   ```
3. **Define Custom Events**: If your workflow requires custom data structures to be passed between steps, define them as Pydantic models inheriting from `Event`.
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
2. **Implement the Test Steps**: Write Python code to implement the Gherkin steps using the `AgentTestRunner`. The test runner provides a sandboxed environment to execute the agent and inspect the resulting events.
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
3. **Run the Tests**: Execute tests from your activated Poetry shell.
   ```bash
   # Run all tests (excluding cloud dependencies)
   poetry run pytest -k "not azure"

   # Run a specific test file
   poetry run pytest tests/test_MyAgent.py
   ```

### 🔍 Step 3: Debug and Observe Your Agent

::: warning Debugging Approach
Due to the asynchronous, event-driven nature of agents, traditional debugging with breakpoints is often ineffective. Instead, adopt a trace-driven debugging methodology.
:::

#### 🔍 The Debugging Mindset: Tracing and Logging over Breakpoints

::: tip Debugging Tools
Your primary tools are **Phoenix Tracing** for visual flow analysis and **structured logging** for detailed event inspection. Use `print` statements within steps for quick checks.
:::

#### 📝 Essential Debugging Tool: The `trigger.py` Script

::: tip Trigger Script
For any non-trivial agent, create a `trigger.py` script. This script programmatically starts your agent and sends it a specific `StartEvent`, allowing you to test a precise scenario in isolation without needing a frontend.
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

#### 👁️ Primary Observability Tool: Phoenix Tracing (Port 6006)

::: warning Phoenix Tracing
**Phoenix** is your most important debugging tool. It provides a web UI to visualize the step-by-step execution of your agent, showing the flow of events, timings, and errors.
:::

- **Access**: `http://localhost:6006` (available when the Docker stack is running).
- **Usage**: Run your agent via its `trigger.py` script, then open the Phoenix UI to find the execution trace. Click on steps to inspect inputs, outputs, and metadata.

#### 🔗 Phoenix MCP Server Integration

::: info Phoenix MCP Server
The Phoenix MCP server is running alongside the development environment and provides programmatic access to trace data for debugging and monitoring agent executions. This integration allows you to query trace information directly from your development tools.
:::

**Key Concepts:**

- **Projects**: Each agent is its own project in Phoenix
- **Traces**: Each agent run is its own trace
- **Spans**: Each step within an agent run is its own span

**Usage in Development:**

- Use the Phoenix MCP server to programmatically check if an agent run was successful
- Query trace data to analyze agent performance and behavior patterns
- Access span annotations and metadata for detailed debugging
- Retrieve experiment results and dataset information for evaluation

**Common MCP Commands:**

- List all projects to see available agents
- Get spans from a specific project to analyze agent steps
- Retrieve span annotations to understand step outcomes
- Access experiment data for agent evaluation workflows

This integration is particularly useful for automated testing, performance analysis, and building monitoring dashboards around agent behavior.

#### 📝 Analyzing Event Flow with Logging

::: tip Event Flow Analysis
Enable logging in your `trigger.py` script to see a detailed, real-time feed of events being produced and consumed by each step. This is invaluable for understanding why a workflow might be stalled or taking an unexpected path.
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

---

## 3. 🎨 A Library of Agent Design Patterns

This section provides a library of established patterns for building robust and sophisticated agents. Each pattern includes a conceptual explanation, use cases, and a reference to a working example in the playground.

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

- **Concept**: A workflow that takes different paths based on data or logic. A step returns one of several possible event types, and the workflow engine routes it to the appropriate downstream step.
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

- **Concept**: Pauses the workflow to request input from a human user. The agent emits a request event and waits for a corresponding response event before continuing.
- **Reference**: `/playground/minimal_workflow/human_in_the_loop_workflow/`
  ```python
  class HumanInTheLoopAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent) -> HumanInTheLoop.request:
          return HumanInTheLoop.invoke(message="Shall I continue?")
      @step()
      async def end_step(self, event: HumanInTheLoop.response) -> StopEvent: ...
  ```

#### 🤖 Agent-in-the-Loop (Orchestration)

- **Concept**: An agent (the orchestrator) invokes another agent (the worker) and waits for its result. This allows for creating complex workflows by composing smaller, specialized agents.
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

- **Concept**: A workflow with multiple, distinct points of human interaction, often used for multi-stage approval processes.
- **Reference**: `/playground/minimal_workflow/multistep_human_in_the_loop_workflow/`
  ```python
  class MultistepHumanInTheLoopAgent(Agent):
      @step()
      async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
          return FirstStepHumanInTheLoop.invoke(message="Shall I continue?")
      @step()
      async def second_hitl(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
          return SecondStepHumanInTheLoop.invoke(message="Are you sure?")
      @step()
      async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent: ...
  ```

### 🔀 Flow Control Patterns

#### 🔁 Bounded Loop

- **Concept**: An iterative workflow that repeats a cycle of steps until a condition is met or a maximum number of iterations is reached. State (like a loop counter) is managed using `RunContext`.
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

- **Concept**: A single step returns a `list` of events, which are then processed in parallel by downstream steps. This is useful for batch processing or concurrent operations.
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

- **Concept**: A step is decorated with a `@precondition` function that must return `True` for the step to execute. This is useful for synchronizing parallel branches of a workflow.
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

- **Concept**: Using nested Pydantic models with detailed `Annotated` fields to create sophisticated, self-validating configurations for production-grade agents.
- **Reference**: `/aihub_agent/agents/RagAgent/configs/RAGAgentConfig.py`
  ```python
  class RAGAgentConfig(AgentConfig):
      llm: Annotated[ChatLLMConfig, Field(description="The LLM configuration for the agent.")]
      number_of_input_tokens: Annotated[int, Field(description="Maximum tokens allowed in input.")]
      context_prompt: Annotated[LocaleString | None, Field(description="Prompt template for context.")] = None
      max_hops: Annotated[int, Field(description="Maximum number of retrieval hops.", ge=1)] = 1
  ```

#### 📶 Configuration-Driven Behavior

- **Concept**: The agent's internal logic branches based on values from its configuration object, allowing its behavior to be changed without altering code.
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

- **Concept**: Building agents that support multiple languages by using the `LocaleHandler` to fetch translated strings from YAML files.
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

- **Concept**: Building robust workflows by setting `stop_on_error=False` on steps that might fail, allowing the agent to catch `ExceptionEvent` and proceed along a failure path.
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

- **Concept**: Providing `name`, `description`, and `icon` metadata in the `@step` decorator to automatically populate monitoring and user-facing UIs.
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

- **Concept**: Using a dedicated agent and framework to measure performance, identify bottlenecks, and test workflows under load.
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

---

## 4. 📚 Reference Material

This section serves as an appendix for locating key files and running specific tasks.

### 🎮 Running Agents Interactively (`run.py`)

::: tip Interactive Testing
While `trigger.py` is for debugging specific, one-shot scenarios, `run.py` is used for interactive testing. A script named `run.py` starts an agent and keeps it running, allowing it to be triggered multiple times from a frontend application. This is useful for testing conversational flows and stateful behavior.
:::

```bash
# Example for starting an agent to interact with from the frontend
cd playground/agent/ExpertAskingAgent
python run.py
```

### 📝 Key Takeaways and Essential Files

::: tip Key Takeaways
- **Start in the Playground**: The best way to learn is to study the examples in `/playground/minimal_workflow/`. Each directory demonstrates a specific pattern.
- **Debug with Phoenix**: Always have `http://localhost:6006` open during development.
- **Test with BDD**: Follow the `pytest-bdd` and `AgentTestRunner` patterns for all new agents.
- **Compose Patterns**: Advanced agents are built by combining the simple patterns outlined in this guide.
:::

::: warning Essential Files to Read
- `/aihub_agent/agents/Agent.py`: The base class for all agents.
- `/aihub_agent/workflow/decorators/step.py`: The implementation of the core `@step` decorator.
- `/aihub_agent/runners/AgentTestRunner.py`: The foundation for all agent testing.
- `/aihub_agent/context/`: The context management system.
:::

### 📖 Glossary of Agent-Specific Terms

This glossary defines terms, concepts, and technologies that have specific meaning within the `aihub_agent` scope, building upon the core AI-Hub terminology.

| Term                      | Definition                                                                                                                                                                                                                             |
| :------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Agent**                 | A **dispatchable workflow** that performs structured operations on input data to achieve a pre-defined goal. Agents are autonomous AI components designed for proactive process automation, working alongside humans to execute tasks. |
| **Agent Configuration**   | A Pydantic model inheriting from `AgentConfig` that defines agent settings, parameters, and behavior. Uses `Annotated` fields with `Field()` for validation and documentation.                                                         |
| **Agent Test Runner**     | A specialized testing framework (`AgentTestRunner`) that provides a sandboxed environment to execute agents and inspect resulting events. Essential for BDD testing with pytest-bdd.                                                   |
| **Agent-in-the-Loop**     | A pattern where one agent (orchestrator) invokes another agent (worker) and waits for its result. Enables complex workflows by composing smaller, specialized agents.                                                                  |
| **Context**               | State management system with two types: `RunContext` (ephemeral, single-run) and `ThreadContext` (persistent, cross-run). Used for maintaining state within and across agent executions.                                               |
| **Dispatchable Workflow** | The base class for all agents. Provides the infrastructure for event-driven step execution, event routing, and workflow orchestration.                                                                                                 |
| **Event**                 | The atomic unit of communication in agent workflows. Pydantic models representing specific occurrences (e.g., `UserMessageEvent`, `StopEvent`, custom domain events).                                                                  |
| **Event Flow**            | The sequence of events produced and consumed by agent steps. Visible in logs and Phoenix traces, crucial for debugging agent workflows.                                                                                                |
| **Fan-Out**               | A workflow pattern where a single step returns a list of events processed in parallel by downstream steps. Used for batch processing and concurrent operations.                                                                        |
| **Human-in-the-Loop**     | A pattern where the workflow pauses to request input from a human user, emitting a request event and waiting for a response before continuing.                                                                                         |
| **Phoenix Tracing**       | A web-based debugging tool available at `http://localhost:6006` that provides step-by-step visualization of agent execution, event flow, and performance analysis.                                                                     |
| **Playground**            | The `/playground` directory containing self-contained examples of every agent pattern. Essential for learning and reference, organized into `agent/` (production examples) and `minimal_workflow/` (pattern examples).                 |
| **Precondition**          | A function decorated with `@precondition()` that must return `True` for a step to execute. Used for synchronizing parallel workflow branches and ensuring data availability.                                                           |
| **Run**                   | A single, traceable execution of an agent's workflow, beginning with a `StartEvent` and ending with a `StopEvent`. Has an ephemeral `RunContext` for state management.                                                                 |
| **Run Context**           | Short-lived storage for ephemeral data within a single agent run. Isolated between runs, ideal for intermediate calculations and temporary caching. Expires after 30 days.                                                             |
| **Step**                  | A method decorated with `@step()` that represents a single operation in an agent workflow. Steps consume events as input and produce events as output, enabling clear workflow composition.                                            |
| **Step Metadata**         | Rich information attached to steps via the `@step()` decorator, including localized names, descriptions, and icons for UI integration and monitoring.                                                                                  |
| **Thread**                | A logical grouping of multiple runs that form a continuous conversation. Maintains state across runs via persistent `ThreadContext` for contextual follow-up interactions.                                                             |
| **Thread Context**        | Persistent storage for state across multiple agent runs within the same conversation thread. Maintains conversational history and user preferences with 30-day TTL.                                                                    |
| **Trigger Script**        | A Python script (`trigger.py`) that programmatically starts an agent, sends it a specific event, and terminates. Essential for focused debugging and testing specific scenarios.                                                       |
| **Workflow**              | The fundamental design pattern for agents. A task broken down into a series of structured, explicit `@step`-decorated methods ensuring testability and transparency.                                                                   |

---

## 5. Production Workflow: Namespace Selection to RAG

This section traces a complete production workflow through the codebase: from namespace selection across multiple
buckets to RAG answer generation. Understanding this flow demonstrates how multi-agent systems coordinate in practice.

### Architecture Overview

The workflow involves three agents working in sequence:

```
┌─────────────────────────┐     ┌──────────────┐     ┌────────────────────────────┐
│ NamespaceSelectionAgent │────>│   RAGAgent   │────>│ KnowledgeRetrievalAgent(s) │
│                         │     │              │     │                            │
│ - Ask user which        │     │ - Condense   │     │ - Query vector store       │
│   collections to search │     │   question   │     │   with namespace filters   │
│ - Parse selection       │     │ - Orchestrate│     │ - Return relevant nodes    │
│ - Delegate to RAG       │     │   retrieval  │     │                            │
└─────────────────────────┘     │ - Generate   │     └────────────────────────────┘
                                │   answer     │
                                └──────────────┘
```

### Key Data Structures

Understanding these data structures is essential for working with the namespace selection flow:

| Structure | Purpose | File |
|-----------|---------|------|
| `BucketReference` | Config-time reference to a bucket (by ID or name) | `agents/NamespaceSelectionAgent/configs/BucketReference.py` |
| `BucketInfo` | Runtime info with available namespaces for selection UI | `agents/NamespaceSelectionAgent/configs/BucketInfo.py` |
| `BucketNamespaceSelection` | User's selection: bucket_name + list of namespace names | `agents/NamespaceSelectionAgent/configs/BucketNamespaceSelection.py` |
| `KnowledgeRetrievalAgentReference` | Links a retrieval agent to a specific bucket via `bucket_name` | `agents/configs/KnowledgeRetrievalAgentReference.py` |
| `KnowledgeRetrievalOverride` | Passes selected namespaces to retrieval agent | `rag/events/RetrievalStartEvent.py` |

### Step-by-Step Flow with Code References

#### Step 1: NamespaceSelectionAgent - Check Precondition

**File**: `agents/NamespaceSelectionAgent/NamespaceSelectionAgent.py`

The agent first checks if namespace selections already exist in `ThreadContext`:

```python
@step(precondition=need_namespace_selection)
async def ask_selection_step(self, event: UserMessageEvent, ...) -> HumanInTheLoop.chat:
    # Only runs if no selection exists in ThreadContext
```

#### Step 2: Fetch Available Namespaces from Database

**File**: `agents/NamespaceSelectionAgent/namespace_data.py:42-74`

For each `BucketReference` in the agent config:
1. Look up the bucket by `bucket_id` or `bucket_name`
2. Query database: `NamespaceEntity.get_namespaces_by_bucket(bucket_id)`
3. Build `BucketInfo` objects containing all available namespaces

#### Step 3: Human-in-the-Loop - Ask User Selection

The agent generates a friendly question using an LLM and returns `HumanInTheLoop.chat.invoke()`. This pauses the
workflow until the user responds with their selection.

#### Step 4: Parse User Selection

**File**: `agents/NamespaceSelectionAgent/selection_parsing.py:70-119`

The agent uses LLM structured output to extract namespace names from the user's response:
1. For each bucket without a selection, parse user's response
2. Validate selected namespace names against available options
3. Create `BucketNamespaceSelection` objects
4. Retry HITL if response is unclear (up to `max_selection_attempts`)

#### Step 5: Create RAGUserMessageEvent and Delegate

**File**: `agents/NamespaceSelectionAgent/namespace_data.py:77-96`

The agent creates a `RAGUserMessageEvent` containing the namespace selections:

```python
RAGUserMessageEvent(
    messages=original_user_event.messages,
    locale=original_user_event.locale,
    user=original_user_event.user,
    bucket_namespace_selections=[
        BucketNamespaceSelection(bucket_name="knowledge", namespaces=["hr-policies"]),
        BucketNamespaceSelection(bucket_name="insights", namespaces=["legal"]),
    ]
)
```

This event is passed to the RAG agent via `AgentInTheLoop.invoke()`.

#### Step 6: RAGAgent - Multi-Step Pipeline

**File**: `agents/RagAgent/RAGAgent.py`

The RAG agent executes its pipeline:
1. **Limit chat history** - Truncate to fit token limits
2. **Condense question** - Convert chat + query to standalone question
3. **Few-shot guard** - Validate question appropriateness
4. **Invoke retrieval agents** - This is where namespace selections are applied

#### Step 7: Resolve Namespace Overrides for Retrieval

**File**: `rag/steps/invoke_retrieval.py:27-52`

This is the critical step where selections become retrieval filters:

```python
def execute_invoke_retrieval(
    query: str,
    locale: Literal["de", "en", "fr", "it"],
    retrieval_agents: list[AgentReference],
    bucket_namespace_selections: list[BucketNamespaceSelection] | None = None,
) -> list[AgentInTheLoop.request]:
```

For each retrieval agent:
1. Check if it's a `KnowledgeRetrievalAgentReference` (has `bucket_name` field)
2. Find matching `BucketNamespaceSelection` with same `bucket_name`
3. Create `KnowledgeRetrievalOverride` containing selected namespaces
4. Package in `RetrievalStartEvent` and invoke the retrieval agent

#### Step 8: KnowledgeRetrievalAgent - Extract Namespaces

**File**: `agents/KnowledgeRetrievalAgent/KnowledgeRetrievalAgent.py:55-77`

The retrieval agent extracts namespaces from the override:

```python
def _get_namespaces(
    override: RetrievalOverride | None,
    config: KnowledgeRetrievalAgentConfig,
) -> list[str] | None:
    if override and isinstance(override, KnowledgeRetrievalOverride):
        return override.namespaces  # User's selected namespaces
    return None  # Fall back to config defaults
```

#### Step 9: Vector Store Query with Namespace Filtering

**File**: `aihub_lib/generative_ai/utils/retrieve_nodes.py:17-42`

The actual filtering happens at the vector store level:

```python
def retrieve_nodes(
    message: str,
    embed_model: BaseEmbedding,
    retrieve_k: int,
    index_namespaces: list[str],  # Selected namespaces from user
    query_mode: VectorStoreQueryMode,
    node_types: list[str],
    vector_store: BasePydanticVectorStore,
) -> list[NodeWithScore] | None:
    # Build metadata filters for namespace/node_type combinations
    filters = MetadataFilters(
        filters=[
            MetadataFilters(
                filters=[
                    MetadataFilter(key=NAMESPACE, value=ns),
                    MetadataFilter(key=TYPE, value=nt),
                ],
                condition=FilterCondition.AND,
            )
            for ns in index_namespaces  # User-selected namespaces
            for nt in node_types
        ],
        condition=FilterCondition.OR,
    )

    # Query returns only nodes matching selected namespaces
    return vector_store.query(VectorStoreQuery(filters=filters, ...))
```

### Complete Event Flow

```
UserMessageEvent
    │
    ▼
NamespaceSelectionAgent.ask_selection_step
    │
    ▼
[HITL: User selects namespaces from available options]
    │
    ▼
NamespaceSelectionAgent.parse_selection_step
    │
    ▼
BucketNamespaceSelection[] created
    │
    ▼
NamespaceSelectionAgent.delegate_to_rag_step
    │
    ▼
RAGUserMessageEvent(bucket_namespace_selections=[...])
    │
    ▼
RAGAgent.invoke_retrieval_step
    │
    ├──────────────────────────────────────────┐
    ▼                                          ▼
RetrievalStartEvent                    RetrievalStartEvent
(bucket: "knowledge",                  (bucket: "insights",
 namespaces: ["hr-policies"])           namespaces: ["legal"])
    │                                          │
    ▼                                          ▼
KnowledgeRetrievalAgent                KnowledgeRetrievalAgent
    │                                          │
    ▼                                          ▼
Vector query with                      Vector query with
NAMESPACE="hr-policies" filter         NAMESPACE="legal" filter
    │                                          │
    └──────────────────────────────────────────┘
                        │
                        ▼
               RAGAgent.respond_with_llm_step
                        │
                        ▼
               LLMStopEvent (answer using only
               retrieved context from selected namespaces)
```

### What is a "Bucket"?

A **bucket** is a logical organizational unit for knowledge bases:

- **Data lake concept**: Buckets partition organizational knowledge (HR, Finance, Engineering, etc.)
- **Namespace container**: Each bucket contains multiple namespaces (e.g., HR bucket → "policies", "benefits", "payroll")
- **Database entity**: Defined in `BucketEntity` (FerretDB/MongoDB)
- **Retrieval agent mapping**: Each `KnowledgeRetrievalAgentReference` maps to exactly one bucket via its `bucket_name` field
- **Multi-bucket support**: NamespaceSelectionAgent can configure multiple buckets, asking users to select namespaces from each

### Key Implementation Patterns

#### Agent-in-the-Loop for Delegation

The NamespaceSelectionAgent delegates to RAGAgent using the AITL pattern:

```python
@step()
async def delegate_to_rag_step(self, event: ...) -> AgentInTheLoop.request:
    return AgentInTheLoop.invoke(
        agent_id=config.rag_agent.agent_id,
        agent_class=config.rag_agent.agent_class,
        start_event=RAGUserMessageEvent(
            bucket_namespace_selections=selections,
            ...
        )
    )
```

#### ThreadContext for Persistent Selection

User selections are stored in `ThreadContext` so follow-up questions in the same thread don't require re-selection:

```python
await thread_context.set(NAMESPACE_SELECTIONS_KEY, selections)
```

#### Configuration-Driven Bucket Mapping

The mapping from retrieval agent to bucket is defined in configuration, not code:

```python
class NamespaceSelectionAgentConfig(AgentConfig):
    buckets: list[BucketReference]  # Which buckets to offer for selection
    rag_agent: RAGAgentReference    # Contains retrieval_agents with bucket_name
```

This allows the same workflow to be deployed with different bucket configurations without code changes.
