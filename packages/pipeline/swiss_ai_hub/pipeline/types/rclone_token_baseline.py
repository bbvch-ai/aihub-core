import hashlib
import json
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.secrets import SecretEncryptionService


class RcloneTokenBaseline(BaseModel):
    """What an observation's private remote was created with, so the token rclone holds afterwards can be told apart
    from it and written back over exactly the stored value this run read.

    Holds no plaintext: the token sent to rclone only as a digest, the stored value only when it is ciphertext. The
    token is parsed with ``json.loads`` and never validated by pydantic, whose errors would echo it.
    """

    path: Annotated[str, Field(description="Dotted path of the token in source_configuration, e.g. 'onedrive.token'.")]
    backend_type: Annotated[str, Field(description="Backend the configuration selected when it was read.")]
    stored_ciphertext: Annotated[
        str | None,
        Field(description="The stored `enc:v1:` value as read; None when the row held no ciphertext.", repr=False),
    ]
    sent_digest: Annotated[str, Field(description="sha256 of the token as sent to rclone.", repr=False)]
    had_refresh_token: Annotated[bool, Field(description="Whether the token sent to rclone carried a refresh token.")]

    @classmethod
    def of(
        cls,
        *,
        path: Annotated[str, "Dotted path of the token in source_configuration"],
        backend_type: Annotated[str, "Backend the configuration selects"],
        stored_value: Annotated[Any, "The value stored at the path, as read from the row"],
        sent_token: Annotated[str, "The token exactly as sent to rclone"],
    ) -> Self:
        return cls(
            path=path,
            backend_type=backend_type,
            stored_ciphertext=stored_value if SecretEncryptionService.is_encrypted(stored_value) else None,
            sent_digest=cls.digest(sent_token),
            had_refresh_token=cls.has_refresh_token(sent_token),
        )

    @staticmethod
    def digest(token: Annotated[str, "OAuth token JSON"]) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def has_refresh_token(token: Annotated[str, "OAuth token JSON"]) -> bool:
        return bool(json.loads(token).get("refresh_token"))
