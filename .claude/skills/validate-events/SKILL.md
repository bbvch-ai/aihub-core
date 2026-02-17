---
name: validate-events
description: Validate Swiss AI Agent Protocol event classes for correct hierarchy, naming, classification (Control vs Display), and completeness per agent/process. Use when user says 'check events', 'validate event system', 'are my events correct', 'event hierarchy check', or 'verify protocol compliance'. Catches misclassified, orphaned, and incomplete events.
allowed-tools: Read, Grep, Glob
---

# Event System Validation

Validate Swiss AI Agent Protocol events for correctness and completeness. Scope via `$ARGUMENTS`: `agents`, `processes`,
a specific agent/process name, or `all` (default).

## Step 1: Find All Event Classes

Search for `BaseEvent` subclasses in these locations:

- `aihub_lib/aihub_lib/events/` — shared/base events
- `aihub_agent/aihub_agent/agents/*/events/` — agent-specific events
- `aihub_process/aihub_process/agentic_processes/*/events/` — process-specific events

Search patterns (use Grep):

- `class *Event(BaseEvent)`
- `class *Event(ControlEvent)`
- `class *Event(DisplayEvent)`
- `class *Event(StartEvent)`
- `class *Event(StopEvent)`
- `class *Event(WorkEvent)`
- `class *Event(WorkRequestEvent)`

**Expected output**: A complete inventory of all event classes with their base types and file locations.

## Step 2: Verify Naming Conventions

Check each event class name follows the convention:

| Pattern        | Convention                   | Example                         |
| -------------- | ---------------------------- | ------------------------------- |
| Agent events   | `<AgentName><Action>Event`   | `ResearchAgentSearchEvent`      |
| Process events | `<ProcessName><Action>Event` | `OnboardingProcessApproveEvent` |
| Start events   | `<Name>StartEvent`           | `ResearchAgentStartEvent`       |
| Stop events    | `<Name>StopEvent`            | `ResearchAgentStopEvent`        |
| Work events    | `<Name>WorkEvent`            | `OnboardingWorkEvent`           |
| Work requests  | `<Name>WorkRequestEvent`     | `OnboardingWorkRequestEvent`    |

Flag any events that do not follow naming conventions.

## Step 3: Verify ControlEvent vs DisplayEvent Classification

Rules:

- **ControlEvent** subclasses: Drive workflow execution, used as `@step` inputs/outputs
- **DisplayEvent** subclasses: For UI/observability only, never affect workflow control flow
- **Violation**: No event class should extend both ControlEvent and DisplayEvent

For each event, verify it is classified correctly by checking how it is used in workflow steps.

## Step 4: Check Agent Event Completeness

For each agent in `aihub_agent/aihub_agent/agents/*/`:

1. Has a `StartEvent` (required)
2. Has a `StopEvent` (required)
3. Event chain is complete — every emitted event is consumed by a step
4. No dead-end events (emitted but never consumed)
5. No orphan events (defined but never emitted)

## Step 5: Check Process Event Completeness

For each process in `aihub_process/aihub_process/agentic_processes/*/`:

1. Has a `StartEvent` and `StopEvent`
2. `WorkEvent` / `WorkRequestEvent` always exist in pairs
3. Delegation annotations are present where needed
4. `FormGroup` exists for any Human-In-The-Loop events

## Step 6: Summary Report

| Category           | Count | Issues                          |
| ------------------ | ----- | ------------------------------- |
| Total events       | 42    | —                               |
| ControlEvents      | 28    | 1 misclassified                 |
| DisplayEvents      | 14    | 0 issues                        |
| Agents complete    | 5/6   | ResearchAgent missing StopEvent |
| Processes complete | 3/3   | All OK                          |

List all issues with file paths and line numbers for easy fixing.

## Examples

- `/validate-events` — Validate all events across agents and processes
- `/validate-events agents` — Validate only agent events
- `/validate-events ResearchAgent` — Validate events for a specific agent

## Troubleshooting

- **"No events found"**: Verify the search paths exist. Agent events live in `agents/*/events/`, not at the agent root.
- **False positive on orphan events**: Some events are emitted dynamically or via `ctx.send_event()`. Check the workflow
  code manually.
- **WorkEvent without pair**: Every `WorkEvent` must have a matching `WorkRequestEvent`. If one is missing, create it.

## Reference

Protocol documentation: `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/`
