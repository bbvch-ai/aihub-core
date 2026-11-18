from enum import StrEnum


class AttributeOutcome(StrEnum):
    """How one stored attribute compares with its label.

    WRONG and GUESSED are the costly ones: a filter silently drops a correct document on them. EMPTY and
    NOT_UNDERSTOOD only cost a read, since a filter keeps unknown values; NOT_UNDERSTOOD also names a format to add.
    """

    CORRECT = "correct"
    WRONG = "wrong"
    GUESSED = "guessed"
    EMPTY = "empty"
    NOT_UNDERSTOOD = "not_understood"
