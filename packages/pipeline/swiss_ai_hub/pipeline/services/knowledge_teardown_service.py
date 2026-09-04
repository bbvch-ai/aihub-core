import logging
from typing import Annotated

from swiss_ai_hub.core.infrastructure import MongoConnectionRegistry
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity, RefDoc

from swiss_ai_hub.pipeline.util.store_builders import build_s3_file_access_service, build_vector_store

logger = logging.getLogger(__name__)


class KnowledgeTeardownService:
    """Destroys a knowledge database or one of its namespaces across every store that holds its data.

    Every step is idempotent, so a failed teardown is safe to re-drive rather than leaving a silent
    half-deletion. The entity rows are removed last: while they exist (flagged ``deleting``, excluded from
    every enumeration path) they are the durable record that the work is still owed.
    """

    @staticmethod
    def teardown_database(
        bucket_id: Annotated[str, "Entity id of the bucket being torn down"],
        bucket_name: Annotated[str, "S3 bucket backing the database"],
        db_name: Annotated[str, "Milvus collection and doc-store database name"],
    ) -> None:
        logger.info(f"Tearing down knowledge database '{db_name}' (bucket '{bucket_name}')")

        build_vector_store(db_name).drop_collection()

        MongoConnectionRegistry.ensure_alias(db_name)
        RefDoc.drop_database(db_name)

        build_s3_file_access_service().delete_container(bucket_name)

        NamespaceEntity.delete_all_for_bucket(bucket_id)
        BucketEntity.delete_bucket(bucket_id)

        logger.info(f"Teardown complete for database '{db_name}'")

    @staticmethod
    def teardown_namespace(
        namespace_id: Annotated[str, "Entity id of the namespace being torn down"],
        namespace_name: Annotated[str, "Namespace as stored in vector/doc metadata"],
        folder_name: Annotated[str, "Folder prefix the namespace occupies in the bucket"],
        bucket_name: Annotated[str, "S3 bucket backing the database"],
        db_name: Annotated[str, "Milvus collection and doc-store database name"],
    ) -> None:
        logger.info(f"Tearing down namespace '{namespace_name}' in database '{db_name}'")

        build_s3_file_access_service().delete_prefix(bucket_name, f"{folder_name}/")

        MongoConnectionRegistry.ensure_alias(db_name)
        RefDoc.delete_by_namespace(db_name, namespace_name)

        # Filtered delete, never a partition drop: namespaces share hashed Milvus partitions, so dropping the
        # partition would also wipe any colliding namespace's vectors.
        build_vector_store(db_name).delete_by_namespace(namespace_name)

        NamespaceEntity.delete_namespace(namespace_id)

        logger.info(f"Teardown complete for namespace '{namespace_name}'")
