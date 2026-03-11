import inspect

from swiss_ai_hub.core.workflow import extract_function_events


def precondition():
    """
    Decorator that marks a function as a precondition for a workflow step.

    ### Why this Decorator?
    A workflow step might have complex preconditions that must be fulfilled before it can run.
    By decorating a function with `@precondition`, you:
    1. Flag it as a precondition for a step in the workflow engine.
    2. Allow the AgentDispatcher to resolve the function arguments you need in order to resolve the condition.

    ### Example
    ```python
    def ensure_enough_events(parallel_events: list[ParallelEvent], config: PreconditionAgentConfig) -> bool:
        return len(parallel_events) == config.number_of_events

    class PreconditionAgent(Agent):
        @step(precondition=ensure_enough_events)
        async def stop_step(self, _: list[ParallelEvent]):
            # Implementation...
            pass
    ```
    """

    def decorator(func):
        input_events, output_events, input_event_mapping, parameter_optional_map, size_requirements = (
            extract_function_events(func)
        )

        # Mark the function as a step and store extracted metadata
        setattr(func, "_is_step", True)
        setattr(func, "_precondition_fn", precondition)
        setattr(func, "_input_events", input_events)
        setattr(func, "_output_events", output_events)
        setattr(func, "_input_event_mapping", input_event_mapping)
        setattr(func, "_parameter_optional_map", parameter_optional_map)
        setattr(func, "_size_requirements", size_requirements)
        setattr(func, "__signature__", inspect.signature(func))

        return func

    return decorator
