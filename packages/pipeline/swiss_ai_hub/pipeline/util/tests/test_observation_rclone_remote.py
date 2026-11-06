import hashlib
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from dagster import DagsterInstance, DagsterRun, DagsterRunStatus
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.pipeline.util.observation_rclone_remote import ObservationRcloneRemote

_MODULE = "swiss_ai_hub.pipeline.util.observation_rclone_remote"
_STORED_MODULE = "swiss_ai_hub.pipeline.util.stored_source_configuration"
_RUN_ID = "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"
_RUN_HEX = "0f1e2d3c4b5a69788796a5b4c3d2e1f0"
_TOKEN = '{"access_token":"a","token_type":"Bearer","refresh_token":"r","expiry":"2020-01-01T00:00:00Z"}'


@pytest.fixture
def encryption() -> Iterator[SecretEncryptionService]:
    service = SecretEncryptionService(Fernet.generate_key().decode())
    with patch(f"{_STORED_MODULE}.SecretEncryptionService.from_settings", return_value=service):
        yield service


@pytest.fixture
def row() -> Iterator[MagicMock]:
    bucket = MagicMock(source="rclone", deleting=False, source_configuration={})
    with (
        patch(f"{_STORED_MODULE}.ensure_main_db_connection"),
        patch(f"{_STORED_MODULE}.BucketEntity") as bucket_cls,
    ):
        bucket_cls.get_bucket_by_bucket_name.return_value = bucket
        yield bucket


@pytest.fixture
def client() -> Iterator[MagicMock]:
    rclone = MagicMock()
    with patch(f"{_MODULE}.build_rclone_client", return_value=rclone):
        yield rclone


def _onedrive(encryption: SecretEncryptionService, token: str = _TOKEN) -> dict:
    return {
        "backend_type": "onedrive",
        "root_path": "Docs",
        "include_patterns": ["*.pdf"],
        "onedrive": {"drive_id": "b!abc", "token": encryption.encrypt(token)},
    }


class TestName:
    def test_the_name_extends_the_databases_remote_with_the_run(self):
        assert ObservationRcloneRemote.name_for("hrdocs", "rclone", _RUN_ID) == f"rclone_hrdocs_obs_{_RUN_HEX}"

    def test_another_source_keeps_its_own_prefix(self):
        assert ObservationRcloneRemote.name_for("hrdocs", "acme_sync", _RUN_ID) == f"acme_sync_hrdocs_obs_{_RUN_HEX}"

    def test_a_context_outside_a_real_run_is_refused(self):
        with pytest.raises(ValueError):
            ObservationRcloneRemote.name_for("hrdocs", "rclone", "EPHEMERAL")


