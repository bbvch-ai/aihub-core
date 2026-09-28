from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class RclonePipelineSettings(EnvironmentSettings):
    """Deployment-level knobs of the rclone source pipeline.

    Only the schedule lives here: which databases to sync, from where and with which credentials is read
    from the database per run, so a deployment has nothing source-specific to configure.
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
