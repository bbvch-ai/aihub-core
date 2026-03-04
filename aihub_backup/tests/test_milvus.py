import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.services.milvus import MilvusHandler
from aihub_backup.settings import BackupSettings


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def milvus_handler(settings: BackupSettings) -> MilvusHandler:
    s3 = MagicMock()
    return MilvusHandler(settings, s3)


def test_yaml_escape_backslashes() -> None:
    assert MilvusHandler._yaml_escape(r"pass\word") == r"pass\\word"


def test_yaml_escape_double_quotes() -> None:
    assert MilvusHandler._yaml_escape('pass"word') == 'pass\\"word'


def test_yaml_escape_combined() -> None:
    # Input: pass\"word (backslash then double-quote)
    # Expected: pass\\\\"word (escaped backslash + escaped quote)
    assert MilvusHandler._yaml_escape('pass\\"word') == 'pass\\\\\\"word'


def test_yaml_escape_no_change() -> None:
    assert MilvusHandler._yaml_escape("simple-password-123") == "simple-password-123"


def test_prepare_workdir_substitutes_config(milvus_handler: MilvusHandler, tmp_dir: Path) -> None:
    """_prepare_workdir substitutes all placeholders in the config template."""
    workdir = tmp_dir / "workdir"
    workdir.mkdir()

    # Create a minimal template
    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text(
        'password: "${MILVUS_ROOT_PASSWORD}"\n'
        'accessKeyID: "${AWS_ACCESS_KEY_ID}"\n'
        'secretAccessKey: "${AWS_SECRET_ACCESS_KEY}"\n'
        'backupRootPath: "${BACKUP_ROOT_PATH}"\n'
    )

    with patch("aihub_backup.services.milvus.CONFIG_SOURCE", config_source):
        milvus_handler._prepare_workdir("2026-02-19_02-00-00", workdir)

    config_file = workdir / "configs" / "backup.yaml"
    assert config_file.exists()
    content = config_file.read_text()

    # Verify all placeholders are replaced
    assert "${MILVUS_ROOT_PASSWORD}" not in content
    assert "${AWS_ACCESS_KEY_ID}" not in content
    assert "${AWS_SECRET_ACCESS_KEY}" not in content
    assert "${BACKUP_ROOT_PATH}" not in content

    # Verify actual values are present
    assert "testpass" in content  # MILVUS_ROOT_PASSWORD and S3_STORAGE_SECRET_KEY
    assert "test" in content  # S3_STORAGE_ACCESS_KEY
    assert "2026-02-19_02-00-00" in content  # backup root path


@patch("aihub_backup.services.milvus.subprocess.run")
def test_backup_calls_create_with_correct_name(
    mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path
) -> None:
    """Backup calls milvus-backup create with the expected backup name."""
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.file_exists.return_value = True
    milvus_handler._s3.download_file.side_effect = lambda key, path: path.write_text(
        json.dumps({"collection_backups": []})
    )

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('password: "${MILVUS_ROOT_PASSWORD}"\nbackupRootPath: "${BACKUP_ROOT_PATH}"\n')

    with patch("aihub_backup.services.milvus.CONFIG_SOURCE", config_source):
        milvus_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    create_call = mock_run.call_args_list[0]
    assert create_call[0][0] == ["milvus-backup", "create", "-n", "milvus_backup_2026_02_19_02_00_00"]

    list_call = mock_run.call_args_list[1]
    assert "list" in list_call[0][0]


def test_verify_backup_raises_when_metadata_missing(milvus_handler: MilvusHandler) -> None:
    """Missing full_meta.json raises RuntimeError instead of silently returning."""
    milvus_handler._s3.file_exists.return_value = False

    with pytest.raises(RuntimeError, match="metadata not found"):
        milvus_handler._verify_backup_or_raise("prefix", "backup_name")


