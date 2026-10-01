from enum import StrEnum


class FitMode(StrEnum):
    """How an attached file's text reached the context block."""

    WHOLE = "whole"
    EXCERPTS = "excerpts"
    BEGINNING = "beginning"
