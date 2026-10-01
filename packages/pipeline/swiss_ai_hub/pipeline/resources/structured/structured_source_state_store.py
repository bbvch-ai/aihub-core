import json
from pathlib import Path
from typing import Annotated

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from swiss_ai_hub.pipeline.types.structured_source_state import StructuredSourceState
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client

_STATE_FILE = "state.json"


class StructuredSourceStateStore:
    """Keeps one database's dlt state in the Dagster bucket between syncs.

    dlt cannot restore state from a custom destination and every step starts in an empty working directory, so
    without this each run would re-read the whole source. Save only after a fully successful run: dlt advances the
    cursor while extracting, before any file is written.
    """

    STATE_BUCKET = "dagster"

    def __init__(
        self,
        source: Annotated[str, "Source pipeline id, so two structured pipelines never share state"],
        bucket: Annotated[str, "Bucket name of the knowledge database the state belongs to"],
    ):
        self.object_key = f"{source}/state/{bucket}.json"

    def restore(
        self,
        pipeline_dir: Annotated[Path, "dlt's working directory of this database's pipeline"],
        scope_fingerprint: Annotated[str, "Fingerprint of the configuration the run syncs with"],
    ) -> bool:
        """Puts the stored state into ``pipeline_dir``. False when there is none or the scope changed since, which
        makes the run read everything again."""
        stored = self._load()
        if stored is None or stored.scope_fingerprint != scope_fingerprint:
            return False
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        (pipeline_dir / _STATE_FILE).write_text(json.dumps(stored.pipeline_state))
        return True

    def save(self, pipeline_dir: Path, scope_fingerprint: str) -> None:
        state = StructuredSourceState(
            scope_fingerprint=scope_fingerprint,
            pipeline_state=json.loads((pipeline_dir / _STATE_FILE).read_text()),
        )
        self._client().put_object(Bucket=self.STATE_BUCKET, Key=self.object_key, Body=state.model_dump_json())

    def delete(self) -> None:
        self._client().delete_object(Bucket=self.STATE_BUCKET, Key=self.object_key)

    def _load(self) -> StructuredSourceState | None:
        try:
            body = self._client().get_object(Bucket=self.STATE_BUCKET, Key=self.object_key)["Body"].read()
        except ClientError as error:
            if error.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise
        return StructuredSourceState.model_validate_json(body)

    def _client(self) -> BaseClient:
        return build_s3_data_lake_client(self.STATE_BUCKET, ensure_bucket=False).raw_client
