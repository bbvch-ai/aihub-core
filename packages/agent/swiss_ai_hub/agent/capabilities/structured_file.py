import posixpath
from typing import ClassVar


class StructuredFile:
    """Files whose structure survives only when code opens them: a spreadsheet, presentation or CSV file read as
    Markdown loses its rows, cells or slides, and of a large one only a slice fits the prompt."""

    EXTENSIONS: ClassVar[frozenset[str]] = frozenset(
        {".xlsx", ".xlsm", ".xls", ".ods", ".csv", ".tsv", ".pptx", ".ppt", ".odp"}
    )
    BINARY_EXTENSIONS: ClassVar[frozenset[str]] = EXTENSIONS - {".csv", ".tsv"}

    @classmethod
    def works_better_in_code(cls, filename: str) -> bool:
        return cls._extension(filename) in cls.EXTENSIONS

    @classmethod
    def is_binary(cls, filename: str) -> bool:
        """A structured file that is not text at all, so even a few of its lines tell the model nothing."""
        return cls._extension(filename) in cls.BINARY_EXTENSIONS

    @staticmethod
    def _extension(filename: str) -> str:
        return posixpath.splitext(filename.lower())[1]
