---
title: AI-Hub Agentic Process Automation
index: 7
---

# 🔄 AI-Hub Process Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_process-core&metric=alert_status&token=0e0aba8b78dd02e4ffecf0ed6470b8b4f65c9c61)](https://sonarcloud.io/summary/new_code?id=aihub-core_process-core)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_process-core&metric=security_rating&token=0e0aba8b78dd02e4ffecf0ed6470b8b4f65c9c61)](https://sonarcloud.io/summary/new_code?id=aihub-core_process-core)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_process-core&metric=vulnerabilities&token=0e0aba8b78dd02e4ffecf0ed6470b8b4f65c9c61)](https://sonarcloud.io/summary/new_code?id=aihub-core_process-core)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_process-core&metric=sqale_rating&token=0e0aba8b78dd02e4ffecf0ed6470b8b4f65c9c61)](https://sonarcloud.io/summary/new_code?id=aihub-core_process-core)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_process-core&metric=ncloc&token=0e0aba8b78dd02e4ffecf0ed6470b8b4f65c9c61)](https://sonarcloud.io/summary/new_code?id=aihub-core_process-core)

## 1. 🎯 Foundational Knowledge of Process Development

This section covers the foundational architecture, patterns, and terminology you need to know before building agentic
processes.

::: info
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you
have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_process`

You are contributing to the **aihub_process** scope, which orchestrates high-level business processes that involve
collaboration between agents, humans, and programs within the AI-Hub platform. This scope implements the highest tier of
AI-Hub's evolution—**Agentic Process Automation**—where workflows are redesigned as dynamic collaborations between
different actors.

### 📁 Project Structure

The `aihub_process` scope is organized as follows:

```
aihub_process/
├── aihub_process/              # Main package source
│   ├── agentic_processes/      # Core AgenticProcess base class
│   ├── delegators/             # Entity delegation system
│   │   ├── agent/             # Agent work delegation
│   │   ├── human/             # Human work delegation
│   │   ├── process/           # Process work delegation
│   │   └── program/           # Program work delegation
│   ├── dispatchers/           # Process event dispatching
│   ├── process/               # Process decorators and annotations
│   │   ├── decorators/        # @process_step decorator
│   │   └── annotations/       # Process metadata extraction
│   ├── runners/               # ProcessRunner and ProcessTestRunner
│   └── i18n/                  # Process-specific internationalization
└── playground/                # Examples and testing - START HERE
    ├── AgenticCVProcess/      # Complex CV processing example
    ├── minimal_processes/     # Self-contained pattern examples - ESSENTIAL
    │   ├── agent_only_process/
    │   ├── human_only_process/
    │   ├── agent_to_human_process/
    │   ├── human_to_agent_process/
    │   ├── fan_out_process/
    │   ├── multi_input_process/
    │   └── process_sequence/
    ├── agents/                # Test agents for playground
    └── events/                # Example work events
```

### 🤖 The AgenticProcess: A Collaborative Workflow Orchestrator

::: info Core Concept
An agentic process is a **dispatchable workflow** that orchestrates high-level business processes through collaboration
between agents, humans, and programs. Processes follow a delegation-based approach where work is distributed to the most
appropriate actors.
:::

```python
class AgenticProcess(DispatchableWorkflow):
    """
    The agentic process is a dispatchable workflow that connects agents, humans and programs to form a
    well-defined process.
    
    In an agentic process, the steps you define describe 'connections' with 'transformations' between
    different entities. Your main goal is simple:
    - Define what the inputs and outputs of your process are.
    - Divide your process into a series of work that must be done
    - Decide for each work what entity should do the work: An agent, a human or a program.
    - Delegate the work to the right entity
    - Wait for the delegated work to be completed, take the result, transform it, and delegate to the next entity.
    """
```

**Key Principles:**

- **Orchestration, Not Execution**: Processes delegate work to entities; they don't execute business logic directly.
- **Entity Collaboration**: Work flows between agents, humans, and programs based on optimal capability matching.
- **Transformation Focus**: Process steps primarily transform outputs of one entity into inputs for the next.

### 🏷️ The `@process_step` Decorator: Delegation Points

::: tip Process Steps
Process steps are defined using the `@process_step()` decorator, which creates delegation points where work is assigned
to specific entities.
:::

```python
@process_step()
def received_cv_2_analyzed_cv(
    self,
    cv: Annotated[SubmittedCV, Program.In(route="/cv", method="POST")],
) -> Annotated[AnalyzeCVRequest, Agent.Out(agent_class="LLMWrappingAgent", agent_id="dev_agent")]:
    return AnalyzeCVRequest(start_event=UserMessageEvent(...))
