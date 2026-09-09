from functools import cache
from typing import Annotated

from swiss_ai_hub.core.persistence import BucketEntity
from swiss_ai_hub.core.secrets import SecretEncryptionService
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.pipeline.resources.rclone.rclone_client import RcloneClient
from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

"""Per-database source builders for the rclone source pipeline.

One deployed code location fills every database whose ``source`` names it, so nothing source-specific can be baked
into resources at ``Definitions``-build time. The target database is resolved per run (from the composite partition
key on the partitioned write path, from the ``aihub/bucket`` run tag on the observe/remove path) and its source
configuration is read from the row here. Unlike ``ingestor_config_for_bucket`` there are no deployment defaults to
fall back to: a database without a valid source configuration must not sync from anything.
"""


def source_config_for_bucket[TConfig: SourcePipelineConfig](
    bucket: Annotated[str, "Bucket name of the knowledge database"],
    source: Annotated[str, "Source pipeline id this code location runs as"],
    config_type: type[TConfig],
) -> TConfig:
    """The database's stored source configuration, secrets decrypted, validated into the pipeline's config class."""
    ensure_main_db_connection()
    entity = BucketEntity.get_bucket_by_bucket_name(bucket)
    if entity.deleting:
        raise ValueError(f"Knowledge database '{bucket}' is being deleted and must not be synced.")
    if entity.source != source:
        raise ValueError(f"Knowledge database '{bucket}' is filled by source '{entity.source}', not '{source}'.")
    decrypted = SecretEncryptionService.from_settings().decrypt_paths(
        entity.source_configuration, config_type.secret_field_paths()
    )
    return config_type.model_validate(decrypted)


def remote_name_for_bucket(bucket: str, source: str) -> str:
    """One remote per database, prefixed with the source so two rclone-backed pipelines never share a daemon entry."""
    return f"{source}_{bucket}"


@cache
def rclone_remote_for_bucket(bucket: str, source: str) -> RcloneRemote:
    """Rebuilds the database's remote in the rclone daemon from the stored configuration and returns how to address it.

    Rebuilding it in every process is what makes a credential edit apply on the next run and a restarted daemon
    (which keeps no config file) need no operator action. Cached per process because every op of a partition run
    loads its input through the IO manager and would otherwise re-upsert the same remote three times per file.
    """
    config = source_config_for_bucket(bucket, source, RcloneSyncConfig)
    name = remote_name_for_bucket(bucket, source)
    build_rclone_client().upsert_remote(config.to_rclone_source_config(name))
    return RcloneRemote(
        name=name,
        fs=config.remote_fs(name),
        include_patterns=config.include_patterns or [],
        exclude_patterns=config.exclude_patterns or [],
    )


@cache
def build_rclone_client() -> RcloneClient:
    return RcloneClient()
