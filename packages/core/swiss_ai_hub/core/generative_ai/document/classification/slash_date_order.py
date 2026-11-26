from enum import StrEnum


class SlashDateOrder(StrEnum):
    """The order a document writes slash dates in, for the ones both orders allow (`05/11/2026`).

    Decided per document by `DocumentValueNormalizer`, never per date: from the document's own unambiguous slash dates
    (`17/11` or `11/17`), else from its currency.
    """

    DAY_FIRST = "day_first"
    MONTH_FIRST = "month_first"
