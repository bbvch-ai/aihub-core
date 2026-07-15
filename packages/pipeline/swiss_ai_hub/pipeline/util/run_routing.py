from dagster import InitResourceContext, InputContext, OpExecutionContext

from swiss_ai_hub.pipeline.util.partition_utils import bucket_of_composite_partition_key

"""Run-level bucket routing for the RAG pipeline.

A run of the RAG pipeline always targets exactly one knowledge database, but the way that bucket
travels into the run differs by trigger:

- **Partitioned write path** (``documents``/``nodes``/``summary``, launched by the automation sensor):
  the bucket is encoded in the composite partition key ``{bucket}|{file_uri}``. Ops and IO managers that
  see the partition key resolve the bucket from it — auto-materialized runs carry no custom run tag.
- **Non-partitioned observe/remove path** (launched by our schedule / NATS sensor / run-after-success
  sensor): the bucket travels in the ``aihub/bucket`` run tag, the only routing signal available to
  resources (``InitResourceContext`` exposes neither the partition key nor op config).
"""

BUCKET_RUN_TAG = "aihub/bucket"


def bucket_from_resource_init(context: InitResourceContext) -> str:
    """Resolve the run's bucket from the ``aihub/bucket`` run tag during resource initialization."""
    dagster_run = context.dagster_run
    if dagster_run is None or BUCKET_RUN_TAG not in dagster_run.tags:
        raise ValueError(
            f"Routed run requires the '{BUCKET_RUN_TAG}' run tag to resolve its "
            f"target knowledge database, but it was not set on the run."
        )
    return dagster_run.tags[BUCKET_RUN_TAG]


def bucket_from_run_tag(context: OpExecutionContext | InputContext) -> str:
    """Resolve the run's bucket from the ``aihub/bucket`` run tag inside an op or IO manager."""
    run_tags = context.run_tags if isinstance(context, OpExecutionContext) else context.step_context.run_tags
    if BUCKET_RUN_TAG not in run_tags:
        raise ValueError(
            f"Routed run requires the '{BUCKET_RUN_TAG}' run tag to resolve its target "
            f"knowledge database, but it was not set on the run."
        )
    return run_tags[BUCKET_RUN_TAG]


def bucket_from_partition_key(partition_key: str) -> str:
    """Resolve the bucket from a composite partition key ``{bucket}|{file_uri}``."""
    return bucket_of_composite_partition_key(partition_key)
