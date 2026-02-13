# aihub_process - Agentic Process Automation

**Purpose**: High-level business process orchestration. Collaborative workflows between agents, humans, and programs.

Tech Stack & Paradigms: Pydantic v2 for process configs and validation. NATS pub-sub for event consumption (StopEvent from agents) and production (StartEvent to next). FastAPI + uvicorn for REST endpoints. MongoEngine for persistence. httpx HTTP client. cachetools for caching. Delegation pattern for agent/human orchestration. Form-based human interaction via HumanInTheLoopEvent. ProcessRunner for local execution. Multi-participant coordination (agents → humans → agents). Observable process flows with explicit state transitions. Minimal process logic (delegates to specialized agents). pytest-bdd for Gherkin BDD tests. asgi-lifespan for testing. Development: aihub_agent as dev dependency for local testing.

## Scope Responsibility

Process-level coordination (NOT task execution). Transforms entity outputs into entity inputs. Delegates work, waits for results, routes to next entity.

## Folder Structure

```
aihub_process/
├── agentic_processes/         # AgenticProcess base class
├── delegators/                # Entity delegation system
│   ├── agent/                 # Agent.In, Agent.Out
│   ├── human/                 # Human.In, Human.Out
│   ├── process/               # Process.In, Process.Out
│   └── program/               # Program.In, Program.Out
├── dispatchers/               # Event dispatching & routing
├── process/                   # @process_step decorator
├── runners/                   # ProcessRunner, ProcessTestRunner
└── playground/                # Examples (START HERE)
    ├── AgenticCVProcess/      # Complex CV processing example
    └── minimal_processes/     # Pattern library (ESSENTIAL)
        ├── agent_only_process/
        ├── human_only_process/
        ├── agent_to_human_process/
        ├── fan_out_process/
        ├── multi_input_process/
        └── process_sequence/
```

## Key Concepts

**Process = Orchestrator**:

- Connects entities (agents, humans, programs)
- Transforms outputs → inputs (light processing only)
- Delegates work, NOT executes work

**Process Step** (`@process_step()`):

- Delegation point where work assigned to entity
- Consumes WorkEvent from one entity
- Produces WorkRequestEvent for next entity

**Entity Types**:

- **Agent**: AI agents (`Agent.In`, `Agent.Out` with `agent_class`, `agent_id`)
- **Human**: Users (`Human.In`, `Human.Out` with `users` list, `route`, `method`)
- **Program**: External systems (`Program.In`, `Program.Out` with `route`, `method`)
- **Process**: Other processes (`Process.In`, `Process.Out` with `process_class`, `process_id`)

## Process Step Pattern

```python
@process_step(
    name=LocaleString(en="Analyze CV"),
    description=LocaleString(en="Agent analyzes CV"),
    icon="pi-file-check",
)
def cv_to_analysis(
    self,
    cv: Annotated[CVSubmitted, Program.In(route="/cv", method="POST")],
) -> Annotated[AnalysisRequest, Agent.Out(agent_class="CVAgent", agent_id="cv_agent")]:
    return AnalysisRequest(start_event=UserMessageEvent(content=cv.data))
```

**Parameters**:

- `name`: Localized step name (UI display)
- `description`: Localized description
- `icon`: PrimeIcons identifier
- `precondition`: Function for multi-input synchronization

## Work Events

**WorkEvent**: Signals entity completed work.

- `AgentWorkEvent`: Agent finished
- `HumanWorkEvent`: Human responded
- `ProgramWorkEvent`: Program returned
- `ProcessWorkEvent`: Sub-process completed

**WorkRequestEvent**: Delegates work to entity.

- `AgentWorkRequestEvent`: Start agent run
- `HumanWorkRequestEvent`: Request user input (forms)
- `ProgramWorkRequestEvent`: Call external API

## Human Integration (Forms)

**Pattern**: Structured input via form groups.

