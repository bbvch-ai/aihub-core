"""E2E tests for swiss_ai_hub.backup — runs against real Docker infrastructure.

Tests exercise backup and restore through Dagster's GraphQL API,
verifying S3 artifacts and data integrity after restore.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import boto3
import docker
import pytest
import requests
from botocore.config import Config as BotoConfig
from dagster import DagsterRunStatus
from dagster_graphql import DagsterGraphQLClient
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DAGSTER_HOST = "127.0.0.1"
DAGSTER_PORT = 3004
BACKUP_CONTAINER = "backup-code"

REPO_ROOT = Path(__file__).resolve().parents[4]
S3_ENDPOINT = "http://127.0.0.1:9000"
MILVUS_API = "http://127.0.0.1:19530/v2/vectordb"

BACKUP_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}/$")


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------
def _load_env() -> dict[str, str | None]:
    """Load .env.dev (or .env) from the repo root."""
    for name in (".env.dev", ".env"):
        path = REPO_ROOT / name
        if path.exists():
            return dotenv_values(str(path))
    pytest.fail("Neither .env.dev nor .env found at repo root")


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------
class BackupResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestamp: str
    run_status: DagsterRunStatus


class RestoreResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_status: DagsterRunStatus


# ---------------------------------------------------------------------------
# Dagster client wrapper
# ---------------------------------------------------------------------------
class _DagsterClient:
    """Thin wrapper around DagsterGraphQLClient for backup/restore jobs."""

    def __init__(self, hostname: str = DAGSTER_HOST, port: int = DAGSTER_PORT) -> None:
        self._client = DagsterGraphQLClient(hostname, port_number=port)

    def submit_backup(self) -> str:
        return self._client.submit_job_execution(job_name="backup_asset_job")

    def submit_full_restore(self, timestamp: str) -> str:
        return self._client.submit_job_execution(
            job_name="full_restore_job",
            tags={"dagster/partition": timestamp},
        )

    def wait_for_run(self, run_id: str, timeout: int = 300) -> DagsterRunStatus:
        deadline = time.monotonic() + timeout
        status = DagsterRunStatus.NOT_STARTED
        while time.monotonic() < deadline:
            status = self._client.get_run_status(run_id)
            if status in (DagsterRunStatus.SUCCESS, DagsterRunStatus.FAILURE, DagsterRunStatus.CANCELED):
                return status
            time.sleep(5)
        raise TimeoutError(f"Run {run_id} did not complete within {timeout}s (last status: {status})")


# ---------------------------------------------------------------------------
# Docker exec helper
# ---------------------------------------------------------------------------
def _exec(client: docker.DockerClient, container: str, cmd: list[str], **kwargs: Any) -> tuple[int, str]:
    """Run a command inside a Docker container, return (exit_code, output)."""
    ctr = client.containers.get(container)
    result = ctr.exec_run(cmd, **kwargs)
    output = result.output.decode() if isinstance(result.output, bytes) else (result.output or "")
    return result.exit_code, output


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------
def _seed_postgres_main(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    sql = (
        "DROP TABLE IF EXISTS e2e_test; "
        "CREATE TABLE e2e_test (id serial PRIMARY KEY, name text, ts timestamp DEFAULT now()); "
        "INSERT INTO e2e_test (name) VALUES ('row1'), ('row2'), ('row3');"
    )
    ec, out = _exec(
        client,
        "postgres",
        ["psql", "-U", env["POSTGRES_USER"] or "admin", "-d", "postgres", "-c", sql],
        environment={"PGPASSWORD": env["POSTGRES_PASSWORD"] or ""},
    )
    assert ec == 0, f"seed postgres-main failed: {out}"


def _seed_postgres_ferretdb(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    sql = (
        "DROP TABLE IF EXISTS e2e_test; "
        "CREATE TABLE e2e_test (id serial PRIMARY KEY, data text); "
        "INSERT INTO e2e_test (data) VALUES ('ferretdb_test_1'), ('ferretdb_test_2');"
    )
    ec, out = _exec(
        client,
        "postgres-ferretdb",
        ["psql", "-U", env["MONGO_USERNAME"] or "admin", "-d", "postgres", "-c", sql],
        environment={"PGPASSWORD": env["MONGO_PASSWORD"] or ""},
    )
    assert ec == 0, f"seed postgres-ferretdb failed: {out}"


def _seed_neo4j(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    """Neo4j bolt takes time to start — retry until ready."""
    cypher = "MERGE (n:E2ETest {id: 1}) SET n.name = 'e2e_backup_test', n.ts = datetime() RETURN n;"
    cmd = ["cypher-shell", "-u", "neo4j", "-p", env["NEO4J_PASSWORD"] or "neo4j", "--non-interactive", cypher]
    for attempt in range(12):
        ec, out = _exec(client, "neo4j", cmd)
        if ec == 0:
            return
        time.sleep(5)
    assert False, f"seed neo4j failed after retries: {out}"


def _seed_clickhouse(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    sql = (
        "DROP TABLE IF EXISTS default.e2e_test; "
        "CREATE TABLE default.e2e_test "
        "(id UInt32, name String, ts DateTime DEFAULT now()) "
        "ENGINE = MergeTree() ORDER BY id; "
        "INSERT INTO default.e2e_test (id, name) VALUES (1, 'ch1'), (2, 'ch2'), (3, 'ch3');"
    )
    ec, out = _exec(
        client,
        "clickhouse",
        [
            "clickhouse-client",
            "--user",
            "clickhouse",
            "--password",
            env["LANGFUSE_CLICKHOUSE_PASSWORD"] or "",
            "--multiquery",
            "--query",
            sql,
        ],
    )
    assert ec == 0, f"seed clickhouse failed: {out}"


def _seed_valkey(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    token = env["REDIS_TOKEN"] or ""
    cmds = [
        ["valkey-cli", "-a", token, "SET", "e2e:key1", "value1"],
        ["valkey-cli", "-a", token, "SET", "e2e:key2", "value2"],
        ["valkey-cli", "-a", token, "HSET", "e2e:hash", "field1", "data1", "field2", "data2"],
    ]
    for cmd in cmds:
        ec, out = _exec(client, "valkey", cmd)
        assert ec == 0, f"seed valkey failed: {out}"


def _seed_nats(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    """Seed NATS by exec-ing into the backup container (has nats CLI)."""
    nats_base = ["nats", "-s", "nats://nats:4222"]
    nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}

    # Delete stream if exists from previous run
    _exec(client, BACKUP_CONTAINER, [*nats_base, "stream", "rm", "E2E_TEST", "-f"], environment=nats_env)

    # Create stream
    ec, out = _exec(
        client,
        BACKUP_CONTAINER,
        [
            *nats_base,
            "stream",
            "add",
            "E2E_TEST",
            "--subjects",
            "e2e.>",
            "--retention",
            "limits",
            "--max-msgs",
            "1000",
            "--max-bytes",
            "1048576",
            "--max-age",
            "1h",
            "--storage",
            "file",
            "--replicas",
            "1",
            "--discard",
            "old",
            "--dupe-window",
            "2m",
            "--defaults",
        ],
        environment=nats_env,
    )
    assert ec == 0, f"seed nats stream create failed: {out}"

    # Publish messages
    for i in range(1, 4):
        ec, out = _exec(
            client,
            BACKUP_CONTAINER,
            [*nats_base, "pub", f"e2e.event{i}", f"message_{i}"],
            environment=nats_env,
        )
        assert ec == 0, f"seed nats pub failed: {out}"


def _seed_mongo(mongo_client: MongoClient) -> None:
    mongo_client.drop_database("e2e_test_db")
    mongo_client["e2e_test_db"]["e2e_collection"].insert_many(
        [{"_id": f"mongo_id_{i}", "name": f"mongo_test_{i}"} for i in range(1, 4)]
    )


def _seed_milvus(env: dict[str, str | None]) -> None:
    """Seed Milvus via REST API (no Docker exec needed)."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer root:{env['MILVUS_ROOT_PASSWORD'] or ''}",
    }

    # Drop collection if exists
    requests.post(
        f"{MILVUS_API}/collections/drop",
        json={"collectionName": "e2e_test"},
        headers=headers,
        timeout=10,
    )

    # Create collection
    resp = requests.post(
        f"{MILVUS_API}/collections/create",
        json={"collectionName": "e2e_test", "dimension": 4, "metricType": "L2"},
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    assert data.get("code") == 0, f"milvus create failed: {data}"

    # Insert vectors
    resp = requests.post(
        f"{MILVUS_API}/entities/insert",
        json={
            "collectionName": "e2e_test",
            "data": [
                {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]},
                {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8]},
                {"id": 3, "vector": [0.9, 1.0, 1.1, 1.2]},
            ],
        },
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    assert data.get("code") == 0, f"milvus insert failed: {data}"


