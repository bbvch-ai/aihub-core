class OpenTerminalError(Exception):
    """The sandbox refused a request; the message carries its reason so a model or user can correct the call."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code
