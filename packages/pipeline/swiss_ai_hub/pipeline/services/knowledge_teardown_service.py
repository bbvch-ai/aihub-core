import logging
from typing import Annotated

from swiss_ai_hub.core.persistence import RefDoc
from swiss_ai_hub.core.persistence.rag.datalake.entities import NamespaceEntity
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import (
    MAX_PARTITIONS,
    get_partition_name_for_namespace,
)

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.util.milvus_utils import build_milvus_client
from swiss_ai_hub.pipeline.util.mongo_utils import ensure_connection

logger = logging.getLogger(__name__)


class KnowledgeTeardownService:
    """Destroys one namespace across every store that holds its data.

    Every step is idempotent, so a failed teardown is safe to re-drive rather than leaving a silent
    half-deletion. The entity row is removed last: while it exists, flagged ``deleting`` and excluded from
    enumeration, it is the durable record that the work is still owed.
    """

    @staticmethod
    def teardown_namespace(
        namespace_id: Annotated[str, "Entity id of the namespace being torn down"],
        namespace_name: Annotated[str, "Namespace as stored in vector and doc metadata"],
        folder_name: Annotated[str, "Folder prefix the namespace occupies in the bucket"],
        db_name: Annotated[str, "Milvus collection and doc-store database name"],
        data_lake_client: AbstractDataLakeClient,
    ) -> None:
        logger.info(f"Tearing down namespace '{namespace_name}' in database '{db_name}'")

        # First: the source files are what an observation would re-enumerate, and the figures each document
        # fans out into live under the same prefix.
        data_lake_client.delete_directory(directory_path=folder_name)

        ensure_connection(db_name=db_name, db_alias=db_name)
        removed = RefDoc.delete_by_namespace(db_alias=db_name, namespace=namespace_name)
        logger.info(f"Removed {removed} document(s) from the doc store of '{db_name}'")

        KnowledgeTeardownService._delete_vectors(db_name=db_name, namespace_name=namespace_name)

        NamespaceEntity.delete_namespace(namespace_id)

        logger.info(f"Teardown complete for namespace '{namespace_name}'")

    @staticmethod
    def _delete_vectors(db_name: str, namespace_name: str) -> None:
        """Filtered delete, never a partition drop.

        Namespaces hash into shared partitions and collisions are expected, so dropping the partition would
        also wipe the vectors of every other namespace that hashed to it.
        """
        client = build_milvus_client()
        if not client.has_collection(collection_name=db_name):
            logger.info(f"Collection '{db_name}' does not exist, skipping vector deletion")
            return

        partitions = client.list_partitions(collection_name=db_name)
        has_manual_partitions = len([name for name in partitions if name.startswith("partition_")]) == MAX_PARTITIONS
        partition_name = get_partition_name_for_namespace(namespace_name) if has_manual_partitions else None

        if partition_name:
            client.load_partitions(collection_name=db_name, partition_names=[partition_name])
        else:
            client.load_collection(collection_name=db_name)

        client.delete(
            collection_name=db_name,
            filter=f'{NAMESPACE} == "{namespace_name}"',
            partition_name=partition_name,
        )
