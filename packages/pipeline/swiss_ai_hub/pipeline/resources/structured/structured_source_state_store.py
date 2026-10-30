import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Annotated, Any

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.types.structured_source_state import StructuredSourceState
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client

_STATE_FILE = "state.json"


class StructuredSourceStateStore:
    """Keeps one database's dlt state in that database's own bucket between syncs.

    dlt cannot restore state from a custom destination and every run starts in an empty working directory, so
    without this each run would re-read the whole source. The state sits in a ``.{source}_dagster`` folder, which
    data lake listings skip, because the ``dagster`` bucket expires its objects after a day; and it is torn down with
    the database. Save only after a fully successful run: dlt advances the cursor while extracting, before any file
    is written.
    """

    def __init__(
        self,
        source: Annotated[str, "Source pipeline id, so two structured pipelines never share state"],
        bucket: Annotated[str, "Bucket name of the knowledge database the state belongs to"],
    ):
        self.bucket = bucket
        self.object_key = f".{source}_dagster/{_STATE_FILE}"

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

    def save(
        self,
        pipeline_dir: Path,
        scope_fingerprint: str,
        unread_files: Annotated[set[str], "Keys of files the source would not serve this run"] = frozenset(),
    ) -> None:
        """Keeps the keys the previous run listed without a file, which the listing after this sync compares
        against; a changed scope drops them, since that run re-reads everything anyway.

        A file that could not be read was already recorded as seen while dlt extracted, before it was loaded, so it is
        removed from every resource's file map here and the next run tries it again.
        """
        stored = self._load()
        missing_keys = stored.missing_keys if stored and stored.scope_fingerprint == scope_fingerprint else []
        pipeline_state = json.loads((pipeline_dir / _STATE_FILE).read_text())
        self._forget_files(pipeline_state, unread_files)
        state = StructuredSourceState(
            scope_fingerprint=scope_fingerprint, pipeline_state=pipeline_state, missing_keys=missing_keys
        )
        self._put(state)

    def missing_at_last_run(self) -> set[str]:
        stored = self._load()
        return set(stored.missing_keys) if stored else set()

    def remember_missing(self, keys: Annotated[set[str], "Keys this run listed without a file"]) -> None:
        """Does nothing without a stored state, so it never brings back a state the sync chose not to keep."""
        stored = self._load()
        if stored is not None:
            self._put(stored.model_copy(update={"missing_keys": sorted(keys)}))

    @staticmethod
    def _forget_files(pipeline_state: dict[str, Any], keys: set[str]) -> None:
        """dlt keeps a resource's state at ``sources.<source>.resources.<resource>``; anything else in the state is
        dlt's own bookkeeping and left as it is."""
        for source_state in _mappings((pipeline_state.get("sources") or {}).values()):
            for resource_state in _mappings((source_state.get("resources") or {}).values()):
                seen = resource_state.get(AbstractStructuredSourceAdapter.FILES_SEEN)
                if isinstance(seen, dict):
                    for key in keys:
                        seen.pop(key, None)

    def delete(self) -> None:
        self._client().delete_object(Bucket=self.bucket, Key=self.object_key)

    def _put(self, state: StructuredSourceState) -> None:
        self._client().put_object(Bucket=self.bucket, Key=self.object_key, Body=state.model_dump_json())

    def _load(self) -> StructuredSourceState | None:
        try:
            body = self._client().get_object(Bucket=self.bucket, Key=self.object_key)["Body"].read()
        except ClientError as error:
            if error.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise
        return StructuredSourceState.model_validate_json(body)

    def _client(self) -> BaseClient:
        return build_s3_data_lake_client(self.bucket, ensure_bucket=False).raw_client


def _mappings(values: Iterable[Any]) -> Iterator[dict[str, Any]]:
    return (value for value in values if isinstance(value, dict))
