from enum import StrEnum


class AttributeValueType(StrEnum):
    """How an attribute's text is read into its stored form, and which metadata keys it occupies."""

    DATE = "date"
    PERIOD = "period"
    TEXT = "text"
    TEXT_LIST = "text_list"
    AMOUNT = "amount"
    CURRENCY = "currency"
    TAX_ID = "tax_id"
