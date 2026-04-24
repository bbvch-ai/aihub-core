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
