---
name: scaffold-process
description: Generate a new agentic business process with entity delegation
  (Agent, Human, Program). Creates process class, work events, form definitions,
  and BDD tests.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Agentic Process

Generate boilerplate for a new business process. The process name/purpose should be provided via `$ARGUMENTS`.

## Before You Start

Read the process scope guide: `/home/user/aihub-core/aihub_process/AGENTS.md`

Study existing processes (check `aihub_process/playground/minimal_processes/` for examples).

## What to Generate

### 1. Process Directory Structure

Create in `aihub_process/aihub_process/agentic_processes/<process_name>/`:

```
<process_name>/
├── __init__.py
├── process.py        # Main AgenticProcess class
├── events/
│   ├── __init__.py
│   └── events.py     # Start, Stop, WorkRequest, Work events
├── config/
│   ├── __init__.py
│   └── config.py     # Process configuration
└── forms/
    ├── __init__.py
    └── forms.py      # FormGroup definitions for Human.In events
```

### 2. Process Class (`process.py`)

- Extend `AgenticProcess`
- Define `@step` methods for workflow stages
- Use entity delegation annotations:
  - `Agent.In` / `Agent.Out` — delegate to an AI agent
  - `Human.In` / `Human.Out` — delegate to a human (via form)
  - `Program.In` / `Program.Out` — delegate to an external program/API

### 3. Events (`events/events.py`)

- `<ProcessName>StartEvent(StartEvent)` — process initiation
- `<ProcessName>StopEvent(StopEvent)` — process completion
- `<ProcessName><Action>WorkRequestEvent(WorkRequestEvent)` — request entity to do work
- `<ProcessName><Action>WorkEvent(WorkEvent)` — receive result from entity
- WorkRequest/Work events always come in pairs

### 4. Forms (`forms/forms.py`)

For `Human.In` events, define FormGroup with:
- Field definitions for user input
- Validation rules
- LocaleString labels (de, en, fr, it)

### 5. Config (`config/config.py`)

- Form duality pattern (same as agents)
- Process-specific parameters
- Delegation configuration (which agents, what timeouts)

### 6. Tests

Create in `aihub_process/tests/agentic_processes/<process_name>/`:
- `test_<process_name>.py` — Unit tests
- `tests/features/<process_name>.feature` — BDD Gherkin scenarios

## Key Patterns

- **WorkEvent pairs**: Every WorkRequestEvent MUST have a matching WorkEvent
- **Entity delegation**: Clear In/Out annotations on all delegation steps
- **Form definitions**: Human interactions require FormGroup with all 4 locales
- **Complete chains**: StartEvent → delegation cycles → StopEvent
