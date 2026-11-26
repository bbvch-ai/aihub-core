from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.util.stored_source_configuration import StoredSourceConfiguration

_MODULE = "swiss_ai_hub.pipeline.util.stored_source_configuration"


@pytest.fixture
def encryption() -> SecretEncryptionService:
    service = SecretEncryptionService(Fernet.generate_key().decode())
    with patch(f"{_MODULE}.SecretEncryptionService.from_settings", return_value=service):
        yield service


@pytest.fixture
def bucket_lookup():
    with patch(f"{_MODULE}.ensure_main_db_connection"), patch(f"{_MODULE}.BucketEntity") as bucket_cls:
        yield bucket_cls.get_bucket_by_bucket_name


class TestRead:
    def test_one_read_gives_the_decrypted_config_and_the_stored_ciphertext(self, encryption, bucket_lookup):
        ciphertext = encryption.encrypt('{"access_token":"a","refresh_token":"r"}')
        bucket_lookup.return_value = MagicMock(
            source="rclone",
            deleting=False,
            source_configuration={"backend_type": "onedrive", "onedrive": {"drive_id": "d", "token": ciphertext}},
        )

        stored = StoredSourceConfiguration[RcloneSyncConfig].read("hrdocs", "rclone", RcloneSyncConfig)

        assert bucket_lookup.call_count == 1
        assert isinstance(stored.config, RcloneSyncConfig)
        assert stored.config.onedrive.token == '{"access_token":"a","refresh_token":"r"}'
        assert stored.stored["onedrive"]["token"] == ciphertext

    def test_neither_the_secret_nor_its_ciphertext_shows_in_the_repr(self, encryption, bucket_lookup):
        ciphertext = encryption.encrypt("TOPSECRET")
        bucket_lookup.return_value = MagicMock(
            source="rclone",
            deleting=False,
            source_configuration={"backend_type": "s3", "s3": {"access_key_id": "a", "secret_access_key": ciphertext}},
        )

        stored = StoredSourceConfiguration[RcloneSyncConfig].read("hrdocs", "rclone", RcloneSyncConfig)

        assert "TOPSECRET" not in repr(stored)
        assert ciphertext not in repr(stored)

    @pytest.mark.parametrize(
        ("row", "message"),
        [
            ({"source": "acme_sync", "deleting": False}, "filled by source 'acme_sync'"),
            ({"source": "rclone", "deleting": True}, "being deleted"),
        ],
    )
    def test_a_database_this_source_must_not_sync_is_refused(self, encryption, bucket_lookup, row, message):
        bucket_lookup.return_value = MagicMock(source_configuration={}, **row)

        with pytest.raises(ValueError, match=message):
            StoredSourceConfiguration[RcloneSyncConfig].read("hrdocs", "rclone", RcloneSyncConfig)
