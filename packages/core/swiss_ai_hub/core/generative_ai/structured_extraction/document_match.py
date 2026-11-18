from typing import Annotated, Literal

from pydantic import BaseModel, Field


class DocumentMatch(BaseModel):
    """How a whole document meets the request's document condition.

    A document is judged once, on its start, so its later windows need not be read when it clearly fails.
    """

    verdict: Annotated[
        Literal["yes", "no", "unsure"],
        Field(
            description='"yes" when the excerpt or title shows the document meets the document condition; "no" only '
            'when they state a fact that contradicts it; "unsure" otherwise, including when the fact is not in the '
            "excerpt."
        ),
    ]
    reason: Annotated[
        str,
        Field(
            description="One short sentence naming or quoting the fact that decided it, e.g. 'Supplier: Initech AG'."
        ),
    ]

    @property
    def fails(self) -> bool:
        return self.verdict == "no"

    @property
    def unsure(self) -> bool:
        return self.verdict == "unsure"
