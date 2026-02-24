import logging
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from aihub_backup.docker_client import DockerManager
from aihub_backup.models import (
    BACKUP_SERVICES,
    TIMESTAMP_FORMAT,
    BackupEntry,
    BackupMode,
    BackupSummary,
    ServiceResult,
    ServiceStatus,
)
from aihub_backup.retention import run_retention
from aihub_backup.s3 import BACKUP_PREFIX_RE, S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

# Container stop/start order for restore
#
# Stop order: apps → infra consumers → databases (top-down dependency order).
# Start order: databases → infra consumers → apps (bottom-up, each tier waits
# for health before the next starts).
#
# APP_CONTAINERS: user-facing services and background workers that depend on
# infrastructure. Stopped first so they don't produce writes during restore.
#
# INFRA_CONSUMERS: services that sit between apps and databases (FerretDB wraps
# Postgres, Neo4j/ClickHouse/Valkey/NATS/Milvus are data stores restored
# individually). Stopped after apps to drain in-flight work.
#
# DATABASE_CONTAINERS: the two PostgreSQL instances that underpin FerretDB and
# Langfuse. Stopped last, started first.
#
# START_ORDER_APPS uses a dependency-aware order: LiteLLM and Langfuse first
# (other services depend on them), then API/Dagster, then agents, then
# frontends and optional tools.
#
# IMPORTANT: If you add, remove, or rename a Docker Compose service,
# update the relevant tuples below to keep them in sync.

APP_CONTAINERS: tuple[str, ...] = (
    "api",
    "web",
    "bot",
    "openwebui",
    "dagster",
    "dagster-webserver",
    "dagster-daemon",
    "litellm",
    "litellm-guardrails",
    "llm-wrapping-agent",
    "rag-agent",
    "expert-rag-agent",
    "expert-asking-agent",
    "retrieval-agent",
    "few-shot-agent",
    "namespace-selection-agent",
    "default-rag-pipeline",
    "shared-rag-pipeline",
    "langfuse-web",
    "langfuse-worker",
    "rclone",
    "attu",
    "jupyter",
)

INFRA_CONSUMERS: tuple[str, ...] = ("ferretdb", "neo4j", "clickhouse", "nats", "valkey", "milvus")

DATABASE_CONTAINERS: tuple[str, ...] = ("postgres", "postgres-ferretdb")

START_ORDER_INFRA: tuple[str, ...] = ("postgres", "postgres-ferretdb")
START_ORDER_SERVICES: tuple[str, ...] = ("ferretdb", "neo4j", "milvus", "clickhouse", "valkey", "nats")
START_ORDER_APPS: tuple[str, ...] = (
    "litellm",
    "litellm-guardrails",
    "langfuse-web",
    "langfuse-worker",
    "api",
    "dagster",
    "dagster-webserver",
    "dagster-daemon",
    "llm-wrapping-agent",
    "rag-agent",
    "expert-rag-agent",
    "expert-asking-agent",
    "retrieval-agent",
    "few-shot-agent",
    "namespace-selection-agent",
    "default-rag-pipeline",
    "shared-rag-pipeline",
    "web",
    "bot",
    "openwebui",
    "rclone",
    "attu",
    "jupyter",
)

assert set(APP_CONTAINERS) == set(START_ORDER_APPS), (
    f"APP_CONTAINERS and START_ORDER_APPS must contain the same entries: "
    f"only in APP_CONTAINERS={set(APP_CONTAINERS) - set(START_ORDER_APPS)}, "
    f"only in START_ORDER_APPS={set(START_ORDER_APPS) - set(APP_CONTAINERS)}"
)
assert set(INFRA_CONSUMERS) == set(START_ORDER_SERVICES), (
    f"INFRA_CONSUMERS and START_ORDER_SERVICES must contain the same entries: "
    f"only in INFRA_CONSUMERS={set(INFRA_CONSUMERS) - set(START_ORDER_SERVICES)}, "
    f"only in START_ORDER_SERVICES={set(START_ORDER_SERVICES) - set(INFRA_CONSUMERS)}"
)

# Per-service restore configuration: which containers to start before restore,
# stop after restore, and how long to wait for health checks.
# (start_before, stop_after, start_timeout)
RESTORE_STEPS: dict[str, tuple[Sequence[str] | None, Sequence[str] | None, int]] = {
    "PostgreSQL": (["postgres", "postgres-ferretdb"], ["postgres", "postgres-ferretdb"], 60),
    "Neo4j": (None, None, 0),
    "ClickHouse": (["clickhouse"], ["clickhouse"], 60),
    "Valkey": (None, None, 0),
    "NATS": (["nats"], ["nats"], 60),
    "Milvus": (["milvus"], ["milvus"], 180),
}

