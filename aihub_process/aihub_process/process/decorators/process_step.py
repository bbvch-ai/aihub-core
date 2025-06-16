import inspect
from typing import Annotated, Optional

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.workflow.annotations.extractors.extract_function_events import extract_function_events

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
        setattr(func, "_is_process_step", True)
        setattr(func, "_input_events", input_events)
        setattr(func, "_output_events", output_events)
        setattr(func, "_input_event_mapping", input_event_mapping)
        setattr(func, "_parameter_optional_map", parameter_optional_map)
        setattr(func, "_size_requirements", size_requirements)

        # --- Part 2: Centralized I/O Extraction using new separated functions ---
        process_inputs = extract_function_process_in_events(func)
        process_outputs = extract_function_process_out_events(func)

        setattr(func, "_process_inputs", process_inputs)
        setattr(func, "_process_outputs", process_outputs)

        # --- Part 3: Standard Metadata ---
        setattr(func, "_step_name", name or LocaleString(en=func.__name__.replace("_", " ").title()))
        setattr(func, "_step_description", description)
        setattr(func, "_step_icon", icon)
        setattr(func, "__signature__", inspect.signature(func))
        setattr(func, "_python_method_name", func.__name__)

        return func

    return decorator
