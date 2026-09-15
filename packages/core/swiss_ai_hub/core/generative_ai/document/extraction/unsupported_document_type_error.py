class UnsupportedDocumentTypeError(Exception):
    """Raised when no loader can read a document.

    `DocumentLoaderSelector` returns `None` instead, which is right for its callers: the API answers 400 and the
    mail-attachment reader skips the file. This helper's whole contract is to return a title and a body, so it has
    no empty result to hand back and says so rather than returning something a caller might treat as content.
    """

    def __init__(self, filename: str, extension: str | None) -> None:
        named = f"'{extension}'" if extension else "no recognisable extension"
        super().__init__(f"No loader can read {filename!r} ({named})")
        self.filename = filename
        self.extension = extension
