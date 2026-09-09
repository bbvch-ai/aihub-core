from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.util.source_builders import (
    rclone_remote_for_bucket,
    remote_name_for_bucket,
    source_config_for_bucket,
)

_MODULE = "swiss_ai_hub.pipeline.util.source_builders"


@pytest.fixture
def encryption() -> SecretEncryptionService:
    service = SecretEncryptionService(Fernet.generate_key().decode())
    with patch(f"{_MODULE}.SecretEncryptionService.from_settings", return_value=service):
        yield service


def _bucket(source: str | None = "rclone", deleting: bool = False, configuration: dict | None = None) -> MagicMock:
    return MagicMock(source=source, deleting=deleting, source_configuration=configuration or {})


@pytest.fixture
def bucket_lookup():
    with patch(f"{_MODULE}.ensure_main_db_connection"), patch(f"{_MODULE}.BucketEntity") as bucket_cls:
        yield bucket_cls.get_bucket_by_bucket_name


class TestSourceConfigForBucket:
    def test_secrets_are_decrypted_and_the_row_validates_into_the_config(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(
            configuration={
                "backend_type": "sftp",
                "sftp": {"host": "h", "user": "u", "password": encryption.encrypt("pw")},
            }
        )

        config = source_config_for_bucket("hrdocs", "rclone", RcloneSyncConfig)

        assert config.sftp.password == "pw"
        assert config.backend_type == "sftp"

    def test_a_database_filled_by_another_source_is_refused(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(source="acme_sync")

        with pytest.raises(ValueError, match="filled by source 'acme_sync'"):
            source_config_for_bucket("hrdocs", "rclone", RcloneSyncConfig)

    def test_a_database_being_deleted_is_refused(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(deleting=True)

        with pytest.raises(ValueError, match="being deleted"):
            source_config_for_bucket("hrdocs", "rclone", RcloneSyncConfig)


class TestRcloneRemoteForBucket:
    def test_the_remote_is_rebuilt_on_every_call_from_the_stored_configuration(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(
            configuration={
                "backend_type": "sftp",
                "root_path": "/srv/docs/",
                "include_patterns": ["*.pdf"],
                "sftp": {"host": "h", "user": "u", "password": encryption.encrypt("pw")},
            }
        )
        client = MagicMock()
        with patch(f"{_MODULE}.build_rclone_client", return_value=client):
            remote = rclone_remote_for_bucket("hrdocs", "rclone")
            rclone_remote_for_bucket("hrdocs", "rclone")

        assert client.upsert_remote.call_count == 2
        upserted = client.upsert_remote.call_args.args[0]
        assert upserted.name == remote_name_for_bucket("hrdocs", "rclone") == "rclone_hrdocs"
        assert upserted.options["pass"] == "pw", "the daemon receives the plaintext, the row never held it"
        assert remote.fs == "rclone_hrdocs:srv/docs"
        assert remote.include_patterns == ["*.pdf"]
