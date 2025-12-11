# aihub_agent - AI Agent Workflows

**Purpose**: Agent logic and workflow definitions. Autonomous AI components designed for proactive process automation.

Tech Stack & Paradigms: LlamaIndex Core workflow engine with custom @step decorator. LlamaIndex LLMs (OpenAI, Azure OpenAI). NATS pub-sub for event-driven architecture. Redis v5 client for Valkey state (RunContext ephemeral, ThreadContext persistent). MongoEngine for persistence. OpenTelemetry SDK + API + OTLP exporter. OpenInference LlamaIndex instrumentation. Pydantic v2 + pydantic-settings. python-i18n for translations. colorlog for logging. cachetools for TTL caching. stringcase for string manipulation. flatdict for nested dict flattening. DispatchableWorkflow base class. Transparent, auditable workflows (not black-box). pytest-bdd for Gherkin BDD tests. AgentRunner and AgentTestRunner. pytest-mock + pytest-asyncio. Development tools: matplotlib, seaborn, tabulate for analysis.

## Scope Responsibility

Implements transparent, workflow-based agents (NOT black boxes). Agents are dispatchable workflows with explicit steps, traceable execution, and integration with processes.

## Folder Structure

```
aihub_agent/
├── agents/                    # Production agent implementations (RagAgent, LLMWrappingAgent)
├── context/                   # RunContext (ephemeral) + ThreadContext (persistent)
├── runners/                   # AgentRunner, AgentTestRunner
├── workflow/                  # Core: @step decorator, DispatchableWorkflow
└── playground/                # START HERE for learning
    ├── agent/                 # Production agent examples
    └── minimal_workflow/      # Self-contained pattern examples (ESSENTIAL)
```

## Key Concepts

**Agent = Dispatchable Workflow**:

- `Agent` inherits from `DispatchableWorkflow`
- Structured operations: `@step()` methods consume events → produce events
- Transparent: Every step traceable in Phoenix

**Step Decorator**:

- `@step()`: Defines workflow building blocks
- Parameters: `max_executions_per_run`, `stop_on_error`, `name`, `description`, `icon`, `precondition`
- Example: `/home/user/aihub-core/aihub_agent/aihub_agent/workflow/decorators/step.py`

**Context Management**:

- **RunContext**: Ephemeral state within single run. Expires 30 days. Use for intermediate calculations.
- **ThreadContext**: Persistent state across runs. Maintains conversation history. Expires 30 days.

**Event Flow**:

- Agents consume/produce events (from `aihub_lib.nats.events`)
- `StartEvent` → workflow steps → `StopEvent`
- Phoenix visualizes flow: http://localhost:6006

## Common Patterns

**Reference**: `/home/user/aihub-core/aihub_agent/playground/minimal_workflow/`

- **Simple Linear**: `simple_workflow/` - Sequential A→B→C
- **Conditional**: `conditional_workflow/` - Branch based on data
- **Human-in-the-Loop**: `human_in_the_loop_workflow/` - Pause for human input
- **Agent-in-the-Loop**: `agent_in_the_loop_workflow/` - Orchestrate sub-agents
- **Bounded Loop**: `bounded_loop/` - Iterate with RunContext counter
- **Fan-Out**: `fan_out_workflow/` - Parallel processing with `list[Event]`
- **Precondition**: `precondition_workflow/` - Synchronize parallel branches
- **Multi-Locale**: `multi_locale_workflow/` - i18n with LocaleHandler

## Development Workflow

1. **Create agent**: Inherit `Agent`, add `@step()` methods
2. **Create config**: `AgentConfig` subclass with Pydantic validation
3. **Create events**: Custom events if needed
4. **Test**: `AgentTestRunner` + `pytest-bdd` (Gherkin features in `tests/features/`)
5. **Debug**: `trigger.py` (one-shot test) or `run.py` (interactive)
6. **Observe**: Phoenix tracing (http://localhost:6006)

## Testing

**BDD with pytest-bdd**:

- Feature files: `tests/features/*.feature` (Gherkin)
- Step implementations: `tests/test_*.py`
- Runner: `AgentTestRunner` provides sandboxed env

**Debug Tools**:

- `trigger.py`: Focused one-shot testing
- `run.py`: Interactive multi-run testing
- Phoenix MCP: Programmatic trace access

## Pre-Commit

```bash
make pr-ready  # Format + lint + type check
make test      # pytest -k "not azure"
```

## Essential Files

- Base agent: `/home/user/aihub-core/aihub_agent/aihub_agent/agents/Agent.py`
- Step decorator: `/home/user/aihub-core/aihub_agent/aihub_agent/workflow/decorators/step.py`
- Test runner: `/home/user/aihub-core/aihub_agent/aihub_agent/runners/AgentTestRunner.py`
- Context: `/home/user/aihub-core/aihub_agent/aihub_agent/context/`
- Playground: `/home/user/aihub-core/aihub_agent/playground/`

## Quick Reference

**Create agent**:

```python
class MyAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> CustomEvent:
        return CustomEvent(data="processed")

    @step()
    async def end_step(self, event: CustomEvent) -> StopEvent:
        return StopEvent()
```

**Access context**:

```python
@step()
async def my_step(self, event: MyEvent, run_context: RunContext, thread_context: ThreadContext):
    count = await thread_context.get("count", 0)
    await thread_context.set("count", count + 1)
```

**Enable logging**:

```python
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```
