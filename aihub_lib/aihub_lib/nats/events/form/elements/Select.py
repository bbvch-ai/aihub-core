from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Select(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Select"""

    formkit: Annotated[Literal["primeSelect"], Field(description="PrimeVue Select element.")] = "primeSelect"

    options: Annotated[
        list[str | LocaleString | dict[str, str | LocaleString]] | list[str],
        Field(description="Array of selectable options (objects or strings). Use this OR options_api_mode."),
    ] = []
    options_api_mode: Annotated[
        str | None,
        Field(
            description="When set, options are fetched from /api/v1/models/mode/{mode}. "
            "Valid modes: chat, embedding, rerank, image_generation, audio_transcription, audio_speech",
            alias="optionsApiMode",
        ),
    ] = None
    option_label: Annotated[
        str | None, Field(description="Property name to use as the label of an option", alias="optionLabel")
    ] = None
    option_value: Annotated[
        str | None, Field(description="Property name to use as the value of an option", alias="optionValue")
    ] = None

    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    show_clear: Annotated[bool, Field(description="Whether to show clear button", alias="showClear")] = False
    filter: Annotated[bool, Field(description="Whether to enable filtering")] = False

    def in_locale(self, t: LocaleHandler) -> "Select":
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        for option in self_copy.options:
            if isinstance(option, str):
                continue
            if isinstance(option, LocaleString):
                option = t.extract(option)
            if isinstance(option[self.option_label], LocaleString):
                option[self.option_label] = t.extract(option[self.option_label])
        return self_copy
