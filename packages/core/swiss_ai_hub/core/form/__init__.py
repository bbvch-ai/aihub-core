from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
    from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
    from swiss_ai_hub.core.form.elements.cascade_select import CascadeSelect
    from swiss_ai_hub.core.form.elements.checkbox import Checkbox
    from swiss_ai_hub.core.form.elements.date_picker import DatePicker
    from swiss_ai_hub.core.form.elements.input_number import InputNumber
    from swiss_ai_hub.core.form.elements.input_text import InputText
    from swiss_ai_hub.core.form.elements.knowledge_database_selector import KnowledgeDatabaseSelector
    from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
    from swiss_ai_hub.core.form.elements.select import Select
    from swiss_ai_hub.core.form.elements.select_button import SelectButton
    from swiss_ai_hub.core.form.elements.slider import Slider
    from swiss_ai_hub.core.form.elements.textarea import Textarea
    from swiss_ai_hub.core.form.form import Form
    from swiss_ai_hub.core.form.normalization import (
        normalize_empty_locale_strings,
        normalize_empty_objects_to_none,
        transform_formkit_arrays,
    )
    from swiss_ai_hub.core.form.template_data import TemplateData

__all__ = [
    "ALL_FORM_OPTIONS",
    "AgentSelector",
    "CascadeSelect",
    "Checkbox",
    "DatePicker",
    "Form",
    "InputNumber",
    "InputText",
    "KnowledgeDatabaseSelector",
    "LocaleInput",
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
    "ALL_FORM_OPTIONS": "swiss_ai_hub.core.form.all_form_options",
    "AgentSelector": "swiss_ai_hub.core.form.elements.agent_selector",
    "CascadeSelect": "swiss_ai_hub.core.form.elements.cascade_select",
    "Checkbox": "swiss_ai_hub.core.form.elements.checkbox",
    "DatePicker": "swiss_ai_hub.core.form.elements.date_picker",
    "Form": "swiss_ai_hub.core.form.form",
    "InputNumber": "swiss_ai_hub.core.form.elements.input_number",
    "InputText": "swiss_ai_hub.core.form.elements.input_text",
    "KnowledgeDatabaseSelector": "swiss_ai_hub.core.form.elements.knowledge_database_selector",
    "LocaleInput": "swiss_ai_hub.core.form.elements.locale_input",
    "Select": "swiss_ai_hub.core.form.elements.select",
    "SelectButton": "swiss_ai_hub.core.form.elements.select_button",
    "Slider": "swiss_ai_hub.core.form.elements.slider",
    "TemplateData": "swiss_ai_hub.core.form.template_data",
    "Textarea": "swiss_ai_hub.core.form.elements.textarea",
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
