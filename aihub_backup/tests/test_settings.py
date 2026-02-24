import pytest
from pydantic import ValidationError

from aihub_backup.settings import BackupSettings

# All secret fields that must be provided explicitly
_REQUIRED_SECRETS = {
    "PGPASSWORD": "x",
    "PGPASSWORD_FERRETDB": "x",
    "MILVUS_ROOT_PASSWORD": "x",
    "CLICKHOUSE_PASSWORD": "x",
    "REDIS_TOKEN": "x",
    "NATS_TOKEN": "x",
    "AWS_SECRET_ACCESS_KEY": "x",
}


def test_default_settings() -> None:
    settings = BackupSettings(**_REQUIRED_SECRETS)  # type: ignore[arg-type]
    assert settings.BACKUP_RETENTION_DAYS == 7
    assert settings.BACKUP_S3_BUCKET == "backups"
    assert settings.POSTGRES_HOST == "postgres"
    assert settings.BACKUP_SKIP_MILVUS_ONLINE is False
    assert settings.BACKUP_SKIP_MILVUS_OFFLINE is False
    assert settings.VALKEY_CONTAINER == "valkey"
    assert settings.NATS_URL == "nats://nats:4222"


def test_secret_fields_are_masked() -> None:
    settings = BackupSettings(**{**_REQUIRED_SECRETS, "PGPASSWORD": "my-secret"})  # type: ignore[arg-type]
    # SecretStr should not reveal the value in string representation
    assert "my-secret" not in str(settings.PGPASSWORD)
    assert settings.PGPASSWORD.get_secret_value() == "my-secret"


def test_missing_secrets_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        BackupSettings()  # type: ignore[call-arg]


def test_negative_retention_days_rejected() -> None:
    with pytest.raises(ValidationError, match="BACKUP_RETENTION_DAYS"):
        BackupSettings(**{**_REQUIRED_SECRETS, "BACKUP_RETENTION_DAYS": -1})  # type: ignore[arg-type]
