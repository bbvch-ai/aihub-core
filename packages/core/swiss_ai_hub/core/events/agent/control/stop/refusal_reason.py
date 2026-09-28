from enum import StrEnum


class RefusalReason(StrEnum):
    """Why a conversational turn was refused before any answer was attempted."""

    CONDENSATION_EMPTY = "condensation_empty"
    INPUT_TOO_LARGE = "input_too_large"
