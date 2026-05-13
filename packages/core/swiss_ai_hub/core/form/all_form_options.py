from typing import Annotated, Any

from pydantic import Discriminator, Tag

from swiss_ai_hub.core.form.base.html_element import HtmlElement
from swiss_ai_hub.core.form.elements.agent_selector import AgentSelector
from swiss_ai_hub.core.form.elements.cascade_select import CascadeSelect
from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.chips_input import ChipsInput
from swiss_ai_hub.core.form.elements.color_picker import ColorPicker
from swiss_ai_hub.core.form.elements.date_picker import DatePicker
from swiss_ai_hub.core.form.elements.group import Group
from swiss_ai_hub.core.form.elements.icon_selector import IconSelector
from swiss_ai_hub.core.form.elements.input_mask import InputMask
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_otp import InputOtp
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.knob import Knob
from swiss_ai_hub.core.form.elements.knowledge_database_selector import KnowledgeDatabaseSelector
from swiss_ai_hub.core.form.elements.listbox import Listbox
from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.multi_select import MultiSelect
from swiss_ai_hub.core.form.elements.org_memory_tenant_input import OrgMemoryTenantInput
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.radio_button import RadioButton
from swiss_ai_hub.core.form.elements.rating import Rating
from swiss_ai_hub.core.form.elements.repeater import Repeater
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.elements.select_button import SelectButton
from swiss_ai_hub.core.form.elements.slider import Slider
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.form.elements.toggle_button import ToggleButton
from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.form.elements.vector_store_input import VectorStoreInput

_FORMKIT_TYPE_MAP: dict[str, str] = {
    "agentSelector": "AgentSelector",
    "chipsInput": "ChipsInput",
    "group": "Group",
    "iconSelector": "IconSelector",
    "knowledgeDatabaseSelector": "KnowledgeDatabaseSelector",
    "localeInput": "LocaleInput",
    "modelSelect": "ModelSelect",
    "orgMemoryTenantInput": "OrgMemoryTenantInput",
    "primeCascadeSelect": "CascadeSelect",
    "primeCheckbox": "Checkbox",
    "primeColorPicker": "ColorPicker",
    "primeDatePicker": "DatePicker",
    "primeInputMask": "InputMask",
    "primeInputNumber": "InputNumber",
    "primeInputOtp": "InputOtp",
    "primeInputText": "InputText",
    "primeKnob": "Knob",
    "primeListbox": "Listbox",
    "primeMultiSelect": "MultiSelect",
    "primePassword": "Password",
    "primeRadioButton": "RadioButton",
    "primeRating": "Rating",
    "primeSelect": "Select",
    "primeSelectButton": "SelectButton",
    "primeSlider": "Slider",
    "primeTextarea": "Textarea",
    "primeToggleButton": "ToggleButton",
    "primeToggleSwitch": "ToggleSwitch",
    "repeater": "Repeater",
    "vectorStoreInput": "VectorStoreInput",
}


def _get_form_element_type(data: Any) -> str:
    """Discriminator function for the form element union."""
    if isinstance(data, dict):
        if "$el" in data or "el" in data:
            return "HtmlElement"
        formkit: str | None = data.get("$formkit") or data.get("formkit")
        if formkit is not None:
            return _FORMKIT_TYPE_MAP.get(formkit, formkit)
        return "HtmlElement"
    if hasattr(data, "el") and not hasattr(data, "formkit"):
        return "HtmlElement"
    return type(data).__name__


_FormElementUnion = (
    Annotated[HtmlElement, Tag("HtmlElement")]
    | Annotated[AgentSelector, Tag("AgentSelector")]
    | Annotated[CascadeSelect, Tag("CascadeSelect")]
    | Annotated[Checkbox, Tag("Checkbox")]
    | Annotated[ChipsInput, Tag("ChipsInput")]
    | Annotated[ColorPicker, Tag("ColorPicker")]
    | Annotated[DatePicker, Tag("DatePicker")]
    | Annotated[Group, Tag("Group")]
    | Annotated[IconSelector, Tag("IconSelector")]
    | Annotated[InputMask, Tag("InputMask")]
    | Annotated[InputNumber, Tag("InputNumber")]
    | Annotated[InputOtp, Tag("InputOtp")]
    | Annotated[InputText, Tag("InputText")]
    | Annotated[KnowledgeDatabaseSelector, Tag("KnowledgeDatabaseSelector")]
    | Annotated[Knob, Tag("Knob")]
    | Annotated[Listbox, Tag("Listbox")]
    | Annotated[LocaleInput, Tag("LocaleInput")]
    | Annotated[ModelSelect, Tag("ModelSelect")]
    | Annotated[MultiSelect, Tag("MultiSelect")]
    | Annotated[OrgMemoryTenantInput, Tag("OrgMemoryTenantInput")]
    | Annotated[Password, Tag("Password")]
    | Annotated[RadioButton, Tag("RadioButton")]
    | Annotated[Rating, Tag("Rating")]
    | Annotated[Repeater, Tag("Repeater")]
    | Annotated[Select, Tag("Select")]
    | Annotated[SelectButton, Tag("SelectButton")]
    | Annotated[Slider, Tag("Slider")]
    | Annotated[Textarea, Tag("Textarea")]
    | Annotated[ToggleButton, Tag("ToggleButton")]
    | Annotated[ToggleSwitch, Tag("ToggleSwitch")]
    | Annotated[VectorStoreInput, Tag("VectorStoreInput")]
)

ALL_FORM_OPTIONS = Annotated[_FormElementUnion, Discriminator(_get_form_element_type)]

Group.model_rebuild()
Repeater.model_rebuild()