class TestOpened:
    def test_the_private_remote_is_created_yielded_with_its_baseline_and_deleted(self, encryption, row, client):
        row.source_configuration = _onedrive(encryption)
        name = f"rclone_hrdocs_obs_{_RUN_HEX}"

        with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID) as remote:
            client.delete_remote.assert_not_called()

        upserted = client.upsert_remote.call_args.args[0]
        assert upserted.name == name
        assert upserted.options["token"] == _TOKEN
        assert upserted.options["token_url"] == "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        assert remote.name == name
        assert remote.fs == f"{name}:Docs"
        assert remote.include_patterns == ["*.pdf"]
        baseline = remote.token_baseline
        assert baseline.path == "onedrive.token"
        assert baseline.backend_type == "onedrive"
        assert baseline.stored_ciphertext == row.source_configuration["onedrive"]["token"]
        assert baseline.sent_digest == hashlib.sha256(_TOKEN.encode()).hexdigest()
        assert baseline.had_refresh_token is True
        client.delete_remote.assert_called_once_with(name)

    def test_a_token_without_a_refresh_token_is_recorded_as_such(self, encryption, row, client):
        row.source_configuration = _onedrive(encryption, token='{"access_token":"a"}')

        with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID) as remote:
            pass

        assert remote.token_baseline.had_refresh_token is False

    def test_a_token_stored_as_plaintext_gives_no_ciphertext_to_compare_against(self, encryption, row, client):
        row.source_configuration = _onedrive(encryption) | {"onedrive": {"drive_id": "b!abc", "token": _TOKEN}}

        with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID) as remote:
            pass

        assert remote.token_baseline.stored_ciphertext is None

    @pytest.mark.parametrize(
        "configuration",
        [
            {"backend_type": "sftp", "sftp": {"host": "h", "user": "u", "password": "pw"}},
            {
                "backend_type": "onedrive",
                "onedrive": {"client_id": "c", "client_secret": "s", "tenant": "t", "drive_id": "d"},
            },
        ],
    )
    def test_a_source_without_a_pasted_token_has_no_baseline(self, encryption, row, client, configuration):
        row.source_configuration = configuration

        with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID) as remote:
            pass

        assert remote.token_baseline is None

    def test_the_remote_is_deleted_when_the_listing_fails(self, encryption, row, client):
        row.source_configuration = _onedrive(encryption)

        with pytest.raises(RuntimeError, match="listing failed"):
            with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID):
                raise RuntimeError("listing failed")

        client.delete_remote.assert_called_once_with(f"rclone_hrdocs_obs_{_RUN_HEX}")

    def test_the_remote_is_deleted_when_creating_it_fails(self, encryption, row, client):
        """rclone writes every parameter into the section before its setup fails, so a failed create still leaves
        the token in the daemon."""
        row.source_configuration = _onedrive(encryption)
        client.upsert_remote.side_effect = ValueError("could not be configured")

        with pytest.raises(ValueError, match="could not be configured"):
            with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID):
                pytest.fail("the body must not run without a remote")

        client.delete_remote.assert_called_once_with(f"rclone_hrdocs_obs_{_RUN_HEX}")

    def test_a_failed_cleanup_keeps_the_original_error_as_its_context(self, encryption, row, client):
        row.source_configuration = _onedrive(encryption)
        client.delete_remote.side_effect = RuntimeError("daemon gone")

        with pytest.raises(RuntimeError, match="daemon gone") as exc_info:
            with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID):
                raise ValueError("listing failed")

        assert isinstance(exc_info.value.__context__, ValueError)
        assert str(exc_info.value.__context__) == "listing failed"

    def test_a_database_this_source_must_not_sync_creates_no_remote(self, encryption, row, client):
        row.deleting = True

        with pytest.raises(ValueError, match="being deleted"):
            with ObservationRcloneRemote.opened("hrdocs", "rclone", _RUN_ID):
                pytest.fail("the body must not run")

        client.upsert_remote.assert_not_called()
        client.delete_remote.assert_not_called()


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


def _run(instance: DagsterInstance, status: DagsterRunStatus) -> str:
    run_id = str(uuid.uuid4())
    instance.add_run(DagsterRun(job_name="rclone_source_observation", run_id=run_id, status=status))
    return uuid.UUID(run_id).hex


class TestSweep:
    def test_only_remotes_of_finished_runs_of_this_source_are_deleted(self, instance, client):
        succeeded = _run(instance, DagsterRunStatus.SUCCESS)
        failed = _run(instance, DagsterRunStatus.FAILURE)
        running = _run(instance, DagsterRunStatus.STARTED)
        unknown = uuid.uuid4().hex
        client.list_remotes.return_value = [
            "rclone_hrdocs",
            f"rclone_hrdocs_obs_{succeeded}",
            f"rclone_sales_obs_{failed}",
            f"rclone_hrdocs_obs_{running}",
            f"rclone_hrdocs_obs_{unknown}",
            f"acme_sync_hrdocs_obs_{succeeded}",
            f"rclone_hr_docs_obs_{succeeded}",
            f"rclone_hrdocs_obs_{succeeded}x",
            f"rclone_hrdocs_obs_{succeeded.upper()}",
        ]

        swept = ObservationRcloneRemote.sweep(instance, "rclone")

        assert swept == 2
        assert [call.args[0] for call in client.delete_remote.call_args_list] == [
            f"rclone_hrdocs_obs_{succeeded}",
            f"rclone_sales_obs_{failed}",
        ]

    def test_the_source_is_matched_literally(self, instance, client):
        finished = _run(instance, DagsterRunStatus.CANCELED)
        client.list_remotes.return_value = [f"aXb_hrdocs_obs_{finished}", f"a.b_hrdocs_obs_{finished}"]

        swept = ObservationRcloneRemote.sweep(instance, "a.b")

        assert swept == 1
        client.delete_remote.assert_called_once_with(f"a.b_hrdocs_obs_{finished}")

    def test_nothing_to_sweep_deletes_nothing(self, instance, client):
        client.list_remotes.return_value = []

        assert ObservationRcloneRemote.sweep(instance, "rclone") == 0
        client.delete_remote.assert_not_called()
