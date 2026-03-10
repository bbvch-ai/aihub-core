from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.form.elements.Checkbox import Checkbox
from swiss_ai_hub.core.nats.events.form.elements.LocaleInput import LocaleInput
from swiss_ai_hub.core.nats.events.form.Form import Form


class FewShotGuardExample(Form):
    """
    A single few-shot guard example for defining accepted/rejected user requests.

    Supports duality pattern for form rendering and data validation.
    """

    user: Annotated[
        LocaleString | LocaleInput,
        Field(description="Example user request/message."),
    ]
    success: Annotated[
        bool | Checkbox,
        Field(description="Whether this example should be accepted (true) or rejected (false)."),
    ]
    reason: Annotated[
        LocaleString | LocaleInput,
        Field(description="Explanation of why the request is accepted or rejected.", title="Reason"),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode FewShotGuardExample."""
        return cls(
            user=LocaleInput(
                label=LocaleString.from_i18n_path("lib.guards.few_shot_example.user.label"),
                help=LocaleString.from_i18n_path("lib.guards.few_shot_example.user.help"),
                input_type="textarea",
            ),
            success=Checkbox(
                label=LocaleString.from_i18n_path("lib.guards.few_shot_example.success.label"),
                help=LocaleString.from_i18n_path("lib.guards.few_shot_example.success.help"),
            ),
            reason=LocaleInput(
                label=LocaleString.from_i18n_path("lib.guards.few_shot_example.reason.label"),
                help=LocaleString.from_i18n_path("lib.guards.few_shot_example.reason.help"),
                input_type="textarea",
            ),
        )
