import aioimaplib


class ImapCommandError(Exception):
    """Raised when the IMAP server answers a command with a non-OK status.

    aioimaplib returns NO/BAD responses instead of raising, so without this check a failed login or
    select would silently flow into response parsing and surface as an empty inbox.
    """

    def __init__(self, command: str, result: str, lines: list[bytes]) -> None:
        detail = " ".join(
            bytes(line).decode(errors="replace") if isinstance(line, bytes | bytearray) else str(line)
            for line in lines
        )
        super().__init__(f"IMAP {command} failed with {result}: {detail}")
        self.command = command
        self.result = result

    @classmethod
    def check(cls, command: str, response: aioimaplib.Response) -> aioimaplib.Response:
        """Fail fast on a non-OK server response, returning the response unchanged otherwise."""
        if response.result != "OK":
            raise cls(command, response.result, response.lines)
        return response
