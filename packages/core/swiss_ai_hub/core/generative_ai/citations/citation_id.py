import hashlib
import re
from typing import ClassVar


class CitationId:
    """The short id an agent cites a document by, the same for that document wherever and whenever it is retrieved.

    Chat clients number sources their own way (OpenWebUI counts the sources of a message in arrival order), so the
    model never cites a number: it cites this id, and the client adapter maps it to the client's index. The leading
    letter keeps it from ever being read as such a number.
    """

    PREFIX: ClassVar[str] = "s"
    HEX_LENGTH: ClassVar[int] = 6
    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"s[0-9a-f]{6}")

    @classmethod
    def of(cls, key: str) -> str:
        """The id for the document identified by `key`: a knowledge document's id, or an attached file's upload id."""
        return cls.PREFIX + hashlib.sha256(key.encode()).hexdigest()[: cls.HEX_LENGTH]
