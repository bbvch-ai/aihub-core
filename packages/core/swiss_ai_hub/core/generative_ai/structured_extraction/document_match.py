from typing import Annotated, Literal

from pydantic import BaseModel, Field


class DocumentMatch(BaseModel):
    """How a whole document meets the request's document condition.

    A document is judged once, on its start, so its later windows need not be read when it clearly fails.
    """

    verdict: Annotated[
        Literal["yes", "no", "unsure"],
        Field(
            description='"yes" when the excerpt or title shows the document meets the document condition; "no" when '
            "they state a value that differs from one the condition itself asks for, such as another party, currency, "
            "document type or status or a date outside the period, never for something the condition does not ask "
            "about, so a draft fails only a condition that asks for a status, and never when the requested value is "
            'also stated elsewhere; "unsure" only when the excerpt or title does not write the fact out (a fact '
            "inferred from the language, a country, an address, the kind of document or other values is not written), "
            "or when a name differs from the requested one only by a letter or two, as an OCR or typing error would, "
            "and the requested name is stated nowhere else."
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
