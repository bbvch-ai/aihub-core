"""Per-database source builders for the rclone source pipeline.

One deployed code location fills every database whose ``source`` names it, so nothing source-specific can be baked
into resources at ``Definitions``-build time. The target database is resolved per run (from the composite partition
key on the partitioned write path, from the ``aihub/bucket`` run tag on the observe/remove path) and its source
configuration is read from the row here. Unlike ``ingestor_config_for_bucket`` there are no deployment defaults to
fall back to: a database without a valid source configuration must not sync from anything.
"""

from functools import cache
from typing import Annotated

from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.pipeline.resources.rclone.rclone_client import RcloneClient
from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote
from swiss_ai_hub.pipeline.util.stored_source_configuration import StoredSourceConfiguration


def source_config_for_bucket[TConfig: SourcePipelineConfig](
    bucket: Annotated[str, "Bucket name of the knowledge database"],
    source: Annotated[str, "Source pipeline id this code location runs as"],
    config_type: type[TConfig],
) -> TConfig:
    """The database's stored source configuration, secrets decrypted, validated into the pipeline's config class."""
    return StoredSourceConfiguration.read(bucket, source, config_type).config


def remote_name_for_bucket(bucket: str, source: str) -> str:
    """One remote per database, prefixed with the source so two rclone-backed pipelines never share a daemon entry."""
    return f"{source}_{bucket}"


@cache
def rclone_remote_for_bucket(bucket: str, source: str) -> RcloneRemote:
    """Rebuilds the database's remote in the rclone daemon from the stored configuration and returns how to address it.

    A host the configuration names must be public (or allowed by the deployment), because the daemon sits on the
    platform's own networks (``RcloneSyncConfig.require_public_hosts``); an S3 remote with an endpoint is sent with a
    path-style provider, so the endpoint host is the only one it contacts. Rebuilding it in every process is what makes
    a credential edit apply on the next run and a restarted daemon (which keeps no config file) need no operator
    action. Cached per process because every op of a partition run loads its input through the IO manager and would
    otherwise re-upsert the same remote three times per file. Write and removal runs share this remote and never write
    a refreshed token back; only the observation does, through a remote of its own (``ObservationRcloneRemote``).
    """
    config = source_config_for_bucket(bucket, source, RcloneSyncConfig)
    config.require_public_hosts()
    name = remote_name_for_bucket(bucket, source)
    remote = RcloneRemote.from_config(config, name)
    build_rclone_client().upsert_remote(config.to_rclone_source_config(name))
    return remote


@cache
def build_rclone_client() -> RcloneClient:
    return RcloneClient()
