---
name: validate-events
description: Validate the event hierarchy, registration, and usage across
  the platform. Checks event classes, classification, serialization,
  and subscriber matching. Use when modifying the event system.
allowed-tools: Read, Grep, Glob
---

# Event System Validation

Validate Swiss AI Agent Protocol events. Scope via `$ARGUMENTS` (agents, processes, specific name, or all).

## Step 1: Find All Event Classes

Search for BaseEvent subclasses in:
- `aihub_lib/aihub_lib/events/`
- `aihub_agent/aihub_agent/agents/*/events/`
- `aihub_process/aihub_process/agentic_processes/*/events/`

Patterns: `class *Event(BaseEvent)`, `class *Event(ControlEvent)`, `class *Event(DisplayEvent)`, `class *Event(StartEvent)`, `class *Event(StopEvent)`, `class *Event(WorkEvent)`, `class *Event(WorkRequestEvent)`

## Step 2: Verify Naming Conventions

- Agent events: `<AgentName><Action>Event`
- Process events: `<ProcessName><Action>Event`
- Start/Stop events: `<Name>StartEvent`, `<Name>StopEvent`
- Work events: `<Name>WorkEvent` / `<Name>WorkRequestEvent` (always in pairs)

## Step 3: Check ControlEvent vs DisplayEvent Classification

- ControlEvents: Drive workflow, used in @step inputs/outputs
- DisplayEvents: UI/observability only, no workflow impact
- No event should extend both

## Step 4: Agent Event Completeness

For each agent: has StartEvent, has StopEvent, event chain is complete, no dead ends, no orphan events.

## Step 5: Process Event Completeness

For each process: has Start/Stop, WorkEvent pairs match, delegation annotations present, FormGroup exists for Human.In events.

## Step 6: Summary

Report: event counts by type, classification correctness, completeness per agent/process, issues found.

## Reference

Protocol docs: `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/`
