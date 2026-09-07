from dagster import JobDefinition, job

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import knowledge_teardown_op


def knowledge_teardown_job(*, source_location_name: str) -> JobDefinition:
    """One-op job that performs an asynchronous knowledge namespace teardown.

    The job name is derived from the bucket so two deploy-bound pipelines in the same Dagster instance get
    their own teardown job rather than colliding on the name. Parameters arrive as op run config from the
    teardown sensor.
    """

    @job(
        name=f"{source_location_name}_knowledge_teardown",
        description="Asynchronous teardown of one knowledge namespace.",
    )
    def _job() -> None:
        knowledge_teardown_op()

    return _job
