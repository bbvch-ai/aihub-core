import inspect
from typing import Annotated, Optional

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity


def extract_process_step_io(func):
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    input_work_type = None
    if len(params) > 1: # First param is 'self'
        input_work_type = params[1].annotation

    output_work_request_type = sig.return_annotation
    return input_work_type, output_work_request_type


def process_step(
    *,
    input_from: BaseProcessEntity.In,
    delegate_to: BaseProcessEntity.Out,
    name: Annotated[Optional[LocaleString], "A localized name for the step"] = None,
    icon: Annotated[Optional[str], "An icon name for the step"] = None,
    description: Annotated[Optional[LocaleString], "A localized description of what the step does"] = None,
):
    def decorator(func):
        input_work_type, output_work_request_type = extract_process_step_io(func)

        setattr(func, "_is_process_step", True)
        setattr(func, "_input_from_config", input_from)
        setattr(func, "_delegate_to_config", delegate_to)
        setattr(func, "_input_work_type", input_work_type) # Store the Pydantic type for input
        setattr(func, "_output_work_request_type", output_work_request_type) # Store the Pydantic type for output

        # UI/Metadata attributes
        setattr(func, "_step_name", name or LocaleString(en=func.__name__.replace("_", " ").title()))
        setattr(func, "_step_description", description)
        setattr(func, "_step_icon", icon)
        setattr(func, "__signature__", inspect.signature(func)) # Keep for reflection

        # Link to the Python method name
        setattr(func, "_python_method_name", func.__name__)
        return func
    return decorator