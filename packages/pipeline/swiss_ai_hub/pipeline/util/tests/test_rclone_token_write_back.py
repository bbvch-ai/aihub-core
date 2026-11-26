import logging
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote
from swiss_ai_hub.pipeline.types.rclone_token_baseline import RcloneTokenBaseline
from swiss_ai_hub.pipeline.util.rclone_token_write_back import RcloneTokenWriteBack

_MODULE = "swiss_ai_hub.pipeline.util.rclone_token_write_back"
_REMOTE = "rclone_hrdocs_obs_0f1e2d3c4b5a69788796a5b4c3d2e1f0"
_SENT = '{"access_token":"SENTACCESS","refresh_token":"SENTREFRESH","expiry":"2020-01-01T00:00:00Z"}'
_REFRESHED = (
    '{"access_token":"NEWACCESS","token_type":"Bearer","refresh_token":"NEWREFRESH","expiry":"2026-11-06T12:00:00Z"}'
)
_SECRETS = ("SENTACCESS", "SENTREFRESH", "NEWACCESS", "NEWREFRESH")


@pytest.fixture
def encryption() -> Iterator[SecretEncryptionService]:
    service = SecretEncryptionService(Fernet.generate_key().decode())
    with patch(f"{_MODULE}.SecretEncryptionService.from_settings", return_value=service):
        yield service


@pytest.fixture
def client() -> Iterator[MagicMock]:
    rclone = MagicMock()
    with patch(f"{_MODULE}.build_rclone_client", return_value=rclone):
        yield rclone


@pytest.fixture
def replace() -> Iterator[MagicMock]:
    with patch(f"{_MODULE}.ensure_main_db_connection"), patch(f"{_MODULE}.BucketEntity") as bucket_cls:
        bucket_cls.replace_source_secret.return_value = True
        yield bucket_cls.replace_source_secret


def _remote(encryption: SecretEncryptionService, sent: str = _SENT, *, path: str = "onedrive.token") -> RcloneRemote:
    baseline = RcloneTokenBaseline.from_token(
        path=path, backend_type=path.split(".")[0], stored_value=encryption.encrypt(sent), sent_token=sent
    )
    return RcloneRemote(name=_REMOTE, fs=f"{_REMOTE}:", token_baseline=baseline)


def _assert_no_secret_in(text: str) -> None:
    for secret in _SECRETS:
        assert secret not in text


