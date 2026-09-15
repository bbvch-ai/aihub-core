from swiss_ai_hub.core.displayers.parser.tool_call_markup import ToolCallMarkup


class ToolCallStreamScrubber:
    """Removes tool-call markup from a relayed text stream.

    The agent path reclassifies the markup as reasoning, which needs display events; a plain relay
    has none, so here it is dropped instead. Reasoning tags are deliberately left alone — on that
    path the client renders them itself.
    """

    def __init__(self):
        self._pending = ""
        self._awaiting_close: str | None = None
        self._withheld = ""
        self._deciding = True
        self._suppressing = False

    def feed(self, delta: str) -> str:
        """The part of ``delta`` safe to forward now; markup and still-undecided text are held back."""
        released = self._release(delta)
        if released is None:
            return ""

        self._pending += released
        return self._drain(final=False)

    def flush(self) -> str:
        """Whatever was held back and turned out to be safe, once the stream has ended."""
        if self._suppressing:
            return ""

        self._pending += self._release_withheld()
        return self._drain(final=True)

    def _release(self, delta: str) -> str | None:
        if self._suppressing:
            return None
        if not self._deciding:
            return delta

        self._withheld += delta
        if ToolCallMarkup.opens_react_object(self._withheld):
            self._suppressing = True
            return None
        if ToolCallMarkup.may_open_react_object(self._withheld):
            return None

        return self._release_withheld()

    def _release_withheld(self) -> str:
        self._deciding = False
        released, self._withheld = self._withheld, ""
        return released

    def _drain(self, final: bool) -> str:
        forwarded: list[str] = []

        while self._pending:
            if self._awaiting_close:
                if self._pending.startswith(self._awaiting_close):
                    self._pending = self._pending[len(self._awaiting_close) :]
                    self._awaiting_close = None
                    continue
                if not final and self._might_complete(self._awaiting_close):
                    break
                self._pending = self._pending[1:]
                continue

            if opened := self._opened_span():
                self._pending = self._pending[len(opened[0]) :]
                self._awaiting_close = opened[1]
                continue

            if not final and any(self._might_complete(opening) for opening, _ in ToolCallMarkup.SPANS):
                break

            forwarded.append(self._pending[0])
            self._pending = self._pending[1:]

        if final:
            self._pending = ""
        return "".join(forwarded)

    def _opened_span(self) -> tuple[str, str] | None:
        return next((span for span in ToolCallMarkup.SPANS if self._pending.startswith(span[0])), None)

    def _might_complete(self, delimiter: str) -> bool:
        return len(self._pending) < len(delimiter) and delimiter.startswith(self._pending)
