---
name: scaffold-process
description: Generate a new agentic business process with entity delegation (Agent,
  Human, Program). Creates process class, work events, forms, config, and BDD tests.
  Use when user says "create a process", "scaffold process", "new business process",
  "add agentic process", "orchestrate agents and humans", or "build a workflow for X".
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Agentic Process

Generate boilerplate for a new business process. The process name/purpose should be provided via `$ARGUMENTS`.

## Step 1: Read Reference Materials

1. Read the process scope guide: `/home/user/aihub-core/aihub_process/AGENTS.md`
2. Study existing processes in `aihub_process/playground/minimal_processes/` for examples
3. Extract the process name from `$ARGUMENTS` and convert to `snake_case` for directories, `CamelCase` for classes

## Step 2: Create Process Directory Structure

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

## Step 3: Create Process Class (`process.py`)

- Extend `AgenticProcess`
- Define `@step` methods for workflow stages
- Use entity delegation annotations:
  - `Agent.In` / `Agent.Out` -- delegate to an AI agent
  - `Human.In` / `Human.Out` -- delegate to a human (via form)
  - `Program.In` / `Program.Out` -- delegate to an external program/API

## Step 4: Create Events (`events/events.py`)

- `<ProcessName>StartEvent(StartEvent)` -- process initiation
- `<ProcessName>StopEvent(StopEvent)` -- process completion
- `<ProcessName><Action>WorkRequestEvent(WorkRequestEvent)` -- request entity to do work
- `<ProcessName><Action>WorkEvent(WorkEvent)` -- receive result from entity
- WorkRequest/Work events always come in **pairs** (request + response)

## Step 5: Create Forms (`forms/forms.py`)

For `Human.In` events, define FormGroup with:
- Field definitions for user input
- Validation rules
- LocaleString labels in all 4 locales (de, en, fr, it)

## Step 6: Create Config (`config/config.py`)

- Form duality pattern (same as agents)
- Process-specific parameters
- Delegation configuration (which agents, what timeouts)

## Step 7: Create Tests

Create in `aihub_process/tests/agentic_processes/<process_name>/`:
- `test_<process_name>.py` -- Unit tests
- `tests/features/<process_name>.feature` -- BDD Gherkin scenarios

## Key Patterns

- **WorkEvent pairs**: Every WorkRequestEvent MUST have a matching WorkEvent
- **Entity delegation**: Clear In/Out annotations on all delegation steps
- **Form definitions**: Human interactions require FormGroup with all 4 locales
- **Complete chains**: StartEvent --> delegation cycles --> StopEvent

## Examples

**Input**: `$ARGUMENTS = "invoice_approval - Process where an agent extracts invoice data and a human approves it"`
**Expected output files**:
- `aihub_process/aihub_process/agentic_processes/invoice_approval/process.py` with class `InvoiceApprovalProcess`
- `aihub_process/aihub_process/agentic_processes/invoice_approval/events/events.py` with `InvoiceApprovalStartEvent`, `InvoiceApprovalExtractWorkRequestEvent`, `InvoiceApprovalExtractWorkEvent`, `InvoiceApprovalApproveWorkRequestEvent`, `InvoiceApprovalApproveWorkEvent`, `InvoiceApprovalStopEvent`
- `aihub_process/aihub_process/agentic_processes/invoice_approval/forms/forms.py` with approval FormGroup

## Troubleshooting

- **Unpaired WorkEvents**: Every `WorkRequestEvent` must have exactly one matching `WorkEvent` -- missing pairs cause runtime errors
- **Entity delegation mismatch**: Ensure `Agent.In`/`Agent.Out`, `Human.In`/`Human.Out`, `Program.In`/`Program.Out` annotations match the event types
- **Missing locale strings**: Forms must define labels in all 4 locales (de, en, fr, it) or the UI will show empty labels
- **Dead-end steps**: Verify the chain StartEvent --> ... --> StopEvent is complete with no orphan steps
