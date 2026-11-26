from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.types.rclone_token_baseline import RcloneTokenBaseline


class RcloneRemote(BaseModel):
    """Where one knowledge database's files are listed and downloaded from, resolved per run.

    ``fs`` is the rclone remote spec (``name:path``) every RC call takes; the patterns are the database's own
    rclone filter rules. Nothing here carries a plaintext credential — those went into the rclone daemon when the
    remote was upserted, and only its name travels through logs and Dagster metadata. An observation's remote also
    carries the baseline its refreshed OAuth token is compared with before it is written back.
    """

    name: Annotated[str, Field(description="Remote name registered in the rclone daemon, one per database.")]
    fs: Annotated[str, Field(description="Remote spec passed to rclone, e.g. 'rclone_hrdocs:Shared Documents'.")]
    include_patterns: Annotated[list[str], Field(description="rclone glob rules to include.")] = []
    exclude_patterns: Annotated[list[str], Field(description="rclone glob rules to exclude.")] = []
    token_baseline: Annotated[
        RcloneTokenBaseline | None,
        Field(description="Set only on an observation's remote whose source holds a refreshable OAuth token."),
    ] = None

    @classmethod
    def from_config(
        cls,
        config: Annotated[RcloneSyncConfig, "The database's validated source configuration"],
        name: Annotated[str, "Remote name the configuration was upserted under"],
        token_baseline: Annotated[RcloneTokenBaseline | None, "Set for an observation's private remote"] = None,
    ) -> Self:
        return cls(
            name=name,
            fs=config.remote_fs(name),
            include_patterns=config.include_patterns or [],
            exclude_patterns=config.exclude_patterns or [],
            token_baseline=token_baseline,
        )
