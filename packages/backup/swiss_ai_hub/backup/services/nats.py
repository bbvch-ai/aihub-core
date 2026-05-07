import logging
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import override

from swiss_ai_hub.backup.s3 import S3Manager
from swiss_ai_hub.backup.services.base import BackupHandler
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)

NATS_LIST_TIMEOUT = 30
NATS_STREAM_TIMEOUT = 120
NATS_READY_TIMEOUT = 60
NATS_READY_PROBE_TIMEOUT = 10
NATS_READY_POLL_INTERVAL = 2

# Substrings that indicate the NATS client could not establish a connection
# (e.g. server restarted mid-run). Operations that fail with these are safe to
# retry after waiting for readiness — the command never reached the server.
_TRANSIENT_CONNECT_ERRORS = (
    "no servers available",
    "connection refused",
    "connection reset",
    "context deadline exceeded",
    "i/o timeout",
    "tls handshake error",
    "eof",
)
_NO_STREAMS_MARKERS = ("no streams", "no jetstream")


class NatsHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager) -> None:
        self._settings = settings
        self._s3 = s3

    @property
    @override
    def service_name(self) -> str:
        return "NATS"

    @override
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        self._wait_for_ready()
        s3_key = f"{s3_prefix}/nats-jetstream.tar.gz"

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-nats-"))
        backup_dir = tmp_dir / "nats-backup"
        tar_file = tmp_dir / "nats-jetstream.tar.gz"
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            stream_names = self._list_streams()
            if not stream_names:
                logger.info("No JetStream streams found, creating empty backup archive")
            else:
                logger.info("Found %d JetStream stream(s): %s", len(stream_names), ", ".join(stream_names))

                for stream_name in stream_names:
                    stream_backup_path = backup_dir / stream_name
                    logger.info("Backing up stream: %s", stream_name)
                    self._run_nats(["stream", "backup", stream_name, str(stream_backup_path)])

            logger.info("Compressing...")
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(str(backup_dir), arcname="nats-backup")

            size_mb = tar_file.stat().st_size / (1024 * 1024)
            logger.info("Archive size: %.1fMB", size_mb)

            self._s3.upload_file(tar_file, s3_key)
            logger.info("NATS: done")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, backup_prefix: str) -> None:
        s3_key = f"{backup_prefix}/nats-jetstream.tar.gz"

        if not self._s3.file_exists(s3_key):
            logger.info("No NATS JetStream backup found in %s, skipping restore", backup_prefix)
            return

        self._wait_for_ready()

        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-nats-"))
        tar_file = tmp_dir / "nats-jetstream.tar.gz"

        try:
            self._s3.download_file(s3_key, tar_file)

            logger.info("Extracting archive...")
            with tarfile.open(tar_file, "r:gz") as tar:
                tar.extractall(tmp_dir, filter="data")

            backup_dir = tmp_dir / "nats-backup"
            if not backup_dir.exists():
                raise RuntimeError("No nats-backup directory found in archive")

            stream_dirs = sorted((d for d in backup_dir.iterdir() if d.is_dir()), key=lambda d: d.name)

            existing_streams = self._list_streams()
            for stream_name in existing_streams:
                logger.info("Deleting existing stream before restore: %s", stream_name)
                self._run_nats(["stream", "rm", stream_name, "-f"])

            for stream_dir in stream_dirs:
                logger.info("Restoring stream: %s", stream_dir.name)
                self._run_nats(["stream", "restore", str(stream_dir)])

            logger.info("NATS restore complete (%d stream(s))", len(stream_dirs))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _wait_for_ready(self) -> None:
        """Probe JetStream itself, not just the core NATS connection.

        ``nats rtt`` only verifies the TCP/TLS handshake — JetStream may still
        be replaying its WAL. ``stream list`` exercises the JS API the backup
        actually depends on, so a successful probe means the next operation
        will not fail with "no servers available" / "JetStream not enabled".
        """
        deadline = time.monotonic() + NATS_READY_TIMEOUT
        last_error = ""
        while True:
            result = subprocess.run(
                [*self._nats_base_args(), "stream", "list", "--names"],
                capture_output=True,
                text=True,
                check=False,
                env=self._nats_env(),
                timeout=NATS_READY_PROBE_TIMEOUT,
            )
            if result.returncode == 0:
                return
            stderr = result.stderr or ""
            if any(marker in stderr.lower() for marker in _NO_STREAMS_MARKERS):
                return
            last_error = stderr.strip()
            if time.monotonic() >= deadline:
                raise RuntimeError(f"NATS not ready after {NATS_READY_TIMEOUT}s: {last_error}")
            time.sleep(NATS_READY_POLL_INTERVAL)

    def _nats_base_args(self) -> list[str]:
        return ["nats", "-s", self._settings.NATS_URL]

    def _nats_env(self) -> dict[str, str]:
        return {
            "NATS_TOKEN": self._settings.NATS_TOKEN.get_secret_value(),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }

    def _list_streams(self) -> list[str]:
        result = self._run_nats_subprocess(["stream", "list", "--names"], timeout=NATS_LIST_TIMEOUT)
        if result.returncode == 0:
            if not result.stdout.strip():
                return []
            return [name.strip() for name in result.stdout.strip().split("\n") if name.strip()]

        stderr = result.stderr.lower() if result.stderr else ""
        if any(marker in stderr for marker in _NO_STREAMS_MARKERS):
            return []
        raise RuntimeError(f"nats stream list failed (exit {result.returncode}): {result.stderr}")

    def _run_nats(self, args: list[str]) -> str:
        result = self._run_nats_subprocess(args, timeout=NATS_STREAM_TIMEOUT)
        if result.returncode != 0:
            raise RuntimeError(f"nats {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}")
        return result.stdout

    def _run_nats_subprocess(
        self, args: list[str], timeout: int, max_attempts: int = 3
    ) -> subprocess.CompletedProcess[str]:
        """Run a `nats` CLI command with bounded retry on transient connect errors.

        A NATS server restart mid-run produces "no servers available for
        connection". The command never reached the server, so re-running is
        safe. Between attempts we re-probe readiness so we don't hammer a
        still-restarting server.

        Partial-execution caveat for write commands (`stream backup`,
        `stream restore`, `stream rm`): a "connection reset" can fire AFTER
        the server received the request, so a retry may hit a non-transient
        follow-up error (e.g. "stream already exists" on restore, or refusal
        to overwrite an existing backup directory). Those surface as
        non-transient and abort the run loudly — no silent corruption — but
        operators may need to clean up partial state before re-running.
        """
        last_result: subprocess.CompletedProcess[str] | None = None
        for attempt in range(1, max_attempts + 1):
            result = subprocess.run(
                [*self._nats_base_args(), *args],
                capture_output=True,
                text=True,
                check=False,
                env=self._nats_env(),
                timeout=timeout,
            )
            last_result = result
            if result.returncode == 0:
                return result
            stderr = (result.stderr or "").lower()
            if not any(marker in stderr for marker in _TRANSIENT_CONNECT_ERRORS):
                return result
            if attempt == max_attempts:
                return result
            logger.warning(
                "nats %s hit transient connect error (attempt %d/%d), re-probing readiness: %s",
                " ".join(args),
                attempt,
                max_attempts,
                result.stderr.strip(),
            )
            self._wait_for_ready()
        assert last_result is not None
        return last_result
