from typing import Annotated, Literal, Self

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement

# Default icon options for common use cases
DEFAULT_ICON_OPTIONS = [
    "mage:robot-fill",
    "mage:email-fill",
    "mage:message-fill",
    "mage:calculator-fill",
    "mage:chart-fill",
    "mage:chart-up-fill",
    "mage:calendar-fill",
    "mage:clipboard-fill",
    "mage:checklist-note-fill",
    "mage:search-fill",
    "mage:book-fill",
    "mage:globe-fill",
    "mage:earth-fill",
    "mage:pen-fill",
    "mage:edit-fill",
    "mage:file-fill",
    "mage:folder-fill",
    "mage:briefcase-fill",
    "mage:users-fill",
    "mage:user-fill",
    "mage:dollar-fill",
    "mage:credit-card-fill",
    "mage:megaphone-a-fill",
    "mage:shopping-cart-fill",
    "mage:phone-fill",
    "mage:clock-fill",
    "mage:database-fill",
    "mage:server-fill",
    "mage:settings-fill",
    "mage:security-shield-fill",
    "mage:bolt-fill",
    "mage:zap-fill",
    "mage:light-bulb-fill",
    "mage:star-fill",
    "mage:bookmark-fill",
    "mage:inbox-fill",
    "mage:archive-fill",
    "mage:share-fill",
    "mage:printer-fill",
    "mage:image-fill",
    "mage:video-fill",
    "mage:microphone-fill",
    "mage:location-fill",
    "mage:home-fill",
    "mage:building-a-fill",
    "mage:id-card-fill",
    "mage:key-fill",
    "mage:compass-fill",
    "mage:rocket-fill",
    "mage:goals-fill",
]


class IconSelector(PrimeVueElement):
    """
    A FormKit element for selecting or entering an Iconify icon name.

    This element renders as an editable select with icon preview capability.
    Users can either select from preset icon options or enter any valid Iconify icon name.
    The selected/entered icon is displayed live in the input field.

    ### Features
    - Dropdown with preset icon options (each showing the icon preview)
    - Editable input for entering custom Iconify icon names
    - Live icon preview in the input field
    - Supports any valid Iconify icon (e.g., 'lucide:bot', 'meteor-icons:robot')

    ### Example Usage
    ```python
    class MyAgentConfig(AgentConfig):
        icon: Annotated[
            str | IconSelector,
            Field(description="Icon for the agent"),
        ]

    # Form mode - for rendering:
    config = MyAgentConfig(
        ...,
        icon=IconSelector(label=LocaleString(en="Icon", de="Symbol")),
    )

    # Data mode - from submission:
    config = MyAgentConfig(
        ...,
        icon="mage:robot",
    )
    ```
    """

    formkit: Annotated[Literal["iconSelector"], Field(description="Icon selector element.")] = "iconSelector"

    options: Annotated[
        list[str],
        Field(description="List of preset icon options to choose from"),
    ] = list(DEFAULT_ICON_OPTIONS)

    placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder text when no icon is selected"),
    ] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy
