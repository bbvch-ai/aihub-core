from dagster import Definitions, DefaultSensorStatus, SensorEvaluationContext, SkipReason, sensor
from mongoengine import DoesNotExist
from swiss_ai_hub.core.infrastructure import RagPipelineSettings
from swiss_ai_hub.core.persistence import BucketEntity, IngestorType

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.rag_definitions_util import rag_pipeline_definitions

PLAYGROUND_BUCKET = "playground"


@sensor(
    minimum_interval_seconds=300,
    default_status=DefaultSensorStatus.RUNNING,
    name="PlaygroundBucketSensor",
    description="Registers the playground's knowledge database so the pipeline routes runs to it.",
)
def playground_bucket_sensor(context: SensorEvaluationContext):
    """Gives the playground a knowledge database of its own.

    The configurable pipeline has no fixed bucket — it discovers the databases it owns from
    ``BucketEntity`` — so the playground needs a row rather than a container name. Registering from a
    sensor rather than at import keeps the code location loadable while Mongo is still coming up.
    """
    ensure_main_db_connection()
    try:
        BucketEntity.get_bucket_by_bucket_name(PLAYGROUND_BUCKET)
    except DoesNotExist:
        BucketEntity.create_bucket(
            bucket_name=PLAYGROUND_BUCKET, db_name=PLAYGROUND_BUCKET, ingestor=IngestorType.RAG.value
        )
        return SkipReason(f"Created the '{PLAYGROUND_BUCKET}' knowledge database.")
    return SkipReason(f"The '{PLAYGROUND_BUCKET}' knowledge database exists.")


settings = RagPipelineSettings()

_pipeline = rag_pipeline_definitions(
    embedding_model_name=settings.EMBEDDING_MODEL,
    llm_model_name=settings.LLM_MODEL,
    with_summary_nodes=settings.WITH_SUMMARY_NODES,
    with_table_refinement=settings.WITH_TABLE_REFINEMENT,
    with_figure_descriptions=settings.WITH_FIGURE_DESCRIPTIONS,
    observe_job_hour=2,
    observe_job_minute=0,
)

defs = Definitions(
    assets=_pipeline.assets,
    resources=_pipeline.resources,
    sensors=[*_pipeline.sensors, playground_bucket_sensor],
    jobs=_pipeline.jobs,
    schedules=_pipeline.schedules,
    executor=_pipeline.executor,
)
