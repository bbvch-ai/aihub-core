import gzip
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.services.postgres import PostgresHandler
from swiss_ai_hub.backup.settings import BackupSettings


@pytest.fixture
def postgres_handler(settings: BackupSettings) -> PostgresHandler:
    s3 = MagicMock()
    return PostgresHandler(settings, s3)


def _make_run_for_backup(databases: list[str] | None = None) -> object:
    """Return a subprocess.run mock that handles pg_dumpall, pg_dump, psql list-databases, and COPY TO STDOUT."""
    dbs = databases or ["openwebui", "langfuse"]

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)

        if "pg_dumpall" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"-- globals SQL", stderr=b"")

        if "pg_dump" in cmd_str:
            stdout_file = kwargs.get("stdout")
            if stdout_file is not None and hasattr(stdout_file, "write"):
                stdout_file.write(b"\x00PGDUMP")
            return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

        if "COPY" in cmd_str and "TO STDOUT" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="1\ttest_db\ttest_col\n", stderr="")

        if "last_value" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="1|true\n", stderr="")

        if "datistemplate" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="\n".join(dbs) + "\n", stderr="")

        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    return fake_run


def _fake_download(s3_key: str, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if s3_key.endswith("ext-catalog.sql.gz"):
        with gzip.open(local_path, "wt") as f:
            f.write("TRUNCATE documentdb_api_catalog.collections CASCADE;\n")
    elif s3_key.endswith(".sql.gz"):
        with gzip.open(local_path, "wb") as f:
            f.write(b"-- globals SQL")
    else:
        local_path.write_bytes(b"\x00PGDUMP")


# ---------------------------------------------------------------------------
# Backup tests
# ---------------------------------------------------------------------------


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_uploads_globals_and_per_db_dumps(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_backup(["openwebui", "langfuse"])

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    s3_keys = [call[0][1] for call in postgres_handler._s3.upload_file.call_args_list]
    assert "2026-02-19_02-00-00/postgres-main/globals.sql.gz" in s3_keys
    assert "2026-02-19_02-00-00/postgres-main/openwebui.dump" in s3_keys
    assert "2026-02-19_02-00-00/postgres-main/langfuse.dump" in s3_keys
    assert "2026-02-19_02-00-00/postgres-ferretdb/globals.sql.gz" in s3_keys
    assert "2026-02-19_02-00-00/postgres-ferretdb/ext-catalog.sql.gz" in s3_keys
    assert postgres_handler._s3.upload_file.call_count == 7


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_dumps_documentdb_catalog_separately(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_backup(["mydb"])

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    all_cmds = [" ".join(str(c) for c in call[0][0]) for call in mock_run.call_args_list]
    copy_calls = [cmd for cmd in all_cmds if "COPY" in cmd and "TO STDOUT" in cmd]
    assert len(copy_calls) == 2
    for table in ("documentdb_api_catalog.collections", "documentdb_api_catalog.collection_indexes"):
        assert any(table in cmd for cmd in copy_calls)

    seq_calls = [cmd for cmd in all_cmds if "last_value" in cmd]
    assert len(seq_calls) == 2

    s3_keys = [call[0][1] for call in postgres_handler._s3.upload_file.call_args_list]
    assert "2026-02-19_02-00-00/postgres-ferretdb/ext-catalog.sql.gz" in s3_keys


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_calls_pg_dump_fc_per_database(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_backup(["openwebui", "langfuse", "dagster"])

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    pg_dump_calls = [
        call[0][0]
        for call in mock_run.call_args_list
        if "pg_dump" in str(call[0][0]) and "pg_dumpall" not in str(call[0][0])
    ]
    assert len(pg_dump_calls) == 6
    pg_dump_dbnames = [cmd[-1] for cmd in pg_dump_calls]
    for dbname in ("openwebui", "langfuse", "dagster"):
        assert pg_dump_dbnames.count(dbname) == 2
    for cmd in pg_dump_calls:
        assert "-Fc" in cmd


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_raises_on_pg_dumpall_failure(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    def failing_dumpall(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0] if args else kwargs.get("args", [])
        if "pg_dumpall" in " ".join(str(c) for c in cmd):
            return subprocess.CompletedProcess(cmd, 1, stdout=b"", stderr=b"connection refused")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    mock_run.side_effect = failing_dumpall

    with pytest.raises(subprocess.CalledProcessError):
        postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_raises_on_pg_dump_failure(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    def failing_pg_dump(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)

        if "pg_dumpall" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"-- globals", stderr=b"")
        if "datname" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="mydb\n", stderr="")
        if "pg_dump" in cmd_str:
            return subprocess.CompletedProcess(cmd, 1, stdout=b"", stderr=b"connection refused")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    mock_run.side_effect = failing_pg_dump

    with pytest.raises(subprocess.CalledProcessError):
        postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_passes_password_via_env(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_backup(["db1"])

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    for mock_call in mock_run.call_args_list:
        env = mock_call.kwargs.get("env") or mock_call[1].get("env", {})
        if env and "PGPASSWORD" in env:
            cmd = mock_call[0][0] if mock_call[0] else mock_call.kwargs.get("args", [])
            assert not any("testpass" in str(arg) for arg in cmd)


# ---------------------------------------------------------------------------
# Restore tests
# ---------------------------------------------------------------------------


def _make_run_for_restore(
    *,
    databases: list[str] | None = None,
    pg_restore_returncode: int = 0,
    pg_restore_stderr: str = "",
) -> object:
    dbs = databases or ["openwebui", "langfuse"]

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)

        if "datistemplate" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="\n".join(dbs) + "\n", stderr="")
        if "pg_restore" in cmd_str:
            return subprocess.CompletedProcess(
                cmd, pg_restore_returncode, stdout=b"", stderr=pg_restore_stderr.encode()
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    return fake_run


def _setup_s3_for_restore(
    handler: PostgresHandler, databases: list[str] | None = None, *, has_ext_catalog: bool = True
) -> None:
    dbs = databases or ["openwebui", "langfuse"]

    def list_keys_side_effect(prefix: str) -> list[str]:
        keys = [f"{prefix}globals.sql.gz"] + [f"{prefix}{db}.dump" for db in dbs]
        if has_ext_catalog and "ferretdb" in prefix:
            keys.append(f"{prefix}ext-catalog.sql.gz")
        return keys

    handler._s3.list_keys.side_effect = list_keys_side_effect
    handler._s3.download_file.side_effect = _fake_download
    handler._s3.file_exists.return_value = has_ext_catalog


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_downloads_and_restores(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore()
    _setup_s3_for_restore(postgres_handler)

    postgres_handler.restore("2026-02-19_02-00-00")

    all_cmds = [" ".join(str(c) for c in call[0][0]) for call in mock_run.call_args_list]
    assert any("pg_restore" in cmd and "--create" in cmd for cmd in all_cmds)
    assert any("psql" in cmd and "globals" not in cmd for cmd in all_cmds)


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_calls_pg_restore_per_database(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore(databases=["postgres", "openwebui", "langfuse"])
    _setup_s3_for_restore(postgres_handler, databases=["postgres", "openwebui", "langfuse"])

    postgres_handler.restore("2026-02-19_02-00-00")

    pg_restore_calls = [call[0][0] for call in mock_run.call_args_list if "pg_restore" in str(call[0][0])]
    assert len(pg_restore_calls) == 6

    for cmd in pg_restore_calls:
        dump_path = cmd[-1]
        assert dump_path.endswith(".dump")
        dbname = Path(dump_path).stem
        if dbname == "postgres":
            assert "--clean" in cmd
            assert "--if-exists" in cmd
            assert "--create" not in cmd
        else:
            assert "--create" in cmd

    restored_names = [Path(cmd[-1]).stem for cmd in pg_restore_calls]
    for dbname in ("postgres", "openwebui", "langfuse"):
        assert restored_names.count(dbname) == 2


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_recreates_postgres_database_before_restore(
    mock_run: MagicMock, postgres_handler: PostgresHandler
) -> None:
    mock_run.side_effect = _make_run_for_restore(databases=["postgres", "openwebui"])
    _setup_s3_for_restore(postgres_handler, databases=["postgres", "openwebui"])

    postgres_handler.restore("2026-02-19_02-00-00")

    all_cmds = [" ".join(str(c) for c in call[0][0]) for call in mock_run.call_args_list]
    recreate_cmds = [cmd for cmd in all_cmds if "template1" in cmd and "DROP DATABASE" in cmd]
    assert len(recreate_cmds) == 2
    for cmd in recreate_cmds:
        assert "CREATE DATABASE postgres" in cmd


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_terminates_then_drops_each_database(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore(databases=["postgres", "openwebui", "langfuse"])
    _setup_s3_for_restore(postgres_handler, databases=["postgres", "openwebui", "langfuse"])

    postgres_handler.restore("2026-02-19_02-00-00")

    all_cmds = [call[0][0] for call in mock_run.call_args_list]
    for dbname in ("openwebui", "langfuse"):
        drop_calls = [cmd for cmd in all_cmds if f'DROP DATABASE IF EXISTS "{dbname}"' in str(cmd)]
        assert drop_calls
        for cmd in drop_calls:
            assert any(f"datname = '{dbname}'" in str(arg) for arg in cmd)

    postgres_drop_calls = [cmd for cmd in all_cmds if 'DROP DATABASE IF EXISTS "postgres"' in str(cmd)]
    assert not postgres_drop_calls


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_on_drop_database_failure(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    def drop_fails(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)
        if "DROP DATABASE" in cmd_str:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="ERROR: cannot drop\n")
        if "datistemplate" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="openwebui\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    mock_run.side_effect = drop_fails
    _setup_s3_for_restore(postgres_handler, databases=["openwebui"])

    with pytest.raises(RuntimeError, match="Failed to drop database openwebui"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_passes_password_via_env(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore()
    _setup_s3_for_restore(postgres_handler)

    postgres_handler.restore("2026-02-19_02-00-00")

    for mock_call in mock_run.call_args_list:
        env = mock_call.kwargs.get("env") or mock_call[1].get("env", {})
        if env:
            assert "PGPASSWORD" in env


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_on_fatal_pg_restore_error(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore(
        pg_restore_returncode=1,
        pg_restore_stderr="FATAL: password authentication failed\n",
    )
    _setup_s3_for_restore(postgres_handler)

    with pytest.raises(RuntimeError, match="password authentication failed"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_on_panic_error(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore(
        pg_restore_returncode=1,
        pg_restore_stderr="PANIC: could not write to WAL\n",
    )
    _setup_s3_for_restore(postgres_handler)

    with pytest.raises(RuntimeError, match="could not write to WAL"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_tolerates_nonfatal_pg_restore_warnings(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore(
        pg_restore_returncode=1,
        pg_restore_stderr="pg_restore: warning: errors ignored on restore\n",
    )
    _setup_s3_for_restore(postgres_handler)

    postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_replays_documentdb_catalog(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore()
    _setup_s3_for_restore(postgres_handler)

    postgres_handler.restore("2026-02-19_02-00-00")

    catalog_psql_calls = [
        call for call in mock_run.call_args_list if call.kwargs.get("input") and "TRUNCATE" in str(call.kwargs["input"])
    ]
    assert len(catalog_psql_calls) == 1


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_when_no_ext_catalog_file(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore()
    _setup_s3_for_restore(postgres_handler, has_ext_catalog=False)

    with pytest.raises(RuntimeError, match="Extension catalog backup missing"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_on_missing_s3_artifacts(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    postgres_handler._s3.list_keys.return_value = []

    with pytest.raises(RuntimeError, match="No backup artifacts found"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_on_connection_refused(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_restore(
        pg_restore_returncode=1,
        pg_restore_stderr="pg_restore: error: could not connect to database\n",
    )
    _setup_s3_for_restore(postgres_handler)

    with pytest.raises(RuntimeError, match="could not"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_rejects_unsafe_database_name(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    def returns_unsafe_db(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)
        if "datistemplate" in cmd_str:
            return subprocess.CompletedProcess(cmd, 0, stdout="safe_db\n'; DROP TABLE evil --\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    mock_run.side_effect = returns_unsafe_db
    _setup_s3_for_restore(postgres_handler, databases=["safe_db"])

    with pytest.raises(ValueError, match="Unsafe database name rejected"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_subprocess_timeout_propagates_from_settings(mock_run: MagicMock, settings: BackupSettings) -> None:
    """Operator-supplied POSTGRES_SUBPROCESS_TIMEOUT_SECONDS must reach every subprocess.run call."""
    custom_timeout = 12345
    overridden = settings.model_copy(update={"POSTGRES_SUBPROCESS_TIMEOUT_SECONDS": custom_timeout})
    handler = PostgresHandler(overridden, MagicMock())
    mock_run.side_effect = _make_run_for_backup(["mydb"])

    handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    timeouts = [call.kwargs.get("timeout") for call in mock_run.call_args_list]
    assert timeouts, "expected at least one subprocess.run call"
    assert all(t == custom_timeout for t in timeouts), f"timeouts seen: {set(timeouts)}"


def _script_psql_calls(mock_run: MagicMock) -> list[tuple[list[str], str]]:
    return [(list(call[0][0]), call.kwargs["input"]) for call in mock_run.call_args_list if call.kwargs.get("input")]


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_runs_backup_sql_restricted_and_stopping_on_error(
    mock_run: MagicMock, postgres_handler: PostgresHandler
) -> None:
    mock_run.side_effect = _make_run_for_restore()
    _setup_s3_for_restore(postgres_handler)

    postgres_handler.restore("2026-02-19_02-00-00")

    script_calls = _script_psql_calls(mock_run)
    assert len(script_calls) == 3
    for cmd, script in script_calls:
        assert cmd[0] == "psql"
        assert "ON_ERROR_STOP=1" in cmd
        assert script.startswith("\\restrict ")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_when_globals_fail(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    restore_run = _make_run_for_restore()

    def fail_globals(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "globals SQL" in str(kwargs.get("input", "")):
            return subprocess.CompletedProcess(args[0], 3, stdout="", stderr="ERROR:  syntax error")
        return restore_run(*args, **kwargs)  # type: ignore[operator]

    mock_run.side_effect = fail_globals
    _setup_s3_for_restore(postgres_handler)

    with pytest.raises(RuntimeError, match="Loading globals on postgres-main failed: ERROR:  syntax error"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_raises_when_documentdb_catalog_fails(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    restore_run = _make_run_for_restore()

    def fail_catalog(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "TRUNCATE" in str(kwargs.get("input", "")):
            return subprocess.CompletedProcess(args[0], 3, stdout="", stderr="ERROR:  relation does not exist")
        return restore_run(*args, **kwargs)  # type: ignore[operator]

    mock_run.side_effect = fail_catalog
    _setup_s3_for_restore(postgres_handler)

    with pytest.raises(RuntimeError, match="DocumentDB catalog restore failed"):
        postgres_handler.restore("2026-02-19_02-00-00")


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_restore_accepts_catalog_artifacts_with_unaligned_booleans(
    mock_run: MagicMock, postgres_handler: PostgresHandler
) -> None:
    mock_run.side_effect = _make_run_for_restore()
    _setup_s3_for_restore(postgres_handler)

    def download_with_legacy_setval(s3_key: str, local_path: Path) -> None:
        _fake_download(s3_key, local_path)
        if s3_key.endswith("ext-catalog.sql.gz"):
            with gzip.open(local_path, "wt") as f:
                f.write("TRUNCATE documentdb_api_catalog.collections CASCADE;\n")
                f.write("SELECT setval('documentdb_api_catalog.collections_collection_id_seq', 7, t);\n")

    postgres_handler._s3.download_file.side_effect = download_with_legacy_setval

    postgres_handler.restore("2026-02-19_02-00-00")

    catalog_script = next(script for _, script in _script_psql_calls(mock_run) if "TRUNCATE" in script)
    assert "SELECT setval('documentdb_api_catalog.collections_collection_id_seq', 7, true);" in catalog_script


@patch("swiss_ai_hub.backup.services.postgres.subprocess.run")
def test_backup_writes_sequence_flags_as_sql_booleans(mock_run: MagicMock, postgres_handler: PostgresHandler) -> None:
    mock_run.side_effect = _make_run_for_backup(["mydb"])
    written: dict[str, str] = {}

    def capture_upload(local_path: Path, s3_key: str) -> None:
        if s3_key.endswith("ext-catalog.sql.gz"):
            with gzip.open(local_path, "rt") as f:
                written["catalog"] = f.read()

    postgres_handler._s3.upload_file.side_effect = capture_upload

    postgres_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    seq_cmds = [" ".join(call[0][0]) for call in mock_run.call_args_list if "last_value" in " ".join(call[0][0])]
    assert all("is_called::text" in cmd for cmd in seq_cmds)
    assert "SELECT setval('documentdb_api_catalog.collections_collection_id_seq', 1, true);" in written["catalog"]
