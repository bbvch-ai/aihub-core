from mongoengine import DoesNotExist

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity


class KnowledgeCollectionLabel:
    """How a knowledge collection is named to users: "Database / Collection", since collection names repeat across
    databases. Chat clients list collections under this label and agents name them by it."""

    @staticmethod
    def of(bucket: BucketEntity, namespace: NamespaceEntity, locale: str) -> str:
        handler = LocaleHandler(locale)
        database = KnowledgeCollectionLabel._text(handler, bucket.name) or bucket.db_name
        collection = KnowledgeCollectionLabel._text(handler, namespace.display_name) or namespace.namespace_name
        return f"{database} / {collection}"

    @staticmethod
    def of_reference(reference: KnowledgeReference, locale: str) -> str:
        """The label of a referenced collection; one that no longer exists is named by its identifiers."""
        try:
            bucket = BucketEntity.get_bucket_by_db_name(reference.database)
            namespace = NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), reference.namespace)
        except DoesNotExist:
            return f"{reference.database} / {reference.namespace}"
        return KnowledgeCollectionLabel.of(bucket, namespace, locale)

    @staticmethod
    def _text(handler: LocaleHandler, value: LocaleStringEntity | None) -> str:
        return (handler.extract(value) or "") if value else ""
