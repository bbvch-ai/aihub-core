import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.services.milvus import MilvusHandler
from swiss_ai_hub.backup.settings import BackupSettings


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
    assert MilvusHandler._yaml_escape('pass\\"word') == 'pass\\\\\\"word'


def test_yaml_escape_no_change() -> None:
    assert MilvusHandler._yaml_escape("simple-password-123") == "simple-password-123"


def test_prepare_workdir_substitutes_config(milvus_handler: MilvusHandler, tmp_dir: Path) -> None:
    workdir = tmp_dir / "workdir"
    workdir.mkdir()

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text(
        'password: "${MILVUS_ROOT_PASSWORD}"\n'
        'accessKeyID: "${AWS_ACCESS_KEY_ID}"\n'
        'secretAccessKey: "${AWS_SECRET_ACCESS_KEY}"\n'
        'backupRootPath: "${BACKUP_ROOT_PATH}"\n'
    )

    with patch("swiss_ai_hub.backup.services.milvus.CONFIG_SOURCE", config_source):
        milvus_handler._prepare_workdir("2026-02-19_02-00-00", workdir)

    config_file = workdir / "configs" / "backup.yaml"
    assert config_file.exists()
    content = config_file.read_text()

    assert "${MILVUS_ROOT_PASSWORD}" not in content
    assert "${AWS_ACCESS_KEY_ID}" not in content
    assert "${AWS_SECRET_ACCESS_KEY}" not in content
    assert "${BACKUP_ROOT_PATH}" not in content

    assert "testpass" in content
    assert "test" in content
    assert "2026-02-19_02-00-00" in content


@patch("swiss_ai_hub.backup.services.milvus.subprocess.run")
def test_backup_calls_create_with_correct_name(
    mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path
) -> None:
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.file_exists.return_value = True
    milvus_handler._s3.download_file.side_effect = lambda key, path: path.write_text(
        json.dumps({"collection_backups": []})
    )

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('password: "${MILVUS_ROOT_PASSWORD}"\nbackupRootPath: "${BACKUP_ROOT_PATH}"\n')

    with patch("swiss_ai_hub.backup.services.milvus.CONFIG_SOURCE", config_source):
        milvus_handler.backup("2026-02-19_02-00-00", "2026-02-19_02-00-00")

    create_call = mock_run.call_args_list[0]
    assert create_call[0][0] == ["milvus-backup", "create", "-n", "milvus_backup_2026_02_19_02_00_00"]

    list_call = mock_run.call_args_list[1]
    assert "list" in list_call[0][0]


def test_verify_backup_raises_when_metadata_missing(milvus_handler: MilvusHandler) -> None:
    milvus_handler._s3.file_exists.return_value = False

    with pytest.raises(RuntimeError, match="metadata not found"):
        milvus_handler._verify_backup_or_raise("prefix", "backup_name")


@patch("swiss_ai_hub.backup.services.milvus.subprocess.run")
def test_restore_picks_latest_backup_prefix(mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path) -> None:
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.list_prefixes.return_value = [
        "2026-02-19_02-00-00/milvus_backup_2026_02_19_02_00_00",
        "2026-02-19_02-00-00/milvus_backup_2026_02_19_03_00_00",
    ]

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('backupRootPath: "${BACKUP_ROOT_PATH}"\n')

    with (
        patch("swiss_ai_hub.backup.services.milvus.CONFIG_SOURCE", config_source),
        patch.object(milvus_handler, "_drop_all_collections"),
    ):
        milvus_handler.restore("2026-02-19_02-00-00")

    restore_call = mock_run.call_args_list[0]
    assert "milvus_backup_2026_02_19_03_00_00" in restore_call[0][0]


def test_verify_milvus_meta_valid(tmp_dir: Path) -> None:
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
                                "binlogs": [{"binlogs": []}],
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
    meta = {"collection_backups": []}
    meta_path = tmp_dir / "meta.json"
    meta_path.write_text(json.dumps(meta))
    assert MilvusHandler._verify_milvus_meta(meta_path) is True


@patch("swiss_ai_hub.backup.services.milvus.subprocess.run")
def test_restore_drops_all_collections_before_restore(
    mock_run: MagicMock, milvus_handler: MilvusHandler, tmp_dir: Path
) -> None:
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    milvus_handler._s3.list_prefixes.return_value = [
        "2026-02-19_02-00-00/milvus_backup_2026_02_19_02_00_00",
    ]

    config_source = tmp_dir / "config-template.yaml"
    config_source.write_text('backupRootPath: "${BACKUP_ROOT_PATH}"\n')

    mock_milvus_client = MagicMock()
    mock_milvus_client.list_collections.return_value = ["coll_old", "coll_new"]

    with (
        patch("swiss_ai_hub.backup.services.milvus.CONFIG_SOURCE", config_source),
        patch("swiss_ai_hub.backup.services.milvus.MilvusClient", return_value=mock_milvus_client) as mock_client_cls,
    ):
        milvus_handler.restore("2026-02-19_02-00-00")

    mock_client_cls.assert_called_once_with(
        uri=f"http://{milvus_handler._settings.MILVUS_HOST}:{milvus_handler._settings.MILVUS_PORT}",
        token=f"root:{milvus_handler._settings.MILVUS_ROOT_PASSWORD.get_secret_value()}",
    )
    assert mock_milvus_client.drop_collection.call_count == 2
    mock_milvus_client.drop_collection.assert_any_call("coll_old")
    mock_milvus_client.drop_collection.assert_any_call("coll_new")
