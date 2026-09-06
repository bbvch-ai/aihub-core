import logging
from typing import Annotated

from dagster import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext, SkipReason, sensor
from swiss_ai_hub.core.persistence import BucketEntity, Ingestor, IngestorEntity

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

logger = logging.getLogger(__name__)

_REGISTRATION_INTERVAL_SECONDS = 300


def ingestor_registration_sensor(
    ingestor: Annotated[Ingestor, "This pipeline's labels, form and schema"],
) -> SensorDefinition:
    """Advertises this pipeline as a selectable ingestor, with the form its databases are configured through.

    The API and the pipelines are separate containers, so a pipeline cannot hand the API anything
    in-process; it publishes its metadata to the database both already share — the ingestor counterpart of
    an agent's discovery response. Doing that from a sensor rather than at import keeps a momentary Mongo
    outage from taking the whole code location down, and re-registers automatically once the database is back.
    """

    @sensor(
        minimum_interval_seconds=_REGISTRATION_INTERVAL_SECONDS,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"IngestorRegistrationSensorFor_{ingestor.id}",
        description="Keeps this pipeline listed as a selectable ingestor, with its configuration form, for new "
        "knowledge databases.",
    )
    def _sensor(context: SensorEvaluationContext) -> SkipReason:
        ensure_main_db_connection()
        IngestorEntity.upsert(ingestor)
        carried = BucketEntity.carry_over_retired_model_columns()
        if carried:
            context.log.info(f"Carried the retired model columns of {carried} knowledge database(s) into configuration")
        return SkipReason(f"Ingestor '{ingestor.id}' is registered.")

    return _sensor
