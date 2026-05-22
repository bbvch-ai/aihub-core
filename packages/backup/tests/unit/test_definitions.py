from swiss_ai_hub.backup.dagster.definitions import backup_definitions


def test_backup_definitions_loads() -> None:
    defs = backup_definitions()
    assert defs is not None


def test_backup_definitions_has_all_backup_assets() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()
    all_keys = {key.to_user_string() for key in asset_graph.get_all_asset_keys()}

    assert "backup/session" in all_keys
    assert "backup/postgres" in all_keys
    assert "backup/milvus" in all_keys
    assert "backup/neo4j" in all_keys
    assert "backup/clickhouse" in all_keys
    assert "backup/valkey" in all_keys
    assert "backup/nats" in all_keys
    assert "backup/finalize" in all_keys


def test_backup_definitions_has_job() -> None:
    defs = backup_definitions()
    job = defs.get_job_def("backup_asset_job")
    assert job is not None
    assert job.name == "backup_asset_job"


def test_restore_definitions_has_all_assets() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()
    all_keys = {key.to_user_string() for key in asset_graph.get_all_asset_keys()}

    assert "restore/session" in all_keys
    assert "restore/postgres" in all_keys
    assert "restore/milvus" in all_keys
    assert "restore/neo4j" in all_keys
    assert "restore/clickhouse" in all_keys
    assert "restore/valkey" in all_keys
    assert "restore/nats" in all_keys
    assert "restore/finalize" in all_keys


def test_restore_definitions_has_job() -> None:
    defs = backup_definitions()
    job = defs.get_job_def("full_restore_job")
    assert job is not None
    assert job.name == "full_restore_job"


def test_backup_service_assets_depend_on_session() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()

    service_keys = [
        "backup/postgres",
        "backup/milvus",
        "backup/neo4j",
        "backup/clickhouse",
        "backup/valkey",
        "backup/nats",
    ]
    for key_str in service_keys:
        matching = [k for k in asset_graph.get_all_asset_keys() if k.to_user_string() == key_str]
        assert matching, f"Asset {key_str} not found"
        parent_keys = asset_graph.get(matching[0]).parent_keys
        parent_strings = {p.to_user_string() for p in parent_keys}
        assert "backup/session" in parent_strings, f"{key_str} should depend on backup/session"


def test_backup_finalize_depends_on_all_services() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()

    finalize_keys = [k for k in asset_graph.get_all_asset_keys() if k.to_user_string() == "backup/finalize"]
    assert finalize_keys
    parent_keys = asset_graph.get(finalize_keys[0]).parent_keys
    parent_strings = {p.to_user_string() for p in parent_keys}

    assert "backup/session" in parent_strings
    assert "backup/postgres" in parent_strings
    assert "backup/milvus" in parent_strings
    assert "backup/neo4j" in parent_strings
    assert "backup/clickhouse" in parent_strings
    assert "backup/valkey" in parent_strings
    assert "backup/nats" in parent_strings


def test_restore_service_assets_depend_on_session() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()

    service_keys = [
        "restore/postgres",
        "restore/milvus",
        "restore/neo4j",
        "restore/clickhouse",
        "restore/valkey",
        "restore/nats",
    ]
    for key_str in service_keys:
        matching = [k for k in asset_graph.get_all_asset_keys() if k.to_user_string() == key_str]
        assert matching, f"Asset {key_str} not found"
        parent_keys = asset_graph.get(matching[0]).parent_keys
        parent_strings = {p.to_user_string() for p in parent_keys}
        assert "restore/session" in parent_strings, f"{key_str} should depend on restore/session"


def test_restore_finalize_depends_on_all_services() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()

    finalize_keys = [k for k in asset_graph.get_all_asset_keys() if k.to_user_string() == "restore/finalize"]
    assert finalize_keys
    parent_keys = asset_graph.get(finalize_keys[0]).parent_keys
    parent_strings = {p.to_user_string() for p in parent_keys}

    assert "restore/session" in parent_strings
    assert "restore/postgres" in parent_strings
    assert "restore/milvus" in parent_strings
    assert "restore/neo4j" in parent_strings
    assert "restore/clickhouse" in parent_strings
    assert "restore/valkey" in parent_strings
    assert "restore/nats" in parent_strings


