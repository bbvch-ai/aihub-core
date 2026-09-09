from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.secrets.secret_encryption_service import SecretEncryptionService
    from swiss_ai_hub.core.secrets.secret_masker import SecretMasker
    from swiss_ai_hub.core.secrets.secret_path_transformer import SecretPathTransformer

__all__ = ["SecretEncryptionService", "SecretMasker", "SecretPathTransformer"]

_LAZY_IMPORTS = {
    "SecretEncryptionService": "swiss_ai_hub.core.secrets.secret_encryption_service",
    "SecretMasker": "swiss_ai_hub.core.secrets.secret_masker",
    "SecretPathTransformer": "swiss_ai_hub.core.secrets.secret_path_transformer",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