assert set(RESTORE_STEPS.keys()) == set(BACKUP_SERVICES), (
    f"RESTORE_STEPS and BACKUP_SERVICES must contain the same entries: "
    f"only in RESTORE_STEPS={set(RESTORE_STEPS.keys()) - set(BACKUP_SERVICES)}, "
    f"only in BACKUP_SERVICES={set(BACKUP_SERVICES) - set(RESTORE_STEPS.keys())}"
)


class Orchestrator:
    def __init__(
        self,
        settings: BackupSettings,
        s3: S3Manager,
        docker: DockerManager,
        handlers: list[BackupHandler],
    ) -> None:
        self._settings = settings
        self._s3 = s3
        self._docker = docker
        self._handlers = {h.service_name: h for h in handlers}

    def run_backup(
        self,
        mode: BackupMode = BackupMode.ONLINE,
        on_service_complete: Callable[[ServiceResult], None] | None = None,
    ) -> BackupSummary:
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        prefix = f"{timestamp}_{mode.value}"
        overall_start = time.monotonic()

        logger.info("=" * 44)
        logger.info("AI-Hub Backup - %s", timestamp)
        logger.info("Mode: %s", "OFFLINE (consistent)" if mode == BackupMode.OFFLINE else "ONLINE")
        logger.info("Destination: s3://%s/%s/", self._s3.bucket, prefix)
        logger.info("=" * 44)

        results: list[ServiceResult] = []

        if mode == BackupMode.OFFLINE:
            self._stop_containers("application services", APP_CONTAINERS)

        try:
            for service_name, handler in self._handlers.items():
                if service_name == "Milvus" and self._should_skip_milvus(mode):
                    result = ServiceResult(name=service_name, status=ServiceStatus.SKIPPED)
                    results.append(result)
                    logger.info("Skipping: Milvus (BACKUP_SKIP_MILVUS_%s=true)", mode.value.upper())
                    if on_service_complete:
                        on_service_complete(result)
                    continue

                result = self._run_service_backup(handler, timestamp, prefix)
                results.append(result)
                if on_service_complete:
                    on_service_complete(result)
        finally:
            if mode == BackupMode.OFFLINE:
                self._restart_app_services()

        retention_warning: str | None = None
        try:
            run_retention(self._s3, self._settings.BACKUP_RETENTION_DAYS)
        except Exception as e:
            retention_warning = str(e)
            logger.warning("Retention cleanup failed (non-fatal): %s", e)

        total_duration = time.monotonic() - overall_start
        summary = BackupSummary(
            timestamp=timestamp,
            mode=mode,
            results=results,
            total_duration_seconds=round(total_duration, 1),
            retention_warning=retention_warning,
        )

        self._log_summary(summary)
        return summary

    def run_restore(
        self,
        timestamp: str | None = None,
        on_service_complete: Callable[[ServiceResult], None] | None = None,
        force: bool = False,
    ) -> BackupSummary:
        """When force=False (default), the first service failure aborts the restore
        and all services are restarted before re-raising. When force=True,
        failures are logged but remaining services continue (best-effort).

        Partial restore is expected on failure: services restored before the
        failing one will have new data while later services retain old data.
        The finally block always restarts all services regardless of outcome.
        """
        overall_start = time.monotonic()

        logger.info("=" * 44)
        logger.info("AI-Hub Full System Restore")
        logger.info("=" * 44)

        if not timestamp:
            resolved = self._s3.find_latest_backup()
            if not resolved:
                raise RuntimeError(f"No backups found in s3://{self._s3.bucket}/")
            timestamp = resolved
            logger.info("Auto-selected latest backup: %s", timestamp)
        else:
            resolved = self._s3.resolve_timestamp(timestamp)
            logger.info("Resolved timestamp: %s -> %s", timestamp, resolved)
            timestamp = resolved

        mode = BackupMode.OFFLINE if timestamp.endswith("_offline") else BackupMode.ONLINE

        # Phase 1: Validate
        logger.info("=== Phase 1: Validation ===")
        self._validate_backups(timestamp)

        # Phase 2: Full Stop
        logger.info("=== Phase 2: Stopping all services ===")
        self._stop_all_services()

        results: list[ServiceResult] = []

        # Phase 3 + 4: Restore data, then always restart all services
        try:
            logger.info("=== Phase 3: Restoring data ===")

            for service_name, (start_before, stop_after, start_timeout) in RESTORE_STEPS.items():
                # Milvus — skip based on whether backup data exists (not current settings)
                if service_name == "Milvus":
                    milvus_prefixes = self._s3.list_prefixes(f"{timestamp}/")
                    if not any("milvus_backup_" in p for p in milvus_prefixes):
                        logger.info("--- Milvus: SKIPPED (no Milvus data in backup) ---")
                        result = ServiceResult(name="Milvus", status=ServiceStatus.SKIPPED)
                        results.append(result)
                        if on_service_complete:
                            on_service_complete(result)
                        continue

                logger.info("--- %s ---", service_name)
                if start_before:
                    self._start_and_wait(start_before, timeout=start_timeout)

                result = self._run_service_restore(service_name, timestamp, force=force)
                results.append(result)
                if on_service_complete:
                    on_service_complete(result)

                if stop_after and result.status != ServiceStatus.FAILED:
                    self._stop_containers(service_name.lower(), stop_after)
        finally:
            # Phase 4: Full Start + Verify
            logger.info("=== Phase 4: Starting all services ===")
            self._start_all_services()

        total_duration = time.monotonic() - overall_start
        summary = BackupSummary(
            timestamp=timestamp,
            mode=mode,
            results=results,
            total_duration_seconds=round(total_duration, 1),
        )

        self._log_summary(summary)
        return summary

    def run_single_restore(self, service_name: str, timestamp: str | None = None) -> ServiceResult:
        """Stops app containers before restore and restarts all services afterwards
        to prevent restoring against live services with active connections.
        """
        if service_name not in RESTORE_STEPS:
            raise RuntimeError(f"Unknown service: {service_name}")

        if not timestamp:
            resolved = self._s3.find_latest_backup()
            if not resolved:
                raise RuntimeError(f"No backups found in s3://{self._s3.bucket}/")
            timestamp = resolved
            logger.info("Auto-selected latest backup: %s", timestamp)
        else:
            resolved = self._s3.resolve_timestamp(timestamp)
            logger.info("Resolved timestamp: %s -> %s", timestamp, resolved)
            timestamp = resolved

        start_before, stop_after, start_timeout = RESTORE_STEPS[service_name]

        self._stop_containers("application services", APP_CONTAINERS)
        try:
            if start_before:
                self._start_and_wait(start_before, timeout=start_timeout)

            result = self._run_service_restore(service_name, timestamp, force=False)

            if stop_after and result.status != ServiceStatus.FAILED:
                self._stop_containers(service_name.lower(), stop_after)
        finally:
            self._start_all_services()

        return result

    def list_backups(self) -> list[BackupEntry]:
        prefixes = self._s3.list_prefixes()
        entries: list[BackupEntry] = []
        for prefix in sorted(prefixes):
            if not BACKUP_PREFIX_RE.match(prefix):
                continue
            file_count = self._s3.count_objects(prefix + "/")
            entries.append(BackupEntry(prefix=prefix, file_count=file_count))
        return entries

    def _run_service_backup(self, handler: BackupHandler, timestamp: str, prefix: str) -> ServiceResult:
        logger.info("--- Backing up: %s ---", handler.service_name)
        start = time.monotonic()
        try:
            handler.backup(timestamp, prefix)
            duration = time.monotonic() - start
            logger.info("Completed in %.0fs", duration)
            return ServiceResult(
                name=handler.service_name, status=ServiceStatus.SUCCEEDED, duration_seconds=round(duration, 1)
            )
        except Exception as e:
            # Continue backing up remaining services even if one fails
            duration = time.monotonic() - start
            logger.error("FAILED after %.0fs: %s", duration, e)
            return ServiceResult(
                name=handler.service_name,
                status=ServiceStatus.FAILED,
                duration_seconds=round(duration, 1),
                error=str(e),
            )

    def _run_service_restore(self, service_name: str, timestamp: str, force: bool) -> ServiceResult:
        handler = self._handlers.get(service_name)
        if handler is None:
            error = f"Unknown service: {service_name}"
            if not force:
                raise RuntimeError(error)
            return ServiceResult(name=service_name, status=ServiceStatus.FAILED, error=error)

        start = time.monotonic()
        try:
            handler.restore(timestamp)
            duration = time.monotonic() - start
            return ServiceResult(name=service_name, status=ServiceStatus.SUCCEEDED, duration_seconds=round(duration, 1))
        except Exception as e:
            duration = time.monotonic() - start
            logger.error("%s restore failed: %s", service_name, e)
            if not force:
                raise
            return ServiceResult(
                name=service_name, status=ServiceStatus.FAILED, duration_seconds=round(duration, 1), error=str(e)
            )

    def _should_skip_milvus(self, mode: BackupMode) -> bool:
        if mode == BackupMode.ONLINE and self._settings.BACKUP_SKIP_MILVUS_ONLINE:
            return True
        if mode == BackupMode.OFFLINE and self._settings.BACKUP_SKIP_MILVUS_OFFLINE:
            return True
        return False

    def _should_tolerate_missing_milvus(self, timestamp: str) -> bool:
        mode = BackupMode.OFFLINE if timestamp.endswith("_offline") else BackupMode.ONLINE
        return self._should_skip_milvus(mode)

    def _validate_backups(self, timestamp: str) -> None:
        missing: list[str] = []

        if not self._s3.file_exists(f"{timestamp}/postgres-main.sql.gz"):
            missing.append("PostgreSQL (main)")
        if not self._s3.file_exists(f"{timestamp}/postgres-ferretdb.sql.gz"):
            missing.append("PostgreSQL (FerretDB)")
        if not self._s3.file_exists(f"{timestamp}/neo4j.dump"):
            missing.append("Neo4j")
        if not self._s3.file_exists(f"{timestamp}/clickhouse.tar.gz"):
            missing.append("ClickHouse")
        if not self._s3.file_exists(f"{timestamp}/valkey.rdb"):
            missing.append("Valkey")
        if not self._s3.file_exists(f"{timestamp}/nats-jetstream.tar.gz"):
            missing.append("NATS JetStream")

        milvus_prefixes = self._s3.list_prefixes(f"{timestamp}/")
        if not any("milvus_backup_" in p for p in milvus_prefixes):
            if not self._should_tolerate_missing_milvus(timestamp):
                missing.append("Milvus")
            else:
                logger.info("No Milvus backup found in %s (skipped per configuration)", timestamp)

        if missing:
            raise RuntimeError(f"Missing backups: {', '.join(missing)}")

        logger.info("All backups validated")

    def _stop_all_services(self) -> None:
        self._stop_containers("application services", APP_CONTAINERS)
        self._stop_containers("infrastructure consumers", INFRA_CONSUMERS)
        self._stop_containers("databases", DATABASE_CONTAINERS)

    def _start_all_services(self) -> None:
        self._start_and_wait(START_ORDER_INFRA, timeout=60, label="infrastructure (postgres)")
        self._start_and_wait(START_ORDER_SERVICES, timeout=120, label="services")
        self._start_and_wait(START_ORDER_APPS, timeout=120, label="application services")

    def _stop_containers(self, label: str, containers: Sequence[str]) -> None:
        logger.info("Stopping %s...", label)
        for name in containers:
            if self._docker.stop_container(name):
                logger.info("  Stopped: %s", name)

    def _start_and_wait(
        self,
        containers: Sequence[str],
        timeout: int = 120,
        label: str | None = None,
    ) -> None:
        if label:
            logger.info("Starting %s...", label)
        existing = [name for name in containers if self._docker.container_exists(name)]
        for name in existing:
            self._docker.start_container(name)
        failed = [name for name in existing if not self._docker.wait_for_healthy(name, timeout)]
        if failed:
            raise RuntimeError(f"Containers failed health check: {', '.join(failed)}")

    def _restart_app_services(self) -> None:
        logger.info("Restarting application services...")
        for name in APP_CONTAINERS:
            if self._docker.container_exists(name):
                self._docker.start_container(name)
        logger.info("Waiting for services to become healthy...")
        failed = [name for name in APP_CONTAINERS if not self._docker.wait_for_healthy(name, 120)]
        if failed:
            logger.error("App containers did not become healthy: %s", ", ".join(failed))
            raise RuntimeError(f"App containers did not become healthy after restart: {', '.join(failed)}")

    def _log_summary(self, summary: BackupSummary) -> None:
        logger.info("=" * 44)
        logger.info("Summary (%.0fs total)", summary.total_duration_seconds)
        logger.info("=" * 44)
        for r in summary.results:
            if r.status == ServiceStatus.SUCCEEDED:
                logger.info("  %s: OK (%.0fs)", r.name, r.duration_seconds)
            elif r.status == ServiceStatus.SKIPPED:
                logger.info("  %s: SKIPPED", r.name)
            else:
                logger.info("  %s: FAILED - %s", r.name, r.error)

        failed = [r for r in summary.results if r.status == ServiceStatus.FAILED]
        if failed:
            logger.error("COMPLETED WITH ERRORS")
        else:
            logger.info("COMPLETED SUCCESSFULLY")