def test_maintenance_definitions_has_all_cleanup_assets() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()
    all_keys = {key.to_user_string() for key in asset_graph.get_all_asset_keys()}

    assert "maintenance/session" in all_keys
    assert "maintenance/postgres_indexes" in all_keys
    assert "maintenance/postgres_autovacuum_tune" in all_keys
    assert "maintenance/dagster_debug_logs" in all_keys
    assert "maintenance/dagster_info_logs" in all_keys
    assert "maintenance/dagster_warning_logs" in all_keys
    assert "maintenance/dagster_unimportant_events" in all_keys
    assert "maintenance/cleanup_finalize" in all_keys
    assert "maintenance/postgres_repack" in all_keys
    assert "maintenance/repack_finalize" in all_keys


def test_maintenance_jobs_registered() -> None:
    defs = backup_definitions()
    cleanup = defs.get_job_def("dagster_cleanup_job")
    repack = defs.get_job_def("postgres_repack_job")
    assert cleanup.name == "dagster_cleanup_job"
    assert repack.name == "postgres_repack_job"


def test_maintenance_handlers_depend_on_session() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()

    handler_keys = [
        "maintenance/postgres_indexes",
        "maintenance/postgres_autovacuum_tune",
        "maintenance/dagster_debug_logs",
        "maintenance/dagster_info_logs",
        "maintenance/dagster_warning_logs",
        "maintenance/dagster_unimportant_events",
        "maintenance/postgres_repack",
    ]
    for key_str in handler_keys:
        matching = [k for k in asset_graph.get_all_asset_keys() if k.to_user_string() == key_str]
        assert matching, f"Asset {key_str} not found"
        parent_keys = asset_graph.get(matching[0]).parent_keys
        parent_strings = {p.to_user_string() for p in parent_keys}
        assert "maintenance/session" in parent_strings, f"{key_str} should depend on maintenance/session"


def test_cleanup_handlers_depend_on_postgres_indexes() -> None:
    """All other cleanup handlers must run AFTER postgres_indexes.

    - The four DELETE handlers need the partial indexes in place to avoid
      seq-scanning event_logs (originally raised on PR #1040).
    - postgres_autovacuum_tune's ALTER TABLE takes the same
      ShareUpdateExclusiveLock on event_logs as CREATE INDEX CONCURRENTLY;
      running them in parallel deadlocks. ShareUpdateExclusive is compatible
      with RowExclusive (DELETE), so once indexes is done, autovacuum_tune
      can run in parallel with the DELETE handlers.
    """
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()

    handlers_depending_on_indexes = [
        "maintenance/dagster_debug_logs",
        "maintenance/dagster_info_logs",
        "maintenance/dagster_warning_logs",
        "maintenance/dagster_unimportant_events",
        "maintenance/postgres_autovacuum_tune",
    ]
    for key_str in handlers_depending_on_indexes:
        matching = [k for k in asset_graph.get_all_asset_keys() if k.to_user_string() == key_str]
        parent_strings = {p.to_user_string() for p in asset_graph.get(matching[0]).parent_keys}
        assert "maintenance/postgres_indexes" in parent_strings, (
            f"{key_str} must depend on maintenance/postgres_indexes (got parents: {parent_strings})"
        )


def test_postgres_affecting_jobs_carry_mutex_tag() -> None:
    """All jobs that touch Postgres must carry ``postgres-mutex=true`` so the
    QueuedRunCoordinator serializes them. Without the tag, a cleanup tick could
    fire mid-backup (postgres stopped → cleanup queries fail)."""
    defs = backup_definitions()
    for job_name in ("backup_asset_job", "full_restore_job", "dagster_cleanup_job", "postgres_repack_job"):
        job = defs.get_job_def(job_name)
        assert job.tags.get("postgres-mutex") == "true", (
            f"{job_name} is missing the postgres-mutex tag (got tags: {job.tags})"
        )
