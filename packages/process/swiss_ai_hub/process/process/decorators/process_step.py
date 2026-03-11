import inspect
from typing import Annotated

from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.workflow import extract_function_events

from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.process.annotations.extractors.extract_function_process_in_events import (
    extract_function_process_in_events,
)
from swiss_ai_hub.process.process.annotations.extractors.extract_function_process_out_events import (
    extract_function_process_out_events,
)


def process_step(
    *,
    name: Annotated[LocaleString | None, "A localized name for the step"] = None,
    icon: Annotated[str | None, "An icon name for the step"] = None,
    description: Annotated[LocaleString | None, "A localized description of what the step does"] = None,
):
    """
    Decorator that marks a function as a process step, attaching metadata and analyzing its event inputs.

    ### Why This Decorator?
    In a process system, steps are special functions that:
    - Define from which the process input originates - e.g. who did the work
    - To which the process step output shall be delegated - e.g. who should do work next
    - Consume Work
    - Delegate Work

    By decorating a function with `@process_step`, you:
    1. Flag it as a step in the process engine.
    2. Extract information about input and output delegation.
    3. Extract and store the event type requirements of its parameters for automated wiring.
    4. Attach metadata (like a user-friendly name and description).

    ### Example
    ```python
    @process_step()
    async def step(
        self, some_work: Annotated[AgentWorkRequest.work, Agent.In(agent_class="AgentA", agent_id="agent_a")]
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        return CustomProcessStopEvent(...)
    ```

    This step expects work from an Agent 'AgentA' with ID 'agent_a' and maps the work to a terminating process
    event.
    """

    def decorator(func):
        # --- Part 1: Standard Event Extraction (for dispatching system) ---
        input_events, output_events, input_event_mapping, parameter_optional_map, size_requirements = (
            extract_function_events(func)
        )
        setattr(func, AgenticProcess.STEP_ANNOTATION, True)
        setattr(func, AgenticProcess.INPUT_EVENTS_ANNOTATION, input_events)
        setattr(func, AgenticProcess.OUTPUT_EVENTS_ANNOTATION, output_events)
        setattr(func, AgenticProcess.INPUT_EVENT_MAPPING_ANNOTATION, input_event_mapping)
        setattr(func, AgenticProcess.PARAMETER_OPTIONAL_MAP_ANNOTATION, parameter_optional_map)
        setattr(func, AgenticProcess.SIZE_REQUIREMENT_ANNOTATION, size_requirements)

        # --- Part 2: Centralized I/O Extraction using new separated functions ---
        process_inputs = extract_function_process_in_events(func)
        process_outputs = extract_function_process_out_events(func)
        setattr(func, AgenticProcess.PROCESS_INPUTS_ANNOTATION, process_inputs)
        setattr(func, AgenticProcess.PROCESS_OUTPUTS_ANNOTATION, process_outputs)

        # --- Part 3: Standard Metadata ---
        setattr(func, AgenticProcess.STEP_NAME_ANNOTATION, name)
        setattr(func, AgenticProcess.STEP_DESCRIPTION_ANNOTATION, description)
        setattr(func, AgenticProcess.STEP_ICON_ANNOTATION, icon)
        setattr(func, AgenticProcess.SIGNATURE_ANNOTATION, inspect.signature(func))

        return func

    return decorator
