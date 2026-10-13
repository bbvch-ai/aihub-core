from typing import Any

from swiss_ai_hub.core.persistence import AgentConfigEntityDocument, ProcessConfigEntityDocument


class EmptyNamespaceScopeMigration:
    """Turns a stored retriever scope of "no namespaces" into the explicit "all namespaces" it used to mean.

    Before #1603 an empty `index_namespaces` searched the whole collection; since then the config model rejects
    it, so every run of such an agent aborts. Rewriting it to `all_namespaces` keeps the behaviour it was saved
    with. Keyed on `collection_name` because only the Milvus vector-store config stores that key, wherever a
    blueprint nests it (a repeater row, a group, FormKit's numbered-dict shape).
    """

    @staticmethod
    def run() -> list[str]:
        """Rewrites every agent and process config still holding an empty scope; returns which ones it rewrote."""
        agents = EmptyNamespaceScopeMigration._migrate(AgentConfigEntityDocument)
        processes = EmptyNamespaceScopeMigration._migrate(ProcessConfigEntityDocument)
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
            widened = EmptyNamespaceScopeMigration.widened(config_data)
            if widened != config_data and document_class.replace_config_data_if_unchanged(
                document.pk, config_data, widened
            ):
                migrated.append(document)
        return migrated

    @staticmethod
    def widened(value: Any) -> Any:
        """A copy of `value` in which every empty retriever scope reads every namespace."""
        if isinstance(value, list):
            return [EmptyNamespaceScopeMigration.widened(item) for item in value]
        if not isinstance(value, dict):
            return value
        widened = {key: EmptyNamespaceScopeMigration.widened(item) for key, item in value.items()}
        if EmptyNamespaceScopeMigration._is_empty_scope(widened):
            widened |= {"all_namespaces": True, "index_namespaces": []}
        return widened

    @staticmethod
    def _is_empty_scope(value: dict[str, Any]) -> bool:
        return (
            isinstance(value.get("collection_name"), str)
            and not value.get("index_namespaces")
            and value.get("all_namespaces") is not True
        )
