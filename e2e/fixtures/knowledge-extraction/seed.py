"""S3: put the corpus into the data lake and trigger ingestion.

Every file goes to S3 directly, followed by the SourceUpdatedEvent an rclone sync would publish.
Usage: seed.py [collection path ...] to (re)seed only some files; no arguments seeds everything.
"""

import asyncio
import mimetypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import COLLECTIONS, CORPUS, connect_like_an_agent, object_key, s3, seeded

SEEDED = seeded()

from swiss_ai_hub.core.infrastructure.nats.nats_settings import NatsSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.publishers.source_updated_publisher import SourceUpdatedPublisher

CONTENT_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def content_type(path: str) -> str:
    return CONTENT_TYPES.get(Path(path).suffix.lower()) or mimetypes.guess_type(path)[0] or "application/octet-stream"


async def put_and_notify(files: list[tuple[str, str]]) -> None:
    connect_like_an_agent()
    nc = await NatsSettings.create_client()
    client = s3()
    try:
        for collection, path in files:
            bucket = BucketEntity.get_bucket_by_bucket_name(COLLECTIONS[collection][0])
            key = object_key(collection, path)
            client.put_object(
                Bucket=bucket.bucket_name,
                Key=key,
                Body=(CORPUS / collection / path).read_bytes(),
                ContentType=content_type(path),
            )
            await SourceUpdatedPublisher.publish(nc, bucket, key)
            print("put + notified", bucket.bucket_name, key)
    finally:
        await nc.close()


def main() -> None:
    requested = list(zip(sys.argv[1::2], sys.argv[2::2], strict=True))
    asyncio.run(put_and_notify(requested or [(c, p) for c, paths in SEEDED.items() for p in paths]))


if __name__ == "__main__":
    main()
