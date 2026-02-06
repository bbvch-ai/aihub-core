from typing import Annotated, Any

from pydantic import Discriminator, Tag

from .base.HtmlElement import HtmlElement
from .elements.AgentSelector import AgentSelector
from .elements.CascadeSelect import CascadeSelect
from .elements.Checkbox import Checkbox
from .elements.ColorPicker import ColorPicker
from .elements.DatePicker import DatePicker
from .elements.Group import Group
from .elements.IconSelector import IconSelector
from .elements.InputMask import InputMask
from .elements.InputNumber import InputNumber
from .elements.InputOtp import InputOtp
from .elements.InputText import InputText
from .elements.Knob import Knob
from .elements.KnowledgeDatabaseSelector import KnowledgeDatabaseSelector
from .elements.Listbox import Listbox
from .elements.LocaleInput import LocaleInput
from .elements.ModelSelect import ModelSelect
from .elements.MultiSelect import MultiSelect
from .elements.Password import Password
from .elements.RadioButton import RadioButton
from .elements.Rating import Rating
from .elements.Repeater import Repeater
from .elements.Select import Select
from .elements.SelectButton import SelectButton
from .elements.Slider import Slider
from .elements.Textarea import Textarea
from .elements.ToggleButton import ToggleButton
from .elements.ToggleSwitch import ToggleSwitch
from .elements.VectorStoreInput import VectorStoreInput

# Mapping from $formkit literal value to element class name for discriminator
_FORMKIT_TYPE_MAP: dict[str, str] = {
    "agentSelector": "AgentSelector",
    "group": "Group",
    "iconSelector": "IconSelector",
    "knowledgeDatabaseSelector": "KnowledgeDatabaseSelector",
    "localeInput": "LocaleInput",
    "modelSelect": "ModelSelect",
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
    """
    Discriminator function for the form element union.

    Determines the correct element type based on:
    - HtmlElement: has $el or el field (no $formkit/formkit)
    - PrimeVueElement subclasses: have $formkit or formkit field with unique literal values

    Note: Pydantic models can serialize using either alias ($formkit) or Python name (formkit)
    depending on configuration, so we check both.
    """
    if isinstance(data, dict):
        # Deserialization from dict (e.g., JSON parsing)
        if "$el" in data or "el" in data:
            return "HtmlElement"
        formkit: str | None = data.get("$formkit") or data.get("formkit")
        if formkit is not None:
            return _FORMKIT_TYPE_MAP.get(formkit, formkit)
        return "HtmlElement"  # Fallback for edge cases
    # Serialization from model instance
    if hasattr(data, "el") and not hasattr(data, "formkit"):
        return "HtmlElement"
    return type(data).__name__


# Define the union with Tag annotations for callable discriminator
# Each Tag value must match what _get_form_element_type returns for that type
_FormElementUnion = (
    Annotated[HtmlElement, Tag("HtmlElement")]
    | Annotated[AgentSelector, Tag("AgentSelector")]
    | Annotated[CascadeSelect, Tag("CascadeSelect")]
    | Annotated[Checkbox, Tag("Checkbox")]
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

# Rebuild models to resolve forward reference to ALL_FORM_OPTIONS
# Group.children and Repeater.children use ALL_FORM_OPTIONS which creates a circular dependency
Group.model_rebuild()
Repeater.model_rebuild()
