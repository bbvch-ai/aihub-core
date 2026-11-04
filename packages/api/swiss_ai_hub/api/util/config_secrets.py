from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import HTTPException
from swiss_ai_hub.core.form import FormkitElement, SecretFieldWalker
from swiss_ai_hub.core.persistence import AgentClassEntity, AgentConfigEntityDocument
from swiss_ai_hub.core.secrets import SecretEncryptionService, SecretPathTransformer


# Not decorated with `trace_fn`: it records every call's inputs and outputs, and each method here handles secrets.
class ConfigSecrets:
    """
    Encrypts, masks and restores the secret fields of an agent profile, found through its class's announced form.

    The key is needed only once a non-empty secret sits at a secret path, so profiles without one work without a key.
    """

    @staticmethod
    def secret_paths(elements: Annotated[list[FormkitElement], "Announced form elements of the class"]) -> set[str]:
        return SecretFieldWalker.secret_paths(elements)

    @staticmethod
    def has_secret_values(
        config: Annotated[dict[str, Any] | None, "Configuration as submitted or as stored"],
        paths: Annotated[set[str], "Dotted paths of the secret fields"],
    ) -> bool:
        """The one condition under which masking, encrypting and the startup guard need the key."""
        return any(
            isinstance(value, str) and value != ""
            for path in paths
            for value in SecretPathTransformer.values_at(config or {}, path)
        )

    @staticmethod
    def masked(
        config: Annotated[dict[str, Any], "Configuration as stored, secrets encrypted"],
        elements: Annotated[list[FormkitElement], "Announced form elements of the class"],
    ) -> dict[str, Any]:
        paths = ConfigSecrets.secret_paths(elements)
        if not ConfigSecrets.has_secret_values(config, paths):
            return config
        return SecretEncryptionService.from_settings().mask_paths(config, paths)

    @staticmethod
    def restored(
        submitted: Annotated[dict[str, Any] | None, "Configuration as submitted, possibly holding masks"],
        stored: Annotated[dict[str, Any] | None, "Configuration currently persisted; None on create"],
        elements: Annotated[list[FormkitElement], "Announced form elements of the class"],
    ) -> dict[str, Any] | None:
        """With nothing stored, as on a create from a cloned or imported form, a mask is the client's mistake: a 400
        rather than a failure in ``encrypt``. Neither this nor the refusal of submitted ciphertext echoes the value."""
        paths = ConfigSecrets.secret_paths(elements)
        if not ConfigSecrets.has_secret_values(submitted, paths):
            return submitted
        service = SecretEncryptionService.from_settings()
        try:
            service.reject_submitted_ciphertext(submitted, paths)
            return service.restore_masked_paths(submitted, stored or {}, paths)
        except ValueError as unusable_secret:
            raise HTTPException(status_code=400, detail=str(unusable_secret)) from None

    @staticmethod
    def encrypted(
        config: Annotated[dict[str, Any], "Configuration with masks already restored"],
        elements: Annotated[list[FormkitElement], "Announced form elements of the class"],
    ) -> dict[str, Any]:
        paths = ConfigSecrets.secret_paths(elements)
        if not ConfigSecrets.has_secret_values(config, paths):
            return config
        return SecretEncryptionService.from_settings().encrypt_paths(config, paths)

    @staticmethod
    def stored_profiles_with_secret_paths() -> Iterator[tuple[AgentConfigEntityDocument, set[str]]]:
        """Every stored profile with its class's secret paths; a class not announced yet has none."""
        paths_by_class: dict[str, set[str]] = {}
        for document in AgentConfigEntityDocument.find_all():
            if document.agent_class not in paths_by_class:
                class_entity = AgentClassEntity.get_by_agent_class(document.agent_class)
                paths_by_class[document.agent_class] = (
                    ConfigSecrets.secret_paths(class_entity.form_elements) if class_entity else set()
                )
            yield document, paths_by_class[document.agent_class]

    @staticmethod
    def ensure_key_for_stored_secrets() -> None:
        """Raise when a stored secret could not be masked for lack of a usable key, before discovery would drop its
        profile and the OpenWebUI sync delete its model."""
        if any(
            ConfigSecrets.has_secret_values(document.config_data, paths)
            for document, paths in ConfigSecrets.stored_profiles_with_secret_paths()
        ):
            SecretEncryptionService.from_settings()
