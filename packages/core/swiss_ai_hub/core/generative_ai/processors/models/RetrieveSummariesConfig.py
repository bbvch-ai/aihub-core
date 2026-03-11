from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.InputNumber import InputNumber
from swiss_ai_hub.core.form.Form import Form
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class RetrieveSummariesConfig(Form):
    """
    Configuration for retrieving parent summary nodes.

    Supports duality pattern for form rendering and data validation.
    """

    max_parent_levels: Annotated[
        int | InputNumber,
        Field(description="Maximum number of parent levels to retrieve summaries from."),
    ] = 2

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RetrieveSummariesConfig."""
        return cls(
            max_parent_levels=InputNumber(
                label=LocaleString.from_i18n_path("lib.processor.retrieve_summaries.max_parent_levels.label"),
                help=LocaleString.from_i18n_path("lib.processor.retrieve_summaries.max_parent_levels.help"),
                min=1,
                step=1,
            ),
        )
