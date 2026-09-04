from dagster import JobDefinition, job

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import knowledge_teardown_op


def knowledge_teardown_job(*, source_location_name: str) -> JobDefinition:
    """One-op job that performs an asynchronous knowledge database / namespace teardown.

    The job name is derived from the ingestor so a second pipeline *type* deployed in the same instance
    gets its own teardown job rather than colliding on the name. Parameters arrive as op run config from
    the teardown sensor; the run is bucket-tagged so any tag-routed resources resolve correctly.
    """

    @job(
        name=f"{source_location_name}_knowledge_teardown",
        description="Asynchronous teardown of a knowledge database or one of its namespaces.",
    )
    def _job() -> None:
        knowledge_teardown_op()

    return _job
