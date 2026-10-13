class InvalidSearchPatternError(ValueError):
    """Raised for a content search query that cannot be run.

    As with `InvalidPathPatternError`, the message is written for whoever chose the query, often a model in a tool
    loop: it names the query and says what to change.
    """

    def __init__(self, query: str, reason: str) -> None:
        shown = query if len(query) <= 80 else query[:80] + "..."
        super().__init__(f"Invalid search query {shown!r}: {reason}")
        self.query = query
        self.reason = reason
