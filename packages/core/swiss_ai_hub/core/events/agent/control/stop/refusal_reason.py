from enum import StrEnum


class RefusalReason(StrEnum):
    """Why a conversational turn was refused before any answer was attempted."""

    CONDENSATION_EMPTY = "condensation_empty"
    IMAGES_NOT_ACCEPTED = "images_not_accepted"
    INPUT_TOO_LARGE = "input_too_large"
    OUT_OF_SCOPE = "out_of_scope"
    TOO_MANY_IMAGES = "too_many_images"
