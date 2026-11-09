from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class RclonePipelineSettings(EnvironmentSettings):
    """Deployment-level knobs of the rclone source pipeline.

    The schedule and which internal hosts a source may name live here: which databases to sync, from where and with
    which credentials is read from the database per run.
    """

    model_config = EnvironmentSettings.create_settings_config("RCLONE_PIPELINE_")

    OBSERVE_JOB_HOUR: Annotated[
        int,
        Field(
            default=22,
            ge=0,
            le=23,
            description="Hour of the daily per-database sync. Before the ingestion pipeline's midnight observation, "
            "so a day's sync is vectorised by the same night's backstop run.",
        ),
    ]
    OBSERVE_JOB_MINUTE: Annotated[
        int, Field(default=0, ge=0, le=59, description="Minute of the daily per-database sync.")
    ]
    MAX_PARTITIONS: Annotated[
        int,
        Field(default=1000, ge=1, description="Maximum partitions added or removed per database per observation."),
    ]
    ALLOWED_PRIVATE_HOSTS: Annotated[
        str,
        Field(
            default="",
            description="Comma-separated host names an S3 endpoint, Azure endpoint or SFTP host may name although "
            "they are internal, such as an object store reachable only on the company network. Every other internal "
            "host is refused, because a knowledge administrator sets it and the rclone daemon can reach the "
            "platform's own services.",
        ),
    ]

    def private_host_allow_list(self) -> frozenset[str]:
        return frozenset(host.strip().lower() for host in self.ALLOWED_PRIVATE_HOSTS.split(",") if host.strip())