class TestPersistRefreshedToken:
    def test_a_refreshed_token_is_stored_encrypted_over_the_value_this_run_read(
        self, encryption, client, replace, caplog
    ):
        remote = _remote(encryption)
        client.get_token.return_value = SecretStr(_REFRESHED)

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote) is True

        client.get_token.assert_called_once_with(_REMOTE)
        arguments = replace.call_args.kwargs
        assert arguments["bucket_name"] == "hrdocs"
        assert arguments["source"] == "rclone"
        assert arguments["backend_type"] == "onedrive"
        assert arguments["path"] == "onedrive.token"
        assert arguments["expected"] == remote.token_baseline.stored_ciphertext
        assert SecretEncryptionService.is_encrypted(arguments["replacement"])
        assert encryption.decrypt(arguments["replacement"]) == _REFRESHED
        assert f"Stored the refreshed OAuth token of rclone remote '{_REMOTE}'" in caplog.text
        _assert_no_secret_in(caplog.text)

    def test_an_unchanged_token_is_not_written(self, encryption, client, replace, caplog):
        client.get_token.return_value = SecretStr(_SENT)

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", _remote(encryption)) is False

        replace.assert_not_called()
        assert "unchanged" in caplog.text

    def test_a_database_edited_since_the_run_read_it_keeps_its_token(self, encryption, client, replace, caplog):
        client.get_token.return_value = SecretStr(_REFRESHED)
        replace.return_value = False

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", _remote(encryption)) is False

        assert "Kept the database's OAuth token" in caplog.text
        _assert_no_secret_in(caplog.text)

    def test_a_token_that_lost_its_refresh_token_is_refused(self, encryption, client, replace, caplog):
        client.get_token.return_value = SecretStr('{"access_token":"NEWACCESS","expiry":"2026-11-06T12:00:00Z"}')

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", _remote(encryption)) is False

        replace.assert_not_called()
        assert "Refused" in caplog.text
        _assert_no_secret_in(caplog.text)

    def test_a_token_that_never_had_a_refresh_token_may_be_stored_without_one(self, encryption, client, replace):
        client.get_token.return_value = SecretStr('{"access_token":"NEWACCESS"}')
        remote = _remote(encryption, sent='{"access_token":"SENTACCESS"}')

        assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote) is True

    def test_a_token_stored_as_plaintext_is_not_written_back(self, encryption, client, replace, caplog):
        client.get_token.return_value = SecretStr(_REFRESHED)
        baseline = RcloneTokenBaseline.from_token(
            path="onedrive.token", backend_type="onedrive", stored_value=_SENT, sent_token=_SENT
        )
        remote = RcloneRemote(name=_REMOTE, fs=f"{_REMOTE}:", token_baseline=baseline)

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote) is False

        replace.assert_not_called()
        assert "not stored encrypted" in caplog.text
        _assert_no_secret_in(caplog.text)

    def test_a_remote_that_no_longer_holds_a_token_writes_nothing(self, encryption, client, replace, caplog):
        client.get_token.return_value = None

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", _remote(encryption)) is False

        replace.assert_not_called()
        assert "holds no OAuth token" in caplog.text

    def test_a_remote_without_a_baseline_is_not_asked_for_a_token(self, client, replace):
        remote = RcloneRemote(name=_REMOTE, fs=f"{_REMOTE}:")

        assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote) is False

        client.get_token.assert_not_called()
        replace.assert_not_called()

    def test_a_drive_token_sent_on_one_line_is_unchanged_until_rclone_refreshes_it(self, encryption, client, replace):
        """The Drive form re-serialises a pasted token on one line; the baseline is the line rclone was given, so a
        pretty-printed paste is not mistaken for a refresh."""
        config = RcloneSyncConfig.model_validate(
            {
                "backend_type": "drive",
                "drive": {"token": '{\n  "access_token": "SENTACCESS",\n  "refresh_token": "R"\n}'},
            }
        )
        sent = config.to_rclone_source_config("r").options["token"]
        client.get_token.return_value = SecretStr(sent)

        remote = _remote(encryption, sent=sent, path="drive.token")
        assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote) is False

        client.get_token.return_value = SecretStr('{"access_token":"NEWACCESS","refresh_token":"R"}')
        assert RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote) is True
        assert replace.call_args.kwargs["path"] == "drive.token"
        assert replace.call_args.kwargs["backend_type"] == "drive"

    def test_a_failing_database_write_raises_without_quoting_the_token(self, encryption, client, replace):
        client.get_token.return_value = SecretStr(_REFRESHED)
        replace.side_effect = RuntimeError("connection refused")
        remote = _remote(encryption)

        with pytest.raises(RuntimeError) as exc_info:
            RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote)

        _assert_no_secret_in(str(exc_info.value))

    def test_a_token_rclone_returns_that_is_not_json_raises_without_quoting_it(self, encryption, client, replace):
        client.get_token.return_value = SecretStr("NEWACCESS not json")
        remote = _remote(encryption)

        with pytest.raises(ValueError) as exc_info:
            RcloneTokenWriteBack.persist_refreshed_token("hrdocs", "rclone", remote)

        _assert_no_secret_in(str(exc_info.value))
        replace.assert_not_called()

    def test_the_baseline_shows_neither_digest_nor_ciphertext(self, encryption):
        baseline = _remote(encryption).token_baseline

        assert baseline.stored_ciphertext not in repr(baseline)
        assert baseline.sent_digest not in repr(baseline)
