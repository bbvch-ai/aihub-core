import inspect
from typing import Annotated, Optional

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.workflow.annotations.extractors.extract_function_events import extract_function_events

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.process.annotations.extractors.extract_function_process_in_events import (
    extract_function_process_in_events,
)
from aihub_process.process.annotations.extractors.extract_function_process_out_events import (
    extract_function_process_out_events,
)


def process_step(
    *,
    name: Annotated[Optional[LocaleString], "A localized name for the step"] = None,
    icon: Annotated[Optional[str], "An icon name for the step"] = None,
    description: Annotated[Optional[LocaleString], "A localized description of what the step does"] = None,
):
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
        setattr(
            func, AgenticProcess.STEP_NAME_ANNOTATION, name or LocaleString(en=func.__name__.replace("_", " ").title())
        )
        setattr(func, AgenticProcess.STEP_DESCRIPTION_ANNOTATION, description)
        setattr(func, AgenticProcess.STEP_ICON_ANNOTATION, icon)
        setattr(func, AgenticProcess.SIGNATURE_ANNOTATION, inspect.signature(func))

        return func

    return decorator
