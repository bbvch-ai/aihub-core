---
name: debug-agent
description: >-
  Debug a LlamaIndex AI agent by tracing event flow, checking configuration, verifying registration,
  and analyzing step execution. Use when user says 'my agent is broken', 'agent not responding',
  'debug the agent', 'agent stuck', 'agent produces wrong output', 'agent is slow', 'agent throws
  error', or 'agent won't start'. Covers event tracing, config validation, and test coverage.
allowed-tools: Bash, Read, Grep, Glob
---

# Agent Debugging Assistant

Debug an AI agent. Agent name or issue description via `$ARGUMENTS`.

## Step 1: Read Scope Documentation

Read `/home/user/aihub-core/aihub_agent/CLAUDE.md` to understand agent architecture and patterns.

## Step 2: Locate the Agent

1. Search in `aihub_agent/aihub_agent/agents/` and `aihub_agent/playground/` for the agent class
2. Identify these key elements:
   - Class name and base class (e.g., `Workflow`)
   - All `@step` methods with their input/output event types
   - Events consumed and produced by each step
   - Config class (Pydantic model)

**Expected output**: List of all steps with their event signatures.

## Step 3: Map Event Flow

1. Trace the full event chain: `StartEvent -> step_1() -> IntermediateEvent -> step_2() -> ... -> StopEvent`
2. Draw the flow diagram showing all paths
3. Check for these problems:
   - **Dead ends**: Steps that produce events no other step consumes
   - **Missing steps**: Events that are consumed but never produced
   - **Circular paths**: Verify loops have termination conditions
   - **Missing StopEvent**: Every execution path must eventually produce a StopEvent

## Step 4: Verify Configuration

1. Find the Config class associated with the agent
2. Check the form duality pattern (Pydantic model + FormGroup)
3. Verify default values are sensible
4. Verify external resource references (LLM model names, vector store collections, etc.)

## Step 5: Check Registration

1. Verify `trigger.py` or `ClassDiscoveryRequest` registration exists
2. Confirm the module is importable (`python -c "from aihub_agent.agents.<name> import <AgentClass>"`)
3. Check that agent_class and agent_id match what callers expect

## Step 6: Diagnose by Symptom

| Symptom                | What to Check                                                                                |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| **Won't start**        | StartEvent handler exists, runner config correct, NATS connectivity, agent registered        |
| **Stops unexpectedly** | Unhandled exceptions in steps, missing `await` on async calls, LLM call failures             |
| **Wrong output**       | Logic errors in steps, incorrect model name, wrong system prompt, RAG retrieval issues       |
| **Slow performance**   | Vector search `top_k` too high, wrong model selection, unnecessary re-indexing, blocking I/O |
| **No response**        | Check if StopEvent is ever reached, check NATS subject matching                              |

## Step 7: Check Tests

1. Find tests in `aihub_agent/tests/` matching the agent name
2. Find BDD features in `aihub_agent/tests/features/`
3. Verify coverage of: happy path, error cases, edge cases
4. Run tests: `cd /home/user/aihub-core/aihub_agent && poetry run pytest tests/ -k "<agent_name>" -v`

## Step 8: Report

Provide a structured report with:

- **Agent location**: File path and class name
- **Event flow**: Complete step/event chain (valid or broken)
- **Configuration**: Valid or issues found
- **Registration**: Correctly registered or missing
- **Test coverage**: Tests found and their status
- **Root cause**: Most likely issue and affected file/line
- **Suggested fix**: Specific code change to resolve the issue

## Troubleshooting Quick Reference

| Error                          | Likely Cause                               | Fix                                                             |
| ------------------------------ | ------------------------------------------ | --------------------------------------------------------------- |
| `TimeoutError` on agent call   | NATS not connected or agent not subscribed | Check NATS service, verify agent runner is started              |
| `ExceptionEvent` returned      | Unhandled error in a step                  | Check agent logs for full traceback                             |
| Agent registered but not found | Discovery not working                      | Verify `ClassDiscoveryRequest` handler returns correct metadata |
| Config validation error        | Invalid config values                      | Check Config class defaults and env variable overrides          |
