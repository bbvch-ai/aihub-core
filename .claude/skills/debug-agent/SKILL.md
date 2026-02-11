---
name: debug-agent
description: Debug an AI agent by tracing its event flow, checking configuration,
  and analyzing step execution. Use when an agent is not behaving as expected.
allowed-tools: Bash, Read, Grep, Glob
---

# Agent Debugging Assistant

Debug an AI agent. Agent name or issue description via `$ARGUMENTS`.

## Before You Start

Read: `/home/user/aihub-core/aihub_agent/AGENTS.md`

## Step 1: Locate the Agent

Search in `aihub_agent/aihub_agent/agents/` and `aihub_agent/playground/`. Identify: class name, base class, @step methods, events consumed/produced, config class.

## Step 2: Map Event Flow

Trace: StartEvent → step_1() → IntermediateEvent → step_2() → ... → StopEvent

Check for: dead ends, missing steps, circular paths (verify termination).

## Step 3: Verify Configuration

Find Config class. Check form duality pattern (Pydantic + FormGroup). Verify defaults and external resource references.

## Step 4: Check Registration

Verify trigger.py or ClassDiscoveryRequest registration. Check module importability.

## Step 5: Common Issues

- **Won't start**: Check StartEvent, runner config, NATS connectivity
- **Stops unexpectedly**: Unhandled exceptions, missing await, LLM call failures
- **Wrong output**: Logic errors in steps, incorrect model, wrong system prompt, RAG issues
- **Slow**: Vector search top_k, model selection, unnecessary re-indexing, blocking I/O

## Step 6: Check Tests

Find tests and BDD features. Verify coverage of happy path, error cases, edge cases.

## Summary

Report: location, steps, events, config validity, registration, test coverage, potential issues.
