from typing import Any

from swiss_ai_hub.core.persistence import AgentClassEntity, AgentConfigEntityDocument
from swiss_ai_hub.core.secrets import SecretEncryptionService, SecretPathTransformer

from swiss_ai_hub.api.util.config_secrets import ConfigSecrets


class PlaintextAgentSecretMigration:
    """Encrypts every secret an agent profile still stores in plaintext (#1587).

    Saves encrypt secrets now, but profiles saved before keep theirs in plaintext until they are saved again. Which
    fields are secrets is read off the class's announced form, so a profile whose class has not been announced yet is
    left as it is; the migration runs on every start and picks it up once the class is known. The key is only needed
    when something must be encrypted.
    """

    @staticmethod
    def run() -> list[str]:
        """Encrypts every plaintext secret; returns which profiles it rewrote."""
        paths_by_class: dict[str, set[str]] = {}
        service: SecretEncryptionService | None = None
        migrated: list[str] = []
        for document in AgentConfigEntityDocument.find_all():
            if document.agent_class not in paths_by_class:
                class_entity = AgentClassEntity.get_by_agent_class(document.agent_class)
                paths_by_class[document.agent_class] = (
                    ConfigSecrets.secret_paths(class_entity.form_elements) if class_entity else set()
                )
            config_data = document.config_data
            paths = paths_by_class[document.agent_class]
            if not PlaintextAgentSecretMigration.holds_plaintext(config_data, paths):
                continue
            service = service or SecretEncryptionService.from_settings()
            if AgentConfigEntityDocument.replace_config_data_if_unchanged(
                document.pk, config_data, service.encrypt_paths(config_data, paths)
            ):
                migrated.append(f"agent {document.agent_class}/{document.agent_id}")
        return migrated

    @staticmethod
    def holds_plaintext(config_data: dict[str, Any] | None, paths: set[str]) -> bool:
        return any(
            isinstance(value, str) and value != "" and not SecretEncryptionService.is_encrypted(value)
            for path in paths
            for value in SecretPathTransformer.values_at(config_data or {}, path)
        )
