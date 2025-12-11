from .base.HtmlElement import HtmlElement
from .elements.CascadeSelect import CascadeSelect
from .elements.Checkbox import Checkbox
from .elements.ColorPicker import ColorPicker
from .elements.DatePicker import DatePicker
from .elements.Group import Group
from .elements.InputMask import InputMask
from .elements.InputNumber import InputNumber
from .elements.InputOtp import InputOtp
from .elements.InputText import InputText
from .elements.Knob import Knob
from .elements.Listbox import Listbox
from .elements.MultiSelect import MultiSelect
from .elements.Password import Password
from .elements.RadioButton import RadioButton
from .elements.Rating import Rating
from .elements.Select import Select
from .elements.SelectButton import SelectButton
from .elements.Slider import Slider
from .elements.Textarea import Textarea
from .elements.ToggleButton import ToggleButton
from .elements.ToggleSwitch import ToggleSwitch

ALL_FORM_OPTIONS = (
    HtmlElement
    | InputText
    | CascadeSelect
    | Checkbox
    | ColorPicker
    | DatePicker
    | Group
    | InputMask
    | InputNumber
    | InputOtp
    | Knob
    | Listbox
    | MultiSelect
    | Password
    | RadioButton
    | Rating
    | Select
    | SelectButton
    | Slider
    | Textarea
    | ToggleButton
    | ToggleSwitch
)

# Rebuild Group model to resolve forward reference to ALL_FORM_OPTIONS
# Group.children uses ALL_FORM_OPTIONS which creates a circular dependency
Group.model_rebuild()
