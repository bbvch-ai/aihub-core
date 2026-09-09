from typing import Annotated

from pydantic import BaseModel, Field


class RcloneRemote(BaseModel):
    """Where one knowledge database's files are listed and downloaded from, resolved per run.

    ``fs`` is the rclone remote spec (``name:path``) every RC call takes; the patterns are the database's own
    rclone filter rules. Nothing here carries credentials — those went into the rclone daemon when the remote
    was upserted, and only its name travels through logs and Dagster metadata.
    """

    name: Annotated[str, Field(description="Remote name registered in the rclone daemon, one per database.")]
    fs: Annotated[str, Field(description="Remote spec passed to rclone, e.g. 'rclone_hrdocs:Shared Documents'.")]
    include_patterns: Annotated[list[str], Field(description="rclone glob rules to include.")] = []
    exclude_patterns: Annotated[list[str], Field(description="rclone glob rules to exclude.")] = []