```

**Key Parameters:**

- `name`: Localized step name for UI and monitoring
- `description`: Localized step description
- `icon`: Icon identifier for visual representation

### 📎 Entity Delegation System

::: info Entity Types
Processes delegate work to four types of entities:
:::

- **Agent**: AI agents that perform autonomous work (`Agent.In`, `Agent.Out`)
- **Human**: Human users who provide input and decisions (`Human.In`, `Human.Out`)
- **Program**: External programs and APIs (`Program.In`, `Program.Out`)
- **Process**: Other agentic processes (`Process.In`, `Process.Out`)

______________________________________________________________________

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging agentic processes.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

### 🛠️ Step 1: Create the Process, Configuration, and Events

::: info
Follow this three-part process to define a new agentic process. Each part builds on the previous one to create a
complete process implementation.
:::

1. **Create the Process Class**: Define the process workflow by creating a class that inherits from `AgenticProcess` and
   uses the `@process_step` decorator.

   ```python
   # my_process/MyProcess.py
   from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
   from aihub_process.delegators.agent.Agent import Agent
   from aihub_process.delegators.human.Human import Human
   from aihub_process.process.decorators.process_step import process_step

   class MyProcess(AgenticProcess):
       @process_step()
       def start_step(
           self,
           initial_work: Annotated[InitialWork, Agent.In(agent_class="MyAgent", agent_id="my_agent")],
       ) -> Annotated[HumanReviewRequest, Human.Out(users=[])]:
           return HumanReviewRequest(data=initial_work.result)
       
       @process_step()
       def review_step(
           self,
           review_result: Annotated[HumanReviewRequest.approval, Human.In(route="/review", method="POST")],
       ) -> Annotated[FinalResult, Process.Out()]:
           return FinalResult(decision=review_result.decision)
   ```

2. **Define Work Events**: Create events that represent work completion by different entities.

   ```python
   # my_process/events/InitialWork.py
   from typing import Annotated
   from pydantic import Field
   from aihub_lib.nats.events import AgentWorkEvent

   class InitialWork(AgentWorkEvent):
       result: Annotated[str, Field(description="The agent's work result")]
       confidence: Annotated[float, Field(description="Confidence in the result")]

   # my_process/events/HumanReviewRequest.py
   from aihub_lib.nats.events import HumanWorkRequestEvent
   from aihub_lib.nats.events.form import FormGroup

   class HumanReviewRequest(HumanWorkRequestEvent):
       data: Annotated[str, Field(description="Data to review")]
       
       @classmethod
       def approval(cls, display_name: LocaleString, **kwargs) -> FormGroup:
           return FormGroup(display_name=display_name, **kwargs)
   ```

3. **Create Process Configuration**: Define the process metadata.

   ```python
   # Usage in runner or tests
   process_config = ProcessConfig(
       process_id="my_process",
       name=LocaleString(en="My Process"),
       description=LocaleString(en="A process that demonstrates agent-human collaboration"),
   )
   ```

### 🧪 Step 2: Write and Run Tests

::: tip Testing with BDD
Process testing uses BDD with `pytest-bdd` and the `ProcessTestRunner`. This provides a natural language description of
process behavior.
:::

1. **Write a Feature File**: Describe the process behavior in Gherkin syntax.

   ```gherkin
   # tests/features/my_process.feature
   Feature: My Process
     Scenario: Test agent-human collaboration
       Given a MyProcess runner
       And an agent runner for MyAgent
       When the agent completes initial work with result "analysis complete"
       Then a human review request is created
       When the human approves the review
       Then the process produces a final result
   ```

2. **Implement the Test Steps**: Write Python implementations using the `ProcessTestRunner`.

   ```python
   # tests/test_MyProcess.py
   from aihub_lib.testing.asyncio_utils.bdd import async_test
   from aihub_lib.processes.ProcessConfig import ProcessConfig
   from pytest_bdd import given, parsers, scenarios, then, when

   from aihub_process.runners.ProcessTestRunner import ProcessTestRunner

   scenarios("./features/my_process.feature")

   @given("a MyProcess runner", target_fixture="process_runner")
   def process_runner_fixture():
       return ProcessTestRunner(
           process_type=MyProcess,
           process_config=ProcessConfig(
               process_id="my_process",
               name=LocaleString(en="My Process"),
               description=LocaleString(en="Test process"),
           ),
       )

   @when(parsers.parse('the agent completes initial work with result "{result}"'))
   @async_test
   async def agent_completes_work(process_runner: ProcessTestRunner, result: str):
       async with process_runner.test_run():
           await process_runner.send_event(
               InitialWork(result=result, confidence=0.9),
               process_walkthrough_id="test_walkthrough"
           )

   @then("a human review request is created")
   def verify_human_review_request(process_runner: ProcessTestRunner):
       assert process_runner.has_event_of_class(HumanReviewRequest)
   ```

3. **Run the Tests**: Execute tests from the scope directory.

   ```bash
   # Run all tests
   uv run pytest

   # Run specific test file
   uv run pytest tests/test_MyProcess.py
   ```

### 🔍 Step 3: Debug and Observe Your Process

#### 🔍 The Debugging Mindset: Event Flow Analysis

::: tip Debugging Approach
Process debugging focuses on understanding the flow of work events between entities. Use **structured logging** and
**Langfuse tracing** to visualize process execution.
:::

#### 🛠️ Essential Debugging Tools

1. **The `trigger.py` Script**: For focused testing of specific process scenarios.

   ```python
   # my_process/trigger.py
   import asyncio
   from aihub_lib.infrastructure.logging.logger import enable_logging

   enable_logging()

   async def main():
       process_runner = ProcessTestRunner(
           process_type=MyProcess,
           process_config=ProcessConfig(...)
       )
       
       async with process_runner.test_run():
           await process_runner.send_event(
               InitialWork(result="test result", confidence=0.8),
               process_walkthrough_id="debug_walkthrough"
           )

   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. **The `run.py` Script**: For interactive process testing with multiple entities.

   ```python
   # my_process/run.py
   import asyncio
   from aihub_agent.runners.AgentTestRunner import AgentTestRunner
   from aihub_lib.infrastructure.logging.logger import enable_logging

   enable_logging()

   async def main():
       agent_runner = AgentTestRunner(...)
       process_runner = ProcessTestRunner(...)
       
       await asyncio.gather(
           agent_runner.run_forever(),
           process_runner.run_forever(),
       )

   if __name__ == "__main__":
       asyncio.run(main())
   ```

