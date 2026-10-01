from typing import Any

from swiss_ai_hub.core.form import transform_formkit_arrays
from swiss_ai_hub.core.persistence import AgentConfigEntityDocument

_LEGACY_DATABASES_KEY = "knowledge_databases"
_LEGACY_COLLECTION_KEY = "knowledge_namespace"
_PAIRS_KEY = "knowledge_namespaces"


class PrePairKnowledgeCollectionMigration:
    """Rewrites mail categories saved before collections became (database, collection) pairs, and drops the old keys.

    That shape named one collection per category in `knowledge_namespace` and the databases to look it up in once, in
    the classification's `knowledge_databases`. Read at runtime, the old keys could not be told apart from a selection
    switched off since: the edit form round-trips keys it does not render, so a category an admin set to "every
    collection" (`knowledge_namespaces: null`) still carried its old collection and was silently narrowed back to it
    (aihub-core-private#299). Whether the category holds `knowledge_namespaces` at all is what separates the two — the
    pair-aware form always saves the key, `null` included — so only a category without it is carried over, and the
    old keys are removed from every profile so nothing can read them again.

    Every database is paired with the collection name because the old shape did not record which one held it;
    `narrow_retrievers` ignores a pair the delegate does not retrieve from, so a surplus pair is inert.
    """

    @staticmethod
    def run() -> list[str]:
        """Rewrites every agent profile still holding the old keys; returns which ones it rewrote."""
        migrated: list[str] = []
        for document in AgentConfigEntityDocument.find_all():
            config_data = document.config_data
            rewritten = PrePairKnowledgeCollectionMigration.rewritten(config_data)
            if rewritten != config_data and AgentConfigEntityDocument.replace_config_data_if_unchanged(
                document.pk, config_data, rewritten
            ):
                migrated.append(f"agent {document.agent_class}/{document.agent_id}")
        return migrated

    @staticmethod
    def rewritten(value: Any) -> Any:
        """A copy of `value` in which every category set carries its collections as pairs and no old key."""
        if isinstance(value, list):
            return [PrePairKnowledgeCollectionMigration.rewritten(item) for item in value]
        if not isinstance(value, dict):
            return value
        rewritten = {key: PrePairKnowledgeCollectionMigration.rewritten(item) for key, item in value.items()}
        if PrePairKnowledgeCollectionMigration._holds_old_keys(rewritten):
            return PrePairKnowledgeCollectionMigration._carried_over(rewritten)
        return rewritten

    @staticmethod
    def _categories(value: dict[str, Any]) -> list[Any] | None:
        """The category rows as a list, read in FormKit's numbered-dict shape too.

        The runtime converts that shape back to a list before validating, so a profile stored in it reached the old
        runtime carry-over all the same; skipping it here would leave its old keys unread and widen the category.
        """
        categories = transform_formkit_arrays(value.get("categories"))
        return categories if isinstance(categories, list) else None

    @staticmethod
    def _holds_old_keys(value: dict[str, Any]) -> bool:
        categories = PrePairKnowledgeCollectionMigration._categories(value)
        if categories is None:
            return False
        return _LEGACY_DATABASES_KEY in value or any(
            isinstance(category, dict) and _LEGACY_COLLECTION_KEY in category for category in categories
        )

    @staticmethod
    def _carried_over(classification: dict[str, Any]) -> dict[str, Any]:
        stored_databases = classification.get(_LEGACY_DATABASES_KEY) or []
        databases = [database for database in stored_databases if isinstance(database, str)]
        categories = [
            PrePairKnowledgeCollectionMigration._category_carried_over(category, databases)
            for category in PrePairKnowledgeCollectionMigration._categories(classification) or []
        ]
        without_databases = {key: item for key, item in classification.items() if key != _LEGACY_DATABASES_KEY}
        return without_databases | {"categories": categories}

    @staticmethod
    def _category_carried_over(category: Any, databases: list[str]) -> Any:
        if not isinstance(category, dict):
            return category
        legacy_collection = category.get(_LEGACY_COLLECTION_KEY)
        without_legacy = {key: item for key, item in category.items() if key != _LEGACY_COLLECTION_KEY}
        if _PAIRS_KEY in category or not legacy_collection or not databases:
            return without_legacy
        pairs = [{"bucket_name": database, "namespace_name": legacy_collection} for database in databases]
        return without_legacy | {_PAIRS_KEY: pairs}
