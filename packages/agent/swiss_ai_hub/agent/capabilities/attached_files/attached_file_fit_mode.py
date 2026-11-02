from enum import StrEnum


class FitMode(StrEnum):
    """How an attached file's text reached the context block."""

    WHOLE = "whole"
    EXCERPTS = "excerpts"
    BEGINNING = "beginning"
    PAGES = "pages"
    PAGES_CUT = "pages_cut"
