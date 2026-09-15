from typing import Annotated, Any, ClassVar

from swiss_ai_hub.core.secrets.secret_path_transformer import SecretPathTransformer


class SecretMasker:
    """
    Hides stored secrets from API responses and lets a client resubmit a form without knowing them.

    A response replaces every set secret with ``MASK``; a submission that still carries ``MASK`` at a path
    means "keep what is stored", and the stored value is put back before validation and encryption. Empty
    values are not masked, so a client can tell an unset secret from a set one.
    """

    MASK: ClassVar[str] = "••••••••"

    @classmethod
    def mask_paths(cls, config: dict[str, Any], paths: set[str]) -> dict[str, Any]:
        return SecretPathTransformer.transform(config, paths, cls._mask)

    @classmethod
    def restore_masked_paths(
        cls,
        submitted: Annotated[dict[str, Any], "Configuration as resubmitted by the client"],
        stored: Annotated[dict[str, Any], "Configuration currently persisted, secrets encrypted"],
        paths: Annotated[set[str], "Dotted paths of the secret fields"],
    ) -> dict[str, Any]:
        """Repeater items are matched by position; a mask with no stored counterpart is a client error."""
        result = submitted
        for path in paths:
            stored_values = iter(SecretPathTransformer.values_at(stored, path))

            def restore(value: Any, _path: str = path) -> Any:
                stored_value = next(stored_values, None)
                if value != cls.MASK:
                    return value
                if stored_value is None or stored_value == "":
                    raise ValueError(f"'{_path}' was submitted masked but no secret is stored for it.")
                return stored_value

            result = SecretPathTransformer.transform(result, {path}, restore)
        return result

    @classmethod
    def _mask(cls, value: Any) -> Any:
        if value is None or value == "":
            return value
        return cls.MASK
