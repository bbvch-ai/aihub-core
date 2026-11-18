from fastapi import HTTPException, status


class OpenWebuiSignatureRejectedError(HTTPException):
    """Raised when OpenWebUI's signed identity headers are present but fail verification.

    It is final: ``TokenAndOauth2Handler`` must not try the next handler, because that one authenticates the bearer
    token's owner, and OpenWebUI's bearer belongs to the superuser. An expired or forged header set would otherwise
    pass as the superuser instead of being refused.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