```python
class ReviewRequest(HumanWorkRequestEvent):
    data: str

    @classmethod
    def approve(cls, display_name: LocaleString, **kwargs) -> FormGroup:
        return FormGroup(
            display_name=display_name,
            fields=[
                InputTextElement(label=LocaleString(en="Reason")),
            ],
        )

    @classmethod
    def reject(cls, display_name: LocaleString, **kwargs) -> FormGroup:
        return FormGroup(display_name=display_name, fields=[...])
```

**Usage**:

```python
@process_step()
def request_review(...) -> Annotated[ReviewRequest, Human.Out(users=[])]:
    return ReviewRequest(
        data="...",
        forms=[
            ReviewRequest.approve(display_name=LocaleString(en="Approve")),
            ReviewRequest.reject(display_name=LocaleString(en="Reject")),
        ],
    )
```

## Common Patterns

**Reference**: `/home/user/aihub-core/aihub_process/playground/minimal_processes/`

- **Agent-Only**: Sequential agent chain. Example: `agent_only_process/`
- **Human-Only**: Approval workflows. Example: `human_only_process/`
- **Mixed**: Agent analysis + human decision. Example: `agent_to_human_process/`, `human_to_agent_process/`
- **Fan-Out**: Parallel processing. Example: `fan_out_process/`
- **Multi-Input**: Synchronize multiple inputs. Example: `multi_input_process/`
- **Process Sequence**: Chain processes. Example: `process_sequence/`

## Development Workflow

1. **Design process**: Identify entities, work distribution
2. **Create events**: WorkEvents, WorkRequestEvents
3. **Create process**: Inherit `AgenticProcess`, add `@process_step()` methods
4. **Create config**: `ProcessConfig` with metadata
5. **Test**: `ProcessTestRunner` + `pytest-bdd`
6. **Debug**: `trigger.py` (one-shot) or `run.py` (interactive)
7. **Observe**: Phoenix tracing (http://localhost:6006)

## Testing

**BDD with pytest-bdd**:

```python
@given("a MyProcess runner", target_fixture="process_runner")
def process_runner_fixture():
    return ProcessTestRunner(
        process_type=MyProcess,
        process_config=ProcessConfig(
            process_id="my_process",
            name=LocaleString(en="My Process"),
        ),
    )

@when("the agent completes work")
@async_test
async def agent_completes(process_runner: ProcessTestRunner):
    async with process_runner.test_run():
        await process_runner.send_event(
            AgentWorkEvent(...),
            process_walkthrough_id="test_walkthrough",
        )

@then("a human request is created")
def verify_human_request(process_runner: ProcessTestRunner):
    assert process_runner.has_event_of_class(HumanWorkRequestEvent)
```

## Debug Tools

**trigger.py**: One-shot test with specific event
**run.py**: Interactive multi-entity test (agents + process)
**Phoenix**: Visual process flow (http://localhost:6006)

## Pre-Commit

```bash
make pr-ready  # Format + lint
make test      # Run tests
```

## Essential Files

- Base process: `/home/user/aihub-core/aihub_process/aihub_process/agentic_processes/AgenticProcess.py`
- Step decorator: `/home/user/aihub-core/aihub_process/aihub_process/process/decorators/process_step.py`
- Test runner: `/home/user/aihub-core/aihub_process/aihub_process/runners/ProcessTestRunner.py`
- Delegators: `/home/user/aihub-core/aihub_process/aihub_process/delegators/`
- Minimal processes: `/home/user/aihub-core/aihub_process/playground/minimal_processes/`

## Quick Reference

**Create process**:

```python
class MyProcess(AgenticProcess):
    @process_step()
    def start(
        self,
        trigger: Annotated[TriggerEvent, Program.In(route="/start", method="POST")],
    ) -> Annotated[AgentRequest, Agent.Out(agent_class="MyAgent", agent_id="my_agent")]:
        return AgentRequest(start_event=UserMessageEvent(content=trigger.data))

    @process_step()
    def finish(
        self,
        result: Annotated[AgentResult, Agent.In(agent_class="MyAgent", agent_id="my_agent")],
    ) -> Annotated[FinalResult, Process.Out()]:
        return FinalResult(output=result.data)
```

**Enable logging**:

```python
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```
