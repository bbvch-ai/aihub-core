import logging
from typing import Annotated

from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.persistence import BucketEntity, IngestorType
from swiss_ai_hub.core.publishers import SourceUpdatedPublisher

from swiss_ai_hub.pipeline.util.async_utils import run_async
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

logger = logging.getLogger(__name__)


def notify_source_updated(
    bucket: Annotated[str, "Bucket name of the knowledge database whose data lake changed"],
    object_keys: Annotated[list[str], "Object keys written or removed, relative to the bucket"],
) -> None:
    """Tells the database's ingestion pipeline about changed files, one event each, the way a browser upload does.

    A connection per call rather than a cached one: each Dagster op runs in its own process and event loop, and a
    NATS client is bound to the loop it was created on.
    """
    if not object_keys:
        return
    run_async(_notify(bucket, object_keys))


async def _notify(bucket: str, object_keys: list[str]) -> None:
    ensure_main_db_connection()
    entity = BucketEntity.get_bucket_by_bucket_name(bucket)
    if entity.ingestor in {ingestor_type.value for ingestor_type in IngestorType.legacy()}:
        logger.warning(f"No ingestion pipeline consumes events for '{bucket}' (ingestor '{entity.ingestor}'); skipping")
        return
    nc = await NatsSettings.create_client()
    try:
        for object_key in object_keys:
            await SourceUpdatedPublisher.publish(nc, entity, object_key)
    finally:
        await nc.close()
