from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class CronInput(PrimeVueElement):
    """
    A FormKit element for editing the cron schedule of a schedulable agent profile.

    The element renders the five cron positions plus a timezone selector, and the submitted value
    matches the fields of `CronSchedule`:
    {
        "minute": str,
        "hour": str,
        "day_of_month": str,
        "month": str,
        "day_of_week": str,
        "timezone": str,
    }

    Presets and the plain-language summary of the current schedule are delivered by the Admin UI
    (see the cron schedule configuration UI issue); this element only declares the contract.

    ### Form Duality
    ```python
    from swiss_ai_hub.core.form.elements.cron_input import CronInput
    from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule

    class MyAgentConfig(AgentConfig):
        schedule: Annotated[
            CronSchedule | CronInput | None,
            Field(description="When this profile runs automatically"),
        ] = None

    # Form mode - for rendering:
    config = MyAgentConfig(schedule=CronInput(label=LocaleString(en="Schedule")))

    # Data mode - from submission (Pydantic validates into CronSchedule):
    config = MyAgentConfig(schedule=CronSchedule(hour="12", timezone="Europe/Zurich"))
    ```
    """

    formkit: Annotated[Literal["cronInput"], Field(description="Cron schedule input element.")] = "cronInput"

    timezone_placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder for the timezone select", alias="timezonePlaceholder"),
    ] = None
    filter: Annotated[bool, Field(description="Whether to enable filtering/search on the timezone select")] = True

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.timezone_placeholder, LocaleString):
            self_copy.timezone_placeholder = t.extract(self_copy.timezone_placeholder)
        return self_copy