#### 👁️ Primary Observability Tools

- **Langfuse Tracing**: `http://localhost:6006` for visual process flow analysis
- **ProcessTestRunner**: Built-in event observation for testing and debugging
- **Structured Logging**: Real-time event flow monitoring

### ✅ Step 4: Ensure Code Quality

::: warning
Before committing your changes, use the provided Makefile commands.
:::

```bash
# Run this before creating a pull request
make pr-ready

# Or run commands individually
make format      # Ruff formatting
make lint        # Ruff linting
make typecheck   # MyPy type checking
```

::: danger
All process code must use strict Python type annotations and follow the delegation-based design pattern. This is
enforced by CI/CD.
:::

______________________________________________________________________

## 3. 🎨 Process Design Patterns and Best Practices

This section provides a library of established patterns for building robust agentic processes.

### 📎 Basic Delegation Patterns

#### 🤖 Agent-Only Process

::: info Agent-Only Process
- **Concept**: A process that delegates work exclusively to agents in a sequential chain.
- **Reference**: `/playground/minimal_processes/agent_only_process/`
- **Use Case**: Automated processing pipelines where no human intervention is needed.
:::

```python
class AgentOnlyProcess(AgenticProcess):
    @process_step()
    async def agent_a_to_agent_b(
        self,
        work_from_agent_a: Annotated[AgentAWork, Agent.In(agent_class="AgentA", agent_id="agent_a")],
    ) -> Annotated[AgentBWorkRequest, Agent.Out(agent_class="AgentB", agent_id="agent_b")]:
        return AgentBWorkRequest(start_event=AgentBStartEvent(payload=work_from_agent_a.result))
```

#### 👥 Human-Only Process

::: info Human-Only Process
- **Concept**: A process that delegates work exclusively to humans for decision-making workflows.
- **Reference**: `/playground/minimal_processes/human_only_process/`
- **Use Case**: Approval workflows, manual review processes, complex decision chains.
:::

```python
class HumanOnlyProcess(AgenticProcess):
    @process_step()
    def initial_review(
        self,
        request: Annotated[ReviewRequest, Human.In(route="/review", method="POST")],
    ) -> Annotated[ApprovalRequest, Human.Out(users=["manager@company.com"])]:
        return ApprovalRequest(data=request.data, urgency="high")
```

#### 🤝 Mixed Agent-Human Process

::: info Mixed Agent-Human Process
- **Concept**: A process that combines agent automation with human oversight and decision-making.
- **Reference**: `/playground/minimal_processes/agent_to_human_process/`
- **Use Case**: Most production processes where AI provides analysis and humans make final decisions.
:::

```python
class AgentToHumanProcess(AgenticProcess):
    @process_step()
    def agent_analysis(
        self,
        agent_result: Annotated[AnalysisResult, Agent.In(agent_class="AnalystAgent", agent_id="analyst")],
    ) -> Annotated[HumanReviewRequest, Human.Out(users=[])]:
        return HumanReviewRequest(
            analysis=agent_result.analysis,
            confidence=agent_result.confidence,
            recommendation=agent_result.recommendation
        )
```

### 🔀 Advanced Flow Control Patterns

#### 🔀 Fan-Out Process

::: info Fan-Out Process
- **Concept**: A process that distributes work to multiple entities in parallel and collects results.
- **Reference**: `/playground/minimal_processes/fan_out_process/`
- **Use Case**: Batch processing, parallel analysis, distributed work execution.
:::

```python
class FanOutProcess(AgenticProcess):
    @process_step()
    def distribute_work(
        self,
        initial_data: Annotated[InitialData, Process.In()],
    ) -> Annotated[list[WorkItem], Agent.Out(agent_class="WorkerAgent", agent_id="worker_pool")]:
        return [WorkItem(data=chunk) for chunk in initial_data.chunks]
    
    @process_step()
    def collect_results(
        self,
        results: Annotated[list[WorkResult], Agent.In(agent_class="WorkerAgent", agent_id="worker_pool")],
    ) -> Annotated[AggregatedResult, Process.Out()]:
        return AggregatedResult(combined_results=results)
```

#### 🔀 Multi-Input Process

::: info Multi-Input Process
- **Concept**: A process that waits for multiple inputs before proceeding, enabling synchronization.
- **Reference**: `/playground/minimal_processes/multi_input_process/`
- **Use Case**: Processes requiring coordination between multiple data sources or entity types.
:::

```python
class MultiInputProcess(AgenticProcess):
    @process_step()
    def combine_inputs(
        self,
        agent_input: Annotated[AgentData, Agent.In(agent_class="DataAgent", agent_id="data_agent")],
        human_input: Annotated[HumanData, Human.In(route="/input", method="POST")],
    ) -> Annotated[CombinedResult, Process.Out()]:
        return CombinedResult(
            agent_data=agent_input.data,
            human_data=human_input.data,
            timestamp=datetime.now()
        )
```

#### 🔗 Process Sequence

::: info Process Sequence
- **Concept**: A process that triggers other processes in sequence, creating process chains.
- **Reference**: `/playground/minimal_processes/process_sequence/`
- **Use Case**: Complex workflows that span multiple process boundaries.
:::

```python
class InitialProcess(AgenticProcess):
    @process_step()
    def delegate_to_next_process(
        self,
        initial_work: Annotated[InitialWork, Agent.In(agent_class="StartAgent", agent_id="start")],
    ) -> Annotated[NextProcessTrigger, Process.Out(process_class="SubsequentProcess", process_id="subsequent")]:
        return NextProcessTrigger(data=initial_work.result)
```

### 📎 Entity-Specific Patterns

#### 🤖 Agent Integration

::: tip Agent Integration
- **Best Practice**: Use specific agent classes and IDs for clear delegation.
- **Configuration**: Define agent capabilities and expected input/output formats.
:::

```python
@process_step()
def delegate_to_agent(
    self,
    input_data: Annotated[InputData, Program.In(route="/data", method="POST")],
) -> Annotated[AgentWorkRequest, Agent.Out(agent_class="SpecializedAgent", agent_id="instance_1")]:
    return AgentWorkRequest(
        start_event=AgentStartEvent(
            data=input_data.payload,
            parameters={"mode": "thorough", "timeout": 30}
        )
    )
```

#### 👥 Human Integration

::: tip Human Integration
- **Best Practice**: Use form-based interfaces for structured human input.
- **Configuration**: Define specific user groups and input validation.
:::

```python
@process_step()
def request_human_decision(
    self,
    analysis: Annotated[AnalysisResult, Agent.In(agent_class="AnalystAgent", agent_id="analyst")],
) -> Annotated[DecisionRequest, Human.Out(users=["decision_maker@company.com"])]:
    return DecisionRequest(
        forms=[
            DecisionRequest.approve(
                display_name=LocaleString(en="Approve"),
                display_description=LocaleString(en="Approve this analysis"),
                reason=InputTextElement(label=LocaleString(en="Approval reason"))
            ),
            DecisionRequest.reject(
                display_name=LocaleString(en="Reject"),
                display_description=LocaleString(en="Reject this analysis"),
                reason=InputTextElement(label=LocaleString(en="Rejection reason"))
            )
        ]
    )
```


