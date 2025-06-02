from typing import Annotated, Optional

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_process.process.decorators.process_step import process_step
from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity


def process_start(
    *,
    input_from: BaseProcessEntity.In,
    delegate_to: BaseProcessEntity.Out,
    name: Annotated[Optional[LocaleString], "A localized name for the step"] = None,
    icon: Annotated[Optional[str], "An icon name for the step"] = None,
    description: Annotated[Optional[LocaleString], "A localized description of what the step does"] = None,
):
    def decorator(func):
        step_decorator = process_step(
            input_from=input_from,
            delegate_to=delegate_to,
            name=name,
            icon=icon,
            description=description
        )
        decorated_func = step_decorator(func) # Call the decorator to set attributes

        setattr(decorated_func, "_is_process_start", True)
        return decorated_func
    return decorator