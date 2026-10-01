class InvalidPathPatternError(ValueError):
    """Raised for a glob or regex that cannot be applied to document paths.

    The message is written for whoever chose the pattern, often a model in a tool loop: it names the pattern and
    says what to change, because an opaque parser error gives a model nothing to retry with.
    """

    def __init__(self, pattern: str, reason: str) -> None:
        super().__init__(f"Invalid path pattern {pattern!r}: {reason}")
        self.pattern = pattern
        self.reason = reason
