from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.incident.incident_context import IncidentContext
    from swiss_ai_hub.core.incident.incident_settings import IncidentSettings
    from swiss_ai_hub.core.incident.issue_form import IssueForm
    from swiss_ai_hub.core.incident.issue_form_field import IssueFormField
    from swiss_ai_hub.core.incident.issue_form_parser import DEFAULT_FORM_PATH, IssueFormParser

__all__ = [
    "DEFAULT_FORM_PATH",
    "IncidentContext",
    "IncidentSettings",
    "IssueForm",
    "IssueFormField",
    "IssueFormParser",
]

_LAZY_IMPORTS = {
    "DEFAULT_FORM_PATH": "swiss_ai_hub.core.incident.issue_form_parser",
    "IncidentContext": "swiss_ai_hub.core.incident.incident_context",
    "IncidentSettings": "swiss_ai_hub.core.incident.incident_settings",
    "IssueForm": "swiss_ai_hub.core.incident.issue_form",
    "IssueFormField": "swiss_ai_hub.core.incident.issue_form_field",
    "IssueFormParser": "swiss_ai_hub.core.incident.issue_form_parser",
}


def __getattr__(name: str) -> object:
    module_path = _LAZY_IMPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    return getattr(import_module(module_path), name)
