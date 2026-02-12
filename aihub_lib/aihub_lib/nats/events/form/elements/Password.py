from typing import Annotated, Literal, Self

from pydantic import Field, computed_field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Password(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Password"""

    formkit: Annotated[Literal["primePassword"], Field(description="PrimeVue Password element.")] = "primePassword"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    feedback: Annotated[bool, Field(description="Whether to show password strength feedback")] = False
    toggle_mask: Annotated[
        bool, Field(description="Whether to show toggle button to reveal/hide password", alias="toggleMask")
    ] = False
    medium_regex: Annotated[
        str | None, Field(description="Regex pattern for medium strength validation", alias="mediumRegex")
    ] = None
    strong_regex: Annotated[
        str | None, Field(description="Regex pattern for strong strength validation", alias="strongRegex")
    ] = None
    prompt_label: Annotated[
        LocaleString | str | None, Field(description="Label for password prompt", alias="promptLabel")
    ] = None
    weak_label: Annotated[
        LocaleString | str | None, Field(description="Label for weak password strength", alias="weakLabel")
    ] = None
    medium_label: Annotated[
        LocaleString | str | None, Field(description="Label for medium password strength", alias="mediumLabel")
    ] = None
    strong_label: Annotated[
        LocaleString | str | None, Field(description="Label for strong password strength", alias="strongLabel")
    ] = None

    @computed_field
    @property
    def validation(self) -> str:
        validation_rules = []
        base_validation = super().validation
        if base_validation:
            validation_rules.append(base_validation)

        validation_rules.append("length:8,")

        if self.strong_regex:
            validation_rules.append(f"matches:/{self.strong_regex}/")
        elif self.medium_regex:
            validation_rules.append(f"matches:/{self.medium_regex}/")

        return "|".join(validation_rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        if isinstance(self_copy.prompt_label, LocaleString):
            self_copy.prompt_label = t.extract(self_copy.prompt_label)
        if isinstance(self_copy.weak_label, LocaleString):
            self_copy.weak_label = t.extract(self_copy.weak_label)
        if isinstance(self_copy.medium_label, LocaleString):
            self_copy.medium_label = t.extract(self_copy.medium_label)
        if isinstance(self_copy.strong_label, LocaleString):
            self_copy.strong_label = t.extract(self_copy.strong_label)
        return self_copy
