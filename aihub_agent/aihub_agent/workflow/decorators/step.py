import inspect
import logging
from typing import Annotated, Awaitable, Callable, Optional

from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.workflow.annotations.extractors.extract_function_events import extract_function_events

logger = logging.getLogger(__name__)


def step(
    *,
    max_executions_per_run: Annotated[
        Optional[int],
        "Maximum number of times this step can be executed in a single run",
    ] = None,
    stop_on_error: Annotated[bool, "If True, the workflow stops on any error in this step"] = True,
    name: Annotated[Optional[LocaleString], "A localized name for the step, used in UI or logs"] = None,
    description: Annotated[Optional[LocaleString], "A localized description of what the step does"] = None,
    precondition: Annotated[
        Optional[Callable[..., Awaitable[bool]]], "A function to check if the step is ready to run"
    ] = None,
):
    """
    Decorator that marks a function as a workflow step, attaching metadata and analyzing its event inputs.

    ### Why This Decorator?
    In a workflow system, steps are special functions that:
    - Consume certain event types
    - Optionally produce events
    - Have constraints like maximum execution count or custom naming/descriptions
    - Control the workflow's behavior on errors

    By decorating a function with `@step`, you:
    1. Flag it as a step in the workflow engine.
    2. Extract and store the event type requirements of its parameters for automated wiring.
    3. Attach metadata (like a user-friendly name, description, or execution limits).

    ### Stored Attributes
    On the decorated function, this decorator sets:
    - `_is_step`: A boolean marker that this is indeed a workflow step.
    - `_input_events`: A set of all event types the function’s parameters accept.
    - `_input_event_mapping`: A dict mapping parameter names to the event types they accept.
    - `_parameter_optional_map`: A dict mapping parameter names to a boolean indicating if they are optional.
    - `_size_requirements`: A dict mapping parameter names to required collection sizes (if any).
    - `_max_executions_per_run`: The maximum number of times this step can be executed in one run.
    - `_stop_on_error`: Whether to halt the workflow if this step errors.
    - `_step_name` and `_step_description`: Optional human-readable metadata.

    After applying this decorator, the step’s signature is also stored, facilitating reflection or tooling.

    ### Example
    ```python
    @step(max_executions_per_run=3, stop_on_error=False, name=LocaleString(en="My Step"))
    def my_step(event: SomeEvent | None, data: List[AnotherEvent]):
        # Implementation...
        pass
    ```

    This step may run up to three times per run, doesn't stop the workflow on errors,
    and expects either a `SomeEvent` or no event (`None`) and a list of `AnotherEvent` as inputs.
    """

    def decorator(func):
        # Extract the event types and parameter requirements from the function signature
        input_events, input_event_mapping, parameter_optional_map, size_requirements = extract_function_events(func)

        # Mark the function as a step and store extracted metadata
        setattr(func, "_is_step", True)
        setattr(func, "_precondition_fn", precondition)
        setattr(func, "_input_events", input_events)
        setattr(func, "_input_event_mapping", input_event_mapping)
        setattr(func, "_parameter_optional_map", parameter_optional_map)
        setattr(func, "_size_requirements", size_requirements)
        setattr(func, "_max_executions_per_run", max_executions_per_run)
        setattr(func, "_stop_on_error", stop_on_error)
        setattr(func, "_step_name", name)
        setattr(func, "_step_description", description)
        setattr(func, "__signature__", inspect.signature(func))

        logger.debug(f"Decorated step: {func.__name__} with input events: {input_events}")
        logger.debug(f"Decorated step: {func.__name__} with input event mapping: {input_event_mapping}")
        logger.debug(f"Decorated step: {func.__name__} with parameter optional map: {parameter_optional_map}")
        logger.debug(f"Decorated step: {func.__name__} with size requirements: {size_requirements}")
        logger.debug(f"Decorated step: {func.__name__} with max executions per run: {max_executions_per_run}")
        logger.debug(f"Decorated step: {func.__name__} with stop on error: {stop_on_error}")
        logger.debug(f"Decorated step: {func.__name__} with step name: {name}")
        logger.debug(f"Decorated step: {func.__name__} with step description: {description}")

        return func

    return decorator
