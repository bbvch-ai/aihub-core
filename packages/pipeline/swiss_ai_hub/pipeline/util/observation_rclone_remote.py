import logging
import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from dagster import DagsterInstance
from swiss_ai_hub.core.infrastructure.rclone import RcloneSourceConfig
from swiss_ai_hub.core.secrets import SecretPathTransformer

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote
from swiss_ai_hub.pipeline.types.rclone_token_baseline import RcloneTokenBaseline
from swiss_ai_hub.pipeline.util.source_builders import build_rclone_client, remote_name_for_bucket
from swiss_ai_hub.pipeline.util.stored_source_configuration import StoredSourceConfiguration

logger = logging.getLogger(__name__)

_OBSERVATION_MARKER = "_obs_"


class ObservationRcloneRemote:
    """The remote an observation run lists through, private to that run and deleted when it ends.

    Only this run's calls can refresh the token held in a private section, so the token read back after the
    listing is one this run obtained from the configuration it read, never one a concurrent run on the shared
    ``{source}_{bucket}`` remote refreshed from an older or newer configuration. A run killed before its cleanup
    leaves the section behind; ``sweep`` removes it once Dagster reports the run finished.
    """

    @classmethod
    @contextmanager
    def opened(
        cls,
        bucket: Annotated[str, "Bucket name of the knowledge database"],
        source: Annotated[str, "Source pipeline id this code location runs as"],
        run_id: Annotated[str, "Dagster run id of the observation"],
    ) -> Iterator[RcloneRemote]:
        stored = StoredSourceConfiguration[RcloneSyncConfig].read(bucket, source, RcloneSyncConfig)
        name = cls.name_for(bucket, source, run_id)
        rclone_config = stored.config.to_rclone_source_config(name)
        remote = RcloneRemote.from_config(stored.config, name, cls._baseline(stored, rclone_config))
        client = build_rclone_client()
        try:
            client.upsert_remote(rclone_config)
            yield remote
        finally:
            client.delete_remote(name)

    @staticmethod
    def name_for(
        bucket: Annotated[str, "Bucket name of the knowledge database"],
        source: Annotated[str, "Source pipeline id this code location runs as"],
        run_id: Annotated[str, "Dagster run id of the observation"],
    ) -> str:
        return f"{remote_name_for_bucket(bucket, source)}{_OBSERVATION_MARKER}{UUID(run_id).hex}"

    @classmethod
    def sweep(
        cls,
        instance: Annotated[DagsterInstance, "Instance the observation runs belong to"],
        source: Annotated[str, "Source pipeline id this code location runs as"],
    ) -> int:
        """Deletes the private remotes of finished runs. A remote whose run is unknown is left alone: another
        Dagster instance sharing the daemon may still be running it."""
        pattern = re.compile(rf"^{re.escape(source)}_[A-Za-z0-9]+{_OBSERVATION_MARKER}([0-9a-f]{{32}})$")
        client = build_rclone_client()
        swept = 0
        for name in client.list_remotes():
            match = pattern.match(name)
            if match is None:
                continue
            run = instance.get_run_by_id(str(UUID(match.group(1))))
            if run is None or not run.is_finished:
                continue
            client.delete_remote(name)
            logger.info(f"Deleted rclone remote '{name}' left behind by finished run {run.run_id}")
            swept += 1
        return swept

    @staticmethod
    def _baseline(
        stored: StoredSourceConfiguration[RcloneSyncConfig], rclone_config: RcloneSourceConfig
    ) -> RcloneTokenBaseline | None:
        path = stored.config.refreshable_token_path()
        if path is None:
            return None
        return RcloneTokenBaseline.from_token(
            path=path,
            backend_type=stored.config.backend.value,
            stored_value=SecretPathTransformer.values_at(stored.stored, path)[0],
            sent_token=rclone_config.options["token"],
        )
