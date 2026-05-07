from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.processors.vector_prev_next_post_processor import ModeOptions
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RetrievePrevNextConfig(Form):
    """
    Configuration for retrieving previous/next nodes.

    Supports duality pattern for form rendering and data validation.
    """

    enabled: Annotated[
        bool | Checkbox,
        Field(description="Run the previous/next post-processor on retrieved nodes."),
    ] = True
    num_nodes: Annotated[
        int | InputNumber,
        Field(description="The number of previous and next nodes to retrieve."),
    ] = 10
    mode: Annotated[
        ModeOptions | Select,
        Field(description="The mode for the post-processor, can be 'previous', 'next', or 'both'."),
    ] = ModeOptions.BOTH

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RetrievePrevNextConfig."""
        return cls(
            enabled=Checkbox(
                label=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.enabled.label"),
                help=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.enabled.help"),
                ref="retrieve_prev_next_enabled",
            ),
            num_nodes=InputNumber(
                label=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.num_nodes.label"),
                help=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.num_nodes.help"),
                min=1,
                step=1,
                condition_if="$get(retrieve_prev_next_enabled).value",
            ),
            mode=Select(
                label=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.mode.label"),
                help=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.mode.help"),
                options=[
                    {"label": "Previous", "value": ModeOptions.PREVIOUS.value},
                    {"label": "Next", "value": ModeOptions.NEXT.value},
                    {"label": "Both", "value": ModeOptions.BOTH.value},
                ],
                option_label="label",
                option_value="value",
                condition_if="$get(retrieve_prev_next_enabled).value",
            ),
        )
