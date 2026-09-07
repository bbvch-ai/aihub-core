from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
    from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement
    from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
    from swiss_ai_hub.core.form.elements.cascade_select import CascadeSelect
    from swiss_ai_hub.core.form.elements.checkbox import Checkbox
    from swiss_ai_hub.core.form.elements.chips_input import ChipsInput
    from swiss_ai_hub.core.form.elements.cron_input import CronInput
    from swiss_ai_hub.core.form.elements.date_picker import DatePicker
    from swiss_ai_hub.core.form.elements.group import Group
    from swiss_ai_hub.core.form.elements.input_number import InputNumber
    from swiss_ai_hub.core.form.elements.input_text import InputText
    from swiss_ai_hub.core.form.elements.knowledge_database_selector import KnowledgeDatabaseSelector
    from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
    from swiss_ai_hub.core.form.elements.model_select import ModelSelect
    from swiss_ai_hub.core.form.elements.repeater import Repeater
    from swiss_ai_hub.core.form.elements.select import Select
    from swiss_ai_hub.core.form.elements.select_button import SelectButton
    from swiss_ai_hub.core.form.elements.slider import Slider
    from swiss_ai_hub.core.form.elements.tenant_select import TenantSelect
    from swiss_ai_hub.core.form.elements.textarea import Textarea
    from swiss_ai_hub.core.form.elements.vector_store_input import VectorStoreInput
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
    "CronInput",
    "ChipsInput",
    "ConfigAuthorizationViolation",
    "DatePicker",
    "Form",
    "FormkitElement",
    "Group",
    "InputNumber",
    "InputText",
    "KnowledgeDatabaseSelector",
    "LocaleInput",
    "ModelSelect",
    "Repeater",
    "Select",
    "SelectButton",
    "Slider",
    "TemplateData",
    "TenantSelect",
    "VectorStoreInput",
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
    "CronInput": "swiss_ai_hub.core.form.elements.cron_input",
    "ChipsInput": "swiss_ai_hub.core.form.elements.chips_input",
    "ConfigAuthorizationViolation": "swiss_ai_hub.core.form.base.config_authorization_violation",
    "DatePicker": "swiss_ai_hub.core.form.elements.date_picker",
    "Form": "swiss_ai_hub.core.form.form",
    "FormkitElement": "swiss_ai_hub.core.form.base.formkit_element",
    "Group": "swiss_ai_hub.core.form.elements.group",
    "InputNumber": "swiss_ai_hub.core.form.elements.input_number",
    "InputText": "swiss_ai_hub.core.form.elements.input_text",
    "KnowledgeDatabaseSelector": "swiss_ai_hub.core.form.elements.knowledge_database_selector",
    "LocaleInput": "swiss_ai_hub.core.form.elements.locale_input",
    "ModelSelect": "swiss_ai_hub.core.form.elements.model_select",
    "Repeater": "swiss_ai_hub.core.form.elements.repeater",
    "Select": "swiss_ai_hub.core.form.elements.select",
    "SelectButton": "swiss_ai_hub.core.form.elements.select_button",
    "Slider": "swiss_ai_hub.core.form.elements.slider",
    "TemplateData": "swiss_ai_hub.core.form.template_data",
    "TenantSelect": "swiss_ai_hub.core.form.elements.tenant_select",
    "VectorStoreInput": "swiss_ai_hub.core.form.elements.vector_store_input",
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
