from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.workflow.annotations.custom_types.list_of_size import FixedList, ListOfSize
    from swiss_ai_hub.core.workflow.annotations.extractors.extract_event_classes import extract_event_classes
    from swiss_ai_hub.core.workflow.annotations.extractors.extract_function_events import extract_function_events
    from swiss_ai_hub.core.workflow.annotations.extractors.extract_return_events import extract_return_events
    from swiss_ai_hub.core.workflow.dispatchable_workflow import DispatchableWorkflow
    from swiss_ai_hub.core.workflow.visualizers.workflow_visualizer import WorkflowVisualizer

__all__ = [
    "FixedList",
    "DispatchableWorkflow",
    "ListOfSize",
    "WorkflowVisualizer",
    "extract_event_classes",
    "extract_function_events",
    "extract_return_events",
]

_LAZY_IMPORTS: dict[str, str] = {
    "FixedList": "swiss_ai_hub.core.workflow.annotations.custom_types.list_of_size",
    "DispatchableWorkflow": "swiss_ai_hub.core.workflow.dispatchable_workflow",
    "ListOfSize": "swiss_ai_hub.core.workflow.annotations.custom_types.list_of_size",
    "WorkflowVisualizer": "swiss_ai_hub.core.workflow.visualizers.workflow_visualizer",
    "extract_event_classes": "swiss_ai_hub.core.workflow.annotations.extractors.extract_event_classes",
    "extract_function_events": "swiss_ai_hub.core.workflow.annotations.extractors.extract_function_events",
    "extract_return_events": "swiss_ai_hub.core.workflow.annotations.extractors.extract_return_events",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
