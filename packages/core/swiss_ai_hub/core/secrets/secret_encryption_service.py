import hashlib
import hmac
from typing import Annotated, Any, ClassVar, Self

from cryptography.fernet import Fernet

from swiss_ai_hub.core.infrastructure.encryption.config_encryption_settings import ConfigEncryptionSettings
from swiss_ai_hub.core.secrets.secret_path_transformer import SecretPathTransformer

_CIPHERTEXT_PREFIX = "enc:v1:"
_MASK_SEPARATOR = ":"
_HANDLE_DOMAIN = b"swiss-ai-hub:secret-mask-handle:"
_HANDLE_LENGTH = 16
_MISSING_KEY_MESSAGE = (
    "AIHUB_CONFIG_ENCRYPTION_KEY is not set. Secret configuration fields cannot be stored or read without it; "
    "refusing to fall back to plaintext."
)


class SecretEncryptionService:
    """
    Encrypts secret configuration fields at rest, and masks them on the way back to a client.

    Ciphertext is self-describing (``enc:v1:<token>``) so a stored value declares whether it is encrypted:
    decryption passes plaintext through unchanged, encryption never double-wraps, and a key rotation can later
    bump the version. Encryption happens where a configuration is written (the API) and decryption where it
    is consumed (agent runners, pipelines), both with the same key.

    A response replaces every set secret with ``<mask>:<handle>``, where the handle identifies which stored
    secret the mask stands for. Resubmitting a mask means "keep that secret", and it resolves by handle rather
    than by position, so a repeated section survives its rows being reordered, deleted or inserted. The handle
    is an HMAC under a key derived from the encryption key: legacy rows may still hold plaintext, and an
    unkeyed digest of a plaintext password published in a response would be an offline dictionary attack.

    Two invariants callers must respect. ``mask_paths`` and ``restore_masked_paths`` have to be handed the same
    representation of the stored document, normally the encrypted one straight from the database; masking one
    representation and restoring against another makes every handle miss. And a mask is never a value to
    persist: a submission whose secret is absent rather than masked says nothing about whether the stored
    secret should survive, which is a decision for the layer that writes to the database.
    """

    MASK: ClassVar[str] = "••••••••"

    def __init__(self, key: Annotated[str, "Fernet key, url-safe base64 of 32 bytes"]) -> None:
        self._fernet = Fernet(key.encode())
        self._handle_key = hashlib.sha256(_HANDLE_DOMAIN + key.encode()).digest()

    @classmethod
    def from_settings(cls, settings: ConfigEncryptionSettings | None = None) -> Self:
        settings = settings or ConfigEncryptionSettings()
        if settings.ENCRYPTION_KEY is None:
            raise ValueError(_MISSING_KEY_MESSAGE)
        return cls(settings.ENCRYPTION_KEY.get_secret_value())

    @staticmethod
    def is_encrypted(value: Any) -> bool:
        return isinstance(value, str) and value.startswith(_CIPHERTEXT_PREFIX)

    @classmethod
    def is_masked(cls, value: Any) -> bool:
        return isinstance(value, str) and value.startswith(cls.MASK)

    def encrypt(self, value: Any) -> Any:
        """``None`` and the empty string mean "no secret" and stay as they are; the mask must never be persisted."""
        if value is None or value == "":
            return value
        if not isinstance(value, str):
            raise TypeError(f"Secret fields hold strings, got {type(value).__name__}.")
        if self.is_masked(value):
            raise ValueError("Refusing to encrypt the secret mask; restore the stored value before encrypting.")
        if self.is_encrypted(value):
            return value
        return _CIPHERTEXT_PREFIX + self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: Any) -> Any:
        if not self.is_encrypted(value):
            return value
        token = value.removeprefix(_CIPHERTEXT_PREFIX)
        return self._fernet.decrypt(token.encode()).decode()

    def encrypt_paths(self, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config, paths, self.encrypt)

    def decrypt_paths(self, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config, paths, self.decrypt)

    def mask_paths(self, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config, paths, self._mask)

    def restore_masked_paths(
        self,
        submitted: Annotated[dict[str, Any], "Configuration as resubmitted by the client"],
        stored: Annotated[dict[str, Any], "Configuration currently persisted, secrets encrypted"],
        paths: Annotated[set[str], "Dotted paths of the secret fields"],
    ) -> dict[str, Any]:
        """Each mask names the stored secret it was minted from, so row order between response and submission is free."""
        result = submitted
        for path in paths:
            by_handle = {
                self._handle(value): value
                for value in SecretPathTransformer.values_at(stored, path)
                if isinstance(value, str) and value
            }

            def restore(value: Any, _path: str = path, _by_handle: dict[str, str] = by_handle) -> Any:
                if not self.is_masked(value):
                    return value
                prefix = f"{self.MASK}{_MASK_SEPARATOR}"
                if not value.startswith(prefix):
                    raise ValueError(f"'{_path}' was submitted as a bare mask carrying no handle; resubmit the form.")
                stored_value = _by_handle.get(value.removeprefix(prefix))
                if stored_value is None:
                    raise ValueError(
                        f"'{_path}' was submitted masked but no stored secret matches it; resubmit the form."
                    )
                return stored_value

            result = SecretPathTransformer.transform(result, {path}, restore)
        return result

    def _mask(self, value: Any) -> Any:
        """Empty values are not masked, so a client can tell an unset secret from a set one."""
        if value is None or value == "":
            return value
        if not isinstance(value, str):
            raise TypeError(f"Secret fields hold strings, got {type(value).__name__}.")
        if self.is_masked(value):
            return value
        return f"{self.MASK}{_MASK_SEPARATOR}{self._handle(value)}"

    def _handle(self, value: str) -> str:
        return hmac.new(self._handle_key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:_HANDLE_LENGTH]
