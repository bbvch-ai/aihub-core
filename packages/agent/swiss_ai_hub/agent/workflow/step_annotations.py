"""
Agent-specific step annotation keys.

These live in a dependency-free module so the `@step` decorator can stamp them onto step functions
without importing `Agent` — otherwise `agent.py` (which now carries inherited `@step` methods via
`SelfAwarenessMixin`) and `step.py` would form an import cycle.
"""

AGENT_STEP_ANNOTATION = "_is_agent_step"
AGENT_PRECONDITION_FUNCTION_ANNOTATION = "_precondition_fn"
AGENT_STOP_ON_ERROR_ANNOTATION = "_stop_on_error"
AGENT_MAX_EXECUTION_PER_RUN_ANNOTATION = "_max_executions_per_run"
