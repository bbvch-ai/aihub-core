import logging
from collections.abc import Iterator

from swiss_ai_hub.core.displayers.stream.content_type import ContentType

logger = logging.getLogger(__name__)


class TagParser:
    """Internal parser for handling thinking tags in streamed content."""

    THINK_OPEN = "<think>"
    THINK_CLOSE = "</think>"

    def __init__(self):
        self.pending = ""
        self.in_thinking = False

    def process_content(self, content: str) -> Iterator[tuple[ContentType, str]]:
        """Process content and yield parsed characters with their type."""
        self.pending += content

        while self.pending:
            if self.pending.startswith(self.THINK_OPEN):
                self.in_thinking = True
                self.pending = self.pending[len(self.THINK_OPEN) :]
                yield (ContentType.THINKING, "")  # Signal state change

            elif self.pending.startswith(self.THINK_CLOSE):
                self.in_thinking = False
                self.pending = self.pending[len(self.THINK_CLOSE) :]
                yield (ContentType.REGULAR, "")  # Signal state change

            elif self._might_be_incomplete_tag():
                # Wait for more content
                break

            else:
                char = self.pending[0]
                self.pending = self.pending[1:]
                content_type = ContentType.THINKING if self.in_thinking else ContentType.REGULAR
                yield (content_type, char)

    def flush_remaining(self) -> Iterator[tuple[ContentType, str]]:
        """Process any remaining content."""
        if self._might_be_incomplete_tag():
            logger.warning(f"Incomplete tag found at end of stream: {self.pending}")

        for char in self.pending:
            content_type = ContentType.THINKING if self.in_thinking else ContentType.REGULAR
            yield (content_type, char)

        self.pending = ""

    def _might_be_incomplete_tag(self) -> bool:
        """Check if pending content might be an incomplete tag."""
        if not self.pending.startswith("<"):
            return False

        max_tag_len = max(len(self.THINK_OPEN), len(self.THINK_CLOSE))
        return len(self.pending) < max_tag_len and (
            self.THINK_OPEN.startswith(self.pending) or self.THINK_CLOSE.startswith(self.pending)
        )
