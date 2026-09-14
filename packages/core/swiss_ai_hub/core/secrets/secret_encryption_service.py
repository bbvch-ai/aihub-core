from typing import Annotated, Any, Self

from cryptography.fernet import Fernet

from swiss_ai_hub.core.infrastructure.encryption.config_encryption_settings import ConfigEncryptionSettings
from swiss_ai_hub.core.secrets.secret_masker import SecretMasker
from swiss_ai_hub.core.secrets.secret_path_transformer import SecretPathTransformer

_CIPHERTEXT_PREFIX = "enc:v1:"
_MISSING_KEY_MESSAGE = (
    "AIHUB_CONFIG_ENCRYPTION_KEY is not set. Secret configuration fields cannot be stored or read without it; "
    "refusing to fall back to plaintext."
)


class SecretEncryptionService:
    """
    Encrypts secret configuration fields at rest with the platform's shared symmetric key.

    Ciphertext is self-describing (``enc:v1:<token>``) so a stored value declares whether it is encrypted:
    decryption passes plaintext through unchanged, encryption never double-wraps, and a key rotation can later
    bump the version. Encryption happens where a configuration is written (the API) and decryption where it
    is consumed (agent runners, pipelines), both with the same key.
    """

    def __init__(self, key: Annotated[str, "Fernet key, url-safe base64 of 32 bytes"]) -> None:
        self._fernet = Fernet(key.encode())

    @classmethod
    def from_settings(cls, settings: ConfigEncryptionSettings | None = None) -> Self:
        settings = settings or ConfigEncryptionSettings()
        if settings.ENCRYPTION_KEY is None:
            raise ValueError(_MISSING_KEY_MESSAGE)
        return cls(settings.ENCRYPTION_KEY.get_secret_value())

    @staticmethod
    def is_encrypted(value: Any) -> bool:
        return isinstance(value, str) and value.startswith(_CIPHERTEXT_PREFIX)

    def encrypt(self, value: Any) -> Any:
        """``None`` and the empty string mean "no secret" and stay as they are; the mask must never be persisted."""
        if value is None or value == "" or self.is_encrypted(value):
            return value
        if value == SecretMasker.MASK:
            raise ValueError("Refusing to encrypt the secret mask; restore the stored value before encrypting.")
        if not isinstance(value, str):
            raise TypeError(f"Secret fields hold strings, got {type(value).__name__}.")
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
