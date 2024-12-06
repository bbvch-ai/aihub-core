import inspect
from typing import Optional

from lib_core.i18n.LocaleString import LocaleString
from agents_core.workflow.annotations.extractors.extract_function_events import extract_function_events


def step(*,
         max_executions_per_run: int = None,
         stop_on_error: bool = True,
         name: Optional[LocaleString] = None,
         description: Optional[LocaleString] = None):
    def decorator(func):
        input_events, input_event_mapping, parameter_optional_map, size_requirements = extract_function_events(func)
        setattr(func, '_is_step', True)
        setattr(func, '_input_events', input_events)
        setattr(func, '_input_event_mapping', input_event_mapping)
        setattr(func, '_parameter_optional_map', parameter_optional_map)
        setattr(func, '_size_requirements', size_requirements)  # New
        setattr(func, '_max_executions_per_run', max_executions_per_run)
        setattr(func, '_stop_on_error', stop_on_error)
        setattr(func, '_step_name', name)
        setattr(func, '_step_description', description)
        setattr(func, '__signature__', inspect.signature(func))
        return func

    return decorator