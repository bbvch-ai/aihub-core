import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.workflow.annotations.extractors.extract_function_events import extract_function_events

from swiss_ai_hub.agent.agents.Agent import Agent

logger = logging.getLogger(__name__)


def step(
    *,
    max_executions_per_run: Annotated[
        int | None,
        "Maximum number of times this step can be executed in a single run",
    ] = None,
    stop_on_error: Annotated[bool, "If True, the workflow stops on any error in this step"] = True,
    name: Annotated[LocaleString | None, "A localized name for the step, used in UI or logs"] = None,
    icon: Annotated[str | None, "An icon name for the step from iconify.design, used in UI"] = None,
    description: Annotated[LocaleString | None, "A localized description of what the step does"] = None,
    precondition: Annotated[
        Callable[..., Awaitable[bool]] | None, "A function to check if the step is ready to run"
    ] = None,
):
    """
    Decorator that marks a function as a agentic workflow step, attaching metadata and analyzing its event inputs.

    ### Why This Decorator?
    In a agentic workflow system, steps are special functions that:
    - Consume certain event types
    - Optionally produce events
    - Have constraints like maximum execution count or custom naming/descriptions
    - Control the agentic workflow's behavior on errors

    By decorating a function with `@step`, you:
    1. Flag it as a step in the agentic workflow engine.
    2. Extract and store the event type requirements of its parameters for automated wiring.
    3. Attach metadata (like a user-friendly name, description, or execution limits).

    ### Example
    ```python
    @step(max_executions_per_run=3, stop_on_error=False, name=LocaleString(en="My Step"))
    def my_step(event: SomeEvent | None, data: list[AnotherEvent]):
        # Implementation...
        pass
    ```

    This step may run up to three times per run, doesn't stop the agentic workflow on errors,
    and expects either a `SomeEvent` or no event (`None`) and a list of `AnotherEvent` as inputs.
    """

    def decorator(func):
        input_events, output_events, input_event_mapping, parameter_optional_map, size_requirements = (
            extract_function_events(func)
        )

        # Mark the function as a step and store extracted metadata
        setattr(func, Agent.STEP_ANNOTATION, True)
        setattr(func, Agent.PRECONDITION_FUNCTION_ANNOTATION, precondition)
        setattr(func, Agent.INPUT_EVENTS_ANNOTATION, input_events)
        setattr(func, Agent.OUTPUT_EVENTS_ANNOTATION, output_events)
        setattr(func, Agent.INPUT_EVENT_MAPPING_ANNOTATION, input_event_mapping)
        setattr(func, Agent.PARAMETER_OPTIONAL_MAP_ANNOTATION, parameter_optional_map)
        setattr(func, Agent.SIZE_REQUIREMENT_ANNOTATION, size_requirements)
        setattr(func, Agent.MAX_EXECUTION_PER_RUN_ANNOTATION, max_executions_per_run)
        setattr(func, Agent.STOP_ON_ERROR_ANNOTATION, stop_on_error)
        setattr(func, Agent.STEP_NAME_ANNOTATION, name)
        setattr(func, Agent.STEP_DESCRIPTION_ANNOTATION, description)
        setattr(func, Agent.STEP_ICON_ANNOTATION, icon)
        setattr(func, Agent.SIGNATURE_ANNOTATION, inspect.signature(func))

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
