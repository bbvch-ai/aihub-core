from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
    from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
    from swiss_ai_hub.core.form import CascadeSelect
    from swiss_ai_hub.core.form import Checkbox
    from swiss_ai_hub.core.form import DatePicker
    from swiss_ai_hub.core.form.form import Form
    from swiss_ai_hub.core.form import InputNumber
    from swiss_ai_hub.core.form import InputText
    from swiss_ai_hub.core.form import Select
    from swiss_ai_hub.core.form import SelectButton
    from swiss_ai_hub.core.form import Slider
    from swiss_ai_hub.core.form.template_data import TemplateData
    from swiss_ai_hub.core.form import Textarea
    from swiss_ai_hub.core.form.normalization import normalize_empty_locale_strings
    from swiss_ai_hub.core.form.normalization import normalize_empty_objects_to_none
    from swiss_ai_hub.core.form.normalization import transform_formkit_arrays

__all__ = [
    "ALL_FORM_OPTIONS",
    "AgentSelector",
    "CascadeSelect",
    "Checkbox",
    "DatePicker",
    "Form",
    "InputNumber",
    "InputText",
    "Select",
    "SelectButton",
    "Slider",
    "TemplateData",
    "Textarea",
    "normalize_empty_locale_strings",
    "normalize_empty_objects_to_none",
    "transform_formkit_arrays",
]

_LAZY_IMPORTS = {
    "ALL_FORM_OPTIONS": "swiss_ai_hub.core.form",
    "AgentSelector": "swiss_ai_hub.core.form.elements.agent_selector",
    "CascadeSelect": "swiss_ai_hub.core.form",
    "Checkbox": "swiss_ai_hub.core.form",
    "DatePicker": "swiss_ai_hub.core.form",
    "Form": "swiss_ai_hub.core.form.form",
    "InputNumber": "swiss_ai_hub.core.form",
    "InputText": "swiss_ai_hub.core.form",
    "Select": "swiss_ai_hub.core.form",
    "SelectButton": "swiss_ai_hub.core.form",
    "Slider": "swiss_ai_hub.core.form",
    "TemplateData": "swiss_ai_hub.core.form.template_data",
    "Textarea": "swiss_ai_hub.core.form",
    "normalize_empty_locale_strings": "swiss_ai_hub.core.form.normalization",
    "normalize_empty_objects_to_none": "swiss_ai_hub.core.form.normalization",
    "transform_formkit_arrays": "swiss_ai_hub.core.form.normalization",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
