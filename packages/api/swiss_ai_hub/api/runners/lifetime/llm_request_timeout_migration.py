from typing import Any

from swiss_ai_hub.core.persistence import AgentConfigEntityDocument, ProcessConfigEntityDocument

PREVIOUS_DEFAULT_TIMEOUT = 600
CURRENT_DEFAULT_TIMEOUT = 300.0


class LLMRequestTimeoutMigration:
    """Lowers stored LLM request timeouts still at the old 600 s default to the new 300 s one.

    The form saves the default it showed, so lowering it in `LLMParameter` reaches only profiles saved afterwards
    (aihub-core-private#349). A 600 s an admin typed is indistinguishable from the saved default and is lowered too.
    Keyed on `temperature` next to `timeout` because only the LLM parameters store both, wherever a blueprint nests
    them; embedding parameters have a `timeout` of their own and are left alone.
    """

    @staticmethod
    def run() -> list[str]:
        """Rewrites every agent and process config still holding the old default; returns which ones it rewrote."""
        agents = LLMRequestTimeoutMigration._migrate(AgentConfigEntityDocument)
        processes = LLMRequestTimeoutMigration._migrate(ProcessConfigEntityDocument)
        return [f"agent {agent.agent_class}/{agent.agent_id}" for agent in agents] + [
            f"process {process.process_class}/{process.process_id}" for process in processes
        ]

    @staticmethod
    def _migrate[TDocument: AgentConfigEntityDocument | ProcessConfigEntityDocument](
        document_class: type[TDocument],
    ) -> list[TDocument]:
        """The documents of `document_class` that this call rewrote, skipping any saved again meanwhile."""
        migrated: list[TDocument] = []
        for document in document_class.find_all():
            config_data = document.config_data
            lowered = LLMRequestTimeoutMigration.lowered(config_data)
            if lowered != config_data and document_class.replace_config_data_if_unchanged(
                document.pk, config_data, lowered
            ):
                migrated.append(document)
        return migrated

    @staticmethod
    def lowered(value: Any) -> Any:
        """A copy of `value` in which every LLM request timeout at the old default holds the new one."""
        if isinstance(value, list):
            return [LLMRequestTimeoutMigration.lowered(item) for item in value]
        if not isinstance(value, dict):
            return value
        lowered = {key: LLMRequestTimeoutMigration.lowered(item) for key, item in value.items()}
        if LLMRequestTimeoutMigration._is_llm_parameter_at_old_default(lowered):
            lowered["timeout"] = CURRENT_DEFAULT_TIMEOUT
        return lowered

    @staticmethod
    def _is_llm_parameter_at_old_default(value: dict[str, Any]) -> bool:
        timeout = value.get("timeout")
        return (
            "temperature" in value
            and isinstance(timeout, int | float)
            and not isinstance(timeout, bool)
            and timeout == PREVIOUS_DEFAULT_TIMEOUT
        )
