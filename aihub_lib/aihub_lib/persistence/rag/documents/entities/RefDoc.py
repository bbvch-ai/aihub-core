from typing import List, Optional

from mongoengine import (
    DictField,
    Document,
    DynamicEmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)


class Metadata(DynamicEmbeddedDocument):
    namespace = StringField(required=True)
    source = StringField(required=True)
    content_hash = StringField(required=True)
    type = StringField(required=True)
    version = StringField(required=True)
    created_at = IntField(required=True)
    updated_at = IntField(required=True)
    inserted_at = IntField(required=True)


class DocumentData(DynamicEmbeddedDocument):
    id = StringField(required=True, db_field="id_")
    metadata = EmbeddedDocumentField(Metadata)
    excluded_embed_metadata_keys = ListField(StringField())
    excluded_llm_metadata_keys = ListField(StringField())
    relationships = DictField()
    text = StringField(required=True)
    mimetype = StringField(required=True)
    start_char_idx = IntField()
    end_char_idx = IntField()
    text_template = StringField(default="{metadata_str}\n\n{content}")
    metadata_template = StringField(default="{key}: {value}")
    metadata_seperator = StringField(default="\n")
    class_name = StringField(default="Document")


class RefDoc(Document):
    meta = {
        "collection": "documents-data",
        "strict": False,
    }
    id = StringField(primary_key=True)
    data = EmbeddedDocumentField(DocumentData, db_field="__data__")  # Renamed for querying convenience
    type_ = StringField(db_field="__type__")  # Renamed for consistency

    # Static methods for querying
    @classmethod
    def by_id(cls, doc_id: str) -> "RefDoc":
        return cls.objects.get(id=doc_id)

    @classmethod
    def by_namespace(
        cls,
        namespace: str,
        exclude_ids: Optional[List[str]] = None,
    ) -> List["RefDoc"]:
        return list(cls.objects.filter(data__metadata__namespace=namespace, id__nin=(exclude_ids or [])))