# ---------------------------------------------------------------------------
# Clean functions (destroy seeded test data)
# ---------------------------------------------------------------------------
def _clean_postgres_main(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    ec, out = _exec(
        client,
        "postgres",
        ["psql", "-U", env["POSTGRES_USER"] or "admin", "-d", "postgres", "-c", "DROP TABLE IF EXISTS e2e_test;"],
        environment={"PGPASSWORD": env["POSTGRES_PASSWORD"] or ""},
    )
    assert ec == 0, f"clean postgres-main failed: {out}"


def _clean_postgres_ferretdb(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    ec, out = _exec(
        client,
        "postgres-ferretdb",
        ["psql", "-U", env["MONGO_USERNAME"] or "admin", "-d", "postgres", "-c", "DROP TABLE IF EXISTS e2e_test;"],
        environment={"PGPASSWORD": env["MONGO_PASSWORD"] or ""},
    )
    assert ec == 0, f"clean postgres-ferretdb failed: {out}"


def _clean_neo4j(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    cypher = "MATCH (n:E2ETest) DETACH DELETE n;"
    cmd = ["cypher-shell", "-u", "neo4j", "-p", env["NEO4J_PASSWORD"] or "neo4j", "--non-interactive", cypher]
    for attempt in range(12):
        ec, out = _exec(client, "neo4j", cmd)
        if ec == 0:
            return
        time.sleep(5)
    assert False, f"clean neo4j failed after retries: {out}"


def _clean_clickhouse(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    ec, out = _exec(
        client,
        "clickhouse",
        [
            "clickhouse-client",
            "--user",
            "clickhouse",
            "--password",
            env["LANGFUSE_CLICKHOUSE_PASSWORD"] or "",
            "--query",
            "DROP TABLE IF EXISTS default.e2e_test;",
        ],
    )
    assert ec == 0, f"clean clickhouse failed: {out}"


def _clean_valkey(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    token = env["REDIS_TOKEN"] or ""
    for key in ("e2e:key1", "e2e:key2", "e2e:hash"):
        ec, out = _exec(client, "valkey", ["valkey-cli", "-a", token, "DEL", key])
        assert ec == 0, f"clean valkey failed on {key}: {out}"


def _clean_nats(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}
    ec, out = _exec(
        client,
        BACKUP_CONTAINER,
        ["nats", "-s", "nats://nats:4222", "stream", "rm", "E2E_TEST", "-f"],
        environment=nats_env,
    )
    assert ec == 0, f"clean nats failed: {out}"


def _clean_mongo(mongo_client: MongoClient) -> None:
    mongo_client.drop_database("e2e_test_db")


def _clean_milvus(env: dict[str, str | None]) -> None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer root:{env['MILVUS_ROOT_PASSWORD'] or ''}",
    }
    resp = requests.post(
        f"{MILVUS_API}/collections/drop",
        json={"collectionName": "e2e_test"},
        headers=headers,
        timeout=10,
    )
    data = resp.json()
    assert data.get("code") == 0, f"clean milvus failed: {data}"


# ---------------------------------------------------------------------------
# Absence checks (confirm data is gone after cleaning)
# ---------------------------------------------------------------------------
def _assert_absent_postgres_main(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    ec, _out = _exec(
        client,
        "postgres",
        [
            "psql",
            "-U",
            env["POSTGRES_USER"] or "admin",
            "-d",
            "postgres",
            "-t",
            "-c",
            "SELECT 1 FROM e2e_test LIMIT 1;",
        ],
        environment={"PGPASSWORD": env["POSTGRES_PASSWORD"] or ""},
    )
    assert ec != 0, "e2e_test table still exists in postgres-main after mutation"


def _assert_absent_postgres_ferretdb(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    ec, _out = _exec(
        client,
        "postgres-ferretdb",
        [
            "psql",
            "-U",
            env["MONGO_USERNAME"] or "admin",
            "-d",
            "postgres",
            "-t",
            "-c",
            "SELECT 1 FROM e2e_test LIMIT 1;",
        ],
        environment={"PGPASSWORD": env["MONGO_PASSWORD"] or ""},
    )
    assert ec != 0, "e2e_test table still exists in postgres-ferretdb after mutation"


def _assert_absent_neo4j(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    cypher = "MATCH (n:E2ETest) RETURN count(n) AS c;"
    cmd = ["cypher-shell", "-u", "neo4j", "-p", env["NEO4J_PASSWORD"] or "neo4j", "--non-interactive", cypher]
    for attempt in range(12):
        ec, out = _exec(client, "neo4j", cmd)
        if ec == 0:
            assert "0" in out, f"E2ETest nodes still exist in neo4j after mutation: {out}"
            return
        time.sleep(5)
    assert False, f"neo4j unreachable for absence check: {out}"


def _assert_absent_clickhouse(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    ec, _out = _exec(
        client,
        "clickhouse",
        [
            "clickhouse-client",
            "--user",
            "clickhouse",
            "--password",
            env["LANGFUSE_CLICKHOUSE_PASSWORD"] or "",
            "--query",
            "SELECT 1 FROM default.e2e_test LIMIT 1;",
        ],
    )
    assert ec != 0, "e2e_test table still exists in clickhouse after mutation"


def _assert_absent_valkey(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    token = env["REDIS_TOKEN"] or ""
    for key in ("e2e:key1", "e2e:key2", "e2e:hash"):
        ec, out = _exec(client, "valkey", ["valkey-cli", "-a", token, "EXISTS", key])
        lines = [line for line in out.strip().splitlines() if not line.startswith("Warning:")]
        value = lines[-1].strip() if lines else ""
        assert value == "0", f"valkey key {key} still exists after mutation"


def _assert_absent_nats(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}
    ec, out = _exec(
        client,
        BACKUP_CONTAINER,
        ["nats", "-s", "nats://nats:4222", "stream", "info", "E2E_TEST", "--json"],
        environment=nats_env,
    )
    assert ec != 0, f"E2E_TEST stream still exists in NATS after mutation: {out}"


def _assert_absent_mongo(mongo_client: MongoClient) -> None:
    assert "e2e_test_db" not in mongo_client.list_database_names()


def _assert_absent_milvus(env: dict[str, str | None]) -> None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer root:{env['MILVUS_ROOT_PASSWORD'] or ''}",
    }
    resp = requests.post(
        f"{MILVUS_API}/collections/describe",
        json={"collectionName": "e2e_test"},
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    assert data.get("code") != 0, f"e2e_test collection still exists in milvus after mutation: {data}"


# ---------------------------------------------------------------------------
# Verification functions
# ---------------------------------------------------------------------------
def _verify_postgres_main(client: docker.DockerClient, env: dict[str, str | None]) -> int:
    ec, out = _exec(
        client,
        "postgres",
        ["psql", "-U", env["POSTGRES_USER"] or "admin", "-d", "postgres", "-t", "-c", "SELECT count(*) FROM e2e_test;"],
        environment={"PGPASSWORD": env["POSTGRES_PASSWORD"] or ""},
    )
    assert ec == 0, f"verify postgres-main failed: {out}"
    return int(out.strip())


def _verify_postgres_ferretdb(client: docker.DockerClient, env: dict[str, str | None]) -> list[str]:
    ec, out = _exec(
        client,
        "postgres-ferretdb",
        [
            "psql",
            "-U",
            env["MONGO_USERNAME"] or "admin",
            "-d",
            "postgres",
            "-t",
            "-A",
            "-c",
            "SELECT data FROM e2e_test ORDER BY id;",
        ],
        environment={"PGPASSWORD": env["MONGO_PASSWORD"] or ""},
    )
    assert ec == 0, f"verify postgres-ferretdb failed: {out}"
    return [line.strip() for line in out.strip().splitlines() if line.strip()]


def _verify_neo4j(client: docker.DockerClient, env: dict[str, str | None]) -> str:
    """Neo4j needs time to start after offline restore — retry until bolt is ready."""
    cypher = "MATCH (n:E2ETest {id: 1}) RETURN n.name AS name;"
    cmd = ["cypher-shell", "-u", "neo4j", "-p", env["NEO4J_PASSWORD"] or "neo4j", "--non-interactive", cypher]
    for attempt in range(12):
        ec, out = _exec(client, "neo4j", cmd)
        if ec == 0:
            return out
        time.sleep(5)
    assert False, f"verify neo4j failed after retries: {out}"


def _verify_clickhouse(client: docker.DockerClient, env: dict[str, str | None]) -> int:
    ec, out = _exec(
        client,
        "clickhouse",
        [
            "clickhouse-client",
            "--user",
            "clickhouse",
            "--password",
            env["LANGFUSE_CLICKHOUSE_PASSWORD"] or "",
            "--query",
            "SELECT count() FROM default.e2e_test;",
        ],
    )
    assert ec == 0, f"verify clickhouse failed: {out}"
    return int(out.strip())


def _verify_clickhouse_names(client: docker.DockerClient, env: dict[str, str | None]) -> list[str]:
    ec, out = _exec(
        client,
        "clickhouse",
        [
            "clickhouse-client",
            "--user",
            "clickhouse",
            "--password",
            env["LANGFUSE_CLICKHOUSE_PASSWORD"] or "",
            "--query",
            "SELECT name FROM default.e2e_test ORDER BY id FORMAT TabSeparated;",
        ],
    )
    assert ec == 0, f"verify clickhouse names failed: {out}"
    return [line.strip() for line in out.strip().splitlines() if line.strip()]


def _verify_valkey_strings(client: docker.DockerClient, env: dict[str, str | None]) -> dict[str, str]:
    token = env["REDIS_TOKEN"] or ""
    result: dict[str, str] = {}
    for key in ("e2e:key1", "e2e:key2"):
        ec, out = _exec(client, "valkey", ["valkey-cli", "-a", token, "GET", key])
        assert ec == 0, f"verify valkey GET {key} failed: {out}"
        lines = [line for line in out.strip().splitlines() if not line.startswith("Warning:")]
        result[key] = lines[-1].strip() if lines else ""
    return result


def _verify_valkey_hash(client: docker.DockerClient, env: dict[str, str | None]) -> dict[str, str]:
    token = env["REDIS_TOKEN"] or ""
    ec, out = _exec(client, "valkey", ["valkey-cli", "-a", token, "HGETALL", "e2e:hash"])
    assert ec == 0, f"verify valkey hash failed: {out}"
    lines = [line for line in out.strip().splitlines() if not line.startswith("Warning:")]
    it = iter(lines)
    return {k.strip(): v.strip() for k, v in zip(it, it)}


def _verify_nats_streams(client: docker.DockerClient, env: dict[str, str | None]) -> list[str]:
    """Return list of NATS stream names via exec into backup container."""
    nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}
    ec, out = _exec(
        client,
        BACKUP_CONTAINER,
        ["nats", "-s", "nats://nats:4222", "stream", "list", "--names"],
        environment=nats_env,
    )
    assert ec == 0, f"verify nats failed: {out}"
    return [s.strip() for s in out.strip().split("\n") if s.strip()]


def _verify_nats_message_count(client: docker.DockerClient, env: dict[str, str | None], stream_name: str) -> int:
    nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}
    ec, out = _exec(
        client,
        BACKUP_CONTAINER,
        ["nats", "-s", "nats://nats:4222", "stream", "info", stream_name, "--json"],
        environment=nats_env,
    )
    assert ec == 0, f"nats stream info failed: {out}"
    info = json.loads(out)
    return int(info["state"]["messages"])


def _verify_mongo(mongo_client: MongoClient) -> list[dict[str, Any]]:
    """FerretDB needs time to reconnect to PostgreSQL after container restart — retry."""
    for _ in range(24):
        try:
            docs = list(mongo_client["e2e_test_db"]["e2e_collection"].find().sort("_id"))
            if docs:
                return docs
        except Exception:
            pass
        time.sleep(5)
    return list(mongo_client["e2e_test_db"]["e2e_collection"].find().sort("_id"))


def _verify_milvus(env: dict[str, str | None]) -> tuple[int, list[int]]:
    """Load collection and query vectors. Returns (count, sorted_ids)."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer root:{env['MILVUS_ROOT_PASSWORD'] or ''}",
    }

    # Load collection (required after restore)
    requests.post(
        f"{MILVUS_API}/collections/load",
        json={"collectionName": "e2e_test"},
        headers=headers,
        timeout=30,
    )
    time.sleep(3)

    resp = requests.post(
        f"{MILVUS_API}/entities/query",
        json={"collectionName": "e2e_test", "filter": "", "limit": 10, "outputFields": ["vector"]},
        headers=headers,
        timeout=15,
    )
    data = resp.json()
    assert data.get("code") == 0, f"milvus query failed: {data}"
    entities = data.get("data", [])
    ids = sorted(e["id"] for e in entities)
    return len(entities), ids


# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------
def _find_latest_prefix(s3_client: Any, bucket: str) -> str:
    """Find the latest backup prefix."""
    paginator = s3_client.get_paginator("list_objects_v2")
    prefixes: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            prefixes.append(cp["Prefix"])

    matching = sorted([p for p in prefixes if BACKUP_PREFIX_RE.match(p)])
    assert matching, f"No backup prefix found among: {prefixes}"
    return matching[-1].rstrip("/")


def _s3_key_exists(s3_client: Any, bucket: str, key: str) -> bool:
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def _s3_prefix_has_objects(s3_client: Any, bucket: str, prefix: str) -> bool:
    resp = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
    return bool(resp.get("KeyCount", 0) > 0)


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------
def _cleanup_seed_data(client: docker.DockerClient, env: dict[str, str | None], mongo_client: MongoClient) -> None:
    """Best-effort cleanup of seeded test data."""
    cleaners: list[tuple[Callable[..., None], tuple[Any, ...]]] = [
        (_clean_postgres_main, (client, env)),
        (_clean_postgres_ferretdb, (client, env)),
        (_clean_mongo, (mongo_client,)),
        (_clean_neo4j, (client, env)),
        (_clean_clickhouse, (client, env)),
        (_clean_valkey, (client, env)),
        (_clean_nats, (client, env)),
        (_clean_milvus, (env,)),
    ]
    for fn, args in cleaners:
        try:
            fn(*args)
        except Exception:
            logging.debug("Cleanup failed for %s", fn.__name__, exc_info=True)


# ===========================================================================
# Fixtures (module-scoped)
# ===========================================================================
@pytest.fixture(scope="module")
def env() -> dict[str, str | None]:
    return _load_env()


@pytest.fixture(scope="module")
def docker_client() -> docker.DockerClient:
    return docker.from_env()


@pytest.fixture(scope="module")
def dagster_client() -> _DagsterClient:
    return _DagsterClient()


@pytest.fixture(scope="module")
def mongo_client(env: dict[str, str | None]) -> Generator[MongoClient]:
    client: MongoClient = MongoClient(
        host="127.0.0.1",
        port=27017,
        username=env["MONGO_USERNAME"] or "admin",
        password=env["MONGO_PASSWORD"] or "",
    )
    yield client
    client.close()


@pytest.fixture(scope="module")
def s3_client(env: dict[str, str | None]) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=env["S3_STORAGE_ACCESS_KEY"] or "admin",
        aws_secret_access_key=env["S3_STORAGE_SECRET_KEY"] or "",
        config=BotoConfig(signature_version="s3v4"),
    )


@pytest.fixture(scope="module")
def s3_bucket() -> str:
    return "backups"


_DATA_CONTAINERS = ("postgres", "postgres-ferretdb", "ferretdb", "neo4j", "clickhouse", "valkey", "nats", "milvus")


def _ensure_containers_running(client: docker.DockerClient) -> None:
    """Start and wait for all data containers — previous test runs may have left them stopped."""
    for name in _DATA_CONTAINERS:
        ctr = client.containers.get(name)
        if ctr.status != "running":
            ctr.start()
    for name in _DATA_CONTAINERS:
        ctr = client.containers.get(name)
        ctr.reload()
        for _ in range(30):
            if ctr.status == "running":
                break
            time.sleep(2)
            ctr.reload()
        assert ctr.status == "running", f"{name} failed to start"


@pytest.fixture(scope="module")
def seeded_services(
    docker_client: docker.DockerClient,
    env: dict[str, str | None],
    mongo_client: MongoClient,
) -> Generator[None]:
    """Seed test data into all 8 services, clean up after module."""
    _ensure_containers_running(docker_client)
    _seed_postgres_main(docker_client, env)
    _seed_postgres_ferretdb(docker_client, env)
    _seed_mongo(mongo_client)
    _seed_neo4j(docker_client, env)
    _seed_clickhouse(docker_client, env)
    _seed_valkey(docker_client, env)
    _seed_nats(docker_client, env)
    _seed_milvus(env)
    yield
    _cleanup_seed_data(docker_client, env, mongo_client)


@pytest.fixture(scope="module")
def backup(
    seeded_services: None,
    dagster_client: _DagsterClient,
    s3_client: Any,
    s3_bucket: str,
) -> BackupResult:
    """Submit a backup via Dagster and wait for completion."""
    run_id = dagster_client.submit_backup()
    status = dagster_client.wait_for_run(run_id, timeout=600)
    timestamp = _find_latest_prefix(s3_client, s3_bucket)
    return BackupResult(timestamp=timestamp, run_status=status)


@pytest.fixture(scope="module")
def mutated_services(
    backup: BackupResult,
    docker_client: docker.DockerClient,
    env: dict[str, str | None],
    mongo_client: MongoClient,
) -> None:
    """Destroy seeded data after backup — proves restore overwrites, not a no-op."""
    _clean_postgres_main(docker_client, env)
    _clean_postgres_ferretdb(docker_client, env)
    _clean_mongo(mongo_client)
    _clean_neo4j(docker_client, env)
    _clean_clickhouse(docker_client, env)
    _clean_valkey(docker_client, env)
    _clean_nats(docker_client, env)
    _clean_milvus(env)

    _assert_absent_postgres_main(docker_client, env)
    _assert_absent_postgres_ferretdb(docker_client, env)
    _assert_absent_mongo(mongo_client)
    _assert_absent_neo4j(docker_client, env)
    _assert_absent_clickhouse(docker_client, env)
    _assert_absent_valkey(docker_client, env)
    _assert_absent_nats(docker_client, env)
    _assert_absent_milvus(env)


@pytest.fixture(scope="module")
def full_restore(
    backup: BackupResult,
    mutated_services: None,
    dagster_client: _DagsterClient,
) -> RestoreResult:
    """Submit a full restore from the backup and wait for completion."""
    run_id = dagster_client.submit_full_restore(backup.timestamp)
    status = dagster_client.wait_for_run(run_id, timeout=900)
    return RestoreResult(run_status=status)


# ===========================================================================
# Precondition tests (before backup)
# ===========================================================================
class TestPreconditions:
    def test_containers_running_before_backup(
        self,
        seeded_services: None,
        docker_client: docker.DockerClient,
    ) -> None:
        """All data containers must be running before the backup job starts."""
        for name in _DATA_CONTAINERS:
            ctr = docker_client.containers.get(name)
            assert ctr.status == "running", f"{name} not running before backup: {ctr.status}"


# ===========================================================================
# Backup tests
# ===========================================================================
class TestBackup:
    def test_backup_succeeds(self, backup: BackupResult) -> None:
        assert backup.run_status == DagsterRunStatus.SUCCESS

    def test_s3_postgres_main(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{backup.timestamp}/postgres-main/globals.sql.gz")

    def test_s3_postgres_ferretdb(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{backup.timestamp}/postgres-ferretdb/globals.sql.gz")

    def test_s3_neo4j(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{backup.timestamp}/neo4j.dump")

    def test_s3_clickhouse(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_prefix_has_objects(s3_client, s3_bucket, f"{backup.timestamp}/clickhouse/backup_")

    def test_s3_valkey(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{backup.timestamp}/valkey.rdb")

    def test_s3_nats(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{backup.timestamp}/nats-jetstream.tar.gz")

    def test_s3_milvus(self, backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_prefix_has_objects(s3_client, s3_bucket, f"{backup.timestamp}/milvus_backup_")

    def test_containers_running_after_backup(
        self,
        backup: BackupResult,
        docker_client: docker.DockerClient,
    ) -> None:
        """Successful backup restarts all previously-running containers via backup_finalize."""
        for name in _DATA_CONTAINERS:
            ctr = docker_client.containers.get(name)
            assert ctr.status == "running", f"{name} not running after backup: {ctr.status}"


# ===========================================================================
# Full restore + data verification tests
# ===========================================================================
class TestFullRestore:
    def test_full_restore_succeeds(self, full_restore: RestoreResult) -> None:
        assert full_restore.run_status == DagsterRunStatus.SUCCESS

    def test_postgres_data_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        count = _verify_postgres_main(docker_client, env)
        assert count == 3

    def test_postgres_ferretdb_data_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        rows = _verify_postgres_ferretdb(docker_client, env)
        assert rows == ["ferretdb_test_1", "ferretdb_test_2"]

    def test_mongo_data_after_restore(
        self,
        full_restore: RestoreResult,
        mongo_client: MongoClient,
    ) -> None:
        docs = _verify_mongo(mongo_client)
        assert len(docs) == 3
        assert [d["name"] for d in docs] == ["mongo_test_1", "mongo_test_2", "mongo_test_3"]

    def test_neo4j_data_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        output = _verify_neo4j(docker_client, env)
        assert "e2e_backup_test" in output

    def test_clickhouse_data_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        count = _verify_clickhouse(docker_client, env)
        assert count == 3
        names = _verify_clickhouse_names(docker_client, env)
        assert names == ["ch1", "ch2", "ch3"]

    def test_valkey_data_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        strings = _verify_valkey_strings(docker_client, env)
        assert strings == {"e2e:key1": "value1", "e2e:key2": "value2"}
        hash_data = _verify_valkey_hash(docker_client, env)
        assert hash_data == {"field1": "data1", "field2": "data2"}

    def test_nats_streams_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        streams = _verify_nats_streams(docker_client, env)
        assert "E2E_TEST" in streams
        count = _verify_nats_message_count(docker_client, env, "E2E_TEST")
        assert count == 3

    def test_milvus_data_after_restore(
        self,
        full_restore: RestoreResult,
        env: dict[str, str | None],
    ) -> None:
        count, ids = _verify_milvus(env)
        assert count == 3
        assert ids == [1, 2, 3]

    def test_containers_running_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
    ) -> None:
        """Successful restore restarts all containers via restore_finalize."""
        for name in _DATA_CONTAINERS:
            ctr = docker_client.containers.get(name)
            assert ctr.status == "running", f"{name} not running after restore: {ctr.status}"
