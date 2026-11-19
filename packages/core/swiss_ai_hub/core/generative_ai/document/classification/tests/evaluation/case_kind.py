from enum import StrEnum


class CaseKind(StrEnum):
    """Why a case is in the sample, so each measurement counts the cases it is about.

    Invoices alone cannot show precision: a classifier that calls everything an invoice scores 100% on them. Documents
    that resemble invoices measure precision; plainly different documents only show the classifier is not absurd.
    """

    INVOICE = "invoice"
    BOUNDARY_INVOICE = "boundary_invoice"
    HARD_NEGATIVE = "hard_negative"
    EASY_NEGATIVE = "easy_negative"

    @property
    def is_invoice(self) -> bool:
        return self in (CaseKind.INVOICE, CaseKind.BOUNDARY_INVOICE)
