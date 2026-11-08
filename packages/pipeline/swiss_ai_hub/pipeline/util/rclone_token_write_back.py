import logging
from typing import Annotated

from swiss_ai_hub.core.persistence import BucketEntity
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.pipeline.types.rclone_remote import RcloneRemote
from swiss_ai_hub.pipeline.types.rclone_token_baseline import RcloneTokenBaseline
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.source_builders import build_rclone_client

logger = logging.getLogger(__name__)


class RcloneTokenWriteBack:
    """Stores the OAuth token rclone refreshed during an observation, so the next run starts from it.

    rclone refreshes an expired access token in its in-memory daemon only, and every run rebuilds the remote from
    the database. Microsoft rotates the refresh token on every refresh, so without this a pasted token stops working
    once its original refresh token expires. Logs name only the remote; the token, its digest and its ciphertext
    never reach a log, an exception or Dagster metadata.
    """

    @classmethod
    def persist_refreshed_token(
        cls,
        bucket: Annotated[str, "Bucket name of the knowledge database"],
        source: Annotated[str, "Source pipeline id this code location runs as"],
        remote: Annotated[RcloneRemote, "The observation's private remote, still open"],
    ) -> bool:
        """True when the refreshed token was stored. Nothing to store, a refused token and a database edited since
        this run read it all return False without raising: none of them is a reason to fail the observation."""
        baseline = remote.token_baseline
        if baseline is None:
            return False
        token = build_rclone_client().get_token(remote.name)
        if token is None:
            logger.warning(f"rclone remote '{remote.name}' holds no OAuth token any more; nothing written back")
            return False
        refreshed = token.get_secret_value()
        if RcloneTokenBaseline.digest(refreshed) == baseline.sent_digest:
            logger.debug(f"OAuth token of rclone remote '{remote.name}' unchanged; nothing written back")
            return False
        if baseline.had_refresh_token and not RcloneTokenBaseline.has_refresh_token(refreshed):
            logger.warning(
                f"Refused to store the OAuth token of rclone remote '{remote.name}': it has lost its refresh token"
            )
            return False
        if baseline.stored_ciphertext is None:
            logger.warning(
                f"OAuth token of rclone remote '{remote.name}' is not stored encrypted; the refreshed one is not "
                "written back. Save the source again to encrypt it."
            )
            return False
        return cls._replace(bucket, source, remote.name, baseline, refreshed)

    @staticmethod
    def _replace(
        bucket: Annotated[str, "Bucket name of the knowledge database"],
        source: Annotated[str, "Source pipeline id this code location runs as"],
        remote_name: Annotated[str, "Name of the observation's rclone remote, the only thing logged"],
        baseline: Annotated[RcloneTokenBaseline, "What the remote was created with"],
        refreshed: Annotated[str, "The refreshed token JSON, plaintext"],
    ) -> bool:
        ensure_main_db_connection()
        stored = BucketEntity.replace_source_secret(
            bucket_name=bucket,
            source=source,
            backend_type=baseline.backend_type,
            path=baseline.path,
            expected=baseline.stored_ciphertext,
            replacement=SecretEncryptionService.from_settings().encrypt(refreshed),
        )
        if stored:
            logger.info(f"Stored the refreshed OAuth token of rclone remote '{remote_name}'")
        else:
            logger.info(
                f"Kept the database's OAuth token for rclone remote '{remote_name}': the stored token, the backend "
                "or the source changed since this run read it, or the database is being deleted"
            )
        return stored
