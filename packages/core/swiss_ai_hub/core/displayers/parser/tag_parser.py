import logging
from collections.abc import Iterator

from swiss_ai_hub.core.displayers.parser.tool_call_markup import ToolCallMarkup
from swiss_ai_hub.core.displayers.stream.content_type import ContentType

logger = logging.getLogger(__name__)


class TagParser:
    """Internal parser splitting streamed content into the answer and what must stay out of it.

    Reasoning spans and tool-call markup are both routed to ``THINKING``: the collapsed block keeps
    a misbehaving model diagnosable, where dropping the span outright would leave nothing to read.
    """

    THINK_OPEN = "<think>"
    THINK_CLOSE = "</think>"

    def __init__(self):
        self.pending = ""
        self.awaiting_close: str | None = None

    @property
    def in_thinking(self) -> bool:
        return self.awaiting_close is not None

    @property
    def _spans(self) -> tuple[tuple[str, str], ...]:
        return ((self.THINK_OPEN, self.THINK_CLOSE), *ToolCallMarkup.SPANS)

    def process_content(self, content: str) -> Iterator[tuple[ContentType, str]]:
        """Process content and yield parsed characters with their type."""
        self.pending += content

        while self.pending:
            if closing := self._closed_span():
                self.pending = self.pending[len(closing) :]
                self.awaiting_close = None
                yield (ContentType.REGULAR, "")  # Signal state change

            elif opened := self._opened_span():
                self.pending = self.pending[len(opened[0]) :]
                self.awaiting_close = opened[1]
                yield (ContentType.THINKING, "")  # Signal state change

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

    def _opened_span(self) -> tuple[str, str] | None:
        """The span starting at the head of pending, if any. Spans do not nest."""
        if self.awaiting_close:
            return None
        return next((span for span in self._spans if self.pending.startswith(span[0])), None)

    def _closed_span(self) -> str | None:
        """A close delimiter at the head of pending.

        A bare ``</think>`` closes too: some chat templates pre-fill the opening tag, so the model
        only ever emits the closing one.
        """
        if self.awaiting_close:
            return self.awaiting_close if self.pending.startswith(self.awaiting_close) else None
        return self.THINK_CLOSE if self.pending.startswith(self.THINK_CLOSE) else None

    def _might_be_incomplete_tag(self) -> bool:
        """Check if pending content might be an incomplete tag."""
        if not self.pending.startswith("<"):
            return False

        candidates = (
            (self.awaiting_close,)
            if self.awaiting_close
            else (self.THINK_CLOSE, *(opening for opening, _ in self._spans))
        )
        return any(
            len(self.pending) < len(candidate) and candidate.startswith(self.pending) for candidate in candidates
        )
