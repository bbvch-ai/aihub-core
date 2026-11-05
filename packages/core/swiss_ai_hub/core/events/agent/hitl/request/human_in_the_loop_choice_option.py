from typing import Annotated

from pydantic import BaseModel, Field

OPTION_LABEL_LENGTH = 80
OPTION_DESCRIPTION_LENGTH = 240


class HumanInTheLoopChoiceOption(BaseModel):
    """One answer a choice question offers; lengths are capped as OpenWebUI's dialog caps them."""

    label: Annotated[str, Field(min_length=1, max_length=OPTION_LABEL_LENGTH, description="The answer's short label.")]
    description: Annotated[
        str,
        Field(min_length=1, max_length=OPTION_DESCRIPTION_LENGTH, description="What choosing the answer means."),
    ]
