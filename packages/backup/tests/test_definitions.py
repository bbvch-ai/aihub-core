from swiss_ai_hub.backup.dagster.definitions import backup_definitions


def test_backup_definitions_loads() -> None:
    defs = backup_definitions()
    assert defs is not None


def test_backup_definitions_has_healthcheck_asset() -> None:
    defs = backup_definitions()
    asset_keys = {key.to_user_string() for key in defs.resolve_asset_graph().get_all_asset_keys()}
    assert "backup/healthcheck" in asset_keys
