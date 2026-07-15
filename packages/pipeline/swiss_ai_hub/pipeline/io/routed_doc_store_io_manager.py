from dagster import ConfigurableIOManager, InputContext, OutputContext
from llama_index.storage.docstore.mongodb import MongoDocumentStore

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id
from swiss_ai_hub.pipeline.util.partition_utils import split_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_doc_store


class RoutedDocStoreIOManager(ConfigurableIOManager):
    """Mongo document store IO manager for the RAG pipeline, routed per run by bucket.

    Partition keys are composite ``{bucket}|{file_uri}``: the store name is resolved from the ``bucket``
    component (via ``get_db_name_from_bucket_name``) and the document id from the decoded file URI. This lets
    one deployed pipeline persist/read documents for every self-service database. The non-partitioned branch
    (unused by the standard graph) resolves the bucket from the ``aihub/bucket`` run tag for parity.
    """

    encode_partition_keys: bool = True

    def handle_output(self, context: OutputContext, obj: RefDocDocument | list[RefDocDocument]) -> None:
        documents = [obj] if isinstance(obj, RefDocDocument) else obj
        bucket, _ = split_composite_partition_key(context.partition_key, encode=self.encode_partition_keys)
        store = self._store_for_bucket(bucket)
        for document in documents:
            context.log.info(f"Adding document to docstore '{bucket}': {document.id_}")
        store.add_documents(documents)

    def load_input(self, context: InputContext) -> RefDocDocument | list[RefDocDocument]:
        if context.has_partition_key:
            bucket, file_uri = split_composite_partition_key(context.partition_key, encode=self.encode_partition_keys)
            return self._load_ref_doc(self._store_for_bucket(bucket), file_uri, context)

        bucket = bucket_from_run_tag(context)
        store = self._store_for_bucket(bucket)
        bucket_prefix = f"{bucket}|"
        partitions_def = context.upstream_output.asset_partitions_def
        if partitions_def is None:
            raise ValueError("Cannot load documents without partition information.")
        all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
        return [
            self._load_ref_doc(store, split_composite_partition_key(key, encode=self.encode_partition_keys)[1], context)
            for key in all_partition_keys
            if key.startswith(bucket_prefix)
        ]

    @staticmethod
    def _store_for_bucket(bucket: str) -> MongoDocumentStore:
        return build_doc_store(get_db_name_from_bucket_name(bucket))

    @staticmethod
    def _load_ref_doc(store: MongoDocumentStore, file_uri: str, context: InputContext) -> RefDocDocument:
        doc_id = uri_to_id(file_uri)
        context.log.info(f"Loading document with ID: {doc_id}")
        document = store.get_document(doc_id)
        return RefDocDocument(**document.to_dict())
