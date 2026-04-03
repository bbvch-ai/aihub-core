from swiss_ai_hub.backup.dagster.definitions import backup_definitions


def test_backup_definitions_loads() -> None:
    defs = backup_definitions()
    assert defs is not None


def test_backup_definitions_has_session_and_finalize_assets() -> None:
    defs = backup_definitions()
    asset_graph = defs.resolve_asset_graph()
    all_keys = {key.to_user_string() for key in asset_graph.get_all_asset_keys()}

    assert "backup/session" in all_keys
    assert "backup/finalize" in all_keys


def test_backup_definitions_has_job() -> None:
    defs = backup_definitions()
    job = defs.get_job_def("backup_asset_job")
    assert job is not None
    assert job.name == "backup_asset_job"
