"""Poll the doc stores until every seeded source is ingested. Usage: wait_ingested.py [timeout_seconds] [collection path ...]"""

import os
import sys
import time
from pathlib import Path

from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).parent))
from common import COLLECTIONS, seeded, source  # noqa: E402
SEEDED = seeded()
API_UPLOADED: dict[str, list[str]] = {}


def main() -> None:
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 2400
    requested = list(zip(sys.argv[2::2], sys.argv[3::2], strict=True))
    expected = requested or [(c, p) for group in (SEEDED, API_UPLOADED) for c, paths in group.items() for p in paths]
    client = MongoClient(os.environ["MONGO_CONNECTION_STRING"])
    started = time.monotonic()
    done_at: dict[tuple[str, str], float] = {}
    while True:
        for collection, path in expected:
            if (collection, path) in done_at:
                continue
            row = client[COLLECTIONS[collection][0]]["documents-data"].find_one(
                {"__data__.metadata.source": source(collection, path)},
                {"__data__.metadata.is_ingested": 1, "__type__": 1},
            )
            if row and row["__type__"] != "placeholder" and row["__data__"]["metadata"].get("is_ingested") is not False:
                done_at[(collection, path)] = time.monotonic() - started
                print(f"[{done_at[(collection, path)]:7.0f}s] ingested {collection}/{path}", flush=True)
        if len(done_at) == len(expected):
            print(f"all {len(expected)} ingested after {time.monotonic() - started:.0f}s")
            return
        if time.monotonic() - started > timeout:
            missing = [f"{c}/{p}" for c, p in expected if (c, p) not in done_at]
            print("TIMEOUT, still pending:", missing)
            sys.exit(1)
        time.sleep(15)


if __name__ == "__main__":
    main()
