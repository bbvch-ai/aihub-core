---
name: scaffold-agent
description: Generate a new AI agent with all required boilerplate. Creates the agent
  class, events, config (with form duality), BDD tests, trigger, and runner setup.
  Follows the LlamaIndex workflow pattern.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New AI Agent

Generate all boilerplate for a new AI agent. The agent name/description should be provided via `$ARGUMENTS`.

## Before You Start

Read the agent scope guide: `/home/user/aihub-core/aihub_agent/AGENTS.md`

Study an existing agent for reference patterns (e.g., the playground agents in `aihub_agent/playground/`).

## What to Generate

### 1. Agent Directory Structure

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

### 2. Agent Class (`agent.py`)

- Extend `Workflow` from LlamaIndex
- Define `@step` methods for each workflow stage
- Start with: StartEvent → processing step(s) → StopEvent
- Use async for all I/O operations
- Include proper type hints on all methods

### 3. Events (`events/events.py`)

- Create `<AgentName>StartEvent(StartEvent)` — with input parameters
- Create `<AgentName>StopEvent(StopEvent)` — with output result
- Create intermediate `ControlEvent` subclasses as needed
- Follow naming: `<AgentName><Action>Event`

### 4. Config (`config/config.py`)

- Use the **form duality pattern**: Pydantic model with `@property` methods returning `FormGroup`
- Define `Field` elements for each configurable parameter
- Include sensible defaults
- Support all 4 locales in `LocaleString` (de, en, fr, it)

### 5. Tests

Create in `aihub_agent/tests/agents/<agent_name>/`:

- `test_<agent_name>.py` — Unit tests for step methods
- `tests/features/<agent_name>.feature` — BDD scenario (happy path)

### 6. Registration

Set up agent registration via `trigger.py` or `ClassDiscoveryRequest`.

## Key Patterns to Follow

- **Event chain**: Every event emitted by a step MUST be consumed by another step
- **No dead ends**: StartEvent → ... → StopEvent must be complete
- **Form duality**: Config class serves as both data container AND UI form definition
- **Async consistently**: All I/O uses async/await
- **Type hints**: Mandatory on all parameters and returns
