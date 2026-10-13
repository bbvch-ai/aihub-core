class InvalidRecordSchemaError(ValueError):
    """Raised when the proposed record schema cannot be used for extraction.

    A `ValueError` so callers degrade on it with the same single clause they already use for malformed structured
    output, as the agent guide prescribes.
    """

    def __init__(self, problems: list[str]) -> None:
        super().__init__(f"The proposed record schema is unusable: {'; '.join(problems)}.")
        self.problems = problems
