from dataclasses import dataclass, field


@dataclass
class StreamBuffer:
    """Internal class to manage content buffering with flush conditions."""

    content: str = ""
    max_length: int = 512
    flush_on_chars: set[str] = field(default_factory=lambda: {".", "\n"})

    def add(self, char: str) -> bool:
        """Add a character and return True if flush is needed."""
        self.content += char
        return char in self.flush_on_chars or len(self.content) >= self.max_length

    def get_and_clear(self) -> str:
        """Get content and clear buffer."""
        result = self.content
        self.content = ""
        return result

    def __bool__(self) -> bool:
        """Return True if buffer has content."""
        return bool(self.content)
