import gzip
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import override

from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

_SUBPROCESS_TIMEOUT = 300
_SAFE_DBNAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class PostgresHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager) -> None:
        self._settings = settings
        self._s3 = s3

    @property
    @override
    def service_name(self) -> str:
        return "PostgreSQL"

    @override
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-postgres-"))
        try:
            self._backup_host(
                host=self._settings.POSTGRES_HOST,
                user=self._settings.POSTGRES_USER,
                password=self._settings.POSTGRES_PASSWORD.get_secret_value(),
                label="postgres-main",
                s3_prefix=s3_prefix,
                tmp_dir=tmp_dir,
            )
            self._backup_host(
                host=self._settings.POSTGRES_FERRETDB_HOST,
                user=self._settings.MONGO_USERNAME,
                password=self._settings.MONGO_PASSWORD.get_secret_value(),
                label="postgres-ferretdb",
                s3_prefix=s3_prefix,
                tmp_dir=tmp_dir,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @override
    def restore(self, backup_prefix: str) -> None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="backup-postgres-"))
        try:
            self._restore_host(
                host=self._settings.POSTGRES_HOST,
                user=self._settings.POSTGRES_USER,
                password=self._settings.POSTGRES_PASSWORD.get_secret_value(),
                label="postgres-main",
                backup_prefix=backup_prefix,
                tmp_dir=tmp_dir,
            )
            self._restore_host(
                host=self._settings.POSTGRES_FERRETDB_HOST,
                user=self._settings.MONGO_USERNAME,
                password=self._settings.MONGO_PASSWORD.get_secret_value(),
                label="postgres-ferretdb",
                backup_prefix=backup_prefix,
                tmp_dir=tmp_dir,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _backup_host(self, host: str, user: str, password: str, label: str, s3_prefix: str, tmp_dir: Path) -> None:
        env = self._pg_env(password)
        host_dir = tmp_dir / label
        host_dir.mkdir()

        self._dump_globals(host, user, env, label, host_dir, s3_prefix)
        databases = self._list_all_databases(host, user, env)
        logger.info("[%s] Found databases: %s", label, databases)
        for db in databases:
            self._dump_database(host, user, env, db, label, host_dir, s3_prefix)

        logger.info("[%s] Backed up globals + %d databases", label, len(databases))

    def _dump_globals(
        self, host: str, user: str, env: dict[str, str], label: str, host_dir: Path, s3_prefix: str
    ) -> None:
        logger.info("[%s] Dumping globals...", label)
        globals_file = host_dir / "globals.sql.gz"
        result = subprocess.run(
            ["pg_dumpall", "-h", host, "-U", user, "--globals-only"],
            capture_output=True,
            env=env,
            check=False,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, "pg_dumpall", stderr=result.stderr.decode())
        with gzip.open(globals_file, "wb") as f:
            f.write(result.stdout)
        self._s3.upload_file(globals_file, f"{s3_prefix}/{label}/globals.sql.gz")
        globals_file.unlink()

    def _dump_database(
        self, host: str, user: str, env: dict[str, str], dbname: str, label: str, host_dir: Path, s3_prefix: str
    ) -> None:
        logger.info("[%s] Dumping database %s...", label, dbname)
        dump_file = host_dir / f"{dbname}.dump"
        with dump_file.open("wb") as f:
            result = subprocess.run(
                ["pg_dump", "-h", host, "-U", user, "-Fc", dbname],
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, "pg_dump", stderr=result.stderr.decode())

        size_mb = dump_file.stat().st_size / (1024 * 1024)
        logger.info("[%s] %s: %.1fMB", label, dbname, size_mb)
        self._s3.upload_file(dump_file, f"{s3_prefix}/{label}/{dbname}.dump")
        dump_file.unlink()

    def _restore_host(
        self,
        host: str,
        user: str,
        password: str,
        label: str,
        backup_prefix: str,
        tmp_dir: Path,
    ) -> None:
        env = self._pg_env(password)
        host_dir = tmp_dir / label
        host_dir.mkdir()

        s3_label_prefix = f"{backup_prefix}/{label}/"
        logger.info("[%s] Listing S3 keys under %s", label, s3_label_prefix)
        keys = self._s3.list_keys(s3_label_prefix)
        logger.info("[%s] Found %d artifacts: %s", label, len(keys), [k.rsplit("/", 1)[-1] for k in keys])
        if not keys:
            raise RuntimeError(f"No backup artifacts found under {s3_label_prefix}")

        for key in keys:
            filename = key.rsplit("/", 1)[-1]
            self._s3.download_file(key, host_dir / filename)

        logger.info("[%s] Terminating backends...", label)
        self._terminate_backends(host, user, env)
        logger.info("[%s] Dropping databases...", label)
        self._drop_all_databases(host, user, env, label)
        logger.info("[%s] Loading globals...", label)
        self._load_globals(host, user, env, label, host_dir / "globals.sql.gz")
        logger.info("[%s] Restoring databases...", label)
        self._restore_databases(host, user, env, label, host_dir)

        shutil.rmtree(host_dir, ignore_errors=True)
        logger.info("[%s] Restore complete", label)

    def _terminate_backends(self, host: str, user: str, env: dict[str, str]) -> None:
        self._run_sql(
            host, user, env, "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid()"
        )

    def _drop_all_databases(self, host: str, user: str, env: dict[str, str], label: str) -> None:
        databases = [db for db in self._list_all_databases(host, user, env) if db != "postgres"]
        logger.info("[%s] Databases to drop: %s", label, databases)
        for db in databases:
            self._validated_dbname_or_raise(db)
            logger.info("[%s] Dropping %s...", label, db)
            terminate_sql = (
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{db}' AND pid <> pg_backend_pid()"
            )
            drop_sql = f'DROP DATABASE IF EXISTS "{db}"'
            result = subprocess.run(
                [
                    "psql",
                    "-h",
                    host,
                    "-U",
                    user,
                    "-d",
                    "postgres",
                    "-X",
                    "--tuples-only",
                    "--no-align",
                    "-c",
                    terminate_sql,
                    "-c",
                    drop_sql,
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=_SUBPROCESS_TIMEOUT,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to drop database {db} on {label}: {result.stderr.strip()}")

    def _load_globals(self, host: str, user: str, env: dict[str, str], label: str, globals_file: Path) -> None:
        with gzip.open(globals_file, "rb") as f:
            sql = f.read().decode()
        logger.info("[%s] Globals SQL size: %d bytes", label, len(sql))
        result = subprocess.run(
            ["psql", "-h", host, "-U", user, "-d", "postgres", "-X"],
            input=sql,
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if result.stderr:
            logger.info("[%s] Globals stderr: %s", label, result.stderr.strip()[:500])

    def _recreate_postgres_database(self, host: str, user: str, env: dict[str, str], label: str) -> None:
        """Drop and recreate the postgres database via template1 for a clean restore."""
        terminate_sql = (
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = 'postgres' AND pid <> pg_backend_pid()"
        )
        result = subprocess.run(
            [
                "psql",
                "-h",
                host,
                "-U",
                user,
                "-d",
                "template1",
                "-X",
                "--tuples-only",
                "--no-align",
                "-c",
                terminate_sql,
                "-c",
                "DROP DATABASE IF EXISTS postgres",
                "-c",
                f'CREATE DATABASE postgres OWNER "{user}"',
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to recreate postgres database on {label}: {result.stderr.strip()}")
        logger.info("[%s] Recreated postgres database", label)

    def _restore_databases(self, host: str, user: str, env: dict[str, str], label: str, host_dir: Path) -> None:
        dump_files = sorted(host_dir.glob("*.dump"))
        logger.info("[%s] Dump files to restore: %s", label, [f.name for f in dump_files])
        for dump_file in dump_files:
            dbname = dump_file.stem
            if dbname == "postgres":
                self._recreate_postgres_database(host, user, env, label)
                logger.info("[%s] Restoring %s into fresh database...", label, dbname)
                cmd = ["pg_restore", "-h", host, "-U", user, "-d", "postgres", str(dump_file)]
            else:
                logger.info("[%s] Restoring %s (--create)...", label, dbname)
                cmd = ["pg_restore", "-h", host, "-U", user, "--create", "-d", "postgres", str(dump_file)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                env=env,
                check=False,
                timeout=_SUBPROCESS_TIMEOUT,
            )
            if result.returncode != 0:
                stderr_text = result.stderr.decode()
                logger.info(
                    "[%s] pg_restore %s exit %d, stderr: %s",
                    label,
                    dbname,
                    result.returncode,
                    stderr_text.strip()[:500],
                )
                if self._has_fatal_error(stderr_text):
                    raise RuntimeError(
                        f"pg_restore of {dbname} on {label} failed (exit {result.returncode}): {stderr_text}"
                    )
            else:
                logger.info("[%s] pg_restore %s: OK", label, dbname)

    @staticmethod
    def _has_fatal_error(stderr: str) -> bool:
        for line in stderr.splitlines():
            stripped = line.strip()
            if stripped.startswith(("FATAL:", "PANIC:", "pg_restore: error: could not")):
                return True
        return False

    @staticmethod
    def _list_all_databases(host: str, user: str, env: dict[str, str]) -> list[str]:
        result = subprocess.run(
            [
                "psql",
                "-h",
                host,
                "-U",
                user,
                "-d",
                "postgres",
                "-X",
                "--tuples-only",
                "--no-align",
                "-c",
                "SELECT datname FROM pg_database WHERE datistemplate = false",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    @staticmethod
    def _run_sql(host: str, user: str, env: dict[str, str], sql: str) -> None:
        subprocess.run(
            ["psql", "-h", host, "-U", user, "-d", "postgres", "-X", "--tuples-only", "--no-align", "-c", sql],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=_SUBPROCESS_TIMEOUT,
        )

    @staticmethod
    def _validated_dbname_or_raise(name: str) -> None:
        if not _SAFE_DBNAME_RE.match(name):
            raise ValueError(f"Unsafe database name rejected: {name!r}")

    @staticmethod
    def _pg_env(password: str) -> dict[str, str]:
        return {"PGPASSWORD": password, "PATH": "/usr/local/bin:/usr/bin:/bin"}
