from typing import Annotated, Any, Literal, Self

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class CascadeSelect(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/CascadeSelect"""

    formkit: Annotated[Literal["primeCascadeSelect"], Field(description="PrimeVue CascadeSelect element.")] = (
        "primeCascadeSelect"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    options: Annotated[
        list[dict[str, str | LocaleString | Any]], Field(description="Array of hierarchical option objects")
    ]
    option_label: Annotated[
        str | None, Field(description="Property name to use as the label of an option", alias="optionLabel")
    ] = None
    option_value: Annotated[
        str | None, Field(description="Property name to use as the value of an option", alias="optionValue")
    ] = None
    option_group_label: Annotated[
        str | None, Field(description="Property name to use as the label of an option group", alias="optionGroupLabel")
    ] = None
    option_group_children: Annotated[
        list[str] | None,
        Field(description="Property names that define the children of option groups", alias="optionGroupChildren"),
    ] = None
    filter: Annotated[bool, Field(description="Whether to enable filtering")] = False
    multiple: Annotated[bool, Field(description="Whether to allow multiple selections")] = False

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)

        for option in self_copy.options:
            if isinstance(option[self.option_label], LocaleString):
                option[self.option_label] = t.extract(option[self.option_label])

        return self_copy
