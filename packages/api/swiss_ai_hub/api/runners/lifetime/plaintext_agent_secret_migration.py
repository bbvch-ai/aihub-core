from typing import Annotated, Any

from swiss_ai_hub.core.persistence import AgentConfigEntityDocument
from swiss_ai_hub.core.secrets import SecretEncryptionService, SecretPathTransformer

from swiss_ai_hub.api.util.config_secrets import ConfigSecrets


class PlaintextAgentSecretMigration:
    """Encrypts the secrets agent profiles stored in plaintext before #1587.

    A profile whose class has not been announced yet is left as it is and picked up on a later start.
    """

    @staticmethod
    def run() -> list[str]:
        """Encrypts every plaintext secret; returns which profiles it rewrote."""
        service: SecretEncryptionService | None = None
        migrated: list[str] = []
        for document, paths in ConfigSecrets.stored_profiles_with_secret_paths():
            config_data = document.config_data
            if not PlaintextAgentSecretMigration._holds_plaintext(config_data, paths):
                continue
            service = service or SecretEncryptionService.from_settings()
            if AgentConfigEntityDocument.replace_config_data_if_unchanged(
                document.pk, config_data, service.encrypt_paths(config_data, paths)
            ):
                migrated.append(f"agent {document.agent_class}/{document.agent_id}")
        return migrated

    @staticmethod
    def _holds_plaintext(
        config_data: Annotated[dict[str, Any] | None, "Configuration as stored"],
        paths: Annotated[set[str], "Dotted paths of the secret fields"],
    ) -> bool:
        return any(
            isinstance(value, str) and value != "" and not SecretEncryptionService.is_encrypted(value)
            for path in paths
            for value in SecretPathTransformer.values_at(config_data or {}, path)
        )
