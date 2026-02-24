import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.services.milvus import MilvusHandler, _verify_milvus_meta, _yaml_escape
from aihub_backup.settings import BackupSettings


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def milvus_handler(settings: BackupSettings) -> MilvusHandler:
    s3 = MagicMock()
    return MilvusHandler(settings, s3)


def test_yaml_escape_backslashes() -> None:
    assert _yaml_escape(r"pass\word") == r"pass\\word"


def test_yaml_escape_double_quotes() -> None:
    assert _yaml_escape('pass"word') == 'pass\\"word'


def test_yaml_escape_combined() -> None:
    # Input: pass\"word (backslash then double-quote)
    # Expected: pass\\\\"word (escaped backslash + escaped quote)
    assert _yaml_escape('pass\\"word') == 'pass\\\\\\"word'


def test_yaml_escape_no_change() -> None:
    assert _yaml_escape("simple-password-123") == "simple-password-123"


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
        milvus_handler._prepare_workdir("2026-02-19_02-00-00_online", workdir)

    config_file = workdir / "configs" / "backup.yaml"
    assert config_file.exists()
    content = config_file.read_text()

    # Verify all placeholders are replaced
    assert "${MILVUS_ROOT_PASSWORD}" not in content
    assert "${AWS_ACCESS_KEY_ID}" not in content
    assert "${AWS_SECRET_ACCESS_KEY}" not in content
    assert "${BACKUP_ROOT_PATH}" not in content

    # Verify actual values are present
    assert "testpass" in content  # MILVUS_ROOT_PASSWORD and AWS_SECRET_ACCESS_KEY
    assert "test" in content  # AWS_ACCESS_KEY_ID
    assert "2026-02-19_02-00-00_online" in content  # backup root path


@patch("aihub_backup.services.milvus.subprocess.run")
def test_backup_calls_milvus_backup_create(mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path) -> None:
    """Backup calls milvus-backup create with correct name."""
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.file_exists.return_value = False

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('password: "${MILVUS_ROOT_PASSWORD}"\nbackupRootPath: "${BACKUP_ROOT_PATH}"\n')

    with patch("aihub_backup.services.milvus.CONFIG_SOURCE", config_source):
        milvus_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00_online")

    # First call should be "create"
    create_call = mock_run.call_args_list[0]
    assert "create" in create_call[0][0]
    assert "-n" in create_call[0][0]


@patch("aihub_backup.services.milvus.subprocess.run")
def test_restore_picks_latest_backup_prefix(mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path) -> None:
    """Restore selects the latest backup_ prefix when multiple exist."""
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.list_prefixes.return_value = [
        "2026-02-19_02-00-00_online/milvus_backup_2026_02_19_02_00_00",
        "2026-02-19_02-00-00_online/milvus_backup_2026_02_19_03_00_00",
    ]

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('backupRootPath: "${BACKUP_ROOT_PATH}"\n')

    with patch("aihub_backup.services.milvus.CONFIG_SOURCE", config_source):
        milvus_handler.restore("2026-02-19_02-00-00_online")

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
    assert _verify_milvus_meta(meta_path) is True


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
    assert _verify_milvus_meta(meta_path) is False


def test_verify_milvus_meta_empty(tmp_dir: Path) -> None:
    """Empty Milvus (no collections) passes."""
    meta = {"collection_backups": []}
    meta_path = tmp_dir / "meta.json"
    meta_path.write_text(json.dumps(meta))
    assert _verify_milvus_meta(meta_path) is True
