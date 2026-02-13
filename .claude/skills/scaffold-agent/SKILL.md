---
name: scaffold-agent
description: Generate a new LlamaIndex AI agent with all required boilerplate (agent
  class, events, config with form duality, BDD tests, trigger, runner). Use when user
  says "create new agent", "scaffold an agent", "generate agent boilerplate", "add AI
  agent", "new workflow agent", or "build an agent for X".
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New AI Agent

Generate all boilerplate for a new AI agent. The agent name/description should be provided via `$ARGUMENTS`.

## Step 1: Read Reference Materials

1. Read the agent scope guide: `/home/user/aihub-core/aihub_agent/CLAUDE.md`
2. Study an existing agent for reference patterns (e.g., the playground agents in `aihub_agent/playground/`)
3. Extract the agent name from `$ARGUMENTS` and convert to `snake_case` for directories, `CamelCase` for classes

## Step 2: Create Agent Directory Structure

Create in `aihub_agent/aihub_agent/agents/<agent_name>/`:

```
<agent_name>/
├── __init__.py
├── agent.py          # Main agent class
├── config/
│   ├── __init__.py
│   └── config.py     # Config with form duality
├── events/
│   ├── __init__.py
│   └── events.py     # Start, Stop, and intermediate events
├── trigger.py        # Agent trigger/registration
└── run.py           # Standalone runner for testing
```

## Step 3: Create the Agent Class (`agent.py`)

- Extend `Workflow` from LlamaIndex
- Define `@step` methods for each workflow stage
- Start with: StartEvent --> processing step(s) --> StopEvent
- Use async for all I/O operations
- Include proper type hints on all methods

## Step 4: Create Events (`events/events.py`)

- Create `<AgentName>StartEvent(StartEvent)` with input parameters
- Create `<AgentName>StopEvent(StopEvent)` with output result
- Create intermediate `ControlEvent` subclasses as needed
- Follow naming convention: `<AgentName><Action>Event`

## Step 5: Create Config (`config/config.py`)

- Use the **form duality pattern**: Pydantic model with `@property` methods returning `FormGroup`
- Define `Field` elements for each configurable parameter
- Include sensible defaults
- Support all 4 locales in `LocaleString` (de, en, fr, it)

## Step 6: Create Tests

Create in `aihub_agent/tests/agents/<agent_name>/`:

- `test_<agent_name>.py` -- Unit tests for step methods
- `tests/features/<agent_name>.feature` -- BDD scenario (happy path)

## Step 7: Register the Agent

Set up agent registration via `trigger.py` or `ClassDiscoveryRequest`.

## Key Patterns to Follow

- **Event chain**: Every event emitted by a step MUST be consumed by another step
- **No dead ends**: StartEvent --> ... --> StopEvent must be complete
- **Form duality**: Config class serves as both data container AND UI form definition
- **Async consistently**: All I/O uses async/await
- **Type hints**: Mandatory on all parameters and returns

## Examples

**Input**: `$ARGUMENTS = "document_summarizer - An agent that summarizes uploaded documents"`
**Expected output files**:
- `aihub_agent/aihub_agent/agents/document_summarizer/agent.py` with class `DocumentSummarizerWorkflow`
- `aihub_agent/aihub_agent/agents/document_summarizer/events/events.py` with `DocumentSummarizerStartEvent`, `DocumentSummarizerStopEvent`
- `aihub_agent/aihub_agent/agents/document_summarizer/config/config.py` with form duality config
- `aihub_agent/tests/agents/document_summarizer/test_document_summarizer.py`

## Troubleshooting

- **Missing event consumer**: If you get "event has no consumer" errors, ensure every emitted event type has a `@step` method that accepts it
- **Import errors**: Verify all `__init__.py` files export the necessary classes
- **Form duality issues**: Config must inherit from Pydantic BaseModel AND define `@property` methods returning `FormGroup`
- **BDD test limitations**: pytest-bdd has async limitations -- use plain pytest for async step tests
