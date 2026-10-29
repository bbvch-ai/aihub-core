"""Seed the semantic-discovery archive into collection `semantic` of kxe2e. Usage: seed_semantic.py setup|seed|wait

Run from the repository root with `.env` loaded, after `setup_knowledge.py` created kxe2e.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DB_MAIN, api, connect_like_an_agent, s3  # noqa: E402
from semantic_corpus import DOCUMENTS  # noqa: E402

NAMESPACE = "semantic"


def setup() -> None:
    with api() as client:
        response = client.post(
            f"/knowledge/databases/{DB_MAIN}/namespaces/{NAMESPACE}",
            json={"folder_name": NAMESPACE, "display_name": "semantic (archive with neutral file names)"},
        )
        print(response.status_code, response.text[:300])


async def seed() -> None:
    from swiss_ai_hub.core.infrastructure.nats.nats_settings import NatsSettings
    from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
    from swiss_ai_hub.core.publishers.source_updated_publisher import SourceUpdatedPublisher

    connect_like_an_agent()
    nats = await NatsSettings.create_client()
    bucket = BucketEntity.get_bucket_by_bucket_name(DB_MAIN)
    client = s3()
    try:
        for path, text in DOCUMENTS.items():
            key = f"{NAMESPACE}/{path}"
            client.put_object(
                Bucket=bucket.bucket_name, Key=key, Body=text.encode("utf-8"), ContentType="text/markdown"
            )
            await SourceUpdatedPublisher.publish(nats, bucket, key)
            print("put + notified", key, flush=True)
    finally:
        await nats.close()


def wait(timeout: int = 1800) -> None:
    store = MongoClient(os.environ["MONGO_CONNECTION_STRING"])[DB_MAIN]["documents-data"]
    started, pending = time.monotonic(), set(DOCUMENTS)
    while pending:
        for path in sorted(pending):
            row = store.find_one(
                {"__data__.metadata.source": f"s3://{DB_MAIN}/{NAMESPACE}/{path}"},
                {"__data__.metadata.is_ingested": 1, "__type__": 1},
            )
            if row and row["__type__"] != "placeholder" and row["__data__"]["metadata"].get("is_ingested") is not False:
                pending.discard(path)
                print(f"[{time.monotonic() - started:5.0f}s] ingested {path}", flush=True)
        if pending and time.monotonic() - started > timeout:
            sys.exit(f"TIMEOUT, pending: {sorted(pending)}")
        if pending:
            time.sleep(10)
    print(f"all {len(DOCUMENTS)} ingested after {time.monotonic() - started:.0f}s")


if __name__ == "__main__":
    match sys.argv[1]:
        case "setup":
            setup()
        case "seed":
            asyncio.run(seed())
        case "wait":
            wait()