@patch("aihub_backup.services.milvus.subprocess.run")
def test_restore_picks_latest_backup_prefix(mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path) -> None:
    """Restore selects the latest backup_ prefix when multiple exist."""
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.list_prefixes.return_value = [
        "2026-02-19_02-00-00/milvus_backup_2026_02_19_02_00_00",
        "2026-02-19_02-00-00/milvus_backup_2026_02_19_03_00_00",
    ]

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('backupRootPath: "${BACKUP_ROOT_PATH}"\n')

    with (
        patch("aihub_backup.services.milvus.CONFIG_SOURCE", config_source),
        patch.object(milvus_handler, "_drop_all_collections"),
    ):
        milvus_handler.restore("2026-02-19_02-00-00")

    # Should use the latest backup name (sorted last)
    restore_call = mock_run.call_args_list[0]
    assert "milvus_backup_2026_02_19_03_00_00" in restore_call[0][0]


def test_verify_milvus_meta_valid(tmp_dir: Path) -> None:
    """Valid metadata with populated segments passes."""
    meta = {
        "collection_backups": [
            {
                "collection_name": "test_coll",
                "db_name": "default",
                "partition_backups": [
                    {
                        "partition_name": "p0",
                        "segment_backups": [
                            {
                                "segment_id": "1",
                                "is_l0": False,
                                "num_of_rows": 100,
                                "binlogs": [{"binlogs": [{"log_path": "data/1"}]}],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    meta_path = tmp_dir / "meta.json"
    meta_path.write_text(json.dumps(meta))
    assert MilvusHandler._verify_milvus_meta(meta_path) is True


def test_verify_milvus_meta_corrupt(tmp_dir: Path) -> None:
    """Segments with missing insert logs fail integrity check."""
    meta = {
        "collection_backups": [
            {
                "collection_name": "test_coll",
                "db_name": "default",
                "partition_backups": [
                    {
                        "partition_name": "p0",
                        "segment_backups": [
                            {
                                "segment_id": "1",
                                "is_l0": False,
                                "num_of_rows": 100,
                                "binlogs": [{"binlogs": []}],  # empty insert logs
                            }
                        ],
                    }
                ],
            }
        ]
    }
    meta_path = tmp_dir / "meta.json"
    meta_path.write_text(json.dumps(meta))
    assert MilvusHandler._verify_milvus_meta(meta_path) is False


def test_verify_milvus_meta_empty(tmp_dir: Path) -> None:
    """Empty Milvus (no collections) passes."""
    meta = {"collection_backups": []}
    meta_path = tmp_dir / "meta.json"
    meta_path.write_text(json.dumps(meta))
    assert MilvusHandler._verify_milvus_meta(meta_path) is True


@patch("aihub_backup.services.milvus.subprocess.run")
def test_restore_drops_all_collections_before_restore(
    mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path
) -> None:
    """Restore drops all existing collections before running milvus-backup restore."""
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.list_prefixes.return_value = [
        "2026-02-19_02-00-00/milvus_backup_2026_02_19_02_00_00",
    ]

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('backupRootPath: "${BACKUP_ROOT_PATH}"\n')

    mock_milvus_client = MagicMock()
    mock_milvus_client.list_collections.return_value = ["coll_old", "coll_new"]

    with (
        patch("aihub_backup.services.milvus.CONFIG_SOURCE", config_source),
        patch("aihub_backup.services.milvus.MilvusClient", return_value=mock_milvus_client) as mock_client_cls,
    ):
        milvus_handler.restore("2026-02-19_02-00-00")

    mock_client_cls.assert_called_once_with(
        uri=f"http://{milvus_handler._settings.MILVUS_HOST}:{milvus_handler._settings.MILVUS_PORT}",
        token=f"root:{milvus_handler._settings.MILVUS_ROOT_PASSWORD.get_secret_value()}",
    )
    assert mock_milvus_client.drop_collection.call_count == 2
    mock_milvus_client.drop_collection.assert_any_call("coll_old")
    mock_milvus_client.drop_collection.assert_any_call("coll_new")
