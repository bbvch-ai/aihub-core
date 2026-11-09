import socket
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
_STORED_MODULE = "swiss_ai_hub.pipeline.util.stored_source_configuration"


@pytest.fixture
def encryption() -> SecretEncryptionService:
    service = SecretEncryptionService(Fernet.generate_key().decode())
    with patch(f"{_STORED_MODULE}.SecretEncryptionService.from_settings", return_value=service):
        yield service


def _bucket(source: str | None = "rclone", deleting: bool = False, configuration: dict | None = None) -> MagicMock:
    return MagicMock(source=source, deleting=deleting, source_configuration=configuration or {})


@pytest.fixture
def bucket_lookup():
    with patch(f"{_STORED_MODULE}.ensure_main_db_connection"), patch(f"{_STORED_MODULE}.BucketEntity") as bucket_cls:
        yield bucket_cls.get_bucket_by_bucket_name


class TestSourceConfigForBucket:
    def test_secrets_are_decrypted_and_the_row_validates_into_the_config(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(
            configuration={
                "backend_type": "s3",
                "s3": {"access_key_id": "id", "secret_access_key": encryption.encrypt("pw")},
            }
        )

        config = source_config_for_bucket("hrdocs", "rclone", RcloneSyncConfig)

        assert config.s3.secret_access_key == "pw"
        assert config.backend_type == "s3"

    def test_a_database_filled_by_another_source_is_refused(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(source="acme_sync")

        with pytest.raises(ValueError, match="filled by source 'acme_sync'"):
            source_config_for_bucket("hrdocs", "rclone", RcloneSyncConfig)

    def test_a_database_being_deleted_is_refused(self, encryption, bucket_lookup):
        bucket_lookup.return_value = _bucket(deleting=True)

        with pytest.raises(ValueError, match="being deleted"):
            source_config_for_bucket("hrdocs", "rclone", RcloneSyncConfig)


class TestRcloneRemoteForBucket:
    def test_the_remote_is_rebuilt_from_the_stored_configuration_once_per_process(self, encryption, bucket_lookup):
        rclone_remote_for_bucket.cache_clear()
        bucket_lookup.return_value = _bucket(
            configuration={
                "backend_type": "s3",
                "root_path": "/srv/docs/",
                "include_patterns": ["*.pdf"],
                "s3": {"access_key_id": "id", "secret_access_key": encryption.encrypt("pw")},
            }
        )
        client = MagicMock()
        with patch(f"{_MODULE}.build_rclone_client", return_value=client):
            remote = rclone_remote_for_bucket("hrdocs", "rclone")
            rclone_remote_for_bucket("hrdocs", "rclone")

        assert client.upsert_remote.call_count == 1, "the second call within the process reuses the remote"
        upserted = client.upsert_remote.call_args.args[0]
        assert upserted.name == remote_name_for_bucket("hrdocs", "rclone") == "rclone_hrdocs"
        assert upserted.options["secret_access_key"] == "pw", "the daemon receives the plaintext, the row never held it"
        assert remote.fs == "rclone_hrdocs:srv/docs"
        assert remote.include_patterns == ["*.pdf"]


class TestOnlyPublicEndpoints:
    @pytest.fixture(autouse=True)
    def _fresh_cache(self, monkeypatch: pytest.MonkeyPatch):
        rclone_remote_for_bucket.cache_clear()
        monkeypatch.setenv("RCLONE_PIPELINE_ALLOWED_PRIVATE_HOSTS", "")
        yield
        rclone_remote_for_bucket.cache_clear()

    def _s3_bucket(self, encryption: SecretEncryptionService, endpoint: str) -> MagicMock:
        return _bucket(
            configuration={
                "backend_type": "s3",
                "s3": {
                    "provider": "Minio",
                    "endpoint": endpoint,
                    "access_key_id": "id",
                    "secret_access_key": encryption.encrypt("pw"),
                },
            }
        )

    @pytest.mark.parametrize(
        "endpoint", ["http://seaweedfs-s3:9000", "seaweedfs-filer:8888", "http://127.0.0.1:5572", "10.0.0.5"]
    )
    def test_an_internal_endpoint_never_reaches_the_daemon(self, encryption, bucket_lookup, endpoint: str):
        bucket_lookup.return_value = self._s3_bucket(encryption, endpoint)
        client = MagicMock()

        with (
            patch(f"{_MODULE}.build_rclone_client", return_value=client),
            pytest.raises(ValueError, match="RCLONE_PIPELINE_ALLOWED_PRIVATE_HOSTS"),
        ):
            rclone_remote_for_bucket("hrdocs", "rclone")

        client.upsert_remote.assert_not_called()

    def test_an_endpoint_the_deployment_allows_is_used(self, encryption, bucket_lookup, monkeypatch):
        monkeypatch.setenv("RCLONE_PIPELINE_ALLOWED_PRIVATE_HOSTS", "minio.intra")
        bucket_lookup.return_value = self._s3_bucket(encryption, "http://minio.intra:9000")
        client = MagicMock()

        with patch(f"{_MODULE}.build_rclone_client", return_value=client):
            rclone_remote_for_bucket("hrdocs", "rclone")

        assert client.upsert_remote.call_args.args[0].options["endpoint"] == "http://minio.intra:9000"


class TestOnlyTheEndpointHostIsContacted:
    """In virtual-hosted style rclone would contact `<bucket>.<endpoint host>`, a name the endpoint's owner can point
    anywhere, so a remote with an endpoint is sent with a path-style provider and only the endpoint host is checked."""

    @pytest.fixture(autouse=True)
    def _fresh_cache(self, monkeypatch: pytest.MonkeyPatch):
        rclone_remote_for_bucket.cache_clear()
        monkeypatch.setenv("RCLONE_PIPELINE_ALLOWED_PRIVATE_HOSTS", "")
        yield
        rclone_remote_for_bucket.cache_clear()

    @pytest.fixture
    def looked_up(self) -> list[str]:
        return []

    @pytest.fixture
    def dns(self, monkeypatch: pytest.MonkeyPatch, looked_up: list[str]) -> dict[str, list[str]]:
        """What each host name resolves to; a name missing here does not resolve."""
        answers: dict[str, list[str]] = {}

        def getaddrinfo(host: str, port: int, **_: object) -> list[tuple]:
            looked_up.append(host)
            if host not in answers:
                raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port)) for ip in answers[host]]

        monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
        return answers

    def _s3_bucket(self, encryption: SecretEncryptionService, provider: str, endpoint: str) -> MagicMock:
        return _bucket(
            configuration={
                "backend_type": "s3",
                "root_path": "docs/hr",
                "s3": {
                    "provider": provider,
                    "endpoint": endpoint,
                    "access_key_id": "id",
                    "secret_access_key": encryption.encrypt("pw"),
                },
            }
        )

    def test_a_virtual_hosted_provider_reaches_the_daemon_as_path_style(
        self, encryption, bucket_lookup, dns, looked_up
    ):
        dns["ep.attacker.example"] = ["93.184.216.34"]
        dns["docs.ep.attacker.example"] = ["10.0.0.5"]
        bucket_lookup.return_value = self._s3_bucket(encryption, "AWS", "http://ep.attacker.example:9000")
        client = MagicMock()

        with patch(f"{_MODULE}.build_rclone_client", return_value=client):
            rclone_remote_for_bucket("hrdocs", "rclone")

        assert client.upsert_remote.call_args.args[0].options["provider"] == "Other"
        assert looked_up == ["ep.attacker.example"]

    def test_an_allowed_path_style_endpoint_behind_wildcard_dns_is_used(
        self, encryption, bucket_lookup, dns, monkeypatch
    ):
        """rclone never contacts the bucket subdomain of a path-style store, so what it resolves to does not matter."""
        monkeypatch.setenv("RCLONE_PIPELINE_ALLOWED_PRIVATE_HOSTS", "minio.intra.acme.ch")
        dns["minio.intra.acme.ch"] = ["10.1.2.2"]
        dns["docs.minio.intra.acme.ch"] = ["10.1.2.3"]
        bucket_lookup.return_value = self._s3_bucket(encryption, "Minio", "https://minio.intra.acme.ch")
        client = MagicMock()

        with patch(f"{_MODULE}.build_rclone_client", return_value=client):
            rclone_remote_for_bucket("hrdocs", "rclone")

        assert client.upsert_remote.call_args.args[0].options["provider"] == "Minio"
