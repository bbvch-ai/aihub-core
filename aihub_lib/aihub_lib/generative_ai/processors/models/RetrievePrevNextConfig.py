from typing import Annotated, Self

from pydantic import Field

from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.Select import Select
from aihub_lib.nats.events.form.Form import Form


class RetrievePrevNextConfig(Form):
    """
    Configuration for retrieving previous/next nodes.

    Supports duality pattern for form rendering and data validation.
    """

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
            num_nodes=InputNumber(
                label=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.num_nodes.label"),
                help=LocaleString.from_i18n_path("lib.processor.retrieve_prev_next.num_nodes.help"),
                min=1,
                step=1,
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
            ),
        )
