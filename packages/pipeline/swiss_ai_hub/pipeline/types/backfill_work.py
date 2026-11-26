from enum import StrEnum


class BackfillWork(StrEnum):
    """What a classification backfill owes one document, decided from the versions it was classified with."""

    CLASSIFY = "classify"
    RENORMALIZE = "renormalize"
    UP_TO_DATE = "up_to_date"
    SYNCED_RECORD = "synced_record"
