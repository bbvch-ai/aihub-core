import hashlib
import hmac
from typing import Annotated, Any, ClassVar, Self

from cryptography.fernet import Fernet

from swiss_ai_hub.core.infrastructure.encryption.config_encryption_settings import ConfigEncryptionSettings
from swiss_ai_hub.core.secrets.secret_path_transformer import SecretPathTransformer

_CIPHERTEXT_PREFIX = "enc:v1:"
_MASK = "••••••••"
_MASK_PREFIX = f"{_MASK}:"
_HANDLE_DOMAIN = b"swiss-ai-hub:secret-mask-handle:"
_HANDLE_LENGTH = 16
_MISSING_KEY_MESSAGE = (
    "AIHUB_CONFIG_ENCRYPTION_KEY is not set. Secret configuration fields cannot be stored or read without it; "
    "refusing to fall back to plaintext."
)


class SecretEncryptionService:
    """
    Encrypts secret configuration fields at rest, and masks them on the way back to a client.

    Ciphertext is self-describing (``enc:v1:<token>``) so a stored value declares whether it is encrypted, and a
    response carries ``<mask>:<handle>`` instead of a secret, where the handle names which stored secret the mask
    stands for. Resubmitting a mask therefore keeps that secret whatever happened to row order in between.

    Callers must hand ``mask_paths`` and ``restore_masked_paths`` the same representation of the stored document,
    normally the encrypted one straight from the database; masking one and restoring against another misses every
    handle. See ``docs/arc42/decisions/2026_09_14_secret_mask_carries_identity_handle.md``.
    """

    MASK: ClassVar[str] = _MASK

    def __init__(self, key: Annotated[str, "Fernet key, url-safe base64 of 32 bytes"]) -> None:
        self._fernet = Fernet(key.encode("utf-8"))
        self._handle_key = hashlib.sha256(_HANDLE_DOMAIN + key.encode("utf-8")).digest()

    @classmethod
    def from_settings(cls, settings: ConfigEncryptionSettings | None = None) -> Self:
        settings = settings or ConfigEncryptionSettings()
        if settings.ENCRYPTION_KEY is None:
            raise ValueError(_MISSING_KEY_MESSAGE)
        return cls(settings.ENCRYPTION_KEY.get_secret_value())

    @staticmethod
    def is_encrypted(value: Any) -> bool:
        return isinstance(value, str) and value.startswith(_CIPHERTEXT_PREFIX)

    @staticmethod
    def is_masked(value: Any) -> bool:
        """True for a bare mask too, so ``encrypt`` rejects one a client invented rather than received."""
        return isinstance(value, str) and value.startswith(_MASK)

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
        return _CIPHERTEXT_PREFIX + self._fernet.encrypt(value.encode("utf-8")).decode()

    def decrypt(self, value: Any) -> Any:
        if not self.is_encrypted(value):
            return value
        token = value.removeprefix(_CIPHERTEXT_PREFIX)
        return self._fernet.decrypt(token.encode("utf-8")).decode()

    def encrypt_paths(self, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config, paths, self.encrypt)

    def decrypt_paths(self, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config, paths, self.decrypt)

    def mask_paths(self, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        """Empty values are not masked, so a client can tell an unset secret from a set one."""
        result = config
        for path in paths:

            def mask(value: Any, _path: str = path) -> Any:
                if value is None or value == "":
                    return value
                if not isinstance(value, str):
                    raise TypeError(f"Secret fields hold strings, got {type(value).__name__}.")
                return f"{_MASK_PREFIX}{self._handle(_path, value)}"

            result = SecretPathTransformer.transform(result, {path}, mask)
        return result

    def restore_masked_paths(
        self,
        submitted: Annotated[dict[str, Any], "Configuration as resubmitted by the client"],
        stored: Annotated[dict[str, Any], "Configuration currently persisted, secrets encrypted"],
        paths: Annotated[set[str], "Dotted paths of the secret fields"],
    ) -> dict[str, Any]:
        """Each mask names the stored secret it was minted from, so row order is free to change in between."""
        result = submitted
        for path in paths:
            by_handle = {
                self._handle(path, value): value
                for value in SecretPathTransformer.values_at(stored, path)
                if isinstance(value, str) and value
            }

            def restore(value: Any, _path: str = path, _by_handle: dict[str, str] = by_handle) -> Any:
                if not self.is_masked(value):
                    return value
                if not value.startswith(_MASK_PREFIX):
                    raise ValueError(f"'{_path}' was submitted as a bare mask carrying no handle; resubmit the form.")
                stored_value = _by_handle.get(value.removeprefix(_MASK_PREFIX))
                if stored_value is None:
                    raise ValueError(
                        f"'{_path}' was submitted masked but no stored secret matches it; resubmit the form."
                    )
                return stored_value

            result = SecretPathTransformer.transform(result, {path}, restore)
        return result

    def _handle(self, path: str, value: str) -> str:
        """The path is part of the message so a handle minted at one secret field cannot resolve at another."""
        message = f"{path}\0{value}".encode()
        return hmac.new(self._handle_key, message, hashlib.sha256).hexdigest()[:_HANDLE_LENGTH]
