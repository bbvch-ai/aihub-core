"""E2E tests for aihub_backup — runs against real Docker infrastructure.

Tests exercise backup and restore through Dagster's GraphQL API,
verifying S3 artifacts and data integrity after restore.

Auto-skips when Dagster is not reachable (no Docker stack running).
"""

from __future__ import annotations

import re
import time
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

import boto3
import docker
import pytest
import requests
from botocore.config import Config as BotoConfig
from dagster import DagsterRunStatus, RunConfig
from dagster_graphql import DagsterGraphQLClient
from dotenv import dotenv_values

from aihub_backup.dagster.config import BackupConfig, RestoreConfig, SingleServiceRestoreConfig
from aihub_backup.models import BACKUP_SERVICES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DAGSTER_HOST = "localhost"
DAGSTER_PORT = 3004
S3_ENDPOINT = "http://localhost:9000"
MILVUS_API = "http://localhost:19530/v2/vectordb"

BACKUP_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_(online|offline)/$")


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


def _dagster_available() -> bool:
    try:
        resp = requests.get(f"http://{DAGSTER_HOST}:{DAGSTER_PORT}/server_info", timeout=5)
        return resp.ok
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _dagster_available(),
    reason="Dagster not reachable — start Docker stack first",
)


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

    def submit_backup(self, mode: Literal["online", "offline"] = "online") -> str:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        return self._client.submit_job_execution(
            job_name="backup_asset_job",
            run_config=RunConfig(ops={"create_backup": BackupConfig(mode=mode)}),
            tags={"dagster/partition": today},
        )

    def submit_full_restore(self, timestamp: str, force: bool = True) -> str:
        return self._client.submit_job_execution(
            job_name="full_restore_job",
            run_config=RunConfig(ops={"run_full_restore": RestoreConfig(timestamp=timestamp, force=force)}),
        )

    def submit_single_restore(self, service_name: str, timestamp: str) -> str:
        return self._client.submit_job_execution(
            job_name="single_service_restore_job",
            run_config=RunConfig(
                ops={
                    "run_single_service_restore": SingleServiceRestoreConfig(
                        service_name=service_name,  # type: ignore[arg-type]  # runtime-validated Literal
                        timestamp=timestamp,
                    )
                }
            ),
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
    cypher = "MERGE (n:E2ETest {id: 1}) SET n.name = 'e2e_backup_test', n.ts = datetime() RETURN n;"
    ec, out = _exec(
        client,
        "neo4j",
        ["cypher-shell", "-u", "neo4j", "-p", env["NEO4J_PASSWORD"] or "neo4j", "--non-interactive", cypher],
    )
    assert ec == 0, f"seed neo4j failed: {out}"


def _seed_clickhouse(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    sql = (
        "CREATE TABLE IF NOT EXISTS default.e2e_test "
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
    _exec(client, "backup", [*nats_base, "stream", "rm", "E2E_TEST", "-f"], environment=nats_env)

    # Create stream
    ec, out = _exec(
        client,
        "backup",
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
            "backup",
            [*nats_base, "pub", f"e2e.event{i}", f"message_{i}"],
            environment=nats_env,
        )
        assert ec == 0, f"seed nats pub failed: {out}"


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


def _verify_neo4j(client: docker.DockerClient, env: dict[str, str | None]) -> str:
    cypher = "MATCH (n:E2ETest {id: 1}) RETURN n.name AS name;"
    ec, out = _exec(
        client,
        "neo4j",
        ["cypher-shell", "-u", "neo4j", "-p", env["NEO4J_PASSWORD"] or "neo4j", "--non-interactive", cypher],
    )
    assert ec == 0, f"verify neo4j failed: {out}"
    return out


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


def _verify_valkey(client: docker.DockerClient, env: dict[str, str | None]) -> str:
    token = env["REDIS_TOKEN"] or ""
    ec, out = _exec(client, "valkey", ["valkey-cli", "-a", token, "GET", "e2e:key1"])
    assert ec == 0, f"verify valkey failed: {out}"
    return out.strip()


def _verify_nats_streams(client: docker.DockerClient, env: dict[str, str | None]) -> list[str]:
    """Return list of NATS stream names via exec into backup container."""
    nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}
    ec, out = _exec(
        client,
        "backup",
        ["nats", "-s", "nats://nats:4222", "stream", "list", "--names"],
        environment=nats_env,
    )
    assert ec == 0, f"verify nats failed: {out}"
    return [s.strip() for s in out.strip().split("\n") if s.strip()]


def _verify_milvus(env: dict[str, str | None]) -> int:
    """Load collection and query vectors. Returns count."""
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
    return len(data.get("data", []))


# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------
def _find_latest_prefix(s3_client: Any, bucket: str, mode: str) -> str:
    """Find the latest backup prefix matching the given mode."""
    paginator = s3_client.get_paginator("list_objects_v2")
    prefixes: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            prefixes.append(cp["Prefix"])

    pattern = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}_{mode}/$")
    matching = sorted([p for p in prefixes if pattern.match(p)])
    assert matching, f"No S3 prefix found for mode={mode} among: {prefixes}"
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
def _cleanup_seed_data(client: docker.DockerClient, env: dict[str, str | None]) -> None:
    """Best-effort cleanup of seeded test data."""
    try:
        _exec(
            client,
            "postgres",
            ["psql", "-U", env["POSTGRES_USER"] or "admin", "-d", "postgres", "-c", "DROP TABLE IF EXISTS e2e_test;"],
            environment={"PGPASSWORD": env["POSTGRES_PASSWORD"] or ""},
        )
    except Exception:
        pass

    try:
        _exec(
            client,
            "postgres-ferretdb",
            ["psql", "-U", env["MONGO_USERNAME"] or "admin", "-d", "postgres", "-c", "DROP TABLE IF EXISTS e2e_test;"],
            environment={"PGPASSWORD": env["MONGO_PASSWORD"] or ""},
        )
    except Exception:
        pass

    try:
        _exec(
            client,
            "neo4j",
            [
                "cypher-shell",
                "-u",
                "neo4j",
                "-p",
                env["NEO4J_PASSWORD"] or "neo4j",
                "--non-interactive",
                "MATCH (n:E2ETest) DELETE n;",
            ],
        )
    except Exception:
        pass

    try:
        _exec(
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
    except Exception:
        pass

    try:
        token = env["REDIS_TOKEN"] or ""
        for key in ("e2e:key1", "e2e:key2", "e2e:hash"):
            _exec(client, "valkey", ["valkey-cli", "-a", token, "DEL", key])
    except Exception:
        pass

    try:
        nats_env = {"NATS_TOKEN": env["NATS_TOKEN"] or ""}
        _exec(
            client,
            "backup",
            ["nats", "-s", "nats://nats:4222", "stream", "rm", "E2E_TEST", "-f"],
            environment=nats_env,
        )
    except Exception:
        pass

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer root:{env['MILVUS_ROOT_PASSWORD'] or ''}",
        }
        requests.post(
            f"{MILVUS_API}/collections/drop",
            json={"collectionName": "e2e_test"},
            headers=headers,
            timeout=10,
        )
    except Exception:
        pass


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


@pytest.fixture(scope="module")
def seeded_services(
    docker_client: docker.DockerClient,
    env: dict[str, str | None],
) -> Generator[None]:
    """Seed test data into all 7 services, clean up after module."""
    _seed_postgres_main(docker_client, env)
    _seed_postgres_ferretdb(docker_client, env)
    _seed_neo4j(docker_client, env)
    _seed_clickhouse(docker_client, env)
    _seed_valkey(docker_client, env)
    _seed_nats(docker_client, env)
    _seed_milvus(env)
    yield
    _cleanup_seed_data(docker_client, env)


@pytest.fixture(scope="module")
def online_backup(
    seeded_services: None,
    dagster_client: _DagsterClient,
    s3_client: Any,
    s3_bucket: str,
) -> BackupResult:
    """Submit an online backup via Dagster and wait for completion."""
    run_id = dagster_client.submit_backup(mode="online")
    status = dagster_client.wait_for_run(run_id, timeout=300)
    timestamp = _find_latest_prefix(s3_client, s3_bucket, "online")
    return BackupResult(timestamp=timestamp, run_status=status)


@pytest.fixture(scope="module")
def offline_backup(
    seeded_services: None,
    dagster_client: _DagsterClient,
    s3_client: Any,
    s3_bucket: str,
) -> BackupResult:
    """Submit an offline backup via Dagster and wait for completion."""
    run_id = dagster_client.submit_backup(mode="offline")
    status = dagster_client.wait_for_run(run_id, timeout=300)
    timestamp = _find_latest_prefix(s3_client, s3_bucket, "offline")
    return BackupResult(timestamp=timestamp, run_status=status)


@pytest.fixture(scope="module")
def per_service_restores(
    online_backup: BackupResult,
    dagster_client: _DagsterClient,
) -> dict[str, DagsterRunStatus]:
    """Submit single-service restores for all services from the online backup."""
    results: dict[str, DagsterRunStatus] = {}
    for service_name in BACKUP_SERVICES:
        run_id = dagster_client.submit_single_restore(service_name, online_backup.timestamp)
        status = dagster_client.wait_for_run(run_id, timeout=300)
        results[service_name] = status
    return results


@pytest.fixture(scope="module")
def full_restore(
    online_backup: BackupResult,
    dagster_client: _DagsterClient,
) -> RestoreResult:
    """Submit a full restore from the online backup and wait for completion."""
    run_id = dagster_client.submit_full_restore(online_backup.timestamp, force=True)
    status = dagster_client.wait_for_run(run_id, timeout=300)
    return RestoreResult(run_status=status)


# ===========================================================================
# Online backup tests
# ===========================================================================
class TestOnlineBackup:
    def test_online_backup_succeeds(self, online_backup: BackupResult) -> None:
        assert online_backup.run_status == DagsterRunStatus.SUCCESS

    def test_online_s3_postgres_main(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{online_backup.timestamp}/postgres-main.sql.gz")

    def test_online_s3_postgres_ferretdb(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{online_backup.timestamp}/postgres-ferretdb.sql.gz")

    def test_online_s3_neo4j(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{online_backup.timestamp}/neo4j.dump")

    def test_online_s3_clickhouse(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{online_backup.timestamp}/clickhouse.tar.gz")

    def test_online_s3_valkey(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{online_backup.timestamp}/valkey.rdb")

    def test_online_s3_nats(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_key_exists(s3_client, s3_bucket, f"{online_backup.timestamp}/nats-jetstream.tar.gz")

    def test_online_s3_milvus(self, online_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        assert _s3_prefix_has_objects(s3_client, s3_bucket, f"{online_backup.timestamp}/milvus_backup_")


# ===========================================================================
# Offline backup tests
# ===========================================================================
class TestOfflineBackup:
    def test_offline_backup_succeeds(self, offline_backup: BackupResult) -> None:
        assert offline_backup.run_status == DagsterRunStatus.SUCCESS

    def test_offline_s3_artifacts_exist(self, offline_backup: BackupResult, s3_client: Any, s3_bucket: str) -> None:
        expected_keys = [
            f"{offline_backup.timestamp}/postgres-main.sql.gz",
            f"{offline_backup.timestamp}/postgres-ferretdb.sql.gz",
            f"{offline_backup.timestamp}/neo4j.dump",
            f"{offline_backup.timestamp}/clickhouse.tar.gz",
            f"{offline_backup.timestamp}/valkey.rdb",
            f"{offline_backup.timestamp}/nats-jetstream.tar.gz",
        ]
        for key in expected_keys:
            assert _s3_key_exists(s3_client, s3_bucket, key), f"Missing offline artifact: {key}"
        assert _s3_prefix_has_objects(
            s3_client, s3_bucket, f"{offline_backup.timestamp}/milvus_backup_"
        ), "Missing offline milvus backup"


# ===========================================================================
# Individual service restore tests
# ===========================================================================
class TestPerServiceRestore:
    def test_restore_postgresql_succeeds(self, per_service_restores: dict[str, DagsterRunStatus]) -> None:
        assert per_service_restores["PostgreSQL"] == DagsterRunStatus.SUCCESS

    def test_restore_milvus_succeeds(self, per_service_restores: dict[str, DagsterRunStatus]) -> None:
        assert per_service_restores["Milvus"] == DagsterRunStatus.SUCCESS

    def test_restore_neo4j_succeeds(self, per_service_restores: dict[str, DagsterRunStatus]) -> None:
        assert per_service_restores["Neo4j"] == DagsterRunStatus.SUCCESS

    def test_restore_clickhouse_succeeds(self, per_service_restores: dict[str, DagsterRunStatus]) -> None:
        assert per_service_restores["ClickHouse"] == DagsterRunStatus.SUCCESS

    def test_restore_valkey_succeeds(self, per_service_restores: dict[str, DagsterRunStatus]) -> None:
        assert per_service_restores["Valkey"] == DagsterRunStatus.SUCCESS

    def test_restore_nats_succeeds(self, per_service_restores: dict[str, DagsterRunStatus]) -> None:
        assert per_service_restores["NATS"] == DagsterRunStatus.SUCCESS


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
        assert count >= 3

    def test_valkey_data_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        value = _verify_valkey(docker_client, env)
        assert value == "value1"

    def test_nats_streams_after_restore(
        self,
        full_restore: RestoreResult,
        docker_client: docker.DockerClient,
        env: dict[str, str | None],
    ) -> None:
        streams = _verify_nats_streams(docker_client, env)
        assert "E2E_TEST" in streams

    def test_milvus_data_after_restore(
        self,
        full_restore: RestoreResult,
        env: dict[str, str | None],
    ) -> None:
        count = _verify_milvus(env)
        assert count >= 3
